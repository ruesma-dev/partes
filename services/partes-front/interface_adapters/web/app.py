# interface_adapters/web/app.py
"""Portal de revision de partes de trabajo (sv4).

Paginas:
  GET /                       -> redirige a /trabajadores
  GET /trabajadores           -> una linea por TRABAJADOR (agregado)
  GET /trabajadores/{key}     -> detalle: una linea por REGISTRO horario
  GET /partes                 -> una linea por PARTE DIARIO
  GET /partes/{document_id}   -> detalle del parte (empleados + firma + aprobar)

APIs / acciones:
  GET   /api/sigrid/tipos-hora            -> opciones del desplegable auxhor
  PATCH /api/registros/{id}/hora          -> fija el codigo de hora (auxhor)
  PATCH /api/registros/{id}               -> edita tipo_hora / horas
  POST  /documents/{id}/approve|unapprove|delete  (form -> redirect 'back')
"""
from __future__ import annotations

import html
import logging
import os
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

import httpx
import yaml
from fastapi import Body, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from application.services.comprobacion_sigrid import (
    ComprobacionSigrid,
    RegistroComprobaciones,
)
from application.services.congelacion import CongeladoError
from application.services.incidencias_horas import (
    Incompatibilidad,
    TablaIncidencias,
    parsear_tabla,
    resumen_por_dia,
)
from application.services.tipo_hora_catalog import TipoHoraCatalog
from application.services.calendar_builder import (
    build_calendar,
    build_period_options,
    normalize_mode,
    parse_period_key,
    DayObra,
)
from application.services.calendario_provider import CalendarioProvider
from application.services.holiday_provider import HolidayProvider
from application.services.jornada_admin import (
    ABREVIATURA_DIA,
    DIAS as DIAS_JORNADA,
    JornadaInvalida,
    a_hasta_exclusivo,
    buscar_solape,
    describir_conflicto,
    entrada_desde_fila,
    normalizar_entrada,
    ultimo_dia_incluido_de_fila,
    validar_entrada,
    validar_vigencia,
)
from application.services.jornada_provider import JornadaEmpleadoProvider
from application.services.text_match import normalize_dni
from application.services.jornada_resolver import (
    candef_valido,
    detalle_jornada_dia,
    jornada_dia,
    jornada_efectiva,
    parsear_mapa_semanal,
)
from config.settings import Settings
from infrastructure.sesame.sesame_api_client import SesameApiClient
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    extras_por_jornada,
)
from infrastructure.database.session_factory import SessionFactory
from infrastructure.transfer.resultado_sigrid import aplicar_resultado
from infrastructure.transfer.transfer_client import TransferClient
from infrastructure.transfer.transfer_queue_publisher import (
    TransferQueuePublisher,
)
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient
from infrastructure.graph.token_provider import GraphTokenProvider
from interface_adapters.web.identidad import (
    CABECERA_ID,
    CABECERA_NOMBRE,
    CABECERA_TOKEN,
    actor_desde_cabeceras,
    senal_de_despliegue,
)
from application.services.obra_catalog import ObraCatalog
from application.services.empleado_catalog import EmpleadoCatalog
from application.services.empresas import (
    NOMBRES_EMPRESA,
    nombre_empresa_o_vacio,
)
from application.services.recurso_catalog import (
    RecursoCatalog,
    asignacion_de,
)
from application.services import empleado_reconciler as recon
from application.services.reparto_obras import (
    SEPARADOR_CLAVE,
    UMBRAL_PLEGADO,
    GrupoObra,
    agregar_ejecucion,
    agregar_preflight,
    listado_grupo,
    repartir_claves,
    totales,
)

logger = logging.getLogger(__name__)


@dataclass
class Preparado:
    """F-022: una aprobacion lista para sv5, ya repartida por obra.

    `claves` son las de pisar de cada grupo, sin su prefijo (R19); `datos`
    es lo que devolvio el repositorio (para `excluidas` y su detalle).
    """

    grupos: list[GrupoObra]
    claves: dict[str, list[str]]
    datos: dict

#: F-003 (R23/R24). Motivo del bloqueo del registro cuando Sesame esta
#: configurado pero no responde: sin sus festivos, el computo de horas
#: puede estar mal y registrar en Sigrid escribe de verdad. La unica
#: salida es el override consciente del modal, que queda marcado.
MOTIVO_BLOQUEO_SESAME = (
    "calendario Sesame no disponible: el calculo puede ser incorrecto"
)

#: F-022 (DA11): ids por aprobacion con `ambito`. Una obra x mes ronda las
#: mil lineas; el tope evita que una peticion desbocada lea media base.
MAX_IDS_APROBACION = 5000

# Leyenda de incidencias (para mostrar el nombre largo del codigo).
_INCIDENCIAS = {
    "V": "Vacaciones",
    "B": "Baja enf. comun",
    "AT": "Accidente trabajo",
    "FJ": "Falta justificada",
    "F": "Falta no justif.",
    "H": "Huelga",
    "M": "Maternidad/Pat.",
}


def _fmt_horas(value: Any) -> str:
    if value is None or value == "":
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    if n == int(n):
        return f"{int(n)} h"
    return f"{n:.2f}".replace(".", ",") + " h"


def _fmt_fecha(value: Any) -> str:
    """ISO 'YYYY-MM-DD' -> 'DD/MM/YYYY'."""
    if not value:
        return "—"
    s = str(value)
    parts = s.split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return s


def _incidencia_label(codigo: Any) -> str:
    if not codigo:
        return ""
    return _INCIDENCIAS.get(str(codigo).upper(), str(codigo))


