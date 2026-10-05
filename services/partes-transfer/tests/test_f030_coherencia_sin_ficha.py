# tests/test_f030_coherencia_sin_ficha.py
"""F-030 · R17 y R21: sv5 con un recurso de una «ficha de recurso».

Tests de CARACTERIZACION (T1): pasan contra el codigo de hoy; sv5 no
cambia en F-030 (DA9, lista cerrada intacta).

  - R17: un recurso `MO/` con `res.conide` 0 (sin ficha de empleado) lee su
    DNI de `res.cif` (el `LEFT JOIN emp` no encuentra ficha) y la
    verificacion de empresa, alta y persona pasa cuando la linea trae
    `empleado_dni` = ese `res.cif` (sv3 lo guarda tal cual, R12).
  - R21: un recurso sin cuenta en ninguna fila de `reshor` (todos los de la
    empresa 28 hoy) se escribe con `caa_ide = 0`, motivo
    `recurso_sin_cuenta` y sin aviso (F-021 R3).

Sin red ni Sigrid: sigrid-api simulado y `SigridFake`. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

import httpx
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.coherencia_recurso import verificar_recurso
from application.services.cuenta_analitica import MOTIVO_RECURSO_SIN_CUENTA
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    RecursoSigrid,
)
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests.dobles import SettingsFake, SigridFake

CIF = "09876543B"
FECHA = 20260925
CENTRO = 77


class SigridApiFalso:
    """sigrid-api en memoria: una respuesta por lectura."""

    def __init__(self, columnas, *respuestas) -> None:
        self.columnas = columnas
        self.respuestas = list(respuestas)
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        filas = self.respuestas.pop(0) if self.respuestas else []
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": False})


def _obra_28() -> ObraEntrada:
    o = ObraEntrada(ide=724, codigo="0724", nombre="Obra Porsan", empresa=28)
    o.cenide = CENTRO
    return o


# ============================== R17 ===================================== #

def test_f030_r17_cliente_el_dni_de_un_recurso_sin_ficha_es_su_cif(
        monkeypatch) -> None:
    """Lo que devuelve Sigrid para `conide` 0: el `CASE` cae en `res.cif`."""
    falso = SigridApiFalso(["reside", "emp", "fecbaj", "dni"],
                           [[950, 28, 0, CIF]])
    monkeypatch.setattr(modulo.httpx, "post", falso)
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="clave-de-test", database="bd")
    datos = cli.datos_recursos([950])
    assert datos == {950: RecursoSigrid(950, 28, 0, CIF)}
    sql = " ".join(falso.lecturas[0]["sql"].split())
    assert "LEFT JOIN emp ON emp.ide = res.conide" in sql
    assert "ELSE res.cif END AS dni" in sql
    assert verificar_recurso(datos[950], 28, FECHA, CIF) is None


def test_f030_r17_la_verificacion_falla_si_el_recurso_no_vale() -> None:
    """Control: con otra empresa, de baja u otra persona no pasa."""
    rec = RecursoSigrid(950, 28, 0, CIF)
    assert verificar_recurso(rec, 1, FECHA, CIF) is not None
    assert verificar_recurso(RecursoSigrid(950, 28, FECHA, CIF), 28, FECHA,
                             CIF) is not None
    assert verificar_recurso(rec, 28, FECHA, "11111111H") is not None


def test_f030_r17_pipeline_escribe_la_linea_del_recurso_sin_ficha() -> None:
    horas = {950: [HoraRecurso(horide=1, cod="HL01", res=None, pre=10.0,
                               caa_cod=None, defecto=True),
                   HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0)]}
    cli = SigridFake(obras={"0724": _obra_28()}, horas=horas,
                     recursos={950: RecursoSigrid(950, 28, 0, CIF)})
    linea = LineaEntrada(registro_id=1, fecha_int=FECHA, recurso_ide=950,
                         dni=CIF, nombre="Persona", tipo_hora="normal",
                         horas=8.0)
    r = RegistroPipeline(cliente=cli, settings=SettingsFake()).ejecutar(
        obra=_obra_28(), lineas=[linea])
    assert [e["registro_id"] for e in r.escritas] == [1]
    assert r.omitidas == []
    assert cli.recursos_leidos == [[950]]


# ============================== R21 ===================================== #

def _horas_sin_cuenta() -> dict:
    return {950: [HoraRecurso(horide=1, cod="HL01", res=None, pre=10.0,
                              caa_cod=None, defecto=True),
                  HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0)]}


def _cli_28() -> SigridFake:
    return SigridFake(obras={"0724": _obra_28()}, horas=_horas_sin_cuenta(),
                      recursos={950: RecursoSigrid(950, 28, 0, CIF)},
                      cuentas=[(CENTRO, 28, 701, "0724.LAB")])


def _lineas() -> list[LineaEntrada]:
    return [LineaEntrada(registro_id=1, fecha_int=FECHA, recurso_ide=950,
                         dni=CIF, nombre="Persona", tipo_hora="normal",
                         horas=8.0),
            LineaEntrada(registro_id=2, fecha_int=FECHA, recurso_ide=950,
                         dni=CIF, nombre="Persona", tipo_hora="extra",
                         horas=1.0)]


def test_f030_r21_preflight_cuenta_cero_recurso_sin_cuenta_sin_aviso() -> None:
    pf = RegistroPipeline(cliente=_cli_28(), settings=SettingsFake()) \
        .preflight(obra=_obra_28(), lineas=_lineas())
    assert {a.registro_id: (a.accion, a.caa_ide, a.caa_cod, a.caa_motivo,
                            a.caa_aviso) for a in pf.acciones} == {
        1: ("escribir", 0, None, MOTIVO_RECURSO_SIN_CUENTA, None),
        2: ("escribir", 0, None, MOTIVO_RECURSO_SIN_CUENTA, None)}


def test_f030_r21_el_insert_lleva_caaide_cero(caplog) -> None:
    cli = _cli_28()
    with caplog.at_level(logging.INFO):
        r = RegistroPipeline(cliente=cli, settings=SettingsFake()).ejecutar(
            obra=_obra_28(), lineas=_lineas())
    assert sorted(e["registro_id"] for e in r.escritas) == [1, 2]
    assert {l["caaide"] for l in cli.lineas} == {0}
    assert [e["caa_cod"] for e in r.escritas] == [None, None]
    assert "cuentas obra=0724 ok=0 recurso_sin_cuenta=2" in caplog.text
