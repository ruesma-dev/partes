# tests/test_f021_preflight_cuenta.py
"""F-021 · R19-R21: el aviso de cuenta analitica en el modal del preflight.

sv5 calcula, por accion, `caa_ide`, `caa_cod`, `caa_motivo` y `caa_aviso`
(este solo cuando la obra no tiene la cuenta del recurso o tiene varias).
sv4 no resuelve ni guarda cuentas: reenvia esos campos tal cual (R21) y el
modal pinta un bloque informativo con las lineas `escribir` que traen
aviso (R19), o nada si no hay ninguna o sv5 es anterior a F-021 (R20).

El proyecto no tiene arnes de tests JS: los dos primeros bloques miran el
texto de `app.js` y el tercero EJECUTA la funcion con `node` (si no esta
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

ACCIONES = [
    {"registro_id": 1, "accion": "escribir", "nombre": "Persona Uno",
     "fecha_int": 20260518, "caa_ide": 701, "caa_cod": "0100.LAB",
     "caa_motivo": None, "caa_aviso": None},
    {"registro_id": 2, "accion": "escribir", "nombre": "Persona Dos",
     "fecha_int": 20260519, "caa_ide": 0, "caa_cod": None,
     "caa_motivo": "obra_sin_cuenta",
     "caa_aviso": "la obra 0100 no tiene la cuenta analitica .EXT: la "
                  "linea ira sin cuenta"},
    {"registro_id": 3, "accion": "omitir", "nombre": "Persona Tres",
     "fecha_int": 20260520, "caa_ide": 0, "caa_cod": None,
     "caa_motivo": None, "caa_aviso": "no deberia pintarse"},
]


# ============================ R21 · reenvio ============================ #

class TransferClientFake:
    def __init__(self, acciones) -> None:
        self.acciones = acciones

    def preflight(self, payload: dict) -> dict:
        return {"ok": True, "conflictos": [], "partes": [],
                "acciones": json.loads(json.dumps(self.acciones)),
                "resumen": {"escribir": 2}}


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
                    transfer_client=TransferClientFake(ACCIONES),
                    calendario_provider=ProveedorFake(por_dni={},
                                                      por_defecto=set()))
    return TestClient(app), ids


def test_f021_r21_el_preflight_reenvia_los_caa_de_sv5(cliente) -> None:
    http, ids = cliente
    cuerpo = http.post("/api/aprobar/preflight",
                       json={"registro_ids": ids}).json()
    assert cuerpo["acciones"] == ACCIONES


# ===================== R19-R20 · texto de app.js ===================== #

def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def test_f021_r19_app_js_define_avisos_cuenta_y_filtra_escribir() -> None:
    cuerpo = _funcion(_js(), "avisosCuentaHtml")
    assert 'a.accion === "escribir"' in cuerpo
    assert "a.caa_aviso" in cuerpo


def test_f021_r19_resumen_html_llama_a_avisos_cuenta() -> None:
    assert "avisosCuentaHtml(pf.acciones)" in _funcion(_js(), "resumenHtml")


# =================== R19-R20 · comportamiento (node) =================== #

NODE = shutil.which("node")


def _pintar(acciones) -> str:
    js = _js()
    fuente = "".join(_funcion(js, n) for n in
                     ("esc", "fechaLegible", "avisosCuentaHtml"))
    programa = (fuente + "\nprocess.stdout.write(avisosCuentaHtml("
                + json.dumps(acciones) + "));\n")
    salida = subprocess.run([NODE, "-e", programa], capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return salida.stdout


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f021_r19_pinta_una_fila_por_linea_escribir_con_aviso() -> None:
    html = _pintar(ACCIONES)
    assert "ap-ctx" in html
    assert "<strong>1</strong>" in html
    assert html.count("<li>") == 1
    assert ("<li>Persona Dos · 19/05/2026 — la obra 0100 no tiene la "
            "cuenta analitica .EXT: la linea ira sin cuenta</li>") in html
    assert "Persona Uno" not in html and "Persona Tres" not in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f021_r19_cuenta_todas_las_lineas_con_aviso() -> None:
    dos = [dict(ACCIONES[1], registro_id=8, nombre="Persona Ocho")] \
        + ACCIONES
    html = _pintar(dos)
    assert "<strong>2</strong>" in html and html.count("<li>") == 2


@pytest.mark.skipif(NODE is None, reason="node no instalado")
def test_f021_r19_escapa_el_texto_que_llega_del_servidor() -> None:
    raro = [dict(ACCIONES[1], nombre="<b>X</b>", caa_aviso="a & <i>b</i>")]
    html = _pintar(raro)
    assert "&lt;b&gt;X&lt;/b&gt;" in html
    assert "a &amp; &lt;i&gt;b&lt;/i&gt;" in html


@pytest.mark.skipif(NODE is None, reason="node no instalado")
@pytest.mark.parametrize("acciones", [
    [],                                                   # nada
    None,                                                 # sin acciones
    [{"accion": "escribir", "nombre": "P", "fecha_int": 20260518}],  # sv5 viejo
    [dict(ACCIONES[0])],                                  # sin aviso
    [dict(ACCIONES[2])],                                  # omitir con aviso
])
def test_f021_r20_sin_avisos_no_pinta_el_bloque(acciones) -> None:
    assert _pintar(acciones) == ""
