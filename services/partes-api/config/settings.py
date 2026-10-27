# config/settings.py
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["gemini", "claude", "openai"]
#: Nombres válidos de proveedor (los de ``ProviderName``).
PROVEEDORES_VALIDOS = ("gemini", "claude", "openai")
#: Variable de la clave de cada proveedor (mensajes del validador).
_VARIABLE_CLAVE = {
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class Settings(BaseSettings):
    """Configuracion del servicio 2 de partes (partes-extractor).

    Version simplificada respecto al sv2 de albaranes: una sola fase de
    extraccion con el proveedor primario que elige ``IA_PROVIDER`` (gemini
    por defecto; en Azure, openai), que debe estar habilitado y con clave.
    F-058: si la cabecera sale vacia o su obra no existe en Sigrid, la
    pagina se relee una vez con ``RELECTURA_CABECERA_PROVIDER`` (gemini por
    defecto), si esta habilitado, con clave y es otro que el primario.
    """

    # --- Flags de proveedor --- #
    gemini_enabled: bool = Field(True, alias="ENABLE_GEMINI")
    claude_enabled: bool = Field(False, alias="ENABLE_CLAUDE")
    openai_enabled: bool = Field(False, alias="ENABLE_OPENAI")

    # --- Azure Storage (colas/blobs del pipeline). En Azure las inyecta la
    # Container App; en local se leen del .env como el resto de config. --- #
    # Connection strings para LOCAL (Azurite o cuenta con clave). Si estan,
    # MANDAN sobre las account_url + identidad. BLOBS se deriva de COLAS si
    # falta (Azurite: puerto 10001 -> 10000).
    colas_connection_string: str | None = Field(
        None, alias="COLAS_CONNECTION_STRING"
    )
    blobs_connection_string: str | None = Field(
        None, alias="BLOBS_CONNECTION_STRING"
    )

    colas_account_url: str | None = Field(None, alias="COLAS_ACCOUNT_URL")
    blobs_account_url: str | None = Field(None, alias="BLOBS_ACCOUNT_URL")

    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")
    # Resolucion de medios (Gemini 3). Valores: default|unspecified|low|medium|high.
    # "default" deja decidir al SDK (NO fuerza tokens extra). "high" mejora la
    # lectura de manuscritos finos pero sube tokens/pagina y consumo de cuota.
    gemini_media_resolution: str = Field("default", alias="GEMINI_MEDIA_RESOLUTION")

    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-sonnet-4-5", alias="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(8192, alias="ANTHROPIC_MAX_TOKENS")
    anthropic_timeout_s: int = Field(120, alias="ANTHROPIC_TIMEOUT_S")

    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")
    openai_max_output_tokens: int | None = Field(
        None, alias="OPENAI_MAX_OUTPUT_TOKENS"
    )
    openai_timeout_s: int = Field(120, alias="OPENAI_TIMEOUT_S")
    # F-059 (DA4): "detail" de toda input_image de OpenAI (páginas convertidas
    # y fotos del móvil). Vacío = no se manda y OpenAI aplica su "auto".
    openai_image_detail: str = Field("high", alias="OPENAI_IMAGE_DETAIL")

    # --- Proveedor activo y prompt --- #
    ia_provider: ProviderName = Field("gemini", alias="IA_PROVIDER")
    prompt_key: str = Field("parte_trabajo_es", alias="PROMPT_KEY")
    prompts_yaml_path: str = Field("config/prompts.yaml", alias="PROMPTS_YAML_PATH")

    # --- F-059: página escaneada a la IA como imagen derecha --- #
    # Interruptor (DA3: encendido por defecto; volver atrás es ponerlo a
    # false en la Container App) y proveedores a los que se aplica (DA1: CSV,
    # solo openai por defecto; vacío = ninguno).
    pagina_como_imagen: bool = Field(True, alias="PAGINA_COMO_IMAGEN")
    pagina_como_imagen_proveedores: str = Field(
        "openai", alias="PAGINA_COMO_IMAGEN_PROVEEDORES"
    )

    # --- F-058: relectura de la cabecera con otro proveedor --- #
    # Interruptor (DA5: encendido; volver atrás es ponerlo a false en la
    # Container App) y proveedor de relectura, con su modelo ya configurado
    # (sin variable de modelo propia). Solo relee si ese proveedor es otro
    # que IA_PROVIDER, está habilitado y tiene clave; si no, sv2 arranca
    # igual y lo avisa en el log de cableado.
    relectura_cabecera_enabled: bool = Field(True, alias="RELECTURA_CABECERA")
    relectura_cabecera_provider: ProviderName = Field(
        "gemini", alias="RELECTURA_CABECERA_PROVIDER"
    )
    # DA12 = A: tope de la consulta de obra a sigrid-api, en segundos (> 0).
    # Independiente de SIGRID_API_TIMEOUT_S, que sigue siendo el del catálogo.
    obra_existe_timeout_s: float = Field(
        5.0, gt=0, alias="OBRA_EXISTE_TIMEOUT_S"
    )

    # --- Reintentos LLM --- #
    llm_max_retries: int = Field(2, alias="LLM_MAX_RETRIES")
    llm_backoff_base_s: float = Field(2.0, alias="LLM_BACKOFF_BASE_S")
    llm_backoff_cap_s: float = Field(30.0, alias="LLM_BACKOFF_CAP_S")

    # --- IA call logging (tuning de prompts) --- #
    ia_logging_enabled: bool = Field(False, alias="IA_LOGGING_ENABLED")
    ia_logging_dir: str = Field("logs/ia", alias="IA_LOGGING_DIR")

    # --- Catalogo de codigos de hora (auxhor) desde sigrid-api --- #
    # Si se cablean las tres SIGRID_API_*, sv2 lee el catalogo de codigos de
    # hora, filtra maquinaria/becario y lo inyecta en el prompt para que la IA
    # PROPONGA el codigo por categoria + normal/extra + incidencia.
    sigrid_api_base_url: str | None = Field(None, alias="SIGRID_API_BASE_URL")
    sigrid_api_function_key: str | None = Field(
        None, alias="SIGRID_API_FUNCTION_KEY"
    )
    sigrid_api_database: str | None = Field(None, alias="SIGRID_API_DATABASE")
    # F-038 (R14, DA4): (0, 200]; el balanceador de sigrid-api corta a 230 s.
    sigrid_api_timeout_s: float = Field(30.0, alias="SIGRID_API_TIMEOUT_S",
                                        gt=0, le=200)
    # F-038 (R2, R3; DA1 = B, DA2 = A): opcional, 1..500.000 (tope de la
    # instancia); el defecto es el MAX_ROWS_DEFECTO del cliente.
    sigrid_api_max_rows: int = Field(500_000, alias="SIGRID_API_MAX_ROWS",
                                     ge=1, le=500_000)
    auxhor_cache_ttl_s: int = Field(600, alias="AUXHOR_CACHE_TTL_S")
    # Palabras clave (en la descripcion/codigo) a EXCLUIR del catalogo antes
    # de mandarlo a la IA. CSV. Por defecto maquinaria + becario.
    auxhor_exclude_keywords: str = Field(
        "MAQUINARIA,MAQUINA,BECARIO,BECARIA", alias="AUXHOR_EXCLUDE_KEYWORDS"
    )
    auxhor_exclude_codes: str | None = Field(
        None, alias="AUXHOR_EXCLUDE_CODES"
    )

    # --- API + meta --- #
    api_host: str = Field("127.0.0.1", alias="API_HOST")
    api_port: int = Field(8010, alias="API_PORT")
    max_file_mb: int = Field(25, alias="MAX_FILE_MB")
    cors_allow_origins: str | None = Field(None, alias="CORS_ALLOW_ORIGINS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("1.0.0", alias="SERVICE_VERSION")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sigrid_catalog_enabled(self) -> bool:
        return bool(
            (self.sigrid_api_base_url or "").strip()
            and (self.sigrid_api_function_key or "").strip()
            and (self.sigrid_api_database or "").strip()
        )

    @property
    def auxhor_exclude_keywords_list(self) -> tuple[str, ...]:
        return tuple(
            k.strip() for k in (self.auxhor_exclude_keywords or "").split(",")
            if k.strip()
        )

    @property
    def auxhor_exclude_codes_list(self) -> tuple[str, ...]:
        return tuple(
            c.strip() for c in (self.auxhor_exclude_codes or "").split(",")
            if c.strip()
        )

    @property
    def proveedores_pagina_como_imagen(self) -> frozenset[str]:
        return frozenset(
            p.strip().lower()
            for p in (self.pagina_como_imagen_proveedores or "").split(",")
            if p.strip()
        )

    def _habilitado(self, provider: str) -> bool:
        return {
            "gemini": self.gemini_enabled,
            "claude": self.claude_enabled,
            "openai": self.openai_enabled,
        }.get(provider, False)

    def _clave_de(self, provider: str) -> str:
        """Clave del proveedor sin espacios ("" si falta)."""
        return ({
            "gemini": self.gemini_api_key,
            "claude": self.anthropic_api_key,
            "openai": self.openai_api_key,
        }.get(provider) or "").strip()

    @property
    def relectura_cabecera_motivo_inactiva(self) -> str | None:
        """F-058: por qué la relectura encendida no puede releer.

        ``None`` si está apagada o activa; si no, por orden,
        ``mismo_proveedor``, ``no_habilitado`` o ``sin_clave``.
        """
        if not self.relectura_cabecera_enabled:
            return None
        proveedor = self.relectura_cabecera_provider
        if proveedor == self.ia_provider:
            return "mismo_proveedor"
        if not self._habilitado(proveedor):
            return "no_habilitado"
        if not self._clave_de(proveedor):
            return "sin_clave"
        return None

    @property
    def relectura_cabecera_activa(self) -> str | None:
        """F-058: el proveedor de relectura si puede releer, o ``None``."""
        if (self.relectura_cabecera_enabled
                and self.relectura_cabecera_motivo_inactiva is None):
            return self.relectura_cabecera_provider
        return None

    @model_validator(mode="after")
    def _validar_proveedores_pagina_como_imagen(self) -> Settings:
        desconocidos = sorted(
            self.proveedores_pagina_como_imagen - set(PROVEEDORES_VALIDOS)
        )
        if desconocidos:
            raise ValueError(
                "PAGINA_COMO_IMAGEN_PROVEEDORES con proveedor(es) desconocido(s): "
                f"{', '.join(desconocidos)}. Válidos: {', '.join(PROVEEDORES_VALIDOS)}."
            )
        return self

    @model_validator(mode="after")
    def _ensure_provider_enabled_and_keyed(self) -> "Settings":
        """Solo el proveedor primario impide arrancar (la relectura, no)."""
        if not self._habilitado(self.ia_provider):
            raise ValueError(
                f"IA_PROVIDER='{self.ia_provider}' pero "
                f"ENABLE_{self.ia_provider.upper()} no esta a true."
            )
        if not self._clave_de(self.ia_provider):
            raise ValueError(
                f"IA_PROVIDER={self.ia_provider} requiere "
                f"{_VARIABLE_CLAVE[self.ia_provider]}."
            )
        return self
