# application/services/recurso_catalog.py
"""Cachea los RECURSOS ACTIVOS de Sigrid (F-035) con TTL.

Alimenta los selectores de trabajador del portal (Conciliar, Nuevo parte,
modal «+ Añadir linea», combo del detalle de obra): recursos de clase
persona de alta hoy, con o sin DNI (F-040: el sin DNI llega con `dni`
None y el portal lo marca), filtrables por empresa. Un trabajador con
recurso y sin ficha de empleado (caso F-030) tambien sale.

`asignacion_de` es el UNICO sitio con la regla de que se escribe en la
linea al elegir un recurso (R12/R13); el endpoint la serializa para el JS.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from infrastructure.sigrid.sigrid_lookup_client import (
    RecursoOption,
    SigridLookupClient,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Asignacion:
    """Lo que se escribe en la linea al elegir un recurso."""
    empleado_ide: int | None
    codigo: str | None
    nombre: str | None
    dni: str | None
    reside: int

    def como_guardar(self) -> dict[str, Any]:
        """Los `empleado_*` con los nombres de columna (payload del JS)."""
        return {
            "empleado_ide": self.empleado_ide,
            "empleado_codigo": self.codigo,
            "empleado_nombre": self.nombre,
            "empleado_dni": self.dni,
            "empleado_reside": self.reside,
        }


def asignacion_de(r: RecursoOption) -> Asignacion:
    """Con ficha enlazada: la ficha (DNI de la ficha y, si vacio, el del
    recurso: el orden con que sv5 verifica). Sin ficha: el recurso.
    F-040 (R16): un recurso sin DNI deja `dni` None en los dos casos."""
    if r.empleado_ide is not None:
        return Asignacion(
            empleado_ide=r.empleado_ide, codigo=r.empleado_codigo,
            nombre=r.empleado_nombre, dni=r.empleado_dni or r.dni,
            reside=r.ide)
    return Asignacion(empleado_ide=None, codigo=r.codigo, nombre=r.nombre,
                      dni=r.dni, reside=r.ide)


class RecursoCatalog:
    def __init__(
        self,
        *,
        client: SigridLookupClient | None,
        ttl_seconds: int = 600,
    ) -> None:
        self._client = client
        self._ttl = int(ttl_seconds)
        self._lock = threading.RLock()
        self._items: list[RecursoOption] = []
        self._by_ide: dict[int, RecursoOption] = {}
        self._loaded_at: float = 0.0
        self._ever_loaded = False

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @property
    def cargado(self) -> bool:
        """¿Hubo alguna carga buena? Distingue «Sigrid no respondio nunca»
        (False) de «lista vacia de verdad» o «ultima lista buena» (R6)."""
        return self._ever_loaded

    def list(self, empresa: int | None = None) -> list[RecursoOption]:
        """Recursos activos; con `empresa`, solo los de esa empresa (R5)."""
        self._ensure_fresh()
        if empresa is None:
            return list(self._items)
        return [r for r in self._items if r.empresa == int(empresa)]

    def get_by_ide(self, ide: int | None) -> RecursoOption | None:
        if ide is None:
            return None
        self._ensure_fresh()
        return self._by_ide.get(int(ide))

    def _ensure_fresh(self) -> None:
        if self._client is None:
            return
        with self._lock:
            now = time.time()
            if self._ever_loaded and (now - self._loaded_at) < self._ttl:
                return
            try:
                items = self._client.fetch_recursos_activos()
                self._items = items
                self._by_ide = {r.ide: r for r in items}
                self._loaded_at = now
                self._ever_loaded = True
            except Exception as exc:  # noqa: BLE001
                # R6: se sirve la ultima lista buena (vacia si nunca cargo).
                logger.warning("[recurso-catalog] refresco fallo: %r", exc)
