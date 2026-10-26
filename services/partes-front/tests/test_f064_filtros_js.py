# tests/test_f064_filtros_js.py
"""F-064 · los filtros del portal se guardan por usuario y pantalla.

Tres bloques (patron de `test_f049_editor_js.py` y del DOM falso de F-043):

  - **puras**: se EJECUTAN en node las funciones de `FiltrosSesion`
    (caducidad, poda, foto vacia, consulta de las listas, dias) (R5-R10,
    R12, R14, R16, R17, R19).
  - **DOM falso**: el IIFE `FiltrosSesion` real, con `wireColumnFilters`,
    `_setupDaySelection` y `wireDayFilters` reales, sobre un DOM minimo y
    un `localStorage` falso (R5-R18).
  - **fuente**: el cableado del `DOMContentLoaded`, las plantillas y las
    funciones que NO deben cambiar (R15, R19-R23).

Sin navegador, red ni BBDD. Datos sinteticos.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

SV4 = Path(__file__).resolve().parents[1]
APP_JS = SV4 / "static" / "app.js"
PLANTILLAS = SV4 / "templates"
NODE = shutil.which("node")

PREFIJO = "partes.filtros.v1:"
SESION_MS = 8 * 3600 * 1000
AHORA = 1761480000000
AVISO = "Filtros recuperados de tu sesión"


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _filtros_sesion(js: str) -> str:
    m = re.search(r"\nvar FiltrosSesion = \(function \(\) \{.*?\n\}\)\(\);\n",
                  js, re.DOTALL)
    assert m, "app.js no define FiltrosSesion"
    return m.group(0)


def _avisar(js: str) -> str:
    m = re.search(r"\nfunction avisarCambioLineas\(\) \{.*?\n\}\n", js,
                  re.DOTALL)
    assert m, "app.js no define avisarCambioLineas"
    return m.group(0)


def _node(programa: str):
    """Ejecuta el programa desde un fichero temporal: con `node -e`, el de
    los tests de DOM pasa del limite de la linea de ordenes de Windows."""
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    with tempfile.TemporaryDirectory() as carpeta:
        fichero = Path(carpeta) / "programa.js"
        fichero.write_text(programa, encoding="utf-8")
        r = subprocess.run([NODE, str(fichero)], capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


#: DOM minimo: elementos con atributos, clases, hijos, `rows`/`cells`/
#: `cellIndex`, eventos sin burbuja y selectores compuestos
#: (`tag.clase[attr="v"]`, listas con coma y descendientes con espacio).
DOM_JS = r"""
"use strict";
var escrituras = [], reemplazos = [], almacen = {}, sinAlmacen = false;
var eventosDoc = [], docOn = {}, ahora = %(ahora)d;
Date.now = function () { return ahora; };
function E(tag, attrs, texto) {
  this.tagName = (tag || "div").toUpperCase(); this.attrs = {};
  this.children = []; this.parentNode = null; this.value = "";
  this.checked = false; this.hidden = false; this.on = {}; this.style = {};
  this.dataset = {}; this._texto = texto || "";
  var self = this;
  this.classList = {
    add: function (c) { var l = self._clases();
      if (l.indexOf(c) < 0) l.push(c); self.attrs["class"] = l.join(" "); },
    remove: function () { var q = [].slice.call(arguments);
      self.attrs["class"] = self._clases().filter(function (c) {
        return q.indexOf(c) < 0; }).join(" "); },
    contains: function (c) { return self._clases().indexOf(c) >= 0; },
    toggle: function (c, f) {
      if (f === undefined) f = !this.contains(c);
      if (f) this.add(c); else this.remove(c); return f; },
  };
  for (var k in (attrs || {})) this.setAttribute(k, attrs[k]);
}
E.prototype._clases = function () {
  return (this.attrs["class"] || "").split(/\s+/).filter(Boolean); };
Object.defineProperty(E.prototype, "className", {
  get: function () { return this.attrs["class"] || ""; },
  set: function (v) { this.attrs["class"] = v; } });
Object.defineProperty(E.prototype, "id", {
  get: function () { return this.attrs.id || ""; },
  set: function (v) { this.attrs.id = v; } });
Object.defineProperty(E.prototype, "textContent", {
  get: function () { return this._texto + this.children.map(function (c) {
    return c.textContent; }).join(""); },
  set: function (v) { this._texto = String(v);
    this.children.forEach(function (c) { c.parentNode = null; });
    this.children = []; } });
Object.defineProperty(E.prototype, "cellIndex", {
  get: function () { return this.parentNode
    ? this.parentNode.children.indexOf(this) : -1; } });
Object.defineProperty(E.prototype, "rows", {
  get: function () { return this.children.filter(function (c) {
    return c.tagName === "TR"; }); } });
Object.defineProperty(E.prototype, "cells", {
  get: function () { return this.children.filter(function (c) {
    return c.tagName === "TD" || c.tagName === "TH"; }); } });
Object.defineProperty(E.prototype, "firstChild", {
  get: function () { return this.children[0] || null; } });
E.prototype.getAttribute = function (k) {
  return Object.prototype.hasOwnProperty.call(this.attrs, k)
    ? this.attrs[k] : null; };
E.prototype.setAttribute = function (k, v) {
  v = String(v);
  if (k === "value") { this.value = v; return; }
  this.attrs[k] = v; };
E.prototype.hasAttribute = function (k) { return this.getAttribute(k) !== null; };
E.prototype.removeAttribute = function (k) { delete this.attrs[k]; };
E.prototype.appendChild = function (c) {
  if (c.parentNode) c.remove(); c.parentNode = this; this.children.push(c);
  return c; };
E.prototype.insertBefore = function (c, ref) {
  if (!ref) return this.appendChild(c);
  if (c.parentNode) c.remove(); c.parentNode = this;
  this.children.splice(this.children.indexOf(ref), 0, c); return c; };
