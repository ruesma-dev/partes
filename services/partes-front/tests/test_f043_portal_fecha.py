# tests/test_f043_portal_fecha.py
"""F-043 · el portal: rotulo, confirmacion y parte «en espera».

- R1: «Fecha del parte» en las cabeceras y en cada `.fecha-edit`.
- R5-R11: confirmar el cambio de fecha con el alcance del parte.
- R18-R26, R40: espera de un solo parte, aviso no modal, sondeo y
  «Actualizar» que conserva la vista; nada recarga solo.

Las funciones puras de `static/app.js` se EJECUTAN con node (se saltan
sin node); el cableado se lee del fuente. Sin red. Datos sinteticos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_SV4 = Path(__file__).resolve().parents[1]
PLANTILLAS = RAIZ_SV4 / "templates"
APP_JS = RAIZ_SV4 / "static" / "app.js"
STYLES = RAIZ_SV4 / "static" / "styles.css"

TITULO = "Es la fecha del PARTE: cambiarla mueve todas sus líneas y trabajadores"


def _fuente(nombre: str) -> str:
    return (PLANTILLAS / nombre).read_text(encoding="utf-8")


def _inputs_fecha(fuente: str) -> list[str]:
    """Cada etiqueta `<input ...>` con la clase `fecha-edit`."""
    return [m.group(0) for m in re.finditer(r"<input\b[^>]*>", fuente,
                                            re.DOTALL)
            if re.search(r'class="[^"]*\bfecha-edit\b', m.group(0))]


# ================================ R1 =================================== #

@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f043_r1_la_cabecera_dice_fecha_del_parte(plantilla) -> None:
    fuente = _fuente(plantilla)
    assert f'<th title="{TITULO}">Fecha del parte</th>' in fuente
    assert "<th>Fecha</th>" not in fuente


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html",
                                       "parte_detail.html"])
def test_f043_r1_cada_fecha_edit_lo_explica(plantilla) -> None:
    inputs = _inputs_fecha(_fuente(plantilla))
    assert len(inputs) == 1, inputs
    for etiqueta in inputs:
        assert f'title="{TITULO}"' in etiqueta
        assert 'aria-label="Fecha del parte"' in etiqueta


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html",
                                       "parte_detail.html"])
def test_f043_r1_r37_las_plantillas_parsean(plantilla) -> None:
    from jinja2 import Environment, FileSystemLoader

    entorno = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])


# ====================== app.js ejecutado con node ======================= #

import json as _json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

NODE = shutil.which("node")


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _motivo_http(js: str) -> str:
    m = re.search(r"\nvar MotivoHttp = \(function \(\) \{.*?\n\}\)\(\);\n",
                  js, re.DOTALL)
    assert m, "app.js no define MotivoHttp"
    return m.group(0)


def _variables(js: str, prefijos: tuple[str, ...]) -> str:
    """Las `var` de nivel IIFE (dos espacios) que empiezan por esos nombres."""
    lineas = [l for l in js.split("\n")
              if re.match(r"  var (" + "|".join(prefijos) + r")\w* = ", l)]
    assert lineas, prefijos
    return "\n".join(lineas) + "\n"


#: DOM minimo: elementos con atributos, clases, hijos y selectores
#: compuestos (`tag.clase[attr="v"]`, listas con coma; sin descendientes).
DOM_JS = r"""
"use strict";
var eventos = [], timers = [], peticiones = [], rutas = {};
var ahora = 1000000, confirmar = true, almacen = {}, sinAlmacen = false;
Date.now = function () { return ahora; };
globalThis.setTimeout = function (f, ms) {
  eventos.push("timer:" + ms); timers.push([f, ms]); return timers.length; };
globalThis.clearTimeout = function () {};
function E(tag, attrs) {
  this.tagName = (tag || "div").toUpperCase(); this.attrs = {};
  this.children = []; this.parentNode = null; this.disabled = false;
  this.value = ""; this.defaultValue = ""; this.textContent = "";
  this.title = ""; this.hidden = false; this.scrollTop = 0;
  this.scrollLeft = 0; this.on = {}; this.style = {};
  var self = this;
  this.classList = {
    add: function (c) { var l = self._clases();
      if (l.indexOf(c) < 0) l.push(c); self.attrs["class"] = l.join(" "); },
    remove: function () { var q = [].slice.call(arguments);
      self.attrs["class"] = self._clases().filter(function (c) {
        return q.indexOf(c) < 0; }).join(" "); },
    contains: function (c) { return self._clases().indexOf(c) >= 0; },
  };
  for (var k in (attrs || {})) this.setAttribute(k, attrs[k]);
}
E.prototype._clases = function () {
  return (this.attrs["class"] || "").split(/\s+/).filter(Boolean); };
Object.defineProperty(E.prototype, "className", {
  get: function () { return this.attrs["class"] || ""; },
  set: function (v) { this.attrs["class"] = v; } });
E.prototype.getAttribute = function (k) {
  return Object.prototype.hasOwnProperty.call(this.attrs, k)
    ? this.attrs[k] : null; };
E.prototype.setAttribute = function (k, v) {
  v = String(v);
  if (k === "value") { this.value = v; this.defaultValue = v; return; }
  if (k === "disabled") { this.disabled = true; return; }
  if (k === "title") { this.title = v; return; }
  this.attrs[k] = v; };
