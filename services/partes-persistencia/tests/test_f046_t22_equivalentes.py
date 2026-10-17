# tests/test_f046_t22_equivalentes.py
"""F-046 T22 · demostracion ejecutable de los mutantes EQUIVALENTES de sv3
(`progress/mutacion_F-046.md`, seccion «Equivalentes»; pendientes de que
el humano los acepte).

Cada test fija la razon por la que la linea mutada no puede cambiar nada
observable: pasa con el original y con el mutante, por construccion. Si un
cambio futuro rompiera esa razon, el test lo diria. Datos SINTETICOS.
"""
from __future__ import annotations

import ast
import inspect
import random
import textwrap

from application.services import recurso_conciliador
from application.services.reparto_ponderado import _EPS
from tests.dobles import RepositorioFake
from tests.test_f046_conciliar import _conciliador


# --- recurso_conciliador.py:468 y :553 (valores iniciales de los contadores) --- #

def _pasada() -> tuple[ast.AST, set[int]]:
    """El AST de `_pasada` y los nodos que cuelgan de un
    `if self._reajuste:`."""
    arbol = ast.parse(textwrap.dedent(inspect.getsource(
        recurso_conciliador.RecursoConciliador._pasada)))
    dentro: set[int] = set()
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.If)
                and ast.unparse(nodo.test) == "self._reajuste"):
            dentro.update(id(hijo) for hijo in ast.walk(nodo))
    return arbol, dentro


def _asignaciones(nombre: str) -> list[bool]:
    """Por cada asignacion a `nombre`: si esta dentro del interruptor."""
    arbol, dentro = _pasada()
    return [id(n) in dentro for n in ast.walk(arbol)
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == nombre
                    for t in n.targets)]


def _lecturas_fuera_del_if(nombre: str) -> int:
    arbol, dentro = _pasada()
    return sum(1 for n in ast.walk(arbol)
               if isinstance(n, ast.Name) and n.id == nombre
               and isinstance(n.ctx, ast.Load) and id(n) not in dentro)


def test_f046_t22_eq_contadores_iniciales_son_almacenes_muertos():
    """`materializacion` y `guardado` se inicializan una vez FUERA del
    interruptor, se reasignan DENTRO de `if self._reajuste:` y solo se
    leen dentro de otro `if self._reajuste:`. Con el interruptor apagado
    no se leen; encendido, se leen ya reasignados: el valor inicial
    (0 o 1) no llega nunca al resultado."""
    for nombre in ("materializacion", "guardado"):
        assert _asignaciones(nombre) == [False, True], nombre
        assert _lecturas_fuera_del_if(nombre) == 0, nombre


def test_f046_t22_eq_apagado_no_hay_contadores_del_reajuste():
    res = _conciliador(RepositorioFake([]), reajuste=False).conciliar_todos()
    assert not [k for k in res if k.startswith("repartos_")
                and k != "repartos_con_congeladas"]


# ------------ reparto_ponderado.py:364 (`abs(extra) > _EPS` -> `>=`) ------------ #

def test_f046_t22_eq_una_extra_redondeada_a_centesimas_nunca_vale_eps():
    """`extra = round(trabajado - despues, 2)`: su valor absoluto es 0 o
    >= 0,01, nunca exactamente `_EPS` (1e-9), asi que `> _EPS` y
    `>= _EPS` dan lo mismo. Barrido de 200.000 diferencias, incluidas las
    que caen a menos de 1e-8 de 0."""
    azar = random.Random(20261017)
    muestras = [azar.uniform(-24.0, 24.0) for _ in range(100_000)]
    muestras += [azar.uniform(-1e-8, 1e-8) for _ in range(100_000)]
    muestras += [0.0, -0.0, _EPS, -_EPS, 0.005, -0.005, 0.004999999]
    for x in muestras:
        extra = round(x, 2)
        assert (abs(extra) > _EPS) == (abs(extra) >= _EPS), x