E.prototype.remove = function () {
  var p = this.parentNode; if (!p) return;
  p.children.splice(p.children.indexOf(this), 1); this.parentNode = null; };
E.prototype.addEventListener = function (t, f) {
  (this.on[t] = this.on[t] || []).push(f); };
E.prototype.dispatchEvent = function (ev) {
  ev.target = ev.target || this;
  (this.on[ev.type] || []).forEach(function (f) { f(ev); }); return true; };
E.prototype.click = function () {
  this.dispatchEvent({type: "click", stopPropagation: function () {},
                      preventDefault: function () {}}); };
E.prototype._todos = function () {
  var out = [];
  this.children.forEach(function (c) { out.push(c); out.push.apply(out, c._todos()); });
  return out; };
function casa(el, sel) {
  var tag = /^[a-zA-Z]*/.exec(sel)[0], resto = sel.slice(tag.length), x;
  if (tag && el.tagName !== tag.toUpperCase()) return false;
  var re = /\.([\w-]+)|\[([\w-]+)(?:="([^"]*)")?\]|#([\w-]+)/g;
  while ((x = re.exec(resto))) {
    if (x[1]) { if (!el.classList.contains(x[1])) return false; }
    else if (x[4]) { if (el.getAttribute("id") !== x[4]) return false; }
    else if (x[3] === undefined) { if (!el.hasAttribute(x[2])) return false; }
    else if (el.getAttribute(x[2]) !== x[3]) return false;
  }
  return true; }
function casaCadena(el, partes) {           // descendientes: "a b.c"
  if (!casa(el, partes[partes.length - 1])) return false;
  var i = partes.length - 2;
  for (var e = el.parentNode; e && i >= 0; e = e.parentNode) {
    if (e.matches && casa(e, partes[i])) i--;
  }
  return i < 0; }
E.prototype.matches = function (sel) {
  var self = this;
  return sel.split(",").some(function (s) {
    return casaCadena(self, s.trim().split(/\s+/)); }); };
E.prototype.querySelectorAll = function (sel) {
  return this._todos().filter(function (e) { return e.matches(sel); }); };
E.prototype.querySelector = function (sel) {
  return this.querySelectorAll(sel)[0] || null; };
E.prototype.closest = function (sel) {
  for (var e = this; e; e = e.parentNode) { if (e.matches && e.matches(sel)) return e; }
  return null; };
function el(tag, attrs, hijos, texto) {
  var e = new E(tag, attrs, texto);
  (hijos || []).forEach(function (h) { e.appendChild(h); });
  return e; }
var body = new E("body");
globalThis.document = {
  body: body,
  createElement: function (t) { return new E(t); },
  getElementById: function (id) {
    return body._todos().filter(function (e) {
      return e.getAttribute("id") === id; })[0] || null; },
  querySelectorAll: function (s) { return body.querySelectorAll(s); },
  querySelector: function (s) { return body.querySelector(s); },
  addEventListener: function (t, f) { (docOn[t] = docOn[t] || []).push(f); },
  dispatchEvent: function (ev) { eventosDoc.push(ev.type);
    (docOn[ev.type] || []).forEach(function (f) { f(ev); }); return true; },
};
globalThis.Event = function (t, o) { this.type = t; this.bubbles = !!(o && o.bubbles); };
globalThis.CustomEvent = globalThis.Event;
var falso = {
  getItem: function (k) {
    return Object.prototype.hasOwnProperty.call(almacen, k) ? almacen[k] : null; },
  setItem: function (k, v) { escrituras.push(k); almacen[k] = String(v); },
  removeItem: function (k) { delete almacen[k]; },
  key: function (i) { var l = Object.keys(almacen); return i < l.length ? l[i] : null; },
};
Object.defineProperty(falso, "length", {get: function () {
  return Object.keys(almacen).length; }});
var ventana = {location: {pathname: "/", search: "",
  replace: function (u) { reemplazos.push(u); }}};
Object.defineProperty(ventana, "localStorage", {get: function () {
  if (sinAlmacen) throw new Error("sin localStorage"); return falso; }});
globalThis.window = ventana;
function salir(x) { process.stdout.write(JSON.stringify(x)); }
""" % {"ahora": AHORA}

#: Constructores de pagina y lecturas para los tests de DOM.
PAGINA_JS = r"""
var DATOS = {Fecha: ["2026-10-01", "2026-10-02", "2026-10-03"],
             Trabajador: ["López", "Pérez", "López"],
             Tipo: ["extra", "normal", "normal"], "": ["", "", ""],
             "~Sel": ["", "", ""]};
