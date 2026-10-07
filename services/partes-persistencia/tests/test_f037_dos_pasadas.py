# tests/test_f037_dos_pasadas.py
"""F-037 · R10-R16: dos pasadas seguidas de sv3 sobre la base de memoria.

Cada mensaje de sv3 recalcula TODOS los partes activos: revierte las
extras automaticas de la pasada anterior, lee, calcula los splits y los
aplica. La incidencia de produccion (obra 0678, 01-03/10/2026) era que,
con la base `omitido` y su extra automatica ya `registrado`, cada pasada
restauraba la base, la volvia a partir y creaba una `extra_auto` nueva.

Aqui se ejercita el ciclo COMPLETO con el repositorio real (SQLite en
memoria, mismo ORM) y el conciliador real; solo los maestros de Sigrid son
dobles: el indice de personas siempre elige el recurso 501 (`IndiceFijo`)
y su reshor es el par laborable/extra de siempre (candef 8).

Lo que se vigila en cada pasada, ademas de las filas resultantes, es
`extras_reclasificadas` del resumen: el numero de `extra_auto` que la
pasada ha CREADO. Matiz del humano (2026-10-07): «no deberia ni salir la
tercera linea; al existir ya esas horas extra guardadas, ignorarla». Con
la extra de la pareja congelada el recalculo no genera NINGUNA extra, ni
siquiera una transitoria que luego se borre.

Todo SINTETICO (DNI de prueba, obra 10, recurso 501); ni red ni Sigrid.
"""
from __future__ import annotations

from sqlalchemy import select

from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import ResolucionRecurso
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    reshor_par,
    sembrar_lineas,
)

RECURSO = 501
JUEVES = "2026-10-01"      # laborable; jornada del dia 8 h (candef 8)
SABADO = "2026-10-03"      # no laborable
NO_LABORABLES = {SABADO, "2026-10-04"}


class IndiceFijo:
    """Indice de personas que siempre elige el recurso 501.

    Los tests de F-037 no van de casar recursos (eso es F-023/F-036): con
    este doble no construyen `RecursoRow` ni `IndicePersonas`.
    """

    recursos: list = []

    def empresa_de_obra(self, obra_ide):  # noqa: ARG002
        return None

    def elegir_recurso(self, *args, **kwargs):  # noqa: ARG002
        return ResolucionRecurso(ide=RECURSO, motivo="ok")


def _conciliador(fabrica) -> RecursoConciliador:
    return RecursoConciliador(
        repository=SqlAlchemyParteRepository(fabrica),
        lookup=LookupFake(reshor=reshor_par(RECURSO)),
        calendario=CalendarioFake(set(NO_LABORABLES)),
        indice_provider=lambda: IndiceFijo(),
    )


def _filas(fabrica) -> list[tuple]:
    """(id, line_index, horas, horas_orig, extra_auto, sigrid_estado) de
    todas las filas, por id."""
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.id, ParteRegistroOrm.line_index,
                   ParteRegistroOrm.horas, ParteRegistroOrm.horas_orig,
                   ParteRegistroOrm.extra_auto,
                   ParteRegistroOrm.sigrid_estado)
            .order_by(ParteRegistroOrm.id)
        ).all()
    return [tuple(f) for f in filas]


def _extras(filas: list[tuple]) -> list[tuple]:
    return [f for f in filas if f[4]]


def _dos_pasadas(fabrica) -> tuple[list[dict], list[list[tuple]]]:
    """Dos `conciliar_todos` seguidos: resumen y filas tras cada uno."""
    conciliador = _conciliador(fabrica)
    resumenes, fotos = [], []
    for _ in range(2):
        resumenes.append(conciliador.conciliar_todos())
        fotos.append(_filas(fabrica))
    return resumenes, fotos


# ================= R16 · lo no congelado, como siempre ================== #
# Caracterizacion: verde antes y despues de F-037.

def test_f037_r16_sin_nada_congelado_se_reparte_en_cada_pasada() -> None:
    fabrica = FabricaSesionSqlite()
    base, = sembrar_lineas(fabrica, [{"horas": 10.0}], fecha=JUEVES)

    resumenes, fotos = _dos_pasadas(fabrica)

    for resumen, filas in zip(resumenes, fotos):
        # Cada pasada deshace la extra anterior y la vuelve a crear.
        assert resumen["extras_reclasificadas"] == 1
        assert filas[0] == (base, 0, 8.0, 10.0, False, None)
        extras = _extras(filas)
        assert len(extras) == 1
        assert extras[0][1:] == (0, 2.0, None, True, None)


def test_f037_r16_no_laborable_sin_nada_congelado_todo_a_extra() -> None:
    fabrica = FabricaSesionSqlite()
    base, = sembrar_lineas(fabrica, [{"horas": 4.0}], fecha=SABADO)

    resumenes, fotos = _dos_pasadas(fabrica)

    for resumen, filas in zip(resumenes, fotos):
        assert resumen["extras_reclasificadas"] == 1
        assert filas[0] == (base, 0, 0.0, 4.0, False, None)
        extras = _extras(filas)
        assert len(extras) == 1
        assert extras[0][1:] == (0, 4.0, None, True, None)
