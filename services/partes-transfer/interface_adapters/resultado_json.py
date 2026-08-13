# interface_adapters/resultado_json.py
"""Serializacion del ResultadoRegistro al JSON publico de sv5.

Fuente UNICA del contrato: lo usan el endpoint HTTP
`POST /api/registro/ejecutar` y el consumidor de `q-transfer`, que publica
exactamente el mismo JSON en `q-transfer-result`. Tenerlo en un solo sitio
es lo que impide que los dos canales se separen con el tiempo.
"""
from __future__ import annotations

from dataclasses import asdict

from domain.models.registro_models import ResultadoRegistro


def resultado_a_dict(r: ResultadoRegistro) -> dict:
    return {
        "ok": r.ok,
        "obra_destino": asdict(r.obra_destino),
        "forzada_pruebas": r.forzada_pruebas,
        "partes": [asdict(x) for x in r.partes],
        "escritas": r.escritas,
        "omitidas": r.omitidas,
        "ya_registradas": r.ya_registradas,
        "pisadas": r.pisadas,
        "borradas": r.borradas,
        "pendientes_confirmacion": [asdict(c)
                                    for c in r.pendientes_confirmacion],
    }
