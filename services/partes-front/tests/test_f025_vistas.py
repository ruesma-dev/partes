# tests/test_f025_vistas.py
"""F-025 · el conflicto se ve en las vistas de obra y de trabajador
(R15-R19), no se rechaza ninguna edicion (R20) y sin tabla todo sigue
como antes (R23).

Sin red ni PostgreSQL: SQLite en memoria con el ORM, `TestClient` sobre
el HTML renderizado y, con `node` instalado, las funciones puras de
`static/app.js`. Personas, DNIs y obras SINTETICOS.
"""
from __future__ import annotations

import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from jinja2 import Environment, FileSystemLoader
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import DNI_B, OBRA_20, sembrar
from tests.test_f025_deteccion import TABLA

MARZO = "2026-03"
RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
APP_JS = RAIZ_SERVICIO / "static" / "app.js"
STYLES = RAIZ_SERVICIO / "static" / "styles.css"
MOTIVO_M = ("Maternidad/Paternidad (M) es de día completo y ese día hay 9 h "
            "de trabajo: deja solo una de las dos")


def _escenario(fabrica) -> dict[str, list[int]]:
    """Persona A (emp-77): dia 02 con M en la obra 20 y horas en la 10
    (bloqueo); dia 03 con FJ y 2 h extra en la 10 (aviso); dia 04 normal.
    Persona B (emp-88): dia 02 normal en la obra 10."""
    return {
        "inc_m": sembrar(fabrica, [{"inc": "M"}], doc="v-m", obra=OBRA_20),
        "bloq": sembrar(fabrica, [{"horas": 8.0},
                                  {"tipo": "extra", "horas": 1.0}],
                        doc="v-bloq"),
        "aviso": sembrar(fabrica, [{"inc": "FJ"}, {"horas": 6.0},
                                   {"tipo": "extra", "horas": 2.0}],
                         doc="v-aviso", fecha="2026-03-03"),
        "libre": sembrar(fabrica, [{"horas": 8.0}], doc="v-libre",
                         fecha="2026-03-04"),
        "otra": sembrar(fabrica, [{"horas": 8.0}], doc="v-otra", dni=DNI_B,
                        empleado_ide=88, nombre="Persona B"),
    }


def _repo():
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    return ParteReviewRepository(fabrica), fabrica, ids


def _celda(detalle, worker_key: str, dia: str):
    fila = next(r for r in detalle.rows if r.worker_key == worker_key)
    return next(c for c in fila.cells if c.date_iso == dia)


def _niveles(registros) -> dict[int, str | None]:
    return {v.id: v.incompat_nivel for v in registros}


# ===================================================================== #
# T6 · repositorio de las vistas
# ===================================================================== #

def test_f025_r15_repo_celdas_de_la_matriz_de_obra() -> None:
    repo, _f, _ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    bloq = _celda(det, "emp-77", "2026-03-02")
    assert bloq.incompat_nivel == "bloqueo"
    assert "Maternidad/Paternidad (M) es de día completo" in \
        bloq.incompat_motivo
    aviso = _celda(det, "emp-77", "2026-03-03")
    assert aviso.incompat_nivel == "aviso"
    assert "(FJ) y 2 h extra" in aviso.incompat_motivo
    for wk, dia in (("emp-77", "2026-03-04"), ("emp-88", "2026-03-02"),
                    ("emp-77", "2026-03-05")):
        celda = _celda(det, wk, dia)
        assert (celda.incompat_nivel, celda.incompat_motivo) == (None, None)


def test_f025_r18_repo_la_incidencia_en_otra_obra_marca_las_dos() -> None:
    repo, _f, ids = _repo()
    det20 = repo.get_obra("obr-20", period_key=MARZO, incidencias=TABLA)
    assert _celda(det20, "emp-77", "2026-03-02").incompat_nivel == "bloqueo"
    assert _niveles(det20.registros) == {ids["inc_m"][0]: "bloqueo"}
    det10 = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    niveles = _niveles(det10.registros)
    assert [niveles[i] for i in ids["bloq"]] == ["bloqueo", "bloqueo"]


def test_f025_r17_repo_lineas_de_la_vista_de_obra() -> None:
    repo, _f, ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    niveles = _niveles(det.registros)
    assert [niveles[i] for i in ids["aviso"]] == ["aviso"] * 3
    assert niveles[ids["libre"][0]] is None
    assert niveles[ids["otra"][0]] is None
    motivos = {v.id: v.incompat_motivo for v in det.registros}
    assert "(M)" in motivos[ids["bloq"][0]]
    assert motivos[ids["libre"][0]] is None


