# tests/test_f023_columnas_empresa.py
"""F-023 · DA11 y R6: la empresa del parte se guarda en `parte_documents`.

Tres columnas NULLABLES nuevas, en las dos copias de `orm_models.py`
(el guardian `tests/test_f010_orm_models_gemelos.py` vigila que sigan
siendo byte-identicas):

  - `empresa_membrete`: el texto del membrete tal cual lo leyo sv2 (R6);
  - `empresa`: la empresa del parte (`con.emp`, R15);
  - `empresa_origen`: de donde sale (`membrete`, `obra`, `trabajadores`,
    `nombre` o NULL).

Sin ellas la conciliacion no sabe la empresa de un parte sin obra casada
y nadie puede auditar por que se eligio una gemela. Se anaden solas al
arrancar: `ddl_complementario()` genera su `ADD COLUMN IF NOT EXISTS`.
"""
from __future__ import annotations

from application.services.parte_normalizer import ParteNormalizer
from domain.models.parte_records import ObraMatch, ParteDocumento
from infrastructure.database.orm_models import ParteDocumentOrm, ddl_complementario
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite


# ============================ DA11 · esquema ============================ #

def test_f023_da11_el_ddl_de_arranque_anade_las_tres_columnas() -> None:
    sentencias = ddl_complementario()
    for definicion in ("empresa_membrete VARCHAR(255)", "empresa INTEGER",
                       "empresa_origen VARCHAR(24)"):
        assert ("ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS "
                f"{definicion}") in sentencias


def test_f023_da11_las_tres_columnas_son_nullables() -> None:
    columnas = ParteDocumentOrm.__table__.columns
    for nombre in ("empresa_membrete", "empresa", "empresa_origen"):
        assert columnas[nombre].nullable is True
        assert columnas[nombre].server_default is None


# ============================ R6 · normalizar =========================== #

def _normalizar(cabecera: dict) -> ParteDocumento:
    return ParteNormalizer().normalize(
        {"cabecera": cabecera, "firma": {}, "empleados": []})


def test_f023_r6_el_normalizador_lee_la_empresa_del_membrete() -> None:
    parte = _normalizar({"empresa_membrete": "Porsan e Hijos, S.L."})
    assert parte.empresa_membrete == "Porsan e Hijos, S.L."


def test_f023_r6_sin_la_clave_o_vacia_queda_a_none() -> None:
    """Un sv2 anterior a F-023 no manda la clave (DA9: sv3 lo tolera)."""
    assert _normalizar({}).empresa_membrete is None
    assert _normalizar({"empresa_membrete": "   "}).empresa_membrete is None


# ============================ R6 · persistir ============================ #

def test_f023_r6_r15_el_repositorio_guarda_las_tres_columnas() -> None:
    fabrica = FabricaSesionSqlite()
    repositorio = SqlAlchemyParteRepository(fabrica)   # type: ignore[arg-type]
    parte = ParteDocumento(
        fecha_iso="2026-09-15", fecha_int=20260915, obra_numero_leido="100",
        obra=ObraMatch(ide=200, codigo="0100", method="codigo_membrete",
                       empresa=28),
        empresa_membrete="PORSAN", empresa=28, empresa_origen="membrete",
    )
    repositorio.save_parte(
        document_id="doc-f023", parte=parte, meta={}, context={},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=False)
    with fabrica.create_session() as sesion:
        doc = sesion.get(ParteDocumentOrm, "doc-f023")
        assert (doc.empresa_membrete, doc.empresa, doc.empresa_origen) == \
            ("PORSAN", 28, "membrete")
        assert doc.obra_match_method == "codigo_membrete"


def test_f023_r15_un_parte_sin_empresa_guarda_null() -> None:
    fabrica = FabricaSesionSqlite()
    repositorio = SqlAlchemyParteRepository(fabrica)   # type: ignore[arg-type]
    repositorio.save_parte(
        document_id="doc-sin", parte=ParteDocumento(), meta={}, context={},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=True)
    with fabrica.create_session() as sesion:
        doc = sesion.get(ParteDocumentOrm, "doc-sin")
        assert (doc.empresa_membrete, doc.empresa, doc.empresa_origen) == \
            (None, None, None)
