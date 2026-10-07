# tests/test_f035_recurso_catalog.py
"""F-035 · R5, R6, R12 y R13 en el catalogo de recursos (`RecursoCatalog`).

  - R5: `list(empresa)` filtra por la empresa del recurso; sin ella, todos.
  - R6: si el refresco falla se sirve la ultima lista buena (vacia si nunca
    cargo) y se registra un WARNING.
  - R12/R13: `asignacion_de` es la UNICA regla de que se escribe en la
    linea al elegir un recurso (con ficha / sin ficha).

Sin red: cliente de Sigrid sustituido por un doble. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

import pytest

from application.services.recurso_catalog import (
    Asignacion,
    RecursoCatalog,
    asignacion_de,
)
from infrastructure.sigrid.sigrid_lookup_client import RecursoOption

CON_FICHA = RecursoOption(
    ide=901, codigo="MO/0001", nombre="Uno Recurso", dni="00000001R",
    empresa=1, empleado_ide=11, empleado_codigo="E11",
    empleado_nombre="Uno Ficha", empleado_dni="1R", categoria="Oficial",
    candef=8.0)
SIN_FICHA = RecursoOption(
    ide=903, codigo="MO/0037", nombre="Tres Solo Recurso", dni="00000003A",
    empresa=28, categoria="Peon", candef=8.0)
FICHA_SIN_DNI = RecursoOption(
    ide=902, codigo="MO/0002", nombre="Dos Recurso", dni="00000002W",
    empresa=28, empleado_ide=12, empleado_codigo="E12",
    empleado_nombre="Dos Ficha", empleado_dni=None)


class ClienteFalso:
    def __init__(self, respuestas) -> None:
        self.respuestas = list(respuestas)
        self.llamadas = 0

    def fetch_recursos_activos(self):
        self.llamadas += 1
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return list(r)


def _catalogo(respuestas, ttl=600) -> tuple[RecursoCatalog, ClienteFalso]:
    cliente = ClienteFalso(respuestas)
    return RecursoCatalog(client=cliente, ttl_seconds=ttl), cliente


# ================================ R5 ==================================== #

def test_f035_r5_filtra_por_empresa_y_sin_ella_todos() -> None:
    cat, cliente = _catalogo([[CON_FICHA, SIN_FICHA, FICHA_SIN_DNI]])
    assert [r.ide for r in cat.list()] == [901, 903, 902]
    assert [r.ide for r in cat.list(28)] == [903, 902]
    assert [r.ide for r in cat.list(1)] == [901]
    assert cat.list(99) == []
    assert cliente.llamadas == 1           # cache con TTL


def test_f035_r5_get_by_ide_y_enabled() -> None:
    cat, _ = _catalogo([[CON_FICHA, SIN_FICHA]])
    assert cat.enabled is True
    assert cat.get_by_ide(903) == SIN_FICHA
    assert cat.get_by_ide("901") == CON_FICHA
    assert cat.get_by_ide(999) is None
    assert cat.get_by_ide(None) is None


def test_f035_r5_sin_cliente_no_hay_recursos() -> None:
    cat = RecursoCatalog(client=None)
    assert cat.enabled is False
    assert cat.list() == [] and cat.list(1) == []
    assert cat.get_by_ide(901) is None


def test_f035_r5_la_lista_devuelta_es_una_copia() -> None:
    cat, _ = _catalogo([[CON_FICHA]])
    cat.list().clear()
    assert len(cat.list()) == 1


# ================================ R6 ==================================== #

def test_f035_r6_fallo_de_refresco_conserva_la_ultima_lista(caplog) -> None:
    cat, cliente = _catalogo([[CON_FICHA], RuntimeError("caida")], ttl=0)
    assert [r.ide for r in cat.list()] == [901]
    with caplog.at_level(logging.WARNING):
        assert [r.ide for r in cat.list()] == [901]
    assert cliente.llamadas == 2
    assert any(rec.levelno == logging.WARNING and "caida" in rec.getMessage()
               for rec in caplog.records)


def test_f035_r6_si_nunca_cargo_lista_vacia_y_reintenta(caplog) -> None:
    cat, cliente = _catalogo([RuntimeError("caida"), [SIN_FICHA]])
    with caplog.at_level(logging.WARNING):
        assert cat.list() == []
    assert any(rec.levelno == logging.WARNING for rec in caplog.records)
    assert [r.ide for r in cat.list()] == [903]   # no quedo «cargado»
    assert cliente.llamadas == 2


# =========================== R12 / R13 ================================== #

def test_f035_r12_con_ficha_se_guarda_la_ficha_y_su_dni() -> None:
    assert asignacion_de(CON_FICHA) == Asignacion(
        empleado_ide=11, codigo="E11", nombre="Uno Ficha", dni="1R",
        reside=901)


def test_f035_r12_ficha_sin_dni_usa_el_del_recurso() -> None:
    assert asignacion_de(FICHA_SIN_DNI) == Asignacion(
        empleado_ide=12, codigo="E12", nombre="Dos Ficha", dni="00000002W",
        reside=902)


def test_f035_r13_sin_ficha_se_guarda_el_recurso() -> None:
    assert asignacion_de(SIN_FICHA) == Asignacion(
        empleado_ide=None, codigo="MO/0037", nombre="Tres Solo Recurso",
        dni="00000003A", reside=903)


@pytest.mark.parametrize("recurso", [CON_FICHA, SIN_FICHA, FICHA_SIN_DNI])
def test_f035_r12_r13_como_dict_para_el_js(recurso) -> None:
    a = asignacion_de(recurso)
    assert a.como_guardar() == {
        "empleado_ide": a.empleado_ide, "empleado_codigo": a.codigo,
        "empleado_nombre": a.nombre, "empleado_dni": a.dni,
        "empleado_reside": a.reside}
