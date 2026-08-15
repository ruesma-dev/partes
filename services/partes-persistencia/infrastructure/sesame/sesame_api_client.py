# infrastructure/sesame/sesame_api_client.py
"""Cliente HTTP de SOLO LECTURA contra ``sesame-api`` (F-003).

``sesame-api`` es la pasarela general de la casa sobre Sesame HR: le
preguntamos los FESTIVOS del calendario asignado a cada trabajador (por
su DNI) y el tipo de JORNADA de su contrato. Identificacion por DNI
normalizado, clave propia en la cabecera ``x-api-key``.

En sv3 lo que importa son los festivos: el computo de extras manda TODAS
las horas ordinarias de un dia no laborable a horas extra, asi que un
festivo que falte se paga como jornada normal.

De sesame-api solo se usan tres rutas:

  ``GET /api/v1/festivos?dni=&ano=``   festivos del calendario del trabajador
  ``GET /api/v1/calendarios-festivos`` calendarios, para el "por defecto"
  ``GET /api/v1/jornada?dni=``         tipo de jornada del contrato

El dia y el fin de semana se calculan en local (D5): cachear rangos
multiplicaria las entradas sin aportar nada que no sepamos deducir de la
fecha. La cuarta ruta (``/api/v1/calendario``) queda sin usar por eso.

GEMELO del cliente de sv4 (``services/partes-front/infrastructure/
sesame/sesame_api_client.py``): adaptadores por servicio, sin libreria
compartida (docs/ARCHITECTURE.md). Quien toque uno cambia LOS DOS.

Diferencia deliberada con los clientes de Sigrid: el constructor acepta un
``transport`` de httpx, para poder ejercitarlo con ``httpx.MockTransport``
sin red (R19). Los de Sigrid construyen el ``httpx.Client`` por dentro y
por eso hoy estan sin cubrir; no se repite el defecto.

Este cliente NO decide nada: traduce HTTP a datos y sube ``RuntimeError``
ante cualquier fallo. La cascada de degradacion vive en el adaptador
(``infrastructure/calendario/sesame_calendario_laboral.py``).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sesame-client]"

#: Los cuerpos de error se recortan al loguearlos y al envolverlos: una
#: pagina de error de un proxy puede traer kilobytes de HTML.
_MAX_CUERPO = 300


@dataclass(frozen=True)
class FestivoDia:
    """Un dia festivo del calendario de Sesame."""
    fecha: str              # ISO 'YYYY-MM-DD'
    nombre: str | None


@dataclass(frozen=True)
class JornadaContrato:
    """Jornada del contrato ACTUAL segun Sesame.

    OJO: hoy sesame-api NO devuelve las horas (ni por dia ni por semana),
    solo el nombre del tipo y un booleano derivado. Por eso esta clase no
    puede sustituir al CanDefecto de Sigrid: es la peticion P1 del design.
    """
    tipo: str | None
    reducida: bool | None
    tipo_contrato: str | None


class SesameApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_s: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("SesameApiClient requiere base_url no vacio")
        if not api_key:
            raise ValueError("SesameApiClient requiere api_key no vacio")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = float(timeout_s)
        self._transport = transport
        logger.info(
            "%s Instanciado. base_url=%s key_len=%s timeout_s=%s",
            _LOG_PREFIX, self._base_url, len(api_key), self._timeout_s,
        )

    # ------------------------------------------------------------- #
    # Consultas.
    # ------------------------------------------------------------- #
    def festivos(self, dni: str, ano: int) -> list[FestivoDia] | None:
        """Festivos del calendario asignado a ese DNI, en ese ano.

        ``None`` si Sesame no conoce el DNI (404). Es distinto de la
        lista vacia: "no se quien es" manda al calendario por defecto
        (R4), "no tiene festivos" es un dato bueno.
        """
        cuerpo = self._get(
            "/api/v1/festivos", {"dni": dni, "ano": ano}, label="festivos"
        )
        if cuerpo is None:
            return None
        return self._festivos_del_ano(cuerpo.get("data"), ano)

    def calendario_por_defecto(self, ano: int) -> list[FestivoDia] | None:
        """Festivos del calendario marcado ``por_defecto`` en Sesame.

        ``None`` si ningun calendario lo esta: sin ese dato no hay nada
        fiable que ofrecer y el proveedor debe caer al respaldo, no dar
        el ano entero por laborable.
        """
        cuerpo = self._get(
            "/api/v1/calendarios-festivos", {}, label="calendarios"
        )
        if cuerpo is None:
            return None
        for cal in cuerpo.get("data") or []:
            if isinstance(cal, dict) and cal.get("por_defecto"):
                return self._festivos_del_ano(cal.get("festivos"), ano)
        logger.warning(
            "%s ningun calendario marcado por_defecto en Sesame",
            _LOG_PREFIX,
        )
        return None

    def jornada(self, dni: str) -> JornadaContrato | None:
        """Jornada del contrato de ese DNI; ``None`` si Sesame no lo tiene."""
        cuerpo = self._get("/api/v1/jornada", {"dni": dni}, label="jornada")
        if cuerpo is None:
            return None
        datos = cuerpo.get("data")
        if not isinstance(datos, dict):
            return None
        reducida = datos.get("reducida")
        return JornadaContrato(
            tipo=_opt_str(datos.get("tipo")),
            reducida=bool(reducida) if reducida is not None else None,
            tipo_contrato=_opt_str(datos.get("tipo_contrato")),
        )

    # ------------------------------------------------------------- #
    # HTTP.
    # ------------------------------------------------------------- #
    def _get(
        self, path: str, params: dict[str, Any], *, label: str
    ) -> dict[str, Any] | None:
        """GET a sesame-api. ``None`` si 404; ``RuntimeError`` si falla."""
        url = f"{self._base_url}{path}"
        headers = {"x-api-key": self._api_key}
        transport = self._transport or httpx.HTTPTransport(retries=1)
        try:
            with httpx.Client(
                timeout=self._timeout_s, transport=transport
            ) as client:
                response = client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"sesame-api no se pudo consultar en {label}: {exc!r}"
            ) from exc
        status = response.status_code
        texto = (response.text or "")[:_MAX_CUERPO]
        if status == 404:
            logger.info(
                "%s %s: 404 (Sesame no conoce ese DNI)", _LOG_PREFIX, label
            )
            return None
        if status >= 400:
            raise RuntimeError(
                f"sesame-api respondio {status} en {label}: {texto}"
            )
        try:
            cuerpo = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"sesame-api respuesta no JSON en {label}: {texto}"
            ) from exc
        if not isinstance(cuerpo, dict) or not cuerpo.get("ok", False):
            raise RuntimeError(
                f"sesame-api devolvio ok=false en {label}: {texto}"
            )
        return cuerpo

    @staticmethod
    def _festivos_del_ano(datos: Any, ano: int) -> list[FestivoDia]:
        """Festivos de ese ano, descartando filas sin fecha utilizable."""
        prefijo = f"{int(ano):04d}-"
        out: list[FestivoDia] = []
        for item in datos or []:
            if not isinstance(item, dict):
                continue
            fecha = _opt_str(item.get("fecha"))
            if not fecha or not fecha.startswith(prefijo):
                continue
            out.append(FestivoDia(fecha=fecha,
                                  nombre=_opt_str(item.get("nombre"))))
        return out


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None
