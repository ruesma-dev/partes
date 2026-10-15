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


# F-046 (mutacion): la copia de sv3, columna a columna, por si sola.
PREFIJO = "ALTER TABLE reparto_pendiente ADD COLUMN IF NOT EXISTS "

DDL_REPARTO_PENDIENTE = (
    PREFIJO + "recurso_ide INTEGER DEFAULT '0' NOT NULL",
    PREFIJO + "fecha_int INTEGER DEFAULT '0' NOT NULL",
    PREFIJO + "estado VARCHAR(16) DEFAULT 'pendiente' NOT NULL",
    PREFIJO + "firma VARCHAR(64) DEFAULT '' NOT NULL",
    PREFIJO + "cambios TEXT DEFAULT '{}' NOT NULL",
    PREFIJO + "resultado TEXT",
    PREFIJO + "error VARCHAR(255)",
    PREFIJO + "decision VARCHAR(16)",
    PREFIJO + "decidido_por VARCHAR(120)",
    PREFIJO + "decidido_at_utc VARCHAR(64)",
    PREFIJO + "creado_at_utc VARCHAR(64) DEFAULT '' NOT NULL",
    PREFIJO + "actualizado_at_utc VARCHAR(64) DEFAULT '' NOT NULL",
    PREFIJO + "materializado_at_utc VARCHAR(64)",
    ("CREATE INDEX IF NOT EXISTS ix_reparto_pendiente_estado "
     "ON reparto_pendiente (estado)"),
    ("CREATE INDEX IF NOT EXISTS ix_reparto_pendiente_grupo "
     "ON reparto_pendiente (recurso_ide, fecha_int)"),
)


def test_f046_r39_ddl_literal_de_reparto_pendiente_sv3():
    assert tuple(d for d in ddl_complementario()
                 if "reparto_pendiente" in d) == DDL_REPARTO_PENDIENTE


def test_f046_r39_clave_primaria_con_serie_sv3():
    col = RepartoPendienteOrm.__table__.c.id
    assert col.primary_key is True and col.autoincrement is True
