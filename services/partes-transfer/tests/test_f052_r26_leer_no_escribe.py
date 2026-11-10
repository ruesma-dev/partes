# tests/test_f052_r26_leer_no_escribe.py
"""F-052 en sv5 (R26): `POST /api/sincronizar/leer` nunca escribe en Sigrid.

Ninguna sentencia de F-052 escribe: la ruta solo usa las dos lecturas del
cliente (`lineas_sincronizar` y `lineas_sincronizar_por_synckey`) y nunca
`escribir`, ni cuando todo va bien ni cuando la lectura falla o la petición
sobra. El espía apunta la llamada sin reventar (un `except` de la ruta no
puede taparla), y una guardia estática mira el cuerpo de la ruta.

Sin red: dobles del cliente.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import build_app
from tests.test_f052_api_sincronizar import CUERPO_OBRA, _linea, _settings

LECTURAS = {"lineas_sincronizar", "lineas_sincronizar_por_synckey"}


class LectorEspia:
    """Cliente de Sigrid en memoria que apunta TODO lo que se le pide:
    las lecturas, `escribir` y cualquier otro método."""

    def __init__(self, *, fallo: str | None = None) -> None:
        self.fallo = fallo
        self.llamadas: list[str] = []

    def lineas_sincronizar(self, **kwargs):
        self.llamadas.append("lineas_sincronizar")
        if self.fallo == "ambito":
            raise RuntimeError("sigrid-api caida")
        return [_linea(30)]

    def lineas_sincronizar_por_synckey(self, claves):
        self.llamadas.append("lineas_sincronizar_por_synckey")
        if self.fallo == "synckey":
            raise TimeoutError("corte de 230 s")
        return [_linea(10, origen="partes", registro_id=1)]

    def escribir(self, statements):
        self.llamadas.append("escribir")
        return {"ok": True}

    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        self.llamadas.append(nombre)
        return lambda *a, **k: {"ok": True}


@pytest.mark.parametrize(("fallo", "cuerpo", "status"), [
    (None, CUERPO_OBRA, 200),
    (None, {"recurso_ide": 501, "desde": 20261001, "hasta": 20261031,
            "registro_ids": []}, 200),
    ("ambito", CUERPO_OBRA, 502),
    ("synckey", CUERPO_OBRA, 502),
    (None, {"obra_ide": 686, "desde": 20261001, "hasta": 20261031,
            "registro_ids": [1, 2, 3, 4]}, 422),     # sobran ids (tope 3)
])
def test_f052_r26_leer_nunca_llama_a_escribir(fallo, cuerpo, status) -> None:
    lector = LectorEspia(fallo=fallo)
    st = _settings(max_ids=3)
    app = build_app(st, pipeline=RegistroPipeline(cliente=lector,
                                                  settings=st),
                    lector=lector)
    r = TestClient(app).post("/api/sincronizar/leer", json=cuerpo)
    assert r.status_code == status
    assert "escribir" not in lector.llamadas
    assert set(lector.llamadas) <= LECTURAS
    if status == 422:
        assert lector.llamadas == []


def test_f052_r26_la_ruta_de_leer_no_nombra_escrituras() -> None:
    """Guardia estática: el cuerpo de la ruta no menciona `escribir`, el
    lock ni el pipeline (que es quien registra en Sigrid)."""
    fuente = Path(inspect.getsourcefile(modulo_app)).read_text(
        encoding="utf-8")
    rutas = [n for n in ast.walk(ast.parse(fuente))
             if isinstance(n, ast.FunctionDef)
             and any(isinstance(d, ast.Call) and d.args
                     and isinstance(d.args[0], ast.Constant)
                     and d.args[0].value == "/api/sincronizar/leer"
                     for d in n.decorator_list)]
    assert len(rutas) == 1
    nombres = ({n.attr for n in ast.walk(rutas[0])
                if isinstance(n, ast.Attribute)}
               | {n.id for n in ast.walk(rutas[0])
                  if isinstance(n, ast.Name)})
    assert not nombres & {"escribir", "lock", "_lock", "pipeline"}
    lecturas = {n.func.attr for n in ast.walk(rutas[0])
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Call)
                and getattr(n.func.value.func, "id", None) == "_lector"}
    assert lecturas == LECTURAS
