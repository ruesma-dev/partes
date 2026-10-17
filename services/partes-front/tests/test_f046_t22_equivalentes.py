# tests/test_f046_t22_equivalentes.py
"""F-046 T22 · demostracion ejecutable de los mutantes EQUIVALENTES de sv4
(`progress/mutacion_F-046.md`, seccion «Equivalentes»; pendientes de que
el humano los acepte).

Cada test fija la razon por la que la linea mutada no puede cambiar nada
observable: pasa con el original y con el mutante, por construccion. Si un
cambio futuro rompiera esa razon, el test lo diria. Datos SINTETICOS.
"""
from __future__ import annotations

import ast
import inspect
import textwrap

from application.services.reparto_aviso import (
    DECISION_APLICAR,
    ESTADOS_BLOQUEAN,
    excluidas_por_reparto,
)
from interface_adapters.web import app as modulo_app


def _funcion(nombre: str) -> ast.FunctionDef:
    arbol = ast.parse(textwrap.dedent(inspect.getsource(
        modulo_app.build_app)))
    (f,) = [n for n in ast.walk(arbol)
            if isinstance(n, ast.FunctionDef) and n.name == nombre]
    return f


# ---------- web/app.py:2379 (`{"ok": False, ...}` -> `True` al fallar) ---------- #

def test_f046_t22_eq_veredictos_reparto_no_lee_ok_de_la_respuesta():
    """`_veredictos_reparto` decide SOLO por `veredictos` y `error` de la
    respuesta de sv5: la clave `ok` del dict que fabrica al fallar no se
    lee nunca, asi que su valor no cambia nada."""
    f = _funcion("_veredictos_reparto")
    claves = {ast.literal_eval(n.args[0]) for n in ast.walk(f)
              if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute)
              and n.func.attr == "get"
              and isinstance(n.func.value, ast.Name)
              and n.func.value.id == "r"}
    assert claves == {"veredictos", "error"}
    assert not [n for n in ast.walk(f)
                if isinstance(n, ast.Subscript)
                and isinstance(n.value, ast.Name) and n.value.id == "r"]


# ------- web/app.py:2500 (`_aplicados`: `decision == aplicar` -> `!=`) ------- #

def test_f046_t22_eq_un_reparto_aplicado_no_excluye_con_o_sin_decision():
    """`_aplicados` solo devuelve repartos en estado `aplicado`, y ese
    estado no esta en `ESTADOS_BLOQUEAN`: sus lineas viajan con decision o
    sin ella. Ademas `aplicado` solo sale de «Aplicar» («Mantener» deja
    `rechazado`), asi que la mutacion (conjunto vacio) y el original dan
    las mismas exclusiones."""
    assert "aplicado" not in ESTADOS_BLOQUEAN
    fila = [{"id": 7, "estado": "aplicado", "registro_ids": [70, 71]}]
    assert excluidas_por_reparto(fila, {}) == {}
    assert excluidas_por_reparto(fila, {7: DECISION_APLICAR}) == {}
