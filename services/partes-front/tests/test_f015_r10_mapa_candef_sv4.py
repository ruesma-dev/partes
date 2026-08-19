# tests/test_f015_r10_mapa_candef_sv4.py
"""R10 en sv4 · el mapa candef -> jornada semanal y su fail-fast.

El portal decide con este mapa que dias marca como «jornada incompleta».
Dos cosas tienen que cumplirse:

  - el mapa es ESPEJO del de sv3 (mismo nombre de variable y mismo valor
    por defecto): si discrepan, el portal avisa de jornadas incompletas
    que sv3 no genera, y el usuario deja de fiarse de los avisos;
  - una cadena mal escrita tira el ARRANQUE de la app, no una vista suelta
    a mitad de mes.

Sin BBDD (SQLite en memoria) y con `Settings(_env_file=None)` para no leer
el `.env` de quien ejecute la suite.
"""
from __future__ import annotations

import logging

import pytest
from application.services.jornada_resolver import (
    jornada_semanal_de,
    parsear_mapa_semanal,
)
from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite

MAPA = {8.0: 40.0, 9.0: 42.0}


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _monta(entorno):
    return build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(FabricaSesionSqlite()),
    )


# ------------------------------ el parseo ------------------------------- #

def test_f015_r10_sv4_el_mapa_por_defecto(entorno) -> None:
    assert Settings(_env_file=None).jornada_semanal_por_candef == "8:40,9:42"
    assert parsear_mapa_semanal("8:40,9:42") == MAPA


def test_f015_r10_sv4_el_ttl_por_defecto(entorno) -> None:
    assert Settings(_env_file=None).jornada_cache_ttl_s == 600


@pytest.mark.parametrize("candef, semanal, origen", [
    (8.0, 40.0, "mapa"),
    (9.0, 42.0, "mapa"),
    (10.0, 50.0, "plana"),
])
def test_f015_r10_sv4_jornada_semanal_del_mapa(candef, semanal, origen) -> None:
    assert jornada_semanal_de(candef, mapa=MAPA) == (semanal, origen)


# ------------------------- fail-fast del arranque ----------------------- #

@pytest.mark.parametrize("texto", ["8:40,9", "x:40", "8:40,8:41", "", "8:0"])
def test_f015_r10_sv4_un_mapa_mal_formado_no_levanta_la_app(
        entorno, texto) -> None:
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", texto)
    with pytest.raises(ValueError):
        _monta(entorno)


def test_f015_r10_sv4_el_error_nombra_la_variable(entorno) -> None:
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", "8:40,9")
    with pytest.raises(ValueError) as exc:
        _monta(entorno)
    assert "JORNADA_SEMANAL_POR_CANDEF" in str(exc.value)


def test_f015_r10_sv4_con_el_mapa_bueno_la_app_levanta(entorno) -> None:
    app = _monta(entorno)
    assert app.state.mapa_semanal == MAPA


def test_f015_r10_sv4_el_mapa_se_puede_ampliar_por_entorno(entorno) -> None:
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", "8:40,9:42,10:48")
    assert _monta(entorno).state.mapa_semanal == {
        8.0: 40.0, 9.0: 42.0, 10.0: 48.0}


def test_f015_r10_sv4_el_wiring_deja_el_mapa_en_el_log(
        entorno, caplog) -> None:
    with caplog.at_level(logging.INFO):
        _monta(entorno)
    assert "[jornada][wiring]" in caplog.text
    assert "8:40" in caplog.text


def test_f015_r10_sv4_el_proveedor_de_excepciones_queda_cableado(
        entorno) -> None:
    """Sin inyeccion se construye sobre el repositorio; la tabla vacia."""
    app = _monta(entorno)
    assert app.state.jornada_provider is not None
    from datetime import date
    assert app.state.jornada_provider.excepcion_para(
        "12345678Z", date(2026, 3, 20)) is None
