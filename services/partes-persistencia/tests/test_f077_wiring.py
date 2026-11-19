# tests/test_f077_wiring.py
"""F-077 · R16 y R17: configuracion y cableado de Sesame HR en sv3.

  - R16: `SESAME_BASE_URL`, `SESAME_TOKEN`, `SESAME_TIMEOUT_S` (10, > 0) y
    `SESAME_FESTIVOS_MINIMOS`; `sesame_enabled` exige URL y token no en
    blanco; una URL con valor que no empieza por `https://` no arranca
    (DA14). Las `SESAME_API_*` de la pasarela ya no se leen.
  - R17: el log de arranque dice `CABLEADO base_url=… token_len=…
    festivos_minimos=… festivos=tabla` o `DESACTIVADO (faltan
    SESAME_BASE_URL/SESAME_TOKEN)`, nunca el token; el refresco recibe un
    `FestivosSesameHr` sobre un `SesameHrClient` con esos valores.

`build_app` monta PostgreSQL y no se levanta en la suite: el cableado vive
en `construir_calendario` y `construir_refresco_festivos`. Datos ficticios.
"""
from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from application.services.refresco_festivos import RefrescoFestivos
from config.settings import Settings
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import SesameHrClient
from interface_adapters.api.app import (
    construir_calendario,
    construir_refresco_festivos,
)
from tests.fixtures_sesame import BASE_URL, TOKEN

VARIABLES = ("SESAME_BASE_URL", "SESAME_TOKEN", "SESAME_TIMEOUT_S",
             "SESAME_FESTIVOS_MINIMOS", "SESAME_API_BASE_URL",
             "SESAME_API_KEY", "SESAME_API_TIMEOUT_S")


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    for clave in VARIABLES:
        monkeypatch.delenv(clave, raising=False)
    return monkeypatch


@pytest.fixture
def con_sesame(entorno):
    entorno.setenv("SESAME_BASE_URL", BASE_URL)
    entorno.setenv("SESAME_TOKEN", TOKEN)
    return entorno


class RepoFestivos:
    def leer_todas(self):
        return {}

    def guardar(self, fila):
        raise AssertionError("el cableado no escribe")


# --------------------------------- R16 ---------------------------------- #

def test_f077_r16_por_defecto_apagado_y_timeout_10(entorno) -> None:
    s = Settings(_env_file=None)
    assert (s.sesame_base_url, s.sesame_token) == (None, None)
    assert s.sesame_timeout_s == 10.0
    assert s.sesame_festivos_minimos == 1
    assert s.sesame_enabled is False


def test_f077_r16_url_y_token_encienden(entorno) -> None:
    entorno.setenv("SESAME_BASE_URL", BASE_URL)
    assert Settings(_env_file=None).sesame_enabled is False
    entorno.setenv("SESAME_TOKEN", TOKEN)
    s = Settings(_env_file=None)
    assert s.sesame_enabled is True
    assert (s.sesame_base_url, s.sesame_token) == (BASE_URL, TOKEN)


def test_f077_r16_solo_token_no_enciende(entorno) -> None:
    entorno.setenv("SESAME_TOKEN", TOKEN)
    assert Settings(_env_file=None).sesame_enabled is False


@pytest.mark.parametrize("url, token", [("   ", TOKEN), (BASE_URL, "   ")])
def test_f077_r16_valores_en_blanco_no_encienden(entorno, url, token) -> None:
    entorno.setenv("SESAME_BASE_URL", url)
    entorno.setenv("SESAME_TOKEN", token)
    assert Settings(_env_file=None).sesame_enabled is False


@pytest.mark.parametrize("url", ["http://sesame.ejemplo.test",
                                 "sesame.ejemplo.test", "ftp://x"])
def test_f077_r16_url_sin_https_no_arranca(entorno, url) -> None:
    entorno.setenv("SESAME_BASE_URL", url)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f077_r16_timeout_configurable_y_positivo(entorno) -> None:
    entorno.setenv("SESAME_TIMEOUT_S", "4.5")
    assert Settings(_env_file=None).sesame_timeout_s == 4.5
    # Design 5.3: `gt=0`; medio segundo es un plazo valido (T16).
    entorno.setenv("SESAME_TIMEOUT_S", "0.5")
    assert Settings(_env_file=None).sesame_timeout_s == 0.5
    for malo in ("0", "-1", "rapido"):
        entorno.setenv("SESAME_TIMEOUT_S", malo)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)


def test_f077_r16_las_variables_de_la_pasarela_se_ignoran(entorno) -> None:
    entorno.setenv("SESAME_API_BASE_URL", "http://pasarela.ejemplo.test")
    entorno.setenv("SESAME_API_KEY", "clave-vieja")
    entorno.setenv("SESAME_API_TIMEOUT_S", "3")
    s = Settings(_env_file=None)
    assert s.sesame_enabled is False
    for viejo in ("sesame_api_base_url", "sesame_api_key",
                  "sesame_api_timeout_s"):
        assert not hasattr(s, viejo)


# --------------------------------- R17 ---------------------------------- #

def test_f077_r17_desactivado(entorno, caplog) -> None:
    settings = Settings(_env_file=None)
    with caplog.at_level(logging.INFO):
        cal = construir_calendario(settings, RepoFestivos())
        assert construir_refresco_festivos(settings, RepoFestivos(),
                                           cal) is None
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert wiring[0].startswith(
        "[sesame][wiring] DESACTIVADO (faltan SESAME_BASE_URL/SESAME_TOKEN)")


def test_f077_r17_cableado_sin_el_token(con_sesame, caplog) -> None:
    con_sesame.setenv("SESAME_FESTIVOS_MINIMOS", "4")
    with caplog.at_level(logging.INFO):
        construir_calendario(Settings(_env_file=None), RepoFestivos())
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert wiring[0].startswith(
        f"[sesame][wiring] CABLEADO base_url={BASE_URL} "
        f"token_len={len(TOKEN)} festivos_minimos=4 festivos=tabla")
    assert TOKEN not in caplog.text


def test_f077_r17_el_refresco_lleva_el_adaptador_de_sesame_hr(
        con_sesame, caplog) -> None:
    con_sesame.setenv("SESAME_TIMEOUT_S", "7")
    settings = Settings(_env_file=None)
    repo = RepoFestivos()
    cal = construir_calendario(settings, repo)
    with caplog.at_level(logging.INFO):
        refresco = construir_refresco_festivos(settings, repo, cal)
    assert isinstance(cal, TablaCalendarioLaboral)
    assert isinstance(refresco, RefrescoFestivos)
    adaptador = refresco._cliente                          # noqa: SLF001
    assert isinstance(adaptador, FestivosSesameHr)
    cliente = adaptador._cliente                           # noqa: SLF001
    assert isinstance(cliente, SesameHrClient)
    assert cliente._base_url == BASE_URL                   # noqa: SLF001
    assert cliente._token == TOKEN                         # noqa: SLF001
    assert cliente._timeout_s == 7.0                       # noqa: SLF001
    assert refresco._al_guardar == cal.olvidar             # noqa: SLF001
    assert TOKEN not in caplog.text
