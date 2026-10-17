# tests/test_f046_reparto_aviso.py
"""F-046 · reglas puras del aviso de reparto en sv4 (R30-R33).

  - `bloque_repartos`: lo que el modal ensena por reparto (R30, R31).
  - `excluidas_por_reparto`: que lineas no viajan sin decision (R32).
  - `payload_reajuste`: lo que sv4 manda a sv5 al «Aplicar» (R33).

Datos sinteticos: ni nombres ni DNIs.
"""
from __future__ import annotations

from application.services.reparto_aviso import (
    DECISION_APLICAR,
    DECISION_MANTENER,
    MOTIVO_APLICANDO,
    MOTIVO_PENDIENTE,
    MOTIVO_RECHAZADO,
    bloque_repartos,
    excluidas_por_reparto,
    id_provisional,
    payload_reajuste,
)

BASE, EXTRA, LIBRE, NUEVA = 11, 12, 13, 990000001


def _c(rid, base, tipo, antes, despues, estado="registrado", **kw):
    d = {"registro_id": rid, "base_registro_id": base, "tipo": tipo,
         "antes": antes, "despues": despues, "sigrid_estado": estado,
         "obra_codigo": "0678", "parte_cod": "PT26/09001"}
    d.update(kw)
    return d


def _fila(cambios=None, estado="pendiente", rid=7, registro_ids=(LIBRE,)):
    return {"id": rid, "estado": estado, "recurso_ide": 501,
            "fecha_int": 20261014, "error": None,
            "cambios": cambios if cambios is not None else [
                _c(BASE, BASE, "ordinaria", 8.0, 2.5),
                _c(EXTRA, BASE, "extra", -4.0, 1.5)],
            "registro_ids": list(registro_ids)}


def _nueva_cambio(estado="registrado"):
    return _c(None, BASE, "extra", 0.0, 2.5, estado=estado,
              recurso_ide=501, fecha_int=20261014, hora_ide=9,
              hora_codigo="HE01", partida_ide=33, partida_cod="P-33",
              obra_ide=678)


# ------------------------------- R30 ------------------------------- #

def test_f046_r30_bloque_por_reparto_con_sus_lineas():
    v = {7: {"error": None, "lineas": {
        BASE: {"editable": True, "motivo": None},
        EXTRA: {"editable": True, "motivo": None}}}}
    (b,) = bloque_repartos([_fila()], v)
    assert (b["id"], b["fecha"], b["recurso_ide"], b["estado"],
            b["editable"], b["motivo"]) == (7, "2026-10-14", 501,
                                            "pendiente", True, None)
    assert b["opciones"] == [DECISION_APLICAR, DECISION_MANTENER]
    assert b["registro_ids"] == [LIBRE]
    assert [(x["registro_id"], x["tipo"], x["obra_codigo"], x["parte_cod"],
             x["antes"], x["despues"], x["en_sigrid"], x["editable"],
             x["nueva"]) for x in b["lineas"]] == [
        (BASE, "ordinaria", "0678", "PT26/09001", 8.0, 2.5, True, True,
         False),
        (EXTRA, "extra", "0678", "PT26/09001", -4.0, 1.5, True, True,
         False)]


def test_f046_r30_las_solo_aprobadas_no_van_a_sv5_y_son_editables():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 5.5, estado=None),
                  _nueva_cambio(estado=None)])
    (b,) = bloque_repartos([fila], {})
    assert b["editable"] and b["opciones"] == [DECISION_APLICAR,
                                               DECISION_MANTENER]
    assert [(x["en_sigrid"], x["editable"], x["nueva"]) for x in
            b["lineas"]] == [(False, True, False), (False, True, True)]


def test_f046_r30_la_nueva_se_casa_con_su_id_provisional():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 5.5), _nueva_cambio()])
    v = {7: {"error": None, "lineas": {
        BASE: {"editable": True, "motivo": None},
        id_provisional(BASE): {"editable": False, "motivo": "choque"}}}}
    (b,) = bloque_repartos([fila], v)
    assert not b["editable"] and b["motivo"] == "choque"
    assert b["lineas"][1]["registro_id"] is None
    assert (b["lineas"][1]["editable"], b["lineas"][1]["motivo"]) == (
        False, "choque")


def test_f046_r30_id_provisional_negativo_y_unico():
    assert id_provisional(BASE) == -BASE
    assert id_provisional(BASE) != id_provisional(EXTRA)


# ------------------------------- R31 ------------------------------- #

