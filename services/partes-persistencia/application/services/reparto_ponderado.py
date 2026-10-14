# application/services/reparto_ponderado.py
"""F-045: reparto PONDERADO de la jornada del dia entre obras y lineas (sv3).

Hasta F-045 el exceso de jornada caia entero en el ultimo parte en llegar
(el `registro_id` mayor): con 10 h en una obra y 4 h en otra salia 8 + 2 y
0 + 4. Ahora la jornada se reparte en proporcion a las horas de cada obra
y, dentro de ella, de cada linea, por MAYOR RESTO y a medias horas.

Nucleo puro: ni base, ni red, ni nada de `infrastructure/` (R6). Lo usa
`RecursoConciliador._reclasificar_extras_jornada`, que es quien sabe que
lineas estan congeladas y cual es la jornada del dia.
"""
from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass

#: Granularidades del reparto, de la preferida a la de respaldo (R3, DA5).
PASOS: tuple[float, ...] = (0.5, 0.25, 0.01)

#: Resolucion con la que se comparan los pesos (diezmilesimas de hora): el
#: reparto trabaja en ENTEROS para que la suma salga exacta, sin floats
#: acumulados. TIENE que ser una potencia de 10 con al menos tantos ceros
#: como decimales traen las horas (2 en los partes): asi `peso x escala` es
#: entero salvo ruido de coma flotante y `round` nunca cae en un .5, de
#: modo que la escala conserva las proporciones y los empates de resto
#: (R2) siguen siendo empates. Con otra escala (p. ej. 10 001), 1,5 y 2,5
#: redondean hacia lados distintos y el desempate cambia (review F-045).
_RESOLUCION = 10_000

#: Tolerancia para decidir si un valor es multiplo de un paso.
_TOLERANCIA = 1e-6


def _es_multiplo(valor: float, paso: float) -> bool:
    return abs(valor / paso - round(valor / paso)) <= _TOLERANCIA


def elegir_paso(total: float, pesos: Iterable[float]) -> float:
    """R3: 0,5 si el total y todos los pesos son multiplos de 0,5; si no,
    0,25 si lo son de 0,25; si no, 0,01."""
    valores = [total, *pesos]
    for paso in PASOS[:-1]:
        if all(_es_multiplo(v, paso) for v in valores):
            return paso
    return PASOS[-1]


@dataclass(frozen=True)
class Participante:
    """Quien recibe una cuota: una obra o una linea.

    `llegada` desempata en ultimo lugar (R2): la obra, su `registro_id`
    minimo; la linea, su `registro_id`. Gana el que llego antes.
    """

    clave: Hashable
    peso: float
    llegada: int


def _horas(unidades: int, paso: float) -> float:
    return round(unidades * paso, 6)


