# tests/test_f023_empresa_membrete.py
"""F-023 · R5: sv2 extrae la empresa impresa en el membrete del parte.

Es la unica fuente de la empresa del parte que no depende de Sigrid: el
membrete (o el logotipo) dice para quien se trabajo. sv2 solo lo COPIA tal
cual; traducirlo a una empresa de Sigrid es cosa de sv3 (R7).

Dos frentes, los dos sin red ni modelo de IA:

  - el ESQUEMA (`CabeceraParte` es `extra="forbid"`: sin el campo, una
    respuesta del modelo que lo trajera haria fallar el parseo entero), y
    el JSON Schema que se envia al proveedor, que se genera del modelo;
  - el PROMPT (`config/prompts.yaml`): la vineta de la cabecera y la clave
    en `schema_hint`. Nada mas del prompt cambia (DA12).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.models.parte_models import CabeceraParte, ParteTrabajo
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"


def _parte(cabecera: dict) -> dict:
    return {"cabecera": cabecera, "firma": {"firmado": False}, "empleados": []}


# ------------------------------- esquema -------------------------------- #

def test_f023_r5_la_cabecera_admite_la_empresa_del_membrete() -> None:
    cab = CabeceraParte.model_validate({"empresa_membrete": "PORSAN"})
    assert cab.empresa_membrete == "PORSAN"


def test_f023_r5_sin_membrete_la_empresa_es_null() -> None:
    assert CabeceraParte.model_validate({}).empresa_membrete is None
    assert CabeceraParte.model_validate(
        {"empresa_membrete": None}).empresa_membrete is None


def test_f023_r5_el_texto_se_guarda_tal_cual() -> None:
    """Tal cual: sin normalizar mayusculas, espacios ni signos."""
    texto = "Porsan e Hijos  Construcciones, S.L."
    parte = ParteTrabajo.model_validate(_parte({"empresa_membrete": texto}))
    assert parte.cabecera.empresa_membrete == texto


def test_f023_r5_la_cabecera_sigue_rechazando_campos_no_declarados() -> None:
    """El campo nuevo no abre la puerta a cualquier clave."""
    with pytest.raises(ValidationError):
        CabeceraParte.model_validate({"empresa": "PORSAN"})


def test_f023_r5_el_json_schema_del_proveedor_lleva_el_campo() -> None:
    """Gemini recibe `model_json_schema()` del modelo: ahi tiene que estar."""
    esquema = ParteTrabajo.model_json_schema()
    props = esquema["$defs"]["CabeceraParte"]["properties"]
    assert "empresa_membrete" in props


# -------------------------------- prompt -------------------------------- #

@pytest.fixture(scope="module")
def prompt():
    return YamlPromptRepository(RUTA_PROMPTS).get("parte_trabajo_es")


def test_f023_r5_el_prompt_pide_la_empresa_del_membrete(prompt) -> None:
    vineta = next(
        (bloque for bloque in re.split(r"\n\s*- ", prompt.task)
         if bloque.startswith("cabecera.empresa_membrete")),
        None,
    )
    assert vineta is not None, "falta la vineta de cabecera.empresa_membrete"
    texto = " ".join(vineta.split()).lower()
    assert "membrete" in texto and "logotipo" in texto
    assert "tal cual" in texto
    assert "null" in texto
    # Nunca se deduce de otros datos del parte.
    for fuente in ("obra", "encargado", "trabajadores"):
        assert fuente in texto


def test_f023_r5_la_vineta_va_en_el_bloque_de_cabecera(prompt) -> None:
    cabecera, firma = prompt.task.split("2) FIRMA", 1)
    assert "cabecera.empresa_membrete" in cabecera
    assert "empresa_membrete" not in firma


def test_f023_r5_el_schema_hint_lleva_la_clave_en_la_cabecera(prompt) -> None:
    bloque = prompt.schema_hint.split('"firma"', 1)[0]
    assert '"empresa_membrete"' in bloque
