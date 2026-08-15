# infrastructure/calendario/sesame_calendario_laboral.py
"""Calendario laboral con los festivos REALES de Sesame (F-003).

Implementa el mismo `CalendarioLaboralPort` que `JsonCalendarioLaboral`
—cuyo docstring ya anticipaba este adaptador— asi que el computo de
extras no se entera del cambio de fuente: solo cambia el wiring.

Lo que decide este adaptador NO es cosmetico. En un dia no laborable el
computo manda TODAS las horas ordinarias a horas extra: un festivo que
falte se paga como jornada normal, y uno de mas se paga como extra.

Cascada, en este orden:

  1. FIN DE SEMANA: de la propia fecha, sin preguntar a nadie.
  2. Festivos del calendario del trabajador (`GET /festivos?dni=&ano=`),
     cacheados por (DNI x ano).
  3. Si Sesame no conoce el DNI (404) o no hay DNI: calendario por
     defecto. Sesame ha respondido, el dato es bueno.
  4. Si Sesame falla: la respuesta cacheada aunque haya caducado.
  5. Si tampoco hay cache: el respaldo (`JsonCalendarioLaboral`).

Los pasos 4 y 5 son resoluciones DEGRADADAS: el resultado puede no ser
correcto. No se lanza ninguna excepcion por ello —la persistencia del
parte es best-effort y nunca puede caerse por RRHH (R9)— pero queda la
senal `consumir_degradacion()`, que el conciliador recoge para subir el
parte a `review_required` (R26). Un festivo mal resuelto en silencio es
justo lo que no se puede permitir.

`consumir_degradacion()` NO forma parte del puerto: el conciliador la
descubre por duck-typing y `JsonCalendarioLaboral` no la necesita.
"""
from __future__ import annotations

import datetime as _dt
import logging
import re
import threading
import time
from typing import Callable

from domain.ports.calendario_laboral_port import CalendarioLaboralPort
from infrastructure.sesame.sesame_api_client import SesameApiClient

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-calendario]"


def normalizar_dni(dni: str | None) -> str:
    """Sin separadores y en mayusculas: la clave de identidad de la casa."""
    return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()


class SesameCalendarioLaboral(CalendarioLaboralPort):
    def __init__(
        self,
        *,
        cliente: SesameApiClient,
        respaldo: CalendarioLaboralPort,
        ttl_seconds: int = 21600,
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self._cliente = cliente
        self._respaldo = respaldo
        self._ttl = int(ttl_seconds)
        self._reloj = reloj
        self._lock = threading.RLock()
        #: clave -> (timestamp, {fecha: nombre})
        self._cache: dict[str, tuple[float, dict[str, str | None]]] = {}
        #: True si la ULTIMA resolucion tiro de cache caducada o respaldo.
        self._degradado = False

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
        self._degradado = False
        try:
            d = _dt.date.fromisoformat(str(fecha_iso)[:10])
        except (TypeError, ValueError):
            return False

        # 1) Fin de semana: determinista, no hace falta preguntar.
        if d.weekday() >= 5:
            return True

        try:
            festivos, degradado = self._festivos(normalizar_dni(dni), d.year)
        except Exception as exc:  # noqa: BLE001
            # Cinturon y tirantes: el conciliador ya captura, pero este
            # adaptador NO puede ser la causa de que un parte no se
            # persista.
            logger.warning(
                "%s error inesperado resolviendo %s: %r; se usa el respaldo.",
                _LOG_PREFIX, fecha_iso, exc,
            )
            festivos, degradado = None, True

        self._degradado = degradado
        if festivos is None:
            return self._del_respaldo(fecha_iso, dni, localizacion, convenio)
        return fecha_iso in festivos

    def consumir_degradacion(self) -> bool:
        """True si la ULTIMA resolucion fue a ciegas. Resetea la senal.

        La consume el `RecursoConciliador` despues de cada evaluacion,
        para saber que partes hay que dejar marcados para revision.
        """
        valor = self._degradado
        self._degradado = False
        return valor

    # ------------------------------------------------------------- #
    # Interno.
    # ------------------------------------------------------------- #
    def _del_respaldo(
        self, fecha_iso: str, dni: str | None,
        localizacion: str | None, convenio: str | None,
    ) -> bool:
        try:
            return bool(self._respaldo.es_no_laborable(
                fecha_iso, dni=dni, localizacion=localizacion,
                convenio=convenio))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s el respaldo tambien fallo en %s: %r; se trata como "
                "laborable.", _LOG_PREFIX, fecha_iso, exc,
            )
            return False

    def _festivos(
        self, dni_norm: str, ano: int
    ) -> tuple[dict[str, str | None] | None, bool]:
        """Festivos de ese (DNI, ano) y si la resolucion fue degradada."""
        clave = f"fest:{dni_norm or '_default'}:{ano}"
        vigente = self._de_cache(clave)
        if vigente is not None:
            return vigente, False

        try:
            festivos = None
            if dni_norm:
                festivos = self._cliente.festivos(dni_norm, ano)
            if festivos is None:
                # Sin DNI, o Sesame no lo conoce (404): calendario por
                # defecto. Ha respondido, asi que NO es degradacion.
                festivos = self._cliente.calendario_por_defecto(ano)
        except Exception as exc:  # noqa: BLE001
            return self._degradar(clave, dni_norm, ano, exc)

        if festivos is None:
            logger.warning(
                "%s sin festivos utilizables para dni=%s ano=%s (Sesame no "
                "tiene calendario por defecto): se usa el respaldo.",
                _LOG_PREFIX, dni_norm or "(sin dni)", ano,
            )
            return None, True

        mapa = {f.fecha: f.nombre for f in festivos}
        self._a_cache(clave, mapa)
        logger.info(
            "%s dni=%s ano=%s -> %s festivos.",
            _LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa),
        )
        return mapa, False

    def _degradar(
        self, clave: str, dni_norm: str, ano: int, exc: Exception
    ) -> tuple[dict[str, str | None] | None, bool]:
        """Sesame ha fallado: cache caducada si la hay, si no el respaldo.

        La entrada caducada NO se refresca a proposito: asi el siguiente
        parte vuelve a preguntar en cuanto Sesame se recupere, en vez de
        arrastrar el dato viejo durante horas.
        """
        with self._lock:
            entrada = self._cache.get(clave)
        if entrada is not None:
            logger.warning(
                "%s Sesame no responde (%r) para dni=%s ano=%s: se reutiliza "
                "la respuesta caducada; el parte quedara marcado para "
                "revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,
            )
            return entrada[1], True
        logger.warning(
            "%s Sesame no responde (%r) para dni=%s ano=%s y no hay cache "
            "previa: se usa el respaldo local; el parte quedara marcado para "
            "revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,
        )
        return None, True

    def _de_cache(self, clave: str) -> dict[str, str | None] | None:
        if self._ttl <= 0:
            return None
        with self._lock:
            entrada = self._cache.get(clave)
        if entrada is None or (self._reloj() - entrada[0]) >= self._ttl:
            return None
        return entrada[1]

    def _a_cache(self, clave: str, mapa: dict[str, str | None]) -> None:
        with self._lock:
            self._cache[clave] = (self._reloj(), mapa)
