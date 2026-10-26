# tests/test_f061_papelera.py
"""F-061 · papelera, restaurar y borrado físico del parte retirado (R5–R11).

- R5: las líneas de un parte retirado siguen en «Líneas sueltas borradas».
- R6–R8: restaurar devuelve el parte; con otro activo del mismo sha, 409
  sin escribir; restaurar un parte sin vivas devuelve sus líneas.
- R9–R11: al vaciar la papelera, y al «Eliminar» su última fila, el parte
  RETIRADO sin ninguna fila se borra físicamente. Ningún otro.

SQLite en memoria con el ORM real (`tests/dobles.py`). Ni red ni
PostgreSQL. Datos sintéticos. Los `SAWarning` son errores, como en F-010
R11.
"""
from __future__ import annotations

import warnings

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SAWarning

from application.services.parte_vacio import (
    MOTIVO_DUPLICADO_ACTIVO,
    DuplicadoActivoError,
)
from dobles import FabricaSesionSqlite, sembrar_parte
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app

DOC = "doc-f004"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
    }.items():
        monkeypatch.setenv(clave, valor)
    with warnings.catch_warnings():
        warnings.simplefilter("error", SAWarning)
        yield monkeypatch


def _doc(fabrica, document_id: str = DOC) -> ParteDocumentOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, document_id)


def _reg(fabrica, registro_id: int) -> ParteRegistroOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, registro_id)


def _filas(fabrica, document_id: str = DOC) -> int:
    with fabrica.create_session() as s:
        return len(s.execute(select(ParteRegistroOrm.id).where(
            ParteRegistroOrm.document_id == document_id)).all())


def _retirado(lineas, **kw):
    """Un parte con `lineas`, retirado borrando todas sus líneas vivas."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, lineas, **kw)
    repo = ParteReviewRepository(fabrica)
    did = kw.get("document_id", DOC)
    for rid in ids:
        if _reg(fabrica, rid).deleted_at_utc is None:
            repo.borrar_linea(registro_id=rid, by="ana")
    doc = _doc(fabrica, did)
    assert doc.is_active is False and doc.deleted_at_utc is None
    return fabrica, repo, ids


def _marcar(fabrica, document_id: str, **campos) -> None:
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, document_id)
        for k, v in campos.items():
            setattr(doc, k, v)
        s.commit()


def _cliente(repo) -> TestClient:
    return TestClient(build_app(Settings(_env_file=None), repository=repo))


# =============================== R5 =================================== #

def test_f061_r5_la_papelera_lista_las_lineas_y_no_el_parte() -> None:
    _fabrica, repo, ids = _retirado([{}, {}])
    pap = repo.list_papelera()
    assert pap["documentos"] == []
    assert sorted(r["registro_id"] for r in pap["registros"]) == sorted(ids)


# =============================== R6 =================================== #

def test_f061_r6_restaurar_una_linea_devuelve_el_parte() -> None:
    fabrica, repo, ids = _retirado([{}, {}])
    assert repo.restore_registro(registro_id=ids[0]) is True
    doc = _doc(fabrica)
    assert (doc.is_active, doc.deleted_at_utc, doc.deleted_by) == (
        True, None, None)
    assert _reg(fabrica, ids[0]).deleted_at_utc is None
    assert _reg(fabrica, ids[1]).deleted_at_utc is not None


def test_f061_r6_restaurar_en_parte_activo_no_toca_el_parte() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}, {}])
    repo = ParteReviewRepository(fabrica)
    assert repo.restore_registro(registro_id=ids[0]) is True
    doc = _doc(fabrica)
    assert (doc.is_active, doc.deleted_by) == (True, None)


def test_f061_r6_no_reactiva_el_parte_desactivado_por_sv3() -> None:
    """`deleted_by` NULL sin `deleted_at_utc`: reemplazo de sv3 (DA7)."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}])
    _marcar(fabrica, DOC, is_active=False)
    ParteReviewRepository(fabrica).restore_registro(registro_id=ids[0])
    assert _doc(fabrica).is_active is False


# =============================== R7 =================================== #

def _otro_activo_mismo_sha(fabrica) -> None:
    sembrar_parte(fabrica, [{}], document_id="doc-nuevo")
    _marcar(fabrica, "doc-nuevo", source_sha256="sha" + DOC)


def test_f061_r7_restaurar_linea_con_otro_activo_del_mismo_sha() -> None:
    fabrica, repo, ids = _retirado([{}])
    _otro_activo_mismo_sha(fabrica)
    with pytest.raises(DuplicadoActivoError) as error:
        repo.restore_registro(registro_id=ids[0])
    assert error.value.motivo == MOTIVO_DUPLICADO_ACTIVO
    # Nada escrito: ni la línea ni el parte.
    assert _reg(fabrica, ids[0]).deleted_at_utc is not None
    doc = _doc(fabrica)
    assert doc.is_active is False
    assert doc.deleted_by == "sin-lineas · ana"


def test_f061_r7_restaurar_linea_de_parte_en_papelera_de_partes() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}], doc_en_papelera=True)
    _otro_activo_mismo_sha(fabrica)
    with pytest.raises(DuplicadoActivoError):
        ParteReviewRepository(fabrica).restore_registro(registro_id=ids[0])
    assert _doc(fabrica).deleted_at_utc is not None
    assert _reg(fabrica, ids[0]).deleted_at_utc is not None


def test_f061_r7_restaurar_parte_con_otro_activo_del_mismo_sha() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{}], doc_en_papelera=True)
    _otro_activo_mismo_sha(fabrica)
    with pytest.raises(DuplicadoActivoError):
        ParteReviewRepository(fabrica).restore_document(document_id=DOC)
    doc = _doc(fabrica)
    assert (doc.is_active, doc.deleted_at_utc is not None) == (False, True)


