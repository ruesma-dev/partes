# tests/test_f085_sv5_guarda.py
"""F-085 · sv5 no escribe horas con un código de incidencia (R19, R20).

Caso 0678 (18/11/2026): una línea de 8 h normales con el código CIA elegido
en el portal viajó como línea de horas y `_elegir` tomó el primer HL* del
recurso: Sigrid recibió HLOF con 8 h. Desde F-085, una línea que no es
incidencia y trae un código CI* (o CIZ), o un `hora_ide` que es un CI* del
recurso, se omite con `MOTIVO_CODIGO_INCIDENCIA` (D6): cubre las líneas
heredadas (D7) y cualquier otra vía.

Sin red: tipos de hora sintéticos en memoria (códigos y precios
inventados, sin nombres reales ni DNIs).
"""
from __future__ import annotations

import inspect

import pytest
from application.services import reglas_registro
from application.services.reglas_registro import (
    MOTIVO_CODIGO_INCIDENCIA,
    MOTIVO_SIN_HORAS,
    MOTIVO_SIN_RECURSO,
    MOTIVO_TIPO,
    ReglasRegistro,
)
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    es_codigo_ci,
)

FECHA = 20261118
HL, HE, CIA, CIV, CIZ, MENC = 1, 2, 3, 4, 5, 6


def _h(horide: int, cod: str, pre: float = 10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre)


HORAS = {
    601: [_h(HL, "HLOF", 12.0), _h(HE, "HEOF", 15.0), _h(CIA, "CIA", 0.0),
          _h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)],
    602: [_h(MENC, "MENC", 0.0), _h(CIA, "CIA", 0.0), _h(CIZ, "CIZ", 2.0)],
}


def _lin(rid=1, *, recurso=601, tipo="normal", horas=8.0, hora_ide=None,
         hora_codigo=None, **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, tipo_hora=tipo, horas=horas,
                        hora_ide=hora_ide, hora_codigo=hora_codigo,
                        nombre=f"Persona {rid}", **kw)


def _reglas(**kw) -> ReglasRegistro:
    return ReglasRegistro(HORAS, **kw)


def _resumen(a) -> tuple:
    return (a.accion, a.motivo, a.hora_ide, a.hora_codigo, a.can, a.pre,
            a.tot)


# ------------------------------ es_codigo_ci ----------------------------- #

@pytest.mark.parametrize("cod, esperado", [
    ("CIA", True), (" cia ", True), ("CIZ", True), ("CI", True),
    ("HLOF", False), ("HEOF", False), ("MENC", False), (None, False),
    ("", False), ("C", False)])
def test_f085_r19_es_codigo_ci(cod, esperado) -> None:
    assert es_codigo_ci(cod) is esperado


@pytest.mark.parametrize("cod", ["CIA", "ciz", "CIV", "HLOF", "HEOF",
                                 "MENC", "", "CI", "XCI"])
def test_f085_r19_hora_recurso_es_incidencia_igual(cod) -> None:
    assert _h(9, cod).es_incidencia is (cod or "").upper().startswith("CI")


# ---------------------------------- R19 ---------------------------------- #

def test_f085_r19_motivo_exacto() -> None:
    assert MOTIVO_CODIGO_INCIDENCIA == (
        "codigo de incidencia en una linea de horas: vuelve a elegir el "
        "codigo en el portal")
    assert MOTIVO_CODIGO_INCIDENCIA.isascii()


@pytest.mark.parametrize("linea", [
    _lin(hora_ide=CIA, hora_codigo="CIA"),          # caso 0678
    _lin(hora_ide=HL, hora_codigo="CIA"),           # el codigo manda
    _lin(hora_ide=None, hora_codigo=" cia "),
    _lin(hora_ide=CIZ, hora_codigo="CIZ"),
    _lin(hora_ide=CIA, hora_codigo=None),           # el ide del recurso
    _lin(hora_ide=CIV, hora_codigo="HLOF"),
    _lin(tipo="extra", horas=2.0, hora_ide=CIV, hora_codigo="CIV"),
    _lin(horas=0.0, hora_codigo="CIA"),             # antes que sin horas
    _lin(horas=None, hora_codigo="CIA"),
    _lin(recurso=None, hora_codigo="CIA"),          # antes que sin recurso
    _lin(tipo="raro", hora_codigo="CIA"),           # antes que tipo raro
])
def test_f085_r19_linea_de_horas_con_ci_se_omite(linea) -> None:
    a = _reglas().decidir(linea)
    assert (a.accion, a.motivo) == ("omitir", MOTIVO_CODIGO_INCIDENCIA)
    assert a.hora_ide is None and a.can is None


