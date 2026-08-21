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
from interface_adapters.web.identidad import ACTOR_SIN_IDENTIDAD

logger = logging.getLogger(__name__)


def _quien_firma(sobre: dict) -> str:
    """F-017 R18/R24: quien firma el marcado de un resultado encolado.

    Aqui NO hay peticion HTTP ni cabecera de Easy Auth que leer: este hilo
    consume una cola. La identidad tiene que venir en el sobre, que viaja
    firmado desde `aprobar_encolar` con el actor real (R16). **El sobre
    manda, y su valor se respeta intacto**: ya viene normalizado del punto
    unico, y reprocesarlo aqui solo podria estropearlo.

    Si el sobre NO trae usuario, el fallback es `sin-identidad` — el mismo
    valor de R5b, y por el mismo motivo. Este consumidor corre **siempre
    desplegado** (vive dentro del proceso web de `ca-sv4-front`), asi que
    un sobre sin firma no es «una sesion sin identificar»: es una anomalia
    —tipicamente un mensaje publicado ANTES del corte de F-017 y aun en
    vuelo— que **debe verse en el log**, no colarse en una columna.

    Lo que NO se hace aqui, y es deliberado (defecto 1 del review de
    F-017, 2026-08-20):

    * **No se lee `settings.default_reviewer`.** Hasta esta correccion la
      linea era `sobre.get("usuario") or getattr(settings,
      "default_reviewer", None)`: una TERCERA lectura de identidad, fuera
      del punto unico (R10/R11), sin test, e invisible para el guardian
      —que solo miraba `app.py`—. Contradecia ademas lo que la feature
      publica en tres documentos: estando desplegado, `DEFAULT_REVIEWER`
      no firma nada.
    * **No se devuelve `None`.** Devolverlo dejaba
      `sigrid_registrado_by = NULL` **despues** del corte y rompia el
      criterio «`autor IS NULL` ⇔ fila anterior a F-017» justo en la
      ventana del despliegue, que es cuando hay mensajes en vuelo.
    """
    usuario = sobre.get("usuario")
    if isinstance(usuario, str) and usuario.strip():
        return usuario
    logger.warning(
        "[identidad] resultado de q-transfer-result SIN usuario en el sobre "
        "(peticion_id=%s): se sella '%s'. Sobre publicado antes de F-017 y "
        "aun en vuelo, o publicador que no firma.",
        sobre.get("peticion_id"), ACTOR_SIN_IDENTIDAD)
    return ACTOR_SIN_IDENTIDAD


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
        usuario = _quien_firma(sobre)
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
