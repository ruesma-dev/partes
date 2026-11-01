# tests/test_f060_cliente_mover.py
"""F-060 · El CIZ movil en el SQL de `SigridWriteClient` (R13, R20-R22).

  - `lineas_de_racha` (R13): UNA lectura por lote de synckeys con lo que
    `decidir_fin` y `stmt_mover_linea` necesitan (`tex`, `pos`, parte y
    `enlazada` con la expresion de F-046/F-053).
  - `stmt_mover_linea` (R20, R21): UN `UPDATE` de la linea con la fecha,
    la synckey y el parte del dia D; `WHERE` optimista con lo leido, sin
    enlaces y con la guarda de parte abierto sobre el parte de ORIGEN (el
    `WHERE` ve la fila antes del `UPDATE`) y sobre el de DESTINO. Se fija
    el TEXTO EXACTO y los parametros (rigor critico).
  - R22: ni `DELETE` ni `INSERT` en el mover (fuente).

Ni una llamada real: `httpx.post` se sustituye. Datos SINTETICOS.
"""
from __future__ import annotations

import inspect

import pytest
from domain.models.registro_models import LineaSigrid, ObraEntrada
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import (
    LOTE_COMPROBACION,
    SigridWriteClient,
)
from tests.test_f053_cliente_anular import EXPR_ENLAZADA, ApiFalsa, _cli, _sql

GUARDA_ORIGEN = ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
                 "WHERE c.ide = hmores.hmoide AND c.est = ?)")
GUARDA_DESTINO = ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
                  "WHERE c.ide = ? AND c.est = ?)")

MOVER = (
    "UPDATE hmores SET fec = ?, synckey = ?, hmoide = ?, obride = ?, "
    "cenide = ?, paride = ?, caaide = ?, ano = ?, mes = ?, pos = ? "
    "WHERE ide = ? AND reside = ? AND fec = ? AND ISNULL(horide, 0) = ? "
    "AND synckey = ? AND ISNULL(can, 0) = 0 AND NOT (" + EXPR_ENLAZADA
    + ") AND " + GUARDA_ORIGEN + " AND " + GUARDA_DESTINO)

RACHA = (
    "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, hmores.reside AS "
    "reside, hmores.fec AS fec, hmores.horide AS horide, auxhor.cod AS hora, "
    "hmores.can AS can, hmores.tot AS tot, hmores.synckey AS synckey, "
    "hmores.tex AS tex, hmores.pos AS pos, CASE WHEN " + EXPR_ENLAZADA
    + " THEN 1 ELSE 0 END AS enlazada FROM hmores LEFT JOIN auxhor ON "
    "auxhor.ide = hmores.horide WHERE hmores.synckey IN ")

COLS = ["ide", "hmoide", "reside", "fec", "horide", "hora", "can", "tot",
        "synckey", "tex", "pos", "enlazada"]


def _linea(**kw) -> LineaSigrid:
    datos = dict(ide=7001, reside=77, fecha_int=20261003, horide=40,
                 hora_codigo="CIZ", can=0.0, tot=0.0, synckey="partes:3",
                 nuestra=True, hmoide=900, pos=192)
    datos.update(kw)
    return LineaSigrid(**datos)


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=10, codigo="0100", nombre="Obra", empresa=1)
    o.cenide = 55
    return o


def _mover(cli=None, **kw) -> dict:
    args = dict(linea=_linea(), destino=_obra(), hmoide=901, pos=320,
                fecha_int=20261004, synckey="partes:4", paride=33,
                caaide=702, ano=2026, mes=10)
    args.update(kw)
    return (cli or _cli()).stmt_mover_linea(**args)


# ---------------------- R20/R21 · texto y parametros ---------------------- #

def test_f060_r20_mover_texto_exacto() -> None:
    assert _sql(_mover()["sql"]) == MOVER


def test_f060_r20_mover_parametros_exactos() -> None:
    assert _mover()["parameters"] == [
        20261004, "partes:4", 901, 10, 55, 33, 702, 2026, 10, 320,
        7001, 77, 20261003, 40, "partes:3", 1, 901, 1]


def test_f060_r20_mover_convierte_tipos_y_nulos() -> None:
    p = _mover(linea=_linea(ide="7001", reside="77", fecha_int="20261003",
                            horide=None),
               hmoide="901", pos="320", fecha_int="20261004", paride=None,
               caaide="702", ano="2026", mes="10")["parameters"]
    assert p == [20261004, "partes:4", 901, 10, 55, 0, 702, 2026, 10, 320,
                 7001, 77, 20261003, 0, "partes:3", 1, 901, 1]
    assert all(type(x) is int for i, x in enumerate(p) if i not in (1, 14))


def test_f060_r20_mover_obra_sin_centro_es_0() -> None:
    o = ObraEntrada(ide=10, codigo="0100", nombre="Obra", empresa=1)
    assert _mover(destino=o)["parameters"][4] == 0


def test_f060_r21_mover_usa_el_estado_del_cliente() -> None:
    p = _mover(_cli(est_parte=4))["parameters"]
    assert p[15] == 4 and p[17] == 4


