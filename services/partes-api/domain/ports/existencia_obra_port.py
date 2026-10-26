# domain/ports/existencia_obra_port.py
"""F-058 · Puerto de la consulta de existencia de una obra en Sigrid."""
from __future__ import annotations

from typing import Protocol


class ExistenciaObraPort(Protocol):
    def existe_obra(self, clave: str, *, timeout_s: float) -> bool:
        """``True`` si hay en Sigrid alguna obra con esa clave (de cualquier
        empresa, también de baja). Un fallo, la respuesta truncada o el tope
        de tiempo superado se lanzan (los recoge ``ComprobadorObra``)."""
        ...
