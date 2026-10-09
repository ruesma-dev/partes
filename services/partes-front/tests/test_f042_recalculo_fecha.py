# tests/test_f042_recalculo_fecha.py
"""F-042 · R1-R11: sv4 pide el recalculo de extras al guardar la fecha.

El reparto ordinaria/extra lo calcula SOLO sv3, y solo cuando le llega un
mensaje por `q-persistencia`. Cambiar la fecha de un parte en el portal
dejaba el reparto del dia viejo hasta la siguiente ingesta. Desde F-042,
sv4 publica un mensaje «recalcular» en esa cola tras guardar (o deshacer)
la fecha, y lo cuenta en la respuesta (`recalculo`).

Sin red: repositorio real sobre SQLite y una cola doble que apunta lo que
se le manda (o que falla). Datos sinteticos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.persistencia.recalculo_publisher import (
    ESTADO_FALLO,
    ESTADO_PEDIDO,
    ESTADO_SIN_COLA,
    MOTIVO_CAMBIO_FECHA,
    MOTIVO_DESHACER_FECHA,
    TIPO_RECALCULAR,
    RecalculoPublisher,
    mensaje_recalculo,
    pedir_recalculo,
)
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

DOC = "doc-f004"                     # el `document_id` de `sembrar_parte`
ACTOR = "revisora@ejemplo.es"
CABECERA = {"X-MS-CLIENT-PRINCIPAL-NAME": ACTOR}
RELOJ_FIJO = datetime(2026, 10, 9, 10, 30, 0, tzinfo=timezone.utc)


# ------------------------------- dobles -------------------------------- #

class ColaFake:
    """`ColaCliente` reducido a `enviar`; apunta o falla."""

    def __init__(self, *, error: Exception | None = None,
                 eventos: list | None = None) -> None:
        self.enviados: list[tuple[str, dict]] = []
        self._error = error
        self._eventos = eventos
        self.al_enviar = None

    def enviar(self, queue_name: str, payload: dict) -> None:
        if self._eventos is not None:
            self._eventos.append("enviar")
        if self.al_enviar is not None:
            self.al_enviar()
        if self._error is not None:
            raise self._error
        self.enviados.append((queue_name, payload))


class RepositorioEspia(ParteReviewRepository):
    """Anota cuando `update_parte_fecha` ha terminado (ya con commit)."""

    def __init__(self, fabrica, eventos: list) -> None:
        super().__init__(fabrica)
        self._eventos = eventos

    def update_parte_fecha(self, **kwargs) -> bool:
        ok = super().update_parte_fecha(**kwargs)
        self._eventos.append("update_parte_fecha")
        return ok


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    return monkeypatch


@pytest.fixture
def montaje(entorno):
    """`_montar(...) -> (cliente, cola, fabrica)` con un parte libre."""

    def _montar(*, cola: ColaFake | None = None, sin_cola: bool = False,
                publisher=None, aprobado: bool = False, repositorio=None,
                fabrica=None):
        fabrica = fabrica or FabricaSesionSqlite()
        sembrar_parte(fabrica, [{"estado": None, "horas": 8.5}],
                      aprobado=aprobado)
        cola = None if sin_cola else (cola or ColaFake())
        app = build_app(
            Settings(_env_file=None),
            repository=repositorio or ParteReviewRepository(fabrica),
            cola_cliente=cola, recalculo_publisher=publisher)
        return TestClient(app), cola, fabrica
    return _montar


def _fecha_doc(fabrica, document_id: str = DOC) -> str | None:
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, document_id)
        return None if doc is None else doc.fecha


def _patch(cliente, fecha: str = "2026-10-01", doc: str = DOC):
    return cliente.patch(f"/api/partes/{doc}/fecha", json={"fecha": fecha},
                         headers=CABECERA)


# ===================== el modulo del contrato (sv4) ===================== #

def test_f042_r1_constantes_del_contrato() -> None:
    assert TIPO_RECALCULAR == "recalcular"
    assert MOTIVO_CAMBIO_FECHA == "cambio_fecha"
    assert MOTIVO_DESHACER_FECHA == "deshacer_cambio_fecha"
    assert (ESTADO_PEDIDO, ESTADO_FALLO, ESTADO_SIN_COLA) == (
        "pedido", "fallo", "sin_cola")


def test_f042_r1_mensaje_recalculo_es_el_del_contrato() -> None:
    assert mensaje_recalculo(
        document_id="doc-1", motivo=MOTIVO_CAMBIO_FECHA,
        solicitado_por=ACTOR, ahora=RELOJ_FIJO,
    ) == {"tipo": "recalcular", "motivo": "cambio_fecha",
          "document_id": "doc-1", "solicitado_por": ACTOR,
          "solicitado_at_utc": "2026-10-09T10:30:00+00:00"}


def test_f042_r1_la_hora_del_mensaje_va_en_utc() -> None:
    madrid = timezone(timedelta(hours=2))
    m = mensaje_recalculo(document_id="d", motivo=MOTIVO_DESHACER_FECHA,
                          solicitado_por=None,
                          ahora=datetime(2026, 10, 9, 12, 30, tzinfo=madrid))
    assert m["solicitado_at_utc"] == "2026-10-09T10:30:00+00:00"
    assert m["solicitado_por"] is None
    assert m["motivo"] == "deshacer_cambio_fecha"


def test_f042_r1_el_publisher_envia_a_su_cola(caplog) -> None:
    cola = ColaFake()
    caplog.set_level(logging.INFO)
    RecalculoPublisher(cola=cola, cola_persistencia="q-x",
                       reloj=lambda: RELOJ_FIJO).pedir(
        document_id="doc-1", motivo=MOTIVO_CAMBIO_FECHA, solicitado_por=ACTOR)
    assert cola.enviados == [("q-x", mensaje_recalculo(
        document_id="doc-1", motivo=MOTIVO_CAMBIO_FECHA,
        solicitado_por=ACTOR, ahora=RELOJ_FIJO))]
    assert "[recalculo] pedido" in caplog.text
    assert "document_id=doc-1" in caplog.text


def test_f042_r1_el_reloj_por_defecto_es_utc_y_de_ahora() -> None:
    cola = ColaFake()
    antes = datetime.now(timezone.utc)
    RecalculoPublisher(cola=cola, cola_persistencia="q-x").pedir(
        document_id="d", motivo=MOTIVO_CAMBIO_FECHA, solicitado_por=None)
    despues = datetime.now(timezone.utc)
    sello = datetime.fromisoformat(cola.enviados[0][1]["solicitado_at_utc"])
    assert sello.utcoffset() == timedelta(0)
    assert antes <= sello <= despues


def test_f042_r3_el_publisher_lanza_si_la_cola_falla() -> None:
    error = ConnectionError("cola caida")
    with pytest.raises(ConnectionError) as exc:
        RecalculoPublisher(cola=ColaFake(error=error),
                           cola_persistencia="q-x").pedir(
            document_id="d", motivo=MOTIVO_CAMBIO_FECHA, solicitado_por=None)
    assert exc.value is error


def test_f042_r3_pedir_recalculo_nunca_lanza(caplog) -> None:
    publisher = RecalculoPublisher(
        cola=ColaFake(error=TimeoutError("sin respuesta")),
        cola_persistencia="q-x")
    caplog.set_level(logging.INFO)
    estado = pedir_recalculo(publisher, document_id="doc-7",
                             motivo=MOTIVO_CAMBIO_FECHA, solicitado_por=ACTOR)
    assert estado == "fallo"
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert "[recalculo] no se pudo pedir" in texto
    assert "document_id=doc-7" in texto and "TimeoutError" in texto


def test_f042_r1_pedir_recalculo_con_exito_es_pedido() -> None:
    cola = ColaFake()
    publisher = RecalculoPublisher(cola=cola, cola_persistencia="q-x")
    assert pedir_recalculo(publisher, document_id="d",
                           motivo=MOTIVO_CAMBIO_FECHA,
                           solicitado_por=None) == "pedido"
    assert len(cola.enviados) == 1


def test_f042_r4_pedir_recalculo_sin_publisher_es_sin_cola() -> None:
    assert pedir_recalculo(None, document_id="d", motivo=MOTIVO_CAMBIO_FECHA,
                           solicitado_por=None) == "sin_cola"


def test_f042_r1_la_cola_de_persistencia_por_defecto(entorno) -> None:
    assert Settings(_env_file=None).cola_persistencia == "q-persistencia"
    entorno.setenv("COLA_PERSISTENCIA", "q-otra")
    assert Settings(_env_file=None).cola_persistencia == "q-otra"


# ======================== R1 · guardar la fecha ========================= #

def test_f042_r1_guardar_la_fecha_pide_el_recalculo(montaje) -> None:
    cola = ColaFake()
    publisher = RecalculoPublisher(cola=cola,
                                   cola_persistencia="q-persistencia",
                                   reloj=lambda: RELOJ_FIJO)
    cliente, _cola, fabrica = montaje(publisher=publisher)

    r = _patch(cliente)

    assert r.status_code == 200
    assert r.json() == {"ok": True, "fecha": "2026-10-01",
                        "fecha_int": 20261001, "recalculo": "pedido"}
    assert _fecha_doc(fabrica) == "2026-10-01"
    assert cola.enviados == [("q-persistencia", {
        "tipo": "recalcular", "motivo": "cambio_fecha", "document_id": DOC,
        "solicitado_por": ACTOR,
        "solicitado_at_utc": "2026-10-09T10:30:00+00:00"})]


# =========== R10 · sin inyeccion, el publisher usa `cola_cliente` ======= #

def test_f042_r10_el_publisher_se_monta_sobre_cola_cliente(montaje) -> None:
    cliente, cola, _f = montaje()
    assert _patch(cliente).json()["recalculo"] == "pedido"
    (nombre, mensaje), = cola.enviados
    assert nombre == "q-persistencia"
    assert mensaje["tipo"] == "recalcular"
    assert mensaje["document_id"] == DOC
    assert mensaje["solicitado_por"] == ACTOR


def test_f042_r10_respeta_cola_persistencia(montaje, entorno) -> None:
    entorno.setenv("COLA_PERSISTENCIA", "q-persistencia-pruebas")
    cliente, cola, _f = montaje()
    _patch(cliente)
    assert [n for n, _m in cola.enviados] == ["q-persistencia-pruebas"]


def test_f042_r10_el_publisher_inyectado_manda(montaje) -> None:
    propia = ColaFake()
    cliente, cola, _f = montaje(publisher=RecalculoPublisher(
        cola=propia, cola_persistencia="q-y"))
    _patch(cliente)
    assert cola.enviados == []
    assert [n for n, _m in propia.enviados] == ["q-y"]


# ===================== R2 · publicar tras el commit ===================== #

def test_f042_r2_se_publica_despues_de_confirmar_la_fecha(montaje) -> None:
    eventos: list[str] = []
    fabrica = FabricaSesionSqlite()
    cola = ColaFake(eventos=eventos)
    vista: list[str | None] = []
    # Lo que ve OTRA sesion en el momento de publicar: ya la fecha nueva.
    cola.al_enviar = lambda: vista.append(_fecha_doc(fabrica))
    cliente, _c, _f = montaje(
        cola=cola, fabrica=fabrica,
        repositorio=RepositorioEspia(fabrica, eventos))

    assert _patch(cliente).status_code == 200

    assert eventos == ["update_parte_fecha", "enviar"]
    assert vista == ["2026-10-01"]


# ================ R3 · la cola falla, la fecha se queda ================= #

def test_f042_r3_si_la_cola_falla_la_fecha_queda_guardada(montaje,
                                                          caplog) -> None:
    cliente, _cola, fabrica = montaje(
        cola=ColaFake(error=ConnectionError("cola caida")))
    caplog.set_level(logging.INFO)

    r = _patch(cliente)

    assert r.status_code == 200
    assert r.json() == {"ok": True, "fecha": "2026-10-01",
                        "fecha_int": 20261001, "recalculo": "fallo"}
    assert _fecha_doc(fabrica) == "2026-10-01"
    avisos = [x.getMessage() for x in caplog.records
              if x.levelno == logging.WARNING and "[recalculo]" in
              x.getMessage()]
    assert len(avisos) == 1
    assert f"document_id={DOC}" in avisos[0]
    assert "ConnectionError" in avisos[0]


# ======================= R4 · sin cola configurada ====================== #

def test_f042_r4_sin_cola_guarda_y_lo_dice(montaje) -> None:
    cliente, cola, fabrica = montaje(sin_cola=True)
    assert cola is None

    r = _patch(cliente)

    assert r.status_code == 200
    assert r.json()["recalculo"] == "sin_cola"
    assert _fecha_doc(fabrica) == "2026-10-01"


# =================== R5 · si no se guarda, no se publica ================ #

@pytest.mark.parametrize("fecha", ["no-es-fecha", "2026-02-30", ""])
def test_f042_r5_fecha_invalida_no_publica(montaje, fecha) -> None:
    cliente, cola, fabrica = montaje()
    r = _patch(cliente, fecha=fecha)
    assert r.status_code == 400
    assert "recalculo" not in r.json()
    assert cola.enviados == []
    assert _fecha_doc(fabrica) == "2026-03-02"


def test_f042_r5_parte_inexistente_no_publica(montaje) -> None:
    cliente, cola, _f = montaje()
    r = _patch(cliente, doc="no-existe")
    assert r.status_code == 404
    assert cola.enviados == []


def test_f042_r5_parte_congelado_no_publica(montaje) -> None:
    cliente, cola, fabrica = montaje(aprobado=True)
    r = _patch(cliente)
    assert r.status_code == 409
    assert "recalculo" not in r.json()
    assert cola.enviados == []
    assert _fecha_doc(fabrica) == "2026-03-02"


# =================== R6 · la misma fecha tambien publica ================ #

def test_f042_r6_volver_a_guardar_la_misma_fecha_publica(montaje) -> None:
    cliente, cola, _f = montaje()
    assert _patch(cliente, fecha="2026-03-02").json()["recalculo"] == "pedido"
    assert _patch(cliente, fecha="02/03/2026").json()["recalculo"] == "pedido"
    assert len(cola.enviados) == 2
    assert {m["motivo"] for _n, m in cola.enviados} == {"cambio_fecha"}


# ================= R7-R9 · deshacer un cambio de fecha (DA1) ============ #

def _undo(cliente):
    return cliente.post("/api/undo", headers=CABECERA)


def _id_linea(fabrica) -> int:
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        return s.query(ParteRegistroOrm.id).filter(
            ParteRegistroOrm.document_id == DOC).scalar()


def test_f042_r9_undo_last_devuelve_la_accion_y_los_documentos(
        entorno) -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"estado": None}])
    repo = ParteReviewRepository(fabrica)
    repo.update_parte_fecha(document_id=DOC, fecha_iso="2026-10-01",
                            fecha_int=20261001)
    res = repo.undo_last()
    assert res["ok"] is True
    assert res["action"] == "parte_fecha"
    assert res["document_ids"] == [DOC]
    assert _fecha_doc(fabrica) == "2026-03-02"


def test_f042_r9_otra_accion_sin_documentos(entorno) -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"estado": None}])
    repo = ParteReviewRepository(fabrica)
    assert repo.update_registro(registro_id=_id_linea(fabrica), horas=6.0)
    res = repo.undo_last()
    assert res["ok"] is True
    assert res["action"] == "registro_edit"
    assert res["document_ids"] == []


def test_f042_r9_sin_nada_que_deshacer_no_hay_accion(entorno) -> None:
    fabrica = FabricaSesionSqlite()
    res = ParteReviewRepository(fabrica).undo_last()
    assert res["ok"] is False
    assert "action" not in res


def test_f042_r7_deshacer_la_fecha_pide_el_recalculo(montaje) -> None:
    cliente, cola, fabrica = montaje()
    _patch(cliente)

    r = _undo(cliente)

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert cuerpo["recalculo"] == "pedido"
    assert _fecha_doc(fabrica) == "2026-03-02"
    assert [m["motivo"] for _n, m in cola.enviados] == [
        "cambio_fecha", "deshacer_cambio_fecha"]
    nombre, mensaje = cola.enviados[1]
    assert nombre == "q-persistencia"
    assert mensaje["tipo"] == "recalcular"
    assert mensaje["document_id"] == DOC
    assert mensaje["solicitado_por"] == ACTOR


def test_f042_r7_deshacer_con_la_cola_caida_avisa(montaje, caplog) -> None:
    cola = ColaFake()
    cliente, _c, fabrica = montaje(cola=cola)
    _patch(cliente)
    cola._error = ConnectionError("cola caida")
    caplog.set_level(logging.INFO)

    r = _undo(cliente)

    assert (r.status_code, r.json()["recalculo"]) == (200, "fallo")
    assert _fecha_doc(fabrica) == "2026-03-02"       # el undo SI se aplico
    assert any("[recalculo] no se pudo pedir" in x.getMessage()
               for x in caplog.records if x.levelno == logging.WARNING)


def test_f042_r7_deshacer_sin_cola(montaje) -> None:
    cliente, _cola, fabrica = montaje(sin_cola=True)
    _patch(cliente)
    r = _undo(cliente)
    assert r.json()["recalculo"] == "sin_cola"
    assert _fecha_doc(fabrica) == "2026-03-02"


def test_f042_r8_deshacer_otra_accion_no_publica(montaje) -> None:
    cliente, cola, fabrica = montaje()
    linea = _id_linea(fabrica)
    assert cliente.patch(f"/api/registros/{linea}",
                         json={"horas": 6.0}).status_code == 200

    r = _undo(cliente)

    assert r.status_code == 200 and r.json()["ok"] is True
    assert "recalculo" not in r.json()
    assert cola.enviados == []


def test_f042_r8_sin_nada_que_deshacer_no_publica(montaje) -> None:
    cliente, cola, _f = montaje()
    r = _undo(cliente)
    assert r.status_code == 400
    assert "recalculo" not in r.json()
    assert cola.enviados == []


class RepoUndoFijo(ParteReviewRepository):
    """`undo_last` devuelve lo que se le diga (varios documentos o ninguno)."""

    def __init__(self, fabrica, resultado: dict) -> None:
        super().__init__(fabrica)
        self._resultado = resultado

    def undo_last(self) -> dict:
        return dict(self._resultado)


class PublisherSelectivo:
    """Falla solo para los documentos indicados."""

    def __init__(self, fallan: set[str]) -> None:
        self.pedidos: list[tuple[str, str, str | None]] = []
        self._fallan = fallan

    def pedir(self, *, document_id, motivo, solicitado_por) -> None:
        self.pedidos.append((document_id, motivo, solicitado_por))
        if document_id in self._fallan:
            raise ConnectionError("cola caida")


def test_f042_r7_varios_documentos_y_el_peor_estado(montaje) -> None:
    fabrica = FabricaSesionSqlite()
    publisher = PublisherSelectivo({"doc-b"})
    cliente, _c, _f = montaje(
        fabrica=fabrica, publisher=publisher,
        repositorio=RepoUndoFijo(fabrica, {
            "ok": True, "action": "parte_fecha",
            "document_ids": ["doc-a", "doc-b", "doc-c"]}))

    cuerpo = _undo(cliente).json()

    assert cuerpo["recalculo"] == "fallo"
    assert publisher.pedidos == [
        ("doc-a", "deshacer_cambio_fecha", ACTOR),
        ("doc-b", "deshacer_cambio_fecha", ACTOR),
        ("doc-c", "deshacer_cambio_fecha", ACTOR)]


def test_f042_r7_sin_documentos_no_hay_recalculo(montaje) -> None:
    fabrica = FabricaSesionSqlite()
    publisher = PublisherSelectivo(set())
    cliente, _c, _f = montaje(
        fabrica=fabrica, publisher=publisher,
        repositorio=RepoUndoFijo(fabrica, {
            "ok": True, "action": "parte_fecha", "document_ids": []}))
    assert "recalculo" not in _undo(cliente).json()
    assert publisher.pedidos == []


def test_f042_r8_un_undo_fallido_de_fecha_no_publica(montaje) -> None:
    fabrica = FabricaSesionSqlite()
    publisher = PublisherSelectivo(set())
    cliente, _c, _f = montaje(
        fabrica=fabrica, publisher=publisher,
        repositorio=RepoUndoFijo(fabrica, {
            "ok": False, "action": "parte_fecha", "document_ids": ["doc-a"],
            "error": "x"}))
    r = _undo(cliente)
    assert r.status_code == 400
    assert "recalculo" not in r.json()
    assert publisher.pedidos == []


@pytest.mark.parametrize("estados, peor", [
    (["pedido"], "pedido"), (["sin_cola"], "sin_cola"), (["fallo"], "fallo"),
    (["pedido", "sin_cola"], "sin_cola"), (["sin_cola", "pedido"], "sin_cola"),
    (["pedido", "fallo"], "fallo"), (["fallo", "sin_cola"], "fallo"),
    (["pedido", "pedido"], "pedido"),
])
def test_f042_r7_peor_estado(estados, peor) -> None:
    from infrastructure.persistencia.recalculo_publisher import peor_estado
    assert peor_estado(estados) == peor
    assert peor_estado(iter(estados)) == peor


# ================== R11 · el portal pinta el estado (node) ============== #
# Se EJECUTAN las funciones reales de `static/app.js` (`wireFechaInput`,
# `wireUndo`, `setStatus`...) con un DOM y un `fetch` falsos.

import json as _json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")

TEXTO_PEDIDO = "✓ Guardado · recalculando extras (recarga en 1–2 min)"
TEXTO_FALLO = ("Fecha guardada, pero no se pudo pedir el recálculo de "
               "extras: vuelve a guardar la fecha")
TEXTO_SIN_COLA = "✓ Guardado (sin recálculo automático)"


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _funcion(js: str, nombre: str) -> str:
    m = re.search(r"\n  function " + nombre + r"\(.*?\n  \}\n", js, re.DOTALL)
    assert m, f"app.js no define {nombre}"
    return m.group(0)


def _motivo_http(js: str) -> str:
    m = re.search(r"\nvar MotivoHttp = \(function \(\) \{.*?\n\}\)\(\);\n",
                  js, re.DOTALL)
    assert m, "app.js no define MotivoHttp"
    return m.group(0)


DOM_JS = r"""
"use strict";
var eventos = [];
globalThis.setTimeout = function (f, ms) { eventos.push("timer:" + ms); };
function El(id) {
  this.id = id; this.textContent = ""; this.className = ""; this.title = "";
  this.value = ""; this.disabled = false; this.attrs = {}; this.on = {};
  var self = this;
  this.classList = {
    add: function (c) { self.className = (self.className + " " + c).trim(); },
    remove: function () {},
  };
}
El.prototype.getAttribute = function (k) { return this.attrs[k] || null; };
El.prototype.addEventListener = function (t, f) { this.on[t] = f; };
var els = {};
function el(id) { return (els[id] = els[id] || new El(id)); }
globalThis.document = {
  getElementById: function (id) { return els[id] || null; },
  querySelectorAll: function () { return []; },
};
globalThis.alert = function (m) { eventos.push("alert:" + m); };
globalThis.window = {location: {reload: function () {
  eventos.push("reload"); }}};
