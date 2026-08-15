# config/settings.py
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuracion del servicio 4 (partes-portal).

    Portal de revision de partes de trabajo. Lee la BBDD 'partes'
    (compartida con sv3) y la presenta: una pagina con una linea por
    trabajador y, dentro, el detalle con una linea por registro horario.

    El CODIGO DE HORA (auxhor) se edita desde un desplegable poblado en
    vivo desde Sigrid (lookup de SOLO LECTURA), si SIGRID_API_* esta
    configurado. Si no, el desplegable queda vacio y se conserva lo que
    caso el sv3.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------ #
    # BBDD compartida (misma que sv3).
    # ------------------------------------------------------------ #
    pg_host: str = Field("localhost", alias="PG_HOST")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_db: str = Field("partes", alias="PG_DB")
    pg_user: str = Field("postgres", alias="PG_USER")
    pg_password: str = Field(..., alias="PG_PASSWORD")

    pg_admin_db: str = Field("postgres", alias="PG_ADMIN_DB")
    pg_admin_user: str = Field("postgres", alias="PG_ADMIN_USER")
    pg_admin_password: str = Field(..., alias="PG_ADMIN_PASSWORD")
    auto_create_database: bool = Field(True, alias="AUTO_CREATE_DATABASE")

    # ------------------------------------------------------------ #
    # Sigrid (solo lectura) — desplegable de tipos de hora (auxhor).
    # ------------------------------------------------------------ #
    sigrid_api_base_url: str | None = Field(None, alias="SIGRID_API_BASE_URL")
    sigrid_api_function_key: str | None = Field(
        None, alias="SIGRID_API_FUNCTION_KEY"
    )
    sigrid_api_database: str | None = Field(None, alias="SIGRID_API_DATABASE")
    sigrid_api_timeout_s: float = Field(30.0, alias="SIGRID_API_TIMEOUT_S")

    # ------------------------------------------------------------ #
    # partes-transfer (sv5) — registro de los partes APROBADOS en
    # Sigrid. sv4 NO escribe en Sigrid: delega en este servicio.
    # ------------------------------------------------------------ #
    transfer_base_url: str | None = Field(None, alias="TRANSFER_BASE_URL")
    transfer_timeout_s: float = Field(120.0, alias="TRANSFER_TIMEOUT_S")

    # ------------------------------------------------------------ #
    # Colas de aprobacion asincrona (F-002). TODAS opcionales: sin
    # ellas el portal registra por HTTP sincrono como hasta ahora
    # (R3), que es tambien el modo de trabajo en local sin Azurite.
    #   q-transfer         sv4 -> sv5 (peticion de registro)
    #   q-transfer-result  sv5 -> sv4 (veredicto por linea)
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
    cola_visibility_s: int = Field(600, alias="COLA_VISIBILITY_S")
    cola_max_dequeue: int = Field(5, alias="COLA_MAX_DEQUEUE")

    # ------------------------------------------------------------ #
    # Microsoft Graph — visor del PDF del parte (descarga desde
    # SharePoint el archivo subido por sv3). Solo lectura.
    # ------------------------------------------------------------ #
    graph_key: str | None = Field(None, alias="GRAPH_KEY")
    graph_timeout_s: int = Field(60, alias="GRAPH_TIMEOUT_S")
    # Drive de respaldo si el documento no tiene sharepoint_drive_id guardado.
    sharepoint_drive_id: str | None = Field(None, alias="SHAREPOINT_DRIVE_ID")

    # ------------------------------------------------------------ #
    # API + presentacion.
    # ------------------------------------------------------------ #
    api_host: str = Field("127.0.0.1", alias="API_HOST")
    api_port: int = Field(8014, alias="API_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("1.0.0", alias="SERVICE_VERSION")
    app_title: str = Field("Partes de Trabajo", alias="APP_TITLE")
    default_reviewer: str | None = Field(None, alias="DEFAULT_REVIEWER")
    # Jornada por defecto y umbral de CanDefecto (deben coincidir con sv3):
    # un CanDefecto <= candef_minimo_valido se considera NO informado en
    # Sigrid y la vista muestra la jornada por defecto marcada "asignado".
    jornada_por_defecto: float = Field(8.0, alias="JORNADA_POR_DEFECTO")
    candef_minimo_valido: float = Field(2.0, alias="CANDEF_MINIMO_VALIDO")

    # --- Festivos del calendario --- #
    # RESPALDO de los festivos: se usa cuando Sesame no esta configurado
    # (F-003 apagada) o no responde. No se retira hasta que sesame-api
    # este desplegado y rodado.
    holidays_enabled: bool = Field(True, alias="HOLIDAYS_ENABLED")
    holidays_subdiv: str = Field("MD", alias="HOLIDAYS_SUBDIV")
    # Festivos locales extra (CSV de 'YYYY-MM-DD').
    holidays_extra: str | None = Field(None, alias="HOLIDAYS_EXTRA")

    # ------------------------------------------------------------ #
    # sesame-api (F-003) — festivos REALES por trabajador y tipo de
    # jornada del contrato. Pasarela de solo lectura sobre Sesame HR,
    # con clave propia en la cabecera 'x-api-key'.
    #
    # OPCIONAL: sin las dos variables el portal usa el respaldo
    # 'holidays' de siempre y no hace ni una llamada (R7).
    # ------------------------------------------------------------ #
    sesame_api_base_url: str | None = Field(None, alias="SESAME_API_BASE_URL")
    sesame_api_key: str | None = Field(None, alias="SESAME_API_KEY")
    sesame_api_timeout_s: float = Field(10.0, alias="SESAME_API_TIMEOUT_S")
    # 6 h: los festivos de un ano no cambian casi nunca, y la cache es lo
    # que evita que un timeout puntual de Sesame bloquee una aprobacion.
    sesame_cache_ttl_s: int = Field(21600, alias="SESAME_CACHE_TTL_S")

    # ------------------------------------------------------------ #
    # Derivados.
    # ------------------------------------------------------------ #
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.pg_user}:{quote_plus(self.pg_password)}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def admin_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.pg_admin_user}:"
            f"{quote_plus(self.pg_admin_password)}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_admin_db}"
        )

    @property
    def sigrid_lookup_enabled(self) -> bool:
        return bool(
            (self.sigrid_api_base_url or "").strip()
            and (self.sigrid_api_function_key or "").strip()
            and (self.sigrid_api_database or "").strip()
        )

    @property
    def sesame_enabled(self) -> bool:
        """Hay pasarela de Sesame cableada (mismo patron que Sigrid).

        Mientras sea False, F-003 esta APAGADA: festivos del respaldo, ni
        bloqueos ni avisos, comportamiento identico al anterior.
        """
        return bool(
            (self.sesame_api_base_url or "").strip()
            and (self.sesame_api_key or "").strip()
        )

    @property
    def transfer_enabled(self) -> bool:
        return bool((self.transfer_base_url or "").strip())

    @property
    def transfer_queue_enabled(self) -> bool:
        """Hay cola configurada: la aprobacion puede ir en asincrono."""
        return bool((self.colas_connection_string or "").strip()
                    or (self.colas_account_url or "").strip())

    @property
    def preview_enabled(self) -> bool:
        # El visor del PDF necesita Graph (GRAPH_KEY). El drive/item se toman
        # del propio documento; SHAREPOINT_DRIVE_ID es solo respaldo.
        return bool((self.graph_key or "").strip())

    @property
    def holidays_extra_list(self) -> tuple[str, ...]:
        return tuple(
            x.strip() for x in (self.holidays_extra or "").split(",")
            if x.strip()
        )
