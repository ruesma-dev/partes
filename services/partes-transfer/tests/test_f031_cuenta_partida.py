# tests/test_f031_cuenta_partida.py
"""F-031 · D (pura): la partida como respaldo de la cuenta (design §7.2).

Manda la ficha de horas del recurso (F-021, R20). Solo si el recurso no da
subcuenta, la de la partida si es de COSTE (`CI*`/`CD*`; nunca `CP` ni
`INGR`, R21); si tampoco, sin cuenta (R22). Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.cuenta_analitica import (
    SUBCUENTAS_COSTE_PARTIDA,
    OrigenSubcuenta,
    origen_subcuenta,
    subcuenta_de_partida,
)
from domain.models.registro_models import HoraRecurso, PartidaCuenta

HL, HE = 1, 2


def _h(horide, cod, caa=None, defecto=False) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=10.0,
                       caa_cod=caa, defecto=defecto)


CON_CUENTA = [_h(HL, "HL01", "00000.CIMO09", True), _h(HE, "HE01")]
SIN_CUENTA = [_h(HL, "HL01", None, True), _h(HE, "HE01")]
MAQUINISTA = PartidaCuenta(300, "01.02", "0100.CIMO12")


# ======================== subcuenta_de_partida ======================== #

def test_f031_subcuentas_de_coste_son_ci_y_cd() -> None:
    assert SUBCUENTAS_COSTE_PARTIDA == ("CI", "CD")


@pytest.mark.parametrize("caa_cod, esperado", [
    ("0100.CIMO12", "CIMO12"),
    ("0100.CDQA01", "CDQA01"),
    ("0100. CICO01 ", "CICO01"),       # la misma `subcuenta()` de F-021
    ("0100.cimo12", "cimo12"),         # el prefijo se mira en mayusculas
    ("0100.cd01", "cd01"),
    ("0100.CI", "CI"),
])
def test_f031_r21_subcuenta_de_partida_de_coste(caa_cod, esperado) -> None:
    assert subcuenta_de_partida(caa_cod) == esperado


@pytest.mark.parametrize("caa_cod", [
    "0100.CP00", "0100.INGR", "0100.C", "0100.CX01", "0100.ICIMO",
    "CIMO12", "0100.", "", None,
])
def test_f031_r22_subcuenta_de_partida_que_no_vale(caa_cod) -> None:
    assert subcuenta_de_partida(caa_cod) is None


# ========================== origen_subcuenta ========================== #

def test_f031_r20_el_recurso_manda_aunque_la_partida_tenga_otra() -> None:
    assert origen_subcuenta(CON_CUENTA, HL, MAQUINISTA) == \
        OrigenSubcuenta("CIMO09", "recurso", None)


def test_f031_r20_el_recurso_por_su_tipo_por_defecto_tambien_manda() -> None:
    assert origen_subcuenta(CON_CUENTA, HE, MAQUINISTA) == \
        OrigenSubcuenta("CIMO09", "recurso", None)


def test_f031_r20_recurso_con_cuenta_y_sin_partida() -> None:
    assert origen_subcuenta(CON_CUENTA, HL, None) == \
        OrigenSubcuenta("CIMO09", "recurso", None)


def test_f031_r21_recurso_sin_cuenta_usa_la_partida_de_coste() -> None:
    o = origen_subcuenta(SIN_CUENTA, HL, MAQUINISTA)
    assert o == OrigenSubcuenta(
        "CIMO12", "partida",
        "el recurso no tiene cuenta para esa hora: se usa la de la partida "
        "01.02 (.CIMO12)")


def test_f031_r21_partida_cd_y_recurso_sin_horas() -> None:
    o = origen_subcuenta([], HL, PartidaCuenta(301, "02.01", "0100.CDQA01"))
    assert (o.sub, o.origen) == ("CDQA01", "partida")
    assert "02.01" in o.nota and ".CDQA01" in o.nota


@pytest.mark.parametrize("partida", [
    None,
    PartidaCuenta(302, "09.01", "0100.CP00"),
    PartidaCuenta(303, "10.01", "0100.INGR"),
    PartidaCuenta(304, "11.01", None),
])
def test_f031_r22_sin_cuenta_de_recurso_ni_de_partida(partida) -> None:
    assert origen_subcuenta(SIN_CUENTA, HL, partida) == \
        OrigenSubcuenta(None, None, None)