E.prototype.hasAttribute = function (k) { return this.getAttribute(k) !== null; };
E.prototype.removeAttribute = function (k) { delete this.attrs[k]; };
E.prototype.appendChild = function (c) {
  if (c.parentNode) c.remove(); c.parentNode = this; this.children.push(c);
  return c; };
E.prototype.remove = function () {
  var p = this.parentNode; if (!p) return;
  p.children.splice(p.children.indexOf(this), 1); this.parentNode = null; };
E.prototype.addEventListener = function (t, f) {
  (this.on[t] = this.on[t] || []).push(f); };
E.prototype.disparar = function (t, ev) {
  ev = ev || {type: t, key: null, preventDefault: function () {}};
  (this.on[t] || []).forEach(function (f) { f(ev); }); };
E.prototype.dispatchEvent = function (ev) {
  eventos.push("evento:" + ev.type); this.disparar(ev.type, ev); return true; };
E.prototype._todos = function () {
  var out = [];
  this.children.forEach(function (c) { out.push(c); out.push.apply(out, c._todos()); });
  return out; };
function casa(el, sel) {
  var tag = /^[a-zA-Z]*/.exec(sel)[0], resto = sel.slice(tag.length), x;
  if (tag && el.tagName !== tag.toUpperCase()) return false;
  var re = /\.([\w-]+)|\[([\w-]+)(?:="([^"]*)")?\]/g;
  while ((x = re.exec(resto))) {
    if (x[1]) { if (!el.classList.contains(x[1])) return false; }
    else if (x[3] === undefined) { if (!el.hasAttribute(x[2])) return false; }
    else if (el.getAttribute(x[2]) !== x[3]) return false;
  }
  return true; }
E.prototype.matches = function (sel) {
  var self = this;
  return sel.split(",").some(function (s) { return casa(self, s.trim()); }); };
E.prototype.querySelectorAll = function (sel) {
  return this._todos().filter(function (e) { return e.matches(sel); }); };
E.prototype.querySelector = function (sel) {
  return this.querySelectorAll(sel)[0] || null; };
E.prototype.closest = function (sel) {
  for (var e = this; e; e = e.parentNode) { if (e.matches && e.matches(sel)) return e; }
  return null; };
function el(tag, attrs, hijos) {
  var e = new E(tag, attrs);
  (hijos || []).forEach(function (h) { e.appendChild(h); });
  return e; }
var body = new E("body");
globalThis.document = {
  body: body, activeElement: null,
  createElement: function (t) { return new E(t); },
  getElementById: function (id) {
    return body._todos().filter(function (e) {
      return e.getAttribute("id") === id; })[0] || null; },
  querySelectorAll: function (s) { return body.querySelectorAll(s); },
  querySelector: function (s) { return body.querySelector(s); },
  addEventListener: function () {},
};
globalThis.Event = function (t, o) { this.type = t; this.bubbles = !!(o && o.bubbles); };
var ventana = {
  confirm: function (m) { eventos.push("confirm:" + m); return confirmar; },
  alert: function (m) { eventos.push("alert:" + m); },
  location: {href: "https://portal.example/obras/obr-10?period=2026-03",
             reload: function () { eventos.push("reload"); }},
  scrollX: 0, scrollY: 0,
  scrollTo: function (x, y) { eventos.push("scrollTo:" + x + "," + y); },
};
Object.defineProperty(ventana, "sessionStorage", {get: function () {
  if (sinAlmacen) throw new Error("sin sessionStorage");
  return {getItem: function (k) { return k in almacen ? almacen[k] : null; },
          setItem: function (k, v) { almacen[k] = String(v); },
          removeItem: function (k) { delete almacen[k]; }}; }});
