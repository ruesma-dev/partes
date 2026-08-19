# tests/test_f015_r28_log_trazable.py
"""R28 · el log dice por que la jornada de ese dia no era el candef.

Cuando Administracion pregunte «por que a este hombre le sale la ordinaria
en 6 el viernes», la respuesta tiene que estar en el log del worker sin
reconstruir el calculo a mano: jornada aplicada, jornada semanal, de donde
salio (mapa, excepcion o plana) y si ese dia era el ultimo laborable.

Y al reves: en el caso NORMAL (candef 8, jornada 8) la marca no aparece.
Un log que repite lo obvio en cada linea de cada parte es un log que nadie
lee.
"""
from __future__ import annotations

import logging

from application.services.recurso_conciliador import RecursoConciliador
from domain.ports.jornada_empleado_port import JornadaEmpleadoRow
from tests.dobles import (
    CalendarioFake,
    JornadasFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

LUNES = 20260316
VIERNES = 20260320


def _splits(regs, *, candef=9.0, jornadas=None, no_laborables=()):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set(no_laborables)),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0, jornadas=jornadas,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


# ------------------------------ la marca -------------------------------- #

def test_f015_r28_la_jornada_incompleta_lleva_la_marca(caplog) -> None:
    """Viernes de 4 h con jornada 6: extra -2 y traza de por que 6."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=4.0)])
    assert "jornada_dia=6.00" in caplog.text
    assert "semanal=42.00" in caplog.text
    assert "origen=mapa" in caplog.text
    assert "ultimo_laborable=si" in caplog.text


def test_f015_r28_el_recorte_a_extra_lleva_la_marca(caplog) -> None:
    """Viernes de 9 h con jornada 6: 3 h a extra, con la misma traza."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=9.0)])
    assert "jornada_dia=6.00" in caplog.text
    assert "ultimo_laborable=si" in caplog.text
    assert "recurso=501" in caplog.text


def test_f015_r28_la_marca_dice_cuando_la_S_es_de_una_excepcion(caplog) -> None:
    jornadas = JornadasFake([
        JornadaEmpleadoRow(dni_norm="12345678Z", jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=4.0)],
                candef=10.0, jornadas=jornadas)
    assert "origen=excepcion" in caplog.text
    assert "semanal=48.00" in caplog.text
    assert "jornada_dia=8.00" in caplog.text


def test_f015_r28_la_jornada_plana_no_se_etiqueta_como_del_mapa(caplog) -> None:
    """Candef fuera del mapa: la jornada del dia es `c` en todo laborable,
    asi que no hay nada que explicar; lo que no puede pasar es que se
    etiquete como 'mapa' algo que el mapa no dijo."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=4.0)], candef=11.0)
    assert "origen=mapa" not in caplog.text


# --------------------- el caso normal no se ensucia --------------------- #

def test_f015_r28_con_candef_8_no_hay_marca(caplog) -> None:
    """La jornada del dia ES el candef efectivo: no hay nada que explicar."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=6.0)], candef=8.0)
    assert "jornada_dia=" not in caplog.text


def test_f015_r28_un_dia_no_ultimo_con_candef_9_tampoco_lleva_marca(
        caplog) -> None:
    """El lunes de la cuadrilla vale 9, que es el candef: nada que decir."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=LUNES, horas=6.0)])
    assert "jornada_dia=" not in caplog.text


def test_f015_r28_el_dia_no_laborable_no_lleva_marca(caplog) -> None:
    """Su mensaje es el de F-003 y no cambia."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=5.0)],
                no_laborables={"2026-03-20"})
    assert "jornada_dia=" not in caplog.text
    assert "dia NO laborable" in caplog.text


def test_f015_r28_el_log_no_lleva_el_dni_de_nadie(caplog) -> None:
    """El log del worker se archiva: ahi no van datos personales."""
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=VIERNES, horas=4.0)])
    assert "12345678Z" not in caplog.text
