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

import pytest
from sqlalchemy import select

from application.services.recurso_conciliador import (
    RecursoConciliador,
    _congelado,
)
from application.services.seleccion_sigrid import ResolucionRecurso
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    registro,
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


# =============== R10 · congelada por pareja = congelada ================= #
# Directo sobre el conciliador, con el repositorio en memoria de siempre.

def _reg(rid: int, horas: float, *, tipo: str = "normal",
         por_pareja: bool = False, estado: str | None = None) -> dict:
    r = registro(rid, fecha_int=20261001, horas=horas, tipo=tipo,
                 sigrid_estado=estado)
    r.update(recurso_ide=RECURSO, congelada_por_pareja=por_pareja)
    return r


class IndiceOtro(IndiceFijo):
    """Elige OTRO recurso: si una linea se re-resuelve, se nota."""

    def elegir_recurso(self, *args, **kwargs):  # noqa: ARG002
        return ResolucionRecurso(ide=777, motivo="ok")


def _conciliar_fake(registros, indice=None) -> RepositorioFake:
    repo = RepositorioFake(registros)
    RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(RECURSO) + reshor_par(777)),
        calendario=CalendarioFake(set(NO_LABORABLES)),
        indice_provider=lambda: indice or IndiceFijo(),
    ).conciliar_todos()
    return repo


def test_f037_r10_la_marca_congela_como_el_estado() -> None:
    assert _congelado({"congelada_por_pareja": True}) is True
    assert _congelado({"congelada_por_pareja": False}) is False
    assert _congelado({}) is False
    assert _congelado({"sigrid_estado": "registrado",
                       "congelada_por_pareja": False}) is True


def test_f037_r10_no_re_resuelve_su_recurso() -> None:
    repo = _conciliar_fake([_reg(1, 8.0, por_pareja=True),
                            _reg(2, 8.0)], IndiceOtro())
    assert [m["registro_id"] for m in repo.matches] == [2]
    assert repo.matches[0]["recurso_ide"] == 777


def test_f037_r10_suma_en_el_dia_y_no_es_candidata_a_recorte() -> None:
    """Base marcada (id 5, 8 h) + su extra congelada (2 h) + libre (id 1,
    3 h): el recorte de 3 h cae entero en la libre aunque la base tenga el
    id mayor."""
    repo = _conciliar_fake([
        _reg(1, 3.0),
        _reg(5, 8.0, por_pareja=True),
        _reg(6, 2.0, tipo="extra", estado="registrado"),
    ])
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in repo.splits] == [(1, 0.0, 3.0)]


def test_f037_r10_no_es_pivote_de_una_jornada_incompleta() -> None:
    """6 h en el dia con jornada 8: sube la libre, no la base marcada."""
    repo = _conciliar_fake([_reg(1, 2.0), _reg(5, 4.0, por_pareja=True)])
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in repo.splits] == [(1, 4.0, -2.0)]


def test_f037_r10_si_solo_queda_la_marcada_no_se_genera_nada(caplog) -> None:
    import logging

    with caplog.at_level(logging.WARNING):
        repo = _conciliar_fake([_reg(5, 4.0, por_pareja=True)])
    assert repo.splits == []
    assert "CONGELADAS" in caplog.text


# ============ R11-R15 · dos pasadas sobre la base de memoria ============ #

def _base(horas, horas_orig, estado=None, *, li=0) -> dict:
    return {"horas": horas, "horas_orig": horas_orig, "estado": estado,
            "line_index": li, "empleado_line_no": 1, "recurso_ide": RECURSO}


def _extra(horas, estado=None, *, li=0) -> dict:
    return {"horas": horas, "tipo": "extra", "extra_auto": True,
            "estado": estado, "line_index": li, "empleado_line_no": 1,
            "recurso_ide": RECURSO}


def _sin_cambios_y_sin_extras_nuevas(fabrica, esperado) -> None:
    """El matiz del humano: ni una extra nueva en ninguna pasada."""
    resumenes, fotos = _dos_pasadas(fabrica)
    for resumen, filas in zip(resumenes, fotos):
        assert resumen["extras_reclasificadas"] == 0
        assert filas == esperado


