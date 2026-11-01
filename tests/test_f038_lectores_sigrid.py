# tests/test_f038_lectores_sigrid.py
"""Guardián de los lectores de Sigrid del monorepo (F-038, R11–R13).

Todo lo que lee Sigrid lo hace por `POST /api/sql/read` de sigrid-api. Este
guardián recorre `services/` y fija tres cosas:

  - R11: el conjunto de LECTORES es exactamente la lista cerrada de
    `design.md` §6. Un lector nuevo rompe el test hasta que alguien lo
    añade a la lista a conciencia (y, con ello, a las dos reglas de abajo).
  - R12: cada lector comprueba `truncated` con una llamada `.get("truncated")`
    en código (un docstring que lo mencione no cuenta).
  - R13: ningún lector fija un `max_rows` literal por debajo del límite
    efectivo: ni como valor de la clave `"max_rows"` de un dict, ni como
    argumento `max_rows=`, ni como valor por defecto de un parámetro
    `max_rows`. `PAGINA_FILAS + 1` es una operación, no un literal, y no
    cuenta.

Umbral de R13: la spec lo escribe con el defecto de DA1 = A (200.000). El
humano eligió DA1 = B (500.000, el tope de la instancia; aprobación literal
en `requirements.md`), así que el umbral es 500.000: un literal menor sería
un límite por debajo del acordado.

Un LECTOR es un `.py` de `services/` (fuera de `tests/` y de los entornos
virtuales) con una constante de cadena de código —también la parte fija de
un f-string— que contiene `/api/sql/read` y que NO es docstring de módulo,
clase o función.

Se lee por AST, sin importar nada (los servicios tienen paquetes que se
llaman igual). Cada comprobación se prueba además contra código sintético
que la incumple: el guardián tiene que saber fallar.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_f038_...py`.
RAIZ = Path(__file__).resolve().parents[1]
SERVICIOS = RAIZ / "services"

#: Ruta que identifica una lectura de sigrid-api.
RUTA_LECTURA = "/api/sql/read"

#: Umbral de R13 (DA1 = B): ningún literal de `max_rows` por debajo.
UMBRAL_MAX_ROWS = 500_000

#: Carpetas que no son código de producción de un servicio.
CARPETAS_EXCLUIDAS = frozenset({
    "tests", ".venv", "venv", "__pycache__", "node_modules"})

#: Lista cerrada de lectores (`design.md` §6, DA6 = A).
LECTORES_ESPERADOS = frozenset({
    "services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py",
    "services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py",
    "services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py",
    "services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py",
    "services/partes-transfer/prueba_escritura_sigrid.py",
})


# ------------------------------ comprobaciones ------------------------- #

def _docstrings(arbol: ast.AST) -> set[int]:
    """`id` de los nodos constantes que son docstring."""
    ids: set[int] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and nodo.body:
            primero = nodo.body[0]
            if (isinstance(primero, ast.Expr)
                    and isinstance(primero.value, ast.Constant)
                    and isinstance(primero.value.value, str)):
                ids.add(id(primero.value))
    return ids


def es_lector(arbol: ast.AST) -> bool:
    """Hay una cadena de CÓDIGO (no docstring) con `/api/sql/read`."""
    docstrings = _docstrings(arbol)
    return any(isinstance(nodo, ast.Constant)
               and isinstance(nodo.value, str)
               and RUTA_LECTURA in nodo.value
               and id(nodo) not in docstrings
               for nodo in ast.walk(arbol))


def comprueba_truncated(arbol: ast.AST) -> bool:
    """Hay una llamada `<algo>.get("truncated", ...)` (R12)."""
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "get"
                and nodo.args
                and isinstance(nodo.args[0], ast.Constant)
                and nodo.args[0].value == "truncated"):
            return True
    return False


def _entero_bajo(nodo: ast.AST | None) -> bool:
    return (isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, int)
            and not isinstance(nodo.value, bool)
            and nodo.value < UMBRAL_MAX_ROWS)


def literales_max_rows_bajos(arbol: ast.AST) -> list[int]:
    """Líneas con un `max_rows` literal por debajo del umbral (R13)."""
    lineas: list[int] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Dict):
            for clave, valor in zip(nodo.keys, nodo.values):
                if (isinstance(clave, ast.Constant)
                        and clave.value == "max_rows"
                        and _entero_bajo(valor)):
                    lineas.append(valor.lineno)
        elif isinstance(nodo, ast.keyword):
            if nodo.arg == "max_rows" and _entero_bajo(nodo.value):
                lineas.append(nodo.value.lineno)
        elif isinstance(nodo, ast.arguments):
            posicionales = [*nodo.posonlyargs, *nodo.args]
            pares = list(zip(posicionales[len(posicionales)
                                          - len(nodo.defaults):],
                             nodo.defaults))
            pares += list(zip(nodo.kwonlyargs, nodo.kw_defaults))
            for argumento, defecto in pares:
                if argumento.arg == "max_rows" and _entero_bajo(defecto):
                    lineas.append(defecto.lineno)
    return sorted(lineas)


def lectores_del_repo() -> dict[str, ast.AST]:
    """Lectores de `services/` por ruta relativa a la raíz (con `/`)."""
    lectores: dict[str, ast.AST] = {}
    for ruta in sorted(SERVICIOS.rglob("*.py")):
        relativa = ruta.relative_to(RAIZ)
        if CARPETAS_EXCLUIDAS.intersection(relativa.parts):
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), str(ruta))
        if es_lector(arbol):
            lectores[relativa.as_posix()] = arbol
    return lectores


# --------------------------- contra el repositorio ---------------------- #

def test_f038_r11_lectores_son_la_lista_cerrada() -> None:
    encontrados = set(lectores_del_repo())
    sobran = sorted(encontrados - LECTORES_ESPERADOS)
    faltan = sorted(LECTORES_ESPERADOS - encontrados)
    assert not sobran and not faltan, (
        f"Lectores de Sigrid fuera de la lista cerrada: {sobran}; "
        f"de la lista que ya no leen: {faltan}. Un lector nuevo se añade "
        "a LECTORES_ESPERADOS a conciencia (y cumple R12 y R13).")


@pytest.mark.parametrize("ruta", sorted(LECTORES_ESPERADOS))
def test_f038_r12_cada_lector_comprueba_truncated(ruta: str) -> None:
    arbol = ast.parse((RAIZ / ruta).read_text(encoding="utf-8"))
    assert comprueba_truncated(arbol), (
        f"{ruta} no comprueba `truncated` (falta `.get(\"truncated\")`)")


@pytest.mark.parametrize("ruta", sorted(LECTORES_ESPERADOS))
def test_f038_r13_ningun_max_rows_literal_bajo(ruta: str) -> None:
    arbol = ast.parse((RAIZ / ruta).read_text(encoding="utf-8"))
    lineas = literales_max_rows_bajos(arbol)
    assert not lineas, (
        f"{ruta}: `max_rows` literal por debajo de {UMBRAL_MAX_ROWS} en las "
        f"líneas {lineas}")


# ------------------------- prueba de verdad del guardián ---------------- #

def test_f038_r11_lector_se_detecta_en_codigo_y_en_fstring() -> None:
    assert es_lector(ast.parse('URL = "http://x/api/sql/read"'))
    assert es_lector(ast.parse(
        'def f(base):\n    return f"{base}/api/sql/read"\n'))


def test_f038_r11_docstring_no_hace_lector() -> None:
    codigo = ('"""Lee por POST /api/sql/read."""\n'
              'class C:\n    """Usa /api/sql/read."""\n'
              '    def f(self):\n        """/api/sql/read"""\n'
              '        return 1\n')
    assert not es_lector(ast.parse(codigo))


def test_f038_r12_prueba_de_verdad_sin_truncated_falla() -> None:
    sin = ast.parse('def leer(body):\n'
                    '    """Mira body.get("truncated")."""\n'
                    '    return body.get("rows")\n')
    con = ast.parse('def leer(body):\n'
                    '    if body.get("truncated"):\n'
                    '        raise RuntimeError("truncada")\n')
    assert not comprueba_truncated(sin)
    assert comprueba_truncated(con)


@pytest.mark.parametrize("codigo", [
    'P = {"sql": s, "max_rows": 1000}\n',
    'cliente.leer(sql, max_rows=10000)\n',
    'def leer(sql, max_rows=499_999):\n    pass\n',
    'def leer(*, sql, max_rows: int = 200_000):\n    pass\n',
])
def test_f038_r13_prueba_de_verdad_literal_bajo_falla(codigo: str) -> None:
    assert literales_max_rows_bajos(ast.parse(codigo)) == [1]


@pytest.mark.parametrize("codigo", [
    'P = {"max_rows": PAGINA_FILAS + 1}\n',
    'P = {"max_rows": self._max_rows}\n',
    'cliente.leer(sql, max_rows=500_000)\n',
    'def leer(*, sql, max_rows: int = MAX_ROWS_DEFECTO):\n    pass\n',
    'def leer(*, sql, max_rows: int | None = None):\n    pass\n',
    'P = {"timeout_seconds": 60, "otro": 1000}\n',
])
def test_f038_r13_lo_que_no_es_literal_bajo_no_cuenta(codigo: str) -> None:
    assert literales_max_rows_bajos(ast.parse(codigo)) == []
