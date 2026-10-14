# tests/test_f046_wiring.py
"""F-046 · interruptor `REPARTO_REAJUSTE` y espera del candado (DA2, R10,
R18): ajustes y cableado de sv3. Sin red ni BBDD."""
from __future__ import annotations

import inspect

import pytest
from config.settings import Settings
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import construir_casado_sigrid
from tests.dobles import JornadasFake, RepositorioFake


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": "clave-de-test",
        "SIGRID_API_DATABASE": "bd",
    }.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("REPARTO_REAJUSTE", raising=False)
    monkeypatch.delenv("CANDADO_CONCILIAR_ESPERA_S", raising=False)
    return monkeypatch


def _conciliador(settings):
    return construir_casado_sigrid(
        settings, repository=RepositorioFake(), jornadas=JornadasFake(),
        mapa_semanal={8.0: 40.0})[3]


def test_f046_r10_interruptor_apagado_por_defecto(entorno):
    s = Settings(_env_file=None)
    assert s.reparto_reajuste is False
    assert _conciliador(s)._reajuste is False


def test_f046_r10_interruptor_encendido_llega_al_conciliador(entorno):
    entorno.setenv("REPARTO_REAJUSTE", "true")
    s = Settings(_env_file=None)
    assert s.reparto_reajuste is True
    assert _conciliador(s)._reajuste is True


def test_f046_r18_espera_del_candado(entorno):
    assert Settings(_env_file=None).candado_espera_s == 300.0
    entorno.setenv("CANDADO_CONCILIAR_ESPERA_S", "45")
    assert Settings(_env_file=None).candado_espera_s == 45.0


def test_f046_r18_build_app_pasa_la_espera_al_repositorio():
    fuente = inspect.getsource(modulo_app.build_app)
    assert ("SqlAlchemyParteRepository(\n        session_factory, "
            "candado_espera_s=settings.candado_espera_s)") in fuente.replace(
        "\r\n", "\n")
