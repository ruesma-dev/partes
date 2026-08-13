# config/settings.py
"""Configuracion de partes-transfer (sv5): registro de partes en Sigrid."""
from __future__ import annotations

from pydantic import Field, field_validator
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

    # ------------------------------------------------------------ #
    # Storage: cola de aprobacion asincrona (F-002). TODAS opcionales:
    # sin ellas sv5 arranca como siempre, solo con su API HTTP, y sv4
    # cae al registro sincrono (R3).
    # ------------------------------------------------------------ #
    colas_connection_string: str | None = Field(
        None, alias="COLAS_CONNECTION_STRING")      # local / Azurite
    colas_account_url: str | None = Field(None, alias="COLAS_ACCOUNT_URL")
    blobs_connection_string: str | None = Field(
        None, alias="BLOBS_CONNECTION_STRING")
    blobs_account_url: str | None = Field(None, alias="BLOBS_ACCOUNT_URL")

    cola_transfer: str = Field("q-transfer", alias="COLA_TRANSFER")
    cola_transfer_result: str = Field("q-transfer-result",
                                      alias="COLA_TRANSFER_RESULT")
    blob_transfer: str = Field("transfer", alias="BLOB_TRANSFER")

    # Con N workers esperando el lock de escritura, un mensaje puede
    # quedar invisible casi todo este tiempo mientras espera turno. Con
    # TRANSFER_WORKERS=3 y escrituras de segundos sobra; si se subiera
    # mucho el pool, hay que subir el visibility en proporcion.
    cola_visibility_s: int = Field(600, alias="COLA_VISIBILITY_S")
    cola_max_dequeue: int = Field(5, alias="COLA_MAX_DEQUEUE")

    # Hilos consumidores de q-transfer. Solapan la fase de PREPARACION;
    # la de escritura sigue serializada por el lock (R18/R19).
    transfer_workers: int = Field(3, alias="TRANSFER_WORKERS")

    @field_validator("transfer_workers")
    @classmethod
    def _al_menos_un_worker(cls, valor: int) -> int:
        """0 o negativo dejaria la cola sin consumir en silencio."""
        return max(1, int(valor))

    @property
    def storage_habilitado(self) -> bool:
        """Hay cola configurada (nube o Azurite)."""
        return bool((self.colas_connection_string or "").strip()
                    or (self.colas_account_url or "").strip())
