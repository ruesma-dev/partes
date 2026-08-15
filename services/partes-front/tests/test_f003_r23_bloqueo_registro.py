# tests/test_f003_r23_bloqueo_registro.py
"""R23-R25, R27 · nivel 2: sin Sesame disponible NO se registra.

Es la correccion del humano al fail-open original. En las vistas basta
con avisar (nivel 1), pero el REGISTRO en Sigrid escribe horas: sin los
festivos reales el computo puede estar mal, y dejarlo pasar con un
WARNING que no mira nadie es peor que parar.

Con el bloqueo hay una unica salida, consciente y marcada: el override
manual del modal, que va por la via SINCRONA (`/ejecutar`) —una decision
humana no viaja por una cola con reentregas, mismo argumento que
`pisar_claves` en F-002— y deja las lineas marcadas `[SIN-SESAME]`.

Con Sesame sin configurar, nada de esto existe (R27).
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
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


# --------------------------- R23 · el preflight ------------------------- #

def test_f003_r23_el_preflight_anexa_el_bloqueo(montaje) -> None:
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=False)
    datos = cliente.post("/api/aprobar/preflight",
                         json={"registro_ids": ids}).json()
    assert datos["sesame_bloqueo"]
    assert "Sesame no disponible" in datos["sesame_bloqueo"]
    assert "incorrecto" in datos["sesame_bloqueo"]


def test_f003_r23_sin_degradacion_no_hay_bloqueo(montaje) -> None:
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=True)
    datos = cliente.post("/api/aprobar/preflight",
                         json={"registro_ids": ids}).json()
    assert datos.get("sesame_bloqueo") is None


def test_f003_r23_el_preflight_se_sirve_igual(montaje) -> None:
    """Bloquear el registro no es tumbar el preflight: el humano tiene
    que poder ver que se iba a registrar antes de decidir."""
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=False)
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["escribir"] == 2


def test_f003_r23_la_fiabilidad_se_pregunta_por_dni_y_ano(montaje) -> None:
    cliente, _f, ids, _sv5, _p, proveedor = montaje(fiable=True)
    cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    consultas = [c for c in proveedor.consultas if c[0] == "fiable_para"]
    assert ("12345678Z", 2026) in consultas[-1][1]


# ------------------- R24 · la guarda esta en el servidor ---------------- #

def test_f003_r24_ejecutar_sin_override_da_422(montaje) -> None:
    cliente, _f, ids, sv5, _p, _prov = montaje(fiable=False)
    r = cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    assert r.status_code == 422
    # El JS mira `ok` antes que el status: si viniera true, el modal
    # cantaria victoria sobre un registro que no se ha hecho.
    assert r.json()["ok"] is False
    assert "Sesame no disponible" in r.json()["error"]
    assert sv5.ejecutadas == []      # ni se ha llamado a sv5


def test_f003_r24_encolar_sin_override_da_422(montaje) -> None:
    cliente, _f, ids, _sv5, publisher, _prov = montaje(fiable=False)
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert publisher.publicadas == []


def test_f003_r24_el_bloqueo_no_depende_del_modal(montaje) -> None:
    """Una peticion a pelo, sin pasar por el preflight, tambien se para."""
    cliente, _f, ids, sv5, _p, _prov = montaje(fiable=False)
    assert cliente.post("/api/aprobar/ejecutar",
                        json={"registro_ids": ids}).status_code == 422
    assert sv5.ejecutadas == []


def test_f003_r24_sin_degradacion_el_registro_procede(montaje) -> None:
    cliente, _f, ids, sv5, _p, _prov = montaje(fiable=True)
    assert cliente.post("/api/aprobar/ejecutar",
                        json={"registro_ids": ids}).status_code == 200
    assert len(sv5.ejecutadas) == 1


# ----------------------------- R25 · override --------------------------- #

def test_f003_r25_con_override_ejecutar_procede(montaje) -> None:
    cliente, _f, ids, sv5, _p, _prov = montaje(fiable=False)
    r = cliente.post("/api/aprobar/ejecutar",
                     json={"registro_ids": ids, "forzar_sin_sesame": True})
    assert r.status_code == 200
    assert len(sv5.ejecutadas) == 1


def test_f003_r25_el_override_marca_las_lineas(montaje) -> None:
    cliente, fabrica, ids, _sv5, _p, _prov = montaje(fiable=False)
    cliente.post("/api/aprobar/ejecutar",
                 json={"registro_ids": ids, "forzar_sin_sesame": True})
    estados = estados_sigrid(fabrica, ids)
    for rid in ids:
        estado, motivo, *_ = estados[rid]
        assert estado == "registrado"
        assert motivo.startswith("[SIN-SESAME]")


def test_f003_r25_sin_override_las_lineas_ok_no_llevan_motivo(
        montaje) -> None:
    cliente, fabrica, ids, _sv5, _p, _prov = montaje(fiable=True)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    for rid in ids:
        assert estados_sigrid(fabrica, ids)[rid][1] is None


def test_f003_r25_el_override_no_vale_por_la_cola(montaje) -> None:
    """Una decision humana no viaja por una cola con reentregas."""
    cliente, _f, ids, _sv5, publisher, _prov = montaje(fiable=False)
    r = cliente.post("/api/aprobar/encolar",
                     json={"registro_ids": ids, "forzar_sin_sesame": True})
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert "ejecutar" in r.json()["error"]
    assert publisher.publicadas == []


def test_f003_r25_la_cola_sin_publisher_tampoco_marca_de_mas(
        montaje) -> None:
    """`/encolar` sin colas configuradas degrada al registro sincrono y
    traza el resultado. Ese camino NO pasa por el override: sus lineas no
    pueden salir marcadas."""
    cliente, fabrica, ids, sv5, _p, _prov = montaje(
        fiable=True, con_publisher=False)
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["modo"] == "sincrono"
    for rid in ids:
        assert estados_sigrid(fabrica, ids)[rid][1] is None


def test_f003_r25_una_linea_ya_registrada_tambien_se_marca(
        montaje) -> None:
    """sv5 puede devolver una linea como `ya_registradas` (idempotencia
    por synckey). Se registro igual con el calendario a ciegas: lleva la
    misma marca que las escritas."""
    cliente, fabrica, ids, sv5, _p, _prov = montaje(fiable=False)

    def ejecutar(payload: dict) -> dict:
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": [l["registro_id"]
                                   for l in payload["lineas"]]}

    sv5.ejecutar = ejecutar   # type: ignore[assignment]
    cliente.post("/api/aprobar/ejecutar",
                 json={"registro_ids": ids, "forzar_sin_sesame": True})
    for rid in ids:
        estado, motivo, *_ = estados_sigrid(fabrica, ids)[rid]
        assert estado == "registrado"
        assert motivo.startswith("[SIN-SESAME]")


def test_f003_r25_el_override_sin_degradacion_no_marca_nada(montaje) -> None:
    """Mandar el flag cuando no hace falta no ensucia la traza."""
    cliente, fabrica, ids, _sv5, _p, _prov = montaje(fiable=True)
    cliente.post("/api/aprobar/ejecutar",
                 json={"registro_ids": ids, "forzar_sin_sesame": True})
    for rid in ids:
        assert estados_sigrid(fabrica, ids)[rid][1] is None


def test_f003_r25_el_payload_a_sv5_no_cambia(montaje) -> None:
    """sv5 no sabe nada de Sesame y no tiene por que enterarse."""
    cliente, _f, ids, sv5, _p, _prov = montaje(fiable=False)
    cliente.post("/api/aprobar/ejecutar",
                 json={"registro_ids": ids, "forzar_sin_sesame": True})
    assert set(sv5.ejecutadas[0]) == {"obra", "lineas", "pisar_claves",
                                      "usuario"}


def test_f003_r25_la_marca_se_ve_en_las_vistas(montaje) -> None:
    """De nada sirve marcar si no se ve: badge en las dos vistas."""
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=False)
    cliente.post("/api/aprobar/ejecutar",
                 json={"registro_ids": ids, "forzar_sin_sesame": True})
    trabajador = cliente.get("/trabajadores/emp-77?modo=natural").text
    obra = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "badge-sin-sesame" in trabajador
    assert "badge-sin-sesame" in obra


def test_f003_r25_una_linea_normal_no_lleva_badge(montaje) -> None:
    cliente, _f, ids, _sv5, _p, _prov = montaje(fiable=True)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    assert "badge-sin-sesame" not in cliente.get(
        "/trabajadores/emp-77?modo=natural").text


def test_f003_r25_la_marca_cabe_en_el_campo(montaje) -> None:
    """`sigrid_motivo` es String(255): sin schema nuevo."""
    from infrastructure.transfer.resultado_sigrid import MOTIVO_SIN_SESAME
    assert len(MOTIVO_SIN_SESAME) <= 255


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
