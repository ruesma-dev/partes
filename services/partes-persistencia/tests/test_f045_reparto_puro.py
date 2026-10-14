# tests/test_f045_reparto_puro.py
"""F-045 · R1-R6: el nucleo puro del reparto por mayor resto.

`repartir(total, participantes, paso)` reparte un total en cuotas multiplo
del paso, proporcionales al peso de cada participante, con suma EXACTA.
`elegir_paso` escoge la granularidad (0,5; 0,25; 0,01). Sin red ni BBDD:
el modulo es aritmetica pura y una rejilla fija de pesos y totales basta
para comprobar las propiedades.
"""
from __future__ import annotations

import ast
import random
import itertools
from pathlib import Path

import pytest

from application.services.reparto_ponderado import (
    PASOS,
    Participante,
    elegir_paso,
    repartir,
)

_MODULO = (Path(__file__).resolve().parents[1] / "application" / "services"
           / "reparto_ponderado.py")


def _p(clave, peso, llegada=None) -> Participante:
    return Participante(clave=clave, peso=peso,
                        llegada=llegada if llegada is not None else 0)


def _multiplo(x: float, paso: float) -> bool:
    return abs(x / paso - round(x / paso)) < 1e-9


# ------------------------------- R1 ------------------------------------ #

def test_f045_r1_mayor_resto_ejemplo_1() -> None:
    """J 8 entre 10 h y 4 h: 5,714 y 2,286 -> suelos 5,5 y 2; el medio
    paso que falta va al mayor resto (B)."""
    cuotas = repartir(8.0, [_p("A", 10.0, 1), _p("B", 4.0, 2)], 0.5)
    assert cuotas == {"A": 5.5, "B": 2.5}


def test_f045_r1_una_cuota_por_participante_y_suma_exacta() -> None:
    cuotas = repartir(8.0, [_p("A", 5.0, 1), _p("B", 4.0, 2)], 0.5)
    assert set(cuotas) == {"A", "B"}
    assert cuotas == {"A": 4.5, "B": 3.5}
    assert sum(cuotas.values()) == 8.0


def test_f045_r1_k_pasos_de_mas_a_los_k_de_mayor_resto() -> None:
    """Tres de 1 h repartiendo 2 h a medias horas: 0,667 cada uno, suelo
    0,5 (1,5 en total) y falta UN paso: solo uno recibe 1."""
    cuotas = repartir(2.0, [_p("A", 1.0, 1), _p("B", 1.0, 2),
                            _p("C", 1.0, 3)], 0.5)
    assert cuotas == {"A": 1.0, "B": 0.5, "C": 0.5}


def test_f045_r1_cuarto_de_hora() -> None:
    cuotas = repartir(8.0, [_p("A", 7.75, 1), _p("B", 2.0, 2)], 0.25)
    assert cuotas == {"A": 6.25, "B": 1.75}


def test_f045_r1_peso_cero_recibe_cero() -> None:
    cuotas = repartir(8.0, [_p("A", 8.0, 1), _p("B", 0.0, 2)], 0.5)
    assert cuotas == {"A": 8.0, "B": 0.0}


# ------------------------------- R2 ------------------------------------ #

def test_f045_r2_empate_de_resto_gana_el_mayor_peso() -> None:
    """Restos iguales (0,25 h cada uno de 0,5): A pesa mas, A se lleva el
    paso aunque llegara despues."""
    # 3 h entre 2,5 y 3,5 (Σ 6): 1,25 y 1,75 -> suelos 1 y 1,5, restos
    # 0,5 pasos los dos; falta un paso.
    cuotas = repartir(3.0, [_p("A", 3.5, 9), _p("B", 2.5, 1)], 0.5)
    assert cuotas == {"A": 2.0, "B": 1.0}


def test_f045_r2_empate_de_resto_y_peso_gana_el_que_llego_antes() -> None:
    cuotas = repartir(8.0, [_p("A", 6.0, 3), _p("B", 6.0, 1),
                            _p("C", 6.0, 2)], 0.5)
    assert cuotas == {"B": 3.0, "C": 2.5, "A": 2.5}


def test_f045_r2_el_mayor_resto_manda_sobre_el_peso() -> None:
    """B pesa menos pero su resto es mayor: el paso es suyo."""
    cuotas = repartir(8.0, [_p("A", 10.0, 1), _p("B", 4.0, 2)], 0.5)
    assert cuotas["B"] == 2.5


