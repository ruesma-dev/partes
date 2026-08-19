# tests/test_f015_r18_orm_empleado_jornada.py
"""R18 · `empleado_jornada` en el ORM de sv3 (y de sv4, byte a byte).

La tabla de excepciones de jornada nace VACIA y se espera que siga asi
mucho tiempo: su valor esta en existir con la forma correcta el dia que
haga falta una excepcion, sin tener que tocar el schema con partes ya
cargados. Aqui se fija esa forma —columnas, tipos, `nullable` y
`server_default`— y que `create_all` la crea de verdad.

`origen` esta desde el principio aunque hoy solo valga `manual`: el dia
que la excepcion venga de Sigrid (`auxtur`) o de Sesame no habra que
migrar nada.

Sin BBDD real: SQLite en memoria con el MISMO ORM que usa PostgreSQL.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    Base,
    EmpleadoJornadaOrm,
)
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

COLUMNAS = (
    "id", "dni_norm", "jornada_semanal",
    "h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom",
    "desde", "hasta", "origen", "nota", "is_active",
    "created_at_utc", "created_by", "updated_at_utc", "updated_by",
)


def _motor():
    from sqlalchemy.pool import StaticPool
    motor = create_engine(
        "sqlite://", future=True, poolclass=StaticPool,
        connect_args={"check_same_thread": False})
    Base.metadata.create_all(motor)
    return motor


# ------------------------------ declaracion ----------------------------- #

def test_f015_r18_la_tabla_esta_declarada_con_sus_columnas() -> None:
    tabla = Base.metadata.tables["empleado_jornada"]
    assert tuple(c.name for c in tabla.columns) == COLUMNAS


def test_f015_r18_el_dni_va_indexado() -> None:
    """Se consulta por DNI normalizado; sin indice seria un scan por celda."""
    tabla = Base.metadata.tables["empleado_jornada"]
    assert tabla.columns["dni_norm"].index is True
    assert "ix_empleado_jornada_dni_norm" in {i.name for i in tabla.indexes}


def test_f015_r18_los_defaults_de_origen_y_is_active() -> None:
    columnas = Base.metadata.tables["empleado_jornada"].columns
    assert columnas["origen"].default.arg == "manual"
    assert str(columnas["origen"].server_default.arg) == "manual"
    assert columnas["is_active"].default.arg is True
    assert str(columnas["is_active"].server_default.arg) == "true"


def test_f015_r18_la_vigencia_admite_hasta_abierto() -> None:
    columnas = Base.metadata.tables["empleado_jornada"].columns
    assert columnas["desde"].nullable is False
    assert columnas["hasta"].nullable is True


def test_f015_r18_el_patron_son_siete_columnas_opcionales() -> None:
    columnas = Base.metadata.tables["empleado_jornada"].columns
    dias = ("h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom")
    assert all(columnas[d].nullable for d in dias)
    assert len(dias) == 7


def test_f015_r18_parte_registros_no_gana_ni_pierde_columnas() -> None:
    """R21: F-015 no toca la tabla grande."""
    columnas = Base.metadata.tables["parte_registros"].columns
    assert len(columnas) == 56


# ------------------------------ create_all ------------------------------ #

def test_f015_r18_create_all_crea_la_tabla() -> None:
    motor = _motor()
    assert "empleado_jornada" in inspect(motor).get_table_names()


def test_f015_r18_se_puede_insertar_y_leer_una_excepcion() -> None:
    """Una fila de las que cargara el humano por SQL hasta F-016."""
    motor = _motor()
    sesion = sessionmaker(bind=motor, expire_on_commit=False, future=True)
    with sesion() as s:
        s.add(EmpleadoJornadaOrm(
            dni_norm="00000000T", jornada_semanal=48.0, desde="2026-01-01",
            created_at_utc="2026-08-19T00:00:00Z"))
        s.commit()
    with sesion() as s:
        fila = s.execute(select(EmpleadoJornadaOrm)).scalars().one()
    assert (fila.dni_norm, fila.jornada_semanal, fila.hasta) == (
        "00000000T", 48.0, None)
    # Los defaults de la papelera logica y del origen, sin escribirlos.
    assert (fila.is_active, fila.origen) == (True, "manual")


def test_f015_r18_se_puede_guardar_un_patron_de_siete_valores() -> None:
    motor = _motor()
    sesion = sessionmaker(bind=motor, expire_on_commit=False, future=True)
    with sesion() as s:
        s.add(EmpleadoJornadaOrm(
            dni_norm="00000000T", desde="2026-07-01", hasta="2026-09-01",
            h_lun=7.0, h_mar=7.0, h_mie=7.0, h_jue=7.0, h_vie=7.0,
            h_sab=0.0, h_dom=0.0, origen="manual",
            created_at_utc="2026-08-19T00:00:00Z"))
        s.commit()
    with sesion() as s:
        fila = s.execute(select(EmpleadoJornadaOrm)).scalars().one()
    assert [fila.h_lun, fila.h_mar, fila.h_mie, fila.h_jue, fila.h_vie,
            fila.h_sab, fila.h_dom] == [7.0] * 5 + [0.0, 0.0]
    assert fila.jornada_semanal is None
