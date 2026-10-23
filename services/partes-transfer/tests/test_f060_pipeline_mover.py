# tests/test_f060_pipeline_mover.py
"""F-060 · El CIZ de la racha se mueve en el pipeline de registro (R13-R27)
y en el doble `SigridFake` (design §5, §8).

  - Contrato y ajustes: `racha_registro_ids` llega por los dos canales
    (HTTP y cola) y `MOVER_CIZ` va apagado por defecto (R26, DA11).
  - Doble: `lineas_de_racha` y la op `mover` evaluan el `UPDATE` de
    `stmt_mover_linea` como SQL Server (WHERE optimista y guardas).
  - Pipeline: paso 6 bis (R13-R19, R25, R26) y paso 9 (R20-R24) con el
    ejemplo del humano dia a dia, el cambio de mes, la carrera y la
    reentrega.

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from config.settings import Settings
from domain.models.registro_models import (
    AccionLinea,
    HoraRecurso,
    LineaEntrada,
    LineaSigrid,
    ObraEntrada,
)
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
from interface_adapters.queue import transfer_consumer
from tests.dobles import SettingsFake, SigridFake

OBRA = 10
REC = 501
HN, CIV, CIZ = 1, 30, 40
HMO_SEP, HMO_OCT = 900, 901          # partes de septiembre y octubre
REGISTRO, CERRADO = 1, 3


def _obra(ide=OBRA, cod="0100", empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = 77
    return o


def _h(horide, cod, pre=0.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=None, defecto=False)


HORAS = {REC: [_h(HN, "HL01", 15.0), _h(2, "HE01", 25.0), _h(CIV, "CIV"),
               _h(CIZ, "CIZ")]}


# ------------------------- contrato y ajustes ------------------------- #

ENTORNO_MINIMO = {
    "SIGRID_API_BASE_URL": "http://sigrid.invalido",
    "SIGRID_API_FUNCTION_KEY": "clave-de-test",
}


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    for k, v in ENTORNO_MINIMO.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("MOVER_CIZ", raising=False)
    monkeypatch.chdir(tmp_path)
    return monkeypatch


def test_f060_r26_settings_mover_ciz_apagado_por_defecto(entorno) -> None:
    assert Settings().mover_ciz is False


@pytest.mark.parametrize("valor,esperado", [("true", True), ("1", True),
                                            ("false", False), ("0", False)])
def test_f060_r26_settings_mover_ciz_del_entorno(entorno, valor,
                                                 esperado) -> None:
    entorno.setenv("MOVER_CIZ", valor)
    assert Settings().mover_ciz is esperado


def test_f060_contrato_modelos_con_defecto() -> None:
    a = LineaEntrada(registro_id=1, fecha_int=20261004)
    b = LineaEntrada(registro_id=2, fecha_int=20261004)
    assert a.racha_registro_ids == [] and b.racha_registro_ids == []
    a.racha_registro_ids.append(9)
    assert b.racha_registro_ids == []          # sin lista compartida
    acc = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=10,
                      fecha_int=20261004)
    assert acc.mover is None
    ls = LineaSigrid(ide=1, reside=REC, fecha_int=20261004, horide=CIZ,
                     hora_codigo="CIZ", can=0.0, tot=0.0, synckey=None)
    assert ls.tex is None and ls.pos is None


class _PipelineEspia:
    """Apunta las lineas que le llegan (HTTP y cola) sin tocar Sigrid."""

    def __init__(self) -> None:
        self.lineas: list[LineaEntrada] = []

    def ejecutar(self, *, obra, lineas, pisar_claves=None, usuario=None):
        from domain.models.registro_models import ResultadoRegistro
        self.lineas.extend(lineas)
        return ResultadoRegistro(ok=True, obra_destino=obra,
                                 forzada_pruebas=False)


PETICION = {
    "obra": {"ide": OBRA, "codigo": "0100", "nombre": "Obra Uno"},
    "lineas": [
        {"registro_id": 4, "fecha_int": 20261004, "recurso_ide": REC,
         "es_incidencia": True, "incidencia_rol": "fin",
         "racha_registro_ids": [2, 3]},
        {"registro_id": 5, "fecha_int": 20261005, "recurso_ide": REC,
         "tipo_hora": "normal", "horas": 8.0}],
    "pisar_claves": [], "usuario": "ana",
}


def test_f060_contrato_http_trae_racha_registro_ids() -> None:
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    r = TestClient(app).post("/api/registro/ejecutar", json=PETICION)
    assert r.status_code == 200
    assert [l.racha_registro_ids for l in espia.lineas] == [[2, 3], []]


def test_f060_contrato_cola_trae_racha_registro_ids() -> None:
    _obra_d, lineas = transfer_consumer._a_dominio(PETICION)
    assert [l.racha_registro_ids for l in lineas] == [[2, 3], []]


def test_f060_contrato_payload_viejo_sin_la_clave() -> None:
    """Un sv4 anterior a F-060 no manda la clave: lista vacia (R26)."""
    viejo = {"obra": PETICION["obra"],
             "lineas": [{"registro_id": 4, "fecha_int": 20261004}]}
    _obra_d, lineas = transfer_consumer._a_dominio(viejo)
    assert lineas[0].racha_registro_ids == []
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    TestClient(app).post("/api/registro/ejecutar", json=viejo)
    assert espia.lineas[0].racha_registro_ids == []
