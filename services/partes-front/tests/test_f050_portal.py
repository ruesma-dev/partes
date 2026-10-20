# tests/test_f050_portal.py
"""F-050 · portal: enlaces antiguos (R14, R15), alta desde la vista del
trabajador (R19) y el «Ver» de «Nuevo parte» (R20).

TestClient sobre `build_app` con SQLite en memoria (`tests/dobles.py`). Ni
red, ni Sigrid, ni PostgreSQL. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite
from tests.test_f050_vistas import _doc, _reg

O_A, O_B, O_C = 10, 20, 30


def _escenario(fabrica) -> dict[str, int]:
    ids: dict[str, int] = {}
    with fabrica.create_session() as s:
        # E1: dos leidos distintos del recurso 6001 (antes, dos `nom-`).
        _doc(s, "d-a", O_A)
        ids["ia"] = _reg(
            s, "d-a", O_A, 0, tipo="extra", horas=2.0, empleado_line_no=3,
            recurso_ide=6001, empleado_match_method="recurso_dni",
            trabajador_nombre_leido="Nombre Apellido")
        ids["manual"] = _reg(
            s, "d-a", O_A, 1, empleado_line_no=3, empleado_reside=6001,
            empleado_match_method="recurso_manual",
            empleado_nombre="APELLIDO NOMBRE",
            trabajador_nombre_leido="Nombre Apellido")
        # E2: ficha 77 con recurso 501 (antes `emp-77`); en otra fecha
        # mas reciente, sin ficha y del mismo recurso.
        ids["ficha"] = _reg(
            s, "d-a", O_A, 2, empleado_line_no=1, empleado_ide=77,
            recurso_ide=501, empleado_nombre="Persona Siete",
            trabajador_nombre_leido="Persona Siete")
        _doc(s, "d-b", O_B, fecha="2026-03-05")
        ids["sin_ficha"] = _reg(
            s, "d-b", O_B, 0, fecha="2026-03-05", empleado_line_no=1,
            recurso_ide=501, empleado_match_method="recurso_nombre",
            trabajador_nombre_leido="P. Siete")
        # Homonimos sin ficha casados con dos recursos (antes una `nom-`).
        ids["homo1"] = _reg(
            s, "d-b", O_B, 1, fecha="2026-03-05", empleado_line_no=2,
            recurso_ide=9101, empleado_match_method="recurso_dni",
            trabajador_nombre_leido="Juan Igual")
        ids["homo2"] = _reg(
            s, "d-b", O_B, 2, fecha="2026-03-05", empleado_line_no=3,
            recurso_ide=9102, empleado_match_method="recurso_dni",
            trabajador_nombre_leido="Juan Igual")
        # Una ficha (81) con dos recursos (antes una `emp-`).
        _doc(s, "d-c", O_C, fecha="2026-03-06")
        ids["f81_a"] = _reg(
            s, "d-c", O_C, 0, fecha="2026-03-06", empleado_line_no=1,
            empleado_ide=81, recurso_ide=8101)
        ids["f81_b"] = _reg(
            s, "d-c", O_C, 1, fecha="2026-03-06", empleado_line_no=2,
            empleado_ide=81, recurso_ide=8102)
        # Una ficha sin recurso (E12): su clave sigue siendo `emp-90`.
        ids["e12"] = _reg(
            s, "d-c", O_C, 2, fecha="2026-03-06", empleado_line_no=3,
            empleado_ide=90, trabajador_nombre_leido="Ficha Sola")
        # Sin casar: sigue siendo `nom-PEPE_PEREZ`.
        ids["sin_casar"] = _reg(
            s, "d-c", O_C, 3, fecha="2026-03-06", empleado_line_no=4,
            trabajador_nombre_leido="Pepe Perez")
        # Una ficha con el mismo leido que E1: con la regla anterior era
        # `emp-95`, no `nom-NOMBRE_APELLIDO`.
        ids["ficha_homo"] = _reg(
            s, "d-c", O_C, 4, fecha="2026-03-06", empleado_line_no=5,
            empleado_ide=95, recurso_ide=9501,
            trabajador_nombre_leido="Nombre Apellido")
        # En la papelera: no cuenta para redirigir.
        _reg(s, "d-c", O_C, 5, fecha="2026-03-06", empleado_line_no=6,
             empleado_ide=96, recurso_ide=9601, deleted_at_utc="2026-03-07")
        s.commit()
    return ids


@pytest.fixture
def repo_ids():
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    return ParteReviewRepository(fabrica), ids


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


# ===================================================================== #
# R14 · una clave antigua con destino unico redirige (307)
# ===================================================================== #

@pytest.mark.parametrize("antigua,destino", [
    ("nom-NOMBRE_APELLIDO", "rec-6001"),
    ("emp-77", "rec-501"),
])
def test_f050_r14_repo_destino_unico(repo_ids, antigua, destino) -> None:
    repo, _ids = repo_ids
    assert repo.clave_actual_de_clave_antigua(antigua) == destino


def test_f050_r14_repo_nom_solo_de_lineas_sin_ficha(repo_ids) -> None:
    """«Las lineas que darian esa clave con la regla anterior»: una linea
    con ficha daba `emp-`, asi que la ficha 95, con el mismo leido que E1,
    no es destino de `nom-NOMBRE_APELLIDO` (si no, habria dos: R15)."""
    repo, _ids = repo_ids
    assert repo.clave_actual_de_clave_antigua(
        "nom-NOMBRE_APELLIDO") == "rec-6001"
    assert repo.clave_actual_de_clave_antigua("emp-95") == "rec-9501"


@pytest.mark.parametrize("antigua,destino", [
    ("nom-NOMBRE_APELLIDO", "rec-6001"),
    ("emp-77", "rec-501"),
])
def test_f050_r14_get_redirige_307_conservando_la_query(
        portal, antigua, destino) -> None:
    cliente, _ids = portal
    r = cliente.get(f"/trabajadores/{antigua}?modo=natural&period=2026-03",
                    follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == \
        f"/trabajadores/{destino}?modo=natural&period=2026-03"


def test_f050_r14_sin_query_redirige_sin_interrogacion(portal) -> None:
    cliente, _ids = portal
    r = cliente.get("/trabajadores/emp-77", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (
        307, "/trabajadores/rec-501")


def test_f050_r14_el_destino_se_sirve(portal) -> None:
    cliente, _ids = portal
    r = cliente.get("/trabajadores/emp-77")
    assert r.status_code == 200
    assert str(r.url).endswith("/trabajadores/rec-501")


def test_f050_r14_las_claves_vigentes_no_redirigen(portal) -> None:
    cliente, _ids = portal
    for clave in ("emp-90", "nom-PEPE_PEREZ", "rec-501"):
        r = cliente.get(f"/trabajadores/{clave}", follow_redirects=False)
        assert r.status_code == 200, clave


# ===================================================================== #
# R15 · sin lineas o con varios destinos: 404
# ===================================================================== #

@pytest.mark.parametrize("antigua", [
    "nom-JUAN_IGUAL",   # homonimos: dos destinos
    "emp-81",           # una ficha con dos recursos: dos destinos
    "emp-999",          # ninguna linea
    "nom-NADIE",        # ninguna linea
    "emp-96",           # solo en la papelera
    "emp-abc",          # no es una ficha
    "rec-404",          # no es una clave antigua
    "sin-trabajador",
])
def test_f050_r15_404(portal, repo_ids, antigua) -> None:
    cliente, _ids = portal
    r = cliente.get(f"/trabajadores/{antigua}", follow_redirects=False)
    assert r.status_code == 404
    repo, _ids = repo_ids
    assert repo.clave_actual_de_clave_antigua(antigua) is None


def test_f050_r15_la_misma_clave_no_es_destino(repo_ids) -> None:
    """Si las lineas de la clave antigua siguen dando esa misma clave, no
    hay a donde redirigir (la vista ya las encuentra)."""
    repo, _ids = repo_ids
    assert repo.clave_actual_de_clave_antigua("emp-90") is None
    assert repo.clave_actual_de_clave_antigua("nom-PEPE_PEREZ") is None