function pagina(ruta, search, usuario) {
  window.location.pathname = ruta; window.location.search = search || "";
  if (usuario !== null) body.dataset.filtrosUsuario =
    usuario === undefined ? "u-ana" : usuario;
  var cont = el("div", {"class": "container"});
  body.appendChild(el("main", {"class": "page-shell"}, [cont]));
  return cont;
}
// Una cabecera "~Nombre" es una columna con titulo y SIN filtro.
function tablaFiltrable(attrs, cabeceras, filas, conLimpiar) {
  var cab = el("tr", {}, cabeceras.map(function (c) {
    return el("th", {}, [], c.replace(/^~/, "")); }));
  var filtro = el("tr", {"class": "filter-row"}, cabeceras.map(function (c) {
    if (c && c.charAt(0) === "~") return el("th");
    if (c) return el("th", {}, [el("input", {"class": "col-filter"})]);
    return el("th", {}, conLimpiar
      ? [el("button", {"class": "filter-clear"}, [], "Limpiar")] : []);
  }));
  var cuerpo = el("tbody", {}, filas.map(function (f) {
    return el("tr", f.attrs || {}, f.celdas.map(function (t) {
      return el("td", {}, [], t); })); }));
  return el("table", attrs, [el("thead", {}, [cab, filtro]), cuerpo]);
}
function lineas(cont, orden) {
  orden = orden || ["Fecha", "Trabajador", "Tipo", ""];
  var filas = [0, 1, 2].map(function (i) {
    return {attrs: {"data-fecha": DATOS.Fecha[i],
                    "data-trabajador": DATOS.Trabajador[i]},
            celdas: orden.map(function (c) { return DATOS[c][i]; })}; });
  var t = tablaFiltrable({id: "lines-table", "class": "table lines-table"},
                         orden, filas, true);
  cont.appendChild(t); wireColumnFilters(t); return t;
}
function lista(cont) {
  var t = tablaFiltrable({"class": "table docs-table filterable"},
    ["Obra", "Estado", ""], [{celdas: ["0404", "pendiente", ""]},
                             {celdas: ["0500", "aprobado", ""]}], true);
  cont.appendChild(t); wireColumnFilters(t); return t;
}
function matriz(cont) {
  var cab = el("tr", {}, [el("th", {}, [], "Trabajador"),
    el("th", {}, [], "Categoría"), el("th", {}, [], "1"),
    el("th", {}, [], "2")]);
  var filtro = el("tr", {"class": "filter-row"}, [
    el("th", {}, [el("input", {"class": "col-filter"})]),
    el("th", {}, [el("input", {"class": "col-filter"})]),
    el("th"), el("th")]);
  var filas = ["López", "Pérez"].map(function (n) {
    return el("tr", {"data-sin-extra": n === "Pérez" ? "1" : "0"}, [
      el("td", {}, [], n), el("td", {}, [], "Oficial"),
      el("td", {"class": "mx-pick", "data-fecha": "2026-10-01",
                "data-trabajador": n}),
      el("td", {"class": "mx-pick", "data-fecha": "2026-10-02",
                "data-trabajador": n})]); });
  var t = el("table", {"class": "matrix filterable"},
             [el("thead", {}, [cab, filtro]), el("tbody", {}, filas)]);
  cont.appendChild(t); wireColumnFilters(t); return t;
}
function periodo(cont, valor, modo) {
  cont.appendChild(el("form", {"class": "cal-period"}, [
    el("input", {type: "hidden", name: "modo", value: modo}),
    el("select", {id: "period", value: valor})]));
}
function calendario(cont, fechas) {
  cont.appendChild(el("div", {"class": "cal-grid"}, fechas.map(function (f) {
    return el("div", {"class": "cal-pick", "data-fecha": f}); })));
  cont.appendChild(el("span", {"data-day-badge": ""},
                      [el("b", {"data-count": ""})]));
  cont.appendChild(el("button", {"data-day-clear": ""}));
}
function casilla(cont) {
  var c = el("input", {type: "checkbox", id: "hide-sin-extra"});
  c.checked = true; cont.appendChild(c); return c;
}
function guardado(usuario, pantallas, t) {
  almacen["partes.filtros.v1:" + usuario] = JSON.stringify(
    {v: 1, t: t === undefined ? ahora - 1000 : t, pantallas: pantallas});
}
function estado(usuario) {
  var c = almacen["partes.filtros.v1:" + (usuario || "u-ana")];
  return c === undefined ? null : JSON.parse(c);
}
function filtrosDe(t) {
  return t.querySelector("tr.filter-row").querySelectorAll(".col-filter")
    .map(function (i) { return i.value; });
}
function visibles(t) {
  return t.querySelector("tbody").rows.filter(function (r) {
    return r.style.display !== "none" && !r.classList.contains("filtered-day");
  }).map(function (r) { return r.textContent; });
}
function aviso() {
  var a = document.getElementById("filtros-sesion-aviso");
  return (a && !a.hidden && a.parentNode) ? a : null;
}
"""

#: Funciones de `app.js` que cablean la pagina como en produccion.
FUNCIONES_DOM = ("_norm", "_filterCellText", "wireColumnFilters",
                 "_setupDaySelection", "wireDayFilters")


def _dom(cuerpo: str) -> dict:
    js = _js()
    programa = (DOM_JS + _avisar(js)
                + "".join(_funcion(js, f) for f in FUNCIONES_DOM)
                + _filtros_sesion(js) + PAGINA_JS + cuerpo)
    return _node(programa)


def _pura(nombre: str, *args):
    js = _js()
    programa = (DOM_JS + _filtros_sesion(js)
                + "salir(FiltrosSesion.puras.%s(...%s));"
                % (nombre, json.dumps(list(args))))
    return _node(programa)


def _estado(t: int, pantallas: dict | None = None) -> str:
    return json.dumps({"v": 1, "t": t, "pantallas": pantallas or {}})


# =========================== puras · R6 ================================ #

def test_f064_r6_constantes_de_sesion() -> None:
    fuente = _filtros_sesion(_js())
    assert '  var PREFIJO = "partes.filtros.v1:";' in fuente
    assert "  var SESION_MS = 8 * 3600 * 1000;" in fuente
    assert "  var MAX_PANTALLAS = 50;" in fuente


def test_f064_r6_vigente_justo_antes_de_8h() -> None:
    est = _pura("estadoVigente", _estado(AHORA - SESION_MS + 1), AHORA)
    assert est == {"v": 1, "t": AHORA - SESION_MS + 1, "pantallas": {}}


def test_f064_r6_caduca_exactamente_a_las_8h() -> None:
    assert _pura("estadoVigente", _estado(AHORA - SESION_MS), AHORA) is None


@pytest.mark.parametrize("crudo", [
    "{no es json", "null", "[]", '"texto"',
    json.dumps({"v": 2, "t": AHORA, "pantallas": {}}),
    json.dumps({"v": 1, "t": "ayer", "pantallas": {}}),
    json.dumps({"v": 1, "t": AHORA, "pantallas": []}),
    json.dumps({"v": 1, "t": AHORA}),
])
def test_f064_r6_invalido_u_otra_version_es_vacio(crudo: str) -> None:
    assert _pura("estadoVigente", crudo, AHORA) is None


def test_f064_r6_t_en_el_futuro_es_vacio_salvo_el_margen() -> None:
    assert _pura("estadoVigente", _estado(AHORA + 60001), AHORA) is None
    assert _pura("estadoVigente", _estado(AHORA + 60000), AHORA) is not None


# ======================= puras · R5, R9, ruta ========================== #

def test_f064_r5_r9_clave_de_almacen_por_usuario() -> None:
    a = _pura("claveAlmacen", "u-ana")
    b = _pura("claveAlmacen", "u-luis")
    assert a == PREFIJO + "u-ana" and b == PREFIJO + "u-luis" and a != b
    assert _pura("claveAlmacen", "") == ""
    assert _pura("claveAlmacen", None) == ""


@pytest.mark.parametrize("entrada, salida", [
    ("/obras/obr-10/", "/obras/obr-10"), ("/obras//", "/obras"),
    ("/", "/"), ("", "/"), ("/partes", "/partes")])
def test_f064_r3_ruta_normal_sin_barra_final(entrada, salida) -> None:
    assert _pura("rutaNormal", entrada) == salida


# =================== puras · R7, R10, R14 (conPantalla) ================= #

FOTO = {"cols": {"lines-table": {"Tipo": "extra"}}}


def test_f064_r4_r10_con_pantalla_pone_la_foto_con_su_t() -> None:
    est = _pura("conPantalla", None, "/obras/obr-10", FOTO, AHORA)
    assert est == {"v": 1, "t": AHORA, "pantallas": {
        "/obras/obr-10": {"cols": {"lines-table": {"Tipo": "extra"}},
                          "t": AHORA}}}


def test_f064_r10_r14_foto_vacia_quita_la_entrada() -> None:
    previo = json.loads(_estado(AHORA - 5, {"/a": {"t": 1, "query": "x"},
                                            "/b": {"t": 2, "query": "y"}}))
    est = _pura("conPantalla", previo, "/a", {"cols": {"t": {}}}, AHORA)
    assert est["t"] == AHORA and list(est["pantallas"]) == ["/b"]


def test_f064_r7_poda_a_las_50_mas_recientes() -> None:
    pantallas = {f"/p{i}": {"t": i, "query": "search=x"} for i in range(1, 51)}
    est = _pura("conPantalla", {"v": 1, "t": 50, "pantallas": pantallas},
                "/nueva", FOTO, AHORA)
    assert len(est["pantallas"]) == 50
    assert "/p1" not in est["pantallas"] and "/nueva" in est["pantallas"]
    assert "/p2" in est["pantallas"]


def test_f064_r7_con_pantalla_no_muta_el_estado_de_entrada() -> None:
    js = _js()
    r = _node(DOM_JS + _filtros_sesion(js) + """
