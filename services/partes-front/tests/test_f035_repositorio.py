# tests/test_f035_repositorio.py
"""F-035 · R12, R13, R16 y R19 en el repositorio del portal (sv4).

  - R12/R13: las cuatro asignaciones de trabajador (`backfill_empleado`,
    `reassign_empleado_by_leido`, `…_by_worker_key`, `…_by_registro_ids`)
    aceptan `reside` (el recurso elegido): sueltan el recurso como F-023
    R42 y dejan `empleado_reside`; sin ficha (`ide` None) marcan
    `recurso_manual`, que cuenta como casado y sale de la cola.
  - R16: deshacer restaura `empleado_reside` y `empleado_match_method`; un
    snapshot antiguo sin esas claves no falla.
  - R19: `crear_parte_manual` marca `recurso_manual` sin ficha y con
    recurso.
  - Conciliar (R8): cada grupo de `list_unmatched_workers` trae las
    empresas de sus partes.

Sin red ni PostgreSQL: SQLite en memoria. Datos SINTETICOS.
"""
from __future__ import annotations

import json

import infrastructure.database.parte_repository as pr
import pytest
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

LEIDO = "Tres Solo Recurso"


def _marcar(fabrica, ids, **campos) -> None:
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            for k, v in campos.items():
                setattr(reg, k, v)
        s.commit()


def _fila(fabrica, rid) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


