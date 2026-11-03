# tests/test_f052_contrato_motivos.py
"""Contrato de F-052 entre sv4 y sv3 (R23, DA15): el motivo `sincronizar`.

«Traer de Sigrid» (sv4) cambia horas de líneas congeladas y pide UN
recálculo compartido de extras (F-049) con el motivo `sincronizar`. El
motivo es solo traza: sv3 hace la misma pasada para todos. Este test ata
que lo que construye y publica sv4 con ese motivo sv3 lo clasifica como
recálculo (mismo contrato que F-042 y F-049). Los módulos se cargan POR
RUTA con nombres únicos (los paquetes de los servicios se llaman igual).
Sin red ni BBDD.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA_SV4 = (RAIZ / "services/partes-front/infrastructure/persistencia/"
            "recalculo_publisher.py")
RUTA_SV3 = (RAIZ / "services/partes-persistencia/interface_adapters/workers/"
            "mensajes.py")
AHORA = datetime(2026, 11, 3, 9, 30, tzinfo=timezone.utc)


def _cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def sv4():
    return _cargar(RUTA_SV4, "f052_contrato_sv4_recalculo_publisher")


@pytest.fixture(scope="module")
def sv3():
    return _cargar(RUTA_SV3, "f052_contrato_sv3_mensajes")


def test_f052_r23_el_motivo_tiene_su_valor(sv4) -> None:
    assert sv4.MOTIVO_SINCRONIZAR == "sincronizar"


def test_f052_r23_sv3_clasifica_como_recalculo_el_motivo(sv4, sv3) -> None:
    mensaje = sv4.mensaje_recalculo(
        document_id="doc-s", motivo=sv4.MOTIVO_SINCRONIZAR,
        solicitado_por="revisora@ejemplo.es", ahora=AHORA)
    por_la_cola = json.loads(json.dumps(mensaje, ensure_ascii=False))
    assert sv3.clasificar(por_la_cola) == sv3.CLASE_RECALCULO
    assert len(json.dumps(mensaje).encode("utf-8")) < 1024


def test_f052_r23_lo_que_publica_el_publisher_tambien(sv4, sv3) -> None:
    enviados: list[tuple[str, dict]] = []

    class Cola:
        def enviar(self, cola: str, payload: dict) -> None:
            enviados.append((cola, payload))

    sv4.RecalculoPublisher(cola=Cola(), cola_persistencia="q-persistencia",
                           reloj=lambda: AHORA).pedir(
        document_id="doc-s", motivo=sv4.MOTIVO_SINCRONIZAR,
        solicitado_por=None)
    (cola, payload), = enviados
    assert cola == "q-persistencia"
    assert payload["motivo"] == "sincronizar"
    assert sv3.clasificar(json.loads(json.dumps(payload))) \
        == sv3.CLASE_RECALCULO
