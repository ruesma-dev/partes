# tests/test_f038_sigrid_limite.py
"""F-038 en sv5: límite de filas de las lecturas de Sigrid y timeouts.

- R1: toda lectura (`_read`) manda el `max_rows` del cliente, en una
  lectura de cada fila del inventario (`design.md` §1).
- R2: sin `SIGRID_API_MAX_ROWS`, 500.000 (DA1 = B) en settings y en el
  constructor, que coinciden.
- R3 y R14: fuera de rango, el servicio no arranca.
- R5: el cableado (`app.py`, `main.py`, `comprobar_asiento_analitico.py`)
  pasa `settings.sigrid_api_max_rows`.
- R6: el cliente registra en INFO su `max_rows` y su `timeout_s`, sin la
  clave.
- R9: `truncated` sigue siendo error en las lecturas sin lote.
- R15: con timeout 200, plazo HTTP 230 y `timeout_seconds` 200.

Sin red: `httpx.post` del módulo cliente se sustituye por un falso.
"""
from __future__ import annotations

import logging

import httpx
import pytest
from pydantic import ValidationError

import comprobar_asiento_analitico as herramienta
import main as modulo_main
from config.settings import Settings
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from interface_adapters.api import app as modulo_app

CLAVE = "clave-de-test-f038"

ENTORNO_MINIMO = {
    "SIGRID_API_BASE_URL": "http://sigrid.invalid",
    "SIGRID_API_FUNCTION_KEY": CLAVE,
}


class SigridApiFalso:
    """sigrid-api en memoria: responde sin filas y apunta cada petición."""

    def __init__(self, *, truncated: bool = False) -> None:
        self.truncated = truncated
        self.lecturas: list[dict] = []
        self.plazos: list[float] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        self.plazos.append(timeout)
        return httpx.Response(200, json={
            "ok": True, "columns": ["m"], "rows": [],
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kwargs) -> SigridWriteClient:
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key=CLAVE, database="bd", **kwargs)


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    for k, v in ENTORNO_MINIMO.items():
        monkeypatch.setenv(k, v)
    for k in ("SIGRID_API_MAX_ROWS", "SIGRID_API_TIMEOUT_S"):
        monkeypatch.delenv(k, raising=False)
    # Que no se cuele el .env del desarrollador en la suite.
    monkeypatch.chdir(tmp_path)
    return monkeypatch


#: Una lectura de cada fila de `design.md` §1 (sv5).
LECTURAS = [
    ("obra_por_codigo", ("0404",)),
    ("obra_por_ide", (7,)),
    ("siguiente_cod_pt", (2026, 1)),
    ("max_pos", (9,)),
    ("datos_recursos", ([501],)),
    ("lineas_por_synckey", (["partes:1"],)),
    ("lineas_por_ide", ([1],)),
    ("partes_por_ide", ([1],)),
    ("estados_de_partes", ([1],)),
    ("lineas_para_reajuste", (["partes:1", "partes:2"],)),
    ("partes_existentes", (7, [(2026, 10)])),
    ("partes_del_periodo", (7, 2026, 10)),
    ("cuentas_de_centro", (3, 1, ["01"])),
    ("partidas_de_lineas", ([11],)),
    ("recursos_por_dni", (["00000001R"],)),
    ("horas_de_recursos", ([501],)),
    ("lineas_existentes", (9, [501], [20261001])),
]


# --------------------------------- R1 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", LECTURAS)
def test_f038_r1_cada_lectura_manda_el_max_rows_del_cliente(
        monkeypatch, metodo, args) -> None:
    falso = SigridApiFalso()
    getattr(_cliente(monkeypatch, falso, max_rows=12345), metodo)(*args)
    assert falso.lecturas, f"{metodo} no ha leído"
    assert [p["max_rows"] for p in falso.lecturas] == \
        [12345] * len(falso.lecturas)


# --------------------------------- R2 ----------------------------------- #

def test_f038_r2_defecto_500000_en_settings_y_constructor(
        entorno, monkeypatch) -> None:
    # Por atributo y no por import: sin la constante, el test falla solo.
    assert modulo_cliente.MAX_ROWS_DEFECTO == 500_000
    assert Settings().sigrid_api_max_rows == modulo_cliente.MAX_ROWS_DEFECTO
    falso = SigridApiFalso()
    _cliente(monkeypatch, falso).max_pos(9)
    assert falso.lecturas[0]["max_rows"] == 500_000


