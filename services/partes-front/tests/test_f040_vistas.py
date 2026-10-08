# tests/test_f040_vistas.py
"""F-040 · R15: el portal marca «sin DNI» los recursos que no lo tienen.

Donde hoy se pinta «DNI …» (o «· dni») de un recurso:

  1. Conciliar, busqueda manual (`wireConciliacion`).
  2. Combo de trabajador del detalle de obra (`wireEmpleadoCombo`).
  3. «+ Nuevo parte» (`_comboSimple("emp-combo", …)`).
  4. «+ Añadir linea» (`_comboSimple("addline-emp-combo", …)`).
  5. Candidatos de Conciliar (plantilla `conciliacion.html`).

El JS se EJECUTA con node (no basta con mirar el texto: en F-035 se escapo
un ReferenceError con tests que solo leian `app.js`): las funciones reales
de `static/app.js` corren sobre un DOM falso minimo. La plantilla se
renderiza de verdad con el portal montado (SQLite y Sigrid simulados).

Datos SINTETICOS.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from config.settings import Settings
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import RecursoOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f035_endpoints import ENTORNO, SIGRID, LookupFalso

RAIZ = Path(__file__).resolve().parents[1]
APP_JS = RAIZ / "static" / "app.js"
PLANTILLAS = RAIZ / "templates"
NODE = shutil.which("node")

CON_DNI = {"ide": 901, "codigo": "MO/0001", "nombre": "UNO RECURSO",
           "dni": "00000001R", "empresa": 28, "empresa_nombre": "Porsan",
           "score": 90}
SIN_DNI = {"ide": 904, "codigo": "MO/0004", "nombre": "CUATRO <SIN> DNI",
           "dni": None, "empresa": 28, "empresa_nombre": "Porsan",
           "score": 80}


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _llamada_combo(js: str, combo: str, filtro: str) -> str:
    inicio = js.index(f'_comboSimple("{combo}"')
    fin = js.index(f"deLaEmpresaDe({filtro}));", inicio) + len(
        f"deLaEmpresaDe({filtro}));")
    return js[inicio:fin]


#: DOM falso minimo: lo justo para que corran las funciones reales.
DOM_JS = r"""
"use strict";
function El(tag) {
  this.tag = tag; this.children = []; this.listeners = {}; this._html = "";
  this.style = {}; this.attrs = {}; this.hidden = true; this.value = "";
  this.q = {}; this.qa = {}; this.up = {};
}
Object.defineProperty(El.prototype, "innerHTML", {
  get: function () { return this._html; },
  set: function (v) { this._html = v; this.children = []; } });
El.prototype.addEventListener = function (t, f) {
  (this.listeners[t] = this.listeners[t] || []).push(f); };
El.prototype.removeEventListener = function () {};
El.prototype.appendChild = function (c) { this.children.push(c); return c; };
El.prototype.getAttribute = function (k) {
  return this.attrs[k] === undefined ? null : this.attrs[k]; };
El.prototype.fire = function (t) {
  (this.listeners[t] || []).forEach(function (f) { f({}); }); };
El.prototype.select = function () {};
El.prototype.getBoundingClientRect = function () {
  return { bottom: 0, left: 0, width: 0 }; };
El.prototype.contains = function () { return false; };
El.prototype.querySelector = function (s) { return this.q[s] || null; };
El.prototype.querySelectorAll = function (s) { return this.qa[s] || []; };
El.prototype.closest = function (s) { return this.up[s] || null; };
var docQ = {};
var document = {
  createElement: function (t) { return new El(t); },
  querySelector: function (s) { return docQ[s] || null; } };
var window = { addEventListener: function () {},
               removeEventListener: function () {} };
var RECS = %(recs)s;
function fetchRecursos() { return Promise.resolve(RECS); }
function fetch() {
  return Promise.resolve({ json: function () {
    return Promise.resolve({ ok: true, items: RECS }); } });
}
function _empReasignar() {}
function _confirmarCasado() {}
function deLaEmpresaDe() { return null; }
var selEmpresa = null, selAddEmpresa = null;
"""

#: Los cuatro puntos de pintado, ejecutados; la salida es un JSON.
ESCENARIOS_JS = r"""
var salida = {};
// 1. Conciliar: busqueda manual.
var list = new El("div"), card = new El("div"), input = new El("input"),
    results = new El("div");
