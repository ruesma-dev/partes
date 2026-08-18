# application/services/jornada_resolver.py
"""Jornada teorica (horas ordinarias esperadas por dia) del recurso.

UN solo sitio con la regla, que el computo de extras llevaba escrita a
mano dentro de `_reclasificar_extras_jornada`: el `candef` de Sigrid manda
si esta informado (estrictamente por encima del minimo); si no, la jornada
por defecto. Un `candef` de 0/1/2 significa "Sigrid no lo tiene
informado", no "este hombre trabaja dos horas": sin el umbral, el dia
entero se iria a horas extra.

GEMELO del de sv4 (`services/partes-front/application/services/
jornada_resolver.py`): adaptadores por servicio, sin libreria compartida
(docs/ARCHITECTURE.md). Quien cambie la regla cambia LAS DOS copias; hay
un test que compara ambas implementaciones.

F-003 deja aqui el ENCHUFE para la jornada real del contrato (Sesame).
Hoy no se puede: `GET /api/v1/jornada` de sesame-api devuelve el tipo de
jornada y si es reducida, pero NO las horas (peticion P1 del design).
"""
from __future__ import annotations


def candef_valido(candef: float | str | None, *, minimo: float) -> bool:
    """True si Sigrid informa una jornada creible para el recurso."""
    if candef is None or candef == "":
        return False
    try:
        valor = float(candef)
    except (TypeError, ValueError):
        return False
    return valor > float(minimo)


def jornada_efectiva(
    candef: float | str | None, *, minimo: float, por_defecto: float
) -> float:
    """Horas ordinarias del dia: `candef` si es valido, si no `por_defecto`.

    `candef` se tolera como texto (llega de Sigrid) y como `None`.
    Cualquier valor no numerico se trata como no informado.
    """
    if not candef_valido(candef, minimo=minimo):
        return float(por_defecto)
    return float(candef)  # type: ignore[arg-type]
