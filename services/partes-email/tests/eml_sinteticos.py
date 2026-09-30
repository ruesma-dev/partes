# tests/eml_sinteticos.py
"""Correos RFC 822 sinteticos para la suite de sv1 (F-020).

Todo se construye en memoria: ningun `.eml` en disco, ninguna direccion,
nombre ni PDF reales. Las direcciones son `@example.com`.

  - `pdf_bytes(paginas)`: un PDF valido de N paginas en blanco (pypdf).
  - `Fichero`: un adjunto de fichero (PDF, imagen, texto...).
  - `correo(...)`: un `EmailMessage` con cuerpo de texto opcional y adjuntos;
    un adjunto que sea `EmailMessage` (o `Anidado`) se adjunta como parte
    `message/rfc822`.
  - `envolver(interior, niveles)`: anida `interior` dentro de `niveles`
    correos mas (cada uno lo lleva como `message/rfc822`).
  - `a_bytes(msg)`: los bytes RFC 822 que devolveria Graph en `$value`.
"""
from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import SMTP
from io import BytesIO

from pypdf import PdfWriter


def pdf_bytes(paginas: int = 1) -> bytes:
    """PDF valido con `paginas` paginas en blanco (A4)."""
    writer = PdfWriter()
    for _ in range(paginas):
        writer.add_blank_page(width=595, height=842)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@dataclass(frozen=True)
class Fichero:
    """Adjunto de fichero de un correo sintetico."""

    datos: bytes
    maintype: str = "application"
    subtype: str = "pdf"
    nombre: str | None = "parte.pdf"
    cte: str = "base64"


@dataclass(frozen=True)
class Anidado:
    """Correo adjuntado como parte `message/rfc822`, con nombre opcional."""

    mensaje: EmailMessage
    nombre: str | None = None


def fichero_pdf(nombre: str | None = "parte.pdf", paginas: int = 1,
                *, cte: str = "base64") -> Fichero:
    return Fichero(datos=pdf_bytes(paginas), nombre=nombre, cte=cte)


def fichero_imagen(nombre: str = "foto.png") -> Fichero:
    return Fichero(datos=b"\x89PNG\r\n\x1a\nFALSO", maintype="image",
                   subtype="png", nombre=nombre)


def fichero_texto(nombre: str = "nota.txt") -> Fichero:
    return Fichero(datos=b"texto de prueba", maintype="text",
                   subtype="plain", nombre=nombre)


def correo(
    *,
    subject: str | None = "Attached Image",
    sender: str | None = "escaner@example.com",
    date: str | None = "Wed, 30 Sep 2026 08:16:00 +0200",
    cuerpo: str | None = None,
    adjuntos: list[Fichero | EmailMessage | Anidado] | None = None,
) -> EmailMessage:
    """Un correo con los adjuntos dados en orden.

    Sin cuerpo y con un solo PDF reproduce la forma observada en la sonda
    (`multipart/mixed` -> `application/pdf`).
    """
    msg = EmailMessage()
    if subject is not None:
        msg["Subject"] = subject
    if sender is not None:
        msg["From"] = sender
    msg["To"] = "partes@example.com"
    if date is not None:
        msg["Date"] = date
    if cuerpo is not None:
        msg.set_content(cuerpo)
    for adjunto in adjuntos or []:
        if isinstance(adjunto, Fichero):
            kwargs = {"maintype": adjunto.maintype, "subtype": adjunto.subtype,
                      "cte": adjunto.cte}
            if adjunto.nombre is not None:
                kwargs["filename"] = adjunto.nombre
            msg.add_attachment(adjunto.datos, **kwargs)
        else:
            anidado = (adjunto if isinstance(adjunto, Anidado)
                       else Anidado(mensaje=adjunto))
            if anidado.nombre is not None:
                msg.add_attachment(anidado.mensaje, filename=anidado.nombre)
            else:
                msg.add_attachment(anidado.mensaje)
    return msg


def envolver(interior: EmailMessage, niveles: int) -> EmailMessage:
    """Mete `interior` dentro de `niveles` correos, del interior al exterior.

    `envolver(x, 0)` es `x`. El correo devuelto es el nivel 1 y `interior`
    queda en el nivel `niveles + 1`.
    """
    actual = interior
    for n in range(niveles, 0, -1):
        actual = correo(subject=f"Nivel {n}", sender=f"nivel{n}@example.com",
                        adjuntos=[Anidado(actual, nombre=f"nivel{n + 1}.eml")])
    return actual


def a_bytes(msg: EmailMessage) -> bytes:
    """Los bytes RFC 822 del correo (lo que devuelve Graph en `$value`)."""
    return msg.as_bytes(policy=SMTP)
