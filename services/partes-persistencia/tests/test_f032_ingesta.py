# tests/test_f032_ingesta.py
"""F-032 · R4, R5, R8–R10: el refresco de festivos dentro de la ingesta.

`PersistPartePipeline(refresco_festivos=...)` refresca ANTES de
`save_parte`, con los DNIs distintos de las lineas (sin las que no tienen)
y los anos de la semana ISO de la fecha del parte (sin fecha, hoy). Un
`sin_dato` o un error inesperado suben el parte a revision con un WARNING
(R8, R9); un `sin_calendario` no (R5). El parte se guarda siempre. El
duplicado sale antes y no pide nada (R10). Sin refresco cableado, todo
como hoy.

Dobles en memoria (los de `test_f047_parte_nuevo_sv3`); sin red ni BBDD.
"""
from __future__ import annotations

import datetime as dt
import logging

import pytest

from application.pipelines.persist_parte_pipeline import PersistPartePipeline
from application.services.refresco_festivos import ResultadoRefresco
from domain.models.parte_records import (
    EmpleadoMatch,
    ExistingParte,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
    TipoHoraMatch,
)
from tests.test_f047_parte_nuevo_sv3 import _Repo, _request

DNI_A = "12345678Z"
DNI_B = "87654321X"


def _registro(i, dni):
    return RegistroNormalizado(
        line_index=i, empleado_line_no=i + 1, tipo_hora="normal", horas=8.0,
        empleado=EmpleadoMatch(ide=i + 1, dni=dni, method="dni"),
        hora=TipoHoraMatch(ide=1, codigo="HL01"))


def _parte(fecha_iso="2026-03-18", dnis=(DNI_A, "8765-4321 x", DNI_A, None,
                                         "")):
    return ParteDocumento(
        firmado=True, fecha_iso=fecha_iso,
        fecha_int=int(fecha_iso.replace("-", "")) if fecha_iso else 20260318,
        obra=ObraMatch(ide=1, codigo="0100", method="codigo"),
        registros=[_registro(i, d) for i, d in enumerate(dnis)])


class _Normalizador:
    def __init__(self, parte):
        self.parte = parte

    def normalize(self, data, *, email_text=None):
        return self.parte


class _Refresco:
    def __init__(self, eventos, resultado=None, error=None):
        self.eventos = eventos
        self.resultado = resultado or ResultadoRefresco(1, 0, 0, 0)
        self.error = error
        self.llamadas: list = []

    def refrescar(self, dnis, anos):
        self.eventos.append("refresco")
        self.llamadas.append((sorted(dnis), sorted(anos)))
        if self.error is not None:
            raise self.error
        return self.resultado


def _pipeline(eventos, parte, refresco, *, repo=None,
              hoy=lambda: dt.date(2026, 12, 31)):
    repo = repo or _Repo(eventos)
    return PersistPartePipeline(
        repository=repo, normalizer=_Normalizador(parte),
        matcher_provider=None, refresco_festivos=refresco, hoy=hoy), repo


# --------------------------------- R4 ----------------------------------- #

def test_f032_r4_refresca_antes_de_guardar_con_dnis_y_anos():
    eventos: list = []
    refresco = _Refresco(eventos)
    pipeline, repo = _pipeline(eventos, _parte(), refresco)
    pipeline.run(_request())
    assert eventos[:2] == ["refresco", "save"]
    assert refresco.llamadas == [([DNI_A, DNI_B], [2026])]
    assert repo.guardados[0]["review_required"] is False


def test_f032_r4_sin_fecha_usa_los_anos_de_la_semana_de_hoy():
    eventos: list = []
    refresco = _Refresco(eventos)
    pipeline, _ = _pipeline(eventos, _parte(fecha_iso=None), refresco)
    pipeline.run(_request())
    # Hoy (falso) = jueves 31/12/2026: su semana ISO acaba en 2027.
    assert refresco.llamadas == [([DNI_A, DNI_B], [2026, 2027])]


