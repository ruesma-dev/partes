# tests/test_f052_api_sincronizar.py
"""F-052 en sv5: `POST /api/sincronizar/leer` (R1, R4-R6).

- R1: las líneas del ámbito y las de los `registro_ids`, sin repetir.
- R4: un fallo o un corte por tiempo de sigrid-api es 502 sin parciales.
- R5: no toma el lock de escritura, no llama a `/api/sql/write` y lee la
  base configurada (`ruesma`).
- R6: 422 sin leer Sigrid si el cuerpo no vale.
- `SINCRONIZAR_MAX_REGISTRO_IDS`: 3000 por defecto.

Sin red: dobles del cliente y `httpx.post` sustituido por un falso.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import FrozenInstanceError

import httpx
import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from config.settings import Settings
from domain.models.registro_models import LineaSincronizar
from fastapi.testclient import TestClient
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from interface_adapters.api.app import build_app
from pydantic import ValidationError
from tests.dobles import SettingsFake

CUERPO_OBRA = {"obra_ide": 686, "desde": 20261001, "hasta": 20261031,
               "registro_ids": [2, 1, 2]}


def _linea(ide: int, **cambios) -> LineaSincronizar:
    base = dict(hmores_ide=ide, hmoide=7001, parte_cod="PT26/00001",
                parte_est=1, obra_ide=686, obra_cod="0686", recurso_ide=501,
                fecha_int=20261014, hora_ide=3, hora_cod="HL01", hora_ext=0,
                partida_ide=11, partida_cod="P1", can=8.0, tot=120.0,
                enlazada=False, origen="manual")
    base.update(cambios)
    return LineaSincronizar(**base)


class LectorFalso:
    """Cliente de Sigrid en memoria: apunta cada lectura y revienta si
    alguien intenta escribir."""

    def __init__(self, *, ambito=None, por_synckey=None,
                 fallo: str | None = None) -> None:
        self.ambito = ambito or []
        self.por_synckey = por_synckey or []
        self.fallo = fallo
        self.llamadas: list[tuple[str, object]] = []

    def lineas_sincronizar(self, **kwargs):
        self.llamadas.append(("lineas_sincronizar", kwargs))
        if self.fallo == "lineas_sincronizar":
            raise RuntimeError("sigrid-api caida")
        return list(self.ambito)

    def lineas_sincronizar_por_synckey(self, claves):
        self.llamadas.append(("por_synckey", list(claves)))
        if self.fallo == "por_synckey":
            raise RuntimeError("sigrid-api caida")
        return list(self.por_synckey)

    def escribir(self, statements):   # pragma: no cover - no debe llamarse
        raise AssertionError("sincronizar no puede escribir")


def _settings(max_ids: int = 3000) -> SettingsFake:
    st = SettingsFake()
    st.sincronizar_max_registro_ids = max_ids
    return st


def _app(lector, *, st=None, lock=None):
    st = st or _settings()
    pipeline = RegistroPipeline(cliente=lector, settings=st, lock=lock)
    return build_app(st, pipeline=pipeline, lector=lector)


# --------------------------------- R1 ----------------------------------- #

def test_f052_r1_endpoint_une_ambito_y_synckeys_sin_repetir() -> None:
    lector = LectorFalso(
        ambito=[_linea(30), _linea(10, origen="partes", registro_id=1)],
        por_synckey=[_linea(10, origen="partes", registro_id=1),
                     _linea(20, origen="partes", registro_id=2,
                            obra_ide=999, obra_cod="0999")])
    r = TestClient(_app(lector)).post("/api/sincronizar/leer",
                                      json=CUERPO_OBRA)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert [l["hmores_ide"] for l in cuerpo["lineas"]] == [10, 20, 30]
    assert cuerpo["lineas"][1]["obra_ide"] == 999
    assert set(cuerpo["lineas"][0]) == {
        "hmores_ide", "hmoide", "parte_cod", "parte_est", "obra_ide",
        "obra_cod", "recurso_ide", "fecha_int", "hora_ide", "hora_cod",
        "hora_ext", "partida_ide", "partida_cod", "can", "tot", "enlazada",
        "origen", "registro_id", "ajuste_id"}
    assert lector.llamadas == [
        ("lineas_sincronizar", {"obra_ide": 686, "recurso_ide": None,
                                "desde": 20261001, "hasta": 20261031}),
        ("por_synckey", ["partes:1", "partes:2"])]


def test_f052_r1_endpoint_por_recurso_y_sin_registro_ids() -> None:
    lector = LectorFalso(ambito=[_linea(5)])
    r = TestClient(_app(lector)).post("/api/sincronizar/leer", json={
        "recurso_ide": 501, "desde": 20260916, "hasta": 20261015})
    assert r.status_code == 200
    assert [l["hmores_ide"] for l in r.json()["lineas"]] == [5]
    assert lector.llamadas == [
        ("lineas_sincronizar", {"obra_ide": None, "recurso_ide": 501,
                                "desde": 20260916, "hasta": 20261015})]


def test_f052_r6_endpoint_admite_62_dias_y_el_tope_justo() -> None:
    lector = LectorFalso()
    r = TestClient(_app(lector, st=_settings(max_ids=3))).post(
        "/api/sincronizar/leer", json={
            "obra_ide": 686, "desde": 20261001, "hasta": 20261201,
            "registro_ids": [1, 2, 3]})
    assert r.status_code == 200


# --------------------------------- R6 ----------------------------------- #

@pytest.mark.parametrize("cuerpo", [
    {"desde": 20261001, "hasta": 20261031},
    {"obra_ide": 686, "recurso_ide": 501, "desde": 20261001,
     "hasta": 20261031},
    {"obra_ide": 686, "desde": 20261332, "hasta": 20261340},
    {"obra_ide": 686, "desde": 2026101, "hasta": 20261031},
    {"obra_ide": 686, "desde": 20261031, "hasta": 20261001},
    {"obra_ide": 686, "desde": 20261001, "hasta": 20261202},
    {"obra_ide": 0, "desde": 20261001, "hasta": 20261031},
    {"recurso_ide": -1, "desde": 20261001, "hasta": 20261031},
    {"obra_ide": 686, "desde": 20261001},
    {"obra_ide": 686, "desde": 20261001, "hasta": 20261031,
     "registro_ids": [1, 2, 3, 4]},
])
def test_f052_r6_endpoint_422_sin_leer_sigrid(cuerpo) -> None:
    lector = LectorFalso()
    r = TestClient(_app(lector, st=_settings(max_ids=3))).post(
        "/api/sincronizar/leer", json=cuerpo)
    assert r.status_code == 422
    assert lector.llamadas == []


def test_f052_r6_settings_max_registro_ids(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    monkeypatch.delenv("SINCRONIZAR_MAX_REGISTRO_IDS", raising=False)
    monkeypatch.chdir(tmp_path)
    assert Settings().sincronizar_max_registro_ids == 3000
    monkeypatch.setenv("SINCRONIZAR_MAX_REGISTRO_IDS", "10")
    assert Settings().sincronizar_max_registro_ids == 10
    monkeypatch.setenv("SINCRONIZAR_MAX_REGISTRO_IDS", "0")
    with pytest.raises(ValidationError):
        Settings()


# --------------------------------- R4 ----------------------------------- #

@pytest.mark.parametrize("donde", ["lineas_sincronizar", "por_synckey"])
def test_f052_r4_endpoint_fallo_de_lectura_502_sin_parciales(donde) -> None:
    lector = LectorFalso(ambito=[_linea(1)], fallo=donde)
    r = TestClient(_app(lector)).post("/api/sincronizar/leer",
                                      json=CUERPO_OBRA)
    assert r.status_code == 502
    assert r.json()["ok"] is False and "caida" in r.json()["error"]
    assert "lineas" not in r.json()


class SigridApiFalso:
    """sigrid-api en memoria: cada petición devuelve lo de `respuesta`
    (o lanza la excepción) y apunta la url y el cuerpo."""

    def __init__(self, respuesta) -> None:
        self.respuesta = respuesta
        self.urls: list[str] = []
        self.cuerpos: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.urls.append(url)
        self.cuerpos.append(json)
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        return self.respuesta


def _settings_con_sigrid() -> SettingsFake:
    st = _settings()
    st.sigrid_api_base_url = "http://sigrid.invalid"
    st.sigrid_api_function_key = "clave-de-test"
    st.sigrid_api_database = "ruesma"
    st.sigrid_api_timeout_s = 5
    st.sigrid_api_max_rows = 500000
    st.sigrid_max_statements = 15
    st.tip_parte_trabajo = 35
    st.est_parte_activo = 1
    return st


@pytest.mark.parametrize("respuesta", [
    httpx.ReadTimeout("corte por tiempo"),
    httpx.Response(504, text="Gateway Timeout"),
    httpx.Response(200, json={"ok": True, "columns": ["ide"],
                              "rows": [[1]], "truncated": True}),
    httpx.Response(200, json={"ok": False, "error": "x"}),
])
def test_f052_r4_endpoint_corte_o_truncado_502_sin_parciales(
        monkeypatch, respuesta) -> None:
    falso = SigridApiFalso(respuesta)
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    r = TestClient(build_app(_settings_con_sigrid())).post(
        "/api/sincronizar/leer", json=CUERPO_OBRA)
    assert r.status_code == 502
    assert r.json()["ok"] is False and "lineas" not in r.json()


# --------------------------------- R5 ----------------------------------- #

@pytest.mark.parametrize("con_pipeline", [True, False])
def test_f052_r5_endpoint_solo_lee_la_base_configurada(
        monkeypatch, con_pipeline) -> None:
    """Sin `lector` inyectado, la app usa un SigridWriteClient (el suyo o,
    con pipeline de fuera, uno nuevo) y solo llama a `/api/sql/read`."""
    falso = SigridApiFalso(httpx.Response(200, json={
        "ok": True, "columns": ["ide"], "rows": [], "truncated": False}))
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    st = _settings_con_sigrid()
    pipeline = (RegistroPipeline(cliente=LectorFalso(), settings=st)
                if con_pipeline else None)
    cliente_http = TestClient(build_app(st, pipeline=pipeline))
    for _ in range(2):
        r = cliente_http.post("/api/sincronizar/leer", json=CUERPO_OBRA)
        assert r.status_code == 200 and r.json() == {"ok": True,
                                                     "lineas": []}
    assert falso.urls and all(u == "http://sigrid.invalid/api/sql/read"
                              for u in falso.urls)
    assert {c["database"] for c in falso.cuerpos} == {"ruesma"}


def test_f052_r5_endpoint_no_toma_el_lock_de_escritura() -> None:
    """Con el lock tomado por otro hilo (una escritura en curso), la
    lectura responde igual: no espera a nadie."""
    lock = threading.Lock()
    cliente_http = TestClient(_app(LectorFalso(), lock=lock))
    respuesta: dict = {}

    def _pedir():
        respuesta["r"] = cliente_http.post("/api/sincronizar/leer",
                                           json=CUERPO_OBRA)

    assert lock.acquire(timeout=1)
    try:
        hilo = threading.Thread(target=_pedir, daemon=True)
        hilo.start()
        hilo.join(timeout=10)
        assert not hilo.is_alive(), "la sincronizacion espero al lock"
    finally:
        lock.release()
    assert respuesta["r"].status_code == 200


# ------------- supervivientes de la mutación (mutacion_F-052.md) -------- #

def test_f052_r2_linea_sincronizar_inmutable() -> None:
    """La línea leída de Sigrid no se toca después (mutante 35)."""
    with pytest.raises(FrozenInstanceError):
        _linea(1).can = 0.0


@pytest.mark.parametrize("cuerpo", [
    {"obra_ide": 1, "desde": 20261014, "hasta": 20261014},
    {"recurso_ide": 1, "desde": 20261014, "hasta": 20261014}])
def test_f052_r6_ide_1_y_un_solo_dia_son_validos(cuerpo) -> None:
    """El ide 1 y el rango de un día (`desde == hasta`) son válidos
    (mutantes 36, 37, 38 y 39)."""
    lector = LectorFalso()
    r = TestClient(_app(lector)).post("/api/sincronizar/leer", json=cuerpo)
    assert r.status_code == 200, r.text
    assert lector.llamadas[0][1]["desde"] == lector.llamadas[0][1]["hasta"]


def test_f052_r6_settings_max_registro_ids_minimo_1(monkeypatch,
                                                    tmp_path) -> None:
    """Un solo `registro_id` por petición es un tope válido (mutante 34)."""
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    monkeypatch.setenv("SINCRONIZAR_MAX_REGISTRO_IDS", "1")
    monkeypatch.chdir(tmp_path)
    assert Settings().sincronizar_max_registro_ids == 1


def test_f052_r6_demasiados_registro_ids_ok_false() -> None:
    """El 422 por el tope de `registro_ids` lleva `ok: false` como el
    resto de errores de sv5 (mutante 41)."""
    lector = LectorFalso()
    r = TestClient(_app(lector, st=_settings(max_ids=1))).post(
        "/api/sincronizar/leer", json=dict(CUERPO_OBRA, registro_ids=[1, 2]))
    assert r.status_code == 422
    assert r.json()["ok"] is False and "como mucho 1" in r.json()["error"]
    assert lector.llamadas == []


def test_f052_r1_lector_inyectado_sin_pipeline(monkeypatch) -> None:
    """Con `lector` inyectado y sin `pipeline`, la lectura usa ese lector y
    no el cliente que la app construye para escribir (mutante 40)."""
    falso = SigridApiFalso(httpx.Response(200, json={
        "ok": True, "columns": ["ide"], "rows": [], "truncated": False}))
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    lector = LectorFalso(ambito=[_linea(5)])
    r = TestClient(build_app(_settings_con_sigrid(), lector=lector)).post(
        "/api/sincronizar/leer", json=CUERPO_OBRA)
    assert r.status_code == 200
    assert [l["hmores_ide"] for l in r.json()["lineas"]] == [5]
    assert falso.urls == []


@pytest.mark.parametrize("cuerpo, ambito", [
    (CUERPO_OBRA, "obra"),
    ({"recurso_ide": 501, "desde": 20261001, "hasta": 20261031},
     "recurso")])
def test_f052_r1_log_dice_el_ambito(caplog, cuerpo, ambito) -> None:
    """El log INFO de la lectura dice si fue por obra o por recurso
    (mutante 42)."""
    with caplog.at_level(logging.INFO,
                         logger="interface_adapters.api.app"):
        r = TestClient(_app(LectorFalso())).post("/api/sincronizar/leer",
                                                 json=cuerpo)
    assert r.status_code == 200
    linea = next(m for m in caplog.messages if "[sincronizar] ambito=" in m)
    assert f"ambito={ambito} " in linea
