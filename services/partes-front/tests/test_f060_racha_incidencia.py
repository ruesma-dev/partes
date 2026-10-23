# tests/test_f060_racha_incidencia.py
"""F-060 · Regla pura de la racha de incidencia en sv4 (R2-R5, R7-R10),
`application/services/racha_incidencia.py`.

  - `ventana` (DA1): del dia 1 del mes anterior al de D hasta D - 1.
  - `hasta_delante`: el ultimo dia del mes siguiente al de D.
  - `decidir` (R2-R5, R9): el rol de una incidencia del dia D y, con
    `fin`, las lineas de la racha hacia atras y hacia delante.
  - `colapsar` (R7, R8): un solo `fin` por racha y un solo `inicio` por
    dia, persona y letra en una misma aprobacion.
  - `aviso_desordenada` (R10): el siguiente dia con lineas ya tiene una
    incidencia registrada.
  - `clave_incidencia` (DA4): la letra de la tabla o, si no, los codigos.

Sin BBDD. Personas, fechas e ids SINTETICOS.
"""
from __future__ import annotations

import inspect

import pytest
from application.services import racha_incidencia
from application.services.racha_incidencia import (
    DecisionRacha,
    LineaHist,
    LineaRol,
    aviso_desordenada,
    clave_incidencia,
    colapsar,
    decidir,
    hasta_delante,
    motivo_desordenada,
    ventana,
)
from tests.test_f025_deteccion import TABLA


def inc(rid: int, fecha: int, clave: str = "V", *, activa: bool = True,
        estado: str | None = None) -> LineaHist:
    return LineaHist(registro_id=rid, fecha_int=fecha, es_incidencia=True,
                     clave=clave, horas=0.0, sigrid_estado=estado,
                     activa=activa)


def trab(rid: int, fecha: int, horas: float | None = 8.0, *,
         activa: bool = True, estado: str | None = None) -> LineaHist:
    return LineaHist(registro_id=rid, fecha_int=fecha, es_incidencia=False,
                     clave="", horas=horas, sigrid_estado=estado,
                     activa=activa)


# ------------------------------ ventana ------------------------------ #

@pytest.mark.parametrize("d,esperada", [
    (20261015, (20260901, 20261014)),
    (20261001, (20260901, 20260930)),
    (20260101, (20251201, 20251231)),        # 1 de enero: diciembre
    (20260301, (20260201, 20260228)),
    (20280301, (20280201, 20280229)),        # bisiesto
    (20260131, (20251201, 20260130)),
])
def test_f060_r1_ventana(d, esperada) -> None:
    assert ventana(d) == esperada


@pytest.mark.parametrize("d,esperada", [
    (20261015, 20261130), (20261201, 20270131), (20261130, 20261231),
    (20260131, 20260228), (20280115, 20280229), (20251231, 20260131),
])
def test_f060_r9_hasta_delante(d, esperada) -> None:
    assert hasta_delante(d) == esperada


# --------------------------- decidir: el rol --------------------------- #

def test_f060_r2_sin_nada_en_la_ventana_es_inicio() -> None:
    assert decidir([], 20261004, "V") == DecisionRacha("inicio", ())


def test_f060_r2_lo_anterior_a_la_ventana_no_cuenta() -> None:
    assert decidir([inc(1, 20260831)], 20261004, "V").rol == "inicio"
    assert decidir([inc(1, 20260901)], 20261004, "V").rol == "fin"


def test_f060_r2_lo_del_mismo_dia_y_posterior_no_cuenta_para_el_rol() -> None:
    hist = [inc(1, 20261004), inc(2, 20261005), trab(3, 20261003)]
    assert decidir(hist, 20261004, "V").rol == "inicio"


def test_f060_r3_dia_trabajado_es_inicio() -> None:
    hist = [inc(1, 20261001), trab(2, 20261002)]
    assert decidir(hist, 20261003, "V").rol == "inicio"


def test_f060_r3_horas_negativas_tambien_es_trabajado() -> None:
    hist = [inc(1, 20261001), inc(3, 20261002), trab(2, 20261002, -1.0)]
    assert decidir(hist, 20261003, "V").rol == "inicio"


def test_f060_r3_incidencia_y_horas_el_mismo_dia_es_trabajado() -> None:
    hist = [inc(1, 20261002), trab(2, 20261002, 8.0)]
    assert decidir(hist, 20261003, "V").rol == "inicio"


def test_f060_r3_otra_letra_abre_racha() -> None:
    """DA4: V seguida de B cierra la V y abre la B con su CI*."""
    hist = [inc(1, 20261001, "V"), inc(2, 20261002, "V")]
    assert decidir(hist, 20261003, "B").rol == "inicio"
    assert decidir(hist, 20261003, "V").rol == "fin"


def test_f060_r3_dia_con_dos_letras_sigue_las_dos() -> None:
    hist = [inc(1, 20261002, "V"), inc(2, 20261002, "B")]
    assert decidir(hist, 20261003, "V").rol == "fin"
    assert decidir(hist, 20261003, "B").rol == "fin"


