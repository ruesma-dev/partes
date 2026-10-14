# tests/test_f046_aprobar_documento.py
"""F-046 · R36: aprobar un documento con lineas en un grupo con reparto
`pendiente`, `aplicando` o `rechazado` se rechaza con un motivo (DA13).

Repositorio contra SQLite en memoria; la ruta, con el cliente de pruebas
de FastAPI en T17. Datos sinteticos.
"""
from __future__ import annotations

import pytest
from application.services.reparto_aviso import (
    MOTIVO_APROBAR_CON_REPARTO,
    RepartoPendienteError,
)
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    RepartoPendienteOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _reparto(fabrica, estado="pendiente", fecha=20260302) -> int:
    with fabrica.create_session() as s:
        f = RepartoPendienteOrm(recurso_ide=501, fecha_int=fecha,
                                estado=estado, firma="f", cambios="{}",
                                creado_at_utc="x", actualizado_at_utc="x")
        s.add(f)
        s.commit()
        return f.id


def _aprobado(fabrica, doc) -> bool:
    with fabrica.create_session() as s:
        return bool(s.get(ParteDocumentOrm, doc).approved)


@pytest.mark.parametrize("estado", ["pendiente", "aplicando", "rechazado"])
def test_f046_r36_repositorio_aprobar_con_reparto_vivo_se_rechaza(
        fabrica, estado):
    sembrar_parte(fabrica, [{"horas": 5.5}], document_id="doc-704")
    _reparto(fabrica, estado)
    repo = ParteReviewRepository(fabrica)  # type: ignore[arg-type]
    with pytest.raises(RepartoPendienteError) as exc:
        repo.approve_document(document_id="doc-704", approved_by="a")
    assert exc.value.motivo == MOTIVO_APROBAR_CON_REPARTO
    assert not _aprobado(fabrica, "doc-704")


@pytest.mark.parametrize("estado", ["aplicado", "materializado",
                                    "mantenido", "obsoleto"])
def test_f046_r36_repositorio_otros_estados_no_bloquean(fabrica, estado):
    sembrar_parte(fabrica, [{"horas": 5.5}], document_id="doc-704")
    _reparto(fabrica, estado)
    repo = ParteReviewRepository(fabrica)  # type: ignore[arg-type]
    assert repo.approve_document(document_id="doc-704", approved_by="a")
    assert _aprobado(fabrica, "doc-704")


def test_f046_r36_repositorio_reparto_de_otro_dia_no_bloquea(fabrica):
    sembrar_parte(fabrica, [{"horas": 5.5}], document_id="doc-704")
    _reparto(fabrica, fecha=20260303)
    repo = ParteReviewRepository(fabrica)  # type: ignore[arg-type]
    assert repo.approve_document(document_id="doc-704", approved_by="a")


def test_f046_r36_repositorio_linea_en_papelera_no_bloquea(fabrica):
    sembrar_parte(fabrica, [{"horas": 5.5, "borrada": True}],
                  document_id="doc-704")
    _reparto(fabrica)
    repo = ParteReviewRepository(fabrica)  # type: ignore[arg-type]
    assert repo.approve_document(document_id="doc-704", approved_by="a")
