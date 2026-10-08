# tests/test_f040_catalogo.py
"""F-040 · R14, R16: el portal ofrece los recursos persona SIN DNI (sv4).

  - R14: `fetch_recursos_activos` ofrece tambien los recursos persona de
    alta sin DNI (ni `res.cif` ni el de la ficha), con `dni` None, y
    loguea cuantos; `_SQL_RECURSOS_ACTIVOS` no cambia.
  - R16: `asignacion_de` de un recurso sin DNI: con ficha, su `ide` y
    `empleado_dni` None; sin ficha, el recurso con `empleado_dni` None y
    `reside` = el recurso (la linea queda `recurso_manual`, ver
    `tests/test_f040_alias.py`).

Sin red: sigrid-api simulado con `httpx.MockTransport`. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

from application.services.recurso_catalog import Asignacion, asignacion_de
from infrastructure.sigrid import sigrid_lookup_client as cliente_mod
from infrastructure.sigrid.sigrid_lookup_client import RecursoOption
from tests.test_f023_catalogo_empresa import SigridFalso, _cliente

COLS = ["ide", "codigo", "nombre", "empresa", "cif", "empleado_ide",
        "empleado_codigo", "empleado_nombre", "empleado_dni", "categoria",
        "candef"]

FILAS = [
    [901, "MO/0001", "Uno Recurso", 1, "00000001R", 11, "E11", "Uno Ficha",
     "00000001R", "Oficial", 8.0],
    # Sin cif ni ficha; dos filas por el JOIN: la segunda completa.
    [904, "MO/0004", "Cuatro Sin Dni", 28, None, None, None, None, None,
     None, None],
    [904, "MO/0004", "Cuatro Sin Dni", 28, None, None, None, None, None,
     "Peon", 7.5],
    # Sin cif y ficha sin DNI (espacios).
    [905, "MO/0005", "Cinco Ficha Sin Dni", 28, "", 15, "E15", "Cinco",
     "  ", "Oficial", None],
]


def _recursos(monkeypatch, filas=FILAS):
    falso = SigridFalso(COLS, filas)
    return _cliente(monkeypatch, falso).fetch_recursos_activos(), falso


def test_f040_r14_se_ofrecen_los_sin_dni_con_dni_none(monkeypatch) -> None:
    recursos, _ = _recursos(monkeypatch)
    por_ide = {r.ide: r for r in recursos}
    assert [r.ide for r in recursos] == [901, 904, 905]
    assert por_ide[904] == RecursoOption(
        ide=904, codigo="MO/0004", nombre="Cuatro Sin Dni", dni=None,
        empresa=28, categoria="Peon", candef=7.5)
    assert por_ide[905] == RecursoOption(
        ide=905, codigo="MO/0005", nombre="Cinco Ficha Sin Dni", dni=None,
        empresa=28, empleado_ide=15, empleado_codigo="E15",
        empleado_nombre="Cinco", empleado_dni=None, categoria="Oficial",
        candef=None)


def test_f040_r14_loguea_cuantos_sin_dni(monkeypatch, caplog) -> None:
    with caplog.at_level(logging.INFO):
        _recursos(monkeypatch)
    (linea,) = [m for m in caplog.messages if "recursos_activos" in m]
    assert "-> 3 recursos (2 sin DNI, ofrecidos marcados)" in linea


def test_f040_r14_sin_ninguno_sin_dni_cuenta_cero(monkeypatch,
                                                  caplog) -> None:
    with caplog.at_level(logging.INFO):
        _recursos(monkeypatch, FILAS[:1])
    (linea,) = [m for m in caplog.messages if "recursos_activos" in m]
    assert "-> 1 recursos (0 sin DNI, ofrecidos marcados)" in linea


def test_f040_r14_el_sql_no_filtra_por_dni() -> None:
    """El DNI lo decide Python; el SQL sigue filtrando solo clase y alta
    (la clase la vigila `tests/test_f036_recurso_persona_gemelos.py`)."""
    sql = " ".join(cliente_mod._SQL_RECURSOS_ACTIVOS.split())
    donde = sql.split(" WHERE ", 1)[1]
    assert donde.startswith("res.cla = 1 AND")
    assert "cif" not in donde and "dni" not in donde.lower()


# ================================ R16 =================================== #

SIN_DNI_SIN_FICHA = RecursoOption(
    ide=904, codigo="MO/0004", nombre="Cuatro Sin Dni", dni=None, empresa=28)
SIN_DNI_CON_FICHA = RecursoOption(
    ide=905, codigo="MO/0005", nombre="Cinco Ficha Sin Dni", dni=None,
    empresa=28, empleado_ide=15, empleado_codigo="E15",
    empleado_nombre="Cinco", empleado_dni=None)


def test_f040_r16_sin_dni_sin_ficha_el_recurso_con_dni_none() -> None:
    assert asignacion_de(SIN_DNI_SIN_FICHA) == Asignacion(
        empleado_ide=None, codigo="MO/0004", nombre="Cuatro Sin Dni",
        dni=None, reside=904)


def test_f040_r16_sin_dni_con_ficha_la_ficha_con_dni_none() -> None:
    assert asignacion_de(SIN_DNI_CON_FICHA) == Asignacion(
        empleado_ide=15, codigo="E15", nombre="Cinco", dni=None, reside=905)
    assert asignacion_de(SIN_DNI_CON_FICHA).como_guardar()["empleado_dni"] \
        is None
