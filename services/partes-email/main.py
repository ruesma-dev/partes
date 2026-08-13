# main.py
from __future__ import annotations

import logging
from pathlib import Path

from application.pipelines.polling_pipeline import PollingPipeline
from config.logging_config import configure_logging
from config.settings import Settings
from infrastructure.document.pdf_page_splitter import PdfPageSplitter
from infrastructure.graph.mail_client import GraphMailClient
from infrastructure.graph.token_provider import GraphTokenProvider
from infrastructure.azure.credenciales import (
    construir_blob_cliente,
    construir_cola_cliente,
)
from infrastructure.queue.blob_queue_sink import BlobQueueSink

logger = logging.getLogger(__name__)


def main() -> int:
    settings = Settings()
    configure_logging(Path(settings.log_dir), settings.log_level)

    logger.info("Arranque email-partes-ingestor (poller -> pipeline de colas)")
    logger.info(
        "mailbox=%s poll=%ss source_folder=%s",
        settings.mailbox_address,
        settings.poll_interval_s,
        settings.source_folder,
    )
    logger.info(
        "blob=%s cola=%s/%s container=%s",
        settings.blobs_account_url,
        settings.colas_account_url,
        settings.cola_extraccion,
        settings.blob_input_container,
    )

    # --- Graph (lectura del buzon) --- #
    token_provider = GraphTokenProvider(
        settings.graph_key,
        timeout_s=settings.graph_timeout_s,
    )
    mailbox = GraphMailClient(
        token_provider=token_provider,
        timeout_s=settings.graph_timeout_s,
    )

    # --- Salida: ingesta al pipeline de colas (Blob + Storage Queue) --- #
    colas_cs = getattr(settings, "colas_connection_string", None)
    cola = construir_cola_cliente(
        connection_string=colas_cs,
        account_url=settings.colas_account_url,
    )
    blob = construir_blob_cliente(
        connection_string=getattr(settings, "blobs_connection_string", None),
        account_url=settings.blobs_account_url,
        colas_connection_string=colas_cs,
    )
    if colas_cs:
        # Modo local (Azurite arranca vacio): asegura cola y contenedor.
        cola.asegurar_colas([settings.cola_extraccion])
        blob.asegurar_contenedores([settings.blob_input_container])
    sink = BlobQueueSink(
        blob=blob,
        cola=cola,
        input_container=settings.blob_input_container,
        cola_extraccion=settings.cola_extraccion,
    )

    PollingPipeline(
        mailbox=mailbox,
        sink=sink,
        pdf_splitter=PdfPageSplitter(),
    ).run_forever(settings)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
