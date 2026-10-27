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

import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

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


# ====================== portal: plantilla y JS (T17) ====================== #

RAIZ_SV4 = Path(__file__).resolve().parents[1]
APP_JS = RAIZ_SV4 / "static" / "app.js"
STYLES = RAIZ_SV4 / "static" / "styles.css"
NODE = shutil.which("node")


def _html(cliente, modo="nomina") -> str:
    r = cliente.get(f"/trabajadores/rec-{REC}",
                    params={"period": "2026-10", "modo": modo})
    assert r.status_code == 200, r.text
    return r.text


def test_f056_r15_cada_candidato_lleva_sus_lineas():
    lineas = [{"registro_id": 12, "fecha_int": 20261015, "recurso_ide": REC},
              {"registro_id": 11, "fecha_int": 20261001, "recurso_ide": REC}]
    [c] = fq.candidatos(lineas, {}, {REC: {"franquicia": 8.0,
                                           "estado": "activa"}},
                        lambda _k: fq.DiaAjuste(date(2026, 10, 15)))
    assert c["registro_ids"] == [11, 12]
    [it] = fq.bloque_franquicias([c], {}, None)["items"]
    assert it["registro_ids"] == [11, 12]


def test_f056_r20_plantilla_decidido_con_boton_aplicar(fabrica, portal):
    _dia15(fabrica)
    f = _con_fila(fabrica)
    cliente, _sv5 = portal()
    html = _html(cliente)
    assert "franquicia-ajuste" in html
    assert f'data-franquicia-aplicar="{f["id"]}"' in html
    assert "decidido" in html


def test_f056_r20_plantilla_aplicado_x_usada_y_actual_sin_aplicar(fabrica,
                                                                  portal):
    _dia15(fabrica)
    _con_fila(fabrica, cerrar=True)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos={
        "estado": "ok", "motivo": None,
        "recursos": {str(REC): {"franquicia": 9.0, "estado": "activa"}}}))
    html = _html(cliente)
    bloque = html[html.index("franquicia-ajuste"):]
    assert "data-franquicia-aplicar" not in html
    assert "PT26/00314" in bloque and "aplicado" in bloque
    assert re.search(r"X usada[^<]*</th>", bloque)
    assert "8,00" in bloque and "9,00" in bloque


def test_f056_r44_plantilla_aviso_si_sv5_no_sabe(fabrica, portal):
    _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos=RuntimeError("caido")))
    assert (fq.AVISO_NO_COMPROBADA + "caido") in _html(cliente)


def test_f056_r20_plantilla_modo_natural_sin_bloque(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica)
    cliente, _sv5 = portal()
    assert "franquicia-ajuste" not in _html(cliente, modo="natural")


def test_f056_r13_estilos_del_aviso_y_de_la_vista():
    css = STYLES.read_text(encoding="utf-8")
    for selector in (".ap-franquicias", ".ap-franquicia",
                     ".franquicia-ajuste"):
        assert selector in css


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _variable(js: str, nombre: str) -> str:
    m = re.search(r"\n  var " + nombre + r" = \{.*?\n  \};\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _node(cuerpo: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    js = _js()
    programa = (_funcion(js, "esc")
                + _variable(js, "TEXTO_DECISION_FRANQUICIA")
                + _funcion(js, "numFranquicia")
                + _funcion(js, "franquiciasHtml")
                + _funcion(js, "franquiciasPara")
                + _funcion(js, "resultadoFranquiciaHtml")
                + "process.stdout.write(JSON.stringify((function () {\n"
                + cuerpo + "\n})()));\n")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60, check=False)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _item(**kw):
    base = {"clave": "501|2026-10", "recurso_ide": REC, "periodo": "2026-10",
            "inicio": "2026-09-16", "fin": "2026-10-15", "nombre": "Pepe",
            "tipo": "nuevo", "id": None, "estado": None, "dia": "2026-10-15",
            "obra": {"ide": 10, "codigo": "0100"}, "partida_cod": "01.01",
            "franquicia": 8.0, "franquicia_estado": "activa",
            "franquicia_usada": None, "extras": 12.0, "extras_pendientes": 2.0,
            "objetivo": -6.0, "actual": None, "parte_cod": "PT26/00314",
            "accion": "crear", "ajustable": True, "pide_decision": True,
            "decisiones": ["ajustar", "no_ajustar"], "motivo": None,
            "registro_ids": [11, 12]}
    return dict(base, **kw)


