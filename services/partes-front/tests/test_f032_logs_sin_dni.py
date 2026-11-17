# tests/test_f032_logs_sin_dni.py
"""F-032 · R3 (enmienda tras la review 1): ningun DNI llega a los logs de sv4.

Con F-032 sv4 llama de verdad a `GET /api/v1/jornada?dni=…`. Con el cliente
REAL (`SesameApiClient` sobre `httpx.MockTransport`, sin red), el
`CalendarioProvider` y la `configure_logging` REAL de sv4 en INFO, ningun
registro (de ningun logger, httpx incluido) ni el fichero de log pueden
llevar el DNI: ni con 200, ni con 404, ni en el WARNING de
`jornada_contrato` cuando Sesame falla y su cuerpo repite el DNI. DNI
sintetico.
"""
from __future__ import annotations

import logging

import httpx
import pytest

from application.services.calendario_provider import CalendarioProvider
from config.logging_config import configure_logging
from infrastructure.sesame.sesame_api_client import SesameApiClient
from tests.fixtures_sesame import JORNADA

DNI = "12345678Z"
CLAVE = "clave-de-prueba-no-es-un-secreto"


class _Captura(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.registros: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.registros.append(record)

    def textos(self) -> list[str]:
        return [f"{r.name} | {r.getMessage()}" for r in self.registros]


@pytest.fixture
def logging_real(tmp_path):
    """`configure_logging` de sv4 en INFO; deja el logging como estaba."""
    raiz = logging.getLogger()
    antes = (list(raiz.handlers), raiz.level,
             logging.getLogger("httpx").level,
             logging.getLogger("httpcore").level)
    configure_logging(tmp_path, "INFO")
    captura = _Captura()
    raiz.addHandler(captura)
    yield captura, tmp_path / "partes_portal.log"
    for h in list(raiz.handlers):
        raiz.removeHandler(h)
        if h not in antes[0]:
            h.close()
    for h in antes[0]:
        raiz.addHandler(h)
    raiz.setLevel(antes[1])
    logging.getLogger("httpx").setLevel(antes[2])
    logging.getLogger("httpcore").setLevel(antes[3])


def _proveedor(respuesta: httpx.Response) -> CalendarioProvider:
    cliente = SesameApiClient(
        base_url="http://sesame.local", api_key=CLAVE,
        transport=httpx.MockTransport(lambda request: respuesta))
    return CalendarioProvider(cliente=cliente,
                              respaldo_holiday_name=lambda d: None,
                              leer_festivos=lambda: [])


def _sin_dni(captura, fichero) -> None:
    for h in logging.getLogger().handlers:
        h.flush()
    for texto in captura.textos():
        assert DNI not in texto, texto
    assert DNI not in fichero.read_text(encoding="utf-8")


@pytest.mark.parametrize("respuesta, hay_jornada", [
    (httpx.Response(200, json=JORNADA), True),
    (httpx.Response(404, json={"detail": f"empleado con DNI {DNI} no "
                                         "encontrado en Sesame"}), False),
], ids=["200", "404"])
def test_f032_r3_la_jornada_real_no_deja_dnis_en_los_logs(
        logging_real, respuesta, hay_jornada) -> None:
    captura, fichero = logging_real
    jornada = _proveedor(respuesta).jornada_contrato(DNI)
    assert (jornada is not None) is hay_jornada
    _sin_dni(captura, fichero)


def test_f032_r3_el_warning_de_jornada_no_lleva_dni_ni_la_excepcion(
        logging_real) -> None:
    captura, fichero = logging_real
    respuesta = httpx.Response(500, text=f"error interno consultando {DNI}")
    assert _proveedor(respuesta).jornada_contrato(DNI) is None
    avisos = [r for r in captura.registros if r.levelno >= logging.WARNING]
    assert avisos, "un fallo de Sesame deja un WARNING"
    assert any("RuntimeError" in r.getMessage() for r in avisos)
    assert not any("error interno" in r.getMessage() for r in avisos)
    _sin_dni(captura, fichero)


def test_f032_r3_la_configuracion_de_sv4_silencia_httpx(logging_real) -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
