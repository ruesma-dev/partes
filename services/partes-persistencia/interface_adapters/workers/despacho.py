# interface_adapters/workers/despacho.py
"""Handler del worker de sv3 sobre `q-persistencia` (F-042, R12-R17).

`construir_handler` devuelve la funcion que `ColaCliente.consumir` llama
con cada mensaje. Segun su clase (`mensajes.clasificar`):

  - **ingesta**: lo de siempre. Descarga el PDF y el envelope y ejecuta el
    pipeline de persistencia (cuerpo movido sin cambios desde
    `main_worker.py`).
  - **recalculo**: UNA pasada de `RecursoConciliador.conciliar_todos`, la
    misma que sigue a cada ingesta, sin blobs, sin pipeline y sin partidas.
    Sin `try/except` a proposito (DA3): aqui la pasada ES el trabajo, asi
    que si falla el mensaje no se borra, se reintenta y, al agotar
    `max_dequeue`, acaba en `q-persistencia-poison`. Por eso no se
    reutiliza `_conciliar_recursos_safely`, que traga el error porque alli
    lo que importa es haber guardado el parte.
  - **desconocido**: ERROR en el log y se relanza (mismo camino).

El `document_id` del recalculo es solo traza: `conciliar_todos` recalcula
siempre todo lo activo, porque la jornada se mide por trabajador y dia
entre obras y partes.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Any, Callable

from application.pipelines.persist_parte_pipeline import PersistParteRequest
from interface_adapters.workers.mensajes import (
    CLASE_RECALCULO,
    MensajeDesconocido,
    clasificar,
)

logger = logging.getLogger(__name__)


def construir_handler(
    *,
    blob: Any,
    pipeline: Any,
    recurso_conciliador: Any,
    contenedor_input: str,
    contenedor_envelopes: str,
) -> Callable[[dict], None]:
    """El handler de `q-persistencia`. `recurso_conciliador` es None
    cuando sv3 arranca sin Sigrid cableado (R17)."""

    def _ingerir(payload: dict) -> None:
        document_id = payload["document_id"]
        filename = payload.get("filename", "document.pdf")
        mime = payload.get("mime_type", "application/pdf")
        context = payload.get("context", {})
        pdf = blob.descargar(contenedor_input, f"{document_id}.pdf")
        envelope = json.loads(
            blob.descargar(contenedor_envelopes, f"{document_id}.json"))
        result = pipeline.run(PersistParteRequest(
            filename=filename, mime_type=mime, file_bytes=pdf,
            extraction_envelope=envelope,
            context=context if isinstance(context, dict) else {}))
        logger.info("[sv3-worker] persistido document_id=%s -> %s",
                    document_id, asdict(result))

    def _recalcular(payload: dict) -> None:
        motivo = payload.get("motivo")
        document_id = payload.get("document_id")
        por = payload.get("solicitado_por")
        if recurso_conciliador is None:
            logger.warning(
                "[sv3-worker] recalculo pedido pero Sigrid no esta cableado: "
                "se da por consumido sin recalcular (motivo=%s "
                "document_id=%s por=%s)", motivo, document_id, por)
            return
        res = recurso_conciliador.conciliar_todos()
        logger.info("[sv3-worker] recalculo motivo=%s document_id=%s por=%s "
                    "-> %s", motivo, document_id, por, res)

    def handler(payload: dict) -> None:
        try:
            clase = clasificar(payload)
        except MensajeDesconocido as exc:
            logger.error("[sv3-worker] mensaje desconocido en la cola: %s; "
                         "se reintentara y acabara en la poison.", exc)
            raise
        if clase == CLASE_RECALCULO:
            _recalcular(payload)
            return
        _ingerir(payload)

    return handler
