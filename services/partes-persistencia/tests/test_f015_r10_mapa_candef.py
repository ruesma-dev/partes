# tests/test_f015_r10_mapa_candef.py
"""R10 · la jornada SEMANAL se deriva del candef por un mapa configurable.

El mapa (`JORNADA_SEMANAL_POR_CANDEF`, por defecto `8:40,9:42`) es lo
unico que sabe que un recurso de candef 9 hace 42 h a la semana y no 45.
Dos propiedades que sostienen el resto de la feature:

  - un candef VALIDO pero fuera del mapa cae a jornada PLANA (`5 x c`),
    que es exactamente el comportamiento anterior a F-015: nadie empeora
    por no estar en el mapa;
  - una cadena mal formada revienta al PARSEAR (en el cableado), nunca en
    caliente: un mapa invalido en produccion cambiaria el reparto de
    horas en silencio.

Sin red, sin BBDD: `parsear_mapa_semanal` y `jornada_semanal_de` son
funciones puras.
"""
from __future__ import annotations

import pytest
from application.services.jornada_resolver import (
    jornada_semanal_de,
    parsear_mapa_semanal,
)


# ---------------------------- el parseo --------------------------------- #

def test_f015_r10_mapa_por_defecto_se_parsea() -> None:
    assert parsear_mapa_semanal("8:40,9:42") == {8.0: 40.0, 9.0: 42.0}


def test_f015_r10_mapa_tolera_espacios_y_decimales() -> None:
    assert parsear_mapa_semanal(" 8 : 40 , 7.5:37.5 ") == {
        8.0: 40.0, 7.5: 37.5}


def test_f015_r10_mapa_de_un_solo_par() -> None:
    assert parsear_mapa_semanal("9:42") == {9.0: 42.0}


@pytest.mark.parametrize("texto", [
    "",             # cadena vacia
    "   ",
    "8:40,9",       # par sin ':'
    "x:40",         # clave no numerica
    "8:cuarenta",   # valor no numerico
    "8:40,8:41",    # clave repetida
    "8:40,,9:42",   # par vacio
    "0:40",         # candef fuera de rango
    "8:0",          # semanal fuera de rango
    "8:200",        # mas de 24*7
    "8:40:9",       # tres campos
])
def test_f015_r10_mapa_mal_formado_es_error(texto: str) -> None:
    """ValueError al PARSEAR: el cableado lo convierte en fallo de arranque."""
    with pytest.raises(ValueError):
        parsear_mapa_semanal(texto)


def test_f015_r10_el_error_dice_que_cadena_fallo() -> None:
    with pytest.raises(ValueError) as exc:
        parsear_mapa_semanal("8:40,8:41")
    assert "8" in str(exc.value)


# ------------------------- la jornada semanal --------------------------- #

MAPA = {8.0: 40.0, 9.0: 42.0}


@pytest.mark.parametrize("candef, semanal, origen", [
    (8.0, 40.0, "mapa"),
    (9.0, 42.0, "mapa"),
    (10.0, 50.0, "plana"),    # valido pero fuera del mapa -> 5 x c
    (7.0, 35.0, "plana"),
])
def test_f015_r10_jornada_semanal_del_mapa(candef, semanal, origen) -> None:
    assert jornada_semanal_de(candef, mapa=MAPA) == (semanal, origen)


def test_f015_r10_un_mapa_ampliado_saca_el_candef_de_la_jornada_plana() -> None:
    """Con `8:40,9:42,10:48`, el candef 10 deja de ser 'plana'."""
    mapa = parsear_mapa_semanal("8:40,9:42,10:48")
    assert jornada_semanal_de(10.0, mapa=mapa) == (48.0, "mapa")


def test_f015_r10_mapa_vacio_deja_todo_en_jornada_plana() -> None:
    assert jornada_semanal_de(9.0, mapa={}) == (45.0, "plana")
