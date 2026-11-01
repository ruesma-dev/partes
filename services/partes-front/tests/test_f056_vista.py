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
import logging
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from application.services import franquicia as fq
from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests import test_f056_decisiones as dec
from tests.dobles import sembrar_parte
from tests.test_f056_decisiones import (
    ACTOR,
    EJECUTAR_OK,
    PROP,
    REC,
    CalendarioNoFiable,
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


# ================== decidir desde la vista (T17b: R45, R46) ================== #

def _decidir(cliente, decision, rec=REC, periodo="2026-10"):
    return cliente.post("/api/franquicia/decidir", json={
        "recurso_ide": rec, "periodo": periodo, "decision": decision})


def _filas_ajuste(fabrica):
    return _repo(fabrica).ajustes_de([(REC, "2026-10")])


def _sin_sv5(sv5):
    assert sv5.recursos_pedidos == [] and sv5.franq_comprobadas == []
    assert sv5.franq_ejecutadas == [] and sv5.ejecutadas == []


@pytest.mark.parametrize("crudo, esperado", [
    ({"recurso_ide": 7, "periodo": "2026-10", "decision": "ajustar"},
     (7, "2026-10", "ajustar")),
    ({"recurso_ide": "7", "periodo": "2026-10", "decision": "recalcular"},
     (7, "2026-10", "recalcular")),
])
def test_f056_r45_decision_vista_admite_ajustar_y_recalcular(crudo, esperado):
    assert fq.decision_vista(crudo) == esperado


@pytest.mark.parametrize("crudo", [
    {"recurso_ide": 7, "periodo": "2026-10", "decision": "no_ajustar"},
    {"recurso_ide": 7, "periodo": "2026-10", "decision": "mantener"},
    {"recurso_ide": 7, "periodo": "2026-10", "decision": "borrar"},
    {"recurso_ide": 7, "periodo": "2026-13", "decision": "ajustar"},
    {"recurso_ide": 0, "periodo": "2026-10", "decision": "ajustar"},
    {"recurso_ide": True, "periodo": "2026-10", "decision": "ajustar"},
    {"periodo": "2026-10", "decision": "ajustar"},
    "x", None, [],
])
def test_f056_r45_decision_vista_rechaza_lo_demas(crudo):
    with pytest.raises(fq.DecisionInvalida):
        fq.decision_vista(crudo)


def test_f056_r45_r21_decidir_ajustar_sin_fila_guarda_la_propuesta(fabrica,
                                                                  portal):
    _dia15(fabrica)
    cliente, sv5 = portal()
    r = _decidir(cliente, "ajustar")
    assert r.status_code == 200, r.text
    aj = r.json()["ajuste"]
    assert r.json()["ok"] is True and aj["id"]
    assert (aj["estado"], aj["decision"], aj["fecha_int"], aj["obra_ide"],
            aj["partida_cod"], aj["decidido_por"]) == (
        "decidido", "ajustar", 20261015, 10, "01.01", ACTOR)
    assert _filas_ajuste(fabrica)[(REC, "2026-10")]["id"] == aj["id"]
    _sin_sv5(sv5)


def test_f056_r45_decidir_ajustar_desde_rechazado(fabrica, portal):
    _dia15(fabrica)
    f = _con_fila(fabrica, "no_ajustar")
    cliente, _sv5 = portal()
    aj = _decidir(cliente, "ajustar").json()["ajuste"]
    assert (aj["id"], aj["estado"]) == (f["id"], "decidido")


def test_f056_r45_decidir_recalcular_desde_aplicado(fabrica, portal):
    _dia15(fabrica)
    f = _con_fila(fabrica, cerrar=True)
    cliente, sv5 = portal()
    aj = _decidir(cliente, "recalcular").json()["ajuste"]
    assert (aj["id"], aj["estado"], aj["decision"]) == (
        f["id"], "decidido", "recalcular")
    _sin_sv5(sv5)


@pytest.mark.parametrize("previa, decision", [
    (None, "recalcular"), ("ajustar", "ajustar")])
def test_f056_r45_r16_decidir_transicion_que_no_cabe_es_409(
        fabrica, portal, previa, decision):
    _dia15(fabrica)
    if previa:
        _con_fila(fabrica, previa)
    cliente, sv5 = portal()
    r = _decidir(cliente, decision)
    assert r.status_code == 409 and r.json()["error"]
    _sin_sv5(sv5)


@pytest.mark.parametrize("cuerpo", [
    {"recurso_ide": REC, "periodo": "2026-10", "decision": "no_ajustar"},
    {"recurso_ide": REC, "periodo": "2026-10", "decision": "mantener"},
    {"recurso_ide": REC, "periodo": "octubre", "decision": "ajustar"},
    {"periodo": "2026-10", "decision": "ajustar"},
    ["x"],
])
def test_f056_r45_decidir_formato_o_decision_invalida_es_422(fabrica, portal,
                                                             cuerpo):
    _dia15(fabrica)
    cliente, sv5 = portal()
    r = cliente.post("/api/franquicia/decidir", json=cuerpo)
    assert r.status_code == 422, r.text
    assert _filas_ajuste(fabrica) == {}
    _sin_sv5(sv5)


@pytest.mark.parametrize("rec, periodo", [(REC, "2026-11"), (999, "2026-10")])
def test_f056_r45_decidir_sin_lineas_del_recurso_en_el_periodo_es_422(
        fabrica, portal, rec, periodo):
    _dia15(fabrica)
    cliente, _sv5 = portal()
    r = _decidir(cliente, "ajustar", rec=rec, periodo=periodo)
    assert r.status_code == 422 and "lineas" in r.json()["error"]
    assert _repo(fabrica).ajustes_de([(rec, periodo)]) == {}


def test_f056_r45_r12_decidir_con_extras_de_varios_recursos_es_409(fabrica,
                                                                   portal):
    _dia15(fabrica)
    sembrar_parte(fabrica, [{"horas": 1.0, "tipo": "extra"}],
                  document_id="d-otro", fecha="2026-10-01", recurso_ide=777)
    cliente, _sv5 = portal()
    r = _decidir(cliente, "ajustar")
    assert r.status_code == 409
    assert r.json()["error"] == fq.MOTIVO_VARIOS_RECURSOS


def test_f056_r45_r6_decidir_ajustar_sin_calendario_es_409(fabrica, portal):
    _dia15(fabrica)
    cliente, _sv5 = portal(calendario=CalendarioNoFiable())
    r = _decidir(cliente, "ajustar")
    assert r.status_code == 409 and "dia de ajuste" in r.json()["error"]
    assert _filas_ajuste(fabrica) == {}


def test_f056_r45_decidir_sin_sv5_configurado_es_503(fabrica, entorno):
    entorno.delenv("TRANSFER_BASE_URL", raising=False)
    _dia15(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    r = TestClient(app).post("/api/franquicia/decidir", json={
        "recurso_ide": REC, "periodo": "2026-10", "decision": "ajustar"})
    assert r.status_code == 503
    assert _filas_ajuste(fabrica) == {}


def test_f056_r20_plantilla_botones_de_decidir(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica, cerrar=True)
    cliente, _sv5 = portal()
    html = _html(cliente)
    assert 'data-franquicia-decidir="recalcular"' in html
    assert f'data-recurso="{REC}"' in html and 'data-periodo="2026-10"' in html
    assert 'data-franquicia-decidir="ajustar"' not in html


@pytest.mark.parametrize("previa", ["no_ajustar", None])
def test_f056_r20_plantilla_ajustar_en_rechazado_o_sin_fila(fabrica, portal,
                                                            previa):
    _dia15(fabrica)
    if previa:
        _con_fila(fabrica, previa)
    cliente, _sv5 = portal()
    html = _html(cliente)
    assert 'data-franquicia-decidir="ajustar"' in html
    assert "data-franquicia-aplicar" not in html


def test_f056_r20_plantilla_decidido_no_ofrece_decidir(fabrica, portal):
    _dia15(fabrica)
    _con_fila(fabrica)
    cliente, _sv5 = portal()
    assert "data-franquicia-decidir" not in _html(cliente)


def test_f056_r46_la_vista_decide_y_luego_aplica_sin_recargar():
    js = _js()
    cuerpo = _funcion(js, "decidirDesdeVista")
    assert cuerpo.index('"/api/franquicia/decidir"') < cuerpo.index(
        '"/aplicar"')
    assert "r.ajuste.id" in cuerpo
    assert "resultadoFranquiciaHtml(" in cuerpo
    assert "botonActualizar()" in cuerpo
    assert "reload" not in cuerpo
    assert "[data-franquicia-decidir]" in js


# ============ supervivientes de la campana de mutacion (2026-10-29) ============ #
# Cada test caza un mutante que la suite dejaba vivo (numero entre corchetes:
# el de `progress/mutacion_F-056.md`).

def test_f056_r20_vista_fallo_propio_con_traza(fabrica, portal, monkeypatch,
                                               caplog):
    """[46] El aviso del fallo de la vista lleva la traza (`exc_info`)."""
    _dia15(fabrica)
    cliente, _sv5 = portal()

    def roto(self, claves):
        raise RuntimeError("bbdd caida")
    monkeypatch.setattr(type(_repo(fabrica)), "ajustes_de", roto)
    with caplog.at_level(logging.WARNING):
        _vista(cliente)
    assert any(r.getMessage() == "[franquicia] el ajuste de la vista fallo"
               and r.exc_info for r in caplog.records)


def test_f056_r20_vista_sin_periodo_no_pregunta_a_sv5(fabrica, portal):
    """[45] Sin periodo (lineas sin fecha) no hay ajuste que ensenar: ni se
    pregunta a sv5 ni se tumba la pagina."""
    ids = _dia15(fabrica)
    with fabrica.create_session() as s:
        for rid in ids:
            r = s.get(dec.ParteRegistroOrm, rid)
            r.fecha, r.fecha_int = None, None
        s.commit()
    cliente, sv5 = portal()
    r = cliente.get(f"/trabajadores/rec-{REC}", params={"modo": "nomina"})
    assert r.status_code == 200, r.text
    assert r.context["franquicia"] is None
    assert sv5.recursos_pedidos == []


@pytest.mark.parametrize("ruta", ["/api/franquicia/decidir",
                                  "/api/franquicia/{ajuste_id}/aplicar"])
def test_f056_r21_rutas_de_franquicia_fuera_del_esquema(fabrica, portal,
                                                        ruta):
    """[47, 50] Como el resto de la API interna del portal, no se publican
    en OpenAPI."""
    cliente, _sv5 = portal()
    assert ruta not in cliente.app.openapi()["paths"]


@pytest.mark.parametrize("ruta", ["/api/franquicia/decidir",
                                  "/api/franquicia/7/aplicar"])
def test_f056_r21_sin_sv5_configurado_es_503_ok_false(fabrica, entorno,
                                                      ruta):
    """[48, 51, 52] Sin sv5 configurado: 503 y `ok: false` con el motivo."""
    entorno.delenv("TRANSFER_BASE_URL", raising=False)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    r = TestClient(app).post(ruta, json={
        "recurso_ide": REC, "periodo": "2026-10", "decision": "ajustar"})
    assert (r.status_code, r.json()["ok"]) == (503, False)
    assert "TRANSFER_BASE_URL" in r.json()["error"]


def test_f056_r45_decidir_linea_sin_recurso_no_es_del_recurso_1(fabrica,
                                                                portal):
    """[49] La persona del recurso 1 (por su DNI) tiene en el periodo una
    linea SIN recurso: esa linea no hace que el recurso 1 tenga lineas en
    el periodo (422)."""
    sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-sep",
                  fecha="2026-09-10", recurso_ide=1)
    [sin] = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-oct",
                          fecha="2026-10-15")
    with fabrica.create_session() as s:
        s.get(dec.ParteRegistroOrm, sin).recurso_ide = None
        s.commit()
    cliente, _sv5 = portal()
    r = _decidir(cliente, "ajustar", rec=1)
    assert r.status_code == 422 and "lineas" in r.json()["error"]
    assert _repo(fabrica).ajustes_de([(1, "2026-10")]) == {}


def test_f056_da32_decidir_obra_del_recurso_del_ajuste(fabrica, portal):
    """DA32, R7, R45: «Ajustar» desde la vista guarda la obra del recurso
    del ajuste (0100) aunque la persona tenga mas horas el dia de ajuste
    con otro recurso de otra empresa (0200)."""
    dec._otro_recurso_con_mas_horas(fabrica)
    _dia15(fabrica)
    cliente, _sv5 = portal()
    r = _decidir(cliente, "ajustar")
    assert r.status_code == 200, r.text
    aj = r.json()["ajuste"]
    assert (aj["recurso_ide"], aj["fecha_int"], aj["obra_ide"],
            aj["obra_codigo"], aj["partida_cod"]) == (
        REC, 20261015, 10, "0100", "01.01")