var previo = {v: 1, t: 5, pantallas: {"/a": {t: 5, query: "x"}}};
var copia = JSON.stringify(previo);
FiltrosSesion.puras.conPantalla(previo, "/a", {}, %d);
salir(JSON.stringify(previo) === copia);""" % AHORA)
    assert r is True


@pytest.mark.parametrize("foto, vacia", [
    ({}, True), (None, True),
    ({"cols": {"lines-table": {}}}, True),
    ({"sinExtra": True}, True),
    ({"dias": {"periodo": "p", "claves": []}}, True),
    ({"query": ""}, True),
    ({"cols": {"tabla": {"Obra": "04"}}}, False),
    ({"dias": {"periodo": "p", "claves": ["2026-10-01"]}}, False),
    ({"sinExtra": False}, False),
    ({"query": "search=04"}, False),
])
def test_f064_r14_foto_vacia(foto, vacia) -> None:
    assert _pura("fotoVacia", foto) is vacia


@pytest.mark.parametrize("foto, repuestos", [
    ({"cols": {"tabla": {"Obra": "04"}}}, True),
    ({"dias": {"periodo": "p", "claves": ["d"]}}, True),
    ({"sinExtra": False, "query": "search=x"}, False),
    ({}, False),
])
def test_f064_r17_filtros_repuestos(foto, repuestos) -> None:
    assert _pura("filtrosRepuestos", foto) is repuestos


# ==================== puras · R19 (listas del servidor) ================= #

@pytest.mark.parametrize("ruta, search, consulta", [
    ("/partes", "?search=&pendientes=1", "pendientes=1"),
    ("/partes", "?pendientes=1&search=0404", "search=0404&pendientes=1"),
    ("/partes", "?search=", ""),
    ("/partes", "", ""),
    ("/obras", "?search=Calle%20Mayor", "search=Calle%20Mayor"),
    ("/trabajadores", "?search=l%C3%B3pez", "search=l%C3%B3pez"),
    ("/partes", "?search=x&message=hola", None),
    ("/obras", "?pendientes=1", None),
    ("/obras/obr-10", "?search=x", None),
    ("/papelera", "", None),
])
def test_f064_r19_consulta_de_lista(ruta, search, consulta) -> None:
    assert _pura("consultaDeLista", ruta, search) == consulta


@pytest.mark.parametrize("ruta, search, pantalla, destino", [
    ("/partes", "", {"query": "search=0404"}, "/partes?search=0404"),
    ("/obras", "", {"query": "search=04"}, "/obras?search=04"),
    ("/partes", "?search=", {"query": "search=0404"}, None),
    ("/partes", "?message=hola", {"query": "search=0404"}, None),
    ("/partes", "", None, None),
    ("/partes", "", {"query": ""}, None),
    ("/partes", "", {"cols": {"tabla": {"Obra": "04"}}}, None),
    ("/obras/obr-10", "", {"query": "search=04"}, None),
])
def test_f064_r19_destino_restaurar(ruta, search, pantalla, destino) -> None:
    assert _pura("destinoRestaurar", ruta, search, pantalla) == destino


# ==================== puras · R12, R16 (dias) ========================== #

def test_f064_r12_dias_de_otro_periodo_no_se_reponen() -> None:
    assert _pura("diasRestaurables", {"periodo": "2026-09|natural",
                                      "claves": ["2026-09-01"]},
                 "2026-10|natural", ["2026-09-01"]) == []


def test_f064_r16_dias_interseccion_en_el_orden_de_la_pagina() -> None:
    assert _pura("diasRestaurables",
                 {"periodo": "2026-10|natural",
                  "claves": ["2026-10-03", "2026-10-31", "2026-10-01"]},
                 "2026-10|natural",
                 ["2026-10-01", "2026-10-02", "2026-10-03"]) == [
        "2026-10-01", "2026-10-03"]


def test_f064_r16_sin_dias_guardados_nada() -> None:
    assert _pura("diasRestaurables", None, "", ["2026-10-01"]) == []
    assert _pura("diasRestaurables", {"periodo": ""}, "", ["d"]) == []


# ============ DOM falso · R4, R11, R15, R16, R18 (restaurar) =========== #

def test_f064_r11_r15_r18_repone_por_tabla_y_columna_aunque_se_muevan() -> None:
    r = _dom("""
