# tests/test_f015_r13_ultimo_laborable.py
"""R13 · la jornada del DIA y la regla del ultimo dia laborable.

El corazon de F-015. Con jornada semanal `S` y candef efectivo `c`, los
dias L-V laborables valen `c` salvo el ULTIMO laborable de su semana, que
recibe el resto: `max(0, S - 4c)`. Los festivos L-V cuentan como jornada
a efectos del resto (lectura A del humano en F-012), asi que el ultimo
laborable siempre recibe `S - 4c`, haya festivos o no.

Semana de referencia: 2026-03-16 (L) ... 2026-03-22 (D), sin festivos
nacionales, para que los festivos de los casos los ponga el doble y no el
calendario real.
"""
from __future__ import annotations

from datetime import date

import pytest
from application.services.jornada_resolver import (
    detalle_jornada_dia,
    es_ultimo_laborable,
    jornada_dia,
)
from tests.dobles import es_laborable_fake

LUNES = date(2026, 3, 16)
MARTES = date(2026, 3, 17)
MIERCOLES = date(2026, 3, 18)
JUEVES = date(2026, 3, 19)
VIERNES = date(2026, 3, 20)
SABADO = date(2026, 3, 21)
DOMINGO = date(2026, 3, 22)

SEMANA = (LUNES, MARTES, MIERCOLES, JUEVES, VIERNES)

MAPA = {8.0: 40.0, 9.0: 42.0}


def _jornadas(no_laborables=(), *, candef=9.0, mapa=None, dias=SEMANA,
              excepcion=None):
    es_lab = es_laborable_fake(no_laborables)
    return [
        jornada_dia(d, candef=candef, minimo=2.0, por_defecto=8.0,
                    mapa=MAPA if mapa is None else mapa,
                    es_laborable=es_lab, excepcion=excepcion)
        for d in dias
    ]


# ------------------------ `es_ultimo_laborable` ------------------------- #

def test_f015_r13_el_viernes_es_el_ultimo_laborable_de_la_semana() -> None:
    es_lab = es_laborable_fake()
    assert es_ultimo_laborable(VIERNES, es_lab) is True
    assert es_ultimo_laborable(JUEVES, es_lab) is False


def test_f015_r13_con_el_viernes_festivo_lo_es_el_jueves() -> None:
    es_lab = es_laborable_fake({"2026-03-20"})
    assert es_ultimo_laborable(JUEVES, es_lab) is True
    assert es_ultimo_laborable(VIERNES, es_lab) is False


def test_f015_r13_un_dia_no_laborable_nunca_es_el_ultimo() -> None:
    es_lab = es_laborable_fake({"2026-03-18"})
    assert es_ultimo_laborable(MIERCOLES, es_lab) is False


def test_f015_r13_el_finde_nunca_es_el_ultimo_laborable() -> None:
    """Ni siquiera si el calendario declarase laborable el sabado (D11)."""
    es_lab = es_laborable_fake(finde_laborable=True)
    assert es_ultimo_laborable(SABADO, es_lab) is False
    assert es_ultimo_laborable(DOMINGO, es_lab) is False
    assert es_ultimo_laborable(VIERNES, es_lab) is True


def test_f015_r13_solo_mira_los_dias_POSTERIORES_de_su_semana() -> None:
    """El lunes de la semana SIGUIENTE no cuenta para esta."""
    consultadas: list[str] = []
    es_lab = es_laborable_fake(registro=consultadas)
    assert es_ultimo_laborable(VIERNES, es_lab) is True
    assert all(f <= "2026-03-20" for f in consultadas)


# --------------------- la tabla de casos de F-012 ----------------------- #

def test_f015_r13_semana_normal_c9_reparte_9999_6() -> None:
    """Escenario A: cuadrilla de regimen 42 -> L-J 9 h y viernes 6 h."""
    assert _jornadas() == [9.0, 9.0, 9.0, 9.0, 6.0]


