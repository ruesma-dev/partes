# tests/test_f062_inicio_con_ciz.py
"""F-062 · sv4 marca el `inicio` que escribe CI* y CIZ el mismo dia
(R1-R5, R24).

  - Puro (`racha_incidencia.py`): `racha_delante` (R1: el tramo delante del
    inicio, con su papelera) e `inicios_con_ciz` (R2: sin hermano si su
    `fin` viaja en la misma aprobacion).

Sin BBDD en los puros. Personas, fechas e ids SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.racha_incidencia import (
    FIN,
    INICIO,
    INTERMEDIO,
    LineaRol,
    inicios_con_ciz,
    racha_delante,
)
from tests.test_f060_racha_incidencia import inc, trab

D = 20261004


# =============================== Puro =============================== #

def test_f062_r1_puro_tramo_hasta_el_primer_dia_que_no_es_de_la_racha() -> None:
    hist = [inc(1, D), inc(2, D + 1), inc(3, D + 2), trab(4, D + 3),
            inc(5, D + 4)]
    assert racha_delante(hist, D, "V") == (2, 3)


def test_f062_r1_puro_sin_tramo_vacio() -> None:
    assert racha_delante([inc(1, D)], D, "V") == ()
    assert racha_delante([], D, "V") == ()


@pytest.mark.parametrize("corte", [trab(9, D + 1), inc(9, D + 1, "B")])
def test_f062_r1_puro_corta_por_trabajo_o_por_otra_letra(corte) -> None:
    assert racha_delante([corte, inc(2, D + 2)], D, "V") == ()


def test_f062_r1_puro_salta_los_dias_sin_lineas() -> None:
    hist = [inc(2, D + 1), trab(3, D + 2, 0.0), inc(4, D + 4),
            trab(5, D + 5)]
    assert racha_delante(hist, D, "V") == (2, 4)


def test_f062_r1_puro_dia_trabajado_con_incidencia_corta() -> None:
    hist = [inc(2, D + 1), inc(3, D + 2), trab(4, D + 2), inc(5, D + 3)]
    assert racha_delante(hist, D, "V") == (2,)


def test_f062_r1_puro_solo_las_lineas_de_la_clave() -> None:
    hist = [inc(2, D + 1), inc(3, D + 1, "B"), inc(4, D + 1), inc(5, D + 2)]
    assert racha_delante(hist, D, "V") == (2, 4, 5)


def test_f062_r1_puro_lo_anterior_y_el_propio_dia_no_cuentan() -> None:
    hist = [inc(1, D - 1), inc(7, D), inc(2, D + 1)]
    assert racha_delante(hist, D, "V") == (2,)


def test_f062_r1_puro_papelera_no_corta_ni_cuenta_como_dia() -> None:
    hist = [inc(2, D + 1), trab(3, D + 2, activa=False), inc(4, D + 3)]
    assert racha_delante(hist, D, "V") == (2, 4)


@pytest.mark.parametrize("linea,viaja", [
    (inc(8, D + 2, activa=False, estado="registrado"), True),
    (inc(8, D + 2, activa=False, estado="encolado"), True),
    (inc(8, D + 3, activa=False, estado="registrado"), True),
    (inc(8, D + 2, activa=False, estado="pendiente"), False),
    (inc(8, D + 2, activa=False), False),
    (inc(8, D + 2, "B", activa=False, estado="registrado"), False),
    (inc(8, D + 4, activa=False, estado="registrado"), False),
    (inc(8, D, activa=False, estado="registrado"), False),
    (inc(8, D - 1, activa=False, estado="registrado"), False),
    (trab(8, D + 2, activa=False, estado="registrado"), False),
])
def test_f062_r1_puro_papelera_del_tramo(linea, viaja) -> None:
    """La papelera de la clave `registrado`/`encolado` con fecha en
    (D, ultimo dia del tramo], tambien de los dias saltados."""
    hist = [inc(2, D + 1), inc(3, D + 3), trab(4, D + 4), linea]
    esperado = (2, 3, 8) if viaja else (2, 3)
    assert racha_delante(hist, D, "V") == esperado


def test_f062_r1_puro_sin_tramo_la_papelera_no_viaja() -> None:
    hist = [inc(8, D + 1, activa=False, estado="registrado"),
            trab(4, D + 2)]
    assert racha_delante(hist, D, "V") == ()


def test_f062_r1_puro_hasta_el_ultimo_dia_del_mes_siguiente() -> None:
    d = 20261031
    hist = [inc(i, f) for i, f in ((1, 20261101), (2, 20261130),
                                   (3, 20261201))]
    hist += [inc(i, 20261100 + i) for i in range(4, 30)]
    assert racha_delante(hist, d, "V")[:2] == (1, 2)
    assert 3 not in racha_delante(hist, d, "V")


def test_f062_r1_puro_diciembre_a_enero() -> None:
    hist = [inc(1, 20270101), inc(2, 20270102), trab(3, 20270103)]
    assert racha_delante(hist, 20261231, "V") == (1, 2)


def test_f062_r1_puro_ordenada_y_sin_repetidos() -> None:
    hist = [inc(9, D + 2), inc(2, D + 1), inc(2, D + 1),
            inc(5, D + 2, activa=False, estado="registrado")]
    assert racha_delante(hist, D, "V") == (2, 5, 9)


def _rol(rid, rol, *, persona="dni:1", fecha=D, clave="V",
         racha=()) -> LineaRol:
    return LineaRol(registro_id=rid, persona=persona, fecha_int=fecha,
                    clave=clave, rol=rol, racha_registro_ids=tuple(racha))


def test_f062_r1_puro_inicio_solo_lleva_ciz() -> None:
    lineas = [_rol(1, INICIO)]
    assert inicios_con_ciz(lineas, {1: INICIO}) == {1}


def test_f062_r2_puro_su_fin_en_la_misma_aprobacion() -> None:
    lineas = [_rol(1, INICIO), _rol(4, FIN, fecha=D + 3, racha=[1, 2, 3])]
    assert inicios_con_ciz(lineas, {1: INICIO, 4: FIN}) == set()


@pytest.mark.parametrize("fin", [
    _rol(4, FIN, fecha=D + 3, racha=[2, 3]),                # otra racha
    _rol(4, FIN, fecha=D + 3, racha=[1], persona="dni:2"),  # otra persona
    _rol(4, FIN, fecha=D + 3, racha=[1], clave="B"),        # otra clave
])
def test_f062_r2_puro_un_fin_ajeno_no_lo_quita(fin) -> None:
    assert inicios_con_ciz([_rol(1, INICIO), fin],
                           {1: INICIO, 4: FIN}) == {1}


def test_f062_r2_puro_solo_cuentan_los_roles_finales() -> None:
    """Un `fin` colapsado a `intermedio` no quita el hermano; un `inicio`
    colapsado a `intermedio` no lo lleva."""
    lineas = [_rol(1, INICIO), _rol(4, FIN, fecha=D + 3, racha=[1]),
              _rol(2, INICIO)]
    assert inicios_con_ciz(lineas, {1: INICIO, 4: INTERMEDIO,
                                    2: INTERMEDIO}) == {1}


def test_f062_r2_puro_varios_inicios() -> None:
    lineas = [_rol(1, INICIO), _rol(10, INICIO, fecha=D + 9),
              _rol(12, FIN, fecha=D + 11, racha=[10, 11])]
    assert inicios_con_ciz(lineas, {1: INICIO, 10: INICIO,
                                    12: FIN}) == {1}
