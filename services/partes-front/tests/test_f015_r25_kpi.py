# tests/test_f015_r25_kpi.py
"""R25 · el KPI de jornada enseña con qué números se está calculando.

Sin esto, F-015 sería magia: el portal dejaría de avisar de unos días y
empezaría a avisar de otros sin que nadie pudiera ver por qué. El KPI
muestra el candef efectivo, la jornada semanal aplicada —marcada cuando
viene de una excepción— y las horas del último día laborable, que es el
número que más sorprende («¿por qué el viernes son 6 h?»).

Se comprueba el CONTEXTO de la vista y que la plantilla lo pinta; el
aspecto visual es verificación MANUAL del humano.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader
from tests.test_f015_r24_avisos import _cliente, entorno  # noqa: F401

VIERNES = "2026-03-20"

PLANTILLA = (
    Path(__file__).resolve().parents[1] / "templates" / "trabajador_detail.html"
)

EXCEPCION_48 = {
    "dni_norm": "12345678Z", "jornada_semanal": 48.0, "desde": "2026-01-01",
    "hasta": None, "origen": "manual",
    "h_lun": None, "h_mar": None, "h_mie": None, "h_jue": None,
    "h_vie": None, "h_sab": None, "h_dom": None,
}

EXCEPCION_PATRON = {
    "dni_norm": "12345678Z", "jornada_semanal": None, "desde": "2026-01-01",
    "hasta": None, "origen": "manual",
    "h_lun": 7.0, "h_mar": 7.0, "h_mie": 7.0, "h_jue": 7.0, "h_vie": 7.0,
    "h_sab": 0.0, "h_dom": 0.0,
}


def _kpi(candef, *, excepciones=()):
    respuesta = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": candef}],
        excepciones=excepciones,
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural")
    assert respuesta.status_code == 200
    return respuesta.context["jornada_kpi"]


# ------------------------------ el contexto ----------------------------- #

def test_f015_r25_el_kpi_lleva_candef_semanal_origen_y_ultimo(entorno) -> None:
    kpi = _kpi(9.0)
    assert kpi == {
        "candef": 9.0, "semanal": 42.0, "origen": "mapa",
        "ultimo_laborable": 6.0, "patron": None,
    }


def test_f015_r25_con_candef_8_el_kpi_dice_40_y_8(entorno) -> None:
    kpi = _kpi(8.0)
    assert (kpi["semanal"], kpi["ultimo_laborable"], kpi["origen"]) == (
        40.0, 8.0, "mapa")


def test_f015_r25_un_candef_fuera_del_mapa_se_declara_plano(entorno) -> None:
    kpi = _kpi(10.0)
    assert (kpi["semanal"], kpi["origen"], kpi["ultimo_laborable"]) == (
        50.0, "plana", 10.0)


def test_f015_r25_un_candef_no_informado_sigue_marcandose_asignado(
        entorno) -> None:
    """R12: el KPI de CanDefecto no cambia de semantica."""
    respuesta = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": 0.0}],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural")
    assert respuesta.context["candef_kpi"]["asignado"] is True
    assert respuesta.context["jornada_kpi"]["candef"] == 8.0


def test_f015_r25_una_excepcion_se_declara_como_tal(entorno) -> None:
    kpi = _kpi(10.0, excepciones=[EXCEPCION_48])
    assert (kpi["semanal"], kpi["origen"], kpi["ultimo_laborable"]) == (
        48.0, "excepcion", 8.0)


def test_f015_r25_una_excepcion_de_patron_ensena_el_patron(entorno) -> None:
    kpi = _kpi(9.0, excepciones=[EXCEPCION_PATRON])
    assert kpi["origen"] == "excepcion"
    assert kpi["patron"] == (7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0)
    # Con patron no hay "resto de la semana" que ensenar.
    assert kpi["ultimo_laborable"] is None


def test_f015_r25_el_ultimo_laborable_nunca_es_negativo(entorno) -> None:
    """Con `S < 4c` el resto se corta en 0, igual que en el calculo."""
    kpi = _kpi(10.0, excepciones=[dict(EXCEPCION_48, jornada_semanal=30.0)])
    assert kpi["ultimo_laborable"] == 0.0


# ----------------------------- la plantilla ----------------------------- #

def test_f015_r25_la_plantilla_parsea() -> None:
    """`docs/CONVENTIONS.md`: parseo Jinja2 de toda plantilla tocada."""
    entorno_jinja = Environment(loader=FileSystemLoader(str(PLANTILLA.parent)))
    entorno_jinja.filters["horas"] = lambda v: v
    entorno_jinja.filters["fecha"] = lambda v: v
    entorno_jinja.filters["incidencia"] = lambda v: v
    entorno_jinja.get_template(PLANTILLA.name)


def test_f015_r25_la_plantilla_usa_el_kpi() -> None:
    fuente = PLANTILLA.read_text(encoding="utf-8")
    assert "jornada_kpi" in fuente
    assert "jornada_kpi.semanal" in fuente
    assert "jornada_kpi.ultimo_laborable" in fuente


def test_f015_r25_la_vista_pinta_la_jornada_semanal(entorno) -> None:
    html = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": 9.0}],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural").text
    assert "jornada-semanal" in html
    assert "42" in html


def test_f015_r25_la_vista_marca_la_excepcion(entorno) -> None:
    html = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": 10.0}],
        excepciones=[EXCEPCION_48],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural").text
    assert "jornada-excepcion" in html


def test_f015_r25_sin_excepcion_no_se_marca_nada(entorno) -> None:
    html = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": 9.0}],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural").text
    assert "jornada-excepcion" not in html


@pytest.mark.parametrize("candef", [8.0, 9.0, 10.0])
def test_f015_r25_la_vista_se_sirve_con_cualquier_candef(
        entorno, candef) -> None:
    respuesta = _cliente(
        [{"fecha": VIERNES, "horas": 6.0, "candef": candef}],
    ).get("/trabajadores/emp-77?period=2026-03&modo=natural")
    assert respuesta.status_code == 200
