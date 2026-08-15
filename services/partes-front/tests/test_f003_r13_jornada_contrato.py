# tests/test_f003_r13_jornada_contrato.py
"""R13 y R14 · el tipo de jornada del contrato en la vista trabajador.

sesame-api NO da hoy las horas del contrato (peticion P1 del design), asi
que el CanDefecto de Sigrid sigue mandando en el calculo. Lo que si da es
el TIPO de jornada y si es reducida, y con eso se puede al menos avisar
de una divergencia que hoy no ve nadie: contrato de jornada reducida
contra una jornada aplicada de 8 h.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sesame.sesame_api_client import JornadaContrato
from interface_adapters.web.app import build_app

from tests.dobles import FabricaSesionSqlite, sembrar_dias
from tests.test_f003_r2_vistas_festivos import ProveedorFake

COMPLETA = JornadaContrato(tipo="Completa", reducida=False,
                           tipo_contrato="Indefinido")
REDUCIDA = JornadaContrato(tipo="Parcial", reducida=True,
                           tipo_contrato="Indefinido")


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _html(entorno, *, jornada, candef=8.0) -> str:
    proveedor = ProveedorFake(por_dni={"12345678Z": set()}, jornada=jornada)
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-05-11", "horas": 8.0,
                            "candef": candef}])
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=proveedor)
    return TestClient(app).get("/trabajadores/emp-77?modo=natural").text


# ----------------------- R13 · el badge del contrato -------------------- #

def test_f003_r13_muestra_el_tipo_de_jornada_del_contrato(entorno) -> None:
    html = _html(entorno, jornada=COMPLETA)
    assert "jornada-contrato" in html
    assert "Completa" in html


def test_f003_r13_sin_dato_de_sesame_el_kpi_va_como_hoy(entorno) -> None:
    """Si Sesame no lo puede dar, ni badge ni hueco raro: como siempre."""
    html = _html(entorno, jornada=None)
    assert "jornada-contrato" not in html
    assert "8 h" in html            # el KPI sigue estando


def test_f003_r13_con_sesame_apagado_no_hay_badge(entorno) -> None:
    """Con el proveedor REAL sin cliente (feature apagada) no hay dato de
    contrato que ensenar, y la vista queda como antes de F-003."""
    from application.services.calendario_provider import CalendarioProvider

    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-05-11", "horas": 8.0,
                            "candef": 8.0}])
    proveedor = CalendarioProvider(cliente=None,
                                   respaldo_holiday_name=lambda _d: None)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=proveedor)
    html = TestClient(app).get("/trabajadores/emp-77?modo=natural").text
    assert "jornada-contrato" not in html
    assert "jornada-divergencia" not in html
    assert "8 h" in html


# --------------------- R14 · aviso de divergencia ----------------------- #

def test_f003_r14_contrato_reducido_con_jornada_de_8_avisa(entorno) -> None:
    html = _html(entorno, jornada=REDUCIDA, candef=8.0)
    assert "jornada-divergencia" in html
    assert "reducida" in html.lower()


def test_f003_r14_contrato_reducido_con_jornada_menor_no_avisa(
        entorno) -> None:
    """Coherente: contrato reducido y jornada aplicada de 6 h."""
    html = _html(entorno, jornada=REDUCIDA, candef=6.0)
    assert "jornada-divergencia" not in html


def test_f003_r14_contrato_completo_nunca_avisa(entorno) -> None:
    html = _html(entorno, jornada=COMPLETA, candef=8.0)
    assert "jornada-divergencia" not in html


def test_f003_r14_reducida_desconocida_no_avisa(entorno) -> None:
    """`reducida=None` es "no se sabe", no "no es reducida": no se
    inventa un aviso con un dato que Sesame no ha dado."""
    desconocida = JornadaContrato(tipo="Otra", reducida=None,
                                  tipo_contrato="Temporal")
    html = _html(entorno, jornada=desconocida, candef=8.0)
    assert "jornada-divergencia" not in html
    assert "jornada-contrato" in html


def test_f003_r14_el_umbral_es_la_jornada_por_defecto(entorno,
                                                      monkeypatch) -> None:
    """Con candef 9 (por encima de la jornada por defecto) tambien avisa."""
    html = _html(entorno, jornada=REDUCIDA, candef=9.0)
    assert "jornada-divergencia" in html
