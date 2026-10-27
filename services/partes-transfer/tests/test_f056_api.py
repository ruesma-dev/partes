# tests/test_f056_api.py
"""F-056 · rutas `POST /api/franquicia/comprobar` y `/api/franquicia/
ejecutar` de sv5 (R22) y su composicion en `main.py`.

Enmienda 2026-10-27 (T11, DA1 = C): la peticion ya no trae X (R41), la
respuesta trae `franquicia` y `franquicia_estado`, y hay una ruta nueva,
`POST /api/franquicia/recursos` (R40); `/health` dice si la franquicia
esta `apagada` o `configurada` y `main.py` deja una linea de cableado.

Sin red: el pipeline es un doble que graba lo que recibe, o el real sobre
`SigridFake`. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from application.pipelines.franquicia_pipeline import FranquiciaPipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    EstadoFranquicias,
    LecturaFranquicia,
    PeticionFranquicia,
    ResultadoFranquicia,
)
from interface_adapters.api.app import build_app
from tests.dobles import SettingsFake
from tests.test_f056_pipeline import _cli, _pipe

RUTAS = ["/api/franquicia/comprobar", "/api/franquicia/ejecutar"]
RECURSOS = "/api/franquicia/recursos"


class FranquiciaGrabador:
    """Doble de `FranquiciaPipeline`: graba y devuelve lo configurado."""

    def __init__(self, resultado=None, fallo: Exception | None = None,
                 estado: EstadoFranquicias | None = None):
        self.resultado = resultado or ResultadoFranquicia(ok=True,
                                                          accion="crear")
        self.fallo = fallo
        self.estado = estado or EstadoFranquicias("apagada", "vacio")
        self.llamadas: list[tuple] = []

    def franquicias(self, ides):
        self.llamadas.append(("recursos", list(ides), None))
        if self.fallo:
            raise self.fallo
        return self.estado

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


def _app(franquicia, campo: str = "") -> TestClient:
    st = SettingsFake(franquicia_campo_res=campo)
    st.sigrid_api_database = "bd"
    reg = RegistroPipeline(cliente=object(), settings=st)
    return TestClient(build_app(st, pipeline=reg, comprobador=object(),
                                reajuste=object(), franquicia=franquicia))


def _cuerpo(**kw) -> dict:
    d = {"ajuste_id": 5, "recurso_ide": 501,
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
    assert (p.ajuste_id, p.recurso_ide, p.periodo, p.inicio,
            p.fin, p.fecha_int, p.partida_ide, p.partida_cod,
            p.extras_pendientes, p.usuario) == (
        5, 501, "2026-10", 20260916, 20261015, 20261015, 33, "01.01",
        -2.5, "usuario-de-prueba")
    assert (p.obra.ide, p.obra.codigo) == (10, "0100")
    if op == "ejecutar":
        assert usuario == "usuario-de-prueba"


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("cambio", [
    {"ajuste_id": -1},
    {"recurso_ide": 0},
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
        error="parte_no_abierto: x", franquicia=8.0,
        franquicia_estado="activa")
    r = _app(FranquiciaGrabador(res)).post(ruta, json=_cuerpo())
    assert r.status_code == 200
    assert r.json() == {
        "ok": False, "accion": "no_editable", "extras": 6.0,
        "objetivo": -6.0, "actual": -5.0, "hmores_ide": 7009, "hmoide": 900,
        "parte_cod": "PT26/00314", "parte_estado": 3, "complementario": True,
        "hora_codigo": "HE01", "pre": 25.0, "motivo": "parte_no_abierto: x",
        "escrita": False, "forzada_pruebas": True,
        "error": "parte_no_abierto: x", "franquicia": 8.0,
        "franquicia_estado": "activa"}


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
    assert (r.json()["franquicia"], r.json()["franquicia_estado"]) == (
        8.0, "activa")


@pytest.mark.parametrize("ruta", RUTAS)
def test_f056_r41_la_x_de_la_peticion_se_ignora(ruta):
    """R41: X no viaja en la peticion; un sv4 viejo que la mande no la cuela
    (pydantic ignora el campo de mas)."""
    fq = FranquiciaGrabador()
    r = _app(fq).post(ruta, json=_cuerpo(franquicia=99.0))
    assert r.status_code == 200
    assert not hasattr(fq.llamadas[0][1], "franquicia")


# ------------------------- /api/franquicia/recursos ------------------------- #

def test_f056_r40_recursos_ok_por_recurso():
    fq = FranquiciaGrabador(estado=EstadoFranquicias("ok", None, {
        501: LecturaFranquicia("activa", 8.0),
        502: LecturaFranquicia("inactiva", 0.0),
        503: LecturaFranquicia("invalida", None, "valor -1 fuera")}))
    r = _app(fq).post(RECURSOS, json={"recurso_ides": [501, 502, 503]})
    assert r.status_code == 200, r.text
    assert r.json() == {"estado": "ok", "motivo": None, "recursos": {
        "501": {"franquicia": 8.0, "estado": "activa"},
        "502": {"franquicia": 0.0, "estado": "inactiva"},
        "503": {"franquicia": None, "estado": "invalida"}}}
    assert fq.llamadas == [("recursos", [501, 502, 503], None)]


@pytest.mark.parametrize("estado", [
    EstadoFranquicias("apagada", "FRANQUICIA_CAMPO_RES vacio"),
    EstadoFranquicias("no_disponible", "la columna x no existe en res")])
def test_f056_r40_recursos_sin_ok_va_vacio(estado):
    r = _app(FranquiciaGrabador(estado=estado)).post(
        RECURSOS, json={"recurso_ides": [501]})
    assert r.status_code == 200
    assert r.json() == {"estado": estado.estado, "motivo": estado.motivo,
                        "recursos": {}}


@pytest.mark.parametrize("cuerpo", [
    {}, {"recurso_ides": []}, {"recurso_ides": None},
    {"recurso_ides": [0]}, {"recurso_ides": [-3]}, {"recurso_ides": ["x"]},
    {"recurso_ides": list(range(1, 502))}, {"recurso_ides": 501}])
def test_f056_r40_recursos_cuerpo_invalido_es_422(cuerpo):
    fq = FranquiciaGrabador()
    r = _app(fq).post(RECURSOS, json=cuerpo)
    assert r.status_code == 422, (cuerpo, r.text)
    assert fq.llamadas == []


def test_f056_r40_recursos_admite_500():
    fq = FranquiciaGrabador()
    r = _app(fq).post(RECURSOS, json={"recurso_ides": list(range(1, 501))})
    assert r.status_code == 200
    assert len(fq.llamadas[0][1]) == 500


def test_f056_r40_recursos_fallo_al_leer_el_tipo_es_502():
    fq = FranquiciaGrabador(fallo=RuntimeError("sigrid-api read HTTP 500"))
    r = _app(fq).post(RECURSOS, json={"recurso_ides": [501]})
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": "sigrid-api read HTTP 500"}


def test_f056_r40_recursos_sin_pipeline_es_503():
    r = _app(None).post(RECURSOS, json={"recurso_ides": [501]})
    assert r.status_code == 503 and r.json()["ok"] is False


def test_f056_r40_recursos_con_el_pipeline_real_sin_lock():
    cli = _cli()
    cli.valores_res = {501: 8.0, 502: None}
    pipe, lock = _pipe(cli)
    r = _app(pipe).post(RECURSOS, json={"recurso_ides": [502, 501, 999]})
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "ok"
    assert r.json()["recursos"] == {
        "501": {"franquicia": 8.0, "estado": "activa"},
        "502": {"franquicia": 0.0, "estado": "inactiva"},
        "999": {"franquicia": None, "estado": "invalida"}}
    assert lock.tomas == 0 and "escribir" not in cli.llamadas


# --------------------------------- /health --------------------------------- #

@pytest.mark.parametrize("campo, esperado", [
    ("", "apagada"), ("CampoInventado", "configurada"),
    ("a];--", "configurada")])
def test_f056_r3_health_dice_si_la_franquicia_esta_configurada(campo,
                                                               esperado):
    """design §4: sin leer Sigrid (un nombre malo sale `configurada`: su
    `no_disponible` lo da `/recursos`, que si lee)."""
    fq = FranquiciaGrabador()
    r = _app(fq, campo=campo).get("/health")
    assert r.status_code == 200
    assert r.json()["franquicia"] == esperado
    assert fq.llamadas == []


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
    assert st.franquicia_campo_res == ""
    assert isinstance(franquicia, FranquiciaPipeline)
    assert franquicia.lock is pipeline.lock
    assert franquicia._cli is capturado["reajuste"]._cli


def _main_con_campo(monkeypatch, campo: str):
    import main as entrypoint

    st = SettingsFake(franquicia_campo_res=campo)
    for k, v in {"log_dir": "logs", "log_level": "INFO",
                 "sigrid_api_base_url": "http://sigrid.invalid",
                 "sigrid_api_function_key": "k", "sigrid_api_database": "bd",
                 "sigrid_api_timeout_s": 1.0, "sigrid_max_statements": 15,
                 "sigrid_api_max_rows": 500000,
                 "tip_parte_trabajo": 35, "storage_habilitado": False,
                 "api_host": "127.0.0.1", "api_port": 1}.items():
        setattr(st, k, v)
    monkeypatch.setattr(entrypoint, "Settings", lambda: st)
    monkeypatch.setattr(entrypoint, "configure_logging", lambda *a: None)
    monkeypatch.setattr(entrypoint, "build_app", lambda s, **kw: "app")
    monkeypatch.setattr(entrypoint.uvicorn, "run", lambda *a, **kw: None)
    assert entrypoint.main() == 0


@pytest.mark.parametrize("campo, nivel, texto", [
    ("", logging.INFO, "apagada"),
    ("CampoInventado", logging.INFO, "configurada"),
    ("a];DROP TABLE res;--", logging.WARNING, "no es un nombre de columna"),
])
def test_f056_r38_main_deja_la_linea_de_cableado(monkeypatch, caplog, campo,
                                                 nivel, texto):
    """design §4: una linea INFO con el estado al arrancar (WARNING si el
    nombre no casa `CAMPO_RE`); sv5 arranca igual (R38)."""
    with caplog.at_level(logging.INFO):
        _main_con_campo(monkeypatch, campo)
    lineas = [r for r in caplog.records if "[franquicia]" in r.getMessage()]
    assert len(lineas) == 1
    assert lineas[0].levelno == nivel and texto in lineas[0].getMessage()