def test_f025_r17_r18_repo_lineas_de_la_vista_de_trabajador() -> None:
    repo, _f, ids = _repo()
    det = repo.get_worker("emp-77", incidencias=TABLA)
    niveles = _niveles(det.registros)
    assert [niveles[i] for i in ids["inc_m"] + ids["bloq"]] == \
        ["bloqueo"] * 3
    assert [niveles[i] for i in ids["aviso"]] == ["aviso"] * 3
    assert niveles[ids["libre"][0]] is None
    otra = repo.get_worker("emp-88", incidencias=TABLA)
    assert _niveles(otra.registros) == {ids["otra"][0]: None}


def test_f025_r23_repo_vistas_sin_tabla_como_antes() -> None:
    repo, _f, _ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO)
    assert {(c.incompat_nivel, c.incompat_motivo)
            for r in det.rows for c in r.cells} == {(None, None)}
    assert {v.incompat_nivel for v in det.registros} == {None}
    assert {v.incompat_nivel
            for v in repo.get_worker("emp-77").registros} == {None}


# ===================================================================== #
# T7 · plantillas y CSS (HTML renderizado)
# ===================================================================== #

class _Etiquetas(HTMLParser):
    """Etiquetas de apertura con sus atributos, y la linea de la tabla
    (`tr[data-registro-id]`) en la que esta cada una."""

    def __init__(self) -> None:
        super().__init__()
        self.etiquetas: list[tuple[str, dict, int | None]] = []
        self._fila: int | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            rid = a.get("data-registro-id")
            self._fila = int(rid) if rid else None
        self.etiquetas.append((tag, a, self._fila))

    def handle_endtag(self, tag):
        if tag == "tr":
            self._fila = None


def _etiquetas(html: str) -> list[tuple[str, dict, int | None]]:
    p = _Etiquetas()
    p.feed(html)
    return p.etiquetas


def _clases(a: dict) -> set[str]:
    return set((a.get("class") or "").split())


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), ids


def _celdas_obra(html: str) -> dict[tuple[str, str], dict]:
    return {(a["data-trabajador"], a["data-fecha"]): a
            for t, a, _f in _etiquetas(html)
            if t == "td" and "mx-cell" in _clases(a) and "data-fecha" in a}


def _insignias(html: str) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for t, a, fila in _etiquetas(html):
        if t == "span" and fila is not None and "incompat" in _clases(a):
            out.setdefault(fila, []).append(a)
    return out


def test_f025_r15_html_celdas_de_la_matriz(portal) -> None:
    cliente, _ids = portal
    html = cliente.get(f"/obras/obr-10?period={MARZO}").text
    celdas = _celdas_obra(html)
    bloq = celdas[("Persona A", "2026-03-02")]
    assert "mx-incompat" in _clases(bloq)
    assert "mx-incompat-aviso" not in _clases(bloq)
    assert bloq["title"] == MOTIVO_M
    aviso = celdas[("Persona A", "2026-03-03")]
    assert "mx-incompat-aviso" in _clases(aviso)
    assert "mx-incompat" not in _clases(aviso)
    assert "(FJ) y 2 h extra" in aviso["title"]
    for clave in (("Persona A", "2026-03-04"), ("Persona B", "2026-03-02")):
        assert not _clases(celdas[clave]) & {"mx-incompat",
                                             "mx-incompat-aviso"}
        assert "title" not in celdas[clave]


def test_f025_r15_html_el_title_convive_con_el_del_visor(portal,
                                                         monkeypatch) -> None:
    cliente, _ids = portal
    cliente.app.state.settings.graph_key = "irrelevante"   # visor activo
    with cliente.app.state.repository._session_factory.create_session() as s:
        from infrastructure.database.orm_models import ParteDocumentOrm
        doc = s.get(ParteDocumentOrm, "v-bloq")
        doc.sharepoint_drive_id, doc.sharepoint_item_id = "d", "i"
        s.commit()
    html = cliente.get(f"/obras/obr-10?period={MARZO}").text
    bloq = _celdas_obra(html)[("Persona A", "2026-03-02")]
    assert bloq["title"] == MOTIVO_M + " · Ver parte del 2026-03-02"
    assert html.count('title="Ver parte del 2026-03-02"') == 0


def test_f025_r18_html_la_obra_de_la_incidencia_tambien(portal) -> None:
    cliente, _ids = portal
    html = cliente.get(f"/obras/obr-20?period={MARZO}").text
    celda = _celdas_obra(html)[("Persona A", "2026-03-02")]
    assert "mx-incompat" in _clases(celda)
    assert celda["title"] == MOTIVO_M


