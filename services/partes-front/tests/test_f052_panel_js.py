# tests/test_f052_panel_js.py
"""F-052 · el panel de «Sincronizar con Sigrid» (`static/app.js`).

Se EJECUTAN en node las funciones reales del panel (extraídas del IIFE de
aprobar con la misma expresión que F-049), con un DOM, un `fetch` (`post`)
y un `modal` falsos. Sin navegador ni red. Datos sintéticos.

- R16: filtros por clase, acciones de lo visible, «todas las de esta
  clase»; las líneas a 0 h ocultas por defecto (DA13).
- R17: confirmación con el número de líneas y el resumen ANTES de llamar.
- R24: `reaprobar` reutiliza el modal de aprobar (`aprobar`).
- R25: al terminar una acción se vuelve a sincronizar y se pinta.
- `esc()` en todo lo que llega del servidor.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
APP_JS = RAIZ / "static" / "app.js"
STYLES = RAIZ / "static" / "styles.css"
NODE = shutil.which("node")

FUNCIONES = ("esc", "num", "fechaLegible", "etiquetasClaseSync",
             "etiquetasAccionSync", "filtrarItemsSync",
             "textoDiferenciasSync", "accionesVisiblesSync", "filaSyncHtml",
             "panelSyncHtml", "resumenAccionSyncHtml", "itemsAplicarSync",
             "resultadoSyncHtml", "ambitoSync", "pintarSync",
             "sincronizarAmbito", "seleccionSync", "aplicarSync",
             "confirmarAccionSync")

#: DOM, `post`, `modal` y `aprobar` falsos; `registro` apunta todo.
ENTORNO = r"""
var registro = { post: [], modal: [], aprobar: [], cerrar: 0 };
var respuestas = {};
var panel = { hidden: true, innerHTML: "" };
var marcadas = [];
var document = {
  getElementById: function (id) {
    return id === "sincronizar-panel" ? panel : null; },
  querySelectorAll: function () { return marcadas; },
};
function post(url, body) {
  registro.post.push({ url: url, body: body });
  var r = respuestas[url];
  if (Array.isArray(r)) r = r.shift();
  return Promise.resolve(r || { ok: false, error: "sin respuesta" });
}
function modal(titulo, html, acciones) {
  registro.modal.push({ titulo: titulo, html: html,
                        acciones: (acciones || []).map(function (a) {
                          return a.texto; }) });
  registro.ultimas = acciones || [];
}
function cerrar() { registro.cerrar += 1; }
function aprobar(peticion, contexto) {
  registro.aprobar.push({ peticion: peticion, contexto: contexto }); }
var estadoSync = { boton: null, resp: null,
                   filtro: { clase: "todas", verACero: false } };
var botonObra = { disabled: false, dataset: { vista: "obra",
  obraKey: "obr-686", period: "2026-10", mode: "natural" } };
