# infrastructure/http/persistence_http_client.py
from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from domain.ports.persistence_client import PersistenceClient

logger = logging.getLogger(__name__)


class PersistenceHttpClient(PersistenceClient):
    """Cliente HTTP del servicio 3 (partes-persister).

    Envia en multipart: el fichero del documento logico, el envelope de
    extraccion (sv2) serializado y el contexto de email/adjunto/documento.
    El sv3 persiste, casa contra Sigrid (empleado/obra/codigo de hora) y
    devuelve ``{"ok": true, "document_id": "..."}``.
    """

    def __init__(self, *, base_url: str, persist_path: str, timeout_s: int) -> None:
        self._url = f"{base_url.rstrip('/')}{persist_path}"
        self._timeout_s = int(timeout_s)

    def persist(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        extraction_envelope: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        files = {
            "file": (
                filename or "document.bin",
                file_bytes,
                mime_type or "application/octet-stream",
            )
        }
        data = {
            "extraction_json": json.dumps(extraction_envelope, ensure_ascii=False),
            "context_json": json.dumps(context, ensure_ascii=False),
        }
        logger.info(
            "POST sv3 persist url=%s filename=%s size=%dB",
            self._url,
            filename,
            len(file_bytes),
        )
        with httpx.Client(timeout=self._timeout_s) as client:
            response = client.post(self._url, files=files, data=data)
        if response.status_code >= 300:
            raise RuntimeError(
                f"sv3 persist {response.status_code}: {response.text[:400]}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError(
                f"sv3 persist devolvio un cuerpo no-objeto: {type(body)!r}"
            )
        return body
