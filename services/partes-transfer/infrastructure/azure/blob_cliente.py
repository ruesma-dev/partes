# infrastructure/azure/blob_cliente.py
"""Cliente de Blob para el hand-off de peticiones y resultados de sv5.

Adaptacion del adaptador de sv3. Contenedor: 'transfer', con dos prefijos
—'peticiones/' (lo que sv4 pide registrar) y 'resultados/' (el veredicto por
linea)—. El mensaje de cola lleva solo la referencia: una obra x mes supera
de sobra los 64 KB de un mensaje de Storage Queue.

Lo durable sigue viviendo en Sigrid (lineas) y en PostgreSQL (traza en sv4);
estos blobs son efimeros y los purga la lifecycle policy.
"""
from __future__ import annotations

import logging

from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


class BlobCliente:
    def __init__(
        self,
        account_url: str | None = None,
        credential=None,
        *,
        connection_string: str | None = None,
    ) -> None:
        # Dos modos (patron albaranes):
        #  - connection_string: local/Azurite (o cuenta con clave).
        #  - account_url + credential: nube (managed identity / az login).
        if connection_string:
            self._svc = BlobServiceClient.from_connection_string(
                connection_string
            )
        elif account_url:
            self._svc = BlobServiceClient(
                account_url=account_url, credential=credential
            )
        else:
            raise ValueError(
                "BlobCliente requiere BLOBS_CONNECTION_STRING (local/Azurite)"
                " o BLOBS_ACCOUNT_URL (nube)."
            )

    def asegurar_contenedores(self, nombres: list[str]) -> None:
        """Crea los contenedores si no existen (modo local con Azurite;
        idempotente)."""
        from azure.core.exceptions import ResourceExistsError
        for n in nombres:
            try:
                self._svc.create_container(n)
                logger.info("[blob] creado contenedor '%s'", n)
            except ResourceExistsError:
                pass

    def subir(self, container: str, name: str, data: bytes,
              content_type: str | None = None) -> None:
        from azure.storage.blob import ContentSettings
        cs = ContentSettings(content_type=content_type) if content_type else None
        bc = self._svc.get_blob_client(container=container, blob=name)
        bc.upload_blob(data, overwrite=True, content_settings=cs)
        logger.info("[blob] subido %s/%s (%s bytes)", container, name, len(data))

    def descargar(self, container: str, name: str) -> bytes:
        bc = self._svc.get_blob_client(container=container, blob=name)
        data = bc.download_blob().readall()
        logger.info("[blob] descargado %s/%s (%s bytes)", container, name,
                    len(data))
        return data
