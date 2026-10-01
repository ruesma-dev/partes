# application/services/comprobacion_sigrid.py
"""F-024 · ¿Siguen en Sigrid las lineas que el portal da por registradas?

Administracion puede borrar en Sigrid lineas que escribio sv5. El portal
lo detecta al abrir la vista de una obra o de una persona (en segundo
plano, desde el navegador) o con el boton «Comprobar en Sigrid»:

  vista/boton -> POST /api/sigrid/comprobar -> ComprobacionSigrid
     -> RegistroComprobaciones (antimartilleo por id, R19)
     -> sv5 /api/registro/comprobar (solo lectura, lotes de 500)
     -> repositorio.aplicar_comprobacion_sigrid (CAS por linea)

sv4 no lee Sigrid ni conoce el formato del `synckey`: eso es de sv5.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)


class RegistroComprobaciones:
    """Antimartilleo (R19): un id comprobado o EN CURSO no vuelve a sv5
    sin `forzar` hasta pasados `ttl_s` segundos en este proceso.

    Se sella al RESERVAR, no al terminar: asi un id en curso no se envia
    dos veces y un lote fallido no se reintenta en cada recarga contra un
    sv5 caido. Seguro entre hilos; purga las entradas caducadas en cada
    reserva para no crecer sin limite.
    """

    def __init__(self, *, ttl_s: float,
                 reloj: Callable[[], float] = time.monotonic) -> None:
        self._ttl = float(ttl_s)
        self._reloj = reloj
        self._lock = threading.Lock()
        self._sellos: dict[int, float] = {}

    def reservar(self, ids: Iterable[int], *, forzar: bool) -> list[int]:
        """Los ids que hay que enviar a sv5 (en el orden recibido, sin
        repetir); quedan sellados con la hora de ahora."""
        with self._lock:
            ahora = self._reloj()
            self._sellos = {i: t for i, t in self._sellos.items()
                            if ahora - t < self._ttl}
            nuevos = [i for i in dict.fromkeys(int(x) for x in ids)
                      if forzar or i not in self._sellos]
            for i in nuevos:
                self._sellos[i] = ahora
            return nuevos

    def vigentes(self) -> int:
        """Ids sellados ahora mismo (diagnostico y tests)."""
        with self._lock:
            return len(self._sellos)
