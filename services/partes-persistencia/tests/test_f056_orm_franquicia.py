# tests/test_f056_orm_franquicia.py
"""F-056 · R34: `franquicia_ajuste` en la copia de sv3 del ORM.

sv3 no lee ni escribe la tabla: solo la declara porque el schema de la base
`partes` es uno y `orm_models.py` es gemelo byte a byte del de sv4 (guardian
de raiz de F-010). Pero `create_all` la crea al arrancar sv3 si sv4 aun no lo
hizo, y la campana de mutacion juzga cada copia SOLO con la suite de su
servicio: sin estos tests, cualquier cambio de la copia de sv3 (un NOT NULL,
una longitud, el indice unico, la serie de la clave) pasaba en verde (22
supervivientes de la campana del 2026-10-29). Igual que F-019 hace con la
bandeja (`test_f019_orm_bandeja.py`).

Funcion pura: compila contra PostgreSQL sin conexion, y SQLite en memoria
con el MISMO ORM para el alta. Datos SINTETICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    Base,
    FranquiciaAjusteOrm,
    ddl_complementario,
)
from sqlalchemy import inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from tests.dobles import FabricaSesionSqlite

#: El DDL que crea `create_all` en PostgreSQL (R34), literal: tipo,
#: longitud, nulabilidad, `server_default` y la serie de la clave.
DDL_TABLA = """
CREATE TABLE franquicia_ajuste (
\tid SERIAL NOT NULL,
\trecurso_ide INTEGER DEFAULT '0' NOT NULL,
\tperiodo VARCHAR(7) DEFAULT '' NOT NULL,
\tfecha_int INTEGER DEFAULT '0' NOT NULL,
\tobra_ide INTEGER DEFAULT '0' NOT NULL,
\tobra_codigo VARCHAR(32),
\tpartida_ide INTEGER,
\tpartida_cod VARCHAR(32),
\tfranquicia FLOAT,
\textras FLOAT,
\tajuste FLOAT,
\testado VARCHAR(16) DEFAULT 'decidido' NOT NULL,
\tdecision VARCHAR(16),
\thmores_ide INTEGER,
\thmoide INTEGER,
\tparte_cod VARCHAR(32),
\tresultado TEXT,
\terror VARCHAR(255),
\tdecidido_por VARCHAR(120),
\taplicado_por VARCHAR(120),
\tdecidido_at_utc VARCHAR(64),
\taplicado_at_utc VARCHAR(64),
\tcreado_at_utc VARCHAR(64) DEFAULT '' NOT NULL,
\tactualizado_at_utc VARCHAR(64) DEFAULT '' NOT NULL,
\tPRIMARY KEY (id)
)

"""

P_AJ = "ALTER TABLE franquicia_ajuste ADD COLUMN IF NOT EXISTS "

#: Lo que el arranque anade a una tabla que ya existia (R34): el mismo
#: contrato, columna a columna, y los dos indices.
DDL_ARRANQUE = (
    P_AJ + "recurso_ide INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "periodo VARCHAR(7) DEFAULT '' NOT NULL",
    P_AJ + "fecha_int INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "obra_ide INTEGER DEFAULT '0' NOT NULL",
    P_AJ + "obra_codigo VARCHAR(32)",
    P_AJ + "partida_ide INTEGER",
    P_AJ + "partida_cod VARCHAR(32)",
    P_AJ + "franquicia FLOAT",
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


def test_f056_r34_sv3_ddl_de_la_tabla_literal() -> None:
    tabla = Base.metadata.tables["franquicia_ajuste"]
    ddl = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    # Linea a linea y sin el espacio final que SQLAlchemy deja tras cada
    # coma (los editores lo quitan del literal).
    assert [x.rstrip() for x in ddl.splitlines()] == DDL_TABLA.splitlines()


def test_f056_r34_sv3_ddl_de_arranque_literal() -> None:
    assert tuple(d for d in ddl_complementario()
                 if "franquicia_ajuste" in d) == DDL_ARRANQUE


def test_f056_r34_sv3_indices_unico_por_periodo_y_por_estado() -> None:
    tabla = Base.metadata.tables["franquicia_ajuste"]
    assert {(i.name, tuple(c.name for c in i.columns), i.unique)
            for i in tabla.indexes} == {
        ("ux_franquicia_ajuste_periodo", ("recurso_ide", "periodo"), True),
        ("ix_franquicia_ajuste_estado", ("estado",), False)}
    assert tabla.foreign_keys == set()


def test_f056_r34_sv3_clave_primaria_con_serie() -> None:
    col = FranquiciaAjusteOrm.__table__.c.id
    assert col.primary_key is True and col.autoincrement is True


def test_f056_r34_sv3_create_all_crea_la_tabla_y_numera_la_fila() -> None:
    fabrica = FabricaSesionSqlite()
    assert "franquicia_ajuste" in inspect(fabrica.engine).get_table_names()
    with fabrica.create_session() as s:
        s.add(FranquiciaAjusteOrm(recurso_ide=501, periodo="2026-10"))
        s.commit()
    with fabrica.create_session() as s:
        fila = s.execute(select(FranquiciaAjusteOrm)).scalars().one()
    assert (fila.id, fila.estado, fila.fecha_int, fila.obra_ide) == (
        1, "decidido", 0, 0)
