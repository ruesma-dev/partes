# infrastructure/database/recalculo_seguimiento.py
"""Marca de «recalculo terminado» en `parte_documents` (F-043, R27-R32).

sv4 escribe `recalculo_pedido_id` (uuid4) y su hora en el documento ANTES
de publicar el recalculo de F-042. sv3:

  1. lee ese pedido antes de la pasada (`pedido_actual`);
  2. tras una pasada sin excepcion, lo copia a `recalculo_terminado_id`
     (`marcar_terminado`) SOLO si el documento sigue con ese pedido.

El UPDATE condicional es lo que hace correcto el desorden (R32): si sv4
escribio un pedido mas nuevo durante la pasada, esta no lo marca (la
pasada que lo atienda lo hara), repetir el mensaje no cambia nada y un
mensaje viejo nunca marca un pedido posterior. No se comparan relojes.

sv3 no decide si el parte esta «en espera»: eso lo hace sv4 con las dos
columnas y el plazo (`seguimiento_recalculo.py` de sv4).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select, update

from infrastructure.database.orm_models import ParteDocumentOrm


def _ahora_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqlAlchemyRecalculoSeguimiento:
    """Lee el pedido de sv4 y marca el terminado de sv3."""

    def __init__(self, session_factory: Any,
                 reloj: Callable[[], str] = _ahora_utc_iso) -> None:
        self._session_factory = session_factory
        self._reloj = reloj

    def pedido_actual(self, document_id: str) -> str | None:
        """El `recalculo_pedido_id` del documento (None si no hay)."""
        with self._session_factory.create_session() as session:
            return session.execute(
                select(ParteDocumentOrm.recalculo_pedido_id)
                .where(ParteDocumentOrm.id == document_id)
            ).scalar_one_or_none()

    def marcar_terminado(self, document_id: str, peticion_id: str) -> bool:
        """Copia `peticion_id` a terminado si sigue siendo el pedido.

        True si toco una fila (repetirlo vuelve a dar True: idempotente).
        """
        with self._session_factory.create_session() as session:
            resultado = session.execute(
                update(ParteDocumentOrm)
                .where(ParteDocumentOrm.id == document_id,
                       ParteDocumentOrm.recalculo_pedido_id == peticion_id)
                .values(recalculo_terminado_id=peticion_id,
                        recalculo_terminado_at_utc=self._reloj())
                .execution_options(synchronize_session=False))
            session.commit()
            return resultado.rowcount == 1
