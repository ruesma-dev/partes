# domain/ports/conversor_pagina.py
"""F-059 · Puerto del conversor de página escaneada a imagen derecha."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.conversion_adjunto import ResultadoConversion
from domain.models.llm_attachment import LlmAttachment


class ConversorPaginaImagen(ABC):
    @abstractmethod
    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion:
        """Página escaneada -> imagen derecha. «No aplica» se devuelve; un
        fallo se lanza (lo recoge el pipeline)."""
        raise NotImplementedError
