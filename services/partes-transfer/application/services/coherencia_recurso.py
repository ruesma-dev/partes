# application/services/coherencia_recurso.py
"""Verificacion del recurso antes de escribir en Sigrid (F-023, R36-R37).

sv5 no casa: escribe lo que sv3 y el portal dejaron. Pero es el ultimo
punto antes del ERP, y un recurso puede haberse quedado rancio (reasignado
el trabajador, dado de baja el recurso despues de conciliar...). Por eso,
por cada linea:

  - R36: el recurso tiene que ser de la EMPRESA de la obra destino, estar
    DE ALTA a la fecha de la linea y, si la linea trae DNI, ser de esa
    PERSONA. Si no, la linea se omite con el motivo de lo que fallo.
  - R37: una linea sin recurso y con DNI solo se resuelve con un UNICO
    candidato de esa empresa y de alta a esa fecha.

Duplicacion TOLERADA (DA6, lista cerrada de `CLAUDE.md`): `de_alta` y la
eleccion de recurso por DNI existen tambien en sv3
(`application/services/seleccion_sigrid.py`). La equivalencia de `de_alta`
la vigila `tests/test_f023_de_alta_gemelos.py` en la raiz; quien toque una
copia cambia las dos en la misma feature.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from application.services.reglas_registro import (
    MOTIVO_RECURSO_AMBIGUO,
    MOTIVO_RECURSO_BAJA,
    MOTIVO_RECURSO_NO_EXISTE,
    MOTIVO_RECURSO_OTRA_EMPRESA,
    MOTIVO_RECURSO_OTRA_PERSONA,
    MOTIVO_SIN_RECURSO_EMPRESA,
)


def de_alta(fecbaj: int | None, fecha: int) -> bool:
    """R1: `con.fecbaj` NULL, 0 o mayor que `fecha` (`YYYYMMDD`)."""
    return not fecbaj or fecbaj > fecha


def _dni(dni: str | None) -> str:
    """DNI comparable: solo alfanumerico y en mayusculas."""
    return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()


@dataclass(frozen=True)
class RecursoSigrid:
    """Lo que sv5 lee de un recurso para verificarlo.

    `empresa` y `fecbaj` son `con.emp` y `con.fecbaj` del recurso; `dni`
    es `emp.dni` de su empleado (via `res.conide`) o, si esta vacio,
    `res.cif`.
    """

    reside: int
    empresa: int | None
    fecbaj: int | None
    dni: str | None


def verificar_recurso(
    r: RecursoSigrid | None, empresa: int, fecha: int, dni: str | None
) -> str | None:
    """R36: None si el recurso vale para esa linea; si no, el motivo."""
    if r is None:
        return MOTIVO_RECURSO_NO_EXISTE
    if r.empresa != empresa:
        return MOTIVO_RECURSO_OTRA_EMPRESA
    if not de_alta(r.fecbaj, fecha):
        return MOTIVO_RECURSO_BAJA
    dni_linea = _dni(dni)
    if dni_linea and _dni(r.dni) != dni_linea:
        return MOTIVO_RECURSO_OTRA_PERSONA
    return None


def elegir_por_dni(
    cands: list[RecursoSigrid], empresa: int, fecha: int
) -> tuple[int | None, str | None]:
    """R37: `(reside, None)` con un unico candidato de la empresa y de alta
    a la fecha; `(None, motivo)` con cero o con varios."""
    resides = {
        c.reside for c in cands
        if c.empresa == empresa and de_alta(c.fecbaj, fecha)
    }
    if len(resides) == 1:
        (reside,) = resides
        return reside, None
    if resides:
        return None, MOTIVO_RECURSO_AMBIGUO
    return None, MOTIVO_SIN_RECURSO_EMPRESA
