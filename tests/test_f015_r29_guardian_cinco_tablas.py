# tests/test_f015_r29_guardian_cinco_tablas.py
"""R29 · el guardián de F-010 sigue mordiendo con la quinta tabla.

F-010 dejó `orm_models.py` duplicado byte a byte entre sv3 y sv4, con un
guardián que lo comprueba en cada `bash harness/init.sh`. F-015 añade
`empleado_jornada` a las DOS copias, y el riesgo evidente es que al
ampliar la lista de tablas del guardián se relaje algo por el camino: que
deje de mirar la tabla nueva, o que la lista literal de `parte_registros`
se toque «para que pase».

Estos tests son el guardián DEL guardián. No duplican F-010: comprueban
que sus utilidades siguen detectando una divergencia **en la tabla que
F-015 acaba de añadir**, alterando copias en `tmp_path` (el árbol real no
se toca nunca).

Sin red y sin BBDD: sistema de ficheros y compilación de tipos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.test_f010_orm_models_gemelos import (
    COLUMNAS_EMPLEADO_JORNADA,
    COLUMNAS_PARTE_REGISTROS,
    RUTA_SV3,
    RUTA_SV4,
    TABLAS,
    _cargar,
    _diferencias,
    _huella,
)

# ------------------------- la lista no se relaja ------------------------ #

def test_f015_r29_el_guardian_declara_cinco_tablas() -> None:
    assert TABLAS == (
        "empleado_alias",
        "empleado_jornada",
        "parte_documents",
        "parte_registros",
        "undo_log",
    )


def test_f015_r29_la_lista_de_parte_registros_sigue_siendo_de_56() -> None:
    """R21: F-015 no toca la tabla grande, así que su lista tampoco cambia."""
    assert len(COLUMNAS_PARTE_REGISTROS) == 56
    assert COLUMNAS_PARTE_REGISTROS[0] == "id"
    assert COLUMNAS_PARTE_REGISTROS[-1] == "confianza_pct"


def test_f015_r29_la_lista_de_empleado_jornada_es_literal_y_completa() -> None:
    assert len(COLUMNAS_EMPLEADO_JORNADA) == 19
    modulo = _cargar(RUTA_SV3, "orm_models_sv3_f015_r29_lista")
    columnas = tuple(
        c.name for c in modulo.Base.metadata.tables["empleado_jornada"].columns
    )
    assert columnas == COLUMNAS_EMPLEADO_JORNADA


def test_f015_r29_las_dos_copias_siguen_siendo_byte_identicas() -> None:
    """La barrera final de F-010, ya con la tabla nueva dentro."""
    assert RUTA_SV3.read_bytes() == RUTA_SV4.read_bytes()


# --------------------- el guardián detecta la alteración ---------------- #

def _quitar_la_clase_nueva(fuente: str) -> str:
    bloques = re.split(r"(?m)^(?=class )", fuente)
    return "".join(
        b for b in bloques if '__tablename__ = "empleado_jornada"' not in b
    )


def _quitar_el_indice_del_dni(fuente: str) -> str:
    return fuente.replace(
        'String(32), nullable=False, server_default="", index=True',
        'String(32), nullable=False, server_default=""',
        1,
    )


def _cambiar_el_tipo_de_una_columna_nueva(fuente: str) -> str:
    return fuente.replace(
        "    nota: Mapped[str | None] = mapped_column(String(255))",
        "    nota: Mapped[str | None] = mapped_column(String(120))",
        1,
    )


def _quitar_el_server_default_de_origen(fuente: str) -> str:
    return fuente.replace(
        'String(16), nullable=False, default="manual", server_default="manual"',
        'String(16), nullable=False, default="manual"',
        1,
    )


ALTERACIONES: tuple[tuple[str, object, str], ...] = (
    ("tabla_perdida", _quitar_la_clase_nueva, "empleado_jornada"),
    ("indice_perdido", _quitar_el_indice_del_dni, "dni_norm"),
    ("tipo_distinto", _cambiar_el_tipo_de_una_columna_nueva, "nota"),
    ("default_perdido", _quitar_el_server_default_de_origen, "origen"),
)


@pytest.mark.parametrize(
    "caso,alterar,esperado",
    ALTERACIONES,
    ids=[a[0] for a in ALTERACIONES],
)
def test_f015_r29_el_guardian_caza_una_divergencia_en_la_tabla_nueva(
    caso: str, alterar, esperado: str, tmp_path: Path
) -> None:
    """Alterar la tabla nueva en UNA copia tiene que salir por el guardián.

    Sin esto, la ampliación de F-010 podría estar mirando cuatro tablas y
    nadie se enteraría hasta que las dos copias divergieran de verdad.
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

    difs = _diferencias(
        _huella(_cargar(intacta, f"orm_f015_intacta_{caso}").Base.metadata),
        _huella(_cargar(tocada, f"orm_f015_tocada_{caso}").Base.metadata),
        etiqueta_a="intacta",
        etiqueta_b="tocada",
    )

    assert difs, f"el guardián NO detectó la alteración '{caso}'"
    assert any(esperado in d for d in difs), (
        f"el guardián detectó algo, pero no nombra '{esperado}'. Dijo:\n  - "
        + "\n  - ".join(difs)
    )


def test_f015_r29_el_arbol_real_no_se_toca(tmp_path: Path) -> None:
    antes = {ruta: ruta.read_bytes() for ruta in (RUTA_SV3, RUTA_SV4)}
    for _, alterar, _ in ALTERACIONES:
        (tmp_path / "copia.py").write_text(
            alterar(RUTA_SV3.read_text(encoding="utf-8")), encoding="utf-8"
        )
    assert {ruta: ruta.read_bytes() for ruta in (RUTA_SV3, RUTA_SV4)} == antes
