# tests/test_f055_fecha_linea.py
"""F-055 · regla pura de la fecha de una linea (R1, R2).

`motivo_fecha_no_valida(fecha_int, hoy=...)` devuelve None si la fecha es
valida y, si no, el motivo entero `fecha_no_valida: <detalle>; corrige la
fecha en el portal y reaprueba`. `hoy` fijo: 31/10/2026 (design §8).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from application.services import fecha_linea
from application.services.fecha_linea import (
    DIAS_FUTURO,
    FECHA_MINIMA,
    MOTIVO_FECHA_NO_VALIDA,
    motivo_fecha_no_valida,
)

HOY = date(2026, 10, 31)
COLA = "; corrige la fecha en el portal y reaprueba"


def _int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def _motivo(detalle: str) -> str:
    return f"fecha_no_valida: {detalle}{COLA}"


def test_f055_constantes() -> None:
    assert MOTIVO_FECHA_NO_VALIDA == "fecha_no_valida"
    assert FECHA_MINIMA == 20260101
    assert DIAS_FUTURO == 62


@pytest.mark.parametrize("valor", [
    None, 0, -1, -20261020, True, False, "20261020", 20261020.0, [20261020]])
def test_f055_r1_sin_fecha(valor) -> None:
    assert motivo_fecha_no_valida(valor, hoy=HOY) == _motivo(
        "la linea no tiene fecha")


@pytest.mark.parametrize("valor", [
    20261340, 20260230, 20260229, 20261000, 20261032, 20260001, 99999999,
    1, 99, 20261])
def test_f055_r1_no_calendario(valor) -> None:
    assert motivo_fecha_no_valida(valor, hoy=HOY) == _motivo(
        f"{valor} no es una fecha del calendario")


def test_f055_r1_bisiesto_real_es_valido() -> None:
    """2028 es bisiesto: el 29/02 existe (y no es posterior si hoy esta
    cerca)."""
    assert motivo_fecha_no_valida(20280229, hoy=date(2028, 2, 1)) is None


def test_f055_r1_limite_inferior() -> None:
    assert motivo_fecha_no_valida(20251231, hoy=HOY) == _motivo(
        "31/12/2025 es anterior al 01/01/2026")
    assert motivo_fecha_no_valida(20260101, hoy=HOY) is None
    assert motivo_fecha_no_valida(20160315, hoy=HOY) == _motivo(
        "15/03/2016 es anterior al 01/01/2026")


def test_f055_r1_ano_de_tres_cifras_con_ceros() -> None:
    assert motivo_fecha_no_valida(5010203, hoy=HOY) == _motivo(
        "03/02/0501 es anterior al 01/01/2026")


def test_f055_r1_hoy_es_valido() -> None:
    assert motivo_fecha_no_valida(_int(HOY), hoy=HOY) is None


def test_f055_r1_limite_superior() -> None:
    tope = HOY + timedelta(days=62)
    assert _int(tope) == 20270101
    assert motivo_fecha_no_valida(20270101, hoy=HOY) is None
    assert motivo_fecha_no_valida(20270102, hoy=HOY) == _motivo(
        "02/01/2027 es posterior al 01/01/2027")
    assert motivo_fecha_no_valida(20620315, hoy=HOY) == _motivo(
        "15/03/2062 es posterior al 01/01/2027")


def test_f055_r1_el_tope_se_mueve_con_hoy() -> None:
    otro = date(2026, 3, 1)
    assert motivo_fecha_no_valida(20260502, hoy=otro) is None
    assert motivo_fecha_no_valida(20260503, hoy=otro) == _motivo(
        "03/05/2026 es posterior al 02/05/2026")


def test_f055_r1_tope_usa_la_constante(monkeypatch) -> None:
    """El margen sale de `DIAS_FUTURO`, no de un 62 escrito a mano."""
    monkeypatch.setattr(fecha_linea, "DIAS_FUTURO", 1)
    assert motivo_fecha_no_valida(20261101, hoy=HOY) is None
    assert motivo_fecha_no_valida(20261102, hoy=HOY) == _motivo(
        "02/11/2026 es posterior al 01/11/2026")


def test_f055_r1_minima_usa_la_constante(monkeypatch) -> None:
    monkeypatch.setattr(fecha_linea, "FECHA_MINIMA", 20260301)
    assert motivo_fecha_no_valida(20260301, hoy=HOY) is None
    assert motivo_fecha_no_valida(20260228, hoy=HOY) == _motivo(
        "28/02/2026 es anterior al 01/03/2026")


@pytest.mark.parametrize("valor,hoy", [
    (0, HOY), (20261340, HOY), (20251231, HOY), (20620315, HOY),
    (99999999, HOY), (-5, HOY)])
def test_f055_r2_texto_del_motivo(valor, hoy) -> None:
    m = motivo_fecha_no_valida(valor, hoy=hoy)
    assert m is not None
    prefijo, _, resto = m.partition(":")
    assert prefijo == MOTIVO_FECHA_NO_VALIDA
    assert resto.startswith(" ") and ":" not in resto
    assert m.endswith(COLA)
    assert m.isascii()
    assert len(m) <= 255
