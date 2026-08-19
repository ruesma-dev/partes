# tests/test_f015_r17_tabla_caida_o_vacia.py
"""R17 · la tabla de excepciones no puede tumbar la conciliacion.

`empleado_jornada` es un ACCESORIO: la jornada del dia se sabe derivar
del candef sin ella. Si la lectura falla —base caida, tabla que todavia
no existe, driver que revienta— sv3 sigue conciliando con la regla
derivada y deja un WARNING; y con la tabla VACIA, que es como va a estar
mucho tiempo, no puede haber ni aviso ni diferencia ninguna.

El aviso va una vez por pasada, no una por registro: un fallo de BBDD con
41 partes en cola llenaria el log de lo mismo y taparia el resto.
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
    registro,
)

DNI = "12345678Z"
LUNES = 20260316
VIERNES = 20260320


def _conciliador(puerto):
    return RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), jornada_ordinaria_horas=8.0,
        candef_minimo=2.0, jornadas=puerto,
    )


def _detalle(conciliador, fecha_int, *, candef=9.0):
    regs = [registro(1, fecha_int=fecha_int, horas=1.0, dni=DNI)]
    return conciliador._detalle_jornada(fecha_int, regs, candef)


# ------------------------------ tabla caida ----------------------------- #

def test_f015_r17_un_fallo_de_lectura_no_aborta_el_calculo(caplog) -> None:
    conciliador = _conciliador(JornadasFake(fallo=RuntimeError("BBDD caida")))
    with caplog.at_level(logging.WARNING):
        detalle = _detalle(conciliador, VIERNES)
    assert (detalle.horas, detalle.origen) == (6.0, "mapa")


def test_f015_r17_un_fallo_de_lectura_deja_un_warning(caplog) -> None:
    conciliador = _conciliador(JornadasFake(fallo=RuntimeError("BBDD caida")))
    with caplog.at_level(logging.WARNING):
        _detalle(conciliador, VIERNES)
    assert "empleado_jornada" in caplog.text
    assert "BBDD caida" in caplog.text


def test_f015_r17_el_fallo_se_avisa_una_vez_por_pasada(caplog) -> None:
    """Un WARNING por registro llenaria el log y taparia lo importante."""
    puerto = JornadasFake(fallo=RuntimeError("BBDD caida"))
    conciliador = _conciliador(puerto)
    with caplog.at_level(logging.WARNING):
        for fecha in (LUNES, VIERNES, LUNES + 1, LUNES + 2):
            _detalle(conciliador, fecha)
    avisos = [m for m in caplog.messages if "empleado_jornada" in m]
    assert len(avisos) == 1


def test_f015_r17_tras_el_fallo_no_se_reintenta_en_la_misma_pasada() -> None:
    puerto = JornadasFake(fallo=RuntimeError("BBDD caida"))
    conciliador = _conciliador(puerto)
    for fecha in (LUNES, VIERNES):
        _detalle(conciliador, fecha)
    assert puerto.llamadas == 1


def test_f015_r17_el_resultado_es_el_mismo_que_sin_tabla() -> None:
    caido = _conciliador(JornadasFake(fallo=RuntimeError("BBDD caida")))
    sin_tabla = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()),
    )
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni=DNI)]
    assert (_detalle(caido, VIERNES).horas
            == sin_tabla._detalle_jornada(VIERNES, regs, 9.0).horas)


# ------------------------------ tabla vacia ----------------------------- #

def test_f015_r17_la_tabla_vacia_no_avisa_de_nada(caplog) -> None:
    """El estado esperado durante mucho tiempo: ni ruido ni diferencia."""
    conciliador = _conciliador(JornadasFake([]))
    with caplog.at_level(logging.WARNING):
        detalle = _detalle(conciliador, VIERNES)
    assert (detalle.horas, detalle.origen) == (6.0, "mapa")
    assert "empleado_jornada" not in caplog.text


def test_f015_r17_una_tabla_con_filas_de_otros_tampoco_avisa(caplog) -> None:
    conciliador = _conciliador(JornadasFake([
        JornadaEmpleadoRow(dni_norm="00000000T", jornada_semanal=48.0,
                           desde="2026-01-01"),
    ]))
    with caplog.at_level(logging.WARNING):
        assert _detalle(conciliador, VIERNES).horas == 6.0
    assert "empleado_jornada" not in caplog.text


# ------------------- la pasada siguiente vuelve a intentarlo ------------ #

def test_f015_r17_conciliar_todos_reinicia_el_aviso(caplog) -> None:
    """`conciliar_todos` limpia los acumuladores de la pasada, como ya hace
    con los partes degradados: un fallo de ayer no silencia el de hoy."""
    puerto = JornadasFake(fallo=RuntimeError("BBDD caida"))
    conciliador = _conciliador(puerto)
    with caplog.at_level(logging.WARNING):
        _detalle(conciliador, VIERNES)
        conciliador.conciliar_todos()
        _detalle(conciliador, VIERNES)
    avisos = [m for m in caplog.messages if "empleado_jornada" in m]
    assert len(avisos) == 2
