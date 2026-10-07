# tests/test_f036_recursos_por_dni_persona.py
"""F-036 · R18: sv5 `recursos_por_dni` solo considera recursos PERSONA.

Es la otra mitad de la eleccion por DNI de la lista cerrada de `CLAUDE.md`
(sv3 `elegir_recurso` / sv5 `elegir_por_dni`, «mismos candidatos»): desde
F-036 sv3 solo propone recursos con `res.cla = 1`, asi que las dos ramas
del SQL (DNI de la ficha via `res.conide` y `res.cif`) filtran igual.

Sin red: se captura el SQL que el cliente mandaria a sigrid-api.
"""
from __future__ import annotations

import re

from infrastructure.sigrid.sigrid_write_client import SigridWriteClient


def _sql_capturado(monkeypatch) -> tuple[str, list]:
    cliente = SigridWriteClient(base_url="http://sigrid.invalid",
                                function_key="clave-de-test", database="bd")
    pedidos: list[tuple[str, list]] = []

    def leer(sql, params):
        pedidos.append((sql, params))
        return []

    monkeypatch.setattr(cliente, "_read", leer)
    cliente.recursos_por_dni(["12345678-z"])
    (pedido,) = pedidos
    return " ".join(pedido[0].split()), pedido[1]


def _ramas(sql: str) -> list[str]:
    interior = sql[sql.index("FROM (") + len("FROM ("):sql.rindex(") q")]
    return [r.strip() for r in interior.split("UNION ALL")]


def test_f036_r18_las_dos_ramas_filtran_recurso_persona(monkeypatch) -> None:
    sql, params = _sql_capturado(monkeypatch)
    ramas = _ramas(sql)
    assert len(ramas) == 2
    assert "JOIN emp ON emp.ide = res.conide" in ramas[0]
    assert "res.cif" in ramas[1] and "JOIN emp" not in ramas[1]
    for rama in ramas:
        assert re.search(r"\bAND res\.cla = 1\b", rama), rama
    assert params == ["12345678Z", "12345678Z"]


def test_f036_r18_sin_dnis_no_consulta(monkeypatch) -> None:
    cliente = SigridWriteClient(base_url="http://sigrid.invalid",
                                function_key="clave-de-test", database="bd")
    monkeypatch.setattr(cliente, "_read", lambda *_a: 1 / 0)
    assert cliente.recursos_por_dni([None, "", " - "]) == {}
