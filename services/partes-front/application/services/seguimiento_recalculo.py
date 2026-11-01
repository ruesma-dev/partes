# application/services/seguimiento_recalculo.py
"""F-043 · Estado del recalculo de extras de un parte («en espera»).

F-042 hace que sv4 pida a sv3 un recalculo al guardar (o deshacer) la
fecha de un parte, pero sv4 no sabia cuando terminaba. Desde F-043 el
documento lleva una marca a dos manos (`parte_documents`):

  - `recalculo_pedido_id` / `_at_utc`: los escribe sv4 al pedir;
  - `recalculo_terminado_id` / `_at_utc`: sv3 copia ahi el pedido que
    leyo cuando termina la pasada.

Con esas columnas y la hora, `estado_seguimiento` decide (glosario de la
spec):

  - `sin_seguimiento`: no hay pedido (partes anteriores o sin cola);
  - `terminado`: sv3 marco el ultimo pedido;
  - `pendiente`: distintos y el pedido tiene `ESPERA_MAX_S` o menos: el
    parte esta **en espera** (filas deshabilitadas y ediciones con 409);
  - `vencido`: distintos y el pedido es mas viejo (o su hora no se lee):
    algo fallo; el parte se edita como siempre para no bloquearlo nunca
    mas de 10 min (DA13).

F-047: el pedido tambien lo escribe sv3 al guardar un parte nuevo, con
el id del propio documento. `motivo_espera` lo distingue: `nuevo` (pedido
= id) o `recalculo` (el uuid4 de sv4). El estado no cambia por el motivo.

`RecalculandoError` es la guarda del parte en espera (R38): subclase de
`CongeladoError` para que el manejador 409 de F-004 y los `except
CongeladoError` existentes la traten sin cambios.

Modulo PURO (ni BBDD, ni FastAPI, ni ORM), como `congelacion.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from application.services.congelacion import CongeladoError

#: Estados del seguimiento (respuesta de `GET /api/recalculo`).
ESTADO_SIN_SEGUIMIENTO = "sin_seguimiento"
ESTADO_TERMINADO = "terminado"
ESTADO_VENCIDO = "vencido"
ESTADO_PENDIENTE = "pendiente"
#: Documento desconocido o en papelera (solo el endpoint).
ESTADO_NO_EXISTE = "no_existe"

#: Segundos que un pedido sin terminar deja el parte en espera (DA13).
#: Constante en codigo a proposito: no es configuracion de despliegue.
ESPERA_MAX_S = 600

#: F-047 (R11): por que espera un parte. `nuevo`: lo guardo sv3 y aun no
#: ha repartido sus horas; `recalculo`: sv4 pidio un recalculo (F-042).
MOTIVO_NUEVO = "nuevo"
MOTIVO_RECALCULO = "recalculo"

#: Motivo del 409 de una edicion sobre un parte en espera (R38).
MOTIVO_RECALCULANDO = (
    "El parte se está recalculando (extras): espera a que termine.")


class RecalculandoError(CongeladoError):
    """Edicion rechazada porque sv3 esta recalculando el parte (R38)."""

    def __init__(self) -> None:
        super().__init__(MOTIVO_RECALCULANDO)


def _hora_utc(texto: str | None) -> datetime | None:
    """La hora ISO del pedido, en UTC; None si no se puede leer."""
    try:
        hora = datetime.fromisoformat(texto)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if hora.tzinfo is None:
        hora = hora.replace(tzinfo=timezone.utc)
    return hora


def motivo_espera(document_id: str | None, pedido_id: str | None) -> str:
    """F-047 (R11): `nuevo` si el pedido es el id del propio documento (lo
    escribio sv3 al guardarlo); `recalculo` en cualquier otro caso."""
    if pedido_id and pedido_id == document_id:
        return MOTIVO_NUEVO
    return MOTIVO_RECALCULO


def estado_seguimiento(pedido_id: str | None, terminado_id: str | None,
                       pedido_at_utc: str | None, ahora: datetime) -> str:
    """Estado del recalculo de un documento (glosario de la spec)."""
    if not pedido_id:
        return ESTADO_SIN_SEGUIMIENTO
    if pedido_id == terminado_id:
        return ESTADO_TERMINADO
    pedido_at = _hora_utc(pedido_at_utc)
    if pedido_at is None:
        return ESTADO_VENCIDO
    if (ahora - pedido_at).total_seconds() > ESPERA_MAX_S:
        return ESTADO_VENCIDO
    return ESTADO_PENDIENTE
