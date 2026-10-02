# tests/test_f028_ancho_detalle.py
"""F-028 · detalle de obra y de trabajador a todo el ancho de la ventana.

El contenedor principal (`<main class="page-shell"><div class="container">`)
de `base.html` estaba topado a 1500 px en todas las paginas. Las vistas de
detalle de obra y de trabajador lo ensanchan con una clase extra
(`container--ancho`); los listados y la barra superior no cambian.

Se mira el HTML REAL que sirve la app (patron de `test_f022_vistas_seleccion`)
y el texto de `static/styles.css`. Sin red ni BBDD reales: SQLite en memoria
con datos SINTETICOS.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
STYLES = RAIZ_SERVICIO / "static" / "styles.css"

CLASE_ANCHA = "container--ancho"

URL_OBRA = "/obras/obr-10?period=2026-03&modo=natural"
URL_PERSONA = "/trabajadores/emp-77?period=2026-03&modo=natural"
URLS_DETALLE = [URL_OBRA, URL_PERSONA]
URLS_LISTADO = ["/obras", "/trabajadores", "/partes"]


@pytest.fixture
def cliente(monkeypatch) -> TestClient:
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests"}.items():
        monkeypatch.setenv(clave, valor)
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"estado": None}, {"estado": "registrado"}])
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app)


def _clases_contenedor_main(html: str) -> list[str]:
    m = re.search(r'<main class="page-shell">\s*<div class="([^"]*)">', html)
    assert m, "no se encuentra el contenedor del <main>"
    return m.group(1).split()


def _clases_contenedor_topbar(html: str) -> list[str]:
    m = re.search(r'<header class="topbar">\s*<div class="([^"]*)">', html)
    assert m, "no se encuentra el contenedor de la topbar"
    return m.group(1).split()


def _regla(css: str, selector: str) -> str:
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert m, f"no hay regla para {selector}"
    return m.group(1)


# ===================================================================== #
# Acceptance 1 · los detalles llevan la clase ancha
# ===================================================================== #

@pytest.mark.parametrize("url", URLS_DETALLE)
def test_f028_r1_detalle_contenedor_main_con_clase_ancha(cliente,
                                                         url) -> None:
    respuesta = cliente.get(url)
    assert respuesta.status_code == 200
    clases = _clases_contenedor_main(respuesta.text)
    assert "container" in clases
    assert CLASE_ANCHA in clases


def test_f028_r1_css_clase_ancha_sin_tope() -> None:
    css = STYLES.read_text(encoding="utf-8")
    cuerpo = _regla(css, "." + CLASE_ANCHA)
    assert re.search(r"width:\s*calc\(100%\s*-\s*32px\)", cuerpo), cuerpo
    # Sin tope: ni min(1500px, ...) ni max-width.
    assert "1500px" not in cuerpo
    assert "min(" not in cuerpo
    assert "max-width" not in cuerpo


def test_f028_r1_css_clase_ancha_despues_de_container() -> None:
    # A igual especificidad gana la ultima regla: la ancha tiene que ir
    # despues de `.container` para pisar su `width`.
    css = STYLES.read_text(encoding="utf-8")
    pos_container = re.search(r"\.container\s*\{", css).start()
    pos_ancha = re.search(re.escape("." + CLASE_ANCHA) + r"\s*\{", css).start()
    assert pos_ancha > pos_container


# ===================================================================== #
# Acceptance 2 · los listados conservan el tope de 1500 px
# ===================================================================== #

@pytest.mark.parametrize("url", URLS_LISTADO)
def test_f028_r2_listado_contenedor_main_sin_clase_ancha(cliente,
                                                         url) -> None:
    respuesta = cliente.get(url)
    assert respuesta.status_code == 200
    assert _clases_contenedor_main(respuesta.text) == ["container"]


def test_f028_r2_css_container_conserva_tope_1500() -> None:
    css = STYLES.read_text(encoding="utf-8")
    cuerpo = _regla(css, ".container")
    assert re.search(r"width:\s*min\(1500px,\s*calc\(100%\s*-\s*32px\)\)",
                     cuerpo), cuerpo


# ===================================================================== #
# Acceptance 3 · la barra superior no cambia
# ===================================================================== #

@pytest.mark.parametrize("url", URLS_DETALLE + URLS_LISTADO)
def test_f028_r3_topbar_sin_cambios(cliente, url) -> None:
    html = cliente.get(url).text
    assert _clases_contenedor_topbar(html) == ["container", "topbar-inner"]
