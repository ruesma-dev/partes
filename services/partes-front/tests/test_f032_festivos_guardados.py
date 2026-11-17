# tests/test_f032_festivos_guardados.py
"""F-032 · R42: la cascada de lectura y el formato de `festivos_json`.

Modulo puro gemelo (sv3 y sv4, DA20): este fichero existe igual en los dos
servicios para que la campana de mutacion juzgue cada copia con la suite de
su servicio; el guardian de la raiz (`tests/test_f032_festivos_guardados_
gemelos.py`) compara las dos.
"""
from __future__ import annotations

import json

import pytest

from application.services.festivos_guardados import (
    FUENTE_SESAME,
    FUENTE_SIN_FILA,
    FilaFestivos,
    a_json,
    del_ano,
    elegir,
    fila_de,
)


def _fila(dni="12345678Z", ano=2026, festivos=None):
    return FilaFestivos(dni_norm=dni, ano=ano,
                        festivos=festivos or {"2026-03-19": "San Jose"},
                        leido_en_utc="2026-11-17T10:00:00Z")


# ------------------------------- elegir --------------------------------- #

def test_f032_r42_elegir_dni_con_fila_es_sesame():
    fila = _fila()
    pedidos = []

    def leer(dni, ano):
        pedidos.append((dni, ano))
        return fila

    assert elegir("12345678Z", 2026, leer) == (fila, FUENTE_SESAME)
    assert pedidos == [("12345678Z", 2026)]


def test_f032_r42_elegir_dni_sin_fila_es_sin_fila():
    assert elegir("12345678Z", 2026, lambda d, a: None) == (
        None, FUENTE_SIN_FILA)


@pytest.mark.parametrize("dni", ["", None])
def test_f032_r42_elegir_sin_dni_no_llama_a_leer(dni):
    def leer(dni, ano):
        raise AssertionError("sin DNI no se lee la tabla")

    assert elegir(dni, 2026, leer) == (None, FUENTE_SIN_FILA)


def test_f032_r42_elegir_propaga_el_fallo_de_lectura():
    """La lectura fallida la decide el llamante (respaldo + WARNING)."""
    def leer(dni, ano):
        raise RuntimeError("bbdd caida")

    with pytest.raises(RuntimeError):
        elegir("12345678Z", 2026, leer)


def test_f032_r42_fuentes():
    assert (FUENTE_SESAME, FUENTE_SIN_FILA) == ("sesame", "sin_fila")


# ------------------------------- del_ano -------------------------------- #

def test_f032_r42_del_ano_solo_dias_del_ano_y_validos():
    pares = [
        ("2026-01-01", "Ano Nuevo"),
        ("2025-12-25", "Navidad"),          # otro ano
        ("2027-01-01", "Ano Nuevo"),        # otro ano
        ("2026-02-30", "No existe"),        # fecha imposible
        ("basura", "x"),
        (None, "x"),
        ("2026-05-01T00:00:00", " Trabajo "),  # ISO con hora, nombre a limpiar
        ("2026-08-15", None),
        ("2026-08-16", "   "),               # nombre vacio => None
    ]
    assert del_ano(pares, 2026) == {
        "2026-01-01": "Ano Nuevo",
        "2026-05-01": "Trabajo",
        "2026-08-15": None,
        "2026-08-16": None,
    }


def test_f032_r42_del_ano_vacio():
    assert del_ano([], 2026) == {}


# -------------------------------- a_json -------------------------------- #

def test_f032_r42_a_json_ordenado_y_con_tildes():
    texto = a_json({"2026-12-08": "Inmaculada Concepción",
                    "2026-01-06": None})
    assert texto == ('{"2026-01-06": null, '
                     '"2026-12-08": "Inmaculada Concepción"}')
    assert json.loads(texto) == {"2026-01-06": None,
                                 "2026-12-08": "Inmaculada Concepción"}


def test_f032_r42_a_json_vacio():
    assert a_json({}) == "{}"


# -------------------------------- fila_de ------------------------------- #

def test_f032_r42_fila_de_bien_formada():
    fila = fila_de("12345678Z", 2026,
                   '{"2026-03-19": "San Jose", "2026-01-06": null}',
                   "2026-11-17T10:00:00Z")
    assert fila == FilaFestivos(
        dni_norm="12345678Z", ano=2026,
        festivos={"2026-01-06": None, "2026-03-19": "San Jose"},
        leido_en_utc="2026-11-17T10:00:00Z")
    assert list(fila.festivos) == ["2026-01-06", "2026-03-19"]


def test_f032_r42_fila_de_vacia_es_valida():
    assert fila_de("X1", 2026, "{}", "t").festivos == {}


@pytest.mark.parametrize("texto", [
    "no es json",
    "[]",
    '"cadena"',
    '{"2026-13-01": "mes imposible"}',
    '{"2025-12-25": "otro ano"}',
    '{"2026-01-01": 7}',
    '{"2026-01-01T00:00:00": "con hora"}',
    "null",
])
def test_f032_r42_fila_de_mal_formada_es_value_error(texto):
    with pytest.raises(ValueError):
        fila_de("12345678Z", 2026, texto, "t")


@pytest.mark.parametrize("dni,ano", [("", 2026), ("X1", 0), ("X1", "2026")])
def test_f032_r42_fila_de_clave_invalida_es_value_error(dni, ano):
    with pytest.raises(ValueError):
        fila_de(dni, ano, "{}", "t")


def test_f032_r42_fila_es_inmutable():
    fila = _fila()
    with pytest.raises(Exception):
        fila.ano = 2027  # type: ignore[misc]
