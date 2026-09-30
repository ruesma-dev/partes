# tests/dobles.py
"""Dobles de la suite de sv1 (F-020). Ni red, ni Graph, ni Blob, ni colas.

  - `BuzonFalso`: implementa el puerto `MailboxClient` en memoria. Sirve
    adjuntos y `$value` por id, puede fallar la descarga de los ids que se
    le digan y REGISTRA cada llamada (R6: ninguna llamada a Graph adicional).
  - `SumideroFalso`: implementa `DocumentSink`; guarda lo encolado y puede
    fallar en la N-esima llamada.
  - `construir_pipeline` / `ejecutar`: la unica forma en que los tests montan
    y lanzan el pipeline, para que un cambio de constructor toque solo esto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from application.pipelines.polling_pipeline import PollingPipeline
from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.extractor_correo_adjunto import ExtractorCorreoAdjunto
from domain.ports.mailbox_client import MailboxClient
from infrastructure.document.mime_pdf_extractor import MimePdfExtractor
from infrastructure.document.pdf_page_splitter import PdfPageSplitter

BUZON = "partes@example.com"
CARPETA_ORIGEN = "origen-id"
CARPETA_PROCESADOS = "procesados-id"
CARPETA_ERRORES = "errores-id"
MAX_MB = 25

ODATA_FILE = "#microsoft.graph.fileAttachment"
ODATA_ITEM = "#microsoft.graph.itemAttachment"
ODATA_REFERENCE = "#microsoft.graph.referenceAttachment"


class ErrorGraphFalso(Exception):
    """Fallo simulado de Graph en una descarga."""


class BuzonFalso(MailboxClient):
    def __init__(self) -> None:
        self.mensajes: list[EmailMessage] = []
        self.adjuntos: dict[str, list[EmailAttachment]] = {}
        self.valores: dict[str, bytes] = {}
        self.fallo_descarga: set[str] = set()
        self.llamadas: list[tuple] = []
        self.movidos: list[tuple[str, str]] = []

    # --- preparacion ---------------------------------------------------- #
    def anadir_mensaje(self, msg: EmailMessage,
                       adjuntos: list[tuple[EmailAttachment, bytes | None]]
                       ) -> None:
        """Registra un mensaje con sus adjuntos y los bytes de su `$value`."""
        self.mensajes.append(msg)
        self.adjuntos[msg.id] = [att for att, _ in adjuntos]
        for att, valor in adjuntos:
            if valor is not None:
                self.valores[att.id] = valor

    # --- puerto --------------------------------------------------------- #
    def assert_folder_accessible(self, mailbox: str, folder: str) -> None:
        self.llamadas.append(("assert_folder_accessible", folder))

    def resolve_folder_id(self, mailbox: str, folder: str,
                          create_if_missing: bool = False) -> str:
        self.llamadas.append(("resolve_folder_id", folder))
        return folder

    def ensure_folder(self, mailbox: str, display_name: str,
                      parent_folder_id: str | None = None) -> str:
        self.llamadas.append(("ensure_folder", display_name))
        return display_name

    def list_unread_with_attachments(self, mailbox: str, folder: str,
                                     top: int) -> list[EmailMessage]:
        self.llamadas.append(("list_unread_with_attachments", folder))
        return list(self.mensajes)

    def list_attachments(self, mailbox: str,
                         message_id: str) -> list[EmailAttachment]:
        self.llamadas.append(("list_attachments", message_id))
        return list(self.adjuntos.get(message_id, []))

    def download_attachment_value(self, mailbox: str, message_id: str,
                                  attachment_id: str) -> bytes:
        self.llamadas.append(("download_attachment_value", message_id,
                              attachment_id))
        if attachment_id in self.fallo_descarga:
            raise ErrorGraphFalso(f"fallo simulado att={attachment_id}")
        return self.valores[attachment_id]

    def move_message(self, mailbox: str, message_id: str,
                     destination_folder_id: str) -> None:
        self.llamadas.append(("move_message", message_id,
                              destination_folder_id))
        self.movidos.append((message_id, destination_folder_id))

    # --- consultas de los tests ----------------------------------------- #
    def destino(self, message_id: str) -> str | None:
        destinos = [d for m, d in self.movidos if m == message_id]
        return destinos[-1] if destinos else None


@dataclass
class Encolado:
    document_id: str
    filename: str
    mime_type: str
    file_bytes: bytes
    context: dict


@dataclass
class SumideroFalso:
    """`DocumentSink` en memoria; `fallar_en` es 1-based (None = nunca)."""

    fallar_en: int | None = None
    encolados: list[Encolado] = field(default_factory=list)
    llamadas: int = 0

    def enqueue(self, *, document_id: str, filename: str, mime_type: str,
                file_bytes: bytes, context: dict) -> None:
        self.llamadas += 1
        if self.fallar_en is not None and self.llamadas == self.fallar_en:
            raise RuntimeError("fallo simulado de blob/cola")
        self.encolados.append(Encolado(document_id, filename, mime_type,
                                       file_bytes, context))


def mensaje(id: str = "msg-1", *, subject: str = "Parte escaneado",
            sender: str = "escaner@example.com") -> EmailMessage:
    return EmailMessage(id=id, subject=subject, sender=sender,
                        received_datetime="2026-09-30T06:16:00Z",
                        body_preview="")


def adjunto(id: str, *, name: str = "parte.pdf",
            content_type: str = "application/pdf", size: int = 1000,
            is_inline: bool = False,
            odata_type: str | None = ODATA_FILE) -> EmailAttachment:
    return EmailAttachment(id=id, name=name, content_type=content_type,
                           size=size, is_inline=is_inline,
                           odata_type=odata_type)


def construir_pipeline(buzon: BuzonFalso, sumidero: SumideroFalso, *,
                       extractor: ExtractorCorreoAdjunto | None = None
                       ) -> PollingPipeline:
    """Pipeline con el troceador y (salvo que se pase otro) el extractor
    MIME REALES."""
    return PollingPipeline(
        mailbox=buzon, sink=sumidero, pdf_splitter=PdfPageSplitter(),
        extractor_correo=(MimePdfExtractor() if extractor is None
                          else extractor))


def ejecutar(pipeline: PollingPipeline, *,
             max_bytes: int | None = None) -> None:
    """Una pasada de polling; el limite por defecto es `MAX_MB` megas."""
    pipeline.run_once(
        mailbox=BUZON,
        source_folder=CARPETA_ORIGEN,
        processed_folder_id=CARPETA_PROCESADOS,
        errors_folder_id=CARPETA_ERRORES,
        top=10,
        max_attachment_bytes=(MAX_MB * 1024 * 1024 if max_bytes is None
                              else max_bytes),
    )
