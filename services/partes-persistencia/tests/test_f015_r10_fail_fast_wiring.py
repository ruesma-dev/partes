# tests/test_f015_r10_fail_fast_wiring.py
"""R10 (fail-fast) · un mapa mal escrito no arranca el servicio.

`JORNADA_SEMANAL_POR_CANDEF` decide cuantas horas de cada dia son
ordinarias. Si alguien escribe `8:40,9` en el script de provision, las
opciones son dos: que el servicio no levante, o que reparta las horas de
todos los partes con un mapa a medias y nadie se entere hasta que
Administracion cuadre la nomina. F-015 elige la primera.

Por eso el mapa se parsea en el CABLEADO y no en `config/settings.py`
(que ademas acabaria importando de `application/`, invirtiendo las capas).

`build_app` de sv3 monta la SessionFactory contra PostgreSQL y no se puede
levantar en la suite —igual que en F-003 con el calendario—, asi que la
parte cableable se prueba por `construir_mapa_semanal` y el ORDEN se
comprueba sobre el fuente.
"""
from __future__ import annotations

import inspect
import logging

import pytest
from config.settings import Settings
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import construir_mapa_semanal


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


# ------------------------------ el default ------------------------------ #

def test_f015_r10_el_mapa_por_defecto_es_8_40_y_9_42(entorno) -> None:
    assert Settings(_env_file=None).jornada_semanal_por_candef == "8:40,9:42"
    assert construir_mapa_semanal(Settings(_env_file=None)) == {
        8.0: 40.0, 9.0: 42.0}


def test_f015_r10_el_ttl_de_las_excepciones_por_defecto(entorno) -> None:
    assert Settings(_env_file=None).jornada_cache_ttl_s == 600


def test_f015_r10_el_mapa_se_puede_ampliar_por_entorno(entorno) -> None:
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", "8:40,9:42,10:48")
    assert construir_mapa_semanal(Settings(_env_file=None)) == {
        8.0: 40.0, 9.0: 42.0, 10.0: 48.0}


def test_f015_r10_el_wiring_deja_el_mapa_en_el_log(entorno, caplog) -> None:
    with caplog.at_level(logging.INFO):
        construir_mapa_semanal(Settings(_env_file=None))
    assert "[jornada][wiring]" in caplog.text
    assert "8:40" in caplog.text
    assert "9:42" in caplog.text


# ------------------------------- fail-fast ------------------------------ #

@pytest.mark.parametrize("texto", [
    "8:40,9", "x:40", "8:40,8:41", "", "   ", "8:0", "0:40",
])
def test_f015_r10_un_mapa_mal_formado_tira_el_arranque(
        entorno, texto) -> None:
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", texto)
    with pytest.raises(ValueError):
        construir_mapa_semanal(Settings(_env_file=None))


def test_f015_r10_el_error_nombra_la_variable(entorno) -> None:
    """Quien lea el log del contenedor caido tiene que saber que tocar."""
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", "8:40,9")
    with pytest.raises(ValueError) as exc:
        construir_mapa_semanal(Settings(_env_file=None))
    assert "JORNADA_SEMANAL_POR_CANDEF" in str(exc.value)


# ------------------------------ el cableado ----------------------------- #

FUENTE_BUILD_APP = inspect.getsource(modulo_app.build_app)


def test_f015_r10_build_app_valida_el_mapa_antes_de_abrir_la_bbdd() -> None:
    """Fail-fast de verdad: si el mapa esta mal, ni se toca PostgreSQL."""
    assert "construir_mapa_semanal(settings)" in FUENTE_BUILD_APP
    assert (FUENTE_BUILD_APP.index("construir_mapa_semanal(settings)")
            < FUENTE_BUILD_APP.index("SessionFactory("))


def test_f015_r10_build_app_inyecta_el_mapa_en_el_conciliador() -> None:
    assert "mapa_semanal=mapa_semanal" in FUENTE_BUILD_APP


def test_f015_r10_build_app_inyecta_el_repositorio_de_excepciones() -> None:
    assert "jornadas=SqlAlchemyJornadaRepository(session_factory)" in (
        FUENTE_BUILD_APP)
    assert "jornada_cache_ttl_s=settings.jornada_cache_ttl_s" in (
        FUENTE_BUILD_APP)


def test_f015_r10_el_conciliador_usa_el_mapa_que_se_le_inyecta() -> None:
    """Que el parametro llegue no basta: tiene que mandar en el calculo."""
    from application.services.recurso_conciliador import RecursoConciliador
    from tests.dobles import (
        CalendarioFake,
        LookupFake,
        RepositorioFake,
        indice_reshor,
        registro,
    )

    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), mapa_semanal={9.0: 40.0},
    )
    regs = [registro(1, fecha_int=20260320, horas=4.0)]
    splits = conciliador._reclasificar_extras_jornada(
        regs, {1: 501}, indice_reshor(501, candef=9.0))
    # Viernes: 40 - 36 = 4 h de jornada, asi que 4 h trabajadas cuadran.
    assert splits == []
