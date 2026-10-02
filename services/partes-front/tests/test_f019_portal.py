# tests/test_f019_portal.py
"""F-019 · la linea en dedicacion en el portal (R15-R24).

T5: `dedicacion` congela como `registrado` (R15) y no se borra
definitivamente (R16). T8: no viaja a sv5 al aprobar (R17) y el listado
del modal la ensena «a dedicacion» (R18). T9: «Retirar de dedicacion»
(R21-R24). T10: las vistas (R19) y «Marcar pendiente» (R20).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM, `TestClient` y
los dobles de sv5, publisher y calendario de F-022. Personas, obras y
partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADO_DEDICACION,
    MOTIVO_DOC_APROBADO,
    MOTIVO_DOC_DEDICACION,
    MOTIVO_DOC_ENCOLADO,
    MOTIVO_DOC_REGISTRADO,
    MOTIVO_HARD_DELETE_DEDICACION,
    MOTIVO_HARD_DELETE_REGISTRADO,
    MOTIVO_LINEA_DEDICACION,
    MOTIVO_LINEA_ENCOLADA,
    MOTIVO_LINEA_REGISTRADA,
    CongeladoError,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
    vive_fuera,
)
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import sembrar


# ========================== T5 · R15 · la congelacion ========================== #

@pytest.mark.parametrize("estado", ["dedicacion", " Dedicacion ",
                                    "DEDICACION"])
def test_f019_r15_dedicacion_congela_la_linea(estado) -> None:
    for aprobado in (False, True):
        assert motivo_congelacion_linea(
            doc_aprobado=aprobado, sigrid_estado=estado) == \
            MOTIVO_LINEA_DEDICACION


def test_f019_r15_el_motivo_dice_dedicacion_y_como_liberarla() -> None:
    assert ESTADO_DEDICACION == "dedicacion"
    for motivo in (MOTIVO_LINEA_DEDICACION, MOTIVO_DOC_DEDICACION):
        assert "dedicación" in motivo
        assert "«Retirar de dedicación»" in motivo


def test_f019_r15_prioridad_de_la_linea() -> None:
    """encolado > registrado > dedicacion > aprobado (no hay dos estados
    en una linea; la prioridad se ve en el documento)."""
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado="encolado") == MOTIVO_LINEA_ENCOLADA
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado="registrado") == \
        MOTIVO_LINEA_REGISTRADA


@pytest.mark.parametrize("estados,aprobado,esperado", [
    (["dedicacion"], False, MOTIVO_DOC_DEDICACION),
    (["dedicacion", None], True, MOTIVO_DOC_DEDICACION),
    (["registrado", "dedicacion"], False, MOTIVO_DOC_REGISTRADO),
    (["dedicacion", "encolado"], False, MOTIVO_DOC_ENCOLADO),
    ([None, "omitido"], True, MOTIVO_DOC_APROBADO),
    ([None, "omitido"], False, None),
])
def test_f019_r15_el_documento_con_una_linea_en_dedicacion(
        estados, aprobado, esperado) -> None:
    assert motivo_congelacion_documento(
        aprobado=aprobado, estados_lineas=estados) == esperado


def test_f019_r15_el_repositorio_rechaza_editar_la_linea() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "dedicacion"}], doc="d1")
    repo = ParteReviewRepository(fabrica)
    with pytest.raises(CongeladoError) as error:
        repo.update_registro(registro_id=rid, horas=4.0)
    assert error.value.motivo == MOTIVO_LINEA_DEDICACION
    with pytest.raises(CongeladoError):
        repo.soft_delete_registro(registro_id=rid, by="ana")


# =================== T5 · R16 · no se borra definitivamente ==================== #

@pytest.mark.parametrize("estado,esperado", [
    ("dedicacion", True), (" Dedicacion ", True), ("registrado", True),
    ("encolado", False), ("omitido", False), ("borrado_sigrid", False),
    (None, False), ("", False),
])
def test_f019_r16_vive_fuera(estado, esperado) -> None:
    assert vive_fuera(estado) is esperado


def test_f019_r16_hard_delete_de_una_linea_en_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "dedicacion", "borrada": True}],
                     doc="d1")
    repo = ParteReviewRepository(fabrica)
    with pytest.raises(CongeladoError) as error:
        repo.hard_delete_registro(registro_id=rid)
    assert error.value.motivo == MOTIVO_HARD_DELETE_DEDICACION
    assert "dedicación" in MOTIVO_HARD_DELETE_DEDICACION
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, rid) is not None


def test_f019_r16_hard_delete_de_registrada_sigue_con_su_motivo() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "registrado", "borrada": True}],
                     doc="d1")
    with pytest.raises(CongeladoError) as error:
        ParteReviewRepository(fabrica).hard_delete_registro(registro_id=rid)
    assert error.value.motivo == MOTIVO_HARD_DELETE_REGISTRADO


def test_f019_r16_hard_delete_del_documento_con_linea_en_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"estado": "dedicacion"}, {}], doc="d1",
            doc_activo=False)
    with pytest.raises(CongeladoError) as error:
        ParteReviewRepository(fabrica).hard_delete_document(
            document_id="d1")
    assert error.value.motivo == MOTIVO_HARD_DELETE_DEDICACION


def test_f019_r16_vaciar_la_papelera_respeta_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"estado": "dedicacion"}], doc="d1", doc_activo=False)
    sembrar(fabrica, [{}], doc="d2", doc_activo=False)
    (suelta,) = sembrar(fabrica, [{"estado": "dedicacion", "borrada": True}],
                        doc="d3")
    (libre,) = sembrar(fabrica, [{"borrada": True}], doc="d4")
    resultado = ParteReviewRepository(fabrica).vaciar_papelera()
    assert resultado == {"documentos": 1, "registros": 1, "omitidos": 2}
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, suelta) is not None
        assert s.get(ParteRegistroOrm, libre) is None
