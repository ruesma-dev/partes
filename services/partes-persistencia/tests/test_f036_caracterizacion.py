# tests/test_f036_caracterizacion.py
"""F-036 · R20, R21: lo que el casado contra recursos NO cambia.

Tests de CARACTERIZACION: se escribieron y pasaron contra el codigo de
antes de F-036 y deben seguir pasando despues, sin tocarlos.

  - R20: `de_alta`, `esta_congelado` y `ESTADOS_CONGELADOS` dan lo mismo
    que hoy (los guardianes de la raiz, `tests/test_f023_de_alta_gemelos.py`
    y `tests/test_f024_borrado_no_congela_gemelos.py`, vigilan ademas que
    sus gemelos de sv4/sv5 coincidan).
  - R21: una linea congelada no re-resuelve su recurso (F-023 R30), ni
    siquiera cuando su recurso ya no esta en el maestro de personas.

Todo SINTETICO.
"""
from __future__ import annotations

from datetime import date

import pytest

from application.services.recurso_conciliador import (
    ESTADOS_CONGELADOS,
    RecursoConciliador,
    esta_congelado,
)
from application.services.seleccion_sigrid import IndicePersonas, de_alta
from tests.dobles import LookupFake, RepositorioFake, registro, reshor_par

FECHA = 20260915


# ============================== R20 =================================== #

@pytest.mark.parametrize("fecbaj, esperado", [
    (None, True), (0, True), (FECHA + 1, True), (FECHA, False),
    (FECHA - 1, False), (20210126, False),
])
def test_f036_r20_de_alta_igual_que_antes(fecbaj, esperado) -> None:
    assert de_alta(fecbaj, FECHA) is esperado


def test_f036_r20_estados_congelados_igual_que_antes() -> None:
    assert ESTADOS_CONGELADOS == frozenset(
        {"encolado", "registrado", "dedicacion"})


@pytest.mark.parametrize("estado, aprobado, esperado", [
    (None, False, False), ("", False, False), ("error", False, False),
    ("borrado", False, False), ("pendiente", False, False),
    ("encolado", False, True), (" Registrado ", False, True),
    ("dedicacion", False, True), (None, True, True), ("error", 1, True),
])
def test_f036_r20_esta_congelado_igual_que_antes(estado, aprobado,
                                                 esperado) -> None:
    assert esta_congelado(estado, aprobado) is esperado


# ============================== R21 =================================== #

def _conciliar(registros, indice: IndicePersonas):
    repo = RepositorioFake(registros)
    RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(777)),
        indice_provider=lambda: indice,
        hoy=lambda: date(2026, 9, 15),
    ).conciliar_todos()
    return repo


def test_f036_r21_congelada_no_se_re_resuelve_aunque_su_recurso_no_exista(
) -> None:
    """El recurso guardado (999) no esta en el maestro: una linea libre lo
    perderia; la congelada no se toca."""
    registrada = registro(1, fecha_int=FECHA, horas=8.0,
                          sigrid_estado="registrado", obra_ide=None)
    registrada["recurso_ide"] = 999
    aprobada = registro(2, fecha_int=FECHA, horas=8.0, doc_approved=True,
                        obra_ide=None)
    aprobada["recurso_ide"] = 999
    dedicacion = registro(3, fecha_int=FECHA, horas=8.0,
                          sigrid_estado="dedicacion", obra_ide=None)
    libre = registro(4, fecha_int=FECHA, horas=8.0, obra_ide=None)
    libre["recurso_ide"] = 999
    repo = _conciliar([registrada, aprobada, dedicacion, libre],
                      IndicePersonas([], []))
    assert [u["registro_id"] for u in repo.matches] == [4]
    assert repo.matches[0]["recurso_ide"] is None
