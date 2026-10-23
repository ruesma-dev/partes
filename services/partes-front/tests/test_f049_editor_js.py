# tests/test_f049_editor_js.py
"""F-049 · el popup del doble clic en la matriz de obra (`static/app.js`).

Se EJECUTAN en node las funciones reales del IIFE «Matriz de obra»
(`camposCelda`, `cuerpoCelda`, `textoOtras`, `avisoAfectadas` y
`abrirPopupCelda`), extraídas con la misma expresión que F-042, con un DOM
y un `fetch` falsos. Sin navegador ni red. Datos sintéticos.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")

CELDA = {"obraKey": "obr-678", "wk": "rec-501", "fecha": "2026-10-14"}
NOTA = ("En día laborable, las ordinarias del día se ajustan a la jornada y "
        "la diferencia pasa a extra. Las extras que escribas se respetan.")
AVISO_REPARTO = ("Este día tiene un reparto entre obras pendiente de "
                 "decidir: al guardar se vuelve a calcular.")
AVISO_FALLO = ("Horas guardadas, pero no se pudo pedir el recálculo de "
               "extras: se hará en la siguiente pasada.")
TITULO_AFECTADAS = "Guardado. Este cambio recalcula también ese día en:"
SUFIJO_CONGELADA = (" (aprobada o en Sigrid: si su reparto cambia, quedará "
                    "pendiente de decidir al aprobar)")
RECARGA = "La celda ha cambiado desde que la abriste: recarga la página."


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


PURAS = ("camposCelda", "cuerpoCelda", "textoOtras", "avisoAfectadas")


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _pura(nombre: str, *args):
    js = _js()
    programa = ("".join(_funcion(js, f) for f in PURAS)
                + "process.stdout.write(JSON.stringify(%s(...%s)));"
                % (nombre, json.dumps(list(args))))
    return _node(programa)


# ============================ camposCelda =============================== #

def _campo(id_, tipo, etiqueta, valor, *, congelada=False, nueva=False):
    return {"id": id_, "tipo": tipo, "etiqueta": etiqueta, "valor": valor,
            "congelada": congelada, "nueva": nueva}


def test_f049_r1_r2_solo_extra_ofrece_la_ordinaria_nueva():
    assert _pura("camposCelda", [{"id": 5, "t": "e", "h": 10}], True) == [
        _campo(None, "n", "Ord. (nueva)", 0, nueva=True),
        _campo(5, "e", "Extra", 10)]


def test_f049_r2_solo_ordinaria_ofrece_la_extra_nueva():
    assert _pura("camposCelda", [{"id": 3, "t": "n", "h": 8,
                                  "p": "CI-01"}], True) == [
        _campo(3, "n", "Ord. · CI-01", 8),
        _campo(None, "e", "Extra (nueva)", 0, nueva=True)]


def test_f049_r1_r10_una_fila_por_linea_y_extra_de_jornada():
    assert _pura("camposCelda", [
        {"id": 1, "t": "n", "h": 8}, {"id": 2, "t": "e", "h": 2, "a": 1},
        {"id": 4, "t": "e", "h": 1, "p": "P9"}], True) == [
        _campo(1, "n", "Ord.", 8), _campo(2, "e", "Extra (jornada)", 2),
        _campo(4, "e", "Extra · P9", 1)]


def test_f049_r3_todas_congeladas_sin_nuevas():
    assert _pura("camposCelda", [{"id": 5, "t": "e", "h": 10, "c": 1}],
                 True) == [_campo(5, "e", "Extra", 10, congelada=True)]


def test_f049_r2_con_alguna_libre_si_ofrece_nueva():
    assert _pura("camposCelda", [
        {"id": 5, "t": "e", "h": 10, "c": 1}, {"id": 6, "t": "e", "h": 1}],
        True)[0] == _campo(None, "n", "Ord. (nueva)", 0, nueva=True)


def test_f049_r35_sin_trabajador_sin_nuevas():
    assert _pura("camposCelda", [{"id": 5, "t": "e", "h": 10}], False) == [
        _campo(5, "e", "Extra", 10)]


# ============================ cuerpoCelda =============================== #

E2_CAMPOS = [_campo(None, "n", "Ord. (nueva)", 0, nueva=True),
             _campo(5, "e", "Extra", 10)]


def test_f049_r7_cuerpo_con_la_nueva_y_el_cambio():
    assert _pura("cuerpoCelda", E2_CAMPOS, ["8", "2"], CELDA) == {
        "obra_key": "obr-678", "worker_key": "rec-501",
        "fecha": "2026-10-14", "lineas": [{"id": 5, "antes": 10, "horas": 2}],
        "nueva_ordinaria": 8, "nueva_extra": None}


def test_f049_r7_vacio_vale_antes_y_la_nueva_a_cero_es_null():
    campos = [_campo(1, "n", "Ord.", 8), _campo(2, "e", "Extra", 1),
              _campo(None, "e", "Extra (nueva)", 0, nueva=True)]
    assert _pura("cuerpoCelda", campos + [_campo(3, "n", "Ord.", 2)],
                 ["", "1.5", "0", "abc"], CELDA)["lineas"] == [
        {"id": 1, "antes": 8, "horas": 8}, {"id": 2, "antes": 1,
                                            "horas": 1.5},
        {"id": 3, "antes": 2, "horas": 2}]


def test_f049_r7_las_congeladas_no_viajan():
    campos = [_campo(1, "n", "Ord.", 8, congelada=True),
              _campo(2, "e", "Extra", 1)]
    cuerpo = _pura("cuerpoCelda", campos, ["5", "3"], CELDA)
    assert cuerpo["lineas"] == [{"id": 2, "antes": 1, "horas": 3}]


def test_f049_r6_sin_cambios_es_null():
    campos = [_campo(1, "n", "Ord.", 8),
              _campo(None, "e", "Extra (nueva)", 0, nueva=True)]
    assert _pura("cuerpoCelda", campos, ["8", "0"], CELDA) is None
    assert _pura("cuerpoCelda", campos, ["", ""], CELDA) is None


def test_f049_r7_solo_la_extra_nueva_tambien_es_cambio():
    campos = [_campo(1, "n", "Ord.", 8),
              _campo(None, "e", "Extra (nueva)", 0, nueva=True)]
    cuerpo = _pura("cuerpoCelda", campos, ["8", "-1"], CELDA)
    assert cuerpo["nueva_extra"] == -1 and cuerpo["nueva_ordinaria"] is None
    assert cuerpo["lineas"] == [{"id": 1, "antes": 8, "horas": 8}]


# ===================== textoOtras / avisoAfectadas ===================== #

AFECTADAS = [
    {"obra_key": "obr-686", "obra_codigo": "0686", "document_id": "d-x",
     "congelada": False},
    {"obra_key": "obr-690", "obra_codigo": "0690", "document_id": "d-w",
     "congelada": True},
    {"obra_key": "cod-SIN", "obra_codigo": None, "document_id": "d-s",
     "congelada": False},
]


def test_f049_r36_texto_de_otras_obras():
    assert _pura("textoOtras", AFECTADAS[:1]) == (
        "Este trabajador tiene horas ese día en otras obras (0686): al "
        "guardar se recalcula el reparto del día en todas.")
    assert _pura("textoOtras", AFECTADAS) == (
        "Este trabajador tiene horas ese día en otras obras (0686, 0690, "
        "cod-SIN): al guardar se recalcula el reparto del día en todas.")


def test_f049_r36_sin_otras_no_hay_texto():
    assert _pura("textoOtras", []) is None
    assert _pura("textoOtras", None) is None


def test_f049_r36_codigo_repetido_una_vez():
    dos = [AFECTADAS[0], dict(AFECTADAS[0], document_id="d-x2")]
    assert "(0686):" in _pura("textoOtras", dos)


def test_f049_r37_enlaces_por_obra():
    assert _pura("avisoAfectadas", AFECTADAS) == [
        {"href": "/obras/obr-686", "texto": "0686"},
        {"href": "/obras/obr-690", "texto": "0690" + SUFIJO_CONGELADA},
        {"href": "/obras/cod-SIN", "texto": "cod-SIN"}]


def test_f049_r37_href_escapado():
    assert _pura("avisoAfectadas", [{"obra_key": "nom-A B/C",
                                     "obra_codigo": "X",
                                     "congelada": False}]) == [
        {"href": "/obras/nom-A%20B%2FC", "texto": "X"}]


def test_f049_r37_sin_afectadas_lista_vacia():
    assert _pura("avisoAfectadas", None) == []


# ===================== popup con DOM falso (R1-R8, R32-R37) ============= #

DOM_JS = r"""
"use strict";
var eventos = [];
function El(tag) {
  this.tagName = tag; this.children = []; this.textContent = "";
  this.className = ""; this.title = ""; this.value = ""; this.href = "";
  this.type = ""; this.disabled = false; this.readOnly = false;
  this.hidden = false; this.style = {}; this.dataset = {}; this.on = {};
  this.padres = {};
}
El.prototype.appendChild = function (h) { this.children.push(h); return h; };
El.prototype.replaceChildren = function () { this.children = []; };
El.prototype.addEventListener = function (t, f) { this.on[t] = f; };
El.prototype.closest = function (sel) { return this.padres[sel] || null; };
El.prototype.focus = function () {}; El.prototype.select = function () {};
El.prototype.remove = function () { eventos.push("remove"); };
function todos(el, out) {
  out = out || [];
  out.push(el);
  el.children.forEach(function (h) { todos(h, out); });
  return out;
}
function vista(el) {
  return todos(el).map(function (n) {
    return [n.tagName, n.className, n.textContent, n.value, n.href,
            n.hidden, n.disabled];
  });
}
globalThis.document = {createElement: function (t) { return new El(t); }};
globalThis.window = {location: {reload: function () {
  eventos.push("reload"); }}, alert: function (m) {
  eventos.push("alert:" + m); }};
