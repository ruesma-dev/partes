# infrastructure/sesame/sesame_hr_client.py
"""Cliente HTTP de SOLO LECTURA contra la API oficial de Sesame HR (F-077).

sv3 es el unico servicio que habla con Sesame (DA1) y solo por aqui: sin la
pasarela `sesame-api` (DA2). Tres rutas, todas `GET` (R9):

  ``/core/v3/employees``            empleados, para el indice por DNI (R6)
  ``/schedule/v1/holidays``         festivos de un empleado en un ano (R7)
  ``/schedule/v1/holiday-calendar`` calendarios, para la herramienta (R8)

Autenticacion ``Authorization: Bearer <token>`` (R1). Los listados se
paginan con ``limit``/``page`` hasta ``meta.lastPage`` (R2) y un listado a
medias es FALLO, nunca un listado recortado: un indice parcial convertiria
DNIs conocidos en «no encontrados» sin que nadie se entere.

Reintentos ante 429/5xx y errores de red con espera inyectable (R3);
401/403/4xx sin reintento (R4). Todo lo que no es «hay datos» sube como
``RuntimeError``; lo que dice «Sesame no esta disponible» (red, 429/5xx
agotados, 4xx) es ``SesameNoDisponible`` y abre el corte del adaptador
(``festivos_sesame_hr.py``). Los textos de excepcion llevan solo el estado
o el tipo del error y la ruta sin query (R5): ni cuerpo, ni parametros, ni
URL, ni token.

El token probablemente permite escribir en Sesame: este modulo no tiene ni
una llamada que no sea ``get`` (lo vigila un guardian por AST).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from application.services.text_match import normalize_dni

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-hr]"

RUTA_EMPLEADOS = "/core/v3/employees"
RUTA_FESTIVOS = "/schedule/v1/holidays"
RUTA_CALENDARIOS = "/schedule/v1/holiday-calendar"

#: Estados que se reintentan (R3).
_REINTENTABLES = frozenset({429, 500, 502, 503, 504})

#: Tope de la espera de un ``Retry-After`` (R3).
_ESPERA_MAXIMA_S = 30.0


class SesameNoDisponible(RuntimeError):
    """Red, 429/5xx agotados o 401/403/4xx: Sesame no esta disponible."""


@dataclass(frozen=True)
class FestivoDia:
    """Un dia festivo de Sesame (el mismo contrato que en F-032)."""
    fecha: str              # ISO 'YYYY-MM-DD'
    nombre: str | None


@dataclass(frozen=True)
class EmpleadoSesame:
    """Lo unico que se guarda de un empleado de Sesame (R6, R11)."""
    id: str
    dni_norm: str
    activo: bool


@dataclass(frozen=True)
class CalendarioSesame:
    """Un calendario de festivos de Sesame (R8)."""
    id: str
    nombre: str | None
    por_defecto: bool
    festivos: tuple[FestivoDia, ...]


class SesameHrClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout_s: float = 10.0,
        page_size: int = 100,
        max_reintentos: int = 2,
        tope_filas: int = 20_000,
        transport: httpx.BaseTransport | None = None,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        if not (base_url or "").startswith("https://"):
            raise ValueError("SesameHrClient requiere una base_url https://")
        if not (token or "").strip():
            raise ValueError("SesameHrClient requiere un token no vacio")
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout_s = float(timeout_s)
        self._page_size = int(page_size)
        self._max_reintentos = int(max_reintentos)
        self._tope_filas = int(tope_filas)
        self._transport = transport
        self._dormir = dormir
        #: Paginas que trajo el ultimo listado (para el log del indice).
        self.ultimas_paginas = 0
        logger.info(
            "%s Instanciado base_url=%s token_len=%s timeout_s=%s",
            _LOG_PREFIX, self._base_url, len(token), self._timeout_s,
        )

    # ------------------------------------------------------------- #
    # Consultas.
    # ------------------------------------------------------------- #
    def empleados(self) -> list[EmpleadoSesame]:
        """Activos e inactivos (DA7), con solo id, DNI normalizado y estado.

        Nombre, apellidos, email, codigo y tipo de documento se descartan
        al leer la fila: no salen de esta funcion (R6).
        """
        filas = self._paginado(RUTA_EMPLEADOS,
                               {"status[in]": "active,inactive"})
        out: list[EmpleadoSesame] = []
        for fila in filas:
            if not isinstance(fila, dict) or fila.get("id") is None:
                continue
            out.append(EmpleadoSesame(
                id=str(fila["id"]),
                dni_norm=normalize_dni(fila.get("nid")),
                activo=fila.get("status") == "active",
            ))
        return out

    def festivos_de_empleado(self, employee_id: str,
                             ano: int) -> list[FestivoDia]:
        """Festivos de ese empleado en ese ano, ordenados por fecha (R7).

        Un 404 es FALLO (``RuntimeError``), no «no encontrado» (DA6): el
        empleado esta en el indice.
        """
        filas = self._paginado(RUTA_FESTIVOS,
                               {"employeeId": employee_id, "year": int(ano)})
        dias: list[Any] = []
        for fila in filas:
            if not isinstance(fila, dict):
                continue
            dias.append(fila.get("dayOff"))
            if isinstance(fila.get("daysOff"), list):
                dias.extend(fila["daysOff"])
        return _festivos(dias, f"{int(ano):04d}-")

    def calendarios_festivos(self) -> list[CalendarioSesame]:
        """Todos los calendarios de festivos de Sesame (R8)."""
        out: list[CalendarioSesame] = []
        for cal in self._paginado(RUTA_CALENDARIOS, {}):
            if not isinstance(cal, dict):
                continue
            dias = cal.get("daysOff")
            if dias is None:
                dias = cal.get("dayOff")
            if isinstance(dias, dict):
                dias = [dias]
            out.append(CalendarioSesame(
                id=str(cal.get("id")),
                nombre=_opt_str(cal.get("name")),
                por_defecto=bool(cal.get("default")),
                festivos=tuple(_festivos(dias or [], "")),
            ))
        return out

    # ------------------------------------------------------------- #
    # HTTP.
    # ------------------------------------------------------------- #
    def _paginado(self, ruta: str, params: dict[str, Any]) -> list[Any]:
        """Todas las paginas de un listado; a medias es FALLO (R2)."""
        out: list[Any] = []
        pagina = 1
        while True:
            cuerpo = self._get(ruta, {**params, "limit": self._page_size,
                                      "page": pagina})
            if cuerpo is None:
                raise RuntimeError(f"sesame HTTP 404 en {ruta}")
            if not isinstance(cuerpo, dict):
                raise RuntimeError(f"sesame cuerpo sin listado en {ruta}")
            datos = cuerpo.get("data") or []
            if isinstance(datos, dict):
                datos = [datos]
            if not isinstance(datos, list):
                raise RuntimeError(f"sesame cuerpo sin listado en {ruta}")
            try:
                ultima = int((cuerpo.get("meta") or {}).get("lastPage") or 1)
            except (TypeError, ValueError):
                raise RuntimeError(
                    f"sesame cuerpo sin listado en {ruta}") from None
            if not datos and pagina < ultima:
                raise RuntimeError(
                    f"sesame pagina {pagina} vacia antes de la ultima "
                    f"en {ruta}")
            out.extend(datos)
            if len(out) > self._tope_filas:
                raise RuntimeError(f"sesame listado supera el tope en {ruta}")
            if pagina >= ultima:
                self.ultimas_paginas = pagina
                return out
            pagina += 1

    def _get(self, ruta: str, params: dict[str, Any]) -> Any:
        """Un GET con reintentos; ``None`` si 404 (R3, R4, R5)."""
        cabeceras = {"Authorization": f"Bearer {self._token}",
                     "Accept": "application/json"}
        url = f"{self._base_url}{ruta}"
        with httpx.Client(timeout=self._timeout_s, transport=self._transport,
                          headers=cabeceras) as client:
            intento = 0
            while True:
                try:
                    respuesta = client.get(url, params=params)
                except httpx.HTTPError as exc:
                    if intento >= self._max_reintentos:
                        raise SesameNoDisponible(
                            f"sesame red en {ruta}: {type(exc).__name__}"
                        ) from None
                    espera = 1.0 * (intento + 1)
                    logger.warning("%s %s -> %s; reintento en %.1f s",
                                   _LOG_PREFIX, ruta, type(exc).__name__,
                                   espera)
                    self._dormir(espera)
                    intento += 1
                    continue
                estado = respuesta.status_code
                if estado == 404:
                    return None
                if estado in _REINTENTABLES:
                    if intento >= self._max_reintentos:
                        raise SesameNoDisponible(
                            f"sesame HTTP {estado} en {ruta}") from None
                    espera = _espera(respuesta.headers.get("Retry-After"),
                                     intento)
                    logger.warning("%s %s -> %s; reintento en %.1f s",
                                   _LOG_PREFIX, ruta, estado, espera)
                    self._dormir(espera)
                    intento += 1
                    continue
                if estado >= 400:
                    raise SesameNoDisponible(
                        f"sesame HTTP {estado} en {ruta}") from None
                try:
                    return respuesta.json()
                except ValueError:
                    raise RuntimeError(
                        f"sesame cuerpo no JSON en {ruta}") from None


def _espera(retry_after: str | None, intento: int) -> float:
    """``Retry-After`` en segundos con tope; si no es numero, 1 + intento."""
    try:
        segundos = float(retry_after)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return float(1 + intento)
    if not segundos >= 0:          # negativo o NaN: tampoco es una espera
        return float(1 + intento)
    return min(segundos, _ESPERA_MAXIMA_S)


def _festivos(dias: Any, prefijo: str) -> list[FestivoDia]:
    """Los dias con fecha que empiezan por ``prefijo``, ordenados."""
    out = []
    for dia in dias:
        if not isinstance(dia, dict):
            continue
        fecha = _opt_str(dia.get("date"))
        if not fecha or not fecha.startswith(prefijo):
            continue
        out.append(FestivoDia(fecha=fecha, nombre=_opt_str(dia.get("name"))))
    out.sort(key=lambda f: f.fecha)
    return out


def _opt_str(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
