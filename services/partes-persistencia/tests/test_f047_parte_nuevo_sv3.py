# tests/test_f047_parte_nuevo_sv3.py
"""F-047 · R1-R10: sv3 marca el parte nuevo «en espera» y lo da por repartido.

Al guardar un parte nuevo con el conciliador de recurso y el seguimiento
cableados, `save_parte` escribe `recalculo_pedido_id` = id del documento
en el mismo commit (R1); tras las dos conciliaciones, si la de recurso no
lanzó, el pipeline llama a `marcar_terminado(document_id, document_id)`
(R4). Un fallo no se propaga (R5, R6). El UPDATE condicional de F-043
respeta un pedido posterior de sv4 (R7).

`save_parte` real sobre SQLite en memoria (mismo ORM); el pipeline, con
dobles que apuntan eventos. Ni red, ni PostgreSQL, ni Sigrid. Datos
sintéticos.
"""
from __future__ import annotations

import inspect
import logging

import pytest
from sqlalchemy import select

from application.pipelines.persist_parte_pipeline import (
    PersistPartePipeline,
    PersistParteRequest,
)
from application.services.parte_normalizer import ParteNormalizer
from domain.models.parte_records import (
    EmpleadoMatch,
    ExistingParte,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
)
from domain.ports.parte_repository import ParteRepository
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.recalculo_seguimiento import (
    SqlAlchemyRecalculoSeguimiento,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

DOC = "00000000-0000-4000-8000-000000000047"
DNI = "12345678Z"          # el de `sembrar_lineas`: mismo trabajador


class _FabricaContadora(FabricaSesionSqlite):
    """La fábrica de SQLite que cuenta los `commit` de sus sesiones."""

    def __init__(self) -> None:
        super().__init__()
        self.commits = 0

    def create_session(self):
        sesion = super().create_session()
        original = sesion.commit

        def _commit() -> None:
            self.commits += 1
            original()

        sesion.commit = _commit  # type: ignore[method-assign]
        return sesion


def _parte(*, fecha_int: int = 20260320, obra: str = "0100") -> ParteDocumento:
    return ParteDocumento(
        fecha_iso=f"{str(fecha_int)[:4]}-{str(fecha_int)[4:6]}-"
                  f"{str(fecha_int)[6:]}",
        fecha_int=fecha_int, firmado=True,
        obra=ObraMatch(ide=10, codigo=obra, method="codigo"),
        registros=[RegistroNormalizado(
            line_index=0, empleado_line_no=1, tipo_hora="normal", horas=10.0,
            trabajador_nombre_leido="ANA FICTICIA",
            empleado=EmpleadoMatch(ide=None, dni=DNI, reside=501,
                                   method="recurso_dni"))])


def _guardar(repo: SqlAlchemyParteRepository, document_id: str = DOC,
             **extra) -> None:
    repo.save_parte(
        document_id=document_id, parte=_parte(), meta={},
        context={"document": {"sha256": "sha-" + document_id}},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=False, **extra)


def _doc(fabrica, document_id: str = DOC) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.execute(select(ParteDocumentOrm)
                         .where(ParteDocumentOrm.id == document_id)
                         ).scalar_one()


def _seguimiento(doc: ParteDocumentOrm) -> tuple:
    return (doc.recalculo_pedido_id, doc.recalculo_pedido_at_utc,
            doc.recalculo_terminado_id, doc.recalculo_terminado_at_utc)


# ===================== R1, R2, R8, R9 · save_parte ====================== #

def test_f047_r1_save_parte_escribe_el_pedido_en_el_mismo_commit() -> None:
    fabrica = _FabricaContadora()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=DOC)
    doc = _doc(fabrica)
    assert fabrica.commits == 1
    assert doc.recalculo_pedido_id == DOC
    # La hora del pedido es la del guardado (la de `created_at_utc`).
    assert doc.recalculo_pedido_at_utc == doc.created_at_utc
    assert doc.recalculo_pedido_at_utc.endswith("+00:00")
    assert doc.recalculo_terminado_id is None
    assert doc.recalculo_terminado_at_utc is None
    with fabrica.create_session() as s:
        assert len(s.get(ParteDocumentOrm, DOC).registros) == 1


