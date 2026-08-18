# tests/test_f010_r6_ddl_complementario.py
"""El DDL complementario se GENERA del ORM (F-010, R6/R9/R10).

`Base.metadata.create_all()` crea las tablas que faltan, pero no añade
columnas ni índices a una tabla que ya existe. Por eso sv3 y sv4
arrastraban cada uno su lista de `ALTER TABLE ... ADD COLUMN IF NOT
EXISTS` escrita a mano; y por eso las dos listas acabaron incompletas y
distintas (la de sv3 no cubría `sigrid_*` ni `deleted_*`, la de sv4 no
cubría `horas_orig`/`extra_auto`).

La cura es no escribirla a mano: `ddl_complementario()` la deriva del
propio ORM, así que una columna nueva trae su `ALTER` sin que nadie se
acuerde de añadirlo (R9). La función es PURA —compila contra el dialecto
PostgreSQL sin conexión— así que estos tests no tocan ni red ni BBDD.

Cobertura de requisitos:

- **R6 (a)** contenido: las sentencias literales que se esperan del ORM real.
- **R6 (b)** las columnas PRIMARIAS no llevan `ALTER` (ya existen con la tabla).
- **R6 (c)** orden y conteo deterministas, sobre un `MetaData` de juguete.
- **R6 (d)** idempotencia por construcción: todo lleva `IF NOT EXISTS`.
- **R9** ni una sola columna no primaria del ORM se queda sin su `ALTER`.
- **R10** el DDL es SOLO ADITIVO: nada que altere o borre lo que ya existe.
"""

from __future__ import annotations

from infrastructure.database.orm_models import (
    DDL_EXTRA_POSTGRES,
    Base,
    ddl_complementario,
)
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateColumn

#: Verbos que cambiarían o destruirían lo que la BBDD ya tiene. El DDL de
#: arranque se ejecuta en producción sin supervisión: si alguna vez emite
#: uno de estos, el despliegue toca datos reales de 41 partes.
VERBOS_PROHIBIDOS: tuple[str, ...] = (
    "ALTER COLUMN", "DROP ", "RENAME ", "TRUNCATE", "DELETE ", "UPDATE ",
)


def _metadata_de_juguete() -> MetaData:
    """Dos tablas mínimas, declaradas en orden inverso al alfabético.

    Sirve para fijar el orden de salida sin depender del ORM real: si el
    generador ordenara por orden de declaración en vez de por nombre, este
    `MetaData` lo delata.
    """
    metadata = MetaData()
    Table(
        "zeta", metadata,
        Column("id", Integer, primary_key=True),
        Column("b", String(8)),
        Column("a", Integer, index=True),
    )
    Table(
        "alfa", metadata,
        Column("id", Integer, primary_key=True),
        Column("x", Boolean, nullable=False, server_default="false"),
    )
    return metadata


# ------------------------------ R6 (a): contenido ----------------------- #


def test_f010_r6a_cubre_las_columnas_que_las_listas_a_mano_olvidaban() -> None:
    """Las columnas que cada servicio se dejaba fuera ahora salen solas."""
    sentencias = ddl_complementario()

    # Las que faltaban en la lista de sv4 (las escribe sv3).
    assert (
        "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS horas_orig FLOAT"
        in sentencias
    )
    assert (
        "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "
        "extra_auto BOOLEAN DEFAULT 'false' NOT NULL" in sentencias
    )
    # Las que faltaban en la lista de sv3 (las escribe sv4).
    assert (
        "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "
        "sigrid_estado VARCHAR(16)" in sentencias
    )
    assert (
        "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "
        "sigrid_hmores_ide INTEGER" in sentencias
    )
    # La tabla que sv3 ni siquiera declaraba.
    assert (
        "ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS actor VARCHAR(120)"
        in sentencias
    )


