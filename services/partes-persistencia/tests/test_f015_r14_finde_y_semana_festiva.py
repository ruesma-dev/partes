# tests/test_f015_r14_finde_y_semana_festiva.py
"""R14 · fin de semana y semanas sin ningun dia laborable.

Dos bordes que, mal resueltos, regalarian o robarian horas:

  - un sabado NUNCA es candidato a "ultimo laborable": si el viernes es
    fiesta, el resto se queda en el jueves, no salta al sabado. Con el
    calendario cableado (produccion desde F-003) el sabado no es laborable
    y su jornada es 0, asi que todo lo trabajado es extra, como hoy;
  - una semana entera festiva no tiene ultimo laborable: ningun dia
    recibe el resto, todos valen 0.
"""
from __future__ import annotations

from datetime import date

from application.services.recurso_conciliador import RecursoConciliador
from application.services.jornada_resolver import es_ultimo_laborable, jornada_dia
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    es_laborable_fake,
    indice_reshor,
    registro,
)

LUNES = date(2026, 3, 16)
JUEVES = date(2026, 3, 19)
VIERNES = date(2026, 3, 20)
SABADO = date(2026, 3, 21)
DOMINGO = date(2026, 3, 22)
SEMANA = (LUNES, date(2026, 3, 17), date(2026, 3, 18), JUEVES, VIERNES)

MAPA = {8.0: 40.0, 9.0: 42.0}

SEMANA_ENTERA_FESTIVA = {
    "2026-03-16", "2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20",
}


def _jornada(d, no_laborables=(), *, candef=9.0):
    return jornada_dia(d, candef=candef, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_laborable_fake(no_laborables))


# ------------------------------ fin de semana --------------------------- #

def test_f015_r14_el_sabado_no_tiene_jornada_ordinaria() -> None:
    assert _jornada(SABADO) == 0.0
    assert _jornada(DOMINGO) == 0.0


def test_f015_r14_un_viernes_festivo_no_asciende_al_sabado() -> None:
    """El resto se queda en el jueves; el sabado sigue valiendo 0."""
    assert _jornada(JUEVES, {"2026-03-20"}) == 6.0
    assert _jornada(SABADO, {"2026-03-20"}) == 0.0
    assert es_ultimo_laborable(
        SABADO, es_laborable_fake({"2026-03-20"})) is False


def test_f015_r14_sabado_trabajado_va_entero_a_extra() -> None:
    """Escenario J: 6 h en sabado con calendario -> 6 h extra."""
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake({"2026-03-21"}),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
    )
    regs = [registro(1, fecha_int=20260321, horas=6.0)]
    splits = conciliador._reclasificar_extras_jornada(
        regs, {1: 501}, indice_reshor(501, candef=9.0))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (0.0, 6.0)]


# -------------------------- semana entera festiva ----------------------- #

def test_f015_r14_semana_entera_festiva_no_reparte_nada() -> None:
    """Escenario F: sin ningun laborable L-V, ningun dia recibe el resto."""
    assert [_jornada(d, SEMANA_ENTERA_FESTIVA) for d in SEMANA] == [0.0] * 5


def test_f015_r14_semana_entera_festiva_no_tiene_ultimo_laborable() -> None:
    es_lab = es_laborable_fake(SEMANA_ENTERA_FESTIVA)
    assert not any(es_ultimo_laborable(d, es_lab) for d in SEMANA)


def test_f015_r14_semana_festiva_con_candef_8_tambien_da_cero() -> None:
    assert [_jornada(d, SEMANA_ENTERA_FESTIVA, candef=8.0) for d in SEMANA] \
        == [0.0] * 5
