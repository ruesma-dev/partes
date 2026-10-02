# tests/test_f025_deteccion.py
"""F-025 · deteccion de incidencia y horas el mismo dia (R4-R8).

Funcion pura: ni BBDD ni red. Personas y fechas sinteticas.
"""
from __future__ import annotations

from application.services.incidencias_horas import (
    NIVEL_AVISO,
    NIVEL_BLOQUEO,
    Incompatibilidad,
    LineaDia,
    detectar,
    parsear_tabla,
    resumen_por_dia,
)
from tests.test_f025_tabla import _datos_validos

TABLA = parsear_tabla(dict(_datos_validos(), M={
    "sigrid": "CIM", "nombre": "Maternidad/Paternidad",
    "clase": "dia_completo"}, FJ={
    "sigrid": "CIP", "nombre": "Permiso", "clase": "parcial"}))

DIA = 20260302


def inc(rid: int, letra: str | None, *, hora_codigo: str | None = None,
        persona: str = "dni:A", fecha: int | None = DIA) -> LineaDia:
    return LineaDia(registro_id=rid, persona=persona, fecha_int=fecha,
                    es_incidencia=True, incidencia_codigo=letra,
                    hora_codigo=hora_codigo, es_extra=False, horas=None)


def hor(rid: int, horas: float | None = 8.0, *, extra: bool = False,
        persona: str = "dni:A", fecha: int | None = DIA) -> LineaDia:
    return LineaDia(registro_id=rid, persona=persona, fecha_int=fecha,
                    es_incidencia=False, incidencia_codigo=None,
                    hora_codigo="HE01" if extra else "HL01",
                    es_extra=extra, horas=horas)


def niveles(resultado: dict) -> dict[int, str]:
    return {rid: i.nivel for rid, i in resultado.items()}


# ============================ R5 · bloqueo ============================= #

def test_f025_r5_dia_completo_y_ordinarias_bloquea_todas_las_lineas() -> None:
    r = detectar([inc(1, "M"), hor(2, 8.0), hor(3, 2.0, extra=True)], TABLA)
    assert niveles(r) == {1: NIVEL_BLOQUEO, 2: NIVEL_BLOQUEO,
                          3: NIVEL_BLOQUEO}
    assert r[1].motivo == (
        "Maternidad/Paternidad (M) es de día completo y ese día hay 10 h de "
        "trabajo: deja solo una de las dos")
    assert r[1] == r[2] == r[3]


def test_f025_r5_dia_completo_con_solo_una_extra() -> None:
    r = detectar([inc(1, "V"), hor(2, 1.5, extra=True)], TABLA)
    assert niveles(r) == {1: NIVEL_BLOQUEO, 2: NIVEL_BLOQUEO}
    assert "Vacaciones (V)" in r[2].motivo
    assert "1.5 h de trabajo" in r[2].motivo


def test_f025_r5_la_clase_sale_del_codigo_de_hora_sin_letra() -> None:
    r = detectar([inc(1, None, hora_codigo="CIF"), hor(2)], TABLA)
    assert niveles(r) == {1: NIVEL_BLOQUEO, 2: NIVEL_BLOQUEO}
    assert "(F)" in r[1].motivo


def test_f025_r5_varias_incidencias_se_nombran_en_orden_de_letra() -> None:
    r = detectar([inc(1, "V"), inc(2, "M"), inc(3, "V"), hor(4)], TABLA)
    assert r[4].motivo.startswith(
        "Maternidad/Paternidad (M) y Vacaciones (V) son de día completo")


# ============================= R6 · aviso ============================== #

def test_f025_r6_parcial_y_extra_positiva_avisa_en_todas() -> None:
    r = detectar([inc(1, "FJ"), hor(2, 6.0), hor(3, 2.0, extra=True)], TABLA)
    assert niveles(r) == {1: NIVEL_AVISO, 2: NIVEL_AVISO, 3: NIVEL_AVISO}
    assert r[3].motivo == ("Permiso (FJ) y 2 h extra el mismo día: "
                           "comprueba que sean correctas")


