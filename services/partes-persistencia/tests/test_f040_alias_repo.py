# tests/test_f040_alias_repo.py
"""F-040 · R6, R20, R21: el alias aprendido contra el RECURSO, en sv3.

  - R20: `EmpleadoAliasOrm` con `empleado_ide` nullable y la columna nueva
    `recurso_ide INTEGER NULL` (la copia de sv4 la vigila
    `tests/test_f010_orm_models_gemelos.py` de la raiz: byte-identicas).
  - R21: `ddl_complementario()` anade la columna y relaja el `NOT NULL` de
    `empleado_ide` con la sentencia de `DDL_EXTRA_POSTGRES`; nada de
    `UPDATE` de filas.
  - R6: `find_empleado_alias` devuelve tambien `recurso_ide`.

Sin red ni PostgreSQL: el DDL se compila sin conexion y el repositorio
corre sobre SQLite en memoria. Datos SINTETICOS.
"""
from __future__ import annotations

from application.services import text_match as tm
from infrastructure.database.orm_models import (
    DDL_EXTRA_POSTGRES,
    EmpleadoAliasOrm,
    ddl_complementario,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite

RELAJAR = ("ALTER TABLE empleado_alias ALTER COLUMN empleado_ide "
           "DROP NOT NULL")


# ============================== R20 =================================== #

def test_f040_r20_empleado_ide_es_nullable() -> None:
    assert EmpleadoAliasOrm.__table__.c.empleado_ide.nullable is True


def test_f040_r20_recurso_ide_integer_nullable_al_final() -> None:
    columna = EmpleadoAliasOrm.__table__.c.recurso_ide
    assert columna.nullable is True
    assert columna.type.python_type is int
    assert list(EmpleadoAliasOrm.__table__.c.keys())[-1] == "recurso_ide"


# ============================== R21 =================================== #

def test_f040_r21_ddl_anade_recurso_ide() -> None:
    assert ("ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS "
            "recurso_ide INTEGER") in ddl_complementario()


def test_f040_r21_ddl_relaja_empleado_ide_al_final() -> None:
    sentencias = ddl_complementario()
    assert RELAJAR in DDL_EXTRA_POSTGRES
    assert sentencias[-len(DDL_EXTRA_POSTGRES):] == DDL_EXTRA_POSTGRES
    # El `ADD COLUMN` de `empleado_ide` ya no lleva NOT NULL.
    assert ("ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS "
            "empleado_ide INTEGER") in sentencias


def test_f040_r21_ninguna_sentencia_reescribe_filas() -> None:
    for sentencia in ddl_complementario():
        assert "UPDATE " not in sentencia.upper(), sentencia
        assert "DELETE " not in sentencia.upper(), sentencia


# =============================== R6 =================================== #

def _repo_con(**alias) -> SqlAlchemyParteRepository:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        s.add(EmpleadoAliasOrm(nombre_norm=tm.normalize("Pepe Leido"),
                               created_at_utc="2026-10-01T00:00:00Z",
                               **alias))
        s.commit()
    return SqlAlchemyParteRepository(fabrica)


def test_f040_r6_alias_sin_ficha_devuelve_recurso_ide() -> None:
    repo = _repo_con(empleado_ide=None, empleado_codigo="MO/9001",
                     empleado_nombre="PEPE RECURSO", empleado_dni=None,
                     recurso_ide=9001)
    assert repo.find_empleado_alias("pepe  LEIDO") == {
        "ide": None, "codigo": "MO/9001", "nombre": "PEPE RECURSO",
        "dni": None, "recurso_ide": 9001,
    }


def test_f040_r6_alias_de_ficha_devuelve_recurso_ide_none() -> None:
    repo = _repo_con(empleado_ide=10, empleado_codigo="E10",
                     empleado_nombre="PEPE FICHA", empleado_dni="00000001R")
    assert repo.find_empleado_alias("Pepe Leido") == {
        "ide": 10, "codigo": "E10", "nombre": "PEPE FICHA",
        "dni": "00000001R", "recurso_ide": None,
    }


def test_f040_r6_sin_alias_none() -> None:
    repo = _repo_con(empleado_ide=10)
    assert repo.find_empleado_alias("Otro Nombre") is None
    assert repo.find_empleado_alias("") is None
