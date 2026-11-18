# tests/test_f032_contrato_festivos.py
"""F-032 · R1 y R2: la tabla `festivos_trabajador` en las DOS copias del ORM.

R1: seis columnas, tipos, `server_default` en toda NOT NULL, indice UNICO
(`dni_norm`, `ano`) y sin `origen` ni `is_active` (DA19 = B: no hay fila
`*` ni se guarda el 404). R2: `create_all` sobre SQLite la crea sin tocar
las demas y `ddl_complementario()` trae su indice.

Patron de `test_f056_contrato_franquicia` / del guardian de F-010: cada
copia se carga por ruta como modulo independiente. Sin red ni BBDD real
(SQLite en memoria).
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

from tests.test_f010_orm_models_gemelos import RUTA_SV3, RUTA_SV4, _cargar

COLUMNAS = ("id", "dni_norm", "ano", "festivos_json", "n_festivos",
            "leido_en_utc")

P = "ALTER TABLE festivos_trabajador ADD COLUMN IF NOT EXISTS "
DDL_ESPERADO = (
    P + "dni_norm VARCHAR(32) DEFAULT '' NOT NULL",
    P + "ano INTEGER DEFAULT '0' NOT NULL",
    P + "festivos_json TEXT DEFAULT '{}' NOT NULL",
    P + "n_festivos INTEGER DEFAULT '0' NOT NULL",
    P + "leido_en_utc VARCHAR(40) DEFAULT '1970-01-01T00:00:00Z' NOT NULL",
    ("CREATE UNIQUE INDEX IF NOT EXISTS ux_festivos_trabajador_dni_ano "
     "ON festivos_trabajador (dni_norm, ano)"),
)


@pytest.fixture(scope="module", params=[("sv3", RUTA_SV3), ("sv4", RUTA_SV4)],
                ids=["sv3", "sv4"])
def modulo(request):
    etiqueta, ruta = request.param
    return _cargar(ruta, f"orm_models_{etiqueta}_f032")


def test_f032_r1_seis_columnas_literales(modulo):
    tabla = modulo.Base.metadata.tables["festivos_trabajador"]
    assert tuple(c.name for c in tabla.columns) == COLUMNAS


def test_f032_r1_sin_origen_ni_is_active(modulo):
    tabla = modulo.Base.metadata.tables["festivos_trabajador"]
    assert not {"origen", "is_active"} & set(tabla.c.keys())


def test_f032_r1_tipos_defaults_y_nulabilidad(modulo):
    tabla = modulo.Base.metadata.tables["festivos_trabajador"]
    assert tabla.c.id.primary_key is True
    assert tabla.c.id.autoincrement is True
    for col in tabla.columns:
        assert col.foreign_keys == set(), col.name
        if col.primary_key:
            continue
        assert col.nullable is False, col.name
        assert col.server_default is not None, col.name
    assert tabla.c.dni_norm.server_default.arg == ""
    assert tabla.c.ano.server_default.arg == "0"
    assert tabla.c.festivos_json.server_default.arg == "{}"
    assert tabla.c.n_festivos.server_default.arg == "0"
    assert tabla.c.leido_en_utc.server_default.arg == "1970-01-01T00:00:00Z"


def test_f032_r1_indice_unico_dni_ano(modulo):
    tabla = modulo.Base.metadata.tables["festivos_trabajador"]
    assert {i.name: (tuple(c.name for c in i.columns), i.unique)
            for i in tabla.indexes} == {
        "ux_festivos_trabajador_dni_ano": (("dni_norm", "ano"), True)}


def test_f032_r1_clase_orm_expuesta(modulo):
    assert modulo.FestivoTrabajadorOrm.__tablename__ == "festivos_trabajador"


def test_f032_r2_ddl_complementario_trae_columnas_e_indice(modulo):
    ddl = tuple(d for d in modulo.ddl_complementario()
                if "festivos_trabajador" in d)
    assert ddl == DDL_ESPERADO


def test_f032_r2_create_all_sobre_sqlite_la_crea_sin_tocar_las_demas(modulo):
    engine = create_engine("sqlite://")
    # Una base «vieja»: todas las tablas menos la nueva.
    viejas = [t for n, t in modulo.Base.metadata.tables.items()
              if n != "festivos_trabajador"]
    modulo.Base.metadata.create_all(engine, tables=viejas)
    insp = inspect(engine)
    assert "festivos_trabajador" not in insp.get_table_names()
    antes = {n: [c["name"] for c in insp.get_columns(n)]
             for n in insp.get_table_names()}

    modulo.Base.metadata.create_all(engine)

    insp = inspect(engine)
    assert "festivos_trabajador" in insp.get_table_names()
    assert [c["name"] for c in insp.get_columns("festivos_trabajador")] == \
        list(COLUMNAS)
    unicos = [i for i in insp.get_indexes("festivos_trabajador")
              if i["unique"]]
    assert [i["column_names"] for i in unicos] == [["dni_norm", "ano"]]
    assert {n: [c["name"] for c in insp.get_columns(n)]
            for n in antes} == antes
