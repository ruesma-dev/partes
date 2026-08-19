# tests/test_f015_r24_avisos.py
"""R24 · el portal avisa contra la jornada del DIA, no contra el candef.

Es el ruido que la cuadrilla ve todas las semanas: con candef 9 y jornada
plana, el viernes de 6 h sale marcado como «jornada incompleta» aunque el
trabajador haya hecho su semana completa de 42 h. Y al reves: un lunes de
8 h, que SI le falta una hora, hoy no se marca si el candef es 8.

Con la jornada del dia, el aviso dice lo que un encargado esperaria. La
propiedad que no se puede romper es la de siempre: con candef 8 el
conjunto de dias marcados tiene que ser EXACTAMENTE el de antes de F-015.

TestClient + SQLite en memoria + doble de calendario: ni red ni Sesame ni
PostgreSQL, y `Settings(_env_file=None)` para no leer el `.env` de nadie.
"""
from __future__ import annotations

from datetime import date

import pytest
from application.services.calendario_provider import DiaCalendario
from application.services.jornada_provider import JornadaEmpleadoProvider
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias

# Semana de referencia: 2026-03-16 (L) ... 2026-03-20 (V).
LUNES = "2026-03-16"
MARTES = "2026-03-17"
JUEVES = "2026-03-19"
VIERNES = "2026-03-20"


class CalendarioFake:
    """Doble del `CalendarioProvider`: festivos por fecha, para todos."""

    def __init__(self, festivos=()) -> None:
        self._festivos = set(festivos)
        self.activo = True

    def holiday_name_para(self, dni):
        def _nombre(d: date) -> str | None:
            return "Fiesta de prueba" if d.isoformat() in self._festivos else None
        return _nombre

    def dia(self, d: date, dni):
        festivo = d.isoformat() in self._festivos
        finde = d.weekday() >= 5
        return DiaCalendario(
            fecha=d.isoformat(), laborable=not (finde or festivo),
            fin_de_semana=finde, festivo=festivo,
            festivo_nombre="Fiesta de prueba" if festivo else None,
            fiable=True,
        )

    def jornada_contrato(self, dni):
        return None

    def fiable_para(self, consultas):
        for _ in consultas:
            pass
        return True


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _cliente(dias, *, festivos=(), excepciones=(), **kw):
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, dias, **kw)
    app = build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(fabrica),
        calendario_provider=CalendarioFake(festivos),
        jornada_provider=JornadaEmpleadoProvider(lambda: list(excepciones)),
    )
    return TestClient(app)


def _incompletos_trabajador(dias, **kw) -> set[str]:
    respuesta = _cliente(dias, **kw).get(
        "/trabajadores/emp-77?period=2026-03&modo=natural")
    assert respuesta.status_code == 200
    return respuesta.context["dias_incompletos"]


def _incompletos_obra(dias, **kw) -> set[str]:
    respuesta = _cliente(dias, **kw).get(
        "/obras/obr-10?period=2026-03&modo=natural")
    assert respuesta.status_code == 200
    return respuesta.context["incompletos"]


# --------------------- vista trabajador (candef 9) ---------------------- #

