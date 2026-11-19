# application/services/calendario_provider.py
"""Calendario laboral del portal: festivos de cada trabajador (F-003, F-032).

Quien DECIDE. Desde F-032 los festivos NO se piden a Sesame: los lee de
la tabla `festivos_trabajador`, que escribe sv3 al ingerir cada parte
(DA16). Desde F-077 sv4 no llama a Sesame para nada (DA1): sin cliente y
sin la jornada del contrato. Cascada de lectura (DA19 = B,
`festivos_guardados.elegir`) y FUENTE de cada resolucion:

    sesame      fila del trabajador en la tabla                  fiable
    sin_fila    sin fila o sin DNI: libreria `holidays`          aviso
    respaldo    la tabla no se pudo leer: `holidays`             aviso
    sin_sesame  Sesame sin configurar: `holidays`, como siempre  fiable

Las vistas se sirven igual con cualquiera de ellas (nunca se cae el portal
por RRHH). `sin_fila` y `respaldo` solo encienden el aviso de la UI: desde
DA17 = B ningun calendario bloquea el registro en Sigrid.

Apagado (`activo=False`, `FESTIVOS_SESAME_ENABLED=false`) ni se lee la
tabla: el portal se comporta exactamente como antes de F-003 (R7/R27). La
tabla entera se lee de una vez y se cachea `ttl_tabla_s` segundos (<= 60).
"""
from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from application.services.festivos_guardados import (
    FUENTE_SIN_FILA,
    FilaFestivos,
    elegir,
    fila_de,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-calendario]"

#: Fuentes fiables: la fila del trabajador o Sesame apagado (F-032). Las
#: demas (`sin_fila`, `respaldo`) solo encienden el aviso.
FUENTES_FIABLES = frozenset({"sesame", "sin_sesame"})

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
    #: False si el trabajador no tiene fila o la tabla no se pudo leer.
    fiable: bool = True


def normalizar_dni(dni: str | None) -> str:
    """Sin separadores y en mayusculas: la clave de identidad de la casa."""
    return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()


class CalendarioProvider:
    def __init__(
        self,
        *,
        activo: bool = False,
        respaldo_holiday_name: Callable[[date], str | None],
        reloj: Callable[[], float] = time.time,
        leer_festivos: Callable[[], Iterable[dict]] | None = None,
        ttl_tabla_s: float = 60,
    ) -> None:
        self._activo = bool(activo)
        self._respaldo = respaldo_holiday_name
        self._reloj = reloj
        self._leer_festivos = leer_festivos
        self._ttl_tabla_s = ttl_tabla_s
        self._lock = threading.RLock()
        #: (momento de la lectura, filas por (DNI, ano)) o None.
        self._tabla: tuple[float, dict] | None = None

    @property
    def activo(self) -> bool:
        """True si la tabla de Sesame esta encendida (F-077, R21)."""
        return self._activo

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

    def fuente_para(self, dni: str | None, ano: int) -> str:
        """De donde salen los festivos de ese (DNI, ano): ver el modulo."""
        return self._resolver(normalizar_dni(dni), int(ano))[1]

    def fiable_para(
        self, consultas: Iterable[tuple[str | None, int]]
    ) -> bool:
        """True si TODAS esas resoluciones (DNI x ano) tienen fila.

        Gobierna el aviso de las vistas y el `aviso_sesame` del preflight
        (F-032, R22, R25); ya no bloquea nada (DA17 = B). Sin Sesame
        configurado siempre es True (R27).
        """
        if not self._activo:
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

        `None` como mapa significa "usa el respaldo": o no hay Sesame, o el
        trabajador no tiene fila, o la tabla no se pudo leer.
        """
        if not self._activo:
            return None, "sin_sesame"
        try:
            fila, fuente = elegir(dni_norm, ano, self._fila)
        except Exception as exc:  # noqa: BLE001 - R20
            logger.warning(
                "%s no se pudo leer festivos_trabajador (%s): se usa el "
                "respaldo local de festivos.", _LOG_PREFIX,
                type(exc).__name__,
            )
            return None, "respaldo"
        if fila is None:
            return None, FUENTE_SIN_FILA
        return dict(fila.festivos), fuente

    def _fila(self, dni_norm: str, ano: int) -> FilaFestivos | None:
        return self._filas().get((dni_norm, ano))

    def _filas(self) -> dict[tuple[str, int], FilaFestivos]:
        """La tabla entera, cacheada `ttl_tabla_s` segundos."""
        with self._lock:
            ahora = self._reloj()
            if (self._tabla is not None
                    and ahora - self._tabla[0] < self._ttl_tabla_s):
                return self._tabla[1]
            filas: dict[tuple[str, int], FilaFestivos] = {}
            crudas = self._leer_festivos() if self._leer_festivos else ()
            for cruda in crudas:
                try:
                    fila = fila_de(cruda.get("dni_norm"), cruda.get("ano"),
                                   cruda.get("festivos_json"),
                                   cruda.get("leido_en_utc"))
                except ValueError as exc:
                    logger.warning(
                        "%s fila id=%s de festivos_trabajador mal formada, "
                        "se omite: %s", _LOG_PREFIX, cruda.get("id"), exc,
                    )
                    continue
                filas[(fila.dni_norm, fila.ano)] = fila
            self._tabla = (ahora, filas)
            return filas
