# tests/test_f068_conciliar_recalculo.py
"""F-068 · casar o reasignar un trabajador (o deshacerlo) pide a sv3 el
recálculo de extras.

Una línea sin casar no tiene jornada y sv3 no la parte en ordinaria y
extra. Hasta F-068, casarla en Conciliar la dejaba con todas sus horas
como ordinarias y aprobable hasta la siguiente pasada completa de sv3
(obra 0694, 04/11/2026). Desde F-068, sv4 pide UN recálculo con pedido
compartido (F-049) sobre los partes de las líneas que escribió.

Sin red: repositorio real sobre SQLite, una cola doble y un cliente de
Sigrid falso. Datos sintéticos.
"""
from __future__ import annotations

from infrastructure.persistencia.recalculo_publisher import (
    MOTIVO_CASADO_CONCILIACION,
    MOTIVO_DESHACER_TRABAJADOR,
    MOTIVO_REASIGNACION,
)


# ======================= R20 · las constantes ========================== #

def test_f068_r20_constantes_de_motivo() -> None:
    assert MOTIVO_CASADO_CONCILIACION == "casado_conciliacion"
    assert MOTIVO_REASIGNACION == "reasignacion_trabajador"
    assert MOTIVO_DESHACER_TRABAJADOR == "deshacer_trabajador"
