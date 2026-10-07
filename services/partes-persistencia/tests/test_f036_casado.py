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

from application.services.casado_recurso import casar_trabajador
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import EmpleadoRow, RecursoRow

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


# ======================= casar_trabajador (R4-R14) ======================= #

HOY = 20260915
DNI_A = "11111111H"      # ficha en la 1, un recurso enlazado
DNI_B = "22222222J"      # ficha en la 1, dos recursos: desempata el reside
DNI_C = "33333333P"      # ficha en la 1 y recurso SIN enlazar en la 28 (R7)
DNI_E = "55555555K"      # sin ficha: recurso por cif en la 28
DNI_G = "66666666Q"      # solo un recurso que no es de persona (cla 2)
DNI_H = "77777777B"      # dos recursos por cif en la 1, sin desempate
DNI_I = "88888888Y"      # solo un recurso de baja


def _ficha(ide, nombre, dni, reside, empresa=1):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre, dni=dni,
                       reside=reside, empresa=empresa, fecbaj=0)


def _rec(ide, nombre, *, cif=None, conide=None, empresa=1, fecbaj=0, cla=1):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=f"MO/{ide}", nombre=nombre,
                      cla=cla)


FICHAS = [
    _ficha(10, "ANA UNO", DNI_A, 910),
    _ficha(20, "BEA DOS", DNI_B, 921),
    _ficha(30, "CARLOS TRES", DNI_C, 930),
]
RECURSOS = [
    _rec(910, "ZZZZ QQQQ", conide=10),
    _rec(920, "BEA DOS", conide=20),
    _rec(921, "BEA DOS", conide=20),
    _rec(930, "CARLOS TRES", conide=30),
    _rec(950, "TRES CARLOS", cif=DNI_C, empresa=28),
    _rec(960, "EVA SINFICHA", cif=DNI_E, empresa=28),
    _rec(970, "GRUA", cif=DNI_G, cla=2),
    _rec(980, "HUGO IGUAL", cif=DNI_H),
    _rec(981, "HUGO IGUAL", cif=DNI_H),
    _rec(990, "IRENE BAJA", cif=DNI_I, fecbaj=20200101),
    _rec(995, "SIN DNI NADIE", cif=None),
]
INDICE = IndicePersonas(FICHAS, RECURSOS)


class _Alias:
    """El alias perezoso: cuenta cuantas veces se consulta."""

    def __init__(self, valor=None) -> None:
        self.valor = valor
        self.llamadas = 0

    def __call__(self):
        self.llamadas += 1
        return self.valor


def _casar(dni=None, nombre=None, alias=None, empresa=1, fecha=HOY,
           indice=INDICE):
    return casar_trabajador(
        dni_leido=dni, nombre_leido=nombre, alias=alias or _Alias(),
        indice=indice, matcher=EmpleadoMatcher(min_score=UMBRAL),
        empresa=empresa, fecha=fecha)


def _clave(m: EmpleadoMatch):
    return (m.ide, m.codigo, m.nombre, m.dni, m.reside, m.score, m.method)


SIN_CASAR = (None, None, None, None, None, 0.0)


# ------------------------------ por DNI -------------------------------- #

def test_f036_r4_r13_dni_con_ficha_enlazada() -> None:
    assert _clave(_casar(DNI_A)) == \
        (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "dni")


def test_f036_r4_dni_leido_se_normaliza_y_se_guarda_canonico() -> None:
    assert _casar(" 11111111-h ").dni == DNI_A


def test_f036_r4_dni_varios_recursos_desempata_el_reside() -> None:
    assert _clave(_casar(DNI_B))[4:] == (921, 1.0, "dni")


def test_f036_r7_r14_ficha_en_a_y_recurso_sin_enlazar_en_b() -> None:
    assert _clave(_casar(DNI_C, empresa=28)) == \
        (None, "MO/950", "TRES CARLOS", DNI_C, 950, 1.0, "recurso_dni")
    assert _clave(_casar(DNI_C, empresa=1))[4:] == (930, 1.0, "dni")


