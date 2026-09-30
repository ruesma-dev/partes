# tests/test_f023_empresa_membrete.py
"""F-023 · R7-R8: del texto del membrete a una empresa de Sigrid (sv3).

sv2 copia el membrete tal cual («PORSAN E HIJOS», «Construcciones
Ruesma, S.A.»...). `auxemp` no trae CIF y su nombre oficial no es lo que
pone el logotipo, asi que la traduccion es una tabla VERSIONADA de alias
por `numemp` (`config/empresas_membrete.yaml`, DA3): casa si el texto
normalizado contiene, como palabras completas, un alias de exactamente
UNA empresa valida (existe en `auxemp`, sin baja ni desactivada). Si no,
la empresa del membrete queda desconocida y se loguea el texto (R8).
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from application.services.empresa_membrete import (
    ResolutorEmpresa,
    parsear_alias,
)
from domain.models.sigrid_models import EmpresaRow

RAIZ = Path(__file__).resolve().parents[1]

EMPRESAS = [
    EmpresaRow(numemp=1, nombre="CONSTRUCCIONES UNO", fecbaj=0, desact=0),
    EmpresaRow(numemp=28, nombre="VEINTIOCHO E HIJOS SL", fecbaj=None,
               desact=None),
    EmpresaRow(numemp=5, nombre="DE BAJA", fecbaj=20200101, desact=0),
    EmpresaRow(numemp=6, nombre="DESACTIVADA", fecbaj=0, desact=1),
]
ALIAS = {1: ["RUESMA"], 28: ["PORSAN", "Porsan e Hijos"]}


def _resolutor(alias=None, empresas=None) -> ResolutorEmpresa:
    return ResolutorEmpresa(ALIAS if alias is None else alias,
                            EMPRESAS if empresas is None else empresas)


# ================================ R7 ==================================== #

@pytest.mark.parametrize("texto, empresa", [
    ("PORSAN", 28),
    ("Porsan e Hijos Construcciones, S.L.", 28),
    ("porsán", 28),                       # sin acentos
    ("CONSTRUCCIONES RUESMA S.A.", 1),
    ("  ruesma\n", 1),
])
def test_f023_r7_un_alias_de_una_sola_empresa_casa(texto, empresa) -> None:
    assert _resolutor().resolver(texto) == (empresa, "membrete")


def test_f023_r7_solo_palabras_completas() -> None:
    """«PORSANES» o «RUESMAS» no son el alias."""
    assert _resolutor().resolver("PORSANES SA") == (None, "sin_alias")
    assert _resolutor().resolver("xruesma") == (None, "sin_alias")


def test_f023_r7_alias_de_varias_palabras() -> None:
    resolutor = _resolutor(alias={28: ["hijos de porsan"]})
    assert resolutor.resolver("Los HIJOS DE PORSAN") == (28, "membrete")
    assert resolutor.resolver("hijos porsan") == (None, "sin_alias")


def test_f023_r7_la_empresa_tiene_que_existir_en_auxemp(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        resolutor = _resolutor(alias={99: ["FANTASMA"], 1: ["RUESMA"]})
    assert "99" in caplog.text
    assert resolutor.resolver("FANTASMA") == (None, "empresa_no_valida")
    assert resolutor.resolver("RUESMA") == (1, "membrete")


@pytest.mark.parametrize("numemp", [5, 6])
def test_f023_r7_empresa_de_baja_o_desactivada_no_vale(numemp, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        resolutor = _resolutor(alias={numemp: ["OTRA"]})
    assert str(numemp) in caplog.text
    assert resolutor.resolver("OTRA") == (None, "empresa_no_valida")


def test_f023_r7_la_empresa_invalida_no_anula_a_la_valida() -> None:
    """Un alias invalido y otro valido en el mismo texto: casa la valida."""
    resolutor = _resolutor(alias={5: ["OTRA"], 28: ["PORSAN"]})
    assert resolutor.resolver("OTRA PORSAN") == (28, "membrete")


def test_f023_r7_dos_alias_de_la_misma_empresa_no_son_varias() -> None:
    assert _resolutor().resolver("PORSAN E HIJOS") == (28, "membrete")


# ================================ R8 ==================================== #

@pytest.mark.parametrize("texto", [None, "", "   ", ".,-"])
def test_f023_r8_sin_texto(texto) -> None:
    assert _resolutor().resolver(texto) == (None, "sin_texto")


def test_f023_r8_sin_alias(caplog) -> None:
    with caplog.at_level(logging.INFO):
        assert _resolutor().resolver("Logo ilegible") == (None, "sin_alias")
    assert "Logo ilegible" in caplog.text


def test_f023_r8_alias_de_varias_empresas(caplog) -> None:
    with caplog.at_level(logging.INFO):
        assert _resolutor().resolver("RUESMA / PORSAN") == (None, "varias")
    assert "RUESMA / PORSAN" in caplog.text


def test_f023_r8_sin_tabla_de_alias_nada_casa() -> None:
    assert _resolutor(alias={}).resolver("PORSAN") == (None, "sin_alias")


def test_f023_r8_el_caso_resuelto_no_se_loguea_como_desconocido(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _resolutor().resolver("PORSAN")
    assert "desconocida" not in caplog.text


# ======================= tabla versionada de alias ====================== #

def test_f023_r7_la_tabla_versionada_trae_las_dos_empresas_activas() -> None:
    datos = yaml.safe_load(
        (RAIZ / "config" / "empresas_membrete.yaml").read_text("utf-8"))
    assert parsear_alias(datos) == {1: ["RUESMA"], 28: ["PORSAN"]}


def test_f023_parsear_alias_acepta_claves_de_texto_y_quita_vacios() -> None:
    assert parsear_alias({"28": ["PORSAN", "  ", "Porsan e Hijos"]}) == \
        {28: ["PORSAN", "Porsan e Hijos"]}
    assert parsear_alias(None) == {}


@pytest.mark.parametrize("datos", [
    ["PORSAN"],                 # no es un mapa
    {"x": ["PORSAN"]},          # la clave no es un numero
    {28: "PORSAN"},             # los alias no son una lista
    {28: [7]},                  # un alias no es texto
])
def test_f023_parsear_alias_rechaza_formatos_mal_escritos(datos) -> None:
    with pytest.raises(ValueError):
        parsear_alias(datos)
