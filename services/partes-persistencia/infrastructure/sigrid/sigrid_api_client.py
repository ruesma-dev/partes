# infrastructure/sigrid/sigrid_api_client.py
"""Cliente HTTP de SOLO LECTURA contra la Function App ``sigrid-api``.

Sirve los lookups que el sv3 necesita para casar un parte:
  - ``fetch_empleados``   -> tabla ``emp`` (extiende ``con``)
  - ``fetch_obras``       -> tabla ``obr`` (extiende ``con``)
  - ``fetch_tipos_hora``  -> tabla ``auxhor`` (codigo de hora)
  - ``fetch_recursos``, ``fetch_reshor``, ``fetch_empresas``,
    ``fetch_partidas_obra`` y ``fetch_hmo_obra``.

Realiza POST a ``/api/sql/read`` con cabecera ``x-functions-key`` y
cuerpo ``{database, sql, parameters, timeout_seconds, max_rows}``. La
respuesta es ``{ok, columns, rows, row_count, truncated}``.

F-023: los maestros son de TODAS las empresas (``con.emp`` viaja en cada
fila; ``SIGRID_EMPRESA`` ya no filtra nada). Todo listado se PAGINA
(``_leer_paginado``: ``ORDER BY`` por clave unica + ``OFFSET/FETCH`` de
``PAGINA_FILAS``) y una respuesta con ``truncated: true`` es una
excepcion: un maestro a medias puede hacer unica a una persona que tiene
dos fichas.

Cumple el puerto ``SigridLookupPort``. Best-effort: ante error de Sigrid
las llamadas lanzan, pero el pipeline las captura y degrada a "sin
casar" (los lookups solo se invocan si Sigrid esta cableado).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from domain.models.sigrid_models import (
    EmpleadoRow, EmpresaRow, HmoRow, ObraRow, PartidaRow, RecursoRow,
    ReshorRow, TipoHoraRow,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sigrid-client]"

#: Filas por pagina de los listados (F-023, R3). Se piden con
#: ``max_rows = PAGINA_FILAS + 1``: con ``FETCH NEXT PAGINA_FILAS`` la API
#: nunca tiene motivo para recortar, asi que ``truncated`` es siempre error.
PAGINA_FILAS = 5000


# Empleados: emp extiende con (emp.ide = con.ide). Codigo en con.cod,
# nombre completo en emp.res, DNI en emp.dni, Recurso en emp.reside.
# F-023: de TODAS las empresas, con la empresa (con.emp) y la baja del
# concepto (con.fecbaj), que es la que cuenta (DA1).
_SQL_EMPLEADOS = """\
SELECT
    con.ide    AS ide,
    con.cod    AS codigo,
    emp.res    AS nombre,
    emp.dni    AS dni,
    emp.reside AS reside,
    con.emp    AS empresa,
    con.fecbaj AS fecbaj
FROM emp
JOIN con ON emp.ide = con.ide
"""

# Obras: obr extiende con. Sin DISTINCT (obr.res es text/ntext y SQL
# Server no permite DISTINCT sobre ese tipo). F-023: una entrada por ide
# con su empresa; NO se deduplica por codigo (hay codigos en dos empresas).
_SQL_OBRAS = """\
SELECT
    con.ide AS ide,
    con.cod AS codigo,
    obr.res AS nombre,
    con.emp AS empresa
FROM obr
JOIN con ON obr.ide = con.ide
WHERE con.cod IS NOT NULL
"""

# Tipos de hora (auxhor). fecbaj=0 (o NULL) => activo. ext distingue
# normal(0)/extra(1). Se pagina por auxhor.ide y el orden (ext, cod) se
# rehace en Python.
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
"""

# Empresas (auxemp), F-023: numemp es el numero que usa con.emp.
_SQL_EMPRESAS = """\
SELECT
    auxemp.numemp AS numemp,
    auxemp.res    AS nombre,
    auxemp.fecbaj AS fecbaj,
    auxemp.desact AS desact
FROM auxemp
"""


# Partidas del presupuesto de una obra (obrparpar). padide = capitulo padre
# (raices padide=0). cod/res/tex describen; tipdes=0 activa; cosindide marca
# tipo de coste indirecto. El arbol, la clasificacion CD/CI/CP (por capitulo
# raiz) y la deteccion de hoja se hacen en partida_catalog.py.
_SQL_PARTIDAS = """\
SELECT
    obrparpar.ide       AS ide,
    obrparpar.padide    AS padide,
    obrparpar.cod       AS cod,
    obrparpar.res       AS res,
    obrparpar.tex       AS tex,
    obrparpar.tipdes    AS tipdes,
    obrparpar.cosindide AS cosindide,
    obrparpar.unimed    AS unimed
FROM obrparpar
WHERE obrparpar.obride = ?
"""


