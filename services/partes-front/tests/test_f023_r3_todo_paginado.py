# tests/test_f023_r3_todo_paginado.py
"""F-023 · R3 (guardian): ningun listado de sv4 se lee sin paginar.

Recorre TODOS los `fetch_*` de `SigridLookupClient`: cada peticion de un
listado lleva `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` y `max_rows` =
pagina + 1. Las lecturas EXENTAS son las de lote acotado o agregado
(design §6, `sigrid_api.md` §6.7) y estan escritas aqui, con su motivo:
un `fetch_*` nuevo sin paginar pone el test en rojo hasta que alguien
decida, a la vista del reviewer, si es un listado o un lote.
"""
from __future__ import annotations

import inspect
import json

import httpx
import pytest

from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import (
    PAGINA_FILAS,
    SigridLookupClient,
)

#: `fetch_*` que NO paginan a proposito.
EXENTOS: dict[str, str] = {
    "fetch_dnis_sin_extra": "agregado por DNI de un lote acotado",
    "fetch_hora_extra_recurso": "TOP 1 de un recurso",
}

FETCHS = sorted(n for n, _ in inspect.getmembers(SigridLookupClient)
                if n.startswith("fetch_"))


def _cliente(monkeypatch, peticiones: list[dict]) -> SigridLookupClient:
    def responder(request: httpx.Request) -> httpx.Response:
        peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True, "columns": [],
                                         "rows": []})

    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridLookupClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")


def test_f023_r3_paginado_los_exentos_existen() -> None:
    """Un exento renombrado o borrado no puede seguir eximiendo a nadie."""
    assert set(EXENTOS) <= set(FETCHS)
    assert {"fetch_obras", "fetch_empleados", "fetch_tipos_hora",
            "fetch_partidas_obra"} <= set(FETCHS)


@pytest.mark.parametrize("metodo", [m for m in FETCHS if m not in EXENTOS])
def test_f023_r3_paginado_cada_fetch_pagina(monkeypatch, metodo) -> None:
    peticiones: list[dict] = []
    funcion = getattr(_cliente(monkeypatch, peticiones), metodo)
    funcion(*[77 for _ in inspect.signature(funcion).parameters])
    assert peticiones, f"{metodo} no hizo ninguna peticion"
    for p in peticiones:
        assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in p["sql"], metodo
        assert p["max_rows"] == PAGINA_FILAS + 1, metodo


@pytest.mark.parametrize("metodo, args", [
    ("fetch_dnis_sin_extra", ({"1A"},)), ("fetch_hora_extra_recurso", (5,)),
])
def test_f023_r3_paginado_los_exentos_leen_un_lote(
        monkeypatch, metodo, args) -> None:
    peticiones: list[dict] = []
    getattr(_cliente(monkeypatch, peticiones), metodo)(*args)
    (p,) = peticiones
    assert "OFFSET" not in p["sql"]
