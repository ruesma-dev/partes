# application/pipelines/extract_parte_pipeline.py
"""Pipeline de extraccion de un parte de trabajo (sv2, una fase).

Valida el adjunto, ejecuta el proveedor LLM configurado y devuelve un
envelope ``{meta, data, debug}`` con la misma forma que el sv2 de
albaranes, para que sv3 lo consuma de forma homogenea.

F-059: con la conversión activa (interruptor ``PAGINA_COMO_IMAGEN`` y el
proveedor en ``PAGINA_COMO_IMAGEN_PROVEEDORES``), una página escaneada viaja
a la IA como imagen derecha (``_preparar_para_ia``); si no aplica o falla,
va el PDF original byte a byte. ``meta.source_*`` siguen siendo del
documento recibido y ``meta.adjunto_ia`` deja la traza de lo enviado.
"""
from __future__ import annotations

import hashlib
import logging
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from application.services.parte_extraction_service import (
    ParteExtractionService,
    ProviderExtractionResult,
)
from application.services.auxhor_catalog_provider import AuxhorCatalogProvider
from domain.models.conversion_adjunto import (
    APAGADA,
    CONVERTIDA,
    ERROR,
    MOTIVO_INTERRUPTOR,
    MOTIVO_NO_ES_PDF,
    MOTIVO_PROVEEDOR_FUERA_DE_LISTA,
    NO_APLICA,
)
from domain.models.llm_attachment import LlmAttachment
from domain.ports.conversor_pagina import ConversorPaginaImagen

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractParteRequest:
    filename: str
    mime_type: str
    file_bytes: bytes


