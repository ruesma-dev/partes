# tests/test_f040_casado.py
"""F-040 · R2-R5, R7, R8, R12: el casado del trabajador sin DNI (sv3).

  - R2: los candidatos por nombre se agrupan por CLAVE DE PERSONA (el DNI
    del recurso o, sin el, `emp:<conide>` / `res:<ide>`), con el umbral y
    el empate de siempre.
  - R3 (DA1): si gana una clave sin DNI, NO se casa: `nombre_sin_dni`,
    sin `ide` ni `reside`; la linea va a Conciliar.
  - R4: si gana una clave con DNI, se casa como hoy; un sin DNI que la
    empata la deja en `nombre_ambiguo`.
  - R5: vale sin DNI leido y con un DNI que Sigrid no conoce; un DNI con
    recursos persona o conocido sin ellos sigue cerrando la linea.
  - R7-R8, R12: el alias aprendido contra el recurso (seccion final).

Todo SINTETICO.
"""
from __future__ import annotations

import pytest

from application.services.casado_recurso import casar_trabajador
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import EmpleadoRow, RecursoRow

HOY = 20260915
UMBRAL = 0.55
EMPRESA = 28
DNI_A = "11111111H"      # ficha con DNI y su recurso
DNI_D = "44444444A"      # recurso por cif, dos recursos
DNI_X = "99999999R"      # conocido por Sigrid: recurso que no es persona
DNI_Y = "12121212K"      # dos recursos persona sin desempate
NADIE = "00000000T"      # Sigrid no lo conoce


def _ficha(ide, nombre, dni, reside, empresa=EMPRESA):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre, dni=dni,
                       reside=reside, empresa=empresa, fecbaj=0)


def _rec(ide, nombre, *, cif=None, conide=None, empresa=EMPRESA, fecbaj=0,
         cla=1):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=f"MO/{ide}", nombre=nombre,
                      cla=cla)


FICHAS = [
    _ficha(10, "ANA UNO", DNI_A, 910),
    _ficha(40, "LUIS SINDNI", None, 941),     # ficha sin DNI, dos recursos
    _ficha(50, "PEPE GEMELO", None, 950),
]
RECURSOS = [
    _rec(910, "ANA UNO", conide=10),
    _rec(940, "LUIS SINDNI", conide=40),
    _rec(941, "LUIS SINDNI", conide=40),
    _rec(950, "PEPE GEMELO", conide=50),
    _rec(960, "PEPE GEMELO"),                 # sin ficha ni DNI: otra persona
    _rec(970, "RITA SOLA"),                   # sin ficha ni DNI
    _rec(980, "ANA UNO"),                     # homonimo sin DNI de ANA UNO
    _rec(990, "DORA DOBLE", cif=DNI_D),
    _rec(991, "DORA DOBLE", cif=DNI_D),
    _rec(995, "GRUA", cif=DNI_X, cla=2),
    _rec(996, "YAGO Y", cif=DNI_Y),
    _rec(997, "YAGO Y", cif=DNI_Y),
    _rec(998, "RITA SOLA BIS", fecbaj=20200101),   # de baja: no compite
]
INDICE = IndicePersonas(FICHAS, RECURSOS)
PROPUESTA = EmpleadoMatch(method="nombre_sin_dni")


def _casar(dni=None, nombre=None, alias=None, empresa=EMPRESA,
           indice=INDICE) -> EmpleadoMatch:
    return casar_trabajador(
        dni_leido=dni, nombre_leido=nombre,
        alias=(lambda: alias), indice=indice,
        matcher=EmpleadoMatcher(min_score=UMBRAL), empresa=empresa,
        fecha=HOY)


def _clave(m: EmpleadoMatch):
    return (m.ide, m.codigo, m.nombre, m.dni, m.reside, m.score, m.method)


# ============================ R3 · propone ============================= #

def test_f040_r3_gana_un_recurso_sin_dni_ni_ficha_se_propone() -> None:
    assert _casar(nombre="Rita Sola") == PROPUESTA


def test_f040_r3_gana_una_ficha_sin_dni_se_propone() -> None:
    """Dos recursos de la misma ficha sin DNI: una persona (`emp:40`)."""
    assert _casar(nombre="Luis Sindni") == PROPUESTA


def test_f040_r3_la_propuesta_no_lleva_nada_casado() -> None:
    m = _casar(nombre="Rita Sola")
    assert _clave(m) == (None, None, None, None, None, 0.0, "nombre_sin_dni")


# ============================ R2 · por clave =========================== #

def test_f040_r2_dos_personas_sin_dni_con_el_mismo_nombre_ambiguo() -> None:
    """`emp:50` y `res:960` empatan: no se propone ninguna."""
    assert _casar(nombre="Pepe Gemelo").method == "nombre_ambiguo"


def test_f040_r2_por_debajo_del_umbral_none() -> None:
    assert _casar(nombre="Xiomara Zeta").method == "none"


def test_f040_r2_un_recurso_de_baja_no_compite() -> None:
    """998 (de baja) se parece mas a «Rita Sola Bis», pero no compite."""
    assert _casar(nombre="Rita Sola Bis") == PROPUESTA


# ============================ R4 · con DNI ============================= #

def test_f040_r4_con_dni_que_gana_casa_como_hoy() -> None:
    sin_homonimo = IndicePersonas(FICHAS, [r for r in RECURSOS
                                           if r.ide != 980])
    assert _clave(_casar(nombre="Ana Uno", indice=sin_homonimo)) == \
        (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "nombre")


def test_f040_r4_sin_dni_que_empata_deja_nombre_ambiguo() -> None:
    assert _casar(nombre="Ana Uno").method == "nombre_ambiguo"


def test_f040_r4_dni_con_varios_recursos_sigue_casando_por_dni() -> None:
    """`casar_por_dni` sin candidato unico: `nombre_ambiguo` como hoy."""
    assert _casar(nombre="Dora Doble").method == "nombre_ambiguo"


# ======================= R5 · DNI leido ================================ #

def test_f040_r5_dni_que_sigrid_no_conoce_sigue_al_nombre() -> None:
    assert _casar(dni=NADIE, nombre="Rita Sola") == PROPUESTA


def test_f040_r5_dni_conocido_sin_recurso_persona_cierra() -> None:
    assert _casar(dni=DNI_X, nombre="Rita Sola").method == "dni_sin_recurso"


def test_f040_r5_dni_ambiguo_cierra() -> None:
    assert _casar(dni=DNI_Y, nombre="Rita Sola").method == "dni_ambiguo"


def test_f040_r5_dni_con_recurso_casa_por_dni() -> None:
    assert _clave(_casar(dni=DNI_A, nombre="Rita Sola")) == \
        (10, "E10", "ANA UNO", DNI_A, 910, 1.0, "dni")


@pytest.mark.parametrize("dni", [None, "", "   "])
def test_f040_r5_sin_dni_leido_va_al_nombre(dni) -> None:
    assert _casar(dni=dni, nombre="Rita Sola") == PROPUESTA
