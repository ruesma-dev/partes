# tests/test_f053_pisado.py
"""F-053 · Regla pura del pisado (R5-R8, R11, R13), `application/services/
pisado.py`.

  - `tiene_horas`: `can` no nulo y distinto de 0 (el criterio de F-034 R4).
  - `es_incidencia`: codigo de hora que empieza por `CI` (semantica 4).
  - `choques`: mismo recurso, dia y codigo, synckey fuera de la peticion y,
    salvo que la linea a escribir sea incidencia, CON HORAS (R5, DA5).
  - `origen_linea`: `partes`, `ajena` o `manual` para el INFO de R13.
  - motivos de R6 y R7: prefijo, `ide`, codigo del parte, que hacer, sin
    tildes, sin nombres ni DNIs y <= 255.

Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services import parte_abierto
from application.services.pisado import (
    LIMITE_MOTIVO,
    MOTIVO_INCIDENCIA_EN_SIGRID,
    MOTIVO_LINEA_ENLAZADA,
    PREFIJO_PARTES,
    choques,
    es_incidencia,
    motivo_incidencia_en_sigrid,
    motivo_linea_enlazada,
    nombrar_lineas,
    origen_linea,
    tiene_horas,
)
from domain.models.registro_models import AccionLinea, LineaSigrid
from infrastructure.sigrid.sigrid_write_client import PREFIJO_SYNCKEY

RES, DIA, HN, HE, CIV = 77, 20261015, 11, 12, 30


def _ls(ide: int, *, can=8.0, reside=RES, fec=DIA, horide=HN,
        synckey=None, enlazada=False) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=reside, fecha_int=fec, horide=horide,
                       hora_codigo=None, can=can, tot=None, synckey=synckey,
                       enlazada=enlazada)


def _a(*, horide=HN, codigo="HN", reside=RES, fec=DIA) -> AccionLinea:
    return AccionLinea(registro_id=501, accion="escribir", ano=2026, mes=10,
                       fecha_int=fec, recurso_ide=reside, hora_ide=horide,
                       hora_codigo=codigo, can=8.0)


# ---------------------------- tiene_horas (R5) ---------------------------- #

@pytest.mark.parametrize("can,esperado", [
    (None, False), (0, False), (0.0, False), (-0.0, False), (-2, True),
    (8, True), (0.25, True), (-0.001, True)])
def test_f053_r5_tiene_horas(can, esperado) -> None:
    assert tiene_horas(_ls(1, can=can)) is esperado


# --------------------------- es_incidencia (R6) --------------------------- #

@pytest.mark.parametrize("cod,esperado", [
    ("CIV", True), ("CIZ", True), ("ci", True), (" CIE", True),
    ("HN", False), ("HE1", False), ("C", False), ("", False), (None, False),
    ("XCI", False)])
def test_f053_r6_es_incidencia(cod, esperado) -> None:
    assert es_incidencia(cod) is esperado


# ------------------------------ choques (R5) ------------------------------ #

def test_f053_r5_choque_con_horas_del_mismo_recurso_dia_y_codigo() -> None:
    ajena = _ls(9001)
    assert choques([ajena], _a(), set()) == [ajena]


def test_f053_r5_linea_a_cero_no_choca() -> None:
    """Una linea a 0 (pisada antes o anulada a mano) no es conflicto."""
    assert choques([_ls(9001, can=0), _ls(9002, can=None)], _a(), set()) == []


def test_f053_r5_horas_negativas_si_chocan() -> None:
    neg = _ls(9001, can=-2)
    assert choques([neg], _a(), set()) == [neg]


def test_f053_r5_incidencia_a_cero_si_choca_con_incidencia() -> None:
    """Para una incidencia (siempre sin horas) cuenta la linea, no `can`."""
    inc = _ls(9001, can=0, horide=CIV)
    assert choques([inc], _a(horide=CIV, codigo="CIV"), set()) == [inc]


def test_f053_r5_las_mias_no_chocan() -> None:
    mia = _ls(9001, synckey="partes:501")
    otra = _ls(9002, synckey="partes:480")
    assert choques([mia, otra], _a(), {"partes:501"}) == [otra]


@pytest.mark.parametrize("cambio", [
    {"reside": RES + 1}, {"fec": DIA + 1}, {"horide": HE}],
    ids=["otro-recurso", "otro-dia", "otro-codigo"])
def test_f053_r5_otro_recurso_dia_o_codigo_no_choca(cambio) -> None:
    assert choques([_ls(9001, **cambio)], _a(), set()) == []


def test_f053_r5_horide_nulo_choca_con_accion_sin_codigo() -> None:
    sin = _ls(9001, horide=None)
    assert choques([sin], _a(horide=None, codigo=None), set()) == [sin]
    assert choques([sin], _a(), set()) == []


def test_f053_r5_conserva_el_orden() -> None:
    a, b, c = _ls(3), _ls(1, can=0), _ls(2)
    assert choques([a, b, c], _a(), set()) == [a, c]


# ---------------------------- origen_linea (R13) ---------------------------- #

def test_f053_r13_prefijo_es_el_del_cliente() -> None:
    assert PREFIJO_PARTES == PREFIJO_SYNCKEY == "partes:"


@pytest.mark.parametrize("sk,esperado", [
    ("partes:480", "partes"), ("porcentajes:12", "ajena"),
    ("partes", "ajena"), ("xpartes:1", "ajena"), (None, "manual"),
    ("", "manual"), ("   ", "manual")])
def test_f053_r13_origen_linea(sk, esperado) -> None:
    assert origen_linea(sk) == esperado


# ------------------------------ motivos (R11) ------------------------------ #

def test_f053_r11_prefijos_y_limite() -> None:
    assert MOTIVO_INCIDENCIA_EN_SIGRID == "incidencia_en_sigrid"
    assert MOTIVO_LINEA_ENLAZADA == "linea_enlazada"
    assert LIMITE_MOTIVO == parte_abierto.LIMITE_MOTIVO == 255


def test_f053_r11_nombrar_lineas() -> None:
    assert nombrar_lineas([9001]) == ("linea 9001", False)
    assert nombrar_lineas([9002, 9001, 9002]) == ("lineas 9001, 9002", True)
    assert nombrar_lineas([]) == ("linea ?", False)


def test_f053_r6_motivo_incidencia_en_sigrid_texto_exacto() -> None:
    assert motivo_incidencia_en_sigrid([9001], "PT26/00314") == (
        "incidencia_en_sigrid: la incidencia ya consta en Sigrid ese dia "
        "(linea 9001 del parte PT26/00314); no se duplica")
    assert motivo_incidencia_en_sigrid([9002, 9001], None) == (
        "incidencia_en_sigrid: la incidencia ya consta en Sigrid ese dia "
        "(lineas 9001, 9002 del parte ?); no se duplica")


def test_f053_r7_motivo_linea_enlazada_texto_exacto() -> None:
    assert motivo_linea_enlazada([9001], "PT26/00314") == (
        "linea_enlazada: la linea 9001 del parte PT26/00314 tiene ese dia "
        "las mismas horas y esta enlazada (albaran, factura, dedicacion o "
        "nomina); no se pone a 0. Corrigela en Sigrid")
    assert motivo_linea_enlazada([9002, 9001], "PT26/00314") == (
        "linea_enlazada: las lineas 9001, 9002 del parte PT26/00314 tienen "
        "ese dia las mismas horas y estan enlazadas (albaran, factura, "
        "dedicacion o nomina); no se ponen a 0. Corrigelas en Sigrid")
    assert "del parte ?" in motivo_linea_enlazada([9001], None)


@pytest.mark.parametrize("cod", ["PT26/" + "9" * 400, "x" * 300],
                         ids=["codigo-400", "texto-300"])
def test_f053_r11_motivos_caben_en_255(cod) -> None:
    for m in (motivo_incidencia_en_sigrid([9001], cod),
              motivo_linea_enlazada([9001], cod)):
        assert len(m) == LIMITE_MOTIVO
    assert motivo_incidencia_en_sigrid([1], cod).startswith(
        "incidencia_en_sigrid: ")
    assert motivo_linea_enlazada([1], cod).startswith("linea_enlazada: ")


def test_f053_r11_motivos_sin_tildes_ni_datos_personales() -> None:
    for m in (motivo_incidencia_en_sigrid([9001], "PT26/00314"),
              motivo_linea_enlazada([9001, 9002], "PT26/00314")):
        assert len(m) < LIMITE_MOTIVO
        assert m.isascii()