docQ[".recon-list"] = list;
list.qa[".manual-q"] = [input];
input.up[".recon-card"] = card;
card.q[".manual-results"] = results;
input.attrs["data-nombre"] = "Leido";
input.value = "cuatro";
wireConciliacion();
input.fire("input");
// 2. Combo del detalle de obra.
var wrap = new El("div"), cinput = new El("input"), panel = new El("div");
wrap.q[".combo-input"] = cinput; wrap.q[".combo-panel"] = panel;
wireEmpleadoCombo(wrap);
cinput.fire("focus");
// 3 y 4. Etiqueta de los combos de «Nuevo parte» y «+ Añadir linea».
var etiquetas = {};
var combo = "";
function _comboSimple(root, i, p, url, render) {
  etiquetas[root] = RECS.map(render);
}
%(llamadas)s
setTimeout(function () {
  salida.conciliar = results.children.map(function (c) { return c.innerHTML; });
  salida.detalle = panel.children.map(function (c) { return c.innerHTML; });
  salida.combos = etiquetas;
  process.stdout.write(JSON.stringify(salida));
}, 400);
"""

FUNCIONES = ("_esc", "_norm", "empresaSufijo", "recLabel", "dniHtml",
             "dniSufijo", "wireConciliacion", "wireEmpleadoCombo")


def _ejecutar(recs: list[dict]) -> dict:
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    js = _js()
    programa = (
        DOM_JS % {"recs": json.dumps(recs)}
        + "".join(_funcion(js, f) for f in FUNCIONES)
        + ESCENARIOS_JS % {"llamadas": "\n".join((
            _llamada_combo(js, "emp-combo", "selEmpresa"),
            _llamada_combo(js, "addline-emp-combo", "selAddEmpresa")))})
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def pintado() -> dict:
    return _ejecutar([CON_DNI, SIN_DNI])


# ======================== R15 · JS ejecutado ============================ #

def test_f040_r15_conciliar_busqueda_manual(pintado) -> None:
    con, sin = pintado["conciliar"]
    assert '<span class="cell-sub">DNI 00000001R</span>' in con
    assert "sin DNI" not in con
    assert '<span class="cell-sub">sin DNI</span>' in sin
    assert "CUATRO &lt;SIN&gt; DNI" in sin           # sigue escapado


def test_f040_r15_combo_detalle_de_obra(pintado) -> None:
    con, sin = pintado["detalle"]
    assert con.endswith(' <span class="cell-sub">DNI 00000001R</span>')
    assert sin.endswith(' <span class="cell-sub">sin DNI</span>')
    assert "MO/0004 · CUATRO &lt;SIN&gt; DNI · Porsan" in sin


@pytest.mark.parametrize("combo", ["emp-combo", "addline-emp-combo"])
def test_f040_r15_combos_nuevo_parte_y_anadir_linea(pintado, combo) -> None:
    assert pintado["combos"][combo] == [
        "MO/0001 · UNO RECURSO · Porsan · 00000001R",
        "MO/0004 · CUATRO <SIN> DNI · Porsan · sin DNI",
    ]


def test_f040_r15_helpers_por_casos() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    js = _js()
    casos = ['{dni: "1R"}', '{dni: ""}', "{dni: null}", "{}", "null",
             '{dni: "<b>"}']
    programa = (
        "".join(_funcion(js, f) for f in ("_esc", "dniHtml", "dniSufijo"))
        + "process.stdout.write(JSON.stringify(["
        + ", ".join(f"[dniHtml({c}), dniSufijo({c})]" for c in casos)
        + "]));")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr
    sin = [' <span class="cell-sub">sin DNI</span>', " · sin DNI"]
    assert json.loads(r.stdout) == [
        [' <span class="cell-sub">DNI 1R</span>', " · 1R"],
        sin, sin, sin, sin,
        [' <span class="cell-sub">DNI &lt;b&gt;</span>', " · <b>"],
    ]


def test_f040_r15_app_js_pasa_node_check() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, timeout=30)
    assert r.returncode == 0, r.stderr


def test_f040_r15_no_quedan_pintados_de_dni_sin_marca() -> None:
    """Los cuatro puntos usan los helpers; no queda el patron viejo."""
    js = _js()
    assert "(it.dni ? ' <span" not in js
    assert "(e.dni ? ' <span" not in js
    assert '(r.dni ? " · " + r.dni : "")' not in js
    assert js.count("dniHtml(") == 3       # definicion + 2 usos
    assert js.count("dniSufijo(") == 3


# ===================== R15 · plantilla de Conciliar ===================== #

def test_f040_r15_plantilla_parsea() -> None:
    Environment(loader=FileSystemLoader(str(PLANTILLAS))).get_template(
        "conciliacion.html")


class LookupF040(LookupFalso):
    def fetch_recursos_activos(self) -> list:
        return [
            RecursoOption(ide=901, codigo="MO/0001", nombre="PEPE CUATRO",
                          dni="00000001R", empresa=28),
            RecursoOption(ide=904, codigo="MO/0004", nombre="PEPE CUATRO",
                          dni=None, empresa=28),
        ]


def test_f040_r15_candidatos_de_conciliar_marcan_sin_dni(monkeypatch) -> None:
    for clave, valor in {**ENTORNO, **SIGRID}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupF040)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"leido": "Pepe Cuatro"}],
                        empleado_ide=None, empleado_dni="",
                        empleado_nombre=None)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).empleado_match_method = "none"
        s.commit()
    cliente = TestClient(build_app(Settings(_env_file=None),
                                   repository=ParteReviewRepository(fabrica)))
    html = cliente.get("/conciliacion").text
    filas = re.findall(r'<tr class="recon-cand".*?</tr>', html, re.S)
    assert len(filas) == 2
    por_ide = {re.search(r'data-recurso-ide="(\d+)"', f).group(1): f
               for f in filas}
    assert '<span class="cell-sub">DNI 00000001R</span>' in por_ide["901"]
    assert "sin DNI" not in por_ide["901"]
    assert '<span class="cell-sub">sin DNI</span>' in por_ide["904"]