guardado("u-ana", {"/obras/obr-10": {t: ahora - 5000, cols: {
  "lines-table": {"Tipo": "extra", "Inexistente": "x"},
  "matriz": {"Trabajador": "lopez"},
  "otra-tabla": {"Obra": "04"}}}});
var cont = pagina("/obras/obr-10");
var mx = matriz(cont);
var t = lineas(cont, ["Tipo", "Fecha", "Trabajador", ""]);  // columnas movidas
escrituras = []; eventosDoc = [];
FiltrosSesion.restaurar(wireDayFilters());
salir({lineas: filtrosDe(t), matriz: filtrosDe(mx), visibles: visibles(t),
       visiblesMx: visibles(mx), escrituras: escrituras.length,
       cambios: eventosDoc.filter(function (e) { return e === "lineas:cambio"; }).length,
       aviso: aviso() ? aviso().textContent : null,
       est: estado()});
""")
    assert r["lineas"] == ["extra", "", ""]
    assert r["matriz"] == ["lopez", ""]
    assert r["visibles"] == ["extra2026-10-01López"]          # R18: apply
    assert r["visiblesMx"] == ["LópezOficial"]
    assert r["cambios"] >= 1                                    # R18
    assert r["escrituras"] == 1                                 # R15
    assert r["aviso"] is not None and AVISO in r["aviso"]
    assert "Quitar filtros" in r["aviso"]
    pantalla = r["est"]["pantallas"]["/obras/obr-10"]
    assert pantalla["cols"] == {"lines-table": {"Tipo": "extra"},
                                "matriz": {"Trabajador": "lopez"}}
    assert pantalla["t"] == AHORA and r["est"]["t"] == AHORA   # R7


def test_f064_r11_columna_sin_filtro_delante_cuenta_por_cellindex() -> None:
    """Observacion 2 de la review: con una columna SIN filtro antes de las
    filtrables, la columna se identifica por la posicion de su `th`
    (`cellIndex`), no por el orden entre los `.col-filter`."""
    r = _dom("""
guardado("u-ana", {"/obras/obr-10": {t: ahora - 5000, cols: {
  "lines-table": {"Tipo": "extra"}}}});
var cont = pagina("/obras/obr-10");
var t = lineas(cont, ["~Sel", "Fecha", "Trabajador", "Tipo", ""]);
FiltrosSesion.restaurar(wireDayFilters());
var repuesto = {filtros: filtrosDe(t), visibles: visibles(t)};
var f = t.querySelector("tr.filter-row").querySelectorAll(".col-filter");
f[0].value = "2026-10"; f[0].dispatchEvent(new Event("input", {bubbles: true}));
salir({repuesto: repuesto,
       cols: estado().pantallas["/obras/obr-10"].cols["lines-table"]});
""")
    assert r["repuesto"] == {"filtros": ["", "", "extra"],
                             "visibles": ["2026-10-01Lópezextra"]}
    assert r["cols"] == {"Fecha": "2026-10", "Tipo": "extra"}


def test_f064_r11_tabla_sin_id_es_tabla_y_columna_por_data_col_key() -> None:
    r = _dom("""
var cont = pagina("/partes", "?search=04");
var t = lista(cont);
var ths = t.querySelector("thead").querySelector("tr").children;
ths[0].setAttribute("data-col-key", "Obra"); ths[0].textContent = "Obra ▲";
FiltrosSesion.restaurar(wireDayFilters());
var f = t.querySelector("tr.filter-row").querySelectorAll(".col-filter");
f[0].value = "04"; f[0].dispatchEvent(new Event("input", {bubbles: true}));
salir(estado());
""")
    assert r["pantallas"]["/partes"]["cols"] == {"tabla": {"Obra": "04"}}
    assert r["pantallas"]["/partes"]["query"] == "search=04"


def test_f064_r10_un_cambio_de_filtro_guarda_y_limpiar_borra() -> None:
    r = _dom("""
var cont = pagina("/obras/obr-10/");
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
var antes = estado();
var f = t.querySelector("tr.filter-row").querySelectorAll(".col-filter");
f[2].value = "extra"; f[2].dispatchEvent(new Event("input", {bubbles: true}));
var tras = estado();
t.querySelector(".filter-clear").click();
salir({antes: antes, tras: tras, limpio: estado()});
""")
    assert r["antes"] is None                                  # sin filtros
    assert r["tras"]["pantallas"]["/obras/obr-10"]["cols"] == {
        "lines-table": {"Tipo": "extra"}}
    assert r["limpio"] is None or r["limpio"]["pantallas"] == {}


def test_f064_r12_r16_dias_del_calendario_solo_los_que_existen() -> None:
    r = _dom("""
