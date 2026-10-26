# tests/test_f062_ciz_mismo_dia.py
"""F-062 · El inicio de una incidencia escribe CI* y CIZ el mismo dia (sv5).

  - Puro: `synckey_ciz_de`, `registro_de_synckey` con el sufijo `:ciz`
    (R20), `es_ciz_del_recurso` y `decidir_mismo_dia` (R11).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services import racha_ciz
from application.services.racha_ciz import (
    MOTIVO_POSTERIOR,
    MOTIVO_YA_EXISTE,
    decidir_mismo_dia,
    es_ciz_del_recurso,
    registro_de_synckey,
)
from domain.models.registro_models import LineaSigrid
from infrastructure.sigrid.sigrid_write_client import (
    SUFIJO_CIZ,
    synckey_ciz_de,
    synckey_de,
)

REC = 501
D = 20261004
H_CIV, H_CIZ = 30, 40


def _ls(ide, fec, *, reside=REC, hora="CIZ", can=0.0, tex=None,
        sk=None) -> LineaSigrid:
    return LineaSigrid(
        ide=ide, reside=reside, fecha_int=fec,
        horide=H_CIZ if hora == "CIZ" else H_CIV, hora_codigo=hora, can=can,
        tot=0.0, synckey=sk or f"partes:{ide}", nuestra=True, hmoide=901,
        tex=tex, pos=64)


# =============================== Puro =============================== #

def test_f062_r20_puro_synckey_ciz_de() -> None:
    assert SUFIJO_CIZ == ":ciz"
    assert synckey_ciz_de(7) == "partes:7:ciz"
    assert synckey_ciz_de("12") == "partes:12:ciz"
    assert synckey_ciz_de(7) == synckey_de(7) + SUFIJO_CIZ


@pytest.mark.parametrize("sk,esperado", [
    ("partes:7:ciz", None), ("partes:7", 7), (" partes:12 ", 12),
    ("partes:7:CIZ", None), ("partes:x", None), (None, None), ("", None),
    ("otro:7", None)])
def test_f062_r20_puro_registro_de_synckey_con_sufijo(sk, esperado) -> None:
    assert registro_de_synckey(sk) == esperado


def test_f062_r20_puro_registro_de_synckey_sufijo_explicito() -> None:
    """El sufijo se trata a proposito, no por el `ValueError` de `int`."""
    import inspect
    fuente = inspect.getsource(racha_ciz.registro_de_synckey)
    assert "SUFIJO_CIZ" in fuente


@pytest.mark.parametrize("cambio,esperado", [
    ({}, True), ({"reside": REC + 1}, False), ({"hora": "CIV"}, False),
    ({"can": 1.0}, False), ({"can": None}, True)])
def test_f062_r11_puro_es_ciz_del_recurso(cambio, esperado) -> None:
    assert es_ciz_del_recurso(_ls(1, D, **cambio), REC, None) is esperado


def test_f062_r11_puro_es_ciz_del_recurso_minusculas_y_blancos() -> None:
    ls = _ls(1, D)
    ls.hora_codigo = " ciz "
    assert es_ciz_del_recurso(ls, REC, None) is True


@pytest.mark.parametrize("tex,esperado", [
    (None, False), ("", False), ("x PRUEBA-IA x", True)])
def test_f062_r11_puro_es_ciz_del_recurso_en_pruebas(tex, esperado) -> None:
    assert es_ciz_del_recurso(_ls(1, D, tex=tex), REC,
                              "PRUEBA-IA") is esperado


def test_f062_r11_puro_sin_nada_se_escribe() -> None:
    assert decidir_mismo_dia(D, REC, [], None, marca_pruebas=None) is None


def test_f062_r11_puro_propia_ya_existe() -> None:
    propia = _ls(9, D, sk=synckey_ciz_de(4))
    assert decidir_mismo_dia(D, REC, [], propia,
                             marca_pruebas=None) == MOTIVO_YA_EXISTE == (
        "ya_existe")


def test_f062_r11_puro_ya_existe_manda_sobre_posterior() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1)], _ls(9, D),
                             marca_pruebas=None) == "ya_existe"


def test_f062_r11_puro_ciz_posterior() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 2)], None,
                             marca_pruebas=None) == MOTIVO_POSTERIOR == (
        "posterior")


@pytest.mark.parametrize("linea", [
    _ls(5, D), _ls(5, D - 1), _ls(5, D + 1, reside=REC + 1),
    _ls(5, D + 1, hora="CIV"), _ls(5, D + 1, can=2.0)])
def test_f062_r11_puro_lo_que_no_es_ciz_posterior_no_cuenta(linea) -> None:
    assert decidir_mismo_dia(D, REC, [linea], None,
                             marca_pruebas=None) is None


def test_f062_r11_puro_en_pruebas_sin_marca_no_cuenta() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1)], None,
                             marca_pruebas="PRUEBA-IA") is None
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1, tex="PRUEBA-IA")], None,
                             marca_pruebas="PRUEBA-IA") == "posterior"
