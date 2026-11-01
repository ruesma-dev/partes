# tests/test_f034_cliente_guarda.py
"""F-034 · La guarda de parte abierto en el SQL de `SigridWriteClient`
(R1-R7, design §3).

Toda sentencia de sv5 que inserta, actualiza o borra una fila de `hmores`
lleva `EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE c.ide =
<hmoide> AND c.est = ?)`: SQL Server comprueba el estado en el mismo
instante de escribir y retiene la fila de `con` hasta el `commit`. Se fija
el TEXTO EXACTO y la lista de parametros de cada sentencia (rigor critico:
un mutante de cadena tiene que morir).

Ni una llamada real: los constructores de sentencias no tocan la red.
Datos SINTETICOS.
"""
from __future__ import annotations

import inspect
import re

import pytest
from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

GUARDA_Q = ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
            "WHERE c.ide = ? AND c.est = ?)")

INSERT_LINEA = (
    "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
    "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
    "tex, synckey) SELECT x.n, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, "
    "?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH "
    "(UPDLOCK, HOLDLOCK)) x WHERE EXISTS (SELECT 1 FROM con c WITH "
    "(UPDLOCK, HOLDLOCK) WHERE c.ide = ? AND c.est = ?)")

PARAMS_LINEA = [900, 501, 77, 200, 33, 128, 20260915, 11, 8.0, 10.5, 84.0,
                2026, 9, 701, "", "partes:1"]


def _sql(texto: str) -> str:
    return " ".join(texto.split())


def _cli(est_parte: int = 1) -> SigridWriteClient:
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd",
                             est_parte=est_parte)


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=200, codigo="0404", nombre="Pruebas", empresa=1)
    o.cenide = 77
    return o


def _insert(cli=None, **kw) -> dict:
    args = {"hmoide": 900, "obra": _obra(), "reside": 501, "pos": 128,
            "fecha_int": 20260915, "horide": 11, "can": 8.0, "pre": 10.5,
            "paride": 33, "ano": 2026, "mes": 9, "synckey": "partes:1",
            "tex": None, "caaide": 701}
    args.update(kw)
    return (cli or _cli()).stmt_insert_linea(**args)


# --------------------------- R1 · el fragmento --------------------------- #

def test_f034_r1_guarda_texto_exacto() -> None:
    cli = _cli()
    assert cli._guarda_parte_abierto("?") == GUARDA_Q
    assert cli._guarda_parte_abierto("hmores.hmoide") == (
        "EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
        "WHERE c.ide = hmores.hmoide AND c.est = ?)")


# ------------------------ R2 · INSERT de la linea ------------------------ #

def test_f034_r2_insert_linea_texto_y_parametros_exactos() -> None:
    st = _insert()
    assert _sql(st["sql"]) == INSERT_LINEA
    assert st["parameters"] == PARAMS_LINEA + [900, 1]
    assert _sql(st["sql"]).count("?") == len(st["parameters"])


def test_f034_r2_el_estado_es_est_parte_activo() -> None:
    assert _insert(_cli(est_parte=7))["parameters"][-1] == 7


def test_f034_r2_la_guarda_es_sobre_el_hmoide_de_la_linea() -> None:
    st = _insert(hmoide="905")
    assert st["parameters"][0] == 905 and st["parameters"][-2] == 905
    assert isinstance(st["parameters"][-2], int)


def test_f034_r2_ide_de_subconsulta_nunca_agregado_con_where() -> None:
    """Un `SELECT MAX(...)+1 ... WHERE <falso>` devuelve fila igualmente:
    el `ide` sale de la subconsulta `x` y el `WHERE` va fuera."""
    sql = _sql(_insert()["sql"])
    assert "SELECT x.n, " in sql
    assert "SELECT ISNULL(MAX(ide),0)+1," not in sql
    assert re.search(r"MAX\(ide\),0\)\+1 AS n FROM hmores WITH "
                     r"\(UPDLOCK, HOLDLOCK\)\) x WHERE ", sql)


# -------------------- R4 · INSERT con lineas pisadas -------------------- #

def test_f034_r4_con_pisadas_solo_entra_si_ninguna_sigue_con_horas() -> None:
    st = _insert(pisadas=[4001, "4002"])
    assert _sql(st["sql"]) == INSERT_LINEA + (
        " AND NOT EXISTS (SELECT 1 FROM hmores p WHERE p.ide IN (?,?) "
        "AND ISNULL(p.can, 0) <> 0)")
    assert st["parameters"] == PARAMS_LINEA + [900, 1, 4001, 4002]
    assert isinstance(st["parameters"][-1], int)
    assert _sql(st["sql"]).count("?") == len(st["parameters"])