guardado("u-ana", {"/trabajadores/rec-501": {t: ahora - 5000, dias: {
  periodo: "2026-10|natural", claves: ["2026-10-03", "2026-10-31", "2026-10-01"]}}});
var cont = pagina("/trabajadores/rec-501");
periodo(cont, "2026-10", "natural");
calendario(cont, ["2026-10-01", "2026-10-02", "2026-10-03"]);
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
salir({marcadas: document.querySelectorAll(".day-selected").map(function (c) {
         return c.getAttribute("data-fecha"); }),
       visibles: visibles(t), aviso: !!aviso(),
       dias: estado().pantallas["/trabajadores/rec-501"].dias});
""")
    assert r["marcadas"] == ["2026-10-01", "2026-10-03"]
    assert r["visibles"] == ["2026-10-01Lópezextra", "2026-10-03Lópeznormal"]
    assert r["aviso"] is True
    assert r["dias"] == {"periodo": "2026-10|natural",
                         "claves": ["2026-10-01", "2026-10-03"]}


def test_f064_r12_otro_periodo_no_repone_ni_pierde_los_dias() -> None:
    r = _dom("""
var dias = {periodo: "2026-09|natural", claves: ["2026-09-01"]};
guardado("u-ana", {"/trabajadores/rec-501": {t: ahora - 5000, dias: dias}});
var cont = pagina("/trabajadores/rec-501");
periodo(cont, "2026-10", "natural");
calendario(cont, ["2026-09-01", "2026-10-01"]);
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
salir({marcadas: document.querySelectorAll(".day-selected").length,
       aviso: !!aviso(), est: estado()});
""")
    assert r["marcadas"] == 0 and r["aviso"] is False
    assert r["est"]["pantallas"]["/trabajadores/rec-501"]["dias"] == {
        "periodo": "2026-09|natural", "claves": ["2026-09-01"]}


def test_f064_r12_matriz_un_clic_guarda_el_dia_con_su_periodo() -> None:
    r = _dom("""
var cont = pagina("/obras/obr-10");
periodo(cont, "2026-10", "nomina");
var mx = matriz(cont);
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
mx.querySelectorAll("td.mx-pick")[1].click();
salir({tras: estado().pantallas["/obras/obr-10"].dias});
""")
    assert r["tras"] == {"periodo": "2026-10|nomina",
                         "claves": ["lopez|2026-10-02"]}


def test_f064_r12_sin_formulario_el_periodo_es_vacio() -> None:
    r = _dom("""
var cont = pagina("/obras/obr-10");
var mx = matriz(cont);
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
mx.querySelectorAll("td.mx-pick")[0].click();
salir(estado().pantallas["/obras/obr-10"].dias);
""")
    assert r == {"periodo": "", "claves": ["lopez|2026-10-01"]}


def test_f064_r13_casilla_de_la_matriz_solo_desmarcada() -> None:
    r = _dom("""
guardado("u-ana", {"/obras/obr-10": {t: ahora - 5000, sinExtra: false}});
var cont = pagina("/obras/obr-10");
var c = casilla(cont);
var cambios = 0; c.addEventListener("change", function () { cambios++; });
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
var repuesta = {checked: c.checked, cambios: cambios, aviso: !!aviso(),
                sinExtra: estado().pantallas["/obras/obr-10"].sinExtra};
c.checked = true; c.dispatchEvent(new Event("change"));
salir({repuesta: repuesta, tras: estado()});
""")
    assert r["repuesta"] == {"checked": False, "cambios": 1, "aviso": False,
                             "sinExtra": False}
    assert r["tras"] is None or "/obras/obr-10" not in r["tras"]["pantallas"]


def test_f064_r17_quitar_filtros_lo_deja_todo_limpio() -> None:
    r = _dom("""
guardado("u-ana", {"/obras/obr-10": {t: ahora - 5000, sinExtra: false,
  cols: {"lines-table": {"Tipo": "extra"}, "matriz": {"Trabajador": "lopez"}},
  dias: {periodo: "2026-10|natural", claves: ["lopez|2026-10-01"]}}});
var cont = pagina("/obras/obr-10");
periodo(cont, "2026-10", "natural");
var c = casilla(cont);
var mx = matriz(cont);
cont.appendChild(el("button", {"data-day-clear": ""}));
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
var antes = {marcadas: document.querySelectorAll(".day-selected").length,
             lineas: filtrosDe(t), matriz: filtrosDe(mx), casilla: c.checked};
aviso().querySelector("button").click();
salir({antes: antes, lineas: filtrosDe(t), matriz: filtrosDe(mx),
       marcadas: document.querySelectorAll(".day-selected").length,
       casilla: c.checked, aviso: !!aviso(), visibles: visibles(t),
       est: estado()});
""")
    assert r["antes"] == {"marcadas": 1, "lineas": ["", "", "extra"],
                          "matriz": ["lopez", ""], "casilla": False}
    assert r["lineas"] == ["", "", ""] and r["matriz"] == ["", ""]
    assert r["marcadas"] == 0 and r["casilla"] is True
    assert r["aviso"] is False
    assert len(r["visibles"]) == 3
    assert r["est"] is None or "/obras/obr-10" not in r["est"]["pantallas"]


# ========= observacion 4 · entradas mal formadas en el almacen ========= #

def test_f064_r6_entradas_de_pantalla_mal_formadas_se_descartan() -> None:
    crudo = json.dumps({"v": 1, "t": AHORA, "pantallas": {
        "/a": None, "/b": {"t": 5, "query": "search=x"}, "/c": 7,
        "/d": [], "/e": {"query": "sin-t"}, "/f": "texto",
        "/g": {"t": "ayer"}}})
    est = _pura("estadoVigente", crudo, AHORA)
    assert est == {"v": 1, "t": AHORA,
                   "pantallas": {"/b": {"t": 5, "query": "search=x"}}}


def _cola_del_init(js: str) -> str:
    """Las lineas reales del `DOMContentLoaded` principal desde
    `FiltrosSesion.restaurar(dias);` hasta `esperasDeLaPagina();`."""
    bloque = _bloque_principal(js)
    ini = bloque.index("    FiltrosSesion.restaurar(dias);\n")
    fin = bloque.index("    esperasDeLaPagina();\n", ini)
    return bloque[ini:fin + len("    esperasDeLaPagina();\n")]


def test_f064_r6_pantalla_null_no_corta_el_init_de_f043() -> None:
    """Observacion 4: una pantalla `null` (u otra basura) en el almacen no
    puede lanzar dentro de `restaurar` y dejar sin correr `restaurarVista`
    ni `esperasDeLaPagina` (F-043)."""
    r = _dom("""
