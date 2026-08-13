# application/pipelines/polling_pipeline.py
"""Loop de polling del sv1 de partes (ingesta al pipeline de colas).

A diferencia de la version anterior (que llamaba sv2 y sv3 en cadena HTTP
sincrona), este sv1 desacopla: por cada documento logico sube el PDF a Blob
y encola un trabajo en 'q-extraccion'. A partir de ahi, sv2 (extraccion IA)
y sv3 (persistencia + casado Sigrid + SharePoint) procesan de forma
asincrona escalando por KEDA.

Flujo (run_once):
  1. Lista mensajes no leidos con adjuntos del SOURCE_FOLDER via Graph.
  2. Para cada mensaje:
     a. Lista adjuntos y filtra (no-inline, tipo file, bajo limite de MB).
     b. Para cada adjunto valido:
        i.   Descarga sus bytes via Graph.
        ii.  Si es PDF multipagina, lo divide en N documentos logicos de
             1 pagina (convencion: cada pagina es un parte).
        iii. Calcula sha256 del adjunto y de cada pagina.
        iv.  Genera un document_id de transporte (uuid) y lo INGIERE en el
             pipeline (Blob input/{id}.pdf + mensaje en q-extraccion).
     c. Mueve el email a Procesados si TODO se ingirio bien, o a Errores.

Importante: aqui 'Procesados' significa *ingerido en el pipeline*, no
*procesado end-to-end*. La extraccion/persistencia ocurren despues, de forma
asincrona; sus fallos persistentes van a la DLQ ('-poison'), no al buzon. El
buzon sigue actuando como cola de pendientes: un email no leido con adjuntos
esta pendiente de ingesta. Un email puede reprocesarse moviendolo de vuelta
al inbox y marcandolo como no leido.
"""
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone

from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.document_sink import DocumentSink
from domain.ports.mailbox_client import MailboxClient
from infrastructure.document.pdf_page_splitter import (
    PdfPageSplitter,
    PreparedDocument,
)

logger = logging.getLogger(__name__)


# Tipos de adjunto en Graph que NO son archivos reales a procesar.
_NON_FILE_ODATA_TYPES = frozenset({
    "#microsoft.graph.itemAttachment",
    "#microsoft.graph.referenceAttachment",
})

# Extensiones soportadas como documento logico (PDF + imagenes).
_SUPPORTED_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".webp")


