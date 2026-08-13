# tests/conftest.py
"""Configuración de pytest para la suite de la raíz del monorepo.

Los tests de esta carpeta comprueban el repositorio *como conjunto*, así que
importan las herramientas del arnés (`harness.servicios`). Para que ese
import funcione, la raíz del repositorio tiene que estar en `sys.path`.

Pytest la añade sola cuando se lanza desde la raíz y no hay paquete que lo
impida, pero eso depende del directorio de trabajo de quien ejecute la suite.
Fijarlo aquí cuesta cuatro líneas y evita el fallo más caro de diagnosticar:
un `ModuleNotFoundError: harness` que solo aparece en la máquina de otro.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: Raíz del repositorio: esta carpeta es `<raíz>/tests`.
RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
