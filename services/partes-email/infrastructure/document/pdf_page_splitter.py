# infrastructure/document/pdf_page_splitter.py
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class PreparedDocument:
    filename: str
    mime_type: str
    file_bytes: bytes
    page_number: int
    page_count: int
    was_split: bool


class PdfPageSplitter:
    def split(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> List[PreparedDocument]:
        safe_filename = filename or "document.pdf"
        is_pdf = (
            (mime_type or "").lower() == "application/pdf"
            or safe_filename.lower().endswith(".pdf")
        )
        if not is_pdf:
            return [
                PreparedDocument(
                    filename=safe_filename,
                    mime_type=mime_type or "application/octet-stream",
                    file_bytes=file_bytes,
                    page_number=1,
                    page_count=1,
                    was_split=False,
                )
            ]

        reader = PdfReader(BytesIO(file_bytes))
        page_count = len(reader.pages)
        if page_count <= 1:
            return [
                PreparedDocument(
                    filename=safe_filename,
                    mime_type="application/pdf",
                    file_bytes=file_bytes,
                    page_number=1,
                    page_count=page_count or 1,
                    was_split=False,
                )
            ]

        stem = Path(safe_filename).stem or "document"
        suffix = Path(safe_filename).suffix or ".pdf"
        documents: List[PreparedDocument] = []
        digits = max(3, len(str(page_count)))

        for index, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            buffer = BytesIO()
            writer.write(buffer)
            page_filename = (
                f"{stem}__page_{index:0{digits}d}_of_{page_count:0{digits}d}"
                f"{suffix}"
            )
            documents.append(
                PreparedDocument(
                    filename=page_filename,
                    mime_type="application/pdf",
                    file_bytes=buffer.getvalue(),
                    page_number=index,
                    page_count=page_count,
                    was_split=True,
                )
            )

        return documents
