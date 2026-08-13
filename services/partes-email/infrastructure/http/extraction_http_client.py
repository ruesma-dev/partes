# infrastructure/http/extraction_http_client.py
from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from domain.ports.extraction_client import ExtractionClient

logger = logging.getLogger(__name__)


class ExtractionHttpClient(ExtractionClient):
    """Cliente HTTP del servicio 2 (partes-extractor).

    Envia el documento logico (PDF de una pagina o imagen) en multipart
    y devuelve el envelope JSON tal cual (``{meta, data, debug}``). sv1
    no interpreta la estructura: la pasa integra al sv3.
    """

    def __init__(self, *, base_url: str, extract_path: str, timeout_s: int) -> None:
        self._url = f"{base_url.rstrip('/')}{extract_path}"
        self._timeout_s = int(timeout_s)

    def extract(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> Dict[str, Any]:
        files = {
            "file": (
                filename or "document.bin",
                file_bytes,
                mime_type or "application/octet-stream",
            )
        }
        logger.info(
            "POST sv2 extract url=%s filename=%s mime=%s size=%dB",
            self._url,
            filename,
            mime_type,
            len(file_bytes),
        )
        with httpx.Client(timeout=self._timeout_s) as client:
            response = client.post(self._url, files=files)
        if response.status_code >= 300:
            raise RuntimeError(
                f"sv2 extract {response.status_code}: {response.text[:400]}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError(
                f"sv2 extract devolvio un cuerpo no-objeto: {type(body)!r}"
            )
        return body
