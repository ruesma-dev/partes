# config/settings.py
"""Configuracion de partes-transfer (sv5): registro de partes en Sigrid."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore",
        populate_by_name=True,
    )

    # --- sigrid-api (unico acceso a Sigrid) --- #
    sigrid_api_base_url: str = Field(..., alias="SIGRID_API_BASE_URL")
    sigrid_api_function_key: str = Field(..., alias="SIGRID_API_FUNCTION_KEY")
    # La ESCRITURA solo admite 'ruesma' (nunca la replica ruesma_rep).
    sigrid_api_database: str = Field("ruesma", alias="SIGRID_API_DATABASE")
    sigrid_empresa: int = Field(1, alias="SIGRID_EMPRESA")
    sigrid_api_timeout_s: float = Field(60.0, alias="SIGRID_API_TIMEOUT_S")
    # Tope de sentencias por batch de sigrid-api (MAX_STATEMENTS_PER_BATCH=20).
    sigrid_max_statements: int = Field(15, alias="SIGRID_MAX_STATEMENTS")

    # --- Modo PRUEBAS (OPCIONAL, por defecto DESACTIVADO) --- #
    # true  -> TODAS las escrituras se desvian a `obra_pruebas_cod`,
    #          ignorando la obra del parte, y se marcan en hmores.tex.
    # false -> comportamiento NORMAL: cada parte va a SU obra.
    obra_pruebas_forzar: bool = Field(False, alias="OBRA_PRUEBAS_FORZAR")
    obra_pruebas_cod: str = Field("0404", alias="OBRA_PRUEBAS_COD")
    # Marca en hmores.tex de las lineas escritas en modo pruebas.
    marca_pruebas: str = Field("PRUEBA-IA", alias="MARCA_PRUEBAS")

    # --- Constantes del modelo Sigrid (confirmadas con datos reales) --- #
    tip_parte_trabajo: int = Field(35, alias="TIP_PARTE_TRABAJO")
    est_parte_activo: int = Field(1, alias="EST_PARTE_ACTIVO")
    paso_pos: int = Field(64, alias="PASO_POS")

    # --- Servidor --- #
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8005, alias="API_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