def test_f036_r14_dni_sin_ficha_recurso_dni() -> None:
    assert _clave(_casar(DNI_E, empresa=28)) == \
        (None, "MO/960", "EVA SINFICHA", DNI_E, 960, 1.0, "recurso_dni")


@pytest.mark.parametrize("dni, empresa, metodo", [
    (DNI_H, 1, "dni_ambiguo"),
    (DNI_I, 1, "dni_solo_baja"),
    (DNI_E, 1, "dni_otra_empresa"),
])
def test_f036_r5_dni_sin_candidato_cierra_sin_alias_ni_nombre(
        dni, empresa, metodo) -> None:
    alias = _Alias({"ide": 10, "dni": DNI_A})
    m = _casar(dni, nombre="ANA UNO", alias=alias, empresa=empresa)
    assert _clave(m) == (*SIN_CASAR, metodo)
    assert alias.llamadas == 0


def test_f036_r4_dni_que_decide_no_consulta_el_alias() -> None:
    alias = _Alias({"ide": 20, "dni": DNI_B})
    assert _casar(DNI_A, alias=alias).ide == 10
    assert alias.llamadas == 0


@pytest.mark.parametrize("dni", [None, "", "99999999R"])
def test_f036_r6_sin_dni_o_dni_desconocido_sigue_al_alias_y_al_nombre(
        dni) -> None:
    alias = _Alias()
    m = _casar(dni, nombre="Ana Uno", alias=alias)
    assert _clave(m) == (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "nombre")
    assert alias.llamadas == 1


@pytest.mark.parametrize("dni, fichas", [
    (DNI_G, FICHAS),                    # solo un recurso que no es persona
    ("12121212R", FICHAS + [_ficha(70, "SIN RECURSO", "12121212R", None)]),
    (" 12121212-r ", FICHAS + [_ficha(70, "SIN RECURSO", "12121212R", None)]),
])
def test_f036_r6_persona_conocida_sin_recurso_persona_queda_sin_casar(
        dni, fichas) -> None:
    """Humano, 2026-10-07 (opcion A): DNI de una persona que Sigrid conoce
    (ficha o recurso) sin ningun recurso persona: sin casar, sin alias ni
    nombre (que podrian casar a OTRA persona), y a la cola de Conciliar."""
    alias = _Alias({"ide": 10, "dni": DNI_A})
    m = _casar(dni, nombre="Ana Uno", alias=alias,
               indice=IndicePersonas(fichas, RECURSOS))
    assert _clave(m) == (*SIN_CASAR, "dni_sin_recurso")
    assert alias.llamadas == 0


def test_f036_r6_el_metodo_cabe_en_la_columna() -> None:
    """`parte_registros.empleado_match_method` es String(24)."""
    assert len("dni_sin_recurso") <= 24


def test_f036_r6_sin_alias_cableado_va_al_nombre() -> None:
    m = casar_trabajador(
        dni_leido=None, nombre_leido="Ana Uno", alias=None, indice=INDICE,
        matcher=EmpleadoMatcher(min_score=UMBRAL), empresa=1, fecha=HOY)
    assert m.method == "nombre"


# ------------------------------- alias --------------------------------- #

def test_f036_r8_alias_con_dni() -> None:
    m = _casar(nombre="ANITA", alias=_Alias({"ide": 99, "dni": DNI_A}))
    assert _clave(m) == (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "alias")


@pytest.mark.parametrize("dni", [None, ""])
def test_f036_r8_alias_sin_dni_toma_el_de_su_ficha(dni) -> None:
    m = _casar(nombre="BEITA", alias=_Alias({"ide": 20, "dni": dni}))
    assert _clave(m)[4:] == (921, 1.0, "alias")


def test_f036_r8_alias_se_resuelve_en_la_empresa_del_parte() -> None:
    m = _casar(nombre="CARLITOS", alias=_Alias({"ide": 30, "dni": DNI_C}),
               empresa=28)
    assert _clave(m) == \
        (None, "MO/950", "TRES CARLOS", DNI_C, 950, 1.0, "recurso_nombre")


