# tests/test_f069_pareja_puro.py
"""F-069 · nucleo puro: vista revertida, huellas y emparejamiento.

`vista_revertida` es lo que la pasada ve tras el revert SIN haberlo
escrito (R7, R11). `huellas_por_clave` resume por pareja lo que decide su
revert y su split, para saber si sv4 la cambio entre la lectura y la
escritura (R13). `emparejar_extras` decide que extra existente reutiliza
cada split (R2, R3, R5).

Sin base ni red. Datos sinteticos.
"""
from __future__ import annotations

import dataclasses

import pytest

from application.services.pareja_extra import (
    CAMPOS_HUELLA,
    LecturaPasada,
    PlanRevert,
    emparejar_extras,
    huellas_por_clave,
    vista_revertida,
)

K = ("doc-1", 0, None, 20261001)


def _plan(*, borrar=(), restaurar=(), duplicadas=()) -> PlanRevert:
    return PlanRevert(borrar=tuple(borrar), restaurar=tuple(restaurar),
                      duplicadas=tuple(duplicadas), congeladas=0,
                      protegidas=0, dobles=())


def _fila(rid: int, *, horas=8.0, horas_orig=None, tipo="normal",
          extra_auto=False, estado=None, borrada=None, aprobado=False,
          activo=True, line_index=0, eln=None, doc="doc-1",
          fecha=20261001) -> dict:
    return {"registro_id": rid, "document_id": doc, "line_index": line_index,
            "empleado_line_no": eln, "fecha_int": fecha, "horas": horas,
            "horas_orig": horas_orig, "tipo_hora": tipo,
            "extra_auto": extra_auto, "sigrid_estado": estado,
            "deleted_at_utc": borrada, "doc_approved": aprobado,
            "doc_activo": activo, "otro": "x"}


# ========================== vista_revertida ============================ #

def test_f069_r11_vista_quita_las_borradas_y_restaura_las_bases() -> None:
    filas = [_fila(1, horas=8.0, horas_orig=10.0),
             _fila(2, horas=2.0, tipo="extra", extra_auto=True),
             _fila(3, horas=4.0, line_index=1)]
    vista = vista_revertida(filas, _plan(borrar=[2], restaurar=[1]))
    assert [f["registro_id"] for f in vista] == [1, 3]
    assert vista[0]["horas"] == 10.0 and vista[0]["horas_orig"] is None
    assert vista[1] == filas[2]
    assert vista[0]["otro"] == "x"


def test_f069_r7_vista_no_muta_la_entrada() -> None:
    filas = [_fila(1, horas=8.0, horas_orig=10.0),
             _fila(2, horas=2.0, extra_auto=True)]
    copia = [dict(f) for f in filas]
    vista = vista_revertida(filas, _plan(borrar=[2], restaurar=[1]))
    assert filas == copia
    assert vista[0] is not filas[0]


def test_f069_r11_vista_sin_plan_es_una_copia_igual() -> None:
    filas = [_fila(1), _fila(2, line_index=1)]
    vista = vista_revertida(filas, _plan())
    assert vista == filas and vista[0] is not filas[0]


def test_f069_r11_vista_conserva_el_orden_de_entrada() -> None:
    filas = [_fila(5), _fila(2, line_index=1), _fila(9, line_index=2)]
    assert [f["registro_id"] for f in vista_revertida(filas, _plan())] == \
        [5, 2, 9]


# ========================== huellas_por_clave ========================== #

def test_f069_r13_campos_de_la_huella() -> None:
    assert CAMPOS_HUELLA == (
        "registro_id", "horas", "horas_orig", "tipo_hora", "extra_auto",
        "sigrid_estado", "deleted_at_utc", "doc_approved", "doc_activo")


def test_f069_r13_huella_por_clave_con_sus_miembros() -> None:
    filas = [_fila(1, horas=8.0, horas_orig=10.0),
             _fila(2, horas=2.0, tipo="extra", extra_auto=True),
             _fila(3, line_index=1)]
    h = huellas_por_clave(filas)
    assert set(h) == {K, ("doc-1", 1, None, 20261001)}
    assert h[K] == frozenset({
        (1, 8.0, 10.0, "normal", False, None, None, False, True),
        (2, 2.0, None, "extra", True, None, None, False, True),
    })


def test_f069_r13_una_extra_explicita_no_es_miembro() -> None:
    filas = [_fila(1), _fila(2, tipo="extra", extra_auto=False)]
    assert huellas_por_clave(filas)[K] == frozenset(
        {(1, 8.0, None, "normal", False, None, None, False, True)})


