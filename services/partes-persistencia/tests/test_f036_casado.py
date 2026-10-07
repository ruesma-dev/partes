# tests/test_f036_casado.py
"""F-036 · R4-R14: el casado del trabajador leido contra recursos persona.

  - `EmpleadoMatcher.match_nombre` (R10-R12): cada candidato puntua con el
    MAXIMO entre el nombre del recurso y el de su ficha; gana la PERSONA
    (DNI del recurso) de mayor puntuacion; otra persona que empata o la
    supera es `nombre_ambiguo`; sin llegar al umbral, `none`.
  - `casar_trabajador` (R4-R8, R13, R14): DNI -> alias -> nombre, y lo que
    se guarda en la linea segun el recurso elegido tenga ficha o no.

Todo SINTETICO.
"""
from __future__ import annotations

import pytest

from application.services.empleado_matcher import EmpleadoMatcher

UMBRAL = 0.55


def _nombre(nombre, candidatos, umbral=UMBRAL):
    return EmpleadoMatcher(min_score=umbral).match_nombre(
        nombre=nombre, candidatos=candidatos)


# ===================== match_nombre por persona (R10) =================== #

def test_f036_r10_nombre_puntua_el_maximo_de_recurso_y_ficha() -> None:
    """El nombre del recurso no se parece; el de la ficha es identico."""
    persona, score, metodo = _nombre("Ana Uno", [
        ("A", ("ZZZZ QQQQ", "ANA UNO")),
    ])
    assert (persona, score, metodo) == ("A", 1.0, "nombre")


def test_f036_r10_nombre_puntua_el_nombre_del_recurso_sin_ficha() -> None:
    assert _nombre("Ana Uno", [("A", ("ANA UNO", None))]) == \
        ("A", 1.0, "nombre")


def test_f036_r10_nombre_el_orden_de_los_nombres_no_importa() -> None:
    assert _nombre("Ana Uno", [("A", ("ANA UNO", "ZZZZ QQQQ"))]) == \
        ("A", 1.0, "nombre")


def test_f036_r10_nombre_el_mejor_entre_personas_gana() -> None:
    persona, score, metodo = _nombre("Ana Uno", [
        ("B", ("BEA DOS", None)), ("A", ("ANA UNO", None)),
    ])
    assert (persona, score, metodo) == ("A", 1.0, "nombre")


def test_f036_r10_nombre_la_puntuacion_se_redondea_a_4_decimales() -> None:
    persona, score, metodo = _nombre("Ana Uno Tres", [("A", ("ANA UNO", None))],
                                     umbral=0.1)
    assert persona == "A" and metodo == "nombre"
    assert 0 < score < 1 and score == round(score, 4)


def test_f036_r10_nombre_el_umbral_se_alcanza_con_la_puntuacion_justa() -> None:
    assert _nombre("Ana Uno", [("A", ("ANA UNO", None))], umbral=1.0) == \
        ("A", 1.0, "nombre")


# ================ match_nombre: ambiguedad por persona (R11) ============= #

def test_f036_r11_nombre_otra_persona_empata_nombre_ambiguo() -> None:
    assert _nombre("Pepe Igual", [
        ("A", ("PEPE IGUAL", None)), ("B", (None, "PEPE IGUAL")),
    ]) == (None, 0.0, "nombre_ambiguo")


def test_f036_r11_nombre_otra_persona_por_debajo_no_es_ambiguedad() -> None:
    assert _nombre("Pepe Igual", [
        ("A", ("PEPE IGUAL", None)), ("B", ("PEPE DISTINTO", None)),
    ]) == ("A", 1.0, "nombre")


def test_f036_r11_nombre_varios_recursos_de_la_misma_persona_no_son_ambiguedad(
) -> None:
    assert _nombre("Pepe Igual", [
        ("A", ("PEPE IGUAL", None)), ("A", ("PEPE IGUAL", "PEPE IGUAL")),
        ("A", ("OTRO NOMBRE", None)),
    ]) == ("A", 1.0, "nombre")


def test_f036_r11_nombre_la_persona_puntua_por_su_mejor_recurso() -> None:
    """A tiene un recurso flojo y otro identico; B uno intermedio: gana A
    (agrupar por persona con el maximo, no con el ultimo)."""
    assert _nombre("Pepe Igual", [
        ("A", ("PEPE IGUAL", None)), ("B", ("PEPE IGUALES", None)),
        ("A", ("ZZZZ QQQQ", None)),
    ], umbral=0.1)[0] == "A"


# =================== match_nombre: sin casar (R12) ====================== #

def test_f036_r12_nombre_por_debajo_del_umbral_none() -> None:
    assert _nombre("Xiomara Zeta", [("A", ("ANA UNO", "ANA UNO"))]) == \
        (None, 0.0, "none")


@pytest.mark.parametrize("nombre", [None, "", "   "])
def test_f036_r12_nombre_sin_nombre_leido_none(nombre) -> None:
    assert _nombre(nombre, [("A", ("ANA UNO", None))]) == (None, 0.0, "none")


def test_f036_r12_nombre_sin_candidatos_none() -> None:
    assert _nombre("Ana Uno", []) == (None, 0.0, "none")


def test_f036_r12_nombre_candidato_sin_nombres_no_puntua() -> None:
    assert _nombre("Ana Uno", [("A", (None, None))], umbral=0.0) == \
        (None, 0.0, "none")
