# tests/test_f032_wiring.py
"""F-032 · R6, R12, R14 y R3: el cableado de los festivos en sv3.

  - `SESAME_FESTIVOS_MINIMOS`: entero >= 0, por defecto 1; negativo o no
    entero no arranca (R6). `SESAME_CACHE_TTL_S` ya no se lee (R17).
  - Sin Sesame: el JSON de siempre, log `DESACTIVADO` y sin refresco; ni
    se toca la tabla (R12).
  - Con Sesame: `TablaCalendarioLaboral` (respaldo JSON) y un
    `RefrescoFestivos` con `al_guardar = calendario.olvidar`; la linea de
    wiring trae `festivos_minimos=` y `festivos=tabla`, sin la clave (R3).
    F-077: variables `SESAME_BASE_URL`/`SESAME_TOKEN` y cliente de Sesame HR.
  - R14: una pasada `conciliar_todos` con ese cableado no llama nunca a
    Sesame (un cliente que explota no se entera).

`build_app` monta PostgreSQL y no se levanta en la suite: por eso el
cableado vive en `construir_calendario` y `construir_refresco_festivos`.
"""
from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from application.services.festivos_guardados import FilaFestivos
from application.services.recurso_conciliador import RecursoConciliador
from application.services.refresco_festivos import RefrescoFestivos
from config.settings import Settings
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import (
    construir_calendario,
    construir_refresco_festivos,
)
from tests.dobles import (
    LookupFake,
    RepositorioFake,
    recurso_persona,
    registro,
    reshor_par,
)

CLAVE = "clave-secretisima-de-prueba"
DNI = "12345678Z"


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    for clave in ("SESAME_BASE_URL", "SESAME_TOKEN", "SESAME_TIMEOUT_S",
                  "SESAME_FESTIVOS_MINIMOS", "SESAME_CACHE_TTL_S"):
        monkeypatch.delenv(clave, raising=False)
    return monkeypatch


@pytest.fixture
def con_sesame(entorno):
    entorno.setenv("SESAME_BASE_URL", "https://sesame.ejemplo.test")
    entorno.setenv("SESAME_TOKEN", CLAVE)
    return entorno


class RepoQueNoSeToca:
    def leer_todas(self):
        raise AssertionError("sin Sesame no se lee la tabla")

    def guardar(self, fila):
        raise AssertionError("sin Sesame no se escribe la tabla")


class RepoFestivos:
    def __init__(self, filas=None):
        self.filas = dict(filas or {})

    def leer_todas(self):
        return dict(self.filas)

    def guardar(self, fila):
        self.filas[(fila.dni_norm, fila.ano)] = fila


# ------------------------------ settings (R6) --------------------------- #

def test_f032_r6_minimo_por_defecto_1(entorno):
    assert Settings(_env_file=None).sesame_festivos_minimos == 1


@pytest.mark.parametrize("valor,esperado", [("0", 0), ("8", 8)])
def test_f032_r6_minimo_configurable(entorno, valor, esperado):
    entorno.setenv("SESAME_FESTIVOS_MINIMOS", valor)
    assert Settings(_env_file=None).sesame_festivos_minimos == esperado


