# tests/test_f046_cliente_reajuste.py
"""F-046 · SQL del reajuste en `SigridWriteClient` (R21, R24, R25, R27, R47).

  - lecturas: `lineas_para_reajuste` (con `pre`, `hmoide` y los seis
    enlaces de `hmores`) y `estados_de_partes`;
  - sentencias: `stmt_actualizar_linea` (`UPDATE` con `WHERE` optimista y
    `tot = ROUND(can x pre, 2)`), `stmt_guardia_reajuste` (aborta el lote)
    y `stmt_insertar_extra` (INSERT condicionado a la base);
  - `escribir_lote`: UN solo POST (una transaccion) y filas por sentencia;
  - [E] R47: ninguna sentencia de reajuste es un `DELETE`.

Ni una llamada real: `httpx.post` se sustituye. Datos SINTETICOS.
"""
from __future__ import annotations

import httpx
import pytest
from domain.models.registro_models import LineaSigrid, ObraEntrada
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import (
    ENLACES_HMORES,
    SigridWriteClient,
)


class ApiFalsa:
    """sigrid-api en memoria: respuestas de lectura en orden y una
    respuesta de escritura configurable. Apunta cada POST."""

    def __init__(self, columnas=None, *lecturas, truncated=False,
                 escritura=None, estado=200) -> None:
        self.columnas = columnas or []
        self.lecturas = list(lecturas)
        self.truncated = truncated
        self.escritura = escritura
        self.estado = estado
        self.posts: list[tuple[str, dict]] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.posts.append((url, json))
        if url.endswith("/api/sql/write"):
            return httpx.Response(self.estado, json=self.escritura)
        filas = self.lecturas.pop(0) if self.lecturas else []
        return httpx.Response(self.estado, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cli(monkeypatch, api, **kw) -> SigridWriteClient:
    monkeypatch.setattr(modulo.httpx, "post", api)
    kw.setdefault("est_parte", 1)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd",
                             **kw)


def _sql(texto: str) -> str:
    return " ".join(texto.split())


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=10, codigo="9999", nombre="obra sintetica",
                    empresa=1)
    o.cenide = 77
    return o


# ============================ lecturas ============================ #

COLS_LINEAS = ["ide", "hmoide", "reside", "fec", "horide", "hora", "can",
               "tot", "pre", "synckey", "enlazada"]


def test_f046_r21_enlaces_son_los_seis_de_hmores():
    assert ENLACES_HMORES == ("dvaproide", "dvfproide", "hdereside",
                              "emprccide", "empdpreide", "empabside")


def test_f046_r21_lineas_para_reajuste_trae_pre_hmoide_y_enlaces(
        monkeypatch):
    api = ApiFalsa(COLS_LINEAS, [
        [4001, 7001, 501, 20261014, 7, "HL01", 8.0, 160.0, 20.0,
         "partes:11", 0],
        [4002, 7001, 501, 20261014, 9, "HE01", -4.0, -100.0, 25.0,
         "partes:12", 1],
    ])
    out = _cli(monkeypatch, api).lineas_para_reajuste(
        ["partes:12", "partes:11", "partes:11", ""])
    assert set(out) == {"partes:11", "partes:12"}
    a = out["partes:11"]
    assert (a.ide, a.hmoide, a.reside, a.fecha_int, a.horide, a.can, a.pre,
            a.enlazada, a.nuestra) == (4001, 7001, 501, 20261014, 7, 8.0,
                                       20.0, False, True)
    assert out["partes:12"].enlazada is True
    ((url, cuerpo),) = api.posts
    assert url.endswith("/api/sql/read")
    sql = _sql(cuerpo["sql"])
    assert sql.startswith("SELECT hmores.ide AS ide, hmores.hmoide AS hmoide")
    assert "hmores.pre AS pre" in sql
    for campo in ENLACES_HMORES:
        assert f"ISNULL(hmores.{campo}, 0) <> 0" in sql
    assert sql.endswith("WHERE hmores.synckey IN (?,?)")
    assert cuerpo["parameters"] == ["partes:11", "partes:12"]


