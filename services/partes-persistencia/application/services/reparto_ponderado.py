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
#: acumulados.
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
