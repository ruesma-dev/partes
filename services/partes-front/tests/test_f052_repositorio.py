# tests/test_f052_repositorio.py
"""F-052 en sv4: lecturas del repositorio para sincronizar (R7, R12).

- `lineas_para_sincronizar`: las líneas activas del ámbito (obra
  `obr-{ide}` o persona `rec-{R}`, F-050) con fecha en el periodo; fuera la
  papelera y los partes inactivos. Periodo de nómina y natural.
- `donde_estan` (R12, DA16): `papelera`, `parte_reemplazado` (parte
  desactivado por la reingesta de sv3), `otro_ambito` o `no_existe`.

SQLite en memoria con el ORM real; datos sintéticos.
"""
from __future__ import annotations

import pytest
from application.services.calendar_builder import period_bounds
from application.services.sincronizacion import LineaPortal
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-10-20T08:00:00+00:00"


def _doc(s, did: str, *, obra_ide: int | None = 686, activo: bool = True,
         deleted_by: str | None = None,
         deleted_at: str | None = None) -> None:
    s.add(ParteDocumentOrm(
        id=did, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + did,
        fecha="2026-10-14", fecha_int=20261014, created_at_utc=AHORA,
        obra_ide=obra_ide, obra_codigo="0686", obra_nombre="Obra",
        is_active=activo, deleted_by=deleted_by, deleted_at_utc=deleted_at))


def _reg(s, did: str, fecha_int: int, **cambios) -> int:
    base = dict(document_id=did, line_index=0, fecha=str(fecha_int),
                fecha_int=fecha_int, obra_ide=686, obra_codigo="0686",
                obra_nombre="Obra", empleado_ide=77, recurso_ide=501,
                tipo_hora="normal", horas=8.0, hora_ide=3,
                hora_codigo="HL01", partida_ide=11, partida_cod="P1")
    base.update(cambios)
    reg = ParteRegistroOrm(**base)
    s.add(reg)
    s.flush()
    return reg.id


@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    return fabrica, ParteReviewRepository(fabrica)


def _sembrar(fabrica) -> dict[str, int]:
    ids: dict[str, int] = {}
    with fabrica.create_session() as s:
        _doc(s, "a")
        _doc(s, "otra", obra_ide=999)
        _doc(s, "inactivo", activo=False)
        ids["sep16"] = _reg(s, "a", 20260916)
        ids["oct01"] = _reg(s, "a", 20261001)
        ids["oct15"] = _reg(s, "a", 20261015, tipo_hora="extra",
                            sigrid_estado="registrado",
                            sigrid_hmores_ide=9001, sigrid_hmoide=7001,
                            sigrid_motivo="m")
        ids["oct16"] = _reg(s, "a", 20261016, hora_ext=1, horas=None)
        ids["oct31"] = _reg(s, "a", 20261031, es_incidencia=True,
                            hora_codigo="CIV")
        ids["nov01"] = _reg(s, "a", 20261101)
        ids["papelera"] = _reg(s, "a", 20261010, deleted_at_utc=AHORA)
        ids["inactivo"] = _reg(s, "inactivo", 20261010)
        ids["otra_obra"] = _reg(s, "otra", 20261010, obra_ide=999)
        ids["reside"] = _reg(s, "otra", 20261011, obra_ide=999,
                             recurso_ide=None, empleado_reside=501)
        ids["sin_casar"] = _reg(s, "otra", 20261012, obra_ide=999,
                                empleado_ide=None,
                                trabajador_nombre_leido="Leido")
        ids["otro_recurso"] = _reg(s, "otra", 20261013, obra_ide=999,
                                   recurso_ide=502)
        s.commit()
    return ids


def _ids(lineas) -> list[int]:
    return [l.registro_id for l in lineas]


@pytest.mark.parametrize("modo, esperados", [
    ("natural", ["oct01", "oct15", "oct16", "oct31"]),
    ("nomina", ["sep16", "oct01", "oct15"]),
])
def test_f052_r7_obra_en_el_periodo_sin_papelera(repo, modo,
                                                 esperados) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    desde, hasta = period_bounds(2026, 10, modo)
    lineas = r.lineas_para_sincronizar(
        obra_ide=686, desde=int(desde.strftime("%Y%m%d")),
        hasta=int(hasta.strftime("%Y%m%d")))
    assert _ids(lineas) == sorted(ids[k] for k in esperados)


def test_f052_r7_persona_rec_por_recurso_y_reside_casada(repo) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    lineas = r.lineas_para_sincronizar(recurso_ide=501, desde=20261001,
                                       hasta=20261031)
    assert _ids(lineas) == sorted(
        ids[k] for k in ("oct01", "oct15", "oct16", "oct31", "otra_obra",
                         "reside"))


def test_f052_r7_linea_portal_con_lo_que_compara(repo) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    por_id = {l.registro_id: l for l in r.lineas_para_sincronizar(
        recurso_ide=501, desde=20261001, hasta=20261031)}
    assert por_id[ids["oct15"]] == LineaPortal(
        registro_id=ids["oct15"], fecha_int=20261015, recurso_ide=501,
        obra_ide=686, horas=8.0, extra=True, es_incidencia=False,
        hora_codigo="HL01", partida_ide=11, partida_cod="P1",
        sigrid_estado="registrado", sigrid_motivo="m",
        sigrid_hmores_ide=9001, sigrid_hmoide=7001)
    assert por_id[ids["oct16"]].extra is True
    assert por_id[ids["oct16"]].horas is None
    assert por_id[ids["oct01"]].extra is False
    assert por_id[ids["oct31"]].es_incidencia is True
    assert por_id[ids["reside"]].recurso_ide == 501
    assert por_id[ids["reside"]].obra_ide == 999


@pytest.mark.parametrize("kwargs", [{}, {"obra_ide": 1, "recurso_ide": 2}])
def test_f052_r7_exige_obra_o_recurso(repo, kwargs) -> None:
    _f, r = repo
    with pytest.raises(ValueError):
        r.lineas_para_sincronizar(desde=20261001, hasta=20261031, **kwargs)


def test_f052_r7_sin_lineas_lista_vacia(repo) -> None:
    _f, r = repo
    assert r.lineas_para_sincronizar(obra_ide=686, desde=20261001,
                                     hasta=20261031) == []


# ------------------------------ donde_estan ------------------------------ #

def test_f052_r12_donde_estan(repo) -> None:
    fabrica, r = repo
    with fabrica.create_session() as s:
        _doc(s, "vivo")
        _doc(s, "en_papelera", activo=False, deleted_by="ana",
             deleted_at=AHORA)
        _doc(s, "retirado", activo=False, deleted_by="retirado:ana")
        _doc(s, "reemplazado", activo=False)
        viva = _reg(s, "vivo", 20261014)
        borrada = _reg(s, "vivo", 20261014, deleted_at_utc=AHORA)
        doc_papelera = _reg(s, "en_papelera", 20261014)
        retirado = _reg(s, "retirado", 20261014, deleted_at_utc=AHORA)
        reemplazado = _reg(s, "reemplazado", 20261014)
        s.commit()
    assert r.donde_estan([viva, borrada, doc_papelera, retirado,
                          reemplazado, 99999, viva]) == {
        viva: "otro_ambito", borrada: "papelera",
        doc_papelera: "papelera", retirado: "papelera",
        reemplazado: "parte_reemplazado", 99999: "no_existe"}


def test_f052_r12_donde_estan_sin_ids(repo) -> None:
    _f, r = repo
    assert r.donde_estan([]) == {}
