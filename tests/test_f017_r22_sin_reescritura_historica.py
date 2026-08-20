# tests/test_f017_r22_sin_reescritura_historica.py
"""Guardián del corte de auditoría de F-017 (R22).

F-017 no reescribe ni una fila histórica: ni migración, ni `UPDATE`, ni valor
inventado. El motivo no es pereza — es que **rellenar un `NULL` de autor con
cualquier nombre sería inventar una firma**, y eso no es una migración, es
falsificar una auditoría. `NULL` ya dice la verdad: «no se sabe».

Lo que este guardián protege es la propiedad que hace útil ese corte:

> `autor IS NULL` ⇔ «fila anterior al despliegue de F-017»

Es un criterio exacto, comprobable con una consulta y sin guardar la fecha en
ninguna parte, y es el que F-018 va a heredar (`design.md` §12). Se sostiene
sobre dos cosas, y aquí se vigilan las dos:

1. **Las columnas de autor no cambian** de nombre ni de ancho, en las **dos**
   copias del ORM. Si alguien las ensanchara o las renombrara, las filas
   antiguas dejarían de ser comparables con las nuevas.
2. **Nadie reescribe esas columnas en masa.** No existe en el árbol ningún
   `UPDATE` sobre ellas ni ningún `.sql` de migración nuevo.

Sin red, sin BBDD: solo lectura del árbol y del ORM.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_f017_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_SV3 = RAIZ / "services/partes-persistencia/infrastructure/database/orm_models.py"
RUTA_SV4 = RAIZ / "services/partes-front/infrastructure/database/orm_models.py"
COPIAS: tuple[tuple[str, Path], ...] = (("sv3", RUTA_SV3), ("sv4", RUTA_SV4))

#: Las siete columnas de autor del portal, con su ancho declarado
#: (`design.md` §3, confirmado contra la base real el 2026-08-20). El ancho
#: importa: el mínimo común —120— es el que fija `ACTOR_MAX_LEN`, y por eso
#: F-017 puede truncar una vez y no tocar el schema.
COLUMNAS_DE_AUTOR: tuple[tuple[str, str, int], ...] = (
    ("ParteDocumentOrm", "approved_by", 255),
    ("ParteDocumentOrm", "deleted_by", 255),
    ("ParteRegistroOrm", "deleted_by", 255),
    ("ParteRegistroOrm", "sigrid_registrado_by", 255),
    ("EmpleadoAliasOrm", "created_by", 120),
    ("EmpleadoJornadaOrm", "created_by", 120),
    ("EmpleadoJornadaOrm", "updated_by", 120),
    ("UndoLogOrm", "actor", 120),
)

#: El ancho más estrecho manda: es el que `identidad.py` usa para truncar.
ANCHO_MINIMO = 120


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _bloque_de_clase(fuente: str, clase: str) -> str:
    """El cuerpo de una clase del ORM, hasta la siguiente `class`."""
    inicio = fuente.index(f"class {clase}(Base):")
    resto = fuente[inicio + 1:]
    siguiente = resto.find("\nclass ")
    return resto if siguiente == -1 else resto[:siguiente]


# ====================================================================== #
# (a) Las columnas de autor conservan nombre y ancho, en las DOS copias
# ====================================================================== #

@pytest.mark.parametrize("copia, ruta", COPIAS)
@pytest.mark.parametrize("clase, columna, ancho", COLUMNAS_DE_AUTOR)
def test_f017_r22_las_columnas_de_autor_no_cambian(
        copia: str, ruta: Path, clase: str, columna: str,
        ancho: int) -> None:
    """Mismo nombre y mismo ancho que antes del corte, en sv3 y en sv4.

    Se comprueba en las dos copias porque `orm_models.py` está duplicado a
    propósito y el que las desincroniza rompe la base compartida.
    """
    bloque = _bloque_de_clase(_fuente(ruta), clase)
    patron = rf"{columna}:\s*Mapped\[[^\]]+\]\s*=\s*mapped_column\(\s*String\({ancho}\)"
    assert re.search(patron, bloque), (
        f"{copia}: {clase}.{columna} ya no es String({ancho})")


def test_f017_r22_el_ancho_minimo_sigue_siendo_120() -> None:
    """`ACTOR_MAX_LEN` no puede quedarse por encima de la columna más
    estrecha: si alguien estrechara una, el truncado dejaría de proteger.
    """
    from importlib.util import module_from_spec, spec_from_file_location

    ruta = (RAIZ / "services/partes-front/interface_adapters/web"
            / "identidad.py")
    spec = spec_from_file_location("identidad_f017", ruta)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)

    assert min(a for _c, _col, a in COLUMNAS_DE_AUTOR) == ANCHO_MINIMO
    assert modulo.ACTOR_MAX_LEN == ANCHO_MINIMO


def test_f017_r22_no_se_han_añadido_columnas_de_autor() -> None:
    """F-017 no crea ninguna columna: esa es la frontera con F-018.

    Si aparece una columna de autor nueva (un `actor_oid`, por ejemplo),
    hay que declararla arriba **y** justificar que no era trabajo de
    F-018 (`requirements.md` §2.3).
    """
    for copia, ruta in COPIAS:
        fuente = _fuente(ruta)
        encontradas = set(re.findall(
            r"^\s+(\w*(?:_by|actor))\s*:\s*Mapped", fuente, re.MULTILINE))
        declaradas = {col for _c, col, _a in COLUMNAS_DE_AUTOR}
        assert encontradas <= declaradas, (
            f"{copia}: columnas de autor sin declarar: "
            f"{encontradas - declaradas}")


# ====================================================================== #
# (b) Nadie reescribe las filas históricas
# ====================================================================== #

COLUMNAS_SUELTAS = ("approved_by", "deleted_by", "created_by", "updated_by",
                    "sigrid_registrado_by", "actor")


def _ficheros_de_produccion() -> list[Path]:
    return [
        p for p in (RAIZ / "services").rglob("*.py")
        if "tests" not in p.parts and "__pycache__" not in p.parts
    ]


@pytest.mark.parametrize("columna", COLUMNAS_SUELTAS)
def test_f017_r22_no_hay_update_masivo_sobre_las_columnas_de_autor(
        columna: str) -> None:
    """Ni un `UPDATE ... SET <columna>` en SQL crudo en todo el árbol.

    Las escrituras legítimas son por ORM y fila a fila (aprobar ESE parte,
    borrar ESA línea). Un `UPDATE` textual sobre una columna de autor solo
    puede ser una cosa: reescribir el pasado en masa.
    """
    patron = re.compile(rf"UPDATE\s+\w+\s+SET[^;]*\b{columna}\b",
                        re.IGNORECASE | re.DOTALL)
    culpables = [p.relative_to(RAIZ) for p in _ficheros_de_produccion()
                 if patron.search(p.read_text(encoding="utf-8"))]
    assert culpables == [], f"reescriben {columna} en masa: {culpables}"


def test_f017_r22_no_hay_ficheros_sql_de_migracion() -> None:
    """F-017 no trae migración. Ninguna, ni siquiera «por si acaso»."""
    sql = [p.relative_to(RAIZ) for p in RAIZ.rglob("*.sql")
           if "__pycache__" not in p.parts and ".venv" not in p.parts]
    assert sql == [], f"han aparecido ficheros .sql: {sql}"


def test_f017_r22_el_ddl_complementario_no_toca_las_columnas_de_autor() -> None:
    """El DDL que el ORM no sabe expresar existe (F-010) y es aditivo.

    Se comprueba que ahí no se ha colado un `UPDATE` ni un `ALTER` que
    reescriba o estreche una columna de autor.
    """
    for _copia, ruta in COPIAS:
        fuente = _fuente(ruta)
        for columna in COLUMNAS_SUELTAS:
            assert not re.search(
                rf"ALTER\s+TABLE[^\"']*ALTER\s+COLUMN\s+{columna}",
                fuente, re.IGNORECASE)
            assert not re.search(rf"UPDATE[^\"']*\b{columna}\b\s*=",
                                 fuente, re.IGNORECASE)


def test_f017_r22_el_guardian_muerde() -> None:
    """Un guardián que no se ha visto fallar no protege de nada.

    Se comprueba sobre texto fabricado —nunca sobre el árbol real— que el
    patrón de `UPDATE` masivo se detecta.
    """
    patron = re.compile(r"UPDATE\s+\w+\s+SET[^;]*\bapproved_by\b",
                        re.IGNORECASE | re.DOTALL)
    assert patron.search(
        "UPDATE parte_documents SET approved_by = 'desconocido-pre-f017'")
    assert patron.search(
        "UPDATE parte_documents\n   SET approved_by='x', deleted_by='y'")
    # Y que no salta con una escritura legítima por ORM.
    assert not patron.search("doc.approved_by = _actor(request)")
