# tests/test_f049_e12_otra_obra.py
"""F-049 · R40: lo que ya hace sv3 con otra obra del mismo día (E12).

Caracterización, sin tocar código de sv3: cuando el editor de celda de
sv4 añade una ordinaria a la obra Y y pide el recálculo, la pasada de sv3
es COMPLETA y reparte la jornada del (recurso, día) entre las obras
(F-045) o propone el reajuste de lo congelado (F-046). El otro día de la
semana no cambia. Casos E12a/b/c de `requirements.md`, con las cifras de
`repartir_dia` y `proponer_dia` reales; el ciclo entero, con el
repositorio real sobre SQLite en memoria. Datos sintéticos.
"""
from __future__ import annotations

import json

from application.services.reparto_ponderado import (
    LineaDia,
    proponer_dia,
    repartir_dia,
)
from infrastructure.database.orm_models import (
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from sqlalchemy import select
from tests.dobles import FabricaSesionSqlite, registro, sembrar_lineas
from tests.test_f045_conciliar import _splits
from tests.test_f046_conciliar import _conciliador

Y, X = 678, 686
LUNES, MARTES = 20260302, 20260303
RECURSO = 501


# ======================= núcleo puro (F-045 / F-046) ==================== #

def _o(rid, obra, horas, *, fija=False, reaj=False):
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="ordinaria",
                    horas=horas, horas_orig=None, fija=fija,
                    reajustable=reaj)


def _e(rid, obra, horas):
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="extra",
                    horas=horas, horas_orig=None, fija=False)


def test_f049_r40_e12a_repartir_dia_entre_y_y_x():
    """Y: 2 ord. nueva + 2 extra explícita; X: 8 ord. libre."""
    res = repartir_dia([_o(1, Y, 2.0), _e(2, Y, 2.0), _o(3, X, 8.0)], 8.0)
    assert {a.registro_id: (a.horas_norm, a.extra_horas)
            for a in res.ajustes} == {1: (2.5, -0.5), 3: (5.5, 2.5)}


def test_f049_r40_e12b_x_congelada_y_absorbe_lo_que_queda():
    res = repartir_dia([_o(1, Y, 2.0), _e(2, Y, 2.0),
                        _o(3, X, 8.0, fija=True)], 8.0)
    assert {a.registro_id: (a.horas_norm, a.extra_horas)
            for a in res.ajustes} == {1: (0.0, 2.0)}


def test_f049_r40_e12c_proponer_dia_con_x_registrada():
    p = proponer_dia([_o(1, Y, 2.0), _e(2, Y, 2.0),
                      _o(3, X, 8.0, fija=True, reaj=True)], 8.0)
    assert {a.registro_id: (a.horas_norm, a.extra_horas)
            for a in p.ajustes} == {1: (2.5, -0.5)}
    assert [(c.registro_id, c.base_registro_id, c.tipo, c.antes, c.despues)
            for c in p.cambios] == [(3, 3, "ordinaria", 8.0, 5.5),
                                    (None, 3, "extra", 0.0, 2.5)]


# ============== `_reclasificar_extras_jornada` (dobles) ================= #

def _resumen(splits):
    return sorted((s["normal_id"], s["horas_norm"], s["extra_horas"])
                  for s in splits)


def _semana(*, x_registrada: bool = False):
    """E12 el lunes y la misma obra X el martes (otro día de la semana)."""
    estado = "registrado" if x_registrada else None
    return [
        registro(1, fecha_int=LUNES, horas=2.0, obra_ide=Y,
                 document_id="d-y"),
        registro(2, fecha_int=LUNES, horas=2.0, tipo="extra", obra_ide=Y,
                 document_id="d-y"),
        registro(3, fecha_int=LUNES, horas=8.0, obra_ide=X,
                 document_id="d-x", sigrid_estado=estado),
        registro(4, fecha_int=MARTES, horas=9.0, obra_ide=X,
                 document_id="d-x2"),
    ]


def test_f049_r40_e12a_la_pasada_reparte_y_y_x_y_no_toca_el_martes():
    assert _resumen(_splits(_semana())) == [
        (1, 2.5, -0.5), (3, 5.5, 2.5), (4, 8.0, 1.0)]


