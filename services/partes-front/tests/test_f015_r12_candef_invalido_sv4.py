# tests/test_f015_r12_candef_invalido_sv4.py
"""R12 · un candef que Sigrid no informa sigue cayendo a la jornada 8.

F-015 se construye ENCIMA de `jornada_efectiva` (F-003), no la sustituye:
un candef vacio, no numerico o <= `CANDEF_MINIMO_VALIDO` sigue valiendo la
jornada por defecto, y su jornada semanal es la que el mapa asigne a esa
jornada por defecto (40). Sin esto, un 0 de Sigrid mandaria el dia entero
a horas extra, que es el error que F-003 vino a quitar.
"""
from __future__ import annotations

from datetime import date

import pytest
from application.services.jornada_resolver import (
    candef_valido,
    detalle_jornada_dia,
    jornada_dia,
)
from tests.dobles import es_laborable_fake

LUNES = date(2026, 3, 16)
VIERNES = date(2026, 3, 20)
MAPA = {8.0: 40.0, 9.0: 42.0}

INVALIDOS = [0.0, 1.0, 2.0, None, "", "ocho"]


@pytest.mark.parametrize("candef", INVALIDOS)
def test_f015_r12_sv4_candef_invalido_da_8_en_todo_laborable(candef) -> None:
    es_lab = es_laborable_fake()
    for d in (LUNES, VIERNES):
        assert jornada_dia(d, candef=candef, minimo=2.0, por_defecto=8.0,
                           mapa=MAPA, es_laborable=es_lab) == 8.0


@pytest.mark.parametrize("candef", INVALIDOS)
def test_f015_r12_sv4_el_detalle_lo_declara_como_candef_efectivo_8(candef) -> None:
    det = detalle_jornada_dia(
        VIERNES, candef=candef, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake())
    assert (det.candef_efectivo, det.semanal, det.origen) == (
        8.0, 40.0, "mapa")


@pytest.mark.parametrize("candef", INVALIDOS)
def test_f015_r12_sv4_candef_valido_sigue_diciendo_que_no(candef) -> None:
    """El KPI del portal marca 'asignado' leyendo de aqui: no cambia."""
    assert candef_valido(candef, minimo=2.0) is False


def test_f015_r12_sv4_una_jornada_por_defecto_distinta_manda() -> None:
    """Si la jornada por defecto fuese 7, su `S` seria la plana 35."""
    det = detalle_jornada_dia(
        VIERNES, candef=None, minimo=2.0, por_defecto=7.0, mapa=MAPA,
        es_laborable=es_laborable_fake())
    assert (det.candef_efectivo, det.semanal, det.horas, det.origen) == (
        7.0, 35.0, 7.0, "plana")
