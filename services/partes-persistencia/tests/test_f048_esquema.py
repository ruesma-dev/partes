# tests/test_f048_esquema.py
"""F-048 · la columna `parte_registros.horas_extra_leidas` (R6, R24).

La ingesta suma las extras leidas > 0 de cada fila a su ordinaria y guarda
en esta columna la parte de cada registro que la IA leyo como extra: solo
traza. `Float`, nula y sin defecto en las dos copias del ORM (la gemela de
sv4 la vigila `tests/test_f010_orm_models_gemelos.py` en la raiz);
`ddl_complementario` la anade a la tabla ya creada. Ni red ni PostgreSQL:
el DDL se compila sin conexion y el guardado va sobre SQLite en memoria.
"""
from __future__ import annotations

import dataclasses

from domain.models.parte_records import (
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
)
from infrastructure.database.orm_models import (
    ParteRegistroOrm,
    ddl_complementario,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from sqlalchemy import Float, select
from tests.dobles import FabricaSesionSqlite

SENTENCIA = ("ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "
             "horas_extra_leidas FLOAT")


def test_f048_r24_ddl_complementario_anade_la_columna() -> None:
    assert SENTENCIA in ddl_complementario()


def test_f048_r24_columna_float_nula_y_sin_defecto() -> None:
    columna = ParteRegistroOrm.__table__.c.horas_extra_leidas
    assert isinstance(columna.type, Float)
    assert columna.nullable is True
    assert columna.default is None
    assert columna.server_default is None


def test_f048_r24_columna_justo_tras_horas_orig() -> None:
    nombres = [c.name for c in ParteRegistroOrm.__table__.columns]
    assert nombres.index("horas_extra_leidas") == nombres.index(
        "horas_orig") + 1


def test_f048_r2_el_registro_normalizado_la_lleva_nula_por_defecto() -> None:
    campos = {f.name: f for f in dataclasses.fields(RegistroNormalizado)}
    assert "horas_extra_leidas" in campos
    assert RegistroNormalizado(line_index=0).horas_extra_leidas is None


def _guardar(fabrica, registros: list[RegistroNormalizado]) -> None:
    parte = ParteDocumento(
        fecha_iso="2026-03-02", fecha_int=20260302, obra_numero_leido="100",
        obra=ObraMatch(ide=10, codigo="0100", method="codigo"))
    parte.registros.extend(registros)
    SqlAlchemyParteRepository(fabrica).save_parte(  # type: ignore[arg-type]
        document_id="doc-f048", parte=parte, meta={}, context={},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=False)


def test_f048_r6_save_parte_guarda_y_se_relee() -> None:
    fabrica = FabricaSesionSqlite()
    _guardar(fabrica, [
        RegistroNormalizado(line_index=0, tipo_hora="normal", horas=9.0,
                            horas_extra_leidas=5.0),
        RegistroNormalizado(line_index=1, tipo_hora="normal", horas=8.0),
        RegistroNormalizado(line_index=2, tipo_hora="extra", horas=-2.0),
    ])
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.line_index, ParteRegistroOrm.horas,
                   ParteRegistroOrm.horas_extra_leidas)
            .order_by(ParteRegistroOrm.line_index)).all()
    assert [tuple(f) for f in filas] == [
        (0, 9.0, 5.0), (1, 8.0, None), (2, -2.0, None)]
