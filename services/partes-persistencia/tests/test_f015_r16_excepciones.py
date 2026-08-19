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


# ================= refuerzo tras la campana de mutacion ================= #
# Lo que dejaron al descubierto los mutantes supervivientes: el adaptador
# real no tenia ni un test, `Excepcion.valida()` no tenia bordes y las
# vigencias solapadas no se probaban.

import dataclasses  # noqa: E402

import pytest  # noqa: E402
from application.services.jornada_resolver import (  # noqa: E402
    DetalleJornada,
    Excepcion,
)
from infrastructure.database.sqlalchemy_jornada_repository import (  # noqa: E402
    SqlAlchemyJornadaRepository,
)
from tests.dobles import FabricaSesionSqlite, sembrar_jornadas  # noqa: E402

PATRON_7 = (7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0)


# --------------------- el adaptador contra la BBDD ---------------------- #

def _repositorio(filas):
    fabrica = FabricaSesionSqlite()
    sembrar_jornadas(fabrica, filas)
    return SqlAlchemyJornadaRepository(fabrica)


def test_f015_r16_el_adaptador_lee_las_filas_activas() -> None:
    filas = _repositorio([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
    ]).fetch_jornadas()
    assert [(f.dni_norm, f.jornada_semanal, f.patron, f.desde, f.hasta,
             f.origen) for f in filas] == [
        (DNI, 48.0, None, "2026-01-01", None, "manual")]


def test_f015_r16_el_adaptador_NO_lee_las_filas_desactivadas() -> None:
    """`is_active` es la papelera logica: una fila retirada no puede seguir
    cambiando el reparto de horas de nadie."""
    assert _repositorio([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "is_active": False},
    ]).fetch_jornadas() == []


def test_f015_r16_el_adaptador_solo_deja_fuera_las_desactivadas() -> None:
    filas = _repositorio([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "is_active": True},
        {"dni_norm": "00000000T", "jornada_semanal": 35.0,
         "is_active": False},
    ]).fetch_jornadas()
    assert [f.dni_norm for f in filas] == [DNI]


def test_f015_r16_el_adaptador_arma_el_patron_con_las_siete_horas() -> None:
    filas = _repositorio([
        {"dni_norm": DNI, "patron": list(PATRON_7), "desde": "2026-07-01",
         "hasta": "2026-09-01"},
    ]).fetch_jornadas()
    assert filas[0].patron == PATRON_7
    assert filas[0].jornada_semanal is None
    assert (filas[0].desde, filas[0].hasta) == ("2026-07-01", "2026-09-01")


def test_f015_r16_el_adaptador_ignora_un_patron_a_medias() -> None:
    """Con una sola hora a NULL no hay patron: se entiende "solo semanal"."""
    filas = _repositorio([
        {"dni_norm": DNI, "jornada_semanal": 48.0,
         "patron": [7.0, 7.0, 7.0, 7.0, 7.0, 0.0, None]},
    ]).fetch_jornadas()
    assert filas[0].patron is None
    assert filas[0].jornada_semanal == 48.0


def test_f015_r16_el_adaptador_conserva_el_origen_de_la_fila() -> None:
    """`origen` dira algun dia si la excepcion vino de Sigrid o de Sesame."""
    filas = _repositorio([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "origen": "sigrid"},
    ]).fetch_jornadas()
    assert filas[0].origen == "sigrid"


def test_f015_r16_el_adaptador_normaliza_el_dni() -> None:
    filas = _repositorio([
        {"dni_norm": "12345678-z", "jornada_semanal": 48.0},
    ]).fetch_jornadas()
    assert filas[0].dni_norm == "12345678Z"


def test_f015_r16_el_adaptador_con_la_tabla_vacia_devuelve_lista_vacia(
) -> None:
    assert _repositorio([]).fetch_jornadas() == []


# ------------------------ `Excepcion.valida()` -------------------------- #

def test_f015_r16_una_excepcion_sin_nada_no_es_valida() -> None:
    """Ni jornada semanal ni patron: no dice nada, no se puede aplicar."""
    assert Excepcion().valida() is False
    assert Excepcion(semanal=None, patron=None).valida() is False


@pytest.mark.parametrize("semanal, esperado", [
    (0.0, False),      # el limite inferior es ABIERTO
    (0.5, True),
    (42.0, True),
    (168.0, True),     # 24 x 7: el limite superior es CERRADO
    (168.1, False),
    (-1.0, False),
])
def test_f015_r16_los_bordes_de_la_jornada_semanal(semanal, esperado) -> None:
    assert Excepcion(semanal=semanal).valida() is esperado


@pytest.mark.parametrize("horas, esperado", [
    ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), True),
    ((24.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), True),   # 24 h es el limite
    ((24.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), False),
    ((-1.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0), False),
    ((30.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0), False),
    ((7.0, 7.0, 7.0, 7.0, 7.0, 0.0), False),        # solo 6 valores
    ((7.0,) * 8, False),                            # 8 valores
])
def test_f015_r16_los_bordes_del_patron(horas, esperado) -> None:
    assert Excepcion(patron=horas).valida() is esperado


def test_f015_r16_un_patron_con_un_hueco_no_es_valido() -> None:
    assert Excepcion(
        patron=(7.0, 7.0, 7.0, 7.0, 7.0, 0.0, None)).valida() is False


def test_f015_r16_el_patron_manda_sobre_la_semanal_al_validar() -> None:
    """Con patron valido, la semanal ya no se mira (no se aplica)."""
    assert Excepcion(semanal=999.0, patron=PATRON_7).valida() is True


def test_f015_r16_una_hora_del_patron_fuera_de_rango_anula_la_fila() -> None:
    """De punta a punta: la fila mala no cambia el reparto de nadie."""
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, patron=(30.0, 7.0, 7.0, 7.0, 7.0,
                                                 0.0, 0.0),
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, VIERNES, candef=9.0) == 6.0


# ----------------- vigencias solapadas: gana la mas nueva --------------- #

def test_f015_r16_con_dos_vigencias_solapadas_gana_la_mas_reciente() -> None:
    """F-016 impedira el solape; hasta entonces las carga el humano a mano y
    el criterio tiene que ser determinista: la que alguien anadio despues."""
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01"),
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=30.0,
                           desde="2026-03-01"),
    ])
    # Con candef 10: la de 48 daria 8 el viernes; la de 30, 0.
    assert _horas(conciliador, VIERNES, candef=10.0) == 0.0


def test_f015_r16_el_orden_no_depende_de_como_lleguen_las_filas() -> None:
    conciliador = _conciliador([
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=30.0,
                           desde="2026-03-01"),
        JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0,
                           desde="2026-01-01"),
    ])
    assert _horas(conciliador, VIERNES, candef=10.0) == 0.0


# ----------------- las dataclases son inmutables a proposito ------------ #

@pytest.mark.parametrize("instancia", [
    Excepcion(semanal=42.0),
    DetalleJornada(horas=6.0, candef_efectivo=9.0, semanal=42.0,
                   origen="mapa", ultimo_laborable=True),
    JornadaEmpleadoRow(dni_norm=DNI),
])
def test_f015_r16_las_dataclases_son_inmutables(instancia) -> None:
    """Se comparten entre grupos y entre dias dentro de una pasada: si se
    pudieran mutar, el reparto de un dia contaminaria al del siguiente."""
    campo = dataclasses.fields(instancia)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instancia, campo, "tocado")