globalThis.window = ventana;
globalThis.fetch = function (url, opts) {
  peticiones.push([url, (opts && opts.method) || "GET"]);
  var clave = Object.keys(rutas).filter(function (k) {
    return url.indexOf(k) >= 0; })[0];
  var r = clave ? rutas[clave] : {status: 200, json: {ok: true}};
  if (typeof r === "function") r = r(url);
  if (r === "red") return Promise.reject(new TypeError("Failed to fetch"));
  return Promise.resolve({ok: r.status < 400, status: r.status,
    json: function () { return Promise.resolve(r.json); }});
};
function tic() { return new Promise(function (r) { setImmediate(r); }); }
async function drenar() { for (var i = 0; i < 15; i++) { await tic(); } }
function salir(x) { process.stdout.write(JSON.stringify(x)); }
"""

#: Funciones de `app.js` que necesita el portal de fecha y espera.
FUNCIONES = ("flashEl", "setStatus", "estadoRecalculo", "fmtFechaEs",
             "textoConfirmacionFecha", "wireFechaInput")


def _programa(cuerpo: str, funciones: tuple[str, ...] = FUNCIONES,
              variables: tuple[str, ...] = ()) -> str:
    js = _js()
    return (DOM_JS + _motivo_http(js)
            + (_variables(js, variables) if variables else "")
            + "".join(_funcion(js, f) for f in funciones)
            + "(async function () {\n" + cuerpo + "\n})();\n")


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return _json.loads(r.stdout)


# ======================= R6/R7 · textos puros ========================== #

def test_f043_r6_fmt_fecha_es() -> None:
    assert _node(_programa(
        'salir([fmtFechaEs("2026-10-01"), fmtFechaEs("2026-03-20T00:00"),'
        ' fmtFechaEs(""), fmtFechaEs(null), fmtFechaEs("raro")]);',
        ("fmtFechaEs",))) == ["01/10/2026", "20/03/2026", "", "", "raro"]


def test_f043_r6_r7_texto_de_la_confirmacion() -> None:
    casos = [
        [{"trabajadores": 4, "lineas": 9}, "2026-10-11", "2026-10-01"],
        [{"trabajadores": 2, "lineas": 1}, "2026-10-11", "2026-10-01"],
        [{"trabajadores": 1, "lineas": 3}, "2026-10-11", "2026-10-01"],
        [{"trabajadores": 1, "lineas": 1}, "2026-10-11", "2026-10-01"],
        [{"trabajadores": 0, "lineas": 0}, "2026-10-11", "2026-10-01"],
        [None, "2026-10-11", "2026-10-01"],
    ]
    textos = _node(_programa(
        "var c = " + _json.dumps(casos) + "; salir(c.map(function (x) {"
        " return textoConfirmacionFecha(x[0], x[1], x[2]); }));",
        ("fmtFechaEs", "textoConfirmacionFecha")))
    assert textos == [
        "Vas a cambiar la fecha del PARTE entero: sus 4 trabajadores "
        "(9 líneas) pasan del 11/10/2026 al 01/10/2026. ¿Seguro?",
        "Vas a cambiar la fecha del PARTE entero: sus 2 trabajadores "
        "(1 línea) pasan del 11/10/2026 al 01/10/2026. ¿Seguro?",
        "Vas a cambiar la fecha del PARTE entero: su único trabajador "
        "(3 líneas) pasa del 11/10/2026 al 01/10/2026. ¿Seguro?",
        "Vas a cambiar la fecha del PARTE entero: su único trabajador "
        "(1 línea) pasa del 11/10/2026 al 01/10/2026. ¿Seguro?",
        "El parte no tiene líneas activas; su fecha pasa del 11/10/2026 "
        "al 01/10/2026. ¿Seguro?",
        "Vas a cambiar la fecha del PARTE entero (todas sus líneas y "
        "trabajadores) al 01/10/2026. ¿Seguro?",
    ]


# ===================== R5-R11 · wireFechaInput ========================= #

#: Una vista con dos filas del mismo parte y una de otro.
VISTA_JS = r"""
function fila(doc, reg, fecha) {
  var inp = el("input", {"class": "fecha-edit cell-edit", type: "date",
    "data-document-id": doc, value: fecha,
    title: "Es la fecha del PARTE", "data-status": "st-" + reg});
  return el("tr", {"data-registro-id": reg, "data-document-id": doc,
                   "data-fecha": fecha},
    [el("td", {"class": "cell-fecha"}, [inp])]);
}
var tabla = el("table", {}, [fila("doc-1", "1", "2026-10-11"),
  fila("doc-1", "2", "2026-10-11"), fila("doc-2", "3", "2026-10-12")]);
body.appendChild(tabla);
body.appendChild(el("span", {id: "st-1"}));
var inps = document.querySelectorAll(".fecha-edit");
inps.forEach(function (i) { wireFechaInput(i); });
var inp = inps[0];
rutas["/alcance"] = {status: 200, json: {ok: true, document_id: "doc-1",
  fecha: "2026-10-11", trabajadores: 2, lineas: 2}};
rutas["/fecha"] = {status: 200, json: {ok: true, fecha: "2026-10-01",
  fecha_int: 20261001, recalculo: "sin_cola"}};
