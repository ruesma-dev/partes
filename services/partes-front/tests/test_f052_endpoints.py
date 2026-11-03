# tests/test_f052_endpoints.py
"""F-052 en sv4: `POST /api/sincronizar` y su configuración (R7, R10, R15,
R30; DA18).

- 503 sin `TRANSFER_BASE_URL` (R30), 422 con un ámbito que no lee Sigrid
  (R15) o sin ámbito.
- DA18: por defecto (`SINCRONIZAR_SECO` sin poner) es seco: una línea
  `registrado` que no está en Sigrid sigue `registrado` en la base; con
  `SINCRONIZAR_SECO=false` pasa a `borrado_sigrid` como F-024 (R10).
- `SINCRONIZAR_TIMEOUT_S` (150, < 230) llega a sv5; `TransferClient.
  sincronizar_leer` llama a `/api/sincronizar/leer`.

SQLite en memoria con el repositorio real y un doble de sv5; sin red.
"""
from __future__ import annotations

import httpx
import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.persistencia.recalculo_publisher import MOTIVO_SINCRONIZAR
from infrastructure.transfer import transfer_client as modulo_tc
from infrastructure.transfer.transfer_client import TransferClient
from interface_adapters.web.app import build_app
from pydantic import ValidationError
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_parte

AMBITO = {"vista": "obra", "obra_key": "obr-10", "period": "2026-03",
          "mode": "natural"}


class Sv5Sync:
    """Doble de sv5 para levantar el portal: lectura de sincronizar y
    veredicto de F-024. `borradas` son los registro_id que Sigrid no
    tiene; el resto, presentes."""

    def __init__(self, lineas=(), borradas=()) -> None:
        self.lineas = list(lineas)
        self.borradas = set(borradas)
        self.leer: list[tuple[dict, float]] = []
        self.comprobaciones: list[dict] = []
        self.otras: list[str] = []

    def sincronizar_leer(self, payload, *, timeout_s):
        self.leer.append((payload, timeout_s))
        return {"ok": True, "lineas": list(self.lineas)}

    def comprobar(self, payload, *, timeout_s):
        self.comprobaciones.append(payload)
        return {"ok": True, "veredictos": [
            {"registro_id": l["registro_id"],
             "estado": "borrada" if l["registro_id"] in self.borradas
             else "presente", "hmores_ide": l.get("hmores_ide"),
             "hmoide": l.get("hmoide")} for l in payload["lineas"]]}

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
    for clave in ("TRANSFER_BASE_URL", "SINCRONIZAR_SECO",
                  "SINCRONIZAR_TIMEOUT_S", "COMPROBACION_SIGRID_LOTE"):
        monkeypatch.delenv(clave, raising=False)

    def _levantar(estados, *, sv5=None, con_sv5=True, entorno=None):
        for clave, valor in (entorno or {}).items():
            monkeypatch.setenv(clave, valor)
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, [{"estado": e} for e in estados])
        repo = ParteReviewRepository(fabrica)
        if con_sv5 and sv5 is None:
            sv5 = Sv5Sync(borradas=ids)
        app = build_app(Settings(_env_file=None), repository=repo,
                        transfer_client=sv5 if con_sv5 else None)
        return TestClient(app), fabrica, ids, sv5
    return _levantar


def test_f052_r30_sin_transfer_503(portal) -> None:
    cliente, _f, _ids, _ = portal(["registrado"], con_sv5=False)
    r = cliente.post("/api/sincronizar", json={"ambito": AMBITO})
    assert r.status_code == 503
    assert "TRANSFER_BASE_URL" in r.json()["error"]


@pytest.mark.parametrize("cuerpo", [
    {"ambito": dict(AMBITO, obra_key="cod-0100")},
    {"ambito": {"vista": "trabajador", "worker_key": "emp-77",
                "period": "2026-03"}},
    {"ambito": dict(AMBITO, period="")},
])
def test_f052_r15_endpoint_ambito_no_valido_422(portal, cuerpo) -> None:
    cliente, _f, _ids, sv5 = portal(["registrado"])
    r = cliente.post("/api/sincronizar", json=cuerpo)
    assert r.status_code == 422
    assert r.json()["ok"] is False and sv5.leer == []


def test_f052_r7_endpoint_sin_ambito_422(portal) -> None:
    cliente, _f, _ids, sv5 = portal(["registrado"])
    assert cliente.post("/api/sincronizar", json={}).status_code == 422
    assert sv5.leer == []