almacen["partes.filtros.v1:u-ana"] = JSON.stringify({v: 1, t: ahora - 1000,
  pantallas: {"/otra": null, "/rota": 7,
              "/obras/obr-10": {t: ahora - 5000,
                                cols: {"lines-table": {"Tipo": "extra"}}}}});
var corridas = [], error = null;
function restaurarVista() { corridas.push("restaurarVista"); }
function esperasDeLaPagina() { corridas.push("esperasDeLaPagina"); }
var cont = pagina("/obras/obr-10");
var t = lineas(cont);
try {
  var dias = wireDayFilters();
""" + _cola_del_init(_js()) + """
} catch (e) { error = String(e); }
salir({error: error, corridas: corridas, filtros: filtrosDe(t),
       pantallas: Object.keys(estado().pantallas)});
""")
    assert r["error"] is None
    assert r["corridas"] == ["restaurarVista", "esperasDeLaPagina"]
    assert r["filtros"] == ["", "", "extra"]
    assert r["pantallas"] == ["/obras/obr-10"]


# ===================== DOM falso · R5, R6, R8, R9 ====================== #

def test_f064_r5_sin_clave_de_usuario_no_guarda_ni_repone() -> None:
    r = _dom("""
guardado("", {"/obras/obr-10": {t: ahora, cols: {"lines-table": {"Tipo": "x"}}}});
var cont = pagina("/obras/obr-10", "", "");
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
var f = t.querySelector("tr.filter-row").querySelectorAll(".col-filter");
f[2].value = "extra"; f[2].dispatchEvent(new Event("input", {bubbles: true}));
salir({filtros: filtrosDe(t), escrituras: escrituras.length,
       redirige: FiltrosSesion.redirigir(), aviso: !!aviso()});
""")
    assert r == {"filtros": ["", "", "extra"], "escrituras": 0,
                 "redirige": False, "aviso": False}


def test_f064_r5_localstorage_que_lanza_no_rompe_nada() -> None:
    r = _dom("""
sinAlmacen = true;
var cont = pagina("/partes");
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
var f = t.querySelector("tr.filter-row").querySelectorAll(".col-filter");
f[2].value = "extra"; f[2].dispatchEvent(new Event("input", {bubbles: true}));
salir({redirige: FiltrosSesion.redirigir(), visibles: visibles(t).length});
""")
    assert r == {"redirige": False, "visibles": 1}


def test_f064_r6_r8_barre_caducados_de_cualquier_usuario() -> None:
    r = _dom("""
guardado("u-luis", {"/partes": {t: 1, query: "search=x"}}, ahora - %d);
guardado("u-eva", {"/partes": {t: 1, query: "search=y"}}, ahora - 1000);
guardado("u-ana", {"/obras": {t: 1, query: "search=z"}}, ahora - %d);
almacen["partes.filtros.v1:u-rota"] = "{rota";
almacen["ct:/partes:tabla"] = "{}";
var cont = pagina("/obras");
lista(cont);
FiltrosSesion.restaurar(wireDayFilters());
salir({claves: Object.keys(almacen).sort(), reemplazos: reemplazos});
""" % (SESION_MS, SESION_MS))
    assert r["claves"] == ["ct:/partes:tabla", PREFIJO + "u-eva"]
    assert r["reemplazos"] == []


def test_f064_r6_estado_caducado_no_redirige() -> None:
    r = _dom("""
guardado("u-ana", {"/partes": {t: 1, query: "search=0404"}}, ahora - %d);
pagina("/partes");
salir({redirige: FiltrosSesion.redirigir(), reemplazos: reemplazos,
       queda: estado()});
""" % SESION_MS)
    assert r == {"redirige": False, "reemplazos": [], "queda": None}


def test_f064_r9_lo_de_un_usuario_no_lo_lee_otro() -> None:
    r = _dom("""
guardado("u-ana", {"/obras/obr-10": {t: ahora, cols: {"lines-table": {"Tipo": "extra"}}},
                   "/partes": {t: ahora, query: "search=0404"}});
var cont = pagina("/obras/obr-10", "", "u-luis");
var t = lineas(cont);
FiltrosSesion.restaurar(wireDayFilters());
window.location.pathname = "/partes";
salir({filtros: filtrosDe(t), aviso: !!aviso(),
       redirige: FiltrosSesion.redirigir(),
       ana: estado("u-ana").pantallas["/obras/obr-10"].cols});
""")
    assert r["filtros"] == ["", "", ""] and r["aviso"] is False
    assert r["redirige"] is False
    assert r["ana"] == {"lines-table": {"Tipo": "extra"}}


# ===================== DOM falso · R19 (redirigir) ===================== #

def test_f064_r19_lista_sin_consulta_vuelve_a_la_busqueda() -> None:
    r = _dom("""
