# domain/models/email_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmailMessage:
    id: str
    subject: str
    sender: Optional[str]
    received_datetime: Optional[str]
    body_preview: Optional[str] = None


@dataclass(frozen=True)
class EmailAttachment:
    id: str
    name: str
    content_type: str
    size: int
    is_inline: bool
    odata_type: Optional[str] = None


# --------------------------------------------------------------------- #
# F-020: correos adjuntos (message/rfc822) abiertos hasta el PDF.
# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class CorreoEmbebido:
    """Un correo de la cadena que lleva hasta un PDF interior.

    ``level`` 1 es el correo adjunto descargado de Graph; cada
    ``message/rfc822`` interior suma un nivel. Las cabeceras llegan ya
    leidas de forma defensiva y truncadas (R12).
    """

    level: int
    attachment_name: Optional[str]
    subject: Optional[str]
    sender: Optional[str]
    date: Optional[str]

    def to_context(self) -> dict:
        """Elemento de ``embedded_in`` del contexto (design §5)."""
        return {
            "level": self.level,
            "attachment_name": self.attachment_name,
            "subject": self.subject,
            "sender": self.sender,
            "date": self.date,
        }


@dataclass(frozen=True)
class PdfEmbebido:
    """PDF hallado dentro de un correo adjunto, con sus bytes decodificados."""

    filename: str
    file_bytes: bytes
    cadena: tuple[CorreoEmbebido, ...]


@dataclass(frozen=True)
class ExtraccionCorreoAdjunto:
    """Resultado de recorrer un correo adjunto.

    ``pdfs`` va en orden de aparicion (R7). Con ``tope_excedido`` el
    pipeline no ingiere nada de este correo adjunto (R10, D3).
    ``partes_ignoradas`` es solo para el log.
    """

    pdfs: tuple[PdfEmbebido, ...]
    tope_excedido: bool
    partes_ignoradas: int
