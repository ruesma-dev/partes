# tests/test_f040_alias.py
"""F-040 · R16-R19: el portal aprende el alias contra el RECURSO (sv4).

  - R16: elegir un recurso sin DNI deja la linea segun `asignacion_de`:
    con ficha, su `ide` y `empleado_dni` NULL; sin ficha, `recurso_manual`,
    `empleado_dni` NULL y `empleado_reside` = el recurso.
  - R17: confirmar en Conciliar o reasignar con `recurso_ide` guarda el
    alias TAMBIEN sin ficha (`empleado_ide` o NULL, codigo, nombre, DNI o
    NULL y `recurso_ide`); por el camino de ficha (`ide` sin
    `recurso_ide`), como hoy con `recurso_ide` NULL.
  - R18: `upsert_empleado_alias` sin `empleado_ide` ni `recurso_ide` no
    escribe nada.
  - R19: el deshacer guarda y restaura `recurso_ide`; un snapshot anterior
    a F-040 (sin la clave) lo restaura a NULL.

Sin red ni PostgreSQL: Sigrid simulado y SQLite en memoria (los dobles de
`tests/test_f035_endpoints.py`). Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from infrastructure.database.orm_models import (
    EmpleadoAliasOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import RecursoOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f035_endpoints import (
    ENTORNO,
    LEIDO,
    RECURSOS,
    SIGRID,
    LookupFalso,
)

NORM = "tres solo recurso"
SIN_DNI_SIN_FICHA = RecursoOption(
    ide=904, codigo="MO/0004", nombre="CUATRO SIN DNI", dni=None, empresa=28)
SIN_DNI_CON_FICHA = RecursoOption(
    ide=905, codigo="MO/0005", nombre="CINCO RECURSO", dni=None, empresa=28,
    empleado_ide=15, empleado_codigo="E15", empleado_nombre="Cinco Ficha",
    empleado_dni=None)


class LookupF040(LookupFalso):
    def fetch_recursos_activos(self) -> list:
        return [*RECURSOS, SIN_DNI_SIN_FICHA, SIN_DNI_CON_FICHA]


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {**ENTORNO, **SIGRID}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupF040)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(
        fabrica, [{"leido": LEIDO}, {"leido": LEIDO, "tipo": "extra",
                                     "horas": 1.0}],
        empleado_ide=None, empleado_dni="", empleado_nombre=None)
    with fabrica.create_session() as s:
        for rid in ids:
            s.get(ParteRegistroOrm, rid).empleado_match_method = "none"
        s.commit()
    repo = ParteReviewRepository(fabrica)
    app = build_app(Settings(_env_file=None), repository=repo)
    return TestClient(app), fabrica, ids, repo


def _filas(fabrica, ids) -> list[tuple]:
    with fabrica.create_session() as s:
        return [
            (r.empleado_ide, r.empleado_codigo, r.empleado_nombre,
             r.empleado_dni, r.empleado_reside, r.empleado_match_method)
            for r in (s.get(ParteRegistroOrm, i) for i in ids)
        ]


def _aliases(fabrica) -> list[tuple]:
    with fabrica.create_session() as s:
        return [(a.nombre_norm, a.empleado_ide, a.empleado_codigo,
                 a.empleado_nombre, a.empleado_dni, a.recurso_ide,
                 a.created_by)
                for a in s.query(EmpleadoAliasOrm).all()]


ALIAS_904 = (NORM, None, "MO/0004", "CUATRO SIN DNI", None, 904)
ALIAS_905 = (NORM, 15, "E15", "Cinco Ficha", None, 905)
ALIAS_903 = (NORM, None, "MO/0037", "TRES SOLO RECURSO", "00000003A", 903)
ALIAS_901 = (NORM, 11, "E11", "Uno Ficha", "1R", 901)
ALIAS_10 = (NORM, 10, "E10", "Diez Ficha", "00000010X", None)


# ===================== R16 + R17 · confirmar ============================ #

@pytest.mark.parametrize("recurso, fila, alias", [
    (904, (None, "MO/0004", "CUATRO SIN DNI", None, 904, "recurso_manual"),
     ALIAS_904),
    (905, (15, "E15", "Cinco Ficha", None, 905, "none"), ALIAS_905),
    (903, (None, "MO/0037", "TRES SOLO RECURSO", "00000003A", 903,
           "recurso_manual"), ALIAS_903),
    (901, (11, "E11", "Uno Ficha", "1R", 901, "none"), ALIAS_901),
])
def test_f040_r16_r17_confirmar_con_recurso_guarda_alias(
        portal, recurso, fila, alias) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "recurso_ide": recurso})
    assert r.status_code == 200, r.text
    assert (r.json()["ok"], r.json()["updated"], r.json()["alias_ok"]) == \
        (True, 2, True)
    assert _filas(fabrica, ids) == [fila, fila]
    assert _aliases(fabrica) == [(*alias, "conciliacion")]


def test_f040_r17_confirmar_por_ficha_como_hoy_recurso_ide_null(
        portal) -> None:
    cliente, fabrica, _, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "ide": 10})
    assert r.status_code == 200, r.text
    assert _aliases(fabrica) == [(*ALIAS_10, "conciliacion")]


def test_f040_r17_la_ficha_pisa_el_recurso_de_un_alias_previo(portal) -> None:
    cliente, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="MO/0004",
                               nombre="CUATRO SIN DNI", dni=None,
                               recurso_ide=904, created_by="x")
    cliente.post("/api/conciliacion/confirmar",
                 json={"nombre_leido": LEIDO, "ide": 10})
    assert _aliases(fabrica) == [(*ALIAS_10, "conciliacion")]


def test_f040_r17_alias_que_falla_no_tumba_el_casado(portal,
                                                     monkeypatch) -> None:
    cliente, fabrica, ids, repo = portal

    def _falla(**_kw):
        raise RuntimeError("caida")

    monkeypatch.setattr(repo, "upsert_empleado_alias", _falla)
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "recurso_ide": 904})
    assert (r.status_code, r.json()["alias_ok"]) == (200, False)
    assert _filas(fabrica, ids)[0][4] == 904


# ======================== R17 · reasignar =============================== #

@pytest.mark.parametrize("cuerpo", [
    {"nombre_leido": LEIDO},
    {"worker_key": "nom-TRES_SOLO_RECURSO"},
])
def test_f040_r17_reasignar_a_recurso_sin_dni_guarda_alias(
        portal, cuerpo) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={**cuerpo, "recurso_ide": 904})
    assert r.status_code == 200, r.text
    assert r.json()["alias_ok"] is True
    assert _filas(fabrica, ids)[0][3:] == (None, 904, "recurso_manual")
    assert _aliases(fabrica) == [(*ALIAS_904, "reasignacion")]


def test_f040_r17_reasignar_por_registro_registro_ids_sin_alias(
        portal) -> None:
    """Acotado a lineas concretas: no crea alias, como hoy."""
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"registro_ids": [ids[0]], "recurso_ide": 904})
    assert r.status_code == 200, r.text
    assert _aliases(fabrica) == []


def test_f040_r17_reasignar_por_ficha_recurso_ide_null(portal) -> None:
    cliente, fabrica, _, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"nombre_leido": LEIDO, "ide": 10})
    assert r.status_code == 200, r.text
    assert _aliases(fabrica) == [(*ALIAS_10, "reasignacion")]


# ================================ R18 =================================== #

def test_f040_r18_sin_ficha_ni_recurso_no_escribe(portal) -> None:
    _, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="X",
                               nombre="Y", dni=None, recurso_ide=None)
    assert _aliases(fabrica) == []


def test_f040_r18_no_pisa_un_alias_existente(portal) -> None:
    _, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="MO/0004",
                               nombre="CUATRO SIN DNI", dni=None,
                               recurso_ide=904, created_by="conciliacion")
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="X",
                               nombre="Y", dni=None, recurso_ide=None)
    assert _aliases(fabrica) == [(*ALIAS_904, "conciliacion")]


def test_f040_r18_recurso_ide_por_defecto_none(portal) -> None:
    """Quien llama como antes de F-040 (solo `ide`) guarda `recurso_ide`
    NULL."""
    _, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=10, codigo="E10",
                               nombre="Diez Ficha", dni="00000010X")
    assert _aliases(fabrica) == [(*ALIAS_10, None)]


# ================================ R19 =================================== #

def test_f040_r19_deshacer_restaura_el_recurso_del_alias(portal) -> None:
    cliente, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="MO/0004",
                               nombre="CUATRO SIN DNI", dni=None,
                               recurso_ide=904, created_by="conciliacion")
    r = cliente.post("/api/empleado/reasignar",
                     json={"nombre_leido": LEIDO, "recurso_ide": 901})
    assert r.status_code == 200, r.text
    assert _aliases(fabrica) == [(*ALIAS_901, "reasignacion")]
    deshacer = cliente.post("/api/undo")
    assert deshacer.json()["ok"] is True, deshacer.text
    assert _aliases(fabrica) == [(*ALIAS_904, "conciliacion")]


def test_f040_r19_el_snapshot_lleva_recurso_ide(portal) -> None:
    _, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="MO/0004",
                               nombre="CUATRO SIN DNI", dni=None,
                               recurso_ide=904)
    with fabrica.create_session() as s:
        snap = repo._alias_snapshot(s, NORM)
    assert snap["recurso_ide"] == 904
    assert snap["empleado_ide"] is None


def test_f040_r19_snapshot_anterior_a_f040_restaura_null(portal) -> None:
    _, fabrica, _, repo = portal
    repo.upsert_empleado_alias(nombre_leido=LEIDO, ide=None, codigo="MO/0004",
                               nombre="CUATRO SIN DNI", dni=None,
                               recurso_ide=904)
    viejo = {"nombre_norm": NORM, "existed": True, "empleado_ide": 10,
             "empleado_codigo": "E10", "empleado_nombre": "Diez Ficha",
             "empleado_dni": "00000010X", "created_at_utc": "2026-01-01",
             "created_by": "conciliacion"}
    with fabrica.create_session() as s:
        repo._apply_alias_snapshot(s, viejo)
        s.commit()
    assert _aliases(fabrica) == [(*ALIAS_10, "conciliacion")]
