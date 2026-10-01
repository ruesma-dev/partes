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

import re
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