def test_f015_r24_el_viernes_de_6_horas_no_es_incompleto() -> None:
    """Escenario A: 42 - 36 = 6 es la jornada de ese viernes."""
    assert _incompletos_trabajador([
        {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
    ]) == set()


def test_f015_r24_un_viernes_de_4_horas_si_es_incompleto() -> None:
    """Escenario A'': le faltan 2 h de las 6 que tocaban."""
    assert _incompletos_trabajador([
        {"fecha": VIERNES, "horas": 4.0, "candef": 9.0},
    ]) == {VIERNES}


def test_f015_r24_un_lunes_de_8_horas_si_es_incompleto() -> None:
    """Con candef 9, un lunes de 8 h le falta una hora de verdad."""
    assert _incompletos_trabajador([
        {"fecha": LUNES, "horas": 8.0, "candef": 9.0},
    ]) == {LUNES}


def test_f015_r24_un_lunes_de_9_horas_esta_completo() -> None:
    assert _incompletos_trabajador([
        {"fecha": LUNES, "horas": 9.0, "candef": 9.0},
    ]) == set()


def test_f015_r24_la_semana_de_la_cuadrilla_no_marca_ningun_dia() -> None:
    """9-9-9-9-6: el parte que escriben, sin un solo aviso."""
    dias = [
        {"fecha": LUNES, "horas": 9.0, "candef": 9.0},
        {"fecha": MARTES, "horas": 9.0, "candef": 9.0},
        {"fecha": "2026-03-18", "horas": 9.0, "candef": 9.0},
        {"fecha": JUEVES, "horas": 9.0, "candef": 9.0},
        {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
    ]
    assert _incompletos_trabajador(dias) == set()


def test_f015_r24_con_el_viernes_festivo_el_jueves_de_6_no_avisa() -> None:
    """El resto se corre al jueves: 6 h ese dia son jornada completa."""
    assert _incompletos_trabajador(
        [{"fecha": JUEVES, "horas": 6.0, "candef": 9.0}],
        festivos={VIERNES},
    ) == set()


def test_f015_r24_con_el_viernes_festivo_el_jueves_de_5_si_avisa() -> None:
    assert _incompletos_trabajador(
        [{"fecha": JUEVES, "horas": 5.0, "candef": 9.0}],
        festivos={VIERNES},
    ) == {JUEVES}


def test_f015_r24_un_dia_sin_horas_ordinarias_no_se_marca() -> None:
    """La regla de siempre: 0 h no es "jornada incompleta", es un dia sin
    horas (vacaciones, baja, no vino)."""
    assert _incompletos_trabajador([
        {"fecha": VIERNES, "horas": 0.0, "candef": 9.0},
    ]) == set()


# --------------------------- regresion (R11) ---------------------------- #

def test_f015_r24_con_candef_8_se_marcan_los_mismos_dias_que_antes() -> None:
    dias = [
        {"fecha": LUNES, "horas": 8.0, "candef": 8.0},
        {"fecha": MARTES, "horas": 6.0, "candef": 8.0},
        {"fecha": JUEVES, "horas": 10.0, "candef": 8.0},
        {"fecha": VIERNES, "horas": 6.0, "candef": 8.0},
    ]
    assert _incompletos_trabajador(dias) == {MARTES, VIERNES}


def test_f015_r24_con_candef_8_y_festivo_tampoco_cambia_nada() -> None:
    assert _incompletos_trabajador(
        [{"fecha": JUEVES, "horas": 6.0, "candef": 8.0}],
        festivos={VIERNES},
    ) == {JUEVES}


def test_f015_r24_el_festivo_del_trabajador_nunca_se_marca() -> None:
    assert _incompletos_trabajador(
        [{"fecha": VIERNES, "horas": 4.0, "candef": 8.0}],
        festivos={VIERNES},
    ) == set()


# ---------------------------- matriz de obra ---------------------------- #

def test_f015_r24_la_matriz_no_marca_el_viernes_de_6_horas() -> None:
    assert _incompletos_obra([
        {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
    ]) == set()


def test_f015_r24_la_matriz_marca_el_viernes_de_4_horas() -> None:
    incompletos = _incompletos_obra([
        {"fecha": VIERNES, "horas": 4.0, "candef": 9.0},
    ])
    assert incompletos == {"Pepe Perez|" + VIERNES}


def test_f015_r24_la_matriz_marca_el_lunes_de_8_horas_con_candef_9() -> None:
    assert _incompletos_obra([
        {"fecha": LUNES, "horas": 8.0, "candef": 9.0},
    ]) == {"Pepe Perez|" + LUNES}


def test_f015_r24_la_matriz_con_candef_8_marca_lo_de_siempre() -> None:
    incompletos = _incompletos_obra([
        {"fecha": LUNES, "horas": 8.0, "candef": 8.0},
        {"fecha": MARTES, "horas": 6.0, "candef": 8.0},
    ])
    assert incompletos == {"Pepe Perez|" + MARTES}


def test_f015_r24_la_matriz_respeta_el_festivo_del_trabajador() -> None:
    assert _incompletos_obra(
        [{"fecha": VIERNES, "horas": 4.0, "candef": 9.0}],
        festivos={VIERNES},
    ) == set()


# ---------------------- con excepcion de jornada ------------------------ #

EXCEPCION_48 = {
    "dni_norm": "12345678Z", "jornada_semanal": 48.0, "desde": "2026-01-01",
    "hasta": None, "origen": "manual",
    "h_lun": None, "h_mar": None, "h_mie": None, "h_jue": None,
    "h_vie": None, "h_sab": None, "h_dom": None,
}


def test_f015_r24_una_excepcion_cambia_el_dia_que_se_marca() -> None:
    """`S = 48` con candef 10: el viernes son 8 h, no 10."""
    assert _incompletos_trabajador(
        [{"fecha": VIERNES, "horas": 8.0, "candef": 10.0}],
        excepciones=[EXCEPCION_48],
    ) == set()


def test_f015_r24_sin_la_excepcion_ese_mismo_viernes_avisaria() -> None:
    assert _incompletos_trabajador([
        {"fecha": VIERNES, "horas": 8.0, "candef": 10.0},
    ]) == {VIERNES}


# ================= refuerzo tras la campana de mutacion ================= #
# El filtro de dias de la vista y la eleccion del dia con el que se resuelve
# la excepcion del KPI no estaban fijados: sobrevivian mutantes que cambiaban
# la estructura booleana del filtro y que hacian que el KPI mirase la
# vigencia de HOY en vez de la del periodo que se esta viendo.

SABADO = "2026-03-21"
DOMINGO = "2026-03-22"

#: Vigencia que cubre marzo de 2026 y NADA mas: ni los dias de febrero que
#: la rejilla arrastra para cuadrar la semana, ni el dia de hoy.
EXCEPCION_SOLO_MARZO = {
    "dni_norm": "12345678Z", "jornada_semanal": 48.0,
    "desde": "2026-03-01", "hasta": "2026-04-01", "origen": "manual",
    "h_lun": None, "h_mar": None, "h_mie": None, "h_jue": None,
    "h_vie": None, "h_sab": None, "h_dom": None,
}


def test_f015_r24_un_sabado_trabajado_nunca_es_jornada_incompleta() -> None:
    """El fin de semana no tiene jornada ordinaria: 4 h ahi son extra, no un
    dia al que le falten horas."""
    assert _incompletos_trabajador([
        {"fecha": SABADO, "horas": 4.0, "candef": 9.0},
    ]) == set()


def test_f015_r24_un_domingo_trabajado_tampoco() -> None:
    assert _incompletos_trabajador([
        {"fecha": DOMINGO, "horas": 4.0, "candef": 9.0},
    ]) == set()


def test_f015_r24_un_dia_con_la_jornada_justa_no_se_marca() -> None:
    """El borde: horas == jornada del dia."""
    assert _incompletos_trabajador([
        {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
        {"fecha": LUNES, "horas": 9.0, "candef": 9.0},
    ]) == set()


def test_f015_r25_el_kpi_resuelve_la_excepcion_con_el_periodo_que_se_ve(
) -> None:
    """La rejilla de marzo arrastra dias de febrero para cuadrar la primera
    semana. Si el KPI resolviese la vigencia con uno de esos —o con la fecha
    de hoy— ensenaria una jornada semanal que no es la del mes que se esta
    mirando."""
    respuesta = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": 10.0}],
        excepciones=[EXCEPCION_SOLO_MARZO],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural")
    kpi = respuesta.context["jornada_kpi"]
    assert (kpi["origen"], kpi["semanal"], kpi["ultimo_laborable"]) == (
        "excepcion", 48.0, 8.0)


def test_f015_r25_fuera_de_la_vigencia_el_kpi_vuelve_al_mapa() -> None:
    """Control del test anterior: la misma excepcion, un mes que no cubre."""
    respuesta = _cliente(
        [{"fecha": "2026-05-15", "horas": 6.0, "candef": 10.0}],
        excepciones=[EXCEPCION_SOLO_MARZO],
    ).get("/trabajadores/emp-77?period=2026-05&modo=natural")
    assert respuesta.context["jornada_kpi"]["origen"] == "plana"
