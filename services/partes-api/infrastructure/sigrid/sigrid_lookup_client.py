# infrastructure/sigrid/sigrid_lookup_client.py
"""Cliente HTTP de SOLO LECTURA contra ``sigrid-api`` para sv2 (extracción).

Dos lecturas, ambas por ``POST /api/sql/read`` contra la base configurada:

- ``fetch_tipos_hora``: el catálogo de tipos de hora (``auxhor``) que se
  inyecta en el prompt para que la IA proponga el código de hora (lo cachea
  ``AuxhorCatalogProvider``).
- ``existe_obra`` (F-058, DA10 = B): si hay en Sigrid alguna obra con una
  clave dada, de cualquier empresa y también de baja; una consulta en el
  momento por página, con su propio tope de tiempo, para decidir si se
  relee la cabecera. No casa la obra: eso lo hace sv3.

``truncated: true`` es siempre error (F-038): nunca se decide con filas
parciales.
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from typing import Any

import httpx
from domain.models.clave_obra import clave_obra

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sigrid-lookup]"

#: F-038 (R2, DA1 = B): `max_rows` de la lectura si no se pasa otro; el tope
#: de la instancia de sigrid-api. Igual que `SIGRID_API_MAX_ROWS`.
MAX_ROWS_DEFECTO = 500_000

_SQL_TIPOS_HORA = """\
SELECT
    auxhor.ide    AS ide,
    auxhor.cod    AS codigo,
    auxhor.res    AS descripcion,
    auxhor.ext    AS ext,
    auxhor.pre    AS pre,
    auxhor.prenom AS prenom
FROM auxhor
WHERE (auxhor.fecbaj IS NULL OR auxhor.fecbaj = 0)
ORDER BY auxhor.ext, auxhor.cod
"""

#: F-058 (R7, DA10 = B): ¿hay alguna obra con esta clave? La clave llega como
#: el único parámetro ``?`` (nunca concatenada) y se calcula igual sobre
#: ``con.cod``: sin espacios ni guiones y, si queda solo de dígitos, sin ceros
#: a la izquierda; mayúsculas y acentos los iguala la intercalación. Sin
#: filtro de empresa ni de baja. ``TOP 1``: basta saber si hay alguna.
_SQL_EXISTE_OBRA = """SELECT TOP 1 con.cod AS codigo
FROM obr JOIN con ON obr.ide = con.ide
CROSS APPLY (SELECT REPLACE(REPLACE(con.cod, ' ', ''), '-', '') AS n) a
CROSS APPLY (SELECT CASE WHEN a.n <> '' AND a.n NOT LIKE '%[^0-9]%'
    THEN ISNULL(NULLIF(SUBSTRING(a.n, PATINDEX('%[^0]%', a.n + 'X'), 24), ''), '0')
    ELSE a.n END AS clave) k