def test_f034_r4_una_pisada() -> None:
    st = _insert(pisadas=(4001,))
    assert _sql(st["sql"]).endswith(
        "AND NOT EXISTS (SELECT 1 FROM hmores p WHERE p.ide IN (?) "
        "AND ISNULL(p.can, 0) <> 0)")
    assert st["parameters"][-3:] == [900, 1, 4001]


@pytest.mark.parametrize("pisadas", [(), []])
def test_f034_r4_sin_pisadas_la_condicion_no_aparece(pisadas) -> None:
    st = _insert(pisadas=pisadas)
    assert _sql(st["sql"]) == INSERT_LINEA
    assert "NOT EXISTS" not in st["sql"]
    assert st["parameters"] == PARAMS_LINEA + [900, 1]


def test_f034_r4_pisadas_es_opcional() -> None:
    assert _insert() == _insert(pisadas=())


# ------------------ R3 · la pisada (F-053: puesta a 0) ------------------ #
# Enmienda de F-053 (T2): el `DELETE` de la pisada (`stmt_borrar_linea`) es
# ahora `stmt_anular_linea`; la guarda de R3 se exige igual, sobre el parte
# de la propia fila, y al final de la sentencia.

def _anular(cli=None) -> dict:
    return (cli or _cli()).stmt_anular_linea(
        ide="4001", reside=77, fecha_int=20260915, horide=11, antes=8.0)


def test_f034_r3_anular_linea_con_guarda_sobre_su_parte() -> None:
    st = _anular()
    assert _sql(st["sql"]).startswith("UPDATE hmores SET can = 0, tot = 0 "
                                      "WHERE ide = ? AND ")
    assert _sql(st["sql"]).endswith(
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE "
        "c.ide = hmores.hmoide AND c.est = ?)")
    assert st["parameters"][0] == 4001 and st["parameters"][-1] == 1
    assert isinstance(st["parameters"][0], int)


def test_f034_r3_anular_usa_el_estado_del_cliente() -> None:
    assert _anular(_cli(est_parte=4))["parameters"][-1] == 4


def test_f034_r3_anular_es_metodo_de_instancia() -> None:
    assert not isinstance(
        inspect.getattr_static(SigridWriteClient, "stmt_anular_linea"),
        staticmethod)


# ----------------------------- R7 · sin mas ----------------------------- #

def test_f034_r7_el_cliente_no_tiene_ningun_delete() -> None:
    """Enmienda de F-053 (R4): de «un solo `DELETE`» a ninguno."""
    fuente = inspect.getsource(SigridWriteClient)
    assert re.findall(r"DELETE\s", fuente) == []
    assert not hasattr(SigridWriteClient, "stmt_borrar_linea")


def test_f034_r7_ninguna_escritura_en_con_ni_hmo_salvo_el_alta() -> None:
    """Las unicas sentencias sobre `con`/`hmo` son las dos del alta
    (`stmts_crear_parte`, que no cambia)."""
    fuente = inspect.getsource(SigridWriteClient)
    assert re.findall(r"(?:INSERT INTO|UPDATE|DELETE FROM) (con|hmo)\b",
                      fuente) == ["con", "hmo"]
    alta = inspect.getsource(SigridWriteClient.stmts_crear_parte)
    assert "INSERT INTO con " in alta and "INSERT INTO hmo " in alta


# ---------------------- R5 · reajuste F-046: guardia ---------------------- #

def test_f034_r5_guardia_reajuste_lee_con_con_updlock() -> None:
    st = _cli().stmt_guardia_reajuste([(4001, "partes:11", 8.0)])
    sql = _sql(st["sql"])
    assert sql.endswith(
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE "
        "c.ide = h.hmoide AND c.est = ?)) <> ?)")
    assert "FROM con c WHERE" not in sql
    # Sus parametros de estado no cambian (R5).
    assert st["parameters"] == [4001, 4001, "partes:11", 8.0, 1, 1]


