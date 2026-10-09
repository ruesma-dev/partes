# infrastructure/persistencia/recalculo_publisher.py
"""Peticion de recalculo de extras a sv3 por `q-persistencia` (F-042).

El reparto ordinaria/extra lo calcula SOLO sv3 (`conciliar_todos`), y
solo cuando le llega un mensaje por `q-persistencia`. Cambiar la fecha de
un parte en el portal dejaba el reparto del dia viejo hasta la siguiente
ingesta, y en esa ventana alguien podia aprobarlo y congelarlo. sv4 no
recalcula nada: solo PIDE la pasada de siempre.

Mensaje (`mensaje_recalculo`):

    {"tipo": "recalcular", "motivo": "cambio_fecha" | "deshacer_cambio_fecha",
     "document_id": "<uuid>", "solicitado_por": "<actor o null>",
     "solicitado_at_utc": "<ISO 8601 UTC>"}

El mensaje de sv2 por la misma cola no lleva `tipo`: ese es el
discriminante. Contrato de transporte, no logica: su gemelo en sv3 es
`interface_adapters/workers/mensajes.py` y los ata el test de la raiz
`tests/test_f042_contrato_recalculo.py`, que carga este modulo por ruta.
Por eso **solo importa la biblioteca estandar**.

Publicar es best-effort para el portal: la fecha ya esta guardada cuando
se pide el recalculo, y un fallo de la cola no puede deshacerla. Por eso
`pedir_recalculo` nunca lanza y devuelve el estado que pinta la pantalla.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)

#: Valor de `tipo` que sv3 reconoce como recalculo.
TIPO_RECALCULAR = "recalcular"

#: Motivos (solo traza: sv3 hace la misma pasada para los dos).
MOTIVO_CAMBIO_FECHA = "cambio_fecha"
MOTIVO_DESHACER_FECHA = "deshacer_cambio_fecha"

#: Estado del recalculo en la respuesta del portal (`recalculo`).
ESTADO_PEDIDO = "pedido"
ESTADO_FALLO = "fallo"
ESTADO_SIN_COLA = "sin_cola"

#: Del peor al mejor: con varios recalculos, la pantalla avisa del peor.
_GRAVEDAD = (ESTADO_FALLO, ESTADO_SIN_COLA, ESTADO_PEDIDO)


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def mensaje_recalculo(*, document_id: str, motivo: str,
                      solicitado_por: str | None,
                      ahora: datetime) -> dict:
    """El mensaje del contrato (funcion pura)."""
    return {
        "tipo": TIPO_RECALCULAR,
        "motivo": motivo,
        "document_id": document_id,
        "solicitado_por": solicitado_por,
        "solicitado_at_utc": ahora.astimezone(timezone.utc).isoformat(),
    }


class RecalculoPublisher:
    """Publica el mensaje de recalculo con el cliente de cola del portal."""

    def __init__(self, *, cola: Any, cola_persistencia: str,
                 reloj: Callable[[], datetime] = _ahora_utc) -> None:
        self._cola = cola
        self._cola_persistencia = cola_persistencia
        self._reloj = reloj

    def pedir(self, *, document_id: str, motivo: str,
              solicitado_por: str | None) -> None:
        """Encola el recalculo. LANZA si la cola falla."""
        mensaje = mensaje_recalculo(
            document_id=document_id, motivo=motivo,
            solicitado_por=solicitado_por, ahora=self._reloj())
        self._cola.enviar(self._cola_persistencia, mensaje)
        logger.info("[recalculo] pedido a %s motivo=%s document_id=%s por=%s",
                    self._cola_persistencia, motivo, document_id,
                    solicitado_por)


def pedir_recalculo(publisher: RecalculoPublisher | None, *,
                    document_id: str, motivo: str,
                    solicitado_por: str | None) -> str:
    """`pedido`, `fallo` o `sin_cola`. Nunca lanza (R3, R4)."""
    if publisher is None:
        return ESTADO_SIN_COLA
    try:
        publisher.pedir(document_id=document_id, motivo=motivo,
                        solicitado_por=solicitado_por)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[recalculo] no se pudo pedir el recalculo de extras "
            "document_id=%s (%s); la fecha SI esta guardada.",
            document_id, type(exc).__name__)
        return ESTADO_FALLO
    return ESTADO_PEDIDO


def peor_estado(estados: Iterable[str]) -> str:
    """El estado mas grave de varios: `fallo` > `sin_cola` > `pedido`.

    Lo usa deshacer, que podria pedir mas de un recalculo (uno por
    documento de la entrada; en la practica, uno).
    """
    return min(estados, key=_GRAVEDAD.index)
