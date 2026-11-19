# tests/test_f032_logs_sin_dni.py
"""F-032 · R3: la configuracion de logging de sv4 deja `httpx` en WARNING.

Con F-032 sv4 llamaba a `GET /api/v1/jornada?dni=…` de la pasarela; F-077
la retira (sv4 ya no llama a Sesame, R20) y con ella los casos del cliente
y de `jornada_contrato`. Queda la garantia de la configuracion REAL: httpx
escribe en INFO la URL completa con su query, asi que sv4 solo deja pasar
sus WARNING.
"""
from __future__ import annotations

import logging

import pytest

from config.logging_config import configure_logging


@pytest.fixture
def logging_real(tmp_path):
    """`configure_logging` de sv4 en INFO; deja el logging como estaba."""
    raiz = logging.getLogger()
    antes = (list(raiz.handlers), raiz.level,
             logging.getLogger("httpx").level,
             logging.getLogger("httpcore").level)
    configure_logging(tmp_path, "INFO")
    yield
    for h in list(raiz.handlers):
        raiz.removeHandler(h)
        if h not in antes[0]:
            h.close()
    for h in antes[0]:
        raiz.addHandler(h)
    raiz.setLevel(antes[1])
    logging.getLogger("httpx").setLevel(antes[2])
    logging.getLogger("httpcore").setLevel(antes[3])


def test_f032_r3_la_configuracion_de_sv4_silencia_httpx(logging_real) -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
