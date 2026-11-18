# tests/test_f032_repositorio.py
"""F-032 · R11 y R3: `SqlAlchemyFestivosRepository` sobre SQLite en memoria.

`guardar` es un upsert por (dni_norm, ano): la primera vez inserta y la
segunda sustituye, dejando UNA fila (R11; el indice unico la defiende
tambien con dos replicas). `leer_todas` mapea por (DNI, ano) y omite una
fila mal formada con un WARNING que da su `id` y no el DNI (R3). No hay
metodo de borrado: un 404 no borra nada (R5).
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select

from application.services.festivos_guardados import FilaFestivos
from infrastructure.database.orm_models import FestivoTrabajadorOrm
from infrastructure.database.sqlalchemy_festivos_repository import (
    SqlAlchemyFestivosRepository,
)
from tests.dobles import FabricaSesionSqlite

DNI = "12345678Z"
OTRO = "87654321X"


def _fila(dni=DNI, ano=2026, festivos=None, leido="2026-11-17T10:00:00Z"):
    return FilaFestivos(dni_norm=dni, ano=ano,
                        festivos=festivos if festivos is not None
                        else {"2026-03-19": "San José"},
                        leido_en_utc=leido)


def _filas_bd(fabrica):
    with fabrica.create_session() as s:
        return [(f.dni_norm, f.ano, f.festivos_json, f.n_festivos,
                 f.leido_en_utc)
                for f in s.execute(select(FestivoTrabajadorOrm).order_by(
                    FestivoTrabajadorOrm.id)).scalars()]


def test_f032_r11_guardar_inserta():
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    repo.guardar(_fila())
    assert _filas_bd(fabrica) == [
        (DNI, 2026, '{"2026-03-19": "San José"}', 1, "2026-11-17T10:00:00Z")]


def test_f032_r11_guardar_dos_veces_sustituye_y_deja_una_fila():
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    repo.guardar(_fila())
    # Otra instancia: como una segunda replica de sv3.
    SqlAlchemyFestivosRepository(fabrica).guardar(_fila(
        festivos={"2026-01-06": None, "2026-12-08": "Inmaculada"},
        leido="2026-11-18T09:00:00Z"))
    assert _filas_bd(fabrica) == [
        (DNI, 2026, '{"2026-01-06": null, "2026-12-08": "Inmaculada"}', 2,
         "2026-11-18T09:00:00Z")]
    with fabrica.create_session() as s:
        assert s.execute(select(func.count()).select_from(
            FestivoTrabajadorOrm)).scalar_one() == 1


def test_f032_r11_claves_distintas_son_filas_distintas():
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    repo.guardar(_fila())
    repo.guardar(_fila(ano=2027, festivos={}))
    repo.guardar(_fila(dni=OTRO))
    assert [(d, a, n) for d, a, _, n, _ in _filas_bd(fabrica)] == [
        (DNI, 2026, 1), (DNI, 2027, 0), (OTRO, 2026, 1)]


def test_f032_r11_leer_todas_mapea_por_dni_y_ano():
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    repo.guardar(_fila())
    repo.guardar(_fila(dni=OTRO, ano=2025, festivos={"2025-12-25": None}))
    todas = repo.leer_todas()
    assert todas == {
        (DNI, 2026): _fila(),
        (OTRO, 2025): _fila(dni=OTRO, ano=2025,
                            festivos={"2025-12-25": None}),
    }


def test_f032_r11_leer_todas_vacia():
    assert SqlAlchemyFestivosRepository(FabricaSesionSqlite()).leer_todas() == {}


def test_f032_r3_fila_mal_formada_se_omite_con_warning_sin_dni(caplog):
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    repo.guardar(_fila())
    with fabrica.create_session() as s:
        mala = FestivoTrabajadorOrm(dni_norm=OTRO, ano=2026,
                                    festivos_json="esto no es json",
                                    n_festivos=0, leido_en_utc="t")
        s.add(mala)
        s.commit()
        id_mala = mala.id
    with caplog.at_level(logging.WARNING):
        todas = repo.leer_todas()
    assert list(todas) == [(DNI, 2026)]
    avisos = [r.getMessage() for r in caplog.records
              if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert f"id={id_mala}" in avisos[0]
    assert OTRO not in avisos[0] and DNI not in avisos[0]


def test_f032_r3_los_logs_del_repositorio_no_llevan_dni(caplog):
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyFestivosRepository(fabrica)
    with caplog.at_level(logging.DEBUG):
        repo.guardar(_fila())
        repo.leer_todas()
    assert all(DNI not in r.getMessage() for r in caplog.records)


def test_f032_r5_el_repositorio_no_sabe_borrar():
    publicos = {n for n in dir(SqlAlchemyFestivosRepository)
                if not n.startswith("_")}
    assert publicos == {"guardar", "leer_todas"}
