# tests/test_f056_decisiones.py
"""F-056 · Decision y aplicacion del ajuste de franquicia en sv4.

T14: el repositorio (`franquicia_ajuste` contra SQLite en memoria, el mismo
ORM que produccion: indice unico y CAS sobre `estado`) y el cliente de sv5
(`/api/franquicia/recursos`, `comprobar` y `ejecutar`, sin red).

Datos SINTETICOS: el DNI y el nombre son los ficticios de `dobles`.
"""
from __future__ import annotations

import json

import httpx
import pytest

from application.services import franquicia as fq
from infrastructure.database.orm_models import (
    FranquiciaAjusteOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer import transfer_client as modulo_cliente
from infrastructure.transfer.transfer_client import TransferClient
from tests.dobles import FabricaSesionSqlite, sembrar_parte

REC = 501
DNI = "12345678Z"
PROP = {"fecha_int": 20261015, "obra_ide": 10, "obra_codigo": "0100",
        "partida_ide": 33, "partida_cod": "01.01"}


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _repo(fabrica) -> ParteReviewRepository:
    return ParteReviewRepository(fabrica)  # type: ignore[arg-type]


def _fila(fabrica, ide) -> FranquiciaAjusteOrm:
    with fabrica.create_session() as s:
        return s.get(FranquiciaAjusteOrm, ide)


# -------------------- repositorio: lineas del periodo -------------------- #

def _sembrar_periodo(fabrica):
    a = sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 2.0,
                                                 "tipo": "extra"}],
                      document_id="d-1015", fecha="2026-10-15")
    b = sembrar_parte(fabrica, [{"horas": 8.0, "estado": "encolado"}],
                      document_id="d-0916", fecha="2026-09-16")
    fuera = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-1016",
                          fecha="2026-10-16")
    otro_rec = sembrar_parte(fabrica, [{"horas": 1.0, "tipo": "extra"}],
                             document_id="d-otro", fecha="2026-10-01",
                             recurso_ide=777)
    ajeno = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-ajeno",
                          fecha="2026-10-01", recurso_ide=888,
                          empleado_dni="99999999R")
    borrada = sembrar_parte(fabrica, [{"horas": 8.0, "borrada": True}],
                            document_id="d-borr", fecha="2026-10-02")
    papelera = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-pap",
                             fecha="2026-10-03", doc_en_papelera=True)
    return a, b, fuera, otro_rec, ajeno, borrada, papelera


def test_f056_r7_r12_repositorio_lineas_trabajador_periodo(fabrica):
    a, b, _f, otro, _aj, _bo, _pa = _sembrar_periodo(fabrica)
    lineas = _repo(fabrica).lineas_trabajador_periodo(REC, 20260916,
                                                      20261015)
    assert sorted(x["registro_id"] for x in lineas) == sorted(
        [*a, *b, *otro])
    x = next(x for x in lineas if x["registro_id"] == a[1])
    assert {k: x[k] for k in ("fecha_int", "recurso_ide", "tipo_hora",
                              "horas", "obra_ide", "obra_codigo",
                              "es_incidencia")} == {
        "fecha_int": 20261015, "recurso_ide": REC, "tipo_hora": "extra",
        "horas": 2.0, "obra_ide": 10, "obra_codigo": "0100",
        "es_incidencia": False}
    # La misma persona con otro recurso cuenta (R12, DA16).
    assert fq.varios_recursos(lineas) is True


def test_f056_r12_repositorio_extra_por_hora_ext(fabrica):
    [rid] = sembrar_parte(fabrica, [{"horas": 1.0}], document_id="d-x",
                          fecha="2026-10-01")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, rid).hora_ext = 1
        s.commit()
    [x] = _repo(fabrica).lineas_trabajador_periodo(REC, 20260916, 20261015)
    assert x["tipo_hora"] == "extra"


def test_f056_r18_repositorio_encolados_de(fabrica):
    _sembrar_periodo(fabrica)
    repo = _repo(fabrica)
    assert repo.encolados_de(REC, 20260916, 20261015) == 1
    assert repo.encolados_de(REC, 20260917, 20261015) == 0
    assert repo.encolados_de(888, 20260916, 20261015) == 0


# ---------------------- repositorio: decisiones (R15) ---------------------- #

def test_f056_r16_repositorio_ajustar_crea_decidido(fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="ana")
    assert (f["estado"], f["recurso_ide"], f["periodo"], f["decision"]) == (
        "decidido", REC, "2026-10", "ajustar")
    assert {k: f[k] for k in PROP} == PROP
    fila = _fila(fabrica, f["id"])
    assert (fila.decidido_por, fila.franquicia) == ("ana", None)
    assert fila.decidido_at_utc and fila.creado_at_utc
    assert repo.ajustes_de([(REC, "2026-10"), (REC, "2026-11")]) == {
        (REC, "2026-10"): f}
    assert repo.ajuste(f["id"]) == f
    assert repo.ajuste(999) is None