def test_f010_r6a_el_ddl_de_undo_log_es_el_esquema_real() -> None:
    """`undo_log` entera, tipo a tipo y NOT NULL a NOT NULL.

    sv3 no usa esta tabla —la escribe solo el portal—, pero la declara
    porque la base es una sola y las dos copias son gemelas. Justo por eso
    nadie la miraba: es donde una divergencia pasaria mas desapercibida.
    Se fija aqui el DDL entero, que es lo que se ejecuta en produccion.
    """
    sentencias = ddl_complementario()
    prefijo = "ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS "

    assert tuple(
        s[len(prefijo):] for s in sentencias if s.startswith(prefijo)
    ) == (
        "created_at_utc VARCHAR(40) NOT NULL",
        "action VARCHAR(40) NOT NULL",
        "description TEXT NOT NULL",
        "payload TEXT NOT NULL",
        "undone BOOLEAN NOT NULL",
        "actor VARCHAR(120)",
    )


def test_f010_r6a_el_ddl_de_la_traza_de_sigrid_es_el_esquema_real() -> None:
    """Las 7 columnas `sigrid_*`: las que faltaban en la copia de sv3.

    Las escribe sv4 y las va a leer sv3 (F-012 D7). Un VARCHAR mas corto
    de la cuenta aqui trunca el motivo de un registro fallido en Sigrid.
    """
    sentencias = ddl_complementario()
    prefijo = "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "

    assert tuple(
        s[len(prefijo):] for s in sentencias
        if s.startswith(prefijo + "sigrid_")
    ) == (
        "sigrid_estado VARCHAR(16)",
        "sigrid_registrado_at_utc VARCHAR(64)",
        "sigrid_registrado_by VARCHAR(255)",
        "sigrid_hmoide INTEGER",
        "sigrid_hmores_ide INTEGER",
        "sigrid_parte_cod VARCHAR(64)",
        "sigrid_motivo VARCHAR(255)",
    )


def test_f010_r6a_las_claves_primarias_son_autoincrementales() -> None:
    """`id` de `parte_registros` y `undo_log` es SERIAL, no un INTEGER pelado.

    No sale en el DDL complementario (una PK nace con la tabla), asi que
    se comprueba sobre la declaracion: sin autoincremento, insertar sin
    `id` explicito reventaria en PostgreSQL.
    """
    for tabla in ("parte_registros", "undo_log"):
        columna = Base.metadata.tables[tabla].columns["id"]
        assert columna.autoincrement is True, tabla
        assert str(
            CreateColumn(columna).compile(dialect=postgresql.dialect())
        ) == "id SERIAL NOT NULL", tabla


def test_f010_r6a_los_valores_por_defecto_de_python_son_los_esperados() -> None:
    """Defaults que NO viajan en el DDL pero deciden lo que se inserta.

    `extra_auto=True` por defecto marcaria como generada automaticamente
    toda linea nueva (y el recalculo de extras las borra y recrea);
    `undone=True` daria por deshecha cada accion nada mas registrarla.
    """
    registros = Base.metadata.tables["parte_registros"].columns
    assert registros["extra_auto"].default.arg is False
    assert registros["es_incidencia"].default.arg is False
    assert Base.metadata.tables["undo_log"].columns["undone"].default.arg is False


def test_f010_r6a_incluye_los_indices_declarados_y_el_parcial() -> None:
    """El índice que la BBDD no tenía (D3) y el único parcial de `partes`."""
    sentencias = ddl_complementario()

    assert (
        "CREATE INDEX IF NOT EXISTS ix_parte_registros_deleted_at_utc "
        "ON parte_registros (deleted_at_utc)" in sentencias
    )
    assert (
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active "
        "ON parte_documents (source_sha256) WHERE is_active" in sentencias
    )
    # `DDL_EXTRA_POSTGRES` va al final: es lo que el ORM no sabe expresar.
    assert sentencias[-len(DDL_EXTRA_POSTGRES):] == DDL_EXTRA_POSTGRES


# ------------------------------ R6 (b): PKs fuera ----------------------- #


def test_f010_r6b_las_columnas_primarias_no_llevan_alter() -> None:
    """Una PK nace con la tabla: un `ADD COLUMN` sobre ella no tiene sentido."""
    sentencias = ddl_complementario()

    assert not [s for s in sentencias if " ADD COLUMN IF NOT EXISTS id " in s]
    assert not [
        s for s in sentencias if " ADD COLUMN IF NOT EXISTS nombre_norm " in s
    ]


