# domain/ports/document_sink.py
"""Puerto de salida del sv1: ingesta de un documento logico al pipeline.

El sv1 (poller del buzon) deja de hablar con sv2/sv3 por HTTP. Su unica
responsabilidad de salida es *ingerir* cada documento logico (una pagina =
un parte) en el pipeline asincrono de colas. La implementacion concreta
(Blob + Storage Queue) vive en infrastructure; el pipeline depende solo de
este contrato.
"""
from __future__ import annotations

from typing import Protocol


class DocumentSink(Protocol):
    def enqueue(
        self,
        *,
        document_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        context: dict,
    ) -> None:
        """Ingiere un documento logico en el pipeline.

        Sube el PDF al almacenamiento de hand-off y encola el trabajo para
        el extractor (sv2). Debe ser idempotente respecto al document_id:
        re-ingerir el mismo id sobreescribe el blob y vuelve a encolar.
        """
        ...
