# tests/test_f053_cliente_anular.py
"""F-053 · El pisado pone a 0 en el SQL de `SigridWriteClient` (R2-R4, R9).

  - `stmt_anular_linea` (R2, R3, DA12): `UPDATE hmores SET can = 0, tot = 0`
    con `WHERE` optimista (`ide`, recurso, fecha, codigo y `can` leido con
    tolerancia 0,001), sin enlaces y con la guarda de parte abierto de
    F-034. Se fija el TEXTO EXACTO y los parametros (rigor critico).
  - R4: ni el cliente ni el pipeline de registro contienen `DELETE` ni
    `stmt_borrar_linea` (test sobre la fuente; `prueba_escritura_sigrid.py`
    queda fuera, DA9).
  - R9: `lineas_existentes` lee `enlazada` con la MISMA expresion que
    `lineas_para_reajuste` (`_expr_enlazada`).

Ni una llamada real: `httpx.post` se sustituye. Datos SINTETICOS.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import httpx
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import (
    ENLACES_HMORES,
    SigridWriteClient,
)

RAIZ = Path(__file__).resolve().parents[1]

SIN_ENLACES = ("AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0 "
               "AND ISNULL(hdereside, 0) = 0 AND ISNULL(emprccide, 0) = 0 "
               "AND ISNULL(empdpreide, 0) = 0 AND ISNULL(empabside, 0) = 0")

ANULAR = (
    "UPDATE hmores SET can = 0, tot = 0 WHERE ide = ? AND reside = ? "
    "AND fec = ? AND ISNULL(horide, 0) = ? AND ABS(ISNULL(can, 0) - ?) "
    "<= 0.001 " + SIN_ENLACES + " AND EXISTS (SELECT 1 FROM con c WITH "
    "(UPDLOCK, HOLDLOCK) WHERE c.ide = hmores.hmoide AND c.est = ?)")

EXPR_ENLAZADA = (
    "ISNULL(hmores.dvaproide, 0) <> 0 OR ISNULL(hmores.dvfproide, 0) <> 0 "
    "OR ISNULL(hmores.hdereside, 0) <> 0 OR ISNULL(hmores.emprccide, 0) <> 0 "
    "OR ISNULL(hmores.empdpreide, 0) <> 0 OR ISNULL(hmores.empabside, 0) "
    "<> 0")


class ApiFalsa:
    """sigrid-api en memoria (lecturas en orden); apunta cada POST."""

    def __init__(self, columnas, *lecturas) -> None:
        self.columnas = columnas
        self.lecturas = list(lecturas)
        self.posts: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        assert url.endswith("/api/sql/read")
        self.posts.append(json)
        filas = self.lecturas.pop(0) if self.lecturas else []
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": False})


def _sql(texto: str) -> str:
    return " ".join(texto.split())


def _cli(est_parte: int = 1) -> SigridWriteClient:
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd",
                             est_parte=est_parte)


def _anular(cli=None, **kw) -> dict:
    args = {"ide": 9001, "reside": 77, "fecha_int": 20261015, "horide": 11,
            "antes": 8.0}
    args.update(kw)
    return (cli or _cli()).stmt_anular_linea(**args)


# ---------------------- R2 · texto y parametros exactos ---------------------- #

def test_f053_r2_anular_texto_exacto() -> None:
    assert _sql(_anular()["sql"]) == ANULAR


def test_f053_r2_anular_parametros_exactos() -> None:
    assert _anular()["parameters"] == [9001, 77, 20261015, 11, 8.0, 1]


def test_f053_r2_anular_convierte_tipos() -> None:
    p = _anular(ide="9001", reside="77", fecha_int="20261015", horide="11",
                antes=8)["parameters"]
    assert p == [9001, 77, 20261015, 11, 8.0, 1]
    assert [type(x) for x in p] == [int, int, int, int, float, int]


def test_f053_r2_anular_horide_nulo_es_0_y_antes_nulo_es_0() -> None:
    p = _anular(horide=None, antes=None)["parameters"]
    assert p[3] == 0 and isinstance(p[3], int)
    assert p[4] == 0.0 and isinstance(p[4], float)


def test_f053_r2_anular_horas_negativas_se_respetan() -> None:
    assert _anular(antes=-2.5)["parameters"][4] == -2.5


def test_f053_r2_anular_usa_el_estado_del_cliente() -> None:
    assert _anular(_cli(est_parte=4))["parameters"][-1] == 4


def test_f053_r2_anular_es_metodo_de_instancia() -> None:
    assert not isinstance(
        inspect.getattr_static(SigridWriteClient, "stmt_anular_linea"),
        staticmethod)


def test_f053_r2_anular_lleva_todos_los_enlaces() -> None:
    sql = _sql(_anular()["sql"])
    for campo in ENLACES_HMORES:
        assert f"AND ISNULL({campo}, 0) = 0" in sql


# ----------------------- R3 · solo `can` y `tot` ----------------------- #

def test_f053_r3_anular_solo_cambia_can_y_tot() -> None:
    sql = _sql(_anular()["sql"])
    set_ = sql.split(" SET ", 1)[1].split(" WHERE ", 1)[0]
    assert set_ == "can = 0, tot = 0"
    for columna in ("synckey", "tex", "paride", "caaide", "horide", "pre",
                    "pos", "reside", "fec"):
        assert columna not in set_


# ----------------------- R4 · ningun DELETE (fuente) ----------------------- #

def test_f053_r4_fuente_cliente_sin_delete_ni_borrar() -> None:
    fuente = (RAIZ / "infrastructure" / "sigrid"
              / "sigrid_write_client.py").read_text(encoding="utf-8")
    assert "DELETE" not in fuente.upper().replace("DELETED", "")
    assert "stmt_borrar_linea" not in fuente
    assert not hasattr(SigridWriteClient, "stmt_borrar_linea")


def test_f053_r4_fuente_pipeline_sin_delete_ni_borrar() -> None:
    fuente = (RAIZ / "application" / "pipelines"
              / "registro_pipeline.py").read_text(encoding="utf-8")
    assert "DELETE" not in fuente.upper()
    assert "stmt_borrar_linea" not in fuente
    assert "stmt_anular_linea" in fuente


def test_f053_r4_el_cliente_no_escribe_en_con_ni_hmo_salvo_el_alta() -> None:
    fuente = inspect.getsource(SigridWriteClient)
    assert re.findall(r"(?:INSERT INTO|UPDATE|DELETE FROM) (con|hmo)\b",
                      fuente) == ["con", "hmo"]


# ------------------ R9 · `enlazada` en `lineas_existentes` ------------------ #

COLS = ["ide", "reside", "fec", "horide", "hora", "can", "tot", "synckey",
        "enlazada"]


def test_f053_r9_expr_enlazada_es_la_de_los_seis_enlaces() -> None:
    assert _sql(SigridWriteClient._expr_enlazada()) == EXPR_ENLAZADA


def test_f053_r9_lineas_existentes_sql_exacto(monkeypatch) -> None:
    api = ApiFalsa(COLS, [])
    monkeypatch.setattr(modulo.httpx, "post", api)
    assert _cli().lineas_existentes(900, [78, 77, 77], [20261016,
                                                       20261015]) == []
    (cuerpo,) = api.posts
    assert _sql(cuerpo["sql"]) == (
        "SELECT hmores.ide AS ide, hmores.reside AS reside, hmores.fec AS "
        "fec, hmores.horide AS horide, auxhor.cod AS hora, hmores.can AS "
        "can, hmores.tot AS tot, hmores.synckey AS synckey, CASE WHEN "
        + EXPR_ENLAZADA + " THEN 1 ELSE 0 END AS enlazada FROM hmores LEFT "
        "JOIN auxhor ON auxhor.ide = hmores.horide WHERE hmores.hmoide = ? "
        "AND hmores.reside IN (?,?) AND hmores.fec IN (?,?) ORDER BY "
        "hmores.pos")
    assert cuerpo["parameters"] == [900, 77, 78, 20261015, 20261016]


def test_f053_r9_lineas_existentes_rellena_enlazada_y_parte(
        monkeypatch) -> None:
    api = ApiFalsa(COLS, [
        [9001, 77, 20261015, 11, "HN", 8.0, 120.0, None, 1],
        [9002, 77, 20261015, None, None, 0.0, 0.0, " partes:480 ", 0],
    ])
    monkeypatch.setattr(modulo.httpx, "post", api)
    a, b = _cli().lineas_existentes(900, [77], [20261015])
    assert (a.ide, a.reside, a.fecha_int, a.horide, a.hora_codigo, a.can,
            a.tot, a.synckey, a.nuestra, a.enlazada, a.hmoide) == (
        9001, 77, 20261015, 11, "HN", 8.0, 120.0, None, False, True, 900)
    assert (b.horide, b.synckey, b.nuestra, b.enlazada, b.hmoide) == (
        None, "partes:480", True, False, 900)
    assert a.enlazada is True and b.enlazada is False


def test_f053_r9_reajuste_usa_la_misma_expresion(monkeypatch) -> None:
    """La lectura del reajuste (F-046) y la de choques comparten helper."""
    api = ApiFalsa(["ide"], [])
    monkeypatch.setattr(modulo.httpx, "post", api)
    _cli().lineas_para_reajuste(["partes:11"])
    _cli().lineas_existentes(900, [77], [20261015])
    caso = f"CASE WHEN {EXPR_ENLAZADA} THEN 1 ELSE 0 END AS enlazada"
    assert all(caso in _sql(p["sql"]) for p in api.posts)
    for metodo in ("lineas_existentes", "lineas_para_reajuste"):
        assert "self._expr_enlazada()" in inspect.getsource(
            getattr(SigridWriteClient, metodo))
