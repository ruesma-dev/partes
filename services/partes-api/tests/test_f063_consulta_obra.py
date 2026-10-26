# tests/test_f063_consulta_obra.py
"""F-063 · La consulta de obra de sv2 que usa el índice de ``con.cod``.

- ``patron_like(clave)``: ``%`` y, tras cada carácter de la clave, su clase
  de variantes (minúscula, acentuadas, volados) y otro ``%``. Todo código
  casa con el patrón de su propia clave (R4–R7), así que la consulta trae un
  superconjunto.
- ``existe_obra`` manda ese patrón como único parámetro de un ``SELECT
  DISTINCT ... WHERE con.cod LIKE ?`` sin funciones sobre la columna y filtra
  los candidatos con la MISMA ``clave_obra`` (R1–R3, R8–R10).
- ``es_vacio`` y ``clave_obra`` viven en el dominio (R9, R12).

Sin red ni BBDD: un emulador de ``LIKE`` de T-SQL y ``httpx.MockTransport``.
El emulador no distingue mayúsculas pero SÍ acentos: el caso más exigente
para el superconjunto.
"""
from __future__ import annotations

import ast
import json
import random
import re
from pathlib import Path

import httpx
import pytest
from application.services import obra_sigrid, relectura_cabecera
from domain.models import clave_obra as modulo_clave
from domain.models.clave_obra import clave_obra
from infrastructure.sigrid import sigrid_lookup_client
from infrastructure.sigrid.sigrid_lookup_client import (
    MAX_ROWS_DEFECTO,
    SigridLookupClient,
    patron_like,
)

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
CLAVE_FALSA = "clave-falsa-de-test"

#: R10: candidatos de la clave "692" (el último lleva espacio duro).
CODIGOS_692 = ["692", "0692", "00692", "06-92", "06 92", " 0-6 9-2 ",
               "06 92"]
#: R10: candidatos de la clave "A12".
CODIGOS_A12 = ["a-12", "Á 12", "A12"]


# ------------------------- emulador de LIKE (T-SQL) ------------------------ #

def _clase_regex(contenido: str) -> str:
    negada = contenido.startswith("^")
    if negada:
        contenido = contenido[1:]
    partes: list[str] = []
    i = 0
    while i < len(contenido):
        if i + 2 < len(contenido) and contenido[i + 1] == "-":
            partes.append(f"{re.escape(contenido[i])}-{re.escape(contenido[i + 2])}")
            i += 3
        else:
            partes.append(re.escape(contenido[i]))
            i += 1
    return "[" + ("^" if negada else "") + "".join(partes) + "]"


def _like(cadena: str, patron: str) -> bool:
    """``cadena LIKE patron`` de T-SQL (``%``, ``_``, ``[...]``, ``[^...]``),
    sin distinguir mayúsculas y distinguiendo acentos."""
    regex: list[str] = []
    i = 0
    while i < len(patron):
        c = patron[i]
        if c == "%":
            regex.append(".*")
        elif c == "_":
            regex.append(".")
        elif c == "[" and "]" in patron[i + 1:]:
            fin = patron.index("]", i + 1)
            regex.append(_clase_regex(patron[i + 1:fin]))
            i = fin
        else:
            regex.append(re.escape(c))
        i += 1
    return re.fullmatch("".join(regex), cadena,
                        re.IGNORECASE | re.DOTALL) is not None


def test_f063_emulador_like_escape_de_guion_bajo() -> None:
    assert _like("AX1", "%A%[_]%1%") is False
    assert _like("A_1", "%A%[_]%1%") is True


def test_f063_emulador_like_guion_bajo_es_un_caracter() -> None:
    assert _like("AX1", "%A%_%1%") is True
    assert _like("A1", "%A%_%1%") is False


def test_f063_emulador_like_distingue_acentos_no_mayusculas() -> None:
    assert _like("á", "%a%") is False
    assert _like("a", "%A%") is True
    assert _like("Á", "%[á]%") is True


def test_f063_emulador_like_clases_y_comodines() -> None:
    assert _like("0692", "%6%9%2%") is True
    assert _like("6-9", "%6%9%2%") is False
    assert _like("x", "[^0-9]") is True
    assert _like("5", "[^0-9]") is False
    assert _like("[", "[[]") is True
    assert _like("%", "[%]") is True
    assert _like("a", "[%]") is False


# ------------------------------ R4 · superconjunto ------------------------- #

def _casa_con_su_clave(codigo: str) -> bool:
    return _like(codigo, patron_like(clave_obra(codigo)))


@pytest.mark.parametrize("codigo", CODIGOS_692 + CODIGOS_A12)
def test_f063_r4_codigos_de_r10_casan_con_su_patron(codigo: str) -> None:
    assert _casa_con_su_clave(codigo)


@pytest.mark.parametrize("codigo", [
    "\t692", "692-", "6-92", "0 692", "ª12", "º-7", "¹²³", "ñ-1", "Ç 9",
    "µ5", "obra vieja", "P/12.3", "A%B", "A_B", "[1]",
])
def test_f063_r4_codigos_raros_casan_con_su_patron(codigo: str) -> None:
    assert _casa_con_su_clave(codigo)


