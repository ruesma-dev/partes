# tests/test_f069_mutacion.py
"""F-069 · T15: los supervivientes de la campaña de mutación, cazados.

Cada test fija un contrato que la campaña (`progress/mutacion_F-069.md`)
encontró sin vigilar: los ceros de `ResumenEscritura` (el doble de la
pasada los usa), el `FOR UPDATE` solo en PostgreSQL (R15), el redondeo de
la huella a 6 decimales (design §3) y el lote de 1000 ids (`LOTE_IN`).
Sin red ni PostgreSQL; datos sinteticos.
"""
from __future__ import annotations

import dataclasses

import pytest
from sqlalchemy import event

from application.services.pareja_extra import huellas_por_clave
from infrastructure.database import sqlalchemy_parte_repository as mod
from tests.dobles import FabricaSesionSqlite
from tests.f069_comun import base, extra, sembrar

K = ("doc-1", 0, None, 20261001)


# ===================== ResumenEscritura (design §4.2) =================== #

def test_f069_r6_resumen_por_defecto_todo_a_cero() -> None:
    """`RepositorioFake` y cualquier llamador que solo rellene parte de los
    contadores cuentan con que el resto valga 0."""
    assert dataclasses.astuple(mod.ResumenEscritura()) == (0, 0, 0, 0, 0, 0)


def test_f069_r6_resumen_inmutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        mod.ResumenEscritura().aplicados = 3  # type: ignore[misc]


# ================= R15 · FOR UPDATE solo en PostgreSQL ================= #

class _Resultado:
    def all(self):
        return []


class _SesionFalsa:
    """Lo minimo de una `Session` para ver la sentencia de bloqueo."""

    def __init__(self, dialecto: str) -> None:
        self._dialecto = dialecto
        self.sentencias: list = []

    def get_bind(self):
        return type("B", (), {"dialect": type("D", (), {
            "name": self._dialecto})()})()

    def scalars(self, _stmt):
        return ["doc-1"]

    def execute(self, stmt):
        self.sentencias.append(stmt)
        return _Resultado()


@pytest.mark.parametrize("dialecto, bloquea", [
    ("postgresql", True), ("sqlite", False)])
def test_f069_r15_for_update_solo_en_postgresql(dialecto, bloquea) -> None:
    sesion = _SesionFalsa(dialecto)
    mod.SqlAlchemyParteRepository._bloquear_documentos(sesion, [], [])
    stmt, = sesion.sentencias
    assert (stmt._for_update_arg is not None) is bloquea
    if bloquea:
        tablas = {t.name for t in stmt._for_update_arg.of}
        assert tablas == {"parte_registros"}


# ================== design §3 · huella a 6 decimales =================== #

def _fila(horas: float) -> dict:
    return {"registro_id": 1, "document_id": "doc-1", "line_index": 0,
            "empleado_line_no": None, "fecha_int": 20261001,
            "horas": horas, "horas_orig": None, "tipo_hora": "normal",
            "extra_auto": False, "sigrid_estado": None,
            "deleted_at_utc": None, "doc_approved": False, "doc_activo": True}


def test_f069_r13_huella_ignora_el_septimo_decimal() -> None:
    assert huellas_por_clave([_fila(8.0)]) == \
        huellas_por_clave([_fila(8.0000004)])


# ======================= LOTE_IN · lotes de 1000 ======================= #

def test_f069_r8_ids_de_los_casados_en_lotes_de_1000() -> None:
    fabrica = FabricaSesionSqlite()
    b, _e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)])
    repo = mod.SqlAlchemyParteRepository(fabrica)
    lotes: list[str] = []

    def _antes(_c, _cu, sql, params, *_a):
        if "parte_registros.id IN" in sql:
            lotes.append(len(params))
    event.listen(fabrica.engine, "before_cursor_execute", _antes)
    # 1001 casados: el suyo y 1000 ids que no existen (se saltan).
    updates = [{"registro_id": b}] + [
        {"registro_id": 100000 + i} for i in range(1000)]
    res = repo.escribir_pasada(None, updates, [])
    assert lotes == [1000, 1]
    assert res.actualizados == 1
