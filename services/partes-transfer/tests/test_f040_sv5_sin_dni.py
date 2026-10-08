# tests/test_f040_sv5_sin_dni.py
"""F-040 · R22: sv5 escribe una linea SIN DNI con recurso casado (DA3).

Test de CARACTERIZACION: pasa contra el codigo de antes de F-040, que no
toca sv5 (decision del humano 2026-10-08: «si el recurso esta casado, sv5
no debera poner pega a que no tenga DNI»).

  - Una linea sin DNI con `recurso_ide` de la empresa de la obra y de alta a
    la fecha se escribe, tenga o no DNI el recurso (sv5 no lee `res.cla`,
    asi que tampoco mira si es persona: eso lo acotan sv3 y sv4).
  - De baja, de otra empresa o inexistente: su motivo de hoy.
  - Sin recurso y sin DNI: «sin recurso casado», como hoy.

Sin red ni Sigrid: `SigridFake`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.coherencia_recurso import verificar_recurso
from application.services.reglas_registro import (
    MOTIVO_RECURSO_BAJA,
    MOTIVO_RECURSO_NO_EXISTE,
    MOTIVO_RECURSO_OTRA_EMPRESA,
    MOTIVO_SIN_RECURSO,
)
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    RecursoSigrid,
)
from tests.dobles import SettingsFake, SigridFake

FECHA = 20260925
EMPRESA = 28
CIF = "09876543B"

RECURSOS = {
    950: RecursoSigrid(950, EMPRESA, 0, None),        # sin DNI, de alta
    951: RecursoSigrid(951, EMPRESA, None, ""),       # sin DNI (vacio)
    952: RecursoSigrid(952, EMPRESA, 0, CIF),         # con DNI
    953: RecursoSigrid(953, EMPRESA, FECHA, None),     # de baja ese dia
    954: RecursoSigrid(954, 1, 0, None),              # otra empresa
}


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=724, codigo="0724", nombre="Obra", empresa=EMPRESA)
    o.cenide = 77
    return o


def _horas() -> dict:
    return {ide: [HoraRecurso(horide=1, cod="HL01", res=None, pre=10.0,
                              caa_cod=None, defecto=True),
                  HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0)]
            for ide in RECURSOS}


def _linea(registro_id: int, recurso_ide: int | None,
           dni: str | None = None) -> LineaEntrada:
    return LineaEntrada(registro_id=registro_id, fecha_int=FECHA,
                        recurso_ide=recurso_ide, dni=dni, nombre="Persona",
                        tipo_hora="normal", horas=8.0)


def _ejecutar(lineas: list[LineaEntrada]):
    cli = SigridFake(obras={"0724": _obra()}, horas=_horas(),
                     recursos=dict(RECURSOS))
    return RegistroPipeline(cliente=cli, settings=SettingsFake()).ejecutar(
        obra=_obra(), lineas=lineas)


@pytest.mark.parametrize("recurso", [950, 951, 952])
@pytest.mark.parametrize("dni", [None, ""])
def test_f040_r22_linea_sin_dni_con_recurso_valido_se_escribe(recurso,
                                                              dni) -> None:
    r = _ejecutar([_linea(1, recurso, dni)])
    assert [e["registro_id"] for e in r.escritas] == [1]
    assert r.omitidas == []


@pytest.mark.parametrize("recurso, motivo", [
    (953, MOTIVO_RECURSO_BAJA),
    (954, MOTIVO_RECURSO_OTRA_EMPRESA),
    (999, MOTIVO_RECURSO_NO_EXISTE),
])
def test_f040_r22_linea_sin_dni_con_recurso_no_valido_su_motivo(
        recurso, motivo) -> None:
    r = _ejecutar([_linea(1, recurso)])
    assert r.escritas == []
    assert {o["registro_id"]: o["motivo"] for o in r.omitidas} == {1: motivo}


def test_f040_r22_sin_recurso_ni_dni_sin_recurso_casado() -> None:
    r = _ejecutar([_linea(1, None)])
    assert r.escritas == []
    assert {o["registro_id"]: o["motivo"] for o in r.omitidas} == \
        {1: MOTIVO_SIN_RECURSO}


@pytest.mark.parametrize("dni", [None, "", "  "])
def test_f040_r22_verificar_recurso_no_mira_el_dni_de_un_recurso_sin_dni(
        dni) -> None:
    for recurso in (950, 951, 952):
        assert verificar_recurso(RECURSOS[recurso], EMPRESA, FECHA,
                                 dni) is None
