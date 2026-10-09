# main_worker.py
"""Worker de sv3 (persistencia).

Consume 'q-persistencia', que trae dos tipos de mensaje (F-042; el handler
vive en `interface_adapters/workers/despacho.py`):

  - **ingesta** (de sv2, sin `tipo`): lee el PDF de 'input/{document_id}.pdf'
    y el envelope de 'envelopes/{document_id}.json', y persiste (PostgreSQL +
    SharePoint + Sigrid). La idempotencia at-least-once la cubre el dedup por
    sha256 del propio sv3.
  - **recalculo** (de sv4, `tipo: "recalcular"`, al guardar o deshacer la
    fecha de un parte): una pasada de `conciliar_todos` sin blobs ni
    pipeline. Si falla, se reintenta y acaba en la poison.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from config.logging_config import configure_logging
from config.settings import Settings
from infrastructure.azure.credenciales import (
    construir_blob_cliente,
    construir_cola_cliente,
)
from interface_adapters.api.app import build_app
from interface_adapters.workers.despacho import construir_handler

logger = logging.getLogger(__name__)

COLA_ENTRADA = os.getenv("COLA_PERSISTENCIA", "q-persistencia")
CONTENEDOR_INPUT = os.getenv("BLOB_INPUT", "input")
CONTENEDOR_ENVELOPES = os.getenv("BLOB_ENVELOPES", "envelopes")


def main() -> int:
    settings = Settings()
    configure_logging(Path(settings.log_dir), settings.log_level)
    logger.info("[sv3-worker] arrancando. cola=%s", COLA_ENTRADA)

    colas_cs = settings.colas_connection_string
    colas_url = settings.colas_account_url or os.getenv("COLAS_ACCOUNT_URL")
    if not colas_cs and not colas_url:
        logger.error(
            "[sv3-worker] falta storage: define COLAS_CONNECTION_STRING "
            "(local/Azurite) o COLAS_ACCOUNT_URL (nube) en el .env / "
            "Container App."
        )
        return 1

    cola = construir_cola_cliente(
        connection_string=colas_cs, account_url=colas_url,
        visibility_timeout_s=int(os.getenv("COLA_VISIBILITY_S", "300")),
    )
    blob = construir_blob_cliente(
        connection_string=settings.blobs_connection_string,
        account_url=settings.blobs_account_url
        or os.getenv("BLOBS_ACCOUNT_URL"),
        colas_connection_string=colas_cs,
    )
    if colas_cs:
        # Modo local (Azurite arranca vacio): asegura colas y contenedores.
        cola.asegurar_colas([COLA_ENTRADA])
        blob.asegurar_contenedores([CONTENEDOR_INPUT, CONTENEDOR_ENVELOPES])
    app = build_app(settings)
    handler = construir_handler(
        blob=blob, pipeline=app.state.pipeline,
        recurso_conciliador=app.state.recurso_conciliador,
        contenedor_input=CONTENEDOR_INPUT,
        contenedor_envelopes=CONTENEDOR_ENVELOPES,
    )

    cola.consumir(COLA_ENTRADA, handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