def test_f015_r13_viernes_festivo_pasa_el_resto_al_jueves() -> None:
    """Escenario B: el viernes es fiesta -> el jueves recibe el resto."""
    assert _jornadas({"2026-03-20"}) == [9.0, 9.0, 9.0, 6.0, 0.0]


def test_f015_r13_miercoles_festivo_no_mueve_el_resto() -> None:
    """Escenario C: el festivo del miercoles CUENTA como jornada."""
    assert _jornadas({"2026-03-18"}) == [9.0, 9.0, 0.0, 9.0, 6.0]


def test_f015_r13_jueves_y_viernes_festivos_dejan_el_resto_el_miercoles() -> None:
    """Escenario D."""
    assert _jornadas({"2026-03-19", "2026-03-20"}) == [
        9.0, 9.0, 6.0, 0.0, 0.0]


def test_f015_r13_solo_el_lunes_laborable_recibe_el_resto() -> None:
    """Escenario E: el lunes es a la vez primero y ultimo laborable."""
    assert _jornadas(
        {"2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20"}
    ) == [6.0, 0.0, 0.0, 0.0, 0.0]


def test_f015_r13_candef_8_da_8_todos_los_dias() -> None:
    """Escenario K (regresion): 40 - 32 = 8, igual que hoy."""
    assert _jornadas(candef=8.0) == [8.0] * 5
    assert _jornadas({"2026-03-18"}, candef=8.0) == [
        8.0, 8.0, 0.0, 8.0, 8.0]


def test_f015_r13_otro_mapa_cambia_el_resto() -> None:
    """Con `9:40`, el viernes de la cuadrilla valdria 4 h."""
    assert _jornadas(mapa={9.0: 40.0}) == [9.0, 9.0, 9.0, 9.0, 4.0]


def test_f015_r13_candef_fuera_del_mapa_es_jornada_plana() -> None:
    """Escenario M: c 10 -> S 50 -> 50 - 40 = 10 todos los dias."""
    assert _jornadas(candef=10.0) == [10.0] * 5


def test_f015_r13_el_resto_nunca_es_negativo() -> None:
    """Con `9:30`, `S - 4c` seria -6: se corta en 0."""
    assert _jornadas(mapa={9.0: 30.0}) == [9.0, 9.0, 9.0, 9.0, 0.0]


# --------------------------- orden de la regla -------------------------- #

def test_f015_r13_dia_no_laborable_vale_cero_antes_que_nada() -> None:
    es_lab = es_laborable_fake({"2026-03-20"})
    assert jornada_dia(VIERNES, candef=9.0, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_lab) == 0.0


def test_f015_r13_sabado_laborable_sin_calendario_vale_el_candef() -> None:
    """DA4: sin calendario cableado el sabado es un dia mas y vale `c`."""
    es_lab = es_laborable_fake(finde_laborable=True)
    assert jornada_dia(SABADO, candef=9.0, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_lab) == 9.0


def test_f015_r13_sabado_con_calendario_vale_cero() -> None:
    es_lab = es_laborable_fake()
    assert jornada_dia(SABADO, candef=9.0, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_lab) == 0.0


# ------------------------------ el detalle ------------------------------ #

def test_f015_r13_el_detalle_explica_de_donde_sale_la_jornada() -> None:
    det = detalle_jornada_dia(
        VIERNES, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake())
    assert (det.horas, det.candef_efectivo, det.semanal, det.origen,
            det.ultimo_laborable) == (6.0, 9.0, 42.0, "mapa", True)


def test_f015_r13_el_detalle_de_un_dia_normal() -> None:
    det = detalle_jornada_dia(
        LUNES, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake())
    assert (det.horas, det.origen, det.ultimo_laborable) == (
        9.0, "mapa", False)


def test_f015_r13_el_detalle_de_un_candef_fuera_del_mapa() -> None:
    det = detalle_jornada_dia(
        VIERNES, candef=10.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake())
    assert (det.horas, det.semanal, det.origen) == (10.0, 50.0, "plana")