def test_f060_r20_mover_solo_cambia_fecha_synckey_y_parte() -> None:
    sql = _sql(_mover()["sql"])
    set_ = sql.split(" SET ", 1)[1].split(" WHERE ", 1)[0]
    columnas = [c.split(" = ")[0] for c in set_.split(", ")]
    assert columnas == ["fec", "synckey", "hmoide", "obride", "cenide",
                        "paride", "caaide", "ano", "mes", "pos"]
    for intacta in ("can", "tot", "pre", "horide", "reside", "tex",
                    "dvaproide", "empabside"):
        assert intacta not in columnas


def test_f060_r21_guardas_sobre_origen_y_destino() -> None:
    sql = _sql(_mover()["sql"])
    assert sql.count("WITH (UPDLOCK, HOLDLOCK)") == 2
    assert sql.index(GUARDA_ORIGEN) < sql.index(GUARDA_DESTINO)


def test_f060_r20_mover_es_metodo_de_instancia() -> None:
    assert not isinstance(
        inspect.getattr_static(SigridWriteClient, "stmt_mover_linea"),
        staticmethod)


# --------------------------- R22 · fuente --------------------------- #

def test_f060_r22_mover_sin_delete_ni_insert() -> None:
    fuente = inspect.getsource(SigridWriteClient.stmt_mover_linea)
    assert "DELETE" not in fuente.upper()
    assert "INSERT INTO" not in fuente.upper()
    sql = _sql(_mover()["sql"]).upper()
    assert sql.startswith("UPDATE HMORES SET ")
    assert "DELETE" not in sql and "INSERT" not in sql


def test_f060_r22_lectura_de_racha_solo_lee() -> None:
    fuente = inspect.getsource(SigridWriteClient.lineas_de_racha)
    for prohibido in ("DELETE", "INSERT", "UPDATE", "escribir("):
        assert prohibido not in fuente


# ------------------------- R13 · lineas_de_racha ------------------------- #

def test_f060_r13_racha_sin_claves_no_lee(monkeypatch) -> None:
    api = ApiFalsa(COLS)
    monkeypatch.setattr(modulo.httpx, "post", api)
    assert _cli().lineas_de_racha([]) == {}
    assert _cli().lineas_de_racha([None, ""]) == {}
    assert api.posts == []


def test_f060_r13_racha_sql_exacto_y_claves_unicas(monkeypatch) -> None:
    api = ApiFalsa(COLS, [])
    monkeypatch.setattr(modulo.httpx, "post", api)
    assert _cli().lineas_de_racha(["partes:3", "partes:2", "partes:3"]) == {}
    (cuerpo,) = api.posts
    assert _sql(cuerpo["sql"]) == RACHA + "(?,?)"
    assert cuerpo["parameters"] == ["partes:2", "partes:3"]


def test_f060_r13_racha_por_lotes(monkeypatch) -> None:
    api = ApiFalsa(COLS, [], [])
    monkeypatch.setattr(modulo.httpx, "post", api)
    claves = [f"partes:{i}" for i in range(LOTE_COMPROBACION + 1)]
    _cli().lineas_de_racha(claves)
    assert [len(p["parameters"]) for p in api.posts] == [LOTE_COMPROBACION,
                                                         1]
    assert _sql(api.posts[1]["sql"]) == RACHA + "(?)"


def test_f060_r13_racha_rellena_lo_que_el_mover_necesita(monkeypatch) -> None:
    api = ApiFalsa(COLS, [
        [7001, 900, 77, 20261003, 40, "CIZ", 0.0, 0.0, " partes:3 ",
         "PRUEBA-IA", 192, 0],
        [7002, None, None, None, None, None, None, None, "partes:2", None,
         None, 1],
    ])
    monkeypatch.setattr(modulo.httpx, "post", api)
    out = _cli().lineas_de_racha(["partes:3", "partes:2"])
    a, b = out["partes:3"], out["partes:2"]
    assert (a.ide, a.hmoide, a.reside, a.fecha_int, a.horide, a.hora_codigo,
            a.can, a.tot, a.synckey, a.tex, a.pos, a.enlazada, a.nuestra) == (
        7001, 900, 77, 20261003, 40, "CIZ", 0.0, 0.0, "partes:3",
        "PRUEBA-IA", 192, False, True)
    assert (b.hmoide, b.reside, b.fecha_int, b.horide, b.pos, b.enlazada,
            b.tex) == (None, 0, 0, None, None, True, None)
    assert a.enlazada is False and b.enlazada is True


def test_f060_r13_racha_truncada_es_excepcion(monkeypatch) -> None:
    import httpx

    def post(url, headers=None, timeout=None, json=None):
        return httpx.Response(200, json={"ok": True, "columns": COLS,
                                         "rows": [], "truncated": True})
    monkeypatch.setattr(modulo.httpx, "post", post)
    with pytest.raises(RuntimeError, match="truncada"):
        _cli().lineas_de_racha(["partes:3"])