def test_f032_r4_fecha_ilegible_usa_hoy():
    eventos: list = []
    refresco = _Refresco(eventos)
    parte = _parte()
    parte.fecha_iso = "no es fecha"
    pipeline, repo = _pipeline(eventos, parte, refresco)
    pipeline.run(_request())
    assert refresco.llamadas == [([DNI_A, DNI_B], [2026, 2027])]
    assert len(repo.guardados) == 1


def test_f032_r4_parte_sin_dnis_no_pide_nada():
    eventos: list = []
    refresco = _Refresco(eventos)
    pipeline, repo = _pipeline(eventos, _parte(dnis=(None, "")), refresco)
    pipeline.run(_request())
    assert refresco.llamadas == []
    assert repo.guardados[0]["review_required"] is False


# ------------------------------- R8 y R9 -------------------------------- #

def test_f032_r8_sin_dato_sube_a_revision_con_warning(caplog):
    eventos: list = []
    refresco = _Refresco(eventos, ResultadoRefresco(1, 0, 1, 2))
    pipeline, repo = _pipeline(eventos, _parte(), refresco)
    with caplog.at_level(logging.WARNING):
        resultado = pipeline.run(_request())
    assert repo.guardados[0]["review_required"] is True
    avisos = [r.getMessage() for r in caplog.records if "[festivos]" in
              r.getMessage()]
    assert avisos == [f"[festivos] parte {resultado.document_id} a revision: "
                      "2 clave(s) sin festivos de Sesame"]
    assert all(DNI_A not in a and DNI_B not in a for a in avisos)


def test_f032_r9_un_error_inesperado_sube_a_revision_y_guarda(caplog):
    eventos: list = []
    refresco = _Refresco(eventos, error=RuntimeError(f"boom {DNI_A}"))
    pipeline, repo = _pipeline(eventos, _parte(), refresco)
    with caplog.at_level(logging.WARNING):
        pipeline.run(_request())
    assert eventos[:2] == ["refresco", "save"]
    assert repo.guardados[0]["review_required"] is True
    textos = [r.getMessage() for r in caplog.records]
    assert any("[festivos]" in t and "a revision" in t for t in textos)
    assert all(DNI_A not in t for t in textos)


@pytest.mark.parametrize("resultado", [
    ResultadoRefresco(0, 0, 3, 0),       # solo 404
    ResultadoRefresco(0, 2, 0, 0),       # fallos con fila
    ResultadoRefresco(2, 1, 1, 0),
])
def test_f032_r5_r7_sin_sin_dato_no_hay_revision(resultado, caplog):
    eventos: list = []
    pipeline, repo = _pipeline(eventos, _parte(),
                               _Refresco(eventos, resultado))
    with caplog.at_level(logging.WARNING):
        pipeline.run(_request())
    assert repo.guardados[0]["review_required"] is False
    assert not [r for r in caplog.records if "a revision" in r.getMessage()]


def test_f032_r8_un_parte_ya_en_revision_sigue_en_revision():
    eventos: list = []
    parte = _parte()
    parte.firmado = False
    pipeline, repo = _pipeline(eventos, parte, _Refresco(eventos))
    pipeline.run(_request())
    assert repo.guardados[0]["review_required"] is True


# --------------------------------- R10 ---------------------------------- #

def test_f032_r10_el_duplicado_no_pide_nada():
    eventos: list = []
    repo = _Repo(eventos, existente=ExistingParte(document_id="d1", source_sha256="s",
                                                  registros=3))
    refresco = _Refresco(eventos)
    pipeline, _ = _pipeline(eventos, _parte(), refresco, repo=repo)
    resultado = pipeline.run(_request())
    assert resultado.already_existed is True
    assert refresco.llamadas == [] and eventos == []


# ----------------------------- sin cablear ------------------------------ #

def test_f032_r12_sin_refresco_todo_como_hoy():
    eventos: list = []
    pipeline, repo = _pipeline(eventos, _parte(), None)
    pipeline.run(_request())
    assert eventos == ["save"]
    assert repo.guardados[0]["review_required"] is False


def test_f032_r12_el_parametro_es_opcional():
    eventos: list = []
    pipeline = PersistPartePipeline(
        repository=_Repo(eventos), normalizer=_Normalizador(_parte()),
        matcher_provider=None)
    pipeline.run(_request())
    assert eventos == ["save"]