def test_f025_r17_html_insignias_en_las_lineas_de_obra(portal) -> None:
    cliente, ids = portal
    insignias = _insignias(cliente.get(f"/obras/obr-10?period={MARZO}").text)
    assert set(insignias) == set(ids["bloq"] + ids["aviso"])
    for rid in ids["bloq"]:
        (b,) = insignias[rid]
        assert "incompat-bloqueo" in _clases(b) and b["title"] == MOTIVO_M
    for rid in ids["aviso"]:
        (b,) = insignias[rid]
        assert "incompat-aviso" in _clases(b) and "(FJ)" in b["title"]


def test_f025_r16_r17_html_vista_de_trabajador(portal) -> None:
    cliente, ids = portal
    html = cliente.get(f"/trabajadores/emp-77?period={MARZO}").text
    dias = {a["data-fecha"]: a for t, a, _f in _etiquetas(html)
            if t == "div" and "cal-day" in _clases(a) and "data-fecha" in a}
    assert "cal-incompat" in _clases(dias["2026-03-02"])
    assert "cal-incompat-aviso" not in _clases(dias["2026-03-02"])
    assert "cal-incompat-aviso" in _clases(dias["2026-03-03"])
    assert not _clases(dias["2026-03-04"]) & {"cal-incompat",
                                              "cal-incompat-aviso"}
    marcas = [a for t, a, _f in _etiquetas(html)
              if t == "span" and "cal-incompat-mark" in _clases(a)]
    assert marcas[0]["title"] == MOTIVO_M
    assert len(marcas) == 2 and "(FJ)" in marcas[1]["title"]
    insignias = _insignias(html)
    assert set(insignias) == set(ids["inc_m"] + ids["bloq"] + ids["aviso"])


def test_f025_r16_html_sin_conflictos_no_hay_marcas(portal) -> None:
    cliente, _ids = portal
    html = cliente.get(f"/trabajadores/emp-88?period={MARZO}").text
    assert "cal-incompat" not in html
    assert _insignias(html) == {}


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f025_r15_r17_las_plantillas_parsean(plantilla) -> None:
    entorno = Environment(loader=FileSystemLoader(
        str(RAIZ_SERVICIO / "templates")))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])


def test_f025_r15_r16_el_css_define_las_clases() -> None:
    css = STYLES.read_text(encoding="utf-8")
    for selector in ("td.mx-cell.mx-incompat", "td.mx-cell.mx-incompat-aviso",
                     ".cal-day.cal-incompat", ".cal-day.cal-incompat-aviso",
                     ".badge.incompat", ".cal-incompat-mark"):
        assert selector + " " in css or selector + "{" in css \
            or selector + "," in css, selector


# ===================================================================== #
# T8 · app.js: el modal (R19)
# ===================================================================== #

from tests.test_f022_vistas_seleccion import (
    _ejecutar_js,
    _funcion,
    _js,
)

NODE = shutil.which("node")
sin_node = pytest.mark.skipif(NODE is None, reason="node no instalado")


def test_f025_r19_js_cableado_en_el_modal() -> None:
    js = _js()
    aprobar = _funcion(js, "aprobar")
    assert "incompatiblesHtml(excl.incompatible)" in aprobar
    # Fuera del desplegable de excluidas: antes de pintarlo.
    assert aprobar.index("incompatiblesHtml(") < aprobar.index(
        "excluidasDetalleHtml(")
    # Los avisos de todas las obras, juntos y fuera del pliegue (no en
    # `grupoHtml`: los tests de F-022 la ejecutan con una lista cerrada de
    # funciones).
    assert "g.avisos_incidencia" in aprobar
    assert "avisosIncidenciaHtml(avisosIncid)" in aprobar
    assert aprobar.index("avisosIncidenciaHtml(") < aprobar.index(
        "grupoHtml(g, plegar)")
    for nombre in ("incompatiblesHtml", "avisosIncidenciaHtml"):
        cuerpo = _funcion(js, nombre)
        assert "innerHTML" not in cuerpo


@sin_node
@pytest.mark.parametrize("n", [0, None, "", -1])
def test_f025_r19_js_sin_incompatibles_no_pinta_nada(n) -> None:
    assert _ejecutar_js(["esc", "incompatiblesHtml"],
                        f"incompatiblesHtml({json.dumps(n)})") == ""


