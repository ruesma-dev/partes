# tests/test_f023_r3_todo_paginado.py
"""F-023 · R3 (guardian): NINGUN listado de sv3 se lee sin paginar.

Recorre TODOS los `fetch_*` de `SigridApiClient` y comprueba que cada
peticion que hacen lleva `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` y
`max_rows` = pagina + 1. Un `fetch_*` nuevo que lea a pelo (o uno viejo
al que se le quite la paginacion) pone este test en rojo: un maestro a
medias puede hacer unica a una persona que tiene dos fichas.

En sv3 no hay lecturas exentas (lotes acotados o agregados): si alguna
vez hiciera falta, se anade aqui con su motivo, a la vista del reviewer.
"""
from __future__ import annotations

import inspect
import json

import httpx
import pytest

from infrastructure.sigrid import sigrid_api_client as modulo
from infrastructure.sigrid.sigrid_api_client import (
    PAGINA_FILAS,
    SigridApiClient,
)

#: `fetch_*` que NO paginan a proposito (lote acotado o agregado).
EXENTOS: frozenset[str] = frozenset()

FETCHS = sorted(n for n, _ in inspect.getmembers(SigridApiClient)
                if n.startswith("fetch_"))


def test_f023_r3_paginado_se_recorren_todos_los_fetch() -> None:
    """Que el guardian no quede vacio por un renombrado."""
    assert {"fetch_empleados", "fetch_obras", "fetch_recursos",
            "fetch_empresas"} <= set(FETCHS)


@pytest.mark.parametrize("metodo", [m for m in FETCHS if m not in EXENTOS])
def test_f023_r3_paginado_cada_fetch_pagina(monkeypatch, metodo) -> None:
    peticiones: list[dict] = []

    def responder(request: httpx.Request) -> httpx.Response:
        peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True, "columns": [],
                                         "rows": []})

    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    cliente = SigridApiClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")
    funcion = getattr(cliente, metodo)
    args = [77 for _ in inspect.signature(funcion).parameters]
    funcion(*args)
    assert peticiones, f"{metodo} no hizo ninguna peticion"
    for p in peticiones:
        assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in p["sql"], metodo
        assert p["max_rows"] == PAGINA_FILAS + 1, metodo
