# tests/test_f048_normalizer.py
"""F-048 · la ingesta suma las extras leidas > 0 a la ordinaria (R1-R5, R7).

`ParteNormalizer` puro: un JSON de sv2 sintetico (sin nombres ni DNIs
reales) y los registros que emite. Una fila con `horas_extraordinarias`
> 0 sale como registros `normal` con el trabajado (ordinarias + extras) y
ningun `extra`; `horas_extra_leidas` guarda la parte de cada registro que
la IA leyo como extra (ordinarias primero, en el orden de emision). Las
filas sin extras positivas se expanden como siempre. La tabla de
`design.md` §7 va entera en `test_f048_r1_r2_tabla_del_design`.
"""
from __future__ import annotations

import logging

import pytest
from application.services.parte_normalizer import ParteNormalizer


def _datos(*empleados: dict) -> dict:
    return {"cabecera": {"fecha": "02/03/2026", "obra_numero": "0100"},
            "empleados": list(empleados)}


def _fila(ordinarias=None, extras=None, partidas=None, **extra) -> dict:
    fila = {"nombre": "Persona Uno", "numero_linea": 1,
            "horas_ordinarias": ordinarias,
            "horas_extraordinarias": extras,
            "codigo_hora_ordinaria": "HL01", "codigo_hora_extra": "HE01"}
    if partidas is not None:
        fila["partidas"] = [{"partida": c, "horas": h} for c, h in partidas]
    fila.update(extra)
    return fila


def _registros(*empleados: dict):
    return ParteNormalizer().normalize(
        _datos(*empleados), email_text="marzo 2026").registros


def _resumen(*empleados: dict) -> list[tuple]:
    return [(r.tipo_hora, r.horas, r.horas_extra_leidas, r.partida)
            for r in _registros(*empleados)]


# ------------------------- tabla de design §7 --------------------------- #

@pytest.mark.parametrize(("fila", "esperado"), [
    (_fila(None, 10), [("normal", 10.0, 10.0, None)]),
    (_fila(4, 5), [("normal", 9.0, 5.0, None)]),
    (_fila(8, 0), [("normal", 8.0, None, None)]),
    (_fila(8, -2), [("normal", 8.0, None, None),
                    ("extra", -2.0, None, None)]),
    (_fila(4, 5, [("P1", 6), ("P2", None)]),
     [("normal", 6.0, 2.0, "P1"), ("normal", 3.0, 3.0, "P2")]),
    (_fila(None, 6, [("P1", 2), ("P2", 4)]),
     [("normal", 2.0, 2.0, "P1"), ("normal", 4.0, 4.0, "P2")]),
], ids=["solo-10", "4+5", "8+0", "8-2", "4+5-P1-6-P2-abierta",
        "solo-6-P1-2-P2-4"])
def test_f048_r1_r2_tabla_del_design(fila, esperado) -> None:
    assert _resumen(fila) == esperado


# ------------------------------- R1 y R2 -------------------------------- #

def test_f048_r1_ninguna_extra_de_una_fila_sumable() -> None:
    regs = _registros(_fila(4, 5), _fila(None, 10, numero_linea=2))
    assert {r.tipo_hora for r in regs} == {"normal"}
    assert [r.horas for r in regs] == [9.0, 10.0]


def test_f048_r1_extras_con_decimales_y_texto() -> None:
    assert _resumen(_fila("4,5", "2,5")) == [("normal", 7.0, 2.5, None)]


def test_f048_r1_ordinarias_negativas_cuentan_cero() -> None:
    """DA8: ordinarias <= 0 ya se descartaban; el trabajado son las extras."""
    assert _resumen(_fila(-3, 5)) == [("normal", 5.0, 5.0, None)]


def test_f048_r2_partida_explicita_corta_resto_sin_partida() -> None:
    """P1 con 3 h solo consume ordinarias; el resto (1 ord + 5 extra) va a
    partida None y lleva las 5 extras leidas."""
    assert _resumen(_fila(4, 5, [("P1", 3)])) == [
        ("normal", 3.0, None, "P1"), ("normal", 6.0, 5.0, None)]


def test_f048_r2_la_extra_cae_donde_se_acaban_las_ordinarias() -> None:
    assert _resumen(_fila(4, 5, [("P1", 2), ("P2", 3), ("P3", None)])) == [
        ("normal", 2.0, None, "P1"), ("normal", 3.0, 1.0, "P2"),
        ("normal", 4.0, 4.0, "P3")]


def test_f048_r2_partida_justa_en_las_ordinarias_no_lleva_extra() -> None:
    assert _resumen(_fila(4, 5, [("P1", 4), ("P2", None)])) == [
        ("normal", 4.0, None, "P1"), ("normal", 5.0, 5.0, "P2")]


def test_f048_r2_la_suma_de_lo_leido_es_la_extra_leida() -> None:
    regs = _registros(_fila(3.5, 6.5, [("P1", 2), ("P2", 5), ("P3", None)]))
    assert sum(r.horas_extra_leidas or 0 for r in regs) == 6.5
    assert sum(r.horas for r in regs) == 10.0