def test_f052_da18_endpoint_seco_por_defecto_no_escribe(portal) -> None:
    cliente, fabrica, ids, sv5 = portal(["registrado", None])
    antes = estados_sigrid(fabrica, ids)
    r = cliente.post("/api/sincronizar", json={"ambito": AMBITO})
    assert r.status_code == 200
    c = r.json()
    assert c["seco"] is True
    assert c["marcaria_borrado_sigrid"] == [ids[0]]
    assert [i["clase"] for i in c["items"]] == ["borrada_en_sigrid",
                                                "pendiente"]
    assert estados_sigrid(fabrica, ids) == antes
    assert [l["registro_id"] for l in sv5.comprobaciones[0]["lineas"]] == [
        ids[0]]
    assert sv5.leer[0] == ({"obra_ide": 10, "desde": 20260301,
                            "hasta": 20260331, "registro_ids": ids}, 150.0)
    assert sv5.otras == []


def test_f052_r10_endpoint_fuera_de_seco_pasa_a_borrado_sigrid(portal) -> None:
    cliente, fabrica, ids, sv5 = portal(
        ["registrado"], entorno={"SINCRONIZAR_SECO": "false",
                                 "SINCRONIZAR_TIMEOUT_S": "40"})
    r = cliente.post("/api/sincronizar", json={"ambito": AMBITO})
    assert r.status_code == 200
    assert r.json()["seco"] is False
    assert r.json()["marcadas_borrado_sigrid"] == [ids[0]]
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "borrado_sigrid"
    assert sv5.leer[0][1] == 40.0


def test_f052_r10_endpoint_fuera_de_seco_vuelve_a_comprobar_aunque_sea_reciente(
        portal) -> None:
    """`forzar`: el antimartilleo de F-024 no deja la línea sin confirmar."""
    cliente, fabrica, ids, sv5 = portal(
        ["registrado"], entorno={"SINCRONIZAR_SECO": "false"})
    sv5.borradas = set()
    cliente.post("/api/sigrid/comprobar", json={"registro_ids": ids})
    sv5.borradas = set(ids)
    r = cliente.post("/api/sincronizar", json={"ambito": AMBITO})
    assert r.status_code == 200
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "borrado_sigrid"


# ------------------------------- settings -------------------------------- #

@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    for clave in ("SINCRONIZAR_SECO", "SINCRONIZAR_TIMEOUT_S"):
        monkeypatch.delenv(clave, raising=False)
    return monkeypatch


def test_f052_da18_settings_por_defecto(entorno) -> None:
    st = Settings(_env_file=None)
    assert st.sincronizar_seco is True
    assert st.sincronizar_timeout_s == 150.0


@pytest.mark.parametrize("valor, esperado", [
    ("false", False), ("0", False), ("true", True)])
def test_f052_da18_settings_seco_por_entorno(entorno, valor,
                                             esperado) -> None:
    entorno.setenv("SINCRONIZAR_SECO", valor)
    assert Settings(_env_file=None).sincronizar_seco is esperado


