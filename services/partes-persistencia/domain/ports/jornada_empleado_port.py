# domain/ports/jornada_empleado_port.py
"""Puerto de las EXCEPCIONES de jornada por trabajador (F-015).

La jornada de un dia se deriva del ``candef`` de Sigrid por el mapa
``JORNADA_SEMANAL_POR_CANDEF``. Este puerto es para lo que ese mapa no
puede expresar: un trabajador con otra jornada semanal, o con un patron
explicito de horas por dia (la intensiva). Vive en la tabla
``empleado_jornada`` de la base ``partes``, que nace VACIA.

Se lee la tabla ENTERA de una vez (``fetch_jornadas``) y se indexa por DNI
en memoria: se esperan unidades de filas, y un ``SELECT`` por trabajador y
dia seria una consulta por cada dia de cada parte. El puerto es opcional
(``RecursoConciliador`` funciona con ``jornadas=None``), porque una
excepcion de jornada no puede ser condicion para conciliar un parte.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class JornadaEmpleadoRow:
    """Una fila vigente de ``empleado_jornada``, ya normalizada.

    ``patron`` son 7 horas L..D, o ``None`` si la fila solo trae
    ``jornada_semanal``. ``desde`` es inclusivo y ``hasta`` EXCLUSIVO
    (``desde <= fecha < hasta``); ``hasta`` nulo es vigencia abierta.
    """
    dni_norm: str
    jornada_semanal: float | None = None
    patron: tuple[float, ...] | None = None
    desde: str | None = None
    hasta: str | None = None
    origen: str = "manual"


class JornadaEmpleadoPort(ABC):
    @abstractmethod
    def fetch_jornadas(self) -> list[JornadaEmpleadoRow]:
        """Todas las excepciones ACTIVAS, sin filtrar por fecha ni por DNI."""
        raise NotImplementedError