@pytest.mark.parametrize("orden", list(itertools.permutations(range(3))))
def test_f045_r2_no_depende_del_orden_de_entrada(orden) -> None:
    base = [_p("A", 6.0, 1), _p("B", 6.0, 2), _p("C", 6.0, 3)]
    cuotas = repartir(8.0, [base[i] for i in orden], 0.5)
    assert cuotas == {"A": 3.0, "B": 2.5, "C": 2.5}


# ------------------------------- R3 ------------------------------------ #

def test_f045_r3_pasos_declarados() -> None:
    assert PASOS == (0.5, 0.25, 0.01)


def test_f045_r3_medias_horas() -> None:
    assert elegir_paso(8.0, [10.0, 4.5]) == 0.5


def test_f045_r3_cuartos_si_algun_peso_es_de_cuarto() -> None:
    assert elegir_paso(8.0, [7.75, 2.0]) == 0.25


def test_f045_r3_cuartos_si_el_total_es_de_cuarto() -> None:
    assert elegir_paso(7.75, [4.0, 4.0]) == 0.25


def test_f045_r3_centesimas_si_no_hay_cuartos() -> None:
    assert elegir_paso(8.0, [7.1, 2.0]) == 0.01
    assert elegir_paso(8.4, [4.0]) == 0.01


def test_f045_r3_sin_pesos_manda_el_total() -> None:
    assert elegir_paso(8.0, []) == 0.5


def test_f045_r3_tolera_el_ruido_de_coma_flotante() -> None:
    assert elegir_paso(0.1 + 0.2 + 0.2, [2.5000000001]) == 0.5


# ------------------------------- R4 ------------------------------------ #

_PESOS = [
    (10.0, 4.0), (5.0, 4.0), (4.0, 3.0), (9.5, 0.5), (6.0, 6.0, 6.0),
    (1.0, 1.0, 1.0, 1.0), (7.5, 0.5, 2.0), (3.5, 2.5), (8.0,), (0.5, 0.5),
    (12.0, 0.5, 0.5, 3.0),
]
_TOTALES = [0.0, 0.5, 1.0, 2.5, 7.0, 8.0, 9.0, 10.0, 16.0]


@pytest.mark.parametrize("pesos", _PESOS)
@pytest.mark.parametrize("total", _TOTALES)
def test_f045_r4_propiedades_en_rejilla(pesos, total) -> None:
    """Suma exacta, multiplo del paso, sin signo cruzado y sin depender
    del orden de entrada, para cada combinacion de la rejilla."""
    parts = [_p(i, w, i) for i, w in enumerate(pesos)]
    paso = elegir_paso(total, pesos)
    cuotas = repartir(total, parts, paso)
    assert abs(sum(cuotas.values()) - total) < 1e-9
    assert all(_multiplo(c, paso) for c in cuotas.values())
    if total <= sum(pesos) + 1e-9:
        assert all(cuotas[i] <= w + 1e-9 for i, w in enumerate(pesos))
    if total >= sum(pesos) - 1e-9:
        assert all(cuotas[i] >= w - 1e-9 for i, w in enumerate(pesos))
    assert repartir(total, list(reversed(parts)), paso) == cuotas


# ------------------------------- R5 ------------------------------------ #

def test_f045_r5_total_cero_da_ceros() -> None:
    assert repartir(0.0, [_p("A", 4.0, 1), _p("B", 3.0, 2)], 0.5) == {
        "A": 0.0, "B": 0.0}


def test_f045_r5_sin_peso_positivo_no_reparte_nada() -> None:
    assert repartir(8.0, [_p("A", 0.0, 1), _p("B", -2.0, 2)], 0.5) == {
        "A": 0.0, "B": 0.0}


def test_f045_r5_sin_participantes_dict_vacio() -> None:
    assert repartir(8.0, [], 0.5) == {}


def test_f045_r5_peso_negativo_no_recibe_cuota() -> None:
    assert repartir(8.0, [_p("A", 4.0, 1), _p("B", -4.0, 2)], 0.5) == {
        "A": 8.0, "B": 0.0}


# ------------------------------- R6 ------------------------------------ #