class ExtractPartePipeline:
    def __init__(
        self,
        *,
        extraction_service: ParteExtractionService,
        max_file_mb: int,
        service_version: str,
        provider: str,
        prompt_key: str,
        catalog_provider: AuxhorCatalogProvider | None = None,
        conversor: ConversorPaginaImagen | None = None,
        proveedores_imagen: frozenset[str] = frozenset(),
    ) -> None:
        self._service = extraction_service
        self._max_file_mb = max_file_mb
        self._service_version = service_version
        self._provider = provider
        self._prompt_key = prompt_key
        self._catalog_provider = catalog_provider
        self._conversor = conversor
        self._proveedores_imagen = frozenset(proveedores_imagen)

    def run(self, request: ExtractParteRequest) -> Dict[str, Any]:
        original = self._build_attachment_validated(
            filename=request.filename,
            mime_type=request.mime_type,
            file_bytes=request.file_bytes,
        )
        sha256 = hashlib.sha256(request.file_bytes).hexdigest()
        enviado, adjunto_ia = self._preparar_para_ia(original, sha256)
        dynamic_context = None
        if self._catalog_provider is not None and self._catalog_provider.enabled:
            block = self._catalog_provider.prompt_block()
            dynamic_context = block or None
        result = self._service.extract(
            attachment=enviado,
            provider=self._provider,
            prompt_key=self._prompt_key,
            dynamic_context=dynamic_context,
        )
        return self._envelope(
            provider_result=result,
            attachment=original,
            sha256=sha256,
            adjunto_ia=adjunto_ia,
        )

    # --------------------------------------------------------------- #
    # F-059: página escaneada -> imagen derecha.
    # --------------------------------------------------------------- #
    def _preparar_para_ia(
        self, original: LlmAttachment, sha256: str
    ) -> Tuple[LlmAttachment, Dict[str, Any]]:
        """Devuelve (adjunto a enviar, meta.adjunto_ia).

        Nunca lanza por la conversión: si el conversor falla, se manda el
        PDF original y se avisa con el tipo de excepción y el sha256 corto,
        sin nombre de fichero ni nada del contenido (R13).
        """
        if self._conversor is None:
            return original, self._traza(APAGADA, MOTIVO_INTERRUPTOR, original)
        if self._provider not in self._proveedores_imagen:
            return original, self._traza(
                APAGADA, MOTIVO_PROVEEDOR_FUERA_DE_LISTA, original)
        if original.kind != "pdf":
            return original, self._traza(NO_APLICA, MOTIVO_NO_ES_PDF, original)
        sha_corto = sha256[:12]
        try:
            resultado = self._conversor.convertir(original)
        except Exception as exc:
            tipo = type(exc).__name__
            logger.warning(
                "[partes-sv2][imagen] conversión fallida (%s) en sha256=%s: "
                "se manda el PDF",
                tipo,
                sha_corto,
            )
            return original, self._traza(ERROR, tipo, original)
        if resultado.adjunto is None:
            logger.info(
                "[partes-sv2][imagen] no aplica (%s) en sha256=%s: se manda el PDF",
                resultado.motivo,
                sha_corto,
            )
            return original, self._traza(NO_APLICA, resultado.motivo, original)
        imagen = resultado.adjunto
        logger.info(
            "[partes-sv2][imagen] página convertida en sha256=%s: "
            "giro=%s ancho=%s alto=%s bytes=%s",
            sha_corto,
            resultado.giro_grados,
            resultado.ancho_px,
            resultado.alto_px,
            len(imagen.data),
        )
        traza = self._traza(CONVERTIDA, "", imagen)
        traza.update(
            giro_grados=resultado.giro_grados,
            ancho_px=resultado.ancho_px,
            alto_px=resultado.alto_px,
        )
        return imagen, traza

    @staticmethod
    def _traza(conversion: str, motivo: str, enviado: LlmAttachment) -> Dict[str, Any]:
        """``meta.adjunto_ia`` del adjunto enviado, sin nombre de fichero."""
        return {
            "conversion": conversion,
            "motivo": motivo,
            "kind": enviado.kind,
            "mime_type": enviado.mime_type,
            "size_bytes": len(enviado.data),
        }

    # --------------------------------------------------------------- #
    # Helpers.
    # --------------------------------------------------------------- #
    def _build_attachment_validated(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> LlmAttachment:
        if not file_bytes:
            raise ValueError("Archivo vacio.")
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > self._max_file_mb:
            raise ValueError(
                f"Archivo demasiado grande ({size_mb:.2f} MB) > MAX_FILE_MB={self._max_file_mb}"
            )
        return self._build_attachment(filename, mime_type, file_bytes)

    @staticmethod
    def _build_attachment(filename: str, mime_type: str, file_bytes: bytes) -> LlmAttachment:
        filename = filename or "document.bin"
        is_pdf = mime_type == "application/pdf" or filename.lower().endswith(".pdf")
        if is_pdf:
            return LlmAttachment(
                kind="pdf",
                filename=filename,
                mime_type="application/pdf",
                data=file_bytes,
            )
        guessed_mime, _ = mimetypes.guess_type(filename)
        final_mime = mime_type or guessed_mime or "image/jpeg"
        return LlmAttachment(
            kind="image",
            filename=filename,
            mime_type=final_mime,
            data=file_bytes,
        )

    @staticmethod
    def _utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _envelope(
        self,
        *,
        provider_result: ProviderExtractionResult,
        attachment: LlmAttachment,
        sha256: str,
        adjunto_ia: Dict[str, Any],
    ) -> Dict[str, Any]:
        meta = {
            "phase": "extract",
            "prompt_key": provider_result.prompt_key,
            "schema": provider_result.schema_name,
            "provider": provider_result.provider,
            "model": provider_result.model_name,
            "source_filename": attachment.filename,
            "source_mime_type": attachment.mime_type,
            "source_sha256": sha256,
            "adjunto_ia": adjunto_ia,
            "processed_at_utc": self._utc_iso(),
            "service": "partes-extractor-api",
            "service_version": self._service_version,
        }
        return {
            "meta": meta,
            "data": provider_result.parsed.model_dump(),
            "debug": provider_result.debug_payload,
        }
