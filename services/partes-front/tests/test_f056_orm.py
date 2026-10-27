# tests/test_f056_orm.py
"""F-056 · R1, R34: `empleado_franquicia` y `franquicia_ajuste` en la copia
de sv4 del ORM, columna a columna (tipo, longitud, nulabilidad y
`server_default`) a traves del DDL de arranque, que es lo que llega a
PostgreSQL.

El guardian de gemelos de la raiz compara las DOS copias; este test fija la
de sv4 por si sola (la campana de mutacion juzga cada copia con la suite de
su servicio). Funcion pura: compila contra PostgreSQL sin conexion.
"""
from __future__ import annotations

from infrastructure.database import orm_models as orm
from infrastructure.database.orm_models import (
    EmpleadoFranquiciaOrm,
    FranquiciaAjusteOrm,
    ddl_complementario,
)

P_EMP = "ALTER TABLE empleado_franquicia ADD COLUMN IF NOT EXISTS "
P_AJ = "ALTER TABLE franquicia_ajuste ADD COLUMN IF NOT EXISTS "

DDL_EMPLEADO_FRANQUICIA = (
    P_EMP + "dni_norm VARCHAR(32) DEFAULT '' NOT NULL",
    P_EMP + "horas FLOAT DEFAULT '0' NOT NULL",
    P_EMP + "desde VARCHAR(16) DEFAULT '1900-01-01' NOT NULL",
    P_EMP + "hasta VARCHAR(16)",
    P_EMP + "nota VARCHAR(255)",
    P_EMP + "is_active BOOLEAN DEFAULT 'true' NOT NULL",
    P_EMP + "created_at_utc VARCHAR(40) DEFAULT '1970-01-01T00:00:00Z' "
            "NOT NULL",
    P_EMP + "created_by VARCHAR(120)",
    P_EMP + "updated_at_utc VARCHAR(40)",
    P_EMP + "updated_by VARCHAR(120)",
    ("CREATE INDEX IF NOT EXISTS ix_empleado_franquicia_dni_norm "
     "ON empleado_franquicia (dni_norm)"),
)

DDL_FRANQUICIA_AJUSTE = (
    P_AJ + "recurso_ide INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "periodo VARCHAR(7) DEFAULT '' NOT NULL",
    P_AJ + "fecha_int INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "obra_ide INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "obra_codigo VARCHAR(32)",
    P_AJ + "partida_ide INTEGER",
    P_AJ + "partida_cod VARCHAR(32)",
    P_AJ + "franquicia FLOAT DEFAULT '0' NOT NULL",
    P_AJ + "extras FLOAT",
    P_AJ + "ajuste FLOAT",
    P_AJ + "estado VARCHAR(16) DEFAULT 'decidido' NOT NULL",
    P_AJ + "decision VARCHAR(16)",
    P_AJ + "hmores_ide INTEGER",
    P_AJ + "hmoide INTEGER",
    P_AJ + "parte_cod VARCHAR(32)",
    P_AJ + "resultado TEXT",
    P_AJ + "error VARCHAR(255)",
    P_AJ + "decidido_por VARCHAR(120)",
    P_AJ + "aplicado_por VARCHAR(120)",
    P_AJ + "decidido_at_utc VARCHAR(64)",
    P_AJ + "aplicado_at_utc VARCHAR(64)",
    P_AJ + "creado_at_utc VARCHAR(64) DEFAULT '' NOT NULL",
    P_AJ + "actualizado_at_utc VARCHAR(64) DEFAULT '' NOT NULL",
    ("CREATE INDEX IF NOT EXISTS ix_franquicia_ajuste_estado "
     "ON franquicia_ajuste (estado)"),
    ("CREATE UNIQUE INDEX IF NOT EXISTS ux_franquicia_ajuste_periodo "
     "ON franquicia_ajuste (recurso_ide, periodo)"),
)


def test_f056_r1_ddl_literal_de_empleado_franquicia():
    assert tuple(d for d in ddl_complementario()
                 if "empleado_franquicia" in d) == DDL_EMPLEADO_FRANQUICIA


def test_f056_r34_ddl_literal_de_franquicia_ajuste():
    assert tuple(d for d in ddl_complementario()
                 if "franquicia_ajuste" in d) == DDL_FRANQUICIA_AJUSTE


def test_f056_r34_claves_primarias_con_serie():
    for modelo in (EmpleadoFranquiciaOrm, FranquiciaAjusteOrm):
        col = modelo.__table__.c.id
        assert col.primary_key is True and col.autoincrement is True


def test_f056_r34_sin_fk_ni_nombres_ni_dnis_en_el_ajuste():
    """El ajuste no guarda nombres ni DNIs: el trabajador es su
    `recurso_ide` de Sigrid (design §5)."""
    tabla = FranquiciaAjusteOrm.__table__
    assert all(not c.foreign_keys for c in tabla.columns)
    assert not {"dni", "dni_norm", "nombre", "empleado_nombre"} & set(
        tabla.c.keys())


def test_f056_r34_estados_del_ajuste():
    assert (orm.FRANQUICIA_DECIDIDO, orm.FRANQUICIA_APLICADO,
            orm.FRANQUICIA_RECHAZADO, orm.FRANQUICIA_ERROR) == (
        "decidido", "aplicado", "rechazado", "error")
    assert orm.ESTADOS_FRANQUICIA == ("decidido", "aplicado", "rechazado",
                                      "error")
