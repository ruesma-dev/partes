# tests/test_f002_transfer_consumer.py
"""F-002 · handler de `q-transfer` en sv5 (R6, R7, R9, R10, R14).

Se ejercitan los adaptadores REALES de cola y blob con el SDK de Azure
sustituido por dobles en memoria: nada sale del proceso.
"""
from __future__ import annotations

import json

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from azure.core.exceptions import ResourceNotFoundError
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from interface_adapters.queue.transfer_consumer import (
    construir_handler_transfer,
)
from tests.dobles import (
    BlobServiceClientFake,
    QueueServiceClientFake,
    SettingsFake,
    parchear_blobs,
    parchear_colas,
)
from tests.test_f002_pipeline_fases import _sigrid

PETICION_ID = "11111111-2222-3333-4444-555555555555"


def _peticion(*, lineas=None, pisar_claves=None) -> dict:
    return {
        "peticion_id": PETICION_ID,
        "usuario": "ana",
        "creado_at_utc": "2026-08-13T10:00:00+00:00",
        "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
        "lineas": lineas if lineas is not None else [
            {"registro_id": 1, "fecha_int": 20260302, "recurso_ide": 501,
             "tipo_hora": "normal", "horas": 8.0},
            {"registro_id": 2, "fecha_int": 20260302, "recurso_ide": 501,
             "tipo_hora": "extra", "horas": 2.0},
        ],
        "pisar_claves": pisar_claves or [],
    }


class Montaje:
    """Handler cableado con los adaptadores reales sobre fakes del SDK."""

    def __init__(self, monkeypatch, cli_sigrid, *, peticion=None,
                 subir=True):
        self.svc_cola = parchear_colas(monkeypatch, mod_cola,
                                       QueueServiceClientFake())
        self.svc_blob = parchear_blobs(monkeypatch, mod_blob,
                                       BlobServiceClientFake())
        self.blob = BlobCliente(connection_string="UseDevelopmentStorage=true")
        self.cola = ColaCliente(connection_string="UseDevelopmentStorage=true",
                                poll_interval_s=0)
        self.settings = SettingsFake()
        self.sigrid = cli_sigrid
        self.pipeline = RegistroPipeline(cliente=cli_sigrid,
                                         settings=self.settings)
        self.handler = construir_handler_transfer(
            pipeline=self.pipeline, blob=self.blob, cola=self.cola,
            settings=self.settings)
        if subir:
            self.blob.subir(
                "transfer", f"peticiones/{PETICION_ID}.json",
                json.dumps(peticion or _peticion()).encode("utf-8"))

    @property
    def mensaje(self) -> dict:
        return {"peticion_id": PETICION_ID,
                "blob": f"peticiones/{PETICION_ID}.json"}

    @property
    def mensajes_resultado(self) -> list[dict]:
        return self.svc_cola.get_queue_client(
            "q-transfer-result").payloads_enviados

    def resultado_publicado(self) -> dict:
        datos = self.blob.descargar("transfer",
                                    f"resultados/{PETICION_ID}.json")
        return json.loads(datos.decode("utf-8"))


def test_f002_r6_procesa_la_peticion_y_publica_el_resultado(monkeypatch):
    """R6: blob de peticion -> pipeline -> blob + mensaje de resultado."""
    m = Montaje(monkeypatch, _sigrid())

    m.handler(m.mensaje)

    # Escribio en Sigrid lo que tocaba.
    assert len(m.sigrid.lineas) == 2
    # Mensaje de resultado con la REFERENCIA al blob (no el payload).
    assert m.mensajes_resultado == [
        {"peticion_id": PETICION_ID,
         "blob": f"resultados/{PETICION_ID}.json"}]
    sobre = m.resultado_publicado()
    assert sobre["peticion_id"] == PETICION_ID
    assert sobre["usuario"] == "ana"
    assert sobre["procesado_at_utc"]
    assert sobre["registro_ids"] == [1, 2]
    r = sobre["resultado"]
    assert r["ok"] is True
    assert [e["registro_id"] for e in r["escritas"]] == [1, 2]
    assert r["omitidas"] == [] and r["ya_registradas"] == []
    assert r["pendientes_confirmacion"] == []


def test_f002_r7_la_escritura_del_handler_va_bajo_el_lock(monkeypatch):
    """R7: el consumidor no escribe fuera del lock del pipeline."""
    cli = _sigrid()
    m = Montaje(monkeypatch, cli)
    cli.vigilar_lock(m.pipeline.lock)

    m.handler(m.mensaje)

    assert len(cli.lineas) == 2


