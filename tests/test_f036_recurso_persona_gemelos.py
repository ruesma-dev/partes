# tests/test_f036_recurso_persona_gemelos.py
"""Guardian del criterio «recurso persona» (`res.cla = 1`) de sv3, sv4 y
sv5 (F-036, DA3, R19; copia de sv4 de F-035).

sv3 casa el trabajador y elige el recurso de cada linea solo entre los
recursos PERSONA; sv5, antes de escribir en Sigrid, vuelve a elegir por
DNI (`elegir_por_dni`) entre los que le da `recursos_por_dni`. La lista
cerrada de `CLAUDE.md` exige que las dos elecciones tengan los MISMOS
candidatos, asi que el criterio vive duplicado a proposito:

  - sv3 `application/services/seleccion_sigrid.py`: `CLA_PERSONA = 1` y
    `es_persona`, que filtra los indices de `IndicePersonas` y los
    candidatos por nombre; el maestro lee `res.cla` en `_SQL_RECURSOS`
    (`infrastructure/sigrid/sigrid_api_client.py`).
  - sv5 `infrastructure/sigrid/sigrid_write_client.py::recursos_por_dni`:
    `AND res.cla = 1` en sus DOS ramas (DNI de la ficha y `res.cif`).
  - sv4 `infrastructure/sigrid/sigrid_lookup_client.py`:
    `WHERE res.cla = 1` en `_SQL_RECURSOS_ACTIVOS`, que usa
    `fetch_recursos_activos` para el selector de recursos del portal
    (F-035): ofrece los mismos candidatos que luego casan sv3 y sv5.

Se lee por AST y texto, sin importar (los dos servicios tienen paquetes
que se llaman igual). Cada comprobacion se prueba ademas contra una copia
estropeada en memoria: el guardian tiene que saber fallar.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

#: Raiz del repositorio: este fichero es `<raiz>/tests/test_f036_...py`.
RAIZ = Path(__file__).resolve().parents[1]

SV3 = RAIZ / "services/partes-persistencia"
RUTA_SELECCION = SV3 / "application/services/seleccion_sigrid.py"
RUTA_MAESTRO = SV3 / "infrastructure/sigrid/sigrid_api_client.py"
RUTA_SV5 = (RAIZ / "services/partes-transfer/infrastructure/sigrid/"
            "sigrid_write_client.py")
RUTA_SV4 = (RAIZ / "services/partes-front/infrastructure/sigrid/"
            "sigrid_lookup_client.py")


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _nodo(arbol: ast.AST, tipo, nombre: str):
    for nodo in ast.walk(arbol):
        if isinstance(nodo, tipo) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"no se encuentra `{nombre}`")


def _llama_a(nodo: ast.AST, nombre: str) -> bool:
    """`nombre` aparece como nombre usado (llamada o argumento)."""
    return any(isinstance(n, ast.Name) and n.id == nombre
               for n in ast.walk(nodo))


# ------------------------------ comprobaciones ------------------------- #

def cla_persona_sv3(texto: str) -> int:
    """El valor de `CLA_PERSONA` y que `es_persona` lo use de verdad."""
    arbol = ast.parse(texto)
    valor = None
    for nodo in arbol.body:
        if (isinstance(nodo, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "CLA_PERSONA"
                        for t in nodo.targets)):
            valor = ast.literal_eval(nodo.value)
    assert valor == 1, f"CLA_PERSONA = {valor!r}, se esperaba 1"
    es_persona = _nodo(arbol, ast.FunctionDef, "es_persona")
    espacio: dict = {"CLA_PERSONA": valor}
    exec(compile(ast.Module(body=[es_persona], type_ignores=[]),  # noqa: S102
                 "<es_persona>", "exec"), espacio)

    class _R:
        def __init__(self, cla) -> None:
            self.cla = cla

    tabla = {cla: espacio["es_persona"](_R(cla))
             for cla in (None, 0, 1, 2, 3)}
    assert tabla == {None: False, 0: False, 1: True, 2: False, 3: False}, \
        f"es_persona ya no es «cla == 1»: {tabla}"
    return valor


def filtro_sv3(texto: str) -> None:
    """`IndicePersonas` filtra sus indices por DNI y ficha y los
    candidatos por nombre con `es_persona`."""
    clase = _nodo(ast.parse(texto), ast.ClassDef, "IndicePersonas")
    for metodo in ("__init__", "candidatos_nombre"):
        assert _llama_a(_nodo(clase, ast.FunctionDef, metodo), "es_persona"), \
            f"IndicePersonas.{metodo} ya no filtra con es_persona"


def maestro_sv3(texto: str) -> None:
    """`_SQL_RECURSOS` lee `res.cla` y `fetch_recursos` lo mapea."""
    arbol = ast.parse(texto)
    sql = None
    for nodo in arbol.body:
        if (isinstance(nodo, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "_SQL_RECURSOS"
                        for t in nodo.targets)):
            sql = " ".join(ast.literal_eval(nodo.value).split())
    assert sql is not None and "res.cla AS cla" in sql, \
        "_SQL_RECURSOS ya no lee res.cla"
    fetch = _nodo(arbol, ast.FunctionDef, "fetch_recursos")
    assert any(isinstance(n, ast.keyword) and n.arg == "cla"
               for n in ast.walk(fetch)), "fetch_recursos ya no mapea cla"


def ramas_sv5(texto: str) -> list[int]:
    """El `res.cla` de cada rama de `recursos_por_dni`."""
    funcion = _nodo(ast.parse(texto), ast.FunctionDef, "recursos_por_dni")
    sql = ast.get_source_segment(texto, funcion) or ""
    inicio = sql.index("SELECT q.dnin")
    ramas = sql[inicio:].split("UNION ALL")
    assert len(ramas) == 2, f"recursos_por_dni tiene {len(ramas)} ramas"
    valores = []
    for rama in ramas:
        hallado = re.search(r"AND res\.cla = (\d+)", rama)
        assert hallado, "una rama de recursos_por_dni perdio res.cla"
        valores.append(int(hallado.group(1)))
    return valores


def _conjunciones(clausula: str) -> list[str]:
    """Trocea por `AND` de nivel superior (fuera de parentesis); falla si
    hay un `OR` de nivel superior, que anularia cualquier filtro."""
    partes, actual, nivel = [], [], 0
    for palabra in re.findall(r"\(|\)|[^\s()]+", clausula):
        nivel += (palabra == "(") - (palabra == ")")
        if nivel == 0 and palabra.upper() == "OR":
            raise AssertionError("OR de nivel superior en el WHERE")
        if nivel == 0 and palabra.upper() == "AND":
            partes.append(" ".join(actual))
            actual = []
        else:
            actual.append(palabra)
    partes.append(" ".join(actual))
    return partes


def filtro_sv4(texto: str) -> int:
    """El `res.cla` que filtra `_SQL_RECURSOS_ACTIVOS` en su WHERE (una
    conjuncion de nivel superior) y que `fetch_recursos_activos` la use."""
    arbol = ast.parse(texto)
    sql = None
    for nodo in arbol.body:
        if (isinstance(nodo, ast.Assign)
                and any(isinstance(t, ast.Name)
                        and t.id == "_SQL_RECURSOS_ACTIVOS"
                        for t in nodo.targets)):
            sql = " ".join(ast.literal_eval(nodo.value).split())
    assert sql is not None, "no se encuentra _SQL_RECURSOS_ACTIVOS"
    assert sql.count(" WHERE ") == 1, "_SQL_RECURSOS_ACTIVOS: un solo WHERE"
    clausula = sql.split(" WHERE ", 1)[1]
    valores = [int(m.group(1)) for c in _conjunciones(clausula)
               if (m := re.fullmatch(r"res\.cla = (\d+)", c))]
    assert len(valores) == 1, \
        f"el WHERE de _SQL_RECURSOS_ACTIVOS filtra res.cla {len(valores)} veces"
    fetch = _nodo(arbol, ast.FunctionDef, "fetch_recursos_activos")
    assert _llama_a(fetch, "_SQL_RECURSOS_ACTIVOS"), \
        "fetch_recursos_activos ya no usa _SQL_RECURSOS_ACTIVOS"
    return valores[0]


# ---------------------------------- tests ------------------------------ #

def test_f036_r19_sv3_cla_persona_es_1() -> None:
    assert cla_persona_sv3(_leer(RUTA_SELECCION)) == 1


def test_f036_r19_sv3_filtra_con_es_persona() -> None:
    filtro_sv3(_leer(RUTA_SELECCION))


def test_f036_r19_sv3_lee_res_cla() -> None:
    maestro_sv3(_leer(RUTA_MAESTRO))


def test_f036_r19_sv5_las_dos_ramas_con_el_mismo_cla_que_sv3() -> None:
    cla = cla_persona_sv3(_leer(RUTA_SELECCION))
    assert ramas_sv5(_leer(RUTA_SV5)) == [cla, cla]


def test_f036_r19_sv4_filtra_con_el_mismo_cla_que_sv3() -> None:
    cla = cla_persona_sv3(_leer(RUTA_SELECCION))
    assert filtro_sv4(_leer(RUTA_SV4)) == cla


# ------------------- el guardian sabe fallar (copias rotas) ------------ #

def _roto(texto: str, viejo: str, nuevo: str) -> str:
    assert viejo in texto, f"no se encuentra {viejo!r} para estropearlo"
    return texto.replace(viejo, nuevo, 1)


@pytest.mark.parametrize("viejo, nuevo", [
    ("CLA_PERSONA = 1", "CLA_PERSONA = 2"),
    ("return r.cla == CLA_PERSONA", "return r.cla is not None"),
])
def test_f036_r19_falla_si_sv3_cambia_el_criterio(viejo, nuevo) -> None:
    with pytest.raises(AssertionError):
        cla_persona_sv3(_roto(_leer(RUTA_SELECCION), viejo, nuevo))


def test_f036_r19_falla_si_sv3_deja_de_filtrar_los_indices() -> None:
    roto = _roto(_leer(RUTA_SELECCION), "filter(es_persona, self._recursos)",
                 "self._recursos")
    with pytest.raises(AssertionError):
        filtro_sv3(roto)


def test_f036_r19_falla_si_sv3_deja_de_leer_res_cla() -> None:
    with pytest.raises(AssertionError):
        maestro_sv3(_roto(_leer(RUTA_MAESTRO), "res.cla       AS cla",
                          "NULL          AS cla"))
    with pytest.raises(AssertionError):
        maestro_sv3(_roto(_leer(RUTA_MAESTRO),
                          'cla=_opt_int(rm.get("cla")),', ""))


@pytest.mark.parametrize("rama", [0, 1])
def test_f036_r19_falla_si_una_rama_de_sv5_pierde_el_filtro(rama) -> None:
    texto = _leer(RUTA_SV5)
    marcas = [m.start() for m in re.finditer(r" AND res\.cla = 1", texto)]
    assert len(marcas) == 2
    i = marcas[rama]
    roto = texto[:i] + texto[i + len(" AND res.cla = 1"):]
    with pytest.raises(AssertionError):
        ramas_sv5(roto)


def test_f036_r19_falla_si_sv5_usa_otro_cla() -> None:
    roto = _roto(_leer(RUTA_SV5), "AND res.cla = 1", "AND res.cla = 2")
    assert ramas_sv5(roto) != [1, 1]


@pytest.mark.parametrize("viejo, nuevo", [
    # se quita el filtro
    ("WHERE res.cla = 1\n  AND ", "WHERE "),
    # sigue escrito, pero ya no filtra (disyuncion a nivel superior)
    ("WHERE res.cla = 1\n  AND ", "WHERE res.cla = 1\n  OR "),
    # el filtro baja a un JOIN opcional y deja de restringir `res`
    ("WHERE res.cla = 1\n  AND ",
     "AND res.cla = 1\nWHERE "),
    # fetch_recursos_activos deja de usar la constante
    ("sql=_SQL_RECURSOS_ACTIVOS,", "sql=_SQL_EMPLEADOS,"),
])
def test_f036_r19_falla_si_sv4_pierde_el_filtro(viejo, nuevo) -> None:
    roto = _roto(_leer(RUTA_SV4), viejo, nuevo)  # fuera: su fallo no cuenta
    with pytest.raises(AssertionError):
        filtro_sv4(roto)


def test_f036_r19_falla_si_sv4_usa_otro_cla() -> None:
    roto = _roto(_leer(RUTA_SV4), "WHERE res.cla = 1", "WHERE res.cla = 2")
    assert filtro_sv4(roto) != 1
