# tests/test_f020_contexto_pdf_directo.py
"""F-020 · R18: el contexto de un PDF DIRECTO no cambia.

Escrito contra `polling_pipeline.py` ANTES de modificarlo (T5): fija, con un
dict literal, el formato que sv1 genera hoy para un PDF adjunto como fichero.
Tras F-020 debe seguir saliendo identico, clave a clave y sin `embedded_in`.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from dobles import (
    CARPETA_PROCESADOS,
    BuzonFalso,
    SumideroFalso,
    adjunto,
    construir_pipeline,
    ejecutar,
    mensaje,
)
from eml_sinteticos import pdf_bytes
from pypdf import PdfReader


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def test_f020_r18_contexto_de_pdf_directo_multipagina_identico_al_actual():
    buzon = BuzonFalso()
    sumidero = SumideroFalso()
    datos = pdf_bytes(2)
    msg = mensaje("msg-1", subject="Partes semana 39",
                  sender="encargado@example.com")
    att = adjunto("att-1", name="partes.pdf", size=4321)
    buzon.anadir_mensaje(msg, [(att, datos)])

    ejecutar(construir_pipeline(buzon, sumidero))

    assert buzon.destino("msg-1") == CARPETA_PROCESADOS
    assert len(sumidero.encolados) == 2
    for n, encolado in enumerate(sumidero.encolados, start=1):
        nombre = f"partes__page_{n:03d}_of_002.pdf"
        assert encolado.filename == nombre
        assert encolado.mime_type == "application/pdf"
        assert len(PdfReader(BytesIO(encolado.file_bytes)).pages) == 1
        assert encolado.context == {
            "transport": {
                "document_id": encolado.document_id,
                "source": "email-poller",
            },
            "email": {
                "id": "msg-1",
                "subject": "Partes semana 39",
                "sender": "encargado@example.com",
                "receivedDateTime": "2026-09-30T06:16:00Z",
                "bodyPreview": "",
            },
            "attachment": {
                "id": "att-1",
                "name": "partes.pdf",
                "contentType": "application/pdf",
                "size": 4321,
                "sha256": _sha(datos),
                "page_number": n,
                "page_count": 2,
                "was_split": True,
            },
            "document": {
                "filename": nombre,
                "mime_type": "application/pdf",
                "sha256": _sha(encolado.file_bytes),
                "page_number": n,
                "page_count": 2,
                "was_split": True,
                "source_attachment_filename": "partes.pdf",
                "source_attachment_mime_type": "application/pdf",
                "source_attachment_sha256": _sha(datos),
            },
        }
        assert "embedded_in" not in encolado.context


def test_f020_r18_contexto_de_pdf_directo_de_una_pagina_identico_al_actual():
    buzon = BuzonFalso()
    sumidero = SumideroFalso()
    datos = pdf_bytes(1)
    msg = mensaje("msg-2")
    att = adjunto("att-9", name="uno.pdf", size=999)
    buzon.anadir_mensaje(msg, [(att, datos)])

    ejecutar(construir_pipeline(buzon, sumidero))

    assert buzon.destino("msg-2") == CARPETA_PROCESADOS
    [encolado] = sumidero.encolados
    assert encolado.filename == "uno.pdf"
    assert encolado.file_bytes == datos
    assert encolado.context["attachment"] == {
        "id": "att-9", "name": "uno.pdf", "contentType": "application/pdf",
        "size": 999, "sha256": _sha(datos), "page_number": 1,
        "page_count": 1, "was_split": False,
    }
    assert encolado.context["document"] == {
        "filename": "uno.pdf", "mime_type": "application/pdf",
        "sha256": _sha(datos), "page_number": 1, "page_count": 1,
        "was_split": False, "source_attachment_filename": "uno.pdf",
        "source_attachment_mime_type": "application/pdf",
        "source_attachment_sha256": _sha(datos),
    }
    assert set(encolado.context) == {"transport", "email", "attachment",
                                     "document"}