def test_f060_r4_racha_abierta_es_fin_sin_mirar_delante() -> None:
    hist = [inc(1, 20261001), inc(5, 20261005), inc(6, 20261006)]
    assert decidir(hist, 20261002, "V").rol == "fin"


def test_f060_r4_se_saltan_dias_sin_lineas_y_lineas_a_cero() -> None:
    """Viernes V; sabado y domingo sin parte; lunes solo una linea a 0 h:
    el martes sigue la racha."""
    hist = [trab(1, 20261001), inc(2, 20261002), trab(3, 20261005, 0.0),
            trab(4, 20261005, None)]
    assert decidir(hist, 20261006, "V").rol == "fin"


def test_f060_r5_la_papelera_no_cuenta() -> None:
    hist = [inc(1, 20261001), trab(2, 20261002, activa=False)]
    assert decidir(hist, 20261003, "V").rol == "fin"
    hist = [trab(1, 20261001), inc(2, 20261002, activa=False)]
    assert decidir(hist, 20261003, "V").rol == "inicio"


# ---------------------- decidir: la racha (R9) ---------------------- #

def test_f060_r9_racha_hacia_atras_y_hacia_delante() -> None:
    hist = [
        trab(10, 20261001),
        inc(20, 20261002), trab(21, 20261002, 0.0),
        inc(34, 20261002, activa=False, estado="encolado"),
        trab(35, 20261002, activa=False, estado="registrado"),
        inc(30, 20261003), inc(33, 20261003, "B"),
        inc(31, 20261003, activa=False, estado="registrado"),
        inc(32, 20261003, activa=False, estado="omitido"),
        inc(36, 20261003, "B", activa=False, estado="registrado"),
        inc(60, 20261006), inc(70, 20261007),
        trab(80, 20261008),
        inc(90, 20261009),
    ]
    d = decidir(hist, 20261005, "V")
    assert d == DecisionRacha("fin", (20, 30, 31, 34, 60, 70))


def test_f060_r9_el_dia_d_no_entra_en_la_racha() -> None:
    hist = [inc(1, 20261002), inc(2, 20261003), inc(3, 20261003)]
    assert decidir(hist, 20261003, "V").racha_registro_ids == (1,)


def test_f060_r9_hacia_atras_se_para_en_la_ventana() -> None:
    hist = [inc(i, f) for i, f in enumerate(
        (20260830, 20260831, 20260901, 20260915, 20261003), start=1)]
    assert decidir(hist, 20261004, "V").racha_registro_ids == (3, 4, 5)


def test_f060_r9_hacia_atras_se_para_en_otra_letra() -> None:
    hist = [inc(1, 20261001, "B"), inc(2, 20261002), inc(3, 20261003)]
    assert decidir(hist, 20261004, "V").racha_registro_ids == (2, 3)


def test_f060_r9_hacia_delante_hasta_el_mes_siguiente() -> None:
    hist = [inc(29, 20261029), inc(31, 20261031), inc(1130, 20261130),
            inc(1201, 20261201)]
    d = decidir(hist, 20261030, "V")
    assert d.racha_registro_ids == (29, 31, 1130)


def test_f060_r9_hacia_delante_se_para_en_otra_letra() -> None:
    hist = [inc(1, 20261001), inc(3, 20261003, "B"), inc(4, 20261004)]
    assert decidir(hist, 20261002, "V").racha_registro_ids == (1,)


def test_f060_r9_hacia_delante_salta_papelera_y_dias_a_cero() -> None:
    hist = [inc(1, 20261001), trab(3, 20261003, activa=False),
            trab(4, 20261004, 0.0), inc(5, 20261005)]
    assert decidir(hist, 20261002, "V").racha_registro_ids == (1, 5)


def test_f060_r9_el_inicio_va_sin_racha() -> None:
    hist = [trab(1, 20261001), inc(3, 20261003)]
    assert decidir(hist, 20261002, "V") == DecisionRacha("inicio", ())


def test_f060_r9_ids_sin_repetir_y_ordenados() -> None:
    hist = [inc(9, 20261002), inc(9, 20261002), inc(4, 20261003)]
    assert decidir(hist, 20261004, "V").racha_registro_ids == (4, 9)


# ------------------------------ colapsar ------------------------------ #

def rol(rid, fecha, r, racha=(), persona="dni:A", clave="V") -> LineaRol:
    return LineaRol(registro_id=rid, persona=persona, fecha_int=fecha,
                    clave=clave, rol=r, racha_registro_ids=tuple(racha))


def test_f060_r7_varios_fin_de_una_racha_solo_el_ultimo() -> None:
    lineas = [rol(1, 20261001, "inicio"),
              rol(2, 20261002, "fin", (1, 3, 4)),
              rol(4, 20261004, "fin", (1, 2, 3)),
              rol(3, 20261003, "fin", (1, 2, 4))]
    assert colapsar(lineas) == {1: "inicio", 2: "intermedio",
                                3: "intermedio", 4: "fin"}


def test_f060_r7_enlazados_aunque_solo_uno_vea_al_otro() -> None:
    lineas = [rol(2, 20261002, "fin", ()), rol(5, 20261005, "fin", (2,))]
    assert colapsar(lineas) == {2: "intermedio", 5: "fin"}
    assert colapsar(list(reversed(lineas))) == {2: "intermedio", 5: "fin"}


