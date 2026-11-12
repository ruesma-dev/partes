# tests/test_f069_ids_estables.py
"""F-069 · R1-R6: las extras automaticas conservan su `id` entre pasadas.

Hasta F-069 cada pasada borraba las `extra_auto` no congeladas y las
creaba de nuevo con ids nuevos: los `data-registro-id` de la pagina del
portal dejaban de existir y sv4 rechazaba aprobar («N linea(s) no son de
esta vista», obra 0697, 12/11/2026). Ahora `escribir_pasada` reutiliza en
el sitio la extra que la pareja ya tenia.

SQLite en memoria con el ORM real; datos sinteticos.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite
from tests.f069_comun import base, extra, filas_cortas, sembrar


def _split(normal_id: int, *, norm=8.0, orig=10.0, ext=2.0, **kw) -> dict:
    return dict({
        "normal_id": normal_id, "horas_norm": norm, "horas_orig": orig,
        "extra_horas": ext, "hora_ext_ide": 2, "hora_ext_cod": "HE01",
        "hora_ext_desc": "Hora extra", "hora_ext_ext": 1,
        "hora_candef": 8.0}, **kw)


def _escribir(fabrica, splits, updates=None):
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    return repo.escribir_pasada(lectura, updates or [], splits)


def _extras(fabrica) -> list[tuple]:
    return [f for f in filas_cortas(fabrica) if f[5]]


# =================== R2 · el split reutiliza la extra ================== #

def test_f069_r2_escribir_reutiliza_la_extra_de_la_pareja() -> None:
    fabrica = FabricaSesionSqlite()
    b, e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)])
    res = _escribir(fabrica, [_split(b, norm=7.0, ext=3.0)])
    assert filas_cortas(fabrica) == [
        (b, "doc-1", 0, 7.0, 10.0, False), (e, "doc-1", 0, 3.0, None, True)]
    assert (res.aplicados, res.nuevas, res.reutilizadas, res.borradas) == \
        (1, 0, 1, 0)
    with fabrica.create_session() as s:
        ex = s.get(ParteRegistroOrm, e)
        assert (ex.hora_codigo, ex.hora_ide, ex.hora_match_method) == \
            ("HE01", 2, "extra_jornada")


def test_f069_r2_escribir_sin_extra_previa_la_crea() -> None:
    fabrica = FabricaSesionSqlite()
    b, = sembrar(fabrica, [base(10.0)])
    res = _escribir(fabrica, [_split(b)])
    extras = _extras(fabrica)
    assert len(extras) == 1 and extras[0][3] == 2.0
    assert (res.nuevas, res.reutilizadas, res.borradas) == (1, 0, 0)


# ================ R3 · varias bases o extras en la pareja ============== #

def test_f069_r3_escribir_empareja_por_orden() -> None:
    fabrica = FabricaSesionSqlite()
    b1, b2, e1, e2 = sembrar(fabrica, [base(8.0, 10.0), base(4.0, 5.0),
                                       extra(2.0), extra(1.0)])
    _escribir(fabrica, [_split(b2, norm=4.0, orig=5.0, ext=1.5),
                        _split(b1, ext=2.5)])
    horas = {f[0]: f[3] for f in _extras(fabrica)}
    assert horas == {e1: 2.5, e2: 1.5}


def test_f069_r3_escribir_split_de_mas_crea_extra_nueva() -> None:
    fabrica = FabricaSesionSqlite()
    b1, b2, e1 = sembrar(fabrica, [base(8.0, 10.0), base(4.0, 5.0),
                                   extra(2.0)])
    res = _escribir(fabrica, [_split(b1), _split(b2, norm=4.0, orig=5.0,
                                                   ext=1.0)])
    extras = _extras(fabrica)
    assert [f[0] for f in extras][0] == e1 and len(extras) == 2
    assert {f[0]: f[3] for f in extras}[e1] == 2.0
    assert (res.nuevas, res.reutilizadas) == (1, 1)


def test_f069_r3_escribir_extra_de_mas_se_borra() -> None:
    fabrica = FabricaSesionSqlite()
    b, e1, e2 = sembrar(fabrica, [base(8.0, 10.0), extra(1.0), extra(1.0)])
    res = _escribir(fabrica, [_split(b)])
    assert [(f[0], f[3]) for f in _extras(fabrica)] == [(e1, 2.0)]
    assert (res.reutilizadas, res.borradas) == (1, 1)
    assert e2 not in {f[0] for f in filas_cortas(fabrica)}


# ================ R4 · la pareja ya no necesita extra ================== #

def test_f069_r4_escribir_sin_split_borra_y_restaura() -> None:
    fabrica = FabricaSesionSqlite()
    b, e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)])
    res = _escribir(fabrica, [])
    assert filas_cortas(fabrica) == [(b, "doc-1", 0, 10.0, None, False)]
    assert (res.aplicados, res.borradas) == (0, 1)


def test_f069_r4_escribir_revierte_tambien_partes_inactivos() -> None:
    from infrastructure.database.orm_models import ParteDocumentOrm

    fabrica = FabricaSesionSqlite()
    b, e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)],
                   document_id="doc-2")
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "doc-2").is_active = False
        s.commit()
    _escribir(fabrica, [])
    assert filas_cortas(fabrica) == [(b, "doc-2", 0, 10.0, None, False)]


def test_f069_r4_escribir_borra_las_duplicadas_de_una_pareja_congelada(
) -> None:
    fabrica = FabricaSesionSqlite()
    b, e1, e2 = sembrar(fabrica, [base(8.0, 10.0), extra(2.0, "registrado"),
                                  extra(2.0)])
    res = _escribir(fabrica, [])
    assert [f[0] for f in filas_cortas(fabrica)] == [b, e1]
    assert res.borradas == 1


# ===================== R5 · el split trae su id ======================== #

def test_f069_r5_escribir_split_con_id_crea_esa_extra() -> None:
    fabrica = FabricaSesionSqlite()
    b, e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)])
    res = _escribir(fabrica, [_split(b, id=900)])
    assert [f[0] for f in _extras(fabrica)] == [900]
    assert (res.nuevas, res.reutilizadas, res.borradas) == (1, 0, 1)


# ============= DA2 · una reutilizada es igual que una nueva ============ #

def _sucia(fabrica, rid: int) -> None:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        r.sigrid_estado, r.sigrid_motivo = "error", "fallo de prueba"
        r.deleted_at_utc, r.deleted_by = "2026-10-02T08:00", "alguien"
        r.hora_precio_coste, r.horas_extra_leidas = 9.5, 3.0
        r.incidencia_texto, r.recurso_precio_hora = "x", 12.0
        r.es_incidencia = True
        s.commit()


def _columnas(fabrica, rid: int) -> dict:
    cols = [c for c in ParteRegistroOrm.__table__.columns if c.name != "id"]
    with fabrica.create_session() as s:
        fila = s.execute(select(*cols).where(ParteRegistroOrm.id == rid)
                         ).one()
    return dict(zip((c.name for c in cols), fila))


@pytest.mark.parametrize("sigrid", [None, {"sigrid_estado": "registrado",
                                           "sigrid_hmores_ide": 77}])
def test_f069_da2_escribir_reutilizada_igual_que_nueva_columna_a_columna(
        sigrid) -> None:
    lineas = [dict(base(8.0, 10.0), recurso_ide=501), extra(2.0)]
    hoy = FabricaSesionSqlite()
    b_hoy, e_hoy = sembrar(hoy, lineas)
    _sucia(hoy, e_hoy)
    repo_hoy = SqlAlchemyParteRepository(hoy)
    repo_hoy.revert_extras_auto()
    split = _split(b_hoy, norm=7.0, ext=3.0)
    if sigrid:
        split["sigrid"] = sigrid
    repo_hoy.apply_extras_splits([split])
    nueva = next(f[0] for f in _extras(hoy))

    f069 = FabricaSesionSqlite()
    b, e = sembrar(f069, lineas)
    _sucia(f069, e)
    _escribir(f069, [dict(split, normal_id=b)])
    assert [f[0] for f in _extras(f069)] == [e]
    assert _columnas(f069, e) == _columnas(hoy, nueva)
    assert _columnas(f069, b) == _columnas(hoy, b_hoy)
