# tests/test_f062_cliente_inicio.py
"""F-062 · El CI* y su CIZ hermano en UNA sentencia de `SigridWriteClient`
(R13, R14, DA2; design §5.4).

  - `stmt_insert_inicio_con_fin`: un `INSERT ... SELECT` de dos filas
    (`VALUES` con `k` 0 y 1) con las columnas y valores de
    `stmt_insert_linea`, `can` y `tot` literales 0, el `ide` n y n + 1, la
    guarda de parte abierto de F-034 para las dos filas y, solo en la del
    hermano, que no exista ya su synckey. Se fija el TEXTO EXACTO y los
    parametros en su orden (rigor critico).
  - R14: ni `DELETE` ni `UPDATE` (fuente y SQL).

Ni una llamada real. Datos SINTETICOS.
"""
from __future__ import annotations

import inspect

from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests.test_f053_cliente_anular import _cli, _sql

GUARDA = ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
          "WHERE c.ide = ? AND c.est = ?)")

INICIO_CON_FIN = (
    "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, pos, "
    "fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, tex, "
    "synckey) SELECT x.n + v.k, ?, ?, ?, ?, ?, v.pos, ?, v.horide, 0, "
    "v.pre, 0, ?, ?, 0, 0, v.caaide, ?, v.synckey FROM (SELECT "
    "ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH (UPDLOCK, HOLDLOCK)) x "
    "CROSS JOIN (VALUES (0, ?, ?, ?, ?, ?), (1, ?, ?, ?, ?, ?)) v(k, pos, "
    "horide, pre, caaide, synckey) WHERE " + GUARDA + " AND (v.k = 0 OR "
    "NOT EXISTS (SELECT 1 FROM hmores s WHERE s.synckey = ?))")


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=10, codigo="0100", nombre="Obra", empresa=1)
    o.cenide = 55
    return o


def _inicio(cli=None, **kw) -> dict:
    args = dict(hmoide=901, obra=_obra(), reside=77, fecha_int=20261004,
                paride=33, ano=2026, mes=10, tex="PRUEBA-IA",
                pos=320, horide=30, pre=2.5, caaide=702,
                synckey="partes:4",
                pos_fin=384, horide_fin=40, pre_fin=1.25, caaide_fin=703,
                synckey_fin="partes:4:ciz")
    args.update(kw)
    return (cli or _cli()).stmt_insert_inicio_con_fin(**args)


def test_f062_r13_inicio_con_fin_texto_exacto() -> None:
    assert _sql(_inicio()["sql"]) == INICIO_CON_FIN


def test_f062_r13_inicio_con_fin_parametros_en_orden() -> None:
    assert _inicio()["parameters"] == [
        901, 77, 55, 10, 33, 20261004, 2026, 10, "PRUEBA-IA",
        320, 30, 2.5, 702, "partes:4",
        384, 40, 1.25, 703, "partes:4:ciz",
        901, 1,
        "partes:4:ciz"]


def test_f062_r13_inicio_con_fin_tipos_y_nulos() -> None:
    """Como `stmt_insert_linea`: enteros, `tex` vacio sin pruebas, sin
    partida `paride` 0 y el estado de la guarda del cliente."""
    o = _obra()
    o.cenide = None
    p = _inicio(_cli(est_parte=7), tex=None, paride=None, hmoide="901",
                reside="77", fecha_int="20261004", pos="320", horide="30",
                pre="2.5", caaide="702", pos_fin="384", horide_fin="40",
                pre_fin="1", caaide_fin="703", ano="2026", mes="10",
                obra=o)["parameters"]
    assert p == [901, 77, 0, 10, 0, 20261004, 2026, 10, "",
                 320, 30, 2.5, 702, "partes:4",
                 384, 40, 1.0, 703, "partes:4:ciz",
                 901, 7, "partes:4:ciz"]
    assert [type(x) for x in p[:8]] == [int] * 8
    assert isinstance(p[11], float) and isinstance(p[16], float)


def test_f062_r13_mismas_columnas_que_stmt_insert_linea() -> None:
    linea = _cli().stmt_insert_linea(
        hmoide=901, obra=_obra(), reside=77, pos=320, fecha_int=20261004,
        horide=30, can=0.0, pre=2.5, paride=33, ano=2026, mes=10,
        synckey="partes:4", tex="PRUEBA-IA", caaide=702)
    columnas = _sql(linea["sql"]).split(") SELECT")[0]
    assert _sql(_inicio()["sql"]).split(") SELECT")[0] == columnas


def test_f062_r14_sin_delete_ni_update() -> None:
    fuente = inspect.getsource(SigridWriteClient.stmt_insert_inicio_con_fin)
    assert "DELETE" not in fuente.upper() and "UPDATE " not in fuente
    sql = _sql(_inicio()["sql"]).upper()
    assert sql.startswith("INSERT INTO HMORES (")
    assert "DELETE" not in sql and "UPDATE HMORES" not in sql
    assert "DELETE" not in inspect.getsource(modulo.synckey_ciz_de)


def test_f062_r13_una_sola_sentencia() -> None:
    """DA2: las dos filas viajan en UNA sentencia, nunca partidas entre los
    lotes de `escribir` (corte de 15)."""
    st = _inicio()
    assert set(st) == {"sql", "parameters"}
    assert _sql(st["sql"]).count("INSERT INTO") == 1
