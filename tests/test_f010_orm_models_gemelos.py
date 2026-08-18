# tests/test_f010_orm_models_gemelos.py
"""Guardián de las dos copias de `orm_models.py` (F-010, R1–R4).

El schema PostgreSQL de `partes` está declarado DOS veces a propósito
(sv3 `partes-persistencia` y sv4 `partes-front`): son la única duplicación
tolerada del monorepo junto con los clientes de Sigrid/Sesame. «Tolerada»
significa que quien toca una copia toca la otra en la misma feature — una
promesa que nadie comprobaba y que ya se había roto: sv3 declaraba
`horas_orig`/`extra_auto` que faltaban en sv4, y sv4 las siete `sigrid_*`
y `UndoLogOrm` que faltaban en sv3.

Estos tests convierten la promesa en una propiedad verificada por
`bash harness/init.sh`:

- **R1** (barrera final): los dos ficheros son BYTE-IDÉNTICOS. La primera
  línea —el comentario de ruta relativa que exige `docs/CONVENTIONS.md`—
  coincide porque la ruta relativa AL SERVICIO es la misma en los dos.
- **R2** (diagnóstico legible): las dos declaraciones producen el mismo
  schema (tablas, columnas, tipos compilados a PostgreSQL, nullable, PK,
  server_default, index, unique, FKs e índices). R1 implica R2; R2 existe
  para que un fallo diga QUÉ columna difiere en vez de escupir un diff.
- **R3**: el guardián muerde de verdad. Se alteran copias en `tmp_path`
  (nunca el árbol real) y se exige que la comparación las cace nombrando
  el elemento divergente.
- **R4**: el contenido canónico es la UNIÓN de lo que declaraba cada copia
  (D1 del diseño): cuatro tablas y las 56 columnas reales de
  `parte_registros`, ni una más ni una menos.

Sin red, sin BBDD y sin conexión: solo sistema de ficheros y compilación
de tipos de SQLAlchemy contra el dialecto PostgreSQL.
"""

from __future__ import annotations

