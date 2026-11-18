# tests/test_f003_r23_bloqueo_registro.py
"""F-003 R23-R25, R27, con el bloqueo ya retirado por F-032 (DA17 = B).

F-003 paraba el registro en Sigrid sin el calendario de Sesame y dejaba
una salida unica, el override del modal, que marcaba `[SIN-SESAME]`.
F-032 lo retira: sv4 registra siempre y solo avisa (`aviso_sesame`); el
comportamiento nuevo lo prueba `test_f032_sin_bloqueo.py`. Aqui queda lo
que sigue valiendo: el badge de una linea que YA lleve la marca (F-032
R24) y que con Sesame sin configurar nada de esto existe (R27).
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import (
    FabricaSesionSqlite,
    estados_sigrid,
    sembrar_dias,
)
from tests.test_f003_r2_vistas_festivos import ProveedorFake

DIA = "2026-05-18"      # lunes laborable


class PublisherFake:
    def __init__(self) -> None:
        self.publicadas: list[tuple[dict, str | None]] = []

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        self.publicadas.append((payload, usuario))
        return f"peticion-{len(self.publicadas)}"


class TransferClientFake:
    def __init__(self, ids=None) -> None:
        self._ids = ids or []
        self.ejecutadas: list[dict] = []

    def preflight(self, payload: dict) -> dict:
        return {"ok": True, "conflictos": [], "escribir": len(
            payload.get("lineas") or [])}

    def ejecutar(self, payload: dict) -> dict:
        self.ejecutadas.append(payload)
        return {
            "ok": True,
            "escritas": [{"registro_id": l["registro_id"], "hmoide": 1,
                          "hmores_ide": 2, "parte_cod": "P1"}
                         for l in payload["lineas"]],
            "omitidas": [], "ya_registradas": [],
        }


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


@pytest.fixture
def montaje(entorno):
    def _montar(*, fiable: bool = True, activo: bool = True,
                con_publisher: bool = True, proveedor=None):
        fabrica = FabricaSesionSqlite()
        ids = sembrar_dias(fabrica, [{"fecha": DIA, "horas": 8.0},
                                     {"fecha": DIA, "horas": 2.0,
                                      "tipo": "extra"}])
        if proveedor is None:
            proveedor = ProveedorFake(por_dni={"12345678Z": set()},
                                      fiable=fiable)
            proveedor.activo = activo
        sv5 = TransferClientFake(ids)
        publisher = PublisherFake() if con_publisher else None
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        calendario_provider=proveedor)
        return TestClient(app), fabrica, ids, sv5, publisher, proveedor
    return _montar


# ------------------- R25 / F-032 R24 · lo ya marcado --------------------- #

def test_f003_r25_la_marca_se_ve_en_las_vistas(montaje) -> None:
    """De nada sirve marcar si no se ve: badge en las dos vistas. Desde
    F-032 nada nuevo se marca; la linea llega ya marcada."""
    cliente, fabrica, ids, _sv5, _p, _prov = montaje(fiable=False)
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            reg.sigrid_estado = "registrado"
            reg.sigrid_motivo = ("[SIN-SESAME] registrado con override: "
                                 "calendario de Sesame no disponible")
        s.commit()
    trabajador = cliente.get("/trabajadores/rec-501?modo=natural").text
    obra = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "badge-sin-sesame" in trabajador
    assert "badge-sin-sesame" in obra


def test_f003_r25_una_linea_normal_no_lleva_badge(montaje) -> None:
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=True)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    assert "badge-sin-sesame" not in cliente.get(
        "/trabajadores/rec-501?modo=natural").text

# ---------------------- R27 · con Sesame apagado, nada ------------------ #

def test_f003_r27_sin_sesame_configurado_no_hay_bloqueo(montaje) -> None:
    """El proveedor REAL sin cliente: `fiable_para` siempre dice True."""
    from application.services.calendario_provider import CalendarioProvider

    proveedor = CalendarioProvider(cliente=None,
                                   respaldo_holiday_name=lambda _d: None)
    cliente, _f, ids, sv5, publisher, _prov = montaje(proveedor=proveedor)
    assert cliente.post("/api/aprobar/preflight",
                        json={"registro_ids": ids}).json().get(
                            "sesame_bloqueo") is None
    assert cliente.post("/api/aprobar/ejecutar",
                        json={"registro_ids": ids}).status_code == 200
    assert len(sv5.ejecutadas) == 1


def test_f003_r27_sin_sesame_la_cola_sigue_funcionando(montaje) -> None:
    from application.services.calendario_provider import CalendarioProvider

    proveedor = CalendarioProvider(cliente=None,
                                   respaldo_holiday_name=lambda _d: None)
    cliente, _f, ids, _sv5, publisher, _prov = montaje(proveedor=proveedor)
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 200
    assert len(publisher.publicadas) == 1


def test_f003_r27_sin_sesame_las_lineas_no_se_marcan(montaje) -> None:
    from application.services.calendario_provider import CalendarioProvider

    proveedor = CalendarioProvider(cliente=None,
                                   respaldo_holiday_name=lambda _d: None)
    cliente, fabrica, ids, _sv5, _p, _prov = montaje(proveedor=proveedor)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    for rid in ids:
        assert estados_sigrid(fabrica, ids)[rid][1] is None
