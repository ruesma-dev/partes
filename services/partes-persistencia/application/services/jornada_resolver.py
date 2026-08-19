# application/services/jornada_resolver.py
"""Jornada teorica (horas ordinarias esperadas por dia) del recurso.

UN solo sitio con la regla, que el computo de extras llevaba escrita a
mano dentro de `_reclasificar_extras_jornada`: el `candef` de Sigrid manda
si esta informado (estrictamente por encima del minimo); si no, la jornada
por defecto. Un `candef` de 0/1/2 significa "Sigrid no lo tiene
informado", no "este hombre trabaja dos horas": sin el umbral, el dia
entero se iria a horas extra.

GEMELO del de sv4 (`services/partes-front/application/services/
jornada_resolver.py`): adaptadores por servicio, sin libreria compartida
(docs/ARCHITECTURE.md). Quien cambie la regla cambia LAS DOS copias; hay
un test que compara ambas implementaciones.

F-003 deja aqui el ENCHUFE para la jornada real del contrato (Sesame).
Hoy no se puede: `GET /api/v1/jornada` de sesame-api devuelve el tipo de
jornada y si es reducida, pero NO las horas (peticion P1 del design).

F-015 anade ENCIMA (sin tocar `jornada_efectiva` ni `candef_valido`) la
jornada del DIA: el candef efectivo `c` es lo que se hace de lunes a
jueves, y el ULTIMO dia laborable de la semana recibe el resto de la
jornada semanal `S` (`max(0, S - 4c)`). `S` sale de un mapa configurable
candef -> semanal, o de una excepcion por trabajador. Con `c = 8` y
`S = 40` el resto es 8: identico a antes de F-015 (regresion cero).

Todo lo de aqui son FUNCIONES PURAS: el calendario llega ya ligado al DNI
como callable `es_laborable(date) -> bool` y los avisos los emite quien
llama, que es quien sabe deduplicarlos por recurso y por pasada.
"""
# NOTA (F-015): este modulo NO lleva `from __future__ import
# annotations` a proposito. Se carga por RUTA como modulo suelto
# desde dos guardianes del monorepo (el gemelo de F-003 y el de
# F-015), y con las anotaciones aplazadas `@dataclass` intenta
# resolverlas por `sys.modules[cls.__module__]`, que en esa forma de
# carga no existe: las dataclases de aqui abajo no se podrian
# construir. Las anotaciones nativas de 3.12 bastan para lo que hay.

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Mapping

#: Tolerancia para comparar horas (los datos vienen en float desde Sigrid).
_EPS = 1e-9

#: Cota superior de cualquier cantidad de horas configurada: una semana.
_MAX_HORAS = 24.0 * 7


def candef_valido(candef: float | str | None, *, minimo: float) -> bool:
    """True si Sigrid informa una jornada creible para el recurso."""
    if candef is None or candef == "":
        return False
    try:
        valor = float(candef)
    except (TypeError, ValueError):
        return False
    return valor > float(minimo)


def jornada_efectiva(
    candef: float | str | None, *, minimo: float, por_defecto: float
) -> float:
    """Horas ordinarias del dia: `candef` si es valido, si no `por_defecto`.

    `candef` se tolera como texto (llega de Sigrid) y como `None`.
    Cualquier valor no numerico se trata como no informado.
    """
    if not candef_valido(candef, minimo=minimo):
        return float(por_defecto)
    return float(candef)  # type: ignore[arg-type]


# ======================= F-015 · jornada del DIA ======================== #

