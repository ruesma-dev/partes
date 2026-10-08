# tests/test_f040_caracterizacion.py
"""F-040 · R13: lo que proponer por nombre a los recursos sin DNI NO cambia.

Tests de CARACTERIZACION: se escribieron y pasaron contra el codigo de
antes de F-040 y deben seguir pasando despues, sin tocarlos.

  - R13: una linea congelada (en Sigrid, aprobada o en dedicacion) no
    re-resuelve su recurso, tampoco cuando es una linea SIN DNI y sin ficha
    cuyo recurso preferido es un recurso persona sin DNI (justo el caso que
    F-040 empieza a resolver en las lineas libres, R10).
  - `esta_congelado` y `ESTADOS_CONGELADOS` dan lo mismo que hoy (sus
    gemelos de sv4 los vigila `tests/test_f024_borrado_no_congela_gemelos.py`
    de la raiz).

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
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import ObraRow
from tests.dobles import (
    LookupFake,
    RepositorioFake,
    recurso_persona,
    registro,
    reshor_par,
)

FECHA = 20260915
EMPRESA = 28
SIN_DNI = recurso_persona(ide=950, cif=None, conide=None, empresa=EMPRESA,
                          fecbaj=0, codigo="MO/9950", nombre="SIN DNI UNO")
OTRO_SIN_DNI = recurso_persona(ide=951, cif="", conide=None, empresa=EMPRESA,
                               fecbaj=0, codigo="MO/9951",
                               nombre="SIN DNI DOS")
OBRAS = [ObraRow(ide=10, codigo="0010", nombre="Obra", empresa=EMPRESA)]


def _indice() -> IndicePersonas:
    return IndicePersonas([], [SIN_DNI, OTRO_SIN_DNI], OBRAS)


def _sin_dni(rid: int, *, recurso: int | None, **congelacion) -> dict:
    """Linea sin DNI ni ficha cuyo preferido es el recurso sin DNI 950."""
    r = registro(rid, fecha_int=FECHA, horas=8.0, dni=None, **congelacion)
    r.update(empleado_ide=None, empleado_reside=950, recurso_ide=recurso)
    return r


def _conciliar(registros):
    repo = RepositorioFake(registros)
    RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(950) + reshor_par(951)),
        indice_provider=_indice,
        hoy=lambda: date(2026, 9, 15),
    ).conciliar_todos()
    return repo


@pytest.mark.parametrize("congelacion", [
    {"sigrid_estado": "registrado"},
    {"sigrid_estado": "encolado"},
    {"sigrid_estado": "dedicacion"},
    {"doc_approved": True},
])
@pytest.mark.parametrize("recurso", [None, 951])
def test_f040_r13_congelada_sin_dni_no_se_re_resuelve(congelacion,
                                                      recurso) -> None:
    """Ni gana el recurso sin DNI (None) ni cambia el que tenia (951)."""
    repo = _conciliar([_sin_dni(1, recurso=recurso, **congelacion)])
    assert repo.matches == []
    assert repo.review_required == []


def test_f040_r13_estados_congelados_igual_que_antes() -> None:
    assert ESTADOS_CONGELADOS == frozenset(
        {"encolado", "registrado", "dedicacion"})


@pytest.mark.parametrize("estado, aprobado, esperado", [
    (None, False, False), ("", False, False), ("error", False, False),
    ("borrado", False, False), ("pendiente", False, False),
    ("encolado", False, True), (" Registrado ", False, True),
    ("dedicacion", False, True), (None, True, True), ("error", 1, True),
])
def test_f040_r13_esta_congelado_igual_que_antes(estado, aprobado,
                                                 esperado) -> None:
    assert esta_congelado(estado, aprobado) is esperado
