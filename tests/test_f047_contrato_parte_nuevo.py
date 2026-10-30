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


# ================================ R25 ================================== #

RUTA_REPO_SV3 = (RAIZ / "services/partes-persistencia/infrastructure/"
                 "database/sqlalchemy_parte_repository.py")
RUTA_PIPELINE_SV3 = (RAIZ / "services/partes-persistencia/application/"
                     "pipelines/persist_parte_pipeline.py")
RUTA_SEGUIMIENTO_SV4 = (RAIZ / "services/partes-front/application/services/"
                        "seguimiento_recalculo.py")


def _arbol(ruta: Path) -> ast.AST:
    return ast.parse(ruta.read_text(encoding="utf-8"))


def _funcion(arbol: ast.AST, nombre: str) -> ast.FunctionDef:
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"no se define {nombre}")


def _llamadas(arbol: ast.AST, atributo: str) -> list[ast.Call]:
    return [n for n in ast.walk(arbol) if isinstance(n, ast.Call)
            and isinstance(n.func, (ast.Attribute, ast.Name))
            and getattr(n.func, "attr", getattr(n.func, "id", None))
            == atributo]


def test_f047_r25_el_repositorio_de_sv3_escribe_el_pedido() -> None:
    save = _funcion(_arbol(RUTA_REPO_SV3), "save_parte")
    (documento,) = _llamadas(save, "ParteDocumentOrm")
    claves = {k.arg: ast.unparse(k.value) for k in documento.keywords}
    assert claves["recalculo_pedido_id"] == "recalculo_pedido_id"
    assert "now_iso" in claves["recalculo_pedido_at_utc"]
    assert not [c for c in claves if c.startswith("recalculo_terminado")]


def test_f047_r25_el_repositorio_de_sv3_nunca_escribe_el_terminado() -> None:
    assert "recalculo_terminado" not in RUTA_REPO_SV3.read_text(
        encoding="utf-8")


def test_f047_r25_el_pipeline_pasa_el_id_del_documento() -> None:
    (llamada,) = _llamadas(_arbol(RUTA_PIPELINE_SV3), "save_parte")
    claves = {k.arg: ast.unparse(k.value) for k in llamada.keywords}
    assert claves["document_id"] == "document_id"
    assert claves["recalculo_pedido_id"] == (
        "document_id if seguido else None")


def test_f047_r25_motivo_espera_de_sv4_compara_con_el_id() -> None:
    funcion = _funcion(_arbol(RUTA_SEGUIMIENTO_SV4), "motivo_espera")
    assert [a.arg for a in funcion.args.args] == ["document_id", "pedido_id"]
    comparaciones = [
        {ast.unparse(n.left), *(ast.unparse(c) for c in n.comparators)}
        for n in ast.walk(funcion) if isinstance(n, ast.Compare)
        and all(isinstance(o, ast.Eq) for o in n.ops)]
    assert {"pedido_id", "document_id"} in comparaciones
