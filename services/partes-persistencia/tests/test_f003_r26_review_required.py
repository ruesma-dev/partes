# tests/test_f003_r26_review_required.py
"""R26 · un parte calculado a ciegas queda marcado para revision.

sv3 no puede bloquear nada: es un worker de cola, y la persistencia del
parte es best-effort. Lo que si puede es dejar constancia. Si el computo
de extras evaluo algun dia con el calendario degradado (cache caducada o
respaldo), el parte queda `review_required=true` y el portal lo ensena
como pendiente de revisar.

La marca solo SUBE: un parte que ya venia marcado por otro motivo (una
extraccion dudosa, por ejemplo) no se desmarca por esta via.
"""
from __future__ import annotations

import logging

import pytest

from application.services.recurso_conciliador import RecursoConciliador
from domain.models.sigrid_models import RecursoRow
from tests.dobles import (
    CalendarioFake,
    CalendarioSinSenal,
    LookupFake,
    RepositorioFake,
    registro,
    reshor_par,
)

LUNES = 20260518        # 2026-05-18
VIERNES = 20260515      # 2026-05-15


def _recursos() -> list[RecursoRow]:
    return [RecursoRow(ide=501, conide=1, cif="12345678Z",
                       restip_res="Oficial", horide_def=100)]


def _conciliador(repositorio, calendario) -> RecursoConciliador:
    return RecursoConciliador(
        repository=repositorio,
        lookup=LookupFake(recursos=_recursos(), reshor=reshor_par(501),
                          hmo={}),
        calendario=calendario, jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )


def _repo(registros) -> RepositorioFake:
    return RepositorioFake(registros)


# ------------------------- se marca lo que toca ------------------------- #

def test_f003_r26_un_dia_degradado_marca_su_parte(caplog) -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    with caplog.at_level(logging.WARNING):
        _conciliador(repositorio, calendario).conciliar_todos()
    assert repositorio.review_required == [["doc-A"]]
    assert "revision" in caplog.text.lower()


def test_f003_r26_sin_degradacion_no_se_marca_nada() -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    _conciliador(repositorio, CalendarioFake(set())).conciliar_todos()
    assert repositorio.review_required == []


def test_f003_r26_solo_los_partes_afectados() -> None:
    """El doc-B se resolvio bien: no tiene por que ir a revision."""
    repositorio = _repo([
        registro(1, fecha_int=LUNES, horas=10.0, document_id="doc-A"),
        registro(2, fecha_int=VIERNES, horas=10.0, document_id="doc-B"),
    ])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    _conciliador(repositorio, calendario).conciliar_todos()
    assert repositorio.review_required == [["doc-A"]]


def test_f003_r26_marca_todos_los_partes_del_grupo() -> None:
    """Un (recurso, dia) puede venir de dos partes distintos (dos obras):
    los dos se calcularon con el mismo calendario dudoso."""
    repositorio = _repo([
        registro(1, fecha_int=LUNES, horas=6.0, document_id="doc-A",
                 obra_ide=10),
        registro(2, fecha_int=LUNES, horas=6.0, document_id="doc-B",
                 obra_ide=20),
    ])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    _conciliador(repositorio, calendario).conciliar_todos()
    assert repositorio.review_required == [["doc-A", "doc-B"]]


def test_f003_r26_no_se_repiten_los_document_id() -> None:
    repositorio = _repo([
        registro(1, fecha_int=LUNES, horas=6.0, document_id="doc-A"),
        registro(2, fecha_int=VIERNES, horas=6.0, document_id="doc-A"),
    ])
    calendario = CalendarioFake(set(), degradados={"2026-05-18",
                                                   "2026-05-15"})
    _conciliador(repositorio, calendario).conciliar_todos()
    assert repositorio.review_required == [["doc-A"]]


# ------------------------ R27 · sin Sesame, nada ------------------------ #

def test_f003_r27_un_calendario_sin_senal_no_marca_nada() -> None:
    """`JsonCalendarioLaboral` no ofrece `consumir_degradacion`: el
    conciliador la busca por duck-typing y sigue como siempre."""
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    _conciliador(repositorio, CalendarioSinSenal(set())).conciliar_todos()
    assert repositorio.review_required == []


def test_f003_r27_sin_calendario_cableado_no_marca_nada() -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    _conciliador(repositorio, None).conciliar_todos()
    assert repositorio.review_required == []


