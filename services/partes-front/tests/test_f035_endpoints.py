# tests/test_f035_endpoints.py
"""F-035 · endpoints del portal (sv4) sobre los RECURSOS ACTIVOS.

  - R5: `GET /api/sigrid/recursos[?empresa=N]` con `jornada_sugerida` y lo
    que hay que guardar al elegir (`guardar`); sin Sigrid o con error,
    `ok: false` e `items: []`.
  - R9: `/api/conciliacion/buscar` acepta `empresa`.
  - R11-R15: `confirmar` y `reasignar` aceptan `recurso_ide` (404 si no
    esta, sin tocar nada); con ficha se guarda la ficha y alias, sin ficha
    el recurso y sin alias; con `ide` y sin `recurso_ide`, como siempre.
  - R19: `POST /api/partes/nuevo` sin ficha y con recurso queda casado.
  - R21: «Reasignar a…» (por lineas y por trabajador) con `recurso_ide`.

Sin red ni PostgreSQL: Sigrid simulado y SQLite en memoria. Datos
SINTETICOS.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from application.services.jornada_resolver import jornada_efectiva
from application.services.recurso_catalog import RecursoCatalog
from config.settings import Settings
from infrastructure.database.orm_models import (
    EmpleadoAliasOrm,
    ParteRegistroOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import (
    EmpleadoOption,
    RecursoOption,
)
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

LEIDO = "Tres Solo Recurso"

RECURSOS = [
    RecursoOption(ide=901, codigo="MO/0001", nombre="UNO RECURSO",
                  dni="00000001R", empresa=1, empleado_ide=11,
                  empleado_codigo="E11", empleado_nombre="Uno Ficha",
                  empleado_dni="1R", categoria="Oficial", candef=8.0),
    RecursoOption(ide=902, codigo="MO/0002", nombre="DOS RECURSO",
                  dni="00000002W", empresa=28, empleado_ide=12,
                  empleado_codigo="E12", empleado_nombre="Dos Ficha",
                  empleado_dni=None, categoria=None, candef=None),
    RecursoOption(ide=903, codigo="MO/0037", nombre="TRES SOLO RECURSO",
                  dni="00000003A", empresa=28, categoria="Peon", candef=7.5),
]
FICHAS = [EmpleadoOption(ide=10, codigo="E10", nombre="Diez Ficha",
                         dni="00000010X", reside=910, empresa=1)]


class LookupFalso:
    """Doble de `SigridLookupClient` para montar el portal sin red."""

    def __init__(self, **_kw) -> None:
        pass

    def fetch_tipos_hora(self) -> list:
        return []

    def fetch_obras(self) -> list:
        return []

    def fetch_empleados(self) -> list:
        return list(FICHAS)

    def fetch_recursos_activos(self) -> list:
        return list(RECURSOS)

    def fetch_partidas_obra(self, _obra_ide: int) -> list:
        return []

    def fetch_hora_extra_recurso(self, _recurso_ide: int):
        return None

    def fetch_dnis_sin_extra(self, _dnis) -> set:
        return set()


ENTORNO = {
    "PG_PASSWORD": "irrelevante-en-tests",
    "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    "DEFAULT_REVIEWER": "ana",
}
SIGRID = {
    "SIGRID_API_BASE_URL": "http://sigrid.invalid",
    "SIGRID_API_FUNCTION_KEY": "clave-de-test",
    "SIGRID_API_DATABASE": "bd",
}


def _montar(monkeypatch, *, con_sigrid=True):
    for clave, valor in {**ENTORNO, **(SIGRID if con_sigrid else {})}.items():
        monkeypatch.setenv(clave, valor)
    if not con_sigrid:
        for clave in SIGRID:
            monkeypatch.delenv(clave, raising=False)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupFalso)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(
        fabrica, [{"leido": LEIDO}, {"leido": LEIDO, "tipo": "extra",
                                     "horas": 1.0}],
        empleado_ide=None, empleado_dni="", empleado_nombre=None)
    with fabrica.create_session() as s:
        for rid in ids:
            s.get(ParteRegistroOrm, rid).empleado_match_method = "none"
        s.commit()
    settings = Settings(_env_file=None)
    app = build_app(settings, repository=ParteReviewRepository(fabrica))
    return TestClient(app), fabrica, ids, settings


@pytest.fixture
def portal(monkeypatch):
    return _montar(monkeypatch)


def _filas(fabrica, ids) -> list[tuple]:
    with fabrica.create_session() as s:
        return [
            (r.empleado_ide, r.empleado_codigo, r.empleado_nombre,
             r.empleado_dni, r.empleado_reside, r.empleado_match_method)
            for r in (s.get(ParteRegistroOrm, i) for i in ids)
        ]


def _aliases(fabrica) -> list[tuple]:
    with fabrica.create_session() as s:
        return [(a.nombre_norm, a.empleado_ide)
                for a in s.query(EmpleadoAliasOrm).all()]


def _undos(fabrica) -> int:
    with fabrica.create_session() as s:
        return s.query(UndoLogOrm).count()


SIN_TOCAR = (None, None, None, "", None, "none")
CASADA_903 = (None, "MO/0037", "TRES SOLO RECURSO", "00000003A", 903,
              "recurso_manual")
CASADA_901 = (11, "E11", "Uno Ficha", "1R", 901, "none")


# ================================ R5 ==================================== #

def test_f035_r5_endpoint_recursos_todos(portal) -> None:
    cliente, _, _, settings = portal
    cuerpo = cliente.get("/api/sigrid/recursos").json()
    assert cuerpo["ok"] is True
    items = cuerpo["items"]
    assert [i["ide"] for i in items] == [901, 902, 903]
    tres = items[2]
    assert {k: tres[k] for k in ("codigo", "nombre", "dni", "empresa",
                                 "categoria", "candef")} == {
        "codigo": "MO/0037", "nombre": "TRES SOLO RECURSO",
        "dni": "00000003A", "empresa": 28, "categoria": "Peon",
        "candef": 7.5}
    assert tres["guardar"] == {
        "empleado_ide": None, "empleado_codigo": "MO/0037",
        "empleado_nombre": "TRES SOLO RECURSO", "empleado_dni": "00000003A",
        "empleado_reside": 903}
    assert items[0]["guardar"]["empleado_ide"] == 11
    assert items[1]["guardar"]["empleado_dni"] == "00000002W"
    for i, r in zip(items, RECURSOS):
        assert i["jornada_sugerida"] == jornada_efectiva(
            r.candef, minimo=settings.candef_minimo_valido,
            por_defecto=settings.jornada_por_defecto)


def test_f035_r5_endpoint_recursos_por_empresa(portal) -> None:
    cliente, _, _, _ = portal
    assert [i["ide"] for i in cliente.get(
        "/api/sigrid/recursos?empresa=28").json()["items"]] == [902, 903]
    assert [i["ide"] for i in cliente.get(
        "/api/sigrid/recursos?empresa=1").json()["items"]] == [901]
    assert cliente.get("/api/sigrid/recursos?empresa=5").json() == \
        {"ok": True, "items": []}


def test_f035_r5_endpoint_recursos_sin_sigrid(monkeypatch) -> None:
    cliente, _, _, _ = _montar(monkeypatch, con_sigrid=False)
    cuerpo = cliente.get("/api/sigrid/recursos").json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []


def test_f035_r5_endpoint_recursos_con_error(portal, monkeypatch) -> None:
    cliente, _, _, _ = portal

    def _falla(self, empresa=None):
        raise RuntimeError("caida")

    monkeypatch.setattr(RecursoCatalog, "list", _falla)
    cuerpo = cliente.get("/api/sigrid/recursos").json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []


# ================================ R9 ==================================== #

def test_f035_r9_buscar_por_empresa(portal) -> None:
    cliente, _, _, _ = portal
    todos = cliente.get("/api/conciliacion/buscar?q=recurso").json()["items"]
    assert {i["ide"] for i in todos} == {901, 902, 903}
    porsan = cliente.get(
        "/api/conciliacion/buscar?q=recurso&empresa=28").json()["items"]
    assert {i["ide"] for i in porsan} == {902, 903}
    assert {i["empresa"] for i in porsan} == {28}
    ruesma = cliente.get(
        "/api/conciliacion/buscar?q=tres&empresa=1").json()["items"]
    assert ruesma == []


# ============================ R11 · 404 ================================= #

@pytest.mark.parametrize("ruta, extra", [
    ("/api/conciliacion/confirmar", {"nombre_leido": LEIDO}),
    ("/api/empleado/reasignar", {"nombre_leido": LEIDO}),
])
def test_f035_r11_recurso_desconocido_404_sin_tocar_nada(
        portal, ruta, extra) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post(ruta, json={**extra, "recurso_ide": 999})
    assert r.status_code == 404
    assert r.json()["ok"] is False
    assert _filas(fabrica, ids) == [SIN_TOCAR, SIN_TOCAR]
    assert _undos(fabrica) == 0 and _aliases(fabrica) == []


# ======================= R12-R14 · confirmar ============================ #

def test_f035_r13_r14_confirmar_recurso_sin_ficha(portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "recurso_ide": 903})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["ok"], cuerpo["updated"]) == (True, 2)
    assert cuerpo["empleado"] == {"ide": None, "codigo": "MO/0037",
                                  "nombre": "TRES SOLO RECURSO"}
    assert _filas(fabrica, ids) == [CASADA_903, CASADA_903]
    assert _aliases(fabrica) == []                      # R14
    # Sale de la cola de Conciliar.
    assert LEIDO not in cliente.get("/conciliacion").text


def test_f035_r12_confirmar_recurso_con_ficha(portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "recurso_ide": "901"})
    assert r.status_code == 200, r.text
    assert r.json()["empleado"] == {"ide": 11, "codigo": "E11",
                                    "nombre": "Uno Ficha"}
    assert _filas(fabrica, ids) == [CASADA_901, CASADA_901]
    assert _aliases(fabrica) == [("tres solo recurso", 11)]


def test_f035_r15_confirmar_por_ide_como_siempre(portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO, "ide": 10})
    assert r.status_code == 200, r.text
    assert _filas(fabrica, ids) == [
        (10, "E10", "Diez Ficha", "00000010X", None, "none")] * 2
    assert _aliases(fabrica) == [("tres solo recurso", 10)]


def test_f035_r15_confirmar_sin_ide_ni_recurso_400(portal) -> None:
    cliente, _, _, _ = portal
    r = cliente.post("/api/conciliacion/confirmar",
                     json={"nombre_leido": LEIDO})
    assert r.status_code == 400


# ======================== R21 · reasignar =============================== #

def test_f035_r21_reasignar_lineas_a_un_recurso_sin_ficha(portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"registro_ids": [ids[0]], "recurso_ide": 903})
    assert r.status_code == 200, r.text
    assert r.json()["updated"] == 1
    assert _filas(fabrica, ids) == [CASADA_903, SIN_TOCAR]
    assert _aliases(fabrica) == []


def test_f035_r21_r14_reasignar_trabajador_sin_ficha_no_crea_alias(
        portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"worker_key": "nom-TRES_SOLO_RECURSO",
                           "recurso_ide": 903})
    assert r.status_code == 200, r.text
    assert _filas(fabrica, ids) == [CASADA_903, CASADA_903]
    assert _aliases(fabrica) == []


def test_f035_r21_r12_reasignar_trabajador_con_ficha_crea_alias(
        portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"nombre_leido": LEIDO, "recurso_ide": 901})
    assert r.status_code == 200, r.text
    assert _filas(fabrica, ids) == [CASADA_901, CASADA_901]
    assert _aliases(fabrica) == [("tres solo recurso", 11)]


def test_f035_r15_reasignar_por_ide_como_siempre(portal) -> None:
    cliente, fabrica, ids, _ = portal
    r = cliente.post("/api/empleado/reasignar",
                     json={"registro_ids": ids, "ide": 10})
    assert r.status_code == 200, r.text
    assert _filas(fabrica, ids)[0][:5] == (10, "E10", "Diez Ficha",
                                           "00000010X", None)


# ================================ R19 =================================== #

def test_f035_r19_nuevo_parte_con_recurso_sin_ficha(portal) -> None:
    cliente, fabrica, _, _ = portal
    r = cliente.post("/api/partes/nuevo", json={
        "obra_ide": 10, "obra_codigo": "0100", "obra_nombre": "Obra Uno",
        "empleado_ide": None, "empleado_codigo": "MO/0037",
        "empleado_nombre": "TRES SOLO RECURSO",
        "empleado_dni": "00000003A", "empleado_reside": "903",
        "dias": ["2026-03-04"], "horas_ordinaria": 8, "horas_extra": 0})
    assert r.status_code == 200, r.text
    with fabrica.create_session() as s:
        (reg,) = s.query(ParteRegistroOrm).filter(
            ParteRegistroOrm.fecha == "2026-03-04").all()
        assert (reg.empleado_ide, reg.empleado_reside, reg.recurso_ide,
                reg.empleado_match_method) == (None, 903, 903,
                                               "recurso_manual")


@pytest.mark.parametrize("ruta, extra", [
    ("/api/conciliacion/confirmar", {"nombre_leido": LEIDO}),
    ("/api/empleado/reasignar", {"nombre_leido": LEIDO}),
])
def test_f035_r15_ide_desconocido_404_ok_false(portal, ruta, extra) -> None:
    """Camino `ide` (sin `recurso_ide`): un empleado que no esta en el
    maestro es 404 con `ok: false`, como antes de F-035 (superviviente 1
    de la campana de mutacion)."""
    cliente, fabrica, ids, _ = portal
    r = cliente.post(ruta, json={**extra, "ide": 999})
    assert r.status_code == 404
    assert r.json()["ok"] is False
    assert _filas(fabrica, ids) == [SIN_TOCAR, SIN_TOCAR]
