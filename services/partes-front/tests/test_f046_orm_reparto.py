# tests/test_f046_orm_reparto.py
"""F-046 · R39: `reparto_pendiente` en la copia de sv4 del ORM, columna a
columna (tipo, longitud, nulabilidad y `server_default`) a traves del DDL
de arranque, que es lo que llega a PostgreSQL.

El guardian de gemelos de la raiz compara las DOS copias; este test fija la
de sv4 por si sola (la campana de mutacion juzga cada copia con la suite de
su servicio). Funcion pura: compila contra PostgreSQL sin conexion.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    RepartoPendienteOrm,
    ddl_complementario,
)

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


def test_f046_r39_ddl_literal_de_reparto_pendiente():
    assert tuple(d for d in ddl_complementario()
                 if "reparto_pendiente" in d) == DDL_REPARTO_PENDIENTE


def test_f046_r39_clave_primaria_con_serie():
    col = RepartoPendienteOrm.__table__.c.id
    assert col.primary_key is True and col.autoincrement is True
