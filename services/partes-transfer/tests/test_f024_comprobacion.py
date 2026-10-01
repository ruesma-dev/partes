# tests/test_f024_comprobacion.py
"""F-024 · comprobacion de solo lectura de las lineas de sv5 en Sigrid (R1-R9).

Tres capas, sin red ni Sigrid:

  - `clasificar` (pura): tablas de casos de R2-R6.
  - el cliente (`lineas_por_ide`, `partes_por_ide`) contra sigrid-api
    simulado con `httpx.post` sustituido (R7, R8).
  - `ComprobadorLineas` y el endpoint `POST /api/registro/comprobar` con un
    cliente en memoria (R1, R8, R9).

Todos los `ide`, recursos y codigos son sinteticos.
"""
from __future__ import annotations

import pytest

from application.services.comprobacion_lineas import (
    LineaComprobar,
    Veredicto,
    clasificar,
)
from domain.models.registro_models import LineaSigrid

HMO = 7001          # parte (hmo.ide) sintetico
HMO_OTRO = 7002
COD = "PT26/09001"
COD_OTRO = "PT26/09002"


def _ls(ide: int, *, reside: int = 501, fecha: int = 20260916,
        can: float | None = 8.0, synckey: str | None = None,
        hmoide: int = HMO) -> LineaSigrid:
    """Una fila de `hmores` como la devuelve el cliente."""
    ls = LineaSigrid(ide=ide, reside=reside, fecha_int=fecha, horide=1,
                     hora_codigo=None, can=can, tot=None, synckey=synckey,
                     nuestra=bool(synckey))
    ls.hmoide = hmoide
    return ls


def _linea(rid: int = 11, *, hmores_ide: int | None = 4001,
           hmoide: int | None = HMO, recurso: int | None = 501,
           fecha: int | None = 20260916, horas: float | None = 8.0,
           incidencia: bool = False) -> LineaComprobar:
    return LineaComprobar(registro_id=rid, hmores_ide=hmores_ide,
                          hmoide=hmoide, recurso_ide=recurso,
                          fecha_int=fecha, horas=horas,
                          es_incidencia=incidencia)


def _uno(linea, *, synckey=None, ide=None, partes=None) -> Veredicto:
    por_sk = synckey or {}
    por_ide = ide or {}
    out = clasificar([linea], por_sk, por_ide,
                     {HMO: COD} if partes is None else partes)
    assert len(out) == 1
    return out[0]


# ===================================================================== #
# clasificar · R2-R6
# ===================================================================== #

def test_f024_r2_clasificar_acierto_por_synckey_es_presente() -> None:
    v = _uno(_linea(11), synckey={"partes:11": _ls(4001, synckey="partes:11")})
    assert v.estado == "presente"
    assert v.registro_id == 11
    assert v.sin_synckey is False
    assert v.parte_existe is True
    assert v.diferencias == []
    assert v.motivo is None


def test_f024_r2_clasificar_la_synckey_es_la_del_pipeline() -> None:
    """La clave es `partes:<registro_id>` (la de la idempotencia): otra
    clave del mismo `ide` no cuenta como acierto."""
    v = _uno(_linea(11), synckey={"partes:12": _ls(4001, synckey="partes:12")})
    assert v.estado == "borrada"


def test_f024_r5_clasificar_presente_lleva_las_referencias_actuales() -> None:
    """La linea se movio de parte en Sigrid: el veredicto trae lo de hoy."""
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO),
             synckey={"partes:11": _ls(4999, synckey="partes:11",
                                       hmoide=HMO_OTRO)},
             partes={HMO: COD, HMO_OTRO: COD_OTRO})
    assert (v.hmores_ide, v.hmoide, v.parte_cod) == (4999, HMO_OTRO, COD_OTRO)


def test_f024_r3_clasificar_respaldo_por_ide_sin_synckey() -> None:
    v = _uno(_linea(11), ide={4001: _ls(4001, synckey=None)})
    assert v.estado == "presente"
    assert v.sin_synckey is True
    assert (v.hmores_ide, v.hmoide, v.parte_cod) == (4001, HMO, COD)