# --------------------- R6 (c): orden y conteo deterministas ------------- #


def test_f010_r6c_el_orden_y_el_conteo_son_deterministas() -> None:
    """Tablas por nombre, columnas por declaración, índices después."""
    sentencias = ddl_complementario(_metadata_de_juguete())

    assert sentencias[:4] == (
        "ALTER TABLE alfa ADD COLUMN IF NOT EXISTS x BOOLEAN DEFAULT 'false' NOT NULL",
        "ALTER TABLE zeta ADD COLUMN IF NOT EXISTS b VARCHAR(8)",
        "ALTER TABLE zeta ADD COLUMN IF NOT EXISTS a INTEGER",
        "CREATE INDEX IF NOT EXISTS ix_zeta_a ON zeta (a)",
    )
    # 3 columnas no primarias + 1 índice + los extras de PostgreSQL.
    assert len(sentencias) == 3 + 1 + len(DDL_EXTRA_POSTGRES)


def test_f010_r6c_los_indices_de_una_tabla_salen_en_orden_alfabetico() -> None:
    """`tabla.indexes` es un `set`: sin ordenar, el DDL cambia de orden.

    Un orden que baila hace que dos arranques emitan secuencias distintas
    y que el test de R7/R8 pase o falle segun el dia. `parte_registros`
    tiene tres indices, que es donde se nota.
    """
    indices = [
        s for s in ddl_complementario()
        if s.startswith("CREATE INDEX IF NOT EXISTS ix_parte_registros_")
    ]

    assert indices == sorted(indices)
    assert len(indices) == 3


def test_f010_r6c_dos_llamadas_dan_lo_mismo() -> None:
    """Función pura: el orden no depende de un `set` ni del recolector."""
    assert ddl_complementario() == ddl_complementario()
    assert isinstance(ddl_complementario(), tuple)


# --------------------------- R6 (d): idempotencia ----------------------- #


def test_f010_r6d_toda_sentencia_es_idempotente() -> None:
    """Arrancar dos veces el mismo servicio no puede reventar el arranque."""
    for sentencia in ddl_complementario():
        assert "IF NOT EXISTS" in sentencia, sentencia


# ------------------- R9: ninguna columna se queda fuera ----------------- #


def test_f010_r9_toda_columna_tiene_su_alter() -> None:
    """La propiedad que las dos listas a mano incumplían.

    Es el test que hace que F-015 (`EmpleadoJornadaOrm`) no tenga que
    acordarse de escribir DDL: si añade una columna sin `ALTER`, aquí salta.
    """
    sentencias = ddl_complementario()

    faltan: list[str] = []
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if columna.primary_key:
                continue
            prefijo = (
                f"ALTER TABLE {tabla.name} ADD COLUMN IF NOT EXISTS "
                f"{columna.name} "
            )
            if not any(s.startswith(prefijo) for s in sentencias):
                faltan.append(f"{tabla.name}.{columna.name}")

    assert not faltan, (
        "columnas declaradas en el ORM sin su ADD COLUMN IF NOT EXISTS "
        f"(no existirían en una tabla ya creada): {faltan}"
    )


# ----------------------------- R10: solo aditivo ------------------------ #


def test_f010_r10_ddl_solo_aditivo() -> None:
    """Contra una BBDD que ya lo tiene todo, el DDL entero es un no-op."""
    for sentencia in ddl_complementario():
        for verbo in VERBOS_PROHIBIDOS:
            assert verbo not in sentencia.upper(), (
                f"el DDL de arranque toca lo que ya existe ('{verbo}'): "
                f"{sentencia}"
            )


def test_f010_r10_ninguna_tabla_se_crea_sin_if_not_exists() -> None:
    """`create_all` crea las tablas; el complementario solo las completa."""
    for sentencia in ddl_complementario():
        if "CREATE TABLE" in sentencia.upper():
            assert "IF NOT EXISTS" in sentencia, sentencia
