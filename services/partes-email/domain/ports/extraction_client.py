# domain/ports/extraction_client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ExtractionClient(ABC):
    @abstractmethod
    def extract(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> Dict[str, Any]:
        raise NotImplementedError
