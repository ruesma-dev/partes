# domain/ports/persistence_client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PersistenceClient(ABC):
    @abstractmethod
    def persist(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        extraction_envelope: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError
