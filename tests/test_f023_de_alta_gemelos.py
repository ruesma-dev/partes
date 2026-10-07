# tests/test_f023_de_alta_gemelos.py
"""Guardian de la regla «de alta» duplicada en sv3, sv5 y sv4 (F-023, DA6).

La regla (R1): un empleado o recurso esta de alta a la fecha D si su
`con.fecbaj` es NULL, 0 o mayor que D. Vive DUPLICADA a proposito, porque
`docs/ARCHITECTURE.md` prohibe la libreria compartida:

  - sv3 `application/services/seleccion_sigrid.py::de_alta` (casa),
  - sv5 `application/services/coherencia_recurso.py::de_alta` (verifica
    antes de escribir en Sigrid),
  - sv4 la aplica en SQL, en el filtro de alta a hoy de su catalogo de
    empleados (`_SQL_EMPLEADOS` de `sigrid_lookup_client.py`) y, desde
    F-035, de su catalogo de recursos activos (`_SQL_RECURSOS_ACTIVOS`).

Si divergen, sv5 omitiria lineas que sv3 da por buenas (o al reves) y el
portal ofreceria fichas que la ingesta no casa. Esta en la lista cerrada
de duplicacion de `CLAUDE.md`: quien toque una copia cambia todas.

Las funciones se extraen por AST de cada fichero (sin importar el modulo:
las dos copias viven en paquetes que se llaman igual, `application`) y se
comparan por una tabla comun de casos y por su codigo.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Raiz del repositorio: este fichero es `<raiz>/tests/test_f023_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_SV3 = RAIZ / "services/partes-persistencia/application/services/seleccion_sigrid.py"
RUTA_SV5 = RAIZ / "services/partes-transfer/application/services/coherencia_recurso.py"
RUTA_SV4 = RAIZ / "services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py"

FECHA = 20260915

#: Tabla COMUN de casos: (con.fecbaj, fecha, de alta).
CASOS: tuple[tuple[int | None, int, bool], ...] = (
    (None, FECHA, True),           # NULL: nunca dado de baja
    (0, FECHA, True),              # 0: «sin baja» en Sigrid
    (FECHA + 1, FECHA, True),      # baja futura: aun de alta ese dia
    (FECHA, FECHA, False),         # el dia de la baja ya no
    (FECHA - 1, FECHA, False),
    (20210126, FECHA, False),
)


def _funcion(ruta: Path, nombre: str) -> ast.FunctionDef:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"{ruta} no define `{nombre}`")


def _compilar(nodo: ast.FunctionDef):
    modulo = ast.Module(body=[nodo], type_ignores=[])
    espacio: dict = {}
    exec(compile(modulo, "<de_alta>", "exec"), espacio)   # noqa: S102
    return espacio[nodo.name]


def _sin_docstring(nodo: ast.FunctionDef) -> str:
    cuerpo = list(nodo.body)
    if (cuerpo and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)):
        cuerpo = cuerpo[1:]
    return ast.dump(ast.Module(body=cuerpo, type_ignores=[]))


DE_ALTA = {
    "sv3": _funcion(RUTA_SV3, "de_alta"),
    "sv5": _funcion(RUTA_SV5, "de_alta"),
}


@pytest.mark.parametrize("copia", sorted(DE_ALTA))
@pytest.mark.parametrize("fecbaj, fecha, esperado", CASOS)
def test_f023_de_alta_tabla_comun(copia, fecbaj, fecha, esperado) -> None:
    assert _compilar(DE_ALTA[copia])(fecbaj, fecha) is esperado


def test_f023_de_alta_las_dos_copias_tienen_la_misma_firma_y_codigo() -> None:
    sv3, sv5 = DE_ALTA["sv3"], DE_ALTA["sv5"]
    assert ast.dump(sv3.args) == ast.dump(sv5.args)
    assert _sin_docstring(sv3) == _sin_docstring(sv5), (
        "de_alta de sv3 y de sv5 ya no son el mismo codigo: si la regla "
        "cambia, cambia en las dos (CLAUDE.md, lista cerrada)")


def _constante(ruta: Path, nombre: str) -> str:
    for nodo in ast.parse(ruta.read_text(encoding="utf-8")).body:
        if (isinstance(nodo, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == nombre
                        for t in nodo.targets)):
            return " ".join(ast.literal_eval(nodo.value).split())
    raise AssertionError(f"{ruta} no define `{nombre}`")


def test_f023_de_alta_el_sql_de_sv4_conserva_la_misma_regla() -> None:
    """sv4 filtra ficha y recurso con la misma regla, a hoy (R38)."""
    sql = _constante(RUTA_SV4, "_SQL_EMPLEADOS")
    assert "(con.fecbaj IS NULL OR con.fecbaj = 0 OR con.fecbaj > ?)" in sql
    assert ("rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
            "rescon.fecbaj > ?") in sql


def test_f035_r23_el_sql_de_recursos_de_sv4_conserva_la_misma_regla() -> None:
    """F-035 (DA2): el catalogo de recursos activos de sv4 filtra el
    concepto del recurso con la misma regla, a hoy, y con el mismo texto
    que `_SQL_EMPLEADOS`."""
    sql = _constante(RUTA_SV4, "_SQL_RECURSOS_ACTIVOS")
    regla = ("(rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
             "rescon.fecbaj > ?)")
    assert regla in sql
    assert sql.count("fecbaj > ?") == 1
    assert ("rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
            "rescon.fecbaj > ?") in _constante(RUTA_SV4, "_SQL_EMPLEADOS")
