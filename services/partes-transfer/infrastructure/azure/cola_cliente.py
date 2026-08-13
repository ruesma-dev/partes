# infrastructure/azure/cola_cliente.py
"""Cliente de Storage Queue + bucle de consumo de partes-transfer (sv5).

Adaptacion del adaptador de sv3 (mismo patron operativo: mensajes JSON con
la referencia al blob, auth por managed identity o connection string local,
semantica at-least-once). Dos diferencias:

  - la traza va por `peticion_id` (sv5 no maneja `document_id`);
  - `detener()` es publico: sv5 consume en hilos daemon dentro del proceso
    de la API, donde `signal` no siempre esta disponible (solo el hilo
    principal puede instalar manejadores).

Idempotencia at-least-once: si el handler falla, el mensaje NO se borra y
reaparece tras el visibility timeout; superado `max_dequeue`, se copia a
'<cola>-poison' y se borra de la principal. El blob de la peticion NO se
borra nunca desde aqui (R9): es la unica prueba de lo que se pidio.
"""
from __future__ import annotations

import json
import logging
import signal
import time
from typing import Callable

from azure.storage.queue import QueueClient, QueueServiceClient

logger = logging.getLogger(__name__)


class ColaCliente:
    def __init__(
        self,
        account_url: str | None = None,
        credential=None,
        *,
        connection_string: str | None = None,
        max_dequeue: int = 5,
        visibility_timeout_s: int = 600,
        poll_interval_s: int = 5,
    ) -> None:
        # Dos modos (patron albaranes):
        #  - connection_string: local/Azurite (o cuenta con clave).
        #  - account_url + credential: nube (managed identity / az login).
        if connection_string:
            self._svc = QueueServiceClient.from_connection_string(
                connection_string
            )
        elif account_url:
            self._svc = QueueServiceClient(
                account_url=account_url.rstrip("/"), credential=credential
            )
        else:
            raise ValueError(
                "ColaCliente requiere COLAS_CONNECTION_STRING (local/Azurite)"
                " o COLAS_ACCOUNT_URL (nube)."
            )
        self._max_dequeue = int(max_dequeue)
        self._vt = int(visibility_timeout_s)
        self._poll = int(poll_interval_s)
        self._stop = False

    def detener(self) -> None:
        """Pide al bucle de consumo que termine tras el mensaje en curso."""
        self._stop = True

    def asegurar_colas(self, nombres: list[str]) -> None:
        """Crea las colas (y sus '-poison') si no existen. Para el modo
        local con Azurite, que arranca vacio; idempotente."""
        from azure.core.exceptions import ResourceExistsError
        todos: list[str] = []
        for n in nombres:
            todos.extend((n, f"{n}-poison"))
        for n in todos:
            try:
                self._svc.create_queue(n)
                logger.info("[cola] creada cola '%s'", n)
            except ResourceExistsError:
                pass

    # -- Productor ----------------------------------------------------------
    def enviar(self, queue_name: str, payload: dict) -> None:
        qc = self._svc.get_queue_client(queue_name)
        qc.send_message(json.dumps(payload, ensure_ascii=False))
        logger.info("[cola] -> %s peticion_id=%s", queue_name,
                    payload.get("peticion_id"))

    # -- Consumidor (bucle) -------------------------------------------------
    def consumir(self, queue_name: str, handler: Callable[[dict], None]) -> None:
        principal: QueueClient = self._svc.get_queue_client(queue_name)
        poison: QueueClient = self._svc.get_queue_client(f"{queue_name}-poison")

        # Salida limpia ante SIGTERM (Container Apps reinicia o escala).
        def _sig(_signum, _frame):
            logger.info("[cola] SIGTERM recibido; terminando tras el mensaje "
                        "actual.")
            self._stop = True
        try:
            signal.signal(signal.SIGTERM, _sig)
            signal.signal(signal.SIGINT, _sig)
        except (ValueError, OSError):
            pass  # no en hilo principal: ignorable

        logger.info("[cola] consumiendo '%s' (vt=%ss, max_dequeue=%s)",
                    queue_name, self._vt, self._max_dequeue)
        while not self._stop:
            got = False
            for msg in principal.receive_messages(
                messages_per_page=1, visibility_timeout=self._vt
            ):
                got = True
                peticion_id = "?"
                try:
                    payload = json.loads(msg.content)
                    peticion_id = payload.get("peticion_id", "?")
                    if msg.dequeue_count and msg.dequeue_count > self._max_dequeue:
                        logger.error(
                            "[cola] %s peticion_id=%s supero max_dequeue=%s "
                            "-> poison", queue_name, peticion_id,
                            self._max_dequeue)
                        poison.send_message(msg.content)
                        principal.delete_message(msg)
                        continue
                    handler(payload)
                    principal.delete_message(msg)
                    logger.info("[cola] OK %s peticion_id=%s (dequeue=%s)",
                                queue_name, peticion_id, msg.dequeue_count)
                except Exception:  # noqa: BLE001
                    # No se borra: reaparece tras el visibility timeout.
                    logger.exception(
                        "[cola] FALLO %s peticion_id=%s (dequeue=%s); se "
                        "reintentara.", queue_name, peticion_id,
                        getattr(msg, "dequeue_count", "?"))
                if self._stop:
                    break
            if not got and not self._stop:
                time.sleep(self._poll)
        logger.info("[cola] consumo de '%s' detenido.", queue_name)
