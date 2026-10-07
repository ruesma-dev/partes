# tests/test_f035_vistas.py
"""F-035 · vistas del portal (HTML renderizado) con recursos y empresa.

  - R7: los candidatos de Conciliar salen de los recursos activos de la
    empresa por defecto de la tarjeta (un recurso sin ficha tambien).
  - R8: cada tarjeta tiene selector de empresa: la de sus partes si es una
    sola; con varias o ninguna, «Todas».
  - R10: cada candidato lleva `data-empresa`, el nombre de su empresa y el
    `recurso_ide` que enviara el boton.
  - R17/R18: «Nuevo parte» y el modal «+ Añadir linea» tienen selector de
    empresa (y el modal, el hidden del recurso).
  - R20: el combo de trabajador del detalle de obra lleva la empresa de la
    obra (si se conoce).

Parseo Jinja2 de las cuatro plantillas tocadas. Sin red ni PostgreSQL.
Datos SINTETICOS.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from config.settings import Settings
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import ObraOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f035_endpoints import ENTORNO, SIGRID, LookupFalso

PLANTILLAS = Path(__file__).resolve().parents[1] / "templates"

OBRAS = [ObraOption(ide=10, codigo="0678", nombre="Carmona", empresa=28),
         ObraOption(ide=20, codigo="0678", nombre="Carmona", empresa=1)]


class LookupConObras(LookupFalso):
    def fetch_obras(self) -> list:
        return list(OBRAS)


def _sembrar(fabrica, leido, doc, empresa, *, obra_ide=10) -> list[int]:
    ids = sembrar_parte(fabrica, [{"leido": leido}], document_id=doc,
                        empleado_ide=None, empleado_dni="",
                        empleado_nombre=None, obra_ide=obra_ide)
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, doc).empresa = empresa
        for rid in ids:
            s.get(ParteRegistroOrm, rid).empleado_match_method = "none"
        s.commit()
    return ids


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {**ENTORNO, **SIGRID}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupConObras)
    fabrica = FabricaSesionSqlite()
    # «Tres Solo Recurso»: solo partes de Porsan (28).
    _sembrar(fabrica, "Tres Solo Recurso", "d-porsan", 28)
    # «Uno Recurso»: un parte de cada empresa.
    _sembrar(fabrica, "Uno Recurso", "d-mix-1", 1, obra_ide=20)
    _sembrar(fabrica, "Uno Recurso", "d-mix-28", 28)
    # «Dos Recurso»: partes sin empresa (anteriores a F-023).
    _sembrar(fabrica, "Dos Recurso", "d-sin", None)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), fabrica


def _tarjeta(html: str, nombre: str) -> str:
    """El HTML de la tarjeta de Conciliar de `nombre`."""
    trozos = re.split(r'(?=<div class="recon-card )', html)
    (trozo,) = [t for t in trozos if f'data-nombre="{nombre}"' in t[:200]]
    return trozo


def _empresa_elegida(tarjeta: str) -> str:
    sel = re.search(r'<select class="recon-empresa"[^>]*>(.*?)</select>',
                    tarjeta, re.S)
    assert sel, "la tarjeta no tiene selector de empresa"
    (valor,) = re.findall(r'<option value="([^"]*)" selected', sel.group(1))
    return valor


# =============================== R7 ===================================== #

def test_f035_r7_candidato_recurso_sin_ficha(portal) -> None:
    cliente, _ = portal
    tarjeta = _tarjeta(cliente.get("/conciliacion").text,
                       "Tres Solo Recurso")
    assert "MO/0037" in tarjeta and "TRES SOLO RECURSO" in tarjeta
    assert 'data-recurso-ide="903"' in tarjeta


def test_f035_r7_candidatos_solo_de_la_empresa_por_defecto(portal) -> None:
    cliente, fabrica = portal
    # Si sus partes fueran de Ruesma, el recurso de Porsan no es candidato.
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "d-porsan").empresa = 1
        s.commit()
    tarjeta = _tarjeta(cliente.get("/conciliacion").text,
                       "Tres Solo Recurso")
    assert 'data-recurso-ide="903"' not in tarjeta


# =============================== R8 ===================================== #

def test_f035_r8_empresa_por_defecto_de_cada_tarjeta(portal) -> None:
    cliente, _ = portal
    html = cliente.get("/conciliacion").text
    assert _empresa_elegida(_tarjeta(html, "Tres Solo Recurso")) == "28"
    assert _empresa_elegida(_tarjeta(html, "Uno Recurso")) == ""
    assert _empresa_elegida(_tarjeta(html, "Dos Recurso")) == ""


def test_f035_r8_opciones_del_selector(portal) -> None:
    cliente, _ = portal
    tarjeta = _tarjeta(cliente.get("/conciliacion").text, "Uno Recurso")
    sel = re.search(r'<select class="recon-empresa"[^>]*>(.*?)</select>',
                    tarjeta, re.S).group(1)
    assert re.findall(r'<option value="([^"]*)"[^>]*>([^<]*)</option>',
                      sel) == [("", "Todas"), ("1", "Ruesma"),
                               ("28", "Porsan")]


# =============================== R10 ==================================== #

def test_f035_r10_candidatos_con_su_empresa(portal) -> None:
    cliente, _ = portal
    # Con «Todas», los candidatos de las dos empresas.
    tarjeta = _tarjeta(cliente.get("/conciliacion").text, "Uno Recurso")
    filas = re.findall(r'<tr class="recon-cand" data-empresa="([^"]*)">'
                       r'(.*?)</tr>', tarjeta, re.S)
    por_recurso = {re.search(r'data-recurso-ide="(\d+)"', f).group(1):
                   (emp, f) for emp, f in filas}
    assert por_recurso["901"][0] == "1" and "Ruesma" in por_recurso["901"][1]
    assert 'class="manual-q' in tarjeta
    assert "Buscar otro recurso" in tarjeta


# =========================== R17 / R18 ================================== #

def test_f035_r17_r18_nuevo_parte_con_selector_de_empresa(portal) -> None:
    cliente, _ = portal
    html = cliente.get("/nuevo").text
    sel = re.search(r'<select id="emp-empresa"[^>]*>(.*?)</select>', html,
                    re.S)
    assert sel, "Nuevo parte sin selector de empresa"
    assert re.findall(r'<option value="([^"]*)"', sel.group(1)) == \
        ["", "1", "28"]
    assert "Código, nombre o DNI" in html
    # El selector va encima del trabajador.
    assert html.index('id="emp-empresa"') < html.index('id="emp-input"')


def test_f035_r17_r18_r19_modal_con_empresa_y_recurso(portal) -> None:
    cliente, _ = portal
    html = cliente.get("/nuevo").text          # el modal vive en base.html
    sel = re.search(r'<select id="addline-empresa"[^>]*>(.*?)</select>',
                    html, re.S)
    assert sel, "el modal sin selector de empresa"
    assert re.findall(r'<option value="([^"]*)"', sel.group(1)) == \
        ["", "1", "28"]
    assert '<input type="hidden" id="addline-emp-reside">' in html


# =============================== R20 ==================================== #

def test_f035_r20_combo_del_detalle_de_obra_con_su_empresa(portal) -> None:
    cliente, _ = portal
    html = cliente.get("/obras/obr-10").text
    combos = re.findall(r'<div class="combo-emp"[^>]*>', html)
    assert combos and all('data-empresa="28"' in c for c in combos)
    html_r = cliente.get("/obras/obr-20").text
    assert all('data-empresa="1"' in c
               for c in re.findall(r'<div class="combo-emp"[^>]*>', html_r))


def test_f035_r20_obra_desconocida_sin_filtro(portal, monkeypatch) -> None:
    cliente, fabrica = portal
    with fabrica.create_session() as s:
        for r in s.query(ParteRegistroOrm).all():
            r.obra_ide = 99
        s.commit()
    html = cliente.get("/obras/obr-99").text
    combos = re.findall(r'<div class="combo-emp"[^>]*>', html)
    assert combos and not any("data-empresa" in c for c in combos)


# ===================== JS (cableado, sin navegador) ===================== #

def _js() -> str:
    return (PLANTILLAS.parent / "static" / "app.js").read_text(
        encoding="utf-8")


def test_f035_r10_r11_r21_js_envia_recurso_ide() -> None:
    js = _js()
    assert "body: JSON.stringify({ nombre_leido: nombre, recurso_ide: recursoIde })" in js
    assert "var body = { recurso_ide: recursoIde };" in js     # reasignar
    assert 'getAttribute("data-recurso-ide")' in js
    assert '"&empresa=" + encodeURIComponent(emp)' in js       # buscar
    assert 'wrap.getAttribute("data-empresa")' in js           # R20


def test_f035_r17_r19_js_combos_sobre_recursos_y_reside_del_modal() -> None:
    js = _js()
    assert js.count('"/api/sigrid/recursos"') == 3     # 2 combos + REC_URL
    assert '"/api/sigrid/empleados"' not in js         # jornadas: su plantilla
    assert 'empleado_reside: g("addline-emp-reside").value || null' in js
    assert js.count("deLaEmpresaDe(") == 3             # definicion + 2 usos
    assert js.count("fijarEmpresa(") == 4              # definicion + 3 usos
    assert js.count("function _comboSimple(") == 1     # F-016 DA11 intacto


# ============================ parseo Jinja2 ============================= #

@pytest.mark.parametrize("plantilla", ["conciliacion.html", "nuevo_parte.html",
                                       "base.html", "obra_detail.html"])
def test_f035_plantillas_parsean(plantilla) -> None:
    entorno = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])


# ============== R17/R19: callbacks de los combos, ejecutados ============== #

import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

RECURSO_JS = {
    "ide": 903, "codigo": "MO/0037", "nombre": "TRES SOLO RECURSO",
    "dni": "00000003A", "empresa": 28, "categoria": "Peon",
    "jornada_sugerida": 7.5,
    "guardar": {"empleado_ide": None, "empleado_codigo": "MO/0037",
                "empleado_nombre": "TRES SOLO RECURSO",
                "empleado_dni": "00000003A", "empleado_reside": 903},
}

#: Entorno minimo del callback: `document` falso, los cierres que usa y un
#: `_comboSimple` que llama al `onPick` con un recurso. Sin navegador ni red.
ARNES_JS = """\
"use strict";
var els = {}, llamadas = [];
var document = { getElementById: function (id) {
  return els[id] || (els[id] = { value: "" }); } };
