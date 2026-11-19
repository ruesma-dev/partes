# tests/test_f032_wiring_sv4.py
"""F-032 · R18–R20 en el cableado de sv4: `list_festivos_trabajador` y
`build_app`.

El repositorio lee `festivos_trabajador` entera, en dicts (como
`list_jornadas_empleado`): sv4 solo hace un SELECT, no escribe nunca. Con
`FESTIVOS_SESAME_ENABLED=true` (F-077), `build_app` da al proveedor ese
lector y el log de wiring dice `festivos=tabla`. SQLite en memoria; sin
red.
"""
from __future__ import annotations

import logging
from datetime import date

import httpx
import pytest

from config.settings import Settings
from infrastructure.database.orm_models import FestivoTrabajadorOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite

DNI = "12345678Z"


@pytest.fixture
def base(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)

    def prohibido(*_a, **_kw):
        raise AssertionError("los tests no pueden tocar la red")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", prohibido)
    return monkeypatch


def _sembrar(fabrica, dni=DNI, ano=2026,
             festivos='{"2026-05-15": "San Isidro"}'):
    with fabrica.create_session() as s:
        fila = FestivoTrabajadorOrm(dni_norm=dni, ano=ano,
                                    festivos_json=festivos, n_festivos=1,
                                    leido_en_utc="2026-11-17T10:00:00Z")
        s.add(fila)
        s.commit()
        return fila.id


def test_f032_r18_list_festivos_trabajador_devuelve_dicts():
    fabrica = FabricaSesionSqlite()
    id_ = _sembrar(fabrica)
    _sembrar(fabrica, dni="87654321X", ano=2025, festivos="{}")
    filas = ParteReviewRepository(fabrica).list_festivos_trabajador()
    assert filas[0] == {"id": id_, "dni_norm": DNI, "ano": 2026,
                        "festivos_json": '{"2026-05-15": "San Isidro"}',
                        "n_festivos": 1,
                        "leido_en_utc": "2026-11-17T10:00:00Z"}
    assert [(f["dni_norm"], f["ano"]) for f in filas] == [
        (DNI, 2026), ("87654321X", 2025)]


def test_f032_r18_list_festivos_trabajador_vacia():
    assert ParteReviewRepository(
        FabricaSesionSqlite()).list_festivos_trabajador() == []


def test_f032_r18_build_app_con_sesame_lee_la_tabla(base, caplog):
    base.setenv("FESTIVOS_SESAME_ENABLED", "true")
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica)
    with caplog.at_level(logging.INFO):
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
    proveedor = app.state.calendario_provider
    assert proveedor.activo is True
    assert proveedor.fuente_para(DNI, 2026) == "sesame"
    assert proveedor.holiday_name_para(DNI)(date(2026, 5, 15)) == "San Isidro"
    assert proveedor.fuente_para("87654321X", 2026) == "sin_fila"
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert "CABLEADO" in wiring[0] and "festivos=tabla" in wiring[0]
    assert "sv4 no llama a Sesame" in wiring[0]


def test_f032_r12_build_app_sin_sesame_no_lee_la_tabla(base):
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    proveedor = app.state.calendario_provider
    assert proveedor.activo is False
    assert proveedor.fuente_para(DNI, 2026) == "sin_sesame"
    assert proveedor.holiday_name_para(DNI)(date(2026, 5, 15)) is None
