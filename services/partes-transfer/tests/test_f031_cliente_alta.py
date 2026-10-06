# tests/test_f031_cliente_alta.py
"""F-031 v5 · R41, R42: las sentencias del alta protegida.

`stmts_crear_parte` devuelve `[con, hmo]` para UN `escribir` (una
transaccion) con texto y orden de parametros IDENTICOS a los de
`porcentajes` (`services/dedicacion-transfer/infrastructure/sigrid/
sigrid_write_client.py::stmts_crear_parte`, commit `40b9feb`): la cabecera
solo entra si el codigo esta libre en la empresa y el periodo no tiene ya
un parte En registro, con las dos condiciones FUERA del agregado
`MAX(ide)`; el `hmo` solo se cuelga si ese `con` aun no lo tiene.

Sin red: los constructores de sentencias no llaman a sigrid-api. Datos
SINTETICOS.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

#: Literal de `porcentajes` `40b9feb` (espacios normalizados).
SQL_CON = (
    "INSERT INTO con (ide, emp, tip, est, cod, res, fec) "
    "SELECT x.n, ?, ?, ?, ?, ?, ? FROM "
    "(SELECT ISNULL(MAX(ide),0)+1 AS n "
    "FROM con WITH (UPDLOCK, HOLDLOCK)) x "
    "WHERE NOT EXISTS (SELECT 1 FROM con c "
    "WITH (UPDLOCK, HOLDLOCK) "
    "WHERE c.cod = ? AND c.emp = ? AND c.tip = ?) "
    "AND NOT EXISTS (SELECT 1 FROM hmo h "
    "WITH (UPDLOCK, HOLDLOCK) JOIN con r "
    "WITH (UPDLOCK, HOLDLOCK) ON r.ide = h.ide "
    "WHERE h.obride = ? AND h.ano = ? AND h.mes = ? "
    "AND ISNULL(h.reside, 0) = 0 AND r.tip = ? "
    "AND r.est = ?)")
SQL_HMO = (
    "INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, "
    "cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con "
    "WHERE cod = ? AND tip = ? AND emp = ? "
    "AND NOT EXISTS (SELECT 1 FROM hmo h "
    "WHERE h.ide = con.ide)")


def _cliente(**kw) -> SigridWriteClient:
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd",
                             **kw)


def _obra(empresa=28) -> ObraEntrada:
    o = ObraEntrada(ide=20, codigo="0724", nombre="Obra 0724",
                    empresa=empresa)
    o.cenide = 77
    return o


def _sql(texto: str) -> str:
    return " ".join(texto.split())


def _alta(**kw):
    return _cliente(**kw).stmts_crear_parte(
        obra=_obra(), ano=2026, mes=2, cod="PT26/00122", desc="D" * 200)


def test_f031_r41_r42_una_lista_con_cabecera_y_hmo() -> None:
    sts = _alta()
    assert isinstance(sts, list) and len(sts) == 2
    con, hmo = sts
    assert _sql(con["sql"]) == SQL_CON
    assert _sql(hmo["sql"]) == SQL_HMO


def test_f031_r41_parametros_de_la_cabecera_en_orden() -> None:
    (con, _) = _alta(tip_parte=35, est_parte=1)
    assert con["parameters"] == [
        28, 35, 1, "PT26/00122", "D" * 128, 20260228,      # la fila
        "PT26/00122", 28, 35,                              # codigo libre
        20, 2026, 2, 35, 1]                                # sin En registro
    assert len(con["parameters"]) == 14


def test_f031_r41_tipo_y_estado_salen_del_cliente() -> None:
    (con, hmo) = _alta(tip_parte=7, est_parte=9)
    assert [con["parameters"][i] for i in (1, 2, 8, 12, 13)] == \
        [7, 9, 7, 7, 9]
    assert hmo["parameters"][5] == 7


def test_f031_r41_las_condiciones_van_fuera_del_agregado() -> None:
    (con, _) = _alta()
    sql = _sql(con["sql"])
    agregado = "(SELECT ISNULL(MAX(ide),0)+1 AS n FROM con WITH " \
               "(UPDLOCK, HOLDLOCK)) x"
    assert sql.count("WITH (UPDLOCK, HOLDLOCK)") == 4
    assert sql.index(agregado) < sql.index("WHERE NOT EXISTS")
    assert "NOT EXISTS" not in sql[:sql.index(agregado) + len(agregado)]
    assert sql.count("NOT EXISTS") == 2


def test_f031_r42_hmo_solo_si_el_con_no_lo_tiene() -> None:
    (_, hmo) = _alta()
    assert hmo["parameters"] == [77, 20, 2026, 2, "PT26/00122", 35, 28]
    assert _sql(hmo["sql"]).endswith(
        "AND NOT EXISTS (SELECT 1 FROM hmo h WHERE h.ide = con.ide)")


def test_f031_r41_obra_sin_empresa_sigue_siendo_typeerror() -> None:
    with pytest.raises(TypeError):
        _cliente().stmts_crear_parte(obra=_obra(empresa=None), ano=2026,
                                     mes=2, cod="PT26/00001", desc="d")
