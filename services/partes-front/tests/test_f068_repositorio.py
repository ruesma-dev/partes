# tests/test_f068_repositorio.py
"""F-068 · el repositorio dice qué partes tocó un casado (design §4).

`backfill_empleado` (y, con D3-b, las tres `reassign_empleado_by_*`)
aceptan un colector opcional `documentos`: tras el commit le añaden los
`document_id` de las líneas que ESCRIBIERON (no las congeladas
omitidas), en orden de `id` de línea y sin repetir. El valor de retorno
no cambia (R22): lo afirman tests de F-004, F-023, F-030 y F-035.

Sin red: repositorio real sobre SQLite. Datos sintéticos.
"""
from __future__ import annotations

from types import SimpleNamespace

from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, datos_registros, sembrar_parte

LEIDO = "Juan Leido"
OTRO = "Otro Distinto"
QUIEN = dict(ide=4242, codigo="E42", nombre="Ana Casada", dni="99999999R")


def _sin_casar(fabrica, lineas, *, doc: str, aprobado: bool = False,
               fecha: str = "2026-03-02") -> list[int]:
    """Un parte con líneas SIN casar (`empleado_ide` None)."""
    return sembrar_parte(fabrica, lineas, document_id=doc, aprobado=aprobado,
                         fecha=fecha, empleado_ide=None)


def _libre(leido: str = LEIDO) -> dict:
    return {"estado": None, "leido": leido}


# ========================= `_documentos_de` ============================ #

def _reg(id_: int, doc: str | None) -> SimpleNamespace:
    return SimpleNamespace(id=id_, document_id=doc)


def _documentos_de(regs) -> list[str]:
    return repo_mod._documentos_de(regs)


def test_f068_documentos_de_ordena_por_id_de_linea() -> None:
    regs = [_reg(30, "d-b"), _reg(10, "d-a"), _reg(20, "d-c")]
    assert _documentos_de(regs) == ["d-a", "d-c", "d-b"]


def test_f068_documentos_de_sin_repetir_y_sin_none() -> None:
    regs = [_reg(4, "d-b"), _reg(1, "d-a"), _reg(2, None), _reg(3, "d-a"),
            _reg(5, "")]
    assert _documentos_de(regs) == ["d-a", "d-b"]


def test_f068_documentos_de_vacio() -> None:
    assert _documentos_de([]) == []


# ================= `backfill_empleado` · colector (R4) ================= #

def test_f068_e1_backfill_un_parte() -> None:
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre(), _libre(OTRO)], doc="d-1")
    docs: list[str] = []
    res = ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, documentos=docs, **QUIEN)
    assert res == (1, 0)
    assert docs == ["d-1"]


def test_f068_e2_backfill_dos_partes_en_orden_de_id_de_linea() -> None:
    """D2 se siembra antes: sus líneas tienen ids menores y va delante."""
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre()], doc="d-2", fecha="2026-03-03")
    _sin_casar(fabrica, [_libre(), _libre()], doc="d-1")
    docs: list[str] = []
    res = ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, documentos=docs, **QUIEN)
    assert res == (3, 0)
    assert docs == ["d-2", "d-1"]


def test_f068_e3_r4_parte_con_libres_y_congeladas_recibe_el_pedido() -> None:
    """R4: D1 tiene una libre y una registrada (omitida): D1 entra; D2,
    aprobado entero, no aporta parte."""
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre(), {"estado": "registrado", "leido": LEIDO}],
               doc="d-1")
    _sin_casar(fabrica, [_libre()], doc="d-2", aprobado=True,
               fecha="2026-03-03")
    docs: list[str] = []
    res = ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, documentos=docs, **QUIEN)
    assert res == (1, 2)
    assert docs == ["d-1"]


def test_f068_e4_r4_solo_congeladas_no_aporta_partes() -> None:
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre()], doc="d-2", aprobado=True)
    docs: list[str] = ["previo"]
    res = ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, documentos=docs, **QUIEN)
    assert res == (0, 1)
    assert docs == ["previo"]          # ni se vacía ni se añade nada


def test_f068_backfill_sin_coincidencias_no_toca_el_colector() -> None:
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre()], doc="d-1")
    docs: list[str] = []
    repo = ParteReviewRepository(fabrica)
    assert repo.backfill_empleado(nombre_leido="Nadie", documentos=docs,
                                  **QUIEN) == (0, 0)
    assert repo.backfill_empleado(nombre_leido="  ", documentos=docs,
                                  **QUIEN) == (0, 0)
    assert docs == []


def test_f068_backfill_el_colector_se_extiende_no_se_reemplaza() -> None:
    fabrica = FabricaSesionSqlite()
    _sin_casar(fabrica, [_libre()], doc="d-1")
    docs: list[str] = ["ya-estaba"]
    ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, documentos=docs, **QUIEN)
    assert docs == ["ya-estaba", "d-1"]


def test_f068_r22_backfill_sin_colector_igual_que_hoy() -> None:
    """R22: sin `documentos` el retorno y lo escrito son los de siempre."""
    fabrica = FabricaSesionSqlite()
    ids = _sin_casar(fabrica, [_libre(), _libre(OTRO)], doc="d-1")
    res = ParteReviewRepository(fabrica).backfill_empleado(
        nombre_leido=LEIDO, **QUIEN)
    assert res == (1, 0) and isinstance(res, tuple) and len(res) == 2
    datos = datos_registros(fabrica, ids)
    assert datos[ids[0]]["empleado_ide"] == 4242
    assert datos[ids[1]]["empleado_ide"] is None