def test_f024_r3_clasificar_respaldo_con_synckey_en_blanco() -> None:
    v = _uno(_linea(11), ide={4001: _ls(4001, synckey="   ")})
    assert v.estado == "presente" and v.sin_synckey is True


def test_f024_r3_clasificar_respaldo_sin_hmoide_enviado() -> None:
    """Sin `hmoide` en el portal, basta recurso y fecha (R3)."""
    v = _uno(_linea(11, hmoide=None), ide={4001: _ls(4001)})
    assert v.estado == "presente" and v.sin_synckey is True
    assert v.hmoide == HMO and v.parte_cod == COD


@pytest.mark.parametrize("fila", [
    pytest.param(_ls(4001, synckey="partes:99"), id="otra-synckey"),
    pytest.param(_ls(4001, synckey="ajena"), id="synckey-ajena"),
    pytest.param(_ls(4001, reside=502), id="otro-recurso"),
    pytest.param(_ls(4001, fecha=20260917), id="otra-fecha"),
    pytest.param(_ls(4001, hmoide=HMO_OTRO), id="otro-parte"),
])
def test_f024_r3_clasificar_ide_reutilizado_es_borrada(fila) -> None:
    v = _uno(_linea(11), ide={4001: fila}, partes={HMO: COD, HMO_OTRO: COD_OTRO})
    assert v.estado == "borrada"
    assert v.sin_synckey is False


def test_f024_r3_clasificar_linea_sin_recurso_no_casa_por_ide() -> None:
    v = _uno(_linea(11, recurso=None), ide={4001: _ls(4001)})
    assert v.estado == "borrada"


def test_f024_r4_clasificar_sin_nada_es_borrada_con_motivo() -> None:
    v = _uno(_linea(11, hmores_ide=4001))
    assert v.estado == "borrada"
    assert v.parte_existe is True
    assert v.hmores_ide == 4001 and v.hmoide == HMO and v.parte_cod == COD
    assert v.motivo == f"la linea 4001 del parte {COD} ya no existe en Sigrid"
    assert v.diferencias == []


def test_f024_r4_clasificar_cabecera_borrada() -> None:
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO), partes={})
    assert v.estado == "borrada"
    assert v.parte_existe is False
    assert v.parte_cod is None
    assert v.motivo == f"el parte {HMO} ya no existe en Sigrid"


def test_f024_r4_clasificar_sin_hmoide_no_afirma_que_falte_el_parte() -> None:
    v = _uno(_linea(11, hmores_ide=None, hmoide=None), partes={})
    assert v.estado == "borrada"
    assert v.parte_existe is True
    assert v.motivo == "la linea ? ya no existe en Sigrid"


def test_f024_r4_clasificar_parte_sin_codigo_usa_su_ide() -> None:
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO), partes={HMO: ""})
    assert v.parte_existe is True
    assert v.motivo == f"la linea 4001 del parte {HMO} ya no existe en Sigrid"


def test_f024_r6_clasificar_diferencias_de_recurso_fecha_y_horas() -> None:
    v = _uno(_linea(11, recurso=501, fecha=20260916, horas=8.0),
             synckey={"partes:11": _ls(4001, synckey="partes:11", reside=502,
                                       fecha=20260917, can=6.0)})
    assert v.estado == "presente"
    assert v.diferencias == [
        "recurso: portal 501, Sigrid 502",
        "fecha: portal 20260916, Sigrid 20260917",
        "horas: portal 8, Sigrid 6",
    ]


@pytest.mark.parametrize("can, hay", [
    (8.0, False), (8.004, False), (7.996, False), (8.006, True),
    (7.994, True), (None, True),
])
def test_f024_r6_clasificar_tolerancia_de_horas(can, hay) -> None:
    v = _uno(_linea(11, horas=8.0),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=can)})
    assert bool(v.diferencias) is hay


def test_f024_r6_clasificar_incidencia_no_compara_horas() -> None:
    """Las reglas ponen `can=0` a las incidencias."""
    v = _uno(_linea(11, horas=8.0, incidencia=True),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=0.0)})
    assert v.diferencias == []


def test_f024_r6_clasificar_sin_horas_en_el_portal_no_compara_horas() -> None:
    v = _uno(_linea(11, horas=None),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=3.0)})
    assert v.diferencias == []


