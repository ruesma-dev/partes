# tests/test_f015_r20_computo_ultimo_laborable.py
"""R20 · el reparto ordinaria/extra usa la jornada del DIA.

Es el efecto util de F-015 y el motivo de todo lo demas. Hoy, un peon de
la cuadrilla con regimen de 42 h y candef 9 que trabaja 9-9-9-9-6 recibe
extra automatica todos los dias y una extra NEGATIVA de -3 el viernes:
las cuentas cuadran a fin de mes, pero cada parte miente. Con la jornada
del dia (9 de lunes a jueves, 6 el viernes) no se genera ni un split.

Lo que NO cambia (y se comprueba aqui): la rama de dia no laborable va
delante, el recorte sigue empezando por el registro de mayor id, la extra
automatica negativa sigue siendo UNA sobre el pivote, un dia sin horas
ordinarias no se normaliza y un recurso sin codigo de hora extra no se
toca.

Escenarios A, A', A'', B' y O de F-012 §4.
"""
from __future__ import annotations

from application.services.recurso_conciliador import RecursoConciliador
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

# Semana de referencia: 2026-03-16 (L) ... 2026-03-20 (V).
LUNES = 20260316
JUEVES = 20260319
VIERNES = 20260320


def _splits(regs, *, candef=9.0, no_laborables=(), con_extra=True,
            mapa=None):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set(no_laborables)),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
        mapa_semanal=mapa,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef, con_extra=con_extra),
    )


def _resumen(splits):
    return [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits]


# ------------------------- escenario A: la cuadrilla -------------------- #

def test_f015_r20_nueve_horas_un_lunes_cuadran() -> None:
    """L-J la jornada es el candef: 9 h no generan nada."""
    assert _splits([registro(1, fecha_int=LUNES, horas=9.0)]) == []


def test_f015_r20_seis_horas_un_viernes_cuadran() -> None:
    """Escenario A: el viernes la jornada es 42 - 36 = 6."""
    assert _splits([registro(1, fecha_int=VIERNES, horas=6.0)]) == []


def test_f015_r20_hoy_ese_viernes_generaria_extra_negativa() -> None:
    """Control del valor de la feature: con jornada plana serian -3."""
    assert _resumen(
        _splits([registro(1, fecha_int=VIERNES, horas=6.0)],
                mapa={9.0: 45.0})
    ) == [(1, 9.0, -3.0)]


def test_f015_r20_nueve_horas_un_viernes_dan_tres_extra() -> None:
    """Escenario A': hoy esas 3 h de mas se pierden."""
    assert _resumen(
        _splits([registro(1, fecha_int=VIERNES, horas=9.0)])
    ) == [(1, 6.0, 3.0)]


def test_f015_r20_cuatro_horas_un_viernes_dan_extra_negativa_de_dos() -> None:
    """Escenario A'': jornada incompleta de verdad, sobre 6 y no sobre 9."""
    assert _resumen(
        _splits([registro(1, fecha_int=VIERNES, horas=4.0)])
    ) == [(1, 6.0, -2.0)]


def test_f015_r20_la_semana_entera_de_la_cuadrilla_no_genera_nada() -> None:
    """9-9-9-9-6: el parte que escriben los encargados, sin un solo split."""
    regs = [registro(i + 1, fecha_int=LUNES + i, horas=h)
            for i, h in enumerate([9.0, 9.0, 9.0, 9.0, 6.0])]
    assert _splits(regs) == []


# --------------------------- con festivos ------------------------------- #

def test_f015_r20_con_el_viernes_festivo_el_jueves_de_6_cuadra() -> None:
    """El resto se corre al jueves: 6 h ese dia son jornada completa."""
    assert _splits([registro(1, fecha_int=JUEVES, horas=6.0)],
                   no_laborables={"2026-03-20"}) == []


def test_f015_r20_un_viernes_festivo_trabajado_va_entero_a_extra() -> None:
    """Escenario B': la rama de dia no laborable sigue yendo delante."""
    assert _resumen(
        _splits([registro(1, fecha_int=VIERNES, horas=5.0)],
                no_laborables={"2026-03-20"})
    ) == [(1, 0.0, 5.0)]