class PollingPipeline:
    def __init__(
        self,
        *,
        mailbox: MailboxClient,
        sink: DocumentSink,
        pdf_splitter: PdfPageSplitter,
    ) -> None:
        self._mailbox = mailbox
        self._sink = sink
        self._splitter = pdf_splitter

    # ----------------------------------------------------------- #
    # Bucle infinito (lo invoca main.py).
    # ----------------------------------------------------------- #
    def run_forever(self, settings) -> None:
        # Resuelve la carpeta origen a su id (verificando que existe; la
        # crea si CREATE_SOURCE_IF_MISSING esta activo y es un displayName).
        source_folder_id = self._mailbox.resolve_folder_id(
            settings.mailbox_address,
            settings.source_folder,
            create_if_missing=settings.create_source_if_missing,
        )

        # Procesados/Errores: como SUBcarpetas de la origen si
        # NEST_FOLDERS_UNDER_SOURCE; si no, en la raiz del buzon.
        parent_id = (
            source_folder_id if settings.nest_folders_under_source else None
        )
        processed_folder_id = self._mailbox.ensure_folder(
            settings.mailbox_address,
            settings.folder_procesados,
            parent_folder_id=parent_id,
        )
        errors_folder_id = self._mailbox.ensure_folder(
            settings.mailbox_address,
            settings.folder_errores,
            parent_folder_id=parent_id,
        )

        logger.info(
            "Pre-checks OK. source_id=%s procesados_id=%s errores_id=%s "
            "(anidadas_en_origen=%s)",
            source_folder_id,
            processed_folder_id,
            errors_folder_id,
            settings.nest_folders_under_source,
        )

        max_attachment_bytes = settings.max_attachment_mb * 1024 * 1024

        while True:
            try:
                self.run_once(
                    mailbox=settings.mailbox_address,
                    source_folder=source_folder_id,
                    processed_folder_id=processed_folder_id,
                    errors_folder_id=errors_folder_id,
                    top=settings.max_emails,
                    max_attachment_bytes=max_attachment_bytes,
                )
            except Exception:
                logger.exception("error en run_once, continuando...")

            time.sleep(settings.poll_interval_s)

    # ----------------------------------------------------------- #
    # Una iteracion del polling (testeable, sin sleep).
    # ----------------------------------------------------------- #
    def run_once(
        self,
        *,
        mailbox: str,
        source_folder: str,
        processed_folder_id: str,
        errors_folder_id: str,
        top: int,
        max_attachment_bytes: int,
    ) -> None:
        messages = self._mailbox.list_unread_with_attachments(
            mailbox=mailbox,
            folder=source_folder,
            top=top,
        )
        if not messages:
            logger.debug("sin mensajes nuevos")
            return

        logger.info("polling: %d mensaje(s) con adjuntos", len(messages))
        for msg in messages:
            try:
                self._process_message(
                    msg=msg,
                    mailbox=mailbox,
                    processed_folder_id=processed_folder_id,
                    errors_folder_id=errors_folder_id,
                    max_attachment_bytes=max_attachment_bytes,
                )
            except Exception:
                logger.exception(
                    "msg=%s error inesperado, intentando mover a Errores",
                    msg.id,
                )
                self._safe_move(
                    mailbox=mailbox,
                    message_id=msg.id,
                    target_folder_id=errors_folder_id,
                )

    # ----------------------------------------------------------- #
    # Procesamiento de un mensaje individual.
    # ----------------------------------------------------------- #
    def _process_message(
        self,
        *,
        msg: EmailMessage,
        mailbox: str,
        processed_folder_id: str,
        errors_folder_id: str,
        max_attachment_bytes: int,
    ) -> None:
        logger.info(
            "msg=%s subject=%r sender=%s received=%s",
            msg.id,
            msg.subject,
            msg.sender,
            msg.received_datetime,
        )

        attachments = self._mailbox.list_attachments(
            mailbox=mailbox,
            message_id=msg.id,
        )
        eligible = [
            a for a in attachments if self._is_eligible(a, max_attachment_bytes)
        ]

        if not eligible:
            logger.warning(
                "msg=%s sin adjuntos elegibles (total=%d) -> Errores",
                msg.id,
                len(attachments),
            )
            self._safe_move(
                mailbox=mailbox,
                message_id=msg.id,
                target_folder_id=errors_folder_id,
            )
            return

        all_ok = True
        for att in eligible:
            ok = self._process_attachment(msg=msg, attachment=att, mailbox=mailbox)
            all_ok = all_ok and ok

        target = processed_folder_id if all_ok else errors_folder_id
        target_label = "Procesados" if all_ok else "Errores"
        self._safe_move(
            mailbox=mailbox,
            message_id=msg.id,
            target_folder_id=target,
        )
        logger.info("msg=%s movido a %s", msg.id, target_label)

    def _process_attachment(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
    ) -> bool:
        logger.info(
            "msg=%s att=%s name=%r type=%s size=%dB",
            msg.id,
            attachment.id,
            attachment.name,
            attachment.content_type,
            attachment.size,
        )

        try:
            file_bytes = self._mailbox.download_attachment_value(
                mailbox=mailbox,
                message_id=msg.id,
                attachment_id=attachment.id,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error descarga Graph: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return False

        attachment_sha256 = hashlib.sha256(file_bytes).hexdigest()

        try:
            prepared_pages = self._splitter.split(
                filename=attachment.name,
                mime_type=attachment.content_type,
                file_bytes=file_bytes,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error splitting PDF: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return False

        all_pages_ok = True
        for prepared in prepared_pages:
            page_ok = self._ingest_page(
                msg=msg,
                attachment=attachment,
                attachment_sha256=attachment_sha256,
                prepared=prepared,
            )
            all_pages_ok = all_pages_ok and page_ok

        return all_pages_ok

    def _ingest_page(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        attachment_sha256: str,
        prepared: PreparedDocument,
    ) -> bool:
        document_sha256 = hashlib.sha256(prepared.file_bytes).hexdigest()
        document_id = uuid.uuid4().hex

        logger.info(
            "Ingiriendo documento logico. file=%s page=%d/%d split=%s "
            "document_id=%s",
            prepared.filename,
            prepared.page_number,
            prepared.page_count,
            prepared.was_split,
            document_id,
        )

        context = self._build_context(
            msg=msg,
            attachment=attachment,
            attachment_sha256=attachment_sha256,
            prepared=prepared,
            document_sha256=document_sha256,
            document_id=document_id,
        )

        try:
            self._sink.enqueue(
                document_id=document_id,
                filename=prepared.filename,
                mime_type=prepared.mime_type,
                file_bytes=prepared.file_bytes,
                context=context,
            )
        except Exception as exc:
            logger.error(
                "msg=%s page=%d/%d ERROR ingesta (blob/cola): %s",
                msg.id,
                prepared.page_number,
                prepared.page_count,
                exc,
            )
            return False

        logger.info(
            "Documento logico INGERIDO. file=%s page=%d/%d document_id=%s",
            prepared.filename,
            prepared.page_number,
            prepared.page_count,
            document_id,
        )
        return True

    # ----------------------------------------------------------- #
    # Helpers.
    # ----------------------------------------------------------- #
    @staticmethod
    def _build_context(
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        attachment_sha256: str,
        prepared: PreparedDocument,
        document_sha256: str,
        document_id: str,
    ) -> dict:
        return {
            "transport": {
                "document_id": document_id,
                "source": "email-poller",
            },
            "email": {
                "id": msg.id,
                "subject": msg.subject,
                "sender": msg.sender,
                "receivedDateTime": msg.received_datetime,
                "bodyPreview": msg.body_preview,
            },
            "attachment": {
                "id": attachment.id,
                "name": attachment.name,
                "contentType": attachment.content_type,
                "size": attachment.size,
                "sha256": attachment_sha256,
                "page_number": prepared.page_number,
                "page_count": prepared.page_count,
                "was_split": prepared.was_split,
            },
            "document": {
                "filename": prepared.filename,
                "mime_type": prepared.mime_type,
                "sha256": document_sha256,
                "page_number": prepared.page_number,
                "page_count": prepared.page_count,
                "was_split": prepared.was_split,
                "source_attachment_filename": attachment.name,
                "source_attachment_mime_type": attachment.content_type,
                "source_attachment_sha256": attachment_sha256,
            },
        }

    @staticmethod
    def _is_eligible(att: EmailAttachment, max_bytes: int) -> bool:
        if att.is_inline:
            return False
        if att.odata_type and att.odata_type in _NON_FILE_ODATA_TYPES:
            return False
        name = (att.name or "").lower()
        ctype = (att.content_type or "").lower()
        is_supported = name.endswith(_SUPPORTED_SUFFIXES) or ctype in {
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
        }
        if not is_supported:
            logger.info(
                "att=%s name=%r tipo no soportado -> descartado",
                att.id,
                att.name,
            )
            return False
        if max_bytes > 0 and att.size > max_bytes:
            logger.warning(
                "att=%s name=%r tamano %dB excede limite %dB -> descartado",
                att.id,
                att.name,
                att.size,
                max_bytes,
            )
            return False
        return True

    def _safe_move(
        self,
        *,
        mailbox: str,
        message_id: str,
        target_folder_id: str,
    ) -> None:
        try:
            self._mailbox.move_message(
                mailbox=mailbox,
                message_id=message_id,
                destination_folder_id=target_folder_id,
            )
        except Exception:
            logger.exception(
                "msg=%s no se pudo mover al folder destino %s",
                message_id,
                target_folder_id,
            )


def _to_iso_utc(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)
