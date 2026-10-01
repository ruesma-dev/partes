# tests/test_f024_comprobar_y_estado.py
"""F-024 · comprobacion en Sigrid desde el portal y sondeo del encolado.

R17-R21 (antimartilleo, servicio y endpoint de comprobacion), R26-R28 y
R30. Sin red ni PostgreSQL ni `sleep`: reloj inyectado, SQLite en memoria
y un doble del cliente de sv5.
"""
from __future__ import annotations

import threading

import pytest
from application.services.comprobacion_sigrid import RegistroComprobaciones


class Reloj:
    """Reloj monotono controlado por el test."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


# ===================================================================== #
# T8 · RegistroComprobaciones (R19)
# ===================================================================== #

def test_f024_r19_recientes_dentro_del_ttl_no_repite() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    assert reg.reservar([3, 1, 2], forzar=False) == [3, 1, 2]
    reloj.t += 119.9
    assert reg.reservar([1, 2, 4], forzar=False) == [4]


def test_f024_r19_recientes_pasado_el_ttl_vuelve_a_comprobar() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1], forzar=False)
    reloj.t += 120
    assert reg.reservar([1], forzar=False) == [1]


def test_f024_r19_recientes_forzar_lo_salta_y_vuelve_a_sellar() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1, 2], forzar=False)
    reloj.t += 100
    assert reg.reservar([1, 2], forzar=True) == [1, 2]
    reloj.t += 100      # 200 s desde el primer sello, 100 desde el forzado
    assert reg.reservar([1, 2], forzar=False) == []


def test_f024_r19_recientes_sella_al_reservar_aunque_el_lote_falle() -> None:
    """Un id en curso, o cuyo lote fallo, no se reenvia en cada recarga."""
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1, 2], forzar=False)
    # ...el lote falla (nadie avisa al registro)...
    assert reg.reservar([1, 2], forzar=False) == []


def test_f024_r19_recientes_deduplica_la_entrada() -> None:
    reg = RegistroComprobaciones(ttl_s=120, reloj=Reloj())
    assert reg.reservar([5, 5, 6, 5], forzar=False) == [5, 6]
    assert reg.reservar([7, 7], forzar=True) == [7]


def test_f024_r19_recientes_purga_las_caducadas() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar(list(range(100)), forzar=False)
    reloj.t += 121
    reg.reservar([500], forzar=False)
    assert reg.vigentes() == 1


def test_f024_r19_recientes_ttl_cero_no_retiene_nada() -> None:
    reg = RegistroComprobaciones(ttl_s=0, reloj=Reloj())
    assert reg.reservar([1], forzar=False) == [1]
    assert reg.reservar([1], forzar=False) == [1]


def test_f024_r19_recientes_seguro_con_dos_hilos() -> None:
    """Dos vistas de la misma obra a la vez: cada id va a sv5 una vez."""
    reg = RegistroComprobaciones(ttl_s=120, reloj=Reloj())
    ids = list(range(2000))
    barrera = threading.Barrier(2)
    resultados: list[list[int]] = []

    def _reservar() -> None:
        barrera.wait()
        resultados.append(reg.reservar(ids, forzar=False))

    hilos = [threading.Thread(target=_reservar) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=10)
    assert len(resultados) == 2
    assert sorted(resultados[0] + resultados[1]) == ids


def test_f024_r19_recientes_usa_reloj_monotono_por_defecto() -> None:
    import time
    reg = RegistroComprobaciones(ttl_s=120)
    assert reg._reloj is time.monotonic



# ===================================================================== #
# T9 · ComprobacionSigrid (R14, R17, R21), TransferClient.comprobar y
# variables COMPROBACION_SIGRID_*
# ===================================================================== #

import logging
from datetime import datetime, timezone

import httpx
from application.services.comprobacion_sigrid import ComprobacionSigrid
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer import transfer_client as modulo_tc
from infrastructure.transfer.transfer_client import TransferClient
from tests.dobles import FabricaSesionSqlite, sembrar_parte

PARTE = "PT26/09001"
HMO = 7001
INSTANTE = datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc)


class Sv5Falso:
    """Doble de `TransferClient` para la comprobacion.

    `borradas` son los registro_id que sv5 da por borrados; el resto,
    presentes con las mismas referencias. `fallos` es la lista de
    respuestas forzadas por llamada (None = respuesta normal)."""

    def __init__(self, *, borradas=(), fallos=None, quitar=(),
                 extra: dict | None = None) -> None:
        self.borradas = set(borradas)
        self.fallos = list(fallos or [])
        self.quitar = set(quitar)
        self.extra = extra or {}
        self.llamadas: list[tuple[dict, float]] = []

    def comprobar(self, payload: dict, *, timeout_s: float) -> dict:
        self.llamadas.append((payload, timeout_s))
        forzada = self.fallos.pop(0) if self.fallos else None
        if isinstance(forzada, Exception):
            raise forzada
        if forzada is not None:
            return forzada
        out = []
        for l in payload["lineas"]:
            rid = l["registro_id"]
            if rid in self.quitar:
                continue
            v = {"registro_id": rid, "hmores_ide": l["hmores_ide"],
                 "hmoide": l["hmoide"], "parte_cod": PARTE,
                 "parte_existe": True, "sin_synckey": False,
                 "diferencias": [], "motivo": None,
                 "estado": "borrada" if rid in self.borradas else "presente"}
            v.update(self.extra.get(rid, {}))
            out.append(v)
        return {"ok": True, "veredictos": out}


def _sembrar(estados: list[str | None]):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"estado": e} for e in estados])
    with fabrica.create_session() as s:
        for i, rid in enumerate(ids):
            reg = s.get(ParteRegistroOrm, rid)
            reg.sigrid_hmoide = HMO if reg.sigrid_estado == "registrado" else None
            reg.sigrid_parte_cod = PARTE if reg.sigrid_estado == "registrado" \
                else None
        s.commit()
    return fabrica, ParteReviewRepository(fabrica), ids


def _servicio(repo, sv5, *, lote=500, ttl=120, reloj=None):
    return ComprobacionSigrid(
        repository=repo, transfer_client=sv5, lote=lote, timeout_s=30,
        recientes=RegistroComprobaciones(ttl_s=ttl, reloj=reloj or Reloj()),
        reloj_utc=lambda: INSTANTE)


def _estado(fabrica, rid):
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid).sigrid_estado


def test_f024_r17_servicio_aplica_las_borradas() -> None:
    fabrica, repo, ids = _sembrar(["registrado"] * 3)
    sv5 = Sv5Falso(borradas={ids[1]})
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="vista-obra")
    assert out == {"ok": True, "comprobadas": 3, "recientes": 0,
                   "borradas": 1, "borradas_ids": [ids[1]],
                   "actualizadas": 0, "sin_synckey": 0,
                   "con_diferencias": [], "fallidos": 0}
    assert [_estado(fabrica, i) for i in ids] == [
        "registrado", "borrado_sigrid", "registrado"]
    with fabrica.create_session() as s:
        assert "2026-10-01 09:30 UTC" in s.get(ParteRegistroOrm,
                                               ids[1]).sigrid_motivo


def test_f024_r17_servicio_solo_envia_las_registrado() -> None:
    _f, repo, ids = _sembrar(["registrado", None, "borrado_sigrid",
                              "encolado", "omitido"])
    sv5 = Sv5Falso()
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="boton")
    assert [l["registro_id"] for l in sv5.llamadas[0][0]["lineas"]] == [ids[0]]
    assert out["comprobadas"] == 1
    assert sv5.llamadas[0][0]["lineas"][0] == {
        "registro_id": ids[0], "hmores_ide": 9000, "hmoide": HMO,
        "recurso_ide": 501, "fecha_int": 20260302, "horas": 8.0,
        "es_incidencia": False}


def test_f024_r17_servicio_sin_registrado_no_llama_a_sv5() -> None:
    _f, repo, ids = _sembrar([None, "omitido"])
    sv5 = Sv5Falso()
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="vista-obra")
    assert sv5.llamadas == []
    assert out["ok"] is True and out["comprobadas"] == 0


def test_f024_r17_servicio_lotes_y_timeout() -> None:
    _f, repo, ids = _sembrar(["registrado"] * 5)
    sv5 = Sv5Falso()
    out = _servicio(repo, sv5, lote=2).comprobar_ids(ids, origen="boton")
    assert [len(p["lineas"]) for p, _ in sv5.llamadas] == [2, 2, 1]
    assert {t for _, t in sv5.llamadas} == {30}
    assert out["comprobadas"] == 5


@pytest.mark.parametrize("fallo", [
    pytest.param({"ok": False, "error": "HTTP 502"}, id="ok-false"),
    pytest.param(RuntimeError("sv5 caido"), id="excepcion"),
    pytest.param({"ok": True}, id="sin-veredictos"),
])
def test_f024_r14_servicio_lote_fallido_no_aplica_y_para(fallo) -> None:
    fabrica, repo, ids = _sembrar(["registrado"] * 5)
    sv5 = Sv5Falso(borradas=set(ids), fallos=[None, fallo])
    out = _servicio(repo, sv5, lote=2).comprobar_ids(ids, origen="boton")
    assert len(sv5.llamadas) == 2           # el tercer lote no se envia
    assert out["ok"] is False
    assert out["comprobadas"] == 2 and out["fallidos"] == 3
    assert out["borradas_ids"] == ids[:2]
    assert out["error"]
    assert [_estado(fabrica, i) for i in ids] == (
        ["borrado_sigrid"] * 2 + ["registrado"] * 3)


def test_f024_r14_servicio_veredicto_ausente_no_aplica_el_lote() -> None:
    fabrica, repo, ids = _sembrar(["registrado"] * 3)
    sv5 = Sv5Falso(borradas=set(ids), quitar={ids[2]})
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="boton")
    assert out["ok"] is False and out["fallidos"] == 3
    assert out["borradas"] == 0
    assert "veredicto" in out["error"]
    assert {_estado(fabrica, i) for i in ids} == {"registrado"}


def test_f024_r19_servicio_recientes_no_vuelven_a_sv5() -> None:
    reloj = Reloj()
    _f, repo, ids = _sembrar(["registrado"] * 2)
    sv5 = Sv5Falso(fallos=[{"ok": False, "error": "caido"}])
    servicio = _servicio(repo, sv5, reloj=reloj)
    servicio.comprobar_ids(ids, origen="vista-obra")       # falla
    out = servicio.comprobar_ids(ids, origen="vista-trabajador")
    assert len(sv5.llamadas) == 1
    assert (out["ok"], out["comprobadas"], out["recientes"]) == (True, 0, 2)
    out = servicio.comprobar_ids(ids, origen="boton", forzar=True)
    assert len(sv5.llamadas) == 2 and out["comprobadas"] == 2


def test_f024_r17_servicio_cuenta_sin_synckey_diferencias_y_actualizadas() -> None:
    _f, repo, ids = _sembrar(["registrado"] * 3)
    sv5 = Sv5Falso(extra={
        ids[0]: {"sin_synckey": True},
        ids[1]: {"diferencias": ["horas: portal 8, Sigrid 6"]},
        ids[2]: {"hmores_ide": 4999}})
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="boton")
    assert out["sin_synckey"] == 1
    assert out["con_diferencias"] == [
        {"registro_id": ids[1], "diferencias": ["horas: portal 8, Sigrid 6"]}]
    assert out["actualizadas"] == 1


def test_f024_r21_servicio_deja_log_con_origen_y_recuentos(caplog) -> None:
    _f, repo, ids = _sembrar(["registrado"] * 2)
    with caplog.at_level(logging.INFO):
        _servicio(repo, Sv5Falso(borradas={ids[0]})).comprobar_ids(
            ids + [999999], origen="vista-trabajador")
    lineas = [r.getMessage() for r in caplog.records
              if "[comprobacion-sigrid]" in r.getMessage()]
    assert len(lineas) == 1
    for trozo in ("origen=vista-trabajador", "forzar=False", "pedidas=3",
                  "registrado=2", "recientes=0", "comprobadas=2",
                  "borradas=1", "actualizadas=0", "fallidos=0", "ok=True"):
        assert trozo in lineas[0], trozo


def test_f024_r17_servicio_reloj_utc_por_defecto() -> None:
    servicio = ComprobacionSigrid(
        repository=None, transfer_client=None, lote=1, timeout_s=1,
        recientes=RegistroComprobaciones(ttl_s=1))
    assert servicio._reloj_utc().tzinfo is timezone.utc


# ---------------------- TransferClient.comprobar ------------------------ #

class HttpxFalso:
    def __init__(self, respuesta=None, excepcion=None) -> None:
        self.respuesta = respuesta
        self.excepcion = excepcion
        self.llamadas: list[dict] = []

    def __call__(self, url, json=None, timeout=None):
        self.llamadas.append({"url": url, "json": json, "timeout": timeout})
        if self.excepcion is not None:
            raise self.excepcion
        return self.respuesta


def test_f024_r17_servicio_cliente_comprobar_usa_su_timeout(monkeypatch) -> None:
    falso = HttpxFalso(httpx.Response(200, json={"ok": True,
                                                 "veredictos": []}))
    monkeypatch.setattr(modulo_tc.httpx, "post", falso)
    cli = TransferClient(base_url="http://sv5.interno/", timeout_s=120)
    assert cli.comprobar({"lineas": []}, timeout_s=30) == {
        "ok": True, "veredictos": []}
    assert falso.llamadas == [{"url": "http://sv5.interno/api/registro/comprobar",
                               "json": {"lineas": []}, "timeout": 30.0}]
    cli.preflight({"x": 1})
    assert falso.llamadas[1]["timeout"] == 120.0      # el resto, intacto


def test_f024_r17_servicio_cliente_timeout_dice_su_plazo(monkeypatch) -> None:
    falso = HttpxFalso(excepcion=httpx.ReadTimeout("lento"))
    monkeypatch.setattr(modulo_tc.httpx, "post", falso)
    r = TransferClient(base_url="http://sv5.interno").comprobar(
        {"lineas": []}, timeout_s=30)
    assert r["ok"] is False
    assert "30s" in r["error"]


def test_f024_r17_servicio_cliente_404_de_sv5_viejo_es_ok_false(
        monkeypatch) -> None:
    """DA11: sv4 nuevo contra sv5 sin el endpoint -> nada cambia."""
    falso = HttpxFalso(httpx.Response(404, json={"detail": "Not Found"}))
    monkeypatch.setattr(modulo_tc.httpx, "post", falso)
    r = TransferClient(base_url="http://sv5.interno").comprobar(
        {"lineas": []}, timeout_s=30)
    assert r == {"ok": False, "error": "HTTP 404"}


# ------------------------------ Settings -------------------------------- #

from config.settings import Settings
from pydantic import ValidationError


@pytest.fixture
def entorno_pg(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    for clave in ("COMPROBACION_SIGRID_TTL_S", "COMPROBACION_SIGRID_TIMEOUT_S",
                  "COMPROBACION_SIGRID_LOTE"):
        monkeypatch.delenv(clave, raising=False)
    return monkeypatch


def test_f024_r17_servicio_settings_por_defecto(entorno_pg) -> None:
    st = Settings(_env_file=None)
    assert (st.comprobacion_sigrid_ttl_s, st.comprobacion_sigrid_timeout_s,
            st.comprobacion_sigrid_lote) == (120, 30.0, 500)


def test_f024_r17_servicio_settings_desde_el_entorno(entorno_pg) -> None:
    entorno_pg.setenv("COMPROBACION_SIGRID_TTL_S", "0")
    entorno_pg.setenv("COMPROBACION_SIGRID_TIMEOUT_S", "12.5")
    entorno_pg.setenv("COMPROBACION_SIGRID_LOTE", "1")
    st = Settings(_env_file=None)
    assert (st.comprobacion_sigrid_ttl_s, st.comprobacion_sigrid_timeout_s,
            st.comprobacion_sigrid_lote) == (0, 12.5, 1)


@pytest.mark.parametrize("clave, valor", [
    ("COMPROBACION_SIGRID_TTL_S", "-1"),
    ("COMPROBACION_SIGRID_TIMEOUT_S", "0"),
    ("COMPROBACION_SIGRID_LOTE", "0"),
    ("COMPROBACION_SIGRID_LOTE", "501"),
])
def test_f024_r17_servicio_settings_fuera_de_rango(entorno_pg, clave,
                                                   valor) -> None:
    entorno_pg.setenv(clave, valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f024_r17_servicio_settings_limites_validos(entorno_pg) -> None:
    entorno_pg.setenv("COMPROBACION_SIGRID_LOTE", "500")
    assert Settings(_env_file=None).comprobacion_sigrid_lote == 500


def test_f024_r14_servicio_veredicto_malformado_cuenta_como_ausente() -> None:
    fabrica, repo, ids = _sembrar(["registrado"])
    sv5 = Sv5Falso(fallos=[{"ok": True, "veredictos": [
        {"estado": "borrada"}, "basura", {"registro_id": None}]}])
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="boton")
    assert out["ok"] is False and out["fallidos"] == 1
    assert _estado(fabrica, ids[0]) == "registrado"


def test_f024_r14_servicio_ok_false_sin_texto_tiene_error() -> None:
    _f, repo, ids = _sembrar(["registrado"])
    out = _servicio(repo, Sv5Falso(fallos=[{"ok": False}])).comprobar_ids(
        ids, origen="boton")
    assert out["error"] == "sv5 no respondio ok"



# ===================================================================== #
# T11 · endpoints POST /api/sigrid/comprobar (R17, R18, R21) y
# POST /api/aprobar/estado (R28)
# ===================================================================== #

from fastapi.testclient import TestClient
from interface_adapters.web.app import build_app


class Sv5Portal(Sv5Falso):
    """Doble completo de sv5 para levantar el portal: la comprobacion y
    contadores de lo demas (que estos tests no deben disparar)."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.otras: list[str] = []

    def preflight(self, payload):  # pragma: no cover - no debe llamarse
        self.otras.append("preflight")
        return {"ok": True}

    def ejecutar(self, payload):   # pragma: no cover - no debe llamarse
        self.otras.append("ejecutar")
        return {"ok": True}


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana"}.items():
        monkeypatch.setenv(clave, valor)
    for clave in ("TRANSFER_BASE_URL", "COMPROBACION_SIGRID_TTL_S",
                  "COMPROBACION_SIGRID_LOTE", "COMPROBACION_SIGRID_TIMEOUT_S"):
        monkeypatch.delenv(clave, raising=False)

    def _levantar(estados, *, sv5=None, con_sv5=True, entorno=None):
        for clave, valor in (entorno or {}).items():
            monkeypatch.setenv(clave, valor)
        fabrica, repo, ids = _sembrar(estados)
        sv5 = sv5 or (Sv5Portal() if con_sv5 else None)
        app = build_app(Settings(_env_file=None), repository=repo,
                        transfer_client=sv5)
        return TestClient(app), fabrica, ids, sv5
    return _levantar