#: Alfabeto del corpus (design §5.2): dígitos, letras con y sin acento,
#: blancos, guiones, espacio duro, volados y especiales de LIKE.
_ALFABETO = (
    "0123456789" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz"
    "ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕÅáéíóúàèìòùâêîôûäëïöüãõåÑñÇçÝýÿ"
    "ĀāĂăĄąĆćČčĎďĒēĘęĚěĞğĪīİıŁłŃńŇňŌōŐőŘřŚśŞşŠšŤťŪūŮůŰűŸŹźŻżŽžſ"
    "ªº¹²³µ" "     ----\t " "/._%[]"
)


def test_f063_r4_corpus_aleatorio_casa_con_su_patron() -> None:
    azar = random.Random(63)
    probados = 0
    fallos: list[str] = []
    for _ in range(6000):
        codigo = "".join(azar.choice(_ALFABETO)
                         for _ in range(azar.randint(1, 24)))
        if not clave_obra(codigo):
            continue
        probados += 1
        if not _casa_con_su_clave(codigo):
            fallos.append(codigo)
    assert probados >= 5000
    assert fallos == []


# ------------------------------- R5 · clases ------------------------------- #

def _clase_de(clave: str) -> str:
    patron = patron_like(clave)
    assert patron.startswith("%") and patron.endswith("%")
    return patron[1:-1]


@pytest.mark.parametrize(("base", "variantes"), [
    ("A", "AaªÁáÀàÂâÄäÃãÅåĀāĂăĄą"),
    ("N", "NnÑñŃńŇň"),
    ("2", "2²"),
    ("O", "OoºÓóÒòÔôÖöÕõŌōŐő"),
    ("1", "1¹"),
    ("S", "SsŚśŠšŞşſ"),
    ("C", "CcÇçĆćČč"),
])
def test_f063_r5_clase_con_minuscula_y_variantes(base: str,
                                                 variantes: str) -> None:
    clase = _clase_de(base)
    assert clase.startswith("[") and clase.endswith("]")
    for variante in variantes:
        assert variante in clase, variante


def test_f063_r5_clase_solo_con_su_base() -> None:
    clase = _clase_de("A")
    assert all(clave_obra(c) == "A" for c in clase[1:-1])
    assert "B" not in clase and "Ñ" not in _clase_de("A")


def test_f063_r5_clase_sin_caracteres_especiales_dentro() -> None:
    for base in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        clase = _clase_de(base)
        if clase.startswith("["):
            interior = clase[1:-1]
            assert all(c.isalnum() for c in interior), base
            assert interior == "".join(sorted(set(interior)))


@pytest.mark.parametrize("digito", "0456789")
def test_f063_r5_digito_sin_variantes_va_tal_cual(digito: str) -> None:
    assert patron_like(digito) == f"%{digito}%"


def test_f063_r5_patron_del_ejemplo() -> None:
    assert patron_like("692") == "%6%9%[2²]%"


def test_f063_r5_letra_no_latina_con_variante_del_rango() -> None:
    """``µ`` (U+00B5) tiene la clave ``Μ`` (griega): R5 la pide en su clase."""
    assert "µ" in _clase_de(clave_obra("µ"))


# ------------------------------ R6 · escapes ------------------------------- #

@pytest.mark.parametrize(("especial", "escape"), [
    ("%", "[%]"), ("_", "[_]"), ("[", "[[]")])
def test_f063_r6_especiales_de_like_escapados(especial: str,
                                              escape: str) -> None:
    assert patron_like(especial) == f"%{escape}%"


def test_f063_r6_guion_bajo_no_es_comodin() -> None:
    patron = patron_like("A_1")
    assert "[_]" in patron
    assert _like("AX1", patron) is False
    assert _like("A_1", patron) is True


def test_f063_r6_porcentaje_no_es_comodin() -> None:
    patron = patron_like("A%1")
    assert _like("AXYZ1", patron) is False
    assert _like("a % 1", patron) is True


# ----------------------------- R7 · clave vacía ---------------------------- #

def test_f063_r7_clave_vacia_lanza() -> None:
    with pytest.raises(ValueError):
        patron_like("")


# --------------------------- R1–R3 · la consulta --------------------------- #

class Grabadora:
    def __init__(self, filas: list | None = None, *, truncated: bool = False,
                 estado: int = 200) -> None:
        self.cuerpo = {"ok": True, "columns": ["codigo"],
                       "rows": filas if filas is not None else [],
                       "truncated": truncated}
        self.estado = estado
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        return httpx.Response(self.estado, json=self.cuerpo)

    @property
    def payload(self) -> dict:
        return json.loads(self.peticiones[-1].content)


def _cliente(grabadora: Grabadora, **kwargs) -> SigridLookupClient:
    return SigridLookupClient(
        base_url="https://sigrid.invalid", function_key=CLAVE_FALSA,
        database="ruesma", transport=httpx.MockTransport(grabadora), **kwargs)


