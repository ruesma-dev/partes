# tests/test_f068_conciliar_js.py
"""F-068 · el portal dice si casar o reasignar pidió el recálculo (R14-R18).

Se EJECUTAN en node las funciones reales de `static/app.js`
(`textoRecalculoCasado`, `_confirmarCasado` y, desde T10, `_empReasignar`), extraídas
con la misma expresión que F-042 y F-049, con un DOM, un `fetch`, un
`alert` y un `location.reload` falsos. Sin navegador ni red. Datos
sintéticos.
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

TEXTO_FALLO = ("Casado guardado, pero no se pudo pedir el recálculo de "
               "extras: se hará en la siguiente pasada. No apruebes esos "
               "partes hasta ver sus extras.")
SIN_COLA = "(sin recálculo automático)"


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _pura(*args):
    programa = (_funcion(_js(), "textoRecalculoCasado")
                + "process.stdout.write(JSON.stringify("
                  "textoRecalculoCasado(...%s) ?? null));" % json.dumps(
                      list(args)))
    return _node(programa)


# ===================== textoRecalculoCasado (pura) ===================== #

@pytest.mark.parametrize("partes", [1, 3])
def test_f068_r14_pedido_dice_cuantos_partes(partes) -> None:
    assert _pura("pedido", partes) == [
        f"· recalculando extras de {partes} parte(s) (1–2 min)",
        "recon-recalculo"]


def test_f068_r15_fallo_avisa_en_estilo_de_error() -> None:
    assert _pura("fallo", 2) == [TEXTO_FALLO, "recon-status error"]


def test_f068_r16_sin_cola() -> None:
    assert _pura("sin_cola", 1) == [SIN_COLA, "recon-recalculo"]


@pytest.mark.parametrize("recalculo", [None, "otro"])
def test_f068_r16_null_o_desconocido_no_dice_nada(recalculo) -> None:
    assert _pura(recalculo, 0) is None


# ================== _confirmarCasado (la tarjeta casada) =============== #

_CASAR = r"""
var card = {innerHTML: "", classList: {add: function () {}}};
var statusEl = {textContent: "", className: ""};
var alertas = [];
function alert(t) { alertas.push(t); }
function fetch() {
  return Promise.resolve({ok: true, json: function () {
    return Promise.resolve(RESPUESTA); }});
}
_confirmarCasado("Juan Leido", 501, card, statusEl).then(function () {
  process.stdout.write(JSON.stringify(
    {html: card.innerHTML, alertas: alertas, status: statusEl.textContent}));
});
"""

BASE = {"ok": True, "updated": 2, "alias_ok": True, "congeladas": 0,
        "empleado": {"ide": 4242, "codigo": "E42", "nombre": "Ana Casada"}}


def _casar(**extra) -> dict:
    js = _js()
    programa = ("".join(_funcion(js, f) for f in (
        "textoRecalculoCasado", "_confirmarCasado", "_esc"))
        + "var RESPUESTA = %s;" % json.dumps(dict(BASE, **extra)) + _CASAR)
    return _node(programa)


def _html_de_hoy() -> str:
    return _casar()["html"]


def test_f068_r14_la_tarjeta_dice_recalculando() -> None:
    html = _casar(recalculo="pedido", partes_recalculo=2)["html"]
    assert "2 registro(s) actualizados" in html
    assert ('<span class="recon-recalculo">· recalculando extras de 2 '
            'parte(s) (1–2 min)</span>') in html


def test_f068_r15_la_tarjeta_avisa_del_fallo_y_se_queda() -> None:
    res = _casar(recalculo="fallo", partes_recalculo=1)
    assert (f'<div class="recon-status error">{TEXTO_FALLO}</div>'
            in res["html"])
    assert "✓ Casado con" in res["html"]


def test_f068_r16_sin_cola_lo_dice() -> None:
    html = _casar(recalculo="sin_cola", partes_recalculo=1)["html"]
    assert f'<span class="recon-recalculo">{SIN_COLA}</span>' in html


def test_f068_r16_null_o_sv4_anterior_es_lo_de_hoy() -> None:
    hoy = _html_de_hoy()
    assert "recalcul" not in hoy
    assert _casar(recalculo=None, partes_recalculo=0)["html"] == hoy



# ===================== _empReasignar (R18, D3-b) ======================= #

_REASIGNAR = r"""
var eventos = [];
var PartidaSel = undefined;
var input = {disabled: false, value: "", placeholder: "",
             classList: {add: function () {}, remove: function () {}}};
var wrap = {
  getAttribute: function (k) { return k === "data-worker-key" ? "rec-1" : null; },
  querySelector: function () { return input; }
};
var window = {location: {reload: function () { eventos.push(["reload"]); }}};
function alert(t) { eventos.push(["alert", t]); }
function setTimeout() {}
function fetch() {
  return Promise.resolve({ok: true, json: function () {
    return Promise.resolve(RESPUESTA); }});
}
_empReasignar(wrap, 501, "E42 · Ana Casada");
Promise.resolve().then(function () {}).then(function () {}).then(function () {})
  .then(function () {}).then(function () {
  process.stdout.write(JSON.stringify(eventos));
});
"""


def _reasignar(**extra) -> list:
    js = _js()
    programa = ("".join(_funcion(js, f) for f in (
        "textoRecalculoCasado", "_empReasignar", "flashEl"))
        + "var RESPUESTA = %s;" % json.dumps(dict(BASE, **extra))
        + _REASIGNAR)
    return _node(programa)


def test_f068_r18_reasignar_con_fallo_avisa_antes_de_recargar() -> None:
    assert _reasignar(recalculo="fallo", partes_recalculo=1) == [
        ["alert", TEXTO_FALLO], ["reload"]]


@pytest.mark.parametrize("recalculo", ["pedido", "sin_cola", None])
def test_f068_r18_reasignar_sin_fallo_recarga_como_hoy(recalculo) -> None:
    assert _reasignar(recalculo=recalculo, partes_recalculo=1) == [
        ["reload"]]


def test_f068_r18_reasignar_sv4_anterior_recarga_como_hoy() -> None:
    assert _reasignar() == [["reload"]]
