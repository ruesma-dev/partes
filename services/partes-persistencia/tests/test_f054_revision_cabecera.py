# tests/test_f054_revision_cabecera.py
"""F-054 · R1-R7, R9: un parte sin obra o sin fecha va siempre a revision (sv3).

`PersistPartePipeline._compute_review_required` sube `review_required` si
`motivos_cabecera(parte)` no esta vacia: `sin_obra` (`obra.ide` None, sea
cual sea `obra.method`) y `sin_fecha` (`fecha_int` None o <= 0). `run`
deja un WARNING con `document_id` y los motivos, sin nombres ni DNIs.

Sin red ni PostgreSQL: dobles en memoria y, para las columnas guardadas,
el SQLite de `test_f036_pipeline`. Nombres y DNIs FICTICIOS.
"""
from __future__ import annotations

import logging

import pytest

from application.pipelines import persist_parte_pipeline as modulo
from application.pipelines.persist_parte_pipeline import (
    MOTIVO_SIN_FECHA,
    MOTIVO_SIN_OBRA,
    PersistPartePipeline,
    PersistParteRequest,
    motivos_cabecera,
)
from application.services.lectura_dudosa import MOTIVO_TABLA_DISPERSA
from application.services.parte_normalizer import ParteNormalizer
from domain.models.parte_records import (
    EmpleadoMatch,
    MotivoLectura,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
    TipoHoraMatch,
)
from tests.test_f023_pipeline_match import DNI_A, _casar, _parte

FECHA = 20261020

#: Metodos de `obra_match_method` sin obra casada (`design.md` §1.1), mas
#: uno inventado: R1 vale para los que vengan.
METODOS_SIN_OBRA = ("none", "codigo_otra_empresa", "codigo_ambiguo",
                    "nombre_ambiguo", "metodo_nuevo")
METODOS_CON_OBRA = ("codigo", "codigo_padded", "codigo_membrete",
                    "codigo_trabajadores", "codigo_nombre", "nombre")

#: Cabecera del hallazgo del 2026-10-21 (`design.md` §6.3), con datos
#: ficticios: todo a null, firmado y 4 trabajadores con horas.
NOMBRES = ("ANA FICTICIA", "BEA INVENTADA", "CARLOS SUPUESTO", "DIANA FALSA")
DNIS = ("11111111H", "22222222J", "33333333P", "44444444A")


def _casado(*, obra: ObraMatch | None = None, fecha: int | None = FECHA,
            empleado: EmpleadoMatch | None = None) -> ParteDocumento:
    """Parte que no va a revision: firmado, con fecha, obra y trabajador."""
    registro = RegistroNormalizado(
        line_index=0, empleado_line_no=1, tipo_hora="normal", horas=8.0,
        empleado=empleado or EmpleadoMatch(ide=1, method="dni"),
        hora=TipoHoraMatch(ide=1, codigo="HL01"))
    return ParteDocumento(
        firmado=True, fecha_int=fecha,
        obra=obra or ObraMatch(ide=1, codigo="0100", method="codigo"),
        registros=[registro])


def _revisar(parte: ParteDocumento) -> bool:
    return PersistPartePipeline._compute_review_required(parte)


# ================================ R1 ===================================== #

@pytest.mark.parametrize("metodo", METODOS_SIN_OBRA)
def test_f054_r1_sin_obra_va_a_revision(metodo) -> None:
    assert _revisar(_casado(obra=ObraMatch(method=metodo))) is True


def test_f054_r1_por_el_casado_real() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra=None))
    assert parte.obra.method == "none"
    assert parte.obra.ide is None
    # El trabajador casa: la revision la da la obra, no el.
    assert parte.registros[0].empleado.ide is not None
    assert parte.review is True   # type: ignore[attr-defined]


# ================================ R2 ===================================== #

@pytest.mark.parametrize("fecha", [None, 0, -1])
def test_f054_r2_sin_fecha_va_a_revision(fecha) -> None:
    assert _revisar(_casado(fecha=fecha)) is True


