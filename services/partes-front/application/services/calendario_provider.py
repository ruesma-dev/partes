# application/services/calendario_provider.py
"""Calendario laboral del portal: festivos de Sesame con respaldo (F-003).

Quien DECIDE. El cliente (`infrastructure/sesame/`) solo traduce HTTP;
aqui vive la cascada de degradacion, la cache y —lo importante para la
resiliencia en dos niveles (D2)— la FUENTE de cada resolucion:

    sesame    festivos del calendario del propio trabajador      fiable
    default   404 de su DNI -> calendario por defecto de Sesame  fiable
    stale     Sesame fallo y se reutiliza la cache caducada      degradada
    respaldo  Sesame fallo y no habia cache: libreria `holidays` degradada

Las dos primeras son datos que Sesame ha dado; las dos ultimas son lo
mejor que se ha podido apanar. Las vistas informativas se sirven
igualmente con cualquiera de las cuatro (nunca se cae un portal por
RRHH), pero una resolucion degradada enciende el aviso de la UI (R22) y
bloquea el REGISTRO en Sigrid (R23/R24): sin los festivos reales el
computo de horas no es de fiar, y calcular mal en silencio es peor que
parar.

Con Sesame sin configurar (`cliente is None`) no hay ni llamadas ni
degradacion: el portal se comporta exactamente como antes de F-003
(R7/R27).

Unidad de cache: festivos por (DNI x ano), no por rango (D5). Son pocas
claves y estables —una por trabajador activo y ano— y espejan la cache
del propio sesame-api. El fin de semana no se pregunta: sale de la fecha.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from infrastructure.sesame.sesame_api_client import (
    JornadaContrato,
    SesameApiClient,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-calendario]"

#: Fuentes cuyo dato viene de una respuesta VIGENTE de Sesame.
FUENTES_FIABLES = frozenset({"sesame", "default", "sin_sesame"})

#: Nombre con el que se pinta un festivo que Sesame no nombra. Tiene que
#: ser truthy: las vistas deciden `is_holiday` por el nombre, y un
#: festivo sin nombre no puede desaparecer del calendario.
FESTIVO_SIN_NOMBRE = "Festivo"

#: Centinela para distinguir "ese dia no es festivo" de "es festivo y no
#: tiene nombre" al mirar el mapa de festivos.
_NO_FESTIVO = object()


@dataclass(frozen=True)
class DiaCalendario:
    """Un dia resuelto, en el formato que consume `GET /api/calendario`."""
    fecha: str
    laborable: bool
    fin_de_semana: bool
    festivo: bool
    festivo_nombre: str | None
    #: False si la resolucion salio de la cache caducada o del respaldo.
    fiable: bool = True


def normalizar_dni(dni: str | None) -> str:
    """Sin separadores y en mayusculas: la clave de identidad de la casa."""
    return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()


class CalendarioProvider:
    def __init__(
        self,
        *,
        cliente: SesameApiClient | None,
        respaldo_holiday_name: Callable[[date], str | None],
        ttl_seconds: int = 21600,
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self._cliente = cliente
        self._respaldo = respaldo_holiday_name
        self._ttl = int(ttl_seconds)
        self._reloj = reloj
        self._lock = threading.RLock()
        #: clave -> (timestamp, valor, fuente)
        self._cache: dict[str, tuple[float, object, str]] = {}

    @property
    def activo(self) -> bool:
        """True si hay Sesame cableado (el nivel 2 de D2 solo aplica si si)."""
        return self._cliente is not None

    # ------------------------------------------------------------- #
    # Lo que consumen las vistas.
    # ------------------------------------------------------------- #
    def holiday_name_para(
        self, dni: str | None
    ) -> Callable[[date], str | None]:
        """`holiday_name` del trabajador, con el contrato de `HolidayProvider`.

        Devolver un callable permite que `build_calendar` y `get_obra`
        sigan igual: no se enteran de que la fuente ha cambiado.
        """
        def _nombre(d: date) -> str | None:
            return self._nombre_festivo(d, dni)[0]
        return _nombre

    def dia(self, d: date, dni: str | None) -> DiaCalendario:
        nombre, fuente = self._nombre_festivo(d, dni)
        fin_de_semana = d.weekday() >= 5
        festivo = nombre is not None
        return DiaCalendario(
            fecha=d.isoformat(),
            laborable=not (fin_de_semana or festivo),
            fin_de_semana=fin_de_semana,
            festivo=festivo,
            festivo_nombre=nombre,
            fiable=fuente in FUENTES_FIABLES,
        )

    def jornada_contrato(self, dni: str | None) -> JornadaContrato | None:
        """Tipo de jornada del contrato; `None` si no se puede saber.

        OJO: sesame-api NO da hoy las horas del contrato (peticion P1),
        asi que esto NO sustituye al CanDefecto: alimenta el badge del
        KPI y el aviso de divergencia (R13/R14).
        """
        dni_norm = normalizar_dni(dni)
        if self._cliente is None or not dni_norm:
            return None
        clave = f"jornada:{dni_norm}"
        vigente = self._de_cache(clave)
        if vigente is not None:
            return vigente[0]  # type: ignore[return-value]
        try:
            jornada = self._cliente.jornada(dni_norm)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s jornada de %s no disponible (%r); el KPI se muestra sin "
                "el dato del contrato.", _LOG_PREFIX, dni_norm, exc,
            )
            return None
        self._a_cache(clave, jornada, "sesame")
        return jornada

    def fiable_para(
        self, consultas: Iterable[tuple[str | None, int]]
    ) -> bool:
        """True si TODAS esas resoluciones (DNI x ano) salen de Sesame.

        Es la comprobacion del bloqueo de registro (R23/R24) y del aviso
        de las vistas (R22). Sin Sesame configurado siempre es True: la
        feature apagada no bloquea nada (R27).
        """
        if self._cliente is None:
            return True
        vistos: set[tuple[str, int]] = set()
        for dni, ano in consultas:
            clave = (normalizar_dni(dni), int(ano))
            if clave in vistos:
                continue
            vistos.add(clave)
            if self._resolver(clave[0], clave[1])[1] not in FUENTES_FIABLES:
                return False
        return True

    # ------------------------------------------------------------- #
    # Resolucion y cascada.
    # ------------------------------------------------------------- #
    def _nombre_festivo(
        self, d: date, dni: str | None
    ) -> tuple[str | None, str]:
        mapa, fuente = self._resolver(normalizar_dni(dni), d.year)
        if mapa is None:
            return self._respaldo(d), fuente
        valor = mapa.get(d.isoformat(), _NO_FESTIVO)
        if valor is _NO_FESTIVO:
            return None, fuente
        return (valor or FESTIVO_SIN_NOMBRE), fuente   # type: ignore[return-value]

    def _resolver(
        self, dni_norm: str, ano: int
    ) -> tuple[dict[str, str | None] | None, str]:
        """Festivos de ese (DNI, ano) y de donde han salido.

        `None` como mapa significa "usa el respaldo": o no hay Sesame, o
        no se ha podido sacar nada de el.
        """
        if self._cliente is None:
            return None, "sin_sesame"

        clave = f"fest:{dni_norm or '_default'}:{ano}"
        vigente = self._de_cache(clave)
        if vigente is not None:
            return vigente  # type: ignore[return-value]

        try:
            fuente = "default"
            festivos = None
            if dni_norm:
                festivos = self._cliente.festivos(dni_norm, ano)
                fuente = "sesame"
            if festivos is None:
                # Sin DNI, o Sesame no conoce ese DNI (404). Responde: el
                # calendario por defecto es un dato fiable, no un apano.
                festivos = self._cliente.calendario_por_defecto(ano)
                fuente = "default"
        except Exception as exc:  # noqa: BLE001
            return self._degradar(clave, dni_norm, ano, exc)

        if festivos is None:
            logger.warning(
                "%s sin festivos utilizables para dni=%s ano=%s (Sesame no "
                "tiene calendario por defecto): se usa el respaldo.",
                _LOG_PREFIX, dni_norm or "(sin dni)", ano,
            )
            return None, "respaldo"

        mapa = {f.fecha: f.nombre for f in festivos}
        self._a_cache(clave, mapa, fuente)
        logger.info(
            "%s dni=%s ano=%s -> %s festivos (fuente=%s)",
            _LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa), fuente,
        )
        return mapa, fuente

    def _degradar(
        self, clave: str, dni_norm: str, ano: int, exc: Exception
    ) -> tuple[dict[str, str | None] | None, str]:
        """Sesame ha fallado: cache caducada si la hay, si no el respaldo.

        La entrada caducada NO se refresca a proposito: asi el siguiente
        intento vuelve a preguntar a Sesame en cuanto se recupere, en vez
        de quedarse seis horas sirviendo un dato viejo en silencio.
        """
        with self._lock:
            entrada = self._cache.get(clave)
        if entrada is not None:
            logger.warning(
                "%s Sesame no responde (%r) para dni=%s ano=%s: se reutiliza "
                "la respuesta caducada. El calendario puede no estar al dia.",
                _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,
            )
            return entrada[1], "stale"      # type: ignore[return-value]
        logger.warning(
            "%s Sesame no responde (%r) para dni=%s ano=%s y no hay cache "
            "previa: se usa el respaldo local de festivos.",
            _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,
        )
        return None, "respaldo"

    # ------------------------------------------------------------- #
    # Cache.
    # ------------------------------------------------------------- #
    def _de_cache(self, clave: str) -> tuple[object, str] | None:
        if self._ttl <= 0:
            return None
        with self._lock:
            entrada = self._cache.get(clave)
        if entrada is None:
            return None
        if (self._reloj() - entrada[0]) >= self._ttl:
            return None
        return entrada[1], entrada[2]

    def _a_cache(self, clave: str, valor: object, fuente: str) -> None:
        with self._lock:
            self._cache[clave] = (self._reloj(), valor, fuente)