# ----------------------------- R3 y R14 --------------------------------- #

@pytest.mark.parametrize("valor", ["0", "-1", "500001", "abc", "1.5"])
def test_f038_r3_max_rows_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("valor, esperado", [("1", 1), ("500000", 500_000)])
def test_f038_r3_max_rows_en_los_bordes_vale(entorno, valor,
                                             esperado) -> None:
    entorno.setenv("SIGRID_API_MAX_ROWS", valor)
    assert Settings().sigrid_api_max_rows == esperado


@pytest.mark.parametrize("valor", ["0", "-5", "200.5", "abc"])
def test_f038_r14_timeout_fuera_de_rango_no_arranca(entorno, valor) -> None:
    entorno.setenv("SIGRID_API_TIMEOUT_S", valor)
    with pytest.raises(ValidationError):
        Settings()


def test_f038_r14_timeout_200_vale_y_el_defecto_sigue_en_60(entorno) -> None:
    assert Settings().sigrid_api_timeout_s == 60.0
    entorno.setenv("SIGRID_API_TIMEOUT_S", "200")
    assert Settings().sigrid_api_timeout_s == 200.0


# --------------------------------- R5 ----------------------------------- #

class _Parada(Exception):
    """Corta el cableado en cuanto se ha construido el cliente."""


class _ClienteEspia:
    capturados: list[dict] = []

    def __init__(self, **kwargs) -> None:
        _ClienteEspia.capturados.append(kwargs)
        raise _Parada


@pytest.fixture
def espia(entorno):
    _ClienteEspia.capturados = []
    entorno.setenv("SIGRID_API_MAX_ROWS", "12345")
    return entorno


def test_f038_r5_app_cablea_max_rows(espia) -> None:
    espia.setattr(modulo_app, "SigridWriteClient", _ClienteEspia)
    with pytest.raises(_Parada):
        modulo_app._cliente_sigrid(Settings())
    assert _ClienteEspia.capturados[0]["max_rows"] == 12345


def test_f038_r5_main_cablea_max_rows(espia, tmp_path) -> None:
    espia.setenv("LOG_DIR", str(tmp_path / "logs"))
    espia.setattr(modulo_main, "SigridWriteClient", _ClienteEspia)
    with pytest.raises(_Parada):
        modulo_main.main()
    assert _ClienteEspia.capturados[0]["max_rows"] == 12345


def test_f038_r5_comprobar_asiento_cablea_max_rows(espia) -> None:
    espia.setattr(herramienta, "SigridWriteClient", _ClienteEspia)
    with pytest.raises(_Parada):
        herramienta.main(["--empresa", "1", "--obra", "0404", "--ano",
                          "2026", "--mes", "10"], settings=Settings())
    assert _ClienteEspia.capturados[0]["max_rows"] == 12345


# --------------------------------- R6 ----------------------------------- #

def test_f038_r6_log_de_instanciacion_sin_la_clave(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=modulo_cliente.__name__):
        SigridWriteClient(base_url="http://sigrid.invalid",
                          function_key=CLAVE, database="bd",
                          timeout_s=45, max_rows=4321)
    mensajes = [r.getMessage() for r in caplog.records
                if r.levelno == logging.INFO]
    assert any("max_rows=4321" in m and "timeout_s=45" in m
               for m in mensajes), mensajes
    assert not any(CLAVE in m for m in mensajes)


# --------------------------------- R9 ----------------------------------- #

@pytest.mark.parametrize("metodo, args", [
    ("recursos_por_dni", (["00000001R"],)),
    ("horas_de_recursos", ([501],)),
    ("lineas_existentes", (9, [501], [20261001])),
    ("partidas_de_lineas", ([11],)),
    ("cuentas_de_centro", (3, 1, ["01"])),
])
def test_f038_r9_truncated_es_error_en_las_lecturas_sin_lote(
        monkeypatch, metodo, args) -> None:
    falso = SigridApiFalso(truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)


# --------------------------------- R15 ---------------------------------- #

def test_f038_r15_timeout_200_plazo_http_230(monkeypatch) -> None:
    falso = SigridApiFalso()
    _cliente(monkeypatch, falso, timeout_s=200).max_pos(9)
    assert falso.plazos == [230]
    assert falso.lecturas[0]["timeout_seconds"] == 200
