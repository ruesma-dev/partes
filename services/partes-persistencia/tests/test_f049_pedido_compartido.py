# tests/test_f049_pedido_compartido.py
"""F-049 · R41-R42: sv3 marca «terminado» TODO documento con el pedido.

Desde F-049 (DA13-C), sv4 escribe UN pedido compartido en los partes que
toca y en los de otras obras del mismo (recurso, día) y publica UN mensaje
con el primero. La pasada de sv3 es completa, así que al acabar basta con
copiar el pedido a «terminado» en todo documento que lo lleve
(`SqlAlchemyRecalculoSeguimiento.marcar_terminado`, misma firma). Los
pedidos de un solo documento (F-042/F-043) y el de F-047 (pedido = id del
parte) se marcan como hoy; un pedido viejo nunca marca un documento con
otro (F-043 R32). Adaptador real sobre SQLite en memoria. Datos sintéticos.
"""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import select, update

from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.recalculo_seguimiento import (
    SqlAlchemyRecalculoSeguimiento,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

P = "00000000-0000-4000-8000-0000000000f1"
Q = "00000000-0000-4000-8000-0000000000f2"
AHORA = "2026-10-21T09:00:00+00:00"
DOCS = ("d-y", "d-x", "d-z")


@pytest.fixture
def fabrica():
    fab = FabricaSesionSqlite()
    for doc in DOCS:
        sembrar_lineas(fab, [{"horas": 8.0}], document_id=doc)
    return fab


def _seg(fabrica) -> SqlAlchemyRecalculoSeguimiento:
    return SqlAlchemyRecalculoSeguimiento(fabrica, reloj=lambda: AHORA)


def _pedido(fabrica, doc: str, pedido: str | None) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == doc)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc="2026-10-21T08:59:00Z"))
        s.commit()


def _marcas(fabrica) -> dict[str, tuple]:
    with fabrica.create_session() as s:
        return {d.id: (d.recalculo_pedido_id, d.recalculo_terminado_id,
                       d.recalculo_terminado_at_utc)
                for d in s.execute(select(ParteDocumentOrm)).scalars()}


def test_f049_r41_el_pedido_compartido_marca_y_y_x(fabrica):
    _pedido(fabrica, "d-y", P)
    _pedido(fabrica, "d-x", P)
    assert _seg(fabrica).marcar_terminado("d-y", P) is True
    assert _marcas(fabrica) == {"d-y": (P, P, AHORA), "d-x": (P, P, AHORA),
                                "d-z": (None, None, None)}


def test_f049_r41_e12d_otro_pedido_en_x_no_se_marca(fabrica):
    """X recibió Q antes de que sv3 leyera P: P marca Y; X espera a Q."""
    _pedido(fabrica, "d-y", P)
    _pedido(fabrica, "d-x", Q)
    assert _seg(fabrica).marcar_terminado("d-y", P) is True
    assert _marcas(fabrica)["d-x"] == (Q, None, None)
    assert _marcas(fabrica)["d-y"] == (P, P, AHORA)


def test_f049_r41_el_documento_del_mensaje_ya_no_lo_lleva(fabrica):
    """Y ya tiene un pedido posterior; X, aún P: se marca X y no Y."""
    _pedido(fabrica, "d-y", Q)
    _pedido(fabrica, "d-x", P)
    assert _seg(fabrica).marcar_terminado("d-y", P) is True
    assert _marcas(fabrica) == {"d-y": (Q, None, None), "d-x": (P, P, AHORA),
                                "d-z": (None, None, None)}


def test_f049_r41_sin_pedido_u_otro_no_marca_nada(fabrica):
    _pedido(fabrica, "d-y", Q)
    assert _seg(fabrica).marcar_terminado("d-y", P) is False
    assert _seg(fabrica).marcar_terminado("d-z", P) is False
    assert all(m[1] is None for m in _marcas(fabrica).values())


def test_f049_r42_pedido_de_f047_solo_marca_su_parte(fabrica):
    """F-047: el pedido es el id del propio parte; nunca coincide con el
    de otro documento."""
    _pedido(fabrica, "d-y", "d-y")
    _pedido(fabrica, "d-x", "d-x")
    assert _seg(fabrica).marcar_terminado("d-y", "d-y") is True
    assert _marcas(fabrica)["d-y"] == ("d-y", "d-y", AHORA)
    assert _marcas(fabrica)["d-x"] == ("d-x", None, None)


def test_f049_r42_pedido_de_un_solo_documento_como_hoy(fabrica):
    _pedido(fabrica, "d-z", P)
    assert _seg(fabrica).marcar_terminado("d-z", P) is True
    assert _marcas(fabrica)["d-z"] == (P, P, AHORA)
    assert _marcas(fabrica)["d-y"] == (None, None, None)


def test_f049_r42_repetir_es_idempotente(fabrica):
    _pedido(fabrica, "d-y", P)
    _pedido(fabrica, "d-x", P)
    seg = _seg(fabrica)
    assert seg.marcar_terminado("d-y", P) is True
    assert seg.marcar_terminado("d-x", P) is True
    assert _marcas(fabrica)["d-x"] == (P, P, AHORA)


def test_f049_r42_misma_firma(fabrica):
    firma = inspect.signature(SqlAlchemyRecalculoSeguimiento.marcar_terminado)
    assert list(firma.parameters) == ["self", "document_id", "peticion_id"]
    assert firma.return_annotation in (bool, "bool")
