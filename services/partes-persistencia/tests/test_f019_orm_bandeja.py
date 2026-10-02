# tests/test_f019_orm_bandeja.py
"""F-019 · la bandeja de salida hacia dedicacion en el ORM de sv3 (R29).

sv3 no escribe ni lee la bandeja: solo declara la tabla porque el schema
de la base `partes` es uno y `orm_models.py` es gemelo byte a byte del de
sv4 (guardian de raiz de F-010). Aqui se fija su DDL COMPILADO a
PostgreSQL entero, igual que en sv4, para que la copia de sv3 tenga sus
propios tests: `create_all` la crea al arrancar sv3 si sv4 aun no lo hizo.

Sin BBDD real: SQLite en memoria con el MISMO ORM. Datos SINTETICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import Base, DedicacionBandejaOrm
from sqlalchemy import inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from tests.dobles import FabricaSesionSqlite

#: El DDL que crea `create_all` en PostgreSQL (R29), literal.
DDL_BANDEJA = """
CREATE TABLE dedicacion_bandeja (
\tregistro_id INTEGER NOT NULL, 
\tversion INTEGER DEFAULT '1' NOT NULL, 
\tvigente BOOLEAN DEFAULT 'true' NOT NULL, 
\trecurso_ide INTEGER DEFAULT '0' NOT NULL, 
\tcodigo_mes VARCHAR(16) DEFAULT '' NOT NULL, 
\tfecha_int INTEGER DEFAULT '0' NOT NULL, 
\tanio INTEGER DEFAULT '0' NOT NULL, 
\tmes INTEGER DEFAULT '0' NOT NULL, 
\tobra_ide INTEGER, 
\tobra_codigo VARCHAR(64), 
\tobra_empresa INTEGER, 
\tpartida_ide INTEGER, 
\tpartida_cod VARCHAR(64), 
\ttipo VARCHAR(16) DEFAULT '' NOT NULL, 
\thoras FLOAT, 
\tincidencia_codigo VARCHAR(8), 
\tincidencia_clase VARCHAR(16), 
\tprueba BOOLEAN DEFAULT 'false' NOT NULL, 
\tenviado_por VARCHAR(255), 
\tenviado_at_utc VARCHAR(64), 
\tretirado_por VARCHAR(255), 
\tretirado_at_utc VARCHAR(64), 
\tactualizado_at_utc VARCHAR(64) DEFAULT '' NOT NULL, 
\tPRIMARY KEY (registro_id)
)

"""


# ============================== T4 · el ORM (R29) ============================== #

def test_f019_r29_sv3_ddl_de_la_bandeja_literal() -> None:
    tabla = Base.metadata.tables["dedicacion_bandeja"]
    ddl = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    assert ddl == DDL_BANDEJA


def test_f019_r29_sv3_indice_por_periodo_y_sin_fk() -> None:
    tabla = Base.metadata.tables["dedicacion_bandeja"]
    assert {(i.name, tuple(c.name for c in i.columns), i.unique)
            for i in tabla.indexes} == {
        ("ix_dedicacion_bandeja_periodo", ("anio", "mes"), False)}
    assert tabla.foreign_keys == set()


def test_f019_r29_sv3_create_all_crea_la_bandeja_y_admite_una_fila() -> None:
    fabrica = FabricaSesionSqlite()
    assert "dedicacion_bandeja" in inspect(fabrica.engine).get_table_names()
    with fabrica.create_session() as s:
        s.add(DedicacionBandejaOrm(
            registro_id=7, version=1, vigente=True, recurso_ide=602,
            codigo_mes="MENC", fecha_int=20260302, anio=2026, mes=3,
            tipo="normal", horas=-1.5, prueba=False,
            actualizado_at_utc="2026-03-02T08:00:00+00:00"))
        s.commit()
    with fabrica.create_session() as s:
        fila = s.execute(select(DedicacionBandejaOrm)).scalars().one()
    assert (fila.registro_id, fila.horas, fila.obra_ide) == (7, -1.5, None)


def test_f019_r29_sv3_parte_registros_sigue_con_56_columnas() -> None:
    assert len(Base.metadata.tables["parte_registros"].columns) == 56