def test_f024_r6_clasificar_sin_recurso_en_el_portal_no_compara_recurso() -> None:
    """sv5 resuelve el recurso por DNI si el portal no lo trae (F-023
    R37): eso no es una diferencia hecha a mano."""
    v = _uno(_linea(11, recurso=None),
             synckey={"partes:11": _ls(4001, synckey="partes:11", reside=777)})
    assert v.diferencias == []


def test_f024_r6_clasificar_respaldo_por_ide_tambien_compara_horas() -> None:
    v = _uno(_linea(11, horas=8.0), ide={4001: _ls(4001, can=4.5)})
    assert v.sin_synckey is True
    assert v.diferencias == ["horas: portal 8, Sigrid 4.5"]


def test_f024_r1_clasificar_un_veredicto_por_linea_y_en_orden() -> None:
    lineas = [_linea(3, hmores_ide=1), _linea(1, hmores_ide=2),
              _linea(2, hmores_ide=3)]
    out = clasificar(lineas, {"partes:1": _ls(2, synckey="partes:1")}, {},
                     {HMO: COD})
    assert [(v.registro_id, v.estado) for v in out] == [
        (3, "borrada"), (1, "presente"), (2, "borrada")]


# ===================================================================== #
# cliente · lineas_por_ide / partes_por_ide contra sigrid-api simulado
# (R7, R8). `httpx.post` se sustituye por un doble: ni una peticion real.
# ===================================================================== #

import httpx

from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
)


