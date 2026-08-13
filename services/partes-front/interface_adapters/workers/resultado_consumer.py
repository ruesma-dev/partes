# interface_adapters/workers/resultado_consumer.py
"""Consumidor de `q-transfer-result`: cierra el lazo de la aprobacion.

Cuando la aprobacion pasa a asincrona, el veredicto por linea (escrita /
omitida / ya registrada / conflicto) deja de llegar en la respuesta HTTP.
Alguien tiene que volcarlo igualmente en las columnas `sigrid_*`, y ese
alguien es sv4: es el unico dueno de `parte_registros` en este flujo, y
asi sv5 sigue sin BBDD ni credencial de PostgreSQL.

El hilo vive DENTRO del proceso web y es daemon: no debe impedir que
uvicorn termine. Con dos replicas del portal, ambas compiten por la cola;
es inocuo, porque el marcado es idempotente (R13).

Los fallos de infraestructura (blob inaccesible, JSON corrupto) suben: el
mensaje no se borra, reaparece tras el visibility timeout y, agotados los
reintentos, acaba en `q-transfer-result-poison`, desde donde el humano
puede reencolarlo a mano desde el portal.
"""
from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable

from infrastructure.transfer.resultado_sigrid import aplicar_resultado

logger = logging.getLogger(__name__)


def construir_handler_resultados(
    *, repository, blob, settings,
) -> Callable[[dict], None]:
    """Handler puro: recibe TODOS sus colaboradores por parametro."""

    def _handler(mensaje: dict) -> None:
        nombre_blob = mensaje.get("blob")
        if not nombre_blob:
            raise ValueError(
                f"mensaje de {settings.cola_transfer_result} sin referencia "
                f"de blob: {mensaje!r}")
        crudo = blob.descargar(settings.blob_transfer, nombre_blob)
        sobre = json.loads(crudo.decode("utf-8"))

        resultado = sobre.get("resultado") or {}
        registro_ids = sobre.get("registro_ids") or []
        usuario = sobre.get("usuario") or getattr(
            settings, "default_reviewer", None)
        n = aplicar_resultado(repository, resultado,
                              registro_ids=registro_ids, usuario=usuario)
        logger.info("[transfer-result] peticion_id=%s ok=%s lineas_marcadas=%s",
                    sobre.get("peticion_id"), resultado.get("ok"), n)

    return _handler


def arrancar_consumidor_resultados(
    *, repository, cola, blob, settings,
) -> threading.Thread:
    """Lanza el hilo daemon que consume `q-transfer-result`."""
    handler = construir_handler_resultados(
        repository=repository, blob=blob, settings=settings)

    def _bucle() -> None:
        try:
            cola.consumir(settings.cola_transfer_result, handler)
        except Exception:
            # Los fallos por mensaje ya los absorbe `consumir`; esto es la
            # caida del bucle entero, que sin este `except` subiria como
            # excepcion no capturada de un hilo y se perderia en el log.
            logger.exception("[transfer-result] el consumidor termino por un "
                             "fallo del bucle; el portal sigue sirviendo")

    hilo = threading.Thread(target=_bucle, name="transfer-result",
                            daemon=True)
    hilo.start()
    logger.info("[transfer-result] consumidor arrancado sobre '%s'",
                settings.cola_transfer_result)
    return hilo
