# tests/test_f036_pipeline.py
"""F-036 · R6, R13-R17, R22: el casado contra recursos en la ingesta (sv3).

`PersistPartePipeline._casar_trabajador` delega en `casar_trabajador`:

  - R6: el alias se consulta en la base SOLO si el DNI no decide.
  - R13-R14: lo que queda guardado en la linea (`parte_registros`).
  - R15: la pasada del conciliador que corre tras guardar elige el MISMO
    recurso que eligio el casado (de punta a punta: pipeline real,
    repositorio real sobre SQLite y conciliador real).
  - R16: `recurso_*`, `hmo_ide` y `parte_estado` solo los escribe el
    conciliador.
  - R17: sin `fichas_de_recurso` ni `Matchers.recursos`.
  - R22: un parte ya guardado no se re-casa al ingerir otro.

Sin red ni PostgreSQL: SQLite en memoria y maestros SINTETICOS.
"""
from __future__ import annotations

import dataclasses
import importlib.util
from datetime import date
from pathlib import Path

import pytest

from application.pipelines.persist_parte_pipeline import (
    PersistPartePipeline,
    PersistParteRequest,
)
from application.services import text_match as tm
from application.services.parte_normalizer import ParteNormalizer
from application.services.recurso_conciliador import RecursoConciliador
from application.services.sigrid_matcher_provider import (
    Matchers,
    SigridMatcherProvider,
)
from domain.models.sigrid_models import (
    EmpleadoRow,
    EmpresaRow,
    ObraRow,
    RecursoRow,
    TipoHoraRow,
)
from infrastructure.database.orm_models import EmpleadoAliasOrm, ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, reshor_par

RAIZ_SV3 = Path(__file__).resolve().parents[1]

DNI_A = "11111111H"      # ficha en la 1, un recurso enlazado
DNI_B = "22222222J"      # ficha en la 1, dos recursos: desempata el reside
DNI_C = "33333333P"      # ficha en la 1 y recurso SIN enlazar en la 28 (R7)
DNI_E = "55555555K"      # sin ficha: recurso por cif en la 28
DNI_F = "44444444A"      # ficha cuyo recurso tiene OTRO cif (DA1)
CIF_F = "40404040G"
DNI_H = "77777777B"      # dos recursos por cif en la 1, sin desempate


def _ficha(ide, nombre, dni, reside, empresa=1):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre, dni=dni,
                       reside=reside, empresa=empresa, fecbaj=0)


def _rec(ide, nombre, *, cif=None, conide=None, empresa=1, cla=1):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=0, codigo=f"MO/{ide}", nombre=nombre, cla=cla)


FICHAS = [
    _ficha(10, "ANA UNO", DNI_A, 910),
    _ficha(20, "BEA DOS", DNI_B, 921),
    _ficha(30, "CARLOS TRES", DNI_C, 930),
    _ficha(60, "FELIX SEIS", DNI_F, 965),
]
RECURSOS = [
    _rec(910, "UNO, ANA", conide=10),
    _rec(920, "DOS, BEA", conide=20),
    _rec(921, "DOS, BEA", conide=20),
    _rec(930, "TRES, CARLOS", conide=30),
    _rec(950, "TRES, CARLOS", cif=DNI_C, empresa=28),
    _rec(960, "EVA SINFICHA", cif=DNI_E, empresa=28),
    _rec(965, "SEIS, FELIX", cif=CIF_F, conide=60),
    _rec(980, "HUGO IGUAL", cif=DNI_H),
    _rec(981, "HUGO IGUAL", cif=DNI_H),
]
OBRAS = [ObraRow(ide=100, codigo="0100", nombre="Uno", empresa=1),
         ObraRow(ide=200, codigo="0200", nombre="Veintiocho", empresa=28)]
TIPOS = [TipoHoraRow(ide=1, codigo="HL01", descripcion="Hora laborable",
                     ext=0, pre=None, prenom=None),
         TipoHoraRow(ide=2, codigo="HE01", descripcion="Hora extra", ext=1,
                     pre=None, prenom=None)]


class Lookup:
    """Sigrid en memoria: lo que leen el proveedor y el conciliador."""

    def __init__(self, fichas=FICHAS, recursos=RECURSOS) -> None:
        self.fichas, self.recursos = list(fichas), list(recursos)

    def fetch_empleados(self):
        return list(self.fichas)

    def fetch_obras(self):
        return list(OBRAS)

    def fetch_tipos_hora(self):
        return list(TIPOS)

    def fetch_recursos(self):
        return list(self.recursos)

    def fetch_empresas(self):
        return [EmpresaRow(numemp=1, nombre="UNO"),
                EmpresaRow(numemp=28, nombre="VEINTIOCHO")]

    def fetch_reshor(self):
        return [f for r in self.recursos for f in reshor_par(r.ide)]

    def fetch_hmo_obra(self, _obra_ide):
        return []


