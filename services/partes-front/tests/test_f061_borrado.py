# tests/test_f061_borrado.py
"""F-061 · el parte que se queda sin líneas vivas se RETIRA (R1–R4).

Retirar = `is_active = false`, `deleted_at_utc` a NULL y `deleted_by` con la
marca `sin-lineas` (DA7). No va a la papelera de partes (DA1) y libera su
sha256 para que sv3 pueda reingerir el PDF.

SQLite en memoria con el ORM real (`tests/dobles.py`). Ni red ni
PostgreSQL. Datos sintéticos.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from application.services.congelacion import CongeladoError
from application.services.parte_vacio import MARCA_RETIRADO
from dobles import FabricaSesionSqlite, sembrar_parte
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    worker_key_for_registro,
)
from interface_adapters.web.app import build_app

DOC = "doc-f004"   # el id por defecto de `sembrar_parte`


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _doc(fabrica, document_id: str = DOC) -> ParteDocumentOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, document_id)


def _reg(fabrica, registro_id: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, registro_id)


def _es_retirado(doc: ParteDocumentOrm) -> bool:
    return (doc is not None and not doc.is_active
            and doc.deleted_at_utc is None
            and (doc.deleted_by or "").startswith(MARCA_RETIRADO))


def _montaje(lineas, **kw):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, lineas, **kw)
    return fabrica, ParteReviewRepository(fabrica), ids


# =============================== R1 =================================== #

def test_f061_r1_la_ultima_linea_retira_el_parte() -> None:
    fabrica, repo, ids = _montaje([{"horas": 8.0}, {"horas": 4.0}])

    primera = repo.borrar_linea(registro_id=ids[0], by="ana")
    assert primera == {"ok": True, "parte_retirado": False,
                       "document_id": DOC}
    assert _doc(fabrica).is_active is True

    ultima = repo.borrar_linea(registro_id=ids[1], by="ana")
    assert ultima == {"ok": True, "parte_retirado": True,
                      "document_id": DOC}
    doc = _doc(fabrica)
    assert doc.is_active is False
    assert doc.deleted_at_utc is None          # NO va a la papelera de partes
    assert doc.deleted_by == "sin-lineas · ana"
    assert _reg(fabrica, ids[1]).deleted_at_utc is not None


def test_f061_r1_con_lineas_vivas_el_parte_no_se_toca() -> None:
    fabrica, repo, ids = _montaje([{}, {}, {}])
    assert repo.borrar_linea(registro_id=ids[1], by="ana")[
        "parte_retirado"] is False
    doc = _doc(fabrica)
    assert (doc.is_active, doc.deleted_at_utc, doc.deleted_by) == (
        True, None, None)


def test_f061_r1_cuentan_solo_las_vivas() -> None:
    """Una línea ya en la papelera no sostiene el parte."""
    fabrica, repo, ids = _montaje([{"borrada": True}, {}])
    assert repo.borrar_linea(registro_id=ids[1], by="ana")[
        "parte_retirado"] is True
    assert _es_retirado(_doc(fabrica))


def test_f061_r1_linea_inexistente_o_ya_borrada() -> None:
    _fabrica, repo, ids = _montaje([{"borrada": True}, {}])
    assert repo.borrar_linea(registro_id=999_999, by="ana") == {"ok": False}
    assert repo.borrar_linea(registro_id=ids[0], by="ana") == {"ok": False}


def test_f061_r1_soft_delete_registro_sigue_devolviendo_bool() -> None:
    fabrica, repo, ids = _montaje([{}])
    assert repo.soft_delete_registro(registro_id=ids[0], by="ana") is True
    assert _es_retirado(_doc(fabrica))
    assert repo.soft_delete_registro(registro_id=ids[0], by="ana") is False


def test_f061_r1_endpoint_devuelve_parte_retirado() -> None:
    fabrica, repo, ids = _montaje([{}, {}])
    cliente = TestClient(build_app(Settings(_env_file=None),
                                   repository=repo))

    r1 = cliente.post(f"/api/registro/{ids[0]}/delete")
    assert r1.status_code == 200
    assert r1.json() == {"ok": True, "parte_retirado": False,
                         "document_id": DOC}
    r2 = cliente.post(f"/api/registro/{ids[1]}/delete")
    assert r2.json() == {"ok": True, "parte_retirado": True,
                         "document_id": DOC}
    assert _es_retirado(_doc(fabrica))


def test_f061_r1_marca_sin_actor() -> None:
    fabrica, repo, ids = _montaje([{}])
    repo.borrar_linea(registro_id=ids[0], by=None)
    assert _doc(fabrica).deleted_by == "sin-lineas"


# =============================== R2 =================================== #

def _clave(fabrica, registro_id: int) -> str:
    with fabrica.create_session() as s:
        return worker_key_for_registro(s.get(ParteRegistroOrm, registro_id))


def test_f061_r2_persona_que_vacia_el_parte_lo_retira() -> None:
    fabrica, repo, ids = _montaje([{}, {"tipo": "extra", "horas": 2.0}])
    assert repo.soft_delete_worker(worker_key=_clave(fabrica, ids[0]),
                                   by="ana") == (2, 0)
    doc = _doc(fabrica)
    assert _es_retirado(doc)
    assert doc.deleted_by == "sin-lineas · ana"


def test_f061_r2_persona_con_congeladas_no_retira_el_parte() -> None:
    """F-004 R13: la línea registrada se omite y sigue viva."""
    fabrica, repo, ids = _montaje([{"estado": "registrado"}, {}])
    assert repo.soft_delete_worker(worker_key=_clave(fabrica, ids[1]),
                                   by="ana") == (1, 1)
    doc = _doc(fabrica)
    assert (doc.is_active, doc.deleted_at_utc, doc.deleted_by) == (
        True, None, None)


def test_f061_r2_persona_solo_toca_sus_partes() -> None:
    fabrica = FabricaSesionSqlite()
    (a,) = sembrar_parte(fabrica, [{}], document_id="d-a")
    sembrar_parte(fabrica, [{}], document_id="d-b", empleado_ide=88,
                  empleado_dni="87654321X", empleado_nombre="Otra",
                  recurso_ide=777)
    repo = ParteReviewRepository(fabrica)
    assert repo.soft_delete_worker(worker_key=_clave(fabrica, a),
                                   by="ana") == (1, 0)
    assert _es_retirado(_doc(fabrica, "d-a"))
    assert _doc(fabrica, "d-b").is_active is True


def test_f061_r2_deshacer_creadas_que_vacia_el_parte_lo_retira() -> None:
    fabrica, repo, ids = _montaje([{}])
    with fabrica.create_session() as s:
        repo._deshacer_creadas(s, {"creadas": [ids[0]], "registros": []},
                               actor="ana")
        s.commit()
    assert _reg(fabrica, ids[0]).deleted_at_utc is not None
    doc = _doc(fabrica)
    assert _es_retirado(doc)
    assert doc.deleted_by == "sin-lineas · ana"


def test_f061_r2_deshacer_creadas_con_vivas_no_retira() -> None:
    fabrica, repo, ids = _montaje([{}, {}])
    with fabrica.create_session() as s:
        repo._deshacer_creadas(s, {"creadas": [ids[0]], "registros": []},
                               actor="ana")
        s.commit()
    assert _doc(fabrica).is_active is True


# =============================== R3 =================================== #

def test_f061_r3_sql_de_bloqueo_es_for_update_ordenado_por_id() -> None:
    sql = str(ParteReviewRepository._sql_bloqueo_documentos(["b", "a"])
              .compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in sql
    assert "ORDER BY parte_documents.id" in sql


def test_f061_r3_borrar_linea_bloquea_el_parte_antes_de_las_guardas(
        monkeypatch) -> None:
    """La guarda de congelación salta DESPUÉS de bloquear el parte."""
    fabrica, repo, ids = _montaje([{}], aprobado=True)
    llamadas: list[list[str]] = []
    original = ParteReviewRepository._bloquear_documentos

    def espia(self, session, document_ids):
        # Lo que de verdad se bloquea, y en qué orden.
        docs = original(self, session, document_ids)
        llamadas.append([d.id for d in docs])
        return docs

    monkeypatch.setattr(ParteReviewRepository, "_bloquear_documentos", espia)
    with pytest.raises(CongeladoError):
        repo.borrar_linea(registro_id=ids[0], by="ana")
    assert llamadas == [[DOC]]


def test_f061_r3_soft_delete_worker_bloquea_sus_partes_por_id(
        monkeypatch) -> None:
    fabrica = FabricaSesionSqlite()
    (a,) = sembrar_parte(fabrica, [{}], document_id="d-b")
    sembrar_parte(fabrica, [{}], document_id="d-a")
    repo = ParteReviewRepository(fabrica)
    llamadas: list[list[str]] = []
    original = ParteReviewRepository._bloquear_documentos

    def espia(self, session, document_ids):
        # Lo que de verdad se bloquea, y en qué orden.
        docs = original(self, session, document_ids)
        llamadas.append([d.id for d in docs])
        return docs

    monkeypatch.setattr(ParteReviewRepository, "_bloquear_documentos", espia)
    repo.soft_delete_worker(worker_key=_clave(fabrica, a), by="ana")
    assert llamadas == [["d-a", "d-b"]]


def test_f061_r3_dos_borrados_seguidos_retiran_el_parte() -> None:
    fabrica, repo, ids = _montaje([{}, {}])
    res = [repo.borrar_linea(registro_id=i, by="ana") for i in ids]
    assert [r["parte_retirado"] for r in res] == [False, True]
    assert _es_retirado(_doc(fabrica))


# =============================== R4 =================================== #

def test_f061_r4_borrar_obra_sigue_mandando_a_la_papelera_de_partes() -> None:
    fabrica, repo, _ids = _montaje([{}])
    assert repo.soft_delete_obra(obra_key="obr-10", by="ana") == (1, 0)
    doc = _doc(fabrica)
    assert doc.is_active is False
    assert doc.deleted_at_utc is not None
    assert doc.deleted_by == "ana"


def test_f061_r4_borrar_parte_sigue_mandando_a_la_papelera_de_partes() -> None:
    fabrica, repo, _ids = _montaje([{}])
    assert repo.delete_document(document_id=DOC, deleted_by="ana") is True
    doc = _doc(fabrica)
    assert doc.deleted_at_utc is not None
    assert doc.deleted_by == "ana"
    assert [d["document_id"]
            for d in repo.list_papelera()["documentos"]] == [DOC]