def test_f024_r17_endpoint_comprobar_aplica_y_responde(portal) -> None:
    sv5 = Sv5Portal()
    cliente, fabrica, ids, _ = portal(["registrado", "registrado", None],
                                      sv5=sv5)
    sv5.borradas = {ids[0]}
    r = cliente.post("/api/sigrid/comprobar",
                     json={"registro_ids": ids, "origen": "vista-obra"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo == {"ok": True, "comprobadas": 2, "recientes": 0,
                      "borradas": 1, "borradas_ids": [ids[0]],
                      "actualizadas": 0, "sin_synckey": 0,
                      "con_diferencias": [], "fallidos": 0}
    assert _estado(fabrica, ids[0]) == "borrado_sigrid"
    assert [l["registro_id"] for l in sv5.llamadas[0][0]["lineas"]] == ids[:2]
    assert sv5.otras == []


def test_f024_r17_endpoint_usa_las_variables_de_entorno(portal) -> None:
    cliente, _f, ids, sv5 = portal(
        ["registrado"] * 3, entorno={"COMPROBACION_SIGRID_LOTE": "2",
                                     "COMPROBACION_SIGRID_TIMEOUT_S": "7"})
    cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    assert [len(p["lineas"]) for p, _ in sv5.llamadas] == [2, 1]
    assert {t for _, t in sv5.llamadas} == {7.0}


def test_f024_r19_endpoint_recientes_y_forzar(portal) -> None:
    cliente, _f, ids, sv5 = portal(["registrado"] * 2)
    cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    r = cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    assert (r.json()["comprobadas"], r.json()["recientes"]) == (0, 2)
    assert len(sv5.llamadas) == 1
    r = cliente.post("/api/sigrid/comprobar",
                     json={"registro_ids": ids, "forzar": True})
    assert r.json()["comprobadas"] == 2 and len(sv5.llamadas) == 2


def test_f024_r19_endpoint_ttl_cero_no_retiene(portal) -> None:
    cliente, _f, ids, sv5 = portal(
        ["registrado"], entorno={"COMPROBACION_SIGRID_TTL_S": "0"})
    cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    assert len(sv5.llamadas) == 2


def test_f024_r17_endpoint_sin_sv5_es_503(portal) -> None:
    cliente, *_ = portal(["registrado"], con_sv5=False)
    r = cliente.post("/api/sigrid/comprobar", json={"registro_ids": [1]})
    assert r.status_code == 503
    assert r.json()["ok"] is False


@pytest.mark.parametrize("cuerpo", [
    pytest.param({"registro_ids": []}, id="cero"),
    pytest.param({"registro_ids": list(range(1, 5002))}, id="5001"),
    pytest.param({}, id="sin-ids"),
    pytest.param({"registro_ids": ["x"]}, id="no-numerico"),
])
def test_f024_r17_endpoint_ids_fuera_de_rango_es_422(portal, cuerpo) -> None:
    cliente, _f, _ids, sv5 = portal(["registrado"])
    r = cliente.post("/api/sigrid/comprobar", json=cuerpo)
    assert r.status_code == 422
    assert sv5.llamadas == []


def test_f024_r17_endpoint_admite_5000_ids(portal) -> None:
    cliente, _f, ids, _sv5 = portal(["registrado"])
    r = cliente.post("/api/sigrid/comprobar",
                     json={"registro_ids": list(range(ids[0], ids[0] + 5000))})
    assert r.status_code == 200 and r.json()["comprobadas"] == 1


def test_f024_r14_endpoint_fallo_de_sv5_es_502_y_no_cambia_nada(portal) -> None:
    sv5 = Sv5Portal(fallos=[{"ok": False, "error": "HTTP 404"}])
    cliente, fabrica, ids, _ = portal(["registrado"], sv5=sv5)
    sv5.borradas = set(ids)
    r = cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    assert r.status_code == 502
    assert r.json()["ok"] is False and r.json()["error"] == "HTTP 404"
    assert _estado(fabrica, ids[0]) == "registrado"


@pytest.mark.parametrize("origen, esperado", [
    ("vista-obra", "vista-obra"), ("vista-trabajador", "vista-trabajador"),
    ("boton", "boton"), ("<script>", "boton"), (None, "boton")])
def test_f024_r21_endpoint_log_con_el_origen(portal, caplog, origen,
                                             esperado) -> None:
    cliente, _f, ids, _sv5 = portal(["registrado"])
    cuerpo = {"registro_ids": ids}
    if origen is not None:
        cuerpo["origen"] = origen
    with caplog.at_level(logging.INFO):
        cliente.post("/api/sigrid/comprobar", json=cuerpo)
    lineas = [r.getMessage() for r in caplog.records
              if "[comprobacion-sigrid]" in r.getMessage()]
    assert len(lineas) == 1
    assert f"origen={esperado} " in lineas[0]


def test_f024_r18_endpoint_servir_las_vistas_no_llama_a_sv5(portal) -> None:
    cliente, _f, _ids, sv5 = portal(["registrado", "borrado_sigrid"])
    assert cliente.get("/obras/obr-10").status_code == 200
    assert cliente.get("/trabajadores/emp-77").status_code == 200
    assert sv5.llamadas == [] and sv5.otras == []


def test_f024_r28_endpoint_estado_cuenta_sin_escribir(portal) -> None:
    cliente, fabrica, ids, sv5 = portal(
        ["encolado", "encolado", "registrado", "omitido", "conflicto",
         "error", None])
    antes = {i: _estado(fabrica, i) for i in ids}
    r = cliente.post("/api/aprobar/estado", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "total": 7, "pendientes": 2, "estados": {
        "encolado": 2, "registrado": 1, "omitido": 1, "conflicto": 1,
        "error": 1, "sin_estado": 1}}
    assert {i: _estado(fabrica, i) for i in ids} == antes
    assert sv5.llamadas == [] and sv5.otras == []


def test_f024_r28_endpoint_estado_no_necesita_sv5(portal) -> None:
    cliente, _f, ids, _ = portal(["encolado"], con_sv5=False)
    r = cliente.post("/api/aprobar/estado", json={"registro_ids": ids})
    assert r.status_code == 200 and r.json()["pendientes"] == 1


@pytest.mark.parametrize("cuerpo", [
    pytest.param({"registro_ids": []}, id="cero"),
    pytest.param({"registro_ids": list(range(1, 5002))}, id="5001"),
    pytest.param({}, id="sin-ids"),
])
def test_f024_r28_endpoint_estado_fuera_de_rango_es_422(portal, cuerpo) -> None:
    cliente, *_ = portal(["encolado"])
    assert cliente.post("/api/aprobar/estado", json=cuerpo).status_code == 422


def test_f024_r28_endpoint_estado_admite_5000(portal) -> None:
    cliente, _f, ids, _ = portal(["encolado"])
    r = cliente.post("/api/aprobar/estado",
                     json={"registro_ids": list(range(ids[0], ids[0] + 5000))})
    assert r.status_code == 200 and r.json()["total"] == 1



# ===================================================================== #
# T17 · supervivientes de la campana de mutacion (progress/mutacion_F-024.md)
# ===================================================================== #

def test_f024_r14_servicio_la_excepcion_de_sv5_llega_al_error() -> None:
    """Mutante 18: el texto de la excepcion es el error que se devuelve."""
    fabrica, repo, ids = _sembrar(["registrado"])
    sv5 = Sv5Falso(fallos=[RuntimeError("sv5 caido")])
    out = _servicio(repo, sv5).comprobar_ids(ids, origen="boton")
    assert out["error"] == "error llamando a sv5: sv5 caido"
    assert _estado(fabrica, ids[0]) == "registrado"


def test_f024_r17_servicio_settings_timeout_fraccionario(entorno_pg) -> None:
    """Mutante 36: cualquier plazo positivo vale, tambien menos de 1 s."""
    entorno_pg.setenv("COMPROBACION_SIGRID_TIMEOUT_S", "0.5")
    assert Settings(_env_file=None).comprobacion_sigrid_timeout_s == 0.5


@pytest.mark.parametrize("ruta", ["/api/sigrid/comprobar",
                                  "/api/aprobar/estado"])
def test_f024_r17_endpoint_fuera_del_esquema_publico(portal, ruta) -> None:
    """Mutantes 103 y 113: como el resto de endpoints de aprobacion, no
    se publican en el esquema OpenAPI."""
    cliente, *_ = portal(["registrado"])
    assert ruta not in cliente.app.openapi()["paths"]