def test_f056_r15_repositorio_ajustar_dos_veces_es_409(fabrica):
    repo = _repo(fabrica)
    repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="ana")
    with pytest.raises(fq.AjusteCambiadoError):
        repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="eva")


def test_f056_r16_repositorio_no_ajustar_y_luego_ajustar(fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "no_ajustar", None, actor="ana")
    assert (f["estado"], f["fecha_int"], f["decision"]) == (
        "rechazado", 0, "no_ajustar")
    again = repo.decidir_ajuste(REC, "2026-10", "no_ajustar", None,
                                actor="eva")
    assert again == f                    # repetir no cambia nada
    g = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="eva")
    assert (g["id"], g["estado"], g["fecha_int"], g["decision"]) == (
        f["id"], "decidido", 20261015, "ajustar")
    assert _fila(fabrica, g["id"]).decidido_por == "eva"


def test_f056_r8_repositorio_ajustar_tras_rechazo_conserva_dia_y_obra(
        fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "no_ajustar", PROP, actor="ana")
    otra = dict(PROP, fecha_int=20261014, obra_ide=20)
    g = repo.decidir_ajuste(REC, "2026-10", "ajustar", otra, actor="ana")
    assert (g["id"], g["fecha_int"], g["obra_ide"]) == (f["id"], 20261015,
                                                        10)


@pytest.mark.parametrize("estado", ["aplicado", "error", "decidido"])
def test_f056_r16_repositorio_recalcular_vuelve_a_decidido(fabrica, estado):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="ana")
    with fabrica.create_session() as s:
        s.get(FranquiciaAjusteOrm, f["id"]).estado = estado
        s.commit()
    g = repo.decidir_ajuste(REC, "2026-10", "recalcular", None, actor="eva")
    assert (g["estado"], g["decision"], g["fecha_int"]) == (
        "decidido", "recalcular", 20261015)


@pytest.mark.parametrize("previo, decision", [
    (None, "recalcular"), ("rechazado", "recalcular"),
    ("aplicado", "ajustar"), ("aplicado", "no_ajustar"),
    ("decidido", "no_ajustar"), ("error", "ajustar")])
def test_f056_r15_repositorio_decision_que_no_cuadra_es_409(fabrica, previo,
                                                             decision):
    repo = _repo(fabrica)
    if previo is not None:
        f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
        with fabrica.create_session() as s:
            s.get(FranquiciaAjusteOrm, f["id"]).estado = previo
            s.commit()
    with pytest.raises(fq.AjusteCambiadoError):
        repo.decidir_ajuste(REC, "2026-10", decision, PROP, actor="b")


def test_f056_r15_repositorio_ajustar_sin_datos_es_409(fabrica):
    with pytest.raises(fq.AjusteCambiadoError, match="dia"):
        _repo(fabrica).decidir_ajuste(REC, "2026-10", "ajustar", None,
                                      actor="a")


def test_f056_r16_repositorio_mantener_no_cambia_nada(fabrica):
    repo = _repo(fabrica)
    assert repo.decidir_ajuste(REC, "2026-10", "mantener", None,
                               actor="a") is None
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    assert repo.decidir_ajuste(REC, "2026-10", "mantener", None,
                               actor="b") == f


def test_f056_r15_repositorio_cas_si_otro_cambio_el_estado(fabrica,
                                                           monkeypatch):
    """El estado cambia entre la lectura y el `UPDATE`: 409 sin tocar."""
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    with fabrica.create_session() as s:
        s.get(FranquiciaAjusteOrm, f["id"]).estado = "aplicado"
        s.commit()
    original = ParteReviewRepository._fila_ajuste

    def leer_y_cambiar(session, rec, periodo):
        fila = original(session, rec, periodo)
        with fabrica.create_session() as otra:
            otra.get(FranquiciaAjusteOrm, f["id"]).estado = "rechazado"
            otra.commit()
        return fila
    monkeypatch.setattr(ParteReviewRepository, "_fila_ajuste",
                        staticmethod(leer_y_cambiar))
    with pytest.raises(fq.AjusteCambiadoError, match="otro usuario"):
        repo.decidir_ajuste(REC, "2026-10", "recalcular", None, actor="b")
    assert _fila(fabrica, f["id"]).estado == "rechazado"


def test_f056_r15_repositorio_alta_concurrente_es_409(fabrica, monkeypatch):
    """Dos altas a la vez: el indice unico para la segunda (409)."""
    repo = _repo(fabrica)
    monkeypatch.setattr(ParteReviewRepository, "_fila_ajuste",
                        staticmethod(lambda session, rec, periodo: None))
    repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    with pytest.raises(fq.AjusteCambiadoError, match="otro usuario"):
        repo.decidir_ajuste(REC, "2026-10", "no_ajustar", PROP, actor="b")


# ------------------------- repositorio: cerrar (R17) ------------------------- #

SV5_OK = {"ok": True, "accion": "crear", "extras": 14.0, "objetivo": -6.0,
          "actual": -6.0, "hmores_ide": 7009, "hmoide": 900,
          "parte_cod": "PT26/00314", "franquicia": 8.0,
          "franquicia_estado": "activa", "escrita": True}


