# tests/test_f002_cola_cliente.py
"""F-002 · adaptadores de Storage de sv5 (cola y blob). Sin red."""
from __future__ import annotations

import json

import pytest

from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from tests.dobles import (
    BlobServiceClientFake, QueueServiceClientFake, mensaje_json,
    parchear_blobs, parchear_colas,
)


def _cliente(monkeypatch, svc=None, **kwargs) -> tuple:
    svc = svc or QueueServiceClientFake()
    parchear_colas(monkeypatch, mod_cola, svc)
    cli = ColaCliente(connection_string="UseDevelopmentStorage=true",
                      poll_interval_s=0, **kwargs)
    return cli, svc


def test_f002_r6_enviar_publica_json_en_la_cola(monkeypatch):
    """R6: el mensaje viaja como JSON con la referencia al blob."""
    cli, svc = _cliente(monkeypatch)
    cli.enviar("q-transfer", {"peticion_id": "abc",
                              "blob": "peticiones/abc.json"})
    enviados = svc.get_queue_client("q-transfer").payloads_enviados
    assert enviados == [{"peticion_id": "abc",
                         "blob": "peticiones/abc.json"}]


def test_f002_r9_supera_max_dequeue_va_a_poison(monkeypatch):
    """R9: pasado `max_dequeue` el mensaje va a la '-poison' y NO al handler."""
    cli, svc = _cliente(monkeypatch, max_dequeue=3)
    principal = svc.get_queue_client("q-transfer")
    principal.rondas = [[mensaje_json({"peticion_id": "p1"},
                                      dequeue_count=4, id="m1")]]
    principal.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer", vistos.append)

    assert vistos == []                                   # nunca se proceso
    poison = svc.get_queue_client("q-transfer-poison")
    assert [json.loads(c) for c in poison.enviados] == [{"peticion_id": "p1"}]
    assert principal.borrados == ["m1"]                   # sale de la principal


def test_f002_r9_fallo_del_handler_no_borra_el_mensaje(monkeypatch):
    """R9: si el handler falla, el mensaje NO se borra (reaparece)."""
    cli, svc = _cliente(monkeypatch)
    principal = svc.get_queue_client("q-transfer")
    principal.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]
    principal.on_agotado = cli.detener

    def _handler(_payload):
        raise RuntimeError("sigrid caido")

    cli.consumir("q-transfer", _handler)

    assert principal.borrados == []
    assert svc.get_queue_client("q-transfer-poison").enviados == []


def test_f002_r6_handler_ok_borra_el_mensaje(monkeypatch):
    """El camino feliz: el handler recibe el payload y el mensaje se borra."""
    cli, svc = _cliente(monkeypatch)
    principal = svc.get_queue_client("q-transfer")
    principal.rondas = [[mensaje_json({"peticion_id": "p1",
                                       "blob": "peticiones/p1.json"}, id="m1")]]
    principal.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer", vistos.append)

    assert vistos == [{"peticion_id": "p1", "blob": "peticiones/p1.json"}]
    assert principal.borrados == ["m1"]


def test_f002_asegurar_colas_crea_principal_y_poison(monkeypatch):
    cli, svc = _cliente(monkeypatch)
    cli.asegurar_colas(["q-transfer", "q-transfer-result"])
    assert svc.creadas == ["q-transfer", "q-transfer-poison",
                           "q-transfer-result", "q-transfer-result-poison"]


def test_f002_cola_cliente_exige_configuracion():
    with pytest.raises(ValueError):
        ColaCliente()


def test_f002_r6_blob_sube_y_descarga(monkeypatch):
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
