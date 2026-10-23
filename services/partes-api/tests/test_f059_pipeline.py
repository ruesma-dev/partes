# tests/test_f059_pipeline.py
"""F-059 · R11–R19: el pipeline de sv2 manda la página escaneada derecha.

Con la conversión activa (interruptor encendido y proveedor en la lista), el
pipeline pide al conversor la imagen derecha y se la pasa al cliente del
proveedor en lugar del PDF. Si no aplica o falla, manda el PDF original byte
a byte. ``meta.source_*`` siguen siendo del documento recibido y
``meta.adjunto_ia`` deja la traza de lo que se envió.

Sin red ni IA: el cliente del proveedor es un doble que captura el adjunto;
el conversor, un doble configurable (y uno de extremo a extremo con el real).
"""
from __future__ import annotations

import hashlib
import logging
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from application.pipelines.extract_parte_pipeline import (
    ExtractPartePipeline,
    ExtractParteRequest,
)
from application.services.parte_extraction_service import (
    ParteExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.conversion_adjunto import (
    MOTIVO_IMAGEN_NO_JPEG,
    ResultadoConversion,
)
from domain.models.llm_attachment import LlmAttachment
from domain.ports.conversor_pagina import ConversorPaginaImagen
from domain.ports.llm_client import LlmVisionClient
from infrastructure.document.pagina_pdf_imagen import PaginaPdfImagenConversor
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from tests.f059_pdf_sinteticos import pdf_escaneado

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"
LOGGER_PIPELINE = "application.pipelines.extract_parte_pipeline"
#: Nombre de fichero con «datos» que nunca deben salir en el WARNING.
NOMBRE_FICHERO = "PT_Fulano_de_Tal_12345678Z.pdf"
PDF = b"%PDF-1.4 bytes de un parte de prueba"
SHA_PDF = hashlib.sha256(PDF).hexdigest()
IMAGEN = LlmAttachment(
    kind="image", filename="PT_Fulano_de_Tal_12345678Z.jpg",
    mime_type="image/jpeg", data=b"\xff\xd8 jpeg derecho de prueba",
)
CONVERTIDA = ResultadoConversion(
    adjunto=IMAGEN, motivo="", giro_grados=270, ancho_px=2480, alto_px=3507)
CLAVES_BASE = {"conversion", "motivo", "kind", "mime_type", "size_bytes"}
CLAVES_CONVERTIDA = CLAVES_BASE | {"giro_grados", "ancho_px", "alto_px"}


class ClienteFalso(LlmVisionClient):
    """Cliente del proveedor que solo apunta el adjunto recibido."""

    def __init__(self) -> None:
        self.adjuntos: list[LlmAttachment] = []

    def extract_document(self, *, model, instructions, user_text, attachment,
                         response_model):
        self.adjuntos.append(attachment)
        return response_model.model_validate(
            {"cabecera": {}, "firma": {"firmado": False}, "empleados": []})


class ConversorFalso(ConversorPaginaImagen):
    def __init__(self, resultado: ResultadoConversion | None = None,
                 error: Exception | None = None) -> None:
        self.resultado = resultado or CONVERTIDA
        self.error = error
        self.llamadas: list[LlmAttachment] = []

    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion:
        self.llamadas.append(adjunto)
        if self.error is not None:
            raise self.error
        return self.resultado


def _pipeline(conversor: ConversorPaginaImagen | None = None, *,
              proveedor: str = "openai",
              proveedores_imagen: frozenset[str] = frozenset({"openai"}),
              ) -> tuple[ExtractPartePipeline, ClienteFalso]:
    cliente = ClienteFalso()
    servicio = ParteExtractionService(
        providers=[ProviderClientSpec(
            provider=proveedor, model_name="modelo-falso", client=cliente)],
        prompt_repo=YamlPromptRepository(str(RUTA_PROMPTS)),
        schema_registry=SchemaRegistry(),
    )
    pipeline = ExtractPartePipeline(
        extraction_service=servicio, max_file_mb=25, service_version="test",
        provider=proveedor, prompt_key="parte_trabajo_es",
        conversor=conversor, proveedores_imagen=proveedores_imagen,
    )
    return pipeline, cliente


def _correr(pipeline: ExtractPartePipeline, data: bytes = PDF,
            filename: str = NOMBRE_FICHERO,
            mime_type: str = "application/pdf") -> dict:
    return pipeline.run(ExtractParteRequest(
        filename=filename, mime_type=mime_type, file_bytes=data))


def _registros(caplog, nivel: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records
            if r.name == LOGGER_PIPELINE and r.levelno == nivel]


# ------------------- R11 · la imagen sustituye al PDF -------------------- #

def test_f059_r11_activa_el_cliente_recibe_la_imagen() -> None:
    conversor = ConversorFalso()
    pipeline, cliente = _pipeline(conversor)
    _correr(pipeline)
    assert len(conversor.llamadas) == 1
    assert conversor.llamadas[0].kind == "pdf"
    assert conversor.llamadas[0].data == PDF
    assert cliente.adjuntos == [IMAGEN]


# --------------------- R12 · no aplica: el PDF tal cual ------------------ #

def test_f059_r12_no_aplica_manda_el_pdf_byte_a_byte_e_info(caplog) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_PIPELINE)
    conversor = ConversorFalso(ResultadoConversion(
        adjunto=None, motivo=MOTIVO_IMAGEN_NO_JPEG))
    pipeline, cliente = _pipeline(conversor)
    env = _correr(pipeline)
    (enviado,) = cliente.adjuntos
    assert enviado.kind == "pdf"
    assert enviado.mime_type == "application/pdf"
    assert enviado.data == PDF
    info = [r.getMessage() for r in _registros(caplog, logging.INFO)]
    assert any(MOTIVO_IMAGEN_NO_JPEG in m and SHA_PDF[:12] in m for m in info), info
    assert env["meta"]["adjunto_ia"] == {
        "conversion": "no_aplica", "motivo": MOTIVO_IMAGEN_NO_JPEG,
        "kind": "pdf", "mime_type": "application/pdf", "size_bytes": len(PDF),
    }