def _montar(lookup=None, fabrica=None):
    lookup = lookup or Lookup()
    fabrica = fabrica or FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    proveedor = SigridMatcherProvider(
        lookup=lookup, empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01")
    conciliador = RecursoConciliador(
        repository=repo, lookup=lookup, indice_provider=proveedor.indice,
        hoy=lambda: date(2026, 9, 15))
    pipeline = PersistPartePipeline(
        repository=repo, normalizer=ParteNormalizer(),
        matcher_provider=proveedor, recurso_conciliador=conciliador,
        hoy=lambda: date(2026, 9, 15))
    return pipeline, fabrica


def _request(obra, *trabajadores, sha="sha-1", fecha="15/09/2026"):
    datos = {
        "cabecera": {"fecha": fecha, "obra_numero": obra},
        "firma": {"firmado": True},
        "empleados": [{"nombre": n, "dni": d, "horas_ordinarias": 8}
                      for n, d in trabajadores],
    }
    return PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": datos},
        context={"document": {"sha256": sha}})


def _lineas(fabrica, document_id=None) -> list[ParteRegistroOrm]:
    with fabrica.create_session() as s:
        q = s.query(ParteRegistroOrm)
        if document_id is not None:
            q = q.filter(ParteRegistroOrm.document_id == document_id)
        return q.order_by(ParteRegistroOrm.id).all()


def _empleado(linea: ParteRegistroOrm):
    return (linea.empleado_ide, linea.empleado_codigo, linea.empleado_nombre,
            linea.empleado_dni, linea.empleado_reside,
            linea.empleado_match_method)


# ============================ R13, R14, R15 ============================== #

@pytest.mark.parametrize("obra, nombre, dni, esperado", [
    # R13: con ficha, por DNI
    ("0100", "ANA", DNI_A, (10, "E10", "ANA UNO", DNI_A, 910, "dni")),
    # R4: el reside de la ficha desempata
    ("0100", "BEA", DNI_B, (20, "E20", "BEA DOS", DNI_B, 921, "dni")),
    # R7 + R14: ficha en la 1, recurso sin enlazar en la 28
    ("0200", "CARLOS", DNI_C,
     (None, "MO/950", "TRES, CARLOS", DNI_C, 950, "recurso_dni")),
    # R14: sin ficha
    ("0200", "EVA", DNI_E,
     (None, "MO/960", "EVA SINFICHA", DNI_E, 960, "recurso_dni")),
    # DA1: se lee el cif del recurso y se guarda el DNI de la ficha
    ("0100", "FELIX", CIF_F, (60, "E60", "FELIX SEIS", DNI_F, 965, "dni")),
    # R10, R11: por nombre, varios recursos de la persona
    ("0100", "Bea Dos", None, (20, "E20", "BEA DOS", DNI_B, 921, "nombre")),
    # R10, R14: por nombre, sin ficha
    ("0200", "Eva Sinficha", None,
     (None, "MO/960", "EVA SINFICHA", DNI_E, 960, "recurso_nombre")),
])
def test_f036_r13_r14_r15_el_conciliador_confirma_el_recurso_del_casado(
        obra, nombre, dni, esperado) -> None:
    pipeline, fabrica = _montar()
    pipeline.run(_request(obra, (nombre, dni)))
    (linea,) = _lineas(fabrica)
    assert _empleado(linea) == esperado
    assert linea.recurso_ide == linea.empleado_reside
    assert linea.parte_estado == "sin_parte"


def test_f036_r8_r15_alias_guardado_en_la_base() -> None:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        s.add(EmpleadoAliasOrm(
            nombre_norm=tm.normalize("Anita"), empleado_ide=10,
            empleado_codigo="E10", empleado_nombre="ANA UNO",
            empleado_dni=None, created_at_utc="2026-09-01T00:00:00Z"))
        s.commit()
    pipeline, _ = _montar(fabrica=fabrica)
    pipeline.run(_request("0100", ("Anita", None)))
    (linea,) = _lineas(fabrica)
    assert _empleado(linea) == (10, "E10", "ANA UNO", DNI_A, 910, "alias")
    assert linea.recurso_ide == 910


def test_f036_r5_dni_ambiguo_queda_sin_casar_y_a_revision() -> None:
    pipeline, fabrica = _montar()
    pipeline.run(_request("0100", ("HUGO IGUAL", DNI_H)))
    (linea,) = _lineas(fabrica)
    assert _empleado(linea) == (None, None, None, None, None, "dni_ambiguo")
    assert linea.recurso_ide is None


def test_f036_r14_casado_por_recurso_no_sube_la_revision() -> None:
    pipeline, fabrica = _montar()
    pipeline.run(_request("0200", ("EVA", DNI_E)))
    with fabrica.create_session() as s:
        from infrastructure.database.orm_models import ParteDocumentOrm
        (doc,) = s.query(ParteDocumentOrm).all()
        assert doc.review_required is False


# ================================ R16 =================================== #

def test_f036_r16_sin_conciliador_el_casado_no_escribe_recurso() -> None:
    pipeline, fabrica = _montar()
    pipeline._recurso_conciliador = None
    pipeline.run(_request("0100", ("ANA", DNI_A)))
    (linea,) = _lineas(fabrica)
    assert linea.empleado_reside == 910
    assert (linea.recurso_ide, linea.recurso_cif, linea.hmo_ide,
            linea.parte_estado) == (None, None, None, None)


