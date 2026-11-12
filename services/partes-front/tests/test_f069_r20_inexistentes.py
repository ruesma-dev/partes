# tests/test_f069_r20_inexistentes.py
"""F-069 · R20, R21 (DA1): el 422 de ambito dice si las lineas ya no existen.

Antes de F-069, cada pasada de sv3 borraba y recreaba las extras
automaticas con ids nuevos, y aprobar desde una pagina cargada antes daba
«N linea(s) no son de esta vista» (obra 0697, 12/11/2026). F-069 arregla
la causa en sv3; este mensaje sigue sirviendo cuando una extra desaparece
de verdad: si alguno de los ids fuera del ambito NO existe en
`parte_registros` (ni en la papelera), el 422 lo dice y pide recargar.

Sin red ni PostgreSQL: SQLite en memoria con el ORM real. Datos
sinteticos.
"""
from __future__ import annotations

import pytest
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.parte_repository import ParteReviewRepository
from sqlalchemy import event
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f022_aprobar_seleccion import (  # noqa: F401 - fixture
    ENDPOINTS,
    MARZO,
    portal,
)

NO_EXISTE = 999999

TEXTO_DE_HOY = (
    "{n} linea(s) no son de esta vista (otra obra, otro periodo, otra "
    "persona o en la papelera): recarga la pagina y vuelve a seleccionar")


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_f069_r20_ids_inexistentes_dicen_que_se_recalculan(
        portal, endpoint) -> None:  # noqa: F811
    cliente, _f, ids, sv5, publisher = portal()
    r = cliente.post(endpoint, json={
        "registro_ids": ids["o10_a"] + [NO_EXISTE], "ambito": MARZO})
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert cuerpo["fuera_de_ambito"] == 1
    assert cuerpo["inexistentes"] == 1
    assert cuerpo["error"] == (
        "1 línea(s) no son de esta vista: 1 ya no existen porque se están "
        "recalculando las extras. Recarga en unos segundos y vuelve a "
        "seleccionar")
    assert sv5.preflights == [] and sv5.ejecutadas == []


def test_f069_r20_mezcla_de_ajenos_e_inexistentes(portal) -> None:  # noqa: F811
    cliente, _f, ids, _sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"] + ids["o20_a"][:1]
        + [NO_EXISTE, NO_EXISTE + 1], "ambito": MARZO})
    assert r.status_code == 422
    assert (r.json()["fuera_de_ambito"], r.json()["inexistentes"]) == (3, 2)
    assert r.json()["error"].startswith(
        "3 línea(s) no son de esta vista: 2 ya no existen")


@pytest.mark.parametrize("intruso", ["o20_a", "o10_abril", "papelera"])
def test_f069_r20_ajenos_que_existen_responden_como_hoy(
        portal, intruso) -> None:  # noqa: F811
    cliente, _f, ids, _sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"] + ids[intruso][:1], "ambito": MARZO})
    assert r.status_code == 422
    assert r.json() == {"ok": False, "error": TEXTO_DE_HOY.format(n=1),
                        "fuera_de_ambito": 1}


def test_f069_r21_sin_ids_fuera_no_se_consulta_la_existencia(
        portal, monkeypatch) -> None:  # noqa: F811
    cliente, _f, ids, _sv5, _p = portal()
    llamadas: list = []
    monkeypatch.setattr(ParteReviewRepository, "registro_ids_existentes",
                        lambda self, i: llamadas.append(i) or set())
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"], "ambito": MARZO})
    assert r.status_code == 200 and llamadas == []


def test_f069_r21_con_ids_fuera_una_sola_llamada(
        portal, monkeypatch) -> None:  # noqa: F811
    cliente, _f, ids, _sv5, _p = portal()
    original = ParteReviewRepository.registro_ids_existentes
    llamadas: list = []

    def _espia(self, i):
        llamadas.append(sorted(i))
        return original(self, i)
    monkeypatch.setattr(ParteReviewRepository, "registro_ids_existentes",
                        _espia)
    cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"] + [NO_EXISTE], "ambito": MARZO})
    assert len(llamadas) == 1


# ======================= repositorio de sv4 ============================ #

def test_f069_r20_repo_existentes_incluye_la_papelera() -> None:
    fabrica = FabricaSesionSqlite()
    vivas = sembrar_parte(fabrica, [{}, {}], document_id="d-1")
    borrada = sembrar_parte(fabrica, [{"borrada": True}], document_id="d-2")
    en_papelera = sembrar_parte(fabrica, [{}], document_id="d-3",
                                doc_en_papelera=True)
    repo = ParteReviewRepository(fabrica)
    todos = vivas + borrada + en_papelera
    assert repo.registro_ids_existentes(todos + [NO_EXISTE]) == set(todos)
    assert repo.registro_ids_existentes([]) == set()


def test_f069_r21_repo_una_consulta_por_lote(monkeypatch) -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{}] * 5, document_id="d-1")
    monkeypatch.setattr(repo_mod, "LOTE_IDS_CONSULTA", 2)
    consultas: list[str] = []
    event.listen(fabrica.engine, "before_cursor_execute",
                 lambda _c, _cu, sql, *_a: consultas.append(sql))
    existentes = ParteReviewRepository(fabrica).registro_ids_existentes(
        ids + [NO_EXISTE])
    assert existentes == set(ids)
    assert len([q for q in consultas if q.lstrip().upper().startswith(
        "SELECT")]) == 3
