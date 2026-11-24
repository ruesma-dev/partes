# tests/test_f072_obras_agrupadas_copia.py
"""F-072 · R11: los tests del gemelo `obras_agrupadas.py` contra la copia de
ESTE servicio.

Los tests de las reglas están escritos una vez, en
`services/partes-persistencia/tests/test_f072_obras_agrupadas.py`. Aquí se
cargan por ruta y se ejecutan en la suite de este servicio, así que su
`from application.services.obras_agrupadas import …` resuelve a la copia de
este servicio. El guardián de raíz comprueba que las copias son
byte-idénticas; esto comprueba, además, que cada copia pasa los mismos
tests. Fichero idéntico en sv2, sv4 y sv5.

Si el servicio no tiene `partida_catalog`, el único test que lo usa se
salta: el árbol de partidas se prueba en sv3.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_FUENTE = (Path(__file__).resolve().parents[2] / "partes-persistencia"
           / "tests" / "test_f072_obras_agrupadas.py")
_CATALOGO = "application.services.partida_catalog"


def _sin_catalogo(_filas):
    pytest.skip("este servicio no tiene partida_catalog: se prueba en sv3")


def _cargar() -> ModuleType:
    provisional = None
    try:
        importlib.import_module(_CATALOGO)
    except ImportError:
        provisional = ModuleType(_CATALOGO)
        provisional.build_arbol_partidas = _sin_catalogo
        sys.modules[_CATALOGO] = provisional
    try:
        spec = importlib.util.spec_from_file_location(
            "f072_tests_del_gemelo", _FUENTE)
        assert spec is not None and spec.loader is not None, _FUENTE
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    finally:
        if provisional is not None:
            sys.modules.pop(_CATALOGO, None)
    return modulo


_TESTS = _cargar()
globals().update({nombre: getattr(_TESTS, nombre) for nombre in dir(_TESTS)
                  if nombre.startswith("test_")})


def test_f072_r11_se_prueba_la_copia_de_este_servicio():
    """El módulo que usan los tests es el de este servicio, no el de sv3."""
    propio = Path(__file__).resolve().parents[1]
    usado = Path(sys.modules["application.services.obras_agrupadas"].__file__)
    assert usado.resolve().is_relative_to(propio)