def test_f054_r2_con_fecha_positiva_no_hay_motivo() -> None:
    # Frontera de «<= 0»: cualquier entero positivo cuenta como fecha.
    assert motivos_cabecera(_casado(fecha=1)) == ()
    assert _revisar(_casado(fecha=1)) is False


def test_f054_r2_sin_fecha_por_el_casado_real() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="300", fecha=None))
    assert parte.obra.ide == 300
    assert parte.registros[0].empleado.ide is not None
    assert parte.review is True   # type: ignore[attr-defined]


# ================================ R3 ===================================== #

@pytest.mark.parametrize("con_obra, con_fecha, esperado", [
    (True, True, ()),
    (False, True, ("sin_obra",)),
    (True, False, ("sin_fecha",)),
    (False, False, ("sin_obra", "sin_fecha")),
])
def test_f054_r3_motivos_cabecera(con_obra, con_fecha, esperado) -> None:
    parte = _casado(obra=None if con_obra else ObraMatch(method="none"),
                    fecha=FECHA if con_fecha else None)
    assert motivos_cabecera(parte) == esperado
    assert _revisar(parte) is bool(esperado)


def test_f054_r3_constantes_de_los_motivos() -> None:
    assert (MOTIVO_SIN_OBRA, MOTIVO_SIN_FECHA) == ("sin_obra", "sin_fecha")


# ================================ R4 ===================================== #

@pytest.mark.parametrize("metodo", METODOS_CON_OBRA)
def test_f054_r4_casado_completo_no_va_a_revision(metodo) -> None:
    parte = _casado(obra=ObraMatch(ide=1, codigo="0100", method=metodo))
    assert motivos_cabecera(parte) == ()
    assert _revisar(parte) is False


def test_f054_r4_casado_por_recurso_no_cambia() -> None:
    parte = _casado(empleado=EmpleadoMatch(ide=None, reside=950,
                                           method="recurso_dni"))
    assert _revisar(parte) is False


# ================================ R5 ===================================== #

def _sin_firma(parte: ParteDocumento) -> None:
    parte.firmado = False


def _sin_registros(parte: ParteDocumento) -> None:
    parte.registros = []


def _lectura_dudosa(parte: ParteDocumento) -> None:
    parte.lectura_dudosa = [MotivoLectura(MOTIVO_TABLA_DISPERSA, (1,))]


def _trabajador_sin_casar(parte: ParteDocumento) -> None:
    parte.registros[0].empleado = EmpleadoMatch(ide=None, method="none")


def _hora_sin_resolver(parte: ParteDocumento) -> None:
    parte.registros[0].hora = TipoHoraMatch(ide=None)


@pytest.mark.parametrize("estropear", [
    _sin_firma, _sin_registros, _lectura_dudosa, _trabajador_sin_casar,
    _hora_sin_resolver,
])
def test_f054_r5_las_demas_causas_no_cambian(estropear) -> None:
    parte = _casado()
    assert _revisar(parte) is False
    estropear(parte)
    assert motivos_cabecera(parte) == ()
    assert _revisar(parte) is True


# ================================ R6 ===================================== #

def test_f054_r6_obra_a_revisar_desaparece() -> None:
    assert not hasattr(modulo, "OBRA_A_REVISAR")


# ============================ R7 y R9 (run) ============================== #

class _Repo:
    """Lo que la ingesta pide al repositorio, en memoria."""

    def __init__(self) -> None:
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return None

    def find_empleado_alias(self, _nombre):
        return None

    def save_parte(self, **kwargs) -> None:
        self.guardados.append(kwargs)


def _datos_hallazgo() -> dict:
    return {
        "cabecera": {"fecha": None, "obra_numero": None, "obra_nombre": None,
                     "empresa_membrete": None},
        "firma": {"firmado": True},
        "empleados": [
            {"numero_linea": n, "nombre": nombre, "dni": dni,
             "horas_ordinarias": 8}
            for n, (nombre, dni) in enumerate(zip(NOMBRES, DNIS), start=1)
        ],
    }


