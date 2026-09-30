# tests/conftest.py
"""Configuracion de pytest para la suite del poller del buzon (sv1).

El arnes ejecuta esta suite con `cd services/partes-email && python -m
pytest`, asi que el directorio del servicio ya entra en `sys.path` por el
`-m`. Fijarlo aqui ademas evita que la suite dependa del directorio de
trabajo de quien la lance (mismo patron que sv4).

Ningun test de esta suite toca red, Graph, Blob ni colas: los correos se
construyen en el propio test (`eml_sinteticos.py`) y el buzon y el sumidero
son dobles en memoria (`dobles.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

#: Raiz del servicio: esta carpeta es `<servicio>/tests`.
RAIZ_SERVICIO = Path(__file__).resolve().parents[1]

if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