def test_f060_r7_dos_rachas_de_la_misma_letra_conservan_su_fin() -> None:
    lineas = [rol(2, 20261002, "fin", (1,)), rol(5, 20261005, "fin", (4,))]
    assert colapsar(lineas) == {2: "fin", 5: "fin"}


def test_f060_r7_mismo_dia_en_dos_obras_gana_el_menor_id() -> None:
    lineas = [rol(8, 20261004, "fin", (3,)), rol(7, 20261004, "fin", (3,)),
              rol(9, 20261004, "fin", ())]
    assert colapsar(lineas) == {7: "fin", 8: "intermedio", 9: "intermedio"}


def test_f060_r7_cadena_transitiva() -> None:
    lineas = [rol(1, 20261001, "fin", (2,)), rol(2, 20261002, "fin", ()),
              rol(3, 20261003, "fin", (2,))]
    assert colapsar(lineas)[3] == "fin"
    assert colapsar(lineas)[1] == "intermedio"


def test_f060_r7_otra_persona_u_otra_letra_no_se_juntan() -> None:
    lineas = [rol(2, 20261002, "fin", (5,)),
              rol(5, 20261005, "fin", (2,), persona="dni:B"),
              rol(6, 20261006, "fin", (2,), clave="B")]
    assert colapsar(lineas) == {2: "fin", 5: "fin", 6: "fin"}


def test_f060_r8_varios_inicio_del_mismo_dia_solo_el_menor() -> None:
    lineas = [rol(9, 20261001, "inicio"), rol(4, 20261001, "inicio"),
              rol(6, 20261001, "inicio", clave="B"),
              rol(7, 20261001, "inicio", persona="dni:B"),
              rol(5, 20261002, "inicio")]
    assert colapsar(lineas) == {9: "intermedio", 4: "inicio", 6: "inicio",
                                7: "inicio", 5: "inicio"}


def test_f060_r7_otros_roles_se_conservan() -> None:
    assert colapsar([rol(1, 20261001, "intermedio")]) == {1: "intermedio"}
    assert colapsar([]) == {}


# ------------------------- aviso_desordenada ------------------------- #

def test_f060_r10_siguiente_dia_con_incidencia_registrada() -> None:
    hist = [trab(1, 20261002), inc(3, 20261005, estado="registrado")]
    assert aviso_desordenada(hist, 20261002) == 20261005


@pytest.mark.parametrize("hist", [
    [],                                                   # nada despues
    [trab(1, 20261003), inc(3, 20261005, estado="registrado")],
    [inc(3, 20261005, estado="encolado")],
    [inc(3, 20261005, estado="registrado", activa=False)],
    [inc(3, 20261201, estado="registrado")],              # fuera de plazo
    [inc(3, 20261002, estado="registrado")],              # el mismo dia
    [trab(3, 20261005, estado="registrado")],             # no incidencia
])
def test_f060_r10_sin_aviso(hist) -> None:
    assert aviso_desordenada(hist, 20261002) is None


def test_f060_r10_salta_dias_vacios_y_a_cero() -> None:
    hist = [trab(1, 20261003, 0.0), inc(2, 20261130, estado="registrado")]
    assert aviso_desordenada(hist, 20261002) == 20261130


def test_f060_r10_motivo() -> None:
    texto = motivo_desordenada(20261005)
    assert texto.startswith("racha_desordenada: ")
    assert "2026-10-05" in texto and len(texto) <= 255


# --------------------------- clave (DA4) --------------------------- #

@pytest.mark.parametrize("inc_cod,hora,tabla,esperada", [
    ("V", "CIV", TABLA, "V"),
    (" v ", None, TABLA, "V"),
    (None, "CIV", TABLA, "V"),           # por el codigo de Sigrid
    ("Q", "CIQ", TABLA, "Q"),            # la tabla no la conoce
    (None, "CIQ", TABLA, "CIQ"),
    ("V", "CIV", None, "V"),             # sin tabla
    (None, " ciz ", None, "CIZ"),
    (None, None, None, ""),
])
def test_f060_r3_clave_de_incidencia(inc_cod, hora, tabla, esperada) -> None:
    assert clave_incidencia(inc_cod, hora, tabla) == esperada


def test_f060_regla_pura_sin_bbdd() -> None:
    fuente = inspect.getsource(racha_incidencia)
    for prohibido in ("sqlalchemy", "session", "select(", "httpx"):
        assert prohibido not in fuente


# ===================== R28 · motivo de la linea movida ===================== #

def test_f060_r28_motivo_fin_movido() -> None:
    from application.services.racha_incidencia import motivo_fin_movido
    assert motivo_fin_movido(9000, 20261004) == (
        "fin_movido: el fin de la incidencia (CIZ, linea 9000) paso al dia "
        "2026-10-04")
    # Sin fecha legible no rompe: el dia sale como «?».
    assert motivo_fin_movido(9000, None).endswith("paso al dia ?")
    assert len(motivo_fin_movido("9" * 400, 20261004)) == 255
