# tests/test_f045_reparto_dia.py
"""F-045 · el reparto de UN dia (recurso, fecha) entre obras y lineas.

`repartir_dia` (R7-R19, R22, R23, R26) recibe las lineas ordinarias y
extras del grupo ya marcadas como fijas o no y la jornada del dia, y
devuelve los ajustes (ordinaria = cuota, extra = horas - cuota).
`diferencias_ideal` (R25) mide que lineas congeladas cambiaria el reparto
ideal, sin aplicarlo. Datos sinteticos: obras 1, 2, 3 y jornada 8 salvo
que se diga otra cosa.
"""
from __future__ import annotations

import itertools

import pytest

from application.services.reparto_ponderado import (
    Ajuste,
    LineaDia,
    ResultadoDia,
    diferencias_ideal,
    repartir_dia,
)

A, B, C = 1, 2, 3


def _o(rid, obra, horas, *, fija=False, horas_orig=None) -> LineaDia:
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="ordinaria",
                    horas=horas, horas_orig=horas_orig, fija=fija)


def _e(rid, obra, horas, *, fija=False, extra_auto=False,
       base_id=None) -> LineaDia:
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="extra",
                    horas=horas, horas_orig=None, fija=fija,
                    extra_auto=extra_auto, base_id=base_id)


def _aj(resultado: ResultadoDia) -> dict[int, tuple[float, float]]:
    return {a.registro_id: (a.horas_norm, a.extra_horas)
            for a in resultado.ajustes}


# ------------------------------ R7 / R8 -------------------------------- #

def test_f045_r7_repartir_dia_las_ordinarias_finales_suman_la_jornada(
) -> None:
    lineas = [_o(1, A, 10.0), _o(2, B, 4.0), _o(3, C, 3.0)]
    res = repartir_dia(lineas, 8.0)
    finales = {ln.registro_id: ln.horas for ln in lineas}
    finales.update({k: v[0] for k, v in _aj(res).items()})
    assert res.cuadra is True
    assert sum(finales.values()) == 8.0
    for a in res.ajustes:
        assert a.horas_norm + a.extra_horas == a.horas_orig


