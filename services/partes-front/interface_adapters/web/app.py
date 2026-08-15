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
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import Body, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

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
from application.services.jornada_resolver import (
    candef_valido,
    jornada_efectiva,
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
from application.services.obra_catalog import ObraCatalog
from application.services.empleado_catalog import EmpleadoCatalog
from application.services import empleado_reconciler as recon

logger = logging.getLogger(__name__)

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


def _as_int(value: Any) -> int | None:
    """Coacciona a int tolerando str/float; None si no es convertible."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_app(
    settings: Settings,
    *,
    repository: ParteReviewRepository | None = None,
    transfer_client: TransferClient | None = None,
    publisher: TransferQueuePublisher | None = None,
    cola_cliente=None,
    calendario_provider: CalendarioProvider | None = None,
) -> FastAPI:
    """Portal de revision.

    Los colaboradores se pueden inyectar (repositorio, cliente HTTP de
    sv5, publisher de `q-transfer`, cliente de cola para la gestion de
    poison y proveedor de calendario). Sin inyeccion se construyen desde
    `settings`, que es lo que hace `main.py`; con ella, la suite levanta
    la app sin PostgreSQL, sin red y sin Storage.
    """
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
    app.state.graph_token_provider = graph_token_provider
    app.state.calendario_provider = calendario_provider
    app.state.tables_ready = tables_ready

    templates = Jinja2Templates(
        directory=str(Path(__file__).resolve().parents[2] / "templates")
    )
    templates.env.filters["horas"] = _fmt_horas
    templates.env.filters["fecha"] = _fmt_fecha
    templates.env.filters["incidencia"] = _incidencia_label
    templates.env.globals["asset_version"] = str(int(time.time()))
    app.mount(
        "/static",
        StaticFiles(
            directory=str(Path(__file__).resolve().parents[2] / "static")
        ),
        name="static",
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
        detail = repository.get_worker(worker_key)
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
        # ordinarias del dia por debajo del CanDefecto efectivo (el de
        # Sigrid, u 8 si era <= minimo). Se excluyen findes/festivos y
        # los dias sin horas ordinarias (0).
        candef_efectivo = candef_kpi["valor"]
        dias_incompletos: set[str] = set()
        if calendar is not None:
            for _week in calendar.weeks:
                for _day in _week:
                    if (_day.in_period and not _day.is_weekend
                            and not _day.is_holiday
                            and 0.0 < (_day.normal_h or 0.0)
                            < candef_efectivo - 1e-9):
                        dias_incompletos.add(_day.date_iso)

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
            "dias_incompletos": dias_incompletos,
            "sesame_degradado": sesame_degradado,
            "jornada_contrato": jornada_contrato,
            "jornada_divergente": jornada_divergente,
            "extras": extras_por_jornada(detail.registros),
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
            _eff = jornada_efectiva(_real, minimo=_cd_min, por_defecto=_cd_jor)
            # Festivo SEGUN EL CALENDARIO DE ESTA FILA (R2): la columna
            # pinta el calendario por defecto, pero el aviso no puede
            # heredar los festivos de otra provincia.
            _es_festivo = calendario_provider.holiday_name_para(_row.dni)
            for _c in _row.cells:
                if not _c.date_iso:
                    continue
                _fecha = date.fromisoformat(_c.date_iso)
                _consultas.add((_row.dni, _fecha.year))
                if _c.is_weekend or _es_festivo(_fecha):
                    continue
                if 0.0 < (_c.normal or 0.0) < _eff - 1e-9:
                    incompletos.add((_row.nombre or "") + "|"
                                    + (_c.date_iso or ""))
        _dias_periodo = {int(d.date_iso[:4]) for d in detail.days if d.date_iso}
        _consultas.update((None, ano) for ano in _dias_periodo)
        sesame_degradado = not calendario_provider.fiable_para(_consultas)

        context = {
            "request": request,
            "title": settings.app_title,
            "detail": detail,
            "period_options": detail.period_options,
            "selected_period": detail.period_key,
            "extras": extras_por_jornada(_regs_kpi),
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
            "message": message,
        }
        return templates.TemplateResponse(
            request=request, name="obra_detail.html", context=context
        )

    # -------------------- CONCILIACION de trabajadores ---------------- #
    @app.get("/conciliacion", response_class=HTMLResponse)
    def conciliacion(request: Request) -> HTMLResponse:
        pendientes = repository.list_unmatched_workers()
        empleados = empleado_catalog.list() if empleado_catalog.enabled else []

        filas: list[dict] = []
        n_auto = n_rev = n_sin = n_cat = 0
        for p in pendientes:
            bucket, cands = recon.classify(p["nombre_leido"], empleados, top_n=5)
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
                "candidates": [
                    {"ide": c.ide, "codigo": c.codigo, "nombre": c.nombre,
                     "dni": c.dni, "score": round(c.score * 100)}
                    for c in cands
                ],
            })

        context = {
            "request": request,
            "title": settings.app_title,
            "sigrid_enabled": settings.sigrid_lookup_enabled,
            "preview_enabled": settings.preview_enabled,
            "empleados_total": len(empleados),
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
        ide = _as_int(data.get("ide"))
        if not nombre_leido or ide is None:
            return JSONResponse(
                {"ok": False, "error": "Faltan datos: "
                 f"nombre_leido={nombre_leido!r}, ide={data.get('ide')!r}."},
                status_code=400,
            )
        emp = empleado_catalog.get_by_ide(ide)
        if emp is None:
            return JSONResponse(
                {"ok": False, "error": "Empleado no encontrado en el maestro "
                 f"(ide={ide}). ¿Sigrid configurado en sv4?"},
                status_code=404,
            )
        try:
            updated = repository.backfill_empleado(
                nombre_leido=nombre_leido, ide=emp.ide,
                codigo=emp.codigo, nombre=emp.nombre, dni=emp.dni,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[conciliacion] backfill fallo")
            return JSONResponse(
                {"ok": False, "error": f"Error guardando casado: "
                 f"{type(exc).__name__}: {exc}"},
                status_code=500,
            )
        # El alias es una optimizacion (auto-casado futuro): best-effort.
        alias_ok = True
        try:
            repository.upsert_empleado_alias(
                nombre_leido=nombre_leido, ide=emp.ide,
                codigo=emp.codigo, nombre=emp.nombre, dni=emp.dni,
                created_by="conciliacion",
            )
        except Exception as exc:  # noqa: BLE001
            alias_ok = False
            logger.warning("[conciliacion] alias no guardado: %r", exc)
        return JSONResponse({
            "ok": True, "updated": updated, "alias_ok": alias_ok,
            "empleado": {"ide": emp.ide, "codigo": emp.codigo,
                         "nombre": emp.nombre},
        })

    @app.get("/api/conciliacion/buscar")
    def conciliacion_buscar(
        q: str = Query(default=""),
        nombre_leido: str | None = Query(default=None),
    ) -> JSONResponse:
        empleados = empleado_catalog.list() if empleado_catalog.enabled else []
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
             "dni": e.dni, "score": round(sc * 100)}
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
        ide = _as_int(data.get("ide"))
        if ide is None:
            return JSONResponse(
                {"ok": False, "error": f"Falta o es inválido 'ide' "
                 f"({data.get('ide')!r})."},
                status_code=400,
            )
        emp = empleado_catalog.get_by_ide(ide)
        if emp is None:
            return JSONResponse(
                {"ok": False, "error": "Empleado no encontrado en el maestro "
                 f"(ide={ide}). ¿Sigrid configurado en sv4?"},
                status_code=404,
            )
        registro_id = _as_int(data.get("registro_id"))
        registro_ids_in = data.get("registro_ids")
        worker_key = data.get("worker_key")
        nombre_leido_in = data.get("nombre_leido")
        updated = 0
        leidos: list[str] = []
        try:
            if isinstance(registro_ids_in, list) and registro_ids_in:
                ids = [_as_int(x) for x in registro_ids_in]
                ids = [x for x in ids if x is not None]
                updated = repository.reassign_empleado_by_registro_ids(
                    registro_ids=ids, ide=emp.ide, codigo=emp.codigo,
                    nombre=emp.nombre, dni=emp.dni,
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
                updated = repository.reassign_empleado_by_leido(
                    nombre_leido=leido, ide=emp.ide, codigo=emp.codigo,
                    nombre=emp.nombre, dni=emp.dni,
                )
                leidos = [leido]
            elif worker_key:
                updated, leidos = repository.reassign_empleado_by_worker_key(
                    worker_key=worker_key, ide=emp.ide,
                    codigo=emp.codigo, nombre=emp.nombre, dni=emp.dni,
                )
            elif nombre_leido_in:
                updated = repository.reassign_empleado_by_leido(
                    nombre_leido=nombre_leido_in, ide=emp.ide,
                    codigo=emp.codigo, nombre=emp.nombre, dni=emp.dni,
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
        alias_ok = True
        for leido in leidos:
            try:
                repository.upsert_empleado_alias(
                    nombre_leido=leido, ide=emp.ide, codigo=emp.codigo,
                    nombre=emp.nombre, dni=emp.dni, created_by="reasignacion",
                )
            except Exception as exc:  # noqa: BLE001
                alias_ok = False
                logger.warning("[reasignar] alias no guardado: %r", exc)
        return JSONResponse({
            "ok": True, "updated": updated, "alias_ok": alias_ok,
            "empleado": {"ide": emp.ide, "codigo": emp.codigo,
                         "nombre": emp.nombre},
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
                    {"ide": o.ide, "codigo": o.codigo, "nombre": o.nombre}
                    for o in items
                ],
            }
        )

    @app.get("/api/sigrid/empleados", include_in_schema=False)
    def sigrid_empleados() -> JSONResponse:
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
        def _sugerida(cd: float | None) -> float:
            # CanDefecto no valido (vacio o <= minimo) -> jornada por defecto
            # (mismo umbral que sv3 al reclasificar extras).
            return jornada_efectiva(
                cd,
                minimo=settings.candef_minimo_valido,
                por_defecto=settings.jornada_por_defecto,
            )

        return JSONResponse({
            "ok": True,
            "items": [
                {"ide": e.ide, "codigo": e.codigo, "nombre": e.nombre,
                 "dni": e.dni, "reside": e.reside, "categoria": e.categoria,
                 "candef": e.candef,
                 "jornada_sugerida": _sugerida(e.candef)}
                for e in items
            ],
        })

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
        # cableado o no se encuentra, usa lo que envie el front.
        ide = payload.ide
        nombre = payload.nombre
        if obra_catalog.enabled:
            opt = obra_catalog.get_by_codigo(payload.codigo)
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

    def _payload_registro(body: dict) -> dict | JSONResponse:
        """Construye el payload de sv5 desde los ids (o desde la obra)."""
        ids = [int(i) for i in (body.get("registro_ids") or []) if i]
        if not ids:
            obra_key = (body.get("obra_key") or "").strip()
            if not obra_key:
                return JSONResponse(
                    {"ok": False, "error": "faltan registro_ids u obra_key"},
                    status_code=422)
            ids = repository.registro_ids_de_obra(
                obra_key, period_key=body.get("period"),
                mode=(body.get("mode") or "nomina"))
        datos = repository.lineas_para_registro(ids)
        if not datos["lineas"]:
            return JSONResponse(
                {"ok": False, "error": "no hay lineas activas que registrar"},
                status_code=422)
        return {
            "obra": datos["obra"],
            "lineas": datos["lineas"],
            "pisar_claves": [str(k) for k in (body.get("pisar_claves") or [])],
            "usuario": settings.default_reviewer,
        }

    @app.post("/api/aprobar/preflight", include_in_schema=False)
    async def aprobar_preflight(request: Request) -> JSONResponse:
        if transfer_client is None:
            return JSONResponse(
                {"ok": False, "error": "registro en Sigrid no configurado "
                                       "(TRANSFER_BASE_URL)"},
                status_code=503)
        payload = _payload_registro(await request.json())
        if isinstance(payload, JSONResponse):
            return payload
        return JSONResponse(transfer_client.preflight(payload))

    def _trazar(resultado: dict, ids: list[int]) -> None:
        """Traza el veredicto en `parte_registros`, sin tumbar la respuesta.

        Que falle la traza no invalida lo que sv5 ya escribio en Sigrid;
        y si el registro fue por cola, el mensaje de `q-transfer-result`
        vuelve a intentarlo.
        """
        try:
            aplicar_resultado(repository, resultado, registro_ids=ids,
                              usuario=settings.default_reviewer)
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
        payload = _payload_registro(body)
        if isinstance(payload, JSONResponse):
            return payload
        resultado = transfer_client.ejecutar(payload)
        _trazar(resultado, [l["registro_id"] for l in payload["lineas"]])
        return JSONResponse(resultado)

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
        payload = _payload_registro(body)
        if isinstance(payload, JSONResponse):
            return payload
        ids = [l["registro_id"] for l in payload["lineas"]]

        if publisher is None:
            resultado = transfer_client.ejecutar(payload)     # R3
            _trazar(resultado, ids)
            return JSONResponse(dict(resultado, modo="sincrono"))

        # Primero se publica y luego se marca: al reves, un fallo al
        # publicar dejaria lineas en 'encolado' sin nada que las recoja.
        peticion_id = publisher.publicar(payload,
                                         usuario=settings.default_reviewer)
        try:
            repository.marcar_registros_encolado(
                ids, usuario=settings.default_reviewer)      # R2
        except Exception:
            logger.warning("[transfer-cola] peticion %s encolada pero no se "
                           "pudo marcar 'encolado'; el resultado las marcara",
                           peticion_id, exc_info=True)
        return JSONResponse({"ok": True, "modo": "asincrono",
                             "peticion_id": peticion_id,
                             "encoladas": len(ids)})

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
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        repository.approve_document(
            document_id=document_id,
            approved_by=settings.default_reviewer,
        )
        return _redirect(back, "Parte aprobado")

    @app.post("/documents/{document_id}/unapprove", include_in_schema=False)
    def unapprove_document(
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        repository.unapprove_document(document_id=document_id)
        return _redirect(back, "Parte marcado como pendiente")

    @app.post("/documents/{document_id}/delete", include_in_schema=False)
    def delete_document(
        document_id: str,
        back: str = Form(default="/partes"),
    ) -> RedirectResponse:
        repository.delete_document(
            document_id=document_id,
            deleted_by=settings.default_reviewer,
        )
        # Si borramos desde el detalle del propio parte, volver al listado.
        target = "/partes" if back.startswith(f"/partes/{document_id}") else back
        return _redirect(target, "Parte movido a la papelera")

    # ----------------------------------------------------------- #
    # BORRADO: linea / obra / persona  (soft -> papelera -> hard).
    # ----------------------------------------------------------- #
    @app.post("/api/registro/{registro_id}/delete", include_in_schema=False)
    def api_registro_delete(registro_id: int) -> JSONResponse:
        ok = repository.soft_delete_registro(
            registro_id=registro_id, by=settings.default_reviewer
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
    def api_obra_delete(obra_key: str) -> JSONResponse:
        n = repository.soft_delete_obra(
            obra_key=obra_key, by=settings.default_reviewer
        )
        return JSONResponse({"ok": n > 0, "partes": n})

    @app.post("/api/trabajador/{worker_key}/delete", include_in_schema=False)
    def api_trabajador_delete(worker_key: str) -> JSONResponse:
        n = repository.soft_delete_worker(
            worker_key=worker_key, by=settings.default_reviewer
        )
        return JSONResponse({"ok": n > 0, "lineas": n})

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
            by=settings.default_reviewer,
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
