# tests/test_f047_contrato_parte_nuevo.py
"""Contrato del parte nuevo «en espera» entre sv3 y sv4 (F-047, R24-R25).

F-047 reutiliza el seguimiento de F-043 sin columnas nuevas (DA4): sv3
escribe `recalculo_pedido_id` = id del documento al guardar un parte nuevo
y sv4 deduce de ahí el motivo `nuevo` (pedido = id). No hay librería
compartida (DA5): este test ata las dos mitades de la convención.

- R24: las dos copias de `orm_models.py` siguen byte-idénticas, con las
  cuatro columnas de F-043 y ninguna más con prefijo `recalculo`, y el
  comentario del bloque de seguimiento cuenta que el pedido también lo
  escribe sv3 al guardar un parte nuevo.
- R25 (por AST): el repositorio de sv3 escribe el pedido y no el
  terminado; el pipeline pasa `recalculo_pedido_id=document_id`; y
  `motivo_espera` de sv4 compara con el id del documento.

Sin red ni BBDD: los módulos se leen por ruta.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

#: Raíz del repositorio: este fichero es `<raiz>/tests/test_f047_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_ORM_SV3 = (RAIZ / "services/partes-persistencia/infrastructure/database/"
                "orm_models.py")
RUTA_ORM_SV4 = (RAIZ / "services/partes-front/infrastructure/database/"
                "orm_models.py")

#: Las columnas del seguimiento de F-043 (F-047 no añade ninguna, DA4).
COLUMNAS_F043 = {"recalculo_pedido_id", "recalculo_pedido_at_utc",
                 "recalculo_terminado_id", "recalculo_terminado_at_utc"}


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _bloque_seguimiento(fuente: str) -> str:
    """Las líneas del bloque «Seguimiento del recalculo (F-043)» del ORM,
    desde su cabecera hasta la siguiente cabecera de bloque."""
    lineas = fuente.splitlines()
    inicio = next(i for i, l in enumerate(lineas)
                  if "--- Seguimiento del recalculo (F-043) ---" in l)
    fin = next(i for i in range(inicio + 1, len(lineas))
               if lineas[i].strip().startswith("# ---"))
    return "\n".join(lineas[inicio:fin])


# ================================ R24 ================================== #

def test_f047_r24_las_dos_copias_son_byte_identicas() -> None:
    assert RUTA_ORM_SV3.read_bytes() == RUTA_ORM_SV4.read_bytes()


@pytest.mark.parametrize("ruta", [RUTA_ORM_SV3, RUTA_ORM_SV4],
                         ids=["sv3", "sv4"])
def test_f047_r24_sin_columnas_nuevas_de_recalculo(ruta: Path) -> None:
    orm = _cargar(ruta, f"f047_orm_{ruta.parts[-4]}")
    columnas = {c.name for c in orm.ParteDocumentOrm.__table__.columns
                if c.name.startswith("recalculo")}
    assert columnas == COLUMNAS_F043


def test_f047_r24_el_comentario_cuenta_el_pedido_de_sv3() -> None:
    bloque = _bloque_seguimiento(RUTA_ORM_SV3.read_text(encoding="utf-8"))
    assert "F-047" in bloque
    assert "parte nuevo" in bloque
    assert "id del documento" in bloque
    # El pedido lo escriben los dos; el terminado, solo sv3.
    for linea in bloque.splitlines():
        if "recalculo_pedido" in linea and "mapped_column" in linea:
            assert linea.rstrip().endswith("# sv4 / sv3 (F-047)"), linea
        if "recalculo_terminado" in linea and "mapped_column" in linea:
            assert linea.rstrip().endswith("# sv3"), linea
