# tests/test_f038_sigrid_limite.py
"""F-038 en sv2: límite de filas del catálogo `auxhor` y `truncated`.

- R1: la lectura del catálogo manda el `max_rows` del cliente.
- R2: sin `SIGRID_API_MAX_ROWS`, 500.000 (DA1 = B) en settings y en el
  constructor, que coinciden.
- R3 y R14: fuera de rango, el servicio no arranca.
- R5: `build_app` pasa `settings.sigrid_api_max_rows` al cliente.
- R6: el cliente registra en INFO su `max_rows` y su `timeout_s`, sin la
  clave.
- R7: `truncated: true` es `RuntimeError` con «truncada» y la etiqueta.
- R8 (DA3): ese fallo lo absorbe el proveedor del catálogo como cualquier
  otro fallo de Sigrid (caché anterior o vacío, con WARNING).

Sin red: `httpx.Client` del módulo cliente se sustituye por un falso.
"""
from __future__ import annotations

import logging
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from tests.f059_sdk_falsos import instalar_si_faltan

# Los SDK de IA no están en el .venv de la raíz: dobles solo si faltan.
instalar_si_faltan()

from application.services.auxhor_catalog_provider import (
    AuxhorCatalogProvider,
)
from config.settings import Settings
from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import (
    SigridLookupClient,
)
from interface_adapters.api import app as modulo_app

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
CLAVE = "clave-de-test-f038"
COLUMNAS = ["ide", "codigo", "descripcion", "ext", "pre", "prenom"]
VARIABLES = (
    "ENABLE_GEMINI", "ENABLE_CLAUDE", "ENABLE_OPENAI", "IA_PROVIDER",
    "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "PROMPTS_YAML_PATH", "SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY",
    "SIGRID_API_DATABASE", "SIGRID_API_TIMEOUT_S", "SIGRID_API_MAX_ROWS",
    "IA_LOGGING_ENABLED", "PAGINA_COMO_IMAGEN",
)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch) -> None:
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def _settings(**entorno) -> Settings:
    base = {"ENABLE_GEMINI": False, "ENABLE_OPENAI": True,
            "IA_PROVIDER": "openai", "OPENAI_API_KEY": "clave-falsa",
            "PROMPTS_YAML_PATH": str(RAIZ_SERVICIO / "config" /
                                     "prompts.yaml")}
    base.update(entorno)
    return Settings(_env_file=None, **base)


