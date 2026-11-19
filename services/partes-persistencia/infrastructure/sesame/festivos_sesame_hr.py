# infrastructure/sesame/festivos_sesame_hr.py
"""Festivos de Sesame HR por DNI, para el refresco de la ingesta (F-077).

Sesame identifica por id de empleado y los partes por DNI. Este adaptador
da a `RefrescoFestivos` el contrato de F-032, que NO cambia (R10):

    festivos(dni, ano) -> list[FestivoDia] | None

  - DNI vacio o ausente de un indice bien cargado ⇒ ``None`` («no
    encontrado»: sin fila y sin revision, DA6).
  - DNI presente ⇒ los festivos de su empleado (`SesameHrClient`).
  - Cualquier fallo ⇒ excepcion (el refresco lo trata como fallo).

El INDICE (DNI normalizado -> id y si esta activo) vive solo en memoria
(DA3, R19) y se reconstruye cada `ttl_indice_s` (R11). Con DNIs repetidos
gana el activo y, a igualdad, el primero; las filas sin DNI se omiten
(R12). Es TODO O NADA (DA8, R13): si falla cualquier pagina, salen cero
empleados o ninguno trae DNI, no se guarda nada y la llamada falla. Tras un fallo de
disponibilidad (el del indice o un `SesameNoDisponible` de festivos) se
abre un CORTE de `corte_s`: durante el, cada llamada falla al instante sin
tocar la red (R14), para que un parte de veinte trabajadores no espere
veinte veces a un Sesame caido. Un 404 o un cuerpo ilegible de los
festivos de UN empleado no abren el corte.

Los logs dan solo recuentos; nunca DNIs ni ids (R18).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from application.services.text_match import normalize_dni
from infrastructure.sesame.sesame_hr_client import (
    EmpleadoSesame,
    FestivoDia,
    SesameHrClient,
    SesameNoDisponible,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-hr]"


class FestivosSesameHr:
    def __init__(
        self,
        *,
        cliente: SesameHrClient,
        ttl_indice_s: float = 600,
        corte_s: float = 60,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._cliente = cliente
        self._ttl_s = ttl_indice_s
        self._corte_s = corte_s
        self._reloj = reloj
        self._lock = threading.Lock()
        #: (momento de la construccion, DNI normalizado -> empleado) o None.
        self._indice: tuple[float, dict[str, EmpleadoSesame]] | None = None
        #: Instante hasta el que no se llama a Sesame (o None).
        self._corte_hasta: float | None = None

    def festivos(self, dni: str | None, ano: int) -> list[FestivoDia] | None:
        """Festivos de ese DNI en ese ano; ``None`` si no se le conoce."""
        dni_norm = normalize_dni(dni)
        if not dni_norm:
            return None
        with self._lock:
            self._comprobar_corte()
            indice = self._indice_vigente()
        empleado = indice.get(dni_norm)
        if empleado is None:
            return None
        try:
            return self._cliente.festivos_de_empleado(empleado.id, ano)
        except SesameNoDisponible:
            with self._lock:
                self._abrir_corte()
            raise

    # ------------------------------------------------------------- #
    def _comprobar_corte(self) -> None:
        if (self._corte_hasta is not None
                and self._reloj() < self._corte_hasta):
            raise SesameNoDisponible("corte")

    def _abrir_corte(self) -> None:
        self._corte_hasta = self._reloj() + self._corte_s

    def _indice_vigente(self) -> dict[str, EmpleadoSesame]:
        ahora = self._reloj()
        if self._indice is not None and ahora - self._indice[0] < self._ttl_s:
            return self._indice[1]
        self._indice = None
        try:
            empleados = self._cliente.empleados()
        except Exception as exc:  # noqa: BLE001 - todo o nada (R13)
            self._abrir_corte()
            raise SesameNoDisponible(
                f"sesame indice no disponible: {type(exc).__name__}"
            ) from None
        if not empleados:
            self._abrir_corte()
            raise SesameNoDisponible("sesame indice sin empleados")
        indice: dict[str, EmpleadoSesame] = {}
        duplicados = sin_dni = 0
        for empleado in empleados:
            if not empleado.dni_norm:
                sin_dni += 1
                continue
            previo = indice.get(empleado.dni_norm)
            if previo is None:
                indice[empleado.dni_norm] = empleado
                continue
            duplicados += 1
            if empleado.activo and not previo.activo:
                indice[empleado.dni_norm] = empleado
        logger.info(
            "%s indice empleados=%s duplicados=%s sin_dni=%s paginas=%s",
            _LOG_PREFIX, len(empleados), duplicados, sin_dni,
            self._cliente.ultimas_paginas,
        )
        if not indice:
            # Empleados, pero ninguno con DNI: tan inservible como 0 (R13).
            self._abrir_corte()
            raise SesameNoDisponible("sesame indice sin DNIs")
        self._indice = (ahora, indice)
        return indice
