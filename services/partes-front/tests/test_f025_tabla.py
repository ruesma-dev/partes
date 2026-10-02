# tests/test_f025_tabla.py
"""F-025 · tabla versionada de clases de incidencia (R1-R3) y su arranque.

Sin red ni BBDD: se parsea el YAML versionado de verdad y diccionarios
construidos en el test. Los codigos de Sigrid son los del catalogo publico
de tipos de hora (`CI*`), no datos de personas.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from application.services.incidencias_horas import (
    CLASE_DIA_COMPLETO,
    CLASE_PARCIAL,
    LETRAS_LEYENDA,
    parsear_tabla,
)

RAIZ = Path(__file__).resolve().parents[1]
YAML_VERSIONADO = RAIZ / "config" / "incidencias.yaml"


def _datos_validos() -> dict:
    """Las siete letras con la clasificacion de DA2."""
    return {
        "V": {"sigrid": "CIV", "nombre": "Vacaciones", "clase": "dia_completo"},
        "B": {"sigrid": "CIE", "nombre": "Baja", "clase": "dia_completo"},
        "AT": {"sigrid": "CIA", "nombre": "Accidente", "clase": "parcial"},
        "FJ": {"sigrid": "CIP", "nombre": "Permiso", "clase": "parcial"},
        "F": {"sigrid": "CIF", "nombre": "Falta", "clase": "dia_completo"},
        "H": {"sigrid": "CIH", "nombre": "Huelga", "clase": "parcial"},
        "M": {"sigrid": "CIM", "nombre": "Maternidad", "clase": "dia_completo"},
    }


# ============================ R1 · la tabla ============================ #

def test_f025_r1_el_yaml_versionado_tiene_las_siete_letras_y_da2() -> None:
    tabla = parsear_tabla(yaml.safe_load(
        YAML_VERSIONADO.read_text(encoding="utf-8")))
    assert set(tabla.por_letra) == set(LETRAS_LEYENDA) == {
        "V", "B", "AT", "FJ", "F", "H", "M"}
    clases = {letra: c.clase for letra, c in tabla.por_letra.items()}
    assert clases == {"V": CLASE_DIA_COMPLETO, "B": CLASE_DIA_COMPLETO,
                      "M": CLASE_DIA_COMPLETO, "F": CLASE_DIA_COMPLETO,
                      "AT": CLASE_PARCIAL, "FJ": CLASE_PARCIAL,
                      "H": CLASE_PARCIAL}
    codigos = {letra: c.sigrid for letra, c in tabla.por_letra.items()}
    assert codigos == {"V": "CIV", "B": "CIE", "AT": "CIA", "FJ": "CIP",
                       "F": "CIF", "H": "CIH", "M": "CIM"}
    assert tabla.por_letra["H"].nombre.startswith("Huelga")
    assert tabla.por_letra["M"].nombre.startswith("Maternidad")
    assert all(c.letra == letra for letra, c in tabla.por_letra.items())


def test_f025_r1_indice_por_codigo_de_sigrid() -> None:
    tabla = parsear_tabla(_datos_validos())
    assert set(tabla.por_sigrid) == {"CIV", "CIE", "CIA", "CIP", "CIF",
                                     "CIH", "CIM"}
    assert tabla.por_sigrid["CIM"] is tabla.por_letra["M"]


def test_f025_r1_letras_y_codigos_se_normalizan() -> None:
    datos = _datos_validos()
    datos[" fj "] = dict(datos.pop("FJ"), sigrid=" cip ",
                         clase=" Parcial ")
    tabla = parsear_tabla(datos)
    assert tabla.por_letra["FJ"].sigrid == "CIP"
    assert tabla.por_letra["FJ"].clase == CLASE_PARCIAL
    assert tabla.por_sigrid["CIP"].letra == "FJ"


# ======================== R2 · sin valores en silencio ================== #

@pytest.mark.parametrize("datos", [None, [], "V: dia_completo", 7])
def test_f025_r2_no_es_un_mapa(datos) -> None:
    with pytest.raises(ValueError, match="mapa"):
        parsear_tabla(datos)


@pytest.mark.parametrize("letra", ["V", "M", "AT"])
def test_f025_r2_falta_una_letra(letra) -> None:
    datos = _datos_validos()
    del datos[letra]
    with pytest.raises(ValueError, match=f"faltan.*{letra}"):
        parsear_tabla(datos)


def test_f025_r2_clase_desconocida() -> None:
    datos = _datos_validos()
    datos["B"]["clase"] = "media_jornada"
    with pytest.raises(ValueError, match="B.*clase.*media_jornada"):
        parsear_tabla(datos)


@pytest.mark.parametrize("codigo", ["HE01", "", None, "XCI"])
def test_f025_r2_codigo_que_no_empieza_por_ci(codigo) -> None:
    datos = _datos_validos()
    datos["F"]["sigrid"] = codigo
    with pytest.raises(ValueError, match="F.*CI"):
        parsear_tabla(datos)


@pytest.mark.parametrize("entrada", ["dia_completo", None, ["CIV"]])
def test_f025_r2_entrada_que_no_es_un_mapa(entrada) -> None:
    datos = _datos_validos()
    datos["V"] = entrada
    with pytest.raises(ValueError, match="V"):
        parsear_tabla(datos)


@pytest.mark.parametrize("nombre", ["", "   ", None])
def test_f025_r2_entrada_sin_nombre(nombre) -> None:
    datos = _datos_validos()
    datos["H"]["nombre"] = nombre
    with pytest.raises(ValueError, match="H.*nombre"):
        parsear_tabla(datos)


def test_f025_r2_codigo_de_sigrid_repetido() -> None:
    datos = _datos_validos()
    datos["B"]["sigrid"] = "CIV"
    with pytest.raises(ValueError, match="CIV"):
        parsear_tabla(datos)


# ============================ R3 · clase_de ============================ #

def test_f025_r3_por_letra_sin_espacios_y_en_mayusculas() -> None:
    tabla = parsear_tabla(_datos_validos())
    assert tabla.clase_de("M", None).letra == "M"
    assert tabla.clase_de(" fj ", "HL01").letra == "FJ"
    assert tabla.clase_de("a t", None).letra == "AT"


def test_f025_r3_la_letra_manda_sobre_el_codigo() -> None:
    tabla = parsear_tabla(_datos_validos())
    assert tabla.clase_de("V", "CIM").letra == "V"


def test_f025_r3_sin_letra_conocida_sale_del_codigo_de_hora() -> None:
    tabla = parsear_tabla(_datos_validos())
    assert tabla.clase_de(None, "CIM").letra == "M"
    assert tabla.clase_de("X", " cia ").letra == "AT"
    assert tabla.clase_de("", "CIP").clase == CLASE_PARCIAL


@pytest.mark.parametrize("letra,codigo", [
    (None, "CIZ"), ("Z", "CIZ"), (None, None), ("", ""), ("X", "HL01")])
def test_f025_r3_sin_clase(letra, codigo) -> None:
    assert parsear_tabla(_datos_validos()).clase_de(letra, codigo) is None
