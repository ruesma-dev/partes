# tests/test_f038_sigrid_limite.py
"""F-038 en sv4: límite de filas de las lecturas de Sigrid y timeouts.

- R1: las lecturas sin paginar (`fetch_dnis_sin_extra`,
  `fetch_hora_extra_recurso`) mandan el `max_rows` del cliente.
- R2: sin `SIGRID_API_MAX_ROWS`, 500.000 (DA1 = B) en settings y en el
  constructor, que coinciden (antes 10.000 fijo).
- R3 y R14: fuera de rango, el servicio no arranca.
- R4: las paginadas siguen pidiendo `PAGINA_FILAS + 1` (5.001).
- R5: `build_app` pasa `settings.sigrid_api_max_rows` al cliente.
- R6: el cliente registra en INFO su `max_rows` y su `timeout_s`, sin la
  clave.
- R9: `truncated` sigue siendo error en las lecturas sin paginar.

Sin red: sigrid-api simulado con `httpx.MockTransport`.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from config.settings import Settings
from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import (
    PAGINA_FILAS,
    SigridLookupClient,
)
from interface_adapters.web import app as modulo_app
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
            "ok": True, "columns": ["dni", "max_he"], "rows": [],
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kwargs) -> SigridLookupClient:
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridLookupClient(base_url="http://sigrid.invalid",
                              function_key=CLAVE, database="bd", **kwargs)


def _settings() -> Settings:
    # sv4 resuelve su `.env` por ruta absoluta: nunca un `Settings()` a pelo.
    return Settings(_env_file=None)


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


#: Lecturas sin paginar de sv4 (`design.md` §1).
SIN_PAGINAR = [
    ("fetch_dnis_sin_extra", ({"00000001R"},)),
    ("fetch_hora_extra_recurso", (5,)),
]

#: Lecturas paginadas de sv4.
PAGINADAS = [
    ("fetch_tipos_hora", ()), ("fetch_obras", ()), ("fetch_empleados", ()),
    ("fetch_recursos_activos", ()), ("fetch_partidas_obra", (77,)),
]


# --------------------------------- R1 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", SIN_PAGINAR)
def test_f038_r1_sin_paginar_manda_el_max_rows_del_cliente(
        monkeypatch, metodo, args) -> None:
    falso = SigridFalso()
    getattr(_cliente(monkeypatch, falso, max_rows=12345), metodo)(*args)
    assert [p["max_rows"] for p in falso.peticiones] == [12345]


# --------------------------------- R2 ----------------------------------- #

def test_f038_r2_defecto_500000_en_settings_y_constructor(
        entorno, monkeypatch) -> None:
    # Por atributo y no por import: sin la constante, el test falla solo.
    assert modulo.MAX_ROWS_DEFECTO == 500_000
    assert _settings().sigrid_api_max_rows == modulo.MAX_ROWS_DEFECTO
    falso = SigridFalso()
    _cliente(monkeypatch, falso).fetch_hora_extra_recurso(5)
    assert falso.peticiones[0]["max_rows"] == 500_000


# ----------------------------- R3 y R14 --------------------------------- #

@pytest.mark.parametrize("valor", ["0", "-1", "500001", "abc", "1.5"])
def test_f038_r3_max_rows_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    with pytest.raises(ValidationError):
        _settings()


@pytest.mark.parametrize("valor, esperado", [("1", 1), ("500000", 500_000)])
def test_f038_r3_max_rows_en_los_bordes_vale(entorno, valor,
                                             esperado) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    assert _settings().sigrid_api_max_rows == esperado


@pytest.mark.parametrize("valor", ["0", "-5", "200.5", "abc"])
def test_f038_r14_timeout_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_TIMEOUT_S", valor)
    with pytest.raises(ValidationError):
        _settings()


def test_f038_r14_timeout_200_vale_y_el_defecto_sigue_en_30(entorno) -> None:
    assert _settings().sigrid_api_timeout_s == 30.0
    entorno.setenv("SIGRID_API_TIMEOUT_S", "200")
    assert _settings().sigrid_api_timeout_s == 200.0


# --------------------------------- R4 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", PAGINADAS)
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


def test_f038_r5_build_app_cablea_max_rows(entorno) -> None:
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
    entorno.setattr(modulo_app, "SigridLookupClient", Espia)
    with pytest.raises(_Parada):
        modulo_app.build_app(_settings(), repository=object())
    assert [k["max_rows"] for k in capturados] == [12345]


# --------------------------------- R6 ----------------------------------- #

def test_f038_r6_log_de_instanciacion_sin_la_clave(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=modulo.__name__):
        SigridLookupClient(base_url="http://sigrid.invalid",
                           function_key=CLAVE, database="bd",
                           timeout_s=45, max_rows=4321)
    mensajes = [r.getMessage() for r in caplog.records
                if r.levelno == logging.INFO]
    assert any("max_rows=4321" in m and "timeout_s=45" in m
               for m in mensajes), mensajes
    assert not any(CLAVE in m for m in mensajes)


# --------------------------------- R9 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", SIN_PAGINAR)
def test_f038_r9_truncated_es_error_sin_paginar(monkeypatch, metodo,
                                                args) -> None:
    falso = SigridFalso(truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)