class SigridFalso:
    """`httpx.Client` en memoria: apunta cada petición y responde."""

    def __init__(self, *, filas=None, truncated: bool = False) -> None:
        self.filas = filas if filas is not None else [
            [1, "HN", "Hora normal", 0, 10.0, 10.0]]
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def post(self, url, json=None, headers=None):
        self.peticiones.append(json)
        return httpx.Response(200, json={
            "ok": True, "columns": COLUMNAS, "rows": self.filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kwargs) -> SigridLookupClient:
    monkeypatch.setattr(modulo.httpx, "Client", falso)
    return SigridLookupClient(base_url="http://sigrid.invalid",
                              function_key=CLAVE, database="bd", **kwargs)


# --------------------------------- R1 ----------------------------------- #

def test_f038_r1_tipos_hora_manda_el_max_rows_del_cliente(monkeypatch) -> None:
    falso = SigridFalso()
    opciones = _cliente(monkeypatch, falso, max_rows=12345).fetch_tipos_hora()
    assert [p["max_rows"] for p in falso.peticiones] == [12345]
    assert [o.codigo for o in opciones] == ["HN"]


# --------------------------------- R2 ----------------------------------- #

def test_f038_r2_defecto_500000_en_settings_y_constructor(monkeypatch) -> None:
    # Por atributo y no por import: sin la constante, el test falla solo.
    assert modulo.MAX_ROWS_DEFECTO == 500_000
    assert _settings().sigrid_api_max_rows == modulo.MAX_ROWS_DEFECTO
    falso = SigridFalso()
    _cliente(monkeypatch, falso).fetch_tipos_hora()
    assert falso.peticiones[0]["max_rows"] == 500_000


# ----------------------------- R3 y R14 --------------------------------- #

@pytest.mark.parametrize("valor", ["0", "-1", "500001", "abc", "1.5"])
def test_f038_r3_max_rows_fuera_de_rango_no_arranca(valor) -> None:
    with pytest.raises(ValidationError):
        _settings(SIGRID_API_MAX_ROWS=valor)


@pytest.mark.parametrize("valor, esperado", [("1", 1), ("500000", 500_000)])
def test_f038_r3_max_rows_en_los_bordes_vale(valor, esperado) -> None:
    assert _settings(SIGRID_API_MAX_ROWS=valor).sigrid_api_max_rows == \
        esperado


@pytest.mark.parametrize("valor", ["0", "-5", "200.5", "abc"])
def test_f038_r14_timeout_fuera_de_rango_no_arranca(valor) -> None:
    with pytest.raises(ValidationError):
        _settings(SIGRID_API_TIMEOUT_S=valor)


def test_f038_r14_timeout_200_vale_y_el_defecto_sigue_en_30() -> None:
    assert _settings().sigrid_api_timeout_s == 30.0
    assert _settings(SIGRID_API_TIMEOUT_S="200").sigrid_api_timeout_s == 200.0


# Mutación F-038: el límite inferior es `gt=0` (exclusivo); `gt=1` dejaría
# fuera 0.5 y 1, timeouts válidos que ningún test probaba.
@pytest.mark.parametrize("valor, esperado", [("0.5", 0.5), ("1", 1.0)])
def test_f038_r14_timeout_por_debajo_de_1_vale(valor, esperado) -> None:
    timeout = _settings(SIGRID_API_TIMEOUT_S=valor).sigrid_api_timeout_s
    assert timeout == esperado


# --------------------------------- R5 ----------------------------------- #

def test_f038_r5_build_app_cablea_max_rows(monkeypatch) -> None:
    capturados: list[dict] = []

    class Espia:
        def __init__(self, **kwargs) -> None:
            capturados.append(kwargs)

    monkeypatch.setattr(modulo_app, "SigridLookupClient", Espia)
    modulo_app.build_app(_settings(
        SIGRID_API_BASE_URL="http://sigrid.invalid",
        SIGRID_API_FUNCTION_KEY=CLAVE, SIGRID_API_DATABASE="bd",
        SIGRID_API_MAX_ROWS="12345"))
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


# --------------------------------- R7 ----------------------------------- #

def test_f038_r7_truncated_es_error_sin_filas(monkeypatch) -> None:
    falso = SigridFalso(truncated=True)
    with pytest.raises(RuntimeError, match=r"truncada \[tipos_hora\]"):
        _cliente(monkeypatch, falso).fetch_tipos_hora()


def test_f038_r7_sin_truncated_devuelve_las_filas(monkeypatch) -> None:
    falso = SigridFalso(truncated=False)
    assert len(_cliente(monkeypatch, falso).fetch_tipos_hora()) == 1


# --------------------------------- R8 ----------------------------------- #

def test_f038_r8_catalogo_truncado_degrada_a_vacio_con_warning(
        monkeypatch, caplog) -> None:
    falso = SigridFalso(truncated=True)
    proveedor = AuxhorCatalogProvider(client=_cliente(monkeypatch, falso))
    with caplog.at_level(logging.WARNING):
        assert proveedor.prompt_block() == ""
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("truncada" in r.getMessage() for r in avisos)


def test_f038_r8_catalogo_truncado_conserva_la_cache_anterior(
        monkeypatch) -> None:
    falso = SigridFalso()
    proveedor = AuxhorCatalogProvider(client=_cliente(monkeypatch, falso),
                                      ttl_seconds=0)
    bloque = proveedor.prompt_block()
    assert "HN" in bloque
    falso.truncated = True
    assert proveedor.prompt_block() == bloque
    assert len(falso.peticiones) == 2