def test_f037_r11_laborable_base_omitida_y_extra_registrada() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = sembrar_lineas(fabrica, [_base(8.0, 10.0, "omitido"),
                                           _extra(2.0, "registrado")],
                                 fecha=JUEVES)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 8.0, 10.0, False, "omitido"),
        (extra, 0, 2.0, None, True, "registrado"),
    ])


def test_f037_r12_no_laborable_base_de_cero_horas_y_extra_registrada() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = sembrar_lineas(fabrica, [_base(0.0, 4.0, "omitido"),
                                           _extra(4.0, "registrado")],
                                 fecha=SABADO)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 0.0, 4.0, False, "omitido"),
        (extra, 0, 4.0, None, True, "registrado"),
    ])


def test_f037_r13_laborable_el_duplicado_se_borra_y_no_vuelve() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra, _dup = sembrar_lineas(fabrica, [
        _base(8.0, 10.0, "omitido"), _extra(2.0, "registrado"), _extra(2.0),
    ], fecha=JUEVES)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 8.0, 10.0, False, "omitido"),
        (extra, 0, 2.0, None, True, "registrado"),
    ])


def test_f037_r13_no_laborable_el_duplicado_se_borra_y_no_vuelve() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra, _dup = sembrar_lineas(fabrica, [
        _base(0.0, 4.0, "omitido"), _extra(4.0, "registrado"), _extra(4.0),
    ], fecha=SABADO)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 0.0, 4.0, False, "omitido"),
        (extra, 0, 4.0, None, True, "registrado"),
    ])


def test_f037_r14_base_registrada_conserva_su_extra_sin_estado() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = sembrar_lineas(fabrica, [_base(8.0, 10.0, "registrado"),
                                           _extra(2.0)], fecha=JUEVES)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 8.0, 10.0, False, "registrado"),
        (extra, 0, 2.0, None, True, None),
    ])


def test_f037_r14_base_registrada_conserva_su_extra_en_error() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = sembrar_lineas(fabrica, [_base(8.0, 10.0, "registrado"),
                                           _extra(2.0, "error")],
                                 fecha=JUEVES)
    _sin_cambios_y_sin_extras_nuevas(fabrica, [
        (base, 0, 8.0, 10.0, False, "registrado"),
        (extra, 0, 2.0, None, True, "error"),
    ])


@pytest.mark.parametrize("libre_primero", [True, False])
def test_f037_r15_dia_mixto_el_ajuste_cae_solo_en_la_linea_libre(
        libre_primero: bool) -> None:
    """Pareja congelada (8 + 2) y una linea libre de 3 h del mismo recurso
    y dia: la pareja cuenta una vez (10 h) y las 3 h de la libre pasan a
    extra. Con la libre sembrada antes, la base tiene el id mayor y, sin
    F-037, seria la primera candidata a recorte."""
    fabrica = FabricaSesionSqlite()
    pareja = [_base(8.0, 10.0, "omitido"), _extra(2.0, "registrado")]
    libre = [{"horas": 3.0, "line_index": 1, "empleado_line_no": 1}]
    ids = sembrar_lineas(fabrica, libre + pareja if libre_primero
                         else pareja + libre, fecha=JUEVES)
    id_libre, base, extra = ((ids[0], ids[1], ids[2]) if libre_primero
                             else (ids[2], ids[0], ids[1]))

    resumenes, fotos = _dos_pasadas(fabrica)

    for resumen, filas in zip(resumenes, fotos):
        assert resumen["extras_reclasificadas"] == 1
        por_id = {f[0]: f for f in filas}
        assert por_id[base] == (base, 0, 8.0, 10.0, False, "omitido")
        assert por_id[extra] == (extra, 0, 2.0, None, True, "registrado")
        assert por_id[id_libre] == (id_libre, 1, 0.0, 3.0, False, None)
        nuevas = [f for f in filas if f[4] and f[0] != extra]
        assert len(nuevas) == 1
        assert nuevas[0][1:] == (1, 3.0, None, True, None)