def test_f034_r5_actualizar_linea_lee_con_con_updlock() -> None:
    st = _cli().stmt_actualizar_linea(ide=4001, synckey="partes:11",
                                      antes=8.0, despues=2.5,
                                      est_registro=1)
    sql = _sql(st["sql"])
    assert sql.startswith(
        "UPDATE hmores SET can = ?, tot = ROUND(? * ISNULL(pre, 0), 2) "
        "WHERE ide = ? AND synckey = ? AND ABS(ISNULL(can, 0) - ?) <= 0.001 "
        "AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE "
        "c.ide = hmores.hmoide AND c.est = ?) AND ISNULL(dvaproide, 0) = 0")
    assert "FROM con c WHERE" not in sql
    assert st["parameters"] == [2.5, 2.5, 4001, "partes:11", 8.0, 1]


def test_f034_r5_actualizar_conserva_su_est_registro() -> None:
    st = _cli(est_parte=1).stmt_actualizar_linea(
        ide=4001, synckey="partes:11", antes=8.0, despues=2.5,
        est_registro=6)
    assert st["parameters"][-1] == 6


# -------------------- R6 · reajuste F-046: extra nueva -------------------- #

def _extra(cli=None, **kw) -> dict:
    args = {"hmoide": 7001, "obra": _obra(), "reside": 501, "pos": 192,
            "fecha_int": 20261014, "horide": 9, "can": 2.5, "pre": 25.0,
            "paride": 33, "ano": 2026, "mes": 10,
            "synckey": "partes:990000001", "tex": "PRUEBA-IA", "caaide": 55,
            "base_ide": 4001, "base_synckey": "partes:11",
            "base_despues": 5.5}
    args.update(kw)
    return (cli or _cli()).stmt_insertar_extra(**args)


def test_f034_r6_insertar_extra_lleva_la_guarda_sobre_su_parte() -> None:
    st = _extra()
    assert _sql(st["sql"]) == (
        "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
        "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
        "tex, synckey) SELECT x.n, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, "
        "0, ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH "
        "(UPDLOCK, HOLDLOCK)) x WHERE EXISTS (SELECT 1 FROM hmores b WHERE "
        "b.ide = ? AND b.synckey = ? AND ABS(ISNULL(b.can, 0) - ?) <= 0.001) "
        "AND NOT EXISTS (SELECT 1 FROM hmores s WHERE s.synckey = ?) "
        "AND " + GUARDA_Q)
    assert st["parameters"] == [
        7001, 501, 77, 200, 33, 192, 20261014, 9, 2.5, 25.0, 62.5, 2026, 10,
        55, "PRUEBA-IA", "partes:990000001",
        4001, "partes:11", 5.5, "partes:990000001", 7001, 1]
    assert _sql(st["sql"]).count("?") == len(st["parameters"])


def test_f034_r6_insertar_extra_guarda_con_su_hmoide_y_est_activo() -> None:
    st = _extra(_cli(est_parte=8), hmoide="7404")
    assert st["parameters"][-2:] == [7404, 8]
    assert isinstance(st["parameters"][-2], int)


# --------------- R1 · todas las sentencias de lineas, guardadas --------------- #

def test_f034_r1_toda_sentencia_que_toca_hmores_lleva_la_guarda() -> None:
    cli = _cli()
    sentencias = [
        _insert(cli), _insert(cli, pisadas=[4001]),
        _anular(cli),
        cli.stmt_guardia_reajuste([(4001, "partes:11", 8.0)]),
        cli.stmt_actualizar_linea(ide=4001, synckey="partes:11", antes=8.0,
                                  despues=0.0, est_registro=1),
        _extra(cli),
    ]
    for st in sentencias:
        sql = _sql(st["sql"])
        assert re.match(r"(INSERT INTO|UPDATE|DELETE FROM) hmores\b", sql)
        assert re.search(r"EXISTS \(SELECT 1 FROM con c WITH \(UPDLOCK, "
                         r"HOLDLOCK\) WHERE c\.ide = (\?|hmores\.hmoide|"
                         r"h\.hmoide) AND c\.est = \?\)", sql), sql
        assert "FROM con c WHERE" not in sql


# ------------- T12 · bordes del INSERT que la mutacion dejo vivos ------------- #

def test_f034_t12_insert_linea_sin_partida_va_con_paride_0() -> None:
    """Mutante #20 (`paride or 1`): una linea sin partida no inventa la 1."""
    assert _insert(paride=None)["parameters"][4] == 0
    assert _insert(paride=0)["parameters"][4] == 0


def test_f034_t12_insert_linea_tot_redondeado_a_2_decimales() -> None:
    """Mutante #19 (`round(..., 3)`): `tot` va a 2 decimales."""
    assert _insert(can=0.5, pre=0.123)["parameters"][10] == 0.06