"""


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _node(cuerpo: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    js = _js()
    programa = (ENTORNO + "".join(_funcion(js, f) for f in FUNCIONES)
                + "\n(async function () {\n" + cuerpo
                + "\n})().catch(function (e) { console.error(e); "
                  "process.exit(1); });")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _salida(expr: str) -> str:
    return "process.stdout.write(JSON.stringify(" + expr + "));"


def item(rid, clase, *, acciones=(), a_cero=False, portal=None,
         sigrid=None, **extra) -> dict:
    base = {"clase": clase, "registro_id": rid, "hmores_ide": None,
            "portal": portal, "sigrid": sigrid, "diferencias": [],
            "notas": [], "a_cero": a_cero, "donde": None,
            "acciones": list(acciones), "firma": f"f{rid or 0:015d}"}
    base.update(extra)
    return base


def portal(horas=8.0, estado="registrado", fecha=20261014) -> dict:
    return {"registro_id": 0, "fecha_int": fecha, "horas": horas,
            "hora_codigo": "HL01", "sigrid_estado": estado}


def sigrid(can=6.0, hmores=9001, obra_cod="0686", fecha=20261014) -> dict:
    return {"hmores_ide": hmores, "can": can, "hora_cod": "HL01",
            "fecha_int": fecha, "obra_cod": obra_cod}


ITEMS = [
    item(1, "igual", portal=portal(), sigrid=sigrid(8.0)),
    item(2, "distinta", acciones=["traer_de_sigrid"], portal=portal(),
         sigrid=sigrid(), diferencias=[{"campo": "horas", "portal": 8,
                                        "sigrid": 6}]),
    item(3, "distinta", acciones=["traer_de_sigrid"], portal=portal(5.0),
         sigrid=sigrid(1.0)),
    item(4, "en_sigrid_sin_registrar", acciones=["marcar_registrada"],
         portal=portal(estado="error"), sigrid=sigrid(8.0, hmores=9100)),
    item(None, "solo_sigrid_manual", a_cero=True, sigrid=sigrid(0.0)),
]

RESP = {"ok": True, "seco": False, "periodo": {"desde": 20261001,
                                               "hasta": 20261031},
        "leido_at": "2026-11-03T09:30:00+00:00",
        "recuento": {"total": 5, "a_cero": 1, "por_clase": {
            "igual": 1, "distinta": 2, "en_sigrid_sin_registrar": 1,
            "solo_sigrid_manual": 1}},
        "items": ITEMS, "marcadas_borrado_sigrid": []}


# ------------------------------ R16 filtros ------------------------------ #

def test_f052_r16_filtro_por_clase_y_a_cero_oculto_por_defecto() -> None:
    out = _node(_salida(
        "[filtrarItemsSync(%s, {clase: 'todas', verACero: false}).length,"
        " filtrarItemsSync(%s, {clase: 'todas', verACero: true}).length,"
        " filtrarItemsSync(%s, {clase: 'distinta', verACero: false})"
        ".map(function (i) { return i.registro_id; })]"
        % ((json.dumps(ITEMS),) * 3)))
    assert out == [4, 5, [2, 3]]


def test_f052_r16_panel_pinta_filtros_acciones_y_casillas() -> None:
    out = _node(_salida(
        "[panelSyncHtml(%s, {clase: 'todas', verACero: false}, null),"
        " panelSyncHtml(%s, {clase: 'distinta', verACero: false}, null)]"
        % (json.dumps(RESP), json.dumps(RESP))))
    todas, distintas = out
    assert 'data-sync-filtro="distinta">Distintas (2)' in todas
    assert "Ver las 1 línea(s) a 0 h de Sigrid" in todas
    assert 'data-sync-accion="traer_de_sigrid" data-sync-alcance="seleccion"' \
        in todas
    assert 'data-sync-accion="marcar_registrada"' in todas
    assert 'data-sync-alcance="clase"' not in todas
    assert todas.count("data-sync-sel=") == 3        # solo las accionables
    assert "solo_sigrid_manual" not in todas.split("<tbody>")[1]
    assert ("Traer las horas de Sigrid · todas las de esta clase (2)"
            in distintas)
    assert 'data-sync-accion="marcar_registrada"' not in distintas


def test_f052_r16_todas_las_de_esta_clase_y_seleccion() -> None:
    out = _node(
        "estadoSync.resp = %s; estadoSync.filtro.clase = 'distinta';"
        "var porClase = seleccionSync('traer_de_sigrid', 'clase');"
        "marcadas = [{dataset: {syncSel: '3'}}, {dataset: {syncSel: '0'}}];"
        "var porSel = seleccionSync('marcar_registrada', 'seleccion');"
        % json.dumps(RESP)
        + _salida("[porClase.map(function (i) { return i.registro_id; }),"
                  " porSel.map(function (i) { return i.registro_id; })]"))
    assert out == [[2, 3], [4]]


def test_f052_r7_ambito_de_obra_y_de_persona() -> None:
    out = _node(_salida(
        "[ambitoSync(botonObra), ambitoSync({dataset: {vista: 'trabajador',"
        " workerKey: 'rec-501', period: '2026-10', mode: ''}})]"))
    assert out == [{"vista": "obra", "period": "2026-10", "mode": "natural",
                    "obra_key": "obr-686"},
                   {"vista": "trabajador", "period": "2026-10",
                    "mode": "nomina", "worker_key": "rec-501"}]


# ------------------------------ R17 confirmar ---------------------------- #

def test_f052_r17_confirma_con_recuento_antes_de_llamar() -> None:
    out = _node(
        "estadoSync.boton = botonObra; estadoSync.resp = %s;"
        "respuestas['/api/sincronizar/aplicar'] = {ok: true, aplicados: [2, 3],"
        " descartados: []};"
        "respuestas['/api/sincronizar'] = %s;"
        "confirmarAccionSync('traer_de_sigrid', [%s, %s]);"
        "var antes = registro.post.length; var confirmacion = registro.modal[0];"
        "await registro.ultimas[0].onClick();"
        % (json.dumps(RESP), json.dumps(RESP), json.dumps(ITEMS[1]),
           json.dumps(ITEMS[2]))
        + _salida("{antes: antes, confirmacion: confirmacion,"
                  " post: registro.post}"))
    assert out["antes"] == 0                     # nada antes de confirmar
    c = out["confirmacion"]
    assert c["titulo"] == "Confirmar · Sincronizar con Sigrid"
    assert "Traer las horas de Sigrid</strong>: 2 línea(s)" in c["html"]
    assert "horas 8 → 6" in c["html"] and "horas 5 → 1" in c["html"]
    assert "recálculo de extras" in c["html"]
    assert c["acciones"] == ["Aplicar a 2 línea(s)", "Cancelar"]
    assert out["post"][0] == {"url": "/api/sincronizar/aplicar", "body": {
        "accion": "traer_de_sigrid",
        "ambito": {"vista": "obra", "period": "2026-10", "mode": "natural",
                   "obra_key": "obr-686"},
        "items": [{"registro_id": 2, "firma": "f000000000000002"},
                  {"registro_id": 3, "firma": "f000000000000003"}]}}


def test_f052_r17_sin_seleccion_no_llama() -> None:
    out = _node("confirmarAccionSync('marcar_registrada', []);"
                + _salida("[registro.post.length, registro.modal[0].titulo]"))
    assert out == [0, "Nada seleccionado"]


def test_f052_r17_resumen_marcar_registrada_y_mas_de_diez() -> None:
    muchos = [item(i, "en_sigrid_sin_registrar",
                   portal=portal(estado="error"), sigrid=sigrid(8.0, hmores=i))
              for i in range(1, 13)]
    out = _node(_salida("resumenAccionSyncHtml('marcar_registrada', %s)"
                        % json.dumps(muchos)))
    assert "12 línea(s)" in out
    assert "estado error → registrado (línea 1)" in out
    assert "… y 2 más." in out


# --------------------------- R25 re-sincroniza --------------------------- #

def test_f052_r25_al_terminar_vuelve_a_sincronizar_y_pinta() -> None:
    nueva = dict(RESP, leido_at="2026-11-03T09:31:00+00:00")
    out = _node(
        "estadoSync.boton = botonObra; estadoSync.resp = %s;"
        "respuestas['/api/sincronizar/aplicar'] = {ok: true, aplicados: [2],"
        " descartados: [{registro_id: 3, motivo: 'cambió desde que lo viste'}],"
        " recalculo: 'fallo'};"
        "respuestas['/api/sincronizar'] = %s;"
        "await aplicarSync('traer_de_sigrid', [%s, %s]);"
        % (json.dumps(RESP), json.dumps(nueva), json.dumps(ITEMS[1]),
           json.dumps(ITEMS[2]))
        + _salida("{urls: registro.post.map(function (p) { return p.url; }),"
                  " cuerpo: registro.post[1].body, panel: panel,"
                  " leido: estadoSync.resp.leido_at}"))
    assert out["urls"] == ["/api/sincronizar/aplicar", "/api/sincronizar"]
    assert out["cuerpo"] == {"ambito": {"vista": "obra", "period": "2026-10",
                                        "mode": "natural",
                                        "obra_key": "obr-686"}}
    assert out["leido"] == "2026-11-03T09:31:00+00:00"
    html = out["panel"]["innerHTML"]
    assert out["panel"]["hidden"] is False
    assert "<strong>1</strong> aplicada(s)" in html
    assert "#3: cambió desde que lo viste" in html
    assert "no se pudo pedir el recálculo de extras" in html


def test_f052_r18_error_al_aplicar_no_vuelve_a_sincronizar() -> None:
    out = _node(
        "estadoSync.boton = botonObra;"
        "respuestas['/api/sincronizar/aplicar'] = {ok: false,"
        " error: '<b>ámbito</b>'};"
        "await aplicarSync('marcar_registrada', [%s]);" % json.dumps(ITEMS[3])
        + _salida("{urls: registro.post.map(function (p) { return p.url; }),"
                  " modal: registro.modal[registro.modal.length - 1]}"))
    assert out["urls"] == ["/api/sincronizar/aplicar"]
    assert out["modal"]["titulo"] == "No se pudo aplicar"
    assert "&lt;b&gt;ámbito&lt;/b&gt;" in out["modal"]["html"]


# ------------------------- R24 modal de aprobar -------------------------- #

def test_f052_r24_reaprobar_abre_el_modal_de_aprobar() -> None:
    out = _node(
        "estadoSync.boton = botonObra;"
        "respuestas['/api/sincronizar/aplicar'] = {ok: true, aplicados: [7, 8],"
        " descartados: [], abrir_aprobar: true, incluir_borradas: true};"
        "await aplicarSync('reaprobar', [%s]);"
        % json.dumps(item(7, "borrada_en_sigrid", acciones=["reaprobar"]))
        + _salida("{urls: registro.post.map(function (p) { return p.url; }),"
                  " aprobar: registro.aprobar}"))
    assert out["urls"] == ["/api/sincronizar/aplicar"]
    assert out["aprobar"] == [{"peticion": {
        "registro_ids": [7, 8], "incluir_borradas": True,
        "ambito": {"vista": "obra", "period": "2026-10", "mode": "natural",
                   "obra_key": "obr-686"}}, "contexto": None}]


def test_f052_r24_reaprobar_sin_nada_vigente_no_abre_el_modal() -> None:
    out = _node(
        "estadoSync.boton = botonObra;"
        "respuestas['/api/sincronizar/aplicar'] = {ok: true, aplicados: [],"
        " descartados: [{registro_id: 7, motivo: 'cambió'}],"
        " abrir_aprobar: false};"
        "await aplicarSync('reaprobar', [%s]);"
        % json.dumps(item(7, "pendiente", acciones=["reaprobar"]))
        + _salida("[registro.aprobar.length,"
                  " registro.modal[registro.modal.length - 1].titulo]"))
    assert out == [0, "Nada que reaprobar"]


# --------------------------------- esc() --------------------------------- #

MALO = '<img src=x onerror="alert(1)">\'"'


def test_f052_esc_en_todo_lo_que_pinta_el_panel() -> None:
    malo = item(9, "en_sigrid_sin_registrar",
                acciones=["marcar_registrada"],
                portal=dict(portal(), hora_codigo=MALO, sigrid_estado=MALO),
                sigrid=dict(sigrid(), hora_cod=MALO, hmores_ide=MALO,
                            obra_cod=MALO),
                diferencias=[{"campo": MALO, "portal": MALO, "sigrid": MALO}],
                notas=[MALO], donde=MALO)
    resp = dict(RESP, items=[malo], leido_at=MALO, seco=True,
                marcaria_borrado_sigrid=[MALO])
    out = _node(_salida(
        "[panelSyncHtml(%s, {clase: 'todas', verACero: false}, null),"
        " resumenAccionSyncHtml('marcar_registrada', [%s]),"
        " resultadoSyncHtml({aplicados: [], descartados: [{registro_id: %s,"
        " motivo: %s}]})]"
        % (json.dumps(resp), json.dumps(malo), json.dumps(MALO),
           json.dumps(MALO))))
    for html in out:
        assert "<img" not in html
        assert 'onerror="' not in html
    assert all("&lt;img" in html for html in out)


def test_f052_esc_error_de_sincronizar() -> None:
    out = _node(
        "respuestas['/api/sincronizar'] = {ok: false, error: %s};"
        "await sincronizarAmbito(botonObra, null);" % json.dumps(MALO)
        + _salida("[panel.innerHTML, botonObra.disabled]"))
    assert "<img" not in out[0] and "No se pudo sincronizar" in out[0]
    assert out[1] is False


def test_f052_seco_y_aviso_de_la_0404() -> None:
    nuestra = item(509, "solo_sigrid_nuestra", sigrid=sigrid(obra_cod="0404"),
                   donde="no_existe")
    resp = dict(RESP, seco=True, marcaria_borrado_sigrid=[15389, 15393],
                items=[nuestra])
    out = _node(_salida("panelSyncHtml(%s, {clase: 'todas', verACero: false},"
                        " null)" % json.dumps(resp)))
    assert "modo seco" in out
    assert "se pasarían a borrado_sigrid 2 línea(s): 15389, 15393" in out
    assert "Obra 0404 (pruebas)" in out
    assert "en el portal: no_existe" in out


# ------------------------------- ficheros -------------------------------- #

def test_f052_app_js_sintaxis() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, timeout=60)
    assert r.returncode == 0, r.stderr


def test_f052_el_clic_del_boton_va_al_panel() -> None:
    js = _js()
    assert "if (clicSync(ev)) return;" in js
    assert 'ev.target.closest("#sincronizar-sigrid")' in _funcion(js,
                                                                  "clicSync")
    assert "[data-sync-acero]" in js


def test_f052_estilos_del_panel() -> None:
    css = STYLES.read_text(encoding="utf-8")
    for selector in (".sincronizar-panel", ".sync-filtros", ".sync-tabla",
                     ".sync-acciones", ".sync-mensaje"):
        assert selector in css
