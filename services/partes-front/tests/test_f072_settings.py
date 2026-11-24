# tests/test_f072_settings.py
"""F-072 · Configuración de las obras agrupadas en sv4 (R1, R2, DA11).

sv4 no usa los alias (design §5-§6): no los lee.
Sin valores de negocio en el código: vacío = apagado. Con VAR encendido,
`VAR_PARTIDA_DESDE` es un entero >= 0 o el servicio no arranca. Sin red.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from application.services.obras_agrupadas import Ajustes, Marcas
from config.settings import Settings

VARIABLES = ("POSTVENTA_OBRA_COD", "POSTVENTA_ALIAS", "VAR_OBRA_COD",
             "VAR_ALIAS", "VAR_PARTIDA_DESDE")
BASE_ENTORNO = {"PG_PASSWORD": "irrelevante", "PG_ADMIN_PASSWORD": "irrelevante"}


@pytest.fixture(autouse=True)
def _limpio(monkeypatch, tmp_path):
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in BASE_ENTORNO.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.chdir(tmp_path)          # que no se cuele un .env
    return monkeypatch


def _settings(monkeypatch, **entorno) -> Settings:
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None)


def test_f072_r1_sin_variables_todo_apagado(monkeypatch):
    aj = _settings(monkeypatch).obras_agrupadas
    assert aj == Ajustes(postventa_cod=None, var_cod=None, var_desde=None,
                         marcas=Marcas(postventa=(), var=()))
    assert aj.activo is False
    assert aj.tipo_de("POSTV2") is None and aj.tipo_de("VAR") is None


def test_f072_r1_lee_los_codigos_sin_alias_y_el_umbral(monkeypatch):
    aj = _settings(monkeypatch, POSTVENTA_OBRA_COD="POSTV2",
                   POSTVENTA_ALIAS="POSTVENTA,POSTV,POST", VAR_OBRA_COD="VAR",
                   VAR_ALIAS="V", VAR_PARTIDA_DESDE="29").obras_agrupadas
    assert (aj.postventa_cod, aj.var_cod, aj.var_desde) == ("POSTV2", "VAR", 29)
    assert aj.marcas == Marcas(postventa=("POSTV2",), var=("VAR",))
    assert aj.activo is True
    assert aj.tipo_de("postv2") == "postventa" and aj.tipo_de("VAR") == "var"


def test_f072_r1_postventa_sola_no_pide_umbral(monkeypatch):
    aj = _settings(monkeypatch, POSTVENTA_OBRA_COD="POSTV2").obras_agrupadas
    assert aj.var_cod is None and aj.var_desde is None and aj.activo


@pytest.mark.parametrize("valor", [None, "", "  ", "abc", "-1", "2.5", "+3",
                                   "²"])
def test_f072_r2_var_sin_umbral_valido_no_arranca(monkeypatch, valor):
    entorno = {"VAR_OBRA_COD": "VAR"}
    if valor is not None:
        entorno["VAR_PARTIDA_DESDE"] = valor
    with pytest.raises(ValidationError, match="VAR_PARTIDA_DESDE"):
        _settings(monkeypatch, **entorno)


@pytest.mark.parametrize("valor, desde", [("0", 0), (" 29 ", 29), ("100", 100)])
def test_f072_r2_umbral_valido(monkeypatch, valor, desde):
    st = _settings(monkeypatch, VAR_OBRA_COD="VAR", VAR_PARTIDA_DESDE=valor)
    assert st.obras_agrupadas.var_desde == desde


def test_f072_r2_con_var_apagado_el_umbral_no_cuenta(monkeypatch):
    aj = _settings(monkeypatch, VAR_PARTIDA_DESDE="abc").obras_agrupadas
    assert aj.var_desde is None and aj.activo is False
