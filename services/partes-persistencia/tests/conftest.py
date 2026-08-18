# tests/conftest.py
"""Configuracion de pytest para la suite de persistencia (sv3).

Esta carpeta la inaugura F-003: hasta ahora sv3 no tenia tests y el
portero del arnes lo avisaba en cada arranque ("NADIE esta comprobando
los tests de sv3-persistencia"). Mismo patron que la suite de sv4: el
arnes la ejecuta con `cd services/partes-persistencia && python -m
pytest`, asi que la raiz del servicio ya entra en `sys.path` por el `-m`;
fijarla aqui ademas evita depender del directorio de trabajo.

Ningun test de esta suite toca red ni BBDD real.
"""
from __future__ import annotations

import sys
from pathlib import Path

#: Raiz del servicio: esta carpeta es `<servicio>/tests`.
RAIZ_SERVICIO = Path(__file__).resolve().parents[1]

if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
