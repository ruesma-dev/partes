# tests/test_f015_r22_sin_dni.py
"""R22 · un grupo sin DNI no puede romper nada.

El calendario y la excepcion se resuelven por el DNI del GRUPO (el primer
`empleado_dni` no vacio, el mismo criterio que `_es_no_laborable` desde
F-003). Hay lineas sin DNI —trabajador sin casar contra `emp`— y esas
tienen que caer al calendario por defecto y a la jornada del mapa, sin
excepcion y sin fallar: sv3 es best-effort, no puede dejar de conciliar
un parte porque a una linea le falte el DNI.
"""
from __future__ import annotations

import pytest

from application.services.recurso_conciliador import RecursoConciliador
from domain.ports.jornada_empleado_port import JornadaEmpleadoRow
from tests.dobles import (
    CalendarioFake,
    JornadasFake,
    LookupFake,
    RepositorioFake,
    registro,
)

VIERNES = 20260320


def _conciliador(puerto=None, calendario=None):
    return RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=calendario if calendario is not None
        else CalendarioFake(set()),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0, jornadas=puerto,
    )


def test_f015_r22_sin_dni_la_jornada_sale_del_mapa() -> None:
    conciliador = _conciliador()
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni=None)]
    detalle = conciliador._detalle_jornada(VIERNES, regs, 9.0)
    assert (detalle.horas, detalle.origen) == (6.0, "mapa")


def test_f015_r22_sin_dni_no_se_consulta_la_tabla_de_excepciones() -> None:
    """Un DNI vacio no casa con ninguna fila: preguntar seria trabajo tonto."""
    puerto = JornadasFake([
        JornadaEmpleadoRow(dni_norm="", jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    conciliador = _conciliador(puerto)
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni=None)]
    detalle = conciliador._detalle_jornada(VIERNES, regs, 9.0)
    assert puerto.llamadas == 0
    assert detalle.origen == "mapa"


def test_f015_r22_sin_dni_se_usa_el_calendario_por_defecto() -> None:
    """El puerto recibe `dni=None`, que es lo que ya hacia F-003."""
    calendario = CalendarioFake(set())
    conciliador = _conciliador(calendario=calendario)
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni=None)]
    conciliador._detalle_jornada(VIERNES, regs, 9.0)
    assert all(dni is None for _, dni in calendario.consultas)


def test_f015_r22_el_dni_del_grupo_es_el_primero_no_vacio() -> None:
    calendario = CalendarioFake(set())
    conciliador = _conciliador(calendario=calendario)
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni=None),
            registro(2, fecha_int=VIERNES, horas=1.0, dni="12345678Z")]
    conciliador._detalle_jornada(VIERNES, regs, 9.0)
    assert {dni for _, dni in calendario.consultas} == {"12345678Z"}


def test_f015_r22_un_dni_en_blanco_cuenta_como_sin_dni() -> None:
    puerto = JornadasFake([])
    conciliador = _conciliador(puerto)
    regs = [registro(1, fecha_int=VIERNES, horas=1.0, dni="   ")]
    detalle = conciliador._detalle_jornada(VIERNES, regs, 9.0)
    assert puerto.llamadas == 0
    assert detalle.horas == 6.0


# ================= refuerzo tras la campana de mutacion ================= #
# La rama "sin fecha utilizable" de `_detalle_jornada` no la ejercitaba
# nadie: sobrevivian mutantes que rompian su jornada plana. Es una rama
# defensiva, pero alcanzable (un registro con `fecha_int` a NULL o basura
# existe en la base) y decide horas.

@pytest.mark.parametrize("fecha_int", [None, 0, -1, 20261301, 20260232, "x"])
def test_f015_r22_sin_fecha_utilizable_la_semanal_sale_del_mapa(fecha_int) -> None:
    conciliador = _conciliador()
    regs = [registro(1, fecha_int=fecha_int, horas=1.0)]
    detalle = conciliador._detalle_jornada(fecha_int, regs, 9.0)
    assert (detalle.horas, detalle.candef_efectivo, detalle.semanal,
            detalle.origen, detalle.ultimo_laborable) == (
        9.0, 9.0, 42.0, "mapa", False)


def test_f015_r22_sin_fecha_el_candef_invalido_sigue_cayendo_a_8() -> None:
    conciliador = _conciliador()
    regs = [registro(1, fecha_int=None, horas=1.0)]
    detalle = conciliador._detalle_jornada(None, regs, 0.0)
    assert (detalle.horas, detalle.semanal) == (8.0, 40.0)


def test_f015_r22_sin_fecha_un_candef_fuera_del_mapa_sigue_siendo_plano(
) -> None:
    conciliador = _conciliador()
    regs = [registro(1, fecha_int=None, horas=1.0)]
    detalle = conciliador._detalle_jornada(None, regs, 10.0)
    assert (detalle.horas, detalle.semanal, detalle.origen) == (
        10.0, 50.0, "plana")


def test_f015_r22_sin_fecha_no_se_consulta_el_calendario() -> None:
    calendario = CalendarioFake(set())
    conciliador = _conciliador(calendario=calendario)
    regs = [registro(1, fecha_int=None, horas=1.0)]
    conciliador._detalle_jornada(None, regs, 9.0)
    assert calendario.consultas == []