def test_f063_r1_r2_un_like_parametrizado_sin_funciones() -> None:
    grabadora = Grabadora([["0692"]])
    _cliente(grabadora).existe_obra("692", timeout_s=5.0)
    (peticion,) = grabadora.peticiones
    assert peticion.url.path == "/api/sql/read"
    payload = grabadora.payload
    sql = payload["sql"]
    assert payload["parameters"] == [patron_like("692")]
    assert sql.count("?") == 1
    assert "692" not in sql and patron_like("692") not in sql
    normal = " ".join(sql.split()).upper()
    assert "SELECT DISTINCT CON.COD" in normal
    assert "FROM OBR JOIN CON ON OBR.IDE = CON.IDE" in normal
    assert normal.endswith("WHERE CON.COD LIKE ?")
    for prohibido in ("CROSS APPLY", "COLLATE", "TOP", "REPLACE", "PATINDEX",
                      "SUBSTRING", "ISNULL", "NULLIF", "EMP", "FECBAJ"):
        assert prohibido not in normal, prohibido


def test_f063_r3_pide_el_max_rows_del_cliente_y_el_tope() -> None:
    grabadora = Grabadora()
    _cliente(grabadora, max_rows=4321).existe_obra("692", timeout_s=5.0)
    assert grabadora.payload["max_rows"] == 4321
    assert grabadora.payload["timeout_seconds"] == 5
    _cliente(grabadora).existe_obra("692", timeout_s=5.0)
    assert grabadora.payload["max_rows"] == MAX_ROWS_DEFECTO


def test_f063_r3_truncada_es_error() -> None:
    grabadora = Grabadora([["692"]], truncated=True)
    with pytest.raises(RuntimeError, match="trunca"):
        _cliente(grabadora).existe_obra("692", timeout_s=5.0)


@pytest.mark.parametrize("estado", [400, 500])
def test_f063_r3_error_http_lanza(estado: int) -> None:
    grabadora = Grabadora(estado=estado)
    with pytest.raises(RuntimeError, match=str(estado)):
        _cliente(grabadora).existe_obra("692", timeout_s=5.0)


def test_f063_r7_clave_vacia_no_consulta() -> None:
    grabadora = Grabadora([["692"]])
    with pytest.raises(ValueError):
        _cliente(grabadora).existe_obra("", timeout_s=5.0)
    assert grabadora.peticiones == []


# ----------------------------- R8, R10 · filtro ---------------------------- #

@pytest.mark.parametrize("codigo", CODIGOS_692)
def test_f063_r10_candidato_exacto_de_692(codigo: str) -> None:
    grabadora = Grabadora([["1692"], [codigo], ["6920"]])
    assert _cliente(grabadora).existe_obra("692", timeout_s=5.0) is True


@pytest.mark.parametrize("codigo", CODIGOS_A12)
def test_f063_r10_candidato_exacto_de_a12(codigo: str) -> None:
    grabadora = Grabadora([["A123"], [codigo]])
    assert _cliente(grabadora).existe_obra("A12", timeout_s=5.0) is True


@pytest.mark.parametrize("filas", [
    [["1692"]], [["6920"]], [["69-12"]], [[None]], [[]],
    [["1692"], ["6920"], ["69-12"], [None], ["  "]], [],
])
def test_f063_r8_sin_candidato_exacto_es_false(filas: list) -> None:
    grabadora = Grabadora(filas)
    assert _cliente(grabadora).existe_obra("692", timeout_s=5.0) is False


def test_f063_r8_letras_de_otra_clave_no_cuentan() -> None:
    grabadora = Grabadora([["A-1-2-3"], ["BA12"], ["A1 2B"]])
    assert _cliente(grabadora).existe_obra("A12", timeout_s=5.0) is False


# ------------------------- R9, R12 · clave en dominio ---------------------- #

def test_f063_r9_una_sola_clave_obra() -> None:
    assert relectura_cabecera.clave_obra is modulo_clave.clave_obra
    assert relectura_cabecera.es_vacio is modulo_clave.es_vacio
    assert obra_sigrid.clave_obra is modulo_clave.clave_obra
    assert sigrid_lookup_client.clave_obra is modulo_clave.clave_obra


@pytest.mark.parametrize(("codigo", "clave"), [
    (None, ""), ("", ""), ("   ", ""), ("00672", "672"), ("000", "0"),
    ("06-92", "692"), ("á-b 1", "AB1"), ("ª1", "A1"), ("0A1", "0A1"),
])
def test_f063_r9_clave_obra_sin_cambios(codigo, clave: str) -> None:
    assert modulo_clave.clave_obra(codigo) == clave


def test_f063_r12_dominio_sin_dependencias_de_otras_capas() -> None:
    fuente = (RAIZ_SERVICIO / "domain" / "models" / "clave_obra.py").read_text(
        encoding="utf-8")
    importados: list[str] = []
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            importados += [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            importados.append(nodo.module or "")
    for modulo in importados:
        assert not modulo.startswith(
            ("application", "infrastructure", "interface_adapters", "config")
        ), modulo
