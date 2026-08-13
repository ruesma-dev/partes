# infrastructure/azure/cola_cliente.py
"""Cliente de Storage Queue del portal (sv4).

Mismo patron que los adaptadores de sv1/sv2/sv3 y sv5 (mensajes JSON con
la referencia al blob, auth por managed identity o connection string
local, semantica at-least-once). Cada servicio lleva los suyos: la
arquitectura no tiene libreria compartida y los servicios se acoplan solo
por mensajes.

sv4 lo usa en tres papeles:
  - PRODUCTOR de `q-transfer` (aprobacion asincrona);
  - CONSUMIDOR de `q-transfer-result` (traza del resultado por linea), en
    un hilo daemon dentro del proceso web;
  - GESTOR de las colas `-poison` desde el portal: recuento aproximado y
    reencolado manual.

Idempotencia at-least-once: si el handler falla, el mensaje NO se borra y
reaparece tras el visibility timeout; superado `max_dequeue`, se copia a
'<cola>-poison' y se borra de la principal.
"""
from __future__ import annotations

import json
import logging
import signal
import time
from collections.abc import Callable

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

    # -- Gestion de las colas '-poison' (desde el portal) --------------------
    def contar_aproximado(self, queue_name: str) -> int:
        """Mensajes en la cola, segun la API de Storage.

        Es aproximado y basta: esto alimenta un AVISO, no un contador
        contable. La accion de reencolar vuelve a leer la cola de verdad.
        """
        props = self._svc.get_queue_client(queue_name).get_queue_properties()
        return int(getattr(props, "approximate_message_count", 0) or 0)

    def mover(self, origen: str, destino: str,
              maximo: int = 32) -> list[str]:
        """Reencola hasta `maximo` mensajes de `origen` a `destino`.

        El orden es SEND y despues DELETE, nunca al reves. Si falla entre
        medias, el mensaje queda duplicado —inocuo: el procesamiento es
        idempotente por synckey y el marcado tambien—, pero NUNCA se
        pierde, que es la propiedad que importa en una DLQ.

        Devuelve los ids movidos. Se registra cada uno con su contenido:
        es una accion manual sobre mensajes que ya fallaron, y conviene
        poder reconstruir despues que se movio y cuando.
        """
        cola_origen: QueueClient = self._svc.get_queue_client(origen)
        cola_destino: QueueClient = self._svc.get_queue_client(destino)
        movidos: list[str] = []
        # Acotado por `maximo` tambien en numero de vueltas: un delete que
        # falla no puede convertir esto en un bucle infinito de reenvios.
        for _ in range(int(maximo)):
            lote = list(cola_origen.receive_messages(
                messages_per_page=1, visibility_timeout=self._vt))
            if not lote:
                break
            for msg in lote:
                mid = getattr(msg, "id", "?")
                try:
                    cola_destino.send_message(msg.content)
                except Exception:
                    logger.exception(
                        "[poison] no se pudo reencolar %s de %s; se deja "
                        "donde estaba", mid, origen)
                    return movidos
                logger.info("[poison] %s -> %s id=%s contenido=%s",
                            origen, destino, mid, msg.content)
                movidos.append(mid)
                try:
                    cola_origen.delete_message(msg)
                except Exception:
                    # Ya esta en la principal: se procesara. Como no se
                    # pudo borrar de la poison, reaparecera y podria
                    # reencolarse otra vez; el duplicado es benigno.
                    logger.warning(
                        "[poison] %s reencolado pero NO borrado de %s: "
                        "puede duplicarse (inocuo por synckey)", mid,
                        origen, exc_info=True)
                if len(movidos) >= int(maximo):
                    break
        return movidos

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
                except Exception:
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
