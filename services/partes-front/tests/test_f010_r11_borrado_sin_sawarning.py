# tests/test_f010_r11_borrado_sin_sawarning.py
"""Borrar de la papelera no emite avisos de SQLAlchemy (F-010 R11).

Desde F-004, `hard_delete_document` y `vaciar_papelera` empiezan mirando
si el parte tiene alguna linea REGISTRADA en Sigrid
(`_tiene_linea_registrada`), lo que carga `doc.registros` en la sesion.
Despues borraban las lineas con un `DELETE` masivo en SQL y borraban el
documento; al hacer commit, la cascada `all, delete-orphan` intentaba
borrar otra vez unos objetos que ya no estaban en la tabla y SQLAlchemy
avisaba:

    SAWarning: DELETE statement on table 'parte_registros' expected to
    delete 1 row(s); 0 were matched.

El aviso no rompia nada, pero es el sintoma de que se estaba borrando dos
veces: si algun dia el conteo importara (o el aviso pasara a error, como
en estos tests), el borrado fallaria. Se quita el `DELETE` masivo y se
deja que borre la cascada del ORM, que es quien conoce las lineas.

Aqui los `SAWarning` son ERRORES: un test que solo mirase el resultado
final seguiria pasando con el aviso puesto, que es como llevaba meses.
"""

from __future__ import annotations

import warnings

import pytest
from dobles import FabricaSesionSqlite, sembrar_parte
from infrastructure.database.orm_models import ParteDocumentOrm, ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from sqlalchemy import select
from sqlalchemy.exc import SAWarning


@pytest.fixture()
def sin_avisos():
    """Convierte cualquier `SAWarning` en excepcion mientras dure el test."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", SAWarning)
        yield


def _contar(fabrica: FabricaSesionSqlite) -> tuple[int, int]:
    with fabrica.create_session() as s:
        docs = len(s.execute(select(ParteDocumentOrm)).scalars().all())
        regs = len(s.execute(select(ParteRegistroOrm)).scalars().all())
    return docs, regs


def test_f010_r11_hard_delete_no_emite_sawarning(sin_avisos) -> None:
    """El documento y sus lineas se van; sin avisos y sin doble borrado."""
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 2.0, "tipo": "extra"}],
                  document_id="doc-r11", doc_en_papelera=True)
    repo = ParteReviewRepository(fabrica)

    assert repo.hard_delete_document(document_id="doc-r11") is True

    assert _contar(fabrica) == (0, 0)


def test_f010_r11_vaciar_papelera_no_emite_sawarning(sin_avisos) -> None:
    """Igual por la via masiva, que es la que mas filas toca."""
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 4.0}],
                  document_id="doc-papelera-1", doc_en_papelera=True)
    sembrar_parte(fabrica, [{"horas": 8.0}],
                  document_id="doc-papelera-2", doc_en_papelera=True)
    repo = ParteReviewRepository(fabrica)

    resultado = repo.vaciar_papelera()

    assert resultado["documentos"] == 2
    assert resultado["omitidos"] == 0
    assert _contar(fabrica) == (0, 0)


def test_f010_r11_vaciar_papelera_con_lineas_sueltas_no_emite_sawarning(
    sin_avisos,
) -> None:
    """Un parte VIVO con lineas en papelera: se van las lineas, no el parte."""
    fabrica = FabricaSesionSqlite()
    sembrar_parte(
        fabrica,
        [{"horas": 8.0}, {"horas": 4.0, "borrada": True}],
        document_id="doc-vivo",
    )
    repo = ParteReviewRepository(fabrica)

    resultado = repo.vaciar_papelera()

    assert resultado == {"documentos": 0, "registros": 1, "omitidos": 0}
    assert _contar(fabrica) == (1, 1)


def test_f010_r11_lo_congelado_se_sigue_omitiendo_sin_avisos(sin_avisos) -> None:
    """La proteccion de F-004 R12 no se toca: lo registrado en Sigrid queda.

    Es el caso que mezcla las dos cosas —un parte que se borra y otro que
    se omite en la misma pasada—, que es donde un borrado a medias haria
    mas dano.
    """
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0, "estado": "registrado"}],
                  document_id="doc-en-sigrid", doc_en_papelera=True)
    sembrar_parte(fabrica, [{"horas": 8.0}],
                  document_id="doc-libre", doc_en_papelera=True)
    repo = ParteReviewRepository(fabrica)

    resultado = repo.vaciar_papelera()

    assert resultado["documentos"] == 1
    assert resultado["omitidos"] == 1
    # Queda el parte con linea registrada, con su linea.
    assert _contar(fabrica) == (1, 1)
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "doc-en-sigrid") is not None