def parsear_mapa_semanal(texto: str) -> dict[float, float]:
    """'8:40,9:42' -> {8.0: 40.0, 9.0: 42.0}.

    `ValueError` si esta mal formado: par sin ':', clave o valor no
    numericos, clave repetida, cadena vacia u horas fuera de (0, 24*7].
    Se llama en el CABLEADO de cada servicio para que un mapa invalido
    tire el ARRANQUE (fail-fast): un mapa mal escrito cambiaria el
    reparto ordinaria/extra de todo el mundo y en caliente no se veria.
    """
    if texto is None or not str(texto).strip():
        raise ValueError(
            "JORNADA_SEMANAL_POR_CANDEF vacio: se esperaba algo como "
            "'8:40,9:42'"
        )
    mapa: dict[float, float] = {}
    for par in str(texto).split(","):
        crudo = par.strip()
        if not crudo:
            raise ValueError(
                f"JORNADA_SEMANAL_POR_CANDEF con un par vacio en {texto!r}"
            )
        trozos = crudo.split(":")
        if len(trozos) != 2:
            raise ValueError(
                f"par mal formado {crudo!r} en JORNADA_SEMANAL_POR_CANDEF "
                f"({texto!r}): se esperaba 'candef:semanal'"
            )
        try:
            candef = float(trozos[0].strip())
            semanal = float(trozos[1].strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"par no numerico {crudo!r} en JORNADA_SEMANAL_POR_CANDEF "
                f"({texto!r})"
            ) from exc
        for etiqueta, valor in (("candef", candef), ("semanal", semanal)):
            if not (0 < valor <= _MAX_HORAS):
                raise ValueError(
                    f"{etiqueta}={valor} fuera de rango en el par {crudo!r} "
                    f"de JORNADA_SEMANAL_POR_CANDEF ({texto!r}): se espera "
                    f"un numero de horas en (0, {_MAX_HORAS}]"
                )
        if candef in mapa:
            raise ValueError(
                f"candef {candef} repetido en JORNADA_SEMANAL_POR_CANDEF "
                f"({texto!r}): no se sabria cual gana"
            )
        mapa[candef] = semanal
    return mapa


def jornada_semanal_de(
    candef_efectivo: float, *, mapa: Mapping[float, float]
) -> tuple[float, str]:
    """Horas ordinarias teoricas de la SEMANA y de donde salen.

    `('mapa')` si el candef efectivo esta en el mapa; si no, jornada
    PLANA `5 x c` con origen `'plana'`, que es el comportamiento anterior
    a F-015: quien no este en el mapa no empeora, solo deja de mejorar.
    El aviso de R10 lo emite el llamante mirando este `origen`.
    """
    c = float(candef_efectivo)
    for clave, semanal in mapa.items():
        if abs(float(clave) - c) <= _EPS:
            return float(semanal), "mapa"
    return 5.0 * c, "plana"


def es_ultimo_laborable(d: date, es_laborable: Callable[[date], bool]) -> bool:
    """`d` es L-V, laborable, y ningun dia POSTERIOR L-V de su semana lo es.

    Sabado y domingo no son nunca candidatos (R14), ni aunque el
    calendario los declare laborables. Se consultan como mucho los dias
    que quedan hasta el viernes: cuatro llamadas en el peor caso, todas
    ya cacheadas por (DNI x ano) desde F-003.
    """
    dia_semana = d.weekday()
    if dia_semana >= 5:
        return False
    if not es_laborable(d):
        return False
    for siguiente in range(dia_semana + 1, 5):
        if es_laborable(d + timedelta(days=siguiente - dia_semana)):
            return False
    return True


@dataclass(frozen=True)
class Excepcion:
    """Excepcion de jornada de UN trabajador (tabla `empleado_jornada`).

    O trae `semanal` (y entonces se aplica la regla del ultimo laborable
    con esa `S`), o trae `patron` con 7 valores L..D (y entonces manda el
    patron, sin regla del resto). `origen` dice quien la puso:
    `manual` hoy, `sigrid` o `sesame` el dia que se importen.
    """
    semanal: float | None = None
    patron: tuple[float, ...] | None = None
    origen: str = "manual"

    def valida(self) -> bool:
        """False si la fila esta mal cargada; entonces se IGNORA.

        La tabla se rellena a mano por SQL hasta F-016, asi que el
        resolutor no se fia: un patron incompleto o unas horas absurdas
        no pueden cambiar el reparto en silencio.
        """
        if self.patron is not None:
            if len(self.patron) != 7:
                return False
            return all(
                v is not None and 0.0 <= float(v) <= 24.0
                for v in self.patron
            )
        if self.semanal is None:
            return False
        return 0.0 < float(self.semanal) <= _MAX_HORAS


