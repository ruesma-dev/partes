# tests/test_f058_obra_sigrid.py
"""F-058 · R7, R9, R10: la consulta de obra en el momento (DA10 = B).

- ``ComprobadorObra`` pregunta a sigrid-api, por cada página que lo necesite y
  sin caché, si hay alguna obra con esa clave; mide la duración con un reloj
  monotónico y deja un INFO ``[obra-sigrid]`` con ``document_id``, resultado
  y milisegundos, sin el código. Si la consulta falla, «no se sabe»
  (``existe=None``) con un WARNING con el tipo de error: nunca lanza.
- ``SigridLookupClient.existe_obra`` manda la clave como parámetro ``?`` (nunca
  dentro del SQL), con el tope de tiempo del argumento, y trata ``truncated``
  o un 4xx/5xx como error (F-038).

Sin red: ``httpx.MockTransport`` y dobles del puerto y del reloj.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from application.services.obra_sigrid import ComprobadorObra, ConsultaObra
from infrastructure.sigrid.sigrid_lookup_client import (
    MAX_ROWS_DEFECTO,
    SigridLookupClient,
)

LOGGER_OBRA = "application.services.obra_sigrid"
CODIGO = "09999"
CLAVE = "9999"
CLAVE_FALSA = "clave-falsa-de-test"


class PuertoDoble:
    """``ExistenciaObraPort`` que apunta las llamadas y responde o lanza."""

    def __init__(self, respuesta: bool = True,
                 error: Exception | None = None) -> None:
        self.respuesta = respuesta
        self.error = error
        self.llamadas: list[tuple[str, float]] = []

    def existe_obra(self, clave: str, *, timeout_s: float) -> bool:
        self.llamadas.append((clave, timeout_s))
        if self.error is not None:
            raise self.error
        return self.respuesta


class RelojFalso:
    """Devuelve los instantes dados, en orden."""

    def __init__(self, *instantes: float) -> None:
        self.instantes = list(instantes)

    def __call__(self) -> float:
        return self.instantes.pop(0)


def _comprobador(puerto: PuertoDoble, *instantes: float,
                 timeout_s: float = 5.0) -> ComprobadorObra:
    reloj = RelojFalso(*(instantes or (100.0, 100.25)))
    return ComprobadorObra(client=puerto, timeout_s=timeout_s, reloj=reloj)


def _mensajes(caplog, nivel: int) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == LOGGER_OBRA and r.levelno == nivel]


# --------------------------- R7 · ComprobadorObra -------------------------- #

def test_f058_r7_consulta_con_la_clave_y_el_tope() -> None:
    puerto = PuertoDoble(True)
    consulta = _comprobador(puerto, timeout_s=4.5).consultar(
        CODIGO, document_id="doc-1")
    assert consulta == ConsultaObra(existe=True, ms=250, error_tipo=None)
    assert puerto.llamadas == [(CLAVE, 4.5)]


def test_f058_r7_no_existe() -> None:
    consulta = _comprobador(PuertoDoble(False)).consultar(
        CODIGO, document_id="doc-1")
    assert consulta.existe is False
    assert consulta.error_tipo is None


def test_f058_r7_sin_cache_una_llamada_por_consulta() -> None:
    puerto = PuertoDoble(True)
    comprobador = _comprobador(puerto, 1.0, 1.1, 2.0, 2.2)
    comprobador.consultar(CODIGO, document_id="doc-1")
    comprobador.consultar(CODIGO, document_id="doc-1")
    assert puerto.llamadas == [(CLAVE, 5.0), (CLAVE, 5.0)]


@pytest.mark.parametrize("codigo", [None, "", "   ", " - "])
def test_f058_r7_clave_vacia_no_llama(codigo, caplog) -> None:
    puerto = PuertoDoble(True)
    with caplog.at_level(logging.DEBUG, logger=LOGGER_OBRA):
        consulta = ComprobadorObra(client=puerto).consultar(
            codigo, document_id="doc-1")
    assert consulta == ConsultaObra(existe=None, ms=0, error_tipo=None)
    assert puerto.llamadas == []
    assert _mensajes(caplog, logging.INFO) == []


def test_f058_r9_el_tope_por_defecto_es_5_s() -> None:
    puerto = PuertoDoble(True)
    ComprobadorObra(client=puerto).consultar(CODIGO, document_id="d")
    assert puerto.llamadas == [(CLAVE, 5.0)]


# ------------------------ R9 · fallo = «no se sabe» ------------------------ #

@pytest.mark.parametrize("error", [
    RuntimeError("sigrid-api respondio 500: obra 09999"),
    httpx.ReadTimeout("timed out"),
    ValueError("x"),
])
def test_f058_r9_un_fallo_no_se_sabe_y_no_lanza(error, caplog) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_OBRA):
        consulta = _comprobador(PuertoDoble(error=error), 7.0, 7.5).consultar(
            CODIGO, document_id="doc-7")
    assert consulta == ConsultaObra(
        existe=None, ms=500, error_tipo=type(error).__name__)
    (aviso,) = _mensajes(caplog, logging.WARNING)
    assert aviso == (f"[obra-sigrid] document_id=doc-7 resultado=error "
                     f"error={type(error).__name__} ms=500")
    assert _mensajes(caplog, logging.INFO) == []


# ---------------------------- R10 · log y tiempos -------------------------- #

@pytest.mark.parametrize(("respuesta", "resultado"), [
    (True, "existe"), (False, "no_existe")])
def test_f058_r10_info_con_document_id_resultado_y_ms(
    respuesta, resultado, caplog,
) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_OBRA):
        _comprobador(PuertoDoble(respuesta), 3.0, 3.0421).consultar(
            CODIGO, document_id="doc-3")
    (linea,) = _mensajes(caplog, logging.INFO)
    assert linea == f"[obra-sigrid] document_id=doc-3 resultado={resultado} ms=42"
    assert CLAVE not in linea.split("ms=")[0]


def test_f058_r10_sin_document_id_sale_guion(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_OBRA):
        _comprobador(PuertoDoble(True)).consultar(CODIGO, document_id=None)
    (linea,) = _mensajes(caplog, logging.INFO)
    assert "document_id=- " in linea


def test_f058_r10_el_reloj_por_defecto_es_monotonico() -> None:
    import time

    assert ComprobadorObra(client=PuertoDoble())._reloj is time.perf_counter


# ------------------------ R7, R9 · existe_obra (HTTP) ---------------------- #

class Grabadora:
    def __init__(self, cuerpo: dict | None = None, estado: int = 200) -> None:
        self.cuerpo = cuerpo if cuerpo is not None else {
            "ok": True, "columns": ["codigo"], "rows": [["09999"]],
            "truncated": False}
        self.estado = estado
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        return httpx.Response(self.estado, json=self.cuerpo)

    @property
    def payload(self) -> dict:
        return json.loads(self.peticiones[-1].content)


def _cliente(grabadora: Grabadora, **kwargs) -> SigridLookupClient:
    return SigridLookupClient(
        base_url="https://sigrid.invalid", function_key=CLAVE_FALSA,
        database="ruesma", transport=httpx.MockTransport(grabadora), **kwargs)


def test_f058_r7_existe_obra_parametrizada() -> None:
    grabadora = Grabadora()
    assert _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0) is True
    (peticion,) = grabadora.peticiones
    assert peticion.url.path == "/api/sql/read"
    assert peticion.headers["x-functions-key"] == CLAVE_FALSA
    payload = grabadora.payload
    assert payload["parameters"] == [CLAVE]
    assert CLAVE not in payload["sql"]
    assert payload["sql"].count("?") == 1
    assert "TOP 1" in payload["sql"]
    assert payload["database"] == "ruesma"


def test_f058_r7_existe_obra_sin_filtro_de_empresa_ni_de_baja() -> None:
    grabadora = Grabadora()
    _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0)
    sql = grabadora.payload["sql"].lower()
    assert "emp" not in sql
    assert "fecbaj" not in sql and "baja" not in sql


def test_f058_r7_existe_obra_pide_el_max_rows_del_cliente() -> None:
    """F-038 (R13): ningún lector fija un ``max_rows`` bajo; el ``TOP 1``
    acota la respuesta."""
    grabadora = Grabadora()
    _cliente(grabadora, max_rows=1234).existe_obra(CLAVE, timeout_s=5.0)
    assert grabadora.payload["max_rows"] == 1234
    _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0)
    assert grabadora.payload["max_rows"] == MAX_ROWS_DEFECTO


@pytest.mark.parametrize(("tope", "segundos"), [
    (5.0, 5), (4.2, 5), (0.3, 1), (12.0, 12)])
def test_f058_r9_existe_obra_usa_el_tope_del_argumento(tope, segundos) -> None:
    grabadora = Grabadora()
    _cliente(grabadora, timeout_s=30.0).existe_obra(CLAVE, timeout_s=tope)
    assert grabadora.payload["timeout_seconds"] == segundos
    tiempos = grabadora.peticiones[-1].extensions["timeout"]
    assert tiempos["read"] == tope
    assert tiempos["connect"] == tope


def test_f058_r7_existe_obra_sin_filas_es_false() -> None:
    grabadora = Grabadora({"ok": True, "columns": ["codigo"], "rows": [],
                           "truncated": False})
    assert _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0) is False


def test_f058_r9_existe_obra_truncada_es_error() -> None:
    grabadora = Grabadora({"ok": True, "columns": ["codigo"],
                           "rows": [["09999"]], "truncated": True})
    with pytest.raises(RuntimeError, match="trunca"):
        _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0)


@pytest.mark.parametrize("estado", [400, 500, 503])
def test_f058_r9_existe_obra_con_error_http_lanza(estado: int) -> None:
    grabadora = Grabadora({"ok": False}, estado=estado)
    with pytest.raises(RuntimeError, match=str(estado)):
        _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0)


def test_f058_r9_existe_obra_ok_false_lanza() -> None:
    grabadora = Grabadora({"ok": False, "error": "x"})
    with pytest.raises(RuntimeError):
        _cliente(grabadora).existe_obra(CLAVE, timeout_s=5.0)


def test_f058_r9_existe_obra_no_cambia_fetch_tipos_hora() -> None:
    """El catálogo sigue con el tope y el ``max_rows`` del cliente."""
    grabadora = Grabadora({"ok": True, "columns": ["ide", "codigo"],
                           "rows": [[1, "HLGR"]], "truncated": False})
    cliente = _cliente(grabadora, timeout_s=30.0)
    cliente.existe_obra(CLAVE, timeout_s=5.0)
    (tipo,) = cliente.fetch_tipos_hora()
    assert tipo.ide == 1
    payload = grabadora.payload
    assert payload["parameters"] == []
    assert payload["timeout_seconds"] == 30
    assert payload["max_rows"] == MAX_ROWS_DEFECTO
    assert grabadora.peticiones[-1].extensions["timeout"]["read"] == 30.0