def _datos_completos() -> dict:
    datos = _datos_hallazgo()
    datos["cabecera"] = {"fecha": "20/10/2026", "obra_numero": "0100"}
    return datos


def _ingerir(datos: dict, monkeypatch, *, casar_obra: bool) -> dict:
    """Ingesta completa con un casado de mentira que casa a los trabajadores
    (y la obra, si `casar_obra`): lo que decide es la cabecera."""
    repo = _Repo()
    pipeline = PersistPartePipeline(repository=repo, normalizer=ParteNormalizer(),
                                    matcher_provider=object())  # type: ignore[arg-type]

    def _casar_trabajadores(parte: ParteDocumento) -> None:
        if casar_obra:
            parte.obra = ObraMatch(ide=1, codigo="0100", method="codigo")
        for reg in parte.registros:
            reg.empleado = EmpleadoMatch(ide=reg.empleado_line_no, method="dni")
            reg.hora = TipoHoraMatch(ide=1)

    monkeypatch.setattr(pipeline, "_match", _casar_trabajadores)
    pipeline.run(PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": datos},
        context={"document": {"sha256": "sha-f054"}}))
    assert len(repo.guardados) == 1
    return repo.guardados[0]


def _avisos_de_cabecera(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records
            if "cabecera incompleta" in r.getMessage()]


def test_f054_r7_warning_con_motivos_sin_nombres(monkeypatch, caplog) -> None:
    caplog.set_level(logging.INFO)
    guardado = _ingerir(_datos_hallazgo(), monkeypatch, casar_obra=False)
    (aviso,) = _avisos_de_cabecera(caplog)
    assert aviso.levelno == logging.WARNING
    texto = aviso.getMessage()
    assert f"document_id={guardado['document_id']}" in texto
    assert "motivos=sin_obra,sin_fecha" in texto
    assert "obra_match_method=none" in texto
    assert "obra_leida=None" in texto
    for dato in NOMBRES + DNIS:
        assert dato not in texto


def test_f054_r7_el_warning_lleva_la_obra_leida(monkeypatch, caplog) -> None:
    caplog.set_level(logging.INFO)
    datos = _datos_completos()
    datos["cabecera"]["fecha"] = None
    _ingerir(datos, monkeypatch, casar_obra=True)
    (aviso,) = _avisos_de_cabecera(caplog)
    texto = aviso.getMessage()
    assert "motivos=sin_fecha " in texto
    assert "obra_match_method=codigo" in texto
    assert "obra_leida='0100'" in texto


def test_f054_r7_sin_motivos_no_hay_warning(monkeypatch, caplog) -> None:
    caplog.set_level(logging.INFO)
    guardado = _ingerir(_datos_completos(), monkeypatch, casar_obra=True)
    assert guardado["review_required"] is False
    assert _avisos_de_cabecera(caplog) == []


def test_f054_r9_ingesta_del_hallazgo(monkeypatch) -> None:
    guardado = _ingerir(_datos_hallazgo(), monkeypatch, casar_obra=False)
    parte = guardado["parte"]
    assert len(parte.registros) == 4
    assert all(r.empleado.ide is not None for r in parte.registros)
    assert parte.firmado is True
    assert parte.fecha_int is None
    assert parte.obra.ide is None
    assert guardado["review_required"] is True


def test_f054_r9_columnas_guardadas() -> None:
    from infrastructure.database.orm_models import ParteDocumentOrm
    from tests.test_f036_pipeline import DNI_A as DNI_F036
    from tests.test_f036_pipeline import _montar, _request

    pipeline, fabrica = _montar()
    pipeline.run(_request(None, ("ANA UNO", DNI_F036), fecha=None,
                          sha="sha-f054-sqlite"))
    with fabrica.create_session() as s:
        (doc,) = s.query(ParteDocumentOrm).all()
        assert doc.review_required is True
        assert doc.obra_ide is None
        assert doc.fecha_int is None
        assert doc.obra_match_method == "none"