class SigridApiFalso:
    """sigrid-api en memoria: cada lectura devuelve la siguiente lista de
    filas de `respuestas` y apunta la URL y el cuerpo pedidos."""

    def __init__(self, columnas, *respuestas, truncated=False,
                 status=200, ok=True) -> None:
        self.columnas = columnas
        self.respuestas = list(respuestas)
        self.truncated = truncated
        self.status = status
        self.ok = ok
        self.urls: list[str] = []
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.urls.append(url)
        self.lecturas.append(json)
        filas = self.respuestas.pop(0) if self.respuestas else []
        return httpx.Response(self.status, json={
            "ok": self.ok, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso) -> SigridWriteClient:
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


COLS_HMORES = ["ide", "hmoide", "reside", "fec", "horide", "can", "tot",
               "synckey"]


def test_f024_r7_cliente_lineas_por_ide_en_lotes_de_200(monkeypatch) -> None:
    falso = SigridApiFalso(
        COLS_HMORES,
        [[1, HMO, 501, 20260916, 3, 8.0, 80.0, ""]],
        [[201, HMO_OTRO, 502, 20260917, None, None, None, "partes:9"]])
    out = _cliente(monkeypatch, falso).lineas_por_ide(range(1, 202))
    assert [len(l["parameters"]) for l in falso.lecturas] == [200, 1]
    assert falso.lecturas[1]["parameters"] == [201]
    assert all(l["max_rows"] == 1000 for l in falso.lecturas)
    assert all(u.endswith("/api/sql/read") for u in falso.urls)
    assert _sql(falso.lecturas[0]["sql"]) == (
        "SELECT ide, hmoide, reside, fec, horide, can, tot, synckey "
        "FROM hmores WHERE ide IN (" + ",".join("?" * 200) + ")")
    uno, otro = out[1], out[201]
    assert (uno.ide, uno.hmoide, uno.reside, uno.fecha_int, uno.horide,
            uno.can, uno.tot, uno.synckey, uno.nuestra) == (
        1, HMO, 501, 20260916, 3, 8.0, 80.0, None, False)
    assert (otro.hmoide, otro.horide, otro.synckey, otro.nuestra) == (
        HMO_OTRO, None, "partes:9", True)
    assert sorted(out) == [1, 201]


def test_f024_r7_cliente_lineas_por_ide_deduplica_y_no_lee_sin_ides(
        monkeypatch) -> None:
    falso = SigridApiFalso(COLS_HMORES)
    cli = _cliente(monkeypatch, falso)
    assert cli.lineas_por_ide([]) == {}
    assert cli.lineas_por_ide([None, 0]) == {}
    assert falso.lecturas == []
    cli.lineas_por_ide([5, 5, 3])
    assert falso.lecturas[0]["parameters"] == [3, 5]


def test_f024_r7_cliente_partes_por_ide_en_lotes_de_200(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod"], [[1, COD]], [[201, COD_OTRO]])
    out = _cliente(monkeypatch, falso).partes_por_ide(range(1, 202))
    assert out == {1: COD, 201: COD_OTRO}
    assert [len(l["parameters"]) for l in falso.lecturas] == [200, 1]
    assert all(l["max_rows"] == 1000 for l in falso.lecturas)
    assert _sql(falso.lecturas[1]["sql"]) == (
        "SELECT hmo.ide AS ide, con.cod AS cod FROM hmo "
        "JOIN con ON con.ide = hmo.ide WHERE hmo.ide IN (?)")


def test_f024_r7_cliente_partes_por_ide_sin_ides_no_lee(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod"])
    assert _cliente(monkeypatch, falso).partes_por_ide([None]) == {}
    assert falso.lecturas == []


@pytest.mark.parametrize("metodo", ["lineas_por_ide", "partes_por_ide"])
def test_f024_r8_cliente_truncated_es_una_excepcion(monkeypatch, metodo) -> None:
    falso = SigridApiFalso(COLS_HMORES, [[1, HMO, 501, 20260916, 1, 8, 8, ""]],
                           truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)([1])


@pytest.mark.parametrize("metodo", ["lineas_por_ide", "partes_por_ide"])
def test_f024_r8_cliente_error_http_es_una_excepcion(monkeypatch, metodo) -> None:
    falso = SigridApiFalso(["ide"], status=500)
    with pytest.raises(RuntimeError):
        getattr(_cliente(monkeypatch, falso), metodo)([1])



# ===================================================================== #
# ComprobadorLineas y endpoint `POST /api/registro/comprobar` (R1, R8, R9)
# ===================================================================== #

import threading

from fastapi.testclient import TestClient

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.comprobacion_lineas import (
    ComprobadorLineas,
)
from interface_adapters.api.app import build_app
from tests.dobles import SettingsFake


class ClienteFalso:
    """Cliente de Sigrid en memoria que apunta cada lectura y revienta si
    alguien intenta escribir."""

    def __init__(self, *, por_synckey=None, por_ide=None, partes=None,
                 fallo: str | None = None) -> None:
        self.por_synckey = por_synckey or {}
        self.por_ide = por_ide or {}
        self.partes = partes if partes is not None else {HMO: COD}
        self.fallo = fallo
        self.llamadas: list[tuple[str, list]] = []

    def _anotar(self, nombre, valores):
        self.llamadas.append((nombre, list(valores)))
        if self.fallo == nombre:
            raise RuntimeError(f"sigrid-api caida en {nombre}")

    def lineas_por_synckey(self, claves):
        self._anotar("lineas_por_synckey", claves)
        return {k: v for k, v in self.por_synckey.items() if k in claves}

    def lineas_por_ide(self, ides):
        self._anotar("lineas_por_ide", ides)
        return {k: v for k, v in self.por_ide.items() if k in ides}

    def partes_por_ide(self, hmoides):
        self._anotar("partes_por_ide", hmoides)
        return {k: v for k, v in self.partes.items() if k in hmoides}

    def escribir(self, statements):   # pragma: no cover - no debe llamarse
        self.llamadas.append(("escribir", statements))
        raise AssertionError("la comprobacion no puede escribir")


def test_f024_r1_comprobador_deduplica_por_registro_id() -> None:
    cli = ClienteFalso(por_synckey={"partes:1": _ls(4001, synckey="partes:1")})
    out = ComprobadorLineas(cliente=cli).comprobar(
        [_linea(1), _linea(1, hmores_ide=9), _linea(2, hmores_ide=4002)])
    assert [(v.registro_id, v.estado) for v in out] == [
        (1, "presente"), (2, "borrada")]
    assert cli.llamadas[0] == ("lineas_por_synckey", ["partes:1", "partes:2"])


def test_f024_r3_comprobador_lee_por_ide_solo_los_fallos() -> None:
    cli = ClienteFalso(
        por_synckey={"partes:1": _ls(4001, synckey="partes:1")},
        por_ide={4002: _ls(4002, hmoide=HMO_OTRO)},
        partes={HMO: COD, HMO_OTRO: COD_OTRO})
    out = ComprobadorLineas(cliente=cli).comprobar(
        [_linea(1, hmores_ide=4001), _linea(2, hmores_ide=4002, hmoide=None),
         _linea(3, hmores_ide=None, hmoide=7777)])
    nombres = [n for n, _ in cli.llamadas]
    assert nombres == ["lineas_por_synckey", "lineas_por_ide",
                       "partes_por_ide"]
    assert cli.llamadas[1] == ("lineas_por_ide", [4002])
    assert sorted(cli.llamadas[2][1]) == [HMO, HMO_OTRO, 7777]
    assert [(v.estado, v.sin_synckey, v.parte_cod) for v in out] == [
        ("presente", False, COD), ("presente", True, COD_OTRO),
        ("borrada", False, None)]
    assert out[2].parte_existe is False


def test_f024_r3_comprobador_sin_fallos_no_lee_por_ide() -> None:
    cli = ClienteFalso(por_synckey={"partes:1": _ls(4001, synckey="partes:1")})
    ComprobadorLineas(cliente=cli).comprobar([_linea(1)])
    assert [n for n, _ in cli.llamadas] == ["lineas_por_synckey",
                                            "partes_por_ide"]


def test_f024_r4_comprobador_sin_partes_que_mirar_no_lee_partes() -> None:
    cli = ClienteFalso()
    out = ComprobadorLineas(cliente=cli).comprobar(
        [_linea(1, hmores_ide=None, hmoide=None)])
    assert [n for n, _ in cli.llamadas] == ["lineas_por_synckey"]
    assert out[0].estado == "borrada"


@pytest.mark.parametrize("donde", ["lineas_por_synckey", "lineas_por_ide",
                                   "partes_por_ide"])
def test_f024_r8_comprobador_una_lectura_fallida_sube(donde) -> None:
    cli = ClienteFalso(fallo=donde)
    with pytest.raises(RuntimeError, match="caida"):
        ComprobadorLineas(cliente=cli).comprobar([_linea(1)])


# ------------------------------- endpoint ------------------------------- #

def _app(cli: ClienteFalso, *, lock: threading.Lock | None = None):
    pipeline = RegistroPipeline(cliente=cli, settings=SettingsFake(),
                                lock=lock)
    return build_app(SettingsFake(), pipeline=pipeline,
                     comprobador=ComprobadorLineas(cliente=cli))


def _cuerpo(*lineas: dict) -> dict:
    return {"lineas": list(lineas)}


LINEA_JSON = {"registro_id": 1, "hmores_ide": 4001, "hmoide": HMO,
              "recurso_ide": 501, "fecha_int": 20260916, "horas": 8.0,
              "es_incidencia": False}


def test_f024_r1_endpoint_un_veredicto_por_registro_id() -> None:
    cli = ClienteFalso(por_synckey={"partes:1": _ls(4001, synckey="partes:1")})
    r = TestClient(_app(cli)).post("/api/registro/comprobar", json=_cuerpo(
        LINEA_JSON, dict(LINEA_JSON), dict(LINEA_JSON, registro_id=2,
                                           hmores_ide=4002)))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert [v["registro_id"] for v in cuerpo["veredictos"]] == [1, 2]
    assert cuerpo["veredictos"][0] == {
        "registro_id": 1, "estado": "presente", "hmores_ide": 4001,
        "hmoide": HMO, "parte_cod": COD, "parte_existe": True,
        "sin_synckey": False, "diferencias": [], "motivo": None}
    assert cuerpo["veredictos"][1]["estado"] == "borrada"
    assert all(n != "escribir" for n, _ in cli.llamadas)


def test_f024_r1_endpoint_solo_registro_id_es_obligatorio() -> None:
    cli = ClienteFalso()
    r = TestClient(_app(cli)).post("/api/registro/comprobar",
                                   json=_cuerpo({"registro_id": 5}))
    assert r.status_code == 200
    assert r.json()["veredictos"][0]["estado"] == "borrada"


def test_f024_r1_endpoint_no_toma_el_lock_de_escritura() -> None:
    """Con el lock tomado por otro hilo (una escritura en curso), la
    comprobacion responde igual: no espera a nadie."""
    lock = threading.Lock()
    cli = ClienteFalso()
    cliente_http = TestClient(_app(cli, lock=lock))
    respuesta: dict = {}

    def _pedir():
        respuesta["r"] = cliente_http.post("/api/registro/comprobar",
                                           json=_cuerpo(LINEA_JSON))

    assert lock.acquire(timeout=1)
    try:
        hilo = threading.Thread(target=_pedir, daemon=True)
        hilo.start()
        hilo.join(timeout=10)
        assert not hilo.is_alive(), "la comprobacion espero al lock"
    finally:
        lock.release()
    assert respuesta["r"].status_code == 200


def test_f024_r1_endpoint_admite_500_lineas() -> None:
    cli = ClienteFalso()
    lineas = [dict(LINEA_JSON, registro_id=i) for i in range(1, 501)]
    r = TestClient(_app(cli)).post("/api/registro/comprobar",
                                   json=_cuerpo(*lineas))
    assert r.status_code == 200
    assert len(r.json()["veredictos"]) == 500


@pytest.mark.parametrize("cuerpo", [
    pytest.param({"lineas": []}, id="cero-lineas"),
    pytest.param({"lineas": [dict(LINEA_JSON, registro_id=i)
                             for i in range(1, 502)]}, id="501-lineas"),
    pytest.param({}, id="sin-lineas"),
    pytest.param({"lineas": [{"hmores_ide": 3}]}, id="sin-registro-id"),
    pytest.param({"lineas": [{"registro_id": "x"}]}, id="id-no-numerico"),
])
def test_f024_r9_endpoint_cuerpo_invalido_es_422_sin_leer(cuerpo) -> None:
    cli = ClienteFalso()
    r = TestClient(_app(cli)).post("/api/registro/comprobar", json=cuerpo)
    assert r.status_code == 422
    assert cli.llamadas == []


def test_f024_r8_endpoint_lectura_fallida_es_502_sin_veredictos() -> None:
    cli = ClienteFalso(fallo="lineas_por_ide")
    r = TestClient(_app(cli)).post("/api/registro/comprobar",
                                   json=_cuerpo(LINEA_JSON))
    assert r.status_code == 502
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert "caida" in cuerpo["error"]
    assert "veredictos" not in cuerpo


def test_f024_r8_endpoint_truncated_es_502(monkeypatch) -> None:
    """De punta a punta: sigrid-api devuelve `truncated` y el endpoint no
    da ningun veredicto."""
    falso = SigridApiFalso(["ide"], [], truncated=True)
    cli_real = _cliente(monkeypatch, falso)
    app = build_app(SettingsFake(),
                    pipeline=RegistroPipeline(cliente=cli_real,
                                              settings=SettingsFake()),
                    comprobador=ComprobadorLineas(cliente=cli_real))
    r = TestClient(app).post("/api/registro/comprobar",
                             json=_cuerpo(LINEA_JSON))
    assert r.status_code == 502
    assert "veredictos" not in r.json()
    assert all(u.endswith("/api/sql/read") for u in falso.urls)


def _settings_con_sigrid() -> SettingsFake:
    st = SettingsFake()
    st.sigrid_api_base_url = "http://sigrid.invalid"
    st.sigrid_api_function_key = "clave-de-test"
    st.sigrid_api_database = "bd"
    st.sigrid_api_timeout_s = 5
    st.sigrid_max_statements = 15
    st.tip_parte_trabajo = 35
    st.est_parte_activo = 1
    return st


@pytest.mark.parametrize("con_pipeline", [True, False])
def test_f024_r1_endpoint_sin_comprobador_inyectado_usa_el_cliente_de_sigrid(
        monkeypatch, con_pipeline) -> None:
    """Sin `comprobador`, la app lo construye sobre un SigridWriteClient
    (el suyo o, con pipeline de fuera, uno nuevo en la primera peticion)
    y solo lee."""
    falso = SigridApiFalso(["ide"])
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    st = _settings_con_sigrid()
    pipeline = (RegistroPipeline(cliente=ClienteFalso(), settings=st)
                if con_pipeline else None)
    cliente_http = TestClient(build_app(st, pipeline=pipeline))
    for _ in range(2):
        r = cliente_http.post("/api/registro/comprobar",
                              json=_cuerpo(LINEA_JSON))
        assert r.status_code == 200
        assert r.json()["veredictos"][0]["estado"] == "borrada"
    assert falso.urls and all(u == "http://sigrid.invalid/api/sql/read"
                              for u in falso.urls)
    assert falso.lecturas[0]["database"] == "bd"



# ===================================================================== #
# T17 · supervivientes de la campana de mutacion (progress/mutacion_F-024.md)
# ===================================================================== #

import logging


def test_f024_r21_comprobador_log_con_los_recuentos(caplog) -> None:
    """Mutantes 94, 118, 128, 144, 163 y 168: la linea `[comprobar]`
    cuenta bien cada clase de veredicto (es lo que M3 lee en Log
    Analytics)."""
    cli = ClienteFalso(
        por_synckey={"partes:1": _ls(4001, synckey="partes:1", can=6.0)},
        por_ide={4002: _ls(4002)})
    with caplog.at_level(logging.INFO):
        ComprobadorLineas(cliente=cli).comprobar(
            [_linea(1, hmores_ide=4001), _linea(2, hmores_ide=4002),
             _linea(3, hmores_ide=4003), _linea(4, hmores_ide=4004),
             _linea(5, hmores_ide=4005)])
    lineas = [r.getMessage() for r in caplog.records
              if r.getMessage().startswith("[comprobar]")]
    assert lineas == [("[comprobar] lineas=5 presentes=2 borradas=3 "
                       "sin_synckey=1 con_diferencias=1")]


def test_f024_r6_clasificar_tolerancia_justo_en_el_limite() -> None:
    """Mutante 110: una diferencia de exactamente 0,005 no se avisa."""
    v = _uno(_linea(11, horas=0.0),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=0.005)})
    assert v.diferencias == []


def test_f024_r6_clasificar_por_defecto_no_es_incidencia() -> None:
    """Mutante 136: sin `es_incidencia`, las horas se comparan."""
    linea = LineaComprobar(registro_id=11, recurso_ide=501,
                           fecha_int=20260916, horas=8.0)
    assert linea.es_incidencia is False
    v = _uno(linea, synckey={"partes:11": _ls(4001, synckey="partes:11",
                                              can=6.0)})
    assert v.diferencias == ["horas: portal 8, Sigrid 6"]


def test_f024_r6_endpoint_por_defecto_no_es_incidencia() -> None:
    """Mutante 171: el esquema del endpoint tambien asume `False`."""
    cli = ClienteFalso(por_synckey={"partes:1": _ls(4001, synckey="partes:1",
                                                    can=6.0)})
    linea = {k: v for k, v in LINEA_JSON.items() if k != "es_incidencia"}
    r = TestClient(_app(cli)).post("/api/registro/comprobar",
                                   json=_cuerpo(linea))
    assert r.json()["veredictos"][0]["diferencias"] == [
        "horas: portal 8, Sigrid 6"]


def test_f024_r7_cliente_lineas_por_ide_nulos_a_cero(monkeypatch) -> None:
    """Mutantes 130, 131 y 167: los NULL de Sigrid se leen como 0."""
    falso = SigridApiFalso(COLS_HMORES,
                           [[7, None, None, None, None, None, None, None]])
    fila = _cliente(monkeypatch, falso).lineas_por_ide([7])[7]
    assert (fila.hmoide, fila.reside, fila.fecha_int, fila.horide,
            fila.synckey) == (0, 0, 0, None, None)


def test_f024_r1_endpoint_respeta_el_comprobador_inyectado_sin_pipeline(
        monkeypatch) -> None:
    """Mutante 132: con `pipeline=None` y comprobador inyectado, la app no
    lo sustituye por uno propio."""
    falso = SigridApiFalso(["ide"])
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    cli = ClienteFalso(por_synckey={"partes:1": _ls(4001, synckey="partes:1")})
    app = build_app(_settings_con_sigrid(),
                    comprobador=ComprobadorLineas(cliente=cli))
    r = TestClient(app).post("/api/registro/comprobar",
                             json=_cuerpo(LINEA_JSON))
    assert r.json()["veredictos"][0]["estado"] == "presente"
    assert falso.urls == []