def _montar():
    """Un parte sin casar (dos lineas libres y una registrada), como lo deja
    sv3: sin ficha, metodo `none`, con un recurso viejo colgando."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(
        fabrica, [{"leido": LEIDO}, {"leido": LEIDO, "estado": "registrado"},
                  {"leido": LEIDO, "tipo": "extra", "horas": 1.0}],
        empleado_ide=None, empleado_dni="", empleado_nombre=None)
    _marcar(fabrica, ids, empleado_match_method="none", empleado_reside=800,
            hmo_ide=7, parte_estado="ok")
    return ParteReviewRepository(fabrica), fabrica, ids


def _asignar(repo, metodo, ids, **kw):
    """Llama a una de las cuatro asignaciones con los mismos datos."""
    if metodo == "backfill":
        return repo.backfill_empleado(nombre_leido=LEIDO, **kw)
    if metodo == "leido":
        return repo.reassign_empleado_by_leido(nombre_leido=LEIDO, **kw)
    if metodo == "worker_key":
        key = "nom-" + LEIDO.upper().replace(" ", "_")
        return repo.reassign_empleado_by_worker_key(worker_key=key, **kw)
    return repo.reassign_empleado_by_registro_ids(registro_ids=ids, **kw)


METODOS = ["backfill", "leido", "worker_key", "ids"]

SIN_FICHA = dict(ide=None, codigo="MO/0037", nombre="TRES SOLO RECURSO",
                 dni="00000003A", reside=903)
CON_FICHA = dict(ide=11, codigo="E11", nombre="Uno Ficha", dni="1R",
                 reside=901)


# ============================== R12 / R13 =============================== #

@pytest.mark.parametrize("metodo", METODOS)
def test_f035_r13_sin_ficha_queda_casada_por_recurso(metodo) -> None:
    repo, fabrica, (libre, congelada, extra) = _montar()
    resultado = _asignar(repo, metodo, [libre, congelada, extra],
                         **SIN_FICHA)
    assert (resultado[0], resultado[-1]) == (2, 1)   # tocadas, congeladas
    for rid in (libre, extra):
        r = _fila(fabrica, rid)
        assert (r.empleado_ide, r.empleado_codigo, r.empleado_nombre,
                r.empleado_dni, r.empleado_reside, r.empleado_match_method) \
            == (None, "MO/0037", "TRES SOLO RECURSO", "00000003A", 903,
                "recurso_manual")
        # El recurso se suelta (F-023 R42): lo resuelven sv3 y sv5.
        assert (r.recurso_ide, r.recurso_cif, r.hmo_ide, r.parte_estado) \
            == (None, None, None, None)
        assert pr.esta_casado(r) is True
    r = _fila(fabrica, congelada)             # la congelada no se toca
    assert (r.empleado_reside, r.empleado_match_method) == (800, "none")
    # Las casadas salen de la cola; solo queda la congelada, sin tocar.
    (grupo,) = repo.list_unmatched_workers()
    assert grupo["num_registros"] == 1


@pytest.mark.parametrize("metodo", METODOS)
def test_f035_r12_con_ficha_deja_el_reside_elegido(metodo) -> None:
    repo, fabrica, (libre, congelada, extra) = _montar()
    _asignar(repo, metodo, [libre, congelada, extra], **CON_FICHA)
    for rid in (libre, extra):
        r = _fila(fabrica, rid)
        assert (r.empleado_ide, r.empleado_codigo, r.empleado_nombre,
                r.empleado_dni, r.empleado_reside) == \
            (11, "E11", "Uno Ficha", "1R", 901)
        assert (r.recurso_ide, r.recurso_cif, r.hmo_ide) == (None, None, None)
        assert r.empleado_match_method == "none"   # con ficha no se marca
        assert pr.esta_casado(r) is True


@pytest.mark.parametrize("metodo", METODOS)
def test_f035_r15_sin_reside_todo_como_antes(metodo) -> None:
    repo, fabrica, (libre, congelada, extra) = _montar()
    _asignar(repo, metodo, [libre, congelada, extra], ide=4242, codigo=None,
             nombre=None, dni=None)
    r = _fila(fabrica, libre)
    assert (r.empleado_ide, r.empleado_reside, r.empleado_match_method) == \
        (4242, None, "none")


def test_f035_r13_metodo_manual_y_metodos_de_sv3_intactos() -> None:
    assert pr.METODO_RECURSO_MANUAL == "recurso_manual"
    # La constante espejo de sv3 (F-030) no cambia.
    assert pr.METODOS_RECURSO == frozenset({"recurso_dni", "recurso_nombre"})


@pytest.mark.parametrize("ide, metodo, casado", [
    (None, "recurso_manual", True),
    (None, "recurso_dni", True),
    (None, "none", False),
    (None, None, False),
    (11, "recurso_manual", True),
])
def test_f035_r13_esta_casado(ide, metodo, casado) -> None:
    reg = ParteRegistroOrm(empleado_ide=ide, empleado_match_method=metodo)
    assert pr.esta_casado(reg) is casado


# ================================ R16 =================================== #

def test_f035_r16_deshacer_restaura_reside_y_metodo() -> None:
    repo, fabrica, (libre, _congelada, extra) = _montar()
    repo.reassign_empleado_by_registro_ids(registro_ids=[libre, extra],
                                           **SIN_FICHA)
    assert repo.undo_last()["ok"] is True
    for rid in (libre, extra):
        r = _fila(fabrica, rid)
        assert (r.empleado_ide, r.empleado_codigo, r.empleado_reside,
                r.empleado_match_method) == (None, None, 800, "none")
    assert [g["nombre_leido"] for g in repo.list_unmatched_workers()] == \
        [LEIDO]


def test_f035_r16_snapshot_antiguo_sin_las_claves_no_falla() -> None:
    repo, fabrica, (libre, _congelada, _extra) = _montar()
    repo.reassign_empleado_by_registro_ids(registro_ids=[libre], **SIN_FICHA)
    with fabrica.create_session() as s:
        fila = s.query(UndoLogOrm).one()
        payload = json.loads(fila.payload)
        for snap in payload["registros"]:
            snap.pop("empleado_reside")
            snap.pop("empleado_match_method")
        fila.payload = json.dumps(payload)
        s.commit()
    assert repo.undo_last()["ok"] is True
    r = _fila(fabrica, libre)
    # Lo que el snapshot viejo no tenia se queda como esta.
    assert (r.empleado_codigo, r.empleado_reside, r.empleado_match_method) \
        == (None, 903, "recurso_manual")


# ================================ R19 =================================== #

def _crear(repo, **kw):
    base = dict(obra_ide=10, obra_codigo="0100", obra_nombre="Obra Uno",
                categoria=None, dias=["2026-03-03"], horas_ordinaria=8.0,
                horas_extra=0.0)
    base.update(kw)
    return repo.crear_parte_manual(**base)


def _lineas_creadas(fabrica):
    with fabrica.create_session() as s:
        return s.query(ParteRegistroOrm).filter(
            ParteRegistroOrm.fecha == "2026-03-03").all()


def test_f035_r19_crear_sin_ficha_con_recurso_es_recurso_manual() -> None:
    fabrica = FabricaSesionSqlite()
    repo = ParteReviewRepository(fabrica)
    _crear(repo, empleado_ide=None, empleado_codigo="MO/0037",
           empleado_nombre="TRES", empleado_dni="00000003A",
           empleado_reside=903, horas_extra=1.0)
    lineas = _lineas_creadas(fabrica)
    assert len(lineas) == 2
    for r in lineas:
        assert (r.empleado_ide, r.empleado_reside, r.recurso_ide,
                r.empleado_match_method) == (None, 903, 903, "recurso_manual")
    assert repo.list_unmatched_workers() == []


def test_f035_r19_crear_incidencia_sin_ficha_tambien() -> None:
    fabrica = FabricaSesionSqlite()
    repo = ParteReviewRepository(fabrica)
    _crear(repo, empleado_ide=None, empleado_codigo="MO/0037",
           empleado_nombre="TRES", empleado_dni="00000003A",
           empleado_reside=903, horas_ordinaria=0.0,
           incidencia_codigo="VAC")
    (r,) = _lineas_creadas(fabrica)
    assert (r.es_incidencia, r.empleado_match_method) == (True,
                                                         "recurso_manual")


@pytest.mark.parametrize("ide, reside", [(11, 901), (None, None)])
def test_f035_r19_crear_con_ficha_o_sin_recurso_no_marca(ide, reside) -> None:
    fabrica = FabricaSesionSqlite()
    repo = ParteReviewRepository(fabrica)
    _crear(repo, empleado_ide=ide, empleado_codigo="X", empleado_nombre="X",
           empleado_dni="1R", empleado_reside=reside)
    (r,) = _lineas_creadas(fabrica)
    assert r.empleado_match_method is None


# ========================= R8 · empresas del grupo ====================== #

def test_f035_r8_cada_grupo_trae_las_empresas_de_sus_partes() -> None:
    fabrica = FabricaSesionSqlite()
    for doc, empresa in (("d1", 28), ("d2", 1), ("d3", 28), ("d4", None)):
        sembrar_parte(fabrica, [{"leido": LEIDO}], document_id=doc,
                      empleado_ide=None, empleado_dni="")
        with fabrica.create_session() as s:
            s.get(ParteDocumentOrm, doc).empresa = empresa
            s.commit()
    sembrar_parte(fabrica, [{"leido": "Otro"}], document_id="d5",
                  empleado_ide=None, empleado_dni="")
    grupos = {g["nombre_leido"]: g
              for g in ParteReviewRepository(fabrica).list_unmatched_workers()}
    assert grupos[LEIDO]["empresas"] == [1, 28]
    assert grupos["Otro"]["empresas"] == []


# ============ revision 1 · reasignar a una ficha limpia la marca ============ #

@pytest.mark.parametrize("metodo", METODOS[1:])   # reasignaciones (casadas)
@pytest.mark.parametrize("reside", [901, None])   # por recurso / por `ide`
def test_f035_r12_reasignar_a_una_ficha_quita_recurso_manual(
        metodo, reside) -> None:
    """Una linea `recurso_manual` reasignada despues a un trabajador CON
    ficha no conserva la etiqueta (casada por `empleado_ide`)."""
    repo, fabrica, (libre, congelada, extra) = _montar()
    _asignar(repo, metodo, [libre, extra], **SIN_FICHA)
    assert _fila(fabrica, libre).empleado_match_method == "recurso_manual"
    _asignar(repo, metodo, [libre, extra], **{**CON_FICHA, "reside": reside})
    for rid in (libre, extra):
        r = _fila(fabrica, rid)
        assert r.empleado_ide == 11
        assert r.empleado_match_method is None
    # Otra marca (la de sv3) no se toca: ver test_f035_r12_con_ficha_….