def test_f015_r20_un_miercoles_festivo_no_cambia_el_viernes() -> None:
    """El festivo entre semana CUENTA como jornada (lectura A del humano)."""
    assert _splits([registro(1, fecha_int=VIERNES, horas=6.0)],
                   no_laborables={"2026-03-18"}) == []


# ------------------- el resto del algoritmo, intacto -------------------- #

def test_f015_r20_el_recorte_empieza_por_el_registro_de_mayor_id() -> None:
    regs = [registro(1, fecha_int=VIERNES, horas=5.0),
            registro(2, fecha_int=VIERNES, horas=5.0)]
    assert _resumen(_splits(regs)) == [(2, 1.0, 4.0)]


def test_f015_r20_el_exceso_desborda_al_registro_anterior() -> None:
    regs = [registro(1, fecha_int=VIERNES, horas=5.0),
            registro(2, fecha_int=VIERNES, horas=5.0),
            registro(3, fecha_int=VIERNES, horas=5.0)]
    assert _resumen(_splits(regs)) == [(3, 0.0, 5.0), (2, 1.0, 4.0)]


def test_f015_r20_las_extras_explicitas_no_se_tocan() -> None:
    """6 ordinarias + 2 extra un viernes de jornada 6: el dia cuadra."""
    regs = [registro(1, fecha_int=VIERNES, horas=6.0),
            registro(2, fecha_int=VIERNES, horas=2.0, tipo="extra")]
    assert _splits(regs) == []


def test_f015_r20_con_extras_explicitas_la_negativa_sale_sobre_la_ordinaria(
) -> None:
    """4 ordinarias + 2 extra un viernes de jornada 6: la ordinaria sube a
    6 y la extra automatica sale -2; la extra explicita no se toca."""
    regs = [registro(1, fecha_int=VIERNES, horas=4.0),
            registro(2, fecha_int=VIERNES, horas=2.0, tipo="extra")]
    assert _resumen(_splits(regs)) == [(1, 6.0, -2.0)]


def test_f015_r20_un_dia_sin_horas_ordinarias_no_se_normaliza() -> None:
    regs = [registro(1, fecha_int=VIERNES, horas=4.0, tipo="extra")]
    assert _splits(regs) == []


def test_f015_r20_agrupa_por_recurso_y_dia_across_obras() -> None:
    """4 h en una obra + 4 h en otra el viernes = 8, con jornada 6 -> 2 extra."""
    regs = [registro(1, fecha_int=VIERNES, horas=4.0, obra_ide=10),
            registro(2, fecha_int=VIERNES, horas=4.0, obra_ide=20)]
    assert _resumen(_splits(regs)) == [(2, 2.0, 2.0)]


# ----------------------- escenario O: sin hora extra -------------------- #

def test_f015_r20_recurso_sin_codigo_de_hora_extra_no_se_toca() -> None:
    """Aunque la jornada del dia cambie: sin codigo extra no hay a donde
    imputar, y hoy se respetan las horas del parte tal cual."""
    assert _splits([registro(1, fecha_int=VIERNES, horas=9.0)],
                   con_extra=False) == []


def test_f015_r20_recurso_sin_reshor_no_se_normaliza() -> None:
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()),
    )
    regs = [registro(1, fecha_int=VIERNES, horas=9.0)]
    assert conciliador._reclasificar_extras_jornada(regs, {1: 501}, {}) == []


# --------------------------- con excepcion ------------------------------ #

def test_f015_r20_una_excepcion_de_jornada_cambia_el_reparto() -> None:
    """R16 de punta a punta: `S = 48` con candef 10 -> viernes de 8 h."""
    from domain.ports.jornada_empleado_port import JornadaEmpleadoRow
    from tests.dobles import JornadasFake

    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()),
        jornadas=JornadasFake([
            JornadaEmpleadoRow(dni_norm="12345678Z", jornada_semanal=48.0,
                               desde="2026-01-01"),
        ]),
    )
    regs = [registro(1, fecha_int=VIERNES, horas=8.0)]
    assert conciliador._reclasificar_extras_jornada(
        regs, {1: 501}, indice_reshor(501, candef=10.0)) == []