def test_f061_r7_endpoints_responden_409_con_el_motivo() -> None:
    fabrica, repo, ids = _retirado([{}])
    _otro_activo_mismo_sha(fabrica)
    cliente = _cliente(repo)
    r = cliente.post(f"/api/registro/{ids[0]}/restore")
    assert r.status_code == 409
    assert r.json() == {"ok": False, "error": MOTIVO_DUPLICADO_ACTIVO}

    sembrar_parte(fabrica, [{}], document_id="doc-pap", doc_en_papelera=True)
    _marcar(fabrica, "doc-nuevo", source_sha256="shadoc-pap")
    r = cliente.post("/api/documento/doc-pap/restore")
    assert r.status_code == 409
    assert r.json() == {"ok": False, "error": MOTIVO_DUPLICADO_ACTIVO}


def test_f061_r7_sin_choque_los_endpoints_siguen_igual() -> None:
    fabrica, repo, ids = _retirado([{}])
    r = _cliente(repo).post(f"/api/registro/{ids[0]}/restore")
    assert (r.status_code, r.json()) == (200, {"ok": True})
    assert _doc(fabrica).is_active is True


# =============================== R8 =================================== #

def test_f061_r8_restaurar_parte_sin_vivas_devuelve_sus_lineas() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}, {"borrada": True}],
                        doc_en_papelera=True)
    assert ParteReviewRepository(fabrica).restore_document(
        document_id=DOC) is True
    assert _doc(fabrica).is_active is True
    assert all(_reg(fabrica, i).deleted_at_utc is None for i in ids)


def test_f061_r8_restaurar_parte_con_vivas_solo_el_parte() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}, {}],
                        doc_en_papelera=True)
    ParteReviewRepository(fabrica).restore_document(document_id=DOC)
    assert _reg(fabrica, ids[0]).deleted_at_utc is not None
    assert _reg(fabrica, ids[1]).deleted_at_utc is None


# ============================== R9–R11 ================================= #

def test_f061_r9_vaciar_borra_el_retirado_sin_filas() -> None:
    fabrica, repo, _ids = _retirado([{}, {}])
    res = repo.vaciar_papelera()
    assert res["registros"] == 2
    assert res["partes_borrados"] == 1
    assert _doc(fabrica) is None


def test_f061_r9_retirado_con_fila_que_vive_fuera_sigue() -> None:
    """F-004 R12 / F-019 R16: la fila registrada se omite; el parte queda."""
    fabrica, repo, _ids = _retirado([{"estado": "registrado",
                                      "borrada": True}, {}])
    res = repo.vaciar_papelera()
    assert (res["registros"], res["omitidos"]) == (1, 1)
    assert res.get("partes_borrados", 0) == 0
    doc = _doc(fabrica)
    assert doc is not None and doc.is_active is False
    assert _filas(fabrica) == 1


def test_f061_r11_vaciar_no_borra_lo_que_no_esta_retirado() -> None:
    fabrica = FabricaSesionSqlite()
    # Activo y sin filas (nació vacío, DA6).
    sembrar_parte(fabrica, [], document_id="d-activo-vacio")
    # Desactivado por el reemplazo de sv3: deleted_by NULL.
    sembrar_parte(fabrica, [], document_id="d-sv3")
    _marcar(fabrica, "d-sv3", is_active=False)
    # Inactivo con otra marca en deleted_by (no la de F-061).
    sembrar_parte(fabrica, [], document_id="d-otro")
    _marcar(fabrica, "d-otro", is_active=False, deleted_by="ana")
    # Retirado CON una fila viva (no debería existir, pero no se borra).
    sembrar_parte(fabrica, [{}], document_id="d-con-fila")
    _marcar(fabrica, "d-con-fila", is_active=False,
            deleted_by="sin-lineas · ana")
    res = ParteReviewRepository(fabrica).vaciar_papelera()
    assert res.get("partes_borrados", 0) == 0
    for did in ("d-activo-vacio", "d-sv3", "d-otro", "d-con-fila"):
        assert _doc(fabrica, did) is not None, did


def test_f061_r11_la_papelera_de_partes_sigue_como_hoy() -> None:
    """Un parte de la papelera de partes se borra por su rama de siempre."""
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{}], doc_en_papelera=True)
    res = ParteReviewRepository(fabrica).vaciar_papelera()
    assert res["documentos"] == 1
    assert res.get("partes_borrados", 0) == 0


def test_f061_r10_eliminar_la_ultima_fila_de_un_retirado_lo_borra() -> None:
    fabrica, repo, ids = _retirado([{}, {}])
    assert repo.hard_delete_registro(registro_id=ids[0]) is True
    assert _doc(fabrica) is not None           # le queda una fila
    assert repo.hard_delete_registro(registro_id=ids[1]) is True
    assert _doc(fabrica) is None


def test_f061_r10_eliminar_en_parte_no_retirado_no_lo_borra() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"borrada": True}])   # activo, legado
    ParteReviewRepository(fabrica).hard_delete_registro(registro_id=ids[0])
    assert _doc(fabrica) is not None
    assert _filas(fabrica) == 0


def test_f061_r10_r11_solo_el_parte_de_esa_fila() -> None:
    fabrica, repo, ids = _retirado([{}])
    sembrar_parte(fabrica, [], document_id="d-otro-retirado")
    _marcar(fabrica, "d-otro-retirado", is_active=False,
            deleted_by="sin-lineas")
    repo.hard_delete_registro(registro_id=ids[0])
    assert _doc(fabrica) is None
    assert _doc(fabrica, "d-otro-retirado") is not None
