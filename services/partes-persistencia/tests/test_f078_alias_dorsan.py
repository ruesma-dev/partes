# tests/test_f078_alias_dorsan.py
"""F-078: el membrete de Porsan leido como «Dorsan» se reconoce como la 28.

El OCR leyo «Dorsan S.L. E HIJOS CONSTRUCCIONES» (una D por la P) en partes
de Porsan de la obra 0730 (11-13/11/2026) y la empresa del membrete quedaba
desconocida. La solucion es de configuracion: la tabla VERSIONADA
`config/empresas_membrete.yaml` trae para la empresa 28 el alias DORSAN.

Como en F-029, estos tests cargan la tabla real (no una copia).
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
    "Dorsan S.L. E HIJOS CONSTRUCCIONES",   # lo que leyo el OCR
    "Porsan S.L. E HIJOS CONSTRUCCIONES",   # el nombre correcto sigue valiendo
    "PORSAN E HIJOS CONSTRUCCIONES, S.L.",
])
def test_f078_dorsan_y_porsan_son_la_empresa_28(texto) -> None:
    assert _resolutor_tabla_real().resolver(texto) == (28, "membrete")


def test_f078_dorsan_no_es_alias_de_la_empresa_1() -> None:
    alias = parsear_alias(yaml.safe_load(
        (RAIZ / "config" / "empresas_membrete.yaml").read_text("utf-8")))
    assert "DORSAN" in alias[28]
    assert all(a.upper() != "DORSAN" for a in alias[1])


@pytest.mark.parametrize("texto", ["ruΞsma", "Construcciones Ruesma S.A."])
def test_f078_ruesma_sigue_siendo_la_empresa_1(texto) -> None:
    assert _resolutor_tabla_real().resolver(texto) == (1, "membrete")


def test_f078_ruesma_con_dorsan_da_varias() -> None:
    assert _resolutor_tabla_real().resolver(
        "ruΞsma Dorsan S.L. E HIJOS CONSTRUCCIONES") == (None, "varias")