function estado() {
  return {valores: inps.map(function (i) { return [i.value, i.defaultValue,
    i.disabled]; }), st: document.getElementById("st-1").textContent,
    titulo: inp.title, eventos: eventos.slice(), peticiones: peticiones.slice()};
}
"""

CONFIRMA = ("confirm:Vas a cambiar la fecha del PARTE entero: sus 2 "
            "trabajadores (2 líneas) pasan del 11/10/2026 al 01/10/2026. "
            "¿Seguro?")
ALCANCE = ["/api/partes/doc-1/alcance", "GET"]
PATCH = ["/api/partes/doc-1/fecha", "PATCH"]


def _vista(acciones: str) -> dict:
    return _node(_programa(VISTA_JS + acciones + "\nsalir(estado());"))


def test_f043_r5_change_sin_foco_confirma_con_el_alcance_y_guarda() -> None:
    r = _vista('inp.value = "2026-10-01"; inp.disparar("change"); '
               "await drenar();")
    assert r["peticiones"] == [ALCANCE, PATCH]
    assert [e for e in r["eventos"] if e.startswith("confirm:")] == [CONFIRMA]
    assert r["st"] == "✓ Guardado (sin recálculo automático)"


def test_f043_r5_con_foco_espera_a_salir_del_campo() -> None:
    r = _vista('document.activeElement = inp; inp.value = "2026-10-01";'
               ' inp.disparar("change"); await drenar();'
               " var antes = peticiones.length;"
               ' document.activeElement = null; inp.disparar("blur");'
               " await drenar(); eventos.unshift(\"antes:\" + antes);")
    assert r["eventos"][0] == "antes:0"
    assert r["peticiones"] == [ALCANCE, PATCH]


def test_f043_r5_con_foco_confirma_con_enter() -> None:
    r = _vista('document.activeElement = inp; inp.value = "2026-10-01";'
               ' inp.disparar("change");'
               ' inp.disparar("keydown", {type: "keydown", key: "Tab",'
               " preventDefault: function () {}});"
               " await drenar(); var antes = peticiones.length;"
               ' inp.disparar("keydown", {type: "keydown", key: "Enter",'
               ' preventDefault: function () { eventos.push("pd"); }});'
               ' await drenar(); eventos.unshift("antes:" + antes);')
    assert r["eventos"][0] == "antes:0"
    assert "pd" in r["eventos"]
    assert r["peticiones"] == [ALCANCE, PATCH]


@pytest.mark.parametrize("valor", ["", "2026-10-11"])
def test_f043_r5_vacia_o_la_misma_no_pregunta(valor) -> None:
    r = _vista(f'inp.value = "{valor}"; inp.disparar("change");'
               ' inp.disparar("blur"); await drenar();')
    assert r["peticiones"] == []
    assert not [e for e in r["eventos"] if e.startswith("confirm:")]


def test_f043_r5_las_tres_plantillas_cablean_fecha_edit() -> None:
    js = _js()
    assert '_cablear(".fecha-edit", wireFechaInput);' in js
    cuerpo = _funcion(js, "wireFechaInput")
    for trozo in ('"/alcance"', "window.confirm(", "textoConfirmacionFecha(",
                  'addEventListener("change"', 'addEventListener("blur"',
                  'addEventListener("keydown"', '"Enter"',
                  "document.activeElement !== inp"):
        assert trozo in cuerpo, trozo


def test_f043_r7_si_el_alcance_falla_pregunta_sin_cifras() -> None:
    r = _vista('rutas["/alcance"] = {status: 404, json: {detail: "x"}};'
               ' inp.value = "2026-10-01"; inp.disparar("change");'
               " await drenar();")
    assert [e for e in r["eventos"] if e.startswith("confirm:")] == [
        "confirm:Vas a cambiar la fecha del PARTE entero (todas sus líneas"
        " y trabajadores) al 01/10/2026. ¿Seguro?"]
    assert r["peticiones"] == [ALCANCE, PATCH]


def test_f043_r7_si_el_alcance_no_llega_tambien() -> None:
    r = _vista('rutas["/alcance"] = "red"; inp.value = "2026-10-01";'
               ' inp.disparar("change"); await drenar();')
    assert r["peticiones"] == [ALCANCE, PATCH]


def test_f043_r8_cancelar_vuelve_a_la_guardada_y_no_envia() -> None:
    r = _vista('confirmar = false; inp.value = "2026-10-01";'
               ' inp.disparar("change"); await drenar();'
               ' inp.disparar("blur"); await drenar();')
    assert r["peticiones"] == [ALCANCE]
    assert r["valores"][0] == ["2026-10-11", "2026-10-11", False]


def test_f043_r9_si_el_patch_falla_vuelve_y_dice_por_que() -> None:
    r = _vista('rutas["/fecha"] = {status: 409, json: {ok: false,'
               ' congelado: true, error: "El parte se está recalculando'
               ' (extras): espera a que termine."}};'
               ' inp.value = "2026-10-01"; inp.disparar("change");'
               " await drenar();")
    motivo = "El parte se está recalculando (extras): espera a que termine."
    assert r["valores"][0] == ["2026-10-11", "2026-10-11", False]
    assert r["st"] == "✗ " + motivo
    assert r["titulo"] == motivo


def test_f043_r10_la_nueva_es_la_guardada_en_el_y_sus_hermanos() -> None:
    r = _vista('inp.value = "2026-10-01"; inp.disparar("change");'
               " await drenar();")
    assert r["valores"] == [["2026-10-01", "2026-10-01", False],
                            ["2026-10-01", "2026-10-01", False],
                            ["2026-10-12", "2026-10-12", False]]
    assert r["titulo"] == "Es la fecha del PARTE"


def test_f043_r10_tras_guardar_salir_del_campo_no_repite() -> None:
    r = _vista('inp.value = "2026-10-01"; inp.disparar("change");'
               ' await drenar(); inp.disparar("blur"); await drenar();')
    assert r["peticiones"] == [ALCANCE, PATCH]


def test_f043_r11_el_blur_del_dialogo_no_abre_otro() -> None:
    """`window.confirm` quita el foco: ese blur no cuenta."""
    r = _vista('window.confirm = function (m) { eventos.push("confirm");'
               ' inp.disparar("blur"); inp.disparar("change"); return true; };'
               ' inp.value = "2026-10-01"; inp.disparar("change");'
               " await drenar();")
    assert r["eventos"].count("confirm") == 1
    assert r["peticiones"] == [ALCANCE, PATCH]


def test_f043_r11_con_el_patch_en_vuelo_no_se_abre_otro() -> None:
    r = _vista('rutas["/fecha"] = function () {'
               ' inp.value = "2026-10-02"; inp.disparar("blur");'
               ' inp.disparar("change"); eventos.push("en-vuelo:" + inp.disabled);'
               ' return {status: 200, json: {ok: true, fecha: "2026-10-01"}}; };'
               ' inp.value = "2026-10-01"; inp.disparar("change");'
               " await drenar();")
    assert "en-vuelo:true" in r["eventos"]
    assert r["peticiones"] == [ALCANCE, PATCH]


# ============ R18-R26, R40 · el parte en espera y su aviso ============== #

#: Todo lo que necesita la espera (ademas de `FUNCIONES`).
ESPERA = FUNCIONES + (
    "accionPorEstado", "vistaRestaurable", "textoAvisoRecalculo",
    "contenedoresEspera", "marcarEspera", "ponerEnEspera", "soltarEspera",
    "avisoRecalculo", "vigilarRecalculo", "sondearRecalculo",
    "aplicarEstadoRecalculo", "actualizarVista", "restaurarVista",
    "esperasDeLaPagina")
VARIABLES = ("RECALCULO_", "VISTA_", "recalculo")

#: Dos filas del parte doc-1 (una con un control ya deshabilitado), una de
#: doc-2 y el contenedor del detalle de doc-1.
PAGINA_JS = r"""
function fila(doc, reg, fecha, extra) {
  var hijos = [el("input", {"class": "sel-linea", type: "checkbox"}),
    el("input", {"class": "fecha-edit cell-edit", type: "date",
      "data-document-id": doc, value: fecha, "data-status": "st-" + reg}),
    el("button", {"class": "line-del"})];
  var tr = el("tr", Object.assign({"data-registro-id": reg,
    "data-document-id": doc, "data-fecha": fecha}, extra || {}),
    [el("td", {"class": "cell-fecha"}, hijos),
     el("td", {}, [el("input", {"class": "horas-edit", value: "8"}),
                   el("select", {"class": "combo-hora"}),
                   el("textarea", {}),
                   el("button", {"class": "ya", disabled: "disabled"})])]);
  return tr;
}
var tabla = el("table", {}, [fila("doc-1", "1", "2026-10-11"),
  fila("doc-1", "2", "2026-10-11"), fila("doc-2", "3", "2026-10-12")]);
