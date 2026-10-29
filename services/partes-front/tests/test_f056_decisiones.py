# tests/test_f056_decisiones.py
"""F-056 · Decision y aplicacion del ajuste de franquicia en sv4.

T14: el repositorio (`franquicia_ajuste` contra SQLite en memoria, el mismo
ORM que produccion: indice unico y CAS sobre `estado`) y el cliente de sv5
(`/api/franquicia/recursos`, `comprobar` y `ejecutar`, sin red).

Datos SINTETICOS: el DNI y el nombre son los ficticios de `dobles`.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from application.services import franquicia as fq
from application.services.calendario_provider import CalendarioProvider
from config.settings import Settings
from infrastructure.database.orm_models import (
    FranquiciaAjusteOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer import transfer_client as modulo_cliente
from infrastructure.transfer.transfer_client import TransferClient
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f046_aplicar import PublisherFake, RecalculoFake, Sv5Fake

REC = 501
ACTOR = "local:ana"   # lo que da `_actor` con DEFAULT_REVIEWER=ana
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


# =========================== T15: rutas del portal =========================== #

RECURSOS_OK = {"estado": "ok", "motivo": None, "recursos": {
    "501": {"franquicia": 8.0, "estado": "activa"}}}
COMPROBAR_OK = {"ok": True, "accion": "crear", "extras": 12.0,
                "objetivo": -6.0, "actual": None, "franquicia": 8.0,
                "franquicia_estado": "activa", "motivo": None,
                "parte_cod": "PT26/00314"}


class Sv5Franq(Sv5Fake):
    """sv5 con las rutas de la franquicia (F-056)."""

    def __init__(self, *, recursos=RECURSOS_OK, comprobar=COMPROBAR_OK,
                 acciones=None, ejecutar=None, **kw):
        super().__init__(**kw)
        self.recursos_resp = recursos
        self.comprobar_franq = comprobar
        self.ejecutar_franq = ejecutar or dict(COMPROBAR_OK, escrita=True,
                                               actual=-6.0, hmores_ide=7009,
                                               hmoide=900)
        self.acciones = acciones or []
        self.recursos_pedidos: list[tuple[list, float | None]] = []
        self.franq_comprobadas: list[dict] = []
        self.franq_ejecutadas: list[dict] = []

    def preflight(self, payload):
        self.preflights.append(payload)
        return {"ok": True, "conflictos": [], "acciones": self.acciones}

    def franquicia_recursos(self, ides, *, timeout_s=None):
        self.recursos_pedidos.append((list(ides), timeout_s))
        if isinstance(self.recursos_resp, Exception):
            raise self.recursos_resp
        return self.recursos_resp

    def franquicia_comprobar(self, payload, *, timeout_s=None):
        self.franq_comprobadas.append(payload)
        if isinstance(self.comprobar_franq, Exception):
            raise self.comprobar_franq
        return self.comprobar_franq

    def franquicia_ejecutar(self, payload):
        self.franq_ejecutadas.append(payload)
        if isinstance(self.ejecutar_franq, Exception):
            raise self.ejecutar_franq
        return self.ejecutar_franq


class CalendarioNoFiable(CalendarioProvider):
    """Sesame configurado pero caido: nada es fiable (R6)."""

    def __init__(self):
        super().__init__(cliente=None, respaldo_holiday_name=lambda d: None)

    def fiable_para(self, consultas):
        list(consultas)
        return False


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "TRANSFER_BASE_URL": "http://sv5.interno",
        "HOLIDAYS_ENABLED": "false",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def portal(entorno, fabrica):
    def _montar(*, sv5=None, publisher=None, calendario=None):
        sv5 = sv5 or Sv5Franq()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        recalculo_publisher=RecalculoFake(),
                        calendario_provider=calendario)
        return TestClient(app), sv5
    return _montar


def _dia15(fabrica, document_id="d15"):
    """El trabajador 501 el jueves 2026-10-15 (dia de ajuste de 2026-10):
    8 h y 2 h extra en la 0100, partida 01.01."""
    return sembrar_parte(fabrica, [
        {"horas": 8.0, "partida_cod": "01.01"},
        {"horas": 2.0, "tipo": "extra", "partida_cod": "01.01"}],
        document_id=document_id, fecha="2026-10-15")


def _acc_he(can=2.0):
    return {"accion": "escribir", "recurso_ide": REC, "hora_codigo": "HE01",
            "can": can, "fecha_int": 20261015}


def _preflight(cliente, ids, **extra):
    return cliente.post("/api/aprobar/preflight",
                        json=dict({"registro_ids": ids}, **extra))


def _filas(fabrica):
    with fabrica.create_session() as s:
        return s.query(FranquiciaAjusteOrm).all()


# ----------------------------- preflight (R9-R14) ----------------------------- #

def test_f056_r9_r43_preflight_candidato_nuevo(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, sv5 = portal(sv5=Sv5Franq(acciones=[_acc_he(2.0)]))
    r = _preflight(cliente, ids)
    assert r.status_code == 200, r.text
    [it] = r.json()["franquicias"]["items"]
    assert (it["tipo"], it["recurso_ide"], it["periodo"], it["dia"]) == (
        "nuevo", REC, "2026-10", "2026-10-15")
    assert (it["obra"], it["partida_cod"], it["ajustable"]) == (
        {"ide": 10, "codigo": "0100"}, "01.01", True)
    assert (it["extras_pendientes"], it["objetivo"]) == (2.0, -6.0)
    assert it["decisiones"] == ["ajustar", "no_ajustar"]
    assert r.json()["franquicias"]["aviso"] is None
    assert [p for p, _t in sv5.recursos_pedidos] == [[REC]]      # R43
    [p] = sv5.franq_comprobadas
    assert {k: p[k] for k in ("ajuste_id", "recurso_ide", "periodo",
                              "inicio", "fin", "fecha_int",
                              "extras_pendientes", "usuario")} == {
        "ajuste_id": 0, "recurso_ide": REC, "periodo": "2026-10",
        "inicio": 20260916, "fin": 20261015, "fecha_int": 20261015,
        "extras_pendientes": 2.0, "usuario": ACTOR}
    assert p["obra"] == {"ide": 10, "codigo": "0100"}
    assert "franquicia" not in p
    assert _filas(fabrica) == []                                 # R14


def test_f056_dia7_preflight_sin_linea_del_dia_de_ajuste_no_hay_bloque(
        fabrica, portal):
    ids = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d14",
                        fecha="2026-10-14")
    cliente, sv5 = portal()
    r = _preflight(cliente, ids)
    assert r.status_code == 200 and "franquicias" not in r.json()
    assert sv5.franq_comprobadas == []


def test_f056_r44_preflight_apagada_ni_aviso_ni_candidatos(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, sv5 = portal(sv5=Sv5Franq(recursos={"estado": "apagada",
                                                 "motivo": "x",
                                                 "recursos": {}}))
    r = _preflight(cliente, ids)
    assert r.status_code == 200 and "franquicias" not in r.json()
    assert sv5.franq_comprobadas == []


@pytest.mark.parametrize("resp, texto", [
    ({"estado": "no_disponible", "motivo": "la columna x no existe en res",
      "recursos": {}}, "la columna x no existe en res"),
    ({"ok": False, "error": "HTTP 404"}, "HTTP 404"),
    (RuntimeError("sv5 caido"), "sv5 caido"),
])
def test_f056_r44_preflight_sv5_no_sabe_aviso_sin_candidatos(fabrica, portal,
                                                             resp, texto):
    ids = _dia15(fabrica)
    cliente, sv5 = portal(sv5=Sv5Franq(recursos=resp))
    r = _preflight(cliente, ids)
    assert r.status_code == 200 and r.json()["grupos"]
    assert r.json()["franquicias"] == {
        "aviso": fq.AVISO_NO_COMPROBADA + texto, "items": []}
    assert sv5.franq_comprobadas == []


def test_f056_r10_preflight_ajuste_vivo_con_cualquier_linea(fabrica, portal):
    _dia15(fabrica)
    otra = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d20",
                         fecha="2026-09-20")
    f = _repo(fabrica).decidir_ajuste(REC, "2026-10", "ajustar", PROP,
                                      actor="eva")
    _repo(fabrica).cerrar_ajuste(f["id"], ok=True, sv5=dict(
        COMPROBAR_OK, hmores_ide=7009, objetivo=-4.0), error=None,
        actor="eva")
    sv5 = Sv5Franq(recursos={"estado": "apagada", "recursos": {}},
                   comprobar=dict(COMPROBAR_OK, accion="actualizar",
                                  actual=-4.0))
    cliente, sv5 = portal(sv5=sv5)
    [it] = _preflight(cliente, otra).json()["franquicias"]["items"]
    assert (it["tipo"], it["id"], it["estado"], it["actual"]) == (
        "existente", f["id"], "aplicado", -4.0)
    assert it["decisiones"] == ["recalcular", "mantener"]
    [p] = sv5.franq_comprobadas
    assert (p["ajuste_id"], p["fecha_int"]) == (f["id"], 20261015)


def test_f056_r14_preflight_comprobar_que_lanza_no_tumba_nada(fabrica,
                                                              portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(comprobar=RuntimeError("sv5 caido")))
    r = _preflight(cliente, ids)
    assert r.status_code == 200
    [it] = r.json()["franquicias"]["items"]
    assert it["ajustable"] is False and "sv5 caido" in it["motivo"]


def test_f056_r6_preflight_calendario_no_fiable(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, sv5 = portal(calendario=CalendarioNoFiable())
    [it] = _preflight(cliente, ids).json()["franquicias"]["items"]
    assert (it["dia"], it["ajustable"]) == (None, False)
    assert "Sesame" in it["motivo"]
    assert sv5.franq_comprobadas == []


def test_f056_r12_preflight_varios_recursos_no_ajusta(fabrica, portal):
    ids = _dia15(fabrica)
    sembrar_parte(fabrica, [{"horas": 1.0, "tipo": "extra"}],
                  document_id="d-otro", fecha="2026-10-01", recurso_ide=777)
    cliente, sv5 = portal()
    [it] = _preflight(cliente, ids).json()["franquicias"]["items"]
    assert (it["ajustable"], it["motivo"]) == (False,
                                               fq.MOTIVO_VARIOS_RECURSOS)
    assert sv5.franq_comprobadas == []


def test_f056_r14_preflight_fallo_interno_es_aviso(fabrica, portal,
                                                   monkeypatch):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()

    def roto(self, claves):
        raise RuntimeError("bbdd caida")
    monkeypatch.setattr(ParteReviewRepository, "ajustes_de", roto)
    r = _preflight(cliente, ids)
    assert r.status_code == 200 and r.json()["grupos"]
    assert "bbdd caida" in r.json()["franquicias"]["aviso"]


# -------------------------- ejecutar / encolar (R15) -------------------------- #

def _decision(decision, rec=REC, periodo="2026-10"):
    return [{"recurso_ide": rec, "periodo": periodo, "decision": decision}]


def test_f056_r15_r16_ejecutar_guarda_ajustar_antes_de_los_grupos(fabrica,
                                                                   portal):
    ids = _dia15(fabrica)
    cliente, sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    assert r.status_code == 200, r.text
    [f] = _filas(fabrica)
    assert r.json()["franquicias"] == [{"id": f.id, "estado": "decidido",
                                        "recurso_ide": REC,
                                        "periodo": "2026-10"}]
    assert (f.fecha_int, f.obra_ide, f.partida_cod, f.decidido_por) == (
        20261015, 10, "01.01", ACTOR)
    assert len(sv5.ejecutadas) == 1 and sv5.franq_ejecutadas == []


def test_f056_r16_ejecutar_no_ajustar_deja_rechazado(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("no_ajustar")})
    assert r.json()["franquicias"][0]["estado"] == "rechazado"


def test_f056_r16_ejecutar_mantener_sin_fila_no_lista_nada(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("mantener")})
    assert r.status_code == 200 and "franquicias" not in r.json()
    assert _filas(fabrica) == []


@pytest.mark.parametrize("franquicias", [
    _decision("ajustar", rec=999), _decision("borrar"), "x",
    _decision("ajustar", periodo="2026-11")])
def test_f056_r15_ejecutar_decision_invalida_es_422_sin_nada(
        fabrica, portal, franquicias):
    ids = _dia15(fabrica)
    cliente, sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": franquicias})
    assert r.status_code == 422, r.text
    assert _filas(fabrica) == [] and sv5.ejecutadas == []


def test_f056_r15_ejecutar_decision_que_no_cuadra_es_409(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("recalcular")})
    assert r.status_code == 409
    assert sv5.ejecutadas == []


def test_f056_r6_ejecutar_ajustar_sin_calendario_es_409(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal(calendario=CalendarioNoFiable())
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar"),
        "forzar_sin_sesame": True})
    assert r.status_code == 409 and "dia de ajuste" in r.json()["error"]
    assert _filas(fabrica) == []


def test_f056_r12_ejecutar_ajustar_con_varios_recursos_es_409(fabrica,
                                                              portal):
    ids = _dia15(fabrica)
    sembrar_parte(fabrica, [{"horas": 1.0, "tipo": "extra"}],
                  document_id="d-otro", fecha="2026-10-01", recurso_ide=777)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    assert r.status_code == 409
    assert r.json()["error"] == fq.MOTIVO_VARIOS_RECURSOS


def test_f056_r15_ejecutar_ambito_ajeno_no_decide(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar"),
        "ambito": {"vista": "obra", "obra_key": "obr-999"}})
    assert r.status_code == 422 and _filas(fabrica) == []


def test_f056_r15_encolar_guarda_la_decision_y_publica(fabrica, portal):
    ids = _dia15(fabrica)
    pub = PublisherFake()
    cliente, _sv5 = portal(publisher=pub)
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    assert r.status_code == 200, r.text
    assert r.json()["franquicias"][0]["estado"] == "decidido"
    assert len(pub.publicadas) == 1


def test_f056_r15_encolar_decision_invalida_es_422(fabrica, portal):
    ids = _dia15(fabrica)
    pub = PublisherFake()
    cliente, _sv5 = portal(publisher=pub)
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": ids, "franquicias": _decision("x")})
    assert r.status_code == 422 and pub.publicadas == []


def test_f056_r15_ejecutar_sin_franquicias_como_siempre(fabrica, portal):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})
    assert r.status_code == 200 and "franquicias" not in r.json()


def test_f056_r15_ejecutar_sin_lineas_que_registrar_lista_lo_decidido(
        fabrica, portal):
    """Lineas ya registradas: no queda nada que registrar, pero la decision
    SI se guardo (200 con lo decidido y el aviso)."""
    ids = sembrar_parte(fabrica, [{"horas": 8.0, "estado": "registrado",
                                   "partida_cod": "01.01"}],
                        document_id="dreg", fecha="2026-10-15")
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    assert r.status_code == 200, r.text
    assert r.json()["franquicias"][0]["estado"] == "decidido"
    assert r.json()["aviso"]


# ------------------------- aplicar (R17-R19, R21) ------------------------- #

def _decidido(fabrica, decision="ajustar"):
    return _repo(fabrica).decidir_ajuste(REC, "2026-10", decision, PROP,
                                         actor="eva")


EJECUTAR_OK = dict(COMPROBAR_OK, escrita=True, actual=-6.0, hmores_ide=7009,
                   hmoide=900)


def test_f056_r17_r21_aplicar_deja_aplicado_con_lo_de_sv5(fabrica, portal):
    _dia15(fabrica)
    f = _decidido(fabrica)
    cliente, sv5 = portal(sv5=Sv5Franq(ejecutar=dict(EJECUTAR_OK,
                                                     franquicia=9.0)))
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["ok"] is True and cuerpo["error"] is None
    aj = cuerpo["ajuste"]
    assert (aj["estado"], aj["franquicia"], aj["extras"], aj["ajuste"]) == (
        "aplicado", 9.0, 12.0, -6.0)
    assert (aj["hmores_ide"], aj["parte_cod"], aj["aplicado_por"]) == (
        7009, "PT26/00314", ACTOR)
    [p] = sv5.franq_ejecutadas
    assert (p["ajuste_id"], p["fecha_int"], p["usuario"]) == (
        f["id"], 20261015, ACTOR)
    assert "franquicia" not in p and sv5.franq_comprobadas == []


def test_f056_r17_aplicar_rechazado_por_sv5_deja_error(fabrica, portal):
    _dia15(fabrica)
    f = _decidido(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(ejecutar={
        "ok": False, "accion": "no_editable",
        "motivo": "parte_no_abierto: PT26/00314"}))
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert "parte_no_abierto" in r.json()["error"]
    assert r.json()["ajuste"]["estado"] == "error"


def test_f056_r19_aplicar_sin_respuesta_deja_error_y_se_reintenta(fabrica,
                                                                   portal):
    _dia15(fabrica)
    f = _decidido(fabrica)
    sv5 = Sv5Franq(ejecutar=RuntimeError("timeout"))
    cliente, sv5 = portal(sv5=sv5)
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.json()["ajuste"]["estado"] == "error"
    assert "timeout" in r.json()["error"]
    assert r.json()["ajuste"]["hmores_ide"] is None
    sv5.ejecutar_franq = EJECUTAR_OK
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.json()["ajuste"]["estado"] == "aplicado"
    assert len(sv5.franq_ejecutadas) == 2


def test_f056_r18_aplicar_con_lineas_encoladas_es_409_sin_sv5(fabrica,
                                                              portal):
    sembrar_parte(fabrica, [{"horas": 8.0, "estado": "encolado"}],
                  document_id="denc", fecha="2026-10-01")
    f = _decidido(fabrica)
    cliente, sv5 = portal()
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.status_code == 409
    assert "espera a que termine el registro" in r.json()["error"]
    assert sv5.franq_ejecutadas == []
    assert _fila(fabrica, f["id"]).estado == "decidido"


@pytest.mark.parametrize("decision, estado", [
    ("no_ajustar", "rechazado"), (None, "aplicado")])
def test_f056_r17_aplicar_fuera_de_decidido_o_error_es_409(
        fabrica, portal, decision, estado):
    _dia15(fabrica)
    if decision:
        f = _decidido(fabrica, decision)
    else:
        f = _decidido(fabrica)
        _repo(fabrica).cerrar_ajuste(f["id"], ok=True, sv5=EJECUTAR_OK,
                                     error=None, actor="eva")
    cliente, sv5 = portal()
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.status_code == 409 and estado in r.json()["error"]
    assert sv5.franq_ejecutadas == []


def test_f056_r17_aplicar_ajuste_inexistente_es_404(fabrica, portal):
    cliente, sv5 = portal()
    assert cliente.post("/api/franquicia/999/aplicar").status_code == 404
    assert sv5.franq_ejecutadas == []


# ============ supervivientes de la campana de mutacion (2026-10-29) ============ #
# Cada test caza un mutante que la suite dejaba vivo (numero entre corchetes:
# el de `progress/mutacion_F-056.md`).

def _quitar(fabrica, ids, **campos):
    """Deja sin dato (None) esos campos de esas lineas."""
    with fabrica.create_session() as s:
        for rid in ids:
            r = s.get(ParteRegistroOrm, rid)
            for k, v in campos.items():
                setattr(r, k, v)
        s.commit()


def test_f056_r15_repositorio_recurso_fechas_en_lotes_sin_perder_ninguna(
        fabrica):
    """[18] Con mas de 500 lineas, ningun lote se salta la 501."""
    muchas = sembrar_parte(fabrica, [{"horas": 1.0}] * 500,
                           document_id="d-500", fecha="2026-10-01")
    [ultima] = sembrar_parte(fabrica, [{"horas": 1.0}], document_id="d-501",
                             fecha="2026-10-02", recurso_ide=502)
    assert _repo(fabrica).recurso_fechas_de([*muchas, ultima]) == [
        (REC, 20261001), (502, 20261002)]


def test_f056_r15_repositorio_linea_sin_fecha_sale_con_fecha_0(fabrica):
    """[20] Una linea sin `fecha_int` sale con fecha 0 (sin dato)."""
    [rid] = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-sf")
    _quitar(fabrica, [rid], fecha_int=None)
    assert _repo(fabrica).recurso_fechas_de([rid]) == [(REC, 0)]


def test_f056_r8_repositorio_ajustar_con_obra_solo_por_codigo(fabrica):
    """[21, 22] Una propuesta con obra por codigo (sin ide) esta completa
    y la fila guarda la obra 0 (sin ide), no la 1."""
    f = _repo(fabrica).decidir_ajuste(
        REC, "2026-10", "ajustar", dict(PROP, obra_ide=None), actor="ana")
    assert (f["estado"], f["obra_ide"], f["obra_codigo"]) == (
        "decidido", 0, "0100")


def _logs_cierre(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.getMessage().startswith("[franquicia] ajuste ")
            and " -> " in r.getMessage() and "recurso=" not in
            r.getMessage()]


def test_f056_r17_repositorio_cerrar_deja_su_log_solo_si_cambia(fabrica,
                                                                caplog):
    """[23, 24, 25] Cerrar deja UNA linea de log con el estado nuevo (y el
    motivo si es error); cerrar lo que ya no esta decidido ni en error no
    deja ninguna."""
    repo = _repo(fabrica)
    ok = repo.decidir_ajuste(REC, "2026-10", "ajustar", PROP, actor="a")
    ko = repo.decidir_ajuste(REC, "2026-11", "ajustar",
                             dict(PROP, fecha_int=20261115), actor="a")
    with caplog.at_level(logging.INFO):
        repo.cerrar_ajuste(ok["id"], ok=True, sv5=SV5_OK, error=None,
                           actor="eva")
        repo.cerrar_ajuste(ko["id"], ok=False, sv5=None, error="caido",
                           actor="eva")
        repo.cerrar_ajuste(ok["id"], ok=True, sv5=SV5_OK, error=None,
                           actor="eva")
    assert _logs_cierre(caplog) == [
        f"[franquicia] ajuste {ok['id']} -> aplicado (por eva)",
        f"[franquicia] ajuste {ko['id']} -> error (por eva): caido"]


def _con_traza(caplog, prefijo: str) -> bool:
    """[28, 32, 39, 46, 54] El aviso lleva la traza (`exc_info`): sin ella,
    en los logs de Azure no se sabe donde fallo."""
    return any(r.getMessage().startswith(prefijo) and r.exc_info
               for r in caplog.records)


def test_f056_r44_preflight_fallo_de_recursos_con_traza(fabrica, portal,
                                                        caplog):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(recursos=RuntimeError("caido")))
    with caplog.at_level(logging.WARNING):
        assert _preflight(cliente, ids).status_code == 200
    assert _con_traza(caplog, "[franquicia] /recursos fallo")


def test_f056_r14_preflight_fallo_de_comprobar_con_traza(fabrica, portal,
                                                         caplog):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(comprobar=RuntimeError("caido")))
    with caplog.at_level(logging.WARNING):
        assert _preflight(cliente, ids).status_code == 200
    assert _con_traza(caplog, "[franquicia] comprobar 501|2026-10 fallo")


def test_f056_r14_preflight_fallo_interno_con_traza(fabrica, portal,
                                                    monkeypatch, caplog):
    ids = _dia15(fabrica)
    cliente, _sv5 = portal()

    def roto(self, claves):
        raise RuntimeError("bbdd caida")
    monkeypatch.setattr(ParteReviewRepository, "ajustes_de", roto)
    with caplog.at_level(logging.WARNING):
        assert _preflight(cliente, ids).status_code == 200
    assert _con_traza(caplog, "[franquicia] el aviso del preflight fallo")


def test_f056_r19_aplicar_sin_respuesta_con_traza(fabrica, portal, caplog):
    _dia15(fabrica)
    f = _decidido(fabrica)
    cliente, _sv5 = portal(sv5=Sv5Franq(ejecutar=RuntimeError("timeout")))
    with caplog.at_level(logging.WARNING):
        cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert _con_traza(caplog, f"[franquicia] aplicar {f['id']} fallo")


def test_f056_r43_preflight_pide_la_franquicia_en_lotes_de_500(fabrica,
                                                               portal):
    """[26, 27] R43: mas de 500 recursos van en lotes de 500 (y ninguno se
    queda fuera ni se pide dos veces)."""
    ids = sembrar_parte(fabrica, [{"horas": 1.0}] * 501, document_id="d-r",
                        fecha="2026-10-15")
    with fabrica.create_session() as s:
        for i, rid in enumerate(ids):
            s.get(ParteRegistroOrm, rid).recurso_ide = 1000 + i
        s.commit()
    cliente, sv5 = portal()
    assert _preflight(cliente, ids).status_code == 200
    pedidos = [p for p, _t in sv5.recursos_pedidos]
    assert [len(p) for p in pedidos] == [500, 1]
    assert sorted(x for p in pedidos for x in p) == list(range(1000, 1501))


def test_f056_r9_preflight_linea_sin_recurso_no_estorba(fabrica, portal):
    """[33, 35, 36, 37] Una linea sin recurso en la seleccion no se pide a
    sv5 (no es el recurso 1) ni tumba el aviso del resto."""
    ids = _dia15(fabrica)
    [sin] = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-sin",
                          fecha="2026-10-15", empleado_dni="99999999R")
    _quitar(fabrica, [sin], recurso_ide=None)
    cliente, sv5 = portal()
    r = _preflight(cliente, [*ids, sin])
    assert r.status_code == 200, r.text
    bloque = r.json()["franquicias"]
    assert bloque["aviso"] is None
    assert [it["recurso_ide"] for it in bloque["items"]] == [REC]
    assert [p for p, _t in sv5.recursos_pedidos] == [[REC]]


def test_f056_r10_preflight_el_recurso_1_tiene_su_ajuste(fabrica, portal):
    """[34, 38] El recurso 1 es un recurso: su ajuste vivo sale."""
    ids = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-r1",
                        fecha="2026-10-01", recurso_ide=1)
    repo = _repo(fabrica)
    f = repo.decidir_ajuste(1, "2026-10", "ajustar", PROP, actor="eva")
    repo.cerrar_ajuste(f["id"], ok=True, sv5=SV5_OK, error=None, actor="eva")
    cliente, sv5 = portal()
    r = _preflight(cliente, ids)
    assert r.status_code == 200, r.text
    [it] = r.json()["franquicias"]["items"]
    assert (it["recurso_ide"], it["tipo"], it["id"]) == (1, "existente",
                                                         f["id"])
    assert [p for p, _t in sv5.recursos_pedidos] == [[1]]


def test_f056_r5_preflight_dia_de_ajuste_con_el_candef_del_trabajador(
        fabrica, portal, entorno):
    """[29] R5: la jornada del dia sale del candef de sus lineas. Con candef
    9 y semana de 36 h el viernes 2026-05-15 tiene 0 h (36 - 4x9): el dia
    de ajuste es el jueves 14; con el candef por defecto (8 h) seria el 15."""
    entorno.setenv("JORNADA_SEMANAL_POR_CANDEF", "8:40,9:36")
    a = sembrar_parte(fabrica, [{"horas": 9.0}], document_id="d-0514",
                      fecha="2026-05-14")
    b = sembrar_parte(fabrica, [{"horas": 9.0}], document_id="d-0515",
                      fecha="2026-05-15")
    _quitar(fabrica, [*a, *b], hora_candef=9.0)
    cliente, _sv5 = portal()
    r = _preflight(cliente, [*a, *b])
    assert r.status_code == 200, r.text
    [it] = r.json()["franquicias"]["items"]
    assert (it["periodo"], it["dia"]) == ("2026-05", "2026-05-14")


def test_f056_r7_preflight_obra_de_las_lineas_del_dia_de_ajuste(fabrica,
                                                                portal):
    """[30] R7: la obra es la de mas horas EL DIA de ajuste, no la de otro
    dia con mas horas."""
    ids = _dia15(fabrica)
    sembrar_parte(fabrica, [{"horas": 10.0}], document_id="d-0214",
                  fecha="2026-10-14", obra_ide=20, obra_codigo="0200")
    cliente, sv5 = portal()
    [it] = _preflight(cliente, ids).json()["franquicias"]["items"]
    assert it["obra"] == {"ide": 10, "codigo": "0100"}
    assert sv5.franq_comprobadas[0]["obra"] == {"ide": 10, "codigo": "0100"}


def test_f056_r15_ejecutar_con_una_linea_sin_fecha_en_la_seleccion(fabrica,
                                                                   portal):
    """[40] Una linea sin fecha en la seleccion no da clave de franquicia
    (ni tumba la peticion)."""
    ids = _dia15(fabrica)
    [sin] = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-sf",
                          fecha="2026-10-14")
    _quitar(fabrica, [sin], fecha_int=None)
    cliente, _sv5 = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [*ids, sin], "franquicias": _decision("ajustar")})
    assert r.status_code == 200, r.text
    assert r.json()["franquicias"][0]["estado"] == "decidido"


def test_f056_r16_ejecutar_no_ajustar_sin_propuesta_si_se_guarda(fabrica,
                                                                 portal):
    """[41] «No ajustar» no necesita dia ni obra: sin calendario se guarda
    igual (solo «Ajustar» los exige)."""
    ids = _dia15(fabrica)
    cliente, _sv5 = portal(calendario=CalendarioNoFiable())
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("no_ajustar")})
    # El registro lo para Sesame (422), pero la decision ya se guardo.
    assert r.json()["franquicias"][0]["estado"] == "rechazado", r.text
    [f] = _filas(fabrica)
    assert (f.estado, f.decision) == ("rechazado", "no_ajustar")


def test_f056_r8_ejecutar_ajustar_tras_rechazo_con_dia_sin_calendario(
        fabrica, portal):
    """[42] R8: tras «No ajustar» con dia, «Ajustar» reutiliza el dia y la
    obra de la fila aunque hoy no se pueda calcular la propuesta."""
    ids = _dia15(fabrica)
    _decidido(fabrica, "no_ajustar")
    cliente, _sv5 = portal(calendario=CalendarioNoFiable())
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    # El registro lo para Sesame (422), pero la decision ya se guardo.
    assert r.json()["franquicias"][0]["estado"] == "decidido", r.text
    [f] = _filas(fabrica)
    assert (f.estado, f.fecha_int, f.obra_codigo) == (
        "decidido", 20261015, "0100")


def test_f056_r15_sin_lineas_que_registrar_ok_y_las_excluidas(fabrica,
                                                              portal):
    """[43, 44] Sin nada que registrar pero con la decision guardada: `ok`
    y las excluidas tal cual (no vacias)."""
    ids = sembrar_parte(fabrica, [{"horas": 8.0, "estado": "registrado",
                                   "partida_cod": "01.01"}],
                        document_id="dreg", fecha="2026-10-15")
    cliente, _sv5 = portal()
    sin_franq = cliente.post("/api/aprobar/ejecutar",
                             json={"registro_ids": ids})
    assert sin_franq.status_code == 422
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids, "franquicias": _decision("ajustar")})
    assert r.json()["ok"] is True
    assert r.json()["excluidas"] == sin_franq.json()["excluidas"] != {}


def test_f056_r17_aplicar_inexistente_dice_ok_false(fabrica, portal):
    """[53] El 404 lleva `ok: false` (el JS lo mira)."""
    cliente, _sv5 = portal()
    r = cliente.post("/api/franquicia/999/aplicar")
    assert (r.status_code, r.json()["ok"]) == (404, False)


def test_f056_r19_aplicar_sin_respuesta_conserva_lo_que_dijo_sv5(fabrica,
                                                                 portal):
    """[55] R19: sin respuesta de sv5 la fila pasa a error SIN perder lo
    que sv5 dijo en la aplicacion anterior."""
    _dia15(fabrica)
    repo = _repo(fabrica)
    f = _decidido(fabrica)
    repo.cerrar_ajuste(f["id"], ok=True, sv5=EJECUTAR_OK, error=None,
                       actor="eva")
    repo.decidir_ajuste(REC, "2026-10", "recalcular", None, actor="eva")
    cliente, _sv5 = portal(sv5=Sv5Franq(ejecutar=RuntimeError("timeout")))
    aj = cliente.post(f"/api/franquicia/{f['id']}/aplicar").json()["ajuste"]
    assert (aj["estado"], aj["extras"], aj["ajuste"], aj["hmores_ide"]) == (
        "error", 12.0, -6.0, 7009)


def test_f056_r17_aplicar_que_falla_no_es_ok_aunque_otro_lo_aplicara(
        fabrica, portal):
    """[56] Si sv5 dice que no, la respuesta es `ok: false` aunque otro
    usuario haya dejado la fila `aplicado` mientras tanto."""
    _dia15(fabrica)
    f = _decidido(fabrica)
    repo = _repo(fabrica)

    class Sv5Carrera(Sv5Franq):
        def franquicia_ejecutar(self, payload):
            super().franquicia_ejecutar(payload)
            repo.cerrar_ajuste(f["id"], ok=True, sv5=EJECUTAR_OK, error=None,
                               actor="otro")
            return {"ok": False, "accion": "no_editable", "motivo": "x"}

    cliente, _sv5 = portal(sv5=Sv5Carrera())
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar").json()
    assert (r["ok"], r["ajuste"]["estado"]) == (False, "aplicado")


def test_f056_r48_preflight_pide_solo_el_recurso_de_las_lineas(fabrica,
                                                              portal):
    """R48, DA29: a `/recursos` solo van los `recurso_ide` de las lineas que
    se aprueban (los que eligio sv3 con la empresa de la obra), aunque la
    misma persona tenga otro recurso en otra empresa con lineas en el
    periodo y franquicia propia; el candidato es el de SU recurso."""
    sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-otra-emp",
                  fecha="2026-10-14", recurso_ide=601)   # sin extras: no R12
    ids = _dia15(fabrica)
    recursos = {"estado": "ok", "motivo": None, "recursos": {
        "501": {"franquicia": 8.0, "estado": "activa"},
        "601": {"franquicia": 20.0, "estado": "activa"}}}
    cliente, sv5 = portal(sv5=Sv5Franq(recursos=recursos,
                                       acciones=[_acc_he(2.0)]))
    r = _preflight(cliente, ids)
    assert r.status_code == 200, r.text
    assert [p for p, _t in sv5.recursos_pedidos] == [[REC]]
    [it] = r.json()["franquicias"]["items"]
    assert (it["recurso_ide"], it["franquicia"]) == (REC, 8.0)
    assert [p["recurso_ide"] for p in sv5.franq_comprobadas] == [REC]


def _otro_recurso_con_mas_horas(fabrica):
    """DA32 (observacion 6 del reviewer): la misma persona (mismo DNI) con
    OTRO recurso, de otra empresa, y mas horas ordinarias el dia de ajuste
    en otra obra (sin extras: no dispara R12)."""
    sembrar_parte(fabrica, [{"horas": 12.0, "partida_cod": "02.02"}],
                  document_id="d-otra-emp15", fecha="2026-10-15",
                  recurso_ide=601, obra_ide=20, obra_codigo="0200")


def test_f056_da32_preflight_obra_del_recurso_del_ajuste(fabrica, portal):
    """DA32, R7: la obra propuesta sale solo de las lineas del recurso del
    ajuste (0100), no de la obra de mas horas de la persona (0200)."""
    _otro_recurso_con_mas_horas(fabrica)
    ids = _dia15(fabrica)
    cliente, sv5 = portal(sv5=Sv5Franq(acciones=[_acc_he(2.0)]))
    r = _preflight(cliente, ids)
    assert r.status_code == 200, r.text
    [it] = r.json()["franquicias"]["items"]
    assert (it["recurso_ide"], it["obra"], it["partida_cod"]) == (
        REC, {"ide": 10, "codigo": "0100"}, "01.01")
    [p] = sv5.franq_comprobadas
    assert (p["recurso_ide"], p["obra"], p["fecha_int"]) == (
        REC, {"ide": 10, "codigo": "0100"}, 20261015)