guardado("u-ana", {"/partes": {t: ahora, query: "search=0404&pendientes=1"}});
pagina("/partes/");
salir({redirige: FiltrosSesion.redirigir(), reemplazos: reemplazos});
""")
    assert r == {"redirige": True,
                 "reemplazos": ["/partes?search=0404&pendientes=1"]}


def test_f064_r19_con_otro_parametro_ni_guarda_ni_redirige() -> None:
    r = _dom("""
guardado("u-ana", {"/partes": {t: ahora - 10, query: "search=0404"}});
var cont = pagina("/partes", "?message=Parte%20borrado");
lista(cont);
var redirige = FiltrosSesion.redirigir();
FiltrosSesion.restaurar(wireDayFilters());
salir({redirige: redirige, query: estado().pantallas["/partes"].query});
""")
    assert r == {"redirige": False, "query": "search=0404"}


def test_f064_r19_r20_limpiar_guarda_la_busqueda_vacia() -> None:
    r = _dom("""
guardado("u-ana", {"/obras": {t: ahora - 10, query: "search=04"}});
var cont = pagina("/obras", "?search=");
lista(cont);
var redirige = FiltrosSesion.redirigir();
FiltrosSesion.restaurar(wireDayFilters());
salir({redirige: redirige, est: estado()});
""")
    assert r["redirige"] is False
    assert r["est"] is None or "/obras" not in r["est"]["pantallas"]


def test_f064_r19_la_busqueda_de_la_lista_se_guarda_normalizada() -> None:
    r = _dom("""
var cont = pagina("/partes", "?pendientes=1&search=0404");
lista(cont);
FiltrosSesion.restaurar(wireDayFilters());
salir({est: estado(), aviso: !!aviso()});
""")
    assert r["est"]["pantallas"]["/partes"]["query"] == (
        "search=0404&pendientes=1")
    assert r["aviso"] is False          # la busqueda no enciende el aviso


# ============ DOM falso · T4 (el manejador de dias, R12, R16) =========== #

def test_f064_r16_manejador_de_dias_ignora_lo_que_no_existe() -> None:
    r = _dom("""
var cont = pagina("/trabajadores/rec-501");
calendario(cont, ["2026-10-01", "2026-10-02", "2026-10-02"]);
var t = lineas(cont);
var dias = wireDayFilters();
var disp = dias.disponibles();
dias.seleccionar(["2026-10-02", "2026-10-31"]);
var tras = dias.claves();
var badge = document.querySelector("[data-day-badge]");
var cuenta = badge.querySelector("[data-count]").textContent;
dias.limpiar();
salir({disp: disp, tras: tras, cuenta: cuenta, limpio: dias.claves(),
       visibles: visibles(t).length});
""")
    assert r["disp"] == ["2026-10-01", "2026-10-02"]
    assert r["tras"] == ["2026-10-02"] and r["cuenta"] == "1"
    assert r["limpio"] == [] and r["visibles"] == 3


def test_f064_r16_sin_tabla_de_lineas_el_manejador_es_nulo() -> None:
    r = _dom("""
pagina("/partes");
var dias = wireDayFilters();
dias.seleccionar(["x"]); dias.limpiar();
salir({claves: dias.claves(), disp: dias.disponibles()});
""")
    assert r == {"claves": [], "disp": []}


# ======================== fuente · R15, R19, R21 ======================= #

def _bloque_principal(js: str) -> str:
    ini = js.index('  document.addEventListener("DOMContentLoaded", '
                   'function () {\n')
    return js[ini:js.index("\n  });\n", ini)]


def test_f064_r19_redirigir_es_la_primera_linea_del_init() -> None:
    lineas = [l for l in _bloque_principal(_js()).split("\n")[1:] if l.strip()]
    assert lineas[0].startswith("    if (FiltrosSesion.redirigir()) return;")


def test_f064_r15_restaurar_va_justo_antes_de_restaurar_vista() -> None:
    bloque = _bloque_principal(_js())
    assert "    var dias = wireDayFilters();\n" in bloque
    assert "\n    wireDayFilters();\n" not in bloque
    i = bloque.index("    FiltrosSesion.restaurar(dias);\n")
    j = bloque.index("    restaurarVista();\n")
    assert i < j
    assert bloque[i:j].count("\n") == 1, "nada entre las dos llamadas"


def test_f064_r21_filtros_sesion_no_toca_la_seleccion() -> None:
    fuente = _filtros_sesion(_js())
    assert "PartidaSel" not in fuente
    assert "sel-linea" not in fuente


# ======================== fuente · R22, R23 =========================== #

#: Huella del texto de cada funcion en `dev` (2b2c735, antes de F-064).
HUELLAS = {
    "conjuntoAprobacion": "aa794b6271a3eb10",
    "restaurarVista": "8c08766cae4315b1",
    "vistaRestaurable": "025c76ad623a79ad",
    "actualizarVista": "9593826b31aca6fa",
    "_ctKey": "11f4b540d5f5d9e5",
}


@pytest.mark.parametrize("nombre", sorted(HUELLAS))
def test_f064_r22_r23_funciones_intactas(nombre: str) -> None:
    texto = _funcion(_js(), nombre)
    assert hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16] == (
        HUELLAS[nombre])


def test_f064_r23_vista_clave_intacta() -> None:
    js = _js()
    assert js.count('\n  var VISTA_CLAVE = "partes.vista.restaurar";\n') == 1


# ============================ R20 · plantillas ========================== #

@pytest.mark.parametrize("plantilla, ruta", [
    ("partes_list.html", "/partes"), ("obras_list.html", "/obras"),
    ("trabajadores_list.html", "/trabajadores")])
def test_f064_r20_limpiar_apunta_a_search_vacio(plantilla, ruta) -> None:
    html = (PLANTILLAS / plantilla).read_text(encoding="utf-8")
    assert f'href="{ruta}?search=">Limpiar</a>' in html
    assert f'href="{ruta}">Limpiar</a>' not in html
