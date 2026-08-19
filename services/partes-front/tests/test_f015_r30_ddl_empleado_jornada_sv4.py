# tests/test_f015_r30_ddl_empleado_jornada_sv4.py
"""R30 · el arranque crea `empleado_jornada` sin intervencion manual.

Este proyecto no tiene ficheros `NN_nombre.sql`: el schema vive en el ORM
y los servicios lo materializan al arrancar con `create_all()` +
`ddl_complementario()` (F-010). La tabla nueva sigue ese camino, asi que
lo unico que hay que comprobar es que el generador la cubre ENTERA: si se
quedara una columna fuera, la tabla existiria a medias en una base que ya
la tuviera y el fallo aparecerian meses despues.

`ddl_complementario()` es pura (compila contra el dialecto PostgreSQL sin
abrir conexion): ni red ni BBDD.
"""
from __future__ import annotations

from infrastructure.database.orm_models import Base, ddl_complementario

PREFIJO = "ALTER TABLE empleado_jornada ADD COLUMN IF NOT EXISTS "


def _de_la_tabla() -> tuple[str, ...]:
    return tuple(s for s in ddl_complementario() if "empleado_jornada" in s)


def test_f015_r30_sv4_hay_un_alter_por_columna_no_primaria() -> None:
    alters = [s for s in ddl_complementario() if s.startswith(PREFIJO)]
    columnas = [
        c.name for c in Base.metadata.tables["empleado_jornada"].columns
        if not c.primary_key
    ]
    assert len(alters) == len(columnas) == 18


def test_f015_r30_sv4_el_ddl_de_la_tabla_es_el_esperado() -> None:
    """Literal: los tipos son los que va a tener la tabla en PostgreSQL."""
    assert tuple(
        s[len(PREFIJO):] for s in ddl_complementario() if s.startswith(PREFIJO)
    ) == (
        "dni_norm VARCHAR(32) DEFAULT '' NOT NULL",
        "jornada_semanal FLOAT",
        "h_lun FLOAT",
        "h_mar FLOAT",
        "h_mie FLOAT",
        "h_jue FLOAT",
        "h_vie FLOAT",
        "h_sab FLOAT",
        "h_dom FLOAT",
        "desde VARCHAR(16) DEFAULT '1900-01-01' NOT NULL",
        "hasta VARCHAR(16)",
        "origen VARCHAR(16) DEFAULT 'manual' NOT NULL",
        "nota VARCHAR(255)",
        "is_active BOOLEAN DEFAULT 'true' NOT NULL",
        "created_at_utc VARCHAR(40) DEFAULT '1970-01-01T00:00:00Z' NOT NULL",
        "created_by VARCHAR(120)",
        "updated_at_utc VARCHAR(40)",
        "updated_by VARCHAR(120)",
    )


def test_f015_r30_sv4_el_indice_del_dni_se_crea() -> None:
    assert (
        "CREATE INDEX IF NOT EXISTS ix_empleado_jornada_dni_norm "
        "ON empleado_jornada (dni_norm)" in ddl_complementario()
    )


def test_f015_r30_sv4_la_tabla_aporta_exactamente_19_sentencias() -> None:
    """18 columnas no primarias + 1 indice: ni una mas."""
    assert len(_de_la_tabla()) == 19


def test_f015_r30_sv4_ninguna_columna_not_null_se_queda_sin_default() -> None:
    """Sin `server_default`, un `ADD COLUMN NOT NULL` sobre una tabla con
    filas hace que PostgreSQL rechace el DDL y el servicio no arranque."""
    sin_default = [
        c.name for c in Base.metadata.tables["empleado_jornada"].columns
        if not c.nullable and not c.primary_key and c.server_default is None
    ]
    assert sin_default == []


def test_f015_r30_sv4_toda_sentencia_de_la_tabla_es_idempotente() -> None:
    for sentencia in _de_la_tabla():
        assert "IF NOT EXISTS" in sentencia, sentencia


def test_f015_r30_sv4_el_ddl_de_la_tabla_es_solo_aditivo() -> None:
    for sentencia in _de_la_tabla():
        for verbo in ("ALTER COLUMN", "DROP ", "RENAME ", "DELETE ", "UPDATE "):
            assert verbo not in sentencia.upper(), sentencia


def test_f015_r30_sv4_las_demas_tablas_no_ganan_ni_pierden_sentencias() -> None:
    """El total crece EXACTAMENTE en lo que aporta la tabla nueva."""
    total = len(ddl_complementario())
    otras = [s for s in ddl_complementario() if "empleado_jornada" not in s]
    assert total - len(otras) == 19
