# tests/test_f002_settings_y_app.py
"""F-002 · configuracion de storage de sv5 y `build_app` con pipeline inyectado.

Sin red: el pipeline que recibe la app lleva un cliente de Sigrid en
memoria; nada sale del proceso.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from config.settings import Settings
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
from tests.dobles import SettingsFake, SigridFake
from tests.test_f002_pipeline_fases import OBRA, _sigrid

#: Lo minimo que exige `Settings` (sin secretos reales).
ENTORNO_MINIMO = {
    "SIGRID_API_BASE_URL": "http://sigrid.invalido",
    "SIGRID_API_FUNCTION_KEY": "clave-de-test",
}

PETICION = {
    "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
    "lineas": [{"registro_id": 1, "fecha_int": 20260302, "recurso_ide": 501,
                "tipo_hora": "normal", "horas": 8.0}],
    "pisar_claves": [],
    "usuario": "ana",
}


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    for k, v in ENTORNO_MINIMO.items():
        monkeypatch.setenv(k, v)
    # Que no se cuele el .env del desarrollador en la suite.
    monkeypatch.chdir(tmp_path)
    return monkeypatch


# ------------------------------- Settings ------------------------------- #

def test_f002_settings_storage_opcional_por_defecto(entorno):
    """Sin variables de storage, sv5 arranca como hasta ahora (solo HTTP)."""
    st = Settings()
    assert st.storage_habilitado is False
    assert st.cola_transfer == "q-transfer"
    assert st.cola_transfer_result == "q-transfer-result"
    assert st.blob_transfer == "transfer"
    assert st.cola_visibility_s == 600
    assert st.cola_max_dequeue == 5
    assert st.transfer_workers == 3


def test_f002_settings_storage_habilitado_por_connection_string(entorno):
    entorno.setenv("COLAS_CONNECTION_STRING", "UseDevelopmentStorage=true")
    assert Settings().storage_habilitado is True


def test_f002_settings_storage_habilitado_por_account_url(entorno):
    entorno.setenv("COLAS_ACCOUNT_URL", "https://stpartes.queue.core.windows.net")
    assert Settings().storage_habilitado is True


@pytest.mark.parametrize("valor,esperado", [("0", 1), ("-4", 1), ("1", 1),
                                            ("7", 7)])
def test_f002_r18_transfer_workers_minimo_uno(entorno, valor, esperado):
    """R18: el pool nunca baja de 1 hilo (0 dejaria la cola sin consumir)."""
    entorno.setenv("TRANSFER_WORKERS", valor)
    assert Settings().transfer_workers == esperado


# ------------------------------- build_app ------------------------------ #

def _app_con_pipeline(cli, **kwargs):
    pipeline = RegistroPipeline(cliente=cli, settings=SettingsFake(), **kwargs)
    return build_app(SettingsFake(), pipeline=pipeline), pipeline


def test_f002_r7_ejecutar_del_endpoint_escribe_bajo_el_lock():
    """R7: el HTTP de pisado tampoco escribe fuera del lock.

    El endpoint ya no toma lock por su cuenta: lo adquiere `registrar`.
    El cliente de Sigrid vigila que ninguna lectura de estado escrito ni
    ninguna escritura ocurra con el lock suelto.
    """
    cli = _sigrid()
    app, pipeline = _app_con_pipeline(cli)
    cli.vigilar_lock(pipeline.lock)

    r = TestClient(app).post("/api/registro/ejecutar", json=PETICION)

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert [e["registro_id"] for e in cuerpo["escritas"]] == [1]
    assert len(cli.lineas) == 1


def test_f002_r4_preflight_del_endpoint_no_escribe():
    """R4: el preflight sigue siendo consultivo y sincrono."""
    cli = _sigrid()
    app, _ = _app_con_pipeline(cli)

    r = TestClient(app).post("/api/registro/preflight", json=PETICION)

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert cuerpo["resumen"] == {"escribir": 1, "omitir": 0,
                                 "ya_registrado": 0, "conflictos": 0}
    assert cli.partes == [] and cli.lineas == []


def test_f002_build_app_sin_pipeline_inyectado(entorno):
    """Retrocompatible: sin pipeline, `build_app` construye el suyo."""
    app = build_app(Settings())
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_f002_build_app_usa_el_pipeline_que_recibe():
    """El pipeline inyectado es el que atiende las peticiones."""
    cli = _sigrid()
    app, _ = _app_con_pipeline(cli)
    TestClient(app).post("/api/registro/ejecutar", json=PETICION)
    assert "escribir" in cli.llamadas


def test_f002_r14_error_del_pipeline_responde_502():
    """Un fallo del pipeline sigue devolviendo 502 con el motivo."""
    cli = SigridFake(obras={}, horas={})       # la obra no existe
    app, _ = _app_con_pipeline(cli)
    r = TestClient(app).post("/api/registro/ejecutar", json=PETICION)
    assert r.status_code == 502
    assert r.json()["ok"] is False
    assert "obra no encontrada" in r.json()["error"]


def test_f002_obra_del_payload_llega_al_pipeline():
    """La obra del cuerpo se traduce a dominio sin perder el codigo."""
    cli = _sigrid()
    app, _ = _app_con_pipeline(cli)
    TestClient(app).post("/api/registro/preflight", json=PETICION)
    assert OBRA.codigo == "0100"
    assert "obra_por_ide" in cli.llamadas