# ================================= R6 =================================== #

class _RepoContador:
    """Repositorio de ingesta que cuenta las consultas de alias."""

    def __init__(self) -> None:
        self.consultas: list[str | None] = []
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return None

    def find_empleado_alias(self, nombre):
        self.consultas.append(nombre)   # y sin alias: devuelve None

    def save_parte(self, **kwargs) -> None:
        self.guardados.append(kwargs)


@pytest.mark.parametrize("dni, consultas", [
    (DNI_A, 0),             # el DNI decide: ok
    (DNI_H, 0),             # el DNI decide: dni_ambiguo
    ("99999999R", 1),       # DNI sin recursos persona: alias
    (None, 1),              # sin DNI: alias
])
def test_f036_r6_el_alias_solo_se_consulta_si_el_dni_no_decide(
        dni, consultas) -> None:
    repo = _RepoContador()
    proveedor = SigridMatcherProvider(
        lookup=Lookup(), empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01")
    pipeline = PersistPartePipeline(
        repository=repo, normalizer=ParteNormalizer(),
        matcher_provider=proveedor, hoy=lambda: date(2026, 9, 15))
    pipeline.run(_request("0100", ("ANA UNO", dni)))
    assert len(repo.consultas) == consultas


def test_f036_r10_candidatos_por_nombre_una_vez_por_parte(monkeypatch) -> None:
    """Tres trabajadores sin DNI ni alias: la lista de candidatos por
    nombre se calcula una sola vez para el parte."""
    proveedor = SigridMatcherProvider(
        lookup=Lookup(), empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01")
    indice = proveedor.get().indice
    llamadas: list[tuple] = []
    original = indice.candidatos_nombre

    def espia(empresa, fecha):
        llamadas.append((empresa, fecha))
        return original(empresa, fecha)

    monkeypatch.setattr(indice, "candidatos_nombre", espia)
    pipeline = PersistPartePipeline(
        repository=_RepoContador(), normalizer=ParteNormalizer(),
        matcher_provider=proveedor, hoy=lambda: date(2026, 9, 15))
    pipeline.run(_request("0100", ("Ana Uno", None), ("Bea Dos", None),
                          ("Nadie Nunca", None)))
    assert llamadas == [(1, 20260915)]


# ================================ R17 =================================== #

def test_f036_r17_sin_fichas_de_recurso() -> None:
    modulo = "application.services." + "fichas_de_recurso"
    assert importlib.util.find_spec(modulo) is None
    assert "recursos" not in {f.name for f in dataclasses.fields(Matchers)}


def test_f036_r17_nadie_los_usa() -> None:
    prohibidos = ("fichas_de" + "_recurso", "fichas_" + "candidatas",
                  "matchers." + "recursos", "match_nombre_" + "fichas")
    yo = Path(__file__).resolve()
    usos = [
        f"{ruta.relative_to(RAIZ_SV3)}: {p}"
        for ruta in RAIZ_SV3.rglob("*.py")
        if ruta.resolve() != yo and ".venv" not in ruta.parts
        for p in prohibidos
        if p in ruta.read_text(encoding="utf-8")
    ]
    assert usos == []


# ================================ R22 =================================== #

def test_f036_r22_un_parte_ya_guardado_no_se_re_casa() -> None:
    """Se guarda un parte con ANA (recurso 910). Cambia el maestro: ANA pasa
    a tener solo el 911. Un parte NUEVO casa con el 911; el viejo conserva
    su casado (solo su `recurso_ide` lo re-resuelve el conciliador)."""
    pipeline, fabrica = _montar()
    viejo = pipeline.run(_request("0100", ("ANA", DNI_A), sha="sha-viejo"))
    nuevo_maestro = Lookup(
        fichas=[_ficha(10, "ANA UNO", DNI_A, 911)],
        recursos=[_rec(911, "UNO, ANA", conide=10)])
    pipeline2, _ = _montar(nuevo_maestro, fabrica)
    # Otro dia: un parte de la misma obra y dia sustituiria al viejo.
    nuevo = pipeline2.run(_request("0100", ("ANA", DNI_A), sha="sha-nuevo",
                                   fecha="16/09/2026"))
    (v,) = _lineas(fabrica, viejo.document_id)
    (n,) = _lineas(fabrica, nuevo.document_id)
    assert _empleado(v) == (10, "E10", "ANA UNO", DNI_A, 910, "dni")
    assert _empleado(n) == (10, "E10", "ANA UNO", DNI_A, 911, "dni")
    assert (v.recurso_ide, n.recurso_ide) == (911, 911)


def test_f036_r22_reingerir_el_mismo_parte_no_lo_re_casa() -> None:
    pipeline, fabrica = _montar()
    primero = pipeline.run(_request("0100", ("ANA", DNI_A), sha="sha-x"))
    otra_vez = pipeline.run(_request("0100", ("BEA", DNI_B), sha="sha-x"))
    assert otra_vez.already_existed is True
    assert otra_vez.document_id == primero.document_id
    (linea,) = _lineas(fabrica)
    assert _empleado(linea)[0] == 10