@pytest.mark.parametrize("valor", ["-1", "uno", "1.5"])
def test_f032_r6_minimo_negativo_o_no_entero_no_arranca(entorno, valor):
    entorno.setenv("SESAME_FESTIVOS_MINIMOS", valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f032_r17_ya_no_se_lee_el_ttl_de_sesame(entorno):
    entorno.setenv("SESAME_CACHE_TTL_S", "5")
    assert not hasattr(Settings(_env_file=None), "sesame_cache_ttl_s")


# ------------------------------ sin Sesame (R12) ------------------------ #

def test_f032_r12_sin_sesame_json_desactivado_y_sin_refresco(entorno, caplog):
    settings = Settings(_env_file=None)
    repo = RepoQueNoSeToca()
    with caplog.at_level(logging.INFO):
        cal = construir_calendario(settings, repo)
        refresco = construir_refresco_festivos(settings, repo, cal)
    assert type(cal) is JsonCalendarioLaboral
    assert refresco is None
    assert "[sesame][wiring] DESACTIVADO" in caplog.text
    # El JSON sigue resolviendo sin tocar la tabla.
    assert cal.es_no_laborable("2026-01-01", dni=DNI) is True


def test_f032_r12_sin_sesame_el_repositorio_es_opcional(entorno):
    assert type(construir_calendario(Settings(_env_file=None))) is \
        JsonCalendarioLaboral


# ------------------------------ con Sesame ------------------------------ #

def test_f032_r13_con_sesame_la_tabla_con_el_json_de_respaldo(con_sesame):
    repo = RepoFestivos()
    cal = construir_calendario(Settings(_env_file=None), repo)
    assert isinstance(cal, TablaCalendarioLaboral)
    assert isinstance(cal._respaldo, JsonCalendarioLaboral)
    assert cal._repositorio is repo
    assert cal._ttl_s == 60


def test_f032_r13_con_sesame_sin_repositorio_no_arranca(con_sesame):
    with pytest.raises(ValueError):
        construir_calendario(Settings(_env_file=None))


def test_f032_r15_refresco_cableado_con_olvidar(con_sesame):
    con_sesame.setenv("SESAME_FESTIVOS_MINIMOS", "3")
    settings = Settings(_env_file=None)
    repo = RepoFestivos()
    cal = construir_calendario(settings, repo)
    refresco = construir_refresco_festivos(settings, repo, cal)
    assert isinstance(refresco, RefrescoFestivos)
    assert refresco._minimo == 3
    assert refresco._repositorio is repo
    assert refresco._al_guardar == cal.olvidar
    # F-077: el cliente del refresco es el adaptador de Sesame HR.
    cliente_hr = refresco._cliente._cliente
    assert cliente_hr._base_url == "https://sesame.ejemplo.test"
    assert cliente_hr._timeout_s == settings.sesame_timeout_s
    ahora = refresco._ahora_utc()
    assert ahora.tzinfo is not None and ahora.utcoffset().total_seconds() == 0


def test_f032_r3_log_de_wiring_con_minimo_y_tabla_sin_la_clave(
        con_sesame, caplog):
    with caplog.at_level(logging.INFO):
        construir_calendario(Settings(_env_file=None), RepoFestivos())
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert "CABLEADO" in wiring[0]
    assert "festivos_minimos=1" in wiring[0]
    assert "festivos=tabla" in wiring[0]
    assert f"token_len={len(CLAVE)}" in wiring[0]
    assert "base_url=https://sesame.ejemplo.test" in wiring[0]
    assert CLAVE not in caplog.text


# --------------------------------- R14 ---------------------------------- #

def test_f032_r14_la_pasada_no_llama_a_sesame(con_sesame, monkeypatch):
    """Cliente que explota en las tres rutas: la pasada lee solo la tabla."""
    class ClienteQueExplota:
        def __init__(self, **kw):
            pass

        def empleados(self, *a):
            raise AssertionError("la pasada no pide empleados a Sesame")

        def festivos_de_empleado(self, *a):
            raise AssertionError("ni festivos")

        def calendarios_festivos(self, *a):
            raise AssertionError("ni calendarios")

    monkeypatch.setattr(modulo_app, "SesameHrClient", ClienteQueExplota)
    settings = Settings(_env_file=None)
    festivos = RepoFestivos({(DNI, 2026): FilaFestivos(
        dni_norm=DNI, ano=2026, festivos={"2026-05-18": "fiesta local"},
        leido_en_utc="t")})
    cal = construir_calendario(settings, festivos)
    construir_refresco_festivos(settings, festivos, cal)
    repositorio = RepositorioFake([registro(1, fecha_int=20260518,
                                            horas=8.0, dni=DNI,
                                            document_id="doc-A")])
    conciliador = RecursoConciliador(
        repository=repositorio,
        lookup=LookupFake(recursos=[recurso_persona(
            ide=501, conide=1, cif=DNI, restip_res="Oficial",
            horide_def=100)], reshor=reshor_par(501), hmo={}),
        calendario=cal, jornada_ordinaria_horas=8.0, candef_minimo=2.0)
    conciliador.conciliar_todos()
    # El lunes es festivo en la fila: sus 8 h ordinarias pasan a extra.
    assert [(s["horas_norm"], s["extra_horas"])
            for s in repositorio.splits] == [(0.0, 8.0)]
    assert repositorio.review_required == []
