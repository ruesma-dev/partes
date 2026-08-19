# infrastructure/database/sqlalchemy_jornada_repository.py
"""Adaptador de `JornadaEmpleadoPort` sobre la base `partes` (F-015).

Lee `empleado_jornada` ENTERA (solo las filas activas) y la devuelve como
`JornadaEmpleadoRow`. Se espera que tenga unidades de filas —hoy, cero—,
asi que una lectura completa por pasada sale mucho mas barata que un
`SELECT` por trabajador y dia.

Va aparte del repositorio grande de sv3 a proposito: asi el
`RecursoConciliador` se prueba con un doble del puerto y sigue
funcionando con `jornadas=None`, que es lo que hacen todos los tests
anteriores a F-015.
"""
from __future__ import annotations

import logging

from application.services import text_match as tm
from domain.ports.jornada_empleado_port import (
    JornadaEmpleadoPort,
    JornadaEmpleadoRow,
)
from infrastructure.database.orm_models import EmpleadoJornadaOrm
from infrastructure.database.session_factory import SessionFactory
from sqlalchemy import select

logger = logging.getLogger(__name__)

#: Columnas del patron en orden lunes..domingo.
_DIAS = ("h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom")


class SqlAlchemyJornadaRepository(JornadaEmpleadoPort):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def fetch_jornadas(self) -> list[JornadaEmpleadoRow]:
        """Excepciones ACTIVAS, con el DNI ya normalizado.

        No filtra por fecha: la vigencia la resuelve quien pregunta por un
        dia concreto, que es quien sabe cual. Una fila con las siete horas
        del patron a NULL se entiende como "solo jornada semanal".
        """
        with self._session_factory.create_session() as session:
            filas = session.execute(
                select(EmpleadoJornadaOrm).where(
                    EmpleadoJornadaOrm.is_active.is_(True)
                )
            ).scalars().all()
            out: list[JornadaEmpleadoRow] = []
            for f in filas:
                horas = [getattr(f, dia) for dia in _DIAS]
                patron = (
                    tuple(float(h) for h in horas)
                    if all(h is not None for h in horas) else None
                )
                out.append(JornadaEmpleadoRow(
                    dni_norm=tm.normalize_dni(f.dni_norm),
                    jornada_semanal=(
                        None if f.jornada_semanal is None
                        else float(f.jornada_semanal)
                    ),
                    patron=patron,
                    desde=f.desde,
                    hasta=f.hasta,
                    origen=f.origen or "manual",
                ))
        logger.info(
            "[jornada-excepciones] %s fila(s) activas en empleado_jornada",
            len(out),
        )
        return out
