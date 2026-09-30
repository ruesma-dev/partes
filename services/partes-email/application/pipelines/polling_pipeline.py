# application/pipelines/polling_pipeline.py
"""Loop de polling del sv1 de partes (ingesta al pipeline de colas).

A diferencia de la version anterior (que llamaba sv2 y sv3 en cadena HTTP
sincrona), este sv1 desacopla: por cada documento logico sube el PDF a Blob
y encola un trabajo en 'q-extraccion'. A partir de ahi, sv2 (extraccion IA)
y sv3 (persistencia + casado Sigrid + SharePoint) procesan de forma
asincrona escalando por KEDA.

Flujo (run_once):
  1. Lista mensajes no leidos con adjuntos del SOURCE_FOLDER via Graph.
  2. Para cada mensaje, recorre sus adjuntos UNA vez y en el orden de Graph.
     Cada uno se clasifica (siempre no-inline y bajo el limite de MB):
     a. Correo adjunto (F-020): ``contentType`` ``message/rfc822`` (item o
        fileAttachment, no referenceAttachment). Se descarga su ``$value``
        (el MIME RFC 822) y el extractor inyectado saca los PDF de dentro,
        abriendo hasta 5 niveles de correos anidados. Si se pasa del tope,
        no se ingiere nada de ese correo adjunto. Cada PDF interior sigue el
        camino de un PDF directo y su contexto lleva ``embedded_in``.
     b. Fichero (PDF o imagen): se descarga como siempre.
     Por cada PDF (directo o interior):
        i.   Si es multipagina, lo divide en N documentos logicos de
             1 pagina (convencion: cada pagina es un parte).
        ii.  Calcula sha256 del PDF y de cada pagina.
        iii. Genera un document_id de transporte (uuid) y lo INGIERE en el
             pipeline (Blob input/{id}.pdf + mensaje en q-extraccion).
     c. Mueve el email a Procesados si no fallo nada (descarga, extraccion,
        ingesta, tope de niveles) y se ingirio al menos un documento; si no,
        a Errores. Un correo adjunto sin PDF solo avisa (WARNING).

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
from typing import NamedTuple

from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.document_sink import DocumentSink
from domain.ports.extractor_correo_adjunto import (
    CorreoAdjuntoIlegible,
    ExtractorCorreoAdjunto,
)
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

# Un referenceAttachment es un enlace (OneDrive/SharePoint): nunca se abre.
_ODATA_REFERENCE = "#microsoft.graph.referenceAttachment"

# contentType de Graph de un correo adjunto (F-020).
_CONTENT_TYPE_CORREO = "message/rfc822"

_MIME_PDF = "application/pdf"

# Extensiones soportadas como documento logico (PDF + imagenes).
_SUPPORTED_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".webp")


class _ResultadoAdjunto(NamedTuple):
    """Balance de un adjunto: si todo fue bien y cuantos documentos entraron."""

    ok: bool
    documentos: int


class PollingPipeline:
    def __init__(
        self,
        *,
        mailbox: MailboxClient,
        sink: DocumentSink,
        pdf_splitter: PdfPageSplitter,
        extractor_correo: ExtractorCorreoAdjunto,
    ) -> None:
        self._mailbox = mailbox
        self._sink = sink
        self._splitter = pdf_splitter
        self._extractor_correo = extractor_correo

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

        # Una sola pasada, en el orden de Graph (R19): cada adjunto se
        # clasifica primero como correo adjunto y, si no, como fichero.
        resultados: list[_ResultadoAdjunto] = []
        for att in attachments:
            if self._es_correo_adjunto(att, max_attachment_bytes):
                resultados.append(self._process_correo_adjunto(
                    msg=msg,
                    attachment=att,
                    mailbox=mailbox,
                    max_attachment_bytes=max_attachment_bytes,
                ))
            elif _es_tipo_correo(att):
                # Correo adjunto descartado (inline, enlace o tamano): ya
                # registrado; no es un fichero que evaluar.
                continue
            elif self._is_eligible(att, max_attachment_bytes):
                resultados.append(self._process_attachment(
                    msg=msg,
                    attachment=att,
                    mailbox=mailbox,
                ))

        if not resultados:
            logger.warning(
                "msg=%s sin adjuntos elegibles: ni PDF/imagen directos ni "
                "correos adjuntos (total=%d) -> Errores",
                msg.id,
                len(attachments),
            )
            self._safe_move(
                mailbox=mailbox,
                message_id=msg.id,
                target_folder_id=errors_folder_id,
            )
            return

        # R20: Procesados sii nada fallo y entro al menos un documento.
        documentos = sum(r.documentos for r in resultados)
        all_ok = all(r.ok for r in resultados) and documentos >= 1
        target = processed_folder_id if all_ok else errors_folder_id
        target_label = "Procesados" if all_ok else "Errores"
        self._safe_move(
            mailbox=mailbox,
            message_id=msg.id,
            target_folder_id=target,
        )
        logger.info(
            "msg=%s movido a %s (adjuntos=%d documentos=%d)",
            msg.id,
            target_label,
            len(resultados),
            documentos,
        )

    def _process_attachment(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
    ) -> _ResultadoAdjunto:
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
            return _ResultadoAdjunto(ok=False, documentos=0)

        return self._ingerir_pdf(
            msg=msg,
            attachment=attachment,
            nombre=attachment.name,
            content_type=attachment.content_type,
            size=attachment.size,
            file_bytes=file_bytes,
            embedded_in=None,
        )

    def _process_correo_adjunto(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
        max_attachment_bytes: int,
    ) -> _ResultadoAdjunto:
        """Abre un correo adjunto e ingiere los PDF de su interior (F-020)."""
        logger.info(
            "msg=%s att=%s correo adjunto name=%r type=%s size=%dB",
            msg.id,
            attachment.id,
            attachment.name,
            attachment.content_type,
            attachment.size,
        )

        try:
            raw_mime = self._mailbox.download_attachment_value(
                mailbox=mailbox,
                message_id=msg.id,
                attachment_id=attachment.id,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error descarga Graph del correo adjunto: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return _ResultadoAdjunto(ok=False, documentos=0)

        try:
            extraccion = self._extractor_correo.extraer(
                raw_mime=raw_mime,
                nombre_adjunto=attachment.name,
            )
        except CorreoAdjuntoIlegible as exc:
            logger.error(
                "msg=%s att=%s correo adjunto ilegible: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return _ResultadoAdjunto(ok=False, documentos=0)

        if extraccion.tope_excedido:
            # D3: todo o nada. Ni los PDF hallados en niveles permitidos.
            logger.error(
                "msg=%s att=%s correo adjunto con mas de %d niveles de "
                "correos anidados -> no se ingiere nada de el",
                msg.id,
                attachment.id,
                self._extractor_correo.nivel_maximo,
            )
            return _ResultadoAdjunto(ok=False, documentos=0)

        pdfs = []
        for pdf in extraccion.pdfs:
            if max_attachment_bytes > 0 and (
                len(pdf.file_bytes) > max_attachment_bytes
            ):
                logger.warning(
                    "msg=%s att=%s pdf interior %r tamano %dB excede limite "
                    "%dB -> descartado",
                    msg.id,
                    attachment.id,
                    pdf.filename,
                    len(pdf.file_bytes),
                    max_attachment_bytes,
                )
                continue
            pdfs.append(pdf)

        if not pdfs:
            # R21 (D2): no es un fallo; el destino lo decide el resto.
            logger.warning(
                "msg=%s att=%s correo adjunto sin ningun PDF valido "
                "(partes ignoradas=%d)",
                msg.id,
                attachment.id,
                extraccion.partes_ignoradas,
            )
            return _ResultadoAdjunto(ok=True, documentos=0)

        logger.info(
            "msg=%s att=%s correo adjunto con %d PDF interior(es) "
            "(partes ignoradas=%d)",
            msg.id,
            attachment.id,
            len(pdfs),
            extraccion.partes_ignoradas,
        )
        resultados = [
            self._ingerir_pdf(
                msg=msg,
                attachment=attachment,
                nombre=pdf.filename,
                content_type=_MIME_PDF,
                size=len(pdf.file_bytes),
                file_bytes=pdf.file_bytes,
                embedded_in=[c.to_context() for c in pdf.cadena],
            )
            for pdf in pdfs
        ]
        return _ResultadoAdjunto(
            ok=all(r.ok for r in resultados),
            documentos=sum(r.documentos for r in resultados),
        )

    def _ingerir_pdf(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        nombre: str,
        content_type: str,
        size: int,
        file_bytes: bytes,
        embedded_in: list[dict] | None,
    ) -> _ResultadoAdjunto:
        """Trocea por paginas e ingiere cada una (PDF directo o interior)."""
        attachment_sha256 = hashlib.sha256(file_bytes).hexdigest()

        try:
            prepared_pages = self._splitter.split(
                filename=nombre,
                mime_type=content_type,
                file_bytes=file_bytes,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s name=%r error splitting PDF: %s",
                msg.id,
                attachment.id,
                nombre,
                exc,
            )
            return _ResultadoAdjunto(ok=False, documentos=0)

        ingeridas = 0
        for prepared in prepared_pages:
            if self._ingest_page(
                msg=msg,
                attachment=attachment,
                nombre=nombre,
                content_type=content_type,
                size=size,
                attachment_sha256=attachment_sha256,
                prepared=prepared,
                embedded_in=embedded_in,
            ):
                ingeridas += 1

        return _ResultadoAdjunto(
            ok=ingeridas == len(prepared_pages),
            documentos=ingeridas,
        )

    def _ingest_page(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        nombre: str,
        content_type: str,
        size: int,
        attachment_sha256: str,
        prepared: PreparedDocument,
        embedded_in: list[dict] | None,
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
            nombre=nombre,
            content_type=content_type,
            size=size,
            attachment_sha256=attachment_sha256,
            prepared=prepared,
            document_sha256=document_sha256,
            document_id=document_id,
            embedded_in=embedded_in,
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
        nombre: str,
        content_type: str,
        size: int,
        attachment_sha256: str,
        prepared: PreparedDocument,
        document_sha256: str,
        document_id: str,
        embedded_in: list[dict] | None,
    ) -> dict:
        """Contexto del documento logico.

        ``nombre``/``content_type``/``size`` son los del PDF que se trocea:
        el adjunto de Graph en un PDF directo, el PDF interior en un correo
        adjunto (``attachment.id`` es siempre el id de Graph). Con
        ``embedded_in=None`` (PDF directo) el dict es el de antes de F-020.
        """
        context = {
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
                "name": nombre,
                "contentType": content_type,
                "size": size,
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
                "source_attachment_filename": nombre,
                "source_attachment_mime_type": content_type,
                "source_attachment_sha256": attachment_sha256,
            },
        }
        if embedded_in is not None:
            context["embedded_in"] = embedded_in
        return context

    @staticmethod
    def _es_correo_adjunto(att: EmailAttachment, max_bytes: int) -> bool:
        """R1, R2, R4: correo adjunto que se abre (no inline, no enlace,
        bajo el limite de tamano)."""
        if att.is_inline or not _es_tipo_correo(att):
            return False
        if att.odata_type == _ODATA_REFERENCE:
            logger.info(
                "att=%s name=%r referenceAttachment (enlace) -> descartado",
                att.id,
                att.name,
            )
            return False
        if max_bytes > 0 and att.size > max_bytes:
            logger.warning(
                "att=%s name=%r correo adjunto de tamano %dB excede limite "
                "%dB -> descartado",
                att.id,
                att.name,
                att.size,
                max_bytes,
            )
            return False
        return True

    @staticmethod
    def _is_eligible(att: EmailAttachment, max_bytes: int) -> bool:
        if att.is_inline:
            return False
        if att.odata_type and att.odata_type in _NON_FILE_ODATA_TYPES:
            logger.info(
                "att=%s name=%r type=%s %s no es un fichero -> descartado",
                att.id,
                att.name,
                att.content_type,
                att.odata_type,
            )
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


def _es_tipo_correo(att: EmailAttachment) -> bool:
    """contentType de Graph de correo adjunto (sin distinguir mayusculas)."""
    return (att.content_type or "").lower() == _CONTENT_TYPE_CORREO
