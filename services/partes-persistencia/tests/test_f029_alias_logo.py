# tests/test_f029_alias_logo.py
"""F-029: el logotipo de Ruesma (ruΞsma) se reconoce como empresa 1.

El membrete de la plantilla de Ruesma es el logotipo «ruΞsma», con una Xi
griega en lugar de la E. `text_match.normalize` convierte toda letra no
latina en espacio, asi que «ruΞsma», «RUΞSMA» y «ru≡sma» quedan «ru sma» y
no casaban con el alias RUESMA: la empresa del membrete quedaba
desconocida (`sin_alias`). La solucion es de configuracion: la tabla
VERSIONADA `config/empresas_membrete.yaml` trae para la empresa 1 el alias
del logotipo (RUΞSMA, normalizado «ru sma»).

Estos tests cargan la tabla real (no una copia) para que un cambio en ella
que rompa el logotipo se vea aqui.

Que garantiza la regla de palabras completas para el alias nuevo: casa si
el texto normalizado contiene «ru» y «sma» como dos palabras SEGUIDAS.
Por eso no dispara con «Rusma» (una sola palabra), «ru smart» (sma no es
palabra completa), «Peru Smash» ni «gru sma» (ru no es palabra completa).
No protege, en cambio, de un texto que traiga literalmente las palabras
«ru» y «sma» juntas («RU SMA», «ru-sma»): se acepta, porque no hay otra
empresa ni otro texto de parte conocido que lo produzca.
"""
from __future__ import annotations

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
]


def _resolutor_tabla_real() -> ResolutorEmpresa:
    datos = yaml.safe_load(
        (RAIZ / "config" / "empresas_membrete.yaml").read_text("utf-8"))
    return ResolutorEmpresa(parsear_alias(datos), EMPRESAS)


@pytest.mark.parametrize("texto", [
    "ruΞsma",                       # logotipo real (Xi griega minuscula)
    "RUΞSMA",                       # Xi griega mayuscula
    "ru≡sma",                       # el signo de identidad que a veces lee la IA
    "RUESMA",                       # el alias de siempre sigue valiendo
    "Construcciones Ruesma S.A.",
])
def test_f029_el_logotipo_y_el_nombre_de_ruesma_son_la_empresa_1(texto) -> None:
    assert _resolutor_tabla_real().resolver(texto) == (1, "membrete")


def test_f029_porsan_sigue_siendo_la_28() -> None:
    assert _resolutor_tabla_real().resolver(
        "PORSAN E HIJOS CONSTRUCCIONES, S.L.") == (28, "membrete")


def test_f029_logotipo_de_ruesma_con_nombre_de_porsan_da_varias() -> None:
    assert _resolutor_tabla_real().resolver(
        "ruΞsma PORSAN E HIJOS CONSTRUCCIONES, S.L.") == (None, "varias")


@pytest.mark.parametrize("texto", [
    "Rusma Obras",      # «rusma» es UNA palabra: no es «ru sma»
    "ru smart",         # «sma» no es palabra completa
    "Peru Smash",       # ni «ru» ni «sma» son palabras completas
    "gru sma",          # «ru» no es palabra completa
    "ru obras sma",     # las dos palabras, pero no seguidas
])
def test_f029_el_alias_del_logotipo_no_dispara_con_ru_o_sma_sueltos(
        texto) -> None:
    assert _resolutor_tabla_real().resolver(texto) == (None, "sin_alias")