function refreshUndo() { eventos.push("refreshUndo"); }
var respuesta = null, peticiones = [];
globalThis.fetch = function (url, opts) {
  peticiones.push([url, opts && opts.method]);
  return Promise.resolve({ok: true, status: 200,
    json: function () { return Promise.resolve(respuesta); }});
};
function tic() { return new Promise(function (r) { setImmediate(r); }); }
async function drenar() { for (var i = 0; i < 10; i++) { await tic(); } }
"""

FECHA_JS = r"""
(async function () {
  var casos = %(casos)s, salida = [];
  for (var i = 0; i < casos.length; i++) {
    respuesta = casos[i]; eventos = []; els = {};
    var inp = el("fecha"), st = el("st-fecha");
    inp.attrs = {"data-document-id": "doc-1", "data-status": "st-fecha"};
    inp.value = "2026-10-01";
    wireFechaInput(inp);
    inp.on.change();
    await drenar();
    salida.push([st.textContent, st.className, eventos.slice()]);
  }
  process.stdout.write(JSON.stringify({salida: salida,
                                       peticiones: peticiones}));
})();
"""

UNDO_JS = r"""
(async function () {
  var casos = %(casos)s, salida = [];
  for (var i = 0; i < casos.length; i++) {
    respuesta = casos[i]; eventos = []; els = {};
    el("undo-widget"); var btn = el("undo-btn");
    wireUndo();
    eventos = [];
    btn.on.click();
    await drenar();
    salida.push(eventos.slice());
  }
  process.stdout.write(JSON.stringify(salida));
})();
"""


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no esta instalado: no se puede ejecutar el JS")
    r = subprocess.run([NODE, "-e", programa], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return _json.loads(r.stdout)


def _guardar_fecha(casos: list) -> dict:
    js = _js()
    programa = (DOM_JS + _motivo_http(js)
                + "".join(_funcion(js, f) for f in (
                    "flashEl", "setStatus", "estadoRecalculo",
                    "wireFechaInput"))
                + FECHA_JS % {"casos": _json.dumps(casos)})
    return _node(programa)


def _deshacer(casos: list) -> list:
    js = _js()
    programa = (DOM_JS + "".join(_funcion(js, f) for f in (
        "estadoRecalculo", "wireUndo"))
        + UNDO_JS % {"casos": _json.dumps(casos)})
    return _node(programa)


BASE = {"ok": True, "fecha": "2026-10-01", "fecha_int": 20261001}


def test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo() -> None:
    res = _guardar_fecha([
        dict(BASE, recalculo="pedido"), dict(BASE, recalculo="fallo"),
        dict(BASE, recalculo="sin_cola"), dict(BASE)])
    pedido, fallo, sin_cola, viejo = res["salida"]
    # `saved` se borra solo a los 1,8 s (`setStatus`); `error` se queda
    # (persistente). El 1,6 s es el destello del input (`flashEl`).
    assert pedido == [TEXTO_PEDIDO, "edit-status saved",
                      ["timer:1600", "timer:1800"]]
    assert fallo == [TEXTO_FALLO, "edit-status error", ["timer:1600"]]
    assert sin_cola == [TEXTO_SIN_COLA, "edit-status saved",
                        ["timer:1600", "timer:1800"]]
    assert viejo == ["✓ Guardado", "edit-status saved",
                     ["timer:1600", "timer:1800"]]
    assert res["peticiones"][0] == ["/api/partes/doc-1/fecha", "PATCH"]


def test_f042_r11_tras_deshacer_con_fallo_avisa_antes_de_recargar() -> None:
    fallo, pedido, sin_clave, sin_cola, con_omitidos = _deshacer([
        {"ok": True, "recalculo": "fallo"},
        {"ok": True, "recalculo": "pedido"},
        {"ok": True},
        {"ok": True, "recalculo": "sin_cola"},
        {"ok": True, "omitidos": 2, "recalculo": "fallo"},
    ])
    assert fallo == ["alert:" + TEXTO_FALLO, "reload"]
    assert pedido == ["reload"]
    assert sin_clave == ["reload"]
    assert sin_cola == ["reload"]
    assert con_omitidos[1:] == ["alert:" + TEXTO_FALLO, "reload"]
    assert con_omitidos[0].startswith("alert:2 fila(s) no se han deshecho")


def test_f042_r11_deshacer_que_falla_no_recarga_ni_avisa() -> None:
    assert _deshacer([{"ok": False, "error": "No hay nada que deshacer."}]) \
        == [["refreshUndo"]]


def test_f042_r11_app_js_es_sintacticamente_valido() -> None:
    if NODE is None:
        pytest.skip("node no esta instalado")
    r = subprocess.run([NODE, "--check", str(APP_JS)], capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
