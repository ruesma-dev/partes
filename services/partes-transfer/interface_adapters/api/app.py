# interface_adapters/api/app.py
"""API HTTP de partes-transfer (sv5).

  POST /api/registro/preflight  -> analiza y devuelve que se haria
  POST /api/registro/ejecutar   -> escribe en Sigrid (con pisar_claves)
  GET  /health
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

logger = logging.getLogger(__name__)


# ----------------------------- esquemas ----------------------------- #

class ObraIn(BaseModel):
    ide: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None


class LineaIn(BaseModel):
    registro_id: int
    fecha_int: int
    recurso_ide: Optional[int] = None
    dni: Optional[str] = None
    nombre: Optional[str] = None
    tipo_hora: Optional[str] = None
    es_incidencia: bool = False
    horas: Optional[float] = None
    hora_ide: Optional[int] = None
    hora_codigo: Optional[str] = None
    partida_ide: Optional[int] = None
    partida_cod: Optional[str] = None
    candef: Optional[float] = None
    incidencia_codigo: Optional[str] = None
    incidencia_rol: Optional[str] = None


class PeticionIn(BaseModel):
    obra: ObraIn
    lineas: list[LineaIn] = Field(default_factory=list)
    pisar_claves: list[str] = Field(default_factory=list)
    usuario: Optional[str] = None


def build_app(settings, pipeline: RegistroPipeline | None = None) -> FastAPI:
    """API de sv5.

    `pipeline` se inyecta desde `main.py` para que el HTTP y los hilos
    consumidores de `q-transfer` compartan UNA instancia y, con ella, UN
    lock de escritura (R7). Sin inyeccion construye el suyo, que es el
    comportamiento de siempre.

    Los endpoints NO toman el lock: lo adquiere `RegistroPipeline.
    registrar`, de modo que `ejecutar` queda serializado igualmente y
    `preflight` sigue sin bloquear a nadie.
    """
    app = FastAPI(title="Partes -> Sigrid (transfer)", version="1.0.0")

    if pipeline is None:
        cliente = SigridWriteClient(
            base_url=settings.sigrid_api_base_url,
            function_key=settings.sigrid_api_function_key,
            database=settings.sigrid_api_database,
            empresa=settings.sigrid_empresa,
            timeout_s=settings.sigrid_api_timeout_s,
            max_statements=settings.sigrid_max_statements,
            tip_parte=settings.tip_parte_trabajo,
            est_parte=settings.est_parte_activo,
        )
        pipeline = RegistroPipeline(cliente=cliente, settings=settings)

    def _dominio(p: PeticionIn):
        obra = ObraEntrada(ide=p.obra.ide, codigo=p.obra.codigo,
                           nombre=p.obra.nombre)
        lineas = [LineaEntrada(**l.model_dump()) for l in p.lineas]
        return obra, lineas

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "modo_pruebas": settings.obra_pruebas_forzar,
                "obra_pruebas": settings.obra_pruebas_cod,
                "database": settings.sigrid_api_database}

    @app.post("/api/registro/preflight")
    async def preflight(p: PeticionIn) -> JSONResponse:
        obra, lineas = _dominio(p)
        try:
            pf = pipeline.preflight(obra=obra, lineas=lineas)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[api] preflight fallo")
            return JSONResponse({"ok": False, "error": str(exc)},
                                status_code=502)
        return JSONResponse({
            "ok": True,
            "obra_destino": asdict(pf.obra_destino),
            "forzada_pruebas": pf.forzada_pruebas,
            "partes": [asdict(x) for x in pf.partes],
            "acciones": [asdict(a) for a in pf.acciones],
            "conflictos": [asdict(c) for c in pf.conflictos],
            "resumen": {"escribir": pf.n_escribir, "omitir": pf.n_omitir,
                        "ya_registrado": pf.n_ya,
                        "conflictos": len(pf.conflictos)},
        })

    @app.post("/api/registro/ejecutar")
    async def ejecutar(p: PeticionIn) -> JSONResponse:
        obra, lineas = _dominio(p)
        try:
            r = pipeline.ejecutar(obra=obra, lineas=lineas,
                                 pisar_claves=set(p.pisar_claves),
                                 usuario=p.usuario)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[api] ejecutar fallo")
            return JSONResponse({"ok": False, "error": str(exc)},
                                status_code=502)
        return JSONResponse({
            "ok": r.ok,
            "obra_destino": asdict(r.obra_destino),
            "forzada_pruebas": r.forzada_pruebas,
            "partes": [asdict(x) for x in r.partes],
            "escritas": r.escritas,
            "omitidas": r.omitidas,
            "ya_registradas": r.ya_registradas,
            "pisadas": r.pisadas,
            "borradas": r.borradas,
            "pendientes_confirmacion": [asdict(c)
                                        for c in r.pendientes_confirmacion],
        })

    return app
