# tests/test_f047_parte_nuevo_sv3.py
"""F-047 · R1-R10: sv3 marca el parte nuevo «en espera» y lo da por repartido.

Al guardar un parte nuevo con el conciliador de recurso y el seguimiento
cableados, `save_parte` escribe `recalculo_pedido_id` = id del documento
en el mismo commit (R1); tras las dos conciliaciones, si la de recurso no
lanzó, el pipeline llama a `marcar_terminado(document_id, document_id)`
(R4). Un fallo no se propaga (R5, R6). El UPDATE condicional de F-043
respeta un pedido posterior de sv4 (R7).

`save_parte` real sobre SQLite en memoria (mismo ORM); el pipeline, con
dobles que apuntan eventos. Ni red, ni PostgreSQL, ni Sigrid. Datos
sintéticos.
"""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import select

from domain.models.parte_records import (
    EmpleadoMatch,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
)
from domain.ports.parte_repository import ParteRepository
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

DOC = "00000000-0000-4000-8000-000000000047"
DNI = "12345678Z"          # el de `sembrar_lineas`: mismo trabajador


class _FabricaContadora(FabricaSesionSqlite):
    """La fábrica de SQLite que cuenta los `commit` de sus sesiones."""

    def __init__(self) -> None:
        super().__init__()
        self.commits = 0

    def create_session(self):
        sesion = super().create_session()
        original = sesion.commit

        def _commit() -> None:
            self.commits += 1
            original()

        sesion.commit = _commit  # type: ignore[method-assign]
        return sesion


def _parte(*, fecha_int: int = 20260320, obra: str = "0100") -> ParteDocumento:
    return ParteDocumento(
        fecha_iso=f"{str(fecha_int)[:4]}-{str(fecha_int)[4:6]}-"
                  f"{str(fecha_int)[6:]}",
        fecha_int=fecha_int, firmado=True,
        obra=ObraMatch(ide=10, codigo=obra, method="codigo"),
        registros=[RegistroNormalizado(
            line_index=0, empleado_line_no=1, tipo_hora="normal", horas=10.0,
            trabajador_nombre_leido="ANA FICTICIA",
            empleado=EmpleadoMatch(ide=None, dni=DNI, reside=501,
                                   method="recurso_dni"))])


def _guardar(repo: SqlAlchemyParteRepository, document_id: str = DOC,
             **extra) -> None:
    repo.save_parte(
        document_id=document_id, parte=_parte(), meta={},
        context={"document": {"sha256": "sha-" + document_id}},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=False, **extra)


def _doc(fabrica, document_id: str = DOC) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.execute(select(ParteDocumentOrm)
                         .where(ParteDocumentOrm.id == document_id)
                         ).scalar_one()


def _seguimiento(doc: ParteDocumentOrm) -> tuple:
    return (doc.recalculo_pedido_id, doc.recalculo_pedido_at_utc,
            doc.recalculo_terminado_id, doc.recalculo_terminado_at_utc)


# ===================== R1, R2, R8, R9 · save_parte ====================== #

def test_f047_r1_save_parte_escribe_el_pedido_en_el_mismo_commit() -> None:
    fabrica = _FabricaContadora()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=DOC)
    doc = _doc(fabrica)
    assert fabrica.commits == 1
    assert doc.recalculo_pedido_id == DOC
    # La hora del pedido es la del guardado (la de `created_at_utc`).
    assert doc.recalculo_pedido_at_utc == doc.created_at_utc
    assert doc.recalculo_pedido_at_utc.endswith("+00:00")
    assert doc.recalculo_terminado_id is None
    assert doc.recalculo_terminado_at_utc is None
    with fabrica.create_session() as s:
        assert len(s.get(ParteDocumentOrm, DOC).registros) == 1


def test_f047_r2_save_parte_sin_pedido_deja_las_cuatro_a_null() -> None:
    fabrica = FabricaSesionSqlite()
    _guardar(SqlAlchemyParteRepository(fabrica))
    assert _seguimiento(_doc(fabrica)) == (None, None, None, None)


def test_f047_r2_save_parte_con_pedido_none_igual_que_sin_el() -> None:
    fabrica = FabricaSesionSqlite()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=None)
    assert _seguimiento(_doc(fabrica)) == (None, None, None, None)


def test_f047_r8_save_parte_reemplazo_solo_marca_el_nuevo() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 8.0}], document_id="doc-viejo")
    with fabrica.create_session() as s:
        viejo = s.get(ParteDocumentOrm, "doc-viejo")
        viejo.recalculo_pedido_id = "pedido-viejo"
        viejo.recalculo_pedido_at_utc = "2026-03-20T08:00:00+00:00"
        s.commit()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=DOC)
    viejo = _doc(fabrica, "doc-viejo")
    assert viejo.is_active is False          # el reemplazo ocurrió
    assert _seguimiento(viejo) == ("pedido-viejo",
                                   "2026-03-20T08:00:00+00:00", None, None)
    assert _doc(fabrica).recalculo_pedido_id == DOC


def test_f047_r9_save_parte_parametro_opcional_en_el_puerto() -> None:
    for funcion in (ParteRepository.save_parte,
                    SqlAlchemyParteRepository.save_parte):
        parametro = inspect.signature(funcion).parameters[
            "recalculo_pedido_id"]
        assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
        assert parametro.default is None
