# tests/test_f043_seguimiento_sv3.py
"""F-043 · R27-R33: sv3 marca «terminado» el recalculo que ha hecho.

sv4 escribe en el documento un `recalculo_pedido_id` (uuid4) ANTES de
publicar el recalculo de F-042. sv3 lo lee antes de la pasada y, si la
pasada acaba sin excepcion, lo copia a `recalculo_terminado_id` solo si el
documento sigue con ese pedido (UPDATE condicional). sv4 compara los dos
para saber si el parte sigue «en espera».

Adaptador sobre SQLite en memoria (mismo ORM) y handler con dobles. Ni
red, ni PostgreSQL, ni Sigrid. Datos sinteticos.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest
from sqlalchemy import select, update

from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.recalculo_seguimiento import (
    SqlAlchemyRecalculoSeguimiento,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

DOC = "doc-seg"
PEDIDO_A = "00000000-0000-4000-8000-00000000000a"
PEDIDO_B = "00000000-0000-4000-8000-00000000000b"
AHORA = "2026-10-13T09:00:00+00:00"


def _reloj() -> str:
    return AHORA


@pytest.fixture
def fabrica():
    fab = FabricaSesionSqlite()
    sembrar_lineas(fab, [{"horas": 8.0}], document_id=DOC)
    return fab


def _poner_pedido(fabrica, pedido: str | None,
                  document_id: str = DOC) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc="2026-10-13T08:59:00+00:00"))
        s.commit()


def _marca(fabrica, document_id: str = DOC) -> tuple:
    with fabrica.create_session() as s:
        doc = s.execute(select(ParteDocumentOrm)
                        .where(ParteDocumentOrm.id == document_id)
                        ).scalar_one()
        return (doc.recalculo_pedido_id, doc.recalculo_terminado_id,
                doc.recalculo_terminado_at_utc)


# ============================ adaptador ================================ #

def test_f043_r27_adaptador_lee_el_pedido_actual(fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual(DOC) == PEDIDO_A


def test_f043_r27_adaptador_sin_pedido_es_none(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual(DOC) is None


def test_f043_r27_adaptador_documento_inexistente_es_none(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual("no-existe") is None


def test_f043_r28_adaptador_marca_el_pedido_que_sigue_vigente(
        fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica) == (PEDIDO_A, PEDIDO_A, AHORA)


def test_f043_r32_adaptador_no_marca_si_hay_un_pedido_mas_nuevo(
        fabrica) -> None:
    """sv4 escribio B durante la pasada que leyo A: A no se marca."""
    _poner_pedido(fabrica, PEDIDO_B)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is False
    assert _marca(fabrica) == (PEDIDO_B, None, None)


def test_f043_r32_adaptador_repetir_es_idempotente(fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica) == (PEDIDO_A, PEDIDO_A, AHORA)


def test_f043_r32_adaptador_un_marcado_viejo_no_pisa_el_nuevo(
        fabrica) -> None:
    """Desorden: B ya terminado; un mensaje con A llega tarde y no toca."""
    _poner_pedido(fabrica, PEDIDO_B)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_B) is True
    assert seg.marcar_terminado(DOC, PEDIDO_A) is False
    assert _marca(fabrica) == (PEDIDO_B, PEDIDO_B, AHORA)


def test_f043_r28_adaptador_documento_inexistente_no_marca(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado("no-existe", PEDIDO_A) is False


def test_f043_r28_adaptador_solo_toca_su_documento(fabrica) -> None:
    sembrar_lineas(fabrica, [{"horas": 8.0}], document_id="doc-otro")
    _poner_pedido(fabrica, PEDIDO_A)
    _poner_pedido(fabrica, PEDIDO_A, document_id="doc-otro")
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica, "doc-otro") == (PEDIDO_A, None, None)


def test_f043_r28_adaptador_reloj_por_defecto_es_utc_iso(fabrica) -> None:
    from datetime import datetime, timedelta, timezone

    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica)
    antes = datetime.now(timezone.utc)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    marcado = datetime.fromisoformat(_marca(fabrica)[2])
    assert marcado.utcoffset() == timedelta(0)
    assert antes - timedelta(seconds=5) <= marcado <= antes + timedelta(
        seconds=5)