@pytest.mark.parametrize("valor", ["0", "-1", "230", "abc"])
def test_f052_settings_timeout_fuera_de_rango(entorno, valor) -> None:
    entorno.setenv("SINCRONIZAR_TIMEOUT_S", valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


# ----------------------------- TransferClient ---------------------------- #

def test_f052_r7_transfer_client_sincronizar_leer(monkeypatch) -> None:
    llamadas: list[tuple] = []

    def _post(url, json=None, timeout=None):
        llamadas.append((url, json, timeout))
        return httpx.Response(200, json={"ok": True, "lineas": []})

    monkeypatch.setattr(modulo_tc.httpx, "post", _post)
    tc = TransferClient(base_url="http://sv5.invalid/", timeout_s=120)
    payload = {"obra_ide": 1, "desde": 20261001, "hasta": 20261031,
               "registro_ids": []}
    assert tc.sincronizar_leer(payload, timeout_s=150) == {
        "ok": True, "lineas": []}
    assert llamadas == [("http://sv5.invalid/api/sincronizar/leer",
                         payload, 150.0)]


def test_f052_r13_transfer_client_error_de_sv5_ok_false(monkeypatch) -> None:
    def _post(url, json=None, timeout=None):
        return httpx.Response(502, json={"ok": False, "error": "truncada"})

    monkeypatch.setattr(modulo_tc.httpx, "post", _post)
    tc = TransferClient(base_url="http://sv5.invalid")
    assert tc.sincronizar_leer({}, timeout_s=1) == {"ok": False,
                                                     "error": "truncada"}


# ==================== T10 · POST /api/sincronizar/aplicar ================ #

class RecalculoPub:
    """Doble de `RecalculoPublisher`: apunta cada pedido."""

    def __init__(self) -> None:
        self.pedidos: list[dict] = []

    def pedir(self, *, document_id, motivo, solicitado_por):
        self.pedidos.append({"document_id": document_id, "motivo": motivo,
                             "solicitado_por": solicitado_por})


def linea_sv5(rid: int, *, hmores: int, can: float = 8.0, **cambios) -> dict:
    """Una línea de Sigrid de la obra 10 el 02/03/2026 (la de `sembrar_parte`)."""
    base = dict(hmores_ide=hmores, hmoide=7100, parte_cod="PT26/00100",
                parte_est=1, obra_ide=10, obra_cod="0100", recurso_ide=501,
                fecha_int=20260302, hora_ide=1, hora_cod="HL01", hora_ext=0,
                partida_ide=None, partida_cod=None, can=can, tot=can * 15,
                enlazada=False, origen="partes", registro_id=rid,
                ajuste_id=None)
    base.update(cambios)
    return base


@pytest.fixture
def acciones(monkeypatch):
    """`_montar(lineas, sv5_de_ids) -> (cliente, fabrica, ids, sv5, pub)`."""
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana"}.items():
        monkeypatch.setenv(clave, valor)
    for clave in ("TRANSFER_BASE_URL", "SINCRONIZAR_SECO",
                  "SINCRONIZAR_MAX_ITEMS_ACCION"):
        monkeypatch.delenv(clave, raising=False)

    def _montar(lineas, sv5_de_ids=lambda ids: [], *, con_sv5=True,
                entorno=None, aprobado=True):
        for clave, valor in (entorno or {}).items():
            monkeypatch.setenv(clave, valor)
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, lineas, aprobado=aprobado)
        sv5 = Sv5Sync(sv5_de_ids(ids)) if con_sv5 else None
        pub = RecalculoPub()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, recalculo_publisher=pub)
        return TestClient(app), fabrica, ids, sv5, pub
    return _montar


def _primera(cliente) -> dict:
    r = cliente.post("/api/sincronizar", json={"ambito": AMBITO})
    assert r.status_code == 200, r.text
    return {i["registro_id"]: i for i in r.json()["items"]}


def _aplicar(cliente, accion, items, ambito=AMBITO):
    return cliente.post("/api/sincronizar/aplicar", json={
        "accion": accion, "ambito": ambito, "items": items})


def test_f052_r30_aplicar_sin_transfer_503(acciones) -> None:
    cliente, _f, ids, _sv5, _p = acciones([{"estado": "error"}],
                                          con_sv5=False)
    r = _aplicar(cliente, "marcar_registrada",
                 [{"registro_id": ids[0], "firma": "x" * 16}])
    assert r.status_code == 503


def test_f052_r19_aplicar_marcar_registrada_con_el_actor(acciones) -> None:
    cliente, fabrica, ids, sv5, _p = acciones(
        [{"estado": "error"}], lambda ids: [linea_sv5(ids[0], hmores=9100)])
    item = _primera(cliente)[ids[0]]
    assert item["clase"] == "en_sigrid_sin_registrar"
    r = _aplicar(cliente, "marcar_registrada",
                 [{"registro_id": ids[0], "firma": item["firma"]}])
    assert r.status_code == 200, r.text
    assert r.json()["aplicados"] == [ids[0]]
    assert len(sv5.leer) == 2                       # volvió a sincronizar
    estado, motivo, hmoide, hmores, parte = estados_sigrid(fabrica, ids)[
        ids[0]]
    assert (estado, hmoide, hmores, parte) == ("registrado", 7100, 9100,
                                               "PT26/00100")
    assert motivo.startswith("Sincronizado con Sigrid: estado error→"
                             "registrado · local:ana · ")
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]).sigrid_registrado_by == (
            "local:ana")
    assert sv5.otras == []                          # R26: nada a Sigrid