@dataclass(frozen=True)
class DetalleJornada:
    """Jornada de un dia con TODO lo que hace falta para explicarla.

    `ultimo_laborable` es True cuando a este dia se le ha aplicado el
    resto de la semana. Cuando `S = 5c` la regla no cambia nada y no se
    recorre la semana (es el caso normal, candef 8): el campo queda en
    False porque el resto NO se ha aplicado.
    """
    horas: float
    candef_efectivo: float
    semanal: float
    origen: str
    ultimo_laborable: bool


def detalle_jornada_dia(
    d: date,
    *,
    candef: float | str | None,
    minimo: float,
    por_defecto: float,
    mapa: Mapping[float, float],
    es_laborable: Callable[[date], bool],
    excepcion: Excepcion | None = None,
) -> DetalleJornada:
    """Horas ordinarias teoricas del dia `d` para ese trabajador.

    Orden de la regla (R13):
      1. `d` no laborable -> 0;
      2. `d` laborable pero no L-V -> `c` (solo sin calendario, D11);
      3. `d` es L-V laborable y NO es el ultimo de su semana -> `c`;
      4. `d` es el ultimo laborable -> `max(0, S - 4c)`.

    Un festivo entre semana cuenta como jornada a efectos del resto: el
    ultimo laborable recibe siempre `S - 4c`, haya festivos o no.
    """
    c = jornada_efectiva(candef, minimo=minimo, por_defecto=por_defecto)

    exc = excepcion if (excepcion is not None and excepcion.valida()) else None

    if exc is not None and exc.patron is not None:
        patron = tuple(float(v) for v in exc.patron)
        horas = patron[d.weekday()] if es_laborable(d) else 0.0
        return DetalleJornada(
            horas=horas, candef_efectivo=c, semanal=sum(patron),
            origen="excepcion", ultimo_laborable=False,
        )

    if exc is not None and exc.semanal is not None:
        semanal, origen = float(exc.semanal), "excepcion"
    else:
        semanal, origen = jornada_semanal_de(c, mapa=mapa)

    def _detalle(horas: float, ultimo: bool) -> DetalleJornada:
        return DetalleJornada(
            horas=horas, candef_efectivo=c, semanal=semanal, origen=origen,
            ultimo_laborable=ultimo,
        )

    if not es_laborable(d):
        return _detalle(0.0, False)
    if d.weekday() >= 5:
        return _detalle(c, False)

    resto = max(0.0, semanal - 4.0 * c)
    if abs(resto - c) <= _EPS:
        # La regla no cambia nada (es el caso `S = 5c`, o sea el candef 8
        # de toda la vida): no hace falta recorrer la semana ni preguntar
        # al calendario cuatro veces mas por cada dia de cada parte.
        return _detalle(c, False)
    if es_ultimo_laborable(d, es_laborable):
        return _detalle(resto, True)
    return _detalle(c, False)


def jornada_dia(
    d: date,
    *,
    candef: float | str | None,
    minimo: float,
    por_defecto: float,
    mapa: Mapping[float, float],
    es_laborable: Callable[[date], bool],
    excepcion: Excepcion | None = None,
) -> float:
    """Azucar de `detalle_jornada_dia(...).horas` (la firma que fijo F-012)."""
    return detalle_jornada_dia(
        d, candef=candef, minimo=minimo, por_defecto=por_defecto, mapa=mapa,
        es_laborable=es_laborable, excepcion=excepcion,
    ).horas
