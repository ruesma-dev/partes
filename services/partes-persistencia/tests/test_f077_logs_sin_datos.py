# tests/test_f077_logs_sin_datos.py
"""F-077 · R18: ni DNI, ni nombre, ni email, ni token, ni id en los logs de sv3.

Con la `configure_logging` REAL de sv3 en INFO, el cliente y el adaptador
REALES sobre `httpx.MockTransport` (solo GET) y `RefrescoFestivos`, en
todos los caminos: indice en dos paginas; 200; no encontrado; 404 de
festivos; 429 seguido de 200; 500 agotado; error de red; 401. Ningun
registro (de ningun logger, httpx incluido), ni el fichero de log, ni el
texto de las excepciones pueden llevar el DNI (crudo o normalizado), el
nombre, el apellido, el email, el token ni el id de empleado. Las
respuestas de error REPITEN esos datos a proposito. Datos ficticios.
(capa: integracion)
"""
from __future__ import annotations

import datetime as dt
import logging

import httpx
import pytest

from application.services.refresco_festivos import RefrescoFestivos
from config.logging_config import configure_logging
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import SesameHrClient
from tests.fixtures_sesame import (
    BASE_URL,
    DNI_A,
    DNI_AUSENTE,
    EMPLEADOS_P1,
    EMPLEADOS_P2,
    FESTIVOS_A_2026,
    ID_A,
    ID_B,
    ID_C,
    ID_C_INACTIVO,
    PERSONALES,
    TOKEN,
    Dormir,
    SesameHrFalso,
    secuencia,
)

#: Todo lo que no puede aparecer (R18).
PROHIBIDOS = (DNI_A, "12.345.678-z", "12.345.678-Z", DNI_AUSENTE, TOKEN,
              ID_A, ID_B, ID_C, ID_C_INACTIVO, *PERSONALES)

#: Un cuerpo de error que repite datos personales, como haria un proxy.
ECO = f"empleado {ID_A} dni {DNI_A} persona.a@ejemplo.test token {TOKEN}"


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


def _adaptador(sesame):
    cliente = SesameHrClient(base_url=BASE_URL, token=TOKEN,
                             transport=sesame.transport(), dormir=Dormir())
    return FestivosSesameHr(cliente=cliente)


ESCENARIOS = {
    "200": ({ID_A: FESTIVOS_A_2026}, DNI_A, "guardadas"),
    "no-encontrado": ({}, DNI_AUSENTE, "sin_calendario"),
    "404-festivos": ({ID_A: httpx.Response(404, text=ECO)}, DNI_A,
                     "sin_dato"),
    "429-y-200": ({ID_A: secuencia(
        httpx.Response(429, text=ECO, headers={"Retry-After": "1"}),
        FESTIVOS_A_2026)}, DNI_A, "guardadas"),
    "500-agotado": ({ID_A: lambda r: httpx.Response(500, text=ECO)}, DNI_A,
                    "sin_dato"),
    "red": ({ID_A: lambda r: httpx.ConnectError(f"{r.url} {ECO}")}, DNI_A,
            "sin_dato"),
    "401": ({ID_A: httpx.Response(401, text=ECO)}, DNI_A, "sin_dato"),
}


def _limpio(texto: str) -> None:
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, (prohibido, texto)


@pytest.mark.parametrize("nombre", list(ESCENARIOS))
def test_f077_r18_el_refresco_real_no_deja_datos_personales(
        logging_real, nombre) -> None:
    captura, fichero = logging_real
    festivos, dni, campo = ESCENARIOS[nombre]
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, EMPLEADOS_P2],
                           festivos=festivos)
    res = RefrescoFestivos(
        cliente=_adaptador(sesame), repositorio=_Repo(), minimo=1,
        ahora_utc=lambda: dt.datetime(2026, 11, 18, tzinfo=dt.timezone.utc),
    ).refrescar([dni], {2026})
    assert getattr(res, campo) == 1
    assert sesame.rutas().count("/core/v3/employees") == 2   # dos paginas
    for h in logging.getLogger().handlers:
        h.flush()
    assert any("[sesame-hr] indice" in t for t in captura.textos)
    for texto in captura.textos:
        _limpio(texto)
    _limpio(fichero.read_text(encoding="utf-8"))


@pytest.mark.parametrize("nombre", ["404-festivos", "500-agotado", "red",
                                    "401"])
def test_f077_r18_el_texto_de_las_excepciones_tampoco(
        logging_real, nombre) -> None:
    festivos, dni, _ = ESCENARIOS[nombre]
    adaptador = _adaptador(SesameHrFalso(festivos=festivos))
    with pytest.raises(RuntimeError) as exc:
        adaptador.festivos(dni, 2026)
    _limpio(str(exc.value))
    _limpio(repr(exc.value))


def test_f077_r18_el_indice_caido_tampoco(logging_real) -> None:
    captura, fichero = logging_real
    sesame = SesameHrFalso(empleados=[
        EMPLEADOS_P1, httpx.Response(500, text=ECO)])
    with pytest.raises(RuntimeError) as exc:
        _adaptador(sesame).festivos(DNI_A, 2026)
    _limpio(str(exc.value))
    for h in logging.getLogger().handlers:
        h.flush()
    for texto in captura.textos:
        _limpio(texto)
    _limpio(fichero.read_text(encoding="utf-8"))


def test_f077_r18_la_configuracion_de_sv3_silencia_httpx(logging_real) -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