def _preview_error_html(*, title: str, message: str, external_url: str | None) -> str:
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    link = ""
    if external_url:
        safe_url = html.escape(external_url)
        link = (
            f'<p><a href="{safe_url}" target="_blank" rel="noopener">'
            "Abrir el parte en SharePoint ↗</a></p>"
        )
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Vista previa no disponible</title>
<style>
 body{{font-family:Arial,Helvetica,sans-serif;background:#f4f5f6;color:#1d2024;
  margin:0;padding:24px;display:flex;align-items:center;justify-content:center;height:100vh;box-sizing:border-box}}
 .card{{max-width:560px;background:#fff;border:1px solid #dfe2e4;border-radius:12px;
  padding:24px;box-shadow:0 8px 24px rgba(29,32,36,.07)}}
 h1{{margin-top:0;font-size:18px}} p{{line-height:1.5;color:#4a4f55}}
 a{{color:#9f2842;text-decoration:none;font-weight:600}}
</style></head>
<body><div class="card"><h1>{safe_title}</h1><p>{safe_message}</p>{link}</div></body></html>"""


def _guess_pdf_media_type(name: str | None) -> str:
    n = (name or "").lower()
    if n.endswith(".pdf"):
        return "application/pdf"
    if n.endswith(".png"):
        return "image/png"
    if n.endswith(".jpg") or n.endswith(".jpeg"):
        return "image/jpeg"
    return "application/pdf"


class HoraPayload(BaseModel):
    hora_ide: int


class PartidaPayload(BaseModel):
    partida_ide: int | None = None
    partida_cod: str | None = None
    partida_res: str | None = None
    partida_capitulo: str | None = None


#: Tope de ids por peticion de comprobacion y de estado (F-024, R17/R28).
MAX_IDS_COMPROBAR = 5000

#: Origenes admitidos en el log de la comprobacion (R21). Cualquier otro
#: valor del navegador se registra como `boton`: el log no repite texto
#: libre que llegue de fuera.
ORIGENES_COMPROBACION = ("vista-obra", "vista-trabajador", "boton")


class ComprobarSigridPayload(BaseModel):
    registro_ids: list[int] = Field(min_length=1,
                                    max_length=MAX_IDS_COMPROBAR)
    forzar: bool = False
    origen: str | None = None


class EstadoAprobacionPayload(BaseModel):
    registro_ids: list[int] = Field(min_length=1,
                                    max_length=MAX_IDS_COMPROBAR)


class FechaPayload(BaseModel):
    fecha: str  # ISO 'YYYY-MM-DD' (input date) o 'DD/MM/YYYY'


class ObraPayload(BaseModel):
    codigo: str
    ide: int | None = None
    nombre: str | None = None

    @field_validator("codigo", mode="before")
    @classmethod
    def _codigo_str(cls, v: object) -> str:
        return str(v or "").strip()


def _parse_fecha_to_iso_int(value: str) -> tuple[str, int] | None:
    """Acepta 'YYYY-MM-DD' (input date) o 'DD/MM/YYYY' -> (iso, YYYYMMDD)."""
    s = (value or "").strip()
    if not s:
        return None
    y = m = d = None
    if "-" in s and len(s.split("-")[0]) == 4:
        parts = s.split("-")
        if len(parts) == 3:
            y, m, d = parts
    elif "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            d, m, y = parts
    if y is None or m is None or d is None:
        return None
    try:
        yi, mi, di = int(y), int(m), int(d)
        from datetime import date
        date(yi, mi, di)  # valida
    except (TypeError, ValueError):
        return None
    return f"{yi:04d}-{mi:02d}-{di:02d}", yi * 10000 + mi * 100 + di


class RegistroEditPayload(BaseModel):
    tipo_hora: str | None = None
    horas: float | None = None

    @field_validator("horas", mode="before")
    @classmethod
    def _num_or_none(cls, v: object) -> float | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if not s or s == "\u2014":
            return None
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    @field_validator("tipo_hora", mode="before")
    @classmethod
    def _str_or_none(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


def _borradas_sigrid(registros) -> int:
    """F-024 (R24): lineas de la vista que ya no estan en Sigrid."""
    return sum(1 for r in registros
               if (r.sigrid_estado or "").strip().lower() == "borrado_sigrid")


def _as_int(value: Any) -> int | None:
    """Coacciona a int tolerando str/float; None si no es convertible."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


#: Raiz del servicio: contra ella se resuelven las rutas relativas de los
#: ficheros de datos versionados (`config/*.yaml`).
RAIZ_SERVICIO = Path(__file__).resolve().parents[2]


def construir_tabla_incidencias(settings: Settings) -> TablaIncidencias:
    """F-025 (R1, R2): la tabla versionada de clases de incidencia.

    Se lee AL ARRANCAR y un fallo lo tumba (como la tabla del membrete de
    sv3): una incidencia mal clasificada en silencio dejaria pasar a Sigrid
    horas en un dia de baja, o bloquearia dias correctos sin que nadie
    supiera por que. PyYAML llega con `uvicorn[standard]`.
    """
    ruta = Path(settings.incidencias_path)
    if not ruta.is_absolute():
        ruta = RAIZ_SERVICIO / ruta
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"incidencias: no se puede leer {ruta}: {exc}") from exc
    try:
        datos = yaml.safe_load(texto)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"incidencias: no se puede parsear {ruta}: {exc}") from exc
    tabla = parsear_tabla(datos)
    logger.info(
        "[incidencias][wiring] clases desde %s: %s", ruta,
        ", ".join(f"{c.letra}={c.sigrid}:{c.clase}"
                  for c in tabla.por_letra.values()),
    )
    return tabla


def build_app(
    settings: Settings,
    *,
    repository: ParteReviewRepository | None = None,
    transfer_client: TransferClient | None = None,
    publisher: TransferQueuePublisher | None = None,
    cola_cliente=None,
    calendario_provider: CalendarioProvider | None = None,
    jornada_provider: JornadaEmpleadoProvider | None = None,
) -> FastAPI:
    """Portal de revision.

    Los colaboradores se pueden inyectar (repositorio, cliente HTTP de
    sv5, publisher de `q-transfer`, cliente de cola para la gestion de
    poison, proveedor de calendario y proveedor de excepciones de
    jornada). Sin inyeccion se construyen desde `settings`, que es lo que
    hace `main.py`; con ella, la suite levanta la app sin PostgreSQL, sin
    red y sin Storage.
    """
    # Jornada del DIA (F-015). Lo PRIMERO: un mapa mal escrito cambiaria
    # los avisos de jornada incompleta de todo el portal en silencio, asi
    # que es preferible que la app no levante (fail-fast, R10). Se parsea
    # aqui y no en `config/settings.py` para no invertir las capas.
    mapa_semanal = parsear_mapa_semanal(settings.jornada_semanal_por_candef)
    logger.info(
        "[jornada][wiring] mapa candef -> jornada semanal: %s",
        ", ".join(f"{c:g}:{v:g}" for c, v in sorted(mapa_semanal.items())),
    )
    # F-025: clases de incidencia, tambien fail-fast (R2).
    tabla_incidencias = construir_tabla_incidencias(settings)

    if repository is None:
        session_factory = SessionFactory(
            database_url=settings.database_url,
            admin_database_url=settings.admin_database_url,
            target_database_name=settings.pg_db,
            auto_create_database=settings.auto_create_database,
        )
        repository = ParteReviewRepository(session_factory)
        tables_ready = repository.initialize()
    else:
        tables_ready = True

    sigrid_client: SigridLookupClient | None = None
    if settings.sigrid_lookup_enabled:
        sigrid_client = SigridLookupClient(
            base_url=settings.sigrid_api_base_url,          # type: ignore[arg-type]
            function_key=settings.sigrid_api_function_key,  # type: ignore[arg-type]
            database=settings.sigrid_api_database,          # type: ignore[arg-type]
            timeout_s=settings.sigrid_api_timeout_s,
        )
        logger.info(
            "[sigrid-lookup][wiring] CABLEADO base_url=%s database=%s",
            settings.sigrid_api_base_url, settings.sigrid_api_database,
        )
    else:
        logger.info(
            "[sigrid-lookup][wiring] DESACTIVADO (faltan SIGRID_API_*); "
            "el desplegable de codigo de hora quedara vacio."
        )
    catalog = TipoHoraCatalog(client=sigrid_client)
    obra_catalog = ObraCatalog(client=sigrid_client)
    empleado_catalog = EmpleadoCatalog(client=sigrid_client)
    # F-035: recursos activos de clase persona para los selectores.
    recurso_catalog = RecursoCatalog(client=sigrid_client)

    # Token provider de Graph para el visor de PDF (descarga desde SharePoint).
    graph_token_provider: GraphTokenProvider | None = None
    if settings.preview_enabled:
        graph_token_provider = GraphTokenProvider(
            settings.graph_key, settings.graph_timeout_s  # type: ignore[arg-type]
        )
        logger.info("[preview][wiring] Visor de PDF CABLEADO (Graph).")
    else:
        logger.info(
            "[preview][wiring] Visor de PDF DESACTIVADO (falta GRAPH_KEY)."
        )

    # Festivos. El respaldo (libreria `holidays` + extras) sigue siendo
    # el de siempre; con Sesame configurado, el proveedor lo antepone con
    # el calendario REAL de cada trabajador y deja el respaldo para
    # cuando Sesame no esta (F-003).
    holiday_provider = HolidayProvider(
        enabled=settings.holidays_enabled,
        subdiv=settings.holidays_subdiv,
        extra_iso=settings.holidays_extra_list,
    )
    if calendario_provider is None:
        sesame_client: SesameApiClient | None = None
        if settings.sesame_enabled:
            sesame_client = SesameApiClient(
                base_url=settings.sesame_api_base_url,   # type: ignore[arg-type]
                api_key=settings.sesame_api_key,         # type: ignore[arg-type]
                timeout_s=settings.sesame_api_timeout_s,
            )
            logger.info(
                "[sesame][wiring] CABLEADO base_url=%s key_len=%s ttl_s=%s",
                settings.sesame_api_base_url,
                len(settings.sesame_api_key or ""),
                settings.sesame_cache_ttl_s,
            )
        else:
            logger.info(
                "[sesame][wiring] DESACTIVADO (faltan SESAME_API_*); los "
                "festivos salen del respaldo local y no se bloquea ningun "
                "registro."
            )
        calendario_provider = CalendarioProvider(
            cliente=sesame_client,
            respaldo_holiday_name=holiday_provider.name,
            ttl_seconds=settings.sesame_cache_ttl_s,
        )

    # Excepciones de jornada (`empleado_jornada`). La tabla nace vacia:
    # mientras no tenga filas, el proveedor devuelve None y la jornada de
    # cada dia sale del mapa. Si la lectura falla, las vistas se sirven
    # igual con la jornada derivada (R17).
    if jornada_provider is None:
        jornada_provider = JornadaEmpleadoProvider(
            repository.list_jornadas_empleado,
            ttl_seconds=settings.jornada_cache_ttl_s,
        )

    # Cliente del servicio de REGISTRO en Sigrid (partes-transfer, sv5).
    # Sigue siendo el canal SINCRONO: preflight y pisado de conflictos.
    if transfer_client is None and settings.transfer_enabled:
        transfer_client = TransferClient(
            base_url=settings.transfer_base_url,
            timeout_s=settings.transfer_timeout_s,
        )
        logger.info("[transfer][wiring] CABLEADO base_url=%s",
                    settings.transfer_base_url)
    elif transfer_client is None:
        logger.info("[transfer][wiring] DESHABILITADO (falta TRANSFER_BASE_URL)")

    # F-024: comprobacion de lineas `registrado` contra Sigrid (via sv5).
    # UNA por proceso: su registro de comprobaciones recientes (R19) es lo
    # que evita que cada recarga de una vista vuelva a preguntar a sv5.
    comprobacion_sigrid: ComprobacionSigrid | None = None
    if transfer_client is not None:
        comprobacion_sigrid = ComprobacionSigrid(
            repository=repository, transfer_client=transfer_client,
            lote=settings.comprobacion_sigrid_lote,
            timeout_s=settings.comprobacion_sigrid_timeout_s,
            recientes=RegistroComprobaciones(
                ttl_s=settings.comprobacion_sigrid_ttl_s),
        )

    # Resolver de trabajadores SIN codigo de hora extra (fuente: reshor de
    # Sigrid, ANCLADO POR DNI), con cache en proceso de 10 min. Ante fallo
    # de Sigrid se asume que TODOS tienen (no se excluye a nadie: fail-open).
    # known[dni_normalizado] = True si TIENE extra, False si NO.
    _extra_cache: dict[str, Any] = {"ts": 0.0, "map": {}}

    def _norm_dni(dni: str | None) -> str:
        import re
        return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()

    def recursos_sin_extra_resolver(trabajadores: list[dict]) -> set[str]:
        """Recibe [{'dni':..., 'recurso_ide':...}, ...] y devuelve el
        conjunto de DNIs (normalizados) que NO tienen codigo de hora
        extra en Sigrid. La exclusion se ancla al DNI, no al recurso_ide
        (que puede estar mal persistido)."""
        if not settings.sigrid_lookup_enabled or not sigrid_client:
            return set()
        now = time.time()
        if now - _extra_cache["ts"] > 600:
            _extra_cache["map"] = {}
            _extra_cache["ts"] = now
        known: dict[str, bool] = _extra_cache["map"]

        pedidos = {_norm_dni(t.get("dni")) for t in trabajadores}
        pedidos.discard("")
        faltan = {d for d in pedidos if d not in known}
        if faltan:
            try:
                sin = sigrid_client.fetch_dnis_sin_extra(faltan)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "[recursos-extra] fallo consultando reshor por DNI; no "
                    "se excluye a nadie de los totales", exc_info=True,
                )
                sin = set()  # fail-open: todos cuentan
                for d in faltan:
                    known[d] = True
            else:
                for d in faltan:
                    known[d] = d not in sin  # True = tiene extra
        resultado = {d for d in pedidos if not known.get(d, True)}
        logger.info(
            "[recursos-extra] dnis=%s sin_codigo_extra=%s",
            sorted(pedidos), sorted(resultado),
        )
        return resultado

    app = FastAPI(title=settings.app_title, version=settings.service_version)
    app.state.settings = settings
    app.state.repository = repository
    app.state.catalog = catalog
    app.state.obra_catalog = obra_catalog
    app.state.empleado_catalog = empleado_catalog
    app.state.recurso_catalog = recurso_catalog
    app.state.graph_token_provider = graph_token_provider
    app.state.calendario_provider = calendario_provider
    app.state.jornada_provider = jornada_provider
    app.state.mapa_semanal = mapa_semanal
    app.state.tabla_incidencias = tabla_incidencias
    app.state.tables_ready = tables_ready
    # F-017 R5c, senal B: ¿este proceso ha visto ya alguna cabecera de Easy
    # Auth? Es la red de seguridad de la senal A (las `CONTAINER_APP_*`).
    # Es por PROCESO, no compartida entre replicas: como mucho, una segunda
    # replica tarda una peticion autenticada en aprender lo mismo.
    app.state.easy_auth_visto = False
    # F-017 R9: la nota de arranque se emite UNA vez, en la primera
    # peticion (aqui todavia no se sabe si traera cabecera o no).
    app.state.identidad_anunciada = False

    templates = Jinja2Templates(
        directory=str(Path(__file__).resolve().parents[2] / "templates")
    )
    templates.env.filters["horas"] = _fmt_horas
    templates.env.filters["fecha"] = _fmt_fecha
    templates.env.filters["incidencia"] = _incidencia_label
    templates.env.globals["asset_version"] = str(int(time.time()))
    # Enlace «Jornadas» de la barra (R15). Como global, para no tener que
    # anadirlo al contexto de las diez vistas que ya existen.
    templates.env.globals["jornadas_admin_enabled"] = bool(
        settings.jornadas_admin_enabled)
    # F-035: opciones de los selectores de empresa (Conciliar, Nuevo parte
    # y el modal «+ Añadir linea» de base.html).
    templates.env.globals["EMPRESAS"] = sorted(NOMBRES_EMPRESA.items())
    app.mount(
        "/static",
        StaticFiles(
            directory=str(Path(__file__).resolve().parents[2] / "static")
        ),
        name="static",
    )

    # --- F-016: quien firma y quien puede entrar ---------------------- #

    def _resolver_identidad(request: Request) -> tuple[str, str]:
        """Resuelve `(actor, origen)` y mantiene viva la senal B (R5c).

        Vive junto a `_actor` y NO lo sustituye: `_actor` es la firma que
        consumen los once puntos de escritura y la que vigila el guardian
        de F-016. Aqui esta todo lo que la funcion pura de `identidad.py`
        no puede hacer: leer el entorno del proceso, recordar si ya se ha
        visto una cabecera y escribir en el log.
        """
        senal = senal_de_despliegue(
            os.environ, cabecera_vista=app.state.easy_auth_visto)
        actor, origen = actor_desde_cabeceras(
            request.headers, fallback=settings.default_reviewer,
            desplegado=senal is not None)

        if origen.startswith("cabecera"):
            app.state.easy_auth_visto = True                  # senal B
        elif origen == "sin-identidad-desplegado":
            # R5b: NO es «una sesion sin identificar», es la autenticacion
            # caida. Un WARNING por peticion, porque cada una es un
            # incidente y tiene que verse en Log Analytics en vez de
            # colarse en una columna en silencio.
            logger.warning(
                "[identidad] peticion SIN identidad de Easy Auth estando "
                "desplegado (senal=%s, ruta=%s): se sella '%s'. Revisa la "
                "autenticacion del portal.",
                senal, request.url.path, actor)

        # R9: una sola nota por arranque, con la senal que se encontro.
        # Ni el token ni los claims ni el propio actor salen en el log:
        # aqui interesa el DIAGNOSTICO, no quien es la persona.
        if not app.state.identidad_anunciada:
            app.state.identidad_anunciada = True
            logger.info(
                "[identidad] primera peticion atendida: entorno=%s "
                "senal=%s cabecera_easy_auth=%s",
                "desplegado" if senal else "local", senal,
                "si" if origen.startswith("cabecera") else "no")
        return actor, origen

    def _actor(request: Request) -> str | None:
        """Quien firma el cambio. PUNTO UNICO de identidad del portal (R10).

        F-016 dejo escrito que aqui solo cambiaria el INTERIOR cuando
        llegase F-017: asi ha sido. La firma es la misma y los cinco
        endpoints de jornadas no se han tocado.

        Devuelve el principal de Easy Auth (`X-MS-CLIENT-PRINCIPAL-NAME`,
        o el claim preferido del token si aquella no llega), normalizado y
        truncado a 120. Sin cabecera: `local:<DEFAULT_REVIEWER>` en un
        puesto de desarrollo, `sin-identidad` estando desplegado. **Nunca
        devuelve vacio** (R7): desde F-017, un NULL en una columna de
        autor significa «fila anterior al corte» — en las columnas que el
        portal escribe; `undo_log.actor` no participa del criterio porque
        no la escribe nadie (es trabajo de F-018).

        Se mantiene el tipo `str | None` aunque hoy nunca devuelva `None`:
        es el que aceptan las siete columnas y los repositorios.
        """
        actor, _origen = _resolver_identidad(request)
        return actor

    def _exigir_admin_jornadas() -> None:
        """Puerta UNICA de la pantalla de jornadas (R15).

        Hoy: el interruptor `JORNADAS_ADMIN_ENABLED`. Cuando exista F-008
        (roles), la comprobacion de rol se escribe AQUI y en ningun otro
        sitio. Por eso es una funcion y no un middleware por prefijo: un
        middleware habria que desmontarlo (DA9).

        404 y no 403 a proposito: con la pantalla apagada no existe.
        """
        if not settings.jornadas_admin_enabled:
            raise HTTPException(status_code=404, detail="Pagina no encontrada.")

    # --- F-004: congelacion -> 409 (no es un 500) --------------------- #
    @app.exception_handler(CongeladoError)
    def _congelado_handler(
        _request: Request, exc: CongeladoError
    ) -> JSONResponse:
        """Una edicion sobre algo congelado no es un fallo del sistema:
        es una regla de negocio diciendo que no. El front pinta `error`
        tal cual, asi que el motivo tiene que ser legible por un humano.
        """
        logger.info("[congelado] mutacion rechazada: %s", exc.motivo)
        return JSONResponse(
            {"ok": False, "congelado": True, "error": exc.motivo},
            status_code=409,
        )

    # ----------------------------------------------------------------- #
    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "partes-portal",
            "version": settings.service_version,
            "tables_ready": app.state.tables_ready,
            "database": settings.pg_db,
            "sigrid_lookup_enabled": settings.sigrid_lookup_enabled,
        }

    @app.get("/whoami")
    def whoami(request: Request) -> dict[str, Any]:
        """F-017 R21: quien cree el portal que eres, y por que.

        Existe para que la verificacion M1 se pueda hacer **sin escribir
        una fila**: sin ella habria que aprobar un parte de verdad y mirar
        la base, y si sale mal el dato ya esta escrito.

        Devuelve la identidad de quien pregunta y NADA mas: ni el token,
        ni los claims, ni los valores de las cabeceras, ni un dato de otro
        usuario. De las cabeceras solo salen los NOMBRES de las que
        vienen, que es lo que hace falta para diagnosticar.

        `entorno` y `senal_despliegue` son los campos que delatan el unico
        fallo de esta feature que ensucia datos —creerse local estando
        desplegado (design.md §4.1)—, y por eso van aqui.
        """
        senal = senal_de_despliegue(
            os.environ, cabecera_vista=app.state.easy_auth_visto)
        actor, origen = _resolver_identidad(request)
        return {
            "actor": actor,
            "origen": origen,                  # la RAMA por la que salio
            "entorno": "desplegado" if senal else "local",
            "senal_despliegue": senal,         # POR QUE se cree desplegado
            "cabeceras_easy_auth": [           # NOMBRES, nunca valores
                c for c in (CABECERA_NOMBRE, CABECERA_TOKEN, CABECERA_ID)
                if c.lower() in request.headers
            ],
        }

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/trabajadores", status_code=302)

    # ---------------- Trabajadores ----------------------------------- #
    @app.get("/trabajadores", response_class=HTMLResponse)
    def trabajadores_list(
        request: Request,
        search: str | None = Query(default=None),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        workers = repository.list_workers(search=search)
        context = {
            "request": request,
            "title": settings.app_title,
            "workers": workers,
            "search": search or "",
            "total_normales": round(sum(w.horas_normales for w in workers), 2),
            "total_extra": round(sum(w.horas_extra for w in workers), 2),
            "total_incidencias": sum(w.num_incidencias for w in workers),
            "sin_casar": sum(1 for w in workers if not w.matched),
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="trabajadores_list.html", context=context
        )

    @app.get("/trabajadores/{worker_key}", response_class=HTMLResponse)
    def trabajador_detail(
        request: Request,
        worker_key: str,
        period: str | None = Query(default=None),
        modo: str | None = Query(default=None),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        mode = normalize_mode(modo)
        detail = repository.get_worker(worker_key,
                                       incidencias=tabla_incidencias)
        if detail is None:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado")

        # Agregado por dia y OBRA (para la tarjeta del calendario: el codigo
        # de obra encima de las horas; si hay 2 obras, 2 columnas).
        per_day: dict[str, dict] = {}
        for r in detail.registros:
            if not r.fecha:
                continue
            slot = per_day.setdefault(
                r.fecha,
                {"normal": 0.0, "extra": 0.0, "incidencias": 0, "_obras": {}},
            )
            okey = r.obra_codigo or r.obra_nombre or "—"
            oslot = slot["_obras"].setdefault(
                okey,
                {"codigo": r.obra_codigo, "nombre": r.obra_nombre,
                 "normal": 0.0, "extra": 0.0, "inc": 0},
            )
            if r.es_incidencia:
                slot["incidencias"] += 1
                oslot["inc"] += 1
            elif (r.tipo_hora or "") == "extra" or r.hora_ext == 1:
                slot["extra"] += r.horas or 0.0
                oslot["extra"] += r.horas or 0.0
            else:
                slot["normal"] += r.horas or 0.0
                oslot["normal"] += r.horas or 0.0

        for slot in per_day.values():
            obras = [
                DayObra(
                    obra_codigo=o["codigo"], obra_nombre=o["nombre"],
                    normal_h=round(o["normal"], 2), extra_h=round(o["extra"], 2),
                    incidencias=o["inc"],
                )
                for o in slot.pop("_obras").values()
            ]
            obras.sort(key=lambda x: (x.obra_codigo or "~"))
            slot["obras"] = obras

        period_options = build_period_options(
            [r.fecha for r in detail.registros], mode
        )
        selected = parse_period_key(period)
        if selected is None and period_options:
            selected = parse_period_key(period_options[0].key)

        # Festivos DE ESTE TRABAJADOR (R2/R3): antes de F-003 el
        # calendario era global y a quien no fuera de Madrid le salian
        # avisos de jornada incompleta en dias que para el eran fiesta.
        calendar = None
        anos_consultados: set[int] = set()
        if selected is not None:
            y, m = selected
            calendar = build_calendar(
                year=y,
                month=m,
                per_day=per_day,
                holiday_name=calendario_provider.holiday_name_para(detail.dni),
                mode=mode,
            )
            anos_consultados = {
                int(_d.date_iso[:4])
                for _w in calendar.weeks for _d in _w
                if _d.in_period and _d.date_iso
            }

        # Cantidad por defecto (CanDefecto) del recurso, para diagnostico.
        # Se distingue 0 de None (un 0 significa que Sigrid no tiene la
        # jornada informada; el calculo de sv3 usa 8 en ese caso).
        candef_recurso = sorted({
            float(r.hora_candef)
            for r in detail.registros
            if r.hora_candef is not None
        })
        # Presentacion del CanDefecto: si Sigrid no lo informa o es <= el
        # minimo, se muestra la jornada por defecto (no la de Sigrid) y se
        # marca como valor "asignado".
        _cd_real = min(candef_recurso) if candef_recurso else None
        _cd_efectivo = jornada_efectiva(
            _cd_real,
            minimo=settings.candef_minimo_valido,
            por_defecto=settings.jornada_por_defecto,
        )
        candef_kpi = {
            "valor": _cd_efectivo,
            # "asignado" = el valor mostrado NO viene de Sigrid, se le ha
            # asignado la jornada por defecto porque el candef no era valido.
            "asignado": not candef_valido(
                _cd_real, minimo=settings.candef_minimo_valido
            ),
            "sigrid": _cd_real,
        }

        # Dias LABORABLES con jornada ordinaria incompleta: horas
        # ordinarias del dia por debajo de LA JORNADA DE ESE DIA (F-015),
        # que es el candef efectivo salvo el ultimo dia laborable de la
        # semana, que recibe el resto de la jornada semanal. Se excluyen
        # findes/festivos y los dias sin horas ordinarias (0).
        def _es_laborable_trabajador(d: date) -> bool:
            return calendario_provider.dia(d, detail.dni).laborable

        def _jornada_de(d: date) -> float:
            return jornada_dia(
                d, candef=_cd_real,
                minimo=settings.candef_minimo_valido,
                por_defecto=settings.jornada_por_defecto,
                mapa=mapa_semanal, es_laborable=_es_laborable_trabajador,
                excepcion=jornada_provider.excepcion_para(detail.dni, d),
            )

        dias_incompletos: set[str] = set()
        if calendar is not None:
            for _week in calendar.weeks:
                for _day in _week:
                    if not (_day.in_period and not _day.is_weekend
                            and not _day.is_holiday and _day.date_iso):
                        continue
                    if 0.0 < (_day.normal_h or 0.0) < (
                        _jornada_de(date.fromisoformat(_day.date_iso)) - 1e-9
                    ):
                        dias_incompletos.add(_day.date_iso)

        # F-025 (R16): el peor nivel de cada dia (incidencia de dia
        # completo con horas, o parcial con extra), para el calendario.
        dias_incompatibles = resumen_por_dia(
            (r.fecha, Incompatibilidad(r.incompat_nivel, r.incompat_motivo))
            for r in detail.registros if r.fecha and r.incompat_nivel)

        # KPI de jornada (R25): con que numeros se esta calculando. Sin
        # esto, F-015 seria magia: el portal dejaria de avisar de unos dias
        # y empezaria a avisar de otros sin que se pudiera ver por que. La
        # excepcion se resuelve con el PRIMER dia del periodo mostrado.
        _dia_kpi = next(
            (date.fromisoformat(_d.date_iso)
             for _w in (calendar.weeks if calendar else [])
             for _d in _w if _d.in_period and _d.date_iso),
            None,
        )
        _excepcion_kpi = (
            jornada_provider.excepcion_para(detail.dni, _dia_kpi)
            if _dia_kpi is not None else None
        )
        _detalle_kpi = detalle_jornada_dia(
            _dia_kpi or date.today(), candef=_cd_real,
            minimo=settings.candef_minimo_valido,
            por_defecto=settings.jornada_por_defecto,
            mapa=mapa_semanal, es_laborable=_es_laborable_trabajador,
            excepcion=_excepcion_kpi,
        )
        _patron_kpi = (
            _excepcion_kpi.patron
            if _excepcion_kpi is not None and _excepcion_kpi.valida()
            else None
        )
        jornada_kpi = {
            "candef": _cd_efectivo,
            "semanal": _detalle_kpi.semanal,
            "origen": _detalle_kpi.origen,
            # Horas del ultimo dia laborable de la semana. Con patron no
            # hay "resto" que ensenar: manda el patron entero.
            "ultimo_laborable": (
                None if _patron_kpi is not None
                else max(0.0, _detalle_kpi.semanal - 4.0 * _cd_efectivo)
            ),
            "patron": _patron_kpi,
        }

        # R22: si alguna resolucion de calendario de esta vista salio de
        # la cache caducada o del respaldo, se avisa EN LA PANTALLA. La
        # vista se sirve igual (nivel 1 de D2), pero el usuario tiene que
        # saber que los festivos pueden no estar al dia.
        sesame_degradado = not calendario_provider.fiable_para(
            (detail.dni, ano) for ano in anos_consultados
        )

        # R13/R14: tipo de jornada del contrato. Sesame NO da las horas
        # (peticion P1), asi que esto no toca ni un calculo; sirve para
        # ensenar el dato y para avisar de una divergencia que hoy no ve
        # nadie: contrato de jornada reducida contra jornada aplicada de
        # 8 h. `reducida=None` es "no se sabe" y no dispara el aviso.
        jornada_contrato = calendario_provider.jornada_contrato(detail.dni)
        jornada_divergente = bool(
            jornada_contrato is not None
            and jornada_contrato.reducida
            and _cd_efectivo >= settings.jornada_por_defecto
        )

        context = {
            "request": request,
            "title": settings.app_title,
            "detail": detail,
            "calendar": calendar,
            "candef_recurso": candef_recurso,
            "candef_kpi": candef_kpi,
            "jornada_kpi": jornada_kpi,
            "dias_incompletos": dias_incompletos,
            "dias_incompatibles": dias_incompatibles,
            "sesame_degradado": sesame_degradado,
            "jornada_contrato": jornada_contrato,
            "jornada_divergente": jornada_divergente,
            "extras": extras_por_jornada(detail.registros),
            "borradas_sigrid": _borradas_sigrid(detail.registros),
            "period_options": period_options,
            "selected_period": calendar.period_key if calendar else None,
            "period_mode": mode,
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "preview_enabled": settings.preview_enabled,
            "transfer_enabled": transfer_client is not None,
            "back": f"/trabajadores/{worker_key}",
            "worker_key": worker_key,
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="trabajador_detail.html", context=context
        )

    # ---------------- Partes diarios --------------------------------- #
    # ----------------------------- OBRAS ----------------------------- #
    @app.get("/obras", response_class=HTMLResponse)
    def obras_list(
        request: Request,
        search: str | None = Query(default=None),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        obras = repository.list_obras(
            search=search, sin_extra_resolver=recursos_sin_extra_resolver
        )
        context = {
            "request": request,
            "title": settings.app_title,
            "obras": obras,
            "search": search or "",
            "total_normales": round(sum(o.horas_normales for o in obras), 2),
            "total_extra": round(sum(o.horas_extra for o in obras), 2),
            "total_incidencias": sum(o.num_incidencias for o in obras),
            "num_obras": len(obras),
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="obras_list.html", context=context
        )

    @app.get("/obras/{obra_key}", response_class=HTMLResponse)
    def obra_detail(
        request: Request,
        obra_key: str,
        period: str | None = Query(default=None),
        modo: str | None = Query(default=None),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        mode = normalize_mode(modo)
        # La COLUMNA se tinta con el calendario por defecto (D6): una
        # consulta, no una por fila x dia. La exactitud por trabajador
        # vive donde importa, en los avisos de jornada incompleta.
        detail = repository.get_obra(
            obra_key, period_key=period, mode=mode,
            holiday_name=calendario_provider.holiday_name_para(None),
            sin_extra_resolver=recursos_sin_extra_resolver,
            incidencias=tabla_incidencias,
        )
        if detail is None:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        # Trabajadores SIN codigo de hora extra: sus horas tampoco cuentan
        # en el KPI 'Extra por jornada'.
        _excl_rec = {
            r.recurso_ide for r in detail.rows
            if not r.tiene_extra and r.recurso_ide
        }
        _regs_kpi = [
            v for v in detail.registros
            if not (v.recurso_ide and v.recurso_ide in _excl_rec)
        ]

        # Avisos de jornada incompleta por (trabajador, dia): horas
        # ordinarias EN ESTA OBRA por debajo del CanDefecto efectivo del
        # recurso (u 8 si era <= minimo). Se excluyen findes/festivos.
        _cd_min = settings.candef_minimo_valido
        _cd_jor = settings.jornada_por_defecto
        _candef_real: dict[str, float] = {}
        for _r in detail.registros:
            if _r.hora_candef is None:
                continue
            _nom = _r.trabajador_nombre or ""
            _v = float(_r.hora_candef)
            if _nom not in _candef_real or _v < _candef_real[_nom]:
                _candef_real[_nom] = _v
        incompletos: set[str] = set()
        _consultas: set[tuple[str | None, int]] = set()
        for _row in detail.rows:
            _real = _candef_real.get(_row.nombre or "")
            # Festivo SEGUN EL CALENDARIO DE ESTA FILA (R2): la columna
            # pinta el calendario por defecto, pero el aviso no puede
            # heredar los festivos de otra provincia.
            _es_festivo = calendario_provider.holiday_name_para(_row.dni)

            def _es_laborable_fila(d: date, _dni=_row.dni) -> bool:
                return calendario_provider.dia(d, _dni).laborable

            for _c in _row.cells:
                if not _c.date_iso:
                    continue
                _fecha = date.fromisoformat(_c.date_iso)
                _consultas.add((_row.dni, _fecha.year))
                if _c.is_weekend or _es_festivo(_fecha):
                    continue
                # JORNADA DEL DIA de ESTA fila (F-015): el candef efectivo
                # salvo su ultimo dia laborable, que recibe el resto de la
                # jornada semanal.
                _eff = jornada_dia(
                    _fecha, candef=_real, minimo=_cd_min,
                    por_defecto=_cd_jor, mapa=mapa_semanal,
                    es_laborable=_es_laborable_fila,
                    excepcion=jornada_provider.excepcion_para(
                        _row.dni, _fecha),
                )
                if 0.0 < (_c.normal or 0.0) < _eff - 1e-9:
                    incompletos.add((_row.nombre or "") + "|"
                                    + (_c.date_iso or ""))
        _dias_periodo = {int(d.date_iso[:4]) for d in detail.days if d.date_iso}
        _consultas.update((None, ano) for ano in _dias_periodo)
        sesame_degradado = not calendario_provider.fiable_para(_consultas)

        # F-035 (R20): el combo de trabajador ofrece solo recursos de la
        # empresa de la ficha de obra; sin ella (o sin Sigrid), todos.
        empresa_obra: int | None = None
        try:
            _obra = obra_catalog.get_by_ide(detail.obra_ide)
            empresa_obra = _obra.empresa if _obra is not None else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("[obra-detail] empresa de la obra: %r", exc)

        context = {
            "request": request,
            "title": settings.app_title,
            "detail": detail,
            "period_options": detail.period_options,
            "selected_period": detail.period_key,
            "extras": extras_por_jornada(_regs_kpi),
            "borradas_sigrid": _borradas_sigrid(detail.registros),
            "transfer_enabled": transfer_client is not None,
            "candef_minimo": settings.candef_minimo_valido,
            "jornada_defecto": settings.jornada_por_defecto,
            "incompletos": incompletos,
            "sesame_degradado": sesame_degradado,
            "period_mode": mode,
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "preview_enabled": settings.preview_enabled,
            "back": f"/obras/{obra_key}",
            "obra_key": obra_key,
            "empresa_obra": empresa_obra,
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="obra_detail.html", context=context
        )

    # -------------------- CONCILIACION de trabajadores ---------------- #
    def _candidato_con_empresa(item: dict[str, Any]) -> dict[str, Any]:
        """F-035 (R10): empresa del recurso candidato y su nombre corto."""
        rec = recurso_catalog.get_by_ide(item["ide"])
        empresa = rec.empresa if rec is not None else None
        item["empresa"] = empresa
        item["empresa_nombre"] = nombre_empresa_o_vacio(empresa)  # F-039
        return item

    def _trabajador_pedido(
        data: dict,
    ) -> tuple[dict[str, Any] | None, JSONResponse | None]:
        """F-035 (R11, R15): el trabajador elegido en el cuerpo.

        Con `recurso_ide` se resuelve en el catalogo de recursos y se
        usa su `Asignacion` (R12/R13); sin el, el camino de empleados de
        siempre por `ide`. Devuelve `(datos, None)`, `(None, error)` o
        `(None, None)` si no viene ninguno. Los datos llevan
        `ide/codigo/nombre/dni/reside`."""
        if data.get("recurso_ide") not in (None, ""):
            rec = recurso_catalog.get_by_ide(_as_int(data.get("recurso_ide")))
            if rec is None:
                return None, JSONResponse(
                    {"ok": False, "error": "Recurso no encontrado entre los "
                     f"activos (recurso_ide={data.get('recurso_ide')!r}). "
                     "¿Sigrid configurado en sv4?"},
                    status_code=404,
                )
            a = asignacion_de(rec)
            return {"ide": a.empleado_ide, "codigo": a.codigo,
                    "nombre": a.nombre, "dni": a.dni,
                    "reside": a.reside}, None
        ide = _as_int(data.get("ide"))
        if ide is None:
            return None, None
        emp = empleado_catalog.get_by_ide(ide)
        if emp is None:
            return None, JSONResponse(
                {"ok": False, "error": "Empleado no encontrado en el maestro "
                 f"(ide={ide}). ¿Sigrid configurado en sv4?"},
                status_code=404,
            )
        return {"ide": emp.ide, "codigo": emp.codigo, "nombre": emp.nombre,
                "dni": emp.dni, "reside": None}, None

    @app.get("/conciliacion", response_class=HTMLResponse)
    def conciliacion(request: Request) -> HTMLResponse:
        pendientes = repository.list_unmatched_workers()
        # F-035 (R7): candidatos entre los RECURSOS activos (tambien quien
        # no tiene ficha de empleado), de la empresa por defecto de la
        # tarjeta (R8): la de sus partes si es una sola; si no, todas.
        recursos = recurso_catalog.list() if recurso_catalog.enabled else []

        filas: list[dict] = []
        n_auto = n_rev = n_sin = n_cat = 0
        for p in pendientes:
            empresas_p = p.get("empresas") or []
            empresa_defecto = (
                empresas_p[0] if len(empresas_p) == 1 else None)
            candidatos_de = (
                recursos if empresa_defecto is None
                else [r for r in recursos if r.empresa == empresa_defecto])
            bucket, cands = recon.classify(
                p["nombre_leido"], candidatos_de, top_n=5)
            if bucket == "auto":
                n_auto += 1
            elif bucket == "revisar":
                n_rev += 1
            elif bucket == "categoria":
                n_cat += 1
            else:
                n_sin += 1
            filas.append({
                "nombre_leido": p["nombre_leido"],
                "num_registros": p["num_registros"],
                "obras": p["obras"],
                "categorias": p["categorias"],
                "partes": p.get("partes", []),
                "bucket": bucket,
                "empresa_defecto": empresa_defecto,
                "candidates": [
                    _candidato_con_empresa(
                        {"ide": c.ide, "codigo": c.codigo,
                         "nombre": c.nombre, "dni": c.dni,
                         "score": round(c.score * 100)})
                    for c in cands
                ],
            })

        context = {
            "request": request,
            "title": settings.app_title,
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "preview_enabled": settings.preview_enabled,
            "empleados_total": len(recursos),   # F-035: cuenta recursos
            "filas": filas,
            "n_total": len(filas),
            "n_auto": n_auto,
            "n_revisar": n_rev,
            "n_sin": n_sin,
            "n_categoria": n_cat,
        }
        return templates.TemplateResponse(
            request=request, name="conciliacion.html", context=context
        )

    @app.post("/api/conciliacion/confirmar")
    async def conciliacion_confirmar(request: Request) -> JSONResponse:
        try:
            data = await request.json()
        except Exception:  # noqa: BLE001
            data = None
        if not isinstance(data, dict):
            return JSONResponse(
                {"ok": False, "error": "Body no es JSON válido."},
                status_code=400,
            )
        nombre_leido = data.get("nombre_leido")
        emp: dict[str, Any] | None = None
        if nombre_leido:
            emp, error = _trabajador_pedido(data)
            if error is not None:
                return error
        if not nombre_leido or emp is None:
            return JSONResponse(
                {"ok": False, "error": "Faltan datos: "
                 f"nombre_leido={nombre_leido!r}, ide={data.get('ide')!r}, "
                 f"recurso_ide={data.get('recurso_ide')!r}."},
                status_code=400,
            )
        try:
            updated, congeladas = repository.backfill_empleado(
                nombre_leido=nombre_leido, ide=emp["ide"],
                codigo=emp["codigo"], nombre=emp["nombre"], dni=emp["dni"],
                reside=emp["reside"],
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[conciliacion] backfill fallo")
            return JSONResponse(
                {"ok": False, "error": f"Error guardando casado: "
                 f"{type(exc).__name__}: {exc}"},
                status_code=500,
            )
        # El alias es una optimizacion (auto-casado futuro): best-effort.
        # F-040 (R17): de la ficha o del recurso elegido (`reside`), con o
        # sin ficha y con o sin DNI.
        alias_ok = True
        if emp["ide"] is not None or emp["reside"] is not None:
            try:
                repository.upsert_empleado_alias(
                    nombre_leido=nombre_leido, ide=emp["ide"],
                    codigo=emp["codigo"], nombre=emp["nombre"],
                    dni=emp["dni"], created_by="conciliacion",
                    recurso_ide=emp["reside"],
                )
            except Exception as exc:  # noqa: BLE001
                alias_ok = False
                logger.warning("[conciliacion] alias no guardado: %r", exc)
        return JSONResponse({
            "ok": True, "updated": updated, "alias_ok": alias_ok,
            # F-004 R8: las lineas congeladas se omiten; decirlo evita
            # que el usuario crea que su casado se aplico entero.
            "congeladas": congeladas,
            "empleado": {"ide": emp["ide"], "codigo": emp["codigo"],
                         "nombre": emp["nombre"]},
        })

    @app.get("/api/conciliacion/buscar")
    def conciliacion_buscar(
        q: str = Query(default=""),
        nombre_leido: str | None = Query(default=None),
        empresa: int | None = Query(default=None),
    ) -> JSONResponse:
        # F-035 (R9): entre los recursos activos de `empresa` (o todos).
        empleados = (recurso_catalog.list(empresa)
                     if recurso_catalog.enabled else [])
        query = (q or nombre_leido or "").strip()
        if not query:
            return JSONResponse({"ok": True, "items": []})
        from application.services import text_match as _tm
        scored = []
        qn = _tm.normalize(query)
        for e in empleados:
            s = _tm.name_similarity(query, e.nombre)
            # tambien por subcadena de codigo o nombre (busqueda manual libre)
            sub = qn and (qn in _tm.normalize(e.nombre) or qn in _tm.normalize(e.codigo))
            if s >= 0.30 or sub:
                scored.append((max(s, 0.31 if sub else 0.0), e))
        scored.sort(key=lambda t: t[0], reverse=True)
        items = [
            {"ide": e.ide, "codigo": e.codigo, "nombre": e.nombre,
             "dni": e.dni, "score": round(sc * 100), "empresa": e.empresa,
             "empresa_nombre": nombre_empresa_o_vacio(e.empresa)}  # F-039
            for sc, e in scored[:15]
        ]
        return JSONResponse({"ok": True, "items": items})

    @app.post("/api/empleado/reasignar")
    async def empleado_reasignar(request: Request) -> JSONResponse:
        try:
            data = await request.json()
        except Exception:  # noqa: BLE001
            data = None
        if not isinstance(data, dict):
            return JSONResponse(
                {"ok": False, "error": "Body no es JSON válido."},
                status_code=400,
            )
        emp, error = _trabajador_pedido(data)
        if error is not None:
            return error
        if emp is None:
            return JSONResponse(
                {"ok": False, "error": f"Falta o es inválido 'ide' "
                 f"({data.get('ide')!r})."},
                status_code=400,
            )
        # F-035 (R21): los mismos datos para las cuatro formas de reasignar.
        quien = dict(emp)
        registro_id = _as_int(data.get("registro_id"))
        registro_ids_in = data.get("registro_ids")
        worker_key = data.get("worker_key")
        nombre_leido_in = data.get("nombre_leido")
        updated = 0
        congeladas = 0
        leidos: list[str] = []
        try:
            if isinstance(registro_ids_in, list) and registro_ids_in:
                ids = [_as_int(x) for x in registro_ids_in]
                ids = [x for x in ids if x is not None]
                updated, congeladas = (
                    repository.reassign_empleado_by_registro_ids(
                        registro_ids=ids, **quien,
                    )
                )
                # Acotado a lineas concretas: no se crea alias de mapeo.
                leidos = []
            elif registro_id is not None:
                leido = repository.get_registro_leido(registro_id)
                if not leido:
                    return JSONResponse(
                        {"ok": False, "error": "Registro sin nombre leido"},
                        status_code=400,
                    )
                updated, congeladas = repository.reassign_empleado_by_leido(
                    nombre_leido=leido, **quien,
                )
                leidos = [leido]
            elif worker_key:
                updated, leidos, congeladas = (
                    repository.reassign_empleado_by_worker_key(
                        worker_key=worker_key, **quien,
                    )
                )
            elif nombre_leido_in:
                updated, congeladas = repository.reassign_empleado_by_leido(
                    nombre_leido=nombre_leido_in, **quien,
                )
                leidos = [nombre_leido_in]
            else:
                return JSONResponse(
                    {"ok": False,
                     "error": "Falta registro_id / worker_key / nombre_leido"},
                    status_code=400,
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[reasignar] fallo guardando reasignacion")
            return JSONResponse(
                {"ok": False, "error": f"Error guardando reasignacion: "
                 f"{type(exc).__name__}: {exc}"},
                status_code=500,
            )

        # Alias (auto-casado futuro): best-effort, no debe tumbar la reasignacion.
        # F-040 (R17): de la ficha o del recurso elegido, con o sin ficha.
        alias_ok = True
        con_alias = emp["ide"] is not None or emp["reside"] is not None
        for leido in (leidos if con_alias else []):
            try:
                repository.upsert_empleado_alias(
                    nombre_leido=leido, ide=emp["ide"], codigo=emp["codigo"],
                    nombre=emp["nombre"], dni=emp["dni"],
                    created_by="reasignacion", recurso_ide=emp["reside"],
                )
            except Exception as exc:  # noqa: BLE001
                alias_ok = False
                logger.warning("[reasignar] alias no guardado: %r", exc)
        return JSONResponse({
            "ok": True, "updated": updated, "alias_ok": alias_ok,
            "congeladas": congeladas,   # F-004 R8
            "empleado": {"ide": emp["ide"], "codigo": emp["codigo"],
                         "nombre": emp["nombre"]},
        })

    # ----------------------------- DESHACER --------------------------- #
    @app.get("/api/undo/list", include_in_schema=False)
    def undo_list() -> JSONResponse:
        try:
            items = repository.list_undo(limit=15)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[undo] list fallo: %r", exc)
            return JSONResponse({"ok": False, "items": [], "count": 0})
        return JSONResponse({"ok": True, "items": items, "count": len(items)})

    @app.post("/api/undo", include_in_schema=False)
    def undo_apply() -> JSONResponse:
        try:
            res = repository.undo_last()
        except Exception as exc:  # noqa: BLE001
            logger.exception("[undo] fallo al deshacer")
            return JSONResponse(
                {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
                status_code=500,
            )
        return JSONResponse(res, status_code=200 if res.get("ok") else 400)

    @app.get("/partes", response_class=HTMLResponse)
    def partes_list(
        request: Request,
        search: str | None = Query(default=None),
        pendientes: str = Query(default="0"),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        only_pending = pendientes in {"1", "true", "on"}
        partes = repository.list_partes(
            search=search, only_pending=only_pending
        )
        context = {
            "request": request,
            "title": settings.app_title,
            "partes": partes,
            "search": search or "",
            "only_pending": only_pending,
            "total_pendientes": sum(1 for p in partes if not p.approved),
            "total_sin_firmar": sum(1 for p in partes if not p.firmado),
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="partes_list.html", context=context
        )

    @app.get("/partes/{document_id}", response_class=HTMLResponse)
    def parte_detail(
        request: Request,
        document_id: str,
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        detail = repository.get_parte(document_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Parte no encontrado")
        context = {
            "request": request,
            "title": settings.app_title,
            "parte": detail,
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "preview_enabled": settings.preview_enabled and bool(detail.sharepoint_url),
            "preview_url": f"/partes/{document_id}/preview",
            "back": f"/partes/{document_id}",
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="parte_detail.html", context=context
        )

    # ---------------- Lookup Sigrid (auxhor) ------------------------- #
    @app.get("/api/sigrid/tipos-hora", include_in_schema=False)
    def sigrid_tipos_hora() -> JSONResponse:
        if not catalog.enabled:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4.",
                 "items": []}
            )
        try:
            items = catalog.list()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] tipos_hora fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}",
                 "items": []}
            )
        return JSONResponse(
            {
                "ok": True,
                "items": [
                    {
                        "ide": t.ide,
                        "codigo": t.codigo,
                        "descripcion": t.descripcion,
                        "ext": t.ext,
                    }
                    for t in items
                ],
            }
        )

    # ---------------- Calendario laboral (para el JS) ---------------- #
    #: Tope del rango de `/api/calendario`. Dos meses cubren de sobra el
    #: periodo de nomina mas largo; sin tope, un cliente pidiendo diez
    #: anos pondria al proveedor a resolver una consulta por ano.
    MAX_DIAS_CALENDARIO = 62

    @app.get("/api/calendario", include_in_schema=False)
    def api_calendario(
        desde: str = Query(...),
        hasta: str = Query(...),
        dni: str | None = Query(default=None),
    ) -> JSONResponse:
        """Dias del rango con festivo / finde / laborable (R16).

        Lo consume «+ Nuevo» para marcar en su rejilla los dias que son
        festivo o domingo antes de crear las lineas. Con `dni` se resuelve
        con el calendario de ese trabajador; sin el, con el calendario por
        defecto. `fiable` en la raiz avisa de que alguna resolucion salio
        del respaldo y el calendario puede no estar al dia.
        """
        try:
            d1 = date.fromisoformat(str(desde)[:10])
            d2 = date.fromisoformat(str(hasta)[:10])
        except (TypeError, ValueError):
            return JSONResponse(
                {"ok": False, "error": "desde/hasta deben ser YYYY-MM-DD"},
                status_code=422)
        if d2 < d1:
            return JSONResponse(
                {"ok": False, "error": "hasta no puede ser anterior a desde"},
                status_code=422)
        dias_pedidos = (d2 - d1).days + 1
        if dias_pedidos > MAX_DIAS_CALENDARIO:
            return JSONResponse(
                {"ok": False,
                 "error": f"rango maximo: {MAX_DIAS_CALENDARIO} dias "
                          f"(pedidos {dias_pedidos})"},
                status_code=422)

        datos: list[dict[str, Any]] = []
        anos: set[int] = set()
        d = d1
        while d <= d2:
            dia = calendario_provider.dia(d, dni)
            datos.append({
                "fecha": dia.fecha,
                "laborable": dia.laborable,
                "fin_de_semana": dia.fin_de_semana,
                "festivo": dia.festivo,
                "festivo_nombre": dia.festivo_nombre,
            })
            anos.add(d.year)
            d += timedelta(days=1)
        fiable = calendario_provider.fiable_para((dni, ano) for ano in anos)
        return JSONResponse({"ok": True, "fiable": fiable, "data": datos})

    # ---------------- Lookup Sigrid (obras) -------------------------- #
    @app.get("/api/sigrid/obras", include_in_schema=False)
    def sigrid_obras() -> JSONResponse:
        if not obra_catalog.enabled:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4.",
                 "items": []}
            )
        try:
            items = obra_catalog.list()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] obras fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}",
                 "items": []}
            )
        return JSONResponse(
            {
                "ok": True,
                "items": [
                    {"ide": o.ide, "codigo": o.codigo, "nombre": o.nombre,
                     "empresa": o.empresa,     # F-023 (R40)
                     "empresa_nombre": nombre_empresa_o_vacio(o.empresa)}
                    for o in items
                ],
            }
        )

    def _jornada_sugerida(cd: float | None) -> float:
        # CanDefecto no valido (vacio o <= minimo) -> jornada por defecto
        # (mismo umbral que sv3 al reclasificar extras). La comparten
        # `/api/sigrid/empleados` y `/api/sigrid/recursos` (F-035).
        return jornada_efectiva(
            cd,
            minimo=settings.candef_minimo_valido,
            por_defecto=settings.jornada_por_defecto,
        )

    @app.get("/api/sigrid/empleados", include_in_schema=False)
    def sigrid_empleados(
        fecha: str | None = Query(default=None),
    ) -> JSONResponse:
        """Empleados de Sigrid para «+ Nuevo».

        `jornada_sugerida` es el candef efectivo y NO cambia: hay JS que ya
        la consume. Con `fecha` (ISO) se anade ademas `jornada_dia`, que es
        la jornada de ESE dia para ese trabajador (F-015, R26): el viernes
        de un recurso de regimen 42 son 6 h, no 9.
        """
        dia: date | None = None
        if fecha:
            try:
                dia = date.fromisoformat(str(fecha)[:10])
            except (TypeError, ValueError):
                return JSONResponse(
                    {"ok": False, "error": "fecha debe ser YYYY-MM-DD",
                     "items": []},
                    status_code=422)
        if not empleado_catalog.enabled:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4.",
                 "items": []}
            )
        try:
            items = empleado_catalog.list()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] empleados fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}",
                 "items": []}
            )
        _sugerida = _jornada_sugerida

        def _del_dia(empleado) -> float:
            def _es_laborable(d: date) -> bool:
                return calendario_provider.dia(d, empleado.dni).laborable

            return jornada_dia(
                dia, candef=empleado.candef,          # type: ignore[arg-type]
                minimo=settings.candef_minimo_valido,
                por_defecto=settings.jornada_por_defecto,
                mapa=mapa_semanal, es_laborable=_es_laborable,
                excepcion=jornada_provider.excepcion_para(empleado.dni, dia),
            )

        salida: list[dict[str, Any]] = []
        for e in items:
            fila: dict[str, Any] = {
                "ide": e.ide, "codigo": e.codigo, "nombre": e.nombre,
                "dni": e.dni, "reside": e.reside, "categoria": e.categoria,
                "candef": e.candef,
                "jornada_sugerida": _sugerida(e.candef),
                "empresa": e.empresa,          # F-023 (R40)
                "empresa_nombre": nombre_empresa_o_vacio(e.empresa),  # F-039
            }
            if dia is not None:
                fila["jornada_dia"] = _del_dia(e)
            salida.append(fila)
        return JSONResponse({"ok": True, "items": salida})

    @app.get("/api/sigrid/recursos", include_in_schema=False)
    def sigrid_recursos(
        empresa: int | None = Query(default=None),
    ) -> JSONResponse:
        """F-035 (R5): recursos ACTIVOS de clase persona para los selectores
        de trabajador, de `empresa` (o todos). `guardar` son los
        `empleado_*` que el portal escribe al elegirlo (R12/R13)."""
        if not recurso_catalog.enabled:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4.",
                 "items": []}
            )
        try:
            items = recurso_catalog.list(empresa)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] recursos fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}",
                 "items": []}
            )
        if not recurso_catalog.cargado:
            # El catalogo traga el fallo (R6) pero nunca cargo: una lista
            # vacia aqui pareceria buena. Revision 1 de F-035.
            return JSONResponse(
                {"ok": False, "items": [],
                 "error": "Sigrid no respondio al cargar los recursos."}
            )
        salida = [
            {"ide": r.ide, "codigo": r.codigo, "nombre": r.nombre,
             "dni": r.dni, "empresa": r.empresa,
             "empresa_nombre": nombre_empresa_o_vacio(r.empresa),  # F-039
             "categoria": r.categoria, "candef": r.candef,
             "jornada_sugerida": _jornada_sugerida(r.candef),
             "guardar": asignacion_de(r).como_guardar()}
            for r in items
        ]
        return JSONResponse({"ok": True, "items": salida})

    @app.get("/api/sigrid/partidas", include_in_schema=False)
    def sigrid_partidas(obra_ide: int = Query(...)) -> JSONResponse:
        """Partidas HOJA (sin hijos) del presupuesto de la obra, para imputar.
        Devuelve CD/CI/CP/OTRO sin restriccion (solo se exige que sean hoja)."""
        if sigrid_client is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4.",
                 "items": []}
            )
        from application.services.partida_catalog import (
            build_arbol_partidas,
            partidas_hoja,
        )
        try:
            filas = sigrid_client.fetch_partidas_obra(obra_ide)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] partidas fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}",
                 "items": []}
            )
        nodos = build_arbol_partidas(filas)
        items = [
            {"ide": n.ide, "cod": n.cod, "res": n.res, "capitulo": n.categoria}
            for n in partidas_hoja(nodos)
        ]
        return JSONResponse({"ok": True, "items": items})

    # ---------------- Visor del PDF del parte ------------------------ #
    @app.get("/partes/{document_id}/preview", response_class=Response)
    def parte_preview(document_id: str) -> Response:
        ref = repository.get_sharepoint_ref(document_id)
        if ref is None:
            raise HTTPException(status_code=404, detail="Parte no encontrado")

        external = ref.get("url")
        if not settings.preview_enabled:
            return HTMLResponse(_preview_error_html(
                title="Visor no configurado",
                message="Falta GRAPH_KEY en el .env del portal (sv4).",
                external_url=external,
            ))
        item_id = (ref.get("item_id") or "").strip()
        drive_id = (ref.get("drive_id") or "").strip() or (
            settings.sharepoint_drive_id or ""
        ).strip()
        if not item_id or not drive_id:
            return HTMLResponse(_preview_error_html(
                title="Parte sin archivo en SharePoint",
                message=(
                    "Este parte no tiene referencia de SharePoint guardada "
                    "(se proceso sin archivar o antes de activar SharePoint). "
                    "Reprocesa el parte para poder visualizarlo."
                ),
                external_url=external,
            ))

        token_provider: GraphTokenProvider | None = app.state.graph_token_provider
        if token_provider is None:
            return HTMLResponse(_preview_error_html(
                title="Graph no disponible",
                message="No se pudo inicializar el acceso a Microsoft Graph.",
                external_url=external,
            ))

        content_url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
            f"/items/{item_id}/content"
        )
        try:
            headers = {"Authorization": f"Bearer {token_provider.get_token()}"}
            timeout = httpx.Timeout(
                settings.graph_timeout_s, connect=min(20, settings.graph_timeout_s)
            )
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(content_url, headers=headers)
            if resp.status_code >= 300:
                logger.warning(
                    "[preview] Graph content %s para item=%s: %s",
                    resp.status_code, item_id, resp.text[:300],
                )
                return HTMLResponse(_preview_error_html(
                    title="No se pudo descargar el archivo",
                    message=f"Graph devolvio {resp.status_code} al descargar el PDF.",
                    external_url=external,
                ))
            media = _guess_pdf_media_type(ref.get("filename"))
            fname = ref.get("filename") or "parte.pdf"
            return Response(
                content=resp.content,
                media_type=media,
                headers={
                    "Content-Disposition": f'inline; filename="{fname}"',
                    "Cache-Control": "no-store",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[preview] error document_id=%s", document_id)
            return HTMLResponse(_preview_error_html(
                title="Error obteniendo la vista previa",
                message=str(exc),
                external_url=external,
            ))

    # ---------------- Edicion de cabecera del parte ------------------ #
    @app.patch("/api/partes/{document_id}/fecha")
    def patch_parte_fecha(
        document_id: str,
        payload: FechaPayload = Body(...),
    ) -> dict[str, Any]:
        parsed = _parse_fecha_to_iso_int(payload.fecha)
        if parsed is None:
            raise HTTPException(status_code=400, detail="Fecha invalida.")
        fecha_iso, fecha_int = parsed
        ok = repository.update_parte_fecha(
            document_id=document_id, fecha_iso=fecha_iso, fecha_int=fecha_int
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Parte no encontrado")
        return {"ok": True, "fecha": fecha_iso, "fecha_int": fecha_int}

    def _norm_grupos(cod: str | None) -> str:
        """Normaliza un codigo de partida por grupos numericos: '3.9' y
        '03.09' son la misma partida. Los grupos no numericos se comparan
        en mayusculas tal cual (CI.1.10 == ci.1.10)."""
        partes = [p.strip() for p in (cod or "").strip().upper().split(".")]
        out = []
        for p in partes:
            out.append(str(int(p)) if p.isdigit() else p)
        return ".".join(x for x in out if x)

    def _casar_partida_por_codigo(objetivo: str | None,
                                  hojas: list[dict]) -> dict | None:
        """Match del codigo contra las partidas-hoja de la obra nueva:
        (1) igualdad normalizada; (2) prefijo normalizado UNICO. Ambiguo o
        inexistente -> None (queda en blanco con aviso en el front)."""
        objetivo_n = _norm_grupos(objetivo)
        if not objetivo_n:
            return None
        exactas = [h for h in hojas if _norm_grupos(h.get("cod")) == objetivo_n]
        if len(exactas) == 1:
            return exactas[0]
        if len(exactas) > 1:
            return None
        prefijo = [h for h in hojas
                   if _norm_grupos(h.get("cod")).startswith(objetivo_n + ".")]
        if len(prefijo) == 1:
            return prefijo[0]
        return None

    @app.patch("/api/partes/{document_id}/obra")
    def patch_parte_obra(
        document_id: str,
        payload: ObraPayload = Body(...),
    ) -> dict[str, Any]:
        if not payload.codigo:
            raise HTTPException(status_code=400, detail="Falta el codigo de obra.")
        # Resuelve ide/nombre desde el catalogo (fuente de verdad); si no esta
        # cableado o no se encuentra, usa lo que envie el front. F-023: por
        # el IDE que eligio el usuario: un codigo puede ser de dos obras
        # (gemelas de dos empresas) y por codigo solo se resuelve si es unico.
        ide = payload.ide
        nombre = payload.nombre
        if obra_catalog.enabled:
            opt = obra_catalog.get_by_ide(
                payload.ide) or obra_catalog.get_by_codigo(
                    payload.codigo)
            if opt is not None:
                ide = opt.ide
                nombre = opt.nombre
        objetivos = repository.update_parte_obra(
            document_id=document_id,
            obra_ide=ide,
            obra_codigo=payload.codigo,
            obra_nombre=nombre,
        )
        if objetivos is None:
            raise HTTPException(status_code=404, detail="Parte no encontrado")

        # Re-casar las partidas contra el presupuesto de la obra NUEVA:
        # los paride del presupuesto viejo no valen aunque el codigo sea
        # el mismo texto. Match por codigo normalizado + prefijo unico.
        recasadas, sin_match = 0, 0
        if objetivos and ide and settings.sigrid_lookup_enabled and sigrid_client:
            try:
                from application.services.partida_catalog import (
                    build_arbol_partidas, partidas_hoja,
                )
                filas = sigrid_client.fetch_partidas_obra(int(ide))
                hojas = [
                    {"ide": n.ide, "cod": n.cod, "res": n.res,
                     "capitulo": n.categoria}
                    for n in partidas_hoja(build_arbol_partidas(filas))
                ]
                for obj in objetivos:
                    match = _casar_partida_por_codigo(
                        obj.get("objetivo_cod"), hojas
                    )
                    if match:
                        repository.aplicar_partida_recasada(
                            registro_id=obj["registro_id"], partida=match,
                            metodo=obj.get("metodo_previo") or "parte",
                            score=obj.get("score_previo"),
                        )
                        recasadas += 1
                    else:
                        sin_match += 1
                logger.info(
                    "[obra-cambiada] parte=%s partidas re-casadas=%s "
                    "sin_match=%s (obra %s)",
                    document_id, recasadas, sin_match, payload.codigo,
                )
            except Exception:  # noqa: BLE001
                sin_match = len(objetivos)
                logger.warning(
                    "[obra-cambiada] fallo re-casando partidas; quedan en "
                    "blanco para imputar a mano", exc_info=True,
                )
        elif objetivos:
            sin_match = len(objetivos)

        return {
            "ok": True,
            "obra_ide": ide,
            "obra_codigo": payload.codigo,
            "obra_nombre": nombre,
            "partidas_recasadas": recasadas,
            "partidas_sin_match": sin_match,
        }

    # ---------------- Edicion de registros --------------------------- #
    @app.post("/api/registros/{registro_id}/extra", include_in_schema=False)
    async def registro_crear_extra(registro_id: int, request: Request) -> JSONResponse:
        """Crea la linea EXTRA de un (trabajador, dia) desde la matriz,
        clonando el contexto del registro ORDINARIO ``registro_id``. El
        codigo de hora extra se resuelve best-effort contra reshor."""
        body = await request.json()
        try:
            horas = float(body.get("horas"))
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "error": "horas invalidas"},
                                status_code=422)
        reside = repository.get_registro_recurso(registro_id)
        hora_info = None
        if reside and settings.sigrid_lookup_enabled and sigrid_client:
            try:
                hora_info = sigrid_client.fetch_hora_extra_recurso(reside)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "[crear-extra] fallo resolviendo hora extra del "
                    "recurso=%s; la linea queda sin codigo",
                    reside, exc_info=True,
                )
        nuevo_id = repository.crear_extra_desde(
            registro_id=registro_id, horas=horas, hora=hora_info,
        )
        if nuevo_id is None:
            return JSONResponse({"ok": False, "error": "registro no valido"},
                                status_code=404)
        return JSONResponse({"ok": True, "id": nuevo_id})

    # ------------------------------------------------------------------ #
    # APROBAR -> registrar en Sigrid (delegado en partes-transfer, sv5)
    # ------------------------------------------------------------------ #

    def _preparar_registro(body: dict) -> Preparado | JSONResponse:
        """Las lineas a registrar, repartidas por obra (F-022 §D).

        F-024 (R22, R23): las lineas `registrado` no viajan nunca y las
        `borrado_sigrid` solo con `incluir_borradas`; `excluidas` NO va en
        el payload de sv5, va en la respuesta al navegador.

        F-022: con `ambito`, los ids tienen que ser de la vista (R10-R12);
        sin el, como hasta ahora (ids sueltos u `obra_key`). Mas de
        `APROBACION_MAX_OBRAS` obras se rechaza con el desglose (R15).
        """
        try:
            ids = list(dict.fromkeys(
                int(i) for i in (body.get("registro_ids") or []) if i))
        except (TypeError, ValueError):
            return JSONResponse(
                {"ok": False, "error": "registro_ids no validos"},
                status_code=422)
        if body.get("ambito") is not None:
            rechazo = _validar_ambito(body["ambito"], ids)
            if rechazo is not None:
                return rechazo
        elif not ids:
            obra_key = (body.get("obra_key") or "").strip()
            if not obra_key:
                return JSONResponse(
                    {"ok": False, "error": "faltan registro_ids u obra_key"},
                    status_code=422)
            ids = repository.registro_ids_de_obra(
                obra_key, period_key=body.get("period"),
                mode=(body.get("mode") or "nomina"))
        # F-025 (R9, R12): con la tabla de clases, los dias con una
        # incidencia de dia completo y horas se quedan fuera, sin override.
        datos = repository.lineas_para_registro(
            ids, incluir_borradas=bool(body.get("incluir_borradas")),
            incidencias=tabla_incidencias)
        excluidas = datos["excluidas"]
        if not datos["lineas"]:
            return JSONResponse(
                {"ok": False, "error": _motivo_sin_lineas(excluidas),
                 "excluidas": excluidas},
                status_code=422)
        grupos = [GrupoObra(**g) for g in datos["grupos"]]
        maximo = settings.aprobacion_max_obras
        if len(grupos) > maximo:
            return JSONResponse(
                {"ok": False,
                 "error": f"la aprobacion abarca {len(grupos)} obras y el "
                          f"maximo es {maximo}: filtra la tabla o "
                          "selecciona menos obras",
                 "obras": [{"clave": g.clave,
                            "codigo": g.obra.get("codigo"),
                            "nombre": g.obra.get("nombre"),
                            "lineas": len(g.lineas)} for g in grupos],
                 "excluidas": excluidas},
                status_code=422)
        claves = repartir_claves(
            [str(k) for k in (body.get("pisar_claves") or [])],
            [g.clave for g in grupos])
        if claves is None:
            return JSONResponse(
                {"ok": False,
                 "error": "con varias obras, cada clave que pisar tiene que "
                          f"llevar su obra (<obra>{SEPARADOR_CLAVE}<clave>)"},
                status_code=422)
        return Preparado(grupos=grupos, claves=claves, datos=datos)

    def _payload_grupo(grupo: GrupoObra, claves: list[str],
                       actor: str | None) -> dict:
        """El payload de sv5 de una obra: la forma de siempre (R33).

        `actor` viene por parametro y no se resuelve aqui: la identidad se
        lee en UN solo sitio (F-017 R10).
        """
        return {"obra": grupo.obra, "lineas": grupo.lineas,
                "pisar_claves": claves, "usuario": actor}

    def _rechazo_ambito(error: str, **extra) -> JSONResponse:
        return JSONResponse(dict({"ok": False, "error": error}, **extra),
                            status_code=422)

    def _validar_ambito(ambito, ids: list[int]) -> JSONResponse | None:
        """F-022 (R10-R12, DA7): los ids pedidos tienen que ser de la vista
        de la que salen. Uno ajeno (otra obra, otro periodo, otra persona,
        la papelera o inexistente) rechaza la peticion ENTERA, sin llamar a
        sv5 ni marcar nada: es la senal de una pagina desfasada."""
        if not isinstance(ambito, dict):
            return _rechazo_ambito("ambito no valido")
        vista = ambito.get("vista")
        if vista not in ("obra", "trabajador"):
            return _rechazo_ambito(
                f"ambito no valido: vista desconocida ({vista!r})")
        campo = "obra_key" if vista == "obra" else "worker_key"
        clave = str(ambito.get(campo) or "").strip()
        if not clave:
            return _rechazo_ambito(f"ambito no valido: falta {campo}")
        if not ids:
            return _rechazo_ambito("no hay lineas seleccionadas que aprobar")
        if len(ids) > MAX_IDS_APROBACION:
            return _rechazo_ambito(
                f"demasiadas lineas en una aprobacion ({len(ids)}); el "
                f"maximo es {MAX_IDS_APROBACION}")
        if vista == "obra":
            permitidos = repository.registro_ids_de_obra(
                clave, period_key=ambito.get("period") or None,
                mode=ambito.get("mode") or "nomina")
        else:
            permitidos = repository.registro_ids_de_trabajador(clave)
        fuera = len(set(ids) - set(permitidos))
        if fuera:
            logger.warning("[aprobar] %s id(s) fuera del ambito %s=%s",
                           fuera, campo, clave)
            return _rechazo_ambito(
                f"{fuera} linea(s) no son de esta vista (otra obra, otro "
                "periodo, otra persona o en la papelera): recarga la pagina "
                "y vuelve a seleccionar", fuera_de_ambito=fuera)
        return None

    def _motivo_sin_lineas(excluidas: dict) -> str:
        """R23: por que no queda nada que registrar."""
        partes = []
        if excluidas.get("registrado"):
            partes.append(f"{excluidas['registrado']} ya registrada(s) en "
                          "Sigrid (no se reenvian)")
        if excluidas.get("borrado_sigrid"):
            partes.append(f"{excluidas['borrado_sigrid']} borrada(s) en "
                          "Sigrid (para reenviarlas, marca «Incluir las "
                          "borradas en Sigrid» o usa «Reaprobar»)")
        if excluidas.get("dedicacion"):
            # F-019 (R17).
            partes.append(f"{excluidas['dedicacion']} enviada(s) a "
                          "dedicación (para reenviarlas, «Retirar de "
                          "dedicación»)")
        if excluidas.get("incompatible"):
            # F-025 (R10).
            partes.append(f"{excluidas['incompatible']} con una incidencia "
                          "de día completo y horas el mismo día (corrige el "
                          "día en el portal)")
        if not partes:
            return "no hay lineas activas que registrar"
        return "no hay lineas que registrar: " + " y ".join(partes)

    def _fecha_de_linea(linea: dict) -> date | None:
        """La fecha de una linea del payload, que viaja como YYYYMMDD."""
        fi = _as_int(linea.get("fecha_int"))
        if not fi:
            return None
        try:
            return date(fi // 10000, (fi // 100) % 100, fi % 100)
        except ValueError:
            return None

    def _avisos_calendario(lineas: list[dict]) -> list[dict]:
        """R18: lineas con horas (> 0) en dia festivo o domingo.

        Informativo: no altera QUE se registra. Sirve para que quien
        aprueba un mes entero vea, antes de darle al boton, que hay horas
        en dias no laborables — correcto a veces, error de fecha otras.
        """
        avisos: list[dict] = []
        nombres: dict[str, Callable[[date], str | None]] = {}
        for linea in lineas:
            if abs(float(linea.get("horas") or 0.0)) <= 1e-9:
                continue
            d = _fecha_de_linea(linea)
            if d is None:
                continue
            dni = linea.get("dni")
            resolutor = nombres.get(str(dni))
            if resolutor is None:
                resolutor = calendario_provider.holiday_name_para(dni)
                nombres[str(dni)] = resolutor
            nombre = resolutor(d)
            if nombre:
                tipo, motivo = "festivo", f"dia festivo ({nombre})"
            elif d.weekday() == 6:
                tipo, motivo = "domingo", "domingo"
            else:
                continue
            avisos.append({
                "registro_id": linea.get("registro_id"),
                "fecha": d.isoformat(),
                "nombre": linea.get("nombre"),
                "horas": linea.get("horas"),
                "tipo": tipo,
                "motivo": f"horas registradas en {motivo}",
            })
        return avisos

    def _calendario_fiable(lineas: list[dict]) -> bool:
        """True si el calendario de TODAS las lineas del lote es de fiar.

        Con Sesame configurado pero caido, el computo de horas pierde los
        festivos reales y las jornadas reducidas: lo que se registraria
        puede estar mal. `fiable_para` devuelve True siempre que Sesame
        no este configurado, asi que con la feature apagada esto no
        bloquea nada (R27).
        """
        consultas: set[tuple[str | None, int]] = set()
        for linea in lineas:
            d = _fecha_de_linea(linea)
            if d is not None:
                consultas.add((linea.get("dni"), d.year))
        return calendario_provider.fiable_para(consultas)

    @app.post("/api/aprobar/preflight", include_in_schema=False)
    async def aprobar_preflight(request: Request) -> JSONResponse:
        if transfer_client is None:
            return JSONResponse(
                {"ok": False, "error": "registro en Sigrid no configurado "
                                       "(TRANSFER_BASE_URL)"},
                status_code=503)
        actor = _actor(request)
        preparado = _preparar_registro(await request.json())
        if isinstance(preparado, JSONResponse):
            return preparado
        evaluados = [
            _evaluar_grupo(g, preparado.claves[g.clave], actor)
            for g in preparado.grupos]
        datos = preparado.datos
        return JSONResponse(dict(
            agregar_preflight(evaluados), grupos=evaluados,
            excluidas=datos["excluidas"],
            excluidas_detalle=datos["excluidas_detalle"],
            umbral_plegado=UMBRAL_PLEGADO))

    def _evaluar_grupo(grupo: GrupoObra, claves: list[str],
                       actor: str | None) -> dict:
        """F-022 (R17, R18, R23-R25): el preflight de UNA obra.

        Un fallo de sv5 en esta obra no tumba las demas: el grupo sale con
        `ok` falso y su motivo. Avisos de calendario y bloqueo de Sesame
        son los de SUS lineas (R31).
        """
        try:
            pf = dict(transfer_client.preflight(
                _payload_grupo(grupo, claves, actor)))
        except Exception as exc:
            logger.warning("[transfer] preflight de la obra %s fallo",
                           grupo.clave, exc_info=True)
            pf = {"ok": False, "error": f"no se pudo evaluar la obra: {exc}"}
        evaluado = dict(pf, clave=grupo.clave, obra=grupo.obra,
                        registro_ids=grupo.registro_ids,
                        avisos_calendario=_avisos_calendario(grupo.lineas),
                        avisos_incidencia=grupo.avisos_incidencia)  # F-025
        # F-003 R23: el preflight se sirve igual (el humano tiene que poder
        # ver que se iba a registrar), pero con el motivo del bloqueo dentro.
        if not _calendario_fiable(grupo.lineas):
            evaluado["sesame_bloqueo"] = MOTIVO_BLOQUEO_SESAME
        evaluado["listado"] = listado_grupo(grupo, pf)
        evaluado["totales"] = totales(evaluado["listado"])
        return evaluado

    def _trazar(resultado: dict, ids: list[int], *, actor: str | None,
                sin_sesame: bool = False) -> None:
        """Traza el veredicto en `parte_registros`, sin tumbar la respuesta.

        Que falle la traza no invalida lo que sv5 ya escribio en Sigrid;
        y si el registro fue por cola, el mensaje de `q-transfer-result`
        vuelve a intentarlo.
        """
        try:
            aplicar_resultado(repository, resultado, registro_ids=ids,
                              usuario=actor,
                              sin_sesame=sin_sesame,
                              incidencias=tabla_incidencias)  # F-019
        except Exception:
            logger.warning("[transfer] no se pudo guardar la traza del "
                           "registro", exc_info=True)

    @app.post("/api/aprobar/ejecutar", include_in_schema=False)
    async def aprobar_ejecutar(request: Request) -> JSONResponse:
        if transfer_client is None:
            return JSONResponse(
                {"ok": False, "error": "registro en Sigrid no configurado "
                                       "(TRANSFER_BASE_URL)"},
                status_code=503)
        body = await request.json()
        actor = _actor(request)
        preparado = _preparar_registro(body)
        if isinstance(preparado, JSONResponse):
            return preparado
        # F-003 R24: la guarda la impone el SERVIDOR, no el modal. Una
        # peticion a pelo, sin pasar por el preflight, se para igual.
        # F-022 (R18, R22): por obra y una tras otra; una obra bloqueada o
        # que falla no para a las demas (DA16).
        forzar = bool(body.get("forzar_sin_sesame"))
        ejecutados = []
        for grupo in preparado.grupos:
            degradado = not _calendario_fiable(grupo.lineas)
            if degradado and not forzar:
                ejecutados.append(_bloqueado_sesame(grupo))
                continue
            resultado = _ejecutar_grupo(grupo, preparado.claves[grupo.clave],
                                        actor)
            if degradado:
                # F-003 R17: saltarse la guarda de Sesame es una decision
                # humana consciente, y queda con NOMBRE en el log. El actor
                # nunca es vacio (F-017 R7).
                logger.warning(
                    "[sesame] registro FORZADO por %s con el calendario de "
                    "Sesame no disponible (obra %s); las lineas quedan "
                    "marcadas.", actor, grupo.clave)
            _trazar(resultado, grupo.registro_ids, actor=actor,
                    sin_sesame=degradado)
            ejecutados.append(dict(resultado, clave=grupo.clave,
                                   obra=grupo.obra,
                                   registro_ids=grupo.registro_ids))
        if all(e.get("bloqueado_sesame") for e in ejecutados):
            return JSONResponse(
                {"ok": False, "error": MOTIVO_BLOQUEO_SESAME,
                 "sesame_bloqueo": MOTIVO_BLOQUEO_SESAME},
                status_code=422)
        return JSONResponse(dict(agregar_ejecucion(ejecutados),
                                 grupos=ejecutados,
                                 excluidas=preparado.datos["excluidas"]))

    def _bloqueado_sesame(grupo: GrupoObra) -> dict:
        """F-022 (R18): una obra con el calendario no fiable y sin override
        no se envia; sus lineas no cambian."""
        logger.warning(
            "[sesame] registro BLOQUEADO: obra %s, %s lineas con calendario "
            "no fiable y sin override.", grupo.clave, len(grupo.lineas))
        return {"clave": grupo.clave, "obra": grupo.obra,
                "registro_ids": grupo.registro_ids, "ok": False,
                "bloqueado_sesame": True, "error": MOTIVO_BLOQUEO_SESAME}

    def _ejecutar_grupo(grupo: GrupoObra, claves: list[str],
                        actor: str | None) -> dict:
        """El registro sincrono de UNA obra. Una excepcion se queda en su
        obra (`ok` falso, sus lineas a `error`): las demas siguen."""
        try:
            return dict(transfer_client.ejecutar(
                _payload_grupo(grupo, claves, actor)))
        except Exception as exc:
            logger.warning("[transfer] registro de la obra %s fallo",
                           grupo.clave, exc_info=True)
            return {"ok": False,
                    "error": f"no se pudo registrar la obra: {exc}"}

    @app.post("/api/aprobar/encolar", include_in_schema=False)
    async def aprobar_encolar(request: Request) -> JSONResponse:
        """R1: aprobacion ASINCRONA por `q-transfer`.

        Con colas configuradas responde en cuanto la peticion esta
        encolada, sin esperar a que Sigrid termine: un lote de obra x mes
        tardaba minutos y rozaba los cortes del balanceador.

        Sin colas (R3) degrada al registro HTTP sincrono de siempre, que
        es lo que permite trabajar en local sin Azurite y desplegar el
        codigo antes que la infraestructura.
        """
        body = await request.json()
        # R5/R10: pisar borra lineas de Sigrid. Es una decision humana del
        # modal y no puede viajar por una cola con reentregas.
        if body.get("pisar_claves"):
            return JSONResponse(
                {"ok": False, "error": "pisar conflictos no viaja por la "
                                       "cola: usa /api/aprobar/ejecutar"},
                status_code=422)
        if publisher is None and transfer_client is None:
            return JSONResponse(
                {"ok": False, "error": "registro en Sigrid no configurado "
                                       "(TRANSFER_BASE_URL)"},
                status_code=503)
        actor = _actor(request)
        preparado = _preparar_registro(body)
        if isinstance(preparado, JSONResponse):
            return preparado
        excluidas = preparado.datos["excluidas"]
        # F-022 (R20, R21): una peticion por obra. Una obra bloqueada o que
        # no se pudo publicar no para a las demas.
        grupos = []
        for grupo in preparado.grupos:
            # F-003 R24/R25: igual que `pisar_claves`, el override de
            # Sesame es una decision humana consciente y NO viaja por una
            # cola con reentregas; sin override, la obra degradada se para.
            if not _calendario_fiable(grupo.lineas):
                grupos.append(dict(_bloqueado_sesame(grupo),
                                   estado="bloqueado_sesame",
                                   peticion_id=None))
            elif publisher is None:
                resultado = _ejecutar_grupo(grupo, [], actor)     # F-002 R3
                _trazar(resultado, grupo.registro_ids, actor=actor)
                grupos.append(dict(resultado, clave=grupo.clave,
                                   obra=grupo.obra,
                                   registro_ids=grupo.registro_ids))
            else:
                grupos.append(_publicar_grupo(grupo, actor))
        if all(g.get("bloqueado_sesame") for g in grupos):
            return JSONResponse(
                {"ok": False,
                 "error": MOTIVO_BLOQUEO_SESAME + " Para registrarlo de "
                          "todas formas hay que confirmarlo a mano: usa "
                          "/api/aprobar/ejecutar.",
                 "sesame_bloqueo": MOTIVO_BLOQUEO_SESAME},
                status_code=422)
        if publisher is None:
            return JSONResponse(dict(agregar_ejecucion(grupos),
                                     modo="sincrono", excluidas=excluidas,
                                     grupos=grupos))
        encolados = [g for g in grupos if g["estado"] == "encolado"]
        if not encolados:
            return JSONResponse(
                {"ok": False,
                 "error": "no se pudo encolar ninguna obra: "
                          + "; ".join(f"{g['obra'].get('codigo') or g['clave']}"
                                      f": {g['error']}" for g in grupos),
                 "excluidas": excluidas, "grupos": grupos},
                status_code=502)
        ids = [i for g in encolados for i in g["registro_ids"]]
        # F-024 (R27): los ids encolados, para que el modal sondee su
        # estado (R29) en vez de recargar antes de que llegue el resultado.
        return JSONResponse({
            "ok": True, "modo": "asincrono",
            "peticion_id": encolados[0]["peticion_id"],
            "peticiones": [g["peticion_id"] for g in encolados],
            "encoladas": len(ids), "registro_ids": ids,
            "excluidas": excluidas, "grupos": grupos})

    def _publicar_grupo(grupo: GrupoObra, actor: str | None) -> dict:
        """F-022 (R20, R21): encola UNA obra y marca sus lineas.

        Primero se publica y luego se marca: al reves, un fallo al publicar
        dejaria lineas en 'encolado' sin nada que las recoja.
        """
        base = {"clave": grupo.clave, "obra": grupo.obra,
                "registro_ids": grupo.registro_ids}
        try:
            peticion_id = publisher.publicar(
                _payload_grupo(grupo, [], actor), usuario=actor)
        except Exception as exc:
            logger.warning("[transfer-cola] no se pudo encolar la obra %s; "
                           "sus lineas no cambian", grupo.clave,
                           exc_info=True)
            return dict(base, ok=False, estado="error_cola", peticion_id=None,
                        error=f"no se pudo encolar: {exc}")
        try:
            repository.marcar_registros_encolado(grupo.registro_ids,
                                                 usuario=actor)  # F-002 R2
        except Exception:
            logger.warning("[transfer-cola] peticion %s encolada pero no se "
                           "pudo marcar 'encolado'; el resultado las marcara",
                           peticion_id, exc_info=True)
        return dict(base, ok=True, estado="encolado", peticion_id=peticion_id,
                    error=None)

    @app.post("/api/dedicacion/retirar", include_in_schema=False)
    async def dedicacion_retirar(request: Request) -> JSONResponse:
        """F-019 (R21-R24): «Retirar de dedicacion» de las lineas elegidas.

        El ambito se valida como en la aprobacion (F-022): un id que no es
        de la vista rechaza la peticion entera sin tocar nada. Las que no
        estan en `dedicacion` se cuentan en `no_aplica`. Firma `_actor`."""
        body = await request.json()
        try:
            ids = list(dict.fromkeys(
                int(i) for i in (body.get("registro_ids") or []) if i))
        except (TypeError, ValueError):
            return _rechazo_ambito("registro_ids no validos")
        rechazo = _validar_ambito(body.get("ambito"), ids)
        if rechazo is not None:
            return rechazo
        resultado = repository.retirar_de_dedicacion(ids, _actor(request))
        return JSONResponse(dict(resultado, ok=True))

    @app.post("/api/sigrid/comprobar", include_in_schema=False)
    def sigrid_comprobar(p: ComprobarSigridPayload) -> JSONResponse:
        """F-024 (R17-R21): siguen en Sigrid estas lineas `registrado`?

        Lo llama el navegador al cargar la vista de obra o de persona (sin
        `forzar`) y el boton «Comprobar en Sigrid» (con `forzar`). El GET
        de las vistas NO llama a sv5 (R18). `def`: corre en un hilo del
        pool y no bloquea el bucle mientras sv5 lee Sigrid.
        """
        if comprobacion_sigrid is None:
            return JSONResponse(
                {"ok": False, "error": "registro en Sigrid no configurado "
                                       "(TRANSFER_BASE_URL)"},
                status_code=503)
        origen = p.origen if p.origen in ORIGENES_COMPROBACION else "boton"
        res = comprobacion_sigrid.comprobar_ids(
            p.registro_ids, origen=origen, forzar=p.forzar)
        return JSONResponse(res, status_code=200 if res["ok"] else 502)

    @app.post("/api/aprobar/estado", include_in_schema=False)
    def aprobar_estado(p: EstadoAprobacionPayload) -> JSONResponse:
        """F-024 (R28): en que `sigrid_estado` estan esas lineas. Solo
        lectura; lo sondea el modal tras encolar (R29) y la vista con
        lineas `encolado` (R30)."""
        return JSONResponse({"ok": True,
                             **repository.recuento_estados(p.registro_ids)})

    # ------------------------------------------------------------------ #
    # COLAS 'poison': visibilidad y reencolado manual desde el portal.
    # Sin esto, un mensaje que agota sus reintentos solo se ve entrando en
    # Azure, y sus lineas se quedan en 'encolado' sin que nadie sepa por que.
    # ------------------------------------------------------------------ #

    #: Allowlist CERRADA. El nombre de cola no puede venir del cliente:
    #: solo se admite elegir cual de estas dos, y el sufijo lo pone el
    #: servidor.
    COLAS_REENCOLABLES = (settings.cola_transfer, settings.cola_transfer_result)

    @app.get("/api/admin/poison", include_in_schema=False)
    async def poison_estado() -> JSONResponse:
        if cola_cliente is None:
            return JSONResponse({"habilitado": False})       # R26
        colas = []
        for principal in COLAS_REENCOLABLES:
            poison = f"{principal}-poison"
            try:
                cuantos = cola_cliente.contar_aproximado(poison)
            except Exception:
                # El aviso es accesorio: que Storage no conteste no puede
                # tumbar la pagina que lo muestra.
                logger.warning("[poison] no se pudo contar %s", poison,
                               exc_info=True)
                cuantos = None
            colas.append({"cola": poison, "principal": principal,
                          "mensajes_aprox": cuantos})
        return JSONResponse({"habilitado": True, "colas": colas})

    @app.post("/api/admin/poison/reencolar", include_in_schema=False)
    async def poison_reencolar(request: Request) -> JSONResponse:
        """R24: devuelve a la cola principal hasta 32 mensajes muertos.

        Repetirlo es seguro: sv5 detecta por synckey lo ya escrito (R8) y
        el marcado de sv4 es idempotente (R13).
        """
        if cola_cliente is None:
            return JSONResponse(
                {"ok": False, "error": "colas no configuradas"},
                status_code=409)                              # R26
        body = await request.json()
        cola = (body.get("cola") or "").strip()
        if cola not in COLAS_REENCOLABLES:
            return JSONResponse(
                {"ok": False, "error": f"cola no admitida: {cola!r}"},
                status_code=422)
        poison = f"{cola}-poison"
        movidos = cola_cliente.mover(poison, cola, maximo=32)
        try:
            restantes = cola_cliente.contar_aproximado(poison)
        except Exception:
            restantes = None
        logger.warning("[poison] reencolados %s mensaje(s) de %s a %s por "
                       "peticion del portal", len(movidos), poison, cola)
        return JSONResponse({"ok": True, "movidos": len(movidos),
                             "restantes_aprox": restantes})

    # ----------------------------------------------------------------- #
    # F-016 · administracion de `empleado_jornada`.
    #
    # Esta pantalla edita el COMPUTO DE NOMINAS: una fila mal guardada
    # cambia que horas cuenta sv3 como extra y acaba en Sigrid. De ahi
    # las tres reglas que se repiten en los cinco endpoints:
    #   1. se valida ANTES de escribir, y un rechazo deja la BBDD intacta;
    #   2. un solape se RECHAZA (409) nombrando la fila en conflicto, y
    #      nunca se ajusta la fila ajena (DA3);
    #   3. no hay DELETE: la papelera es logica (R6).
    # ----------------------------------------------------------------- #

    def _numero_texto(valor: Any) -> str:
        """Un float como lo escribiria un humano: `48`, no `48.0`."""
        return "" if valor is None else f"{float(valor):g}"

    def _fila_para_pantalla(fila: dict) -> dict:
        """La fila del repositorio, en el idioma de la pantalla (R7).

        `hasta` NO viaja a la plantilla: lo que se pinta es el ultimo dia
        incluido. La palabra «exclusivo» no aparece en la interfaz.
        """
        horas = [fila.get(dia) for dia in DIAS_JORNADA]
        vista = dict(fila)
        vista["hasta_inclusivo"] = ultimo_dia_incluido_de_fila(fila.get("hasta"))
        vista["patron"] = ([_numero_texto(h) for h in horas]
                           if all(h is not None for h in horas) else None)
        vista["semanal_texto"] = _numero_texto(fila.get("jornada_semanal"))
        return vista

    @app.get("/admin/jornadas", response_class=HTMLResponse)
    def admin_jornadas(
        request: Request,
        editar: int | None = Query(default=None),
    ) -> HTMLResponse:
        """R2 · el listado entero mas el formulario de alta o edicion.

        `?editar=<id>` devuelve el formulario RELLENO desde el servidor
        (patron PRG): cero JS de precarga. Si el id no existe, se cae al
        modo alta en vez de dar un 404: la pagina sigue siendo util.
        """
        _exigir_admin_jornadas()
        filas = [_fila_para_pantalla(f)
                 for f in repository.list_jornadas_admin()]
        edicion = next((f for f in filas if f["id"] == editar), None)
        patron = (edicion or {}).get("patron")
        context = {
            "request": request,
            "title": settings.app_title,
            "filas": filas,
            "edicion": edicion,
            "dias": [
                {"columna": columna,
                 "etiqueta": ABREVIATURA_DIA[columna],
                 "valor": patron[i] if patron else ""}
                for i, columna in enumerate(DIAS_JORNADA)
            ],
            "hoy": date.today().isoformat(),
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            # R14: los minutos salen de la configuracion, no cableados. Se
            # redondea hacia ARRIBA para no prometer menos espera de la real.
            "cache_minutos": max(
                1, -(-int(settings.jornada_cache_ttl_s) // 60)),
            "aviso": request.query_params.get("aviso"),
        }
        return templates.TemplateResponse(
            request=request, name="admin_jornadas.html", context=context)

    async def _cuerpo(request: Request) -> dict[str, Any]:
        """El JSON del formulario, o un diccionario vacio.

        Un cuerpo ilegible no es un 500: cae en las validaciones de campo
        y sale como 422 con el motivo puesto."""
        try:
            datos = await request.json()
        except Exception:                                       # noqa: BLE001
            return {}
        return datos if isinstance(datos, dict) else {}

    def _rechazo(exc: JornadaInvalida) -> JSONResponse:
        """422: lo que el humano escribio no se puede guardar (DA10)."""
        logger.info("[jornada-admin] rechazada: %s (campo=%s)",
                    exc.motivo, exc.campo)
        return JSONResponse(
            {"ok": False, "error": exc.motivo, "campo": exc.campo},
            status_code=422)

    def _conflicto(fila: dict) -> JSONResponse:
        """409: choca con el estado. El humano decide cual cierra."""
        detalle = describir_conflicto(fila)
        fin = detalle["hasta_inclusivo"] or "sin fin"
        logger.info("[jornada-admin] solape con la fila id=%s", detalle["id"])
        return JSONResponse(
            {"ok": False,
             "error": (f"Ese periodo pisa la vigencia de la fila #"
                       f"{detalle['id']} ({detalle['desde']} … {fin}). "
                       "Cierrala primero o cambia las fechas."),
             "conflicto": detalle},
            status_code=409)

    def _no_encontrada() -> JSONResponse:
        return JSONResponse(
            {"ok": False, "error": "Esa excepcion de jornada ya no existe."},
            status_code=404)

    def _invalidar_jornadas() -> None:
        """Tira la cache del proveedor DE ESTE PROCESO (R14).

        No avisa ni a sv3 ni a otras replicas de sv4: eso exigiria un
        acoplamiento entre servicios que `docs/ARCHITECTURE.md` no
        contempla, para ahorrar como mucho `JORNADA_CACHE_TTL_S` en una
        tabla que se toca dos veces al ano. Por eso la pagina lleva el
        aviso permanente en vez de prometer un efecto inmediato.
        """
        proveedor = getattr(app.state, "jornada_provider", None)
        invalidar = getattr(proveedor, "invalidar", None)
        if callable(invalidar):
            invalidar()

    def _aviso_dni_desconocido(dni_norm: str) -> str | None:
        """R19: si el DNI no consta en Sigrid se AVISA, no se bloquea.

        Con el catalogo apagado no se llama al cliente de Sigrid ni una
        vez: la pantalla no depende de que Sigrid este cableado (R17).
        """
        catalogo = getattr(app.state, "empleado_catalog", None)
        if catalogo is None or not catalogo.enabled:
            return None
        try:
            conocidos = {normalize_dni(e.dni) for e in catalogo.list()}
        except Exception:                                       # noqa: BLE001
            logger.warning("[jornada-admin] no se pudo comprobar el DNI "
                           "contra Sigrid", exc_info=True)
            return None
        if dni_norm in conocidos:
            return None
        return ("Ese DNI no consta en el catalogo de empleados de Sigrid. "
                "La excepcion se ha guardado igualmente: comprueba que es "
                "el trabajador que querias.")

    def _por_id(filas: list[dict], jornada_id: int) -> dict | None:
        return next((f for f in filas if f["id"] == jornada_id), None)

    def _a_persistir(entrada) -> dict:
        """De `EntradaJornada` a lo que entiende el repositorio."""
        return {
            "dni_norm": entrada.dni_norm,
            "jornada_semanal": entrada.jornada_semanal,
            "patron": entrada.patron,
            "desde": entrada.desde,
            "hasta": entrada.hasta,
            "nota": entrada.nota,
        }

    @app.post("/api/admin/jornadas", include_in_schema=False)
    async def jornada_crear(request: Request) -> JSONResponse:
        """R3 · alta de una excepcion de jornada."""
        _exigir_admin_jornadas()
        try:
            entrada = normalizar_entrada(await _cuerpo(request))
            validar_entrada(entrada)
        except JornadaInvalida as exc:
            return _rechazo(exc)
        choque = buscar_solape(entrada, repository.list_jornadas_admin())
        if choque is not None:
            return _conflicto(choque)
        nuevo_id = repository.crear_jornada(
            entrada=_a_persistir(entrada), actor=_actor(request))
        _invalidar_jornadas()
        cuerpo: dict[str, Any] = {"ok": True, "id": nuevo_id}
        aviso = _aviso_dni_desconocido(entrada.dni_norm)
        if aviso:
            cuerpo["aviso"] = aviso
        return JSONResponse(cuerpo)

    @app.patch("/api/admin/jornadas/{jornada_id}", include_in_schema=False)
    async def jornada_editar(jornada_id: int,
                             request: Request) -> JSONResponse:
        """R4 · edicion. El `dni_norm` del cuerpo se IGNORA."""
        _exigir_admin_jornadas()
        filas = repository.list_jornadas_admin()
        actual = _por_id(filas, jornada_id)
        if actual is None:
            return _no_encontrada()
        try:
            entrada = normalizar_entrada(await _cuerpo(request),
                                         dni_fijo=actual["dni_norm"])
            validar_entrada(entrada)
        except JornadaInvalida as exc:
            return _rechazo(exc)
        choque = buscar_solape(entrada, filas, excluir_id=jornada_id)
        if choque is not None:
            return _conflicto(choque)
        if not repository.actualizar_jornada(
            jornada_id=jornada_id, entrada=_a_persistir(entrada),
            actor=_actor(request),
        ):
            return _no_encontrada()
        _invalidar_jornadas()
        return JSONResponse({"ok": True, "id": jornada_id})

    @app.post("/api/admin/jornadas/{jornada_id}/cerrar",
              include_in_schema=False)
    async def jornada_cerrar(jornada_id: int,
                             request: Request) -> JSONResponse:
        """R5 · cierre de vigencia por el ULTIMO DIA INCLUIDO.

        Cerrar solo acorta la vigencia, asi que no puede crear un solape
        nuevo: no hace falta revalidarlo.
        """
        _exigir_admin_jornadas()
        actual = _por_id(repository.list_jornadas_admin(), jornada_id)
        if actual is None:
            return _no_encontrada()
        try:
            hasta = a_hasta_exclusivo((await _cuerpo(request)).get(
                "hasta_inclusivo"))
            validar_vigencia(actual["desde"], hasta)
        except JornadaInvalida as exc:
            return _rechazo(exc)
        if not repository.cerrar_jornada(jornada_id=jornada_id, hasta=hasta,
                                         actor=_actor(request)):
            return _no_encontrada()
        _invalidar_jornadas()
        return JSONResponse({"ok": True, "id": jornada_id})

    @app.post("/api/admin/jornadas/{jornada_id}/desactivar",
              include_in_schema=False)
    def jornada_desactivar(jornada_id: int, request: Request) -> JSONResponse:
        """R6 · a la papelera logica. La fila se queda en la tabla."""
        _exigir_admin_jornadas()
        if not repository.set_jornada_activa(
            jornada_id=jornada_id, activa=False, actor=_actor(request),
        ):
            return _no_encontrada()
        _invalidar_jornadas()
        return JSONResponse({"ok": True, "id": jornada_id})

    @app.post("/api/admin/jornadas/{jornada_id}/reactivar",
              include_in_schema=False)
    def jornada_reactivar(jornada_id: int, request: Request) -> JSONResponse:
        """R6 · sacarla de la papelera, REVALIDANDO el solape.

        Mientras estaba inactiva su vigencia no reservaba nada, asi que
        otra fila pudo ocuparla. Si choca, se rechaza y la fila SE QUEDA
        INACTIVA: no se toca ni ella ni la otra.
        """
        _exigir_admin_jornadas()
        filas = repository.list_jornadas_admin()
        actual = _por_id(filas, jornada_id)
        if actual is None:
            return _no_encontrada()
        choque = buscar_solape(entrada_desde_fila(actual), filas,
                               excluir_id=jornada_id)
        if choque is not None:
            return _conflicto(choque)
        if not repository.set_jornada_activa(
            jornada_id=jornada_id, activa=True, actor=_actor(request),
        ):
            return _no_encontrada()
        _invalidar_jornadas()
        return JSONResponse({"ok": True, "id": jornada_id})

    @app.patch("/api/registros/{registro_id}/hora")
    def set_registro_hora(
        registro_id: int,
        payload: HoraPayload = Body(...),
    ) -> dict[str, Any]:
        if not catalog.enabled:
            raise HTTPException(
                status_code=503,
                detail="Sigrid no configurado: no se puede resolver el "
                       "codigo de hora.",
            )
        option = catalog.get_by_ide(payload.hora_ide)
        if option is None:
            raise HTTPException(
                status_code=400,
                detail="El tipo de hora seleccionado no existe en Sigrid.",
            )
        ok = repository.set_registro_hora(
            registro_id=registro_id,
            hora_ide=option.ide,
            hora_codigo=option.codigo,
            hora_descripcion=option.descripcion,
            hora_ext=option.ext,
            hora_precio_coste=option.pre,
            hora_precio_nomina=option.prenom,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {
            "ok": True,
            "registro_id": registro_id,
            "hora_ide": option.ide,
            "hora_codigo": option.codigo,
            "hora_descripcion": option.descripcion,
            "hora_ext": option.ext,
            "tipo_hora": "extra" if option.ext == 1 else "normal",
        }

    @app.patch("/api/registros/{registro_id}/partida")
    def api_set_registro_partida(
        registro_id: int,
        payload: PartidaPayload = Body(...),
    ) -> dict[str, Any]:
        """Reimputa manualmente la partida de un registro. El front envia los
        4 campos (ide/cod/res/capitulo) de la partida-hoja elegida en el combo
        cargado con /api/sigrid/partidas (partidas del presupuesto de la obra).
        """
        ok = repository.set_registro_partida(
            registro_id=registro_id,
            partida_ide=payload.partida_ide,
            partida_cod=payload.partida_cod,
            partida_res=payload.partida_res,
            partida_capitulo=payload.partida_capitulo,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {
            "ok": True,
            "registro_id": registro_id,
            "partida_ide": payload.partida_ide,
            "partida_cod": payload.partida_cod,
            "partida_res": payload.partida_res,
            "partida_capitulo": payload.partida_capitulo,
        }

    @app.patch("/api/registros/{registro_id}")
    def update_registro(
        registro_id: int,
        payload: RegistroEditPayload = Body(...),
    ) -> dict[str, Any]:
        ok = repository.update_registro(
            registro_id=registro_id,
            tipo_hora=payload.tipo_hora,
            horas=payload.horas,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {"ok": True, "registro_id": registro_id}

    # ---------------- Estado del parte (documento) ------------------- #
    @app.post("/documents/{document_id}/approve", include_in_schema=False)
    def approve_document(
        request: Request,
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        # `request: Request` va el PRIMERO y los `Form` se quedan como
        # estaban: FastAPI inyecta `Request` por anotacion de tipo y no lo
        # trata como parametro de query, path ni body, asi que el contrato
        # HTTP y el JS no cambian.
        repository.approve_document(
            document_id=document_id,
            approved_by=_actor(request),
        )
        return _redirect(back, "Parte aprobado")

    @app.post("/documents/{document_id}/unapprove", include_in_schema=False)
    def unapprove_document(
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        # F-004 R10: flujo de FORMULARIO, no JSON; el motivo viaja en el
        # mensaje de la redireccion (el manejador global de 409 solo vale
        # para las APIs que consume el JS).
        try:
            repository.unapprove_document(document_id=document_id)
        except CongeladoError as exc:
            return _redirect(back, exc.motivo)
        return _redirect(back, "Parte marcado como pendiente")

    @app.post("/documents/{document_id}/delete", include_in_schema=False)
    def delete_document(
        request: Request,
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        try:
            repository.delete_document(
                document_id=document_id,
                deleted_by=_actor(request),
            )
        except CongeladoError as exc:   # F-004 R7
            return _redirect(back, exc.motivo)
        # Si borramos desde el detalle del propio parte, volver al listado.
        target = "/partes" if back.startswith(f"/partes/{document_id}") else back
        return _redirect(target, "Parte movido a la papelera")

    # ----------------------------------------------------------- #
    # BORRADO: linea / obra / persona  (soft -> papelera -> hard).
    # ----------------------------------------------------------- #
    @app.post("/api/registro/{registro_id}/delete", include_in_schema=False)
    def api_registro_delete(request: Request,
                            registro_id: int) -> JSONResponse:
        ok = repository.soft_delete_registro(
            registro_id=registro_id, by=_actor(request)
        )
        return JSONResponse({"ok": ok})

    @app.post("/api/registro/{registro_id}/restore", include_in_schema=False)
    def api_registro_restore(registro_id: int) -> JSONResponse:
        return JSONResponse(
            {"ok": repository.restore_registro(registro_id=registro_id)}
        )

    @app.post("/api/registro/{registro_id}/hard-delete", include_in_schema=False)
    def api_registro_hard(registro_id: int) -> JSONResponse:
        return JSONResponse(
            {"ok": repository.hard_delete_registro(registro_id=registro_id)}
        )

    @app.post("/api/obra/{obra_key}/delete", include_in_schema=False)
    def api_obra_delete(request: Request, obra_key: str) -> JSONResponse:
        n, congelados = repository.soft_delete_obra(
            obra_key=obra_key, by=_actor(request)
        )
        # F-004 R13: `congelados` lo pinta la UI; sin ese numero el
        # usuario creeria que se borro la obra entera.
        return JSONResponse(
            {"ok": n > 0, "partes": n, "congelados": congelados})

    @app.post("/api/trabajador/{worker_key}/delete", include_in_schema=False)
    def api_trabajador_delete(request: Request,
                              worker_key: str) -> JSONResponse:
        n, congelados = repository.soft_delete_worker(
            worker_key=worker_key, by=_actor(request)
        )
        return JSONResponse(
            {"ok": n > 0, "lineas": n, "congelados": congelados})

    @app.post("/api/documento/{document_id}/restore", include_in_schema=False)
    def api_documento_restore(document_id: str) -> JSONResponse:
        return JSONResponse(
            {"ok": repository.restore_document(document_id=document_id)}
        )

    @app.post("/api/documento/{document_id}/hard-delete", include_in_schema=False)
    def api_documento_hard(document_id: str) -> JSONResponse:
        return JSONResponse(
            {"ok": repository.hard_delete_document(document_id=document_id)}
        )

    @app.post("/api/papelera/vaciar", include_in_schema=False)
    def api_papelera_vaciar() -> JSONResponse:
        res = repository.vaciar_papelera()
        return JSONResponse({"ok": True, **res})

    @app.get("/papelera", response_class=HTMLResponse)
    def papelera(
        request: Request, message: str | None = Query(default=None)
    ) -> HTMLResponse:
        pap = repository.list_papelera()
        context = {
            "request": request,
            "title": settings.app_title,
            "documentos": pap["documentos"],
            "registros": pap["registros"],
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="papelera.html", context=context
        )

    # ----------------------------------------------------------- #
    # CREAR parte manualmente (un dia o un periodo, con calendario).
    # ----------------------------------------------------------- #
    @app.get("/nuevo", response_class=HTMLResponse)
    def nuevo_parte(request: Request) -> HTMLResponse:
        context = {
            "request": request,
            "title": settings.app_title,
            "sigrid_enabled": getattr(obra_catalog, "enabled", False),
            "hoy": date.today().isoformat(),
        }
        return templates.TemplateResponse(
            request=request, name="nuevo_parte.html", context=context
        )

    # Incidencias estandar del parte (J.310) -> codigo CI* de Sigrid.
    _INCIDENCIAS_CI = {
        "V": "CIV",    # Vacaciones
        "B": "CIE",    # Baja enfermedad comun (Enfermedad/Acc. no laboral)
        "AT": "CIA",   # Accidente / Enf. profesional
        "FJ": "CIP",   # Falta justificada / Permiso
        "F": "CIF",    # Falta injustificada
        "H": "CIH",    # Huelga
        "M": "CIM",    # Maternidad / Paternidad
    }

    @app.post("/api/partes/nuevo", include_in_schema=False)
    async def api_partes_nuevo(request: Request) -> JSONResponse:
        try:
            data = await request.json()
        except Exception:  # noqa: BLE001
            data = None
        if not isinstance(data, dict):
            return JSONResponse(
                {"ok": False, "error": "Body no es JSON válido."}, status_code=400
            )
        dias = data.get("dias") or []
        if not isinstance(dias, list) or not dias:
            return JSONResponse(
                {"ok": False, "error": "Selecciona al menos un día."},
                status_code=400,
            )
        nombre = (data.get("empleado_nombre") or "").strip()
        if not nombre:
            return JSONResponse(
                {"ok": False, "error": "Falta el trabajador."}, status_code=400
            )
        if data.get("obra_ide") is None and not (data.get("obra_codigo") or "").strip():
            return JSONResponse(
                {"ok": False, "error": "Falta la obra."}, status_code=400
            )

        # Incidencia y horas son EXCLUYENTES.
        incidencia = (data.get("incidencia_codigo") or "").strip().upper() or None
        if incidencia and incidencia not in _INCIDENCIAS_CI:
            return JSONResponse(
                {"ok": False,
                 "error": f"Incidencia desconocida: {incidencia}"},
                status_code=400,
            )

        def _f(v: Any) -> float:
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        _ord = _f(data.get("horas_ordinaria"))
        _ext = _f(data.get("horas_extra"))
        if incidencia and (abs(_ord) > 1e-9 or abs(_ext) > 1e-9):
            return JSONResponse(
                {"ok": False, "error": "Una incidencia no lleva horas: pon "
                                       "las horas a 0 o quita la incidencia."},
                status_code=400,
            )
        if not incidencia and abs(_ord) < 1e-9 and abs(_ext) < 1e-9:
            return JSONResponse(
                {"ok": False,
                 "error": "Pon horas (ordinarias o extra) o elige una "
                          "incidencia."},
                status_code=400,
            )

        # Casar el CODIGO DE HORA por categoria+tipo (igual que sv3 en la
        # ingesta), para que las lineas manuales no salgan "sin asignar".
        hora_normal = None
        hora_extra = None
        hora_incidencia = None
        categoria_txt = (data.get("categoria") or "").strip()
        if categoria_txt and sigrid_client is not None:
            try:
                from application.services.tipo_hora_matcher import (
                    HoraMatch, TipoHoraMatcher,
                )
                tipos_catalogo = sigrid_client.fetch_tipos_hora()
                matcher = TipoHoraMatcher(tipos_catalogo)
                hora_normal = matcher.match(categoria_txt, extra=False)
                hora_extra = matcher.match(categoria_txt, extra=True)
                if incidencia:
                    ci_cod = _INCIDENCIAS_CI[incidencia]
                    th = next(
                        (x for x in tipos_catalogo
                         if (x.codigo or "").strip().upper() == ci_cod),
                        None,
                    )
                    if th is not None:
                        hora_incidencia = HoraMatch(
                            ide=th.ide, codigo=th.codigo,
                            descripcion=th.descripcion, ext=th.ext,
                            pre=th.pre, prenom=th.prenom, method="manual",
                        )
            except Exception as exc:  # noqa: BLE001
                logger.warning("[partes-nuevo] match codigo hora fallo: %r", exc)

        # Casar la PARTIDA en el momento de crear (mismo motor que sv3):
        # primero por NOMBRE del trabajador en la descripcion, luego por
        # CATEGORIA, y SOLO en el capitulo CI. Antes esto quedaba pendiente
        # de la siguiente conciliacion de sv3 (al persistir un parte por
        # email), de ahi que registros iguales salieran unos casados y otros
        # en blanco. Si el usuario eligio partida a mano, se respeta.
        partida_ide = _as_int(data.get("partida_ide"))
        partida_cod = data.get("partida_cod") or None
        partida_res_txt = data.get("partida_res") or None
        partida_capitulo = data.get("partida_capitulo") or None
        partida_metodo = "manual" if partida_ide else None
        partida_score = 1.0 if partida_ide else None
        obra_ide_int = _as_int(data.get("obra_ide"))
        if partida_ide is None and sigrid_client is not None and obra_ide_int:
            try:
                from application.services.partida_catalog import (
                    build_arbol_partidas,
                    partidas_hoja,
                )
                from application.services.partida_matcher import match_partida
                filas = sigrid_client.fetch_partidas_obra(obra_ide_int)
                nodos = build_arbol_partidas(filas)
                candidatas = partidas_hoja(nodos, categoria="CI")
                m = match_partida(categoria_txt or None, nombre, candidatas)
                if m is not None:
                    partida_ide = m.partida.ide
                    partida_cod = m.partida.cod
                    partida_res_txt = m.partida.res
                    partida_capitulo = m.partida.categoria
                    partida_metodo = m.metodo
                    partida_score = m.score
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[partes-nuevo] casado de partida fallo: %r", exc
                )

        res = repository.crear_parte_manual(
            obra_ide=_as_int(data.get("obra_ide")),
            obra_codigo=(data.get("obra_codigo") or None),
            obra_nombre=(data.get("obra_nombre") or None),
            empleado_ide=_as_int(data.get("empleado_ide")),
            empleado_codigo=(data.get("empleado_codigo") or None),
            empleado_nombre=nombre,
            empleado_dni=(data.get("empleado_dni") or None),
            empleado_reside=_as_int(data.get("empleado_reside")),
            categoria=(data.get("categoria") or None),
            dias=[str(d) for d in dias],
            horas_ordinaria=_ord,
            horas_extra=_ext,
            incidencia_codigo=incidencia,
            hora_incidencia=hora_incidencia,
            partida_ide=partida_ide,
            partida_cod=partida_cod,
            partida_res=partida_res_txt,
            partida_capitulo=partida_capitulo,
            partida_match_method=partida_metodo,
            partida_match_score=partida_score,
            hora_normal=hora_normal,
            hora_extra=hora_extra,
            by=_actor(request),
        )
        ok = not res.get("error") and (res.get("lineas") or 0) > 0
        return JSONResponse(
            {"ok": ok, **res}, status_code=200 if ok else 400
        )

    return app


def _redirect(path: str, message: str) -> RedirectResponse:
    sep = "&" if "?" in path else "?"
    qs = urlencode({"message": message})
    return RedirectResponse(url=f"{path}{sep}{qs}", status_code=303)