def test_f025_r6_suma_solo_las_extras_positivas() -> None:
    r = detectar([inc(1, "AT"), hor(2, 2.0, extra=True),
                  hor(3, 0.5, extra=True), hor(4, -1.0, extra=True)], TABLA)
    assert r[1].nivel == NIVEL_AVISO
    assert "(AT) y 2.5 h extra" in r[1].motivo


# =========================== R7 · compatibles ========================== #

def test_f025_r7_combinaciones_compatibles_no_llevan_nivel() -> None:
    casos = [
        [inc(1, "FJ"), hor(2, 8.0)],                       # parcial + ord.
        [inc(1, "FJ"), hor(2, -2.0, extra=True)],          # extra negativa
        [inc(1, "M")],                                     # sin horas
        [hor(1, 8.0), hor(2, 2.0, extra=True)],            # sin incidencia
        [inc(1, "V"), inc(2, "B")],                        # varias, sin h
        [inc(1, "M"), hor(2, 0.0), hor(3, None, extra=True)],  # 0 o sin h
        [inc(1, "AT"), hor(2, 0.0, extra=True)],           # extra a 0
        [inc(1, None, hora_codigo="CIZ"), hor(2, 8.0)],    # CIZ sin clase
        [inc(1, "Z"), hor(2, 8.0)],                        # letra ajena
    ]
    for lineas in casos:
        assert detectar(lineas, TABLA) == {}, lineas


def test_f025_r4_otra_persona_u_otro_dia_no_cuentan() -> None:
    r = detectar([inc(1, "M"), hor(2, persona="dni:B"),
                  hor(3, fecha=DIA + 1),
                  inc(4, "M", persona="nom-X"), hor(5, persona="nom-X")],
                 TABLA)
    assert niveles(r) == {4: NIVEL_BLOQUEO, 5: NIVEL_BLOQUEO}


def test_f025_r4_las_lineas_sin_fecha_no_entran() -> None:
    assert detectar([inc(1, "M", fecha=None), hor(2, fecha=None)],
                    TABLA) == {}
    assert detectar([inc(1, "M", fecha=0), hor(2, fecha=0)], TABLA) == {}


def test_f025_r4_cada_dia_se_evalua_por_separado() -> None:
    r = detectar([inc(1, "M"), hor(2),
                  inc(3, "FJ", fecha=DIA + 1), hor(4, 1.0, extra=True,
                                                   fecha=DIA + 1),
                  inc(5, "M", fecha=DIA + 2)], TABLA)
    assert niveles(r) == {1: NIVEL_BLOQUEO, 2: NIVEL_BLOQUEO,
                          3: NIVEL_AVISO, 4: NIVEL_AVISO}


# ====================== R8 · bloqueo sobre aviso ======================= #

def test_f025_r8_si_cumple_los_dos_manda_el_bloqueo() -> None:
    r = detectar([inc(1, "FJ"), inc(2, "B"), hor(3, 2.0, extra=True)], TABLA)
    assert niveles(r) == {1: NIVEL_BLOQUEO, 2: NIVEL_BLOQUEO,
                          3: NIVEL_BLOQUEO}
    assert "(B)" in r[1].motivo and "(FJ)" not in r[1].motivo


# =========================== resumen por dia =========================== #

def test_f025_resumen_por_dia_gana_el_bloqueo() -> None:
    b = Incompatibilidad(NIVEL_BLOQUEO, "b")
    a = Incompatibilidad(NIVEL_AVISO, "a")
    a2 = Incompatibilidad(NIVEL_AVISO, "a2")
    assert resumen_por_dia([("d1", a), ("d1", b), ("d1", a),
                            ("d2", a), ("d2", a2),
                            ("d3", b), ("d3", a)]) == {
        "d1": b, "d2": a, "d3": b}
    assert resumen_por_dia([]) == {}


# ================= Mutacion: supervivientes cazados ==================== #

def test_f025_r6_las_horas_del_motivo_van_con_dos_decimales() -> None:
    r = detectar([inc(1, "FJ"), hor(2, 1.234, extra=True)], TABLA)
    assert "(FJ) y 1.23 h extra" in r[1].motivo