def test_f002_r10_conflictos_no_se_pisan_desde_la_cola(monkeypatch):
    """R10: la linea en conflicto NO se escribe; vuelve como pendiente."""
    cli = _sigrid()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4000, "hmoide": 700, "reside": 501,
                       "fec": 20260302, "horide": 1, "hora_codigo": "HL01",
                       "can": 5.0, "tot": 50.0, "pos": 64, "synckey": None})
    m = Montaje(monkeypatch, cli)

    m.handler(m.mensaje)

    r = m.resultado_publicado()["resultado"]
    assert r["ok"] is True
    assert [e["registro_id"] for e in r["escritas"]] == [2]   # la extra si
    pendientes = r["pendientes_confirmacion"]
    assert [c["clave"] for c in pendientes] == ["501|20260302|1"]
    assert [c["registros"] for c in pendientes] == [[1]]
    # La linea que ya estaba en Sigrid sigue ahi: no se piso nada.
    assert any(l["ide"] == 4000 for l in cli.lineas)


def test_f002_r10_pisar_claves_del_blob_se_ignora(monkeypatch):
    """R10: pisar es humano y sincrono; la cola nunca borra lineas."""
    cli = _sigrid()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4000, "hmoide": 700, "reside": 501,
                       "fec": 20260302, "horide": 1, "hora_codigo": "HL01",
                       "can": 5.0, "tot": 50.0, "pos": 64, "synckey": None})
    m = Montaje(monkeypatch, cli,
                peticion=_peticion(pisar_claves=["501|20260302|1"]))

    m.handler(m.mensaje)

    r = m.resultado_publicado()["resultado"]
    assert r["pisadas"] == []
    assert r["borradas"] == 0
    assert any(l["ide"] == 4000 for l in cli.lineas)
    assert [c["clave"] for c in r["pendientes_confirmacion"]] \
        == ["501|20260302|1"]


def test_f002_r14_fallo_del_pipeline_publica_ok_false_y_consume(monkeypatch):
    """R14: el error global viaja a sv4 y el mensaje NO se reintenta."""
    cli = _sigrid()
    cli.obras = {}                       # la obra no existe en Sigrid
    m = Montaje(monkeypatch, cli)

    m.handler(m.mensaje)                 # NO relanza: el mensaje se borra

    sobre = m.resultado_publicado()
    assert sobre["registro_ids"] == [1, 2]
    r = sobre["resultado"]
    assert r["ok"] is False
    assert "obra no encontrada" in r["error"]
    assert r["escritas"] == []
    assert len(m.mensajes_resultado) == 1


def test_f002_r9_blob_inaccesible_relanza(monkeypatch):
    """R9: fallo de infraestructura -> el mensaje reaparece (y a poison).

    El resultado NO se publica: si se publicara un `ok=false`, sv4
    marcaria las lineas en 'error' por un problema pasajero de Storage.
    """
    m = Montaje(monkeypatch, _sigrid(), subir=False)

    with pytest.raises(ResourceNotFoundError):
        m.handler(m.mensaje)

    assert m.mensajes_resultado == []


def test_f002_r9_json_corrupto_relanza(monkeypatch):
    """R9: una peticion ilegible es fallo de infraestructura, no de negocio."""
    m = Montaje(monkeypatch, _sigrid(), subir=False)
    m.blob.subir("transfer", f"peticiones/{PETICION_ID}.json", b"{no es json")

    with pytest.raises(json.JSONDecodeError):
        m.handler(m.mensaje)

    assert m.mensajes_resultado == []


def test_f002_r9_mensaje_sin_referencia_de_blob_relanza(monkeypatch):
    m = Montaje(monkeypatch, _sigrid())
    with pytest.raises(ValueError, match="sin referencia de blob"):
        m.handler({"peticion_id": PETICION_ID})


def test_f002_r8_reentrega_no_duplica_lineas(monkeypatch):
    """R8: procesar dos veces el mismo mensaje no duplica en Sigrid."""
    cli = _sigrid()
    m = Montaje(monkeypatch, cli)

    m.handler(m.mensaje)
    m.handler(m.mensaje)

    assert len(cli.lineas) == 2
    r = m.resultado_publicado()["resultado"]
    assert r["escritas"] == []
    assert sorted(r["ya_registradas"]) == [1, 2]


def test_f002_r6_el_resultado_conserva_el_esquema_del_http(monkeypatch):
    """El JSON publicado es el MISMO que devuelve /api/registro/ejecutar."""
    m = Montaje(monkeypatch, _sigrid())
    m.handler(m.mensaje)
    r = m.resultado_publicado()["resultado"]
    assert set(r) >= {"ok", "obra_destino", "forzada_pruebas", "partes",
                      "escritas", "omitidas", "ya_registradas", "pisadas",
                      "borradas", "pendientes_confirmacion"}
