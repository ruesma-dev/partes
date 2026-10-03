# tests/test_f019_congelado.py
"""F-019 · R15 en sv3: una linea en `dedicacion` esta congelada.

La linea ya se publico en la bandeja de dedicacion: si la reconciliacion
de sv3 (recurso, extras) la recalculase, el portal y lo publicado dirian
cosas distintas. Misma regla que `registrado`; la comparacion con sv4 la
hace el guardian de raiz de F-024.

Funciones puras: sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from application.services.recurso_conciliador import (
    ESTADOS_CONGELADOS,
    esta_congelado,
)


@pytest.mark.parametrize("estado", ["dedicacion", " Dedicacion ",
                                    "DEDICACION"])
def test_f019_r15_sv3_dedicacion_esta_congelada(estado) -> None:
    assert esta_congelado(estado, False) is True


def test_f019_r15_sv3_los_estados_congelados() -> None:
    assert ESTADOS_CONGELADOS == frozenset(
        {"encolado", "registrado", "dedicacion"})


@pytest.mark.parametrize("estado", [None, "", "omitido", "error",
                                    "conflicto", "borrado_sigrid"])
def test_f019_r15_sv3_lo_demas_sigue_libre(estado) -> None:
    assert esta_congelado(estado, False) is False
