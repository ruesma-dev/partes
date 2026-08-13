# config/settings.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuracion del servicio 1 de partes (email-partes-ingestor).

    Este sv1 actua como POLLER del buzon M365: cada POLL_INTERVAL_S lista
    los correos no leidos con adjuntos, descarga los PDF y los INGIERE en el
    pipeline asincrono de colas (sube a Blob 'input/{id}.pdf' y encola en
    'q-extraccion'). A partir de ahi, sv2 (extraccion IA) y sv3 (persistencia
    + casado Sigrid + SharePoint) procesan escalando por KEDA.

    El buzon actua como cola de pendientes: un email no leido con adjuntos
    esta pendiente de ingesta; tras ingerirlo se mueve a Procesados o, si
    falla la ingesta, a Errores.
    """

    # --------------------------------------------------------------- #
    # Buzon de Microsoft 365 via Microsoft Graph.
    # --------------------------------------------------------------- #
    mailbox_address: str = Field(..., alias="MAILBOX_ADDRESS")
    graph_key: str = Field(..., alias="GRAPH_KEY")
    graph_timeout_s: int = Field(60, alias="GRAPH_TIMEOUT_S")

    source_folder: str = Field("inbox", alias="SOURCE_FOLDER")
    folder_procesados: str = Field("Procesados", alias="FOLDER_PROCESADOS")
    folder_errores: str = Field("Errores", alias="FOLDER_ERRORES")

    # Procesados/Errores como SUBcarpetas de la carpeta origen (True) o
    # en la raiz del buzon (False).
    nest_folders_under_source: bool = Field(
        True, alias="NEST_FOLDERS_UNDER_SOURCE"
    )
    # Crear la carpeta origen si no existe (solo aplica cuando SOURCE_FOLDER
    # es un displayName, no un nombre conocido como 'inbox'). Por defecto
    # False: la origen debe preexistir y solo se verifica.
    create_source_if_missing: bool = Field(
        False, alias="CREATE_SOURCE_IF_MISSING"
    )

    poll_interval_s: int = Field(60, alias="POLL_INTERVAL_S")
    max_emails: int = Field(10, alias="MAX_EMAILS")
    max_attachment_mb: int = Field(25, alias="MAX_ATTACHMENT_MB")

    # --------------------------------------------------------------- #
    # Salida: pipeline asincrono de colas (Storage Queue + Blob).
    # Auth por managed identity (AZURE_CLIENT_ID en Container Apps; cadena
    # por defecto en local). Mismos nombres que sv2/sv3.
    # --------------------------------------------------------------- #
    colas_connection_string: str | None = Field(
        None, alias="COLAS_CONNECTION_STRING"
    )
    blobs_connection_string: str | None = Field(
        None, alias="BLOBS_CONNECTION_STRING"
    )
    colas_account_url: str | None = Field(None, alias="COLAS_ACCOUNT_URL")
    blobs_account_url: str | None = Field(None, alias="BLOBS_ACCOUNT_URL")
    azure_client_id: Optional[str] = Field(None, alias="AZURE_CLIENT_ID")

    cola_extraccion: str = Field("q-extraccion", alias="COLA_EXTRACCION")
    blob_input_container: str = Field("input", alias="BLOB_INPUT")

    # --------------------------------------------------------------- #
    # Logging y meta.
    # --------------------------------------------------------------- #
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("2.0.0", alias="SERVICE_VERSION")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )
