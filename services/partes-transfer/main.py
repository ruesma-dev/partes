# main.py
"""Entrypoint de partes-transfer (sv5): API de registro + consumo de cola.

La composicion vive AQUI (no dentro de los adaptadores): se crean el
cliente de Sigrid, UN lock de escritura y UN pipeline, y ese mismo
pipeline lo comparten la API HTTP (preflight y pisado de conflictos) y
los hilos consumidores de `q-transfer`.

Que compartan pipeline es justo lo que hace efectivo el lock: sv5 corre
con una sola replica (min=1/max=1) porque `MAX(ide)+1` con UPDLOCK exige
serializar la escritura, y un lock de proceso solo protege si todos los
caminos de escritura pasan por el mismo objeto. Por eso el consumidor
vive en el MISMO proceso que la API y no en un worker aparte con KEDA.

Sin storage configurado, sv5 arranca exactamente como antes: solo HTTP.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

import uvicorn
from application.pipelines.registro_pipeline import RegistroPipeline
from config.logging_config import configure_logging
from config.settings import Settings
from infrastructure.azure.credenciales import (
    construir_blob_cliente,
    construir_cola_cliente,
)
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from interface_adapters.api.app import build_app
from interface_adapters.queue.transfer_consumer import arrancar_workers_transfer

logger = logging.getLogger(__name__)


def _arrancar_consumo(settings: Settings, pipeline: RegistroPipeline) -> None:
    """Cablea y lanza el pool de consumidores de `q-transfer`."""
    colas_cs = settings.colas_connection_string

    def _cola():
        # Una instancia POR WORKER: los clientes del SDK no se comparten
        # entre hilos.
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

    if colas_cs:
        # Modo local (Azurite arranca vacio): asegura colas y contenedor.
        # En la nube los crea infra/add_qtransfer_partes.ps1.
        _cola().asegurar_colas([settings.cola_transfer,
                                settings.cola_transfer_result])
        _blob().asegurar_contenedores([settings.blob_transfer])

    arrancar_workers_transfer(
        pipeline=pipeline, settings=settings,
        fabrica_cola=_cola, fabrica_blob=_blob,
    )


def main() -> int:
    settings = Settings()
    configure_logging(Path(settings.log_dir), settings.log_level)

    cliente = SigridWriteClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        empresa=settings.sigrid_empresa,
        timeout_s=settings.sigrid_api_timeout_s,
        max_statements=settings.sigrid_max_statements,
        tip_parte=settings.tip_parte_trabajo,
        est_parte=settings.est_parte_activo,
    )
    # UN lock y UN pipeline para los dos caminos de escritura.
    pipeline = RegistroPipeline(cliente=cliente, settings=settings,
                                lock=threading.Lock())

    if settings.storage_habilitado:
        _arrancar_consumo(settings, pipeline)
    else:
        logger.info("[transfer-cola] DESACTIVADO (faltan COLAS_*): sv5 "
                    "atiende solo por HTTP y sv4 registrara en modo "
                    "sincrono.")

    app = build_app(settings, pipeline=pipeline)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port,
                log_level=settings.log_level.lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
