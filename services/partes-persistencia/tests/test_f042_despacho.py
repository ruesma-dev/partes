# tests/test_f042_despacho.py
"""F-042 · R12-R18: el worker de sv3 distingue ingesta y recalculo.

`q-persistencia` lleva desde F-042 dos clases de mensaje: el de sv2 (sin
`tipo`: un parte nuevo que ingerir) y el de sv4 (`tipo: "recalcular"`: la
fecha de un parte ha cambiado y hay que repetir la pasada de extras). El
handler que construye `construir_handler` decide cual es cada uno.

Todo con dobles: ni blobs, ni PostgreSQL, ni Sigrid. Datos sinteticos.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import pytest

from application.pipelines.persist_parte_pipeline import PersistParteRequest
from interface_adapters.workers.despacho import construir_handler
from interface_adapters.workers.mensajes import (
    CLASE_INGESTA,
    CLASE_RECALCULO,
    TIPO_RECALCULAR,
    MensajeDesconocido,
    clasificar,
)

ENVELOPE = {"data": {"obra": "0100"}, "meta": {"modelo": "doble"}}
PDF = b"%PDF-1.4 sintetico"


# ------------------------------- dobles -------------------------------- #

class BlobFake:
    """`descargar(contenedor, nombre)` sobre un dict; apunta cada llamada."""

    def __init__(self, ficheros: dict[tuple[str, str], bytes] | None = None):
        self.ficheros = ficheros if ficheros is not None else {
            ("in-x", "doc-1.pdf"): PDF,
            ("env-x", "doc-1.json"): json.dumps(ENVELOPE).encode("utf-8"),
        }
        self.llamadas: list[tuple[str, str]] = []

    def descargar(self, contenedor: str, nombre: str) -> bytes:
        self.llamadas.append((contenedor, nombre))
        return self.ficheros[(contenedor, nombre)]


@dataclass
class ResultadoFake:
    document_id: str
    deduplicated: bool


class PipelineFake:
    def __init__(self) -> None:
        self.peticiones: list[PersistParteRequest] = []

    def run(self, peticion: PersistParteRequest) -> ResultadoFake:
        self.peticiones.append(peticion)
        return ResultadoFake(document_id="doc-1", deduplicated=False)


class ConciliadorFake:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.llamadas = 0
        self._error = error

    def conciliar_todos(self) -> dict:
        self.llamadas += 1
        if self._error is not None:
            raise self._error
        return {"registros": 3, "extras_reclasificadas": 2}


def _handler(*, conciliador=None, blob=None, pipeline=None,
             sin_conciliador: bool = False):
    blob = blob if blob is not None else BlobFake()
    pipeline = pipeline if pipeline is not None else PipelineFake()
    if conciliador is None and not sin_conciliador:
        conciliador = ConciliadorFake()
    handler = construir_handler(
        blob=blob, pipeline=pipeline, recurso_conciliador=conciliador,
        contenedor_input="in-x", contenedor_envelopes="env-x")
    return handler, blob, pipeline, conciliador


def _recalculo(**extra) -> dict:
    mensaje = {"tipo": "recalcular", "motivo": "cambio_fecha",
               "document_id": "doc-9", "solicitado_por": "revisor@ejemplo",
               "solicitado_at_utc": "2026-10-09T10:00:00+00:00"}
    mensaje.update(extra)
    return mensaje


# ============================ R12 · clasificar ========================== #

def test_f042_r12_constantes_del_contrato() -> None:
    assert TIPO_RECALCULAR == "recalcular"
    assert CLASE_INGESTA == "ingesta"
    assert CLASE_RECALCULO == "recalcular"
    assert issubclass(MensajeDesconocido, ValueError)


@pytest.mark.parametrize("payload", [
    {"document_id": "d", "filename": "p.pdf", "mime_type": "application/pdf",
     "context": {}},
    {"document_id": "d"},
    {"document_id": "d", "tipo": None},
    {},
])
def test_f042_r12_sin_tipo_o_tipo_nulo_es_ingesta(payload) -> None:
    assert clasificar(payload) == "ingesta"


def test_f042_r12_tipo_recalcular_es_recalculo() -> None:
    assert clasificar(_recalculo()) == "recalcular"
    assert clasificar({"tipo": "recalcular"}) == "recalcular"


@pytest.mark.parametrize("tipo", ["otro", "", "RECALCULAR", "ingesta", 1,
                                  False])
def test_f042_r12_tipo_desconocido_lanza(tipo) -> None:
    with pytest.raises(MensajeDesconocido) as exc:
        clasificar({"document_id": "d", "tipo": tipo})
    assert repr(tipo) in str(exc.value)


@pytest.mark.parametrize("payload", [[], ["tipo"], "recalcular", None, 3,
                                     b"{}"])
def test_f042_r12_payload_que_no_es_objeto_lanza(payload) -> None:
    with pytest.raises(MensajeDesconocido) as exc:
        clasificar(payload)
    assert type(payload).__name__ in str(exc.value)


# ============================ R13 · ingesta ============================== #

def test_f042_r13_ingesta_hace_lo_de_siempre(caplog) -> None:
    handler, blob, pipeline, conciliador = _handler()
    caplog.set_level(logging.INFO)

    resultado = handler({"document_id": "doc-1", "filename": "parte.pdf",
                         "mime_type": "application/x-pdf",
                         "context": {"remitente": "buzon"}})

    assert resultado is None
    assert blob.llamadas == [("in-x", "doc-1.pdf"), ("env-x", "doc-1.json")]
    assert pipeline.peticiones == [PersistParteRequest(
        filename="parte.pdf", mime_type="application/x-pdf", file_bytes=PDF,
        extraction_envelope=ENVELOPE, context={"remitente": "buzon"})]
    assert conciliador.llamadas == 0
    assert ("[sv3-worker] persistido document_id=doc-1 -> "
            "{'document_id': 'doc-1', 'deduplicated': False}") in caplog.text


def test_f042_r13_ingesta_con_los_valores_por_defecto() -> None:
    handler, _blob, pipeline, _c = _handler()
    handler({"document_id": "doc-1"})
    assert pipeline.peticiones == [PersistParteRequest(
        filename="document.pdf", mime_type="application/pdf", file_bytes=PDF,
        extraction_envelope=ENVELOPE, context={})]


def test_f042_r13_contexto_que_no_es_dict_se_cambia_por_vacio() -> None:
    handler, _blob, pipeline, _c = _handler()
    handler({"document_id": "doc-1", "context": ["no", "dict"], "tipo": None})
    assert pipeline.peticiones[0].context == {}


def test_f042_r13_ingesta_sin_conciliador_sigue_funcionando() -> None:
    handler, _blob, pipeline, _c = _handler(sin_conciliador=True)
    handler({"document_id": "doc-1"})
    assert len(pipeline.peticiones) == 1


# ============================ R14 · recalculo =========================== #

def test_f042_r14_recalculo_ejecuta_una_pasada_y_nada_mas(caplog) -> None:
    handler, blob, pipeline, conciliador = _handler()
    caplog.set_level(logging.INFO)

    resultado = handler(_recalculo())

    assert resultado is None
    assert conciliador.llamadas == 1
    assert blob.llamadas == []
    assert pipeline.peticiones == []
    assert ("[sv3-worker] recalculo motivo=cambio_fecha document_id=doc-9 "
            "por=revisor@ejemplo -> {'registros': 3, "
            "'extras_reclasificadas': 2}") in caplog.text
    linea = next(r for r in caplog.records if "recalculo motivo" in
                 r.getMessage())
    assert linea.levelno == logging.INFO


def test_f042_r14_recalculo_con_campos_ausentes_no_rompe(caplog) -> None:
    handler, _blob, _pipeline, conciliador = _handler()
    caplog.set_level(logging.INFO)
    handler({"tipo": "recalcular"})
    assert conciliador.llamadas == 1
    assert ("recalculo motivo=None document_id=None por=None"
            in caplog.text)


# ======================= R15 · un fallo se propaga ====================== #

def test_f042_r15_si_la_pasada_falla_el_handler_propaga() -> None:
    error = RuntimeError("Sigrid caido a media pasada")
    handler, blob, pipeline, conciliador = _handler(
        conciliador=ConciliadorFake(error=error))

    with pytest.raises(RuntimeError) as exc:
        handler(_recalculo())

    assert exc.value is error
    assert conciliador.llamadas == 1
    assert blob.llamadas == [] and pipeline.peticiones == []


# ===================== R16 · mensaje desconocido ======================== #

@pytest.mark.parametrize("payload", [{"tipo": "borrar", "document_id": "d"},
                                     ["no", "es", "objeto"]])
def test_f042_r16_desconocido_se_propaga_sin_tocar_nada(payload,
                                                        caplog) -> None:
    handler, blob, pipeline, conciliador = _handler()
    caplog.set_level(logging.INFO)

    with pytest.raises(MensajeDesconocido):
        handler(payload)

    assert blob.llamadas == []
    assert pipeline.peticiones == []
    assert conciliador.llamadas == 0
    errores = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errores) == 1
    assert "[sv3-worker] mensaje desconocido" in errores[0].getMessage()


# ================== R17 · sin Sigrid, recalculo consumido =============== #

def test_f042_r17_sin_conciliador_avisa_y_da_el_mensaje_por_bueno(
        caplog) -> None:
    handler, blob, pipeline, _c = _handler(sin_conciliador=True)
    caplog.set_level(logging.INFO)

    assert handler(_recalculo()) is None

    assert blob.llamadas == [] and pipeline.peticiones == []
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert ("[sv3-worker] recalculo pedido pero Sigrid no esta cableado"
            in avisos[0].getMessage())
    assert "doc-9" in avisos[0].getMessage()
