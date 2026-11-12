# tests/f069_comun.py
"""F-069: siembra y fotos de la base de memoria comunes a sus tests.

No es un modulo de tests (no empieza por `test_`): lo importan
`test_f069_*`. Datos sinteticos (DNI de prueba, obra 10, recurso 501).
"""
from __future__ import annotations

from sqlalchemy import select

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from tests.dobles import sembrar_lineas

JUEVES = "2026-10-01"      # laborable; jornada 8 h con `reshor_par(501)`
RECURSO = 501


def base(horas: float, horas_orig: float | None = None, estado=None, *,
         li: int = 0, eln: int | None = 1) -> dict:
    return {"horas": horas, "horas_orig": horas_orig, "estado": estado,
            "line_index": li, "empleado_line_no": eln, "recurso_ide": RECURSO}


def extra(horas: float, estado=None, *, li: int = 0, eln: int | None = 1,
          auto: bool = True) -> dict:
    return {"horas": horas, "tipo": "extra", "extra_auto": auto,
            "estado": estado, "line_index": li, "empleado_line_no": eln,
            "recurso_ide": RECURSO}


def sembrar(fabrica, lineas, **kw) -> list[int]:
    return sembrar_lineas(fabrica, lineas, fecha=kw.pop("fecha", JUEVES),
                          **kw)


def escenario(fabrica) -> dict[str, list[int]]:
    """Las variantes de pareja que el revert distingue, en dos partes.

    `doc-1` (activo):
      p0: base 8/10 + extra automatica 2 + extra explicita 1 (no miembro);
      p1: base 6 sin partir;
      p2: base `registrado` 8/10 + extra automatica 2 (protegida, R8);
      p3: base 8/10 + extra `registrado` 2 + extra duplicada 2 (R6);
      p4: base `registrado` 8 SIN `horas_orig` + extra automatica 2 (la
          base no entra en la consulta del revert y la extra se borra);
      p5: base 8/10 en la papelera + su extra 2.
    `doc-2` (INACTIVO): base 8/10 + extra 2 (el revert tambien la toca).
    """
    d1 = sembrar(fabrica, [
        base(8.0, 10.0, li=0), extra(2.0, li=0), extra(1.0, li=0, auto=False),
        base(6.0, li=1),
        base(8.0, 10.0, "registrado", li=2), extra(2.0, li=2),
        base(8.0, 10.0, li=3), extra(2.0, "registrado", li=3),
        extra(2.0, li=3),
        base(8.0, None, "registrado", li=4), extra(2.0, li=4),
        base(8.0, 10.0, li=5), extra(2.0, li=5),
    ], document_id="doc-1")
    d2 = sembrar(fabrica, [base(8.0, 10.0, li=0), extra(2.0, li=0)],
                 document_id="doc-2")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, d1[11]).deleted_at_utc = "2026-10-02T08:00"
        s.get(ParteDocumentOrm, "doc-2").is_active = False
        s.commit()
    return {"doc-1": d1, "doc-2": d2}


def foto(fabrica) -> list[tuple]:
    """Todas las columnas de todas las filas de `parte_registros`, por id."""
    cols = list(ParteRegistroOrm.__table__.columns)
    with fabrica.create_session() as s:
        filas = s.execute(
            select(*cols).order_by(ParteRegistroOrm.id)).all()
    return [tuple(f) for f in filas]


def filas_cortas(fabrica) -> list[tuple]:
    """(id, document_id, line_index, horas, horas_orig, extra_auto)."""
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.id, ParteRegistroOrm.document_id,
                   ParteRegistroOrm.line_index, ParteRegistroOrm.horas,
                   ParteRegistroOrm.horas_orig, ParteRegistroOrm.extra_auto)
            .order_by(ParteRegistroOrm.id)).all()
    return [tuple(f) for f in filas]


class IndiceFijo:
    """Indice de personas que siempre elige el recurso 501 (como el de
    `test_f037_dos_pasadas`: estos tests no van de casar recursos)."""

    recursos: list = []

    def empresa_de_obra(self, obra_ide):  # noqa: ARG002
        return None

    def elegir_recurso(self, *args, **kwargs):  # noqa: ARG002
        from application.services.seleccion_sigrid import ResolucionRecurso

        return ResolucionRecurso(ide=RECURSO, motivo="ok")


def conciliador_f069(fabrica, *, lookup=None, repo=None):
    """Conciliador real sobre el repositorio real; Sigrid en dobles."""
    from application.services.recurso_conciliador import RecursoConciliador
    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )
    from tests.dobles import CalendarioFake, LookupFake, reshor_par

    return RecursoConciliador(
        repository=repo or SqlAlchemyParteRepository(fabrica),
        lookup=lookup or LookupFake(reshor=reshor_par(RECURSO)),
        calendario=CalendarioFake({"2026-10-03", "2026-10-04"}),
        indice_provider=lambda: IndiceFijo(),
    )