var cabecera = el("div", {"class": "info-grid", "data-parte-contenido": "",
  "data-document-id": "doc-1"}, [el("input", {"class": "fecha-edit",
  "data-document-id": "doc-1", value: "2026-10-11"})]);
body.appendChild(tabla); body.appendChild(cabecera);
body.appendChild(el("div", {"class": "table-scroll"}, []));
body.appendChild(el("div", {"class": "matrix-scroll"}, []));
body.appendChild(el("input", {"class": "col-filter", value: ""}));
body.appendChild(el("input", {"class": "col-filter", value: ""}));
body.appendChild(el("span", {id: "st-1"}));
function controles(doc) {
  return document.querySelectorAll('tr[data-document-id="' + doc + '"],' +
    ' [data-parte-contenido][data-document-id="' + doc + '"]')
    .map(function (c) {
      return {esp: c.getAttribute("data-recalculando"),
              dis: c.querySelectorAll("input,select,textarea,button")
                .map(function (x) { return x.disabled; }),
              marcas: c.querySelectorAll(".recalculando-marca")
                .map(function (m) { return m.textContent; })};
    });
}
function tarjetas() {
  return document.querySelectorAll(".recalculo-tarjeta").map(function (t) {
    return {doc: t.getAttribute("data-document-id"),
            texto: t.querySelector(".recalculo-texto").textContent,
            actualizar: !!t.querySelector("[data-recalculo-actualizar]")};
  });
}
function caja() {
  var c = document.getElementById("recalculo-avisos");
  return c && [c.getAttribute("role"), c.getAttribute("aria-live")];
}
async function correrTimers() {
  var t = timers; timers = [];
  t.forEach(function (x) { x[0](); }); await drenar();
}
function foto() {
  return {d1: controles("doc-1"), d2: controles("doc-2"), tarjetas: tarjetas(),
          caja: caja(), eventos: eventos.slice(), peticiones: peticiones.slice(),
          vigilados: Object.keys(recalculoVigilados),
          sondeo: !!recalculoSondeo, almacen: almacen};
}
"""

LIBRES = [False, False, False, False, False, False, True]
ESPERANDO = [True] * 7
TEXTO_ESPERA = ("Recalculando extras del parte del 01/10/2026 (suele tardar "
                "1–2 min). Puedes seguir trabajando con el resto.")
TEXTO_TERMINADO = "Extras del parte del 01/10/2026 recalculadas."
TEXTO_VENCIDO = ("No se ha podido confirmar el recálculo de extras del parte "
                 "del 01/10/2026. Pulsa Actualizar; si las extras no cambian, "
                 "vuelve a guardar la fecha.")
TEXTO_SOLTAR = "✓ Guardado · recalculando extras (recarga en 1–2 min)"
TEXTO_FALLO = ("Fecha guardada, pero no se pudo pedir el recálculo de "
               "extras: vuelve a guardar la fecha")


def _pagina(acciones: str) -> dict:
    return _node(_programa(PAGINA_JS + acciones + "\nsalir(foto());",
                           ESPERA, VARIABLES))


def _estado(estados: dict) -> str:
    return ('rutas["/api/recalculo"] = {status: 200, json: {ok: true, '
            "estados: " + _json.dumps({k: {"estado": v}
                                       for k, v in estados.items()}) + "}};")


def test_f043_r25_accion_por_estado() -> None:
    assert _node(_programa(
        "salir(['pendiente', 'error', undefined, 'raro', 'terminado', "
        "'vencido', 'sin_seguimiento', 'no_existe'].map(accionPorEstado));",
        ("accionPorEstado",))) == [
        "esperar", "esperar", "esperar", "esperar", "terminado", "vencido",
        "soltar", "quitar"]


def test_f043_r21_vista_restaurable() -> None:
    url = "https://portal.example/obras/obr-10?period=2026-03"
    casos = [
        [{"url": url, "t": 1000}, url, 1000 + 59999],
        [{"url": url, "t": 1000}, url, 1000 + 60000],
        [{"url": url, "t": 1000}, url + "&x=1", 1001],
        [{"url": url, "t": 1000}, url, 999],
        [{"url": url}, url, 1001],
        [None, url, 1001],
        ["texto", url, 1001],
    ]
    r = _node(_programa(
        "var c = " + _json.dumps(casos) + "; salir(c.map(function (x) {"
        " return vistaRestaurable(x[0], x[1], x[2]); }));",
        ("vistaRestaurable",), ("VISTA_",)))
    assert r == [{"url": url, "t": 1000}, None, None, None, None, None, None]


def test_f043_r18_constantes() -> None:
    r = _node(_programa(
        "salir([RECALCULO_SONDEO_MS, RECALCULO_SIN_RESPUESTA_MS, VISTA_CLAVE,"
        " VISTA_MAX_MS]);", (), ("RECALCULO_", "VISTA_")))
    assert r == [5000, 720000, "partes.vista.restaurar", 60000]


def test_f043_r18_poner_en_espera_solo_ese_parte() -> None:
    r = _pagina('ponerEnEspera("doc-1"); ponerEnEspera("doc-1");')
    assert [c["esp"] for c in r["d1"]] == ["1", "1", "1"]
    assert [c["dis"] for c in r["d1"]] == [ESPERANDO, ESPERANDO, [True]]
    assert [c["marcas"] for c in r["d1"]] == [["recalculando…"]] * 3
    assert r["d2"] == [{"esp": None, "dis": LIBRES, "marcas": []}]
    assert not [e for e in r["eventos"] if e in ("reload",)
                or e.startswith("scrollTo")]


def test_f043_r23_soltar_espera_devuelve_cada_control() -> None:
    r = _pagina('ponerEnEspera("doc-1"); soltarEspera("doc-1");'
                ' soltarEspera("doc-2");')
    assert r["d1"] == [{"esp": None, "dis": LIBRES, "marcas": []},
                       {"esp": None, "dis": LIBRES, "marcas": []},
                       {"esp": None, "dis": [False], "marcas": []}]
    assert r["d2"] == [{"esp": None, "dis": LIBRES, "marcas": []}]


def _guardar_con(recalculo: str) -> str:
    return ('rutas["/alcance"] = {status: 200, json: {ok: true,'
            ' trabajadores: 2, lineas: 2}};'
            ' rutas["/fecha"] = {status: 200, json: {ok: true,'
            ' fecha: "2026-10-01", fecha_int: 20261001, recalculo: "'
            + recalculo + '"}};'
            ' var inps = document.querySelectorAll(".fecha-edit");'
            " inps.forEach(function (i) { wireFechaInput(i); });"
            ' inps[0].value = "2026-10-01"; inps[0].disparar("change");'
            " await drenar();")


def test_f043_r18_tras_pedir_el_recalculo_el_parte_espera() -> None:
    r = _pagina(_guardar_con("pedido"))
    assert [c["dis"] for c in r["d1"]] == [ESPERANDO, ESPERANDO, [True]]
    assert [c["marcas"] for c in r["d1"]] == [["recalculando…"]] * 3
    assert r["d2"] == [{"esp": None, "dis": LIBRES, "marcas": []}]
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_ESPERA,
                              "actualizar": False}]
    assert r["caja"] == ["status", "polite"]
    assert r["vigilados"] == ["doc-1"] and r["sondeo"] is True
    assert "timer:5000" in r["eventos"]
    assert "reload" not in r["eventos"]


def test_f043_r18_sondea_todos_en_una_peticion_y_sigue_si_pendiente() -> None:
    r = _pagina(_estado({"doc-1": "pendiente", "doc-2": "pendiente"})
                + ' vigilarRecalculo("doc-1", "2026-10-01");'
                ' vigilarRecalculo("doc-2", "2026-10-02");'
                " await correrTimers();")
    assert r["peticiones"] == [["/api/recalculo?ids=doc-1,doc-2", "GET"]]
    assert r["eventos"] == ["timer:5000", "timer:5000"]
    assert r["vigilados"] == ["doc-1", "doc-2"]


def test_f043_r20_terminado_ofrece_actualizar_y_sigue_deshabilitado() -> None:
    r = _pagina(_guardar_con("pedido") + _estado({"doc-1": "terminado"})
                + " eventos = []; await correrTimers();")
    assert [c["dis"] for c in r["d1"]] == [ESPERANDO, ESPERANDO, [True]]
    assert [c["marcas"] for c in r["d1"]] == [
        ["recalculado · pulsa Actualizar"]] * 3
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_TERMINADO,
                              "actualizar": True}]
    assert r["vigilados"] == [] and r["sondeo"] is False
    assert r["eventos"] == []            # ni otro sondeo ni recarga


def test_f043_r21_actualizar_guarda_la_vista_y_recarga() -> None:
    r = _pagina('window.scrollX = 3; window.scrollY = 420;'
                ' document.querySelector(".table-scroll").scrollTop = 77;'
                ' document.querySelector(".matrix-scroll").scrollLeft = 15;'
                ' document.querySelectorAll(".col-filter")[1].value = "pepe";'
                ' avisoRecalculo("doc-1", "terminado", "2026-10-01");'
                ' document.querySelector("[data-recalculo-actualizar]")'
                '.disparar("click");')
    assert r["eventos"] == ["reload"]
    vista = _json.loads(r["almacen"]["partes.vista.restaurar"])
    assert vista == {"url": "https://portal.example/obras/obr-10?"
                            "period=2026-03",
                     "t": 1000000, "x": 3, "y": 420,
                     "scrolls": [[77, 0], [0, 15]], "filtros": ["", "pepe"]}


def test_f043_r21_sin_session_storage_recarga_sin_mas() -> None:
    r = _pagina('sinAlmacen = true; actualizarVista();')
    assert r["eventos"] == ["reload"]


def test_f043_r21_restaurar_la_vista_y_borrarla() -> None:
    vista = {"url": "https://portal.example/obras/obr-10?period=2026-03",
             "t": 1000000 - 5000, "x": 3, "y": 420,
             "scrolls": [[77, 0], [0, 15]], "filtros": ["", "pepe"]}
    r = _node(_programa(
        PAGINA_JS + "almacen['partes.vista.restaurar'] = "
        + _json.dumps(_json.dumps(vista)) + "; restaurarVista();"
        " var ts = document.querySelector('.table-scroll'),"
        " ms = document.querySelector('.matrix-scroll');"
        " salir({eventos: eventos, almacen: almacen,"
        " scrolls: [[ts.scrollTop, ts.scrollLeft], [ms.scrollTop, ms.scrollLeft]],"
        " filtros: document.querySelectorAll('.col-filter').map(function (f)"
        " { return f.value; })});", ESPERA, VARIABLES))
    assert r["almacen"] == {}
    assert r["filtros"] == ["", "pepe"]
    assert r["scrolls"] == [[77, 0], [0, 15]]
    assert r["eventos"] == ["evento:input", "scrollTo:3,420"]


@pytest.mark.parametrize("cambio", [
    "vista.t = ahora - 60000;", 'vista.url = "https://portal.example/otra";'])
def test_f043_r21_no_se_restaura_vieja_ni_de_otra_pagina(cambio) -> None:
    r = _node(_programa(
        PAGINA_JS + "var vista = {url: window.location.href, t: ahora,"
        " x: 1, y: 2, scrolls: [[5, 5]], filtros: ['x']}; " + cambio
        + " almacen['partes.vista.restaurar'] = JSON.stringify(vista);"
        " restaurarVista(); salir({eventos: eventos, almacen: almacen});",
        ESPERA, VARIABLES))
    assert r == {"eventos": [], "almacen": {}}


def test_f043_r21_restaurar_sin_session_storage_no_rompe() -> None:
    r = _node(_programa(PAGINA_JS + "sinAlmacen = true; restaurarVista();"
                        " salir(eventos);", ESPERA, VARIABLES))
    assert r == []


def test_f043_r22_vencido_deja_de_sondear_con_aviso_fijo() -> None:
    r = _pagina(_guardar_con("pedido") + _estado({"doc-1": "vencido"})
                + " eventos = []; await correrTimers();")
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_VENCIDO,
                              "actualizar": True}]
    assert r["vigilados"] == [] and r["sondeo"] is False
    assert r["eventos"] == []


def test_f043_r23_sin_seguimiento_suelta_el_parte() -> None:
    r = _pagina(_guardar_con("pedido") + _estado({"doc-1": "sin_seguimiento"})
                + " await correrTimers();")
    assert [c["dis"] for c in r["d1"]] == [LIBRES, LIBRES, [False]]
    assert [c["esp"] for c in r["d1"]] == [None, None, None]
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_SOLTAR,
                              "actualizar": False}]
    assert r["vigilados"] == []


def test_f043_r23_no_existe_suelta_y_quita_el_aviso() -> None:
    r = _pagina(_guardar_con("pedido") + _estado({"doc-1": "no_existe"})
                + " await correrTimers();")
    assert [c["dis"] for c in r["d1"]] == [LIBRES, LIBRES, [False]]
    assert r["tarjetas"] == []
    assert r["vigilados"] == [] and r["sondeo"] is False


@pytest.mark.parametrize("fallo", [
    'rutas["/api/recalculo"] = "red";',
    'rutas["/api/recalculo"] = {status: 503, json: {}};',
    'rutas["/api/recalculo"] = {status: 200, json: {ok: false}};'])
def test_f043_r23_un_sondeo_fallido_no_corta_nada(fallo) -> None:
    r = _pagina(_guardar_con("pedido") + fallo
                + " eventos = []; await correrTimers();")
    assert r["eventos"] == ["timer:5000"]
    assert r["vigilados"] == ["doc-1"]
    assert [c["dis"] for c in r["d1"]] == [ESPERANDO, ESPERANDO, [True]]


def test_f043_r23_doce_minutos_sin_respuesta_valida_vence() -> None:
    r = _pagina(_guardar_con("pedido") + 'vigilarRecalculo("doc-2", "");'
                ' rutas["/api/recalculo"] = "red";'
                " ahora += 719999; eventos = []; await correrTimers();"
                ' eventos.push("|"); ahora += 1; await correrTimers();')
    assert r["eventos"] == ["timer:5000", "|"]
    textos = {t["doc"]: t["texto"] for t in r["tarjetas"]}
    assert textos["doc-1"] == TEXTO_VENCIDO
    assert textos["doc-2"].startswith("No se ha podido confirmar")
    assert r["vigilados"] == [] and r["sondeo"] is False


def test_f043_r23_una_respuesta_valida_reinicia_el_plazo() -> None:
    r = _pagina(_guardar_con("pedido") + _estado({"doc-1": "pendiente"})
                + " ahora += 700000; await correrTimers();"
                ' rutas["/api/recalculo"] = "red"; ahora += 700000;'
                " eventos = []; await correrTimers();")
    assert r["eventos"] == ["timer:5000"]
    assert r["vigilados"] == ["doc-1"]


def test_f043_r24_si_no_se_pudo_pedir_aviso_fijo_y_sin_espera() -> None:
    r = _pagina(_guardar_con("fallo"))
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_FALLO,
                              "actualizar": False}]
    assert [c["esp"] for c in r["d1"]] == [None, None, None]
    assert r["vigilados"] == [] and "timer:5000" not in r["eventos"]


@pytest.mark.parametrize("recalculo", ["sin_cola", None])
def test_f043_r18_sin_pedido_no_hay_espera_ni_aviso(recalculo) -> None:
    r = _pagina(_guardar_con(str(recalculo)))
    assert r["tarjetas"] == [] and r["vigilados"] == []


def test_f043_r18_la_tarjeta_se_descarta_y_no_se_duplica() -> None:
    r = _pagina('avisoRecalculo("doc-1", "espera", "2026-10-01");'
                ' avisoRecalculo("doc-1", "terminado", "2026-10-01");'
                ' avisoRecalculo("doc-2", "espera", "2026-10-02");'
                ' document.querySelector(\'.recalculo-tarjeta[data-document-id="doc-2"]\')'
                '.querySelector(".recalculo-cerrar").disparar("click");')
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_TERMINADO,
                              "actualizar": True}]


def test_f043_r18_r26_al_cargar_los_partes_marcados_esperan() -> None:
    """La vista (R37) pinta `data-recalculando="1"`: al cargar, en espera
    con su aviso y un unico sondeo para todos. Vale tras deshacer (R26)."""
    r = _pagina('document.querySelectorAll(\'[data-document-id="doc-1"]\')'
                '.forEach(function (c) { if (!c.matches(".fecha-edit"))'
                ' c.setAttribute("data-recalculando", "1"); });'
                " esperasDeLaPagina();")
    assert [c["dis"] for c in r["d1"]] == [ESPERANDO, ESPERANDO, [True]]
    assert r["d2"] == [{"esp": None, "dis": LIBRES, "marcas": []}]
    assert r["tarjetas"] == [{"doc": "doc-1", "texto": TEXTO_ESPERA.replace(
        "01/10/2026", "11/10/2026"), "actualizar": False}]
    assert r["vigilados"] == ["doc-1"]
    assert r["eventos"] == ["timer:5000"]


def test_f043_r18_sin_partes_marcados_no_sondea() -> None:
    r = _pagina("esperasDeLaPagina();")
    assert r["eventos"] == [] and r["tarjetas"] == []


# ------------------------ cableado (fuente) ---------------------------- #

def _manejador_principal(js: str) -> str:
    # El manejador cuyo cuerpo trae el visor de PDF. Desde F-064 su primera
    # linea es `if (FiltrosSesion.redirigir()) return;` (R19), asi que se
    # busca el `addEventListener` que precede al comentario, no pegado a el.
    ini = js.rindex('  document.addEventListener("DOMContentLoaded", function () {\n',
                    0, js.index("    // Toggle del visor de PDF."))
    return js[ini:js.index("\n  });\n", ini)]


def test_f043_r18_r21_r26_al_cargar_restaura_y_pone_en_espera() -> None:
    cuerpo = _manejador_principal(_js())
    assert "restaurarVista();" in cuerpo
    assert "esperasDeLaPagina();" in cuerpo
    # Antes del `return` temprano sin combos de hora, y tras los filtros.
    assert cuerpo.index("esperasDeLaPagina();") < cuerpo.index(
        "if (!combos.length) return;")
    assert cuerpo.index("wireColumnFilters") < cuerpo.index("restaurarVista();")


def test_f043_r18_seleccionar_visibles_salta_el_parte_en_espera() -> None:
    cuerpo = _funcion(_js(), "wireBulkSelect")
    ini = cuerpo.index('querySelector("[data-sel-visibles]")')
    trozo = cuerpo[ini:cuerpo.index("renderBar();", ini)]
    assert 'getAttribute("data-recalculando") !== "1"' in trozo


#: `location.reload` en `app.js` ANTES de F-043 (rama dev, 2026-10-13).
RECARGAS_PREVIAS = 22


def test_f043_r19_r40_ninguna_recarga_nueva_salvo_actualizar() -> None:
    js = _js()
    assert js.count("location.reload") == RECARGAS_PREVIAS + 1
    assert "window.location.reload();" in _funcion(js, "actualizarVista")
    for nombre in ESPERA:
        if nombre in ("actualizarVista",):
            continue
        cuerpo = _funcion(js, nombre)
        assert "reload" not in cuerpo, nombre
        assert ".focus(" not in cuerpo, nombre
        if nombre != "restaurarVista":
            assert "scrollTo" not in cuerpo, nombre


def test_f043_r26_deshacer_no_cambia() -> None:
    cuerpo = _funcion(_js(), "wireUndo")
    assert cuerpo.count("window.location.reload();") == 1
    assert "Espera" not in cuerpo and "vigilar" not in cuerpo


def test_f043_r18_estilos() -> None:
    css = STYLES.read_text(encoding="utf-8")
    for selector in ("#recalculo-avisos", ".recalculo-tarjeta",
                     ".recalculando-marca", 'tr[data-recalculando="1"]'):
        assert selector in css, selector


def test_f043_app_js_es_sintacticamente_valido() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