import difflib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import MetaData
from sqlalchemy.dialects import postgresql

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_f010_...py`.
RAIZ = Path(__file__).resolve().parents[1]

#: Las dos copias toleradas, con su nombre corto para los mensajes de error.
RUTA_SV3 = RAIZ / "services/partes-persistencia/infrastructure/database/orm_models.py"
RUTA_SV4 = RAIZ / "services/partes-front/infrastructure/database/orm_models.py"
COPIAS: tuple[tuple[str, Path], ...] = (("sv3", RUTA_SV3), ("sv4", RUTA_SV4))

DIALECTO = postgresql.dialect()

#: Las 56 columnas de `parte_registros` tras la resincronización (R4), en
#: orden de declaración. Lista LITERAL a propósito: si alguien añade o quita
#: una columna, este test le obliga a declararlo aquí y, por tanto, a mirar
#: si la BBDD real la tiene. La cuenta se comprobó contra
#: `information_schema.columns` el 2026-08-18.
COLUMNAS_PARTE_REGISTROS: tuple[str, ...] = (
    "id",
    "document_id",
    "line_index",
    "empleado_line_no",
    "categoria",
    "trabajador_nombre_leido",
    "empleado_ide",
    "empleado_codigo",
    "empleado_nombre",
    "empleado_dni",
    "empleado_reside",
    "empleado_match_score",
    "empleado_match_method",
    "fecha",
    "fecha_int",
    "obra_codigo",
    "obra_nombre",
    "obra_ide",
    "tipo_hora",
    "deleted_at_utc",
    "deleted_by",
    "es_incidencia",
    "incidencia_codigo",
    "incidencia_texto",
    "incidencia_dias",
    "horas",
    "partida",
    "partida_ide",
    "partida_cod",
    "partida_res",
    "partida_capitulo",
    "partida_match_method",
    "partida_match_score",
    "recurso_ide",
    "recurso_cif",
    "hmo_ide",
    "parte_estado",
    "sigrid_estado",
    "sigrid_registrado_at_utc",
    "sigrid_registrado_by",
    "sigrid_hmoide",
    "sigrid_hmores_ide",
    "sigrid_parte_cod",
    "sigrid_motivo",
    "hora_ide",
    "hora_codigo",
    "hora_descripcion",
    "hora_ext",
    "hora_precio_coste",
    "hora_precio_nomina",
    "hora_candef",
    "recurso_precio_hora",
    "horas_orig",
    "extra_auto",
    "hora_match_method",
    "confianza_pct",
)

#: Las CUATRO tablas de la base `partes` (no tres, como decía la doc).
TABLAS: tuple[str, ...] = (
    "empleado_alias",
    "parte_documents",
    "parte_registros",
    "undo_log",
)


# ------------------------------ utilidades ------------------------------ #


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    """Carga un `orm_models.py` como módulo independiente, por ruta.

    Cada copia define su propio `Base`, así que dos módulos cargados a la
    vez NO colisionan en el registry de SQLAlchemy. El módulo se registra
    en `sys.modules` antes de ejecutarlo porque SQLAlchemy resuelve las
    anotaciones `Mapped[...]` (que son cadenas por `from __future__ import
    annotations`) mirando ahí el namespace del módulo que declara la clase.
    """
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, f"no se pudo cargar {ruta}"
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _huella(metadata: MetaData) -> dict:
    """Schema declarado, reducido a datos comparables e imprimibles.

    El tipo se COMPILA al dialecto PostgreSQL (`VARCHAR(64)`, `FLOAT`,
    `TEXT`...) para que `String(64)` y `String(65)` salgan distintos y
    legibles en el mensaje de fallo, en vez de dos `repr` de objetos.
    """
    huella: dict = {}
    for nombre_tabla, tabla in metadata.tables.items():
        columnas: dict = {}
        for columna in tabla.columns:
            defecto = columna.server_default
            columnas[columna.name] = {
                "tipo": str(columna.type.compile(dialect=DIALECTO)),
                "nullable": bool(columna.nullable),
                "pk": bool(columna.primary_key),
                "server_default": None if defecto is None else str(defecto.arg),
                "index": bool(columna.index),
                "unique": bool(columna.unique),
                "fks": sorted(fk.target_fullname for fk in columna.foreign_keys),
            }
        huella[nombre_tabla] = {
            "columnas": columnas,
            "indices": {
                indice.name: (
                    tuple(c.name for c in indice.columns),
                    bool(indice.unique),
                )
                for indice in tabla.indexes
            },
        }
    return huella


def _diferencias(huella_a: dict, huella_b: dict, *,
                 etiqueta_a: str = "A", etiqueta_b: str = "B") -> list[str]:
    """Diferencias entre dos huellas, una por línea y nombrando el elemento.

    Devuelve una lista vacía si son equivalentes. Cada diferencia nombra la
    tabla, la columna (o el índice) y el atributo, que es lo que hace falta
    para arreglarla sin abrir un diff de 250 líneas.
    """
    difs: list[str] = []

    solo_a = sorted(set(huella_a) - set(huella_b))
    solo_b = sorted(set(huella_b) - set(huella_a))
    for tabla in solo_a:
        difs.append(f"tabla '{tabla}': solo en {etiqueta_a}")
    for tabla in solo_b:
        difs.append(f"tabla '{tabla}': solo en {etiqueta_b}")

    for tabla in sorted(set(huella_a) & set(huella_b)):
        cols_a = huella_a[tabla]["columnas"]
        cols_b = huella_b[tabla]["columnas"]
        for columna in sorted(set(cols_a) - set(cols_b)):
            difs.append(f"{tabla}.{columna}: columna solo en {etiqueta_a}")
        for columna in sorted(set(cols_b) - set(cols_a)):
            difs.append(f"{tabla}.{columna}: columna solo en {etiqueta_b}")
        for columna in sorted(set(cols_a) & set(cols_b)):
            for atributo in sorted(cols_a[columna]):
                valor_a = cols_a[columna][atributo]
                valor_b = cols_b[columna][atributo]
                if valor_a != valor_b:
                    difs.append(
                        f"{tabla}.{columna}.{atributo}: "
                        f"{etiqueta_a}={valor_a!r} != {etiqueta_b}={valor_b!r}"
                    )

        idx_a = huella_a[tabla]["indices"]
        idx_b = huella_b[tabla]["indices"]
        for indice in sorted(set(idx_a) - set(idx_b)):
            difs.append(f"{tabla}: indice '{indice}' solo en {etiqueta_a}")
        for indice in sorted(set(idx_b) - set(idx_a)):
            difs.append(f"{tabla}: indice '{indice}' solo en {etiqueta_b}")
        for indice in sorted(set(idx_a) & set(idx_b)):
            if idx_a[indice] != idx_b[indice]:
                difs.append(
                    f"{tabla}: indice '{indice}': "
                    f"{etiqueta_a}={idx_a[indice]!r} != {etiqueta_b}={idx_b[indice]!r}"
                )
    return difs


# --------------------------------- R1 ----------------------------------- #


def test_f010_r1_las_dos_copias_son_byte_identicas() -> None:
    """Las dos copias de `orm_models.py` son el MISMO fichero, byte a byte."""
    bytes_sv3 = RUTA_SV3.read_bytes()
    bytes_sv4 = RUTA_SV4.read_bytes()

    if bytes_sv3 != bytes_sv4:
        diff = "\n".join(
            difflib.unified_diff(
                bytes_sv3.decode("utf-8").splitlines(),
                bytes_sv4.decode("utf-8").splitlines(),
                fromfile=str(RUTA_SV3.relative_to(RAIZ)),
                tofile=str(RUTA_SV4.relative_to(RAIZ)),
                lineterm="",
            )
        )
        pytest.fail(
            "las dos copias de orm_models.py han divergido: quien toca una "
            "tiene que tocar la otra en la misma feature (CLAUDE.md, LIMITE "
            f"DE SERVICIO). Diferencias:\n{diff}"
        )


# --------------------------------- R2 ----------------------------------- #


def test_f010_r2_las_dos_copias_declaran_el_mismo_schema() -> None:
    """Mismas tablas, columnas, tipos, defaults e índices en las dos copias."""
    sv3 = _cargar(RUTA_SV3, "orm_models_sv3_r2")
    sv4 = _cargar(RUTA_SV4, "orm_models_sv4_r2")

    difs = _diferencias(
        _huella(sv3.Base.metadata),
        _huella(sv4.Base.metadata),
        etiqueta_a="sv3",
        etiqueta_b="sv4",
    )

    assert not difs, (
        "las dos copias de orm_models.py declaran schemas distintos "
        "(la BBDD 'partes' es una sola):\n  - " + "\n  - ".join(difs)
    )


# --------------------------------- R3 ----------------------------------- #


def _alterar_anadiendo_columna(fuente: str) -> str:
    return fuente.replace(
        "    confianza_pct: Mapped[float | None] = mapped_column(Float)",
        "    confianza_pct: Mapped[float | None] = mapped_column(Float)\n"
        "    columna_intrusa: Mapped[str | None] = mapped_column(String(8))",
        1,
    )


def _alterar_cambiando_el_tipo(fuente: str) -> str:
    return fuente.replace(
        "    empleado_dni: Mapped[str | None] = mapped_column(String(64))",
        "    empleado_dni: Mapped[str | None] = mapped_column(String(65))",
        1,
    )


def _alterar_quitando_el_indice(fuente: str) -> str:
    return fuente.replace(
        "    empleado_ide: Mapped[int | None] = mapped_column(Integer, index=True)",
        "    empleado_ide: Mapped[int | None] = mapped_column(Integer)",
        1,
    )


def _alterar_quitando_una_clase(fuente: str) -> str:
    """Elimina el bloque de la clase que mapea `empleado_alias`.

    Se corta por `^class ` en lugar de por líneas en blanco: es lo único
    que no depende del formateo del fichero.
    """
    bloques = re.split(r"(?m)^(?=class )", fuente)
    return "".join(b for b in bloques if '__tablename__ = "empleado_alias"' not in b)


#: (nombre del caso, alteración, texto que DEBE aparecer en la diferencia).
ALTERACIONES: tuple[tuple[str, object, str], ...] = (
    ("columna_de_mas", _alterar_anadiendo_columna, "columna_intrusa"),
    ("tipo_distinto", _alterar_cambiando_el_tipo, "empleado_dni"),
    ("indice_perdido", _alterar_quitando_el_indice, "empleado_ide"),
    ("clase_perdida", _alterar_quitando_una_clase, "empleado_alias"),
)


@pytest.mark.parametrize(
    "caso,alterar,esperado",
    ALTERACIONES,
    ids=[a[0] for a in ALTERACIONES],
)
def test_f010_r3_el_guardian_detecta_una_copia_alterada(
    caso: str, alterar, esperado: str, tmp_path: Path
) -> None:
    """Alterar UNA copia hace fallar la comparación, nombrando el elemento.

    Sin este test, un guardián roto (que comparase siempre igual, o que
    mirase un atributo que nunca cambia) pasaría por bueno para siempre. Se
    trabaja sobre copias en `tmp_path`: el árbol real no se toca.
    """
    original = RUTA_SV3.read_text(encoding="utf-8")
    alterada = alterar(original)
    assert alterada != original, (
        f"la alteración '{caso}' no cambió nada: el fuente de referencia ha "
        f"cambiado y el test estaría comprobando el vacío"
    )

    intacta = tmp_path / "intacta.py"
    tocada = tmp_path / "tocada.py"
    intacta.write_text(original, encoding="utf-8")
    tocada.write_text(alterada, encoding="utf-8")

    modulo_intacto = _cargar(intacta, f"orm_models_intacta_{caso}")
    modulo_tocado = _cargar(tocada, f"orm_models_tocada_{caso}")

    difs = _diferencias(
        _huella(modulo_intacto.Base.metadata),
        _huella(modulo_tocado.Base.metadata),
        etiqueta_a="intacta",
        etiqueta_b="tocada",
    )

    assert difs, f"el guardián NO detectó la alteración '{caso}'"
    assert any(esperado in d for d in difs), (
        f"el guardián detectó algo, pero no nombra '{esperado}', así que no "
        f"se puede arreglar leyendo el fallo. Dijo:\n  - " + "\n  - ".join(difs)
    )


def test_f010_r3_el_arbol_real_no_se_toca(tmp_path: Path) -> None:
    """Control: los casos de R3 escriben en `tmp_path`, nunca en el repo."""
    antes = {ruta: ruta.read_bytes() for _, ruta in COPIAS}

    for _, alterar, _ in ALTERACIONES:
        (tmp_path / "copia.py").write_text(
            alterar(RUTA_SV3.read_text(encoding="utf-8")), encoding="utf-8"
        )

    assert {ruta: ruta.read_bytes() for _, ruta in COPIAS} == antes


# --------------------------------- R4 ----------------------------------- #


def test_f010_r4_el_orm_canonico_tiene_las_cuatro_tablas_y_56_columnas() -> None:
    """Contenido canónico = UNIÓN de las dos copias de partida (D1)."""
    modulo = _cargar(RUTA_SV3, "orm_models_sv3_r4")
    metadata = modulo.Base.metadata

    assert tuple(sorted(metadata.tables)) == TABLAS, (
        "la base 'partes' tiene CUATRO tablas (undo_log solo la escribe sv4)"
    )

    columnas = tuple(c.name for c in metadata.tables["parte_registros"].columns)
    assert columnas == COLUMNAS_PARTE_REGISTROS, (
        "parte_registros no declara exactamente las 56 columnas reales de la "
        "BBDD (comprobadas contra information_schema el 2026-08-18). Sobran: "
        f"{sorted(set(columnas) - set(COLUMNAS_PARTE_REGISTROS))}; faltan: "
        f"{sorted(set(COLUMNAS_PARTE_REGISTROS) - set(columnas))}"
    )
    assert len(columnas) == 56


def test_f010_r4_los_atributos_de_las_columnas_reunidas() -> None:
    """Las columnas que aportaba cada copia conservan tipo, nullable y default.

    R4 exige que la unión no cambie NADA de lo que ya declaraba la copia
    que tenía la columna: la BBDD real ya está creada con esos tipos.
    """
    modulo = _cargar(RUTA_SV3, "orm_models_sv3_r4_attrs")
    huella = _huella(modulo.Base.metadata)
    registros = huella["parte_registros"]["columnas"]

    # Lo que aportaba sv3.
    assert registros["horas_orig"] == {
        "tipo": "FLOAT", "nullable": True, "pk": False,
        "server_default": None, "index": False, "unique": False, "fks": [],
    }
    assert registros["extra_auto"]["tipo"] == "BOOLEAN"
    assert registros["extra_auto"]["nullable"] is False
    assert registros["extra_auto"]["server_default"] == "false"

    # Lo que aportaba sv4.
    assert registros["sigrid_estado"]["tipo"] == "VARCHAR(16)"
    assert registros["sigrid_hmoide"]["tipo"] == "INTEGER"
    assert registros["sigrid_hmores_ide"]["tipo"] == "INTEGER"
    assert registros["sigrid_registrado_at_utc"]["tipo"] == "VARCHAR(64)"
    assert registros["sigrid_registrado_by"]["tipo"] == "VARCHAR(255)"
    assert registros["sigrid_parte_cod"]["tipo"] == "VARCHAR(64)"
    assert registros["sigrid_motivo"]["tipo"] == "VARCHAR(255)"

    # El índice que la BBDD no tenía y que F-010 crea (D3).
    assert registros["deleted_at_utc"]["index"] is True
    assert (
        "ix_parte_registros_deleted_at_utc"
        in huella["parte_registros"]["indices"]
    )

    # `undo_log` (7 columnas), que solo declaraba sv4.
    undo = huella["undo_log"]["columnas"]
    assert tuple(undo) == (
        "id", "created_at_utc", "action", "description", "payload",
        "undone", "actor",
    )
    assert undo["actor"]["tipo"] == "VARCHAR(120)"
    assert undo["payload"]["nullable"] is False
