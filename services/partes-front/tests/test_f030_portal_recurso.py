# tests/test_f030_portal_recurso.py
"""F-030 · R18-R20: el portal (sv4) con un trabajador casado por recurso.

sv3 casa a quien no tiene ficha de empleado contra su «ficha de recurso»:
la linea llega con `empleado_ide` NULL y `empleado_match_method`
`recurso_dni` o `recurso_nombre`. En el portal, al minimo (DA4):

  - R18: cuenta como casado en las cuatro vistas (`esta_casado`).
  - R19: no entra en la cola de conciliacion ni en su confirmacion por
    nombre leido, que le pondria una ficha ajena y soltaria su recurso.
  - R20: catalogo, alta manual y reasignacion no cambian (caracterizacion).

Sin red ni PostgreSQL: SQLite en memoria. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest

import infrastructure.database.parte_repository as pr
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

CIF = "09876543B"
NOMBRE_RECURSO = "GOMEZ RUIZ, PEDRO"
LEIDO = "Pedro Gomez Ruiz"
SIN_CASAR = "Fulano Sin Casar"
MARZO = "2026-03"


def _marcar(fabrica, ids, **campos) -> None:
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            for k, v in campos.items():
                setattr(reg, k, v)
        s.commit()


def _montar(metodo="recurso_dni"):
    """Un parte con el trabajador casado por recurso (2 lineas) y otro con
    un trabajador sin casar."""
    fabrica = FabricaSesionSqlite()
    ids_rec = sembrar_parte(
        fabrica, [{"leido": LEIDO}, {"leido": LEIDO, "tipo": "extra",
                                     "horas": 1.0}],
        document_id="doc-rec", empleado_ide=None, empleado_dni=CIF,
        empleado_nombre=NOMBRE_RECURSO)
    _marcar(fabrica, ids_rec, empleado_match_method=metodo,
            empleado_reside=950, recurso_ide=950, recurso_cif=CIF,
            parte_estado="sin_parte")
    ids_sin = sembrar_parte(
        fabrica, [{"leido": SIN_CASAR}], document_id="doc-sin",
        empleado_ide=None, empleado_dni="", empleado_nombre=None)
    _marcar(fabrica, ids_sin, empleado_match_method="none",
            recurso_ide=None, recurso_cif=None)
    return ParteReviewRepository(fabrica), fabrica, ids_rec, ids_sin


def _fila(fabrica, rid) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


# ============================ R18 · casado =============================== #

def test_f030_r18_metodos_de_recurso() -> None:
    assert pr.METODOS_RECURSO == frozenset({"recurso_dni", "recurso_nombre"})


@pytest.mark.parametrize("ide, metodo, casado", [
    (None, "recurso_dni", True),
    (None, "recurso_nombre", True),
    (77, "nombre", True),
    (77, None, True),
    (77, "recurso_dni", True),
    (None, "none", False),
    (None, None, False),
    (None, "nombre_ambiguo", False),
    (None, "dni_solo_baja", False),
])
def test_f030_r18_esta_casado(ide, metodo, casado) -> None:
    reg = ParteRegistroOrm(empleado_ide=ide, empleado_match_method=metodo)
    assert pr.esta_casado(reg) is casado


@pytest.mark.parametrize("metodo", ["recurso_dni", "recurso_nombre"])
def test_f030_r18_lista_de_trabajadores(metodo) -> None:
    repo, *_ = _montar(metodo)
    casado = {w.nombre: w.matched for w in repo.list_workers()}
    assert casado == {NOMBRE_RECURSO: True, SIN_CASAR: False}
    # Los casados primero, como cualquier trabajador casado.
    assert [w.nombre for w in repo.list_workers()] == \
        [NOMBRE_RECURSO, SIN_CASAR]


def test_f030_r18_detalle_del_trabajador() -> None:
    repo, *_ = _montar()
    (fila,) = [w for w in repo.list_workers() if w.nombre == NOMBRE_RECURSO]
    detalle = repo.get_worker(fila.worker_key)
    assert (detalle.nombre, detalle.matched, detalle.dni) == \
        (NOMBRE_RECURSO, True, CIF)
    sin = [w for w in repo.list_workers() if w.nombre == SIN_CASAR][0]
    assert repo.get_worker(sin.worker_key).matched is False


def test_f030_r18_matriz_de_la_obra() -> None:
    repo, *_ = _montar()
    det = repo.get_obra("obr-10", period_key=MARZO)
    casado = {r.nombre: r.matched for r in det.rows}
    assert casado == {NOMBRE_RECURSO: True, SIN_CASAR: False}
    assert [r.nombre for r in det.rows] == [NOMBRE_RECURSO, SIN_CASAR]


def test_f030_r18_detalle_del_parte() -> None:
    repo, *_ = _montar()
    (emp,) = repo.get_parte("doc-rec").empleados
    assert (emp.empleado_nombre, emp.matched) == (NOMBRE_RECURSO, True)
    (otro,) = repo.get_parte("doc-sin").empleados
    assert otro.matched is False


# ====================== R19 · cola de conciliacion ====================== #

def test_f030_r19_la_cola_no_incluye_a_los_casados_por_recurso() -> None:
    repo, *_ = _montar()
    assert [g["nombre_leido"] for g in repo.list_unmatched_workers()] == \
        [SIN_CASAR]
    assert repo.count_unmatched_workers() == 1


def test_f030_r19_la_cola_sigue_incluyendo_metodo_vacio() -> None:
    """Lineas antiguas sin metodo (NULL) siguen en la cola."""
    repo, fabrica, _, ids_sin = _montar()
    _marcar(fabrica, ids_sin, empleado_match_method=None)
    assert [g["nombre_leido"] for g in repo.list_unmatched_workers()] == \
        [SIN_CASAR]


def test_f030_r19_confirmar_por_nombre_leido_no_toca_al_casado_por_recurso(
) -> None:
    repo, fabrica, ids_rec, _ = _montar("recurso_nombre")
    assert repo.backfill_empleado(nombre_leido=LEIDO, ide=4242, codigo="E1",
                                  nombre="OTRA FICHA", dni="11111111H") == \
        (0, 0)
    for rid in ids_rec:
        fila = _fila(fabrica, rid)
        assert (fila.empleado_ide, fila.empleado_dni, fila.recurso_ide,
                fila.empleado_reside) == (None, CIF, 950, 950)


def test_f030_r19_confirmar_por_nombre_leido_sigue_casando_lo_sin_casar(
) -> None:
    repo, fabrica, _, ids_sin = _montar()
    _marcar(fabrica, ids_sin, empleado_match_method=None)
    assert repo.backfill_empleado(nombre_leido=SIN_CASAR, ide=4242,
                                  codigo="E1", nombre="FICHA",
                                  dni="11111111H") == (1, 0)
    assert _fila(fabrica, ids_sin[0]).empleado_ide == 4242


# ============ R20 · reasignar: como hoy (caracterizacion) =============== #

def test_f030_r20_reasignar_lineas_a_una_ficha_suelta_el_recurso() -> None:
    repo, fabrica, ids_rec, _ = _montar()
    assert repo.reassign_empleado_by_registro_ids(
        registro_ids=ids_rec, ide=4242, codigo="E1", nombre="FICHA",
        dni="11111111H") == (2, 0)
    for rid in ids_rec:
        fila = _fila(fabrica, rid)
        assert (fila.empleado_ide, fila.empleado_dni, fila.recurso_ide,
                fila.empleado_reside, fila.parte_estado) == \
            (4242, "11111111H", None, None, None)


def test_f030_r20_reasignar_por_nombre_leido_suelta_el_recurso() -> None:
    repo, fabrica, ids_rec, _ = _montar()
    assert repo.reassign_empleado_by_leido(
        nombre_leido=LEIDO, ide=4242, codigo="E1", nombre="FICHA",
        dni="11111111H") == (2, 0)
    assert _fila(fabrica, ids_rec[0]).empleado_ide == 4242
    assert _fila(fabrica, ids_rec[0]).recurso_ide is None
