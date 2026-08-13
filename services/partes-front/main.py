# main.py
from __future__ import annotations

import logging
from pathlib import Path

import uvicorn

from config.logging_config import configure_logging
from config.settings import Settings
from infrastructure.azure.credenciales import (
    construir_blob_cliente,
    construir_cola_cliente,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.database.session_factory import SessionFactory
from infrastructure.transfer.transfer_queue_publisher import (
    TransferQueuePublisher,
)
from interface_adapters.web.app import build_app
from interface_adapters.workers.resultado_consumer import (
    arrancar_consumidor_resultados,
)

logger = logging.getLogger(__name__)


def _componentes_de_cola(settings: Settings, repository):
    """Cablea publisher y consumidor de resultados (F-002).

    Devuelve `(publisher, cola_cliente)`. El cliente de cola que se le
    pasa a la app es el de la gestion de poison; el consumidor usa el
    suyo, porque los clientes del SDK no se comparten entre hilos.
    """
    colas_cs = settings.colas_connection_string

    def _cola():
        return construir_cola_cliente(
            connection_string=colas_cs,
            account_url=settings.colas_account_url,
            max_dequeue=settings.cola_max_dequeue,
            visibility_timeout_s=settings.cola_visibility_s,
        )

    def _blob():
        return construir_blob_cliente(
            connection_string=settings.blobs_connection_string,
            account_url=settings.blobs_account_url,
            colas_connection_string=colas_cs,
        )

    cola_publicacion, blob_publicacion = _cola(), _blob()
    if colas_cs:
        # Modo local (Azurite arranca vacio); en la nube las crea
        # infra/add_qtransfer_partes.ps1.
        cola_publicacion.asegurar_colas([settings.cola_transfer,
                                         settings.cola_transfer_result])
        blob_publicacion.asegurar_contenedores([settings.blob_transfer])

    publisher = TransferQueuePublisher(
        cola=cola_publicacion, blob=blob_publicacion,
        cola_transfer=settings.cola_transfer,
        contenedor=settings.blob_transfer,
    )
    arrancar_consumidor_resultados(
        repository=repository, cola=_cola(), blob=_blob(), settings=settings)
    logger.info("[transfer-cola][wiring] CABLEADO cola=%s resultado=%s "
                "contenedor=%s", settings.cola_transfer,
                settings.cola_transfer_result, settings.blob_transfer)
    return publisher, _cola()


def main() -> int:
    settings = Settings()
    configure_logging(Path(settings.log_dir), settings.log_level)

    session_factory = SessionFactory(
        database_url=settings.database_url,
        admin_database_url=settings.admin_database_url,
        target_database_name=settings.pg_db,
        auto_create_database=settings.auto_create_database,
    )
    repository = ParteReviewRepository(session_factory)
    repository.initialize()

    publisher = cola_cliente = None
    if settings.transfer_queue_enabled:
        publisher, cola_cliente = _componentes_de_cola(settings, repository)
    else:
        logger.info("[transfer-cola][wiring] DESACTIVADO (faltan COLAS_*): "
                    "la aprobacion se registrara en modo SINCRONO.")

    app = build_app(settings, repository=repository, publisher=publisher,
                    cola_cliente=cola_cliente)
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