def test_f048_r2_partida_que_excede_se_capa_al_total(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        assert _resumen(_fila(4, 5, [("P1", 12)])) == [
            ("normal", 9.0, 5.0, "P1")]
    assert "se capa al total" in caplog.text
    assert "solo tiene 9.0 h" in caplog.text


@pytest.mark.parametrize(("fila", "esperado"), [
    (_fila(4.3, 5, [("P1", 2.1), ("P2", 2.2), ("P3", None)]),
     [None, None, 5.0]),
    (_fila(4.3, 5), [5.0]),
    (_fila(8.1, 0.2), [0.2]),
], ids=["4,3+5-tres-partidas", "4,3+5", "8,1+0,2"])
def test_f048_r2_sin_residuo_de_coma_flotante(fila, esperado) -> None:
    """Review pasada 1: la resta del acumulado dejaba 8,88e-16,
    5,000000000000001 o 0,1999999999999993. Se redondea a 2 decimales (el
    criterio del conciliador) y lo que queda en 0 es None (R2)."""
    assert [r.horas_extra_leidas for r in _registros(fila)] == esperado


# --------------------------------- R3 ----------------------------------- #

@pytest.mark.parametrize(("fila", "esperado"), [
    (_fila(8, None), [("normal", 8.0, None, None)]),
    (_fila(8, ""), [("normal", 8.0, None, None)]),
    (_fila(None, -2), [("extra", -2.0, None, None)]),
    (_fila(6, 0, [("P1", 2), ("P2", None)]),
     [("normal", 2.0, None, "P1"), ("normal", 4.0, None, "P2")]),
    (_fila(6, -1, [("P1", 2), ("P2", None)]),
     [("normal", 2.0, None, "P1"), ("normal", 4.0, None, "P2"),
      ("extra", -1.0, None, "P2")]),
    (_fila(6, -1, [("P1", 6)]),
     [("normal", 6.0, None, "P1"), ("extra", -1.0, None, None)]),
], ids=["8+null", "8+vacio", "solo-menos-2", "6+0-partidas",
        "6-1-partidas", "6-1-partida-justa"])
def test_f048_r3_sin_extras_positivas_como_hoy(fila, esperado) -> None:
    assert _resumen(fila) == esperado


def test_f048_r3_la_extra_negativa_conserva_su_codigo() -> None:
    (normal, extra) = _registros(_fila(8, -2))
    assert (normal.codigo_hora_propuesto, extra.codigo_hora_propuesto) == (
        "HL01", "HE01")


# --------------------------------- R4 ----------------------------------- #

def test_f048_r4_el_codigo_es_el_ordinario_nunca_el_extra() -> None:
    regs = _registros(_fila(4, 5, [("P1", 6), ("P2", None)]),
                      _fila(None, 10, numero_linea=2))
    assert [r.codigo_hora_propuesto for r in regs] == ["HL01"] * 3


def test_f048_r4_sin_codigo_ordinario_ninguno() -> None:
    (reg,) = _registros(_fila(None, 10, codigo_hora_ordinaria=None))
    assert reg.codigo_hora_propuesto is None


# --------------------------------- R5 ----------------------------------- #

def test_f048_r5_incidencia_line_index_y_campos_de_la_fila() -> None:
    regs = _registros(
        _fila(4, 5, numero_linea=3, categoria="Oficial 1a",
              confianza_pct=91, dni="1234567-l",
              incidencia={"codigo": "AT", "dias": 1}),
        {"nombre": "Persona Dos", "horas_ordinarias": None,
         "horas_extraordinarias": None},
        _fila(None, 2, nombre="Persona Tres", numero_linea=4))
    assert [(r.line_index, r.tipo_hora, r.horas, r.horas_extra_leidas)
            for r in regs] == [(0, "normal", 9.0, 5.0), (1, "AT", 1.0, None),
                               (2, "normal", 2.0, 2.0)]
    primero = regs[0]
    assert (primero.empleado_line_no, primero.categoria,
            primero.trabajador_nombre_leido, primero.trabajador_dni_leido,
            primero.confianza_pct, primero.es_incidencia) == (
        3, "Oficial 1a", "Persona Uno", "01234567L", 91.0, False)
    assert regs[1].es_incidencia is True


def test_f048_r5_la_fila_vacia_se_sigue_omitiendo() -> None:
    assert _registros({"horas_ordinarias": 0, "horas_extraordinarias": 0}) == []


# --------------------------------- R7 ----------------------------------- #

def _linea_info(caplog) -> str:
    return next(m for m in caplog.messages
                if m.startswith("[parte-normalizer] fecha="))


def test_f048_r7_info_cuenta_filas_y_horas_sumadas(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _registros(_fila(None, 10), _fila(4, 5, numero_linea=2),
                   _fila(8, -2, numero_linea=3), _fila(8, 0, numero_linea=4))
    linea = _linea_info(caplog)
    assert linea.endswith(" filas_extra_sumadas=2 horas_extra_sumadas=15.00")
    assert "registros=5" in linea


def test_f048_r7_info_sin_filas_sumadas(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _registros(_fila(8, None))
    assert _linea_info(caplog).endswith(
        "firmado=False filas_extra_sumadas=0 horas_extra_sumadas=0.00")


def test_f048_r7_info_con_decimales(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _registros(_fila(4, "2,25"), _fila(None, 0.5, numero_linea=2))
    assert _linea_info(caplog).endswith(
        "filas_extra_sumadas=2 horas_extra_sumadas=2.75")
