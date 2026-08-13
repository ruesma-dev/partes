# interface_adapters/queue/transfer_consumer.py
"""Handler de `q-transfer`: aprobacion asincrona de partes (F-002).

Camino de un mensaje:

    q-transfer -> blob 'transfer/peticiones/<id>.json' -> dominio
      -> pipeline.preparar   (FUERA del lock: datos maestros, paralelo)
      -> pipeline.registrar  (el lock lo adquiere el pipeline, R7/R19)
      -> blob 'transfer/resultados/<id>.json' + mensaje q-transfer-result

Dos clases de fallo, tratadas distinto a proposito:

  - **De negocio** (la obra no existe, sigrid-api devuelve error al
    escribir): se publica un resultado `ok=false` con el motivo y el
    mensaje se consume (R14). Reintentarlo daria el mismo error cinco
    veces y acabaria en poison sin que nadie se entere; asi el humano lo
    ve en el portal como `sigrid_estado='error'` y puede reaprobar, que
    es seguro por synckey.
  - **De infraestructura** (blob inaccesible, JSON corrupto, no se puede
    publicar el resultado): la excepcion sube, el mensaje NO se borra y
    reaparece tras el visibility timeout; superados los reintentos va a
    `q-transfer-poison` con su blob intacto (R9).

`pisar_claves` se ignora SIEMPRE: pisar borra lineas de Sigrid y es una
decision humana que viaja por HTTP sincrono, nunca por una cola con
reentregas (R10).
"""
from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from dataclasses import fields
from datetime import datetime, timezone

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaEntrada, ObraEntrada

from interface_adapters.resultado_json import resultado_a_dict

logger = logging.getLogger(__name__)

#: Campos que acepta `LineaEntrada` (el payload puede traer alguno de mas).
_CAMPOS_LINEA = {f.name for f in fields(LineaEntrada)}


def _a_dominio(peticion: dict) -> tuple[ObraEntrada, list[LineaEntrada]]:
    o = peticion.get("obra") or {}
    obra = ObraEntrada(ide=o.get("ide"), codigo=o.get("codigo"),
                       nombre=o.get("nombre"))
    lineas = [
        LineaEntrada(**{k: v for k, v in (l or {}).items()
                        if k in _CAMPOS_LINEA})
        for l in (peticion.get("lineas") or [])
    ]
    return obra, lineas


def _resultado_fallido(error: str) -> dict:
    """Mismo esqueleto que el resultado normal, en negativo (R14)."""
    return {"ok": False, "error": error, "escritas": [], "omitidas": [],
            "ya_registradas": [], "pisadas": [], "borradas": 0,
            "pendientes_confirmacion": []}


def construir_handler_transfer(
    *, pipeline: RegistroPipeline, blob, cola, settings,
) -> Callable[[dict], None]:
    """Handler puro: recibe TODOS sus colaboradores por parametro."""

    def _handler(mensaje: dict) -> None:
        peticion_id = str(mensaje.get("peticion_id") or "")
        nombre_blob = mensaje.get("blob")
        if not nombre_blob:
            raise ValueError(
                f"mensaje de {settings.cola_transfer} sin referencia de blob: "
                f"{mensaje!r}")

        # --- Infraestructura: si esto falla, el mensaje se reintenta (R9).
        crudo = blob.descargar(settings.blob_transfer, nombre_blob)
        peticion = json.loads(crudo.decode("utf-8"))

        obra, lineas = _a_dominio(peticion)
        usuario = peticion.get("usuario")
        registro_ids = [l.registro_id for l in lineas]
        logger.info("[transfer-cola] peticion_id=%s lineas=%s usuario=%s",
                    peticion_id, len(lineas), usuario)

        # --- Negocio: el fallo se TRAZA, no se reintenta (R14).
        try:
            contexto = pipeline.preparar(obra=obra, lineas=lineas)
            resultado = pipeline.registrar(contexto, usuario=usuario)
            cuerpo = resultado_a_dict(resultado)
            logger.info(
                "[transfer-cola] peticion_id=%s escritas=%s omitidas=%s "
                "ya=%s pendientes=%s", peticion_id,
                len(cuerpo["escritas"]), len(cuerpo["omitidas"]),
                len(cuerpo["ya_registradas"]),
                len(cuerpo["pendientes_confirmacion"]))
        except Exception as exc:
            logger.exception("[transfer-cola] peticion_id=%s FALLO el "
                             "pipeline; se publica ok=false", peticion_id)
            cuerpo = _resultado_fallido(str(exc))

        # --- Publicacion del resultado (si falla, se reintenta: R9).
        sobre = {
            "peticion_id": peticion_id,
            "usuario": usuario,
            "procesado_at_utc": datetime.now(timezone.utc).isoformat(),
            # sv4 necesita saber QUE lineas iban en la peticion para poder
            # marcarlas todas en 'error' cuando el fallo es global (R14).
            "registro_ids": registro_ids,
            "resultado": cuerpo,
        }
        destino = f"resultados/{peticion_id}.json"
        blob.subir(settings.blob_transfer, destino,
                   json.dumps(sobre, ensure_ascii=False).encode("utf-8"),
                   content_type="application/json")
        cola.enviar(settings.cola_transfer_result,
                    {"peticion_id": peticion_id, "blob": destino})

    return _handler


def arrancar_workers_transfer(
    *, pipeline: RegistroPipeline, settings, fabrica_cola: Callable[[], object],
    fabrica_blob: Callable[[], object],
) -> list[threading.Thread]:
    """Lanza `settings.transfer_workers` consumidores daemon de `q-transfer`.

    Son N bucles identicos, no un receptor unico con pool de futures: asi
    cada worker reutiliza tal cual el bucle `consumir` con su manejo de
    poison, `max_dequeue` y SIGTERM, sin inventar gestion de visibilidad
    para mensajes en vuelo.

    Cada worker recibe SUS PROPIAS instancias de cliente de cola y blob:
    los clientes del SDK de Azure no estan pensados para compartirse entre
    hilos. Lo que SI comparten los N workers (y el HTTP) es el pipeline y,
    con el, el unico lock de escritura.

    Son daemon a proposito: viven dentro del proceso de la API y no deben
    impedir que uvicorn termine.
    """
    n = max(1, int(getattr(settings, "transfer_workers", 1) or 1))
    hilos: list[threading.Thread] = []
    for i in range(n):
        cola = fabrica_cola()
        blob = fabrica_blob()
        handler = construir_handler_transfer(
            pipeline=pipeline, blob=blob, cola=cola, settings=settings)
        hilo = threading.Thread(
            target=_bucle_worker, args=(i, cola, settings.cola_transfer,
                                        handler),
            name=f"transfer-worker-{i}", daemon=True)
        hilo.start()
        hilos.append(hilo)
    logger.info("[transfer-cola] %s worker(s) consumiendo '%s'", n,
                settings.cola_transfer)
    return hilos


def _bucle_worker(indice: int, cola, nombre_cola: str,
                  handler: Callable[[dict], None]) -> None:
    """Bucle de un worker. Si revienta, se lleva SOLO su hilo (R22).

    Los fallos por mensaje ya los absorbe `ColaCliente.consumir`; lo que
    se atrapa aqui es la caida del bucle entero, que sin este `except`
    subiria como excepcion no capturada de un hilo y se perderia en el log
    sin decir de quien era.
    """
    try:
        cola.consumir(nombre_cola, handler)
    except Exception:
        logger.exception("[transfer-cola] worker %s termino por un fallo del "
                         "bucle de consumo; los demas siguen", indice)