def test_f047_r2_save_parte_sin_pedido_deja_las_cuatro_a_null() -> None:
    fabrica = FabricaSesionSqlite()
    _guardar(SqlAlchemyParteRepository(fabrica))
    assert _seguimiento(_doc(fabrica)) == (None, None, None, None)


def test_f047_r2_save_parte_con_pedido_none_igual_que_sin_el() -> None:
    fabrica = FabricaSesionSqlite()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=None)
    assert _seguimiento(_doc(fabrica)) == (None, None, None, None)


def test_f047_r8_save_parte_reemplazo_solo_marca_el_nuevo() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 8.0}], document_id="doc-viejo")
    with fabrica.create_session() as s:
        viejo = s.get(ParteDocumentOrm, "doc-viejo")
        viejo.recalculo_pedido_id = "pedido-viejo"
        viejo.recalculo_pedido_at_utc = "2026-03-20T08:00:00+00:00"
        s.commit()
    _guardar(SqlAlchemyParteRepository(fabrica), recalculo_pedido_id=DOC)
    viejo = _doc(fabrica, "doc-viejo")
    assert viejo.is_active is False          # el reemplazo ocurrió
    assert _seguimiento(viejo) == ("pedido-viejo",
                                   "2026-03-20T08:00:00+00:00", None, None)
    assert _doc(fabrica).recalculo_pedido_id == DOC


def test_f047_r9_save_parte_parametro_opcional_en_el_puerto() -> None:
    for funcion in (ParteRepository.save_parte,
                    SqlAlchemyParteRepository.save_parte):
        parametro = inspect.signature(funcion).parameters[
            "recalculo_pedido_id"]
        assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
        assert parametro.default is None


# ======================== R1-R7 · el pipeline ========================== #

class _Repo:
    """Lo que la ingesta pide al repositorio; apunta en `eventos`."""

    def __init__(self, eventos: list, existente: ExistingParte | None = None
                 ) -> None:
        self.eventos = eventos
        self.existente = existente
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return self.existente

    def find_empleado_alias(self, _nombre):
        return None

    def save_parte(self, **kwargs) -> None:
        self.eventos.append("save")
        self.guardados.append(kwargs)


class _Conciliador:
    def __init__(self, eventos: list, nombre: str,
                 error: BaseException | None = None) -> None:
        self.eventos, self.nombre, self.error = eventos, nombre, error

    def conciliar_todos(self):
        self.eventos.append(self.nombre)
        if self.error is not None:
            raise self.error
        return {"ok": True}


class _Seguimiento:
    def __init__(self, eventos: list, *, marcado: bool = True,
                 error: BaseException | None = None) -> None:
        self.eventos, self.marcado, self.error = eventos, marcado, error

    def marcar_terminado(self, document_id: str, peticion_id: str) -> bool:
        self.eventos.append(("marcar", document_id, peticion_id))
        if self.error is not None:
            raise self.error
        return self.marcado


def _request(sha: str = "sha-f047") -> PersistParteRequest:
    datos = {"cabecera": {"fecha": "20/03/2026", "obra_numero": "0100"},
             "firma": {"firmado": True},
             "empleados": [{"numero_linea": 1, "nombre": "ANA FICTICIA",
                            "dni": DNI, "horas_ordinarias": 10}]}
    return PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": datos},
        context={"document": {"sha256": sha}})


def _pipeline(eventos: list, *, repo=None, partidas: object = "ok",
              recurso: object = "ok", seguimiento: object = "ok"):
    """Pipeline con dobles: "ok" = un doble que no falla; None = sin
    cablear; una excepcion = el doble la lanza."""
    def _conc(valor, nombre):
        if valor is None:
            return None
        return _Conciliador(eventos, nombre,
                            None if valor == "ok" else valor)

    if seguimiento == "ok":
        seguimiento = _Seguimiento(eventos)
    repo = repo or _Repo(eventos)
    pipeline = PersistPartePipeline(
        repository=repo, normalizer=ParteNormalizer(), matcher_provider=None,
        partida_conciliador=_conc(partidas, "partidas"),
        recurso_conciliador=_conc(recurso, "recurso"),
        recalculo_seguimiento=seguimiento)
    return pipeline, repo


