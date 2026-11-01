# tests/test_f046_api_reajuste.py
"""F-046 · rutas `POST /api/reajuste/comprobar` y `/api/reajuste/ejecutar`
de sv5 (R20, R23, R26) y su composicion en `main.py`.

Sin red: el pipeline es el real sobre `SigridReajusteFake`, o un doble que
graba lo que recibe. Datos SINTETICOS.
"""
from __future__ import annotations

import threading

import pytest
from application.pipelines.reajuste_pipeline import ReajustePipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ResultadoReajuste, VeredictoReajuste
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import MAX_LINEAS_REAJUSTE, build_app
from tests.dobles import SettingsFake
from tests.test_f046_reajuste_pipeline import NUEVA, _caso_extra_nueva


class ReajusteGrabador:
    """Doble de `ReajustePipeline`: graba y devuelve lo configurado."""

    def __init__(self, resultado=None, fallo: Exception | None = None):
        self.resultado = resultado or ResultadoReajuste(ok=True)
        self.fallo = fallo
        self.llamadas: list[tuple] = []

    def comprobar(self, ops):
        self.llamadas.append(("comprobar", ops, None))
        if self.fallo:
            raise self.fallo
        return self.resultado

    def ejecutar(self, ops, usuario=None):
        self.llamadas.append(("ejecutar", ops, usuario))
        if self.fallo:
            raise self.fallo
        return self.resultado


def _app(reajuste) -> TestClient:
    st = SettingsFake()
    reg = RegistroPipeline(cliente=object(), settings=st)
    return TestClient(build_app(st, pipeline=reg, comprobador=object(),
                                reajuste=reajuste))


def _linea(rid=11, **kw) -> dict:
    d = {"registro_id": rid, "antes": 8.0, "despues": 2.5}
    d.update(kw)
    return d


@pytest.mark.parametrize("ruta", ["/api/reajuste/comprobar",
                                  "/api/reajuste/ejecutar"])
def test_f046_r20_cuerpo_vacio_o_de_mas_de_50_lineas_es_422(ruta):
    rj = ReajusteGrabador()
    cli = _app(rj)
    assert MAX_LINEAS_REAJUSTE == 50
    assert cli.post(ruta, json={"lineas": []}).status_code == 422
    demasiadas = [_linea(i) for i in range(1, 52)]
    assert cli.post(ruta, json={"lineas": demasiadas}).status_code == 422
    assert rj.llamadas == []
    justas = [_linea(i) for i in range(1, 51)]
    assert cli.post(ruta, json={"lineas": justas}).status_code == 200


def test_f046_r20_comprobar_devuelve_los_veredictos():
    rj = ReajusteGrabador(ResultadoReajuste(
        ok=False, veredictos=[VeredictoReajuste(11, True),
                              VeredictoReajuste(12, False, motivo="x")]))
    r = _app(rj).post("/api/reajuste/comprobar", json={"lineas": [
        _linea(11), _linea(12, antes=-4.0, despues=1.5)]})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert cuerpo["veredictos"] == [
        {"registro_id": 11, "editable": True, "ya_aplicada": False,
         "motivo": None},
        {"registro_id": 12, "editable": False, "ya_aplicada": False,
         "motivo": "x"}]
    ((_, ops, _),) = rj.llamadas
    assert [(o.registro_id, o.antes, o.despues, o.es_nueva) for o in ops] == [
        (11, 8.0, 2.5, False), (12, -4.0, 1.5, False)]


def test_f046_r20_ejecutar_pasa_la_nueva_y_el_usuario():
    rj = ReajusteGrabador(ResultadoReajuste(ok=True, lineas=[{"x": 1}]))
    nueva = {"registro_id": NUEVA, "despues": 2.5, "base_registro_id": 11,
             "recurso_ide": 501, "fecha_int": 20261014, "hora_ide": 9,
             "hora_codigo": "HE01", "partida_ide": 33, "partida_cod": "P-33",
             "obra_ide": 10, "obra_codigo": "9999"}
    r = _app(rj).post("/api/reajuste/ejecutar", json={
        "lineas": [_linea(11, despues=5.5), nueva], "usuario": "admin@test"})
    assert r.status_code == 200 and r.json()["lineas"] == [{"x": 1}]
    ((nombre, ops, usuario),) = rj.llamadas
    assert (nombre, usuario) == ("ejecutar", "admin@test")
    assert ops[1].es_nueva and ops[1].antes is None
    assert (ops[1].base_registro_id, ops[1].recurso_ide, ops[1].hora_ide,
            ops[1].obra_ide) == (11, 501, 9, 10)


