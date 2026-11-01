# tests/test_f058_prompt.py
"""F-058 · R21–R23: el punto 1 del prompt avisa de la cabecera.

Seis páginas de escaneos desplazados salieron con la cabecera entera a
``null`` aunque la tabla se leyó. El punto ``1) CABECERA`` de
``parte_trabajo_es`` empieza ahora con un párrafo que dice que TODA página
tiene una cabecera encima de la tabla «PERSONAL», qué sale de ella (obra,
día, mes y año, membrete y el resto), que se busque aunque el escaneo salga
desplazado, que una cabecera entera a ``null`` con trabajadores es casi
siempre no haberla localizado y que nunca se invente un valor; y la viñeta
``cabecera.fecha`` dice qué hacer con día, mes y año en casillas separadas
(DA9, ``design.md`` §5).

Sin red ni modelo de IA: palabras clave del YAML real, como F-051. El resto
del prompt (R23) lo vigilan los tests de F-023 y F-051, que no se tocan.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"
TITULO_PUNTO_1 = "1) CABECERA (datos del dia/obra):"


def _norm(texto: str) -> str:
    return " ".join(texto.split()).lower()


@pytest.fixture(scope="module")
def prompt():
    return YamlPromptRepository(RUTA_PROMPTS).get("parte_trabajo_es")


@pytest.fixture(scope="module")
def punto1(prompt) -> str:
    """El punto 1 de `task` (CABECERA), sin el 2 (FIRMA) en adelante."""
    assert TITULO_PUNTO_1 in prompt.task and "2) FIRMA" in prompt.task
    return prompt.task.split(TITULO_PUNTO_1, 1)[1].split("2) FIRMA", 1)[0]


@pytest.fixture(scope="module")
def parrafo(punto1) -> str:
    """Lo que va entre el título del punto 1 y la viñeta `cabecera.fecha`."""
    assert re.search(r"\n\s*- cabecera\.fecha:", punto1)
    return _norm(re.split(r"\n\s*- cabecera\.fecha:", punto1, maxsplit=1)[0])


@pytest.fixture(scope="module")
def vineta_fecha(punto1) -> str:
    resto = re.split(r"\n\s*- cabecera\.fecha:", punto1, maxsplit=1)[1]
    return _norm(re.split(r"\n\s*- cabecera\.obra_numero:", resto,
                          maxsplit=1)[0])


# --------------------------------- R21 ----------------------------------- #

def test_f058_r21_el_parrafo_va_antes_de_la_vineta_de_fecha(parrafo) -> None:
    assert len(parrafo) > 200, "falta el párrafo de cabecera del punto 1"


def test_f058_r21_toda_pagina_tiene_cabecera_sobre_la_tabla_personal(
    parrafo,
) -> None:
    assert "toda pagina" in parrafo
    assert "cabecera" in parrafo
    assert '"personal"' in parrafo


@pytest.mark.parametrize("clave", ["nº obra", "dia", "mes", "año", "membrete"])
def test_f058_r21_nombra_lo_que_sale_de_la_cabecera(parrafo, clave: str) -> None:
    assert clave in parrafo


def test_f058_r21_buscarla_aunque_el_escaneo_salga_desplazado(parrafo) -> None:
    assert "desplazado" in parrafo
    assert "girado" in parrafo


def test_f058_r21_cabecera_entera_a_null_con_trabajadores(parrafo) -> None:
    assert "null" in parrafo
    assert "trabajadores" in parrafo
    assert "no la has localizado" in parrafo


def test_f058_r21_nunca_inventes_un_valor(parrafo) -> None:
    assert "nunca inventes" in parrafo


# --------------------------------- R22 ----------------------------------- #

def test_f058_r22_la_fecha_en_casillas_separadas_se_copia_junta(
    vineta_fecha,
) -> None:
    assert "casillas separadas" in vineta_fecha
    assert "dia/mes/año" in vineta_fecha
    # Lo que ya decía la viñeta sigue (R23).
    assert "copiada tal cual" in vineta_fecha
    assert "no la conviertas" in vineta_fecha


# --------------------------------- R23 ----------------------------------- #

def test_f058_r23_el_resto_del_punto_1_sigue(punto1) -> None:
    for vineta in ("cabecera.obra_numero:", "cabecera.obra_nombre:",
                   "cabecera.encargado_nombre:", "cabecera.jefe_obra_nombre:",
                   "cabecera.empresa_membrete:"):
        assert vineta in punto1
