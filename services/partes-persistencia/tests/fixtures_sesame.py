# tests/fixtures_sesame.py
"""Respuestas REALES de sesame-api, para fijar su contrato en los tests.

Copiadas del formato que produce su `interface_adapters/api/app.py`
(repositorio local `sesame-api`, explorado el 2026-08-15): todo va
envuelto en `{"ok": true, ...}`, los 404 son los de FastAPI
(`{"detail": ...}`) y los fallos del upstream salen como 502 con
`{"ok": false, "error": ...}`.

Si sesame-api cambia su contrato, lo que falla son los tests del cliente
(aqui), no el portal en produccion. Ese es justamente el punto.
"""
from __future__ import annotations

#: GET /api/v1/festivos?dni=12345678Z&ano=2026
FESTIVOS_DNI = {
    "ok": True,
    "empleado": "Pepe Perez",
    "ano": 2026,
    "total": 3,
    "data": [
        {"fecha": "2026-01-01", "nombre": "Ano Nuevo",
         "calendario_id": "cal-madrid"},
        {"fecha": "2026-05-15", "nombre": "San Isidro",
         "calendario_id": "cal-madrid"},
        {"fecha": "2027-01-01", "nombre": "Ano Nuevo (del ano siguiente)",
         "calendario_id": "cal-madrid"},
    ],
}

#: GET /api/v1/calendarios-festivos
CALENDARIOS = {
    "ok": True,
    "total": 2,
    "data": [
        {
            "id": "cal-madrid",
            "nombre": "Madrid",
            "por_defecto": False,
            "festivos": [
                {"fecha": "2026-05-15", "nombre": "San Isidro",
                 "calendario_id": "cal-madrid"},
            ],
        },
        {
            "id": "cal-general",
            "nombre": "General",
            "por_defecto": True,
            "festivos": [
                {"fecha": "2026-01-06", "nombre": "Reyes",
                 "calendario_id": "cal-general"},
                {"fecha": "2026-12-25", "nombre": "Navidad",
                 "calendario_id": "cal-general"},
                {"fecha": "2025-12-25", "nombre": "Navidad (ano anterior)",
                 "calendario_id": "cal-general"},
            ],
        },
    ],
}

#: GET /api/v1/jornada?dni=12345678Z
JORNADA = {
    "ok": True,
    "empleado": "Pepe Perez",
    "data": {
        "tipo": "Parcial",
        "reducida": True,
        "tipo_contrato": "Indefinido",
        "contrato_desde": "2020-03-01",
        "contrato_hasta": None,
        "plantilla_horario": "Reducida manana",
    },
}

#: 404 de FastAPI cuando el DNI no existe en Sesame.
NO_ENCONTRADO = {"detail": "empleado con DNI 00000000X no encontrado en Sesame"}

#: 502 del manejador de RuntimeError (Sesame upstream caido).
UPSTREAM_KO = {"ok": False, "error": "Sesame respondio 429 tras 3 reintentos"}
