# tests/test_f061_portal.py
"""F-061 · el portal ante el parte retirado (R12, R13 y el aviso de R7).

- R12: tras borrar la última línea, `app.js` avisa y, si está en el
  detalle de ese parte, lleva a `/partes` en vez de recargar (daría 404).
  Se EJECUTA en node la función real `destinoTrasBorrar`, extraída de
  `static/app.js` como en F-049. Sin navegador ni red.
- R13: `/partes` cuenta empleados y horas solo con las líneas vivas y
  marca con «Sin líneas» el parte activo sin ninguna viva.

SQLite en memoria con el ORM real. Datos sintéticos.
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
from jinja2 import Environment, FileSystemLoader

from dobles import FabricaSesionSqlite, sembrar_parte
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    ParteRow,
)
from interface_adapters.web.app import build_app

RAIZ = Path(__file__).resolve().parents[1]
APP_JS = RAIZ / "static" / "app.js"
PLANTILLAS = RAIZ / "templates"
NODE = shutil.which("node")

AVISO = ("El parte se ha quedado sin líneas y se ha retirado; sus líneas "
         "siguen en la papelera.")


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


# =============================== R12 ================================== #

def _destino(respuestas, ruta):
    js = _funcion(_js(), "destinoTrasBorrar")
    return _node(js + "\nprocess.stdout.write(JSON.stringify("
                 f"destinoTrasBorrar({json.dumps(respuestas)}, "
                 f"{json.dumps(ruta)})));")


def test_f061_r12_sin_parte_retirado_recarga_sin_aviso() -> None:
    assert _destino([{"ok": True, "parte_retirado": False,
                      "document_id": "d1"}], "/partes/d1") == {
        "aviso": None, "destino": None}


def test_f061_r12_en_el_detalle_del_parte_retirado_va_a_partes() -> None:
    resp = [{"ok": True, "parte_retirado": True, "document_id": "d1"}]
    assert _destino(resp, "/partes/d1") == {"aviso": AVISO,
                                            "destino": "/partes"}
    assert _destino(resp, "/partes/d1/") == {"aviso": AVISO,
                                             "destino": "/partes"}


def test_f061_r12_en_otra_pagina_avisa_y_recarga() -> None:
    resp = [{"ok": True, "parte_retirado": True, "document_id": "d1"}]
    assert _destino(resp, "/obras/obr-10") == {"aviso": AVISO,
                                               "destino": None}
    assert _destino(resp, "/partes/d2") == {"aviso": AVISO, "destino": None}


def test_f061_r12_en_bloque_basta_con_una_respuesta() -> None:
    resp = [None, {"ok": False}, {"ok": True, "parte_retirado": False},
            {"ok": True, "parte_retirado": True, "document_id": "d1"}]
    assert _destino(resp, "/partes/d1") == {"aviso": AVISO,
                                            "destino": "/partes"}


def test_f061_r12_los_dos_borrados_usan_la_regla() -> None:
    """El borrado una a una (`.line-del`) y en bloque (`doBorrar`)."""
    js = _js()
    m = re.search(r'_bindClick\("\.line-del".*?\n    \}\);\n', js, re.DOTALL)
    assert m and "_irTrasBorrar([d])" in m.group(0)
    m = re.search(r"\n    function doBorrar\(.*?\n    \}\n", js, re.DOTALL)
    assert m, "app.js no define doBorrar"
    assert "_postJSON(" in m.group(0) and "_irTrasBorrar(" in m.group(0)
    ir = _funcion(js, "_irTrasBorrar")
    assert "destinoTrasBorrar(" in ir and "window.location.pathname" in ir


def test_f061_r7_restaurar_ensena_el_motivo() -> None:
    js = _js()
    for sel in ("[data-restore-doc]", "[data-restore-line]"):
        m = re.search(r'_bindClick\("' + re.escape(sel) + r'".*?\n    \}\);\n',
                      js, re.DOTALL)
        assert m, sel
        assert "alert(d.error)" in m.group(0), sel


def test_f061_r12_app_js_pasa_node_check() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr


# =============================== R13 ================================== #

def _fila(repo, document_id: str) -> ParteRow:
    return next(p for p in repo.list_partes()
                if p.document_id == document_id)


def test_f061_r13_list_partes_cuenta_solo_las_vivas() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 2.0, "tipo": "extra"}],
                  document_id="d1")
    # Otra persona con una línea en la papelera del mismo parte.
    sembrar_parte(fabrica, [{"horas": 5.0, "borrada": True}],
                  document_id="d1-x", empleado_ide=88, recurso_ide=777,
                  empleado_dni="87654321X", empleado_nombre="Otra")
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        for reg in s.query(ParteRegistroOrm).filter_by(document_id="d1-x"):
            reg.document_id = "d1"
        s.commit()
    fila = _fila(ParteReviewRepository(fabrica), "d1")
    assert (fila.num_empleados, fila.num_registros) == (1, 2)
    assert (fila.horas_normales, fila.horas_extra) == (8.0, 2.0)
    assert fila.sin_lineas is False


def test_f061_r13_parte_activo_sin_vivas_lleva_sin_lineas() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"borrada": True}], document_id="d-papelera")
    sembrar_parte(fabrica, [], document_id="d-cero")
    repo = ParteReviewRepository(fabrica)
    for did in ("d-papelera", "d-cero"):
        fila = _fila(repo, did)
        assert fila.sin_lineas is True, did
        assert (fila.num_empleados, fila.num_registros,
                fila.horas_normales, fila.horas_extra) == (0, 0, 0.0, 0.0)


def test_f061_r13_parterow_sin_lineas_por_defecto_false() -> None:
    fila = ParteRow(document_id="d", fecha=None, obra_codigo=None,
                    obra_nombre=None, encargado_nombre=None,
                    num_empleados=0, num_registros=0, horas_normales=0.0,
                    horas_extra=0.0, firmado=False, firmante_rol=None,
                    review_required=None, approved=False)
    assert fila.sin_lineas is False


def test_f061_r13_la_plantilla_pinta_sin_lineas(monkeypatch) -> None:
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests"}.items():
        monkeypatch.setenv(clave, valor)
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"borrada": True}], document_id="d-vacio")
    sembrar_parte(fabrica, [{}], document_id="d-lleno")
    cliente = TestClient(build_app(Settings(_env_file=None),
                                   repository=ParteReviewRepository(fabrica)))
    html = cliente.get("/partes").text
    assert html.count("Sin líneas") == 1
    fila_vacia = re.search(r'href="/partes/d-vacio".*?</tr>', html, re.DOTALL)
    assert fila_vacia and "Sin líneas" in fila_vacia.group(0)


def test_f061_r13_partes_list_parsea_en_jinja2() -> None:
    env = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    env.parse((PLANTILLAS / "partes_list.html").read_text(encoding="utf-8"))