# ---------------- R13 · si la conversión falla, el PDF y sigue ----------- #

@pytest.mark.parametrize(
    "error",
    [ValueError("contenido Fulano 12345678Z"), OSError("truncado"),
     Image.DecompressionBombError("bomba"), KeyError("/XObject")],
    ids=["ValueError", "OSError", "DecompressionBombError", "KeyError"],
)
def test_f059_r13_fallo_manda_el_pdf_con_warning_sin_datos(
    caplog, error: Exception
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_PIPELINE)
    pipeline, cliente = _pipeline(ConversorFalso(error=error))
    env = _correr(pipeline)
    (enviado,) = cliente.adjuntos
    assert enviado.kind == "pdf" and enviado.data == PDF
    avisos = _registros(caplog, logging.WARNING)
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert type(error).__name__ in texto
    assert f"sha256={SHA_PDF[:12]}" in texto
    assert SHA_PDF not in texto, "solo los 12 primeros caracteres"
    assert "Fulano" not in texto and "12345678Z" not in texto
    assert NOMBRE_FICHERO not in texto
    assert avisos[0].exc_info is None, "la traza llevaría el mensaje de la excepción"
    assert env["meta"]["adjunto_ia"] == {
        "conversion": "error", "motivo": type(error).__name__,
        "kind": "pdf", "mime_type": "application/pdf", "size_bytes": len(PDF),
    }
    assert env["data"]["empleados"] == []


# ------------------- R14 · apagada: ni se llama al conversor ------------- #

def test_f059_r14_sin_conversor_es_el_interruptor_apagado() -> None:
    pipeline, cliente = _pipeline(None)
    env = _correr(pipeline)
    assert cliente.adjuntos[0].kind == "pdf" and cliente.adjuntos[0].data == PDF
    assert env["meta"]["adjunto_ia"] == {
        "conversion": "apagada", "motivo": "interruptor",
        "kind": "pdf", "mime_type": "application/pdf", "size_bytes": len(PDF),
    }


def test_f059_r14_los_constructores_de_antes_siguen_valiendo() -> None:
    """Sin los kwargs nuevos, el pipeline se comporta como hasta ahora."""
    cliente = ClienteFalso()
    servicio = ParteExtractionService(
        providers=[ProviderClientSpec(
            provider="openai", model_name="m", client=cliente)],
        prompt_repo=YamlPromptRepository(str(RUTA_PROMPTS)),
        schema_registry=SchemaRegistry(),
    )
    pipeline = ExtractPartePipeline(
        extraction_service=servicio, max_file_mb=25, service_version="t",
        provider="openai", prompt_key="parte_trabajo_es")
    env = _correr(pipeline)
    assert cliente.adjuntos[0].data == PDF
    assert env["meta"]["adjunto_ia"]["conversion"] == "apagada"


@pytest.mark.parametrize(
    "proveedores", [frozenset(), frozenset({"gemini"}), frozenset({"gemini", "claude"})])
def test_f059_r14_proveedor_fuera_de_la_lista_no_llama_al_conversor(
    proveedores: frozenset[str]
) -> None:
    conversor = ConversorFalso()
    pipeline, cliente = _pipeline(conversor, proveedores_imagen=proveedores)
    env = _correr(pipeline)
    assert conversor.llamadas == []
    assert cliente.adjuntos[0].data == PDF
    assert env["meta"]["adjunto_ia"]["conversion"] == "apagada"
    assert env["meta"]["adjunto_ia"]["motivo"] == "proveedor_fuera_de_lista"


def test_f059_r14_la_lista_es_por_proveedor_activo() -> None:
    """Gemini en la lista y activo: se convierte aunque OpenAI no esté."""
    conversor = ConversorFalso()
    pipeline, cliente = _pipeline(
        conversor, proveedor="gemini", proveedores_imagen=frozenset({"gemini"}))
    _correr(pipeline)
    assert len(conversor.llamadas) == 1
    assert cliente.adjuntos == [IMAGEN]


