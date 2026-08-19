# tests/test_f015_r16_excepciones.py
"""R16 · excepciones de jornada por trabajador (`empleado_jornada`).

El mapa candef -> jornada semanal resuelve el caso general, pero hay
trabajadores cuyo regimen no cabe en el candef de Sigrid: una jornada
semanal distinta, o directamente un patron de horas por dia (la
intensiva). Para esos, una fila en `empleado_jornada` con vigencia.

Lo que se fija aqui es la RESOLUCION de la excepcion en sv3: que se
aplique la fila vigente, que una fila fuera de vigencia o desactivada no
pinte nada, y que dos vigencias disjuntas del mismo DNI no se pisen. La
tabla nace vacia, asi que el camino normal —sin excepcion— es el que mas
importa que no cambie.

Sin BBDD: la tabla entra por un doble del puerto.
"""
from __future__ import annotations

from application.services.recurso_conciliador import RecursoConciliador
from domain.ports.jornada_empleado_port import JornadaEmpleadoRow
from tests.dobles import (
    CalendarioFake,
    JornadasFake,
    LookupFake,
    RepositorioFake,
    registro,
)

DNI = "12345678Z"

# Semana de referencia de marzo (L 16 ... V 20) y una de julio (L 6 ... V 10).
LUNES = 20260316
VIERNES = 20260320
L_JULIO = 20260706
X_JULIO = 20260708
V_JULIO = 20260710


def _conciliador(filas=None, *, no_laborables=(), fallo=None):
    return RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set(no_laborables)),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
        jornadas=JornadasFake(filas, fallo=fallo),
    )


def _horas(conciliador, fecha_int, *, candef, dni=DNI):
    regs = [registro(1, fecha_int=fecha_int, horas=1.0, dni=dni)]
    return conciliador._detalle_jornada(fecha_int, regs, candef).horas


def _detalle(conciliador, fecha_int, *, candef, dni=DNI):
    regs = [registro(1, fecha_int=fecha_int, horas=1.0, dni=dni)]
    return conciliador._detalle_jornada(fecha_int, regs, candef)


# --------------------------- excepcion con `S` -------------------------- #

def test_f015_r16_una_jornada_semanal_propia_manda_sobre_el_mapa() -> None:
    """Escenario Q: `S = 48` con candef 10 -> el viernes vale 8."""
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, LUNES, candef=10.0) == 10.0
    assert _horas(conciliador, VIERNES, candef=10.0) == 8.0


def test_f015_r16_el_detalle_dice_que_la_S_viene_de_una_excepcion() -> None:
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    detalle = _detalle(conciliador, VIERNES, candef=10.0)
    assert (detalle.semanal, detalle.origen, detalle.ultimo_laborable) == (
        48.0, "excepcion", True)


# -------------------------- excepcion con patron ------------------------ #

PATRON_INTENSIVA = JornadaEmpleadoRow(
    dni_norm=DNI, patron=(7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0),
    desde="2026-07-01", hasta="2026-09-01",
)


def test_f015_r16_un_patron_da_sus_horas_cada_dia_laborable() -> None:
    """Escenario R: intensiva 7x5 en julio, sin regla del resto."""
    conciliador = _conciliador([PATRON_INTENSIVA])
    for fecha in (L_JULIO, X_JULIO, V_JULIO):
        assert _horas(conciliador, fecha, candef=9.0) == 7.0


def test_f015_r16_el_patron_no_da_horas_en_festivo() -> None:
    conciliador = _conciliador([PATRON_INTENSIVA],
                               no_laborables={"2026-07-08"})
    assert _horas(conciliador, X_JULIO, candef=9.0) == 0.0
    assert _horas(conciliador, V_JULIO, candef=9.0) == 7.0