@sin_node
def test_f025_r19_js_aviso_de_incompatibles_visible() -> None:
    html = _ejecutar_js(["esc", "incompatiblesHtml"], "incompatiblesHtml(3)")
    assert "ap-incompat" in html
    assert re.sub(r"<[^>]+>", "", html) == (
        "3 línea(s) no se registran: tienen una incidencia de día completo "
        "y horas el mismo día. Están en «Excluidas»; corrige el día y "
        "vuelve a aprobar.")
    # Lo que no es un numero no se pinta (ni se cuela como HTML).
    assert _ejecutar_js(["esc", "incompatiblesHtml"],
                        'incompatiblesHtml("<b>2</b>")') == ""


@sin_node
def test_f025_r19_js_avisos_de_incidencia_escapados() -> None:
    avisos = [{"registro_id": 1, "fecha": "2026-03-03",
               "nombre": "<script>x</script>", "horas": 2,
               "motivo": "Permiso (FJ) & <i>2</i> h extra"}]
    html = _ejecutar_js(["esc", "num", "avisosIncidenciaHtml"],
                        f"avisosIncidenciaHtml({json.dumps(avisos)})")
    assert "ap-incid-avisos" in html
    assert "<script>" not in html and "&lt;script&gt;x" in html
    assert "<i>" not in html and "&amp; &lt;i&gt;2" in html
    assert "2026-03-03" in html and "2 h" in html
    assert "<strong>1</strong>" in html


@sin_node
@pytest.mark.parametrize("avisos", [[], None])
def test_f025_r19_js_sin_avisos_no_pinta_nada(avisos) -> None:
    assert _ejecutar_js(["esc", "num", "avisosIncidenciaHtml"],
                        f"avisosIncidenciaHtml({json.dumps(avisos)})") == ""


# ===================================================================== #
# T9 · R20: ninguna creacion ni edicion se rechaza por el conflicto
# ===================================================================== #

@pytest.fixture
def portal_sigrid(monkeypatch):
    """Como `portal`, con el catalogo de tipos de hora ENCENDIDO (doble de
    F-004): sin el, cambiar el codigo responde 503 antes de llegar."""
    from interface_adapters.web import app as app_mod
    from tests.test_f004_endpoints_congelados import SigridLookupClientFake
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "SIGRID_API_BASE_URL": "http://sigrid.interno",
                         "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
                         "SIGRID_API_DATABASE": "ruesma_rep"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)
    monkeypatch.setattr(app_mod, "SigridLookupClient", SigridLookupClientFake)
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), ids


def test_f025_r20_crear_y_editar_un_dia_en_conflicto_sigue_igual(
        portal_sigrid) -> None:
    cliente, ids = portal_sigrid
    base = {"empleado_nombre": "Persona A", "empleado_ide": 77,
            "empleado_dni": "12345678Z", "obra_codigo": "0100",
            "obra_ide": 10}
    # «+ Nuevo»: una incidencia de dia completo sobre un dia con horas, y
    # horas sobre el dia que ya tiene la M.
    r = cliente.post("/api/partes/nuevo", json=dict(
        base, dias=["2026-03-04"], incidencia_codigo="V",
        horas_ordinaria=0, horas_extra=0))
    assert (r.status_code, r.json()["ok"]) == (200, True)
    r = cliente.post("/api/partes/nuevo", json=dict(
        base, dias=["2026-03-02"], horas_ordinaria=4, horas_extra=0))
    assert (r.status_code, r.json()["ok"]) == (200, True)
    # Editar horas, crear la extra y cambiar el codigo de una linea en
    # bloqueo; mover la fecha de un parte libre al dia en conflicto.
    linea = ids["bloq"][0]
    assert cliente.patch(f"/api/registros/{linea}",
                         json={"horas": 5.0}).status_code == 200
    r = cliente.post(f"/api/registros/{linea}/extra", json={"horas": 2.0})
    assert (r.status_code, r.json()["ok"]) == (200, True)
    assert cliente.patch(f"/api/registros/{linea}/hora",
                         json={"hora_ide": 2}).status_code == 200
    r = cliente.patch("/api/partes/v-libre/fecha", json={"fecha": "2026-03-02"})
    assert r.status_code == 200
    # Y el conflicto se sigue viendo (solo se marca, no se rechaza).
    html = cliente.get(f"/trabajadores/emp-77?period={MARZO}").text
    dias = {a["data-fecha"]: a for t, a, _f in _etiquetas(html)
            if t == "div" and "cal-day" in _clases(a) and "data-fecha" in a}
    assert "cal-incompat" in _clases(dias["2026-03-02"])
