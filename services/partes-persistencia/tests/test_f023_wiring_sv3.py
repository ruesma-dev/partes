# tests/test_f023_wiring_sv3.py
"""F-023 · cableado de sv3 (DA3, DA5, R25).

  - DA5: `SIGRID_EMPRESA` sale del codigo; si sigue en Azure, se ignora.
  - DA3: la tabla de alias del membrete se lee AL ARRANCAR desde
    `EMPRESAS_MEMBRETE_PATH` (por defecto la versionada) y un fichero mal
    escrito revienta el arranque.
  - R25: el conciliador de recursos usa el MISMO indice de personas que la
    ingesta (`indice_provider = matcher_provider.indice`).

`construir_casado_sigrid` esta separada de `build_app` para esto: el
`build_app` de sv3 monta PostgreSQL y no se puede levantar en la suite.
Construir el cliente de Sigrid no abre ninguna conexion.
"""
from __future__ import annotations

import pytest

from config.settings import Settings
from interface_adapters.api.app import (
    construir_alias_empresas,
    construir_casado_sigrid,
)
from tests.dobles import JornadasFake, RepositorioFake


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _con_sigrid(entorno) -> Settings:
    entorno.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    entorno.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    entorno.setenv("SIGRID_API_DATABASE", "bd")
    return Settings(_env_file=None)


# ================================ DA5 =================================== #

def test_f023_da5_sigrid_empresa_ya_no_esta_en_los_settings(entorno) -> None:
    entorno.setenv("SIGRID_EMPRESA", "1")      # la variable vieja de Azure
    settings = Settings(_env_file=None)
    assert not hasattr(settings, "sigrid_empresa")


# ================================ DA3 =================================== #

def test_f023_da3_por_defecto_se_lee_la_tabla_versionada(entorno) -> None:
    settings = Settings(_env_file=None)
    assert settings.empresas_membrete_path == "config/empresas_membrete.yaml"
    # F-029: la 1 trae tambien el alias del logotipo (RUΞSMA).
    assert construir_alias_empresas(settings) == {
        1: ["RUESMA", "RUΞSMA"], 28: ["PORSAN"]}


def test_f023_da3_la_ruta_se_puede_cambiar(entorno, tmp_path) -> None:
    fichero = tmp_path / "alias.yaml"
    fichero.write_text("5:\n  - OTRA\n", encoding="utf-8")
    entorno.setenv("EMPRESAS_MEMBRETE_PATH", str(fichero))
    assert construir_alias_empresas(Settings(_env_file=None)) == {5: ["OTRA"]}


def test_f023_da3_una_tabla_mal_escrita_revienta_el_arranque(
        entorno, tmp_path) -> None:
    fichero = tmp_path / "alias.yaml"
    fichero.write_text("- PORSAN\n", encoding="utf-8")
    entorno.setenv("EMPRESAS_MEMBRETE_PATH", str(fichero))
    with pytest.raises(ValueError):
        construir_alias_empresas(Settings(_env_file=None))


def test_f023_da3_sin_la_tabla_no_arranca(entorno, tmp_path) -> None:
    entorno.setenv("EMPRESAS_MEMBRETE_PATH", str(tmp_path / "no-existe.yaml"))
    with pytest.raises(FileNotFoundError):
        construir_alias_empresas(Settings(_env_file=None))


# ============================ el cableado ============================== #

def test_f023_sin_credenciales_no_se_cablea_nada(entorno) -> None:
    assert construir_casado_sigrid(
        Settings(_env_file=None), repository=RepositorioFake(),
        jornadas=JornadasFake(), mapa_semanal={8.0: 40.0},
    ) == (None, None, None, None)


def test_f023_r25_el_conciliador_usa_el_indice_del_proveedor(entorno) -> None:
    settings = _con_sigrid(entorno)
    jornadas = JornadasFake()
    cliente, proveedor, partidas, recursos = construir_casado_sigrid(
        settings, repository=RepositorioFake(), jornadas=jornadas,
        mapa_semanal={8.0: 40.0})
    assert recursos._indice_provider == proveedor.indice
    assert recursos._lookup is cliente and partidas._lookup is cliente
    assert proveedor._alias_empresas == {1: ["RUESMA", "RUΞSMA"],
                                        28: ["PORSAN"]}
    assert recursos._jornadas is jornadas
    assert recursos._mapa_semanal == {8.0: 40.0}
    assert recursos._jornada_ttl == settings.jornada_cache_ttl_s
