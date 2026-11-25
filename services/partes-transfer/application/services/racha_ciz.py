# application/services/racha_ciz.py
"""F-060 · El CIZ de una racha de incidencia se mueve, no se duplica
(regla pura, design §5).

Semantica 4: una racha de incidencia se registra en Sigrid con su codigo
CI* el primer dia y UN `CIZ` el ultimo. sv4 decide el rol de cada dia con
el historico de `partes` y, con el rol `fin`, manda `racha_registro_ids`:
las lineas de esa racha. sv5 lee de Sigrid las lineas con esas synckeys y
`decidir_fin` dice que hacer con el `fin` del dia D:

  - filtra las del mismo recurso, codigo `CIZ` y `can` nulo o 0 y, en modo
    pruebas, con la marca en `tex` (R13, R19: una sin marca no existe);
  - alguna posterior a D => `intermedio`: el fin ya esta mas adelante
    (R14, llegada desordenada), y el motivo nombra su dia; F-083: tambien
    con una linea de la racha posterior de otro codigo (ver abajo);
  - si no, la anterior de mayor (fecha, `ide`) es la que se mueve: si esta
    enlazada => `enlazada` (R18, motivo de F-053); si su parte no esta En
    registro => `parte_cerrado` (R17); si no => `mover`, con cuantas
    anteriores mas habia (`duplicados`, R15);
  - nada => `crear`: el `INSERT` de siempre (R16).

F-062 · el `inicio` escribe su CI* y un CIZ el mismo dia (el «hermano»,
synckey `partes:<X>:ciz`) cuando sv4 lo marca con `ciz_mismo_dia`:

  - `decidir_mismo_dia` (R11, DA5): sin hermano si ya existe
    (`ya_existe`, una reaprobacion) o si la racha ya tiene un CIZ del
    recurso despues de D en su tramo delante (`posterior`);
  - el siguiente `fin` lee tambien `partes:<i>:ciz` de cada id de su lista
    y `decidir_fin`, sin cambios, mueve el hermano como cualquier CIZ;
    `registro_de_synckey` da None para la synckey de un hermano, asi que
    moverlo no deja `movida_de` (X conserva su CI*, R19).

F-083 · una racha solo lleva CIZ en su ultimo dia, aunque se apruebe
desordenada o el CIZ se haya tocado a mano en Sigrid. Desde F-083,
cualquier linea de la racha posterior en Sigrid, sea cual sea su codigo
(`es_linea_de_la_racha`: mismo recurso, `can` nulo o 0 y, en pruebas, la
marca), deja el dia como intermedio, y un CIZ cambiado a mano deja la racha
sin fin:

  - `decidir_fin`: sin CIZ posterior pero con otra linea de la racha
    posterior => `intermedio` con `sin_ciz` y `motivo_intermedio_racha`,
    antes de mover, `enlazada` o `parte_cerrado` (R2-R4, R7);
  - `decidir_mismo_dia`: igual => `MOTIVO_POSTERIOR_SIN_CIZ`, sin hermano
    (R8, R9). Un CIZ posterior sigue mandando (`posterior`, F-060 R14).

En Sigrid no se borra (regla del humano): mover es un `UPDATE` de la linea
(`stmt_mover_linea`), nunca un borrado y un alta. Motivos sin tildes como
el resto de sv5, sin nombres ni DNIs y de 255 caracteres como mucho
(`sigrid_motivo` de sv4). No lee ni escribe: lo llama `RegistroPipeline`.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from application.services.pisado import PREFIJO_PARTES, motivo_linea_enlazada
from application.services.reglas_registro import MOTIVO_INTERMEDIO
from domain.models.registro_models import LineaSigrid, ParteSigrid
from infrastructure.sigrid.sigrid_write_client import SUFIJO_CIZ

#: Codigo de hora del fin de incidencia en Sigrid.
CODIGO_FIN = "CIZ"

#: Prefijo del motivo de un CIZ que no se mueve por estar su parte cerrado.
MOTIVO_CIZ_EN_PARTE_CERRADO = "ciz_en_parte_cerrado"

#: Largo maximo de un motivo (`parte_registro.sigrid_motivo` de sv4).
LIMITE_MOTIVO = 255

#: Tipos de decision.
CREAR, MOVER, INTERMEDIO = "crear", "mover", "intermedio"
PARTE_CERRADO, ENLAZADA = "parte_cerrado", "enlazada"

#: F-062 (R11, R12, R16): por que un inicio no escribe su CIZ hermano.
MOTIVO_POSTERIOR = "posterior"          # la racha ya tiene su CIZ despues
MOTIVO_YA_EXISTE = "ya_existe"          # `partes:<D>:ciz` ya esta escrito
MOTIVO_CIZ_EN_SIGRID = "ciz_en_sigrid"  # CIZ ajeno del recurso el dia D

#: F-083 (R8): el inicio no escribe hermano: la racha sigue despues sin CIZ.
MOTIVO_POSTERIOR_SIN_CIZ = "posterior_sin_ciz"


@dataclass(frozen=True)
class DecisionFin:
    """Que hacer con el `fin` de una racha (design §5)."""
    tipo: str                       # crear | mover | intermedio | ...
    linea: LineaSigrid | None = None  # la que se mueve (`mover`)
    motivo: str | None = None       # el de la omision
    duplicados: int = 0             # otras anteriores que no se tocan
    sin_ciz: bool = False           # F-083 (R7): intermedio por una linea
    #                                 de la racha posterior que no es CIZ


def fecha_iso(fecha_int: int) -> str:
    """20261006 -> «2026-10-06»."""
    f = f"{int(fecha_int):08d}"
    return f"{f[:4]}-{f[4:6]}-{f[6:]}"


def motivo_intermedio_ciz(ide: int, fecha_int: int) -> str:
    """R14: el fin de la racha ya esta en un dia posterior."""
    return (f"{MOTIVO_INTERMEDIO} (el fin, CIZ linea {ide}, ya esta el dia "
            f"{fecha_iso(fecha_int)})")[:LIMITE_MOTIVO]


def motivo_ciz_en_parte_cerrado(ide: int, cod: str | None,
                                estado: str) -> str:
    """R17: el CIZ que habria que mover vive en un parte cerrado."""
    return (f"{MOTIVO_CIZ_EN_PARTE_CERRADO}: el fin de la incidencia (CIZ, "
            f"linea {ide}) esta en el parte {cod or '?'} ({estado}), que ya "
            f"no esta En registro; no se mueve ni se escribe otro. "
            f"Corrigelo en Sigrid")[:LIMITE_MOTIVO]


def registro_de_synckey(synckey: str | None) -> int | None:
    """«partes:3» -> 3 (R23: el `movida_de` de la escrita); None si la
    synckey no es de este proyecto. F-062 (R20): None tambien para la de un
    CIZ hermano («partes:3:ciz»): no es la synckey de ningun registro, asi
    que moverlo no deja `movida_de` (la linea 3 conserva su CI*)."""
    sk = (synckey or "").strip()
    if not sk.startswith(PREFIJO_PARTES) or sk.endswith(SUFIJO_CIZ):
        return None
    try:
        return int(sk[len(PREFIJO_PARTES):])
    except ValueError:
        return None


def motivo_intermedio_racha(ide: int, fecha_int: int, cod: str | None) -> str:
    """F-083 (R2, R19): la racha sigue en Sigrid despues de D con una linea
    que no es CIZ (un CIZ cambiado a mano, por ejemplo): no se escribe un
    fin en medio. Agrupa con los intermedios por el prefijo."""
    return (f"{MOTIVO_INTERMEDIO} (la racha sigue en Sigrid el dia "
            f"{fecha_iso(fecha_int)}, linea {ide} con {cod or 'sin codigo'}, "
            f"sin CIZ despues; no se escribe un fin en medio)")[:LIMITE_MOTIVO]


def es_linea_de_la_racha(ls: LineaSigrid, recurso_ide: int,
                         marca_pruebas: str | None) -> bool:
    """F-083 (D5): mismo recurso, `can` nulo o 0 y, en pruebas, con la
    marca en `tex` (F-060 R19). Cualquier codigo de hora."""
    return (ls.reside == recurso_ide
            and float(ls.can or 0) == 0
            and (not marca_pruebas or marca_pruebas in (ls.tex or "")))


def es_ciz_del_recurso(ls: LineaSigrid, recurso_ide: int,
                       marca_pruebas: str | None) -> bool:
    """R13 y R19: una linea de la racha con codigo `CIZ`. F-062 (R11) la
    usa tambien para el inicio."""
    return (es_linea_de_la_racha(ls, recurso_ide, marca_pruebas)
            and (ls.hora_codigo or "").strip().upper() == CODIGO_FIN)


def ultima_posterior(candidatas: Iterable[LineaSigrid], fecha_int: int,
                     recurso_ide: int, marca_pruebas: str | None, *,
                     solo_ciz: bool) -> LineaSigrid | None:
    """F-083: la linea de la racha (o, con `solo_ciz`, el CIZ de la racha)
    de mayor (fecha, `ide`) con fecha posterior a D; None si no hay."""
    cuenta = es_ciz_del_recurso if solo_ciz else es_linea_de_la_racha
    posteriores = [ls for ls in candidatas if ls.fecha_int > fecha_int
                   and cuenta(ls, recurso_ide, marca_pruebas)]
    if not posteriores:
        return None
    return max(posteriores, key=lambda ls: (ls.fecha_int, ls.ide))


def _nombre_por_defecto(est: int | None) -> str:
    return f"estado {est}"


def decidir_fin(
    fecha_int: int, recurso_ide: int, candidatas: Iterable[LineaSigrid], *,
    partes: Mapping[int, ParteSigrid], est_registro: int,
    marca_pruebas: str | None,
    nombre_estado: Callable[[int | None], str] = _nombre_por_defecto,
) -> DecisionFin:
    """R14-R19: la decision para el `fin` del dia `fecha_int`.

    `partes` son los partes de las candidatas (`hmo.ide` -> su codigo y
    estado); uno que no esta no se pudo leer y cuenta como cerrado (no se
    escribe a ciegas). `nombre_estado` da el nombre del estado para el
    motivo de R17 (el `_nombre_estado` del pipeline). F-083 (R2): sin CIZ
    posterior pero con otra linea de la racha posterior, `intermedio` con
    `sin_ciz`."""
    candidatas = list(candidatas)
    ultima = ultima_posterior(candidatas, fecha_int, recurso_ide,
                              marca_pruebas, solo_ciz=True)
    if ultima is not None:
        return DecisionFin(tipo=INTERMEDIO, motivo=motivo_intermedio_ciz(
            ultima.ide, ultima.fecha_int))
    # F-083 (R2-R4): la racha sigue despues de D sin CIZ (un CIZ cambiado a
    # mano): intermedio, antes de mirar las anteriores, su enlace o su parte.
    sigue = ultima_posterior(candidatas, fecha_int, recurso_ide,
                             marca_pruebas, solo_ciz=False)
    if sigue is not None:
        return DecisionFin(tipo=INTERMEDIO, sin_ciz=True,
                           motivo=motivo_intermedio_racha(
                               sigue.ide, sigue.fecha_int, sigue.hora_codigo))
    anteriores = [ls for ls in candidatas if ls.fecha_int < fecha_int
                  and es_ciz_del_recurso(ls, recurso_ide, marca_pruebas)]
    if not anteriores:
        return DecisionFin(tipo=CREAR)
    elegida = max(anteriores, key=lambda ls: (ls.fecha_int, ls.ide))
    parte = partes.get(int(elegida.hmoide or 0))
    cod = parte.cod if parte is not None else None
    if elegida.enlazada:
        return DecisionFin(tipo=ENLAZADA, motivo=motivo_linea_enlazada(
            [elegida.ide], cod))
    if parte is None or parte.est != est_registro:
        est = parte.est if parte is not None else None
        return DecisionFin(tipo=PARTE_CERRADO, motivo=(
            motivo_ciz_en_parte_cerrado(elegida.ide, cod,
                                        nombre_estado(est))))
    return DecisionFin(tipo=MOVER, linea=elegida,
                       duplicados=len(anteriores) - 1)


def decidir_mismo_dia(
    fecha_int: int, recurso_ide: int, candidatas: Iterable[LineaSigrid],
    propia: LineaSigrid | None, *, marca_pruebas: str | None,
) -> str | None:
    """F-062 (R11, DA5): si el `inicio` del dia D escribe su CIZ hermano.

    `candidatas` son las lineas leidas por las synckeys `partes:<i>` y
    `partes:<i>:ciz` del tramo delante del inicio (sv4); `propia`, la de
    `partes:<D>:ciz`. `MOTIVO_YA_EXISTE` si el hermano ya esta escrito (una
    reaprobacion); `MOTIVO_POSTERIOR` si la racha ya tiene un CIZ del
    recurso despues de D (llegada desordenada: no se escribe otro); F-083
    (R8): `MOTIVO_POSTERIOR_SIN_CIZ` si, sin CIZ, la racha tiene otra linea
    despues de D; None = se escribe."""
    if propia is not None:
        return MOTIVO_YA_EXISTE
    candidatas = list(candidatas)
    if ultima_posterior(candidatas, fecha_int, recurso_ide, marca_pruebas,
                        solo_ciz=True) is not None:
        return MOTIVO_POSTERIOR
    if ultima_posterior(candidatas, fecha_int, recurso_ide, marca_pruebas,
                        solo_ciz=False) is not None:
        return MOTIVO_POSTERIOR_SIN_CIZ
    return None