def test_f046_r21_lineas_para_reajuste_sin_claves_no_lee(monkeypatch):
    api = ApiFalsa(COLS_LINEAS)
    assert _cli(monkeypatch, api).lineas_para_reajuste(["", None]) == {}
    assert api.posts == []


def test_f046_r21_lineas_para_reajuste_por_lotes(monkeypatch):
    api = ApiFalsa(COLS_LINEAS, [], [])
    claves = [f"partes:{i}" for i in range(1, modulo.LOTE_COMPROBACION + 2)]
    _cli(monkeypatch, api).lineas_para_reajuste(claves)
    assert [len(c["parameters"]) for _, c in api.posts] == [
        modulo.LOTE_COMPROBACION, 1]


def test_f046_r21_lineas_para_reajuste_truncada_es_error(monkeypatch):
    api = ApiFalsa(COLS_LINEAS, [], truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cli(monkeypatch, api).lineas_para_reajuste(["partes:11"])


def test_f046_r21_estados_de_partes(monkeypatch):
    api = ApiFalsa(["ide", "obride", "cod", "est"],
                   [[7001, 10, "PT26/09001", 1], [7002, 10, "PT26/09002",
                                                  None]])
    out = _cli(monkeypatch, api).estados_de_partes([7002, 7001, 7001, 0])
    assert out == {7001: {"cod": "PT26/09001", "est": 1, "obride": 10},
                   7002: {"cod": "PT26/09002", "est": None, "obride": 10}}
    ((_, cuerpo),) = api.posts
    assert _sql(cuerpo["sql"]) == (
        "SELECT hmo.ide AS ide, hmo.obride AS obride, con.cod AS cod, "
        "con.est AS est FROM hmo JOIN con ON con.ide = hmo.ide "
        "WHERE hmo.ide IN (?,?)")
    assert cuerpo["parameters"] == [7001, 7002]


def test_f046_r21_estados_de_partes_vacio_no_lee(monkeypatch):
    api = ApiFalsa()
    assert _cli(monkeypatch, api).estados_de_partes([None, 0]) == {}
    assert api.posts == []


# ============================ sentencias ============================ #

def test_f046_r24_r25_actualizar_linea_where_optimista(monkeypatch):
    st = _cli(monkeypatch, ApiFalsa()).stmt_actualizar_linea(
        ide=4001, synckey="partes:11", antes=8.0, despues=2.5,
        est_registro=1)
    sql = _sql(st["sql"])
    assert sql.startswith(
        "UPDATE hmores SET can = ?, tot = ROUND(? * ISNULL(pre, 0), 2) "
        "WHERE ide = ? AND synckey = ? AND ABS(ISNULL(can, 0) - ?) <= 0.001 "
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
        "WHERE c.ide = hmores.hmoide AND c.est = ?)")   # F-034 R5: UPDLOCK
    for campo in ENLACES_HMORES:
        assert f"AND ISNULL({campo}, 0) = 0" in sql
    assert st["parameters"] == [2.5, 2.5, 4001, "partes:11", 8.0, 1]
    # R24: nunca se tocan cuenta, partida ni codigo de hora.
    for campo in ("caaide", "paride", "horide"):
        assert campo not in sql.split("WHERE")[0]


def test_f046_r24_e_a_cero_es_update_con_can_y_tot_a_cero(monkeypatch):
    st = _cli(monkeypatch, ApiFalsa()).stmt_actualizar_linea(
        ide=4002, synckey="partes:12", antes=-2.0, despues=0.0,
        est_registro=1)
    assert _sql(st["sql"]).startswith("UPDATE hmores SET can = ?")
    # can = 0 y tot = ROUND(0 x pre, 2) = 0.
    assert st["parameters"][:2] == [0.0, 0.0]


def test_f046_r25_guardia_cuenta_las_lineas_en_su_estado(monkeypatch):
    st = _cli(monkeypatch, ApiFalsa(), est_parte=1).stmt_guardia_reajuste(
        [(4001, "partes:11", 8.0), (4002, "partes:12", -4.0)])
    sql = _sql(st["sql"])
    assert sql.startswith(
        "UPDATE hmores SET can = CONVERT(INT, 'reajuste-descuadrado-' + "
        "CAST(ide AS VARCHAR(20))) WHERE ide IN (?,?) AND ((SELECT COUNT(*) "
        "FROM hmores h WHERE ((h.ide = ? AND h.synckey = ? AND "
        "ABS(ISNULL(h.can, 0) - ?) <= 0.001) OR (h.ide = ? AND h.synckey = ? "
        "AND ABS(ISNULL(h.can, 0) - ?) <= 0.001))")
    for campo in ENLACES_HMORES:
        assert f"AND ISNULL(h.{campo}, 0) = 0" in sql
    assert sql.endswith(                               # F-034 R5: UPDLOCK
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE "
        "c.ide = h.hmoide AND c.est = ?)) <> ?)")
    assert st["parameters"] == [4001, 4002, 4001, "partes:11", 8.0,
                                4002, "partes:12", -4.0, 1, 2]


def test_f046_r25_guardia_con_nuevas_exige_que_su_synckey_no_exista(
        monkeypatch):
    st = _cli(monkeypatch, ApiFalsa()).stmt_guardia_reajuste(
        [(4001, "partes:11", 8.0)], nuevas=["partes:990000001"])
    sql = _sql(st["sql"])
    assert sql.endswith(
        "c.est = ?)) <> ? OR EXISTS (SELECT 1 FROM hmores n WHERE "
        "n.synckey IN (?)))")
    assert st["parameters"][-3:] == [1, 1, "partes:990000001"]


def test_f046_r25_guardia_sin_lineas_es_error(monkeypatch):
    with pytest.raises(ValueError):
        _cli(monkeypatch, ApiFalsa()).stmt_guardia_reajuste([])


def test_f046_r24_insertar_extra_condicionada_a_la_base(monkeypatch):
    st = _cli(monkeypatch, ApiFalsa()).stmt_insertar_extra(
        hmoide=7001, obra=_obra(), reside=501, pos=192, fecha_int=20261014,
        horide=9, can=2.5, pre=25.0, paride=33, ano=2026, mes=10,
        synckey="partes:990000001", tex="PRUEBA-IA", caaide=55,
        base_ide=4001, base_synckey="partes:11", base_despues=5.5)
    sql = _sql(st["sql"])
    assert sql == (
        "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
        "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
        "tex, synckey) SELECT x.n, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, "
        "0, ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH "
        "(UPDLOCK, HOLDLOCK)) x WHERE EXISTS (SELECT 1 FROM hmores b WHERE "
        "b.ide = ? AND b.synckey = ? AND ABS(ISNULL(b.can, 0) - ?) <= 0.001) "
        "AND NOT EXISTS (SELECT 1 FROM hmores s WHERE s.synckey = ?) "
        # F-034 R6: la guarda de parte abierto sobre su `hmoide`.
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
        "WHERE c.ide = ? AND c.est = ?)")
    assert st["parameters"] == [
        7001, 501, 77, 10, 33, 192, 20261014, 9, 2.5, 25.0, 62.5, 2026, 10,
        55, "PRUEBA-IA", "partes:990000001",
        4001, "partes:11", 5.5, "partes:990000001", 7001, 1]


def test_f046_r28_insertar_extra_sin_marca_lleva_tex_vacio(monkeypatch):
    st = _cli(monkeypatch, ApiFalsa()).stmt_insertar_extra(
        hmoide=7001, obra=_obra(), reside=501, pos=64, fecha_int=20261014,
        horide=9, can=1.5, pre=10.0, paride=0, ano=2026, mes=10,
        synckey="partes:990000002", tex=None, caaide=0, base_ide=4001,
        base_synckey="partes:11", base_despues=6.5)
    assert st["parameters"][14] == ""


# =========================== escribir_lote =========================== #

def test_f046_r24_escribir_lote_un_solo_post_y_filas_por_sentencia(
        monkeypatch):
    api = ApiFalsa(escritura={
        "ok": True, "committed": True, "total_affected_rows": 2,
        "results": [{"operation": "UPDATE", "affected_rows": 0},
                    {"operation": "UPDATE", "affected_rows": 1},
                    {"operation": "INSERT", "affected_rows": 1}]})
    cli = _cli(monkeypatch, api, max_statements=3)
    sts = [{"sql": "UPDATE hmores SET a = 1 WHERE ide = ?", "parameters": [1]}
           for _ in range(3)]
    assert cli.escribir_lote(sts) == [0, 1, 1]
    ((url, cuerpo),) = api.posts
    assert url.endswith("/api/sql/write")
    assert cuerpo == {"database": "bd", "statements": sts}


def test_f046_r27_escribir_lote_que_no_cabe_es_valueerror_sin_post(
        monkeypatch):
    api = ApiFalsa()
    cli = _cli(monkeypatch, api, max_statements=2)
    with pytest.raises(ValueError, match="no cabe"):
        cli.escribir_lote([{"sql": "UPDATE x SET a=1 WHERE b=1",
                            "parameters": []}] * 3)
    assert api.posts == []


def test_f046_r24_escribir_lote_vacio_no_escribe(monkeypatch):
    api = ApiFalsa()
    assert _cli(monkeypatch, api).escribir_lote([]) == []
    assert api.posts == []


@pytest.mark.parametrize("cuerpo", [
    {"ok": False, "committed": False, "results": []},
    {"ok": True, "committed": False, "results": []},
    {"ok": True, "committed": True},
])
def test_f046_r24_escribir_lote_no_confirmado_es_error(monkeypatch, cuerpo):
    api = ApiFalsa(escritura=cuerpo)
    with pytest.raises(RuntimeError):
        _cli(monkeypatch, api).escribir_lote(
            [{"sql": "UPDATE x SET a=1 WHERE b=1", "parameters": []}])


def test_f046_r24_escribir_lote_http_error(monkeypatch):
    api = ApiFalsa(escritura={"detail": "x"}, estado=400)
    with pytest.raises(RuntimeError, match="HTTP 400"):
        _cli(monkeypatch, api).escribir_lote(
            [{"sql": "UPDATE x SET a=1 WHERE b=1", "parameters": []}])


# ================================ R47 ================================ #

def test_f046_r47_e_ninguna_sentencia_de_reajuste_es_un_delete(monkeypatch):
    cli = _cli(monkeypatch, ApiFalsa())
    sentencias = [
        cli.stmt_guardia_reajuste([(4001, "partes:11", 8.0)],
                                  nuevas=["partes:990000001"]),
        cli.stmt_actualizar_linea(ide=4001, synckey="partes:11", antes=8.0,
                                  despues=0.0, est_registro=1),
        cli.stmt_insertar_extra(
            hmoide=7001, obra=_obra(), reside=501, pos=64,
            fecha_int=20261014, horide=9, can=2.5, pre=25.0, paride=0,
            ano=2026, mes=10, synckey="partes:990000001", tex=None,
            caaide=0, base_ide=4001, base_synckey="partes:11",
            base_despues=5.5),
    ]
    for st in sentencias:
        sql = _sql(st["sql"]).upper()
        assert not sql.startswith("DELETE")
        assert "DELETE " not in sql
        assert sql.split()[0] in {"UPDATE", "INSERT"}


def test_f046_r21_linea_sigrid_por_defecto_sin_enlaces():
    ls = LineaSigrid(ide=1, reside=1, fecha_int=20261014, horide=1,
                     hora_codigo=None, can=1.0, tot=None, synckey=None)
    assert (ls.pre, ls.hmoide, ls.enlazada) == (None, None, False)