globalThis.alert = window.alert;
var peticiones = [], OTRAS = {ok: true, afectadas: []}, OTRAS_OK = true,
    GUARDAR = {status: 200, json: {ok: true, editadas: [1], creadas: [],
                                   recalculo: "pedido", afectadas: []}};
globalThis.fetch = function (url, opts) {
  peticiones.push([url, opts && opts.method || "GET",
                   opts && opts.body ? JSON.parse(opts.body) : null]);
  if (/celda\/otras/.test(url)) {
    if (!OTRAS_OK) return Promise.reject(new Error("red"));
    return Promise.resolve({ok: true, status: 200,
      json: function () { return Promise.resolve(OTRAS); }});
  }
  return Promise.resolve({ok: GUARDAR.status < 400, status: GUARDAR.status,
    json: function () { return Promise.resolve(GUARDAR.json); }});
};
function tic() { return new Promise(function (r) { setImmediate(r); }); }
async function drenar() { for (var i = 0; i < 10; i++) { await tic(); } }
function celda(regs, extra) {
  var td = new El("td"), tr = new El("tr"), tabla = new El("table");
  tabla.dataset.obraKey = "obr-678";
  tr.dataset.wk = (extra && extra.wk) || "rec-501";
  td.padres = {"tr": tr, "table": tabla};
  td.dataset.regs = JSON.stringify(regs);
  td.dataset.fecha = "2026-10-14";
  td.dataset.trabajador = "Persona";
  if (extra && extra.reparto) td.dataset.reparto = "pendiente";
  return td;
}
function boton(pop, texto) {
  return todos(pop).filter(function (n) {
    return n.tagName === "button" && n.textContent === texto; })[0] || null;
}
function inputs(pop) {
  return todos(pop).filter(function (n) { return n.tagName === "input"; });
}
var cerrados = 0;
function cerrar() { cerrados += 1; }
"""


def _popup(guion: str, **variables):
    js = _js()
    cabecera = "".join(f"var {k} = {json.dumps(v)};\n"
                       for k, v in variables.items())
    programa = (DOM_JS + _motivo_http(js)
                + "".join(_funcion(js, f) for f in PURAS + (
                    "abrirPopupCelda", "mostrarAfectadas"))
                + cabecera + "(async function () {\n" + guion
                + "\n})().catch(function (e) { console.error(e.stack);"
                  " process.exit(1); });")
    return _node(programa)


ABRIR = """
var pop = abrirPopupCelda(celda(REGS, EXTRA), cerrar);
await drenar();
"""
SALIDA = """
process.stdout.write(JSON.stringify({vista: vista(pop), eventos: eventos,
  peticiones: peticiones, cerrados: cerrados}));
