# infrastructure/http/http_chain_sink.py
"""Sink HTTP sincrono (modo LOCAL): sv1 -> sv2 -> sv3 sin colas ni Blob.

Implementa el puerto ``DocumentSink`` igual que ``BlobQueueSink``, pero en
lugar de subir a Blob y encolar en 'q-extraccion', encadena por HTTP el
flujo clasico: pide la extraccion al sv2 (partes-api) y, con el envelope
resultante, persiste en el sv3 (partes-persistencia) -> Postgres.

Pensado para validar el pipeline en local contra servicios sv2/sv3 que
corren como API (uvicorn) apuntando a una BD local, SIN tocar Azure
(ni credencial, ni Storage). En produccion se sigue usando el sink de
colas; este adaptador solo se cablea cuando SINK_MODE=http.
"""
from __future__ import annotations

import logging

from domain.ports.document_sink import DocumentSink
from domain.ports.extraction_client import ExtractionClient
from domain.ports.persistence_client import PersistenceClient

logger = logging.getLogger(__name__)


class HttpChainSink(DocumentSink):
    def __init__(
        self,
        *,
        extraction_client: ExtractionClient,
        persistence_client: PersistenceClient,
    ) -> None:
        self._extract = extraction_client
        self._persist = persistence_client

    def enqueue(
        self,
        *,
        document_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        context: dict,
    ) -> None:
        # 1) Extraccion IA (sv2): devuelve el envelope {meta, data, debug}.
        envelope = self._extract.extract(
            filename=filename,
            mime_type=mime_type,
            file_bytes=file_bytes,
        )
        # 2) Persistencia + casado Sigrid/recurso (sv3) -> Postgres. Se
        #    propaga el document_id en el contexto para trazabilidad.
        ctx = dict(context or {})
        ctx.setdefault("document_id", document_id)
        result = self._persist.persist(
            filename=filename,
            mime_type=mime_type,
            file_bytes=file_bytes,
            extraction_envelope=envelope,
            context=ctx,
        )
        logger.info(
            "[sink-http] persistido document_id=%s file=%r -> sv3=%s",
            document_id, filename, result,
        )
