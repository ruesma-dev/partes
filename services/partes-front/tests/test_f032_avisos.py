# tests/test_f032_avisos.py
"""F-032 · R25: los avisos dicen «Sin calendario de Sesame».

Con el proveedor REAL sobre una tabla `festivos_trabajador` falsa: un
trabajador sin fila enciende los tres avisos degradados (vista
trabajador, matriz de obra y «+ Nuevo») y el `aviso_sesame` del
preflight, todos con «Sin calendario de Sesame» y ya no con «Sesame no
disponible». Con fila no hay aviso; con Sesame apagado, tampoco.

SQLite en memoria. F-077: el proveedor se enciende con `activo` (sv4 ya
no tiene cliente de Sesame).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from application.services.calendario_provider import CalendarioProvider
from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias
from tests.test_f032_sin_bloqueo import Sv5Simple

DNI = "12345678Z"           # el de `sembrar_dias`
DIA = "2026-05-18"
TEXTO = "Sin calendario de Sesame"
VIEJO = "Sesame no disponible"
FILA = {"id": 1, "dni_norm": DNI, "ano": 2026,
        "festivos_json": '{"2026-05-15": "San Isidro"}',
        "leido_en_utc": "2026-11-17T10:00:00Z"}


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _montar(*, filas=(), activo=True):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_dias(fabrica, [{"fecha": DIA, "horas": 8.0}])
    proveedor = CalendarioProvider(
        activo=activo,
        respaldo_holiday_name=lambda _d: None,
        leer_festivos=lambda: list(filas))
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=Sv5Simple(), publisher=None,
                    calendario_provider=proveedor)
    return TestClient(app), ids


def _vistas(cliente) -> dict[str, str]:
    return {
        "trabajador": cliente.get("/trabajadores/rec-501?modo=natural").text,
        "obra": cliente.get("/obras/obr-10?period=2026-05&modo=natural").text,
    }


def _banner(html: str) -> str:
    """El texto del aviso degradado, o "" si no esta."""
    i = html.find("sesame-degradado")
    if i < 0:
        return ""
    return html[i:html.index("</div>", i)]


def test_f032_r25_vistas_sin_fila_avisan_con_el_texto_nuevo(entorno) -> None:
    cliente, _ids = _montar()
    for nombre, html in _vistas(cliente).items():
        banner = _banner(html)
        assert TEXTO in banner, nombre
        assert VIEJO not in html, nombre


def test_f032_r25_vista_trabajador_con_fila_no_avisa(entorno) -> None:
    """La matriz de obra con todas sus filas con fila la prueba
    `test_f032_rejilla_obra` (R28: sin consultar `(None, ano)`)."""
    cliente, _ids = _montar(filas=[FILA])
    assert "sesame-degradado" not in _vistas(cliente)["trabajador"]


def test_f032_r25_vistas_con_sesame_apagado_no_avisan(entorno) -> None:
    cliente, _ids = _montar(activo=False)
    for nombre, html in _vistas(cliente).items():
        assert "sesame-degradado" not in html, nombre


def test_f032_r25_nuevo_parte_lleva_el_texto_nuevo(entorno) -> None:
    cliente, _ids = _montar()
    html = cliente.get("/nuevo").text
    i = html.index('id="cal-aviso"')
    aviso = html[i:html.index("</p>", i)]
    assert TEXTO in aviso
    assert VIEJO not in html


@pytest.mark.parametrize("filas,activo,fiable", [
    ((), True, False), ((FILA,), True, True), ((), False, True)])
def test_f032_r25_nuevo_parte_enciende_el_aviso_solo_sin_fila(
        entorno, filas, activo, fiable) -> None:
    """El aviso de «+ Nuevo» lo enciende `fiable` de `/api/calendario`."""
    cliente, _ids = _montar(filas=filas, activo=activo)
    r = cliente.get("/api/calendario", params={
        "desde": "2026-05-11", "hasta": "2026-05-17", "dni": DNI})
    assert r.json()["fiable"] is fiable


def test_f032_r25_aviso_sesame_del_preflight(entorno) -> None:
    cliente, ids = _montar()
    datos = cliente.post("/api/aprobar/preflight",
                         json={"registro_ids": ids}).json()
    assert TEXTO in datos["aviso_sesame"]
    assert VIEJO not in datos["aviso_sesame"]


@pytest.mark.parametrize("filas,activo", [((FILA,), True), ((), False)])
def test_f032_r25_sin_aviso_sesame_con_fila_o_apagado(entorno, filas,
                                                      activo) -> None:
    cliente, ids = _montar(filas=filas, activo=activo)
    datos = cliente.post("/api/aprobar/preflight",
                         json={"registro_ids": ids}).json()
    assert "aviso_sesame" not in datos
