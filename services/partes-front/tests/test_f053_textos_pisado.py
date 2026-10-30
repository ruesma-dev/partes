# tests/test_f053_textos_pisado.py
"""F-053 · Textos del portal: pisar pone a 0 en Sigrid, no borra (R19-R22).

  - `conflictosHtml` (R19): la linea actual «se pone a 0 en Sigrid (no se
    borra)» y se escribe la nueva; cada pisada «linea N · codigo · X h ·
    Y € → 0 h» con «nueva: …» al lado; ningun texto afirma que se borra.
  - `resultadoHtml` (R20): «N linea(s) anteriores puestas a 0 en Sigrid
    (pisadas).» con `anuladas`, escapado; `borradas` ya no se pinta.
  - `reparto_obras.agregar_ejecucion` (R20): suma `anuladas`.
  - `MOTIVO_LINEA_REGISTRADA` (R21, DA8): no aconseja borrar en Sigrid.
  - Comentarios de sv4 (R22): «pisar pone a 0».

El pintado se prueba EJECUTANDO las funciones de `app.js` con `node`
(patron de `test_f031_preflight_avisos.py`; sin node, se salta). Datos
SINTETICOS.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from application.services.congelacion import MOTIVO_LINEA_REGISTRADA
from application.services.reparto_obras import agregar_ejecucion

RAIZ = Path(__file__).resolve().parents[1]
APP_JS = RAIZ / "static" / "app.js"
NODE = shutil.which("node")
FUNCIONES = ("fechaLegible", "num", "esc", "claveConGrupo", "conflictosHtml",
             "resultadoHtml")


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _ejecutar(llamada: str, *argumentos) -> str:
    js = _js()
    fuente = ('var SEPARADOR_CLAVE = "::";\n'
              + "".join(_funcion(js, n) for n in FUNCIONES))
    args = ", ".join(json.dumps(a) for a in argumentos)
    programa = (fuente + "\nprocess.stdout.write(" + llamada + "(" + args
                + "));\n")
    salida = subprocess.run([NODE, "-e", programa], capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return salida.stdout


CONFLICTO = {
    "clave": "501|20261015|1", "recurso_ide": 501, "nombre": "Persona Uno",
    "fecha_int": 20261015, "parte_cod": "PT26/00314", "hora_codigo": "HL01",
    "lineas": [{"ide": 9001, "hora_codigo": "HL01", "can": 8, "tot": 120,
                "nuestra": False}],
    "contexto": [{"ide": 9003, "hora_codigo": "HE01", "can": 2, "tot": 50}],
    "nuevas": [{"registro_id": 501, "can": 8, "tot": 120}],
    "nueva_can": 8, "nueva_tot": 120,
}


def _afirma_borrar(texto: str) -> list[str]:
    """Frases que AFIRMAN que se borra («no se borra» no cuenta)."""
    return re.findall(r"(?<!no )se borra|borrad[ao]s?\b|borra la", texto,
                      flags=re.IGNORECASE)


# =========================== R19 · modal =========================== #

@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r19_modal_dice_que_se_pone_a_cero() -> None:
    html = _ejecutar("conflictosHtml", [CONFLICTO], "")
    assert ("Marca las que quieras <strong>pisar</strong>: la linea actual "
            "<strong>se pone a 0 en Sigrid</strong> (no se borra) y se "
            "escribe la nueva. Las lineas con OTRO codigo de ese dia no se "
            "tocan.") in html
    assert _afirma_borrar(html) == []


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r19_cada_pisada_va_a_cero_con_la_nueva_al_lado() -> None:
    html = _ejecutar("conflictosHtml", [CONFLICTO], "")
    assert ("<span class='ap-old'>linea 9001 · HL01 · 8 h · 120 € → 0 h"
            "</span> <span class='ap-new'>nueva: 8 h · 120 €</span>") in html
    assert "actualizacion a" not in html
    # El contexto (otro codigo) sigue igual: informativo y sin flecha.
    assert "<li>linea 9003 · HE01 · 2 h · 50 €</li>" in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r19_pisada_escrita_por_la_app_y_varias_nuevas() -> None:
    c = dict(CONFLICTO, lineas=[dict(CONFLICTO["lineas"][0], nuestra=True)],
             nuevas=[{"can": 4, "partida_cod": "01.02"}, {"can": 4}])
    html = _ejecutar("conflictosHtml", [c], "obr-10")
    assert "→ 0 h <em>(escrita por esta app)</em></span>" in html
    assert "<span class='ap-mini'>(4 h 01.02 + 4 h)</span>" in html
    assert 'value="obr-10::501|20261015|1"' in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r19_la_pisada_se_escapa() -> None:
    c = dict(CONFLICTO, lineas=[{"ide": "<b>1</b>", "hora_codigo": "<i>H</i>",
                                 "can": 1, "tot": 2}])
    html = _ejecutar("conflictosHtml", [c], "")
    assert "linea &lt;b&gt;1&lt;/b&gt; · &lt;i&gt;H&lt;/i&gt; · 1 h" in html
    assert "<b>1</b>" not in html and "<i>H</i>" not in html


def test_f053_r19_fuente_conflictos_sin_se_borra() -> None:
    cuerpo = _funcion(_js(), "conflictosHtml")
    assert _afirma_borrar(cuerpo) == []
    assert "(no se borra)" in cuerpo and "€ → 0 h" in cuerpo


# ========================= R20 · resultado ========================= #

@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r20_resultado_cuenta_anuladas() -> None:
    html = _ejecutar("resultadoHtml", {"escritas": [], "anuladas": 2})
    assert ("<p>2 linea(s) anteriores puestas a 0 en Sigrid (pisadas).</p>"
            in html)
    assert _afirma_borrar(html) == []


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r20_resultado_sin_anuladas_no_dice_nada() -> None:
    for r in ({"escritas": []}, {"escritas": [], "anuladas": 0},
              {"escritas": [], "borradas": 3}):
        html = _ejecutar("resultadoHtml", r)
        assert "puestas a 0" not in html and "borradas" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f053_r20_resultado_escapa_anuladas() -> None:
    html = _ejecutar("resultadoHtml", {"anuladas": "<b>1</b>"})
    assert "&lt;b&gt;1&lt;/b&gt; linea(s) anteriores puestas a 0" in html


def test_f053_r20_fuente_resultado_sin_borradas() -> None:
    cuerpo = _funcion(_js(), "resultadoHtml")
    assert "r.borradas" not in cuerpo and "r.anuladas" in cuerpo


def test_f053_r20_reparto_suma_anuladas() -> None:
    a = {"clave": "obr-10", "ok": True, "escritas": [], "anuladas": 1}
    b = {"clave": "obr-20", "ok": True, "escritas": [], "anuladas": 2}
    c = {"clave": "obr-30", "ok": False, "error": "x", "anuladas": None}
    plano = agregar_ejecucion([a, b, c])
    assert plano["anuladas"] == 3 and "borradas" not in plano


# ======================= R21 · candado (DA8) ======================= #

def test_f053_r21_motivo_linea_registrada_texto_de_da8() -> None:
    assert MOTIVO_LINEA_REGISTRADA == (
        "Linea ya registrada en Sigrid: editarla aqui no la cambiaria alli "
        "(el synckey evita que se reescriba). En Sigrid no se borran "
        "lineas: para corregirla, que Administracion la edite alli (si "
        "sobra, a 0 horas); «Comprobar en Sigrid» enseña la diferencia.")
    assert "borra la linea en Sigrid" not in MOTIVO_LINEA_REGISTRADA


# ===================== R22 · comentarios de sv4 ===================== #

@pytest.mark.parametrize("ruta", [
    "infrastructure/transfer/transfer_queue_publisher.py",
    "interface_adapters/web/app.py"])
def test_f053_r22_fuente_pisar_pone_a_cero(ruta) -> None:
    fuente = (RAIZ / ruta).read_text(encoding="utf-8")
    assert "pisar borra" not in fuente
    assert "pisar pone a 0 lineas de Sigrid" in " ".join(fuente.split())