def test_f015_r16_el_patron_no_aplica_la_regla_del_resto() -> None:
    """El viernes de la intensiva vale 7, no `35 - 28`."""
    conciliador = _conciliador([PATRON_INTENSIVA])
    detalle = _detalle(conciliador, V_JULIO, candef=9.0)
    assert (detalle.horas, detalle.origen, detalle.ultimo_laborable) == (
        7.0, "excepcion", False)


# ------------------------------- vigencia ------------------------------- #

def test_f015_r16_fuera_de_la_vigencia_manda_el_mapa() -> None:
    """En marzo, la fila de julio no existe para el calculo."""
    conciliador = _conciliador([PATRON_INTENSIVA])
    assert _horas(conciliador, VIERNES, candef=9.0) == 6.0
    assert _horas(conciliador, LUNES, candef=9.0) == 9.0


def test_f015_r16_hasta_es_exclusivo() -> None:
    """`hasta = 2026-09-01` significa "hasta el 31 de agosto incluido"."""
    fila = JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                              desde="2026-03-16", hasta="2026-03-20")
    conciliador = _conciliador([fila])
    # El 19 (jueves) esta dentro; el 20 (viernes) ya no.
    assert _detalle(conciliador, 20260319, candef=10.0).origen == "excepcion"
    assert _detalle(conciliador, VIERNES, candef=10.0).origen == "plana"


def test_f015_r16_desde_es_inclusivo() -> None:
    fila = JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                              desde="2026-03-16")
    conciliador = _conciliador([fila])
    assert _detalle(conciliador, LUNES, candef=10.0).origen == "excepcion"
    assert _detalle(conciliador, 20260313, candef=10.0).origen == "plana"


def test_f015_r16_dos_vigencias_disjuntas_no_se_pisan() -> None:
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01", hasta="2026-07-01"),
        PATRON_INTENSIVA,
    ])
    assert _horas(conciliador, VIERNES, candef=10.0) == 8.0     # marzo -> S 48
    assert _horas(conciliador, V_JULIO, candef=10.0) == 7.0     # julio -> patron


def test_f015_r16_una_fila_desactivada_se_ignora() -> None:
    """`is_active` falso: el adaptador no la trae, pero si llegara igual."""
    conciliador = _conciliador([])
    assert _detalle(conciliador, VIERNES, candef=10.0).origen == "plana"


def test_f015_r16_la_fila_de_otro_dni_no_se_aplica() -> None:
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm="00000000T", jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    assert _detalle(conciliador, VIERNES, candef=10.0).origen == "plana"


def test_f015_r16_el_dni_se_normaliza_antes_de_buscar() -> None:
    """En la tabla el DNI va normalizado; en el parte puede venir con guion."""
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm="12345678Z", jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, VIERNES, candef=10.0, dni="12345678-z") == 8.0


# ---------------------- filas mal cargadas: se ignoran ------------------ #

def test_f015_r16_un_patron_incompleto_se_ignora() -> None:
    """Hasta F-016 las filas se cargan por SQL a mano: el resolutor no se fia."""
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, patron=(7.0, 7.0, 7.0),
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, VIERNES, candef=9.0) == 6.0


def test_f015_r16_una_jornada_semanal_absurda_se_ignora() -> None:
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=0.0,
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, VIERNES, candef=9.0) == 6.0


# --------------------------- coste de la lectura ------------------------ #

def test_f015_r16_la_tabla_se_lee_una_vez_por_pasada() -> None:
    puerto = JornadasFake([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), jornadas=puerto,
    )
    for fecha in (LUNES, VIERNES, L_JULIO):
        _horas(conciliador, fecha, candef=10.0)
    assert puerto.llamadas == 1


def test_f015_r16_sin_puerto_cableado_no_hay_excepciones() -> None:
    """El default (`jornadas=None`) es lo que usan todos los tests previos."""
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()),
    )
    regs = [registro(1, fecha_int=VIERNES, horas=1.0)]
    assert conciliador._detalle_jornada(VIERNES, regs, 9.0).origen == "mapa"
