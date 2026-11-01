# tests/test_f046_marcas.py
"""F-046 · el portal: aviso del modal (R31) y marcas de reparto (R37).

- R37: las vistas de obra y de trabajador marcan «reparto pendiente» en
  las lineas afectadas, en las casillas de la matriz y en los dias del
  calendario (repositorio REAL sobre SQLite, vista servida por FastAPI).
- R31: las funciones del modal (`repartosHtml`, `decisionesPara`) se
  EJECUTAN con node (se saltan sin node); el cableado se lee del fuente.

Sin red. Datos sinteticos (el DNI y el nombre ficticios de `dobles`).
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
from infrastructure.database.orm_models import RepartoPendienteOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

RAIZ_SV4 = Path(__file__).resolve().parents[1]
PLANTILLAS = RAIZ_SV4 / "templates"
APP_JS = RAIZ_SV4 / "static" / "app.js"
STYLES = RAIZ_SV4 / "static" / "styles.css"
NODE = shutil.which("node")
OBRA = "/obras/obr-10?period=2026-03&modo=natural"
TRABAJADOR = "/trabajadores/rec-501?period=2026-03&modo=natural"


# ================================ R37 ================================= #

@pytest.fixture
def montaje(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "x", "PG_ADMIN_PASSWORD": "x",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)

    def _montar(estado_reparto: str | None):
        fabrica = FabricaSesionSqlite()
        dia = sembrar_parte(fabrica, [{"horas": 5.5}], document_id="doc-a")
        otro = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-b",
                             fecha="2026-03-03")
        if estado_reparto is not None:
            with fabrica.create_session() as s:
                s.add(RepartoPendienteOrm(
                    recurso_ide=501, fecha_int=20260302,
                    estado=estado_reparto, firma="f", cambios="{}",
                    creado_at_utc="x", actualizado_at_utc="x"))
                s.commit()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app), dia[0], otro[0]
    return _montar


def _fila(html: str, registro_id: int) -> str:
    marca = f'data-registro-id="{registro_id}"'
    ini = html.index(marca)
    return html[ini:html.index("</tr>", ini)]


@pytest.mark.parametrize("url", [OBRA, TRABAJADOR], ids=["obra",
                                                          "trabajador"])
def test_f046_r37_la_linea_afectada_lleva_la_marca(montaje, url):
    cliente, afectada, otra = montaje("pendiente")
    html = cliente.get(url).text
    assert 'data-reparto="pendiente"' in _fila(html, afectada)
    assert "reparto pendiente" in _fila(html, afectada)
    assert 'data-reparto="pendiente"' not in _fila(html, otra)


@pytest.mark.parametrize("estado", ["aplicando", "rechazado"])
def test_f046_r37_tambien_marca_aplicando_y_rechazado(montaje, estado):
    cliente, afectada, _o = montaje(estado)
    assert 'data-reparto="pendiente"' in _fila(cliente.get(OBRA).text,
                                               afectada)


@pytest.mark.parametrize("estado", [None, "aplicado", "materializado",
                                    "mantenido", "obsoleto"])
def test_f046_r37_sin_reparto_vivo_no_hay_marca(montaje, estado):
    cliente, _a, _o = montaje(estado)
    for url in (OBRA, TRABAJADOR):
        html = cliente.get(url).text
        assert 'data-reparto="pendiente"' not in html
        assert 'class="reparto-marca"' not in html


def test_f046_r37_la_casilla_de_la_matriz_lleva_la_marca(montaje):
    cliente, _a, _o = montaje("pendiente")
    html = cliente.get(OBRA).text
    celdas = re.findall(r'<td class="mx-cell[^>]*>', html, re.DOTALL)
    marcadas = [c for c in celdas if 'data-reparto="pendiente"' in c]
    assert len(marcadas) == 1
    assert "data-regs" in marcadas[0]


def test_f046_r37_el_dia_del_calendario_lleva_la_marca(montaje):
    cliente, _a, _o = montaje("pendiente")
    html = cliente.get(TRABAJADOR).text
    dias = re.findall(r'<div class="cal-day[^>]*>', html, re.DOTALL)
    marcados = [d for d in dias if 'data-reparto="pendiente"' in d]
    assert len(marcados) == 1
    assert 'data-fecha="2026-03-02"' in marcados[0]


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f046_r37_las_plantillas_parsean(plantilla):
    from jinja2 import Environment, FileSystemLoader

    entorno = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])


def test_f046_r37_estilos_de_la_marca():
    css = STYLES.read_text(encoding="utf-8")
    for selector in ('tr[data-reparto="pendiente"]', ".reparto-marca",
                     '.mx-cell[data-reparto="pendiente"]', ".ap-repartos"):
        assert selector in css


# ================================ R31 ================================= #

def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _variable(js: str, nombre: str) -> str:
    m = re.search(r"\n  var " + nombre + r" = \{.*?\n  \};\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _node(cuerpo: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    js = _js()
    programa = (_funcion(js, "esc")
                + _variable(js, "TEXTO_DECISION_REPARTO")
                + _variable(js, "TEXTO_ESTADO_REPARTO")
                + _funcion(js, "repartosHtml")
                + _funcion(js, "decisionesPara")
                + _funcion(js, "resultadoRepartosHtml")
                + "process.stdout.write(JSON.stringify((function () {\n"
                + cuerpo + "\n})()));\n")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60, check=False)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _reparto(opciones, motivo=None, editable=True):
    return {"id": 7, "fecha": "2026-03-02", "recurso_ide": 501,
            "estado": "pendiente", "editable": editable, "motivo": motivo,
            "opciones": opciones, "error": None, "registro_ids": [13],
            "lineas": [{"registro_id": 11, "nueva": False,
                        "tipo": "ordinaria", "obra_codigo": "0678",
                        "parte_cod": "PT26/00001", "antes": 8, "despues": 2.5,
                        "en_sigrid": True, "editable": editable,
                        "motivo": motivo}]}


def test_f046_r31_el_aviso_ofrece_aplicar_y_mantener():
    html = _node("return repartosHtml([" + json.dumps(
        _reparto(["aplicar", "mantener"])) + "]);")
    assert "Reparto de la jornada pendiente" in html
    assert html.count("type='radio'") == 2
    assert 'value="aplicar"' in html and 'value="mantener"' in html
    assert "Mantener lo registrado" in html
    assert " checked" not in html                # hay que elegir
    assert "PT26/00001" in html and "2.5" in html


def test_f046_r31_no_editable_solo_mantener_con_su_motivo():
    html = _node("return repartosHtml([" + json.dumps(
        _reparto(["mantener"], motivo="su parte de Sigrid no esta En "
                 "registro", editable=False)) + "]);")
    assert html.count("type='radio'") == 1
    assert 'value="aplicar"' not in html
    assert " checked" in html
    assert "su parte de Sigrid no esta En registro" in html


def test_f046_r31_sin_repartos_no_hay_aviso():
    assert _node("return repartosHtml([]) + repartosHtml(undefined);") == ""


def test_f046_r32_cada_decision_viaja_una_vez_con_sus_lineas():
    salida = _node("""
      var dec = [{id: 7, decision: "aplicar", registro_ids: [13, 14]},
                 {id: 8, decision: "mantener", registro_ids: [20]}];
      var enviadas = {};
      return [decisionesPara(dec, [1, 13], enviadas),
              decisionesPara(dec, [14, 20], enviadas),
              decisionesPara(dec, [13, 20], enviadas),
              decisionesPara(undefined, [13], {})];
    """)
    assert salida == [[{"id": 7, "decision": "aplicar"}],
                      [{"id": 8, "decision": "mantener"}], [], []]


def test_f046_r34_el_resultado_dice_que_paso():
    html = _node("""return resultadoRepartosHtml([
      {id: 7, estado: "aplicado", ok: true, error: null},
      {id: 8, estado: "aplicando", ok: false, error: "timeout"}]);""")
    assert "aplicado en Sigrid" in html
    assert "vuelve a aprobar para reintentarlo" in html and "timeout" in html


def test_f046_r31_el_modal_cablea_aviso_y_decision():
    js = _js()
    aprobar = _funcion(js, "aprobar")
    assert "repartosHtml(pf.repartos)" in aprobar
    assert "decisionesReparto(cj, pf.repartos)" in aprobar
    confirmar = _funcion(js, "confirmar")
    assert "decisionesPara(decisiones, cuerpo.registro_ids, enviadas)" \
        in confirmar
    assert "cuerpo.repartos = dec" in confirmar
