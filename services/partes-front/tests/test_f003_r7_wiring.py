# tests/test_f003_r7_wiring.py
"""R7 · con Sesame SIN configurar, sv4 se comporta exactamente como antes.

La feature se mergea APAGADA (`sesame_enabled=false`) y se enciende
cuando sesame-api este desplegado. Estos tests son la garantia de que
apagada no cambia nada: ni una llamada de red, el respaldo `holidays` de
siempre y el log de wiring diciendo DESACTIVADO.
"""
from __future__ import annotations

import logging

import httpx
import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias


@pytest.fixture
def base(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def sin_red(base):
    """Cualquier peticion que SALGA de verdad hace fallar el test.

    Se corta en `HTTPTransport`, el transporte de red real: el
    `TestClient` habla por `ASGITransport` (en memoria) y no se ve
    afectado, asi que lo unico que puede saltar aqui es una llamada de
    produccion a Sesame.
    """
    def prohibido(*_a, **_kw):
        raise AssertionError("los tests no pueden tocar la red")

    base.setattr(httpx.HTTPTransport, "handle_request", prohibido)
    return base


def _app(settings: Settings, **kw):
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-03-02", "horas": 8.0,
                            "candef": 8.0}])
    return build_app(settings, repository=ParteReviewRepository(fabrica), **kw)


# ------------------------- la propiedad del settings -------------------- #

def test_f003_r7_sesame_enabled_exige_las_dos_variables(base) -> None:
    assert Settings(_env_file=None).sesame_enabled is False

    base.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    assert Settings(_env_file=None).sesame_enabled is False

    base.setenv("SESAME_API_KEY", "clave-de-prueba")
    assert Settings(_env_file=None).sesame_enabled is True


def test_f003_r7_valores_en_blanco_no_activan_sesame(base) -> None:
    base.setenv("SESAME_API_BASE_URL", "   ")
    base.setenv("SESAME_API_KEY", "clave-de-prueba")
    assert Settings(_env_file=None).sesame_enabled is False


def test_f003_r7_valores_por_defecto_del_bloque_sesame(base) -> None:
    s = Settings(_env_file=None)
    assert s.sesame_api_timeout_s == 10.0
    assert s.sesame_cache_ttl_s == 21600


# ------------------------------- el wiring ------------------------------ #

def test_f003_r7_sin_configurar_ni_toca_la_red(sin_red, caplog) -> None:
    with caplog.at_level(logging.INFO):
        cliente = TestClient(_app(Settings(_env_file=None)))
    # La vista con calendario es la que resolveria festivos.
    assert cliente.get("/trabajadores/emp-77").status_code == 200
    assert "[sesame][wiring] DESACTIVADO" in caplog.text


def test_f003_r7_sin_configurar_usa_el_respaldo_holidays(sin_red) -> None:
    """El 2026-01-01 es festivo nacional segun la libreria `holidays`.

    Se comprueba sobre el proveedor REAL que ha cableado `build_app`, no
    sobre un doble: es la unica forma de ver que el respaldo sigue
    enchufado con Sesame apagado.
    """
    from datetime import date

    app = _app(Settings(_env_file=None))
    proveedor = app.state.calendario_provider
    assert proveedor.activo is False
    dia = proveedor.dia(date(2026, 1, 1), "12345678Z")
    assert (dia.festivo, dia.fiable) == (True, True)
    assert proveedor.dia(date(2026, 1, 2), "12345678Z").festivo is False


def test_f003_r7_configurado_cablea_el_proveedor(base, caplog) -> None:
    base.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    base.setenv("SESAME_API_KEY", "clave-de-prueba")
    with caplog.at_level(logging.INFO):
        app = _app(Settings(_env_file=None))
    assert "[sesame][wiring] CABLEADO" in caplog.text
    assert app.state.calendario_provider.activo is True


def test_f003_r7_el_log_de_wiring_no_lleva_la_clave(base, caplog) -> None:
    base.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    base.setenv("SESAME_API_KEY", "clave-secretisima-de-prueba")
    with caplog.at_level(logging.INFO):
        _app(Settings(_env_file=None))
    assert "clave-secretisima-de-prueba" not in caplog.text
    # La longitud se comprueba EN LA LINEA DE WIRING, no en cualquier
    # linea del log: el cliente escribe su propio `key_len` al
    # instanciarse y taparia un fallo aqui.
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert "key_len=27" in wiring[0]
    assert "clave-secretisima-de-prueba" not in wiring[0]


def test_f003_r7_el_proveedor_se_puede_inyectar(sin_red) -> None:
    """Los tests de vistas necesitan meter su propio proveedor, como ya
    hacen con el repositorio y el cliente de sv5."""
    class ProveedorFake:
        activo = True

        def holiday_name_para(self, _dni):
            return lambda _d: None

        def fiable_para(self, _consultas):
            return True

    doble = ProveedorFake()
    app = _app(Settings(_env_file=None), calendario_provider=doble)
    assert app.state.calendario_provider is doble