WHERE con.cod IS NOT NULL AND k.clave COLLATE Latin1_General_CI_AI = ?
"""


# --------------------- F-063 · patrón LIKE de una clave --------------------- #

#: R6: los especiales de ``LIKE`` de T-SQL van como literales.
_ESPECIALES_LIKE = {"%": "[%]", "_": "[_]", "[": "[[]"}

#: Rango de caracteres cuyas variantes se buscan (Latin-1 y Latin Extended-A).
_RANGO_VARIANTES = range(0x00A0, 0x0180)


def _tabla_variantes() -> dict[str, frozenset[str]]:
    """Para cada carácter de U+00A0–U+017F cuya ``clave_obra`` es UNA letra
    o dígito, lo apunta bajo esa base: ``"A"`` → {ª, À, Á, …, à, á, …},
    ``"N"`` → {Ñ, ñ, Ń, …}, ``"2"`` → {²}, ``"O"`` → {º, Ò, …}.

    R5 lo pide para toda base con variantes del rango; casi todas son ASCII,
    pero también ``µ`` (clave ``Μ``, griega). Solo letras y dígitos: dentro
    de ``[...]`` nunca va ``^``, ``-`` ni ``]``.
    """
    tabla: dict[str, set[str]] = {}
    for punto in _RANGO_VARIANTES:
        caracter = chr(punto)
        base = clave_obra(caracter)
        if len(base) == 1 and base.isalnum() and caracter.isalnum():
            tabla.setdefault(base, set()).add(caracter)
    return {base: frozenset(variantes) for base, variantes in tabla.items()}


#: Se calcula una vez al importar el módulo.
_VARIANTES = _tabla_variantes()


def _clase(caracter: str) -> str:
    """Un carácter de la clave como elemento del patrón ``LIKE`` (R5, R6)."""
    if caracter in _ESPECIALES_LIKE:
        return _ESPECIALES_LIKE[caracter]
    opciones = {caracter} | _VARIANTES.get(caracter, frozenset())
    minuscula = caracter.lower()
    if len(minuscula) == 1:
        opciones.add(minuscula)
    if len(opciones) == 1:
        return caracter
    return "[" + "".join(sorted(opciones)) + "]"


def patron_like(clave: str) -> str:
    """F-063 (R4–R7): patrón ``LIKE`` que casa con todo código de esa clave.

    ``%`` y, tras cada carácter de la clave, su clase y otro ``%``: un código
    cuya clave es ``clave`` contiene sus caracteres en orden con cualquier
    cosa entre ellos (blancos, guiones, ceros a la izquierda, espacio duro),
    así que casa siempre, distinga o no la intercalación mayúsculas y
    acentos. Trae un superconjunto: el filtro exacto lo hace ``existe_obra``.
    ``"692"`` → ``"%6%9%[2²]%"``. Una clave vacía lanza ``ValueError``
    (nunca un ``%`` suelto que traiga todas las obras).
    """
    if not clave:
        raise ValueError("patron_like requiere una clave no vacía")
    return "%" + "".join(_clase(c) + "%" for c in clave)


@dataclass(frozen=True)
class TipoHoraOption:
    ide: int
    codigo: str | None
    descripcion: str | None
    ext: int
    pre: float | None
    prenom: float | None


class SigridLookupClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 30.0,
        max_rows: int = MAX_ROWS_DEFECTO,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("SigridLookupClient requiere base_url no vacio")
        if not function_key:
            raise ValueError("SigridLookupClient requiere function_key no vacio")
        if not database:
            raise ValueError("SigridLookupClient requiere database no vacio")
        self._base_url = base_url.rstrip("/")
        self._function_key = function_key
        self._database = database
        self._timeout_s = float(timeout_s)
        self._max_rows = int(max_rows)
        # Solo los tests lo pasan (httpx.MockTransport); si no, el de siempre.
        self._transport = transport
        logger.info(
            "%s Instanciado. base_url=%s database=%s timeout_s=%s "
            "max_rows=%s",
            _LOG_PREFIX, self._base_url, self._database, self._timeout_s,
            self._max_rows,
        )

    def fetch_tipos_hora(self) -> list[TipoHoraOption]:
        columns, rows = self._post_sql_read(
            sql=_SQL_TIPOS_HORA, parameters=[], label="tipos_hora"
        )
        out: list[TipoHoraOption] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(
                TipoHoraOption(
                    ide=ide,
                    codigo=_opt_str(rm.get("codigo")),
                    descripcion=_opt_str(rm.get("descripcion")),
                    ext=_opt_int(rm.get("ext")) or 0,
                    pre=_opt_float(rm.get("pre")),
                    prenom=_opt_float(rm.get("prenom")),
                )
            )
        logger.info("%s tipos_hora -> %s filas", _LOG_PREFIX, len(out))
        return out

    def existe_obra(self, clave: str, *, timeout_s: float) -> bool:
        """F-058: ``True`` si hay alguna obra con esa clave (ya normalizada).

        Con su propio tope (``OBRA_EXISTE_TIMEOUT_S``), no el del catálogo.
        Un error HTTP, ``ok=false``, ``truncated`` o el tope superado lanzan:
        los recoge ``ComprobadorObra`` como «no se sabe».
        """
        _, rows = self._post_sql_read(
            sql=_SQL_EXISTE_OBRA, parameters=[clave], label="existe_obra",
            timeout_s=timeout_s,
        )
        return len(rows) >= 1

    def _post_sql_read(
        self, *, sql: str, parameters: list[Any], label: str,
        timeout_s: float | None = None,
    ) -> tuple[list[str], list[list[Any]]]:
        """``timeout_s`` (F-058): tope de esta lectura; sin él, el del cliente."""
        url = f"{self._base_url}/api/sql/read"
        if timeout_s is None:
            plazo = self._timeout_s
            timeout_seconds = int(self._timeout_s)
        else:
            plazo = float(timeout_s)
            timeout_seconds = max(1, math.ceil(plazo))
        payload = {
            "database": self._database,
            "sql": sql,
            "parameters": parameters,
            "timeout_seconds": timeout_seconds,
            "max_rows": self._max_rows,
        }
        headers = {
            "x-functions-key": self._function_key,
            "Content-Type": "application/json",
        }
        transport = self._transport or httpx.HTTPTransport(retries=1)
        with httpx.Client(timeout=plazo, transport=transport) as client:
            response = client.post(url, json=payload, headers=headers)
        status = response.status_code
        body_text = response.text or ""
        if status >= 400:
            raise RuntimeError(f"sigrid-api respondio {status}: {body_text[:300]}")
        try:
            body: dict[str, Any] = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"sigrid-api respuesta no JSON: {body_text[:300]}"
            ) from exc
        if not body.get("ok", False):
            raise RuntimeError(f"sigrid-api devolvio ok=false: {body!r}")
        if body.get("truncated"):
            # F-038 (R7): nunca se devuelven filas parciales.
            raise RuntimeError(
                f"sigrid-api devolvio una respuesta truncada [{label}]")
        columns: list[str] = list(body.get("columns") or [])
        rows: list[list[Any]] = list(body.get("rows") or [])
        return columns, rows


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return str(value)


def _opt_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _opt_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
