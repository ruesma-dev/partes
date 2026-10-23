# domain/models/conversion_adjunto.py
"""F-059 · Resultado de convertir una página escaneada en imagen derecha.

Dominio puro, sin dependencias: lo produce el conversor
(``domain/ports/conversor_pagina.py``) y lo lee el pipeline para decidir qué
adjunto manda a la IA y qué traza deja en ``meta.adjunto_ia``.
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.models.llm_attachment import LlmAttachment

# --- Valores de ``meta.adjunto_ia.conversion`` --- #
CONVERTIDA = "convertida"
NO_APLICA = "no_aplica"
ERROR = "error"
APAGADA = "apagada"

# --- Motivos cerrados de «no aplica» del conversor (R6–R10) --- #
MOTIVO_VARIAS_PAGINAS = "varias_paginas"
MOTIVO_CONTENIDO_NO_ES_UNA_IMAGEN = "contenido_no_es_una_imagen"
MOTIVO_IMAGEN_NO_JPEG = "imagen_no_jpeg"
MOTIVO_COLOR_NO_SOPORTADO = "color_no_soportado"
MOTIVO_IMAGEN_NO_CUBRE_PAGINA = "imagen_no_cubre_pagina"
MOTIVO_GIRO_NO_VALIDO = "giro_no_valido"

# --- Motivos que pone el pipeline (no el conversor) --- #
MOTIVO_INTERRUPTOR = "interruptor"
MOTIVO_PROVEEDOR_FUERA_DE_LISTA = "proveedor_fuera_de_lista"
MOTIVO_NO_ES_PDF = "no_es_pdf"


@dataclass(frozen=True)
class ResultadoConversion:
    """Imagen derecha (``adjunto``) o «no aplica» (``adjunto=None``)."""

    adjunto: LlmAttachment | None
    motivo: str
    giro_grados: int | None = None
    ancho_px: int | None = None
    alto_px: int | None = None