def _bloque(*items, aviso=None):
    return json.dumps({"aviso": aviso, "items": list(items)})


def test_f056_r13_el_aviso_nuevo_pide_ajustar_o_no():
    html = _node("return franquiciasHtml(" + _bloque(_item()) + ");")
    assert "Franquicia de horas extra" in html
    assert html.count("type='radio'") == 2
    assert 'value="ajustar"' in html and 'value="no_ajustar"' in html
    assert 'name="franq-501|2026-10"' in html
    assert " checked" not in html                     # hay que elegir
    for texto in ("Pepe", "0100", "01.01", "2026-10-15", "PT26/00314"):
        assert texto in html
    assert "8" in html and "12" in html and "-6" in html


def test_f056_r10_el_aviso_existente_ensena_antes_y_despues():
    html = _node("return franquiciasHtml(" + _bloque(_item(
        tipo="existente", id=3, estado="aplicado", actual=-4.0,
        franquicia_usada=8.0, decisiones=["recalcular", "mantener"])) + ");")
    assert 'value="recalcular"' in html and 'value="mantener"' in html
    assert "-4" in html and "→" in html


def test_f056_r12_r44_sin_decision_motivo_y_aviso():
    html = _node("return franquiciasHtml(" + _bloque(_item(
        ajustable=False, pide_decision=False, decisiones=[],
        motivo="extras con mas de un recurso"),
        aviso="no se ha podido comprobar la franquicia: caido") + ");")
    assert "type='radio'" not in html
    assert "extras con mas de un recurso" in html
    assert "no se ha podido comprobar la franquicia: caido" in html
    assert _node("return franquiciasHtml(null) + franquiciasHtml("
                 "{aviso: null, items: []});") == ""


def test_f056_r15_cada_decision_viaja_una_vez_con_sus_lineas():
    salida = _node("""
      var dec = [{recurso_ide: 501, periodo: "2026-10", decision: "ajustar",
                  registro_ids: [11, 12]},
                 {recurso_ide: 502, periodo: "2026-10",
                  decision: "no_ajustar", registro_ids: [20]}];
      var enviadas = {};
      return [franquiciasPara(dec, [1, 12], enviadas),
              franquiciasPara(dec, [11, 20], enviadas),
              franquiciasPara(dec, [12], enviadas),
              franquiciasPara(undefined, [12], {})];
    """)
    assert salida == [
        [{"recurso_ide": 501, "periodo": "2026-10", "decision": "ajustar"}],
        [{"recurso_ide": 502, "periodo": "2026-10",
          "decision": "no_ajustar"}], [], []]


def test_f056_r17_da22_el_resultado_dice_que_paso_y_si_cambio_x():
    html = _node("""return [
      resultadoFranquiciaHtml({ok: true, error: null, ajuste: {
        recurso_ide: 501, periodo: "2026-10", estado: "aplicado",
        franquicia: 9, ajuste: -5, parte_cod: "PT26/00314"}}, 8),
      resultadoFranquiciaHtml({ok: true, error: null, ajuste: {
        recurso_ide: 501, periodo: "2026-10", estado: "aplicado",
        franquicia: 8, ajuste: -6, parte_cod: "PT26/00314"}}, 8),
      resultadoFranquiciaHtml({ok: false, error: "espera a que termine el "
        + "registro", ajuste: null}, 8)];""")
    assert "aplicado" in html[0] and "PT26/00314" in html[0]
    assert "la franquicia en Sigrid era 9" in html[0]
    assert "era" not in html[1]
    assert "espera a que termine el registro" in html[2]
    assert "vista del trabajador" in html[2]


def test_f056_r13_r16_r17_el_modal_cablea_aviso_decision_y_aplicar():
    js = _js()
    aprobar = _funcion(js, "aprobar")
    assert "franquiciasHtml(pf.franquicias)" in aprobar
    assert "decisionesFranquicia(cj, pf.franquicias)" in aprobar
    assert "vigilarDecisionesFranquicia(cajaPf, pf.franquicias)" in aprobar
    confirmar = _funcion(js, "confirmar")
    assert "franquiciasPara(" in confirmar
    assert "cuerpo.franquicias = " in confirmar
    resultado = _funcion(js, "mostrarResultadoGrupos")
    assert "aplicarFranquicias(" in resultado
    aplicar = _funcion(js, "aplicarFranquicias")
    assert "/api/franquicia/" in aplicar and "/aplicar" in aplicar
    assert "[data-franquicia-aplicar]" in js
