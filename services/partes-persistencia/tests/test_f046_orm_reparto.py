# tests/test_f046_orm_reparto.py
"""F-046 · R39: `reparto_pendiente` entra en el DDL de arranque de sv3.

`create_all` crea la tabla si falta; `ddl_complementario()` (generado del
ORM, F-010) le anade columnas e indices si ya existiera. Funcion pura: se
compila contra el dialecto PostgreSQL sin abrir conexion.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    ESTADOS_REPARTO,
    REPARTO_PENDIENTE,
    Base,
    RepartoPendienteOrm,
    ddl_complementario,
)


def test_f046_r39_la_tabla_esta_en_el_esquema_de_sv3():
    assert "reparto_pendiente" in Base.metadata.tables
    assert RepartoPendienteOrm.__tablename__ == "reparto_pendiente"
    assert REPARTO_PENDIENTE == ESTADOS_REPARTO[0] == "pendiente"


def test_f046_r39_ddl_complementario_incluye_columnas_e_indices():
    ddl = ddl_complementario()
    propias = [d for d in ddl if "reparto_pendiente" in d]
    assert ("ALTER TABLE reparto_pendiente ADD COLUMN IF NOT EXISTS estado "
            "VARCHAR(16) DEFAULT 'pendiente' NOT NULL") in propias
    assert ("ALTER TABLE reparto_pendiente ADD COLUMN IF NOT EXISTS cambios "
            "TEXT DEFAULT '{}' NOT NULL") in propias
    assert any(d.startswith("CREATE INDEX IF NOT EXISTS "
                            "ix_reparto_pendiente_grupo ON reparto_pendiente "
                            "(recurso_ide, fecha_int)") for d in propias)
    assert any(d.startswith("CREATE INDEX IF NOT EXISTS "
                            "ix_reparto_pendiente_estado ON reparto_pendiente "
                            "(estado)") for d in propias)
    # 13 columnas no primarias + 2 indices.
    assert len(propias) == 15


def test_f046_r39_sin_nombres_ni_dnis():
    columnas = {c.name for c in RepartoPendienteOrm.__table__.columns}
    assert not any(p in c for c in columnas
                   for p in ("nombre", "dni", "cif"))
