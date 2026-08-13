# tests/test_f002_poison.py
"""F-002 · gestion de las colas `-poison` desde el portal (R23-R26).

Un mensaje que agota sus reintentos acaba en `q-transfer-poison` y hoy
solo se ve entrando en Azure. La ampliacion lo saca al portal: recuento
en la cabecera y reencolado manual acotado.

Sin red: adaptador real de cola sobre el fake del SDK.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.cola_cliente import ColaCliente
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import (
    FabricaSesionSqlite,
    QueueServiceClientFake,
    mensaje_json,
    parchear_colas,
)


@pytest.fixture
def cola(monkeypatch):
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    cli = ColaCliente(connection_string="UseDevelopmentStorage=true",
                      poll_interval_s=0)
    return cli, svc


def _llenar(svc, nombre: str, cuantos: int) -> None:
    q = svc.get_queue_client(nombre)
    q.rondas = [[mensaje_json({"peticion_id": f"p{i}"}, id=f"m{i}")]
                for i in range(cuantos)]
    q.mensajes_aprox = cuantos


# --------------------------- adaptador de cola -------------------------- #

def test_f002_r23_cuenta_los_mensajes_aproximados(cola):
    cli, svc = cola
    svc.get_queue_client("q-transfer-poison").mensajes_aprox = 7
    assert cli.contar_aproximado("q-transfer-poison") == 7


def test_f002_r24_mueve_los_mensajes_a_la_cola_principal(cola):
    cli, svc = cola
    _llenar(svc, "q-transfer-poison", 3)

    movidos = cli.mover("q-transfer-poison", "q-transfer")

    assert len(movidos) == 3
    principal = svc.get_queue_client("q-transfer")
    assert [m["peticion_id"] for m in principal.payloads_enviados] \
        == ["p0", "p1", "p2"]
    assert svc.get_queue_client("q-transfer-poison").borrados \
        == ["m0", "m1", "m2"]


def test_f002_r24_no_mueve_mas_del_tope(cola):
    """R24: como mucho 32 por pasada; repetir la accion es seguro."""
    cli, svc = cola
    _llenar(svc, "q-transfer-poison", 40)

    movidos = cli.mover("q-transfer-poison", "q-transfer", maximo=32)

    assert len(movidos) == 32
    assert len(svc.get_queue_client("q-transfer").enviados) == 32


def test_f002_r24_una_poison_vacia_no_mueve_nada(cola):
    cli, svc = cola
    assert cli.mover("q-transfer-poison", "q-transfer") == []
    assert svc.get_queue_client("q-transfer").enviados == []


def test_f002_r25_el_mensaje_se_borra_SOLO_tras_encolarlo(cola):
    """R25: si falla el borrado, el mensaje se duplica pero NO se pierde."""
    cli, svc = cola
    _llenar(svc, "q-transfer-poison", 1)
    svc.get_queue_client("q-transfer-poison").fallo_delete = True

    movidos = cli.mover("q-transfer-poison", "q-transfer")

    # Esta en la principal (no se ha perdido)...
    assert [m["peticion_id"] for m in
            svc.get_queue_client("q-transfer").payloads_enviados] == ["p0"]
    # ...y sigue en la poison: duplicado benigno, idempotente por synckey.
    assert svc.get_queue_client("q-transfer-poison").borrados == []
    assert movidos == ["m0"]


def test_f002_r25_si_falla_el_encolado_no_se_borra_de_la_poison(cola):
    """El orden inverso perderia el mensaje: eso no puede pasar."""
    cli, svc = cola
    _llenar(svc, "q-transfer-poison", 1)
    svc.get_queue_client("q-transfer").fallo_send = True

    movidos = cli.mover("q-transfer-poison", "q-transfer")

    assert movidos == []
    assert svc.get_queue_client("q-transfer-poison").borrados == []


# ------------------------------- endpoints ------------------------------ #

def _settings() -> Settings:
    """Sin leer el `.env` del desarrollador (ver test_f002_aprobar_encolar)."""
    return Settings(_env_file=None)


@pytest.fixture
def cliente(monkeypatch, cola):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    cli, svc = cola

    def _montar(*, con_cola: bool = True):
        repositorio = ParteReviewRepository(FabricaSesionSqlite())
        app = build_app(_settings(), repository=repositorio,
                        transfer_client=None, publisher=None,
                        cola_cliente=cli if con_cola else None)
        return TestClient(app), svc
    return _montar


def test_f002_r23_el_portal_informa_del_recuento_por_cola(cliente):
    http, svc = cliente()
    svc.get_queue_client("q-transfer-poison").mensajes_aprox = 3
    svc.get_queue_client("q-transfer-result-poison").mensajes_aprox = 1

    r = http.get("/api/admin/poison")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["habilitado"] is True
    assert cuerpo["colas"] == [
        {"cola": "q-transfer-poison", "principal": "q-transfer",
         "mensajes_aprox": 3},
        {"cola": "q-transfer-result-poison", "principal": "q-transfer-result",
         "mensajes_aprox": 1},
    ]


def test_f002_r26_sin_colas_configuradas_el_endpoint_lo_dice(cliente):
    """R26: sin colas no hay aviso que mostrar ni accion que ofrecer."""
    http, _svc = cliente(con_cola=False)
    r = http.get("/api/admin/poison")
    assert r.status_code == 200
    assert r.json() == {"habilitado": False}


def test_f002_r26_sin_colas_reencolar_responde_409(cliente):
    http, _svc = cliente(con_cola=False)
    r = http.post("/api/admin/poison/reencolar", json={"cola": "q-transfer"})
    assert r.status_code == 409
    assert r.json()["ok"] is False


def test_f002_r24_reencolar_desde_el_portal(cliente):
    http, svc = cliente()
    _llenar(svc, "q-transfer-poison", 5)

    r = http.post("/api/admin/poison/reencolar", json={"cola": "q-transfer"})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert cuerpo["movidos"] == 5
    assert "restantes_aprox" in cuerpo
    assert len(svc.get_queue_client("q-transfer").enviados) == 5


def test_f002_r24_reencolar_respeta_el_tope_de_32(cliente):
    http, svc = cliente()
    _llenar(svc, "q-transfer-poison", 50)

    cuerpo = http.post("/api/admin/poison/reencolar",
                       json={"cola": "q-transfer"}).json()

    assert cuerpo["movidos"] == 32


@pytest.mark.parametrize("cola_pedida", ["q-otra-cosa", "", "q-transfer-poison",
                                         "../q-transfer"])
def test_f002_r24_solo_se_admiten_las_dos_colas_de_la_allowlist(cliente,
                                                                cola_pedida):
    """El nombre de cola NUNCA sale del cliente: allowlist cerrada."""
    http, svc = cliente()
    r = http.post("/api/admin/poison/reencolar", json={"cola": cola_pedida})
    assert r.status_code == 422
    assert svc.get_queue_client("q-transfer").enviados == []


def test_f002_r24_la_cola_de_resultados_tambien_se_puede_reencolar(cliente):
    http, svc = cliente()
    _llenar(svc, "q-transfer-result-poison", 2)

    cuerpo = http.post("/api/admin/poison/reencolar",
                       json={"cola": "q-transfer-result"}).json()

    assert cuerpo["movidos"] == 2
    assert len(svc.get_queue_client("q-transfer-result").enviados) == 2


def test_f002_r23_un_fallo_de_storage_no_rompe_la_pagina(cliente,
                                                         monkeypatch):
    """El aviso es accesorio: si Storage no responde, la pagina sigue."""
    http, _svc = cliente()

    def _revienta(_nombre):
        raise RuntimeError("storage caido")

    monkeypatch.setattr(mod_cola.ColaCliente, "contar_aproximado",
                        lambda self, nombre: _revienta(nombre))

    r = http.get("/api/admin/poison")

    assert r.status_code == 200
    assert r.json()["habilitado"] is True
    assert all(c["mensajes_aprox"] is None for c in r.json()["colas"])
