# tests/test_f082_sin_partida.py
"""F-082 · el portal siempre ofrece «— Sin partida —» al editar la partida.

Criterios `acceptance` (sdd=false):

- A1: los dos selectores de partida (el ✎ de la celda, `wirePartidaEdit`, y
  «Editar partida» de la barra de selección, `wireBulkSelect`) usan
  `buildPartidaPicker`, y este ofrece la fila fija «— Sin partida —» SIEMPRE:
  con partidas, con texto que no casa nada, con los chips CD/CI y en una
  obra sin presupuesto. Se EJECUTA en node sobre un DOM mínimo (patrón de
  `test_f064_filtros_js.py`).
- A2: elegirla llama a `onPick` con una partida vacía, y `applyPartidaToIds`
  manda los cuatro campos a null al PATCH. La celda de una línea sin partida
  con método `manual` dice «sin partida» con la etiqueta «manual» y SIN el
  aviso ⚠ en las tres plantillas (obra, parte y trabajador); el resto de
  casos no cambia. Se renderiza la celda `cell-partida` REAL de cada
  plantilla con Jinja2.

Sin red ni BBDD. Datos sintéticos.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import jinja2
import pytest

SV4 = Path(__file__).resolve().parents[1]
APP_JS = SV4 / "static" / "app.js"
PLANTILLAS = SV4 / "templates"
NODE = shutil.which("node")
SIN_PARTIDA = "— Sin partida —"


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    with tempfile.TemporaryDirectory() as carpeta:
        fichero = Path(carpeta) / "programa.js"
        fichero.write_text(programa, encoding="utf-8")
        r = subprocess.run([NODE, str(fichero)], capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


#: DOM mínimo para `buildPartidaPicker`: el `innerHTML` del host crea el
#: input y el panel; el resto son elementos con hijos, clases y eventos.
DOM = r"""
function El(tag) {
  this.tagName = tag; this.children = []; this.className = "";
  this.textContent = ""; this.hidden = false; this.disabled = false;
  this.value = ""; this.placeholder = ""; this._l = {};
}
El.prototype.appendChild = function (c) { this.children.push(c); return c; };
El.prototype.addEventListener = function (t, f) {
  (this._l[t] = this._l[t] || []).push(f);
};
El.prototype.fire = function (t) {
  (this._l[t] || []).forEach(function (f) {
    f({ preventDefault: function () {} });
  });
};
El.prototype.focus = function () { this.fire("focus"); };
Object.defineProperty(El.prototype, "innerHTML", {
  get: function () { return ""; },
  set: function (v) {
    this.children = [];
    if (v.indexOf("combo-input") !== -1) {
      this._input = new El("input"); this._input.disabled = true;
      this._panel = new El("div"); this._panel.hidden = true;
    }
  }
});
El.prototype.querySelector = function (s) {
  if (s === ".combo-input") return this._input;
  if (s === ".combo-panel") return this._panel;
  return null;
};
var document = { createElement: function (t) { return new El(t); } };
var window = { addEventListener: function () {} };
function positionPanel() {}
var MotivoHttp = { lanzarSiFalla: function (r) { return r; } };
var enviados = [];
function fetch(url, o) { enviados.push({ url: url, body: JSON.parse(o.body) });
  return Promise.resolve({ ok: true }); }
var PARTIDAS = {};
function loadPartidas(obra) { return Promise.resolve(PARTIDAS[obra] || []); }
function filas(panel) {
  return panel.children.filter(function (c) {
    return c.className.split(" ").indexOf("combo-option") !== -1;
  });
}
function elegirSinPartida(panel) {
  var f = filas(panel).filter(function (r) {
    return r.textContent === "— Sin partida —";
  })[0];
  if (f) f.fire("mousedown");
}
function textos(panel) {
  return panel.children.map(function (c) { return c.textContent; });
}
"""


def _programa(cuerpo: str) -> str:
    js = _js()
    return (DOM + _funcion(js, "plabel") + _funcion(js, "applyPartidaToIds")
            + _funcion(js, "buildPartidaPicker")
            + "\n(async function () {\n" + cuerpo + "\n})();\n")


ESCENARIOS = r"""
PARTIDAS["100"] = [
  { ide: 1, cod: "P1", res: "Encofrado", capitulo: "CD" },
  { ide: 2, cod: "P2", res: "Gastos generales", capitulo: "CI" }
];
var out = {};
async function abrir(obra) {
  var host = new El("div"), elegidas = [];
  buildPartidaPicker(host, obra, function (p) { elegidas.push(p); });
  await Promise.resolve(); await Promise.resolve();
  return { host: host, input: host._input, panel: host._panel,
           elegidas: elegidas };
}
// Con partidas: la primera fila elegible es «Sin partida».
var a = await abrir("100");
out.con = { textos: textos(a.panel),
            primera: (filas(a.panel)[0] || {}).textContent || null,
            n: filas(a.panel).length, visible: !a.panel.hidden };
// Texto que no casa nada: sigue la fila.
a.input.value = "zzz"; a.input.fire("input");
out.filtro = { filas: filas(a.panel).map(function (r) { return r.textContent; }),
               textos: textos(a.panel) };
