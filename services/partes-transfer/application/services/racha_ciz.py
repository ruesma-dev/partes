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
    (R14, llegada desordenada), y el motivo nombra su dia;
  - si no, la anterior de mayor (fecha, `ide`) es la que se mueve: si esta
    enlazada => `enlazada` (R18, motivo de F-053); si su parte no esta En
    registro => `parte_cerrado` (R17); si no => `mover`, con cuantas
    anteriores mas habia (`duplicados`, R15);
  - nada => `crear`: el `INSERT` de siempre (R16).

En Sigrid no se borra (regla del humano): mover es un `UPDATE` de la linea
(`stmt_mover_linea`), nunca un borrado y un alta. Motivos sin tildes como
el resto de sv5, sin nombres ni DNIs y de 255 caracteres como mucho
(`sigrid_motivo` de sv4). No lee ni escribe: lo llama `RegistroPipeline`.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from application.services.pisado import motivo_linea_enlazada
from application.services.reglas_registro import MOTIVO_INTERMEDIO
from domain.models.registro_models import LineaSigrid, ParteSigrid

#: Codigo de hora del fin de incidencia en Sigrid.
CODIGO_FIN = "CIZ"

#: Prefijo del motivo de un CIZ que no se mueve por estar su parte cerrado.
MOTIVO_CIZ_EN_PARTE_CERRADO = "ciz_en_parte_cerrado"

#: Largo maximo de un motivo (`parte_registro.sigrid_motivo` de sv4).
LIMITE_MOTIVO = 255

#: Tipos de decision.
CREAR, MOVER, INTERMEDIO = "crear", "mover", "intermedio"
PARTE_CERRADO, ENLAZADA = "parte_cerrado", "enlazada"


@dataclass(frozen=True)
class DecisionFin:
    """Que hacer con el `fin` de una racha (design §5)."""
    tipo: str                       # crear | mover | intermedio | ...
    linea: LineaSigrid | None = None  # la que se mueve (`mover`)
    motivo: str | None = None       # el de la omision
    duplicados: int = 0             # otras anteriores que no se tocan


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


def _es_ciz_del_recurso(ls: LineaSigrid, recurso_ide: int,
                        marca_pruebas: str | None) -> bool:
    """R13 y R19: mismo recurso, codigo `CIZ`, sin horas y, en pruebas, con
    la marca en `tex`."""
    return (ls.reside == recurso_ide
            and (ls.hora_codigo or "").strip().upper() == CODIGO_FIN
            and float(ls.can or 0) == 0
            and (not marca_pruebas or marca_pruebas in (ls.tex or "")))


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
    motivo de R17 (el `_nombre_estado` del pipeline)."""
    ciz = [ls for ls in candidatas
           if _es_ciz_del_recurso(ls, recurso_ide, marca_pruebas)]
    posteriores = [ls for ls in ciz if ls.fecha_int > fecha_int]
    if posteriores:
        ultima = max(posteriores, key=lambda ls: (ls.fecha_int, ls.ide))
        return DecisionFin(tipo=INTERMEDIO, motivo=motivo_intermedio_ciz(
            ultima.ide, ultima.fecha_int))
    anteriores = [ls for ls in ciz if ls.fecha_int < fecha_int]
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
