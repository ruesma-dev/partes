# application/services/jornada_provider.py
"""Excepciones de jornada por trabajador para el portal (F-015).

La jornada de cada dia se deriva del `candef` de Sigrid por el mapa
`JORNADA_SEMANAL_POR_CANDEF`. Este proveedor es para lo que ese mapa no
puede expresar: un trabajador con otra jornada semanal, o con un patron
explicito de horas por dia. Vive en la tabla `empleado_jornada` de la
base `partes`, que nace VACIA.

Mismo patron que `CalendarioProvider`: la clase DECIDE (cache, vigencia,
degradacion) y recibe la lectura como *callable*, para que las vistas se
prueben sin BBDD. Y la misma regla de resiliencia que el resto del
portal: si la lectura falla, la vista se sirve igual con la jornada
derivada y queda un WARNING. Un portal caido porque una tabla accesoria
no responde seria peor que un KPI sin excepcion.

Se lee la tabla ENTERA y se indexa por DNI en memoria (DA8): son unidades
de filas, y un `SELECT` por trabajador y dia seria una consulta por celda
de la matriz de obra.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from application.services.jornada_resolver import Excepcion
from application.services.text_match import normalize_dni

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[jornada-excepciones]"


@dataclass(frozen=True)
class JornadaEmpleadoRow:
    """Una fila activa de `empleado_jornada`, ya normalizada.

    `desde` es inclusivo y `hasta` EXCLUSIVO (`desde <= fecha < hasta`);
    `hasta` nulo es vigencia abierta.
    """
    dni_norm: str
    jornada_semanal: float | None = None
    patron: tuple[float, ...] | None = None
    desde: str | None = None
    hasta: str | None = None
    origen: str = "manual"


#: Columnas del patron en orden lunes..domingo, como las declara el ORM.
_DIAS = ("h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom")


def fila_desde_dict(fila: dict) -> JornadaEmpleadoRow:
    """Traduce lo que devuelve el repositorio a la fila del proveedor.

    Una fila con alguna hora del patron a NULL se entiende como "solo
    jornada semanal": un patron a medias no se puede aplicar.
    """
    horas = [fila.get(dia) for dia in _DIAS]
    patron = (
        tuple(float(h) for h in horas)
        if all(h is not None for h in horas) else None
    )
    semanal = fila.get("jornada_semanal")
    return JornadaEmpleadoRow(
        dni_norm=normalize_dni(fila.get("dni_norm")),
        jornada_semanal=None if semanal is None else float(semanal),
        patron=patron,
        desde=fila.get("desde"),
        hasta=fila.get("hasta"),
        origen=fila.get("origen") or "manual",
    )


def _excepcion_de(fila: JornadaEmpleadoRow) -> Excepcion:
    return Excepcion(
        semanal=fila.jornada_semanal, patron=fila.patron, origen=fila.origen,
    )


class JornadaEmpleadoProvider:
    def __init__(
        self,
        cargar: Callable[[], Iterable[dict]],
        *,
        ttl_seconds: int = 600,
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self._cargar = cargar
        self._ttl = int(ttl_seconds)
        self._reloj = reloj
        self._lock = threading.RLock()
        #: (timestamp, {dni_norm: [filas, vigencia mas reciente primero]}).
        self._cache: tuple[float, dict[str, list[JornadaEmpleadoRow]]] | None = None
        #: Se avisa UNA vez por proceso mientras la lectura siga fallando.
        self._avisado = False

    def excepcion_para(self, dni: str | None, fecha: date) -> Excepcion | None:
        """Excepcion vigente de ese trabajador ese dia, o `None`.

        Sin DNI no se busca: un DNI vacio no casa con ninguna fila.
        """
        clave = normalize_dni(dni)
        if not clave:
            return None
        iso = fecha.isoformat()
        for fila in self._indice().get(clave, ()):
            if fila.desde and iso < fila.desde:
                continue
            if fila.hasta and iso >= fila.hasta:
                continue
            return _excepcion_de(fila)
        return None

    def invalidar(self) -> None:
        """Tira la cache: la proxima consulta relee la tabla (F-016).

        La llama la pantalla de administracion tras cada escritura con
        exito, para que el portal refleje el cambio sin esperar al TTL.
        Solo afecta a ESTE proceso: sv3 y otras replicas de sv4 siguen
        con su propio TTL, y la pantalla lo avisa.
        """
        with self._lock:
            self._cache = None

    def _indice(self) -> dict[str, list[JornadaEmpleadoRow]]:
        ahora = self._reloj()
        with self._lock:
            if self._cache is not None and (
                self._ttl > 0 and (ahora - self._cache[0]) < self._ttl
            ):
                return self._cache[1]
        try:
            filas = [fila_desde_dict(f) for f in self._cargar()]
        except Exception as exc:  # noqa: BLE001
            if not self._avisado:
                self._avisado = True
                logger.warning(
                    "%s no se pudo leer empleado_jornada (%r): las vistas "
                    "siguen con la jornada derivada del candef.",
                    _LOG_PREFIX, exc,
                )
            filas = []
        else:
            self._avisado = False
        indice: dict[str, list[JornadaEmpleadoRow]] = {}
        ignoradas = 0
        for fila in filas:
            if not fila.dni_norm or not _excepcion_de(fila).valida():
                # Hasta F-016 las filas las carga el humano por SQL: una
                # mal formada se IGNORA en vez de cambiar los avisos.
                ignoradas += 1
                continue
            indice.setdefault(fila.dni_norm, []).append(fila)
        if ignoradas:
            logger.warning(
                "%s %s fila(s) de empleado_jornada ignoradas por venir mal "
                "formadas (sin DNI, patron incompleto u horas fuera de "
                "rango).", _LOG_PREFIX, ignoradas,
            )
        for lista in indice.values():
            # Vigencia mas reciente primero: si dos filas solapan (F-016 lo
            # impedira; hasta entonces las carga el humano a mano), gana la
            # que alguien anadio despues.
            lista.sort(key=lambda f: (f.desde or ""), reverse=True)
        with self._lock:
            self._cache = (ahora, indice)
        return indice
