# tests/test_f056_vista.py
"""F-056 · el ajuste de franquicia en la vista de trabajador (R20).

En modo nomina, la vista ensena el ajuste del periodo de cada recurso del
trabajador (X usada y X actual de sv5, E, A, dia, obra, parte, estado y
autor) y que accion admite: «Aplicar» (`decidido`/`error`), «Recalcular»
(`aplicado`) y «Ajustar» (`rechazado`, o sin fila con franquicia
`activa`). La X actual sale de UNA llamada a sv5 `/recursos` (R43); si sv5
no la sabe, aviso (R44) y los ajustes que ya existen se ven igual.

SQLite en memoria (`tests/dobles.py`) y un sv5 falso. Ni red ni
PostgreSQL. Datos SINTETICOS.
"""
from __future__ import annotations

from datetime import date

from application.services import franquicia as fq
from tests import test_f056_decisiones as dec
from tests.test_f056_decisiones import (
    ACTOR,
    EJECUTAR_OK,
    PROP,
    REC,
    Sv5Franq,
    _dia15,
    _repo,
)

# Los fixtures del portal y de SQLite son los de `test_f056_decisiones`.
entorno = dec.entorno
fabrica = dec.fabrica
portal = dec.portal

PERIODO = fq.periodo_de_clave("2026-10")


def _vista(cliente, modo="nomina"):
    r = cliente.get(f"/trabajadores/rec-{REC}",
                    params={"period": "2026-10", "modo": modo})
    assert r.status_code == 200, r.text
    return r.context["franquicia"]


def _con_fila(fabrica, decision="ajustar", *, cerrar=None):
    f = _repo(fabrica).decidir_ajuste(REC, "2026-10", decision, PROP,
                                      actor="eva")
    if cerrar is not None:
        f = _repo(fabrica).cerrar_ajuste(f["id"], ok=cerrar, sv5=dict(
            EJECUTAR_OK, franquicia=8.0), error=None if cerrar else "ko",
            actor=ACTOR)
    return f


def test_f056_r20_vista_aplicado_ofrece_recalcular_con_x_usada_y_actual(
        fabrica, portal):
    _dia15(fabrica)
    f = _con_fila(fabrica, cerrar=True)
    sv5 = Sv5Franq(recursos={"estado": "ok", "motivo": None, "recursos": {
        str(REC): {"franquicia": 9.0, "estado": "activa"}}})
    cliente, sv5 = portal(sv5=sv5)
    bloque = _vista(cliente)
    assert bloque["aviso"] is None and bloque["periodo"] == "2026-10"
    [it] = bloque["items"]
    assert (it["id"], it["estado"], it["acciones"]) == (
        f["id"], "aplicado", ["recalcular"])
    assert (it["x_usada"], it["x_actual"], it["x_estado"]) == (
        8.0, 9.0, "activa")
    assert (it["extras"], it["ajuste"], it["dia"], it["obra_codigo"],
            it["parte_cod"]) == (12.0, -6.0, "2026-10-15", "0100",
                                 "PT26/00314")
    assert (it["decidido_por"], it["aplicado_por"]) == ("eva", ACTOR)
    assert [p for p, _t in sv5.recursos_pedidos] == [[REC]]       # R43


def test_f056_r20_vista_decidido_y_error_ofrecen_aplicar(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica)
    cliente, _sv5 = portal()
    [it] = _vista(cliente)["items"]
    assert (it["estado"], it["acciones"], it["x_usada"]) == (
        "decidido", ["aplicar"], None)


def test_f056_r20_vista_error_ofrece_aplicar_con_motivo(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica, cerrar=False)
    cliente, _sv5 = portal()
    [it] = _vista(cliente)["items"]
    assert (it["estado"], it["acciones"], it["error"]) == (
        "error", ["aplicar"], "ko")


def test_f056_r20_vista_rechazado_ofrece_ajustar(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica, "no_ajustar")
    cliente, _sv5 = portal()
    [it] = _vista(cliente)["items"]
    assert (it["estado"], it["acciones"]) == ("rechazado", ["ajustar"])


def test_f056_r20_vista_sin_fila_y_activa_ofrece_ajustar(fabrica, portal):
    _dia15(fabrica)
    cliente, _sv5 = portal()
    [it] = _vista(cliente)["items"]
    assert (it["id"], it["estado"], it["acciones"], it["x_actual"]) == (
        None, None, ["ajustar"], 8.0)


def test_f056_r20_vista_sin_fila_ni_franquicia_activa_no_ensena_nada(
        fabrica, portal):
    _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos={
        "estado": "ok", "motivo": None,
        "recursos": {str(REC): {"franquicia": None, "estado": "inactiva"}}}))
    assert _vista(cliente) is None


def test_f056_r20_vista_apagada_sin_filas_no_ensena_nada(fabrica, portal):
    _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos={
        "estado": "apagada", "motivo": "x", "recursos": {}}))
    assert _vista(cliente) is None


def test_f056_r20_vista_en_modo_natural_no_pregunta_a_sv5(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica)
    cliente, sv5 = portal()
    assert _vista(cliente, modo="natural") is None
    assert sv5.recursos_pedidos == []


def test_f056_r44_vista_sv5_no_sabe_aviso_y_las_filas_se_ven(fabrica,
                                                             portal):
    _dia15(fabrica)
    _con_fila(fabrica, cerrar=True)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos=RuntimeError("caido")))
    bloque = _vista(cliente)
    assert bloque["aviso"] == fq.AVISO_NO_COMPROBADA + "caido"
    [it] = bloque["items"]
    assert (it["estado"], it["x_usada"], it["x_actual"], it["acciones"]) == (
        "aplicado", 8.0, None, ["recalcular"])


def test_f056_r20_vista_fallo_propio_no_tumba_la_pagina(fabrica, portal,
                                                        monkeypatch):
    _dia15(fabrica)
    cliente, _sv5 = portal()

    def roto(self, claves):
        raise RuntimeError("bbdd caida")
    monkeypatch.setattr(type(_repo(fabrica)), "ajustes_de", roto)
    bloque = _vista(cliente)
    assert "bbdd caida" in bloque["aviso"] and bloque["items"] == []


# ------------------------------- puro (R20) ------------------------------- #

def test_f056_r20_vista_franquicia_pura_ordena_y_omite():
    filas = {(7, "2026-10"): {"id": 3, "estado": "aplicado",
                              "franquicia": 5.0, "fecha_int": 20261015}}
    franq = {5: {"franquicia": 4.0, "estado": "activa"},
             6: {"franquicia": None, "estado": "inactiva"}}
    bloque = fq.vista_franquicia(PERIODO, [7, 6, 5], filas, franq, None)
    assert [(i["recurso_ide"], i["acciones"]) for i in bloque["items"]] == [
        (5, ["ajustar"]), (7, ["recalcular"])]
    assert bloque["items"][1]["dia"] == date(2026, 10, 15).isoformat()
    assert fq.vista_franquicia(PERIODO, [6], {}, franq, None) is None
    assert fq.vista_franquicia(PERIODO, [6], {}, None, "x") == {
        "periodo": "2026-10", "aviso": fq.AVISO_NO_COMPROBADA + "x",
        "items": []}