def test_f047_r1_el_pipeline_pasa_el_id_del_documento_como_pedido() -> None:
    eventos: list = []
    pipeline, repo = _pipeline(eventos)
    resultado = pipeline.run(_request())
    (guardado,) = repo.guardados
    assert guardado["recalculo_pedido_id"] == guardado["document_id"]
    assert resultado.document_id == guardado["document_id"]


@pytest.mark.parametrize("falta", ["recurso", "seguimiento", "los_dos"])
def test_f047_r2_sin_conciliador_o_sin_seguimiento_no_hay_pedido(
        falta) -> None:
    eventos: list = []
    pipeline, repo = _pipeline(
        eventos,
        recurso=None if falta in ("recurso", "los_dos") else "ok",
        seguimiento=None if falta in ("seguimiento", "los_dos") else "ok")
    pipeline.run(_request())
    (guardado,) = repo.guardados
    assert guardado["recalculo_pedido_id"] is None
    assert not [e for e in eventos if isinstance(e, tuple)]


def test_f047_r2_sin_seguimiento_concilia_como_hoy() -> None:
    eventos: list = []
    pipeline, _repo = _pipeline(eventos, seguimiento=None)
    pipeline.run(_request())
    assert eventos == ["save", "partidas", "recurso"]


def test_f047_r3_sha256_repetido_ni_guarda_ni_concilia_ni_marca() -> None:
    eventos: list = []
    repo = _Repo(eventos, existente=ExistingParte(
        document_id="doc-existente", source_sha256="sha-f047", registros=3))
    pipeline, _ = _pipeline(eventos, repo=repo)
    resultado = pipeline.run(_request())
    assert eventos == []
    assert repo.guardados == []
    assert resultado.already_existed is True
    assert resultado.document_id == "doc-existente"


def test_f047_r4_orden_guardar_partidas_recurso_marcar() -> None:
    eventos: list = []
    pipeline, _ = _pipeline(eventos)
    resultado = pipeline.run(_request())
    doc = resultado.document_id
    assert eventos == ["save", "partidas", "recurso", ("marcar", doc, doc)]


@pytest.mark.parametrize("partidas", [RuntimeError("partidas rotas"), None],
                         ids=["partidas_fallan", "sin_partidas"])
def test_f047_r4_sin_partidas_o_con_su_fallo_se_marca_igual(
        partidas) -> None:
    eventos: list = []
    pipeline, _ = _pipeline(eventos, partidas=partidas)
    resultado = pipeline.run(_request())
    doc = resultado.document_id
    assert eventos[-2:] == ["recurso", ("marcar", doc, doc)]
    assert resultado.ok is True


@pytest.mark.parametrize("error", [
    RuntimeError("Sigrid caido"),
    TimeoutError("sin candado de F-046 en 300 s"),
], ids=["runtime", "timeout_candado"])
def test_f047_r5_si_la_conciliacion_de_recurso_lanza_no_se_marca(
        error, caplog) -> None:
    caplog.set_level(logging.INFO)
    eventos: list = []
    pipeline, _ = _pipeline(eventos, recurso=error)
    resultado = pipeline.run(_request())
    assert eventos == ["save", "partidas", "recurso"]
    assert resultado.ok is True
    assert resultado.already_existed is False
    avisos = [r for r in caplog.records
              if "conciliacion de recurso fallo" in r.getMessage()]
    assert [r.levelno for r in avisos] == [logging.WARNING]
    assert not [r for r in caplog.records
                if "parte nuevo" in r.getMessage()]


def test_f047_r5_el_resultado_no_cambia_con_la_marca() -> None:
    """Mismo `PersistParteResult` (salvo el id) con y sin seguimiento."""
    con, _ = _pipeline([])
    sin, _ = _pipeline([], seguimiento=None)
    a, b = con.run(_request()), sin.run(_request())
    assert {**vars(a), "document_id": None} == {**vars(b), "document_id": None}


