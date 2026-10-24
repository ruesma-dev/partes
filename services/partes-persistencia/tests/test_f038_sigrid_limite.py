# tests/test_f038_sigrid_limite.py
"""F-038 en sv3: límite de filas de las lecturas de Sigrid y timeouts.

- R2: sin `SIGRID_API_MAX_ROWS`, 500.000 (DA1 = B) en settings y en el
  constructor, que coinciden (antes 10.000).
- R3 y R14: fuera de rango, el servicio no arranca.
- R4: las lecturas paginadas siguen pidiendo `PAGINA_FILAS + 1` (5.001),
  sea cual sea el `max_rows` del cliente.
- R5: `construir_casado_sigrid` y `medir_casado_recursos.main` pasan
  `settings.sigrid_api_max_rows`.
- R6: el cliente registra en INFO su `max_rows` y su `timeout_s`, sin la
  clave.
- R9: `truncated` sigue siendo error en todas las lecturas.

Sin red: sigrid-api simulado con `httpx.MockTransport`.
"""
from __future__ import annotations

import json
import logging

import httpx
import medir_casado_recursos as medir
import pytest
from config.settings import Settings
from infrastructure.sigrid import sigrid_api_client as modulo
from infrastructure.sigrid.sigrid_api_client import (
    PAGINA_FILAS,
    SigridApiClient,
)
from interface_adapters.api import app as modulo_app
from pydantic import ValidationError

CLAVE = "clave-de-test-f038"


class SigridFalso:
    """sigrid-api en memoria: responde sin filas y apunta cada petición."""

    def __init__(self, *, truncated: bool = False) -> None:
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={
            "ok": True, "columns": ["ide"], "rows": [], "row_count": 0,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kwargs) -> SigridApiClient:
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridApiClient(base_url="http://sigrid.invalid",
                           function_key=CLAVE, database="bd", **kwargs)


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    for clave in ("SIGRID_API_MAX_ROWS", "SIGRID_API_TIMEOUT_S",
                  "SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY",
                  "SIGRID_API_DATABASE"):
        monkeypatch.delenv(clave, raising=False)
    return monkeypatch


#: Todas las lecturas del cliente de sv3 (paginadas).
LECTURAS = [
    ("fetch_empleados", ()), ("fetch_obras", ()), ("fetch_tipos_hora", ()),
    ("fetch_empresas", ()), ("fetch_recursos", ()), ("fetch_reshor", ()),
    ("fetch_partidas_obra", (77,)), ("fetch_hmo_obra", (77,)),
]


# --------------------------------- R2 ----------------------------------- #

def test_f038_r2_defecto_500000_en_settings_y_constructor(
        entorno, monkeypatch) -> None:
    # Por atributo y no por import: sin la constante, el test falla solo.
    assert modulo.MAX_ROWS_DEFECTO == 500_000
    assert Settings(_env_file=None).sigrid_api_max_rows == \
        modulo.MAX_ROWS_DEFECTO
    falso = SigridFalso()
    cliente = _cliente(monkeypatch, falso)
    cliente._post_sql_read(sql="SELECT 1", parameters=[], label="r2")
    assert falso.peticiones[0]["max_rows"] == 500_000


# ----------------------------- R3 y R14 --------------------------------- #

@pytest.mark.parametrize("valor", ["0", "-1", "500001", "abc", "1.5"])
def test_f038_r3_max_rows_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("valor, esperado", [("1", 1), ("500000", 500_000)])
def test_f038_r3_max_rows_en_los_bordes_vale(entorno, valor,
                                             esperado) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    assert Settings(_env_file=None).sigrid_api_max_rows == esperado


@pytest.mark.parametrize("valor", ["0", "-5", "200.5", "abc"])
def test_f038_r14_timeout_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_TIMEOUT_S", valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f038_r14_timeout_200_vale_y_el_defecto_sigue_en_30(entorno) -> None:
    assert Settings(_env_file=None).sigrid_api_timeout_s == 30.0
    entorno.setenv("SIGRID_API_TIMEOUT_S", "200")
    assert Settings(_env_file=None).sigrid_api_timeout_s == 200.0


# Mutación F-038: el límite inferior es `gt=0` (exclusivo); `gt=1` dejaría
# fuera 0.5 y 1, timeouts válidos que ningún test probaba.
@pytest.mark.parametrize("valor, esperado", [("0.5", 0.5), ("1", 1.0)])
def test_f038_r14_timeout_por_debajo_de_1_vale(entorno, valor,
                                               esperado) -> None:
    entorno.setenv("SIGRID_API_TIMEOUT_S", valor)
    assert Settings(_env_file=None).sigrid_api_timeout_s == esperado


# --------------------------------- R4 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", LECTURAS)
def test_f038_r4_paginadas_piden_pagina_mas_una(monkeypatch, metodo,
                                                args) -> None:
    falso = SigridFalso()
    getattr(_cliente(monkeypatch, falso, max_rows=7), metodo)(*args)
    assert falso.peticiones
    assert {p["max_rows"] for p in falso.peticiones} == {PAGINA_FILAS + 1}
    assert PAGINA_FILAS + 1 == 5001


# --------------------------------- R5 ----------------------------------- #

class _Parada(Exception):
    """Corta el cableado en cuanto se ha construido el cliente."""


@pytest.fixture
def espia(entorno):
    capturados: list[dict] = []

    class Espia:
        def __init__(self, **kwargs) -> None:
            capturados.append(kwargs)
            raise _Parada

    for clave, valor in {
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": CLAVE, "SIGRID_API_DATABASE": "bd",
        "SIGRID_API_MAX_ROWS": "12345",
    }.items():
        entorno.setenv(clave, valor)
    entorno.setattr(modulo_app, "SigridApiClient", Espia)
    entorno.setattr(medir, "SigridApiClient", Espia)
    return capturados


def test_f038_r5_app_cablea_max_rows(espia) -> None:
    with pytest.raises(_Parada):
        modulo_app.construir_casado_sigrid(
            Settings(_env_file=None), repository=None, jornadas=None,
            mapa_semanal={})
    assert [k["max_rows"] for k in espia] == [12345]


def test_f038_r5_medir_casado_cablea_max_rows(espia, monkeypatch) -> None:
    monkeypatch.setattr(medir, "Settings",
                        lambda: Settings(_env_file=None))
    with pytest.raises(_Parada):
        medir.main()
    assert [k["max_rows"] for k in espia] == [12345]


# --------------------------------- R6 ----------------------------------- #

def test_f038_r6_log_de_instanciacion_sin_la_clave(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=modulo.__name__):
        SigridApiClient(base_url="http://sigrid.invalid", function_key=CLAVE,
                        database="bd", timeout_s=45, max_rows=4321)
    mensajes = [r.getMessage() for r in caplog.records
                if r.levelno == logging.INFO]
    assert any("max_rows=4321" in m and "timeout_s=45" in m
               for m in mensajes), mensajes
    assert not any(CLAVE in m for m in mensajes)


# --------------------------------- R9 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", LECTURAS)
def test_f038_r9_truncated_es_error_en_todas(monkeypatch, metodo,
                                             args) -> None:
    falso = SigridFalso(truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)


def test_f038_r9_truncated_es_error_sin_paginar(monkeypatch) -> None:
    falso = SigridFalso(truncated=True)
    with pytest.raises(RuntimeError, match=r"truncada \[suelta\]"):
        _cliente(monkeypatch, falso)._post_sql_read(
            sql="SELECT 1", parameters=[], label="suelta")