def test_f052_r20_aplicar_traer_de_sigrid_y_recalculo(acciones) -> None:
    cliente, fabrica, ids, _sv5, pub = acciones(
        [{"estado": "registrado"}],
        lambda ids: [linea_sv5(ids[0], hmores=9000, can=6.0)])
    item = _primera(cliente)[ids[0]]
    assert item["clase"] == "distinta"
    r = _aplicar(cliente, "traer_de_sigrid",
                 [{"registro_id": ids[0], "firma": item["firma"]}])
    assert r.status_code == 200, r.text
    assert r.json()["aplicados"] == [ids[0]]
    assert r.json()["recalculo"] == "pedido"
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]).horas == 6.0
    assert pub.pedidos == [{"document_id": "doc-f004",
                            "motivo": MOTIVO_SINCRONIZAR,
                            "solicitado_por": "local:ana"}]
    assert MOTIVO_SINCRONIZAR == "sincronizar"


def test_f052_r18_aplicar_firma_vieja_descarta(acciones) -> None:
    cliente, fabrica, ids, _sv5, _p = acciones(
        [{"estado": "registrado"}],
        lambda ids: [linea_sv5(ids[0], hmores=9000, can=6.0)])
    r = _aplicar(cliente, "traer_de_sigrid",
                 [{"registro_id": ids[0], "firma": "0" * 16}])
    assert r.status_code == 200
    assert r.json()["descartados"] == [{"registro_id": ids[0],
                                        "motivo": "cambió desde que lo viste"}]
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]).horas == 8.0


def test_f052_r18_aplicar_id_ajeno_f022_422_sin_leer(acciones) -> None:
    cliente, _f, _ids, sv5, _p = acciones([{"estado": "error"}])
    r = _aplicar(cliente, "marcar_registrada",
                 [{"registro_id": 99999, "firma": "x" * 16}])
    assert r.status_code == 422
    assert "no son de esta vista" in r.json()["error"]
    assert sv5.leer == []


def test_f052_r24_aplicar_restaurar_desde_la_papelera(acciones) -> None:
    """La línea está en la papelera (fuera de la vista de F-022): su ámbito
    lo prueba la relectura, que la encuentra en Sigrid en ese ámbito."""
    cliente, fabrica, ids, _sv5, _p = acciones(
        [{"estado": "registrado", "borrada": True}],
        lambda ids: [linea_sv5(ids[0], hmores=9000)])
    item = _primera(cliente)[ids[0]]
    assert (item["clase"], item["donde"]) == ("solo_sigrid_nuestra",
                                              "papelera")
    r = _aplicar(cliente, "restaurar",
                 [{"registro_id": ids[0], "firma": item["firma"]}])
    assert r.status_code == 200, r.text
    assert r.json()["aplicados"] == [ids[0]]
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]).deleted_at_utc is None


def test_f052_r18_aplicar_tope_de_items_422(acciones) -> None:
    cliente, _f, _ids, sv5, _p = acciones(
        [{"estado": "error"}], entorno={"SINCRONIZAR_MAX_ITEMS_ACCION": "2"})
    r = _aplicar(cliente, "marcar_registrada",
                 [{"registro_id": i, "firma": "x" * 16} for i in (1, 2, 3)])
    assert r.status_code == 422 and "máximo es 2" in r.json()["error"]
    assert sv5.leer == []


@pytest.mark.parametrize("cuerpo", [
    {"accion": "marcar_registrada", "ambito": AMBITO, "items": []},
    {"accion": "marcar_registrada", "ambito": AMBITO,
     "items": [{"registro_id": 1}]},
    {"accion": "marcar_registrada", "items": [{"registro_id": 1,
                                               "firma": "x"}]},
    {"accion": "borrar", "ambito": AMBITO,
     "items": [{"registro_id": 1, "firma": "x"}]},
])
def test_f052_r18_aplicar_peticion_no_valida_422(acciones, cuerpo) -> None:
    cliente, _f, _ids, sv5, _p = acciones([{"estado": "error"}])
    r = cliente.post("/api/sincronizar/aplicar", json=cuerpo)
    assert r.status_code == 422 and sv5.leer == []


def test_f052_settings_max_items_accion(entorno) -> None:
    assert Settings(_env_file=None).sincronizar_max_items_accion == 500
    for valor in ("0", "5001", "abc"):
        entorno.setenv("SINCRONIZAR_MAX_ITEMS_ACCION", valor)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
