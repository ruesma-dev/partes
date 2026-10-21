# tests/test_f049_guardar_celda.py
"""F-049 · repositorio y rutas del editor de celda de la matriz de obra.

`POST /api/matriz/celda` guarda la celda entera en una transacción con su
entrada de deshacer, crea la ordinaria o la extra que falte desde la
plantilla y pide UN recálculo con un pedido compartido (DA13-C) en los
partes tocados y en los de otras obras del mismo (recurso, día).

SQLite en memoria con el ORM real (`tests/dobles.py`), publicador de
recálculo y cliente de Sigrid falsos. Ni red ni PostgreSQL. Nombres, DNIs
y recursos SINTÉTICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-10-14T08:00:00+00:00"
FECHA = "2026-10-14"                 # martes
FINT = 20261014
MES = {"period_key": "2026-10", "mode": "natural"}
OBRA_Y, OBRA_X = 678, 686
KEY_Y, KEY_X = f"obr-{OBRA_Y}", f"obr-{OBRA_X}"
RECURSO = 501
WK = f"rec-{RECURSO}"


def _doc(s, doc_id: str, obra: int, *, fecha: str = FECHA,
         aprobado: bool = False) -> None:
    s.add(ParteDocumentOrm(
        id=doc_id, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + doc_id,
        fecha=fecha, fecha_int=int(fecha.replace("-", "")),
        created_at_utc=AHORA, obra_ide=obra, obra_codigo=f"0{obra}",
        obra_nombre=f"Obra {obra}", approved=aprobado,
        approved_by="ana" if aprobado else None))


def _reg(s, doc_id: str, obra: int, line_index: int, *,
         fecha: str = FECHA, tipo: str = "normal", horas: float = 8.0,
         recurso: int | None = RECURSO, **campos) -> int:
    datos = dict(
        empleado_line_no=1, empleado_ide=77, empleado_dni="00000077A",
        empleado_nombre="Persona Siete", trabajador_nombre_leido="P. Siete",
        categoria="OFICIAL 1ª", hora_ide=1, hora_codigo="HL01",
        hora_candef=8.0, recurso_cif="00000077A")
    datos.update(campos)
    reg = ParteRegistroOrm(
        document_id=doc_id, line_index=line_index, fecha=fecha,
        fecha_int=int(fecha.replace("-", "")), obra_ide=obra,
        obra_codigo=f"0{obra}", obra_nombre=f"Obra {obra}",
        tipo_hora=tipo, horas=horas, recurso_ide=recurso, **datos)
    s.add(reg)
    s.flush()
    return reg.id


def _celda_de_la_matriz(repo, obra_key: str = KEY_Y, wk: str = WK,
                        fecha: str = FECHA):
    detalle = repo.get_obra(obra_key, **MES)
    fila = next(r for r in detalle.rows if r.worker_key == wk)
    return next(c for c in fila.cells if c.date_iso == fecha)


# ===================== R10 · `a` en las extra_auto ===================== #

def test_f049_r10_regs_marcan_solo_las_extra_auto():
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-y", OBRA_Y)
        base = _reg(s, "d-y", OBRA_Y, 0, horas=8.0, horas_orig=10.0)
        auto = _reg(s, "d-y", OBRA_Y, 0, tipo="extra", horas=2.0,
                    extra_auto=True)
        explicita = _reg(s, "d-y", OBRA_Y, 1, tipo="extra", horas=1.0)
        s.commit()
    celda = _celda_de_la_matriz(ParteReviewRepository(fabrica))
    por_id = {r["id"]: r for r in celda.regs}
    assert por_id[auto] == {"id": auto, "t": "e", "h": 2.0, "p": None,
                            "a": 1}
    assert "a" not in por_id[base]
    assert "a" not in por_id[explicita]
    assert por_id[base] == {"id": base, "t": "n", "h": 8.0, "p": None}
