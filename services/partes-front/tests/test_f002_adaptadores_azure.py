# tests/test_f002_adaptadores_azure.py
"""F-002 · adaptadores de Storage del portal (sv4). Sin red.

sv4 lleva los suyos, como sv1, sv2, sv3 y sv5: la arquitectura no tiene
libreria compartida y los servicios se acoplan solo por mensajes. Lo que
se comprueba aqui es que esta copia se comporta igual que las demas.
"""
from __future__ import annotations

import json

import pytest
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from tests.dobles import (
    BlobServiceClientFake,
    QueueServiceClientFake,
    mensaje_json,
    parchear_blobs,
    parchear_colas,
)


def _cola(monkeypatch, **kwargs):
    svc = QueueServiceClientFake()
    parchear_colas(monkeypatch, mod_cola, svc)
    return ColaCliente(connection_string="UseDevelopmentStorage=true",
                       poll_interval_s=0, **kwargs), svc


def test_f002_r1_enviar_publica_json(monkeypatch):
    cli, svc = _cola(monkeypatch)
    cli.enviar("q-transfer", {"peticion_id": "abc",
                              "blob": "peticiones/abc.json"})
    assert svc.get_queue_client("q-transfer").payloads_enviados == [
        {"peticion_id": "abc", "blob": "peticiones/abc.json"}]


def test_f002_r12_consumir_entrega_el_payload_y_borra(monkeypatch):
    cli, svc = _cola(monkeypatch)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer-result", vistos.append)

    assert vistos == [{"peticion_id": "p1"}]
    assert cola.borrados == ["m1"]


def test_f002_r9_supera_max_dequeue_va_a_poison(monkeypatch):
    cli, svc = _cola(monkeypatch, max_dequeue=2)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, dequeue_count=3,
                                 id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer-result", vistos.append)

    assert vistos == []
    poison = svc.get_queue_client("q-transfer-result-poison")
    assert [json.loads(c) for c in poison.enviados] == [{"peticion_id": "p1"}]


def test_f002_r13_fallo_del_handler_no_borra_el_mensaje(monkeypatch):
    """Si el marcado falla, el mensaje reaparece y se reintenta."""
    cli, svc = _cola(monkeypatch)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]
    cola.on_agotado = cli.detener

    def _handler(_p):
        raise RuntimeError("PostgreSQL caido")

    cli.consumir("q-transfer-result", _handler)

    assert cola.borrados == []


def test_f002_cola_cliente_exige_configuracion():
    with pytest.raises(ValueError):
        ColaCliente()


def test_f002_r1_blob_sube_y_descarga(monkeypatch):
    svc = BlobServiceClientFake()
    parchear_blobs(monkeypatch, mod_blob, svc)
    cli = BlobCliente(connection_string="UseDevelopmentStorage=true")
    cli.asegurar_contenedores(["transfer"])
    cli.subir("transfer", "peticiones/p1.json", b'{"a": 1}',
              content_type="application/json")
    assert svc.contenedores == ["transfer"]
    assert cli.descargar("transfer", "peticiones/p1.json") == b'{"a": 1}'


def test_f002_blob_cliente_exige_configuracion():
    with pytest.raises(ValueError):
        BlobCliente()