def test_f045_r6_modulo_puro_sin_infraestructura_ni_red() -> None:
    arbol = ast.parse(_MODULO.read_text(encoding="utf-8"))
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")
    prohibidos = ("infrastructure", "sqlalchemy", "httpx", "requests",
                  "psycopg", "socket", "urllib", "domain.ports")
    assert not [m for m in importados
                if any(m == p or m.startswith(p + ".") for p in prohibidos)]


# ================= refuerzo tras la campana de mutacion ================= #

def test_f045_r5_un_peso_minimo_se_lleva_todo() -> None:
    """Una diezmilesima de hora de peso es peso: recibe el total entero."""
    assert repartir(0.5, [_p("A", 0.0001, 1)], 0.01) == {"A": 0.5}


def test_f045_r5_un_peso_por_debajo_de_la_resolucion_no_rompe() -> None:
    """Un peso positivo que redondea a 0 no reparte nada (ni divide por 0)."""
    assert repartir(8.0, [_p("A", 0.00001, 1)], 0.5) == {"A": 0.0}


def test_f045_r1_los_participantes_son_inmutables() -> None:
    import dataclasses

    p = _p("A", 1.0, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.peso = 2.0  # type: ignore[misc]
    assert hash(p) == hash(_p("A", 1.0, 1))


# ================== review pasada 1 (2026-10-14) ======================== #
# El desempate de R2 depende de comparar restos EXACTOS. Si la escala con
# la que se pasan los pesos a enteros no conserva sus proporciones (p. ej.
# 10 001, donde `round(1,5 x 10 001)` y `round(2,5 x 10 001)` redondean
# hacia lados distintos), un empate de restos deja de serlo y el paso cae
# del otro lado.

def test_f045_r2_empate_de_restos_con_pesos_de_media_hora() -> None:
    """2 h entre 1,5 y 2,5: suelos 0,5 y 1, restos iguales (0,5 paso); el
    paso que falta va al de mas peso (B), no al que llego antes."""
    assert repartir(2.0, [_p("A", 1.5, 1), _p("B", 2.5, 2)], 0.5) == {
        "A": 0.5, "B": 1.5}


def _referencia(total, participantes, paso):
    """Mayor resto con aritmetica EXACTA (fracciones de los decimales de
    cada peso): el modelo contra el que se mide `repartir`."""
    import math
    from fractions import Fraction

    cuotas = {p.clave: 0.0 for p in participantes}
    pesos = {p.clave: Fraction(str(p.peso)) for p in participantes
             if p.peso > 0}
    if not pesos:
        return cuotas
    objetivo = round(total / paso)
    suma = sum(pesos.values())
    ideal = {k: objetivo * w / suma for k, w in pesos.items()}
    suelos = {k: math.floor(v) for k, v in ideal.items()}
    faltan = objetivo - sum(suelos.values())
    orden = sorted((p for p in participantes if p.clave in pesos),
                   key=lambda p: (-(ideal[p.clave] - suelos[p.clave]),
                                  -pesos[p.clave], p.llegada))
    for p in orden[:faltan]:
        suelos[p.clave] += 1
    cuotas.update({k: round(u * paso, 6) for k, u in suelos.items()})
    return cuotas


def test_f045_r2_coincide_con_el_modelo_exacto_en_horas_de_parte() -> None:
    """3.000 repartos con horas de parte (medias, cuartos y centesimas; muchos
    empates a proposito) dan EXACTAMENTE lo mismo que el modelo con
    fracciones. Con pesos de hasta 4 decimales, `peso x 10 000` es entero
    salvo ruido de coma flotante muy por debajo de 0,5: el redondeo no
    llega nunca a un empate .5 y la escala conserva las proporciones."""
    azar = random.Random(20261014)
    rejillas = ([k / 2 for k in range(1, 25)], [k / 4 for k in range(1, 49)],
                [round(k / 100, 2) for k in range(1, 1201)])
    for _ in range(3000):
        rejilla = azar.choice(rejillas)
        n = azar.randint(1, 5)
        parts = [_p(i, azar.choice(rejilla[:12] if azar.random() < 0.5
                                   else rejilla), azar.randint(1, 9))
                 for i in range(n)]
        total = azar.choice([0.0, 2.0, 6.0, 7.75, 8.0, 8.4, 9.0, 12.5])
        paso = elegir_paso(total, [p.peso for p in parts])
        assert repartir(total, parts, paso) == _referencia(total, parts,
                                                           paso), (
            total, parts)
