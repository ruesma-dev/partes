# tests/test_f056_contrato_franquicia.py
"""Contrato de F-056 entre sv4 y sv5 (R36, R41, R43).

  - Lo que sv4 manda a `/api/franquicia/comprobar` y `/ejecutar`
    (`franquicia.payload_franquicia` + `TransferClient`) lo acepta
    `FranquiciaIn` de sv5 y llega igual a `PeticionFranquicia`, SIN X
    (R41: la lee sv5 del campo extendido del recurso).
  - Lo que sv4 manda a `/api/franquicia/recursos` lo acepta
    `FranquiciaRecursosIn` (R43).
  - Ninguna clave que manda sv4 la tira pydantic en silencio.

Los paquetes de los servicios se llaman igual (`application`...), asi que
cada lado corre en un SUBPROCESO con `cwd` en su servicio, como el
contrato de F-046. Sin red ni BBDD (el `httpx.post` de sv4 se sustituye
por uno que solo apunta lo enviado); datos sinteticos.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SV4 = RAIZ / "services" / "partes-front"
SV5 = RAIZ / "services" / "partes-transfer"

#: Una fila de `franquicia_ajuste` (ejecutar) y una propuesta sin fila
#: (comprobar del preflight, `ajuste_id` 0), como las arma sv4.
DATOS = [
    {"id": 7, "recurso_ide": 501, "periodo": "2026-10",
     "fecha_int": 20261015, "obra_ide": 678, "obra_codigo": "0678",
     "partida_ide": 33, "partida_cod": "01.01", "franquicia": 8.0,
     "estado": "decidido"},
    {"recurso_ide": 502, "periodo": "2026-01", "fecha_int": 20260115,
     "obra_ide": None, "obra_codigo": "0404", "partida_ide": None,
     "partida_cod": None},
]

_SV4_ENVIOS = """
import json, sys
import httpx
from application.services import franquicia as fq
from infrastructure.transfer.transfer_client import TransferClient

enviados = []

class _Resp:
    status_code = 200
    text = "{}"
    def json(self):
        return {"ok": True}
    def raise_for_status(self):
        return None

def _post(url, json=None, timeout=None, **kw):
    enviados.append({"ruta": url.split("sv5.interno", 1)[1], "json": json})
    return _Resp()

httpx.post = _post
cli = TransferClient(base_url="http://sv5.interno")
datos = json.loads(sys.argv[1])
cli.franquicia_comprobar(fq.payload_franquicia(
    datos[1], extras_pendientes=2.5, usuario="admin@test"), timeout_s=5)
cli.franquicia_ejecutar(fq.payload_franquicia(datos[0], usuario="admin@test"))
cli.franquicia_recursos([501, 502], timeout_s=5)
print(json.dumps(enviados))
"""

_SV5_VALIDA = """
import json, sys
from dataclasses import asdict
from interface_adapters.api.app import FranquiciaIn, FranquiciaRecursosIn
out = {"peticiones": [], "recursos": None,
       "campos": sorted(FranquiciaIn.model_fields),
       "campos_recursos": sorted(FranquiciaRecursosIn.model_fields)}
for e in json.loads(sys.argv[1]):
    if e["ruta"] == "/api/franquicia/recursos":
        out["recursos"] = FranquiciaRecursosIn(**e["json"]).recurso_ides
    else:
        out["peticiones"].append(asdict(FranquiciaIn(**e["json"]).a_dominio()))
print(json.dumps(out))
"""


def _correr(servicio: Path, codigo: str, *args: str):
    salida = subprocess.run(
        [sys.executable, "-c", codigo, *args], cwd=servicio,
        capture_output=True, text=True, timeout=120, check=False)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def envios() -> list[dict]:
    return _correr(SV4, _SV4_ENVIOS, json.dumps(DATOS))


@pytest.fixture(scope="module")
def validados(envios) -> dict:
    return _correr(SV5, _SV5_VALIDA, json.dumps(envios))


def test_f056_r36_sv4_llama_a_las_tres_rutas_de_sv5(envios):
    assert [e["ruta"] for e in envios] == [
        "/api/franquicia/comprobar", "/api/franquicia/ejecutar",
        "/api/franquicia/recursos"]


def test_f056_r36_lo_que_manda_sv4_lo_acepta_franquicia_in(validados):
    comprobar, ejecutar = validados["peticiones"]
    assert (comprobar["ajuste_id"], comprobar["recurso_ide"],
            comprobar["periodo"], comprobar["inicio"], comprobar["fin"],
            comprobar["fecha_int"], comprobar["extras_pendientes"],
            comprobar["usuario"]) == (
        0, 502, "2026-01", 20251216, 20260115, 20260115, 2.5, "admin@test")
    assert comprobar["obra"]["codigo"] == "0404"
    assert comprobar["obra"]["ide"] is None
    assert (ejecutar["ajuste_id"], ejecutar["recurso_ide"],
            ejecutar["inicio"], ejecutar["fin"], ejecutar["fecha_int"],
            ejecutar["partida_ide"], ejecutar["partida_cod"]) == (
        7, 501, 20260916, 20261015, 20261015, 33, "01.01")
    assert (ejecutar["obra"]["ide"], ejecutar["obra"]["codigo"]) == (
        678, "0678")


def test_f056_r41_sv4_no_manda_la_x(envios, validados):
    """La X la lee sv5 del campo extendido: ni sv4 la manda ni
    `FranquiciaIn` la tiene (un sv4 viejo que la mandara se ignoraria)."""
    for e in envios[:2]:
        assert "franquicia" not in e["json"]
    assert "franquicia" not in validados["campos"]


def test_f056_r36_ninguna_clave_de_sv4_se_pierde_en_sv5(envios, validados):
    """Cada clave que manda sv4 es un campo de `FranquiciaIn` (o de
    `FranquiciaRecursosIn`): si sv4 anadiera una que sv5 no conoce,
    pydantic la tiraria en silencio."""
    for e in envios[:2]:
        assert set(e["json"]) <= set(validados["campos"]), e["json"]
    assert set(envios[2]["json"]) <= set(validados["campos_recursos"])


def test_f056_r43_lo_que_manda_sv4_lo_acepta_franquicia_recursos_in(
        validados):
    assert validados["recursos"] == [501, 502]