def test_f015_r13_jornada_dia_es_azucar_de_detalle_jornada_dia() -> None:
    for d in SEMANA:
        es_lab = es_laborable_fake()
        assert jornada_dia(
            d, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
            es_laborable=es_lab
        ) == detalle_jornada_dia(
            d, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
            es_laborable=es_laborable_fake()).horas


# ------------------- coste: no se pregunta de mas ----------------------- #

def test_f015_r13_con_S_igual_a_5c_no_se_consulta_el_resto_de_la_semana() -> None:
    """Regresion barata: con c 8 y S 40 la regla no cambia NADA, asi que
    no hace falta recorrer la semana. Es lo que mantiene el coste de
    F-015 a cero para todos los recursos de jornada normal."""
    consultadas: list[str] = []
    jornada_dia(LUNES, candef=8.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
                es_laborable=es_laborable_fake(registro=consultadas))
    assert consultadas == ["2026-03-16"]


def test_f015_r13_como_mucho_se_consultan_los_LV_de_la_semana() -> None:
    consultadas: list[str] = []
    jornada_dia(LUNES, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
                es_laborable=es_laborable_fake(registro=consultadas))
    assert set(consultadas) <= {
        "2026-03-16", "2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20"}


@pytest.mark.parametrize("dia, esperado", [
    (LUNES, 9.0), (MARTES, 9.0), (MIERCOLES, 9.0), (JUEVES, 9.0),
    (VIERNES, 6.0), (SABADO, 0.0), (DOMINGO, 0.0),
])
def test_f015_r13_semana_completa_dia_a_dia(dia, esperado) -> None:
    assert jornada_dia(dia, candef=9.0, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_laborable_fake()) == esperado


# ================= refuerzo tras la campana de mutacion ================= #
# `DetalleJornada.ultimo_laborable` solo estaba fijado en la rama que
# aplica el resto. Las otras tres —dia no laborable, sabado laborable y el
# atajo `S = 5c`— dejaban pasar mutantes que lo ponian a True, y ese campo
# es lo que la traza del log (R28) enseña a Administracion.

def _detalle(dia, *, candef=9.0, no_laborables=(), finde_laborable=False):
    return detalle_jornada_dia(
        dia, candef=candef, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake(no_laborables,
                                       finde_laborable=finde_laborable),
    )


def test_f015_r13_un_dia_no_laborable_no_es_ultimo_laborable() -> None:
    """0 h porque es fiesta, no porque le toque el resto de la semana."""
    det = _detalle(VIERNES, no_laborables={"2026-03-20"})
    assert (det.horas, det.ultimo_laborable) == (0.0, False)


def test_f015_r13_el_finde_laborable_no_es_ultimo_laborable() -> None:
    """DA4: sin calendario cableado el sabado vale `c`, pero NO recibe el
    resto de la semana."""
    det = _detalle(SABADO, finde_laborable=True)
    assert (det.horas, det.ultimo_laborable) == (9.0, False)


def test_f015_r13_con_S_igual_a_5c_ningun_dia_recibe_el_resto() -> None:
    """El atajo del candef 8: la regla no cambia nada, asi que NINGUN dia
    queda marcado como "recibio el resto" (es lo que documenta DI1)."""
    for dia in SEMANA:
        det = _detalle(dia, candef=8.0)
        assert (det.horas, det.ultimo_laborable) == (8.0, False)


def test_f015_r13_solo_el_ultimo_laborable_queda_marcado() -> None:
    marcados = [d for d in SEMANA if _detalle(d).ultimo_laborable]
    assert marcados == [VIERNES]


def test_f015_r13_con_el_viernes_festivo_el_marcado_es_el_jueves() -> None:
    marcados = [
        d for d in SEMANA
        if _detalle(d, no_laborables={"2026-03-20"}).ultimo_laborable
    ]
    assert marcados == [JUEVES]
