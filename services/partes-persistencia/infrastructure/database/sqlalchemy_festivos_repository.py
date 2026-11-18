# infrastructure/database/sqlalchemy_festivos_repository.py
"""Festivos de cada trabajador en `festivos_trabajador` (F-032, design §5.3).

  - `leer_todas()`: la tabla entera como ``{(dni_norm, ano): FilaFestivos}``.
    Son unas 220 filas por ano, asi que una lectura completa (cacheada por
    quien la usa) sale mas barata que un SELECT por trabajador y dia. Una
    fila mal formada se omite con un WARNING que da su ``id``, nunca el DNI
    (R3).
  - `guardar(fila)`: upsert por (dni_norm, ano) con el ``INSERT ... ON
    CONFLICT DO UPDATE`` del dialecto (PostgreSQL en produccion, SQLite en
    los tests). Dos replicas que guardan la misma clave a la vez dejan una
    sola fila: lo resuelve el indice unico (R11).

No hay borrado: un 404 de Sesame no toca la tabla (R5). Solo sv3 escribe.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite

from application.services.festivos_guardados import (
    FilaFestivos,
    a_json,
    fila_de,
)
from infrastructure.database.orm_models import FestivoTrabajadorOrm

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[festivos-tabla]"

_INSERTS = {"postgresql": postgresql.insert, "sqlite": sqlite.insert}


class SqlAlchemyFestivosRepository:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    def leer_todas(self) -> dict[tuple[str, int], FilaFestivos]:
        """Todas las filas bien formadas, por (DNI normalizado, ano)."""
        out: dict[tuple[str, int], FilaFestivos] = {}
        omitidas = 0
        with self._session_factory.create_session() as session:
            filas = session.execute(select(FestivoTrabajadorOrm)).scalars().all()
            for f in filas:
                try:
                    fila = fila_de(f.dni_norm, f.ano, f.festivos_json,
                                   f.leido_en_utc)
                except ValueError as exc:
                    omitidas += 1
                    logger.warning(
                        "%s fila id=%s mal formada, se omite: %s",
                        _LOG_PREFIX, f.id, exc,
                    )
                    continue
                out[(fila.dni_norm, fila.ano)] = fila
        logger.info("%s %s fila(s) leidas, %s omitida(s)",
                    _LOG_PREFIX, len(out), omitidas)
        return out

    def guardar(self, fila: FilaFestivos) -> None:
        """Upsert de la fila por (dni_norm, ano)."""
        valores = {
            "dni_norm": fila.dni_norm,
            "ano": int(fila.ano),
            "festivos_json": a_json(fila.festivos),
            "n_festivos": len(fila.festivos),
            "leido_en_utc": fila.leido_en_utc,
        }
        with self._session_factory.create_session() as session:
            insertar = _INSERTS[session.get_bind().dialect.name]
            sentencia = insertar(FestivoTrabajadorOrm).values(**valores)
            sentencia = sentencia.on_conflict_do_update(
                index_elements=["dni_norm", "ano"],
                set_={k: valores[k] for k in
                      ("festivos_json", "n_festivos", "leido_en_utc")},
            )
            session.execute(sentencia)
            session.commit()
