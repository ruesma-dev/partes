# tests/test_f056_api.py
"""F-056 · rutas `POST /api/franquicia/comprobar` y `/api/franquicia/
ejecutar` de sv5 (R22) y su composicion en `main.py`.

Sin red: el pipeline es un doble que graba lo que recibe, o el real sobre
`SigridFake`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from application.pipelines.franquicia_pipeline import FranquiciaPipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import PeticionFranquicia, ResultadoFranquicia
from interface_adapters.api.app import build_app
from tests.dobles import SettingsFake
from tests.test_f056_pipeline import _cli, _pipe

RUTAS = ["/api/franquicia/comprobar", "/api/franquicia/ejecutar"]


class FranquiciaGrabador:
    """Doble de `FranquiciaPipeline`: graba y devuelve lo configurado."""

    def __init__(self, resultado=None, fallo: Exception | None = None):
        self.resultado = resultado or ResultadoFranquicia(ok=True,
                                                          accion="crear")
        self.fallo = fallo
        self.llamadas: list[tuple] = []

    def comprobar(self, p):
        self.llamadas.append(("comprobar", p, None))
        if self.fallo:
            raise self.fallo
        return self.resultado

    def ejecutar(self, p, usuario=None):
        self.llamadas.append(("ejecutar", p, usuario))
        if self.fallo:
            raise self.fallo
        return self.resultado


def _app(franquicia) -> TestClient:
    st = SettingsFake()
    reg = RegistroPipeline(cliente=object(), settings=st)
    return TestClient(build_app(st, pipeline=reg, comprobador=object(),
                                reajuste=object(), franquicia=franquicia))


def _cuerpo(**kw) -> dict:
    d = {"ajuste_id": 5, "recurso_ide": 501, "franquicia": 8.0,
         "periodo": "2026-10", "inicio": 20260916, "fin": 20261015,
         "fecha_int": 20261015, "obra": {"ide": 10, "codigo": "0100"},
         "partida_ide": 33, "partida_cod": "01.01", "extras_pendientes": 0,
         "usuario": "usuario-de-prueba"}
    d.update(kw)
    return d


# --------------------------------- entrada --------------------------------- #

@pytest.mark.parametrize("ruta", RUTAS)
def test_f056_r22_cuerpo_valido_llega_al_pipeline(ruta):
    fq = FranquiciaGrabador()
    r = _app(fq).post(ruta, json=_cuerpo(extras_pendientes=-2.5))
    assert r.status_code == 200, r.text
    [(op, p, usuario)] = fq.llamadas
    assert op == ruta.rsplit("/", 1)[1]
    assert isinstance(p, PeticionFranquicia)
    assert (p.ajuste_id, p.recurso_ide, p.franquicia, p.periodo, p.inicio,
            p.fin, p.fecha_int, p.partida_ide, p.partida_cod,
            p.extras_pendientes, p.usuario) == (
        5, 501, 8.0, "2026-10", 20260916, 20261015, 20261015, 33, "01.01",
        -2.5, "usuario-de-prueba")
    assert (p.obra.ide, p.obra.codigo) == (10, "0100")
    if op == "ejecutar":
        assert usuario == "usuario-de-prueba"


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("cambio", [
    {"ajuste_id": -1},
    {"recurso_ide": 0},
    {"franquicia": -0.5},
    {"periodo": "2026-13"},
    {"periodo": "26-10"},
    {"periodo": "2026-1"},
    {"inicio": 20261016},                      # inicio > fecha
    {"fin": 20261014},                         # fecha > fin
    {"fecha_int": 20261099},                   # fecha imposible
    {"inicio": 2026091},                       # no es YYYYMMDD
    {"obra": {}},                              # sin ide ni codigo
    {"obra": None},
    {"recurso_ide": None},
])
def test_f056_r22_cuerpo_invalido_es_422_sin_llamar(ruta, cambio):
    fq = FranquiciaGrabador()
    r = _app(fq).post(ruta, json=_cuerpo(**cambio))
    assert r.status_code == 422, (cambio, r.text)
    assert fq.llamadas == []


def test_f056_r22_centinela_vale_para_comprobar():
    fq = FranquiciaGrabador()
    r = _app(fq).post(RUTAS[0], json=_cuerpo(ajuste_id=0))
    assert r.status_code == 200
    assert fq.llamadas[0][1].ajuste_id == 0


def test_f056_r22_centinela_en_ejecutar_es_422():
    fq = FranquiciaGrabador()
    r = _app(fq).post(RUTAS[1], json=_cuerpo(ajuste_id=0))
    assert r.status_code == 422
    assert "ajuste_id" in r.json()["error"]
    assert r.json()["ok"] is False
    assert fq.llamadas == []


def test_f056_r22_obra_solo_por_codigo_vale():
    fq = FranquiciaGrabador()
    r = _app(fq).post(RUTAS[0], json=_cuerpo(obra={"codigo": "0100"}))
    assert r.status_code == 200
    assert fq.llamadas[0][1].obra.ide is None


# --------------------------------- salida --------------------------------- #

@pytest.mark.parametrize("ruta", RUTAS)
def test_f056_r22_respuesta_es_el_resultado_entero(ruta):
    res = ResultadoFranquicia(
        ok=False, accion="no_editable", extras=6.0, objetivo=-6.0,
        actual=-5.0, hmores_ide=7009, hmoide=900, parte_cod="PT26/00314",
        parte_estado=3, complementario=True, hora_codigo="HE01", pre=25.0,
        motivo="parte_no_abierto: x", escrita=False, forzada_pruebas=True,
        error="parte_no_abierto: x")
    r = _app(FranquiciaGrabador(res)).post(ruta, json=_cuerpo())
    assert r.status_code == 200
    assert r.json() == {
        "ok": False, "accion": "no_editable", "extras": 6.0,
        "objetivo": -6.0, "actual": -5.0, "hmores_ide": 7009, "hmoide": 900,
        "parte_cod": "PT26/00314", "parte_estado": 3, "complementario": True,
        "hora_codigo": "HE01", "pre": 25.0, "motivo": "parte_no_abierto: x",
        "escrita": False, "forzada_pruebas": True,
        "error": "parte_no_abierto: x"}


@pytest.mark.parametrize("ruta", RUTAS)
def test_f056_r22_fallo_del_pipeline_es_502(ruta):
    fq = FranquiciaGrabador(fallo=RuntimeError("sigrid-api read HTTP 500"))
    r = _app(fq).post(ruta, json=_cuerpo())
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": "sigrid-api read HTTP 500"}


@pytest.mark.parametrize("ruta", RUTAS)
def test_f056_r22_sin_pipeline_es_503(ruta):
    r = _app(None).post(ruta, json=_cuerpo())
    assert r.status_code == 503
    assert r.json()["ok"] is False


def test_f056_r22_de_punta_a_punta_con_el_pipeline_real():
    cli = _cli()
    pipe, _lock = _pipe(cli)
    c = _app(pipe)
    r = c.post(RUTAS[0], json=_cuerpo())
    assert r.status_code == 200 and r.json()["accion"] == "crear"
    r = c.post(RUTAS[1], json=_cuerpo())
    assert r.status_code == 200, r.text
    assert (r.json()["ok"], r.json()["escrita"], r.json()["actual"]) == (
        True, True, -6.0)


# --------------------------------- main.py --------------------------------- #

def test_f056_r22_main_compone_la_franquicia_sobre_el_pipeline_compartido(
        monkeypatch):
    import main as entrypoint

    st = SettingsFake()
    for k, v in {"log_dir": "logs", "log_level": "INFO",
                 "sigrid_api_base_url": "http://sigrid.invalid",
                 "sigrid_api_function_key": "k", "sigrid_api_database": "bd",
                 "sigrid_api_timeout_s": 1.0, "sigrid_max_statements": 15,
                 "sigrid_api_max_rows": 500000,
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
    franquicia, pipeline = capturado["franquicia"], capturado["pipeline"]
    assert isinstance(franquicia, FranquiciaPipeline)
    assert franquicia.lock is pipeline.lock
    assert franquicia._cli is capturado["reajuste"]._cli