def test_f085_r19_nunca_escribe_hl_ni_he() -> None:
    for linea in (_lin(hora_ide=CIA, hora_codigo="CIA"),
                  _lin(tipo="extra", horas=2.0, hora_codigo="CIV")):
        a = _reglas().decidir(linea)
        assert a.accion != "escribir"


def test_f085_r19_despues_de_las_omisiones_previas() -> None:
    a = _reglas(omisiones={1: "el recurso no existe en Sigrid"}).decidir(
        _lin(hora_codigo="CIA"))
    assert a.motivo == "el recurso no existe en Sigrid"


def test_f085_r19_antes_que_los_mensuales() -> None:
    a = _reglas(mensuales_a_dedicacion=True).decidir(
        _lin(recurso=602, hora_codigo="CIA"))
    assert (a.accion, a.motivo) == ("omitir", MOTIVO_CODIGO_INCIDENCIA)


def test_f085_r19_ide_ci_de_otro_recurso_no_cuenta() -> None:
    """El `hora_ide` solo cuenta si es un CI* del recurso de la linea."""
    otras = {601: [_h(HL, "HLOF", 12.0), _h(HE, "HEOF", 15.0)]}
    a = ReglasRegistro(otras).decidir(_lin(hora_ide=CIA, hora_codigo=None))
    assert (a.accion, a.hora_codigo, a.can) == ("escribir", "HLOF", 8.0)


def test_f085_r19_la_incidencia_sigue_su_camino() -> None:
    linea = LineaEntrada(registro_id=1, fecha_int=FECHA, recurso_ide=601,
                         es_incidencia=True, incidencia_codigo="AT",
                         incidencia_rol="inicio", hora_ide=CIA,
                         hora_codigo="CIA", tipo_hora="AT")
    a = _reglas().decidir(linea)
    assert (a.accion, a.hora_codigo, a.can, a.tot) == (
        "escribir", "CIA", 0.0, 0.0)


# ---------------------------------- R20 ---------------------------------- #

#: (linea, decision de la base de la rama ae0fac7).
CASOS_R20 = [
    (_lin(hora_ide=HL, hora_codigo="HLOF"),
     ("escribir", None, HL, "HLOF", 8.0, 12.0, 96.0)),
    (_lin(hora_ide=None, hora_codigo=None),
     ("escribir", None, HL, "HLOF", 8.0, 12.0, 96.0)),
    (_lin(tipo="extra", horas=2.0, hora_ide=HE, hora_codigo="HEOF"),
     ("escribir", None, HE, "HEOF", 2.0, 15.0, 30.0)),
    (_lin(horas=0.0, hora_codigo="HLOF"),
     ("omitir", MOTIVO_SIN_HORAS, None, None, None, None, None)),
    (_lin(recurso=None, hora_codigo="HLOF"),
     ("omitir", MOTIVO_SIN_RECURSO, None, None, None, None, None)),
    (_lin(tipo="raro", hora_codigo="HLOF"),
     ("omitir", f"{MOTIVO_TIPO}: 'raro'", None, None, None, None, None)),
    (_lin(hora_ide=99, hora_codigo="HXXX"),
     ("escribir", None, HL, "HLOF", 8.0, 12.0, 96.0)),
]


@pytest.mark.parametrize("linea, esperado", CASOS_R20)
def test_f085_r20_lo_demas_como_hoy(linea, esperado) -> None:
    assert _resumen(_reglas().decidir(linea)) == esperado


def test_f085_r20_mensual_con_dedicacion_como_hoy() -> None:
    a = _reglas(mensuales_a_dedicacion=True).decidir(
        _lin(recurso=602, hora_codigo="MENC", hora_ide=MENC))
    assert (a.accion, a.codigo_mes) == ("dedicacion", "MENC")


def test_f085_r19_guarda_en_un_solo_sitio() -> None:
    fuente = inspect.getsource(reglas_registro.ReglasRegistro.decidir)
    assert fuente.count("MOTIVO_CODIGO_INCIDENCIA") == 1