# ------------------- R15 · las fotos van como siempre -------------------- #

@pytest.mark.parametrize(
    ("filename", "mime"),
    [("foto.jpg", "image/jpeg"), ("foto.png", "image/png"),
     ("foto.webp", "image/webp")],
)
def test_f059_r15_una_foto_no_pasa_por_el_conversor(filename: str, mime: str) -> None:
    conversor = ConversorFalso()
    pipeline, cliente = _pipeline(conversor)
    foto = b"bytes de una foto del movil"
    env = _correr(pipeline, data=foto, filename=filename, mime_type=mime)
    assert conversor.llamadas == []
    (enviado,) = cliente.adjuntos
    assert (enviado.kind, enviado.mime_type, enviado.data) == ("image", mime, foto)
    assert env["meta"]["adjunto_ia"] == {
        "conversion": "no_aplica", "motivo": "no_es_pdf",
        "kind": "image", "mime_type": mime, "size_bytes": len(foto),
    }


# ------------------- R16 · meta.source_* del original -------------------- #

def test_f059_r16_meta_source_es_del_documento_recibido() -> None:
    pipeline, _ = _pipeline(ConversorFalso())
    meta = _correr(pipeline)["meta"]
    assert meta["source_filename"] == NOMBRE_FICHERO
    assert meta["source_mime_type"] == "application/pdf"
    assert meta["source_sha256"] == SHA_PDF


# ----------------------- R17 · meta.adjunto_ia --------------------------- #

def test_f059_r17_traza_de_la_convertida() -> None:
    pipeline, _ = _pipeline(ConversorFalso())
    traza = _correr(pipeline)["meta"]["adjunto_ia"]
    assert set(traza) == CLAVES_CONVERTIDA
    assert traza == {
        "conversion": "convertida", "motivo": "", "kind": "image",
        "mime_type": "image/jpeg", "size_bytes": len(IMAGEN.data),
        "giro_grados": 270, "ancho_px": 2480, "alto_px": 3507,
    }


def test_f059_r17_sin_nombre_de_fichero_en_la_traza() -> None:
    for conversor in (ConversorFalso(), ConversorFalso(error=ValueError("x")), None):
        pipeline, _ = _pipeline(conversor)
        traza = _correr(pipeline)["meta"]["adjunto_ia"]
        assert set(traza) in (CLAVES_BASE, CLAVES_CONVERTIDA)
        assert all("Fulano" not in str(v) for v in traza.values())


# ------------------- R18 · debug describe lo enviado --------------------- #

def test_f059_r18_debug_lleva_el_sha256_de_la_imagen() -> None:
    pipeline, _ = _pipeline(ConversorFalso())
    adj = _correr(pipeline)["debug"]["openai_request"]["attachment"]
    assert adj["kind"] == "image"
    assert adj["sha256"] == hashlib.sha256(IMAGEN.data).hexdigest()
    assert adj["size_bytes"] == len(IMAGEN.data)


def test_f059_r18_debug_sin_convertir_es_el_pdf() -> None:
    pipeline, _ = _pipeline(None)
    adj = _correr(pipeline)["debug"]["openai_request"]["attachment"]
    assert adj["kind"] == "pdf" and adj["sha256"] == SHA_PDF


# --------------------- R19 · INFO de la convertida ----------------------- #

def test_f059_r19_info_con_giro_medidas_y_bytes(caplog) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_PIPELINE)
    pipeline, _ = _pipeline(ConversorFalso())
    _correr(pipeline)
    info = [r.getMessage() for r in _registros(caplog, logging.INFO)]
    esperado = f"giro=270 ancho=2480 alto=3507 bytes={len(IMAGEN.data)}"
    assert any(esperado in m for m in info), info
    assert all(NOMBRE_FICHERO not in m for m in info)
    assert _registros(caplog, logging.WARNING) == []


# ------------------ De extremo a extremo con el conversor real ----------- #

def test_f059_r11_extremo_a_extremo_rotate_270() -> None:
    pdf = pdf_escaneado(270)
    pipeline, cliente = _pipeline(PaginaPdfImagenConversor())
    env = _correr(pipeline, data=pdf)
    (enviado,) = cliente.adjuntos
    assert (enviado.kind, enviado.mime_type) == ("image", "image/jpeg")
    img = Image.open(BytesIO(enviado.data))
    assert img.size == (300, 200)
    assert ImageStat.Stat(img.convert("L").crop((0, 0, 40, 40))).mean[0] < 60
    traza = env["meta"]["adjunto_ia"]
    assert (traza["conversion"], traza["giro_grados"]) == ("convertida", 270)
    assert (traza["ancho_px"], traza["alto_px"]) == (300, 200)
    assert env["meta"]["source_sha256"] == hashlib.sha256(pdf).hexdigest()