@pytest.mark.parametrize("marcado", [True, False])
def test_f047_r6_info_al_marcar(marcado, caplog) -> None:
    caplog.set_level(logging.INFO)
    eventos: list = []
    pipeline, _ = _pipeline(eventos, seguimiento=_Seguimiento(
        eventos, marcado=marcado))
    doc = pipeline.run(_request()).document_id
    (registro,) = [r for r in caplog.records
                   if "parte nuevo repartido" in r.getMessage()]
    assert registro.levelno == logging.INFO
    assert registro.name == "application.pipelines.persist_parte_pipeline"
    assert registro.getMessage() == (
        f"[persist-parte] parte nuevo repartido document_id={doc} "
        f"marcado={marcado}")


def test_f047_r6_si_marcar_lanza_warning_sin_propagar(caplog) -> None:
    caplog.set_level(logging.INFO)
    eventos: list = []
    pipeline, _ = _pipeline(eventos, seguimiento=_Seguimiento(
        eventos, error=ConnectionError("base caida")))
    resultado = pipeline.run(_request())
    assert resultado.ok is True
    doc = resultado.document_id
    (aviso,) = [r for r in caplog.records
                if "no se pudo marcar el parte nuevo" in r.getMessage()]
    assert aviso.levelno == logging.WARNING
    assert aviso.getMessage() == (
        f"[persist-parte] no se pudo marcar el parte nuevo document_id={doc} "
        "(ConnectionError): sv4 lo dara por vencido.")
    assert not [r for r in caplog.records
                if "parte nuevo repartido" in r.getMessage()]


# ============ R1, R4, R7 · de punta a punta sobre SQLite ================ #

class _ConciliadorQueEscribe:
    """La pasada de recurso; con `pedido`, sv4 escribe ese pedido mientras
    dura (un cambio de fecha o un deshacer)."""

    def __init__(self, fabrica, pedido: str | None = None) -> None:
        self.fabrica, self.pedido = fabrica, pedido

    def conciliar_todos(self):
        if self.pedido is not None:
            with self.fabrica.create_session() as s:
                doc = s.execute(select(ParteDocumentOrm)
                                .where(ParteDocumentOrm.is_active.is_(True))
                                ).scalar_one()
                doc.recalculo_pedido_id = self.pedido
                doc.recalculo_pedido_at_utc = "2026-03-20T09:00:00+00:00"
                s.commit()
        return {}


def _de_punta_a_punta(pedido_de_sv4: str | None):
    fabrica = FabricaSesionSqlite()
    pipeline = PersistPartePipeline(
        repository=SqlAlchemyParteRepository(fabrica),
        normalizer=ParteNormalizer(), matcher_provider=None,
        recurso_conciliador=_ConciliadorQueEscribe(fabrica, pedido_de_sv4),
        recalculo_seguimiento=SqlAlchemyRecalculoSeguimiento(
            fabrica, reloj=lambda: "2026-03-20T09:00:30+00:00"))
    doc = pipeline.run(_request()).document_id
    return _seguimiento(_doc(fabrica, doc)), doc


def test_f047_r4_de_punta_a_punta_el_parte_queda_terminado() -> None:
    (pedido, pedido_at, terminado, terminado_at), doc = _de_punta_a_punta(
        None)
    assert pedido == terminado == doc
    assert pedido_at is not None
    assert terminado_at == "2026-03-20T09:00:30+00:00"


def test_f047_r7_un_pedido_de_sv4_durante_la_pasada_no_se_toca() -> None:
    seguimiento, _doc_id = _de_punta_a_punta("pedido-de-sv4")
    assert seguimiento == ("pedido-de-sv4", "2026-03-20T09:00:00+00:00",
                           None, None)


@pytest.mark.parametrize("valor, esperado", [
    ("ok", True), (None, False), (RuntimeError("caido"), False)],
    ids=["acaba_bien", "sin_cablear", "lanza"])
def test_f047_r4_r5_las_conciliaciones_dicen_si_acabaron_bien(
        valor, esperado) -> None:
    pipeline, _ = _pipeline([], partidas=valor, recurso=valor)
    assert pipeline._conciliar_partidas_safely() is esperado
    assert pipeline._conciliar_recursos_safely() is esperado
