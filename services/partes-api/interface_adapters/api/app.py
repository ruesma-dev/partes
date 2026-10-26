# interface_adapters/api/app.py
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from application.pipelines.extract_parte_pipeline import (
    ExtractPartePipeline,
    ExtractParteRequest,
)
from application.services.parte_extraction_service import (
    ParteExtractionService,
    ProviderClientSpec,
)
from application.services.auxhor_catalog_provider import AuxhorCatalogProvider
from application.services.obra_sigrid import ComprobadorObra
from application.services.schema_registry import SchemaRegistry
from config.settings import Settings
from infrastructure.document.pagina_pdf_imagen import PaginaPdfImagenConversor
from infrastructure.llm.claude_messages_client import ClaudeMessagesVisionClient
from infrastructure.llm.gemini_genai_client import GeminiGenAiVisionClient
from infrastructure.llm.openai_responses_client import OpenAiResponsesVisionClient
from infrastructure.llm.llm_call_logger import LlmCallLogger
from infrastructure.llm.retry_policy import RetryPolicy
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient

logger = logging.getLogger(__name__)


def _parse_origins(value: str) -> List[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def build_app(settings: Settings) -> FastAPI:
    prompt_repo = YamlPromptRepository(settings.prompts_yaml_path)
    schema_registry = SchemaRegistry()

    retry_policy = RetryPolicy(
        max_retries=settings.llm_max_retries,
        backoff_base_s=settings.llm_backoff_base_s,
        backoff_cap_s=settings.llm_backoff_cap_s,
    )

    ia_log_dir = settings.ia_logging_dir if settings.ia_logging_enabled else None
    call_logger = LlmCallLogger(base_dir=ia_log_dir)

    providers: list[ProviderClientSpec] = []
    if settings.gemini_enabled:
        providers.append(
            ProviderClientSpec(
                provider="gemini",
                model_name=settings.gemini_model,
                client=GeminiGenAiVisionClient(
                    settings.gemini_api_key,
                    media_resolution=settings.gemini_media_resolution,
                    retry_policy=retry_policy,
                    call_logger=call_logger,
                ),
            )
        )
    if settings.claude_enabled:
        providers.append(
            ProviderClientSpec(
                provider="claude",
                model_name=settings.anthropic_model,
                client=ClaudeMessagesVisionClient(
                    api_key=settings.anthropic_api_key,
                    max_tokens=settings.anthropic_max_tokens,
                    timeout_s=settings.anthropic_timeout_s,
                    retry_policy=retry_policy,
                    call_logger=call_logger,
                ),
            )
        )
    if settings.openai_enabled:
        providers.append(
            ProviderClientSpec(
                provider="openai",
                model_name=settings.openai_model,
                client=OpenAiResponsesVisionClient(
                    api_key=settings.openai_api_key,
                    max_output_tokens=settings.openai_max_output_tokens,
                    timeout_s=settings.openai_timeout_s,
                    retry_policy=retry_policy,
                    call_logger=call_logger,
                    image_detail=settings.openai_image_detail,
                ),
            )
        )

    logger.info(
        "[partes-sv2][wiring] proveedores=%s provider_activo=%s prompt=%s",
        [p.provider for p in providers] or "(ninguno)",
        settings.ia_provider,
        settings.prompt_key,
    )

    extraction_service = ParteExtractionService(
        providers=providers,
        prompt_repo=prompt_repo,
        schema_registry=schema_registry,
    )

    # Catalogo de codigos de hora (auxhor) desde sigrid-api, filtrado, para
    # que la IA proponga el codigo. Si Sigrid no esta cableado -> None.
    catalog_provider: AuxhorCatalogProvider | None = None
    sigrid_client: SigridLookupClient | None = None
    if settings.sigrid_catalog_enabled:
        sigrid_client = SigridLookupClient(
            base_url=settings.sigrid_api_base_url,          # type: ignore[arg-type]
            function_key=settings.sigrid_api_function_key,  # type: ignore[arg-type]
            database=settings.sigrid_api_database,          # type: ignore[arg-type]
            timeout_s=settings.sigrid_api_timeout_s,
            max_rows=settings.sigrid_api_max_rows,
        )
        catalog_provider = AuxhorCatalogProvider(
            client=sigrid_client,
            exclude_keywords=settings.auxhor_exclude_keywords_list,
            exclude_codes=settings.auxhor_exclude_codes_list,
            ttl_seconds=settings.auxhor_cache_ttl_s,
        )
        logger.info(
            "[partes-sv2][wiring] catalogo auxhor CABLEADO (excluye=%s).",
            settings.auxhor_exclude_keywords_list,
        )
    else:
        logger.info(
            "[partes-sv2][wiring] catalogo auxhor DESACTIVADO (faltan "
            "SIGRID_API_*); la IA no propondra codigo de hora."
        )

    # F-059: página escaneada a la IA como imagen derecha. Con el interruptor
    # apagado no hay conversor ni lista: el pipeline manda el PDF como antes.
    conversor: PaginaPdfImagenConversor | None = None
    proveedores_imagen: frozenset[str] = frozenset()
    if settings.pagina_como_imagen:
        conversor = PaginaPdfImagenConversor()
        proveedores_imagen = settings.proveedores_pagina_como_imagen
    logger.info(
        "[partes-sv2][wiring] página como imagen=%s proveedores=%s "
        "openai_image_detail=%s",
        settings.pagina_como_imagen,
        sorted(proveedores_imagen) or "(ninguno)",
        settings.openai_image_detail or "(sin detail)",
    )

    # F-058: relectura de la cabecera con otro proveedor y, con sigrid-api
    # cableado, consulta de obra en el momento con el mismo cliente que el
    # catálogo auxhor. Sin secretos en el log.
    relectura_provider = settings.relectura_cabecera_activa
    relectura_model: str | None = None
    obras: ComprobadorObra | None = None
    if relectura_provider is not None:
        relectura_model = extraction_service.model_name(relectura_provider)
        if sigrid_client is not None:
            obras = ComprobadorObra(
                client=sigrid_client, timeout_s=settings.obra_existe_timeout_s)
        logger.log(
            logging.INFO if obras is not None else logging.WARNING,
            "[partes-sv2][wiring] relectura cabecera ACTIVA provider=%s "
            "model=%s comprueba_obra=%s timeout_obra_s=%s",
            relectura_provider,
            relectura_model,
            obras is not None,
            settings.obra_existe_timeout_s,
        )
    elif settings.relectura_cabecera_enabled:
        logger.warning(
            "[partes-sv2][wiring] relectura cabecera INACTIVA motivo=%s",
            settings.relectura_cabecera_motivo_inactiva,
        )
    else:
        logger.info("[partes-sv2][wiring] relectura cabecera DESACTIVADA")

    pipeline = ExtractPartePipeline(
        extraction_service=extraction_service,
        max_file_mb=settings.max_file_mb,
        service_version=settings.service_version,
        provider=settings.ia_provider,
        prompt_key=settings.prompt_key,
        catalog_provider=catalog_provider,
        conversor=conversor,
        proveedores_imagen=proveedores_imagen,
        relectura_provider=relectura_provider,
        obras=obras,
    )

    app = FastAPI(title="Partes de Trabajo Extractor API", version=settings.service_version)
    # Expuesto para que el worker (main_worker.py) reutilice el mismo wiring.
    app.state.pipeline = pipeline

    if settings.cors_allow_origins:
        origins = _parse_origins(settings.cors_allow_origins)
        if origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {
            "ok": True,
            "service": "partes-extractor-api",
            "version": settings.service_version,
            "provider": settings.ia_provider,
            "prompt_key": settings.prompt_key,
            "providers_loaded": [
                {"provider": p.provider, "model": p.model_name} for p in providers
            ],
            # F-058 (R26): el proveedor de relectura activo, o null.
            "relectura_cabecera": (
                None if relectura_provider is None else {
                    "provider": relectura_provider,
                    "model": relectura_model,
                    "comprueba_obra": obras is not None,
                }
            ),
        }

    @app.post("/v1/partes/extract")
    async def extract_parte(file: UploadFile = File(...)) -> Dict[str, Any]:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Archivo vacio.")
        try:
            return pipeline.run(
                ExtractParteRequest(
                    filename=file.filename or "document.bin",
                    mime_type=file.content_type or "application/octet-stream",
                    file_bytes=data,
                )
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Error en extract_parte")
            raise HTTPException(status_code=500, detail=f"Error: {exc}") from exc

    return app
