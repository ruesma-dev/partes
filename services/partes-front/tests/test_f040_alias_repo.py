# tests/test_f040_alias_repo.py
"""F-040 · R20, R21: el alias aprendido contra el RECURSO: esquema en sv4.

  - R20: `EmpleadoAliasOrm` con `empleado_ide` nullable y la columna nueva
    `recurso_ide INTEGER NULL` (la copia de sv3 la vigila
    `tests/test_f010_orm_models_gemelos.py` de la raiz: byte-identicas).
  - R21: `ddl_complementario()` anade la columna y relaja el `NOT NULL` de
    `empleado_ide` con la sentencia de `DDL_EXTRA_POSTGRES`; nada de
    `UPDATE` de filas.
  - R18 y R19 (`upsert_empleado_alias` y el deshacer), en
    `tests/test_f040_alias.py`.

Sin red ni PostgreSQL: el DDL se compila sin conexion (sv4 lo ejecuta al
arrancar, `ParteReviewRepository.initialize`). Datos SINTETICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    DDL_EXTRA_POSTGRES,
    EmpleadoAliasOrm,
    ddl_complementario,
)

RELAJAR = ("ALTER TABLE empleado_alias ALTER COLUMN empleado_ide "
           "DROP NOT NULL")


# ============================== R20 =================================== #

def test_f040_sv4_r20_empleado_ide_es_nullable() -> None:
    assert EmpleadoAliasOrm.__table__.c.empleado_ide.nullable is True


def test_f040_sv4_r20_recurso_ide_integer_nullable_al_final() -> None:
    columna = EmpleadoAliasOrm.__table__.c.recurso_ide
    assert columna.nullable is True
    assert columna.type.python_type is int
    assert list(EmpleadoAliasOrm.__table__.c.keys())[-1] == "recurso_ide"


# ============================== R21 =================================== #

def test_f040_sv4_r21_ddl_anade_recurso_ide() -> None:
    assert ("ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS "
            "recurso_ide INTEGER") in ddl_complementario()


def test_f040_sv4_r21_ddl_relaja_empleado_ide_al_final() -> None:
    sentencias = ddl_complementario()
    assert RELAJAR in DDL_EXTRA_POSTGRES
    assert sentencias[-len(DDL_EXTRA_POSTGRES):] == DDL_EXTRA_POSTGRES
    # El `ADD COLUMN` de `empleado_ide` ya no lleva NOT NULL.
    assert ("ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS "
            "empleado_ide INTEGER") in sentencias


def test_f040_sv4_r21_ninguna_sentencia_reescribe_filas() -> None:
    for sentencia in ddl_complementario():
        assert "UPDATE " not in sentencia.upper(), sentencia
        assert "DELETE " not in sentencia.upper(), sentencia