function g(id) { return document.getElementById(id); }
var selEmpresa = null, selAddEmpresa = null;
var empEmpresa = null, addlineEmpEmpresa = null;
var calDias = { viejo: 1 }, calPedido = "viejo";
function cargarCalendario() { llamadas.push("calendario"); }
function updateBtn() { llamadas.push("updateBtn"); }
function recLabel(r) { return r.nombre; }
function deLaEmpresaDe() { return null; }
var RECURSO = %(recurso)s;
function _comboSimple(root, input, panel, url, render, onPick, filtro) {
  onPick(RECURSO);
}
%(llamada)s
var valores = {};
Object.keys(els).forEach(function (k) { valores[k] = els[k].value; });
console.log(JSON.stringify({ valores: valores, llamadas: llamadas,
  calPedido: calPedido }));
"""


def _llamada_combo(js: str, combo: str, filtro: str) -> str:
    """El `_comboSimple("<combo>", …, deLaEmpresaDe(<filtro>));` de app.js."""
    inicio = js.index(f'_comboSimple("{combo}"')
    fin = js.index(f"deLaEmpresaDe({filtro}));", inicio) + len(
        f"deLaEmpresaDe({filtro}));")
    return js[inicio:fin]


def _ejecutar(llamada: str) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    script = ARNES_JS % {"recurso": json.dumps(RECURSO_JS),
                         "llamada": llamada}
    r = subprocess.run([node, "-e", script], capture_output=True, text=True,
                       timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_f035_r17_r19_nuevo_parte_al_elegir_recurso_rellena_todo() -> None:
    """Elegir un recurso en «Nuevo parte» copia los `guardar.*`, la categoria
    y la jornada sugerida, recarga el calendario y reevalua «Crear»."""
    salida = _ejecutar(_llamada_combo(_js(), "emp-combo", "selEmpresa"))
    assert salida["valores"] == {
        "emp-ide": "", "emp-codigo": "MO/0037",
        "emp-nombre": "TRES SOLO RECURSO", "emp-dni": "00000003A",
        "emp-reside": 903, "categoria": "Peon", "horas-ord": 7.5}
    assert salida["llamadas"] == ["calendario", "updateBtn"]
    assert salida["calPedido"] == ""


def test_f035_r17_r19_modal_al_elegir_recurso_rellena_todo() -> None:
    salida = _ejecutar(_llamada_combo(_js(), "addline-emp-combo",
                                      "selAddEmpresa"))
    assert salida["valores"] == {
        "addline-emp-ide": "", "addline-emp-codigo": "MO/0037",
        "addline-emp-nombre": "TRES SOLO RECURSO",
        "addline-emp-dni": "00000003A", "addline-emp-reside": 903,
        "addline-categoria": "Peon", "addline-ord": 7.5}
