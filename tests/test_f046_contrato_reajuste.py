# tests/test_f046_contrato_reajuste.py
"""Contrato de F-046 entre servicios (R20, R33, R35).

  - Lo que sv4 manda a sv5 (`reparto_aviso.payload_reajuste` mas el
    usuario) lo acepta `ReajusteIn` de sv5 y llega igual a `OpReajuste`.
  - El recalculo que pide sv4 con `MOTIVO_REAJUSTE` sv3 lo clasifica como
    recalculo (mismo contrato que F-042).

Los paquetes de los servicios se llaman igual (`application`...), asi que
cada lado corre en un SUBPROCESO con `cwd` en su servicio, como el guardian
de F-024. Sin red ni BBDD; datos sinteticos.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SV3 = RAIZ / "services" / "partes-persistencia"
SV4 = RAIZ / "services" / "partes-front"
SV5 = RAIZ / "services" / "partes-transfer"

FILAS = [
    {"id": 7, "cambios": [
        {"registro_id": 11, "base_registro_id": 11, "tipo": "ordinaria",
         "antes": 8.0, "despues": 2.5, "sigrid_estado": "registrado"},
        {"registro_id": 12, "base_registro_id": 11, "tipo": "extra",
         "antes": -4.0, "despues": 1.5, "sigrid_estado": "registrado"}]},
    {"id": 8, "cambios": [
        {"registro_id": 21, "base_registro_id": 21, "tipo": "ordinaria",
         "antes": 8.0, "despues": 5.5, "sigrid_estado": "registrado"},
        {"registro_id": None, "base_registro_id": 21, "tipo": "extra",
         "antes": 0.0, "despues": 2.5, "sigrid_estado": "registrado",
         "recurso_ide": 501, "fecha_int": 20261014, "hora_ide": 9,
         "hora_codigo": "HE01", "partida_ide": 33, "partida_cod": "P-33",
         "obra_ide": 678, "obra_codigo": "0678"}]},
]
RESERVAS = {7: {}, 8: {"21": 990000001}}

_SV4_PAYLOADS = """
import json, sys
from application.services.reparto_aviso import payload_reajuste
filas = json.loads(sys.argv[1]); reservas = json.loads(sys.argv[2])
out = []
for f in filas:
    p = payload_reajuste(f, reservas[str(f["id"])])
    p["usuario"] = "admin@test"
    out.append(p)
print(json.dumps(out))
"""

_SV5_VALIDA = """
import json, sys
from domain.models.registro_models import OpReajuste
from interface_adapters.api.app import ReajusteIn
out = []
for p in json.loads(sys.argv[1]):
    r = ReajusteIn(**p)
    ops = [OpReajuste(**l.model_dump()) for l in r.lineas]
    out.append({"usuario": r.usuario, "ops": [
        [o.registro_id, o.antes, o.despues, o.es_nueva, o.base_registro_id,
         o.recurso_ide, o.fecha_int, o.hora_ide, o.hora_codigo,
         o.partida_ide, o.obra_ide, o.obra_codigo] for o in ops]})
print(json.dumps(out))
"""

_SV4_MENSAJE = """
import json
from datetime import datetime, timezone
from infrastructure.persistencia.recalculo_publisher import (
    MOTIVO_REAJUSTE, mensaje_recalculo)
print(json.dumps(mensaje_recalculo(
    document_id="doc-1", motivo=MOTIVO_REAJUSTE, solicitado_por="a",
    ahora=datetime(2026, 10, 14, tzinfo=timezone.utc))))
"""

_SV3_CLASIFICA = """
import json, sys
from interface_adapters.workers.mensajes import CLASE_RECALCULO, clasificar
print(json.dumps(clasificar(json.loads(sys.argv[1])) == CLASE_RECALCULO))
"""


def _correr(servicio: Path, codigo: str, *args: str):
    salida = subprocess.run(
        [sys.executable, "-c", codigo, *args], cwd=servicio,
        capture_output=True, text=True, timeout=120, check=False)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def payloads() -> list[dict]:
    return _correr(SV4, _SV4_PAYLOADS, json.dumps(FILAS),
                   json.dumps({str(k): v for k, v in RESERVAS.items()}))


def test_f046_r33_lo_que_manda_sv4_lo_acepta_sv5(payloads):
    validados = _correr(SV5, _SV5_VALIDA, json.dumps(payloads))
    assert [v["usuario"] for v in validados] == ["admin@test"] * 2
    assert validados[0]["ops"] == [
        [11, 8.0, 2.5, False, None, None, None, None, None, None, None,
         None],
        [12, -4.0, 1.5, False, None, None, None, None, None, None, None,
         None]]
    assert validados[1]["ops"][1] == [
        990000001, None, 2.5, True, 21, 501, 20261014, 9, "HE01", 33, 678,
        "0678"]


def test_f046_r20_el_contrato_no_se_lleva_campos_que_sv5_ignore(payloads):
    """Cada clave que manda sv4 es un campo de `LineaReajusteIn`: si sv4
    anadiera una que sv5 no conoce, pydantic la tiraria en silencio."""
    campos = set(_correr(SV5, (
        "import json\n"
        "from interface_adapters.api.app import LineaReajusteIn\n"
        "print(json.dumps(sorted(LineaReajusteIn.model_fields)))\n")))
    for p in payloads:
        for linea in p["lineas"]:
            assert set(linea) <= campos, set(linea) - campos


def test_f046_r35_sv3_clasifica_como_recalculo_el_motivo_nuevo():
    mensaje = _correr(SV4, _SV4_MENSAJE)
    assert mensaje["motivo"] == "reajuste_reparto"
    assert _correr(SV3, _SV3_CLASIFICA, json.dumps(mensaje)) is True