def test_f003_r26_un_repositorio_sin_el_metodo_no_rompe_nada() -> None:
    """Compatibilidad: el conciliador no puede caerse por la senal."""
    class RepoViejo(RepositorioFake):
        marcar_review_required = None   # type: ignore[assignment]

    repositorio = RepoViejo([registro(1, fecha_int=LUNES, horas=10.0,
                                      document_id="doc-A")])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    resumen = _conciliador(repositorio, calendario).conciliar_todos()
    assert resumen["registros"] == 1
    # Y no se cuenta como marcado, que seria mentir en el resumen.
    assert resumen["partes_a_revisar"] == 0


def test_f003_r26_si_el_marcado_falla_no_se_cuenta_ni_se_propaga() -> None:
    class RepoRoto(RepositorioFake):
        def marcar_review_required(self, document_ids) -> int:
            raise RuntimeError("la BBDD no responde")

    repositorio = RepoRoto([registro(1, fecha_int=LUNES, horas=10.0,
                                     document_id="doc-A")])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    resumen = _conciliador(repositorio, calendario).conciliar_todos()
    assert resumen["partes_a_revisar"] == 0
    assert resumen["extras_reclasificadas"] == 1   # el resto siguio


def test_f003_r26_el_resumen_cuenta_los_partes_marcados() -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    resumen = _conciliador(repositorio, calendario).conciliar_todos()
    assert resumen["partes_a_revisar"] == 1


def test_f003_r26_sin_degradacion_el_resumen_cuenta_cero() -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    resumen = _conciliador(repositorio,
                           CalendarioFake(set())).conciliar_todos()
    assert resumen["partes_a_revisar"] == 0


def test_f003_r26_la_senal_no_se_arrastra_entre_pasadas() -> None:
    repositorio = _repo([registro(1, fecha_int=LUNES, horas=10.0,
                                  document_id="doc-A")])
    calendario = CalendarioFake(set(), degradados={"2026-05-18"})
    conciliador = _conciliador(repositorio, calendario)
    conciliador.conciliar_todos()
    calendario._degradados = set()      # Sesame vuelve
    conciliador.conciliar_todos()
    assert repositorio.review_required == [["doc-A"]]   # solo la primera


# ------------------------ el repositorio de verdad ---------------------- #

def test_f003_r26_fetch_registros_trae_el_document_id() -> None:
    """Sin el `document_id` en el dict no habria a que parte marcar."""
    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )
    import inspect

    fuente = inspect.getsource(
        SqlAlchemyParteRepository.fetch_registros_para_recurso)
    assert '"document_id"' in fuente


def test_f003_r26_marcar_review_required_solo_sube_el_flag() -> None:
    """Sobre SQLite en memoria con el ORM real."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from infrastructure.database.orm_models import Base, ParteDocumentOrm
    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )

    class Fabrica:
        def __init__(self) -> None:
            self.engine = create_engine(
                "sqlite://", future=True, poolclass=StaticPool,
                connect_args={"check_same_thread": False})
            Base.metadata.create_all(self.engine)
            self._sm = sessionmaker(bind=self.engine, expire_on_commit=False,
                                    future=True)

        def create_session(self):
            return self._sm()

    fabrica = Fabrica()
    with fabrica.create_session() as s:
        for doc_id, marcado in (("doc-A", False), ("doc-B", True),
                                ("doc-C", False)):
            s.add(ParteDocumentOrm(
                id=doc_id, source_filename="p.pdf",
                source_mime_type="application/pdf", source_sha256="sha" + doc_id,
                fecha="2026-05-18", fecha_int=20260518,
                created_at_utc="2026-05-18T08:00:00+00:00",
                review_required=marcado))
        s.commit()

    repositorio = SqlAlchemyParteRepository(fabrica)
    assert repositorio.marcar_review_required(["doc-A", "doc-B"]) == 1

    with fabrica.create_session() as s:
        estados = {d: s.get(ParteDocumentOrm, d).review_required
                   for d in ("doc-A", "doc-B", "doc-C")}
    assert estados == {"doc-A": True, "doc-B": True, "doc-C": False}


def test_f003_r26_marcar_review_required_tolera_lo_raro() -> None:
    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )

    class FabricaMuda:
        def create_session(self):
            raise AssertionError("no deberia abrirse sesion")

    repositorio = SqlAlchemyParteRepository(FabricaMuda())
    assert repositorio.marcar_review_required([]) == 0
    assert repositorio.marcar_review_required([None, ""]) == 0
