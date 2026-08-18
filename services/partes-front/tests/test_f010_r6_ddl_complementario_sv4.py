# tests/test_f010_r6_ddl_complementario_sv4.py
"""El generador de DDL, comprobado tambien en LA COPIA DE sv4 (F-010 R6/R9).

`orm_models.py` esta duplicado a proposito en sv3 y sv4, y el guardian de
la raiz (`tests/test_f010_orm_models_gemelos.py`) exige que las dos copias
sean byte-identicas. Siendo asi, ¿por que probar el generador dos veces?

Porque cada suite solo ejercita el codigo de SU servicio. La copia de sv4
es la que ejecuta el portal al arrancar, y sin estos tests lo unico que la
tocaba en la suite de sv4 era el test de `initialize()` (R8), que compara
lo ejecutado contra `ddl_complementario()` del MISMO modulo: si el
generador se estropeara, los dos lados cambiarian a la vez y el test
seguiria en verde. La campana de mutacion de F-010 lo enseño en crudo —
mutantes de la copia de sv4 que sobrevivian a las 456 pruebas del portal
mientras sus gemelos morian en sv3.

Se comprueban aqui las propiedades que importan del DDL que sv4 lanza
contra la base compartida; el detalle exhaustivo vive en la suite de sv3
(`test_f010_r6_ddl_complementario.py`). Sin red ni BBDD: la funcion es
pura.
"""

from __future__ import annotations

from infrastructure.database.orm_models import (
    DDL_EXTRA_POSTGRES,
    Base,
    ddl_complementario,
)


def test_f010_r6_sv4_genera_el_ddl_de_las_columnas_de_los_dos_servicios() -> None:
    """Lo que escribe sv4 y lo que escribe sv3, en la misma lista."""
    sentencias = ddl_complementario()
    prefijo = "ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS "

    # Las que escribe el portal.
    assert prefijo + "sigrid_estado VARCHAR(16)" in sentencias
    assert prefijo + "sigrid_registrado_by VARCHAR(255)" in sentencias
    assert prefijo + "sigrid_motivo VARCHAR(255)" in sentencias
    # Las que escribe sv3 y al portal se le habian olvidado.
    assert prefijo + "horas_orig FLOAT" in sentencias
    assert (
        prefijo + "extra_auto BOOLEAN DEFAULT 'false' NOT NULL" in sentencias
    )
    # La tabla que solo usa el portal.
    assert (
        "ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS actor VARCHAR(120)"
        in sentencias
    )
    assert (
        "ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS undone BOOLEAN NOT NULL"
        in sentencias
    )


def test_f010_r6_sv4_todo_es_idempotente_y_solo_aditivo() -> None:
    """El portal arranca muchas veces al dia: el DDL no puede tocar datos."""
    for sentencia in ddl_complementario():
        assert "IF NOT EXISTS" in sentencia, sentencia
        for verbo in ("ALTER COLUMN", "DROP ", "RENAME ", "TRUNCATE",
                      "DELETE ", "UPDATE "):
            assert verbo not in sentencia.upper(), sentencia


def test_f010_r6_sv4_los_indices_salen_en_orden_alfabetico() -> None:
    """`tabla.indexes` es un `set`: sin ordenar, cada arranque emitiria otro
    orden y la comparacion de R8 pasaria o fallaria segun el dia."""
    indices = [
        s for s in ddl_complementario()
        if s.startswith("CREATE INDEX IF NOT EXISTS ix_parte_registros_")
    ]

    assert indices == sorted(indices)
    assert len(indices) == 3


def test_f010_r6_sv4_el_indice_parcial_va_al_final() -> None:
    """Lo que el ORM no sabe expresar se aplica despues de lo generado."""
    assert ddl_complementario()[-len(DDL_EXTRA_POSTGRES):] == DDL_EXTRA_POSTGRES
    assert DDL_EXTRA_POSTGRES == (
        (
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active "
            "ON parte_documents (source_sha256) WHERE is_active"
        ),
    )


def test_f010_r9_sv4_toda_columna_tiene_su_alter() -> None:
    """Ninguna columna del ORM se queda sin existir en una tabla ya creada."""
    sentencias = ddl_complementario()

    faltan = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if not columna.primary_key
        and not any(
            s.startswith(
                f"ALTER TABLE {tabla.name} ADD COLUMN IF NOT EXISTS "
                f"{columna.name} "
            )
            for s in sentencias
        )
    ]

    assert not faltan, faltan


def test_f010_r6_sv4_los_valores_por_defecto_son_los_esperados() -> None:
    """Defaults que no viajan en el DDL pero deciden lo que inserta el portal.

    `extra_auto=True` por defecto marcaria como generada por el computo de
    extras cada linea que crease el portal (y el recalculo las borra y
    recrea); `undone=True` daria por deshecha cada accion nada mas
    registrarla, dejando el boton de deshacer sin nada que deshacer.
    """
    registros = Base.metadata.tables["parte_registros"].columns
    assert registros["extra_auto"].default.arg is False
    assert registros["es_incidencia"].default.arg is False
    assert Base.metadata.tables["undo_log"].columns["undone"].default.arg is False