def test_f036_r8_r14_alias_a_un_recurso_sin_ficha_es_recurso_nombre() -> None:
    m = _casar(nombre="EVITA", alias=_Alias({"ide": None, "dni": DNI_E}),
               empresa=28)
    assert _clave(m) == \
        (None, "MO/960", "EVA SINFICHA", DNI_E, 960, 1.0, "recurso_nombre")


@pytest.mark.parametrize("alias", [
    {"ide": 99, "dni": None},           # sin DNI y su ficha no existe
    {"ide": None, "dni": ""},
    {"ide": 99, "dni": "99999999R"},    # DNI sin recursos persona
    {"ide": 99, "dni": DNI_G},          # solo un recurso que no es persona
])
def test_f036_r8_alias_no_valido(alias) -> None:
    m = _casar(nombre="Ana Uno", alias=_Alias(alias))
    assert _clave(m) == (*SIN_CASAR, "alias_no_valido")


def test_f036_r8_alias_sin_dni_y_ficha_sin_dni_no_valido() -> None:
    indice = IndicePersonas([_ficha(40, "SIN DNI", None, None)], RECURSOS)
    m = _casar(nombre="X", alias=_Alias({"ide": 40, "dni": None}),
               indice=indice)
    assert m.method == "alias_no_valido"


@pytest.mark.parametrize("dni, empresa, metodo", [
    (DNI_H, 1, "dni_ambiguo"), (DNI_I, 1, "dni_solo_baja"),
    (DNI_E, 1, "dni_otra_empresa"),
])
def test_f036_r8_alias_con_dni_sin_candidato(dni, empresa, metodo) -> None:
    m = _casar(nombre="Ana Uno", alias=_Alias({"ide": None, "dni": dni}),
               empresa=empresa)
    assert _clave(m) == (*SIN_CASAR, metodo)


# ------------------------------- nombre -------------------------------- #

def test_f036_r10_r13_nombre_casa_por_el_nombre_de_la_ficha() -> None:
    """El recurso 910 se llama distinto; la ficha 10 es ANA UNO."""
    assert _clave(_casar(nombre="Ana Uno")) == \
        (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "nombre")


def test_f036_r10_r14_nombre_de_un_recurso_sin_ficha() -> None:
    assert _clave(_casar(nombre="Eva Sinficha", empresa=28)) == \
        (None, "MO/960", "EVA SINFICHA", DNI_E, 960, 1.0, "recurso_nombre")


def test_f036_r10_nombre_solo_compite_la_empresa_del_parte() -> None:
    assert _casar(nombre="Eva Sinficha", empresa=1).method == "none"


def test_f036_r11_nombre_varios_recursos_de_una_persona_desempata_el_reside(
) -> None:
    assert _clave(_casar(nombre="Bea Dos"))[4:] == (921, 1.0, "nombre")


def test_f036_r11_nombre_persona_sin_recurso_unico_es_nombre_ambiguo() -> None:
    assert _clave(_casar(nombre="Hugo Igual")) == \
        (*SIN_CASAR, "nombre_ambiguo")


def test_f036_r11_nombre_dos_personas_empatan() -> None:
    gemelo = _rec(985, "ANA UNO", cif="12121212R")
    indice = IndicePersonas(FICHAS, RECURSOS + [gemelo])
    assert _casar(nombre="Ana Uno", indice=indice).method == "nombre_ambiguo"


def test_f036_r12_nombre_que_no_llega_al_umbral() -> None:
    assert _clave(_casar(nombre="Xiomara Zeta")) == (*SIN_CASAR, "none")


def test_f036_r3_nombre_de_un_recurso_sin_dni_no_casa() -> None:
    assert _casar(nombre="Sin Dni Nadie").method == "none"


def test_f036_r2_nombre_de_un_recurso_que_no_es_persona_no_casa() -> None:
    assert _casar(nombre="Grua").method == "none"


def test_f036_r10_nombre_puntuacion_no_entera_se_guarda() -> None:
    m = _casar(nombre="Ana Uno Tres")
    assert m.method == "nombre" and m.ide == 10 and 0.55 <= m.score < 1.0
