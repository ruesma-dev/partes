# infrastructure/queue/blob_queue_sink.py
"""Adaptador del puerto DocumentSink sobre Blob + Storage Queue.

Flujo de ingesta (por documento logico):
  1. Sube el PDF a 'input/{document_id}.pdf' (Blob).
  2. Encola en 'q-extraccion' el contrato {document_id, filename, mime_type,
     context}, que sv2 (extraccion) consume; sv2 propaga el context a sv3
     (persistencia + SharePoint).

Auth a Blob/Cola por managed identity (igual que sv2/sv3). El sv1 NO espera
el resultado: su exito es 'documento ingerido en el pipeline', no 'procesado
end-to-end'. Si sv2/sv3 fallan de forma persistente, el mensaje acaba en la
cola '-poison' (DLQ), no vuelve al buzon.
"""
from __future__ import annotations

import logging

from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente

logger = logging.getLogger(__name__)


class BlobQueueSink:
    def __init__(
        self,
        *,
        blob: BlobCliente,
        cola: ColaCliente,
        input_container: str,
        cola_extraccion: str,
    ) -> None:
        self._blob = blob
        self._cola = cola
        self._input_container = input_container
        self._cola_extraccion = cola_extraccion

    def enqueue(
        self,
        *,
        document_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        context: dict,
    ) -> None:
        self._blob.subir(
            self._input_container,
            f"{document_id}.pdf",
            file_bytes,
            mime_type or "application/pdf",
        )
        self._cola.enviar(
            self._cola_extraccion,
            {
                "document_id": document_id,
                "filename": filename,
                "mime_type": mime_type or "application/pdf",
                "context": context or {},
            },
        )
        logger.info(
            "[sink] ingerido document_id=%s file=%r (%s bytes) -> %s",
            document_id,
            filename,
            len(file_bytes),
            self._cola_extraccion,
        )
