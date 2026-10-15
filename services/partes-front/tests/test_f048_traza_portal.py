# tests/test_f048_traza_portal.py
"""F-048 · la traza «incl. X h extra leídas» en el portal (R21-R23).

sv3 suma las extras leidas > 0 a la ordinaria de su fila y guarda lo leido
como extra en `parte_registros.horas_extra_leidas`. El portal lo ENSENA
(vistas de parte, obra y trabajador) con una etiqueta `tag-auto` (sin CSS
nuevo) y nunca lo cambia: las ediciones de horas, tipo y codigo de hora no
tocan la columna (DA7).

Sin red ni PostgreSQL: SQLite en memoria con el ORM y `TestClient` sobre el
HTML renderizado. Personas, DNIs y obras SINTETICOS.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    RegistroView,
)
from interface_adapters.web.app import build_app
from jinja2 import Environment, FileSystemLoader
from tests.dobles import FabricaSesionSqlite, sembrar_parte

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLAS = ("parte_detail.html", "obra_detail.html",
              "trabajador_detail.html")
MARZO = "2026-03"
URLS = ("/partes/doc-f048", f"/obras/obr-10?period={MARZO}",
        f"/trabajadores/emp-77?period={MARZO}")


def _sembrar(fabrica, leidas: list[float | None]) -> list[int]:
    """Un parte con una linea por valor de `horas_extra_leidas`."""
    ids = sembrar_parte(fabrica, [{"horas": 8.0} for _ in leidas],
                        document_id="doc-f048")
    with fabrica.create_session() as s:
        for rid, valor in zip(ids, leidas):
            s.get(ParteRegistroOrm, rid).horas_extra_leidas = valor
        s.commit()
    return ids


class _Etiquetas(HTMLParser):
    """Los <span> con su texto y atributos."""

    def __init__(self) -> None:
        super().__init__()
        self.spans: list[tuple[dict, str]] = []
        self._abierto: dict | None = None
        self._texto: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            self._abierto = dict(attrs)
            self._texto = []

    def handle_data(self, data):
        if self._abierto is not None:
            self._texto.append(data)

    def handle_endtag(self, tag):
        if tag == "span" and self._abierto is not None:
            self.spans.append((self._abierto, "".join(self._texto)))
            self._abierto = None


def _leidas(html: str) -> list[tuple[dict, str]]:
    p = _Etiquetas()
    p.feed(html)
    return [(a, t) for a, t in p.spans if "extra leídas" in t]


@pytest.fixture
def portal(monkeypatch):
    for clave in ("PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.setenv(clave, "irrelevante-en-tests")
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)

    def montar(leidas):
        fabrica = FabricaSesionSqlite()
        ids = _sembrar(fabrica, leidas)
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app), ids

    return montar


# ------------------------------ R22 · HTML ------------------------------ #

def test_f048_r22_las_tres_plantillas_parsean() -> None:
    entorno = Environment(loader=FileSystemLoader(str(RAIZ / "templates")))
    for nombre in PLANTILLAS:
        entorno.parse(entorno.loader.get_source(entorno, nombre)[0])


@pytest.mark.parametrize("url", URLS, ids=["parte", "obra", "trabajador"])
def test_f048_r22_etiqueta_solo_con_extras_leidas(portal, url) -> None:
    cliente, _ids = portal([5.0, None, 0.0, 2.5])
    respuesta = cliente.get(url)
    assert respuesta.status_code == 200
    etiquetas = _leidas(respuesta.text)
    assert [t for _a, t in etiquetas] == [
        "incl. 5 h extra leídas", "incl. 2,50 h extra leídas"]
    for attrs, _t in etiquetas:
        assert attrs["class"] == "tag-auto"
        assert "La IA leyó estas horas como extra" in attrs["title"]
        assert "jornada del día" in attrs["title"]
        assert "(F-048)" in attrs["title"]


@pytest.mark.parametrize("url", URLS, ids=["parte", "obra", "trabajador"])
def test_f048_r22_sin_columna_nada_nuevo(portal, url) -> None:
    cliente, _ids = portal([None, 0.0])
    html = cliente.get(url).text
    assert "extra leídas" not in html
    assert "F-048" not in html


def test_f048_r22_sin_css_nuevo() -> None:
    css = (RAIZ / "static" / "styles.css").read_text(encoding="utf-8")
    assert ".tag-auto {" in css
    assert "extra-leidas" not in css and "extra_leidas" not in css


def test_f048_r22_la_vista_lleva_el_dato() -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, [5.0, None])
    detalle = ParteReviewRepository(fabrica).get_parte("doc-f048")
    vistas = [r for emp in detalle.empleados for r in emp.registros]
    assert [v.horas_extra_leidas for v in vistas] == [5.0, None]


def test_f048_r22_registro_view_nula_por_defecto() -> None:
    campos = RegistroView.__dataclass_fields__
    assert campos["horas_extra_leidas"].default is None


# ------------------------------ R23 · edicion --------------------------- #

def _leida(fabrica, rid: int):
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        return reg.horas_extra_leidas, reg.horas, reg.tipo_hora


def test_f048_r23_editar_horas_y_tipo_no_la_toca() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = _sembrar(fabrica, [5.0])
    repo = ParteReviewRepository(fabrica)
    assert repo.update_registro(registro_id=rid, horas=6.5)
    assert _leida(fabrica, rid) == (5.0, 6.5, "normal")
    assert repo.update_registro(registro_id=rid, tipo_hora="extra")
    assert _leida(fabrica, rid) == (5.0, 6.5, "extra")


def test_f048_r23_cambiar_codigo_de_hora_no_la_toca() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = _sembrar(fabrica, [5.0])
    assert ParteReviewRepository(fabrica).set_registro_hora(
        registro_id=rid, hora_ide=2, hora_codigo="HE01",
        hora_descripcion="Hora extra", hora_ext=1, hora_precio_coste=None,
        hora_precio_nomina=None)
    assert _leida(fabrica, rid) == (5.0, 8.0, "extra")