def test_f045_r7_repartir_dia_el_ajuste_conserva_las_horas_originales(
) -> None:
    res = repartir_dia([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0)
    assert res.ajustes == (Ajuste(1, 5.5, 4.5, 10.0), Ajuste(2, 2.5, 1.5, 4.0))
    assert (res.paso, res.n_obras, res.n_lineas) == (0.5, 2, 2)


def test_f045_r8_repartir_dia_la_extra_explicita_nunca_cambia() -> None:
    res = repartir_dia([_o(1, A, 6.0), _o(2, B, 4.0), _e(3, B, 2.0)], 8.0)
    assert 3 not in _aj(res)


def test_f045_r8_repartir_dia_obra_sin_ordinarias_no_recibe_jornada(
) -> None:
    """La obra B solo trae extras: toda la jornada es de A."""
    res = repartir_dia([_o(1, A, 10.0), _e(2, B, 3.0)], 8.0)
    assert _aj(res) == {1: (8.0, 2.0)}
    assert res.n_obras == 1


# -------------------------------- R9 ----------------------------------- #

@pytest.mark.parametrize("horas,esperado", [
    (10.0, {1: (8.0, 2.0)}), (5.0, {1: (8.0, -3.0)}), (8.0, {})])
def test_f045_r9_repartir_dia_una_sola_ordinaria_como_hoy(
        horas, esperado) -> None:
    assert _aj(repartir_dia([_o(1, A, horas)], 8.0)) == esperado


# ------------------------------ R10-R19 -------------------------------- #

def test_f045_r10_r17_repartir_dia_dos_lineas_de_la_misma_obra() -> None:
    res = repartir_dia([_o(1, A, 6.0), _o(2, A, 4.0)], 8.0)
    assert _aj(res) == {1: (5.0, 1.0), 2: (3.0, 1.0)}
    assert (res.n_obras, res.n_lineas) == (1, 2)


def test_f045_r11_repartir_dia_ejemplo_1() -> None:
    assert _aj(repartir_dia([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0)) == {
        1: (5.5, 4.5), 2: (2.5, 1.5)}


def test_f045_r11_repartir_dia_ejemplo_1_llegando_al_reves() -> None:
    """Nunca A 8 + 2 y B 0 + 4, llegue antes quien llegue."""
    assert _aj(repartir_dia([_o(1, B, 4.0), _o(2, A, 10.0)], 8.0)) == {
        1: (2.5, 1.5), 2: (5.5, 4.5)}


def test_f045_r12_repartir_dia_ejemplo_2() -> None:
    assert _aj(repartir_dia([_o(1, A, 5.0), _o(2, B, 4.0)], 8.0)) == {
        1: (4.5, 0.5), 2: (3.5, 0.5)}


def test_f045_r13_repartir_dia_caso_real_sin_congelar() -> None:
    assert _aj(repartir_dia([_o(1, 678, 4.0), _o(2, 704, 8.0)], 8.0)) == {
        1: (2.5, 1.5), 2: (5.5, 2.5)}


def test_f045_r14_repartir_dia_jornada_incompleta_en_dos_obras() -> None:
    assert _aj(repartir_dia([_o(1, A, 4.0), _o(2, B, 3.0)], 8.0)) == {
        1: (4.5, -0.5), 2: (3.5, -0.5)}


def test_f045_r15_repartir_dia_empate_a_tres() -> None:
    lineas = [_o(1, A, 6.0), _o(2, B, 6.0), _o(3, C, 6.0)]
    assert _aj(repartir_dia(lineas, 8.0)) == {
        1: (3.0, 3.0), 2: (2.5, 3.5), 3: (2.5, 3.5)}


def test_f045_r16_repartir_dia_linea_pequena_sin_split() -> None:
    assert _aj(repartir_dia([_o(1, A, 9.5), _o(2, B, 0.5)], 8.0)) == {
        1: (7.5, 2.0)}


def test_f045_r18_repartir_dia_cuartos_de_hora() -> None:
    res = repartir_dia([_o(1, A, 7.75), _o(2, B, 2.0)], 8.0)
    assert res.paso == 0.25
    assert _aj(res) == {1: (6.25, 1.5), 2: (1.75, 0.25)}


def test_f045_r19_repartir_dia_extra_explicita_pesa_en_su_obra() -> None:
    res = repartir_dia([_o(1, A, 6.0), _o(2, B, 4.0), _e(3, B, 2.0)], 8.0)
    assert _aj(res) == {1: (4.0, 2.0)}


def test_f045_r19_repartir_dia_la_obra_llega_por_su_primera_linea() -> None:
    """La llegada de la obra es su registro_id minimo, aunque sea una
    extra: B (ids 1 y 4) llega antes que A (id 2) y gana el empate."""
    lineas = [_e(1, B, 0.0), _o(2, A, 6.0), _o(3, C, 6.0), _o(4, B, 6.0)]
    assert _aj(repartir_dia(lineas, 8.0)) == {
        2: (2.5, 3.5), 3: (2.5, 3.5), 4: (3.0, 3.0)}


# --------------------------- fijas: R22 / R26 --------------------------- #

def test_f045_r22_repartir_dia_reparte_el_residuo_de_lo_congelado() -> None:
    """4 h congeladas en A: quedan 4 de jornada para B (6) y C (2)."""
    lineas = [_o(1, A, 4.0, fija=True), _o(2, B, 6.0), _o(3, C, 2.0)]
    res = repartir_dia(lineas, 8.0)
    assert res.cuadra is True
    assert _aj(res) == {2: (3.0, 3.0), 3: (1.0, 1.0)}


def test_f045_r22_repartir_dia_la_extra_congelada_ni_pesa_ni_cuenta(
) -> None:
    lineas = [_o(1, A, 4.0), _e(2, A, 4.0, fija=True), _o(3, B, 4.0)]
    assert _aj(repartir_dia(lineas, 8.0)) == {}


def test_f045_r22_repartir_dia_la_ordinaria_congelada_de_la_misma_obra(
) -> None:
    """La congelada cuenta en el dia aunque comparta obra con la libre."""
    lineas = [_o(1, A, 2.0), _o(2, A, 4.0, fija=True)]
    assert _aj(repartir_dia(lineas, 8.0)) == {1: (4.0, -2.0)}


def test_f045_r24_repartir_dia_caso_real_congelado() -> None:
    """0678 congelada con 8 + (-4) y 0704 8 h nueva: 0704 0 + 8."""
    lineas = [_o(1, 678, 8.0, fija=True, horas_orig=4.0),
              _e(2, 678, -4.0, fija=True, extra_auto=True, base_id=1),
              _o(3, 704, 8.0)]
    assert _aj(repartir_dia(lineas, 8.0)) == {3: (0.0, 8.0)}


def test_f045_r26_repartir_dia_la_fija_por_pareja_no_se_toca() -> None:
    """Una base congelada POR SU PAREJA llega como fija: ni recibe split ni
    deja de contar."""
    lineas = [_o(1, A, 8.0, fija=True, horas_orig=10.0),
              _e(2, A, 2.0, fija=True, extra_auto=True, base_id=1),
              _o(3, B, 2.0)]
    res = repartir_dia(lineas, 8.0)
    assert _aj(res) == {3: (0.0, 2.0)}


def test_f045_r22_repartir_dia_ordinaria_a_cero_es_fija() -> None:
    res = repartir_dia([_o(1, A, 0.0), _o(2, B, 10.0)], 8.0)
    assert _aj(res) == {2: (8.0, 2.0)}
    assert (res.n_obras, res.n_lineas) == (1, 1)


def test_f045_r22_repartir_dia_ordinaria_negativa_es_fija_y_cuenta(
) -> None:
    res = repartir_dia([_o(1, A, -1.0), _o(2, B, 10.0)], 8.0)
    assert _aj(res) == {2: (9.0, 1.0)}


def test_f045_r22_repartir_dia_obra_de_peso_no_positivo_queda_fija(
) -> None:
    """A: 2 ordinarias y -3 de extra explicita (peso -1): su ordinaria es
    fija y cuenta; B se lleva el resto (6)."""
    lineas = [_o(1, A, 2.0), _e(2, A, -3.0), _o(3, B, 10.0)]
    res = repartir_dia(lineas, 8.0)
    assert _aj(res) == {3: (6.0, 4.0)}
    assert res.n_obras == 1


def test_f045_r22_repartir_dia_obra_de_peso_cero_queda_fija() -> None:
    lineas = [_o(1, A, 2.0), _e(2, A, -2.0), _o(3, B, 10.0)]
    assert _aj(repartir_dia(lineas, 8.0)) == {3: (6.0, 4.0)}


# -------------------------------- R23 ---------------------------------- #

def test_f045_r23_repartir_dia_residuo_negativo_no_cuadra() -> None:
    res = repartir_dia([_o(1, A, 9.0, fija=True), _o(2, B, 2.0)], 8.0)
    assert res.cuadra is False
    assert res.ajustes == ()


def test_f045_r23_repartir_dia_residuo_sin_ajustables_no_cuadra() -> None:
    res = repartir_dia([_o(1, A, 6.0, fija=True)], 8.0)
    assert (res.cuadra, res.ajustes) == (False, ())


def test_f045_r23_repartir_dia_residuo_cero_sin_ajustables_cuadra() -> None:
    res = repartir_dia([_o(1, A, 8.0, fija=True)], 8.0)
    assert (res.cuadra, res.ajustes) == (True, ())


def test_f045_r23_repartir_dia_residuo_cero_con_ajustables_cuadra() -> None:
    res = repartir_dia([_o(1, A, 8.0, fija=True), _o(2, B, 2.0)], 8.0)
    assert res.cuadra is True
    assert _aj(res) == {2: (0.0, 2.0)}


def test_f045_r23_repartir_dia_residuo_de_medio_paso_por_debajo() -> None:
    res = repartir_dia([_o(1, A, 8.5, fija=True), _o(2, B, 0.5)], 8.0)
    assert res.cuadra is False


# ------------------------- no laborable y orden ------------------------- #

def test_f045_r20_repartir_dia_jornada_cero_todo_a_extra() -> None:
    res = repartir_dia([_o(1, A, 6.0), _o(2, B, 4.0)], 0.0)
    assert _aj(res) == {1: (0.0, 6.0), 2: (0.0, 4.0)}


def test_f045_r29_repartir_dia_no_depende_del_orden() -> None:
    lineas = [_o(1, A, 6.0), _o(2, A, 3.5), _o(3, B, 5.0), _e(4, B, 1.0),
              _o(5, C, 2.25)]
    esperado = repartir_dia(lineas, 8.0)
    for perm in itertools.permutations(lineas):
        assert repartir_dia(list(perm), 8.0) == esperado
    assert [a.registro_id for a in esperado.ajustes] == sorted(
        a.registro_id for a in esperado.ajustes)


def test_f045_r28_repartir_dia_multiplos_del_paso() -> None:
    lineas = [_o(1, A, 7.75), _o(2, B, 3.5), _o(3, B, 1.25)]
    res = repartir_dia(lineas, 8.0)
    assert res.paso == 0.25
    for a in res.ajustes:
        assert (a.horas_norm / 0.25).is_integer()
        assert (a.extra_horas / 0.25).is_integer()


def test_f045_r3_repartir_dia_paso_por_jornada_de_centesimas() -> None:
    """Jornada 8,4 (42 h en 5 dias): paso 0,01 y suma exacta."""
    res = repartir_dia([_o(1, A, 6.0), _o(2, B, 4.0)], 8.4)
    assert res.paso == 0.01
    assert round(sum(a.horas_norm for a in res.ajustes), 6) == 8.4


# ========================== R25 · el ideal ============================== #
# Lo que cambiaria en las lineas CONGELADAS si se repartiera el dia entero
# como si nada estuviera en Sigrid. Solo se mide (F-046 lo aplicara).

def test_f045_r25_ideal_caso_real_0678_0704() -> None:
    """0678 congelada con 8 + (-4) (trabajo 4) y 0704 con 8: el ideal da a
    0678 2,5 + 1,5, asi que su base pasaria de 8 a 2,5 y su extra de -4 a
    1,5. La 0704 no se mide: no esta congelada."""
    lineas = [_o(1, 678, 8.0, fija=True, horas_orig=4.0),
              _e(2, 678, -4.0, fija=True, extra_auto=True, base_id=1),
              _o(3, 704, 8.0)]
    assert diferencias_ideal(lineas, 8.0) == ((1, 8.0, 2.5), (2, -4.0, 1.5))


def test_f045_r25_ideal_sin_congeladas_no_mide_nada() -> None:
    assert diferencias_ideal([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0) == ()


def test_f045_r25_ideal_que_coincide_no_da_diferencias() -> None:
    lineas = [_o(1, A, 4.0, fija=True), _o(2, B, 4.0)]
    assert diferencias_ideal(lineas, 8.0) == ()


def test_f045_r25_ideal_pareja_que_ya_es_ideal() -> None:
    lineas = [_o(1, A, 8.0, fija=True, horas_orig=10.0),
              _e(2, A, 2.0, fija=True, extra_auto=True, base_id=1)]
    assert diferencias_ideal(lineas, 8.0) == ()


def test_f045_r25_ideal_congelada_sin_pareja() -> None:
    lineas = [_o(1, A, 8.0, fija=True), _o(2, B, 2.0)]
    assert diferencias_ideal(lineas, 8.0) == ((1, 8.0, 6.5),)


def test_f045_r25_ideal_la_extra_explicita_congelada_no_se_mide() -> None:
    """Pesa en su obra (B 4 + 2) pero nunca cambia."""
    lineas = [_o(1, A, 6.0, fija=True), _o(2, B, 4.0),
              _e(3, B, 2.0, fija=True)]
    assert diferencias_ideal(lineas, 8.0) == ((1, 6.0, 4.0),)


def test_f045_r25_ideal_extra_huerfana_pesa_como_explicita() -> None:
    """Una extra automatica sin su base en el grupo pesa con sus horas:
    A = 2 + 6 = 8 frente a B 4 da a A 5,5 (sin ella, 5)."""
    lineas = [_e(1, A, 2.0, fija=True, extra_auto=True, base_id=99),
              _o(2, A, 6.0, fija=True), _o(3, B, 4.0)]
    assert diferencias_ideal(lineas, 8.0) == ((2, 6.0, 5.5),)


def test_f045_r25_ideal_extra_duplicada_de_la_pareja_iria_a_cero() -> None:
    """Dos extras congeladas de la misma base (F-037 R7): la primera es la
    de la pareja; la segunda sobra en el ideal."""
    lineas = [_o(1, A, 8.0, fija=True, horas_orig=10.0),
              _e(2, A, 2.0, fija=True, extra_auto=True, base_id=1),
              _e(3, A, 2.0, fija=True, extra_auto=True, base_id=1)]
    assert diferencias_ideal(lineas, 8.0) == ((3, 2.0, 0.0),)


def test_f045_r25_ideal_que_no_cuadra_no_mide() -> None:
    """Base congelada sin trabajo (horas_orig 0): el ideal no tiene nada
    ajustable con J' 8, no cuadra y no hay nada que comparar."""
    lineas = [_o(1, A, 2.0, fija=True, horas_orig=0.0)]
    assert diferencias_ideal(lineas, 8.0) == ()


def test_f045_r25_ideal_dia_no_laborable() -> None:
    lineas = [_o(1, A, 6.0, fija=True)]
    assert diferencias_ideal(lineas, 0.0) == ((1, 6.0, 0.0),)


def test_f045_r25_ideal_no_depende_del_orden() -> None:
    lineas = [_o(1, 678, 8.0, fija=True, horas_orig=4.0),
              _e(2, 678, -4.0, fija=True, extra_auto=True, base_id=1),
              _o(3, 704, 8.0)]
    for perm in itertools.permutations(lineas):
        assert diferencias_ideal(list(perm), 8.0) == (
            (1, 8.0, 2.5), (2, -4.0, 1.5))


# ================= refuerzo tras la campana de mutacion ================= #

def test_f045_r7_repartir_dia_resultados_inmutables() -> None:
    import dataclasses

    res = repartir_dia([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0)
    for obj in (res, res.ajustes[0], _o(1, A, 1.0)):
        with pytest.raises(dataclasses.FrozenInstanceError):
            obj.registro_id = 9  # type: ignore[misc,attr-defined]


def test_f045_r22_repartir_dia_ordinaria_a_cero_de_la_misma_obra_no_cuenta(
) -> None:
    """Una linea de 0 h es fija aunque comparta obra con una ajustable: no
    es una linea del reparto."""
    res = repartir_dia([_o(1, A, 0.0), _o(2, A, 10.0)], 8.0)
    assert _aj(res) == {2: (8.0, 2.0)}
    assert res.n_lineas == 1


def test_f045_r28_repartir_dia_la_extra_se_redondea_a_centesimas() -> None:
    """Como hoy: horas que no son de centesimas dan una extra a 2 decimales."""
    res = repartir_dia([_o(1, A, 7.333)], 8.0)
    assert res.paso == 0.01
    assert _aj(res) == {1: (8.0, -0.67)}


def test_f045_r25_ideal_la_extra_explicita_con_base_no_es_de_la_pareja(
) -> None:
    """`base_id` sin `extra_auto` no empareja: la extra explicita pesa en su
    obra (A = 10 + 2 frente a B 4 da a A 6) y nunca cambia."""
    lineas = [_o(1, A, 8.0, fija=True, horas_orig=10.0),
              LineaDia(registro_id=2, obra_ide=A, tipo="extra", horas=2.0,
                       fija=True, base_id=1),
              _o(3, B, 4.0)]
    assert diferencias_ideal(lineas, 8.0) == ((1, 8.0, 6.0),)


def test_f045_r25_ideal_la_extra_de_la_pareja_a_centesimas() -> None:
    """Trabajado 7,333 y 8 (paso 0,01): la base ideal es 3,83 y la extra
    de la pareja 7,333 - 3,83 = 3,503, que se da a centesimas (3,5)."""
    lineas = [_o(1, A, 8.0, fija=True, horas_orig=7.333),
              _e(2, A, -0.667, fija=True, extra_auto=True, base_id=1),
              _o(3, B, 8.0)]
    assert diferencias_ideal(lineas, 8.0) == (
        (1, 8.0, 3.83), (2, -0.667, 3.5))
