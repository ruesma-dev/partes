# infrastructure/calendario/tabla_calendario_laboral.py
"""Calendario laboral con los festivos guardados de cada trabajador (F-032).

Mismo `CalendarioLaboralPort` que `JsonCalendarioLaboral`: el computo de
extras no se entera del cambio de fuente. Lo que decide NO es cosmetico:
en un dia no laborable TODAS las horas ordinarias pasan a extra.

Cascada (design §5.5, DA19 = B):

  1. FIN DE SEMANA: de la propia fecha.
  2. La fila del DNI en `festivos_trabajador` (`festivos_guardados.elegir`).
  3. Sin fila, o sin DNI: el respaldo de siempre (el JSON local).

NUNCA habla con sesame-api (R14): las filas las escribe solo el refresco
de la ingesta. La tabla entera se lee de una vez y se cachea `ttl_s`
segundos (<= 60, R15); `olvidar()` vacia la cache y lo llama el refresco al
guardar, para que la pasada de esa misma ingesta ya use la fila nueva.

Una lectura fallida resuelve ese dia con el respaldo y un WARNING (R16).
No ofrece `consumir_degradacion`: las pasadas no suben partes a revision
por el calendario; eso solo lo hace el refresco (R8).
"""
from __future__ import annotations

import datetime as _dt
import logging
import threading
import time
from typing import Any, Callable

from application.services import text_match as tm
from application.services.festivos_guardados import FilaFestivos, elegir
from domain.ports.calendario_laboral_port import CalendarioLaboralPort

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[festivos-calendario]"


class TablaCalendarioLaboral(CalendarioLaboralPort):
    def __init__(
        self,
        *,
        repositorio: Any,
        respaldo: CalendarioLaboralPort,
        ttl_s: float = 60,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._repositorio = repositorio
        self._respaldo = respaldo
        self._ttl_s = ttl_s
        self._reloj = reloj
        self._lock = threading.RLock()
        #: (momento de la lectura, filas) o None.
        self._cache: tuple[float, dict] | None = None

    # ------------------------------------------------------------- #
    # Puerto.
    # ------------------------------------------------------------- #
    def es_no_laborable(
        self,
        fecha_iso: str,
        *,
        dni: str | None = None,
        localizacion: str | None = None,
        convenio: str | None = None,
    ) -> bool:
        try:
            d = _dt.date.fromisoformat(str(fecha_iso)[:10])
        except (TypeError, ValueError):
            return False
        dia = d.isoformat()
        if d.weekday() >= 5:
            return True
        try:
            fila, _fuente = elegir(tm.normalize_dni(dni), d.year, self._leer)
        except Exception as exc:  # noqa: BLE001 - R16
            logger.warning(
                "%s no se pudo leer festivos_trabajador (%s): el %s se "
                "resuelve con el respaldo.", _LOG_PREFIX,
                type(exc).__name__, dia,
            )
            fila = None
        if fila is not None:
            return dia in fila.festivos
        return self._del_respaldo(dia, dni, localizacion, convenio)

    def olvidar(self) -> None:
        """Vacia la cache: la siguiente consulta relee la tabla (R15)."""
        with self._lock:
            self._cache = None

    # ------------------------------------------------------------- #
    # Interno.
    # ------------------------------------------------------------- #
    def _leer(self, dni_norm: str, ano: int) -> FilaFestivos | None:
        return self._filas().get((dni_norm, ano))

    def _filas(self) -> dict:
        with self._lock:
            ahora = self._reloj()
            if (self._cache is not None
                    and ahora - self._cache[0] < self._ttl_s):
                return self._cache[1]
            filas = dict(self._repositorio.leer_todas())
            self._cache = (ahora, filas)
            return filas

    def _del_respaldo(self, dia: str, dni: str | None,
                      localizacion: str | None, convenio: str | None) -> bool:
        try:
            return bool(self._respaldo.es_no_laborable(
                dia, dni=dni, localizacion=localizacion, convenio=convenio))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s el respaldo fallo en %s (%s): se trata como laborable.",
                _LOG_PREFIX, dia, type(exc).__name__,
            )
            return False