"""


def _textos(res) -> list[str]:
    return [n[2] for n in res["vista"] if n[2]]


def _clase(res, clase: str) -> list[list]:
    return [n for n in res["vista"] if clase in (n[1] or "").split()]


def test_f049_r1_r2_r5_popup_solo_extra():
    res = _popup(ABRIR + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10}],
                 EXTRA={})
    textos = _textos(res)
    assert "Persona · 2026-10-14" in textos
    assert "Ord. (nueva)" in textos and "Extra" in textos
    assert [n[3] for n in res["vista"] if n[0] == "input"] == [0, 10]
    assert _clase(res, "mxe-nueva")
    assert [n[2] for n in _clase(res, "mxe-nota")] == [NOTA]
    assert "Guardar" in textos and "Cancelar" in textos
    assert res["peticiones"] == [[
        "/api/matriz/celda/otras?obra_key=obr-678&worker_key=rec-501"
        "&fecha=2026-10-14", "GET", None]]


def test_f049_r4_sin_lineas_no_hay_popup():
    res = _node(DOM_JS + _motivo_http(_js()) + "".join(
        _funcion(_js(), f) for f in PURAS + ("abrirPopupCelda",
                                            "mostrarAfectadas"))
        + "process.stdout.write(JSON.stringify(["
          "abrirPopupCelda(celda([]), cerrar), peticiones]));")
    assert res == [None, []]


def test_f049_r3_todas_congeladas_solo_lectura():
    res = _popup(ABRIR + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10, "c": 1}],
                 EXTRA={})
    textos = _textos(res)
    assert "Guardar" not in textos and "Cerrar" in textos
    assert "Extra 🔒" in textos and "Ord. (nueva)" not in textos
    assert [n[6] for n in res["vista"] if n[0] == "input"] == [True]


def test_f049_r35_sin_trabajador_sin_nuevas_en_el_popup():
    res = _popup(ABRIR + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10}],
                 EXTRA={"wk": "sin-trabajador"})
    assert "Ord. (nueva)" not in _textos(res)


def test_f049_r32_aviso_de_reparto_pendiente():
    res = _popup(ABRIR + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10}],
                 EXTRA={"reparto": True})
    assert AVISO_REPARTO in [n[2] for n in _clase(res, "mxe-aviso")]
    sin = _popup(ABRIR + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10}],
                 EXTRA={})
    assert AVISO_REPARTO not in _textos(sin)


def test_f049_r36_aviso_de_otras_obras_al_abrir():
    res = _popup("OTRAS = {ok: true, afectadas: AFECTADAS};" + ABRIR + SALIDA,
                 REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 AFECTADAS=AFECTADAS[:1])
    avisos = [(n[2], n[5]) for n in _clase(res, "mxe-aviso")]
    assert ("Este trabajador tiene horas ese día en otras obras (0686): al "
            "guardar se recalcula el reparto del día en todas.",
            False) in avisos


def test_f049_r36_sin_otras_o_si_falla_no_avisa():
    for guion in ("", "OTRAS_OK = false;"):
        res = _popup(guion + ABRIR + SALIDA,
                     REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={})
        assert all(n[5] or not n[2] for n in _clase(res, "mxe-aviso"))


GUARDAR_JS = """
var ins = inputs(pop);
VALORES.forEach(function (v, i) { ins[i].value = v; });
boton(pop, "Guardar").on.click();
await drenar();
"""


def test_f049_r6_guardar_sin_cambios_cierra_sin_peticion():
    res = _popup(ABRIR + GUARDAR_JS + SALIDA,
                 REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["0", "10"])
    assert [p for p in res["peticiones"] if p[1] == "POST"] == []
    assert res["cerrados"] == 1 and "reload" not in res["eventos"]


def test_f049_r7_r8_guardar_una_post_y_recarga():
    res = _popup(ABRIR + GUARDAR_JS + SALIDA,
                 REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["8", "2"])
    posts = [p for p in res["peticiones"] if p[1] == "POST"]
    assert posts == [["/api/matriz/celda", "POST", {
        "obra_key": "obr-678", "worker_key": "rec-501",
        "fecha": "2026-10-14", "lineas": [{"id": 5, "antes": 10, "horas": 2}],
        "nueva_ordinaria": 8, "nueva_extra": None}]]
    assert res["eventos"] == ["reload"]


def test_f049_r8_recalculo_fallido_avisa_antes_de_recargar():
    res = _popup("GUARDAR.json.recalculo = 'fallo';" + ABRIR + GUARDAR_JS
                 + SALIDA, REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["8", "2"])
    assert res["eventos"] == ["alert:" + AVISO_FALLO, "reload"]


def test_f049_r8_error_muestra_el_motivo_y_sigue_abierto():
    res = _popup("GUARDAR = {status: 409, json: {ok: false, error: MOTIVO}};"
                 + ABRIR + GUARDAR_JS + SALIDA,
                 REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["8", "2"], MOTIVO=RECARGA)
    assert "✗ " + RECARGA in _textos(res)
    assert res["eventos"] == [] and res["cerrados"] == 0
    assert [n[6] for n in res["vista"]
            if n[0] == "button" and n[2] == "Guardar"] == [False]


def test_f049_r37_con_afectadas_lista_y_recarga_al_cerrar():
    guion = ("GUARDAR.json.afectadas = AFECTADAS;" + ABRIR + GUARDAR_JS
             + "var antes = eventos.slice();"
             + "var vistaLista = vista(pop);"
             + "boton(pop, 'Cerrar').on.click(); await drenar();"
             + "process.stdout.write(JSON.stringify({antes: antes,"
               " vista: vistaLista, eventos: eventos}));")
    res = _popup(guion, REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["8", "2"], AFECTADAS=AFECTADAS[:2])
    assert res["antes"] == []                          # sin recargar aún
    textos = [n[2] for n in res["vista"] if n[2]]
    assert TITULO_AFECTADAS in textos
    enlaces = [(n[4], n[2]) for n in res["vista"] if n[0] == "a"]
    assert enlaces == [("/obras/obr-686", "0686"),
                       ("/obras/obr-690", "0690" + SUFIJO_CONGELADA)]
    assert "Guardar" not in textos and NOTA not in textos
    assert res["eventos"] == ["reload"]


def test_f049_r37_con_afectadas_y_fallo_lo_dice_en_la_lista():
    guion = ("GUARDAR.json.afectadas = AFECTADAS;"
             "GUARDAR.json.recalculo = 'fallo';" + ABRIR + GUARDAR_JS
             + SALIDA)
    res = _popup(guion, REGS=[{"id": 5, "t": "e", "h": 10}], EXTRA={},
                 VALORES=["8", "2"], AFECTADAS=AFECTADAS[:1])
    assert AVISO_FALLO in _textos(res)
    assert res["eventos"] == []


# ============================== leyenda y node ========================== #

def test_f049_r8_no_usa_promise_all_en_el_editor():
    js = _js()
    inicio = js.index("Matriz de obra:")
    fin = js.index("})();", inicio)
    bloque = js[inicio:fin]
    assert "Promise.all" not in bloque
    assert "/api/registros/" not in bloque
    assert "/api/matriz/celda" in bloque


def test_f049_r11_app_js_es_sintacticamente_valido():
    if NODE is None:
        pytest.skip("node no esta instalado")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
