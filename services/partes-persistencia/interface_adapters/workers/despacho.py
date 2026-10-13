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

El `document_id` del recalculo no acota la pasada: `conciliar_todos`
recalcula siempre todo lo activo, porque la jornada se mide por trabajador
y dia entre obras y partes.

Seguimiento (F-043, R27-R32): con `recalculo_seguimiento`, un recalculo
lee ANTES de la pasada el `recalculo_pedido_id` que sv4 escribio en ese
documento y, si la pasada acaba sin excepcion, lo marca «terminado» (el
adaptador solo lo hace si el documento sigue con ese pedido). Leer o
marcar que fallan dejan un WARNING y el mensaje se consume (DA7): la
pasada ya esta hecha y sv4 da el parte por `vencido` a los 10 min.
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
    recalculo_seguimiento: Any = None,
) -> Callable[[dict], None]:
    """El handler de `q-persistencia`. `recurso_conciliador` es None
    cuando sv3 arranca sin Sigrid cableado (R17); sin
    `recalculo_seguimiento`, el recalculo es el de F-042 (R31)."""

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
        pedido = _pedido_leido(document_id)
        res = recurso_conciliador.conciliar_todos()
        logger.info("[sv3-worker] recalculo motivo=%s document_id=%s por=%s "
                    "-> %s", motivo, document_id, por, res)
        if pedido is not None:
            _marcar_terminado(document_id, pedido)

    def _pedido_leido(document_id: Any) -> str | None:
        """El pedido de sv4 antes de la pasada (R27); None si no se
        sigue o si leerlo falla (R30: se recalcula igual, sin marcar)."""
        if recalculo_seguimiento is None or not isinstance(document_id, str):
            return None
        try:
            return recalculo_seguimiento.pedido_actual(document_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[sv3-worker] no se pudo leer el pedido de recalculo "
                "document_id=%s (%s): se recalcula sin marcar terminado.",
                document_id, type(exc).__name__)
            return None

    def _marcar_terminado(document_id: str, pedido: str) -> None:
        """R28/R30: marca el pedido leido; si falla, WARNING y se
        consume el mensaje."""
        try:
            marcado = recalculo_seguimiento.marcar_terminado(document_id,
                                                             pedido)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[sv3-worker] no se pudo marcar el recalculo terminado "
                "document_id=%s (%s): sv4 lo dara por vencido.",
                document_id, type(exc).__name__)
            return
        logger.info("[sv3-worker] recalculo terminado document_id=%s "
                    "marcado=%s", document_id, marcado)

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
