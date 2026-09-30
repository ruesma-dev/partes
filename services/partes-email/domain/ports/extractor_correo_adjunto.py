# domain/ports/extractor_correo_adjunto.py
"""Puerto: abrir un correo adjunto (RFC 822) y sacar los PDF de su interior.

El pipeline depende de este contrato; la implementacion (recorrido MIME con
la biblioteca estandar) vive en ``infrastructure/document/``.
"""
from __future__ import annotations

from typing import Optional, Protocol

from domain.models.email_models import ExtraccionCorreoAdjunto


class CorreoAdjuntoIlegible(Exception):
    """Los bytes descargados no se pueden interpretar como mensaje RFC 822."""


class ExtractorCorreoAdjunto(Protocol):
    def extraer(
        self,
        *,
        raw_mime: bytes,
        nombre_adjunto: Optional[str],
    ) -> ExtraccionCorreoAdjunto:
        """Recorre el mensaje RFC 822 (nivel 1) y devuelve sus PDF.

        ``nombre_adjunto`` es el ``name`` de Graph del correo adjunto; va al
        primer elemento de la cadena. Lanza ``CorreoAdjuntoIlegible`` si los
        bytes no se pueden interpretar como mensaje.
        """
        ...
