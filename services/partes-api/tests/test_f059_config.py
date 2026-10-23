# tests/test_f059_config.py
"""F-059 · R20–R22 y R24: configuración, cableado y ``detail`` de OpenAI.

- ``PAGINA_COMO_IMAGEN`` (encendido por defecto, DA3) y
  ``PAGINA_COMO_IMAGEN_PROVEEDORES`` (``openai`` por defecto, DA1); un nombre
  desconocido tumba el arranque.
- ``OPENAI_IMAGE_DETAIL`` (``high`` por defecto, DA4) viaja en toda
  ``input_image``; el PDF sigue siendo ``input_file`` sin ``detail``.
- ``build_app`` cablea el conversor solo con el interruptor encendido.
- El manifiesto de sv2 declara pypdf y Pillow.

Sin red: los clientes se construyen con una clave falsa y no se llaman. Los
SDK de IA, si no están instalados, se sustituyen por dobles
(``f059_sdk_falsos``): ``_build_input`` y ``build_app`` no los usan.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from tests.f059_sdk_falsos import instalar_si_faltan

# Los SDK de IA no están en el .venv de la raíz: dobles solo si faltan.
instalar_si_faltan()

from config.settings import Settings
from domain.models.llm_attachment import LlmAttachment
from infrastructure.document.pagina_pdf_imagen import (
    PaginaPdfImagenConversor,
)
from infrastructure.llm.openai_responses_client import (
    OpenAiResponsesVisionClient,
)
from interface_adapters.api.app import build_app

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_SERVICIO.parents[1]
REQUISITOS_SV2 = RAIZ_REPO / "infra" / "manifests" / "sv2" / "requirements.txt"
CLAVE_FALSA = "clave-falsa-de-test"
VARIABLES = (
    "ENABLE_GEMINI", "ENABLE_CLAUDE", "ENABLE_OPENAI", "IA_PROVIDER",
    "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "PAGINA_COMO_IMAGEN", "PAGINA_COMO_IMAGEN_PROVEEDORES",
    "OPENAI_IMAGE_DETAIL", "PROMPTS_YAML_PATH", "SIGRID_API_BASE_URL",
    "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE", "IA_LOGGING_ENABLED",
)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch) -> None:
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def _settings(**entorno) -> Settings:
    base = {"ENABLE_GEMINI": False, "ENABLE_OPENAI": True,
            "IA_PROVIDER": "openai", "OPENAI_API_KEY": CLAVE_FALSA,
            "PROMPTS_YAML_PATH": str(RAIZ_SERVICIO / "config" / "prompts.yaml")}
    base.update(entorno)
    return Settings(_env_file=None, **base)


# ----------------------------- R20 · defectos ---------------------------- #

def test_f059_r20_por_defecto_encendido_y_solo_openai() -> None:
    s = _settings()
    assert s.pagina_como_imagen is True
    assert s.proveedores_pagina_como_imagen == frozenset({"openai"})
    assert s.openai_image_detail == "high"


def test_f059_r20_el_interruptor_se_apaga_desde_el_entorno(monkeypatch) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN", "false")
    assert _settings().pagina_como_imagen is False


def test_f059_r20_la_lista_es_un_csv_sin_espacios_ni_mayusculas(monkeypatch) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN_PROVEEDORES", " openai, Gemini ,claude,")
    assert _settings().proveedores_pagina_como_imagen == frozenset(
        {"openai", "gemini", "claude"})


# ----------------------- R21 · nombres desconocidos ---------------------- #

@pytest.mark.parametrize("valor", ["openai,mistral", "mistral", "gpt"])
def test_f059_r21_un_nombre_desconocido_tumba_el_arranque(
    monkeypatch, valor: str
) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN_PROVEEDORES", valor)
    desconocido = next(v for v in valor.split(",") if v != "openai")
    with pytest.raises(ValueError, match=desconocido):
        _settings()


@pytest.mark.parametrize("valor", ["", " ", " , "])
def test_f059_r21_vacio_es_ningun_proveedor(monkeypatch, valor: str) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN_PROVEEDORES", valor)
    assert _settings().proveedores_pagina_como_imagen == frozenset()


# ----------------------- R22 · detail en input_image --------------------- #

def _bloque_adjunto(cliente: OpenAiResponsesVisionClient,
                    adjunto: LlmAttachment) -> dict:
    (mensaje,) = cliente._build_input(attachment=adjunto, user_text="t")
    return mensaje["content"][1]


IMAGEN = LlmAttachment(kind="image", filename="p.jpg", mime_type="image/jpeg",
                       data=b"\xff\xd8 jpeg")
PDF = LlmAttachment(kind="pdf", filename="p.pdf", mime_type="application/pdf",
                    data=b"%PDF-1.4")


@pytest.mark.parametrize("detalle", ["high", "low", "auto"])
def test_f059_r22_la_imagen_lleva_detail(detalle: str) -> None:
    cliente = OpenAiResponsesVisionClient(api_key=CLAVE_FALSA, image_detail=detalle)
    bloque = _bloque_adjunto(cliente, IMAGEN)
    assert bloque["type"] == "input_image"
    assert bloque["detail"] == detalle
    assert bloque["image_url"].startswith("data:image/jpeg;base64,")


@pytest.mark.parametrize("detalle", ["", None])
def test_f059_r22_sin_valor_no_manda_detail(detalle) -> None:
    cliente = OpenAiResponsesVisionClient(api_key=CLAVE_FALSA, image_detail=detalle)
    assert "detail" not in _bloque_adjunto(cliente, IMAGEN)


def test_f059_r22_por_defecto_el_cliente_no_manda_detail() -> None:
    """El defecto ``high`` vive en settings; el cliente sin él, como antes."""
    cliente = OpenAiResponsesVisionClient(api_key=CLAVE_FALSA)
    assert "detail" not in _bloque_adjunto(cliente, IMAGEN)


def test_f059_r22_el_pdf_sigue_siendo_input_file_sin_detail() -> None:
    cliente = OpenAiResponsesVisionClient(api_key=CLAVE_FALSA, image_detail="high")
    bloque = _bloque_adjunto(cliente, PDF)
    assert bloque["type"] == "input_file"
    assert "detail" not in bloque


# ----------------------- R20–R22 · cableado en app ----------------------- #

def _pipeline_y_cliente(settings: Settings):
    pipeline = build_app(settings).state.pipeline
    cliente = pipeline._service._providers_by_name["openai"].client
    return pipeline, cliente


def test_f059_r20_app_cablea_el_conversor_encendido() -> None:
    pipeline, cliente = _pipeline_y_cliente(_settings())
    assert isinstance(pipeline._conversor, PaginaPdfImagenConversor)
    assert pipeline._proveedores_imagen == frozenset({"openai"})
    assert cliente._image_detail == "high"


def test_f059_r20_app_sin_conversor_con_el_interruptor_apagado(monkeypatch) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN", "false")
    monkeypatch.setenv("OPENAI_IMAGE_DETAIL", "")
    pipeline, cliente = _pipeline_y_cliente(_settings())
    assert pipeline._conversor is None
    assert pipeline._proveedores_imagen == frozenset()
    assert cliente._image_detail == ""


def test_f059_r20_app_pasa_la_lista_configurada(monkeypatch) -> None:
    monkeypatch.setenv("PAGINA_COMO_IMAGEN_PROVEEDORES", "gemini,claude")
    pipeline, _ = _pipeline_y_cliente(_settings())
    assert isinstance(pipeline._conversor, PaginaPdfImagenConversor)
    assert pipeline._proveedores_imagen == frozenset({"gemini", "claude"})


# ----------------------- R24 · manifiesto de sv2 ------------------------- #

def test_f059_r24_requirements_de_sv2_declara_pypdf_y_pillow() -> None:
    lineas = [
        linea.strip().lower()
        for linea in REQUISITOS_SV2.read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.lstrip().startswith("#")
    ]
    assert any(linea.startswith("pypdf>=") for linea in lineas), lineas
    assert any(linea.startswith("pillow>=") for linea in lineas), lineas
