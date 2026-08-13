# infrastructure/transfer/resultado_sigrid.py
"""Traduccion del resultado de sv5 a las columnas `sigrid_*` (F-002).

Un unico sitio que conoce la forma del JSON de sv5, porque hay DOS
caminos por los que ese JSON llega a sv4 y tienen que marcar igual:

  - la respuesta HTTP sincrona (`/api/aprobar/ejecutar` y el fallback de
    `/api/aprobar/encolar` sin colas configuradas);
  - el mensaje de `q-transfer-result` que consume el hilo del portal.

Duplicar el mapeo era la via directa a que un canal marcara los
conflictos y el otro no.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MOTIVO_SIN_DETALLE = "sv5 no pudo completar el registro"


def aplicar_resultado(repository, resultado: dict, *,
                      registro_ids: list[int] | None,
                      usuario: str | None) -> int:
    """Marca las lineas segun el veredicto. Devuelve cuantas cambiaron."""
    if not resultado.get("ok"):
        # R14: fallo global -> la peticion entera queda en 'error' para
        # que el humano pueda reaprobar (seguro por synckey).
        return repository.marcar_registros_sigrid(
            escritas=[], omitidas=[], ya_registradas=[], usuario=usuario,
            registro_ids=registro_ids or [],
            error_global=str(resultado.get("error") or MOTIVO_SIN_DETALLE),
        )
    return repository.marcar_registros_sigrid(
        escritas=resultado.get("escritas") or [],
        omitidas=resultado.get("omitidas") or [],
        ya_registradas=resultado.get("ya_registradas") or [],
        conflictos=resultado.get("pendientes_confirmacion") or [],
        usuario=usuario,
    )
