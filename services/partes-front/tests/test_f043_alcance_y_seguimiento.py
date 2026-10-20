# tests/test_f043_alcance_y_seguimiento.py
"""F-043 · alcance del parte y seguimiento del recalculo (sv4, servidor).

- `estado_seguimiento` (glosario): `sin_seguimiento`, `terminado`,
  `vencido` y `pendiente` (el parte «en espera»), con reloj fijo y el
  borde de `ESPERA_MAX_S` (600 s).
- R2-R4: `GET /api/partes/{id}/alcance` cuenta trabajadores y lineas
  activas sin escribir nada.
- R17: `GET /api/recalculo?ids=...` da el estado de cada documento.

Sin red: repositorio real sobre SQLite y la `ColaFake` de F-042. Datos
sinteticos.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select, update

from application.services import seguimiento_recalculo as seg
from application.services.congelacion import CongeladoError
from application.services.seguimiento_recalculo import (
    ESPERA_MAX_S,
    ESTADO_NO_EXISTE,
    ESTADO_PENDIENTE,
    ESTADO_SIN_SEGUIMIENTO,
    ESTADO_TERMINADO,
    ESTADO_VENCIDO,
    MOTIVO_RECALCULANDO,
    RecalculandoError,
    estado_seguimiento,
)
from infrastructure.database import parte_repository as modulo_repo
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f042_recalculo_fecha import ColaFake

DOC = "doc-f004"
OTRO = "doc-otro"
ACTOR = "revisora@ejemplo.es"
CABECERA = {"X-MS-CLIENT-PRINCIPAL-NAME": ACTOR}
AHORA = datetime(2026, 10, 13, 9, 0, 0, tzinfo=timezone.utc)
PID = "00000000-0000-4000-8000-00000000000a"
PID2 = "00000000-0000-4000-8000-00000000000b"


def _hace(segundos: float) -> str:
    return (AHORA - timedelta(seconds=segundos)).isoformat()


# ========================= estado_seguimiento ========================= #

def test_f043_estado_constantes() -> None:
    assert ESPERA_MAX_S == 600
    assert (ESTADO_SIN_SEGUIMIENTO, ESTADO_TERMINADO, ESTADO_VENCIDO,
            ESTADO_PENDIENTE, ESTADO_NO_EXISTE) == (
        "sin_seguimiento", "terminado", "vencido", "pendiente", "no_existe")


@pytest.mark.parametrize("terminado,at", [
    (None, None), (PID, _hace(5)), (None, _hace(5)), ("x", "basura")])
def test_f043_estado_sin_pedido_es_sin_seguimiento(terminado, at) -> None:
    assert estado_seguimiento(None, terminado, at, AHORA) == \
        ESTADO_SIN_SEGUIMIENTO


@pytest.mark.parametrize("at", [_hace(5), _hace(3600), None, "basura"])
def test_f043_estado_iguales_es_terminado(at) -> None:
    assert estado_seguimiento(PID, PID, at, AHORA) == ESTADO_TERMINADO


@pytest.mark.parametrize("terminado", [None, PID2])
@pytest.mark.parametrize("segundos", [0, 1, 300, ESPERA_MAX_S])
def test_f043_estado_distintos_en_plazo_es_pendiente(terminado,
                                                     segundos) -> None:
    assert estado_seguimiento(PID, terminado, _hace(segundos), AHORA) == \
        ESTADO_PENDIENTE


@pytest.mark.parametrize("terminado", [None, PID2])
@pytest.mark.parametrize("segundos", [ESPERA_MAX_S + 0.001,
                                      ESPERA_MAX_S + 1, 3600])
def test_f043_estado_distintos_fuera_de_plazo_es_vencido(terminado,
                                                         segundos) -> None:
    assert estado_seguimiento(PID, terminado, _hace(segundos), AHORA) == \
        ESTADO_VENCIDO


@pytest.mark.parametrize("at", [None, "", "basura", "2026-13-45T00:00:00"])
def test_f043_estado_hora_ilegible_es_vencido(at) -> None:
    assert estado_seguimiento(PID, None, at, AHORA) == ESTADO_VENCIDO


def test_f043_estado_hora_sin_zona_cuenta_como_utc() -> None:
    sin_zona = (AHORA - timedelta(seconds=30)).replace(tzinfo=None)
    assert estado_seguimiento(PID, None, sin_zona.isoformat(), AHORA) == \
        ESTADO_PENDIENTE
    viejo = (AHORA - timedelta(seconds=601)).replace(tzinfo=None)
    assert estado_seguimiento(PID, None, viejo.isoformat(), AHORA) == \
        ESTADO_VENCIDO


def test_f043_estado_hora_en_otra_zona_se_compara_bien() -> None:
    madrid = timezone(timedelta(hours=2))
    hace_30 = (AHORA - timedelta(seconds=30)).astimezone(madrid)
    assert estado_seguimiento(PID, None, hace_30.isoformat(), AHORA) == \
        ESTADO_PENDIENTE
    hace_700 = (AHORA - timedelta(seconds=700)).astimezone(madrid)
    assert estado_seguimiento(PID, None, hace_700.isoformat(), AHORA) == \
        ESTADO_VENCIDO


def test_f043_estado_recalculando_error_es_un_congelado() -> None:
    exc = RecalculandoError()
    assert isinstance(exc, CongeladoError)
    assert exc.motivo == MOTIVO_RECALCULANDO == (
        "El parte se está recalculando (extras): espera a que termine.")
    assert str(exc) == MOTIVO_RECALCULANDO


# ============================== montaje =============================== #

@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    monkeypatch.setattr(modulo_repo, "_ahora_utc", lambda: AHORA)
    return monkeypatch


@pytest.fixture
def fabrica():
    return FabricaSesionSqlite()


def _cliente(fabrica, *, cola=None, repositorio=None) -> TestClient:
    app = build_app(Settings(_env_file=None),
                    repository=repositorio or ParteReviewRepository(fabrica),
                    cola_cliente=cola)
    return TestClient(app)


def _poner_marca(fabrica, document_id: str, *, pedido: str | None,
                 pedido_at: str | None, terminado: str | None = None,
                 terminado_at: str | None = None) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc=pedido_at,
                          recalculo_terminado_id=terminado,
                          recalculo_terminado_at_utc=terminado_at))
        s.commit()


def _foto(fabrica) -> tuple:
    """Todo lo que una lectura no deberia cambiar."""
    with fabrica.create_session() as s:
        docs = [tuple(getattr(d, c.name) for c in d.__table__.columns)
                for d in s.execute(select(ParteDocumentOrm)
                                   .order_by(ParteDocumentOrm.id)).scalars()]
        regs = [tuple(getattr(r, c.name) for c in r.__table__.columns)
                for r in s.execute(select(ParteRegistroOrm)
                                   .order_by(ParteRegistroOrm.id)).scalars()]
        undo = s.execute(select(func.count()).select_from(UndoLogOrm)
                         ).scalar_one()
    return docs, regs, undo


def _sembrar_dos_trabajadores(fabrica, document_id: str = DOC) -> None:
    """Parte con 2 trabajadores, 3 lineas activas y 1 en papelera."""
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 1.0, "tipo": "extra"},
                            {"horas": 2.0, "borrada": True}],
                  document_id=document_id, fecha="2026-10-01",
                  empleado_ide=77)
    # Segundo trabajador: otra linea del mismo documento, otro empleado.
    with fabrica.create_session() as s:
        s.add(ParteRegistroOrm(
            document_id=document_id, line_index=9, empleado_line_no=2,
            fecha="2026-10-01", fecha_int=20261001, obra_ide=10,
            obra_codigo="0100", obra_nombre="Obra Uno", empleado_ide=78,
            empleado_dni="00000002W", empleado_nombre="Trabajador Dos",
            tipo_hora="normal", horas=8.0, hora_ide=1, hora_codigo="HL01"))
        s.commit()


# ============================= R2-R4 alcance ========================== #

def test_f043_r2_alcance_cuenta_trabajadores_y_lineas_activas(
        entorno, fabrica) -> None:
    _sembrar_dos_trabajadores(fabrica)
    r = _cliente(fabrica).get(f"/api/partes/{DOC}/alcance", headers=CABECERA)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "document_id": DOC,
                        "fecha": "2026-10-01", "trabajadores": 2,
                        "lineas": 3}


def test_f043_r2_alcance_del_repositorio(entorno, fabrica) -> None:
    _sembrar_dos_trabajadores(fabrica)
    assert ParteReviewRepository(fabrica).alcance_parte(DOC) == {
        "document_id": DOC, "fecha": "2026-10-01", "trabajadores": 2,
        "lineas": 3}


def test_f043_r2_alcance_un_trabajador_sin_casar_cuenta_por_nombre(
        entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0, "leido": "Nombre Leido"},
                            {"horas": 1.0, "leido": "Nombre Leido"}],
                  empleado_ide=None)
    assert ParteReviewRepository(fabrica).alcance_parte(DOC)[
        "trabajadores"] == 1


def test_f043_r2_alcance_sin_lineas_activas(entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0, "borrada": True}])
    assert ParteReviewRepository(fabrica).alcance_parte(DOC) == {
        "document_id": DOC, "fecha": "2026-03-02", "trabajadores": 0,
        "lineas": 0}


def test_f043_r2_alcance_no_cuenta_lineas_de_otro_parte(
        entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}])
    sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 8.0}],
                  document_id=OTRO, empleado_ide=90)
    assert ParteReviewRepository(fabrica).alcance_parte(DOC)["lineas"] == 1


def test_f043_r3_alcance_parte_inexistente_404(entorno, fabrica) -> None:
    r = _cliente(fabrica).get("/api/partes/no-existe/alcance",
                              headers=CABECERA)
    assert r.status_code == 404
    assert ParteReviewRepository(fabrica).alcance_parte("no-existe") is None


def test_f043_r3_alcance_parte_en_papelera_404(entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}], doc_en_papelera=True)
    r = _cliente(fabrica).get(f"/api/partes/{DOC}/alcance", headers=CABECERA)
    assert r.status_code == 404


def test_f043_r4_alcance_no_escribe_nada(entorno, fabrica) -> None:
    _sembrar_dos_trabajadores(fabrica)
    antes = _foto(fabrica)
    cola = ColaFake()
    r = _cliente(fabrica, cola=cola).get(f"/api/partes/{DOC}/alcance",
                                         headers=CABECERA)
    assert r.status_code == 200
    assert _foto(fabrica) == antes
    assert cola.enviados == []


# =========================== R17 estados ============================== #

def _sembrar_cuatro(fabrica) -> None:
    for doc, emp in (("d-sin", 1), ("d-term", 2), ("d-venc", 3),
                     ("d-pend", 4)):
        sembrar_parte(fabrica, [{"horas": 8.0}], document_id=doc,
                      empleado_ide=emp)
    _poner_marca(fabrica, "d-term", pedido=PID, pedido_at=_hace(30),
                 terminado=PID, terminado_at=_hace(5))
    _poner_marca(fabrica, "d-venc", pedido=PID, pedido_at=_hace(601))
    _poner_marca(fabrica, "d-pend", pedido=PID2, pedido_at=_hace(30),
                 terminado=PID, terminado_at=_hace(400))


def test_f043_r17_estados_de_varios_documentos(entorno, fabrica) -> None:
    _sembrar_cuatro(fabrica)
    sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-papelera",
                  doc_en_papelera=True)
    r = _cliente(fabrica).get(
        "/api/recalculo?ids=d-sin,d-term,d-venc,d-pend,no-existe,d-papelera",
        headers=CABECERA)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "estados": {
        "d-sin": {"estado": "sin_seguimiento", "pedido_at_utc": None,
                  "terminado_at_utc": None},
        "d-term": {"estado": "terminado", "pedido_at_utc": _hace(30),
                   "terminado_at_utc": _hace(5)},
        "d-venc": {"estado": "vencido", "pedido_at_utc": _hace(601),
                   "terminado_at_utc": None},
        "d-pend": {"estado": "pendiente", "pedido_at_utc": _hace(30),
                   "terminado_at_utc": _hace(400)},
        "no-existe": {"estado": "no_existe", "pedido_at_utc": None,
                      "terminado_at_utc": None},
        "d-papelera": {"estado": "no_existe", "pedido_at_utc": None,
                       "terminado_at_utc": None},
    }}


def test_f043_r17_usa_el_reloj_del_repositorio(entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}])
    _poner_marca(fabrica, DOC, pedido=PID, pedido_at=_hace(30))
    repo = ParteReviewRepository(fabrica)
    assert repo.estados_recalculo([DOC])[DOC]["estado"] == "pendiente"
    entorno.setattr(modulo_repo, "_ahora_utc",
                    lambda: AHORA + timedelta(seconds=600))
    assert repo.estados_recalculo([DOC])[DOC]["estado"] == "vencido"


def test_f043_r17_reloj_real_por_defecto_es_utc_y_de_ahora() -> None:
    antes = datetime.now(timezone.utc)
    ahora = modulo_repo._ahora_utc()
    assert ahora.utcoffset() == timedelta(0)
    assert antes - timedelta(seconds=5) <= ahora <= antes + timedelta(
        seconds=5)


def test_f043_r17_espacios_y_repetidos(entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}])
    r = _cliente(fabrica).get(f"/api/recalculo?ids= {DOC} ,{DOC},,",
                              headers=CABECERA)
    assert r.status_code == 200
    assert list(r.json()["estados"]) == [DOC]


def test_f043_r17_una_sola_consulta(entorno, fabrica) -> None:
    _sembrar_cuatro(fabrica)
    sentencias: list[str] = []

    def _anotar(_conn, _cursor, sentencia, *_a):
        sentencias.append(sentencia)

    event.listen(fabrica.engine, "before_cursor_execute", _anotar)
    try:
        estados = ParteReviewRepository(fabrica).estados_recalculo(
            ["d-sin", "d-term", "d-venc", "d-pend"])
    finally:
        event.remove(fabrica.engine, "before_cursor_execute", _anotar)
    assert len(estados) == 4
    assert len([s for s in sentencias if s.lstrip().upper()
                .startswith("SELECT")]) == 1


def test_f043_r17_sin_ids_no_consulta(entorno, fabrica) -> None:
    assert ParteReviewRepository(fabrica).estados_recalculo([]) == {}


@pytest.mark.parametrize("consulta", ["", "?ids=", "?ids=,,", "?ids=%20"])
def test_f043_r17_sin_ids_422(entorno, fabrica, consulta) -> None:
    r = _cliente(fabrica).get(f"/api/recalculo{consulta}", headers=CABECERA)
    assert r.status_code == 422
    assert r.json()["ok"] is False


def test_f043_r17_cincuenta_ids_valen_y_cincuenta_y_uno_no(
        entorno, fabrica) -> None:
    cliente = _cliente(fabrica)
    ids = [f"d{i}" for i in range(51)]
    r50 = cliente.get("/api/recalculo?ids=" + ",".join(ids[:50]),
                      headers=CABECERA)
    assert r50.status_code == 200
    assert len(r50.json()["estados"]) == 50
    r51 = cliente.get("/api/recalculo?ids=" + ",".join(ids),
                      headers=CABECERA)
    assert r51.status_code == 422
    assert r51.json() == {"ok": False,
                          "error": "Pide entre 1 y 50 documentos."}


def test_f043_r17_no_escribe_nada(entorno, fabrica) -> None:
    _sembrar_cuatro(fabrica)
    antes = _foto(fabrica)
    cola = ColaFake()
    r = _cliente(fabrica, cola=cola).get(
        "/api/recalculo?ids=d-sin,d-term,d-venc,d-pend", headers=CABECERA)
    assert r.status_code == 200
    assert _foto(fabrica) == antes
    assert cola.enviados == []


# ===================== documentos_en_espera (R37) ===================== #

def test_f043_r37_documentos_en_espera_son_los_pendientes(
        entorno, fabrica) -> None:
    _sembrar_cuatro(fabrica)
    repo = ParteReviewRepository(fabrica)
    assert repo.documentos_en_espera(
        ["d-sin", "d-term", "d-venc", "d-pend", "no-existe", None,
         "d-pend"]) == {"d-pend"}
    assert repo.documentos_en_espera([]) == set()
    assert repo.documentos_en_espera([None]) == set()


def test_f043_r37_un_parte_en_papelera_no_esta_en_espera(
        entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}], doc_en_papelera=True)
    _poner_marca(fabrica, DOC, pedido=PID, pedido_at=_hace(30))
    assert ParteReviewRepository(fabrica).documentos_en_espera([DOC]) == set()


def test_f043_r17_el_modulo_no_depende_de_infraestructura() -> None:
    import ast
    import inspect

    arbol = ast.parse(inspect.getsource(seg))
    modulos = {n.module for n in ast.walk(arbol)
               if isinstance(n, ast.ImportFrom)} | {
        a.name for n in ast.walk(arbol) if isinstance(n, ast.Import)
        for a in n.names}
    assert not [m for m in modulos if m and (
        m.startswith("infrastructure") or m.startswith("interface_adapters")
        or m.startswith("sqlalchemy") or m.startswith("fastapi"))]


# ================ R12-R16 · marca de «pedido» de sv4 =================== #

import logging  # noqa: E402

UUID4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _marca(fabrica, document_id: str = DOC) -> tuple:
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, document_id)
        return (doc.recalculo_pedido_id, doc.recalculo_pedido_at_utc,
                doc.recalculo_terminado_id, doc.recalculo_terminado_at_utc)


def _patch(cliente, fecha: str = "2026-10-01", doc: str = DOC):
    return cliente.patch(f"/api/partes/{doc}/fecha", json={"fecha": fecha},
                         headers=CABECERA)


def _undo(cliente):
    return cliente.post("/api/undo", headers=CABECERA)


@pytest.fixture
def parte(entorno, fabrica):
    sembrar_parte(fabrica, [{"horas": 8.5}])
    return fabrica


def test_f043_r12_guardar_la_fecha_marca_el_pedido(parte) -> None:
    cola = ColaFake()
    r = _patch(_cliente(parte, cola=cola))
    assert r.status_code == 200
    assert r.json()["recalculo"] == "pedido"
    pedido, pedido_at, terminado, terminado_at = _marca(parte)
    assert UUID4.match(pedido)
    assert pedido_at == AHORA.isoformat()
    assert (terminado, terminado_at) == (None, None)
    assert ParteReviewRepository(parte).documentos_en_espera([DOC]) == {DOC}


def test_f043_r12_la_marca_esta_confirmada_antes_de_publicar(parte) -> None:
    vistas: list = []
    cola = ColaFake()
    # Lo que veria sv3 al leer la cola: otra sesion, solo lo confirmado.
    cola.al_enviar = lambda: vistas.append(_marca(parte)[0])
    _patch(_cliente(parte, cola=cola))
    assert len(vistas) == 1 and vistas[0] is not None
    assert vistas[0] == _marca(parte)[0]


def test_f043_r12_cada_peticion_es_un_pedido_nuevo(parte) -> None:
    cliente = _cliente(parte, cola=ColaFake())
    _patch(cliente)
    primero = _marca(parte)[0]
    _patch(cliente)
    segundo = _marca(parte)[0]
    assert UUID4.match(primero) and UUID4.match(segundo)
    assert primero != segundo


def test_f043_r12_un_pedido_nuevo_deja_en_espera_un_parte_terminado(
        parte) -> None:
    _poner_marca(parte, DOC, pedido=PID, pedido_at=_hace(100),
                 terminado=PID, terminado_at=_hace(50))
    _patch(_cliente(parte, cola=ColaFake()))
    pedido, _at, terminado, terminado_at = _marca(parte)
    assert pedido != PID
    assert (terminado, terminado_at) == (PID, _hace(50))   # de sv3, intacto
    assert ParteReviewRepository(parte).estados_recalculo([DOC])[DOC][
        "estado"] == "pendiente"


def test_f043_r12_deshacer_la_fecha_marca_otro_pedido(parte) -> None:
    cola = ColaFake()
    cliente = _cliente(parte, cola=cola)
    _patch(cliente)
    del_patch = _marca(parte)[0]
    r = _undo(cliente)
    assert r.status_code == 200 and r.json()["recalculo"] == "pedido"
    del_undo = _marca(parte)[0]
    assert UUID4.match(del_undo) and del_undo != del_patch
    assert [m["motivo"] for _n, m in cola.enviados] == [
        "cambio_fecha", "deshacer_cambio_fecha"]


def test_f043_r12_deshacer_otra_accion_no_marca(parte) -> None:
    cliente = _cliente(parte, cola=ColaFake())
    with parte.create_session() as s:
        reg_id = s.execute(select(ParteRegistroOrm.id)).scalar_one()
    assert cliente.patch(f"/api/registros/{reg_id}", json={"horas": 6.0},
                         headers=CABECERA).status_code == 200
    _undo(cliente)
    assert _marca(parte) == (None, None, None, None)


def test_f043_r12_marcar_en_el_repositorio(parte) -> None:
    repo = ParteReviewRepository(parte)
    antes = _foto(parte)[2]
    assert repo.marcar_recalculo_pedido(DOC, peticion_id=PID) is True
    assert _marca(parte) == (PID, AHORA.isoformat(), None, None)
    assert _foto(parte)[2] == antes                  # sin undo_log
    otra_hora = AHORA + timedelta(seconds=7)
    assert repo.marcar_recalculo_pedido(DOC, peticion_id=PID2,
                                        ahora_utc=otra_hora) is True
    assert _marca(parte) == (PID2, otra_hora.isoformat(), None, None)
    assert repo.marcar_recalculo_pedido("no-existe", peticion_id=PID) is False


def test_f043_r12_marcar_no_mira_la_congelacion(entorno, fabrica) -> None:
    """La marca no es una edicion del usuario: sin guarda de F-004."""
    sembrar_parte(fabrica, [{"horas": 8.0, "estado": "registrado"}],
                  aprobado=True)
    assert ParteReviewRepository(fabrica).marcar_recalculo_pedido(
        DOC, peticion_id=PID) is True


def test_f043_r13_si_publicar_falla_se_anula_la_marca(parte) -> None:
    cola = ColaFake(error=RuntimeError("cola caida"))
    r = _patch(_cliente(parte, cola=cola))
    assert r.status_code == 200
    assert r.json()["recalculo"] == "fallo"
    assert _marca(parte) == (None, None, None, None)
    assert ParteReviewRepository(parte).documentos_en_espera([DOC]) == set()


def test_f043_r13_si_falla_deshacer_tambien_se_anula(parte) -> None:
    cola = ColaFake()
    cliente = _cliente(parte, cola=cola)
    _patch(cliente)
    cola._error = RuntimeError("cola caida")
    r = _undo(cliente)
    assert r.json()["recalculo"] == "fallo"
    assert _marca(parte)[:2] == (None, None)


def test_f043_r13_anular_solo_si_sigue_siendo_suya(parte) -> None:
    repo = ParteReviewRepository(parte)
    _poner_marca(parte, DOC, pedido=PID2, pedido_at=_hace(1),
                 terminado=PID, terminado_at=_hace(9))
    repo.anular_recalculo_pedido(DOC, peticion_id=PID)
    assert _marca(parte) == (PID2, _hace(1), PID, _hace(9))
    repo.anular_recalculo_pedido(DOC, peticion_id=PID2)
    assert _marca(parte) == (None, None, PID, _hace(9))
    repo.anular_recalculo_pedido("no-existe", peticion_id=PID2)


class RepoMarcaRota(ParteReviewRepository):
    def __init__(self, fabrica, *, marcar=None, anular=None) -> None:
        super().__init__(fabrica)
        self._err_marcar = marcar
        self._err_anular = anular

    def marcar_recalculo_pedido(self, document_id, **kw):
        if self._err_marcar is not None:
            raise self._err_marcar
        return super().marcar_recalculo_pedido(document_id, **kw)

    def anular_recalculo_pedido(self, document_id, **kw):
        if self._err_anular is not None:
            raise self._err_anular
        return super().anular_recalculo_pedido(document_id, **kw)


def _avisos(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.levelno == logging.WARNING]


def test_f043_r14_si_marcar_lanza_avisa_y_sigue_como_f042(parte,
                                                          caplog) -> None:
    cola = ColaFake()
    repo = RepoMarcaRota(parte, marcar=OSError("bd caida"))
    with caplog.at_level(logging.WARNING):
        r = _patch(_cliente(parte, cola=cola, repositorio=repo))
    assert r.status_code == 200
    assert r.json() == {"ok": True, "fecha": "2026-10-01",
                        "fecha_int": 20261001, "recalculo": "pedido"}
    assert len(cola.enviados) == 1
    avisos = _avisos(caplog)
    assert len(avisos) == 1
    assert avisos[0].startswith("[recalculo]")
    assert DOC in avisos[0] and "OSError" in avisos[0]
    assert "bd caida" not in avisos[0]
    assert _marca(parte)[:2] == (None, None)


def test_f043_r14_si_marcar_lanza_y_publicar_falla_no_se_anula(
        parte, caplog) -> None:
    cola = ColaFake(error=RuntimeError("cola caida"))
    repo = RepoMarcaRota(parte, marcar=OSError("bd caida"),
                         anular=AssertionError("no hay marca que anular"))
    with caplog.at_level(logging.WARNING):
        r = _patch(_cliente(parte, cola=cola, repositorio=repo))
    assert r.json()["recalculo"] == "fallo"
    assert len(_avisos(caplog)) == 2      # marcar + publicar (F-042)


def test_f043_r14_si_anular_lanza_avisa(parte, caplog) -> None:
    cola = ColaFake(error=RuntimeError("cola caida"))
    repo = RepoMarcaRota(parte, anular=OSError("bd caida"))
    with caplog.at_level(logging.WARNING):
        r = _patch(_cliente(parte, cola=cola, repositorio=repo))
    assert r.status_code == 200
    assert r.json()["recalculo"] == "fallo"
    avisos = [a for a in _avisos(caplog) if "anular" in a]
    assert len(avisos) == 1
    assert avisos[0].startswith("[recalculo]")
    assert DOC in avisos[0] and "OSError" in avisos[0]


def test_f043_r14_parte_inexistente_en_deshacer_no_anula(parte) -> None:
    """`marcar` da False (no hay fila): con fallo no se intenta anular."""
    cola = ColaFake(error=RuntimeError("cola caida"))
    repo = RepoMarcaRota(parte, anular=AssertionError("no debe anular"))

    class RepoUndoAjeno(RepoMarcaRota):
        def undo_last(self) -> dict:
            return {"ok": True, "action": "parte_fecha",
                    "document_ids": ["no-existe"], "description": "x"}

    repo = RepoUndoAjeno(parte, anular=AssertionError("no debe anular"))
    r = _undo(_cliente(parte, cola=cola, repositorio=repo))
    assert r.json()["recalculo"] == "fallo"


def test_f043_r15_sin_cola_no_marca(parte) -> None:
    r = _patch(_cliente(parte, cola=None))
    assert r.json()["recalculo"] == "sin_cola"
    assert _marca(parte) == (None, None, None, None)


def test_f043_r15_sin_cola_deshacer_no_marca(parte) -> None:
    cliente = _cliente(parte, cola=None)
    _patch(cliente)
    assert _undo(cliente).json()["recalculo"] == "sin_cola"
    assert _marca(parte) == (None, None, None, None)


def test_f043_r16_las_respuestas_y_el_mensaje_no_cambian(parte) -> None:
    cola = ColaFake()
    cliente = _cliente(parte, cola=cola)
    assert set(_patch(cliente).json()) == {"ok", "fecha", "fecha_int",
                                           "recalculo"}
    assert set(_undo(cliente).json()) == {
        "ok", "description", "remaining", "omitidos", "action",
        "document_ids", "recalculo"}
    for _nombre, mensaje in cola.enviados:
        assert set(mensaje) == {"tipo", "motivo", "document_id",
                                "solicitado_por", "solicitado_at_utc"}


# ================= R37 · las vistas pintan el parte en espera ========== #

URL_OBRA = "/obras/obr-10?period=2026-03&modo=natural"
URL_PERSONA = "/trabajadores/rec-501?period=2026-03&modo=natural"
MARCA_ESPERA = '<span class="recalculando-marca">recalculando…</span>'


def _fila_html(html: str, registro_id: int) -> str:
    ini = html.index(f'<tr data-registro-id="{registro_id}"')
    return html[ini:html.index("</tr>", ini)]


def _celda_fecha_html(fila: str) -> str:
    ini = fila.index('<td class="cell-fecha">')
    return fila[ini:fila.index("</td>", ini)]


@pytest.fixture
def dos_partes(entorno, fabrica):
    """Mismo trabajador y obra: DOC en espera (pendiente), OTRO no."""
    ids_doc = sembrar_parte(fabrica, [{"horas": 8.0}], fecha="2026-03-02")
    ids_otro = sembrar_parte(fabrica, [{"horas": 7.0}], document_id=OTRO,
                             fecha="2026-03-03")
    _poner_marca(fabrica, DOC, pedido=PID2, pedido_at=_hace(30),
                 terminado=PID)
    _poner_marca(fabrica, OTRO, pedido=PID, pedido_at=_hace(30),
                 terminado=PID)
    return _cliente(fabrica), ids_doc[0], ids_otro[0]


@pytest.mark.parametrize("url", [URL_OBRA, URL_PERSONA])
def test_f043_r37_las_filas_del_parte_en_espera_salen_marcadas(
        dos_partes, url) -> None:
    cliente, reg_doc, reg_otro = dos_partes
    html = cliente.get(url, headers=CABECERA).text
    fila = _fila_html(html, reg_doc)
    assert 'data-recalculando="1"' in fila.split(">", 1)[0]
    assert MARCA_ESPERA in _celda_fecha_html(fila)
    otra = _fila_html(html, reg_otro)
    assert "data-recalculando" not in otra
    assert "recalculando-marca" not in otra


@pytest.mark.parametrize("url", [URL_OBRA, URL_PERSONA])
def test_f043_r37_sin_espera_no_hay_marca(entorno, fabrica, url) -> None:
    sembrar_parte(fabrica, [{"horas": 8.0}])
    _poner_marca(fabrica, DOC, pedido=PID, pedido_at=_hace(601))  # vencido
    html = _cliente(fabrica).get(url, headers=CABECERA).text
    assert "data-recalculando=" not in html
    assert MARCA_ESPERA not in html


def _contenedores(html: str) -> list[str]:
    return re.findall(r"<div[^>]*data-parte-contenido[^>]*>", html)


def test_f043_r37_el_detalle_del_parte_en_espera(dos_partes) -> None:
    cliente, _r1, _r2 = dos_partes
    html = cliente.get(f"/partes/{DOC}", headers=CABECERA).text
    contenedores = _contenedores(html)
    assert len(contenedores) == 2          # cabecera y lineas
    for c in contenedores:
        assert f'data-document-id="{DOC}"' in c
        assert 'data-recalculando="1"' in c
    assert MARCA_ESPERA in html


def test_f043_r37_el_detalle_de_un_parte_que_no_espera(dos_partes) -> None:
    cliente, _r1, _r2 = dos_partes
    html = cliente.get(f"/partes/{OTRO}", headers=CABECERA).text
    contenedores = _contenedores(html)
    assert len(contenedores) == 2
    for c in contenedores:
        assert f'data-document-id="{OTRO}"' in c
        assert "data-recalculando" not in c
    assert MARCA_ESPERA not in html


def test_f043_r37_la_vista_pregunta_por_sus_documentos(entorno,
                                                       fabrica) -> None:
    """Una consulta por vista con los documentos que pinta."""
    sembrar_parte(fabrica, [{"horas": 8.0}], fecha="2026-03-02")
    sembrar_parte(fabrica, [{"horas": 7.0}], document_id=OTRO,
                  fecha="2026-03-03")
    preguntas: list = []

    class Espia(ParteReviewRepository):
        def documentos_en_espera(self, ids):
            ids = list(ids)
            preguntas.append(sorted(set(ids)))
            return super().documentos_en_espera(ids)

    cliente = _cliente(fabrica, repositorio=Espia(fabrica))
    for url in (URL_OBRA, URL_PERSONA):
        cliente.get(url, headers=CABECERA)
    cliente.get(f"/partes/{DOC}", headers=CABECERA)
    assert preguntas == [[DOC, OTRO], [DOC, OTRO], [DOC]]


# ===== R34 · la copia de sv4 de orm_models.py (la que arranca el portal) ===== #

@pytest.mark.parametrize("columna,largo", [
    ("recalculo_pedido_id", 36), ("recalculo_pedido_at_utc", 64),
    ("recalculo_terminado_id", 36), ("recalculo_terminado_at_utc", 64)])
def test_f043_r34_el_ddl_de_sv4_trae_las_cuatro_columnas(columna,
                                                          largo) -> None:
    """El guardian de la raiz no corre en la suite de sv4: esta copia se
    comprueba aqui tambien (patron de `test_f010_r6_..._sv4`)."""
    from infrastructure.database.orm_models import ddl_complementario
    assert (f"ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS {columna} "
            f"VARCHAR({largo})") in ddl_complementario()


def test_f043_r2_r17_los_endpoints_no_salen_en_el_esquema(entorno,
                                                          fabrica) -> None:
    """Internos del portal, como el resto de `/api/...` de F-042/F-024
    (design §3: `include_in_schema=False`)."""
    rutas = _cliente(fabrica).app.openapi()["paths"]
    assert "/api/recalculo" not in rutas
    assert "/api/partes/{document_id}/alcance" not in rutas