def test_f046_r31_no_editable_solo_admite_mantener_con_su_motivo():
    v = {7: {"error": None, "lineas": {
        BASE: {"editable": True, "motivo": None},
        EXTRA: {"editable": False,
                "motivo": "su parte de Sigrid no esta En registro"}}}}
    (b,) = bloque_repartos([_fila()], v)
    assert b["editable"] is False
    assert b["opciones"] == [DECISION_MANTENER]
    assert b["motivo"] == "su parte de Sigrid no esta En registro"


def test_f046_r31_sin_respuesta_de_sv5_solo_mantener():
    (b,) = bloque_repartos([_fila()], {7: {"error": "sv5 caido",
                                           "lineas": {}}})
    assert b["opciones"] == [DECISION_MANTENER]
    assert "sv5 caido" in b["motivo"]


def test_f046_r31_registrada_sin_veredicto_no_es_editable():
    (b,) = bloque_repartos([_fila()], {})
    assert b["opciones"] == [DECISION_MANTENER] and not b["editable"]


def test_f046_r34_aplicando_admite_reintentar_aplicar():
    v = {7: {"error": None, "lineas": {
        BASE: {"editable": True, "motivo": None},
        EXTRA: {"editable": True, "motivo": None}}}}
    (b,) = bloque_repartos([_fila(estado="aplicando")], v)
    assert b["opciones"] == [DECISION_APLICAR]


def test_f046_r35_rechazado_espera_al_recalculo_sin_opciones():
    (b,) = bloque_repartos([_fila(estado="rechazado")], {})
    assert b["opciones"] == [] and b["motivo"] == MOTIVO_RECHAZADO


# ------------------------------- R32 ------------------------------- #

def test_f046_r32_sin_decision_no_viajan():
    filas = [_fila(registro_ids=[LIBRE, 14]),
             _fila(rid=8, estado="aplicando", registro_ids=[20]),
             _fila(rid=9, estado="rechazado", registro_ids=[30])]
    assert excluidas_por_reparto(filas, {}) == {
        LIBRE: MOTIVO_PENDIENTE, 14: MOTIVO_PENDIENTE,
        20: MOTIVO_APLICANDO, 30: MOTIVO_RECHAZADO}


def test_f046_r32_aplicar_deja_viajar_y_mantener_no():
    filas = [_fila(registro_ids=[LIBRE]), _fila(rid=8, registro_ids=[20])]
    assert excluidas_por_reparto(
        filas, {7: DECISION_APLICAR, 8: DECISION_MANTENER}) == {
        20: MOTIVO_PENDIENTE}


def test_f046_r32_otros_estados_no_excluyen():
    filas = [_fila(estado=e, registro_ids=[i]) for i, e in
             enumerate(["aplicado", "materializado", "mantenido",
                        "obsoleto"], start=40)]
    assert excluidas_por_reparto(filas, {}) == {}


# ------------------------------- R33 ------------------------------- #

def test_f046_r33_payload_lleva_solo_las_registradas():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 2.5),
                  _c(EXTRA, BASE, "extra", -4.0, 1.5),
                  _c(50, 50, "ordinaria", 6.0, 4.0, estado=None)])
    assert payload_reajuste(fila, {}) == {"lineas": [
        {"registro_id": BASE, "antes": 8.0, "despues": 2.5},
        {"registro_id": EXTRA, "antes": -4.0, "despues": 1.5}]}


def test_f046_r33_payload_de_la_extra_nueva_con_su_reserva():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 5.5), _nueva_cambio()])
    p = payload_reajuste(fila, {str(BASE): NUEVA})
    assert p["lineas"][1] == {
        "registro_id": NUEVA, "despues": 2.5, "base_registro_id": BASE,
        "recurso_ide": 501, "fecha_int": 20261014, "hora_ide": 9,
        "hora_codigo": "HE01", "partida_ide": 33, "partida_cod": "P-33",
        "obra_ide": 678, "obra_codigo": "0678"}


def test_f046_r33_nueva_de_base_solo_aprobada_no_va_a_sv5():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 5.5, estado=None),
                  _nueva_cambio(estado=None)])
    assert payload_reajuste(fila, {str(BASE): NUEVA}) == {"lineas": []}


def test_f046_r33_sin_reserva_la_nueva_usa_el_id_provisional():
    fila = _fila([_c(BASE, BASE, "ordinaria", 8.0, 5.5), _nueva_cambio()])
    p = payload_reajuste(fila, None)
    assert p["lineas"][1]["registro_id"] == id_provisional(BASE)
