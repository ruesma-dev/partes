# tests/test_f046_aplicar.py
"""F-046 · «Aplicar» / «Mantener lo registrado» en sv4 (R32-R35, R38).

Repositorio contra SQLite en memoria (`FabricaSesionSqlite`, el mismo ORM
que produccion): CAS sobre `reparto_pendiente.estado`, comprobaciones
antes de aplicar, reserva de ids y exclusion de las lineas sin decision.
Datos sinteticos: el DNI y el nombre son los ficticios de `dobles`.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from application.services.reparto_aviso import (
    MOTIVO_PENDIENTE,
    RepartoCambiadoError,
)
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

FECHA = 20260302
RECURSO = 501


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _repo(fabrica) -> ParteReviewRepository:
    return ParteReviewRepository(fabrica)  # type: ignore[arg-type]


def _marcar(fabrica, rid, **campos):
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _dia(fabrica, *, nueva=False):
    """0678 registrada 8 + (-4) y 0704 libre (ya con el ideal 5,5 + 2,5
    que dejo sv3). Con `nueva`, la 0678 no tiene extra (R7)."""
    lineas = [{"estado": "registrado", "horas": 8.0}]
    if not nueva:
        lineas.append({"estado": "registrado", "horas": -4.0,
                       "tipo": "extra"})
    ids678 = sembrar_parte(fabrica, lineas, document_id="doc-678",
                           obra_ide=678, obra_codigo="0678")
    libre, libre_extra = sembrar_parte(
        fabrica, [{"horas": 5.5}, {"horas": 2.5, "tipo": "extra"}],
        document_id="doc-704", obra_ide=704, obra_codigo="0704")
    _marcar(fabrica, libre_extra, extra_auto=True)
    if not nueva:
        _marcar(fabrica, ids678[1], extra_auto=True)
    return ids678, libre, libre_extra


def _cambio(rid, base, tipo, antes, despues, estado="registrado", **kw):
    d = {"registro_id": rid, "base_registro_id": base, "tipo": tipo,
         "antes": antes, "despues": despues, "sigrid_estado": estado,
         "obra_codigo": "0678", "obra_ide": 678, "document_id": "doc-678"}
    d.update(kw)
    return d


def _reparto(fabrica, cambios, ids_grupo, *, estado="pendiente",
             resultado=None) -> int:
    with fabrica.create_session() as s:
        fila = RepartoPendienteOrm(
            recurso_ide=RECURSO, fecha_int=FECHA, estado=estado,
            firma="f" * 64,
            cambios=json.dumps({"ids_grupo": ids_grupo, "cambios": cambios}),
            resultado=resultado, creado_at_utc="x", actualizado_at_utc="x")
        s.add(fila)
        s.commit()
        return fila.id


def _caso_real(fabrica):
    (base, extra), libre, libre_extra = _dia(fabrica)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 2.5),
                             _cambio(extra, base, "extra", -4.0, 1.5)],
                   [base, extra, libre])
    return rid, base, extra, libre, libre_extra


def _fila(fabrica, rid) -> RepartoPendienteOrm:
    with fabrica.create_session() as s:
        return s.get(RepartoPendienteOrm, rid)


# ------------------------------- lectura ------------------------------- #

def test_f046_r30_repositorio_repartos_de_registros(fabrica):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    (f,) = _repo(fabrica).repartos_de_registros([libre, libre_extra])
    assert (f["id"], f["estado"], f["recurso_ide"], f["fecha_int"]) == (
        rid, "pendiente", RECURSO, FECHA)
    assert sorted(f["registro_ids"]) == sorted([libre, libre_extra])
    assert [(c["registro_id"], c["parte_cod"]) for c in f["cambios"]] == [
        (base, "PT26/00001"), (extra, "PT26/00001")]
    assert f["document_ids"] == ["doc-678", "doc-704"]


def test_f046_r30_repositorio_sin_reparto_vivo_no_hay_nada(fabrica):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "obsoleto"
        s.commit()
    assert _repo(fabrica).repartos_de_registros([libre]) == []


def test_f046_r30_repositorio_completa_la_extra_nueva_con_su_base(fabrica):
    (base,), libre, _le = _dia(fabrica, nueva=True)
    _marcar(fabrica, base, partida_ide=33, partida_cod="P-33")
    _reparto(fabrica, [
        _cambio(base, base, "ordinaria", 8.0, 5.5),
        _cambio(None, base, "extra", 0.0, 2.5,
                hora_ext={"ide": 9, "cod": "HE01", "desc": "x", "ext": 1})],
        [base, libre])
    (f,) = _repo(fabrica).repartos_de_registros([libre])
    nueva = f["cambios"][1]
    assert (nueva["recurso_ide"], nueva["fecha_int"], nueva["partida_ide"],
            nueva["partida_cod"], nueva["obra_ide"], nueva["obra_codigo"],
            nueva["hora_ide"], nueva["hora_codigo"], nueva["parte_cod"]) == (
        RECURSO, FECHA, 33, "P-33", 678, "0678", 9, "HE01", "PT26/00001")


def test_f046_r37_repositorio_registros_con_reparto(fabrica):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    repo = _repo(fabrica)
    assert repo.registros_con_reparto([base, extra, libre, libre_extra,
                                       otro]) == {base, extra, libre,
                                                  libre_extra}
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "mantenido"
        s.commit()
    assert repo.registros_con_reparto([base, libre]) == set()


# ------------------------------- R33 ------------------------------- #

def test_f046_r33_repositorio_iniciar_pasa_a_aplicando(fabrica):
    rid, _base, *_ = _caso_real(fabrica)
    f = _repo(fabrica).iniciar_aplicacion(rid, actor="admin@test")
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decision, fila.decidido_por) == (
        "aplicando", "aplicar", "admin@test")
    assert fila.decidido_at_utc
    assert f["id"] == rid and f["reservas"] == {}


def test_f046_r33_repositorio_cas_mantener_tras_aplicar_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    with pytest.raises(RepartoCambiadoError):
        repo.rechazar_reparto(rid, actor="b")
    assert _fila(fabrica, rid).estado == "aplicando"


def test_f046_r33_repositorio_cas_aplicar_tras_mantener_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.rechazar_reparto(rid, actor="a")
    with pytest.raises(RepartoCambiadoError):
        repo.iniciar_aplicacion(rid, actor="b")
    assert _fila(fabrica, rid).estado == "rechazado"


@pytest.mark.parametrize("estado", ["aplicado", "materializado",
                                    "obsoleto", "mantenido"])
def test_f046_r33_repositorio_solo_se_aplica_lo_pendiente(fabrica, estado):
    rid, *_ = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = estado
        s.commit()
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r34_repositorio_reintento_desde_aplicando_conserva_reservas(
        fabrica):
    (base,), libre, _le = _dia(fabrica, nueva=True)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 5.5),
                             _cambio(None, base, "extra", 0.0, 2.5)],
                   [base, libre])
    repo = _repo(fabrica)
    primero = repo.iniciar_aplicacion(rid, actor="a")
    segundo = repo.iniciar_aplicacion(rid, actor="a")
    assert primero["reservas"] == segundo["reservas"]
    (reservado,) = primero["reservas"].values()
    assert reservado > libre                  # mas alla de los ids vivos
    assert json.loads(_fila(fabrica, rid).resultado)["reservas"] == {
        str(base): reservado}


def test_f046_r33_repositorio_linea_cambiada_es_409_sin_tocar_nada(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, horas=7.0)
    with pytest.raises(RepartoCambiadoError, match="cambi"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")
    assert _fila(fabrica, rid).estado == "pendiente"


def test_f046_r33_repositorio_estado_cambiado_es_409(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, sigrid_estado="borrado_sigrid")
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_linea_nueva_en_el_grupo_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    sembrar_parte(fabrica, [{"horas": 2.0}], document_id="doc-nuevo")
    with pytest.raises(RepartoCambiadoError, match="nuevas"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_linea_del_grupo_en_la_papelera_es_409(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, deleted_at_utc="2026-03-03T00:00:00+00:00")
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_documento_en_espera_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, "doc-704")
        doc.recalculo_pedido_id = "p-1"
        doc.recalculo_pedido_at_utc = datetime.now(timezone.utc).isoformat()
        s.commit()
    with pytest.raises(RepartoCambiadoError, match="recalcul"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_cerrar_ok_es_aplicado_con_la_respuesta(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=True, sv5={"ok": True,
                                                     "lineas": [1]},
                                  error=None, actor="a") == "aplicado"
    fila = _fila(fabrica, rid)
    assert fila.estado == "aplicado" and fila.error is None
    assert json.loads(fila.resultado) == {"reservas": {},
                                          "sv5": {"ok": True, "lineas": [1]}}


def test_f046_r34_repositorio_rechazo_de_sv5_vuelve_a_pendiente(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=False, sv5={"ok": False},
                                  error="no editable", actor="a") == \
        "pendiente"
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.error) == ("pendiente", "no editable")


def test_f046_r34_repositorio_sin_respuesta_sigue_aplicando(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=None, sv5=None, error="timeout",
                                  actor="a") == "aplicando"
    assert (_fila(fabrica, rid).estado, _fila(fabrica, rid).error) == (
        "aplicando", "timeout")


# ------------------------------- R35 / R38 ------------------------------- #

def test_f046_r35_repositorio_mantener_pasa_a_rechazado_y_firma(fabrica):
    rid, *_ = _caso_real(fabrica)
    f = _repo(fabrica).rechazar_reparto(rid, actor="admin@test")
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decision, fila.decidido_por) == (
        "rechazado", "mantener", "admin@test")
    # Los partes de sus lineas NO congeladas, para pedir el recalculo.
    assert f["documentos_libres"] == ["doc-704"]


def test_f046_r35_repositorio_mantener_dos_veces_es_idempotente(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.rechazar_reparto(rid, actor="a")
    repo.rechazar_reparto(rid, actor="a")
    assert _fila(fabrica, rid).estado == "rechazado"


def test_f046_r38_repositorio_la_decision_no_entra_en_undo_log(fabrica):
    from infrastructure.database.orm_models import UndoLogOrm
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    repo.cerrar_aplicacion(rid, ok=True, sv5=None, error=None, actor="a")
    with fabrica.create_session() as s:
        assert s.query(UndoLogOrm).count() == 0


# ------------------------------- R32 ------------------------------- #

def test_f046_r32_repositorio_sin_decision_no_viajan(fabrica):
    _rid, _base, _extra, libre, libre_extra = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    datos = _repo(fabrica).lineas_para_registro([libre, libre_extra, otro])
    assert [l["registro_id"] for l in datos["lineas"]] == [otro]
    assert datos["excluidas"]["reparto_pendiente"] == 2
    motivos = {d["registro_id"]: (d["estado"], d["motivo"])
               for d in datos["excluidas_detalle"]}
    assert motivos[libre] == ("reparto_pendiente", MOTIVO_PENDIENTE)


def test_f046_r32_repositorio_con_decision_aplicar_viajan(fabrica):
    rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    datos = _repo(fabrica).lineas_para_registro(
        [libre, libre_extra], repartos_decididos=frozenset({rid}))
    assert sorted(l["registro_id"] for l in datos["lineas"]) == sorted(
        [libre, libre_extra])
    assert "reparto_pendiente" not in datos["excluidas"]


def test_f046_r32_repositorio_aplicado_ya_no_excluye(fabrica):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "aplicado"
        s.commit()
    datos = _repo(fabrica).lineas_para_registro([libre])
    assert [l["registro_id"] for l in datos["lineas"]] == [libre]


def test_f046_r32_repositorio_sin_reparto_igual_que_siempre(fabrica):
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x")
    datos = _repo(fabrica).lineas_para_registro([otro])
    assert "reparto_pendiente" not in datos["excluidas"]
    assert [l["registro_id"] for l in datos["lineas"]] == [otro]


# ============================== rutas (T17) ============================== #
# `build_app` con el repositorio REAL sobre SQLite y dobles de sv5 y del
# publicador del recalculo: ni PostgreSQL, ni red, ni Storage.

from config.settings import Settings
from fastapi.testclient import TestClient
from interface_adapters.web.app import build_app

ACTOR = "local:ana"


class Sv5Fake:
    """Doble del cliente de sv5: registro y reajuste."""

    def __init__(self, *, reajuste=None, comprobar=None):
        self.reajuste = reajuste or {"ok": True, "ya_aplicada": False,
                                     "veredictos": [], "lineas": []}
        self.comprobar_resp = comprobar
        self.ejecutadas: list[dict] = []
        self.preflights: list[dict] = []
        self.reajustes: list[dict] = []
        self.comprobaciones: list[dict] = []

    def ejecutar(self, payload):
        self.ejecutadas.append(payload)
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": []}

    def preflight(self, payload):
        self.preflights.append(payload)
        return {"ok": True, "conflictos": [], "acciones": []}

    def reajuste_ejecutar(self, payload):
        self.reajustes.append(payload)
        return self.reajuste

    def reajuste_comprobar(self, payload, *, timeout_s=None):
        self.comprobaciones.append(payload)
        if self.comprobar_resp is not None:
            return self.comprobar_resp
        return {"ok": True, "veredictos": [
            {"registro_id": l["registro_id"], "editable": True,
             "ya_aplicada": False, "motivo": None}
            for l in payload["lineas"]]}


class RecalculoFake:
    def __init__(self):
        self.pedidos: list[tuple[str, str, str | None]] = []

    def pedir(self, *, document_id, motivo, solicitado_por):
        self.pedidos.append((document_id, motivo, solicitado_por))


class PublisherFake:
    def __init__(self):
        self.publicadas: list[dict] = []

    def publicar(self, payload, usuario=None):
        self.publicadas.append(payload)
        return f"p-{len(self.publicadas)}"


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


def _registradas(sv5) -> list[int]:
    return sorted(l["registro_id"] for p in sv5.ejecutadas
                  for l in p["lineas"])


# ------------------------------- R30 ------------------------------- #

def test_f046_r30_preflight_trae_el_bloque_de_repartos(fabrica, portal):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/preflight",
                     json={"registro_ids": [libre, libre_extra]})
    assert r.status_code == 200, r.text
    (b,) = r.json()["repartos"]
    assert (b["id"], b["fecha"], b["editable"], b["opciones"]) == (
        rid, "2026-03-02", True, ["aplicar", "mantener"])
    assert [(x["registro_id"], x["antes"], x["despues"], x["parte_cod"])
            for x in b["lineas"]] == [(base, 8.0, 2.5, "PT26/00001"),
                                      (extra, -4.0, 1.5, "PT26/00001")]
    (comprobado,) = sv5.comprobaciones
    assert [l["registro_id"] for l in comprobado["lineas"]] == [base, extra]
    # El preflight evalua las lineas como si se aplicara (consultivo).
    assert sorted(l["registro_id"] for l in sv5.preflights[0]["lineas"]) \
        == sorted([libre, libre_extra])


def test_f046_r31_preflight_no_editable_solo_mantener(fabrica, portal):
    _rid, base, extra, libre, _le = _caso_real(fabrica)
    sv5 = Sv5Fake(comprobar={"ok": False, "veredictos": [
        {"registro_id": base, "editable": True, "motivo": None},
        {"registro_id": extra, "editable": False,
         "motivo": "su parte de Sigrid no esta En registro"}]})
    cliente, _s, _r = portal(sv5=sv5)
    (b,) = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": [libre]}).json()["repartos"]
    assert b["opciones"] == ["mantener"]
    assert b["motivo"] == "su parte de Sigrid no esta En registro"


def test_f046_r30_preflight_sin_repartos_no_cambia(fabrica, portal):
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x")
    cliente, sv5, _r = portal()
    cuerpo = cliente.post("/api/aprobar/preflight",
                          json={"registro_ids": [otro]}).json()
    assert "repartos" not in cuerpo and sv5.comprobaciones == []


# ------------------------------- R32 ------------------------------- #

def test_f046_r32_ejecutar_sin_decision_deja_fuera_el_dia(fabrica, portal):
    _rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre, libre_extra, otro]})
    assert r.status_code == 200, r.text
    assert _registradas(sv5) == [otro]
    assert r.json()["excluidas"]["reparto_pendiente"] == 2
    assert sv5.reajustes == []


# ------------------------------- R33 ------------------------------- #

def test_f046_r33_aplicar_reajusta_en_sigrid_y_registra(fabrica, portal):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    cliente, sv5, recalculo = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre, libre_extra],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 200, r.text
    (p,) = sv5.reajustes
    assert p == {"lineas": [
        {"registro_id": base, "antes": 8.0, "despues": 2.5},
        {"registro_id": extra, "antes": -4.0, "despues": 1.5}],
        "usuario": ACTOR}
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decidido_por) == ("aplicado", ACTOR)
    assert sorted(recalculo.pedidos) == [
        ("doc-678", "reajuste_reparto", ACTOR),
        ("doc-704", "reajuste_reparto", ACTOR)]
    assert _registradas(sv5) == sorted([libre, libre_extra])
    assert r.json()["repartos"] == [{
        "id": rid, "decision": "aplicar", "estado": "aplicado", "ok": True,
        "error": None}]


def test_f046_r33_aplicar_solo_aprobadas_no_llama_a_sv5(fabrica, portal):
    (base, extra), libre, _le = _dia(fabrica)
    _marcar(fabrica, base, sigrid_estado=None)
    _marcar(fabrica, extra, sigrid_estado=None)
    rid = _reparto(fabrica, [
        _cambio(base, base, "ordinaria", 8.0, 2.5, estado=None),
        _cambio(extra, base, "extra", -4.0, 1.5, estado=None)],
        [base, extra, libre])
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 200, r.text
    assert sv5.reajustes == [] and _fila(fabrica, rid).estado == "aplicado"


def test_f046_r33_aplicar_con_linea_cambiada_es_409_sin_nada(fabrica,
                                                            portal):
    rid, base, _e, libre, _le = _caso_real(fabrica)
    _marcar(fabrica, base, horas=7.0)
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 409
    assert sv5.reajustes == [] and sv5.ejecutadas == []
    assert _fila(fabrica, rid).estado == "pendiente"


def test_f046_r33_reparto_ajeno_a_la_seleccion_es_409(fabrica, portal):
    rid, *_ = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [otro],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 409 and sv5.reajustes == []


@pytest.mark.parametrize("repartos", [
    [{"id": "x", "decision": "aplicar"}], [{"id": 1, "decision": "borrar"}],
    "no-es-lista", [{"decision": "aplicar"}]])
def test_f046_r32_decisiones_mal_formadas_son_422(fabrica, portal,
                                                   repartos):
    _rid, _b, _e, libre, _le = _caso_real(fabrica)
    cliente, sv5, _r = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre], "repartos": repartos})
    assert r.status_code == 422 and sv5.reajustes == []


# ------------------------------- R34 ------------------------------- #

def test_f046_r34_sv5_rechaza_vuelve_a_pendiente_y_no_registra(fabrica,
                                                               portal):
    rid, base, _extra, libre, _le = _caso_real(fabrica)
    sv5 = Sv5Fake(reajuste={"ok": False, "error": "hay lineas que no se "
                            "pueden reajustar", "veredictos": [
                                {"registro_id": base, "editable": False,
                                 "motivo": "la linea cambio en Sigrid"}]})
    cliente, _s, recalculo = portal(sv5=sv5)
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 200, r.text
    fila = _fila(fabrica, rid)
    assert fila.estado == "pendiente"
    assert "la linea cambio en Sigrid" in fila.error
    assert sv5.ejecutadas == [] and recalculo.pedidos == []
    (res,) = r.json()["repartos"]
    assert (res["estado"], res["ok"]) == ("pendiente", False)


def test_f046_r34_sin_respuesta_sigue_aplicando_y_se_reintenta(fabrica,
                                                               portal):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    sv5 = Sv5Fake(reajuste={"ok": False, "sin_respuesta": True,
                            "error": "timeout"})
    cliente, _s, _r = portal(sv5=sv5)
    cuerpo = {"registro_ids": [libre],
              "repartos": [{"id": rid, "decision": "aplicar"}]}
    cliente.post("/api/aprobar/ejecutar", json=cuerpo)
    assert (_fila(fabrica, rid).estado, _fila(fabrica, rid).error) == (
        "aplicando", "timeout")
    assert sv5.ejecutadas == []
    sv5.reajuste = {"ok": True, "ya_aplicada": True, "lineas": []}
    r = cliente.post("/api/aprobar/ejecutar", json=cuerpo)   # reintento
    assert r.status_code == 200, r.text
    assert _fila(fabrica, rid).estado == "aplicado"
    assert _registradas(sv5) == [libre]


# ------------------------------- R35 ------------------------------- #

def test_f046_r35_mantener_rechaza_pide_recalculo_y_no_registra(fabrica,
                                                                portal):
    rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    cliente, sv5, recalculo = portal()
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": [libre, libre_extra],
        "repartos": [{"id": rid, "decision": "mantener"}]})
    assert r.status_code == 200, r.text
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decision, fila.decidido_por) == (
        "rechazado", "mantener", ACTOR)
    assert recalculo.pedidos == [("doc-704", "reajuste_reparto", ACTOR)]
    assert sv5.reajustes == [] and sv5.ejecutadas == []
    assert r.json()["repartos"][0]["estado"] == "rechazado"


# --------------------------- encolar (R32/R33) --------------------------- #

def test_f046_r33_encolar_aplica_por_http_y_encola_las_lineas(fabrica,
                                                              portal):
    rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    publisher = PublisherFake()
    cliente, sv5, _r = portal(publisher=publisher)
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": [libre, libre_extra],
        "repartos": [{"id": rid, "decision": "aplicar"}]})
    assert r.status_code == 200, r.text
    assert len(sv5.reajustes) == 1
    assert _fila(fabrica, rid).estado == "aplicado"
    (payload,) = publisher.publicadas
    assert sorted(l["registro_id"] for l in payload["lineas"]) == sorted(
        [libre, libre_extra])
    assert r.json()["repartos"][0]["estado"] == "aplicado"


def test_f046_r32_encolar_sin_decision_no_encola_el_dia(fabrica, portal):
    _rid, _b, _e, libre, _le = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    publisher = PublisherFake()
    cliente, _s, _r = portal(publisher=publisher)
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": [libre, otro]})
    assert r.status_code == 200, r.text
    assert [l["registro_id"] for l in publisher.publicadas[0]["lineas"]] \
        == [otro]
