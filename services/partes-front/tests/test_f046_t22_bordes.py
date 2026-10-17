# tests/test_f046_t22_bordes.py
"""F-046 T22 · bordes del reajuste en sv4 que la campana de mutacion dejo
sin vigilar (supervivientes de `progress/mutacion_F-046.md`).

  - repositorio: reserva de ids sin PostgreSQL, comprobaciones de
    `iniciar_aplicacion` (linea que ya no esta, tolerancia, mensaje) y
    `cerrar_aplicacion` (error recortado, CAS perdido, log);
  - cliente de sv5: un 400 es un no y el log recorta el cuerpo;
  - rutas: logs con traza, fallo de `comprobar`, aviso en un rechazo,
    ambito no valido, 409 de un reparto ajeno, sv5 que lanza, motivo del
    rechazo, sv5 sin configurar, «Mantener» y la respuesta cuando ya no
    queda nada que registrar.

Repositorio real sobre SQLite en memoria; sv5 y el recalculo, dobles.
Datos SINTETICOS (los ficticios de `dobles`).
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from application.services.reparto_aviso import (
    MOTIVO_SIN_COMPROBAR,
    RepartoCambiadoError,
)
from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer import transfer_client as modulo_transfer
from infrastructure.transfer.transfer_client import TransferClient
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f046_aplicar import (
    PublisherFake,
    RecalculoFake,
    Sv5Fake,
    _cambio,
    _caso_real,
    _dia,
    _fila,
    _marcar,
    _reparto,
    _repo,
)


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def portal(entorno, fabrica):
    def _montar(*, sv5=None, publisher=None):
        sv5 = sv5 or Sv5Fake()
        recalculo = RecalculoFake()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        recalculo_publisher=recalculo)
        return TestClient(app), sv5, recalculo
    return _montar


# ============================== repositorio ============================== #

def test_f046_t22_reserva_sin_postgresql_es_el_siguiente_al_mayor(fabrica):
    with fabrica.create_session() as s:
        assert ParteReviewRepository._reservar_id(s, {}) == 1
    (a, b) = sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 1.0}])
    with fabrica.create_session() as s:
        assert ParteReviewRepository._reservar_id(s, {}) == b + 1
        assert ParteReviewRepository._reservar_id(
            s, {"7": b + 5, "8": a}) == b + 6


def test_f046_t22_iniciar_con_una_linea_que_ya_no_existe_es_409(fabrica):
    (base, extra), libre, _le = _dia(fabrica)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 2.5),
                             _cambio(999999, base, "extra", -4.0, 1.5)],
                   [base, extra, libre])
    with pytest.raises(RepartoCambiadoError,
                       match="la linea 999999 ya no esta en el portal"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")
    assert _fila(fabrica, rid).estado == "pendiente"


def test_f046_t22_iniciar_con_una_linea_en_la_papelera_dice_cual(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, deleted_at_utc="2026-03-03T00:00:00+00:00")
    with pytest.raises(RepartoCambiadoError,
                       match=f"la linea {base} ya no esta en el portal"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_t22_iniciar_tolera_1e_6_horas(fabrica):
    (base, extra), libre, _le = _dia(fabrica)
    _marcar(fabrica, extra, horas=1e-6)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 2.5),
                             _cambio(extra, base, "extra", 0.0, 1.5)],
                   [base, extra, libre])
    _repo(fabrica).iniciar_aplicacion(rid, actor="a")
    assert _fila(fabrica, rid).estado == "aplicando"


def test_f046_t22_iniciar_con_linea_cambiada_dice_cuanto_tiene(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, horas=7.0)
    with pytest.raises(RepartoCambiadoError) as err:
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")
    assert str(err.value) == (f"la linea {base} cambio: tiene 7 h y el "
                              "aviso decia 8 h; recarga la pagina")


def test_f046_t22_cerrar_recorta_el_error_a_255(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    repo.cerrar_aplicacion(rid, ok=False, sv5=None, error="e" * 300,
                           actor="a")
    assert _fila(fabrica, rid).error == "e" * 255


def test_f046_t22_cerrar_un_reparto_que_ya_no_esta_aplicando(fabrica):
    """Otro proceso lo cerro antes: se devuelve el estado que TIENE."""
    rid, *_ = _caso_real(fabrica)
    assert _repo(fabrica).cerrar_aplicacion(
        rid, ok=True, sv5={"ok": True}, error=None, actor="a") == "pendiente"
    assert _fila(fabrica, rid).estado == "pendiente"


def _log_cierre(caplog, fabrica, *, ok, error):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    with caplog.at_level(logging.INFO):
        repo.cerrar_aplicacion(rid, ok=ok, sv5=None, error=error,
                               actor="admin@test")
    (texto,) = [r.getMessage() for r in caplog.records
                if r.getMessage().startswith(f"[reparto] reparto {rid} -> ")]
    return rid, texto


def test_f046_t22_log_de_cierre_ok_sin_error(fabrica, caplog):
    rid, texto = _log_cierre(caplog, fabrica, ok=True, error="ruido")
    assert texto == f"[reparto] reparto {rid} -> aplicado (por admin@test)"


def test_f046_t22_log_de_cierre_rechazado_con_su_error(fabrica, caplog):
    rid, texto = _log_cierre(caplog, fabrica, ok=False, error="no editable")
    assert texto == (f"[reparto] reparto {rid} -> pendiente "
                     "(por admin@test): no editable")


def test_f046_t22_log_de_cierre_rechazado_sin_error(fabrica, caplog):
    rid, texto = _log_cierre(caplog, fabrica, ok=False, error=None)
    assert texto == f"[reparto] reparto {rid} -> pendiente (por admin@test)"


# ============================= cliente de sv5 ============================= #

def test_f046_t22_un_400_de_sv5_es_un_no_con_su_error(monkeypatch, caplog):
    cuerpo = {"error": "x" * 400}
    monkeypatch.setattr(modulo_transfer.httpx, "post",
                        lambda *a, **k: httpx.Response(400, json=cuerpo))
    cli = TransferClient(base_url="http://sv5.invalid", timeout_s=30)
    with caplog.at_level(logging.WARNING):
        r = cli.reajuste_ejecutar({})
    assert r == {"ok": False, "error": "x" * 400}
    (texto,) = [x.getMessage() for x in caplog.records
                if "HTTP 400" in x.getMessage()]
    assert texto == ("[transfer] /api/reajuste/ejecutar HTTP 400: "
                     + json.dumps(cuerpo, separators=(",", ":"))[:300])


# ================================= rutas ================================= #

def test_f046_t22_comprobar_que_lanza_deja_traza_y_su_error(fabrica, portal,
                                                             caplog):
    _rid, _b, _e, libre, _le = _caso_real(fabrica)

    class Sv5Roto(Sv5Fake):
        def reajuste_comprobar(self, payload, *, timeout_s=None):
            raise RuntimeError("sv5 caido")
    cliente, _s, _r = portal(sv5=Sv5Roto())
    with caplog.at_level(logging.WARNING):
        (b,) = cliente.post("/api/aprobar/preflight", json={
            "registro_ids": [libre]}).json()["repartos"]
    assert b["editable"] is False
    assert b["motivo"] == f"{MOTIVO_SIN_COMPROBAR}: sv5 caido"
    (rec,) = [r for r in caplog.records
              if "comprobar el reparto" in r.getMessage()]
    assert rec.exc_info and rec.exc_info[0] is RuntimeError


@pytest.mark.parametrize("respuesta,motivo", [
    ({"ok": False, "error": "sigrid no contesta"}, "sigrid no contesta"),
    ({"ok": False}, "sin respuesta"),
])
def test_f046_t22_comprobar_sin_veredictos_da_su_motivo(fabrica, portal,
                                                        respuesta, motivo):
    _rid, _b, _e, libre, _le = _caso_real(fabrica)
    cliente, _s, _r = portal(sv5=Sv5Fake(comprobar=respuesta))
    (b,) = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": [libre]}).json()["repartos"]
    assert b["editable"] is False
    assert b["motivo"] == f"{MOTIVO_SIN_COMPROBAR}: {motivo}"


def test_f046_t22_preflight_rechazado_lleva_el_aviso_de_repartos(fabrica,
                                                                  portal):
    """Pedir solo lineas ya registradas es un rechazo; si su dia tiene
    reparto, el rechazo trae el aviso."""
    rid, base, *_ = _caso_real(fabrica)
    cliente, _s, _r = portal()
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": [base]})
    assert r.status_code >= 400
    assert [b["id"] for b in r.json()["repartos"]] == [rid]


def test_f046_t22_preflight_rechazado_sin_reparto_no_lleva_aviso(fabrica,
                                                                 portal):
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0, "estado":
                                       "registrado"}], document_id="doc-x")
    cliente, _s, _r = portal()
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": [otro]})
    assert r.status_code >= 400 and "repartos" not in r.json()


def test_f046_t22_ambito_no_valido_no_decide_ningun_reparto(fabrica, portal):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre], "ambito": {"vista": "nada"},
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 422
    assert sv5.reajustes == [] and _fila(fabrica, rid).estado == "pendiente"


def test_f046_t22_reparto_ajeno_responde_ok_false(fabrica, portal):
    rid, *_ = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    cliente, _s, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [otro],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 409
    assert r.json() == {"ok": False, "error": (
        f"el reparto {rid} no es de un dia de estas lineas o ya no esta "
        "pendiente: recarga la pagina")}


def test_f046_t22_sv5_que_lanza_deja_el_reparto_aplicando(fabrica, portal,
                                                          caplog):
    """Una excepcion del cliente no dice si Sigrid llego a escribirse: el
    reparto sigue `aplicando` (reintento seguro, R34), con traza."""
    rid, _b, _e, libre, _le = _caso_real(fabrica)

    class Sv5Roto(Sv5Fake):
        def reajuste_ejecutar(self, payload):
            raise RuntimeError("conexion cortada")
    cliente, sv5, _r = portal(sv5=Sv5Roto())
    with caplog.at_level(logging.WARNING):
        r = cliente.post("/api/aprobar/ejecutar", json={
            "registro_ids": [libre],
            "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 200, r.text
    assert (_fila(fabrica, rid).estado, _fila(fabrica, rid).error) == (
        "aplicando", "conexion cortada")
    (res,) = r.json()["repartos"]
    assert (res["estado"], res["ok"]) == ("aplicando", False)
    assert sv5.ejecutadas == []
    (rec,) = [x for x in caplog.records
              if f"reajuste {rid} fallo" in x.getMessage()]
    assert rec.exc_info and rec.exc_info[0] is RuntimeError


def test_f046_t22_motivo_del_rechazo_es_el_primero_con_motivo(fabrica,
                                                               portal):
    rid, base, extra, libre, _le = _caso_real(fabrica)
    sv5 = Sv5Fake(reajuste={"ok": False, "error": "hay lineas que no se "
                            "pueden reajustar", "veredictos": [
                                {"registro_id": base, "editable": False,
                                 "motivo": None},
                                {"registro_id": 1, "editable": True,
                                 "motivo": "no cuenta"},
                                {"registro_id": extra, "editable": False,
                                 "motivo": "la linea cambio en Sigrid"}]})
    cliente, _s, _r = portal(sv5=sv5)
    cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert _fila(fabrica, rid).error == ("hay lineas que no se pueden "
                                         "reajustar: la linea cambio en "
                                         "Sigrid")


def test_f046_t22_encolar_sin_sv5_configurado_no_aplica(entorno, fabrica):
    """Con cola pero sin sv5 (sin TRANSFER_BASE_URL), «Aplicar» no puede
    editar Sigrid: el reparto vuelve a `pendiente` con el motivo."""
    entorno.delenv("TRANSFER_BASE_URL")
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=None, publisher=PublisherFake(),
                    recalculo_publisher=RecalculoFake())
    r = TestClient(app).post("/api/aprobar/encolar", json={
        "registro_ids": [libre],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.error) == (
        "pendiente", "registro en Sigrid no configurado (TRANSFER_BASE_URL)")
    (res,) = r.json()["repartos"]
    assert (res["estado"], res["ok"]) == ("pendiente", False)


def test_f046_t22_mantener_sin_nada_que_registrar_responde_ok(fabrica,
                                                              portal):
    """Se decidio «Mantener» y las lineas pedidas quedan fuera: la
    peticion SI hizo algo (200, `ok`), con lo excluido y el aviso."""
    rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    cliente, _s, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre, libre_extra],
        "repartos": [{"id": rid, "decision": "mantener"}]})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["ok"] is True and cuerpo["grupos"] == []
    assert cuerpo["excluidas"] and sum(cuerpo["excluidas"].values()) == 2
    assert cuerpo["aviso"]
    assert cuerpo["repartos"] == [{"id": rid, "decision": "mantener",
                                   "estado": "rechazado", "ok": True,
                                   "error": None}]