def test_f069_r13_clave_solo_con_no_miembros_no_tiene_huella() -> None:
    assert huellas_por_clave([_fila(1, tipo="V")]) == {}


@pytest.mark.parametrize("campo, valor", [
    ("horas", 7.5), ("horas_orig", 9.0), ("tipo_hora", ""),
    ("extra_auto", True), ("sigrid_estado", "encolado"),
    ("deleted_at_utc", "2026-11-12T09:00:00"), ("doc_approved", True),
    ("doc_activo", False), ("registro_id", 99),
])
def test_f069_r13_cada_campo_cambia_la_huella(campo, valor) -> None:
    antes = huellas_por_clave([_fila(1)])
    despues = huellas_por_clave([dict(_fila(1), **{campo: valor})])
    assert antes[K] != despues[K]


def test_f069_r13_un_miembro_nuevo_cambia_la_huella() -> None:
    antes = huellas_por_clave([_fila(1)])
    despues = huellas_por_clave([_fila(1), _fila(2, extra_auto=True,
                                                 tipo="extra")])
    assert antes[K] != despues[K]


def test_f069_r13_horas_redondeadas_a_seis_decimales() -> None:
    a = huellas_por_clave([_fila(1, horas=8.0, horas_orig=10.0)])
    b = huellas_por_clave([_fila(1, horas=8.0000000001,
                                 horas_orig=9.99999999999)])
    assert a == b
    c = huellas_por_clave([_fila(1, horas=8.00001)])
    assert c != huellas_por_clave([_fila(1, horas=8.0)])


def test_f069_r13_booleanos_normalizados() -> None:
    a = huellas_por_clave([_fila(1, aprobado=0, activo=1)])
    b = huellas_por_clave([_fila(1, aprobado=False, activo=True)])
    assert a == b


def test_f069_r13_no_otros_campos() -> None:
    a = huellas_por_clave([_fila(1)])
    b = huellas_por_clave([dict(_fila(1), otro="y", recurso_ide=7)])
    assert a == b


# =========================== emparejar_extras ========================== #

def _split(normal_id: int, **kw) -> dict:
    return dict({"normal_id": normal_id, "extra_horas": 2.0}, **kw)


def test_f069_r2_un_split_reutiliza_la_unica_extra() -> None:
    s = _split(1)
    pares, sobran = emparejar_extras([s], [7])
    assert pares == [(s, 7)] and sobran == []


def test_f069_r3_por_orden_de_normal_id_y_de_id() -> None:
    a, b = _split(5), _split(3)
    pares, sobran = emparejar_extras([a, b], [20, 11])
    assert pares == [(b, 11), (a, 20)] and sobran == []


def test_f069_r3_splits_sobrantes_crean_extra_nueva() -> None:
    a, b = _split(1), _split(2)
    pares, sobran = emparejar_extras([b, a], [9])
    assert pares == [(a, 9), (b, None)] and sobran == []


def test_f069_r3_extras_sobrantes_se_borran() -> None:
    pares, sobran = emparejar_extras([_split(1)], [12, 4, 8])
    assert [p[1] for p in pares] == [4] and sobran == [8, 12]


def test_f069_r4_sin_splits_todas_sobran() -> None:
    assert emparejar_extras([], [3, 1]) == ([], [1, 3])


def test_f069_r3_sin_candidatas_todo_nuevo() -> None:
    a = _split(1)
    assert emparejar_extras([a], []) == ([(a, None)], [])


def test_f069_r5_split_con_id_propio_no_consume_candidata() -> None:
    con_id, sin_id = _split(1, id=500), _split(2)
    pares, sobran = emparejar_extras([con_id, sin_id], [9])
    assert pares == [(con_id, None), (sin_id, 9)] and sobran == []


def test_f069_r5_split_con_id_y_candidata_que_sobra() -> None:
    con_id = _split(1, id=500)
    pares, sobran = emparejar_extras([con_id], [9])
    assert pares == [(con_id, None)] and sobran == [9]


def test_f069_r5_id_none_cuenta_como_sin_id() -> None:
    s = _split(1, id=None)
    assert emparejar_extras([s], [9]) == ([(s, 9)], [])


def test_f069_r3_no_muta_las_entradas() -> None:
    splits, cands = [_split(2), _split(1)], [5, 3]
    emparejar_extras(splits, cands)
    assert [s["normal_id"] for s in splits] == [2, 1] and cands == [5, 3]


# ============================ LecturaPasada ============================ #

def test_f069_lectura_pasada_es_inmutable() -> None:
    lectura = LecturaPasada(registros=[_fila(1)], huellas={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        lectura.registros = []  # type: ignore[misc]
