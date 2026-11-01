# tests/test_f050_empresa.py
"""F-050 · la empresa de la persona a la vista (R23-R26, DA11): columna
«Empresa» con su filtro en «Por persona» y empresa en la cabecera de
`/trabajadores/{clave}`, con la regla de «Por obra» (F-033) sobre la base
`partes`, sin Sigrid ni consultas nuevas.

SQLite en memoria (`tests/dobles.py`) y TestClient. Ni red ni PostgreSQL.
Datos SINTETICOS.
"""
from __future__ import annotations

from html.parser import HTMLParser
from typing import ClassVar

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from sqlalchemy import event
from tests.dobles import FabricaSesionSqlite
from tests.test_f050_vistas import _doc, _reg

RUESMA, PORSAN = 1, 28


def _escenario(fabrica) -> None:
    with fabrica.create_session() as s:
        # E10: la misma persona en Ruesma (ficha 81, recurso 8101) y en
        # Porsan (ficha 82, recurso 8201); y un homonimo sin empresa
        # deducible (8301, solo en un parte manual).
        _doc(s, "d-r", 50, empresa=RUESMA)
        _doc(s, "d-p", 51, fecha="2026-03-03", empresa=PORSAN)
        _doc(s, "d-m", 52, fecha="2026-03-04")            # manual: sin empresa
        # Sembradas al reves del orden esperado (R26 no es el de llegada).
        _reg(s, "d-m", 52, 0, fecha="2026-03-04", empleado_line_no=1,
             empleado_reside=8301, recurso_ide=8301,
             empleado_match_method="recurso_manual",
             empleado_nombre="Persona Diez",
             trabajador_nombre_leido="Persona Diez")
        _reg(s, "d-p", 51, 0, fecha="2026-03-03", empleado_line_no=1,
             empleado_ide=82, recurso_ide=8201, empleado_nombre="Persona Diez",
             trabajador_nombre_leido="Persona Diez")
        _reg(s, "d-r", 50, 0, empleado_line_no=1, empleado_ide=81,
             recurso_ide=8101, empleado_nombre="Persona Diez",
             trabajador_nombre_leido="Persona Diez")
        # Deducida: rec-7002 solo en un parte manual; su recurso sale en un
        # parte de Porsan en una linea sin casar (por eso no es su fila).
        _reg(s, "d-m", 52, 1, fecha="2026-03-04", empleado_line_no=2,
             empleado_reside=7002, recurso_ide=7002,
             empleado_match_method="recurso_manual",
             empleado_nombre="Siete Dos", trabajador_nombre_leido="Siete Dos")
        _reg(s, "d-p", 51, 1, fecha="2026-03-03", empleado_line_no=2,
             recurso_ide=7002, empleado_match_method="nombre_sin_dni",
             trabajador_nombre_leido="S. Dos")
        # Sin casar en partes de las dos empresas.
        _reg(s, "d-r", 50, 1, empleado_line_no=2,
             trabajador_nombre_leido="Pepe Perez")
        _reg(s, "d-p", 51, 2, fecha="2026-03-03", empleado_line_no=3,
             trabajador_nombre_leido="PEPE PÉREZ")
        # En la papelera, en un parte de Ruesma: no da empresa al 8301.
        _reg(s, "d-r", 50, 2, empleado_line_no=3, recurso_ide=8301,
             empleado_match_method="recurso_dni", deleted_at_utc="x")
        s.commit()


@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    _escenario(fabrica)
    return ParteReviewRepository(fabrica)


def _fila(repo, clave):
    (fila,) = [w for w in repo.list_workers() if w.worker_key == clave]
    return fila


# ===================================================================== #
# R23 · columna «Empresa» de «Por persona» (repositorio)
# ===================================================================== #

@pytest.mark.parametrize("clave,empresas,texto", [
    ("rec-8101", [RUESMA], "Ruesma"),
    ("rec-8201", [PORSAN], "Porsan"),
    ("rec-7002", [PORSAN], "Porsan"),          # deducida por su recurso
    ("rec-8301", [], "—"),                     # R25
    ("nom-PEPE_PEREZ", [RUESMA, PORSAN], "Ruesma / Porsan"),
    ("nom-S._DOS", [PORSAN], "Porsan"),
])
def test_f050_r23_r25_empresa_de_cada_fila(repo, clave, empresas,
                                           texto) -> None:
    fila = _fila(repo, clave)
    assert (fila.empresas, fila.empresa_texto) == (empresas, texto)


def test_f050_r26_homonimos_por_empresa_y_sin_empresa_detras(repo) -> None:
    claves = [w.worker_key for w in repo.list_workers()
              if w.nombre == "Persona Diez"]
    assert claves == ["rec-8101", "rec-8201", "rec-8301"]


def test_f050_r26_casados_delante_y_por_nombre(repo) -> None:
    claves = [w.worker_key for w in repo.list_workers()]
    assert claves == ["rec-8101", "rec-8201", "rec-8301", "rec-7002",
                      "nom-PEPE_PEREZ", "nom-S._DOS"]


# ===================================================================== #
# R24 · empresa del detalle (repositorio)
# ===================================================================== #

@pytest.mark.parametrize("clave,empresas,texto", [
    ("rec-8101", [RUESMA], "Ruesma"),
    ("rec-8201", [PORSAN], "Porsan"),
    ("rec-7002", [PORSAN], "Porsan"),
    ("rec-8301", [], "—"),
    ("nom-PEPE_PEREZ", [RUESMA, PORSAN], "Ruesma / Porsan"),
])
def test_f050_r24_empresa_del_detalle(repo, clave, empresas, texto) -> None:
    det = repo.get_worker(clave)
    assert (det.empresas, det.empresa_texto) == (empresas, texto)


