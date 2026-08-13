# tests/test_f002_resultado_consumer.py
"""F-002 · consumidor de `q-transfer-result` en el portal (R12, R13, R14).

Cierra el lazo de la aprobacion asincrona: sv5 publica el veredicto y
este hilo lo vuelca en las columnas `sigrid_*`. Adaptadores reales de
Storage sobre fakes del SDK y repositorio real sobre SQLite en memoria.
"""
from __future__ import annotations

import json
import threading

import pytest
from azure.core.exceptions import ResourceNotFoundError

from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.workers.resultado_consumer import (
    arrancar_consumidor_resultados,
    construir_handler_resultados,
)
from tests.dobles import (
    BlobServiceClientFake,
    FabricaSesionSqlite,
    QueueServiceClientFake,
    estados_sigrid,
    mensaje_json,
    parchear_blobs,
    parchear_colas,
    sembrar_registros,
)

PETICION_ID = "aaaa1111-bbbb-2222-cccc-333344445555"


class SettingsFake:
    blob_transfer = "transfer"
    cola_transfer = "q-transfer"
    cola_transfer_result = "q-transfer-result"
    default_reviewer = "ana"


class Montaje:
    def __init__(self, monkeypatch, *, cantidad: int = 3):
        self.svc_cola = parchear_colas(monkeypatch, mod_cola,
                                       QueueServiceClientFake())
        parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
        self.blob = BlobCliente(connection_string="UseDevelopmentStorage=true")
        self.cola = ColaCliente(connection_string="UseDevelopmentStorage=true",
                                poll_interval_s=0)
        self.settings = SettingsFake()
        self.fabrica = FabricaSesionSqlite()
        self.ids = sembrar_registros(self.fabrica, cantidad=cantidad)
        self.repositorio = ParteReviewRepository(self.fabrica)
        self.repositorio.marcar_registros_encolado(self.ids, usuario="ana")
        self.handler = construir_handler_resultados(
            repository=self.repositorio, blob=self.blob,
            settings=self.settings)

    def publicar_resultado(self, resultado: dict,
                           registro_ids: list[int] | None = None) -> dict:
        sobre = {"peticion_id": PETICION_ID, "usuario": "ana",
                 "procesado_at_utc": "2026-08-13T11:00:00+00:00",
                 "registro_ids": registro_ids if registro_ids is not None
                 else self.ids,
                 "resultado": resultado}
        self.blob.subir("transfer", f"resultados/{PETICION_ID}.json",
                        json.dumps(sobre).encode("utf-8"))
        return {"peticion_id": PETICION_ID,
                "blob": f"resultados/{PETICION_ID}.json"}

    def estados(self):
        return estados_sigrid(self.fabrica, self.ids)


def test_f002_r12_el_consumidor_vuelca_el_veredicto_en_las_columnas(monkeypatch):
    """R12: escritas, omitidas y conflictos, cada linea a su estado."""
    m = Montaje(monkeypatch)
    mensaje = m.publicar_resultado({
        "ok": True,
        "escritas": [{"registro_id": m.ids[0], "hmoide": 901,
                      "hmores_ide": 5001, "parte_cod": "PT26/00001"}],
        "omitidas": [{"registro_id": m.ids[1], "motivo": "sin codigo"}],
        "ya_registradas": [],
        "pendientes_confirmacion": [{"clave": "501|20260302|1",
                                     "registros": [m.ids[2]],
                                     "parte_cod": "PT26/00001"}],
    })

    m.handler(mensaje)

    estados = m.estados()
    assert estados[m.ids[0]] == ("registrado", None, 901, 5001, "PT26/00001")
    assert estados[m.ids[1]][0] == "omitido"
    assert estados[m.ids[2]][0] == "conflicto"
    # Ninguna se queda colgada en 'encolado'.
    assert all(e[0] != "encolado" for e in estados.values())


def test_f002_r12_ya_registradas_salen_de_encolado(monkeypatch):
    m = Montaje(monkeypatch, cantidad=2)
    mensaje = m.publicar_resultado({"ok": True, "escritas": [], "omitidas": [],
                                    "ya_registradas": m.ids})

    m.handler(mensaje)

    assert all(e[0] == "registrado" for e in m.estados().values())


def test_f002_r13_procesar_el_mismo_mensaje_dos_veces_no_cambia_nada(monkeypatch):
    """R13: la reentrega at-least-once deja exactamente el mismo estado."""
    m = Montaje(monkeypatch)
    mensaje = m.publicar_resultado({
        "ok": True,
        "escritas": [{"registro_id": m.ids[0], "hmoide": 901,
                      "hmores_ide": 5001, "parte_cod": "PT26/00001"}],
        "omitidas": [{"registro_id": m.ids[1], "motivo": "sin codigo"}],
        "ya_registradas": [m.ids[2]],
    })

    m.handler(mensaje)
    primera = m.estados()
    m.handler(mensaje)

    assert m.estados() == primera


def test_f002_r14_resultado_fallido_deja_la_peticion_en_error(monkeypatch):
    """R14: con ok=false toda la peticion queda en 'error' con motivo."""
    m = Montaje(monkeypatch)
    mensaje = m.publicar_resultado(
        {"ok": False, "error": "sigrid-api devolvio 500", "escritas": []})

    m.handler(mensaje)

    for estado, motivo, *_ in m.estados().values():
        assert estado == "error"
        assert "sigrid-api devolvio 500" in motivo


def test_f002_r14_sin_registro_ids_no_puede_marcar_error(monkeypatch):
    """Sin la lista de lineas no hay nada que marcar; no se inventa."""
    m = Montaje(monkeypatch)
    mensaje = m.publicar_resultado({"ok": False, "error": "fallo"},
                                   registro_ids=[])

    m.handler(mensaje)

    assert all(e[0] == "encolado" for e in m.estados().values())


def test_f002_r9_blob_de_resultado_inaccesible_relanza(monkeypatch):
    """Fallo de infraestructura: el mensaje NO se borra y se reintenta."""
    m = Montaje(monkeypatch)
    with pytest.raises(ResourceNotFoundError):
        m.handler({"peticion_id": PETICION_ID,
                   "blob": f"resultados/{PETICION_ID}.json"})
    assert all(e[0] == "encolado" for e in m.estados().values())


def test_f002_r9_mensaje_sin_referencia_de_blob_relanza(monkeypatch):
    m = Montaje(monkeypatch)
    with pytest.raises(ValueError, match="sin referencia de blob"):
        m.handler({"peticion_id": PETICION_ID})


def test_f002_r12_el_consumidor_se_engancha_a_la_cola_de_resultados(monkeypatch):
    """El bucle real consume `q-transfer-result` y borra lo procesado."""
    m = Montaje(monkeypatch, cantidad=1)
    mensaje = m.publicar_resultado(
        {"ok": True, "escritas": [{"registro_id": m.ids[0], "hmoide": 901,
                                   "parte_cod": "PT26/00001"}],
         "omitidas": [], "ya_registradas": []})
    cola_fake = m.svc_cola.get_queue_client("q-transfer-result")
    cola_fake.rondas = [[mensaje_json(mensaje, id="m1")]]
    cola_fake.on_agotado = m.cola.detener

    hilo = arrancar_consumidor_resultados(
        repository=m.repositorio, cola=m.cola, blob=m.blob,
        settings=m.settings)
    hilo.join(10)

    assert isinstance(hilo, threading.Thread)
    assert hilo.daemon is True
    assert cola_fake.borrados == ["m1"]
    assert m.estados()[m.ids[0]][0] == "registrado"
