# tests/test_f034_resultado_omitidas.py
"""F-034 · R19-R20: lo que ve el usuario cuando una linea no entra en
Sigrid porque su parte ya no estaba abierto.

sv5 decide y manda el motivo (`parte_no_abierto: ...`); sv4 solo lo pinta:

  - R19: el modal de resultado (`resultadoHtml` de `app.js`) agrupa las
    omitidas por motivo (texto antes de los primeros dos puntos, o el
    motivo entero) con su numero, escapado, en vez de «(reglas)». El texto
    completo sigue en el `title` del badge `omitido` del detalle de obra.
  - R20: la linea queda `omitido` con el motivo de sv5 y se puede
    reaprobar (`ESTADOS_REAPROBACION`), sin cambios en el repositorio.

El pintado se prueba EJECUTANDO las funciones de `app.js` con `node` (si
no esta instalado, se salta; la verificacion en el navegador es MANUAL,
M4). Datos SINTETICOS.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from application.services.reparto_obras import ESTADOS_REAPROBACION
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_dias

RAIZ = Path(__file__).resolve().parents[1]
APP_JS = RAIZ / "static" / "app.js"
OBRA_HTML = RAIZ / "templates" / "obra_detail.html"
NODE = shutil.which("node")
FUNCIONES = ("num", "esc", "resultadoHtml")

MOTIVO_314 = ("parte_no_abierto: el parte PT26/00314 ya no esta En registro "
              "(Cerrado); no se registra. Reaprueba para llevarla al parte "
              "En registro del mes")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _resultado(r: dict) -> str:
    js = APP_JS.read_text(encoding="utf-8")
    fuente = "".join(_funcion(js, n) for n in FUNCIONES)
    programa = (fuente + "\nprocess.stdout.write(resultadoHtml("
                + json.dumps(r) + "));\n")
    salida = subprocess.run([NODE, "-e", programa], capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return salida.stdout


def _om(rid: int, motivo) -> dict:
    return {"registro_id": rid, "motivo": motivo}


def _bloque(html: str) -> str:
    m = re.search(r"<p>\d+ linea\(s\) no registradas:</p>"
                  r"<ul class='ap-list'>.*?</ul>", html, re.DOTALL)
    assert m, html
    return m.group(0)


# ------------------------------- R19 · modal ------------------------------- #

@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_agrupa_las_omitidas_por_motivo() -> None:
    html = _resultado({"escritas": [], "omitidas": [
        _om(1, MOTIVO_314), _om(2, "regla_x: sin tipo de hora"),
        _om(3, MOTIVO_314), _om(4, MOTIVO_314)]})
    assert _bloque(html) == (
        "<p>4 linea(s) no registradas:</p><ul class='ap-list'>"
        "<li>parte_no_abierto · 3</li><li>regla_x · 1</li></ul>")
    assert "(reglas)" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_orden_de_aparicion() -> None:
    html = _resultado({"omitidas": [
        _om(1, "zeta: x"), _om(2, "alfa: y"), _om(3, "zeta: z")]})
    assert _bloque(html).endswith(
        "<li>zeta · 2</li><li>alfa · 1</li></ul>")


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_motivo_sin_dos_puntos_va_entero() -> None:
    html = _resultado({"omitidas": [
        _om(1, "ya registrada en Sigrid"), _om(2, "ya registrada en Sigrid")]})
    assert "<li>ya registrada en Sigrid · 2</li>" in _bloque(html)


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_corta_en_los_primeros_dos_puntos() -> None:
    html = _resultado({"omitidas": [_om(1, "a: b: c")]})
    assert "<li>a · 1</li>" in _bloque(html)


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_motivo_nulo_no_rompe() -> None:
    html = _resultado({"omitidas": [_om(1, None), {"registro_id": 2}]})
    assert _bloque(html) == (
        "<p>2 linea(s) no registradas:</p><ul class='ap-list'>"
        "<li> · 2</li></ul>")


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_escapa_el_motivo() -> None:
    html = _resultado({"omitidas": [_om(1, "<b>x</b> & y: z")]})
    assert "<li>&lt;b&gt;x&lt;/b&gt; &amp; y · 1</li>" in html
    assert "<b>x</b>" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f034_r19_no_pinta_nombres_ni_ids() -> None:
    html = _resultado({"omitidas": [
        {"registro_id": 987654, "motivo": MOTIVO_314,
         "nombre": "Persona Sintetica"}]})
    assert "987654" not in html and "Persona" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
@pytest.mark.parametrize("omitidas", [None, []])
def test_f034_r19_sin_omitidas_el_modal_no_cambia(omitidas) -> None:
    r = {"escritas": [{"parte_cod": "PT26/00314", "hora_codigo": "HL01",
                       "can": 8, "hmores_ide": 5001}],
         "ya_registradas": [7], "borradas": 1}
    if omitidas is not None:
        r["omitidas"] = omitidas
    assert _resultado(r) == (
        "<p><strong>1</strong> linea(s) registradas en Sigrid.</p>"
        "<p>1 linea(s) anteriores borradas (pisadas).</p>"
        "<p>1 linea(s) ya estaban registradas (no se duplican).</p>"
        "<ul class='ap-list'><li>PT26/00314 · HL01 · 8 h → linea 5001</li>"
        "</ul>")


def test_f034_r19_el_badge_omitido_conserva_el_motivo_completo() -> None:
    """DA7: el texto entero del motivo sigue en el `title` del badge."""
    html = OBRA_HTML.read_text(encoding="utf-8")
    assert ("<span class=\"badge warn\" title=\"{{ r.sigrid_motivo or "
            "'No se registra' }}\">omitido</span>") in html


# --------------------------- R20 · repositorio --------------------------- #

def test_f034_r20_no_escrita_queda_omitido_y_es_reaprobable() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar_dias(fabrica, [{"fecha": "2026-10-14", "horas": 8.0}],
                          empleado_nombre="Persona Sintetica",
                          empleado_dni="00000000T")
    repo = ParteReviewRepository(fabrica)
    n = repo.marcar_registros_sigrid(
        escritas=[], omitidas=[_om(rid, MOTIVO_314)], ya_registradas=[],
        usuario="admin@test")
    assert n == 1
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        assert (reg.sigrid_estado, reg.sigrid_motivo) == ("omitido",
                                                          MOTIVO_314)
    assert "omitido" in ESTADOS_REAPROBACION
