# interface_adapters/workers/mensajes.py
"""Clases de mensaje de `q-persistencia` (F-042, R12).

Por esa cola llegan dos cosas:

  - **ingesta** (sv2): `{"document_id", "filename", "mime_type",
    "context"}`, sin `tipo`. Un parte nuevo que persistir.
  - **recalculo** (sv4): `{"tipo": "recalcular", "motivo", "document_id",
    "solicitado_por", "solicitado_at_utc"}`. Se ha cambiado (o deshecho)
    la fecha de un parte y hay que repetir la pasada de extras.

El discriminante es `tipo`: el mensaje de sv2 no lo lleva, asi que el
formato es compatible hacia atras sin versionar nada. Cualquier otro valor
es un mensaje que este sv3 no sabe tratar y se rechaza (reintento y, al
agotarlos, `q-persistencia-poison`).

Contrato de transporte, no logica: su gemelo en sv4 es
`infrastructure/persistencia/recalculo_publisher.py` y los ata el test de
la raiz `tests/test_f042_contrato_recalculo.py`, que carga este modulo por
ruta. Por eso **solo importa la biblioteca estandar**.
"""
from __future__ import annotations

#: Valor de `tipo` del mensaje de recalculo que publica sv4.
TIPO_RECALCULAR = "recalcular"

#: Lo que devuelve `clasificar`.
CLASE_INGESTA = "ingesta"
CLASE_RECALCULO = "recalcular"


class MensajeDesconocido(ValueError):
    """Un mensaje de `q-persistencia` que no es ni ingesta ni recalculo."""


def clasificar(payload: object) -> str:
    """`ingesta` o `recalcular`; `MensajeDesconocido` si no es ninguno.

    Sin `tipo`, o con `tipo` nulo, es el mensaje de sv2 de siempre.
    """
    if not isinstance(payload, dict):
        raise MensajeDesconocido(
            "se esperaba un objeto JSON y ha llegado "
            f"{type(payload).__name__}")
    tipo = payload.get("tipo")
    if tipo is None:
        return CLASE_INGESTA
    if tipo == TIPO_RECALCULAR:
        return CLASE_RECALCULO
    raise MensajeDesconocido(f"tipo de mensaje desconocido: {tipo!r}")
