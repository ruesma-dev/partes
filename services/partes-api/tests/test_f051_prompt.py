# tests/test_f051_prompt.py
"""F-051 · R1-R7: el prompt `parte_trabajo_es` lee la tabla FILA A FILA.

Caso real que lo motiva (obra 0686, fin de semana, escaneo girado, tabla
casi vacia): el modelo subio cada cifra una fila. El prompt debe ordenar
asignar cada cifra a la franja en la que esta escrita, identificada por el
"Nº" y el DNI/nombre impresos, y pedir la autocomprobacion
`numero_linea_horas` (DA1 = A).

Sin red ni modelo de IA: se comprueban las palabras clave del YAML real
(`design.md` §6). El resto del prompt (R8) lo vigilan los tests de F-023,
que no se tocan, y el diff que revisa el reviewer.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"


def _norm(texto: str) -> str:
    return " ".join(texto.split()).lower()


@pytest.fixture(scope="module")
def prompt():
    return YamlPromptRepository(RUTA_PROMPTS).get("parte_trabajo_es")


@pytest.fixture(scope="module")
def punto3(prompt) -> str:
    """El punto 3 de `task` (EMPLEADOS), sin el 4 (INCIDENCIA) en adelante."""
    assert "3) EMPLEADOS" in prompt.task and "4) INCIDENCIA" in prompt.task
    return prompt.task.split("3) EMPLEADOS", 1)[1].split("4) INCIDENCIA", 1)[0]


@pytest.fixture(scope="module")
def bloque(punto3) -> str:
    """El bloque LECTURA FILA A FILA, del titulo a la vineta numero_linea."""
    assert "LECTURA FILA A FILA" in punto3, "falta el bloque LECTURA FILA A FILA"
    resto = punto3.split("LECTURA FILA A FILA", 1)[1]
    assert re.search(r"\n\s*- numero_linea:", resto), (
        "el bloque debe ir antes de la vineta numero_linea")
    return _norm(re.split(r"\n\s*- numero_linea:", resto, maxsplit=1)[0])


def _vineta(punto3: str, clave: str) -> str | None:
    return next(
        (_norm(b) for b in re.split(r"\n\s*- ", punto3)
         if b.startswith(f"{clave}:")),
        None,
    )


# --------------------------------- R1 ----------------------------------- #

def test_f051_r1_el_system_prohibe_la_fila_mas_cercana_y_la_de_arriba(prompt) -> None:
    system = _norm(prompt.system)
    assert "fila mas cercana" in system
    assert "de arriba" in system
    assert "nunca" in system


def test_f051_r1_el_system_identifica_la_fila_por_numero_y_dni(prompt) -> None:
    regla = next(
        (b for b in re.split(r"\n\s*- ", prompt.system)
         if "fila mas cercana" in _norm(b)),
        None,
    )
    assert regla is not None
    regla = _norm(regla)
    assert "nº" in regla and "dni" in regla


def test_f051_r1_el_bloque_cubre_todas_las_cifras_de_la_fila(bloque) -> None:
    assert '"nº"' in bloque
    assert "dni" in bloque
    assert "incidencia" in bloque
    assert "partidas" in bloque


# --------------------------------- R2 ----------------------------------- #

def test_f051_r2_recorrido_fila_a_fila_hasta_ord_y_extraord(bloque) -> None:
    assert "fila a fila" in bloque
    assert '"ord."' in bloque and '"extraord."' in bloque
    assert "solo lo que hay entre las dos lineas" in bloque


# --------------------------------- R3 ----------------------------------- #

def test_f051_r3_celda_vacia_es_null_y_no_se_mueven_cifras(bloque) -> None:
    assert "celda vacia = null" in bloque
    assert "vecina" in bloque
    assert "nunca rellenes" in bloque
    assert "muevas cifras" in bloque


def test_f051_r3_advierte_de_las_pocas_cifras_sueltas(bloque) -> None:
    assert "pocas cifras" in bloque
    assert "sin horas" in bloque


# --------------------------------- R4 ----------------------------------- #

def test_f051_r4_escaneos_girados_y_cifras_que_invaden_la_vecina(bloque) -> None:
    assert "girado" in bloque and "inclinado" in bloque
    assert "lineas de la tabla" in bloque
    assert "centro" in bloque


# --------------------------------- R5 ----------------------------------- #

def test_f051_r5_todas_las_filas_con_trabajador_aunque_no_tengan_horas(bloque) -> None:
    assert "todas las filas con trabajador" in bloque
    assert "horas a null" in bloque
    assert "orden del papel" in bloque


# --------------------------------- R6 ----------------------------------- #

def test_f051_r6_vineta_numero_linea_horas_en_el_punto_3(punto3) -> None:
    vineta = _vineta(punto3, "numero_linea_horas")
    assert vineta is not None, "falta la vineta numero_linea_horas"
    assert "cifra" in vineta and '"nº"' in vineta
    assert "null" in vineta
    assert "no lo copies" in vineta


def test_f051_r6_la_vineta_va_tras_numero_linea_y_antes_de_las_horas(punto3) -> None:
    pos = {
        clave: re.search(rf"\n\s*- {clave}:", punto3)
        for clave in ("numero_linea", "numero_linea_horas", "horas_ordinarias")
    }
    assert all(pos.values())
    assert (pos["numero_linea"].start() < pos["numero_linea_horas"].start()
            < pos["horas_ordinarias"].start())


# --------------------------------- R7 ----------------------------------- #

def test_f051_r7_el_schema_hint_lista_dni_y_numero_linea_horas(prompt) -> None:
    empleados = prompt.schema_hint.split('"empleados"', 1)[1].split("Reglas de tipo", 1)[0]
    assert '"dni"' in empleados
    assert '"numero_linea_horas"' in empleados
    assert empleados.index('"numero_linea"') < empleados.index('"numero_linea_horas"')
    assert empleados.index('"numero_linea_horas"') < empleados.index('"horas_ordinarias"')


def test_f051_r7_las_reglas_de_tipo_dicen_entero_o_null(prompt) -> None:
    reglas = _norm(prompt.schema_hint.split("Reglas de tipo", 1)[1])
    assert "numero_linea_horas es entero o null" in reglas
