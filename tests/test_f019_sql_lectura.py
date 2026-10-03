# tests/test_f019_sql_lectura.py
"""F-019 · R25-R27: el acceso de LECTURA de dedicacion a la bandeja.

`infra/sql/01_dedicacion_lectura.sql` lo ejecuta EL HUMANO con `psql` en
la base `partes` (design §10, M2). Aqui no se ejecuta nada: se analiza el
texto del script (R26) y se comprueba que ningun servicio lleva un `GRANT`
en su codigo (R27; sv3 y sv4 solo crean la tabla al arrancar).

Como en el guardian de F-010, el analizador se prueba tambien contra copias
alteradas del script: un analizador que diera todo por bueno pasaria en
verde para siempre.

Sin red ni BBDD: solo sistema de ficheros y `ast`.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "infra" / "sql" / "01_dedicacion_lectura.sql"

#: Las UNICAS concesiones permitidas, normalizadas (R25).
GRANTS_PERMITIDOS = (
    'GRANT CONNECT ON DATABASE partes TO :"rol";',
    'GRANT USAGE ON SCHEMA public TO :"rol";',
    'GRANT SELECT ON TABLE public.dedicacion_bandeja TO :"rol";',
)

#: Comprobaciones de lectura que el script debe dejar a la vista (§3).
COMPROBACIONES = (
    "has_table_privilege(:'rol', 'public.dedicacion_bandeja', 'SELECT')",
    "has_table_privilege(:'rol', 'public.parte_registros', 'SELECT')",
    "has_schema_privilege(:'rol', 'public', 'CREATE')",
    "SELECT version();",
)

#: Sentencias prohibidas en el codigo (sin comentarios), sin mayusculas.
PROHIBIDAS = (
    r"\bCREATE\s+ROLE\b", r"\bCREATE\s+USER\b", r"\bALTER\s+ROLE\b",
    r"\bALTER\s+USER\b", r"\bALTER\s+SYSTEM\b", r"\bCREATE\s+EXTENSION\b",
    r"\bSUPERUSER\b", r"\bREVOKE\b", r"\bALTER\s+DEFAULT\s+PRIVILEGES\b",
    r"\bDROP\b", r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b",
)

#: En TODO el texto (comentarios incluidos): nada de credenciales ni
#: servidores reales. El comando de la cabecera usa marcadores `<...>`.
SECRETOS = (
    (r"(?i)password", "una contrasena"),
    (r"(?i)\bhost\s*=\s*(?!<)", "un host real"),
    (r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "una IP"),
    (r"(?i)\.postgres\.database\.azure\.com", "un servidor de Azure"),
    (r"(?i)\buser\s*=\s*(?!<)", "un usuario real"),
)


def _sin_comentarios(texto: str) -> str:
    return "\n".join(linea.split("--", 1)[0] for linea in texto.splitlines())


def problemas(texto: str) -> list[str]:
    """Lo que hace inaceptable un script de concesiones (R26)."""
    out: list[str] = []
    codigo = _sin_comentarios(texto)
    if "\\set ON_ERROR_STOP on" not in codigo:
        out.append("falta \\set ON_ERROR_STOP on")
    for patron in PROHIBIDAS:
        if re.search(patron, codigo, re.IGNORECASE):
            out.append(f"sentencia prohibida: {patron}")
    grants = [" ".join(g.split())
              for g in re.findall(r"(?is)\bGRANT\b.*?;", codigo)]
    for g in grants:
        if g not in GRANTS_PERMITIDOS:
            out.append(f"concesion no permitida: {g}")
    for g in GRANTS_PERMITIDOS:
        if g not in grants:
            out.append(f"falta la concesion: {g}")
    for c in COMPROBACIONES:
        if c not in codigo:
            out.append(f"falta la comprobacion: {c}")
    for patron, nombre in SECRETOS:
        if re.search(patron, texto):
            out.append(f"contiene {nombre}")
    return out


def _texto() -> str:
    return SCRIPT.read_text(encoding="utf-8")


# ================================ R25 · el script ============================== #

def test_f019_r25_el_script_existe_y_es_aceptable() -> None:
    assert problemas(_texto()) == []


def test_f019_r25_solo_concede_y_comprueba() -> None:
    """Idempotente: todo lo que ejecuta es `GRANT` o `SELECT` (mas la
    meta-orden `\\set` de psql, que va en su propia linea sin `;`)."""
    lineas = _sin_comentarios(_texto()).splitlines()
    meta = [l.strip() for l in lineas if l.strip().startswith("\\")]
    assert meta == ["\\set ON_ERROR_STOP on"]
    sql = "\n".join(l for l in lineas if not l.strip().startswith("\\"))
    sentencias = [s.strip() for s in sql.split(";") if s.strip()]
    for s in sentencias:
        assert s.split()[0].upper() in ("GRANT", "SELECT"), s
    assert sum(1 for s in sentencias if s.upper().startswith("GRANT")) == 3


def test_f019_r25_la_cabecera_trae_el_comando_del_humano() -> None:
    texto = _texto()
    assert texto.startswith("-- infra/sql/01_dedicacion_lectura.sql")
    assert ('psql "host=<servidor> dbname=partes user=<admin> '
            'sslmode=require"') in texto
    assert "-v rol=<rol_app_dedicacion>" in texto
    assert "-f infra/sql/01_dedicacion_lectura.sql" in texto


# ====================== R26 · el analizador muerde de verdad =================== #

ALTERACIONES = [
    ("crear_rol", 'CREATE ROLE lector LOGIN;'),
    ("alterar_rol", 'ALTER ROLE :"rol" CREATEDB;'),
    ("alter_system", "ALTER SYSTEM SET work_mem = '64MB';"),
    ("extension", "CREATE EXTENSION pgcrypto;"),
    ("superuser", 'ALTER USER :"rol" WITH SUPERUSER;'),
    ("insert", 'GRANT INSERT ON TABLE public.dedicacion_bandeja TO :"rol";'),
    ("todo", 'GRANT ALL ON TABLE public.dedicacion_bandeja TO :"rol";'),
    ("otra_tabla", 'GRANT SELECT ON TABLE public.parte_registros TO :"rol";'),
    ("todas", 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"rol";'),
    ("crear_en_public", 'GRANT CREATE ON SCHEMA public TO :"rol";'),
    ("revoke", 'REVOKE CREATE ON SCHEMA public FROM PUBLIC;'),
    ("password", "-- PASSWORD 'algo'"),
    ("host", "-- psql host=servidor-real.example dbname=partes"),
    ("ip", "-- conectar a 10.1.2.3"),
    ("azure", "-- psql-x.postgres.database.azure.com"),
]


@pytest.mark.parametrize("caso,linea", ALTERACIONES,
                         ids=[a[0] for a in ALTERACIONES])
def test_f019_r26_el_analizador_caza_lo_prohibido(caso, linea) -> None:
    alterado = _texto() + "\n" + linea + "\n"
    assert problemas(alterado), caso


def test_f019_r26_sin_on_error_stop_tambien_falla() -> None:
    alterado = _texto().replace("\\set ON_ERROR_STOP on", "")
    assert "falta \\set ON_ERROR_STOP on" in problemas(alterado)


def test_f019_r26_sin_la_concesion_de_la_bandeja_tambien_falla() -> None:
    alterado = _texto().replace(GRANTS_PERMITIDOS[2], "")
    assert f"falta la concesion: {GRANTS_PERMITIDOS[2]}" in problemas(alterado)


# =========================== R27 · nadie ejecuta GRANT ========================= #

def _cadenas_ejecutables(arbol: ast.AST) -> list[str]:
    """Las cadenas literales del modulo que NO son docstrings."""
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(
                    cuerpo[0].value, ast.Constant):
                docstrings.add(id(cuerpo[0].value))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docstrings]


def test_f019_r27_ningun_servicio_lleva_un_grant_en_su_codigo() -> None:
    culpables = []
    ficheros = list((RAIZ / "services").rglob("*.py"))
    assert len(ficheros) > 100
    for ruta in ficheros:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        if any(re.search(r"\bGRANT\b", c, re.IGNORECASE)
               for c in _cadenas_ejecutables(arbol)):
            culpables.append(str(ruta.relative_to(RAIZ)))
    assert culpables == []


def test_f019_r27_el_detector_ve_un_grant_en_una_cadena() -> None:
    codigo = 'x = 1\nsession.execute(text("grant select on t to r"))\n'
    assert any("grant" in c for c in _cadenas_ejecutables(ast.parse(codigo)))
    doc = '"""Con un GRANT SELECT en la doc."""\n'
    assert _cadenas_ejecutables(ast.parse(doc)) == []
