# tests/test_f032_logs_sin_dni.py
"""F-032 · R3 (enmienda tras la review 1): ningun DNI llega a los logs de sv3.

El refresco de la ingesta pide `GET /api/v1/festivos?dni=…`. Con el cliente
REAL (`SesameApiClient` sobre `httpx.MockTransport`, sin red) y la
`configure_logging` REAL de sv3 en INFO, ningun registro (de ningun logger,
httpx incluido) ni el fichero de log pueden llevar el DNI: ni con 200, ni con
404, ni cuando Sesame falla y su cuerpo repite el DNI. DNI sintetico.
"""
from __future__ import annotations

import datetime as dt
import logging

import httpx
import pytest

from application.services.refresco_festivos import RefrescoFestivos
from config.logging_config import configure_logging
from infrastructure.sesame.sesame_api_client import SesameApiClient
from tests.fixtures_sesame import FESTIVOS_DNI

DNI = "12345678Z"
CLAVE = "clave-de-prueba-no-es-un-secreto"


class _Captura(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.textos: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.textos.append(f"{record.name} | {record.getMessage()}")


@pytest.fixture
def logging_real(tmp_path):
    """`configure_logging` de sv3 en INFO; deja el logging como estaba."""
    raiz = logging.getLogger()
    antes = (list(raiz.handlers), raiz.level,
             logging.getLogger("httpx").level,
             logging.getLogger("httpcore").level)
    configure_logging(tmp_path, "INFO")
    captura = _Captura()
    raiz.addHandler(captura)
    yield captura, tmp_path / "partes_persister.log"
    for h in list(raiz.handlers):
        raiz.removeHandler(h)
        if h not in antes[0]:
            h.close()
    for h in antes[0]:
        raiz.addHandler(h)
    raiz.setLevel(antes[1])
    logging.getLogger("httpx").setLevel(antes[2])
    logging.getLogger("httpcore").setLevel(antes[3])


class _Repo:
    def __init__(self):
        self.filas: dict = {}

    def leer_todas(self):
        return dict(self.filas)

    def guardar(self, fila):
        self.filas[(fila.dni_norm, fila.ano)] = fila


def _refrescar(respuesta: httpx.Response):
    cliente = SesameApiClient(
        base_url="http://sesame.local", api_key=CLAVE,
        transport=httpx.MockTransport(lambda request: respuesta))
    return RefrescoFestivos(
        cliente=cliente, repositorio=_Repo(), minimo=1,
        ahora_utc=lambda: dt.datetime(2026, 11, 17, tzinfo=dt.timezone.utc),
    ).refrescar([DNI], {2026})


def _sin_dni(captura, fichero) -> None:
    for h in logging.getLogger().handlers:
        h.flush()
    assert captura.textos, "el refresco deberia dejar al menos un registro"
    for texto in captura.textos:
        assert DNI not in texto, texto
    assert DNI not in fichero.read_text(encoding="utf-8")


@pytest.mark.parametrize("respuesta, campo", [
    (httpx.Response(200, json=FESTIVOS_DNI), "guardadas"),
    (httpx.Response(404, json={"detail": f"empleado con DNI {DNI} no "
                                         "encontrado en Sesame"}),
     "sin_calendario"),
    (httpx.Response(500, text=f"error interno consultando {DNI}"),
     "sin_dato"),
], ids=["200", "404", "500"])
def test_f032_r3_el_refresco_real_no_deja_dnis_en_los_logs(
        logging_real, respuesta, campo) -> None:
    captura, fichero = logging_real
    res = _refrescar(respuesta)
    assert getattr(res, campo) == 1
    _sin_dni(captura, fichero)


def test_f032_r3_la_configuracion_de_sv3_silencia_httpx(logging_real) -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
