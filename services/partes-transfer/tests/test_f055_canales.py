# tests/test_f055_canales.py
"""F-055 · la guarda de fecha por los tres caminos (R8) y `fecha_int`
nulo o ausente (R9).

HTTP con `TestClient` sobre `build_app` y la cola `q-transfer` con el
montaje real de adaptadores sobre fakes del SDK (`Montaje`). Sin red.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from domain.models.registro_models import LineaEntrada
from interface_adapters.api.app import build_app
from interface_adapters.queue.transfer_consumer import _a_dominio
from tests.dobles import SettingsFake
from tests.test_f002_pipeline_fases import _pipeline, _sigrid
from tests.test_f002_transfer_consumer import Montaje, _peticion

SIN = "fecha_no_valida: la linea no tiene fecha; corrige la fecha en el " \
      "portal y reaprueba"
MES13 = "fecha_no_valida: 20261340 no es una fecha del calendario; " \
        "corrige la fecha en el portal y reaprueba"
VALIDA = {"registro_id": 1, "fecha_int": 20260302, "recurso_ide": 501,
          "tipo_hora": "normal", "horas": 8.0}


def _linea(rid, **cambios) -> dict:
    d = dict(VALIDA, registro_id=rid)
    d.update(cambios)
    return d


def _sin_clave(rid) -> dict:
    d = _linea(rid)
    del d["fecha_int"]
    return d


def _cuerpo(lineas) -> dict:
    return {"obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
            "lineas": lineas, "pisar_claves": [], "usuario": "ana"}


def _api(cli) -> TestClient:
    return TestClient(build_app(SettingsFake(), pipeline=_pipeline(cli)))


LOTE = [_linea(1), _linea(2, fecha_int=0), _linea(3, fecha_int=20261340)]
OMITIDAS = [{"registro_id": 2, "motivo": SIN},
            {"registro_id": 3, "motivo": MES13}]


# ------------------------------- R8 ------------------------------- #

def test_f055_r8_preflight_http() -> None:
    r = _api(_sigrid()).post("/api/registro/preflight", json=_cuerpo(LOTE))
    assert r.status_code == 200
    d = r.json()
    assert [(a["registro_id"], a["accion"], a["motivo"])
            for a in d["acciones"]] == [
        (1, "escribir", None), (2, "omitir", SIN), (3, "omitir", MES13)]
    assert d["resumen"]["omitir"] == 2 and d["resumen"]["escribir"] == 1
    assert [(p["ano"], p["mes"]) for p in d["partes"]] == [(2026, 3)]


def test_f055_r8_ejecutar_http() -> None:
    cli = _sigrid()
    r = _api(cli).post("/api/registro/ejecutar", json=_cuerpo(LOTE))
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert [e["registro_id"] for e in d["escritas"]] == [1]
    assert d["omitidas"] == OMITIDAS
    assert [(p["ano"], p["mes"]) for p in cli.partes] == [(2026, 3)]


def test_f055_r8_cola(monkeypatch) -> None:
    m = Montaje(monkeypatch, _sigrid(), peticion=_peticion(lineas=LOTE))
    m.handler(m.mensaje)
    r = m.resultado_publicado()["resultado"]
    assert r["ok"] is True
    assert [e["registro_id"] for e in r["escritas"]] == [1]
    assert r["omitidas"] == OMITIDAS
    assert [(p["ano"], p["mes"]) for p in m.sigrid.partes] == [(2026, 3)]


# ------------------------------- R9 ------------------------------- #

@pytest.mark.parametrize("ruta", ["preflight", "ejecutar"])
@pytest.mark.parametrize("invalida", ["null", "ausente"])
def test_f055_r9_null_y_ausente_http(ruta, invalida) -> None:
    linea = (_linea(2, fecha_int=None) if invalida == "null"
             else _sin_clave(2))
    cli = _sigrid()
    r = _api(cli).post(f"/api/registro/{ruta}",
                       json=_cuerpo([_linea(1), linea]))
    assert r.status_code == 200, r.text
    d = r.json()
    if ruta == "preflight":
        assert [(a["registro_id"], a["accion"], a["motivo"])
                for a in d["acciones"]] == [(1, "escribir", None),
                                            (2, "omitir", SIN)]
        assert d["resumen"]["omitir"] == 1
    else:
        assert d["ok"] is True
        assert [e["registro_id"] for e in d["escritas"]] == [1]
        assert d["omitidas"] == [{"registro_id": 2, "motivo": SIN}]


@pytest.mark.parametrize("invalida", ["null", "ausente"])
def test_f055_r9_null_y_ausente_cola(monkeypatch, invalida) -> None:
    linea = (_linea(2, fecha_int=None) if invalida == "null"
             else _sin_clave(2))
    m = Montaje(monkeypatch, _sigrid(),
                peticion=_peticion(lineas=[_linea(1), linea]))
    m.handler(m.mensaje)
    r = m.resultado_publicado()["resultado"]
    assert r["ok"] is True
    assert [e["registro_id"] for e in r["escritas"]] == [1]
    assert r["omitidas"] == [{"registro_id": 2, "motivo": SIN}]


def test_f055_r9_ano_mes_con_none() -> None:
    linea = LineaEntrada(1, None)
    assert (linea.ano, linea.mes) == (0, 0)
    assert LineaEntrada(registro_id=1).fecha_int is None


def test_f055_r9_ano_mes_con_fecha() -> None:
    linea = LineaEntrada(1, 20261014)
    assert (linea.ano, linea.mes) == (2026, 10)


def test_f055_r9_a_dominio_sin_la_clave() -> None:
    _o, lineas = _a_dominio(_cuerpo([_sin_clave(4)]))
    assert lineas[0].registro_id == 4 and lineas[0].fecha_int is None