# ===================================================================== #
# R26 · sin consultas nuevas
# ===================================================================== #

def _consultas(fabrica, funcion) -> int:
    n = [0]

    def _contar(*_a, **_k) -> None:
        n[0] += 1

    event.listen(fabrica.engine, "before_cursor_execute", _contar)
    try:
        funcion()
    finally:
        event.remove(fabrica.engine, "before_cursor_execute", _contar)
    return n[0]


def test_f050_r26_sin_consultas_nuevas() -> None:
    """Las mismas dos sentencias de antes (lineas + documentos por
    `selectinload`): la empresa sale de lo ya cargado."""
    fabrica = FabricaSesionSqlite()
    _escenario(fabrica)
    repo = ParteReviewRepository(fabrica)
    assert _consultas(fabrica, repo.list_workers) == 2
    assert _consultas(fabrica, lambda: repo.get_worker("rec-8101")) == 2


# ===================================================================== #
# Plantillas (R23-R25) y sin Sigrid (R26)
# ===================================================================== #

class _Tabla(HTMLParser):
    """Filas de la tabla del listado: texto de cada celda, si lleva
    filtro y el primer enlace de la fila."""

    def __init__(self) -> None:
        super().__init__()
        self.filas: list[dict] = []
        self._celda: dict | None = None

    def handle_starttag(self, tag, attrs) -> None:
        a = dict(attrs)
        if tag == "tr":
            self.filas.append({"celdas": [], "href": None})
        elif tag in ("th", "td") and self.filas:
            self._celda = {"texto": "", "filtro": False,
                           "placeholder": None}
            self.filas[-1]["celdas"].append(self._celda)
        elif tag == "input" and self._celda is not None \
                and "col-filter" in (a.get("class") or "").split():
            self._celda["filtro"] = True
            self._celda["placeholder"] = a.get("placeholder")
        elif tag == "a" and self.filas and self.filas[-1]["href"] is None:
            self.filas[-1]["href"] = a.get("href")

    def handle_endtag(self, tag) -> None:
        if tag in ("th", "td") and self._celda is not None:
            self._celda["texto"] = " ".join(self._celda["texto"].split())
            self._celda = None

    def handle_data(self, data) -> None:
        if self._celda is not None:
            self._celda["texto"] += data


class SigridQueFalla:
    """Doble de `SigridLookupClient`: cualquier llamada falla y se apunta."""

    llamadas: ClassVar[list[str]] = []

    def __init__(self, **_kw) -> None:
        pass

    def __getattr__(self, nombre):
        def _falla(*_a, **_k):
            SigridQueFalla.llamadas.append(nombre)
            raise AssertionError(f"F-050 no debe llamar a Sigrid: {nombre}")
        return _falla


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "SIGRID_API_BASE_URL": "http://sigrid.interno",
                         "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
                         "SIGRID_API_DATABASE": "ruesma_rep"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)
    monkeypatch.setattr(app_mod, "SigridLookupClient", SigridQueFalla)
    SigridQueFalla.llamadas = []
    fabrica = FabricaSesionSqlite()
    _escenario(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app)


def test_f050_r23_columna_y_filtro_alineados(portal) -> None:
    r = portal.get("/trabajadores")
    assert r.status_code == 200
    p = _Tabla()
    p.feed(r.text)
    cabecera, filtros, *cuerpo = p.filas
    titulos = [c["texto"] for c in cabecera["celdas"]]
    assert titulos[:2] == ["Trabajador", "Empresa"]
    assert len(filtros["celdas"]) == len(cabecera["celdas"])
    assert filtros["celdas"][1]["placeholder"] == "Filtrar empresa…"
    for fila in cuerpo:
        assert len(fila["celdas"]) == len(cabecera["celdas"])
    empresa = {f["href"]: f["celdas"][1]["texto"] for f in cuerpo}
    assert empresa == {
        "/trabajadores/rec-8101": "Ruesma",
        "/trabajadores/rec-8201": "Porsan",
        "/trabajadores/rec-8301": "—",
        "/trabajadores/rec-7002": "Porsan",
        "/trabajadores/nom-PEPE_PEREZ": "Ruesma / Porsan",
        "/trabajadores/nom-S._DOS": "Porsan",
    }
    assert SigridQueFalla.llamadas == []


def _cabecera(html: str) -> str:
    ini = html.index('<div class="page-header">')
    fin = html.index('<div class="header-actions">', ini)
    return " ".join(html[ini:fin].split())


@pytest.mark.parametrize("clave,esperada,ausentes", [
    ("rec-8101", "· Ruesma", ["Porsan"]),
    ("rec-8201", "· Porsan", ["Ruesma"]),
    ("nom-PEPE_PEREZ", "· Ruesma / Porsan", []),
])
def test_f050_r24_cabecera_con_su_empresa(portal, clave, esperada,
                                          ausentes) -> None:
    r = portal.get(f"/trabajadores/{clave}")
    assert r.status_code == 200
    cab = _cabecera(r.text)
    assert esperada in cab
    for otra in ausentes:
        assert otra not in cab


def test_f050_r25_cabecera_sin_empresa_no_la_pinta(portal) -> None:
    cab = _cabecera(portal.get("/trabajadores/rec-8301").text)
    for texto in ("Ruesma", "Porsan", "—", "Empresa"):
        assert texto not in cab
