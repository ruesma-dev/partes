# tests/test_f066_set_registro_hora.py
"""F-066 · guardar el código de hora decide `tipo_hora` por el prefijo `HE`
(R8, R12–R18).

- Repositorio (`set_registro_hora`) sobre SQLite en memoria: la clase sale
  del código, no de `auxhor.ext` (R12, R13); la incidencia no cambia (R14);
  sin código no se toca `tipo_hora` (R15); campos y deshacer (R16).
- Endpoint `PATCH /api/registros/{id}/hora` con el `SigridLookupClient` REAL
  sobre un sigrid-api falso (su `_post_sql_read`): la respuesta (R17), el
  excluido `HENC` responde 400 sin tocar la línea (R8), las guardas y varias
  líneas (R18).

Sin red ni PostgreSQL. Datos SINTÉTICOS (obra 0100, recurso 501).
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

#: `auxhor` sintético con lo que dio la M1: ninguna `ext = 1` en Sigrid,
#: salvo la fila 9 (inventada) para probar que `ext` ya no decide.
COLS_AUXHOR = ["ide", "codigo", "descripcion", "ext", "pre", "prenom"]
AUXHOR = [
    [1, "HL01", "Hora ordinaria", 0, 15.0, 12.0],
    [7, "HEOF", "Hora extra oficial", 0, 20.0, 18.0],
    [8, "HECAP", "Hora extra capataz", 0, 22.0, 19.0],
    [9, "HL09", "Ordinaria con ext a 1", 1, 16.0, 13.0],
    [10, "", "Sin codigo", 0, None, None],
    [63, "HENC", "HORA ENCARGADO", 0, 1.0, None],
]


class SigridLookupFalso(SigridLookupClient):
    """El cliente real con la red sustituida: sirve `auxhor` y nada más."""

    def _post_sql_read(self, *, sql, parameters, label, max_rows=None):
        if "FROM auxhor" in sql and parameters[-2] == 0:
            return list(COLS_AUXHOR), [list(f) for f in AUXHOR]
        return [], []


# ----------------------------- repositorio ------------------------------ #

def _fila(fabrica, rid: int) -> dict:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        return {c: getattr(r, c) for c in (
            "tipo_hora", "hora_ide", "hora_codigo", "hora_descripcion",
            "hora_ext", "hora_precio_coste", "hora_precio_nomina",
            "hora_match_method", "es_incidencia")}


def _guardar(repo, rid, ide, codigo, ext, *, desc="d", pre=1.0, prenom=2.0):
    return repo.set_registro_hora(
        registro_id=rid, hora_ide=ide, hora_codigo=codigo,
        hora_descripcion=desc, hora_ext=ext, hora_precio_coste=pre,
        hora_precio_nomina=prenom)


@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [
        {"tipo": "normal"}, {"tipo": "extra"},
        {"tipo": "normal", "es_incidencia": True},
        {"tipo": "extra", "es_incidencia": True},
    ], document_id="doc-f066")
    return ParteReviewRepository(fabrica), fabrica, ids


@pytest.mark.parametrize("codigo", ["HEOF", " hecap ", "HEGR"])
def test_f066_r12_he_ext_0_extra(repo, codigo) -> None:
    repositorio, fabrica, ids = repo
    assert _guardar(repositorio, ids[0], 7, codigo, 0)
    assert _fila(fabrica, ids[0])["tipo_hora"] == "extra"


@pytest.mark.parametrize("codigo", ["HL01", "HL09", "HENC", "MENC"])
def test_f066_r13_sin_prefijo_ext_1_normal(repo, codigo) -> None:
    repositorio, fabrica, ids = repo
    assert _guardar(repositorio, ids[1], 9, codigo, 1)
    assert _fila(fabrica, ids[1])["tipo_hora"] == "normal"


@pytest.mark.parametrize("codigo, ext", [
    ("HEOF", 0), ("HEOF", 1), ("HL01", 0), ("HL01", 1), (None, 1)])
def test_f066_r14_incidencia_no_cambia(repo, codigo, ext) -> None:
    repositorio, fabrica, ids = repo
    assert _guardar(repositorio, ids[2], 7, codigo, ext)
    assert _guardar(repositorio, ids[3], 7, codigo, ext)
    assert _fila(fabrica, ids[2])["tipo_hora"] == "normal"
    assert _fila(fabrica, ids[3])["tipo_hora"] == "extra"


@pytest.mark.parametrize("codigo", [None, "", "   "])
@pytest.mark.parametrize("ext", [0, 1, None])
def test_f066_r15_sin_codigo_no_toca_tipo(repo, codigo, ext) -> None:
    repositorio, fabrica, ids = repo
    assert _guardar(repositorio, ids[0], 10, codigo, ext, desc="Sin codigo")
    assert _guardar(repositorio, ids[1], 10, codigo, ext, desc="Sin codigo")
    normal, extra = _fila(fabrica, ids[0]), _fila(fabrica, ids[1])
    assert (normal["tipo_hora"], extra["tipo_hora"]) == ("normal", "extra")
    for fila in (normal, extra):   # el resto de campos sí se guarda
        assert (fila["hora_ide"], fila["hora_codigo"], fila["hora_ext"],
                fila["hora_descripcion"], fila["hora_match_method"]) == (
            10, codigo, ext, "Sin codigo", "manual")


def test_f066_r16_campos_y_deshacer(repo) -> None:
    repositorio, fabrica, ids = repo
    antes = _fila(fabrica, ids[0])
    assert antes["tipo_hora"] == "normal" and antes["hora_codigo"] == "HL01"
    assert _guardar(repositorio, ids[0], 7, "HEOF", 0, desc="Hora extra",
                    pre=20.0, prenom=18.0)
    assert _fila(fabrica, ids[0]) == {
        "tipo_hora": "extra", "hora_ide": 7, "hora_codigo": "HEOF",
        "hora_descripcion": "Hora extra", "hora_ext": 0,
        "hora_precio_coste": 20.0, "hora_precio_nomina": 18.0,
        "hora_match_method": "manual", "es_incidencia": False}
    deshecho = repositorio.undo_last(actor="ana")
    assert deshecho.get("action") == "registro_hora"
    assert _fila(fabrica, ids[0]) == antes


def test_f066_r16_deshacer_devuelve_extra(repo) -> None:
    repositorio, fabrica, ids = repo
    assert _guardar(repositorio, ids[1], 1, "HL01", 0)
    assert _fila(fabrica, ids[1])["tipo_hora"] == "normal"
    repositorio.undo_last(actor="ana")
    assert _fila(fabrica, ids[1])["tipo_hora"] == "extra"


def test_f066_r16_registro_inexistente(repo) -> None:
    repositorio, _fabrica, _ids = repo
    assert _guardar(repositorio, 999_999, 7, "HEOF", 0) is False


# ------------------------------- endpoint ------------------------------- #

@pytest.fixture
def portal(monkeypatch):
    for clave in ("PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.setenv(clave, "irrelevante-en-tests")
    monkeypatch.setenv("DEFAULT_REVIEWER", "ana")
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)

    def montar(lineas, *, con_sigrid=True, **kw):
        if con_sigrid:
            monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
            monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-prueba")
            monkeypatch.setenv("SIGRID_API_DATABASE", "ruesma_rep")
            monkeypatch.setattr(app_mod, "SigridLookupClient",
                                SigridLookupFalso)
        else:
            for clave in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY"):
                monkeypatch.delenv(clave, raising=False)
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, lineas, document_id="doc-f066", **kw)
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app), fabrica, ids

    return montar


def _patch(cliente, rid, ide):
    return cliente.patch(f"/api/registros/{rid}/hora", json={"hora_ide": ide})


@pytest.mark.parametrize("ide, codigo, ext, tipo", [
    (7, "HEOF", 0, "extra"), (8, "HECAP", 0, "extra"),
    (9, "HL09", 1, "normal"), (1, "HL01", 0, "normal")])
def test_f066_r17_respuesta(portal, ide, codigo, ext, tipo) -> None:
    cliente, fabrica, ids = portal([{"tipo": "normal"}])
    r = _patch(cliente, ids[0], ide)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["hora_codigo"], cuerpo["hora_ext"], cuerpo["tipo_hora"]) \
        == (codigo, ext, tipo)
    assert cuerpo["hora_ide"] == ide and cuerpo["registro_id"] == ids[0]
    assert _fila(fabrica, ids[0])["tipo_hora"] == tipo
    assert _fila(fabrica, ids[0])["hora_ext"] == ext


def test_f066_r17_respuesta_sin_codigo_es_normal(portal) -> None:
    cliente, fabrica, ids = portal([{"tipo": "extra"}])
    r = _patch(cliente, ids[0], 10)
    assert r.status_code == 200, r.text
    assert r.json()["tipo_hora"] == "normal"
    assert _fila(fabrica, ids[0])["tipo_hora"] == "extra"   # R15


def test_f066_r8_patch_excluido_400(portal) -> None:
    cliente, fabrica, ids = portal([{"tipo": "normal"}])
    antes = _fila(fabrica, ids[0])
    r = _patch(cliente, ids[0], 63)
    assert r.status_code == 400
    assert r.json()["detail"] == \
        "El tipo de hora seleccionado no existe en Sigrid."
    assert _fila(fabrica, ids[0]) == antes


def test_f066_r18_varias_lineas(portal) -> None:
    cliente, fabrica, ids = portal([
        {"tipo": "normal"}, {"tipo": "extra"},
        {"tipo": "normal", "es_incidencia": True}])
    for rid in ids:
        assert _patch(cliente, rid, 7).status_code == 200
    assert [_fila(fabrica, r)["tipo_hora"] for r in ids] == \
        ["extra", "extra", "normal"]
    for rid in ids:
        assert _patch(cliente, rid, 1).status_code == 200
    assert [_fila(fabrica, r)["tipo_hora"] for r in ids] == \
        ["normal", "normal", "normal"]


def test_f066_r18_guardas(portal) -> None:
    cliente, _fabrica, ids = portal([{"tipo": "normal", "estado": "registrado"}])
    assert _patch(cliente, ids[0], 7).status_code == 409   # F-004
    assert _patch(cliente, 999_999, 7).status_code == 404
    assert _patch(cliente, ids[0], 4242).status_code == 400


def test_f066_r18_sin_sigrid_503(portal) -> None:
    cliente, _fabrica, ids = portal([{"tipo": "normal"}], con_sigrid=False)
    assert _patch(cliente, ids[0], 7).status_code == 503
