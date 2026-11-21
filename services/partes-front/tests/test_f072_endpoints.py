# tests/test_f072_endpoints.py
"""F-072 · Los endpoints del portal con entradas de obras agrupadas.

- R26: `/api/sigrid/obras` da las obras normales SIN las agrupadas y las
  entradas (`codigo`, `nombre`, `empresa`, `agrupada`, `partida_ide`).
- R27: cambiar la obra a una entrada (`partida_ide`) comprueba el catálogo y
  pone obra, partida y marca; si no está, 422 sin cambios.
- R28: una obra agrupada sin entrada, 422 sin cambios (cambio de obra y
  parte nuevo).
- R32: cambiar la partida de una línea de entrada, 409.
- R33: aprobar una entrada manda a sv5 la obra agrupada con `partida_ide` y
  `partida_metodo` en cada línea; una petición por entrada.
- R34: sincronizar una vista `agr-`, «no sincronizable» con motivo.
- R3: con todo apagado, `/api/sigrid/obras` como siempre.

Sin red ni BBDD real: Sigrid simulado, sv5 falso y SQLite. Datos FICTICIOS.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from application.services.sincronizar_ambito import (
    MOTIVO_ENTRADA_AGRUPADA,
    motivo_no_sincronizable,
)
from config.settings import Settings
from infrastructure.database.orm_models import ParteDocumentOrm, ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import ObraOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f023_catalogo_empresa import LookupPortalFake
from tests.test_f046_aplicar import _marcar
from tests.test_f072_catalogo_entradas import OBRAS, PRESUPUESTOS


class LookupF072(LookupPortalFake):
    def fetch_obras(self) -> list:
        return list(OBRAS) + [ObraOption(10, "0100", "Obra Uno", 1)]

    def fetch_partidas_obra(self, obra_ide: int) -> list:
        return list(PRESUPUESTOS.get(int(obra_ide), []))


class Sv5:
    def __init__(self):
        self.preflights: list[dict] = []

    def preflight(self, payload):
        self.preflights.append(payload)
        return {"ok": True, "conflictos": [], "acciones": []}


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": "clave-de-test",
        "SIGRID_API_DATABASE": "bd",
        "TRANSFER_BASE_URL": "http://sv5.interno",
        "POSTVENTA_OBRA_COD": "POSTV2", "VAR_OBRA_COD": "VAR",
        "VAR_PARTIDA_DESDE": "29",
    }.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupF072)
    return monkeypatch


@pytest.fixture
def portal(entorno):
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 2.0, "tipo": "extra"}],
                  document_id="d1", fecha="2026-11-16")
    sv5 = Sv5()
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=sv5)
    return TestClient(app), fabrica, sv5


def _regs(fabrica, doc="d1"):
    with fabrica.create_session() as s:
        return [(r.obra_ide, r.partida_ide, r.partida_match_method)
                for r in s.query(ParteRegistroOrm).filter_by(
                    document_id=doc).order_by(ParteRegistroOrm.id)]


# --------------------------------- R26 ---------------------------------- #

def test_f072_r26_obras_sin_agrupadas_y_con_entradas(portal):
    cliente, _f, _s = portal
    items = cliente.get("/api/sigrid/obras").json()["items"]
    normales = [i for i in items if not i.get("agrupada")]
    assert not [i for i in normales if i["codigo"] in ("VAR", "POSTV2")]
    assert {i["codigo"] for i in normales} >= {"0578", "0100"}
    var29 = next(i for i in items if i["codigo"] == "VAR-29"
                 and i["empresa"] == 1)
    assert var29 == {"ide": 9101, "codigo": "VAR-29", "nombre": "VARIOS 29",
                     "empresa": 1, "empresa_nombre": var29["empresa_nombre"],
                     "agrupada": "var", "partida_ide": 91012}
    assert any(i["codigo"] == "Postv-0578B" and i["agrupada"] == "postventa"
               for i in items)


def test_f072_r3_apagado_obras_como_siempre(entorno):
    for nombre in ("POSTVENTA_OBRA_COD", "VAR_OBRA_COD", "VAR_PARTIDA_DESDE"):
        entorno.delenv(nombre)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(FabricaSesionSqlite()))
    items = TestClient(app).get("/api/sigrid/obras").json()["items"]
    assert {i["codigo"] for i in items} >= {"VAR", "POSTV2"}
    assert not any("agrupada" in i for i in items)


# ------------------------------ R27 y R28 ------------------------------- #

def test_f072_r27_cambiar_a_una_entrada(portal):
    cliente, fabrica, _s = portal
    r = cliente.patch("/api/partes/d1/obra", json={
        "codigo": "VAR-29", "ide": 9101, "partida_ide": 91012})
    assert r.status_code == 200, r.text
    assert _regs(fabrica) == [(9101, 91012, "var")] * 2
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "d1").obra_codigo == "VAR"


@pytest.mark.parametrize("cuerpo", [
    {"codigo": "VAR-28", "ide": 9101, "partida_ide": 91011},   # fuera
    {"codigo": "VAR", "ide": 9101},                            # sin entrada
    {"codigo": "POSTV2"},                                      # sin entrada
    {"codigo": "X", "ide": 9101, "partida_ide": 90011},        # de otra obra
])
def test_f072_r27_r28_sin_entrada_valida_422_sin_cambios(portal, cuerpo):
    cliente, fabrica, _s = portal
    antes = _regs(fabrica)
    r = cliente.patch("/api/partes/d1/obra", json=cuerpo)
    assert r.status_code == 422, r.text
    assert _regs(fabrica) == antes


def test_f072_r28_parte_nuevo_en_obra_agrupada(portal):
    cliente, fabrica, _s = portal
    base = {"obra_ide": 9101, "obra_codigo": "VAR", "obra_nombre": "VAR",
            "empleado_ide": 77, "empleado_nombre": "Pepe Perez",
            "empleado_dni": "12345678Z", "empleado_reside": "501",
            "dias": ["2026-11-17"], "horas_ordinaria": 8, "horas_extra": 0}
    assert cliente.post("/api/partes/nuevo", json=base).status_code == 422
    r = cliente.post("/api/partes/nuevo", json=dict(base, partida_ide=91012))
    assert r.status_code == 200, r.text
    with fabrica.create_session() as s:
        [reg] = s.query(ParteRegistroOrm).filter_by(fecha="2026-11-17").all()
        assert (reg.obra_ide, reg.partida_ide, reg.partida_match_method) == (
            9101, 91012, "var")


# --------------------------------- R32 ---------------------------------- #

def test_f072_r32_partida_fija_409(portal):
    cliente, fabrica, _s = portal
    cliente.patch("/api/partes/d1/obra", json={
        "codigo": "VAR-29", "ide": 9101, "partida_ide": 91012})
    with fabrica.create_session() as s:
        rid = s.query(ParteRegistroOrm).filter_by(document_id="d1").first().id
    r = cliente.patch(f"/api/registros/{rid}/partida", json={
        "partida_ide": 91013, "partida_cod": "030"})
    assert r.status_code == 409, r.text
    assert "partida fija" in r.json()["error"]


# --------------------------------- R33 ---------------------------------- #

def test_f072_r33_aprobar_una_entrada_manda_la_marca(portal):
    cliente, fabrica, sv5 = portal
    cliente.patch("/api/partes/d1/obra", json={
        "codigo": "VAR-29", "ide": 9101, "partida_ide": 91012})
    with fabrica.create_session() as s:
        ids = [r.id for r in s.query(ParteRegistroOrm).filter_by(
            document_id="d1")]
    for rid in ids:
        _marcar(fabrica, rid, recurso_ide=501, hora_ide=1, hora_codigo="HL01")
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    assert r.status_code == 200, r.text
    [p] = sv5.preflights
    assert p["obra"]["ide"] == 9101
    assert {(x["partida_ide"], x["partida_metodo"]) for x in p["lineas"]} == {
        (91012, "var")}


# --------------------------------- R34 ---------------------------------- #

def test_f072_r34_vista_de_entrada_no_sincronizable():
    assert motivo_no_sincronizable("obra", "agr-9101-91012") == \
        MOTIVO_ENTRADA_AGRUPADA
    assert "no se sincroniza por entrada" in MOTIVO_ENTRADA_AGRUPADA
    assert motivo_no_sincronizable("obra", "obr-9101") is None


# --------------------------------- R35 ---------------------------------- #

def test_f072_r35_los_selectores_de_obra_mandan_la_partida_de_la_entrada():
    """Los tres usos de `/api/sigrid/obras` en `app.js` (cambio de obra,
    parte nuevo y alta de línea) mandan `partida_ide` de la entrada. El
    resto (rótulo `codigo · nombre`) ya lo hace `obraLabel`; M2 lo prueba
    en el portal."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text(
        encoding="utf-8")
    assert "partida_ide: o.partida_ide != null ? o.partida_ide : null" in js
    assert js.count("o.partida_ide != null ? o.partida_ide : null") == 3
    assert "partida_ide: obraEntradaPartida != null" in js
    assert "partida_ide: addlineEntradaPartida != null" in js
