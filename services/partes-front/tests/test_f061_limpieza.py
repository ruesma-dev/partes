# tests/test_f061_limpieza.py
"""F-061 · reglas puras del parte vacío y limpieza de los existentes.

- Funciones puras de `application/services/parte_vacio.py` (design §4.1).
- R14–R18: el script `limpiar_partes_vacios.py` y los métodos del
  repositorio que usa (`partes_vacios_activos`, `limpiar_vacios`).

Ni red ni PostgreSQL: SQLite en memoria con el ORM real. Datos
sintéticos.
"""
from __future__ import annotations

import json

import pytest

from application.services.parte_vacio import (
    MARCA_RETIRADO,
    MOTIVO_DUPLICADO_ACTIVO,
    PARTES_SIGRID_PROTEGIDOS,
    DuplicadoActivoError,
    categoria_vacio,
    empleados_leidos,
    es_retirado,
    marca_retirado,
    motivo_exclusion_limpieza,
)
from application.services.congelacion import CongeladoError


# ========================= Funciones puras ============================ #

def test_f061_marca_retirado() -> None:
    assert MARCA_RETIRADO == "sin-lineas"
    assert marca_retirado(None) == "sin-lineas"
    assert marca_retirado("") == "sin-lineas"
    assert marca_retirado("ana") == "sin-lineas · ana"
    largo = marca_retirado("x" * 400)
    assert len(largo) == 255
    assert largo.startswith("sin-lineas · x")


@pytest.mark.parametrize("activo,borrado,por,esperado", [
    (False, None, "sin-lineas", True),
    (False, None, "sin-lineas · ana", True),
    (False, None, None, False),            # reemplazo de sv3 (DA7)
    (False, None, "ana", False),
    (False, "2026-10-26T00:00:00", "sin-lineas", False),   # papelera
    (True, None, "sin-lineas", False),
])
def test_f061_es_retirado(activo, borrado, por, esperado) -> None:
    assert es_retirado(is_active=activo, deleted_at_utc=borrado,
                       deleted_by=por) is esperado


def test_f061_partes_sigrid_protegidos_lista_cerrada() -> None:
    assert PARTES_SIGRID_PROTEGIDOS == frozenset(
        {"PT26/00373", "PT26/00375", "PT26/00376"})


def test_f061_duplicado_activo_error() -> None:
    error = DuplicadoActivoError()
    assert error.motivo == MOTIVO_DUPLICADO_ACTIVO
    assert str(error) == MOTIVO_DUPLICADO_ACTIVO
    assert not isinstance(error, CongeladoError)
    assert "elimínalo de la papelera" in MOTIVO_DUPLICADO_ACTIVO


@pytest.mark.parametrize("aprobado,estados,partes,esperado", [
    (False, [], [], None),
    (False, [None, "omitido", "error", "borrado_sigrid"], [None], None),
    (True, [], [], "aprobado"),
    (True, ["registrado"], ["PT26/00373"], "aprobado"),     # orden
    (False, ["registrado"], [], "vive_fuera"),
    (False, [" Dedicacion "], [], "vive_fuera"),
    (False, ["encolado"], [], "vive_fuera"),
    (False, ["ENCOLADO "], [], "vive_fuera"),
    (False, ["registrado"], ["PT26/00375"], "vive_fuera"),  # orden
    (False, [None], ["PT26/00376"], "protegido"),
    (False, [None], ["PT26/00374"], None),
])
def test_f061_motivo_exclusion_limpieza(aprobado, estados, partes,
                                        esperado) -> None:
    assert motivo_exclusion_limpieza(
        aprobado=aprobado, estados=estados, partes_sigrid=partes) == esperado


@pytest.mark.parametrize("filas,manual,leidos,esperado", [
    (3, False, 0, "todas_en_papelera"),
    (1, True, 5, "todas_en_papelera"),
    (0, True, 0, "sin_filas_manual"),
    (0, True, 4, "sin_filas_manual"),
    (0, False, 2, "sin_filas_leidos"),
    (0, False, 0, "sin_filas_nada_leido"),
])
def test_f061_r15_categoria_vacio(filas, manual, leidos, esperado) -> None:
    assert categoria_vacio(filas=filas, manual=manual,
                           empleados_leidos=leidos) == esperado


@pytest.mark.parametrize("raw,esperado", [
    (json.dumps({"data": {"empleados": [{}, {}, {}]}}), 3),
    (json.dumps({"data": {"empleados": []}}), 0),
    (json.dumps({"data": {"empleados": "no es lista"}}), 0),
    (json.dumps({"data": None}), 0),
    (json.dumps({"otra": 1}), 0),
    (json.dumps([1, 2]), 0),
    ("{no es json", 0),
    ("", 0),
    (None, 0),
])
def test_f061_empleados_leidos(raw, esperado) -> None:
    assert empleados_leidos(raw) == esperado
