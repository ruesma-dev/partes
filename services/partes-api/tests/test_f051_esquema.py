# tests/test_f051_esquema.py
"""F-051 · R9-R12: autocomprobacion por fila `numero_linea_horas` (DA1 = A).

El modelo de IA escribe, en cada fila de empleado, el "Nº" impreso en la
franja donde esta la cifra de horas. Va en el JSON Schema que recibe el
proveedor JUSTO despues de `numero_linea` y ANTES de las horas, para que el
modelo lo genere antes de escribir las cifras. sv2 no lo juzga: viaja a sv3
en el sobre y es sv3 quien decide si la lectura es dudosa.

Sin red ni modelo de IA: solo el esquema Pydantic.
"""
from __future__ import annotations

import pytest
from domain.models.parte_models import EmpleadoParte, ParteTrabajo
from pydantic import ValidationError


def _parte(empleados: list[dict]) -> dict:
    return {"cabecera": {}, "firma": {"firmado": False}, "empleados": empleados}


# --------------------------------- R9 ----------------------------------- #

def test_f051_r9_el_empleado_admite_numero_linea_horas_entero() -> None:
    emp = EmpleadoParte.model_validate({"numero_linea": 2, "numero_linea_horas": 2})
    assert emp.numero_linea_horas == 2


def test_f051_r9_el_empleado_admite_numero_linea_horas_null() -> None:
    emp = EmpleadoParte.model_validate({"numero_linea": 3, "numero_linea_horas": None})
    assert emp.numero_linea_horas is None


@pytest.mark.parametrize("valor", [0, 15, -1, 99])
def test_f051_r9_un_valor_fuera_de_rango_no_tumba_el_parseo(valor: int) -> None:
    """Sin cotas ge/le: un "Nº" mal leido no debe tirar el parte entero."""
    parte = ParteTrabajo.model_validate(
        _parte([{"numero_linea": 1, "numero_linea_horas": valor}]))
    assert parte.empleados[0].numero_linea_horas == valor


def test_f051_r9_el_campo_no_declara_cotas_en_el_json_schema() -> None:
    props = ParteTrabajo.model_json_schema()["$defs"]["EmpleadoParte"]["properties"]
    campo = props["numero_linea_horas"]
    texto = repr(campo)
    for cota in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
        assert cota not in texto


# --------------------------------- R10 ---------------------------------- #

def test_f051_r10_el_json_schema_lo_pone_tras_numero_linea_y_antes_de_las_horas() -> None:
    """Gemini genera en el orden del esquema: la autocomprobacion va primero."""
    props = ParteTrabajo.model_json_schema()["$defs"]["EmpleadoParte"]["properties"]
    claves = list(props)
    assert "numero_linea_horas" in claves
    i_linea = claves.index("numero_linea")
    i_auto = claves.index("numero_linea_horas")
    assert i_auto == i_linea + 1
    assert i_auto < claves.index("horas_ordinarias")
    assert i_auto < claves.index("horas_extraordinarias")


def test_f051_r10_el_json_schema_lo_declara_entero_o_null() -> None:
    props = ParteTrabajo.model_json_schema()["$defs"]["EmpleadoParte"]["properties"]
    tipos = {t.get("type") for t in props["numero_linea_horas"]["anyOf"]}
    assert tipos == {"integer", "null"}


# --------------------------------- R11 ---------------------------------- #

def test_f051_r11_una_respuesta_sin_el_campo_sigue_validando() -> None:
    parte = ParteTrabajo.model_validate(_parte([
        {"numero_linea": 1, "nombre": "Trabajador A", "horas_ordinarias": 8},
    ]))
    assert parte.empleados[0].numero_linea_horas is None
    assert parte.empleados[0].horas_ordinarias == 8


# --------------------------------- R12 ---------------------------------- #

def test_f051_r12_el_empleado_sigue_rechazando_campos_no_declarados() -> None:
    with pytest.raises(ValidationError):
        EmpleadoParte.model_validate({"numero_linea": 1, "fila_de_horas": 1})


# ----------------------- el dato llega a sv3 ---------------------------- #

def test_f051_el_campo_viaja_en_el_volcado_del_parte() -> None:
    parte = ParteTrabajo.model_validate(_parte([
        {"numero_linea": 2, "numero_linea_horas": 2, "horas_extraordinarias": 12},
        {"numero_linea": 3, "numero_linea_horas": None},
    ]))
    volcado = parte.model_dump()
    assert volcado["empleados"][0]["numero_linea_horas"] == 2
    assert "numero_linea_horas" in volcado["empleados"][1]
    assert volcado["empleados"][1]["numero_linea_horas"] is None
