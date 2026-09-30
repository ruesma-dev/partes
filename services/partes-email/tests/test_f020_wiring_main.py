# tests/test_f020_wiring_main.py
"""F-020 · R25: `main.py` construye el extractor MIME y lo inyecta.

`main.main()` se ejecuta con `Settings`, Graph, colas, blob y el propio
`PollingPipeline` sustituidos por dobles: ni `.env`, ni red, ni bucle.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import ClassVar

import main as modulo_main
from infrastructure.document.mime_pdf_extractor import MimePdfExtractor
from infrastructure.document.pdf_page_splitter import PdfPageSplitter


class PipelineEspia:
    """Sustituye a `PollingPipeline`: guarda con que se construyo."""

    construcciones: ClassVar[list[dict]] = []

    def __init__(self, **kwargs) -> None:
        PipelineEspia.construcciones.append(kwargs)
        self.arrancado_con = None

    def run_forever(self, settings) -> None:
        self.arrancado_con = settings


class _Nada:
    def __init__(self, *args, **kwargs) -> None:
        pass


class _ClienteStorageFalso:
    def asegurar_colas(self, nombres) -> None:
        pass

    def asegurar_contenedores(self, nombres) -> None:
        pass


def _settings_falsos() -> SimpleNamespace:
    return SimpleNamespace(
        log_dir="logs", log_level="INFO",
        mailbox_address="partes@example.com", poll_interval_s=60,
        source_folder="inbox", blobs_account_url="https://blob.example",
        colas_account_url="https://cola.example",
        cola_extraccion="q-extraccion", blob_input_container="input",
        graph_key="no-es-una-clave", graph_timeout_s=5,
        colas_connection_string=None, blobs_connection_string=None,
    )


def test_f020_r25_main_inyecta_el_extractor_mime_en_el_pipeline(monkeypatch):
    PipelineEspia.construcciones = []
    monkeypatch.setattr(modulo_main, "Settings", _settings_falsos)
    monkeypatch.setattr(modulo_main, "configure_logging", lambda *a: None)
    monkeypatch.setattr(modulo_main, "GraphTokenProvider", _Nada)
    monkeypatch.setattr(modulo_main, "GraphMailClient", _Nada)
    monkeypatch.setattr(modulo_main, "construir_cola_cliente",
                        lambda **k: _ClienteStorageFalso())
    monkeypatch.setattr(modulo_main, "construir_blob_cliente",
                        lambda **k: _ClienteStorageFalso())
    monkeypatch.setattr(modulo_main, "BlobQueueSink", _Nada)
    monkeypatch.setattr(modulo_main, "PollingPipeline", PipelineEspia)

    assert modulo_main.main() == 0

    [kwargs] = PipelineEspia.construcciones
    assert isinstance(kwargs["extractor_correo"], MimePdfExtractor)
    assert kwargs["extractor_correo"].nivel_maximo == 5
    assert isinstance(kwargs["pdf_splitter"], PdfPageSplitter)
    assert set(kwargs) == {"mailbox", "sink", "pdf_splitter",
                           "extractor_correo"}


def test_f020_r25_el_pipeline_no_instancia_el_extractor_por_su_cuenta():
    import ast
    from pathlib import Path

    ruta = (Path(__file__).resolve().parents[1] / "application"
            / "pipelines" / "polling_pipeline.py")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
    modulos = {n.module for n in ast.walk(arbol)
               if isinstance(n, ast.ImportFrom)}

    assert "MimePdfExtractor" not in nombres
    assert "infrastructure.document.mime_pdf_extractor" not in modulos
