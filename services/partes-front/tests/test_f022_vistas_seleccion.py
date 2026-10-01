# tests/test_f022_vistas_seleccion.py
"""F-022 · la seleccion en las vistas de obra y de persona (R1, R4-R9).

Dos bloques (los `-k` de tasks.md):

  - `vista` (T9): el HTML REAL de las dos vistas: casilla `sel-linea` en
    cada fila (tambien congelada), barra de seleccion y `#aprobar-todo`
    con lo que el navegador necesita para mandar el `ambito`.
  - `js` (T10): el proyecto no tiene arnes de tests JS; se mira el texto de
    `static/app.js` (patron de `test_f004_r16`) y, con `node` instalado, se
    EJECUTAN las funciones puras del modal. El resto es MANUAL (M2-M7).

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
from jinja2 import Environment, FileSystemLoader
from tests.dobles import FabricaSesionSqlite, sembrar_parte

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
APP_JS = RAIZ_SERVICIO / "static" / "app.js"

URL_OBRA = "/obras/obr-10?period=2026-03&modo=natural"
URL_PERSONA = "/trabajadores/emp-77?period=2026-03&modo=natural"


@pytest.fixture
def montaje(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    fabrica = FabricaSesionSqlite()
    # Una linea libre, una registrada (congelada) y una encolada (congelada).
    ids = sembrar_parte(fabrica, [{"estado": None}, {"estado": "registrado"},
                                  {"estado": "encolado"}])
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), ids


def _fila(html: str, registro_id: int) -> str:
    marca = f'<tr data-registro-id="{registro_id}"'
    ini = html.index(marca)
    return html[ini:html.index("</tr>", ini)]


def _celda_fecha(fila: str) -> str:
    ini = fila.index('<td class="cell-fecha">')
    return fila[ini:fila.index("</td>", ini)]


def _boton_aprobar(html: str) -> str:
    m = re.search(r'<button[^>]*id="aprobar-todo"[^>]*>', html, re.DOTALL)
    assert m, "la vista tiene que tener #aprobar-todo"
    return m.group(0)


# ===================================================================== #
# T9 · R1 · casilla en la celda Fecha de CADA fila
# ===================================================================== #

@pytest.mark.parametrize("url", [URL_OBRA, URL_PERSONA])
def test_f022_r1_vista_casilla_en_cada_fila_tambien_congelada(
        montaje, url) -> None:
    cliente, ids = montaje
    html = cliente.get(url).text
    for rid in ids:
        celda = _celda_fecha(_fila(html, rid))
        casilla = re.search(r'<input[^>]*class="sel-linea"[^>]*>', celda)
        assert casilla, f"la fila {rid} no tiene casilla"
        assert f'data-registro-id="{rid}"' in casilla.group(0)
        assert 'type="checkbox"' in casilla.group(0)
        assert "disabled" not in casilla.group(0)     # DA6: tambien congelada
    assert html.count('class="sel-linea"') == len(ids)


@pytest.mark.parametrize("url", [URL_OBRA, URL_PERSONA])
def test_f022_r3_vista_barra_de_seleccion_y_contador(montaje, url) -> None:
    cliente, _ids = montaje
    html = cliente.get(url).text
    barra = re.search(r'<div class="sel-tools"[^>]*>(.*?)</div>', html,
                      re.DOTALL)
    assert barra, "falta la barra .sel-tools"
    assert "data-sel-visibles" in barra.group(1)
    assert "Seleccionar visibles" in barra.group(1)
    assert "data-sel-ninguna" in barra.group(1)
    assert "Quitar selecci" in barra.group(1)
    assert "data-sel-contador" in barra.group(1)
    # La barra va antes de la tabla de lineas.
    assert html.index('class="sel-tools"') < html.index('id="lines-table"')


def test_f022_r8_vista_obra_boton_con_su_ambito(montaje) -> None:
    cliente, _ids = montaje
    boton = _boton_aprobar(cliente.get(URL_OBRA).text)
    assert 'data-vista="obra"' in boton
    assert 'data-obra-key="obr-10"' in boton
    assert 'data-period="2026-03"' in boton
    assert 'data-mode="natural"' in boton


def test_f022_r8_vista_persona_boton_con_su_ambito(montaje) -> None:
    cliente, _ids = montaje
    boton = _boton_aprobar(cliente.get(URL_PERSONA).text)
    assert 'data-vista="trabajador"' in boton
    assert 'data-worker-key="emp-77"' in boton
    assert "data-obra-key" not in boton


@pytest.mark.parametrize("url", [URL_OBRA, URL_PERSONA])
def test_f022_r9_vista_los_botones_por_linea_no_cambian(montaje, url) -> None:
    cliente, ids = montaje
    fila = _fila(cliente.get(url).text, ids[0])
    boton = re.search(r'<button[^>]*aprobar-linea[^>]*>', fila)
    assert boton
    assert f'data-registro-id="{ids[0]}"' in boton.group(0)
    assert "data-vista" not in boton.group(0)
    assert "ambito" not in boton.group(0)


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f022_r34_vista_las_plantillas_parsean(plantilla) -> None:
    entorno = Environment(loader=FileSystemLoader(
        str(RAIZ_SERVICIO / "templates")))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])


# ===================================================================== #
# T10 · app.js: estaticos (texto) y funciones puras ejecutadas con node
# ===================================================================== #

def _js() -> str:
    return APP_JS.read_text(encoding="utf-8").replace("\r\n", "\n")


def _funcion(js: str, nombre: str, sangria: str = "  ") -> str:
    m = re.search(r"\n" + sangria + "function " + nombre + r"\(.*?\n"
                  + sangria + r"\}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _var(js: str, nombre: str) -> str:
    m = re.search(r"\n  var " + nombre + r" = .*?;\n", js, re.DOTALL)
    assert m, f"app.js no declara {nombre}"
    return m.group(0)


def test_f022_r4_js_filtros_y_orden_ignoran_la_casilla() -> None:
    cuerpo = _funcion(_js(), "_filterCellText")
    assert 'classList.contains("sel-linea")' in cuerpo


def test_f022_r4_js_el_rango_solo_marca_visibles_en_el_orden_actual() -> None:
    js = _js()
    rango = _funcion(js, "selectRange", sangria="    ")
    assert "PartidaSel.visible(filas[i])" in rango
    assert "cuerpo.rows" in rango
    visible = re.search(r"function visible\(tr\) \{.*?\n  \}", js, re.DOTALL)
    assert visible and "filtered-day" in visible.group(0)
    assert 'style.display !== "none"' in visible.group(0)


def test_f022_r2_js_la_casilla_y_la_seleccion_van_juntas() -> None:
    js = _js()
    assert 'querySelector("input.sel-linea")' in _funcion(
        js, "paint", sangria="    ")
    assert "toggle(tr, casilla.checked)" in _funcion(js, "wireBulkSelect")
    # PartidaSel es global: la lee el boton de aprobar de otro IIFE.
    assert "\nvar PartidaSel = (function () {" in js


def test_f022_r6_js_filtros_y_seleccion_avisan_del_cambio() -> None:
    js = _js()
    assert js.count("avisarCambioLineas();") >= 3
    assert 'addEventListener("lineas:cambio", actualizarBoton)' in js
    assert 'addEventListener("lineas:cambio", pintarContador)' in js


def test_f022_r8_js_la_cabecera_manda_ids_y_ambito() -> None:
    js = _js()
    assert ("aprobar({ registro_ids: c.ids, ambito: ambitoDe(todo) }, c)"
            in js)
    assert "obra_key: todo.dataset.obraKey" not in js     # ya no hay atajo
    confirmar = _funcion(js, "confirmar")
    assert "ambito: peticion.ambito" in confirmar
    assert '"/api/aprobar/ejecutar"' in confirmar
    assert '"/api/aprobar/encolar"' in confirmar
    # Repetir con las borradas conserva ids y ambito (F-024 R25).
    assert ("aprobar(Object.assign({}, peticion, { incluir_borradas: true "
            "}), contexto)") in _funcion(js, "aprobar")


def test_f022_r9_js_el_boton_por_linea_no_lleva_ambito() -> None:
    js = _js()
    ini = js.index('var linea = ev.target.closest(".aprobar-linea");')
    bloque = js[ini:js.index("return;", ini)]
    assert "ambito:" not in bloque and "ambitoDe" not in bloque
    assert "aprobar(porLinea, null)" in bloque


def test_f022_r19_js_las_casillas_de_pisar_llevan_el_grupo() -> None:
    js = _js()
    assert 'var SEPARADOR_CLAVE = "::";' in js
    assert "claveConGrupo(grupo, c.clave)" in _funcion(js, "conflictosHtml")
    assert "conflictosHtml(g.conflictos, g.clave)" in _funcion(js, "grupoHtml")


def test_f022_r23_js_el_modal_pinta_el_listado_del_servidor() -> None:
    js = _js()
    assert "listadoHtml(g.listado)" in _funcion(js, "grupoHtml")
    aprobar = _funcion(js, "aprobar")
    assert "pf.grupos" in aprobar
    assert "pf.umbral_plegado" in aprobar
    assert "pf.excluidas_detalle" in aprobar


def test_f021_y_f022_js_el_aviso_de_cuenta_sigue_por_obra() -> None:
    """F-021 R19 vive en `resumenHtml(pf)`; F-022 lo llama por grupo."""
    js = _js()
    assert "avisosCuentaHtml(pf.acciones)" in _funcion(js, "resumenHtml")
    assert "resumenHtml(g)" in _funcion(js, "grupoHtml")


NODE = shutil.which("node")
sin_node = pytest.mark.skipif(NODE is None, reason="node no instalado")


def _ejecutar_js(nombres: list[str], expresion: str, variables=()) -> object:
    js = _js()
    fuente = "".join(_var(js, v) for v in variables)
    fuente += "".join(_funcion(js, n) for n in nombres)
    programa = (fuente + "\nprocess.stdout.write(JSON.stringify("
                + expresion + "));\n")
    salida = subprocess.run([NODE, "-e", programa], capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


GRUPOS = [
    {"clave": "obr-10", "ok": True, "registro_ids": [1, 2]},
    {"clave": "obr-20", "ok": True, "registro_ids": [3]},
    {"clave": "obr-30", "ok": True, "sesame_bloqueo": "sin Sesame",
     "registro_ids": [4]},
    {"clave": "obr-40", "ok": False, "error": "caido", "registro_ids": [5]},
]


def _plan(claves, forzado):
    plan = _ejecutar_js(
        ["planEnvio"], "planEnvio(" + json.dumps(GRUPOS) + ","
        + json.dumps(claves) + "," + json.dumps(forzado) + ")",
        variables=["SEPARADOR_CLAVE"])
    return {k: [g["clave"] for g in v] for k, v in plan.items()}


@sin_node
def test_f022_r29_js_plan_sin_claves_ni_override() -> None:
    assert _plan([], False) == {"sincronos": [], "cola": ["obr-10", "obr-20"],
                                "fuera": ["obr-30", "obr-40"]}


@sin_node
def test_f022_r29_js_plan_con_claves_y_override() -> None:
    assert _plan(["obr-20::501|20260302|1"], True) == {
        "sincronos": ["obr-20", "obr-30"], "cola": ["obr-10"],
        "fuera": ["obr-40"]}


@sin_node
def test_f022_r29_js_ids_y_claves_de_sus_grupos() -> None:
    ids = _ejecutar_js(["idsDe"], "idsDe(" + json.dumps(GRUPOS[:2]) + ")")
    assert ids == [1, 2, 3]
    claves = _ejecutar_js(
        ["clavesDe"], "clavesDe(" + json.dumps(GRUPOS[1:2])
        + ', ["obr-10::a", "obr-20::b", "obr-20::c"])',
        variables=["SEPARADOR_CLAVE"])
    assert claves == ["obr-20::b", "obr-20::c"]


@sin_node
@pytest.mark.parametrize("c,texto,motivo,alcance", [
    ({"modo": "seleccion", "ids": [1, 2], "total": 9, "marcadas": 3},
     "✓ Aprobar seleccionadas (2)", "", "2 seleccionadas de 9"),
    ({"modo": "visibles", "ids": [1], "total": 9, "marcadas": 0},
     "✓ Aprobar visibles (1)", "", "1 visibles de 9"),
    ({"modo": "todo", "ids": [1, 2, 3], "total": 3, "marcadas": 0},
     "✓ Aprobar todo (3)", "", "todas (3) de 3"),
    ({"modo": "seleccion", "ids": [], "total": 9, "marcadas": 3},
     "✓ Aprobar seleccionadas (0)",
     ("Las 3 lineas seleccionadas estan ocultas por los filtros: no se "
      "aprueba ninguna"), "0 seleccionadas de 9"),
    ({"modo": "visibles", "ids": [], "total": 9, "marcadas": 0},
     "✓ Aprobar visibles (0)",
     "Ninguna linea visible con los filtros actuales", "0 visibles de 9"),
    ({"modo": "todo", "ids": [], "total": 0, "marcadas": 0},
     "✓ Aprobar todo (0)", "No hay lineas en la tabla", "todas (0) de 0"),
])
def test_f022_r6_r7_js_texto_motivo_y_alcance_del_boton(
        c, texto, motivo, alcance) -> None:
    out = _ejecutar_js(
        ["textoBoton", "motivoVacio", "alcanceTexto"],
        "(function (c) { return [textoBoton(c), motivoVacio(c), "
        "alcanceTexto(c)]; })(" + json.dumps(c) + ")")
    assert out == [texto, motivo, alcance]


@sin_node
@pytest.mark.parametrize("n,ocultas,esperado", [
    (0, 0, ""), (1, 0, "1 seleccionada"), (3, 0, "3 seleccionadas"),
    (3, 1, "3 seleccionadas (1 oculta: no se aprueban)"),
    (3, 2, "3 seleccionadas (2 ocultas: no se aprueban)"),
])
def test_f022_r5_js_contador_de_seleccion(n, ocultas, esperado) -> None:
    assert _ejecutar_js(["textoSeleccion"],
                        f"textoSeleccion({n}, {ocultas})") == esperado


FUNCIONES_MODAL = ["esc", "fechaLegible", "num", "resumenHtml",
                   "avisosCuentaHtml", "avisosCalendarioHtml",
                   "claveConGrupo", "conflictosHtml", "obraTexto",
                   "horasTexto", "totalesTexto", "listadoHtml", "grupoHtml"]
VARS_MODAL = ["SEPARADOR_CLAVE", "ETIQUETAS_ESTADO", "TIPOS"]

GRUPO = {
    "clave": "obr-10", "ok": True,
    "obra": {"codigo": "0100", "nombre": "Obra <Uno>"},
    "partes": [{"cod": "PT26/00001", "mes": 3, "ano": 2026, "existe": True}],
    "resumen": {"escribir": 1}, "acciones": [], "avisos_calendario": [],
    "conflictos": [{"clave": "501|20260302|1", "nombre": "Persona A",
                    "fecha_int": 20260302, "parte_cod": "PT26/00001",
                    "hora_codigo": "HL01", "lineas": [], "contexto": []}],
    "listado": [{"registro_id": 1, "fecha_int": 20260302,
                 "nombre": "Persona <A>", "tipo": "extra",
                 "hora_codigo": "HE01", "horas": 2.5, "partida_cod": "P-1",
                 "recurso_ide": 501, "estado": "reaprobacion",
                 "motivo": "antes: \"error\""}],
    "totales": {"lineas": 1, "por_estado": {"reaprobacion": 1},
                "horas_ordinarias": 0, "horas_extra": 2.5, "incidencias": 0},
}


def _grupo_html(grupo: dict, plegar: bool) -> str:
    return _ejecutar_js(FUNCIONES_MODAL, "grupoHtml(" + json.dumps(grupo)
                        + ", " + json.dumps(plegar) + ")",
                        variables=VARS_MODAL)


@sin_node
def test_f022_r27_js_seccion_por_obra_con_resumen_y_listado() -> None:
    html = _grupo_html(GRUPO, False)
    assert "<details class='ap-grupo-det' open>" in html
    resumen = re.search(r"<summary>(.*?)</summary>", html).group(1)
    assert "0100 · Obra &lt;Uno&gt;" in resumen
    assert "1 linea(s) · 0 h ordinarias · 2,5 h extra · 0 incidencia(s)" \
        in resumen
    assert "1 reaprobación" in resumen
    fila = re.search(r"<tbody>(.*?)</tbody>", html).group(1)
    assert "02/03/2026" in fila and "Persona &lt;A&gt;" in fila
    assert ">extra<" in fila and ">HE01<" in fila and ">2,5<" in fila
    assert 'title="antes: &quot;error&quot;"' in fila
    assert ">reaprobación<" in fila


@sin_node
def test_f022_r28_js_plegado_con_conflictos_y_errores_fuera() -> None:
    malo = dict(GRUPO, ok=False, error="sv5 <caido>",
                sesame_bloqueo="sin Sesame")
    html = _grupo_html(malo, True)
    assert "<details class='ap-grupo-det'>" in html          # plegada
    fuera = html[html.index("</details>"):]
    assert "No se registra: sv5 &lt;caido&gt;" in fuera
    assert "Bloqueada: sin Sesame" in fuera
    assert 'value="obr-10::501|20260302|1"' in fuera        # R19
    assert "ap-pisar" not in html[:html.index("</details>")]


@sin_node
def test_f022_r26_js_excluidas_y_ocultas_aparte() -> None:
    detalle = [{"fecha_int": 20260302, "nombre": "Persona A",
                "obra_codigo": "0100", "horas": 8,
                "motivo": "ya registrada en Sigrid (parte PT26/00001): no "
                          "se reenvia"}]
    html = _ejecutar_js(
        ["esc", "fechaLegible", "horasTexto", "excluidasDetalleHtml"],
        "excluidasDetalleHtml(" + json.dumps(detalle) + ", 2)")
    assert "<summary>Excluidas (3)</summary>" in html
    assert "02/03/2026 · Persona A · 0100 · 8 h — ya registrada" in html
    assert "2 linea(s) marcadas estan ocultas por los filtros" in html
    assert _ejecutar_js(["esc", "fechaLegible", "horasTexto",
                         "excluidasDetalleHtml"],
                        "excluidasDetalleHtml([], 0)") == ""
