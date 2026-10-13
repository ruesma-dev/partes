# tests/test_f043_seguimiento_sv3.py
"""F-043 · R27-R33: sv3 marca «terminado» el recalculo que ha hecho.

sv4 escribe en el documento un `recalculo_pedido_id` (uuid4) ANTES de
publicar el recalculo de F-042. sv3 lo lee antes de la pasada y, si la
pasada acaba sin excepcion, lo copia a `recalculo_terminado_id` solo si el
documento sigue con ese pedido (UPDATE condicional). sv4 compara los dos
para saber si el parte sigue «en espera».

Adaptador sobre SQLite en memoria (mismo ORM) y handler con dobles. Ni
red, ni PostgreSQL, ni Sigrid. Datos sinteticos.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest
from sqlalchemy import select, update

from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.recalculo_seguimiento import (
    SqlAlchemyRecalculoSeguimiento,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

DOC = "doc-seg"
PEDIDO_A = "00000000-0000-4000-8000-00000000000a"
PEDIDO_B = "00000000-0000-4000-8000-00000000000b"
AHORA = "2026-10-13T09:00:00+00:00"


def _reloj() -> str:
    return AHORA


@pytest.fixture
def fabrica():
    fab = FabricaSesionSqlite()
    sembrar_lineas(fab, [{"horas": 8.0}], document_id=DOC)
    return fab


def _poner_pedido(fabrica, pedido: str | None,
                  document_id: str = DOC) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc="2026-10-13T08:59:00+00:00"))
        s.commit()


def _marca(fabrica, document_id: str = DOC) -> tuple:
    with fabrica.create_session() as s:
        doc = s.execute(select(ParteDocumentOrm)
                        .where(ParteDocumentOrm.id == document_id)
                        ).scalar_one()
        return (doc.recalculo_pedido_id, doc.recalculo_terminado_id,
                doc.recalculo_terminado_at_utc)


# ============================ adaptador ================================ #

def test_f043_r27_adaptador_lee_el_pedido_actual(fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual(DOC) == PEDIDO_A


def test_f043_r27_adaptador_sin_pedido_es_none(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual(DOC) is None


def test_f043_r27_adaptador_documento_inexistente_es_none(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.pedido_actual("no-existe") is None


def test_f043_r28_adaptador_marca_el_pedido_que_sigue_vigente(
        fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica) == (PEDIDO_A, PEDIDO_A, AHORA)


def test_f043_r32_adaptador_no_marca_si_hay_un_pedido_mas_nuevo(
        fabrica) -> None:
    """sv4 escribio B durante la pasada que leyo A: A no se marca."""
    _poner_pedido(fabrica, PEDIDO_B)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is False
    assert _marca(fabrica) == (PEDIDO_B, None, None)


def test_f043_r32_adaptador_repetir_es_idempotente(fabrica) -> None:
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica) == (PEDIDO_A, PEDIDO_A, AHORA)


def test_f043_r32_adaptador_un_marcado_viejo_no_pisa_el_nuevo(
        fabrica) -> None:
    """Desorden: B ya terminado; un mensaje con A llega tarde y no toca."""
    _poner_pedido(fabrica, PEDIDO_B)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_B) is True
    assert seg.marcar_terminado(DOC, PEDIDO_A) is False
    assert _marca(fabrica) == (PEDIDO_B, PEDIDO_B, AHORA)


def test_f043_r28_adaptador_documento_inexistente_no_marca(fabrica) -> None:
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado("no-existe", PEDIDO_A) is False


def test_f043_r28_adaptador_solo_toca_su_documento(fabrica) -> None:
    sembrar_lineas(fabrica, [{"horas": 8.0}], document_id="doc-otro")
    _poner_pedido(fabrica, PEDIDO_A)
    _poner_pedido(fabrica, PEDIDO_A, document_id="doc-otro")
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    assert _marca(fabrica, "doc-otro") == (PEDIDO_A, None, None)


def test_f043_r28_adaptador_reloj_por_defecto_es_utc_iso(fabrica) -> None:
    from datetime import datetime, timedelta, timezone

    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica)
    antes = datetime.now(timezone.utc)
    assert seg.marcar_terminado(DOC, PEDIDO_A) is True
    marcado = datetime.fromisoformat(_marca(fabrica)[2])
    assert marcado.utcoffset() == timedelta(0)
    assert antes - timedelta(seconds=5) <= marcado <= antes + timedelta(
        seconds=5)


# ============================== handler ================================ #

from interface_adapters.workers.despacho import construir_handler  # noqa: E402


class SeguimientoFake:
    """`pedido_actual` / `marcar_terminado` apuntando en `eventos`."""

    def __init__(self, eventos: list, *, pedido: str | None = PEDIDO_A,
                 error_leer: Exception | None = None,
                 error_marcar: Exception | None = None,
                 marcado: bool = True) -> None:
        self.eventos = eventos
        self.pedido = pedido
        self.error_leer = error_leer
        self.error_marcar = error_marcar
        self.marcado = marcado

    def pedido_actual(self, document_id: str) -> str | None:
        self.eventos.append(("leer", document_id))
        if self.error_leer is not None:
            raise self.error_leer
        return self.pedido

    def marcar_terminado(self, document_id: str, peticion_id: str) -> bool:
        self.eventos.append(("marcar", document_id, peticion_id))
        if self.error_marcar is not None:
            raise self.error_marcar
        return self.marcado


class ConciliadorConEventos:
    def __init__(self, eventos: list, *,
                 error: Exception | None = None) -> None:
        self.eventos = eventos
        self.error = error

    def conciliar_todos(self) -> dict:
        self.eventos.append(("pasada",))
        if self.error is not None:
            raise self.error
        return {"registros": 1}


class NadaDeIngesta:
    def descargar(self, *_a):
        raise AssertionError("un recalculo no descarga blobs")

    def run(self, *_a):
        raise AssertionError("un recalculo no ejecuta el pipeline")


def _mensaje(**extra) -> dict:
    mensaje = {"tipo": "recalcular", "motivo": "cambio_fecha",
               "document_id": DOC, "solicitado_por": "revisor@ejemplo",
               "solicitado_at_utc": "2026-10-13T08:59:00+00:00"}
    mensaje.update(extra)
    return mensaje


def _handler(eventos: list, *, seguimiento="defecto",
             conciliador="defecto", **kw_seg):
    if seguimiento == "defecto":
        seguimiento = SeguimientoFake(eventos, **kw_seg)
    if conciliador == "defecto":
        conciliador = ConciliadorConEventos(eventos)
    nada = NadaDeIngesta()
    return construir_handler(
        blob=nada, pipeline=nada, recurso_conciliador=conciliador,
        contenedor_input="in-x", contenedor_envelopes="env-x",
        recalculo_seguimiento=seguimiento)


def test_f043_r27_r28_lee_antes_y_marca_despues_de_la_pasada(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos)(_mensaje())
    assert eventos == [("leer", DOC), ("pasada",),
                       ("marcar", DOC, PEDIDO_A)]
    assert (f"[sv3-worker] recalculo terminado document_id={DOC} "
            "marcado=True") in caplog.text


def test_f043_r28_lo_que_dice_el_adaptador_va_al_log(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, marcado=False)(_mensaje())
    assert ("marcar", DOC, PEDIDO_A) in eventos
    assert (f"[sv3-worker] recalculo terminado document_id={DOC} "
            "marcado=False") in caplog.text


def test_f043_r28_sin_pedido_no_marca(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, pedido=None)(_mensaje())
    assert eventos == [("leer", DOC), ("pasada",)]
    assert "[sv3-worker] recalculo terminado" not in caplog.text


def test_f043_r29_si_la_pasada_lanza_no_marca_y_propaga() -> None:
    eventos: list = []
    conciliador = ConciliadorConEventos(eventos, error=RuntimeError("sigrid"))
    with pytest.raises(RuntimeError, match="sigrid"):
        _handler(eventos, conciliador=conciliador)(_mensaje())
    assert eventos == [("leer", DOC), ("pasada",)]


def test_f043_r30_si_leer_lanza_recalcula_sin_marcar(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, error_leer=OSError("bd caida"))(_mensaje())
    assert eventos == [("leer", DOC), ("pasada",)]
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert texto.startswith("[sv3-worker]")
    assert DOC in texto and "OSError" in texto
    assert "bd caida" not in texto


def test_f043_r30_si_marcar_lanza_avisa_y_consume(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, error_marcar=OSError("bd caida"))(_mensaje())
    assert eventos == [("leer", DOC), ("pasada",),
                       ("marcar", DOC, PEDIDO_A)]
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert texto.startswith("[sv3-worker]")
    assert DOC in texto and "OSError" in texto
    assert "[sv3-worker] recalculo terminado" not in caplog.text


def test_f043_r31_sin_seguimiento_es_f042(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, seguimiento=None)(_mensaje())
    assert eventos == [("pasada",)]
    assert "[sv3-worker] recalculo terminado" not in caplog.text
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_f043_r31_sin_seguimiento_por_defecto_es_f042() -> None:
    """`recalculo_seguimiento` es opcional: la firma de F-042 vale."""
    eventos: list = []
    nada = NadaDeIngesta()
    handler = construir_handler(
        blob=nada, pipeline=nada,
        recurso_conciliador=ConciliadorConEventos(eventos),
        contenedor_input="in-x", contenedor_envelopes="env-x")
    handler(_mensaje())
    assert eventos == [("pasada",)]


def test_f043_r31_sin_conciliador_ni_lee_ni_marca(caplog) -> None:
    eventos: list = []
    with caplog.at_level(logging.INFO):
        _handler(eventos, conciliador=None)(_mensaje())
    assert eventos == []
    assert "Sigrid no esta cableado" in caplog.text


@pytest.mark.parametrize("document_id", [None, 7, ["doc"], {"id": DOC}])
def test_f043_r31_document_id_que_no_es_texto_no_lee_ni_marca(
        document_id) -> None:
    eventos: list = []
    _handler(eventos)(_mensaje(document_id=document_id))
    assert eventos == [("pasada",)]


def test_f043_r31_sin_document_id_no_lee_ni_marca() -> None:
    eventos: list = []
    mensaje = _mensaje()
    del mensaje["document_id"]
    _handler(eventos)(mensaje)
    assert eventos == [("pasada",)]


def test_f043_r31_la_ingesta_no_lee_ni_marca() -> None:
    """Un mensaje de sv2 no toca el seguimiento."""
    eventos: list = []

    class Blob:
        def descargar(self, _contenedor, nombre):
            return b"{}" if nombre.endswith(".json") else b"%PDF"

    class Pipeline:
        def run(self, _peticion):
            from dataclasses import dataclass

            @dataclass
            class Resultado:
                document_id: str = "doc-1"
            return Resultado()

    handler = construir_handler(
        blob=Blob(), pipeline=Pipeline(),
        recurso_conciliador=ConciliadorConEventos(eventos),
        contenedor_input="in-x", contenedor_envelopes="env-x",
        recalculo_seguimiento=SeguimientoFake(eventos))
    handler({"document_id": "doc-1"})
    assert eventos == []


def test_f043_r32_ciclo_real_un_pedido_nuevo_durante_la_pasada_no_se_marca(
        fabrica) -> None:
    """Con el adaptador real: sv4 escribe B mientras sv3 recalcula A."""
    _poner_pedido(fabrica, PEDIDO_A)
    seg = SqlAlchemyRecalculoSeguimiento(fabrica, reloj=_reloj)

    class PasadaConPedidoNuevo:
        def conciliar_todos(self):
            _poner_pedido(fabrica, PEDIDO_B)
            return {}

    nada = NadaDeIngesta()
    handler = construir_handler(
        blob=nada, pipeline=nada, recurso_conciliador=PasadaConPedidoNuevo(),
        contenedor_input="in-x", contenedor_envelopes="env-x",
        recalculo_seguimiento=seg)
    handler(_mensaje())
    assert _marca(fabrica) == (PEDIDO_B, None, None)
    # El mensaje de B (o su reintento) si lo marca.
    handler(_mensaje())
    assert _marca(fabrica) == (PEDIDO_B, PEDIDO_B, AHORA)


# ===================== R33 · cableado de sv3 =========================== #

RAIZ_SV3 = Path(__file__).resolve().parents[1]


class _FabricaDoble:
    def __init__(self, **_kwargs) -> None:
        pass


class _RepoDoble:
    def __init__(self, _fabrica) -> None:
        pass

    def initialize(self) -> None:
        return None


def test_f043_r33_build_app_expone_el_seguimiento(monkeypatch) -> None:
    from config.settings import Settings
    from interface_adapters.api import app as modulo_app

    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setattr(modulo_app, "SessionFactory", _FabricaDoble)
    monkeypatch.setattr(modulo_app, "SqlAlchemyParteRepository", _RepoDoble)
    monkeypatch.setattr(modulo_app, "SqlAlchemyJornadaRepository", _RepoDoble)
    monkeypatch.setattr(modulo_app, "construir_casado_sigrid",
                        lambda *_a, **_k: (None, None, None, None))
    app = modulo_app.build_app(Settings(_env_file=None))
    seg = app.state.recalculo_seguimiento
    assert isinstance(seg, SqlAlchemyRecalculoSeguimiento)
    assert isinstance(seg._session_factory, _FabricaDoble)


def _llamada_construir_handler(arbol: ast.AST) -> ast.Call:
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "construir_handler"):
            return nodo
    raise AssertionError("main_worker no llama a construir_handler")


def test_f043_r33_main_worker_pasa_el_seguimiento() -> None:
    fuente = (RAIZ_SV3 / "main_worker.py").read_text(encoding="utf-8")
    llamada = _llamada_construir_handler(ast.parse(fuente))
    argumentos = {k.arg: ast.unparse(k.value) for k in llamada.keywords}
    assert "recalculo_seguimiento" in argumentos
    assert "recalculo_seguimiento" in argumentos["recalculo_seguimiento"]
    assert "app.state" in argumentos["recalculo_seguimiento"]


def test_f043_r33_main_worker_entrega_el_seguimiento_al_handler(
        monkeypatch) -> None:
    from types import SimpleNamespace

    import main_worker

    recibido: dict = {}
    seg = object()

    def _construir(**kwargs):
        recibido.update(kwargs)
        return lambda _p: None

    class Cola:
        def asegurar_colas(self, _n):
            pass

        def consumir(self, _cola, _handler):
            pass

    class Blob:
        def asegurar_contenedores(self, _n):
            pass

    ajustes = SimpleNamespace(
        log_dir="logs", log_level="INFO",
        colas_connection_string="UseDevelopmentStorage=true",
        colas_account_url=None, blobs_connection_string=None,
        blobs_account_url=None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *_a: None)
    monkeypatch.setattr(main_worker, "construir_cola_cliente",
                        lambda **_k: Cola())
    monkeypatch.setattr(main_worker, "construir_blob_cliente",
                        lambda **_k: Blob())
    monkeypatch.setattr(main_worker, "build_app", lambda _s: SimpleNamespace(
        state=SimpleNamespace(pipeline=None, recurso_conciliador=None,
                              recalculo_seguimiento=seg)))
    monkeypatch.setattr(main_worker, "construir_handler", _construir)
    assert main_worker.main() == 0
    assert recibido["recalculo_seguimiento"] is seg


# ===== R34 · la copia de sv3 de orm_models.py (la que arranca el worker) ===== #

@pytest.mark.parametrize("columna,largo", [
    ("recalculo_pedido_id", 36), ("recalculo_pedido_at_utc", 64),
    ("recalculo_terminado_id", 36), ("recalculo_terminado_at_utc", 64)])
def test_f043_r34_el_ddl_de_sv3_trae_las_cuatro_columnas(columna,
                                                          largo) -> None:
    """El guardian de la raiz no corre en la suite de sv3: esta copia se
    comprueba aqui tambien."""
    from infrastructure.database.orm_models import ddl_complementario
    assert (f"ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS {columna} "
            f"VARCHAR({largo})") in ddl_complementario()