// Chip CI: sigue la fila (y la partida CI).
a.input.value = "";
var chipCI = a.panel.children[0].children[2]; chipCI.fire("mousedown");
out.chip = filas(a.panel).map(function (r) { return r.textContent; });
// Elegirla: onPick con partida vacía y PATCH con los cuatro campos a null.
elegirSinPartida(a.panel);
out.elegida = a.elegidas[0] || null;
if (a.elegidas[0]) await applyPartidaToIds(["7", "8"], a.elegidas[0]);
out.enviados = enviados;
// Una partida normal sigue mandando sus campos.
enviados = [];
await applyPartidaToIds(["9"], PARTIDAS["100"][0]);
out.normal = enviados;
// Obra sin presupuesto: la fila está igual.
var b = await abrir("999");
out.vacia = { filas: filas(b.panel).map(function (r) { return r.textContent; }),
              visible: !b.panel.hidden, placeholder: b.input.placeholder };
elegirSinPartida(b.panel);
out.vacia.elegidas = b.elegidas.length;
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def escenarios() -> dict:
    return _node(_programa(ESCENARIOS))


# --------------------------------- A1 ----------------------------------- #

def test_f082_a1_con_partidas_ofrece_sin_partida_primero(escenarios) -> None:
    con = escenarios["con"]
    assert con["visible"] is True
    assert con["primera"] == SIN_PARTIDA
    assert con["n"] == 3          # «Sin partida» + las dos partidas


def test_f082_a1_texto_sin_coincidencias_mantiene_la_fila(escenarios) -> None:
    f = escenarios["filtro"]
    assert f["filas"] == [SIN_PARTIDA]
    assert "Sin partidas con ese filtro" in f["textos"]


def test_f082_a1_chip_mantiene_la_fila(escenarios) -> None:
    assert escenarios["chip"] == [SIN_PARTIDA, "[CI] P2 · Gastos generales"]


def test_f082_a1_obra_sin_presupuesto_ofrece_sin_partida(escenarios) -> None:
    v = escenarios["vacia"]
    assert v["visible"] is True
    assert v["filas"] == [SIN_PARTIDA]
    assert v["elegidas"] == 1


def test_f082_a1_los_dos_selectores_usan_el_picker() -> None:
    js = _js()
    for nombre in ("wirePartidaEdit", "wireBulkSelect"):
        assert "buildPartidaPicker(" in _funcion(js, nombre), nombre


# --------------------------------- A2 ----------------------------------- #

def test_f082_a2_elegir_sin_partida_manda_todo_null(escenarios) -> None:
    vacio = {"partida_ide": None, "partida_cod": None, "partida_res": None,
             "partida_capitulo": None}
    assert escenarios["elegida"] is not None
    assert escenarios["elegida"]["ide"] is None
    assert [e["url"] for e in escenarios["enviados"]] == [
        "/api/registros/7/partida", "/api/registros/8/partida"]
    assert all(e["body"] == vacio for e in escenarios["enviados"])


def test_f082_a2_partida_normal_sin_cambios(escenarios) -> None:
    assert escenarios["normal"][0]["body"] == {
        "partida_ide": 1, "partida_cod": "P1", "partida_res": "Encofrado",
        "partida_capitulo": "CD"}


PLANTILLAS_CELDA = ("obra_detail.html", "parte_detail.html",
                    "trabajador_detail.html")


def _celda(plantilla: str, **r) -> str:
    fuente = (PLANTILLAS / plantilla).read_text(encoding="utf-8")
    m = re.search(r'<td class="cell-partida">.*?</td>', fuente, re.DOTALL)
    assert m, f"{plantilla} sin celda cell-partida"
    base = {"partida_cod": None, "partida_res": None, "partida_capitulo": None,
            "partida_match_method": None, "partida_leida": None}
    base.update(r)
    html = jinja2.Environment().from_string(m.group(0)).render(r=base)
    return re.sub(r"\s+", " ", html)


@pytest.mark.parametrize("plantilla", PLANTILLAS_CELDA)
def test_f082_a2_sin_partida_manual_sin_aviso(plantilla) -> None:
    for leida in (None, "0716"):
        html = _celda(plantilla, partida_match_method="manual",
                      partida_leida=leida)
        assert "⚠" not in html
        assert "partida-warn" not in html
        assert "no encontrada" not in html
        assert "sin partida" in html
        assert '<span class="tag-manual">manual</span>' in html


@pytest.mark.parametrize("plantilla", PLANTILLAS_CELDA)
def test_f082_a2_resto_de_casos_sin_cambios(plantilla) -> None:
    html = _celda(plantilla, partida_leida="0716",
                  partida_match_method="parte")
    assert "⚠ 0716 no encontrada" in html
    html = _celda(plantilla)
    assert "⚠ sin partida" in html
    assert "tag-manual" not in html
    html = _celda(plantilla, partida_cod="P1", partida_res="Encofrado",
                  partida_capitulo="CD", partida_match_method="manual")
    assert "P1" in html and "tag-manual" in html and "⚠" not in html
