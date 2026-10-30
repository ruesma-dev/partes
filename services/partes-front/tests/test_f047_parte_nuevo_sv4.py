# tests/test_f047_parte_nuevo_sv4.py
"""F-047 · R11-R18: el parte nuevo «en espera» en sv4 (servidor).

sv3 escribe `recalculo_pedido_id` = id del documento al guardar un parte
nuevo. sv4 deduce de ahí el motivo de la espera (`nuevo` o `recalculo`,
R11-R12), lo pinta en las vistas (R13-R14, R18), mantiene el 409 de F-043
(R15) y no aprueba un parte en espera (R16-R17, DA3).

Sin red: repositorio real sobre SQLite, reloj fijo. Datos sintéticos.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, update

from application.services.seguimiento_recalculo import (
    MOTIVO_NUEVO,
    MOTIVO_RECALCULO,
    motivo_espera,
)
from infrastructure.database import parte_repository as modulo_repo
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

AHORA = datetime(2026, 10, 30, 9, 0, 0, tzinfo=timezone.utc)
PID = "00000000-0000-4000-8000-00000000000a"
PID2 = "00000000-0000-4000-8000-00000000000b"


def _hace(segundos: float) -> str:
    return (AHORA - timedelta(seconds=segundos)).isoformat()


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    monkeypatch.setattr(modulo_repo, "_ahora_utc", lambda: AHORA)
    return monkeypatch


@pytest.fixture
def fabrica():
    return FabricaSesionSqlite()


def _poner_marca(fabrica, document_id: str, *, pedido: str | None,
                 pedido_at: str | None, terminado: str | None = None) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc=pedido_at,
                          recalculo_terminado_id=terminado))
        s.commit()


# ================================ R11 ================================== #

def test_f047_r11_constantes_del_motivo() -> None:
    assert (MOTIVO_NUEVO, MOTIVO_RECALCULO) == ("nuevo", "recalculo")


@pytest.mark.parametrize("document_id, pedido_id, esperado", [
    ("doc-1", "doc-1", "nuevo"),
    ("doc-1", PID, "recalculo"),
    ("doc-1", None, "recalculo"),
    ("doc-1", "", "recalculo"),
    ("", "", "recalculo"),
    (None, None, "recalculo"),
])
def test_f047_r11_motivo_espera(document_id, pedido_id, esperado) -> None:
    assert motivo_espera(document_id, pedido_id) == esperado


# ================================ R12 ================================== #

#: (document_id, pedido, segundos desde el pedido, terminado, en papelera)
CASOS_R12 = [
    ("d-nuevo", "d-nuevo", 30, None, False),            # pendiente, nuevo
    ("d-borde", "d-borde", 600, None, False),           # pendiente (borde)
    ("d-recalc", PID2, 30, PID, False),                  # pendiente, recalc.
    ("d-nuevo-term", "d-nuevo-term", 30, "d-nuevo-term", False),
    ("d-nuevo-venc", "d-nuevo-venc", 601, None, False),  # vencido
    ("d-sin", None, None, None, False),                  # sin seguimiento
    ("d-papelera", "d-papelera", 30, None, True),        # en papelera
]
ESPERADO_R12 = {"d-nuevo": "nuevo", "d-borde": "nuevo",
                "d-recalc": "recalculo"}


@pytest.fixture
def siete(entorno, fabrica):
    for i, (doc, pedido, segundos, terminado, papelera) in enumerate(
            CASOS_R12):
        sembrar_parte(fabrica, [{"horas": 8.0}], document_id=doc,
                      empleado_ide=100 + i, doc_en_papelera=papelera)
        _poner_marca(fabrica, doc, pedido=pedido,
                     pedido_at=None if segundos is None else _hace(segundos),
                     terminado=terminado)
    return ParteReviewRepository(fabrica)


def _sentencias(fabrica, funcion) -> tuple:
    sentencias: list[str] = []

    def _anotar(_conn, _cursor, sentencia, *_a):
        sentencias.append(sentencia)

    event.listen(fabrica.engine, "before_cursor_execute", _anotar)
    try:
        resultado = funcion()
    finally:
        event.remove(fabrica.engine, "before_cursor_execute", _anotar)
    return resultado, [s for s in sentencias
                       if s.lstrip().upper().startswith("SELECT")]


def test_f047_r12_motivos_de_los_ids_en_una_consulta(siete,
                                                       fabrica) -> None:
    ids = [c[0] for c in CASOS_R12] + ["no-existe", None, "d-nuevo"]
    motivos, selects = _sentencias(fabrica, lambda: siete.motivos_espera(ids))
    assert motivos == ESPERADO_R12
    assert len(selects) == 1


def test_f047_r12_motivos_de_toda_la_base(siete, fabrica) -> None:
    motivos, selects = _sentencias(fabrica,
                                   lambda: siete.motivos_espera(None))
    assert motivos == ESPERADO_R12
    assert len(selects) == 1
    # Filtrada en la base: activos con pedido distinto del terminado.
    consulta = " ".join(selects[0].split())
    assert "parte_documents.is_active IS 1" in consulta
    assert "parte_documents.recalculo_pedido_id IS NOT NULL" in consulta
    assert ("parte_documents.recalculo_terminado_id IS NULL OR "
            "parte_documents.recalculo_terminado_id != "
            "parte_documents.recalculo_pedido_id") in consulta


@pytest.mark.parametrize("ids", [[], [None, ""], set()])
def test_f047_r12_sin_ids_no_consulta(siete, fabrica, ids) -> None:
    motivos, selects = _sentencias(fabrica, lambda: siete.motivos_espera(ids))
    assert motivos == {}
    assert selects == []


def test_f047_r12_usa_el_reloj_del_repositorio(siete, entorno) -> None:
    entorno.setattr(modulo_repo, "_ahora_utc",
                    lambda: AHORA + timedelta(seconds=1))
    # d-borde pasa de 600 s a 601 s: vencido.
    assert siete.motivos_espera(None) == {"d-nuevo": "nuevo",
                                          "d-recalc": "recalculo"}


def test_f047_r12_acepta_un_generador(siete) -> None:
    assert siete.motivos_espera(c[0] for c in CASOS_R12) == ESPERADO_R12
