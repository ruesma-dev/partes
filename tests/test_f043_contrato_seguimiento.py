# tests/test_f043_contrato_seguimiento.py
"""Contrato del seguimiento del recalculo en `parte_documents` (F-043).

Desde F-043 el documento lleva una marca a dos manos (design §2):

  - sv4 escribe `recalculo_pedido_id` / `recalculo_pedido_at_utc` al pedir
    el recalculo (`ParteReviewRepository.marcar_recalculo_pedido`);
  - sv3 copia ese id a `recalculo_terminado_id` / `_at_utc` cuando termina
    la pasada (`SqlAlchemyRecalculoSeguimiento.marcar_terminado`).

No hay libreria compartida: las columnas viven en las dos copias de
`orm_models.py` (byte-identicas, F-010) y los nombres se repiten en el
adaptador de sv3 y en el repositorio de sv4. Este test ata las tres cosas
(R34, R35) y que el mensaje de F-042 no ha cambiado (R16).

Sin red ni BBDD: los modulos se cargan por ruta con nombres unicos.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import String

#: Raiz del repositorio: este fichero es `<raiz>/tests/test_f043_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_ORM_SV3 = (RAIZ / "services/partes-persistencia/infrastructure/database/"
                "orm_models.py")
RUTA_ORM_SV4 = (RAIZ / "services/partes-front/infrastructure/database/"
                "orm_models.py")
RUTA_REPO_SV4 = (RAIZ / "services/partes-front/infrastructure/database/"
                 "parte_repository.py")
RUTA_ADAPTADOR_SV3 = (RAIZ / "services/partes-persistencia/infrastructure/"
                      "database/recalculo_seguimiento.py")
RUTA_PUBLISHER_SV4 = (RAIZ / "services/partes-front/infrastructure/"
                      "persistencia/recalculo_publisher.py")

#: Columna -> longitud del `String` (design §2).
COLUMNAS: dict[str, int] = {
    "recalculo_pedido_id": 36,
    "recalculo_pedido_at_utc": 64,
    "recalculo_terminado_id": 36,
    "recalculo_terminado_at_utc": 64,
}


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module", params=[("sv3", RUTA_ORM_SV3),
                                        ("sv4", RUTA_ORM_SV4)],
                ids=["sv3", "sv4"])
def orm(request) -> ModuleType:
    nombre, ruta = request.param
    return _cargar(ruta, f"f043_contrato_orm_{nombre}")


def _tupla_literal(fuente: str, nombre: str) -> tuple:
    """El valor literal de una asignacion de modulo `nombre = (...)`."""
    for nodo in ast.parse(fuente).body:
        objetivos = []
        if isinstance(nodo, ast.Assign):
            objetivos = nodo.targets
        elif isinstance(nodo, ast.AnnAssign):
            objetivos = [nodo.target]
        for obj in objetivos:
            if isinstance(obj, ast.Name) and obj.id == nombre:
                return tuple(ast.literal_eval(nodo.value))
    raise AssertionError(f"{nombre} no esta en el fichero")


# ============================ R34 · esquema ============================= #

@pytest.mark.parametrize("columna,largo", sorted(COLUMNAS.items()))
def test_f043_r34_parte_documents_tiene_la_columna(orm, columna,
                                                   largo) -> None:
    tabla = orm.ParteDocumentOrm.__table__
    assert columna in tabla.columns, columna
    col = tabla.columns[columna]
    assert isinstance(col.type, String)
    assert col.type.length == largo
    assert col.nullable is True
    assert not col.index
    assert not col.unique
    assert col.server_default is None
    assert col.default is None


def test_f043_r34_ddl_complementario_las_anade(orm) -> None:
    sentencias = orm.ddl_complementario()
    prefijo = "ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS "
    for columna, largo in COLUMNAS.items():
        assert f"{prefijo}{columna} VARCHAR({largo})" in sentencias, columna


def test_f043_r34_las_dos_copias_son_byte_identicas() -> None:
    assert RUTA_ORM_SV3.read_bytes() == RUTA_ORM_SV4.read_bytes()


def test_f043_r34_las_columnas_no_entran_en_deshacer() -> None:
    campos = _tupla_literal(RUTA_REPO_SV4.read_text(encoding="utf-8"),
                            "_DOC_UNDO_FIELDS")
    assert campos, "_DOC_UNDO_FIELDS vacio"
    assert not set(campos) & set(COLUMNAS)
