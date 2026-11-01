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


# ====================== Repositorio (R1-R5, R24) ====================== #

from sqlalchemy import event  # noqa: E402

from infrastructure.database.parte_repository import (  # noqa: E402
    ParteReviewRepository,
)
from tests.dobles import estados_sigrid  # noqa: E402
from tests.test_f025_aprobacion import CLAVES_LINEA, DNI_B, OBRA_20  # noqa: E402
from tests.test_f025_deteccion import TABLA  # noqa: E402
from tests.test_f060_aprobacion_racha import (  # noqa: E402
    _con_ciz,
    _fabrica,
    _linea,
    _marcar,
    _resultado,
    _roles,
    _t,
    _v,
)


def _datos(fabrica, ids, *, mover=True) -> dict:
    return ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=TABLA, mover_ciz=mover)


def _ciz(datos) -> dict[int, bool]:
    return {l["registro_id"]: l["ciz_mismo_dia"] for l in datos["lineas"]}


def test_f062_r1_un_dia_suelto_lleva_ciz_y_lista_vacia() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    _t(f, 2)
    l1 = _linea(_datos(f, [d1]), d1)
    assert (l1["incidencia_rol"], l1["ciz_mismo_dia"],
            l1["racha_registro_ids"]) == ("inicio", True, [])


def test_f062_r1_aprobar_el_inicio_con_la_racha_ingerida_delante() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2, d3, d4 = (_v(f, n) for n in (2, 3, 4))
    _t(f, 5)
    l1 = _linea(_datos(f, [d1]), d1)
    assert (l1["incidencia_rol"], l1["ciz_mismo_dia"],
            l1["racha_registro_ids"]) == ("inicio", True, [d2, d3, d4])


def test_f062_r1_tramo_con_papelera_registrada() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2 = _v(f, 2, estado="registrado")
    with f.create_session() as s:
        from datetime import datetime, timezone
        from infrastructure.database.orm_models import ParteRegistroOrm
        s.get(ParteRegistroOrm, d2).deleted_at_utc = datetime.now(
            timezone.utc)
        s.commit()
    d3 = _v(f, 3)
    l1 = _linea(_datos(f, [d1]), d1)
    assert l1["racha_registro_ids"] == [d2, d3]


def test_f062_r2_todo_de_una_vez_el_inicio_sin_ciz() -> None:
    """M4: dias 1-4 en una aprobacion: el 1 sin hermano (su `fin`, el 4,
    escribe el CIZ); la lista del 4 no cambia (R3)."""
    f = _fabrica()
    d1, d2, d3, d4 = (_v(f, n) for n in (1, 2, 3, 4))
    datos = _datos(f, [d1, d2, d3, d4])
    assert _roles(datos) == {d1: "inicio", d2: "intermedio",
                             d3: "intermedio", d4: "fin"}
    assert _ciz(datos) == {d1: False, d2: False, d3: False, d4: False}
    assert _linea(datos, d4)["racha_registro_ids"] == [d1, d2, d3]
    assert _linea(datos, d1)["racha_registro_ids"] == [d2, d3, d4]
    assert _linea(datos, d2)["racha_registro_ids"] == []


def test_f062_r2_el_fin_de_otra_obra_tambien_cuenta() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2 = _v(f, 2, obra=OBRA_20)
    datos = _datos(f, [d1, d2])
    assert _roles(datos) == {d1: "inicio", d2: "fin"}
    assert _ciz(datos) == {d1: False, d2: False}
    assert len(datos["grupos"]) == 2


def test_f062_r2_el_fin_de_otra_persona_no_cuenta() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    b1 = _v(f, 1, dni=DNI_B, doc="b1")
    b2 = _v(f, 2, dni=DNI_B, doc="b2")
    datos = _datos(f, [d1, b2])
    assert _ciz(datos) == {d1: True, b2: False}
    assert _linea(datos, b2)["racha_registro_ids"] == [b1]


def test_f062_r3_trabajo_fin_e_intermedio_sin_ciz() -> None:
    f = _fabrica()
    d1 = _v(f, 1, estado="registrado")
    d2 = _v(f, 2)
    t3 = _t(f, 3)
    datos = _datos(f, [d2, t3])
    assert _roles(datos) == {d2: "fin"}
    assert _ciz(datos) == {d2: False, t3: False}
    assert _linea(datos, d2)["racha_registro_ids"] == [d1]
    assert _linea(datos, t3)["racha_registro_ids"] == []


def test_f062_r4_apagado_sin_ciz_y_listas_vacias() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2, d3 = _v(f, 2), _v(f, 3)
    datos = _datos(f, [d1], mover=False)
    assert _ciz(datos) == {d1: False}
    assert _linea(datos, d1)["racha_registro_ids"] == []
    datos = _datos(f, [d1, d2, d3], mover=False)
    assert set(_ciz(datos).values()) == {False}
    assert all(l["racha_registro_ids"] == [] for l in datos["lineas"])


def test_f062_r4_por_defecto_apagado() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    datos = ParteReviewRepository(f).lineas_para_registro(
        [d1], incidencias=TABLA)
    assert _ciz(datos) == {d1: False}


def test_f062_r1_claves_de_la_linea() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    for mover in (True, False):
        datos = _datos(f, [d1], mover=mover)
        assert all(set(l) == CLAVES_LINEA for l in datos["lineas"])
        assert "ciz_mismo_dia" in CLAVES_LINEA


def test_f062_r5_sin_consultas_nuevas() -> None:
    """La misma consulta por persona que F-060 (R12) y el mismo numero de
    sentencias que con F-060 (5, medido en la rama antes de T10)."""
    f = _fabrica()
    ids = [_v(f, n) for n in (1, 2, 3, 4)] + [_t(f, 5)]
    ids += [_v(f, n, dni=DNI_B, doc=f"b{n}") for n in (1, 2)]
    vistos: list[str] = []

    @event.listens_for(f.engine, "before_cursor_execute")
    def _apuntar(conn, cursor, statement, params, context, many):
        vistos.append(statement)
    datos = _datos(f, [ids[0], ids[5]])
    assert _ciz(datos) == {ids[0]: True, ids[5]: True}
    assert len(vistos) == 5
    assert sum("BETWEEN" in v for v in vistos) == 2


def test_f062_r24_el_hermano_movido_no_toca_el_inicio() -> None:
    """El siguiente dia mueve el hermano: la escrita no trae `movida_de`;
    X sigue `registrado` con el `ide` de su CI* y D queda `registrado` con
    el del CIZ."""
    f = _fabrica()
    x = _con_ciz(f, _v(f, 1), ide=8000)
    d = _v(f, 2)
    r = _resultado(d, x, ide=8001)
    del r["escritas"][0]["movida_de"]
    _marcar(f, r)
    est = estados_sigrid(f, [x, d])
    assert est[x][0] == "registrado" and est[x][3] == 8000
    assert est[d][0] == "registrado" and est[d][3] == 8001


def test_f062_r24_ciz_hmores_ide_no_se_guarda() -> None:
    f = _fabrica()
    x = _v(f, 1)
    r = _resultado(x, None, ide=8000, hora_codigo="CIV",
                   ciz_hmores_ide=8001)
    del r["escritas"][0]["movida_de"]
    _marcar(f, r)
    est = estados_sigrid(f, [x])
    assert est[x] == ("registrado", None, 901, 8000, "PT26/00010")