def test_f049_r40_el_martes_da_lo_mismo_sin_la_linea_nueva():
    sin_y = [r for r in _semana() if r["registro_id"] != 1]
    assert (4, 8.0, 1.0) in _resumen(_splits(sin_y))
    assert (4, 8.0, 1.0) in _resumen(_splits(_semana()))


def test_f049_r40_e12b_x_congelada_no_se_toca():
    assert _resumen(_splits(_semana(x_registrada=True))) == [
        (1, 0.0, 2.0), (4, 8.0, 1.0)]


# ================= ciclo completo (`conciliar_todos`) =================== #

def _sembrar(fabrica, *, x_registrada: bool) -> dict:
    ids = {}
    ids["y_ord"], ids["y_ext"] = sembrar_lineas(fabrica, [
        {"horas": 2.0, "recurso_ide": RECURSO},
        {"horas": 2.0, "tipo": "extra", "recurso_ide": RECURSO}],
        document_id="d-y", obra_ide=Y, fecha="2026-03-02")
    (ids["x"],) = sembrar_lineas(fabrica, [
        {"horas": 8.0, "recurso_ide": RECURSO,
         "estado": "registrado" if x_registrada else None}],
        document_id="d-x", obra_ide=X, fecha="2026-03-02")
    (ids["martes"],) = sembrar_lineas(fabrica, [
        {"horas": 8.0, "recurso_ide": RECURSO}],
        document_id="d-x2", obra_ide=X, fecha="2026-03-03")
    return ids


def _lineas(fabrica) -> list[tuple]:
    with fabrica.create_session() as s:
        return sorted(
            (f.document_id, f.tipo_hora, f.horas, f.horas_orig,
             bool(f.extra_auto))
            for f in s.execute(select(ParteRegistroOrm).where(
                ParteRegistroOrm.deleted_at_utc.is_(None))).scalars())


def test_f049_r40_e12a_ciclo_completo_reparte_las_dos_obras():
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, x_registrada=False)
    _conciliador(fabrica, reajuste=False).conciliar_todos()
    assert _lineas(fabrica) == [
        ("d-x", "extra", 2.5, None, True), ("d-x", "normal", 5.5, 8.0, False),
        ("d-x2", "normal", 8.0, None, False),
        ("d-y", "extra", -0.5, None, True), ("d-y", "extra", 2.0, None, False),
        ("d-y", "normal", 2.5, 2.0, False)]


def test_f049_r40_e12b_ciclo_x_congelada_reajuste_apagado():
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, x_registrada=True)
    _conciliador(fabrica, reajuste=False).conciliar_todos()
    assert _lineas(fabrica) == [
        ("d-x", "normal", 8.0, None, False),
        ("d-x2", "normal", 8.0, None, False),
        ("d-y", "extra", 2.0, None, False), ("d-y", "extra", 2.0, None, True),
        ("d-y", "normal", 0.0, 2.0, False)]
    with fabrica.create_session() as s:
        assert s.execute(select(RepartoPendienteOrm)).first() is None


def test_f049_r40_e12c_ciclo_x_registrada_reajuste_encendido():
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, x_registrada=True)
    _conciliador(fabrica, reajuste=True).conciliar_todos()
    lineas = _lineas(fabrica)
    assert ("d-x", "normal", 8.0, None, False) in lineas       # intacta
    assert ("d-y", "normal", 2.5, 2.0, False) in lineas
    assert ("d-y", "extra", -0.5, None, True) in lineas
    with fabrica.create_session() as s:
        (rep,) = s.execute(select(RepartoPendienteOrm)).scalars()
        assert (rep.estado, rep.recurso_ide, rep.fecha_int) == (
            "pendiente", RECURSO, LUNES)
        cambios = json.loads(rep.cambios)["cambios"]
    assert [(c["registro_id"], c["tipo"], c["antes"], c["despues"])
            for c in cambios] == [(ids["x"], "ordinaria", 8.0, 5.5),
                                  (None, "extra", 0.0, 2.5)]