def test_f056_r17_repositorio_cerrar_aplicado_con_la_x_usada(fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    g = repo.cerrar_ajuste(f["id"], ok=True, sv5=SV5_OK, error=None,
                           actor="eva")
    assert (g["estado"], g["extras"], g["ajuste"], g["franquicia"],
            g["hmores_ide"], g["hmoide"], g["parte_cod"], g["error"]) == (
        "aplicado", 14.0, -6.0, 8.0, 7009, 900, "PT26/00314", None)
    fila = _fila(fabrica, f["id"])
    assert fila.aplicado_por == "eva" and fila.aplicado_at_utc
    assert json.loads(fila.resultado)["accion"] == "crear"


def test_f056_r17_repositorio_cerrar_con_error(fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    sv5 = {"ok": False, "accion": "no_editable", "extras": 14.0,
           "objetivo": 0.0, "franquicia": None,
           "franquicia_estado": "no_disponible", "motivo": "x" * 400}
    g = repo.cerrar_ajuste(f["id"], ok=False, sv5=sv5, error="x" * 400,
                           actor="eva")
    assert g["estado"] == "error" and len(g["error"]) == 255
    assert (g["franquicia"], g["ajuste"]) == (None, 0.0)
    # Un error sin respuesta de sv5 deja lo que habia.
    h = repo.cerrar_ajuste(f["id"], ok=False, sv5=None, error="caido",
                           actor="eva")
    assert (h["estado"], h["error"], h["extras"]) == ("error", "caido", 14.0)


def test_f056_r17_repositorio_cerrar_solo_desde_decidido_o_error(fabrica):
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(REC, "2026-10", "no_ajustar", PROP, actor="a")
    g = repo.cerrar_ajuste(f["id"], ok=True, sv5=SV5_OK, error=None,
                           actor="b")
    assert g["estado"] == "rechazado" and g["hmores_ide"] is None
    assert repo.cerrar_ajuste(999, ok=True, sv5=SV5_OK, error=None,
                              actor="b") is None


# ----------------------------- cliente de sv5 ----------------------------- #

def _cliente(monkeypatch, respuesta):
    llamadas: list = []

    def post(url, json=None, timeout=None):
        llamadas.append((url, json, timeout))
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(modulo_cliente.httpx, "post", post)
    return TransferClient(base_url="http://sv5.invalid", timeout_s=30), \
        llamadas


def test_f056_r43_cliente_franquicia_recursos(monkeypatch):
    cuerpo = {"estado": "ok", "motivo": None,
              "recursos": {"501": {"franquicia": 8.0, "estado": "activa"}}}
    cli, llamadas = _cliente(monkeypatch, httpx.Response(200, json=cuerpo))
    assert cli.franquicia_recursos([501, 502], timeout_s=5) == cuerpo
    [(url, enviado, plazo)] = llamadas
    assert url == "http://sv5.invalid/api/franquicia/recursos"
    assert enviado == {"recurso_ides": [501, 502]} and plazo == 5


@pytest.mark.parametrize("respuesta", [
    httpx.Response(404, json={"detail": "Not Found"}),
    httpx.TimeoutException("lento"), httpx.ConnectError("cerrado")])
def test_f056_r44_cliente_franquicia_recursos_fallo_es_ok_false(
        monkeypatch, respuesta):
    cli, _ = _cliente(monkeypatch, respuesta)
    r = cli.franquicia_recursos([501], timeout_s=5)
    assert r["ok"] is False and r["error"]


def test_f056_r9_cliente_franquicia_comprobar(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, httpx.Response(
        200, json={"ok": True, "accion": "crear"}))
    assert cli.franquicia_comprobar({"ajuste_id": 0}, timeout_s=7) == {
        "ok": True, "accion": "crear"}
    [(url, enviado, plazo)] = llamadas
    assert url.endswith("/api/franquicia/comprobar") and plazo == 7
    assert enviado == {"ajuste_id": 0}


def test_f056_r17_cliente_franquicia_ejecutar(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, httpx.Response(
        200, json={"ok": True}))
    assert cli.franquicia_ejecutar({"ajuste_id": 7}) == {"ok": True}
    [(url, _e, plazo)] = llamadas
    assert url.endswith("/api/franquicia/ejecutar") and plazo == 30


@pytest.mark.parametrize("respuesta, sin", [
    (httpx.Response(502, json={"ok": False, "error": "x"}), True),
    (httpx.TimeoutException("lento"), True),
    (httpx.Response(200, json={"ok": False, "error": "no"}), False)])
def test_f056_r19_cliente_franquicia_ejecutar_sin_respuesta(monkeypatch,
                                                            respuesta, sin):
    cli, _ = _cliente(monkeypatch, respuesta)
    r = cli.franquicia_ejecutar({"ajuste_id": 7})
    assert r["ok"] is False and bool(r.get("sin_respuesta")) is sin
