# tests/test_f031_preflight_avisos.py
"""F-031 · R28-R30: el modal del preflight pinta el complementario y la nota
de la cuenta de la partida.

sv5 decide (parte complementario, cuenta por partida) y sv4 solo reenvia y
pinta: el resumen rotula «complementario» y muestra el `aviso` del parte
(escapado, R28); un bloque aparte lista las lineas `escribir` con
`caa_nota` (R29); sin esos campos (sv5 anterior a F-031) el modal sale
exactamente como antes (R30).

El proyecto no tiene arnes de tests JS: el reenvio se prueba por HTTP y el
pintado EJECUTANDO las funciones de `app.js` con `node` (si no esta
instalado, se salta; la verificacion en el navegador es MANUAL, M3).
Datos SINTETICOS.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias
from tests.test_f003_r2_vistas_festivos import ProveedorFake

APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
LUNES = "2026-05-18"

AVISO = ("el parte PT26/00004 (Imputado) de 05/2026 esta cerrado: las "
         "lineas van al parte complementario PT26/00350 (se creara)")
NOTA = ("el recurso no tiene cuenta para esa hora: se usa la de la partida "
        "01.02 (.CIMO12)")

PARTES = [
    {"ano": 2026, "mes": 5, "existe": False, "ide": None,
     "cod": "PT26/00350", "creado": False, "estado": None,
     "complementario": True, "cerrados": ["PT26/00004"],
     "del_periodo": [{"ide": 800, "cod": "PT26/00004", "est": 10}],
     "aviso": AVISO},
]
ACCIONES = [
    {"registro_id": 1, "accion": "escribir", "nombre": "Persona Uno",
     "fecha_int": 20260518, "caa_ide": 702, "caa_cod": "0100.CIMO12",
     "caa_motivo": None, "caa_aviso": None, "caa_origen": "partida",
     "caa_nota": NOTA},
    {"registro_id": 2, "accion": "escribir", "nombre": "Persona Dos",
     "fecha_int": 20260519, "caa_ide": 701, "caa_cod": "0100.CIMO09",
     "caa_motivo": None, "caa_aviso": None, "caa_origen": "recurso",
     "caa_nota": None},
    {"registro_id": 3, "accion": "omitir", "nombre": "Persona Tres",
     "fecha_int": 20260520, "motivo": "parte_cerrado: ya hay horas",
     "caa_ide": 0, "caa_cod": None, "caa_motivo": None, "caa_aviso": None,
     "caa_origen": None, "caa_nota": "no deberia pintarse"},
]


# ============================ reenvio (HTTP) ============================ #

class TransferClientFake:
    def preflight(self, payload: dict) -> dict:
        return {"ok": True, "conflictos": [],
                "partes": json.loads(json.dumps(PARTES)),
                "acciones": json.loads(json.dumps(ACCIONES)),
                "resumen": {"escribir": 2, "omitir": 1}}


@pytest.fixture
def cliente(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_dias(fabrica, [{"fecha": LUNES, "horas": 8.0}])
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=TransferClientFake(),
                    calendario_provider=ProveedorFake(por_dni={},
                                                      por_defecto=set()))
    return TestClient(app), ids


def test_f031_r28_r29_el_preflight_reenvia_partes_y_acciones(cliente) -> None:
    http, ids = cliente
    cuerpo = http.post("/api/aprobar/preflight",
                       json={"registro_ids": ids}).json()
    assert cuerpo["partes"] == PARTES
    assert cuerpo["acciones"] == ACCIONES


# ============================ texto de app.js ============================ #

def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def test_f031_r29_resumen_html_llama_a_notas_cuenta() -> None:
    cuerpo = _funcion(_js(), "resumenHtml")
    assert "notasCuentaHtml(pf.acciones)" in cuerpo
    assert "avisosCuentaHtml(pf.acciones)" in cuerpo       # F-021 intacto


# ====================== comportamiento (node) ====================== #

NODE = shutil.which("node")
FUNCIONES = ("esc", "fechaLegible", "avisosCuentaHtml", "notasCuentaHtml",
             "resumenHtml")


def _ejecutar(llamada: str, argumento) -> str:
    js = _js()
    fuente = "".join(_funcion(js, n) for n in FUNCIONES
                     if re.search(r"\n  function " + n + r"\(", js))
    programa = (fuente + "\nprocess.stdout.write(" + llamada + "("
                + json.dumps(argumento) + "));\n")
    salida = subprocess.run([NODE, "-e", programa], capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return salida.stdout


def _pf(**kw) -> dict:
    pf = {"partes": PARTES, "acciones": ACCIONES,
          "resumen": {"escribir": 2, "omitir": 1}}
    pf.update(kw)
    return pf


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f031_r28_rotula_complementario_y_pinta_el_aviso() -> None:
    html = _ejecutar("resumenHtml", _pf())
    (li,) = re.findall(r"<li>Parte .*?</li>", html)
    assert "<strong>PT26/00350</strong>" in li
    assert "complementario</span>" in li
    assert AVISO in li
    assert "<em>se creara</em>" in li


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f031_r28_complementario_existente() -> None:
    parte = dict(PARTES[0], existe=True, ide=912, estado=1,
                 aviso=AVISO.replace("se creara", "ya existe, en registro"))
    html = _ejecutar("resumenHtml", _pf(partes=[parte]))
    assert "complementario</span>" in html and ": ya existe" in html
    assert "(ya existe, en registro)" in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f031_r28_escapa_el_aviso() -> None:
    parte = dict(PARTES[0], aviso="a & <i>b</i>")
    html = _ejecutar("resumenHtml", _pf(partes=[parte]))
    assert "a &amp; &lt;i&gt;b&lt;/i&gt;" in html
    assert "<i>b</i>" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f031_r29_notas_una_fila_por_linea_escribir_con_nota() -> None:
    html = _ejecutar("notasCuentaHtml", ACCIONES)
    assert "ap-ctx" in html and "<strong>1</strong>" in html
    assert html.count("<li>") == 1
    assert f"<li>Persona Uno · 18/05/2026 — {NOTA}</li>" in html
    assert "Persona Dos" not in html and "Persona Tres" not in html
    assert "ap-cuenta-avisos" not in html          # bloque aparte de F-021
    resumen = _ejecutar("resumenHtml", _pf())
    assert html in resumen


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f031_r29_notas_escapa_y_cuenta_todas() -> None:
    acciones = [dict(ACCIONES[0], nombre="<b>X</b>", caa_nota="n & <i>m</i>"),
                dict(ACCIONES[0], registro_id=9)]
    html = _ejecutar("notasCuentaHtml", acciones)
    assert "<strong>2</strong>" in html and html.count("<li>") == 2
    assert "&lt;b&gt;X&lt;/b&gt;" in html and "n &amp; &lt;i&gt;m&lt;/i&gt;" \
        in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
@pytest.mark.parametrize("acciones", [
    [], None, [dict(ACCIONES[1])], [dict(ACCIONES[2])],
    [{"accion": "escribir", "nombre": "P", "fecha_int": 20260518}],
])
def test_f031_r30_sin_notas_no_pinta_el_bloque(acciones) -> None:
    assert _ejecutar("notasCuentaHtml", acciones) == ""


#: Lo que pintaba `resumenHtml` ANTES de F-031 para `PF_VIEJO` (sv5 sin los
#: campos nuevos). Capturado del `app.js` de `dev` (commit 9a00ce3).
PF_VIEJO = {
    "partes": [
        {"ano": 2026, "mes": 5, "existe": True, "ide": 900,
         "cod": "PT26/00005", "creado": False},
        {"ano": 2026, "mes": 6, "existe": False, "ide": None,
         "cod": "PT26/00006", "creado": False},
    ],
    "acciones": [{"registro_id": 1, "accion": "escribir", "nombre": "P",
                  "fecha_int": 20260518, "caa_ide": 701}],
    "resumen": {"escribir": 1},
}
HTML_VIEJO = (
    "<ul class='ap-list'><li>Parte <strong>PT26/00005</strong> (05/2026): "
    "ya existe</li><li>Parte <strong>PT26/00006</strong> (06/2026): "
    "<em>se creara</em></li></ul><p>Se registraran <strong>1</strong> "
    "linea(s).</p>")


@pytest.mark.skipif(NODE is None, reason="node no instalado")
@pytest.mark.parametrize("extra", [
    {},                                                    # sv5 anterior
    {"complementario": False, "aviso": None, "cerrados": [],
     "estado": 1, "del_periodo": []},                      # F-031 sin nada
])
def test_f031_r30_sin_campos_el_modal_es_el_de_siempre(extra) -> None:
    pf = json.loads(json.dumps(PF_VIEJO))
    for p in pf["partes"]:
        p.update(extra)
    pf["acciones"][0].update({"caa_origen": "recurso", "caa_nota": None}
                             if extra else {})
    assert _ejecutar("resumenHtml", pf) == HTML_VIEJO
