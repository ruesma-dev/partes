# tests/test_f003_r18_preflight_festivos.py
"""R18 · el preflight de aprobacion avisa de las horas en festivo/domingo.

Informativo, no bloqueante: no cambia ni una linea de lo que se registra.
Sirve para que quien aprueba un mes entero vea, antes de darle al boton,
que hay horas imputadas en dias que no eran laborables — que puede ser
correcto (trabajo en festivo) o un error de fecha.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app

from tests.dobles import FabricaSesionSqlite, sembrar_dias
from tests.test_f003_r2_vistas_festivos import ProveedorFake

SAN_ISIDRO = "2026-05-15"   # viernes festivo para el DNI de Pepe
DOMINGO = "2026-05-17"
LUNES = "2026-05-18"


class TransferClientFake:
    def __init__(self) -> None:
        self.preflights: list[dict] = []

    def preflight(self, payload: dict) -> dict:
        self.preflights.append(payload)
        return {"ok": True, "conflictos": [], "escribir": len(
            payload.get("lineas") or [])}

    def ejecutar(self, payload: dict) -> dict:
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": []}


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _monta(entorno, dias, *, proveedor=None):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_dias(fabrica, dias)
    proveedor = proveedor or ProveedorFake(
        por_dni={"12345678Z": {SAN_ISIDRO}}, por_defecto=set())
    sv5 = TransferClientFake()
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=sv5, calendario_provider=proveedor)
    return TestClient(app), ids, sv5


def _preflight(cliente, ids) -> dict:
    return cliente.post("/api/aprobar/preflight",
                        json={"registro_ids": ids}).json()


# --------------------------- lo que se avisa ---------------------------- #

def test_f003_r18_avisa_de_las_horas_en_festivo(entorno) -> None:
    cliente, ids, _ = _monta(entorno, [
        {"fecha": SAN_ISIDRO, "horas": 8.0},
    ])
    avisos = _preflight(cliente, ids)["avisos_calendario"]
    assert len(avisos) == 1
    assert avisos[0]["fecha"] == SAN_ISIDRO
    assert avisos[0]["registro_id"] == ids[0]
    assert avisos[0]["tipo"] == "festivo"
    assert "Fiesta de prueba" in avisos[0]["motivo"]


def test_f003_r18_avisa_de_las_horas_en_domingo(entorno) -> None:
    cliente, ids, _ = _monta(entorno, [{"fecha": DOMINGO, "horas": 4.0}])
    avisos = _preflight(cliente, ids)["avisos_calendario"]
    assert [a["tipo"] for a in avisos] == ["domingo"]


def test_f003_r18_un_dia_laborable_no_genera_aviso(entorno) -> None:
    cliente, ids, _ = _monta(entorno, [{"fecha": LUNES, "horas": 8.0}])
    assert _preflight(cliente, ids)["avisos_calendario"] == []


def test_f003_r18_solo_las_lineas_con_horas(entorno) -> None:
    """Una linea a 0 h en festivo no le importa a nadie."""
    cliente, ids, _ = _monta(entorno, [
        {"fecha": SAN_ISIDRO, "horas": 0.0},
        {"fecha": SAN_ISIDRO, "horas": 3.0},
    ])
    avisos = _preflight(cliente, ids)["avisos_calendario"]
    assert [a["registro_id"] for a in avisos] == [ids[1]]


def test_f003_r18_un_aviso_por_linea_afectada(entorno) -> None:
    cliente, ids, _ = _monta(entorno, [
        {"fecha": SAN_ISIDRO, "horas": 8.0},
        {"fecha": DOMINGO, "horas": 5.0},
        {"fecha": LUNES, "horas": 8.0},
    ])
    avisos = _preflight(cliente, ids)["avisos_calendario"]
    assert sorted(a["fecha"] for a in avisos) == [SAN_ISIDRO, DOMINGO]


def test_f003_r18_el_festivo_se_evalua_con_el_dni_de_la_linea(
        entorno) -> None:
    """Ese dia solo es festivo para otro trabajador: no hay aviso."""
    proveedor = ProveedorFake(por_dni={"11111111A": {SAN_ISIDRO}},
                              por_defecto=set())
    cliente, ids, _ = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                             proveedor=proveedor)
    assert _preflight(cliente, ids)["avisos_calendario"] == []


# ------------------------- lo que NO cambia ----------------------------- #

def test_f003_r18_no_altera_el_payload_que_va_a_sv5(entorno) -> None:
    cliente, ids, sv5 = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}])
    _preflight(cliente, ids)
    enviado = sv5.preflights[0]
    assert set(enviado) == {"obra", "lineas", "pisar_claves", "usuario"}
    assert [l["registro_id"] for l in enviado["lineas"]] == ids


def test_f003_r18_respeta_la_respuesta_de_sv5(entorno) -> None:
    cliente, ids, _ = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}])
    datos = _preflight(cliente, ids)
    assert datos["ok"] is True
    assert datos["escribir"] == 1       # lo que dijo sv5, intacto


def test_f003_r18_es_informativo_no_bloquea(entorno) -> None:
    """Con avisos de festivo, el registro procede igual."""
    cliente, ids, _ = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}])
    r = cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["ok"] is True