# Recursos (res extiende con; ide = con.ide). cif = DNI/NIF; conide =
# empleado asociado (emp). restipide -> auxrestip da la CLASIFICACION
# (categoria: cod/res). horide = tipo de hora por defecto (hora laborable
# ordinaria). Maestro para resolver el recurso y pisar categoria/hora.
# F-023: + empresa y baja del concepto del recurso (con rc).
_SQL_RECURSOS = """\
SELECT
    res.ide       AS ide,
    res.cif       AS cif,
    res.conide    AS conide,
    res.restipide AS restipide,
    auxrestip.cod AS restip_cod,
    auxrestip.res AS restip_res,
    res.horide    AS horide_def,
    rc.emp        AS empresa,
    rc.fecbaj     AS fecbaj,
    rc.cod        AS codigo,
    rc.res        AS nombre,
    res.cla       AS cla
FROM res
JOIN con rc ON rc.ide = res.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
"""

# Costes de horas de los recursos (reshor x auxhor): por cada recurso y
# tipo de hora, su codigo/descripcion, el flag extra y la cantidad por
# defecto (candef = jornada por defecto en la hora laborable). Es la base
# para pisar el codigo de hora del registro con el del recurso y guardar
# el CanDefecto.
_SQL_RESHOR = """\
SELECT
    reshor.reside AS reside,
    reshor.horide AS horide,
    auxhor.cod    AS cod,
    auxhor.res    AS res,
    auxhor.ext    AS ext,
    reshor.candef AS candef,
    reshor.pre    AS pre
FROM reshor
JOIN auxhor ON auxhor.ide = reshor.horide
"""

# Partes de trabajo (hmo) de una obra: ide + recurso + ano + mes. Para
# localizar el parte donde se imputarian las horas (reside+obride+ano+mes).
_SQL_HMO_OBRA = """\
SELECT
    hmo.ide    AS ide,
    hmo.reside AS reside,
    hmo.ano    AS ano,
    hmo.mes    AS mes
FROM hmo
WHERE hmo.obride = ?
"""


class SigridApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 30.0,
        max_rows: int = 10000,
    ) -> None:
        if not base_url:
            raise ValueError("SigridApiClient requiere base_url no vacio")
        if not function_key:
            raise ValueError("SigridApiClient requiere function_key no vacio")
        if not database:
            raise ValueError("SigridApiClient requiere database no vacio")
        self._base_url = base_url.rstrip("/")
        self._function_key = function_key
        self._database = database
        self._timeout_s = float(timeout_s)
        self._max_rows = int(max_rows)
        logger.info(
            "%s Instanciado. base_url=%s database=%s timeout_s=%s "
            "max_rows=%s key_len=%s",
            _LOG_PREFIX,
            self._base_url,
            self._database,
            self._timeout_s,
            self._max_rows,
            len(function_key),
        )

    # ----------------------------------------------------------------- #
    # Lookups publicos.
    # ----------------------------------------------------------------- #
    def fetch_empleados(self) -> list[EmpleadoRow]:
        columns, rows = self._leer_paginado(
            sql=_SQL_EMPLEADOS, parameters=[], orden="con.ide",
            label="empleados",
        )
        out: list[EmpleadoRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(
                EmpleadoRow(
                    ide=ide,
                    codigo=_opt_str(rm.get("codigo")),
                    nombre=_opt_str(rm.get("nombre")),
                    dni=_opt_str(rm.get("dni")),
                    reside=_opt_int(rm.get("reside")),
                    empresa=_opt_int(rm.get("empresa")),
                    fecbaj=_opt_int(rm.get("fecbaj")),
                )
            )
        logger.info("%s empleados -> %s filas", _LOG_PREFIX, len(out))
        return out

    def fetch_obras(self) -> list[ObraRow]:
        columns, rows = self._leer_paginado(
            sql=_SQL_OBRAS, parameters=[], orden="con.ide", label="obras"
        )
        seen: set[int] = set()
        out: list[ObraRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            cod = _opt_str(rm.get("codigo"))
            ide = _opt_int(rm.get("ide"))
            if not cod or ide is None or ide in seen:
                continue
            seen.add(ide)
            out.append(
                ObraRow(ide=ide, codigo=cod, nombre=_opt_str(rm.get("nombre")),
                        empresa=_opt_int(rm.get("empresa")))
            )
        logger.info("%s obras -> %s filas", _LOG_PREFIX, len(out))
        return out

    def fetch_partidas_obra(self, obra_ide: int) -> list[PartidaRow]:
        """Filas crudas de ``obrparpar`` de una obra (lineas y capitulos del
        presupuesto). El arbol/clasificacion se hace en partida_catalog."""
        columns, rows = self._leer_paginado(
            sql=_SQL_PARTIDAS, parameters=[int(obra_ide)],
            orden="obrparpar.ide", label="partidas",
        )
        out: list[PartidaRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(PartidaRow(
                ide=ide,
                padide=_opt_int(rm.get("padide")),
                cod=_opt_str(rm.get("cod")),
                res=_opt_str(rm.get("res")),
                tex=_opt_str(rm.get("tex")),
                tipdes=_opt_int(rm.get("tipdes")) or 0,
                cosindide=_opt_int(rm.get("cosindide")),
                unimed=_opt_str(rm.get("unimed")),
            ))
        logger.info(
            "%s partidas obra=%s -> %s filas", _LOG_PREFIX, obra_ide, len(out)
        )
        return out

    def fetch_recursos(self) -> list[RecursoRow]:
        """Maestro de recursos (``res``): ide, cif (DNI/NIF), conide
        (empleado asociado), su CLASIFICACION (restipide + cod/res de
        ``auxrestip``) y su tipo de hora por defecto (``horide``). F-030:
        tambien su codigo y nombre (``con.cod``/``con.res``), en la misma
        lectura paginada, para las fichas de recurso. F-036 (R1): y su
        clase (``res.cla``), que dice que recursos son de persona."""
        columns, rows = self._leer_paginado(
            sql=_SQL_RECURSOS, parameters=[], orden="res.ide",
            label="recursos",
        )
        out: list[RecursoRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(RecursoRow(
                ide=ide, cif=_opt_str(rm.get("cif")),
                conide=_opt_int(rm.get("conide")),
                restipide=_opt_int(rm.get("restipide")),
                restip_cod=_opt_str(rm.get("restip_cod")),
                restip_res=_opt_str(rm.get("restip_res")),
                horide_def=_opt_int(rm.get("horide_def")),
                empresa=_opt_int(rm.get("empresa")),
                fecbaj=_opt_int(rm.get("fecbaj")),
                codigo=_opt_str(rm.get("codigo")),
                nombre=_opt_str(rm.get("nombre")),
                cla=_opt_int(rm.get("cla")),
            ))
        logger.info("%s recursos -> %s filas", _LOG_PREFIX, len(out))
        return out

    def fetch_reshor(self) -> list[ReshorRow]:
        """Costes de horas de los recursos (``reshor`` x ``auxhor``): por
        cada (recurso, tipo de hora) su codigo/descripcion, flag extra,
        cantidad por defecto (``candef``) y precio coste."""
        columns, rows = self._leer_paginado(
            sql=_SQL_RESHOR, parameters=[], orden="reshor.ide",
            label="reshor",
        )
        out: list[ReshorRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            reside = _opt_int(rm.get("reside"))
            horide = _opt_int(rm.get("horide"))
            if reside is None or horide is None:
                continue
            out.append(ReshorRow(
                reside=reside, horide=horide,
                cod=_opt_str(rm.get("cod")), res=_opt_str(rm.get("res")),
                ext=_opt_int(rm.get("ext")) or 0,
                candef=_opt_float(rm.get("candef")),
                pre=_opt_float(rm.get("pre")),
            ))
        logger.info("%s reshor -> %s filas", _LOG_PREFIX, len(out))
        return out

    def fetch_hmo_obra(self, obra_ide: int) -> list[HmoRow]:
        """Partes de trabajo (``hmo``) de una obra: ide + recurso + ano + mes."""
        columns, rows = self._leer_paginado(
            sql=_SQL_HMO_OBRA, parameters=[int(obra_ide)], orden="hmo.ide",
            label="hmo",
        )
        out: list[HmoRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(HmoRow(
                ide=ide, reside=_opt_int(rm.get("reside")),
                ano=_opt_int(rm.get("ano")), mes=_opt_int(rm.get("mes")),
            ))
        logger.info(
            "%s hmo obra=%s -> %s filas", _LOG_PREFIX, obra_ide, len(out)
        )
        return out

    def fetch_tipos_hora(self) -> list[TipoHoraRow]:
        columns, rows = self._leer_paginado(
            sql=_SQL_TIPOS_HORA, parameters=[], orden="auxhor.ide",
            label="tipos_hora",
        )
        out: list[TipoHoraRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            ide = _opt_int(rm.get("ide"))
            if ide is None:
                continue
            out.append(
                TipoHoraRow(
                    ide=ide,
                    codigo=_opt_str(rm.get("codigo")),
                    descripcion=_opt_str(rm.get("descripcion")),
                    ext=_opt_int(rm.get("ext")) or 0,
                    pre=_opt_float(rm.get("pre")),
                    prenom=_opt_float(rm.get("prenom")),
                )
            )
        # El orden de negocio de siempre (normales antes que extras, por
        # codigo): paginar obliga a pedirlos por auxhor.ide.
        out.sort(key=lambda t: (t.ext, t.codigo or ""))
        logger.info("%s tipos_hora -> %s filas", _LOG_PREFIX, len(out))
        return out

    def fetch_empresas(self) -> list[EmpresaRow]:
        """Empresas de ``auxemp`` (F-023): numero, nombre, baja, desact."""
        columns, rows = self._leer_paginado(
            sql=_SQL_EMPRESAS, parameters=[], orden="auxemp.ide",
            label="empresas",
        )
        out: list[EmpresaRow] = []
        for row in rows:
            rm = dict(zip(columns, row))
            numemp = _opt_int(rm.get("numemp"))
            if numemp is None:
                continue
            out.append(EmpresaRow(
                numemp=numemp, nombre=_opt_str(rm.get("nombre")),
                fecbaj=_opt_int(rm.get("fecbaj")),
                desact=_opt_int(rm.get("desact")),
            ))
        logger.info("%s empresas -> %s filas", _LOG_PREFIX, len(out))
        return out

    # ----------------------------------------------------------------- #
    # Paginacion (F-023, R3).
    # ----------------------------------------------------------------- #
    def _leer_paginado(
        self,
        *,
        sql: str,
        parameters: list[Any],
        orden: str,
        label: str,
    ) -> tuple[list[str], list[list[Any]]]:
        """Lee un listado entero por paginas de ``PAGINA_FILAS``.

        ``orden`` es una clave unica y estable (nunca un campo ``text``):
        sin ella OFFSET/FETCH podria saltarse o repetir filas entre paginas.
        Para en la primera pagina incompleta.
        """
        sql_pagina = (
            f"{sql.rstrip()}\nORDER BY {orden}\n"
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY\n"
        )
        columnas: list[str] = []
        filas: list[list[Any]] = []
        desde = 0
        while True:
            columnas, pagina = self._post_sql_read(
                sql=sql_pagina,
                parameters=[*parameters, desde, PAGINA_FILAS],
                label=label,
                max_rows=PAGINA_FILAS + 1,
            )
            if len(pagina) > PAGINA_FILAS:
                raise RuntimeError(
                    f"sigrid-api devolvio {len(pagina)} filas en una pagina "
                    f"de {PAGINA_FILAS} [{label}]"
                )
            filas.extend(pagina)
            if len(pagina) < PAGINA_FILAS:
                return columnas, filas
            desde += PAGINA_FILAS

    # ----------------------------------------------------------------- #
    # HTTP primitive.
    # ----------------------------------------------------------------- #
    def _post_sql_read(
        self,
        *,
        sql: str,
        parameters: list[Any],
        label: str,
        max_rows: int | None = None,
    ) -> tuple[list[str], list[list[Any]]]:
        url = f"{self._base_url}/api/sql/read"
        payload = {
            "database": self._database,
            "sql": sql,
            "parameters": parameters,
            "timeout_seconds": int(self._timeout_s),
            "max_rows": self._max_rows if max_rows is None else max_rows,
        }
        headers = {
            "x-functions-key": self._function_key,
            "Content-Type": "application/json",
        }
        logger.info(
            "%s REQUEST [%s] -> POST %s db=%s params=%s",
            _LOG_PREFIX, label, url, self._database, parameters,
        )
        transport = httpx.HTTPTransport(retries=1)
        try:
            with httpx.Client(timeout=self._timeout_s, transport=transport) as client:
                response = client.post(url, json=payload, headers=headers)
        except Exception as exc:
            logger.exception(
                "%s FALLO de transporte [%s]. exc=%r", _LOG_PREFIX, label, exc
            )
            raise

        status = response.status_code
        body_text = response.text or ""
        if status >= 400:
            logger.warning(
                "%s RESPONSE [%s] status=%s preview=%s",
                _LOG_PREFIX, label, status, body_text[:300],
            )
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
            # F-023 (R4): filas parciales NUNCA; mejor sin casar que mal.
            raise RuntimeError(
                f"sigrid-api devolvio una respuesta truncada [{label}]"
            )

        columns: list[str] = list(body.get("columns") or [])
        rows: list[list[Any]] = list(body.get("rows") or [])
        logger.info(
            "%s RESPONSE [%s] <- %s filas", _LOG_PREFIX, label, len(rows)
        )
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
