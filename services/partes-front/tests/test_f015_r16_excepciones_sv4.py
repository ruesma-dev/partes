# tests/test_f015_r16_excepciones_sv4.py
"""R16 en sv4 · el portal aplica las mismas excepciones que sv3.

Si sv3 calcula la jornada de un trabajador con una excepcion y el portal
no, el portal marcaria como incompleto un dia que sv3 da por completo:
justo el ruido que F-015 viene a quitar. El proveedor de sv4 es codigo
distinto del puerto de sv3 (uno lee con la sesion de un servicio, otro con
la del otro), pero la REGLA es la misma y sale del resolutor gemelo.

De la BBDD para arriba se ejercita de verdad: `list_jornadas_empleado`
contra SQLite en memoria con el ORM real.
"""
from __future__ import annotations

from datetime import date

from application.services.jornada_provider import JornadaEmpleadoProvider
from application.services.jornada_resolver import jornada_dia
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import (
    FabricaSesionSqlite,
    es_laborable_fake,
    sembrar_jornadas,
)

DNI = "12345678Z"
MAPA = {8.0: 40.0, 9.0: 42.0}

LUNES = date(2026, 3, 16)
VIERNES = date(2026, 3, 20)
X_JULIO = date(2026, 7, 8)
V_JULIO = date(2026, 7, 10)

PATRON_INTENSIVA = {
    "dni_norm": DNI, "patron": [7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0],
    "desde": "2026-07-01", "hasta": "2026-09-01",
}


def _proveedor(filas):
    fabrica = FabricaSesionSqlite()
    sembrar_jornadas(fabrica, filas)
    repositorio = ParteReviewRepository(fabrica)
    return JornadaEmpleadoProvider(repositorio.list_jornadas_empleado)


def _horas(proveedor, dia, *, candef, dni=DNI, no_laborables=()):
    return jornada_dia(
        dia, candef=candef, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=es_laborable_fake(no_laborables),
        excepcion=proveedor.excepcion_para(dni, dia),
    )


# --------------------------- excepcion con `S` -------------------------- #

def test_f015_r16_sv4_una_jornada_semanal_propia_manda() -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
    ])
    assert _horas(proveedor, LUNES, candef=10.0) == 10.0
    assert _horas(proveedor, VIERNES, candef=10.0) == 8.0


def test_f015_r16_sv4_la_excepcion_dice_de_donde_viene() -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01",
         "origen": "manual"},
    ])
    excepcion = proveedor.excepcion_para(DNI, VIERNES)
    assert (excepcion.semanal, excepcion.patron, excepcion.origen) == (
        48.0, None, "manual")


# -------------------------- excepcion con patron ------------------------ #

def test_f015_r16_sv4_un_patron_da_sus_horas() -> None:
    proveedor = _proveedor([PATRON_INTENSIVA])
    assert _horas(proveedor, X_JULIO, candef=9.0) == 7.0
    assert _horas(proveedor, V_JULIO, candef=9.0) == 7.0


def test_f015_r16_sv4_el_patron_no_da_horas_en_festivo() -> None:
    proveedor = _proveedor([PATRON_INTENSIVA])
    assert _horas(proveedor, X_JULIO, candef=9.0,
                  no_laborables={"2026-07-08"}) == 0.0


def test_f015_r16_sv4_un_patron_incompleto_se_ignora() -> None:
    """Hasta F-016 las filas se cargan a mano: solo vale el patron entero."""
    proveedor = _proveedor([
        {"dni_norm": DNI, "patron": [7.0, 7.0, 7.0, None, None, None, None],
         "desde": "2026-01-01"},
    ])
    assert proveedor.excepcion_para(DNI, VIERNES) is None
    assert _horas(proveedor, VIERNES, candef=9.0) == 6.0


# ------------------------------- vigencia ------------------------------- #

def test_f015_r16_sv4_fuera_de_la_vigencia_manda_el_mapa() -> None:
    proveedor = _proveedor([PATRON_INTENSIVA])
    assert proveedor.excepcion_para(DNI, VIERNES) is None
    assert _horas(proveedor, VIERNES, candef=9.0) == 6.0


def test_f015_r16_sv4_hasta_es_exclusivo() -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-03-16",
         "hasta": "2026-03-20"},
    ])
    assert proveedor.excepcion_para(DNI, date(2026, 3, 19)) is not None
    assert proveedor.excepcion_para(DNI, VIERNES) is None


def test_f015_r16_sv4_dos_vigencias_disjuntas_no_se_pisan() -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01",
         "hasta": "2026-07-01"},
        PATRON_INTENSIVA,
    ])
    assert _horas(proveedor, VIERNES, candef=10.0) == 8.0
    assert _horas(proveedor, V_JULIO, candef=10.0) == 7.0


def test_f015_r16_sv4_una_fila_desactivada_no_se_lee() -> None:
    """`is_active` falso es la papelera logica: el repositorio no la trae."""
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01",
         "is_active": False},
    ])
    assert proveedor.excepcion_para(DNI, VIERNES) is None


def test_f015_r16_sv4_la_fila_de_otro_dni_no_se_aplica() -> None:
    proveedor = _proveedor([
        {"dni_norm": "00000000T", "jornada_semanal": 48.0,
         "desde": "2026-01-01"},
    ])
    assert proveedor.excepcion_para(DNI, VIERNES) is None


def test_f015_r16_sv4_el_dni_se_normaliza(fake_dni="12345678-z") -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
    ])
    assert proveedor.excepcion_para(fake_dni, VIERNES) is not None


def test_f015_r16_sv4_sin_dni_no_hay_excepcion() -> None:
    proveedor = _proveedor([
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
    ])
    assert proveedor.excepcion_para(None, VIERNES) is None
    assert proveedor.excepcion_para("   ", VIERNES) is None


# --------------------------- coste de la lectura ------------------------ #

def test_f015_r16_sv4_la_tabla_se_lee_una_vez_por_ttl() -> None:
    llamadas: list[int] = []

    def _cargar():
        llamadas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(_cargar, ttl_seconds=600)
    for _ in range(5):
        proveedor.excepcion_para(DNI, VIERNES)
    assert len(llamadas) == 1


def test_f015_r16_sv4_pasado_el_ttl_se_vuelve_a_leer() -> None:
    llamadas: list[int] = []
    reloj = {"t": 1000.0}

    def _cargar():
        llamadas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(
        _cargar, ttl_seconds=600, reloj=lambda: reloj["t"])
    proveedor.excepcion_para(DNI, VIERNES)
    reloj["t"] += 601
    proveedor.excepcion_para(DNI, VIERNES)
    assert len(llamadas) == 2


def test_f015_r16_sv4_sin_dni_no_se_lee_la_tabla() -> None:
    llamadas: list[int] = []

    def _cargar():
        llamadas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(_cargar)
    assert proveedor.excepcion_para(None, VIERNES) is None
    assert llamadas == []
