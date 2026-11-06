# tests/test_f066_usos_sv4.py
"""F-066 · los demás usos de la regla de extra en sv4 (R6, R19–R21).

- R19 y R20: el SQL de `fetch_hora_extra_recurso` y `fetch_dnis_sin_extra`
  se captura (cliente REAL, `_post_sql_read` falso) y se EJECUTA sobre un
  SQLite en memoria con `res`, `emp`, `reshor` y `auxhor` sintéticos (los
  dos giros de T-SQL, `TOP 1` e `ISNULL`, se traducen), para ver lo que
  devolvería Sigrid y no solo el texto.
- R21: `franquicia.extras_pendientes` no suma los excluidos.
- R6: ningún otro fichero Python de sv4 implementa la regla ni la lista.

Sin red ni BBDD real. DNIs y recursos SINTÉTICOS.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date
from pathlib import Path

import pytest
from application.services import franquicia as fq
from application.services.clase_hora import condicion_sql_extra
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient

RAIZ_SV4 = Path(__file__).resolve().parents[1]

AUXHOR = [(1, "HL01"), (7, "HEOF"), (8, "HEGR"), (63, "HENC"),
          (64, " henc "), (65, "MENC")]


def _base() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE auxhor (ide INTEGER, cod TEXT, res TEXT);
        CREATE TABLE emp (ide INTEGER, dni TEXT);
        CREATE TABLE res (ide INTEGER, conide INTEGER, cif TEXT);
        CREATE TABLE reshor (reside INTEGER, horide INTEGER, pre REAL);
    """)
    db.executemany("INSERT INTO auxhor VALUES (?, ?, ?)",
                   [(i, c, f"hora {c.strip()}") for i, c in AUXHOR])
    return db


class SigridSqlite(SigridLookupClient):
    """El cliente real; el SQL va a un SQLite en vez de a sigrid-api."""

    def __init__(self, db: sqlite3.Connection) -> None:
        super().__init__(base_url="http://sigrid.invalid",
                         function_key="clave-de-test", database="bd")
        self.db = db
        self.sql: list[str] = []

    def _post_sql_read(self, *, sql, parameters, label, max_rows=None):
        self.sql.append(sql)
        lite = sql.replace("ISNULL(", "IFNULL(")
        if "SELECT TOP 1 " in lite:
            lite = lite.replace("SELECT TOP 1 ", "SELECT ") + " LIMIT 1"
        cur = self.db.execute(lite, parameters)
        return [d[0] for d in cur.description], [list(r) for r in cur]


def _reshor(db, reside: int, *horas: int) -> None:
    db.executemany("INSERT INTO reshor VALUES (?, ?, ?)",
                   [(reside, h, 10.0 + h) for h in horas])


# --------------------------------- R19 ---------------------------------- #

def test_f066_r19_hora_extra_recurso_salta_el_excluido() -> None:
    db = _base()
    _reshor(db, 501, 63, 7, 1)        # HENC va antes que HEOF por código
    _reshor(db, 502, 63, 64, 1, 65)   # solo excluidos y ordinarias
    _reshor(db, 503, 8)
    cliente = SigridSqlite(db)
    assert cliente.fetch_hora_extra_recurso(501) == {
        "ide": 7, "cod": "HEOF", "res": "hora HEOF", "pre": 17.0}
    assert cliente.fetch_hora_extra_recurso(502) is None
    assert cliente.fetch_hora_extra_recurso(503)["cod"] == "HEGR"
    assert cliente.fetch_hora_extra_recurso(999) is None


def test_f066_r19_hora_extra_recurso_usa_condicion_sql() -> None:
    cliente = SigridSqlite(_base())
    cliente.fetch_hora_extra_recurso(501)
    (sql,) = cliente.sql
    assert f"WHERE {condicion_sql_extra('auxhor.cod')} AND reshor.reside = ?" \
        in sql
    assert "ORDER BY auxhor.cod" in sql


# --------------------------------- R20 ---------------------------------- #