def repartir(
    total: float, participantes: Sequence[Participante], paso: float
) -> dict[Hashable, float]:
    """R1-R5: una cuota por participante, multiplo de `paso`, con suma
    EXACTA `total` (en pasos enteros).

    Cada uno recibe el suelo de `total x peso / Σpesos` al paso y los `k`
    de mayor resto un paso mas (`k` = lo que falta). Desempate (R2): mayor
    resto, mayor peso, el que llego antes; nunca el orden de entrada. Un
    participante de peso <= 0 recibe 0 y, si nadie tiene peso > 0, no se
    reparte nada (R5).
    """
    cuotas: dict[Hashable, float] = {p.clave: 0.0 for p in participantes}
    positivos = [p for p in participantes if p.peso > 0]
    pesos = {p.clave: round(p.peso * _RESOLUCION) for p in positivos}
    suma = sum(pesos.values())
    if suma <= 0:
        return cuotas
    objetivo = round(total / paso)
    suelos = {k: objetivo * w // suma for k, w in pesos.items()}
    restos = {k: objetivo * w % suma for k, w in pesos.items()}
    faltan = objetivo - sum(suelos.values())
    orden = sorted(
        positivos,
        key=lambda p: (-restos[p.clave], -pesos[p.clave], p.llegada,
                       repr(p.clave)),
    )
    for p in orden[:faltan]:
        suelos[p.clave] += 1
    for clave, unidades in suelos.items():
        cuotas[clave] = _horas(unidades, paso)
    return cuotas


# ------------------------------ el dia --------------------------------- #

#: Tipos de linea que participan en el reparto (las incidencias, no).
ORDINARIA = "ordinaria"
EXTRA = "extra"

#: Tolerancia en horas para comparar cuotas con horas.
_EPS = 1e-9


@dataclass(frozen=True)
class LineaDia:
    """Una linea ordinaria o extra del grupo (recurso, fecha).

    `fija`: congelada (F-004, o por su pareja de F-037); el reparto no la
    toca. `extra_auto` y `base_id` solo los usa `diferencias_ideal` (R25):
    una extra automatica y el `registro_id` de la base de su pareja.
    """

    registro_id: int
    obra_ide: Hashable | None
    tipo: str
    horas: float
    horas_orig: float | None = None
    fija: bool = False
    extra_auto: bool = False
    base_id: int | None = None


@dataclass(frozen=True)
class Ajuste:
    """Split de una ordinaria: `horas_norm` de jornada y `extra_horas`."""

    registro_id: int
    horas_norm: float
    extra_horas: float
    horas_orig: float


@dataclass(frozen=True)
class ResultadoDia:
    """`cuadra` falso: el dia no se puede cuadrar sin tocar lo fijo (R23)."""

    cuadra: bool
    paso: float
    ajustes: tuple[Ajuste, ...]
    n_obras: int
    n_lineas: int


def _es_fija(linea: LineaDia) -> bool:
    """Congelada, u ordinaria sin horas que repartir (<= 0)."""
    return linea.fija or (linea.tipo == ORDINARIA and linea.horas <= 0)


def repartir_dia(lineas: Sequence[LineaDia], jornada: float) -> ResultadoDia:
    """R7-R19, R22, R23: reparte la jornada del dia entre obras y lineas.

    Las fijas no cambian y sus ordinarias cuentan: se reparte `J'` = la
    jornada menos esas ordinarias. Primero entre las obras ajustables por
    su peso (ordinarias y extras explicitas no fijas) y, dentro de cada
    una, entre sus ordinarias ajustables por sus horas. Cada ordinaria
    cuya cuota no sea su horas da un `Ajuste` (la extra puede salir
    negativa, DA6). Con `J' < 0`, o `J' != 0` sin nada ajustable, el dia
    no cuadra y no hay ajustes (R23).
    """
    peso_obra: dict[Hashable | None, float] = {}
    llegada_obra: dict[Hashable | None, int] = {}
    for ln in lineas:
        llegada_obra[ln.obra_ide] = min(
            llegada_obra.get(ln.obra_ide, ln.registro_id), ln.registro_id)
        if not _es_fija(ln):
            peso_obra[ln.obra_ide] = peso_obra.get(ln.obra_ide, 0.0) + ln.horas
    por_obra: dict[Hashable | None, list[LineaDia]] = {}
    for ln in sorted(lineas, key=lambda x: x.registro_id):
        if (ln.tipo == ORDINARIA and not _es_fija(ln)
                and peso_obra[ln.obra_ide] > 0):
            por_obra.setdefault(ln.obra_ide, []).append(ln)
    ajustables = {ln.registro_id for ls in por_obra.values() for ln in ls}
    residuo = jornada - sum(
        ln.horas for ln in lineas
        if ln.tipo == ORDINARIA and ln.registro_id not in ajustables)
    n_lineas = len(ajustables)
    paso = elegir_paso(
        residuo,
        [peso_obra[o] for o in por_obra]
        + [ln.horas for ls in por_obra.values() for ln in ls],
    )
    if residuo < -_EPS or (abs(residuo) > _EPS and not por_obra):
        return ResultadoDia(False, paso, (), len(por_obra), n_lineas)
    cuotas_obra = repartir(
        residuo,
        [Participante(o, peso_obra[o], llegada_obra[o]) for o in por_obra],
        paso,
    )
    ajustes: list[Ajuste] = []
    for obra, ls in por_obra.items():
        cuotas = repartir(
            cuotas_obra[obra],
            [Participante(ln.registro_id, ln.horas, ln.registro_id)
             for ln in ls],
            paso,
        )
        for ln in ls:
            cuota = cuotas[ln.registro_id]
            if abs(cuota - ln.horas) > _EPS:
                ajustes.append(Ajuste(
                    registro_id=ln.registro_id,
                    horas_norm=cuota,
                    extra_horas=round(ln.horas - cuota, 2),
                    horas_orig=ln.horas,
                ))
    ajustes.sort(key=lambda a: a.registro_id)
    return ResultadoDia(True, paso, tuple(ajustes), len(por_obra), n_lineas)


def _trabajado(linea: LineaDia) -> float:
    """Lo trabajado: la base de una pareja ya partida guarda en
    `horas_orig` sus horas de antes del split."""
    if linea.tipo == ORDINARIA and linea.horas_orig is not None:
        return linea.horas_orig
    return linea.horas


def diferencias_ideal(
    lineas: Sequence[LineaDia], jornada: float
) -> tuple[tuple[int, float, float], ...]:
    """R25: `(registro_id, antes, despues)` de las lineas FIJAS que
    cambiaria el reparto ideal del dia. Solo mide; no aplica nada.

    El ideal trata todo el grupo como ajustable: la base de una pareja
    pesa lo trabajado y su extra automatica no pesa por separado (la
    extra ideal de la pareja es lo trabajado menos la cuota; una segunda
    extra de la misma base iria a 0). Una extra automatica sin su base en
    el grupo pesa como una explicita. Las extras explicitas nunca cambian.
    Si el ideal tampoco cuadra, no hay nada que comparar.
    """
    ordinarias = {ln.registro_id: ln for ln in lineas if ln.tipo == ORDINARIA}
    extras_de: dict[int, list[LineaDia]] = {}
    for ln in sorted(lineas, key=lambda x: x.registro_id):
        if ln.extra_auto and ln.base_id in ordinarias:
            extras_de.setdefault(ln.base_id, []).append(ln)
    emparejadas = {e.registro_id for es in extras_de.values() for e in es}
    ideal = [
        LineaDia(registro_id=ln.registro_id, obra_ide=ln.obra_ide,
                 tipo=ln.tipo, horas=_trabajado(ln))
        for ln in lineas if ln.registro_id not in emparejadas
    ]
    resultado = repartir_dia(ideal, jornada)
    if not resultado.cuadra:
        return ()
    cuota = {a.registro_id: a.horas_norm for a in resultado.ajustes}
    diferencias: list[tuple[int, float, float]] = []
    for base in ordinarias.values():
        trabajado = _trabajado(base)
        despues = cuota.get(base.registro_id, trabajado)
        candidatas = [(base, despues)]
        for i, extra in enumerate(extras_de.get(base.registro_id, [])):
            candidatas.append(
                (extra, round(trabajado - despues, 2) if i == 0 else 0.0))
        for ln, despues_ln in candidatas:
            if ln.fija and abs(despues_ln - ln.horas) > _EPS:
                diferencias.append((ln.registro_id, ln.horas, despues_ln))
    return tuple(sorted(diferencias))
