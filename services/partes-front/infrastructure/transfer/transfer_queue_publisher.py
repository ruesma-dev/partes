# infrastructure/transfer/transfer_queue_publisher.py
"""Publicacion de peticiones de registro en `q-transfer` (F-002).

El payload completo va a un blob y por la cola viaja solo la referencia:
una obra x mes son cientos de lineas y superan de sobra los 64 KB que
admite un mensaje de Storage Queue. Mismo patron que el hand-off
sv1 -> sv2 -> sv3.

El blob se sube ANTES de encolar el mensaje. El orden importa: al reves,
un fallo entre ambos pasos dejaria en la cola un mensaje que apunta a un
blob inexistente, y sv5 lo reintentaria hasta acabar en poison. Asi, el
fallo deja como mucho un blob huerfano que nadie lee.

`pisar_claves` se vacia siempre: pisar borra lineas de Sigrid, es una
decision humana del modal y viaja por HTTP sincrono (R5/R10).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TransferQueuePublisher:
    def __init__(self, *, cola, blob, cola_transfer: str,
                 contenedor: str) -> None:
        self._cola = cola
        self._blob = blob
        self._cola_transfer = cola_transfer
        self._contenedor = contenedor

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        """Sube la peticion y la encola. Devuelve el `peticion_id`."""
        peticion_id = str(uuid.uuid4())
        nombre = f"peticiones/{peticion_id}.json"
        lineas = payload.get("lineas") or []
        sobre = {
            "peticion_id": peticion_id,
            "usuario": usuario if usuario is not None
            else payload.get("usuario"),
            "creado_at_utc": datetime.now(timezone.utc).isoformat(),
            "obra": payload.get("obra") or {},
            "lineas": lineas,
            "pisar_claves": [],
        }
        self._blob.subir(
            self._contenedor, nombre,
            json.dumps(sobre, ensure_ascii=False).encode("utf-8"),
            content_type="application/json")
        self._cola.enviar(self._cola_transfer,
                          {"peticion_id": peticion_id, "blob": nombre})
        logger.info("[transfer-cola] encolada peticion_id=%s lineas=%s "
                    "usuario=%s", peticion_id, len(lineas), sobre["usuario"])
        return peticion_id