def _personas(db) -> None:
    # Rama emp.dni: A solo HENC, B con HEOF, C ordinaria, F HENC con espacios.
    db.executemany("INSERT INTO emp VALUES (?, ?)", [
        (1, "11111111A"), (2, "22222222B"), (3, "33333333C"),
        (6, "66666666F")])
    db.executemany("INSERT INTO res VALUES (?, ?, ?)", [
        (601, 1, None), (602, 2, None), (603, 3, None), (606, 6, None),
        # Rama res.cif: D solo HENC, E con HEGR.
        (604, None, "44444444-D"), (605, None, "55555555 E")])
    _reshor(db, 601, 63, 1)
    _reshor(db, 602, 63, 7)
    _reshor(db, 603, 1, 65)
    _reshor(db, 606, 64)
    _reshor(db, 604, 63)
    _reshor(db, 605, 63, 8)


def test_f066_r20_dnis_sin_extra_excluido_no_cuenta() -> None:
    db = _base()
    _personas(db)
    cliente = SigridSqlite(db)
    pedidos = {"11111111A", "22222222B", "33333333C", "44444444D",
               "55555555E", "66666666F", "77777777G"}
    assert cliente.fetch_dnis_sin_extra(pedidos) == {
        "11111111A", "33333333C", "44444444D", "66666666F", "77777777G"}


def test_f066_r20_dnis_sin_extra_las_dos_ramas() -> None:
    cliente = SigridSqlite(_base())
    cliente.fetch_dnis_sin_extra({"11111111A"})
    (sql,) = cliente.sql
    fragmento = (f"CASE WHEN {condicion_sql_extra('auxhor.cod')} "
                 "THEN 1 ELSE 0 END AS es_he")
    assert sql.count(fragmento) == 2
    assert "LIKE 'HE%' THEN" not in sql


# --------------------------------- R21 ---------------------------------- #

P10 = fq.periodo_de(date(2026, 10, 1))      # 2026-09-16 .. 2026-10-15


def _acc(cod, can, accion="escribir", rec=501):
    return {"accion": accion, "recurso_ide": rec, "hora_codigo": cod,
            "can": can, "fecha_int": 20261001}


@pytest.mark.parametrize("acciones, total", [
    ([_acc("HENC", 2.0), _acc("HEOF", 3.0)], 3.0),
    ([_acc(" henc ", 2.0), _acc("henc", 1.0)], 0.0),
    ([_acc(" heof ", 1.5), _acc("HECAP", 0.5), _acc("MENC", 4.0)], 2.0),
    ([_acc("HL01", 8.0), _acc(None, 1.0), _acc("", 1.0)], 0.0),
])
def test_f066_r21_extras_pendientes(acciones, total) -> None:
    assert fq.extras_pendientes([{"acciones": acciones}], 501, P10) == total


# --------------------------------- R6 ----------------------------------- #

_PATRONES_PROHIBIDOS = (
    re.compile(r"""startswith\(\s*["']HE["']"""),
    re.compile(r"""LIKE\s+'HE%'""", re.IGNORECASE),
    re.compile(r"""["']HENC["']"""),
)


def _ficheros_python_sv4() -> list[Path]:
    return [f for f in RAIZ_SV4.rglob("*.py")
            if "tests" not in f.relative_to(RAIZ_SV4).parts
            and ".venv" not in f.parts and "venv" not in f.parts
            and f.name != "clase_hora.py"]


def test_f066_r6_sin_otra_regla() -> None:
    ficheros = _ficheros_python_sv4()
    assert len(ficheros) > 20
    culpables = [
        (str(f.relative_to(RAIZ_SV4)), pat.pattern)
        for f in ficheros
        for pat in _PATRONES_PROHIBIDOS
        if pat.search(f.read_text(encoding="utf-8"))
    ]
    assert culpables == []


def test_f066_r6_clase_hora_si_la_declara() -> None:
    fuente = (RAIZ_SV4 / "application" / "services"
              / "clase_hora.py").read_text(encoding="utf-8")
    assert fuente.count('PREFIJO_EXTRA = "HE"') == 1
    assert fuente.count('("HENC",)') == 1
