# infrastructure/document/mime_pdf_extractor.py
"""Extractor de los PDF que viajan dentro de un correo adjunto (F-020).

El escaner de la empresa manda cada parte como un correo adjunto
(``itemAttachment`` con ``contentType`` ``message/rfc822``) que lleva el PDF
dentro. Graph devuelve ese correo como MIME RFC 822 en ``$value``; aqui se
recorre con la biblioteca estandar ``email`` y se sacan los PDF.

Reglas (requirements R7-R13 de F-020):

  - Recorrido en profundidad y en orden de aparicion: ``multipart/*`` se
    recorre parte a parte en el mismo nivel; ``message/rfc822`` se abre como
    el nivel siguiente. La raiz de ``$value`` es el nivel 1.
  - Recursion PROPIA, no ``Message.walk()``: ``walk`` baja a los
    ``message/rfc822`` sin decir en que nivel esta cada parte.
  - Tope de ``NIVEL_MAXIMO_ANIDAMIENTO`` niveles: abrir uno mas marca
    ``tope_excedido`` y no se baja (el pipeline no ingiere nada, D3).
  - PDF = parte no multipart ``application/pdf`` o con nombre ``.pdf``; sus
    bytes se toman ya decodificados. Lo demas se ignora (log DEBUG).
  - Puro: sin red, sin disco. Ningun log lleva bytes ni cabeceras (R24).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from email import message_from_bytes
from email.message import Message
from email.policy import default as POLITICA_EMAIL
from email.utils import parseaddr
from pathlib import PurePosixPath

from domain.models.email_models import (
    CorreoEmbebido,
    ExtraccionCorreoAdjunto,
    PdfEmbebido,
)
from domain.ports.extractor_correo_adjunto import CorreoAdjuntoIlegible

logger = logging.getLogger(__name__)

#: Niveles de correo que se abren como maximo (el adjunto de Graph es el 1).
NIVEL_MAXIMO_ANIDAMIENTO = 5

#: Tope de caracteres de cada cabecera de la cadena (R12).
_MAX_CARACTERES_CABECERA = 200

_TIPO_CORREO = "message/rfc822"
_TIPO_PDF = "application/pdf"


class _Acumulador:
    """Estado mutable de un recorrido (uno por llamada a ``extraer``)."""

    def __init__(self) -> None:
        self.pdfs: list[PdfEmbebido] = []
        self.tope_excedido = False
        self.partes_ignoradas = 0


class MimePdfExtractor:
    """Implementacion del puerto ``ExtractorCorreoAdjunto``."""

    def __init__(self, nivel_maximo: int = NIVEL_MAXIMO_ANIDAMIENTO) -> None:
        self._nivel_maximo = nivel_maximo

    @property
    def nivel_maximo(self) -> int:
        return self._nivel_maximo

    def extraer(
        self,
        *,
        raw_mime: bytes,
        nombre_adjunto: str | None,
    ) -> ExtraccionCorreoAdjunto:
        if not raw_mime:
            raise CorreoAdjuntoIlegible("el correo adjunto no trae bytes")
        acumulador = _Acumulador()
        try:
            raiz = message_from_bytes(raw_mime, policy=POLITICA_EMAIL)
            cadena = (self._cabeceras(raiz, 1, nombre_adjunto),)
            self._recorrer(raiz, 1, cadena, acumulador)
        except Exception as exc:
            # Solo el tipo de la excepcion: su texto podria llevar contenido.
            raise CorreoAdjuntoIlegible(
                f"no se pudo interpretar como mensaje RFC 822 "
                f"({type(exc).__name__})"
            ) from exc
        return ExtraccionCorreoAdjunto(
            pdfs=tuple(acumulador.pdfs),
            tope_excedido=acumulador.tope_excedido,
            partes_ignoradas=acumulador.partes_ignoradas,
        )

    # ----------------------------------------------------------- #
    # Recorrido.
    # ----------------------------------------------------------- #
    def _recorrer(
        self,
        parte: Message,
        nivel: int,
        cadena: tuple[CorreoEmbebido, ...],
        acumulador: _Acumulador,
    ) -> None:
        tipo = parte.get_content_type()

        if tipo == _TIPO_CORREO:
            interior = self._primer_mensaje(parte)
            if interior is None:
                self._ignorar(acumulador, tipo, nivel)
                return
            if nivel + 1 > self._nivel_maximo:
                acumulador.tope_excedido = True
                return
            eslabon = self._cabeceras(interior, nivel + 1,
                                      _nombre_fichero(parte))
            self._recorrer(interior, nivel + 1, cadena + (eslabon,),
                           acumulador)
            return

        if tipo.startswith("multipart/"):
            for subparte in parte.get_payload() or []:
                self._recorrer(subparte, nivel, cadena, acumulador)
            return

        nombre = _nombre_fichero(parte)
        es_pdf = tipo == _TIPO_PDF or (nombre or "").lower().endswith(".pdf")
        if not es_pdf:
            self._ignorar(acumulador, tipo, nivel)
            return

        datos = parte.get_payload(decode=True)
        if not datos:
            self._ignorar(acumulador, tipo, nivel)
            return

        orden = len(acumulador.pdfs) + 1
        acumulador.pdfs.append(PdfEmbebido(
            filename=_nombre_pdf(nombre, orden),
            file_bytes=datos,
            cadena=cadena,
        ))

    @staticmethod
    def _primer_mensaje(parte: Message) -> Message | None:
        contenido = parte.get_payload()
        if isinstance(contenido, list) and contenido:
            return contenido[0]
        return None

    @staticmethod
    def _ignorar(acumulador: _Acumulador, tipo: str, nivel: int) -> None:
        acumulador.partes_ignoradas += 1
        logger.debug("parte interior ignorada tipo=%s nivel=%d", tipo, nivel)

    # ----------------------------------------------------------- #
    # Cabeceras (R12): nunca una excepcion, siempre truncadas.
    # ----------------------------------------------------------- #
    @staticmethod
    def _cabeceras(
        mensaje: Message,
        nivel: int,
        nombre: str | None,
    ) -> CorreoEmbebido:
        remitente = _leer(lambda: mensaje.get("From"))
        direccion = parseaddr(remitente)[1] if remitente else ""
        return CorreoEmbebido(
            level=nivel,
            attachment_name=_truncar(nombre),
            subject=_leer(lambda: mensaje.get("Subject")),
            sender=_truncar(direccion) if direccion else None,
            date=_leer(lambda: mensaje.get("Date")),
        )


def _leer(obtener: Callable[[], object]) -> str | None:
    """Valor de una cabecera como texto truncado, o None si falta o falla."""
    try:
        valor = obtener()
        texto = "" if valor is None else str(valor)
        return _truncar(texto) if texto else None
    except Exception:
        return None


def _truncar(valor: str | None) -> str | None:
    return None if valor is None else valor[:_MAX_CARACTERES_CABECERA]


def _nombre_fichero(parte: Message) -> str | None:
    try:
        return parte.get_filename()
    except Exception:
        return None


def _nombre_pdf(nombre: str | None, orden: int) -> str:
    """Nombre base del fichero MIME (R11) o ``documento_<orden>.pdf``."""
    if nombre:
        base = PurePosixPath(nombre.replace("\\", "/")).name
        if base:
            return base
    return f"documento_{orden}.pdf"