@pytest.mark.parametrize("ruta", ["/api/reajuste/comprobar",
                                  "/api/reajuste/ejecutar"])
def test_f046_r20_si_sigrid_falla_es_502(ruta):
    rj = ReajusteGrabador(fallo=RuntimeError("sigrid-api caida"))
    r = _app(rj).post(ruta, json={"lineas": [_linea()]})
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": "sigrid-api caida"}


def test_f046_r23_rechazo_es_200_con_ok_false():
    rj = ReajusteGrabador(ResultadoReajuste(ok=False, error="no editable"))
    r = _app(rj).post("/api/reajuste/ejecutar", json={"lineas": [_linea()]})
    assert r.status_code == 200
    assert (r.json()["ok"], r.json()["error"]) == (False, "no editable")


def test_f046_r20_comprobar_por_http_no_toma_el_lock():
    cli, ops = _caso_extra_nueva()
    st = SettingsFake()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=threading.Lock())
    rj = ReajustePipeline(cliente=cli, settings=st, registro=reg)
    app = TestClient(build_app(st, pipeline=reg, comprobador=object(),
                               reajuste=rj))
    cuerpo = {"lineas": [
        {"registro_id": o.registro_id, "antes": o.antes,
         "despues": o.despues, "base_registro_id": o.base_registro_id,
         "recurso_ide": o.recurso_ide, "fecha_int": o.fecha_int,
         "hora_ide": o.hora_ide, "obra_ide": o.obra_ide,
         "obra_codigo": o.obra_codigo} for o in ops]}
    hecho = []
    reg.lock.acquire()
    try:
        hilo = threading.Thread(target=lambda: hecho.append(
            app.post("/api/reajuste/comprobar", json=cuerpo)))
        hilo.start()
        hilo.join(timeout=10)
        assert hecho, "comprobar espero al lock de escritura"
        assert hecho[0].json()["ok"] is True
    finally:
        reg.lock.release()


def test_f046_r20_build_app_sin_reajuste_lo_construye_con_el_lock_del_registro(
        monkeypatch):
    cli, ops = _caso_extra_nueva()
    monkeypatch.setattr(modulo_app, "_cliente_sigrid", lambda _s: cli)
    st = SettingsFake()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=threading.Lock())
    cli.vigilar_lock(reg.lock)      # escribir_lote falla fuera de ESE lock
    app = TestClient(build_app(st, pipeline=reg, comprobador=object()))
    r = app.post("/api/reajuste/ejecutar", json={"lineas": [
        {"registro_id": o.registro_id, "antes": o.antes,
         "despues": o.despues, "base_registro_id": o.base_registro_id,
         "recurso_ide": o.recurso_ide, "fecha_int": o.fecha_int,
         "hora_ide": o.hora_ide, "obra_ide": o.obra_ide,
         "obra_codigo": o.obra_codigo} for o in ops]})
    assert r.status_code == 200 and r.json()["ok"] is True, r.json()


def test_f046_r20_main_compone_el_reajuste_sobre_el_pipeline_compartido(
        monkeypatch):
    import main as entrypoint

    st = SettingsFake()
    for k, v in {"log_dir": "logs", "log_level": "INFO",
                 "sigrid_api_base_url": "http://sigrid.invalid",
                 "sigrid_api_function_key": "k", "sigrid_api_database": "bd",
                 "sigrid_api_timeout_s": 1.0, "sigrid_max_statements": 15,
                 "sigrid_api_max_rows": 500000,   # F-038 (R5)
                 "tip_parte_trabajo": 35, "storage_habilitado": False,
                 "api_host": "127.0.0.1", "api_port": 1}.items():
        setattr(st, k, v)
    capturado: dict = {}
    monkeypatch.setattr(entrypoint, "Settings", lambda: st)
    monkeypatch.setattr(entrypoint, "configure_logging", lambda *a: None)
    monkeypatch.setattr(entrypoint, "build_app",
                        lambda s, **kw: capturado.update(kw) or "app")
    monkeypatch.setattr(entrypoint.uvicorn, "run", lambda *a, **kw: None)
    assert entrypoint.main() == 0
    reajuste, pipeline = capturado["reajuste"], capturado["pipeline"]
    assert isinstance(reajuste, ReajustePipeline)
    assert reajuste.lock is pipeline.lock
