# tests/test_f015_r11_regresion_candef8.py
"""R11 · con candef 8 y S 40, F-015 no mueve ni una hora.

Es LA propiedad que permite mergear y desplegar esta feature sin esperar
a F-014: `40 - 4 x 8 = 8`, o sea que el ultimo laborable recibe la misma
jornada que cualquier otro dia. Todo recurso de jornada normal —que hoy
son todos— sale exactamente igual que antes.

Estos casos se escriben contra el comportamiento vigente y tienen que
pasar ANTES y DESPUES de tocar `_reclasificar_extras_jornada`: si alguno
se pone rojo, la regresion cero se ha roto y hay que parar, no adaptar el
test. Los dorados de F-003 (`test_f003_r15_splits_dorados.py`) cubren el
resto del algoritmo y NO se tocan.
"""
from __future__ import annotations

import pytest
from application.services.recurso_conciliador import RecursoConciliador
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

# Semana de referencia: 2026-03-16 (L) ... 2026-03-22 (D).
LUNES = 20260316
MARTES = 20260317
MIERCOLES = 20260318
JUEVES = 20260319
VIERNES = 20260320
SABADO = 20260321
SEMANA = (LUNES, MARTES, MIERCOLES, JUEVES, VIERNES)


def _splits(regs, *, calendario=None, candef=8.0):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=calendario, jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


# --------------------- la semana completa, dia a dia -------------------- #

@pytest.mark.parametrize("fecha_int", SEMANA)
def test_f015_r11_ocho_horas_cuadran_cualquier_dia_de_la_semana(
        fecha_int) -> None:
    """Tambien el viernes: el ultimo laborable recibe 40 - 32 = 8."""
    regs = [registro(1, fecha_int=fecha_int, horas=8.0)]
    assert _splits(regs, calendario=CalendarioFake(set())) == []


@pytest.mark.parametrize("fecha_int", SEMANA)
def test_f015_r11_seis_horas_dan_extra_negativa_cualquier_dia(
        fecha_int) -> None:
    regs = [registro(1, fecha_int=fecha_int, horas=6.0)]
    splits = _splits(regs, calendario=CalendarioFake(set()))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (8.0, -2.0)]


@pytest.mark.parametrize("fecha_int", SEMANA)
def test_f015_r11_diez_horas_dan_dos_extra_cualquier_dia(fecha_int) -> None:
    regs = [registro(1, fecha_int=fecha_int, horas=10.0)]
    splits = _splits(regs, calendario=CalendarioFake(set()))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (8.0, 2.0)]


# --------------------------- con festivos ------------------------------- #

def test_f015_r11_un_miercoles_festivo_no_cambia_el_viernes() -> None:
    """Escenario K: el festivo entre semana no reparte nada a nadie."""
    calendario = CalendarioFake({"2026-03-18"})
    regs = [registro(1, fecha_int=VIERNES, horas=6.0)]
    splits = _splits(regs, calendario=calendario)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (8.0, -2.0)]


def test_f015_r11_un_viernes_festivo_no_cambia_el_jueves() -> None:
    calendario = CalendarioFake({"2026-03-20"})
    regs = [registro(1, fecha_int=JUEVES, horas=6.0)]
    splits = _splits(regs, calendario=calendario)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (8.0, -2.0)]


def test_f015_r11_el_festivo_trabajado_sigue_yendo_entero_a_extra() -> None:
    calendario = CalendarioFake({"2026-03-20"})
    regs = [registro(1, fecha_int=VIERNES, horas=5.0)]
    splits = _splits(regs, calendario=calendario)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (0.0, 5.0)]


# ----------------------- sin calendario cableado (D11) ------------------ #

@pytest.mark.parametrize("fecha_int", SEMANA)
def test_f015_r11_sin_calendario_todo_LV_sigue_valiendo_8(fecha_int) -> None:
    regs = [registro(1, fecha_int=fecha_int, horas=8.0)]
    assert _splits(regs, calendario=None) == []


def test_f015_r11_sin_calendario_el_sabado_sigue_teniendo_jornada_8() -> None:
    """DA4: sin calendario, el sabado es un dia mas y 6 h son jornada
    incompleta, no 6 h extra. Es lo que hace hoy sv3."""
    regs = [registro(1, fecha_int=SABADO, horas=6.0)]
    splits = _splits(regs, calendario=None)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (8.0, -2.0)]


def test_f015_r11_sin_calendario_el_sabado_de_8_cuadra() -> None:
    regs = [registro(1, fecha_int=SABADO, horas=8.0)]
    assert _splits(regs, calendario=None) == []


# ------------------------- el candef sigue mandando --------------------- #

@pytest.mark.parametrize("candef, norm, extra", [
    (None, 8.0, -2.0),
    (0.0, 8.0, -2.0),
    (2.0, 8.0, -2.0),
    (2.5, 2.5, 3.5),
    (8.0, 8.0, -2.0),
])
def test_f015_r11_el_candef_efectivo_no_cambia_de_semantica(
        candef, norm, extra) -> None:
    """Mismo cuadro que el dorado de F-003, ahora un LUNES de la semana de
    referencia: F-015 se construye ENCIMA de `jornada_efectiva`."""
    regs = [registro(1, fecha_int=LUNES, horas=6.0)]
    splits = _splits(regs, calendario=CalendarioFake(set()), candef=candef)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (norm, extra)]
    assert splits[0]["hora_candef"] == candef


# ================= refuerzo tras la campana de mutacion ================= #
# Sin calendario cableado (D11) solo se probaba con candef 8, que entra por
# el atajo `S = 5c` y no recorre la semana. Con candef 9 SI la recorre, y
# ahi es donde importa que "sin calendario" signifique "todo laborable": si
# significara lo contrario, el LUNES pasaria a ser el ultimo laborable de
# su semana y recibiria el resto (6 h en vez de 9).

@pytest.mark.parametrize("fecha_int, esperado", [
    (LUNES, 9.0), (MARTES, 9.0), (MIERCOLES, 9.0), (JUEVES, 9.0),
    (VIERNES, 6.0),
])
def test_f015_r11_sin_calendario_el_ultimo_laborable_es_el_viernes(
        fecha_int, esperado) -> None:
    """D11: sin calendario, la semana es L-V entera y el resto cae el
    viernes. Es la situacion de todos los tests previos a F-003."""
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(), calendario=None,
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
    )
    regs = [registro(1, fecha_int=fecha_int, horas=1.0)]
    assert conciliador._detalle_jornada(fecha_int, regs, 9.0).horas == esperado


def test_f015_r11_sin_calendario_solo_el_viernes_recibe_el_resto() -> None:
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(), calendario=None,
    )
    marcados = []
    for fecha_int in SEMANA:
        regs = [registro(1, fecha_int=fecha_int, horas=1.0)]
        if conciliador._detalle_jornada(fecha_int, regs, 9.0).ultimo_laborable:
            marcados.append(fecha_int)
    assert marcados == [VIERNES]


def test_f015_r11_sin_calendario_un_viernes_de_6_horas_cuadra() -> None:
    """De punta a punta: sin calendario y con candef 9, el viernes tipico de
    la cuadrilla tampoco genera extras."""
    regs = [registro(1, fecha_int=VIERNES, horas=6.0)]
    assert _splits(regs, calendario=None, candef=9.0) == []
