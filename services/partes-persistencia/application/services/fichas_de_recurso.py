# application/services/fichas_de_recurso.py
"""F-030 (R4): la «ficha de recurso» de quien no tiene ficha de empleado.

Hay trabajadores con un recurso de mano de obra en Sigrid (`MO/`, con su
DNI en `res.cif`) pero sin ficha `emp`. Para ellos, el recurso hace de
ficha: se construye un `EmpleadoRow` con su DNI (`res.cif` tal cual),
su nombre (`con.res`), su empresa y su baja, y se casa con el MISMO
codigo que las fichas de empleado (`IndicePersonas.elegir_ficha`,
`fichas_candidatas` y `EmpleadoMatcher.match_nombre`).

Un recurso es ficha de recurso si:
  - su codigo empieza por `MO/` (solo la mano de obra lleva DNI en `cif`),
  - su `cif` normalizado no esta vacio,
  - ninguna ficha `emp` tiene ese DNI normalizado (de cualquier empresa y
    estado: esa persona casa por su ficha), y
  - su `conide` es None o no es el `ide` de ninguna ficha (si lo es, la
    persona ya casa por esa ficha).

Se devuelven de TODAS las empresas y estados: la empresa y la baja las
filtra `elegir_ficha`, con los mismos motivos que para las fichas de
empleado. `emp.ide` y `res.ide` son `con.ide`, unicos en Sigrid: una ficha
de recurso nunca choca con una de empleado. Funcion pura, sin red.
"""
from __future__ import annotations

from collections.abc import Iterable

from application.services import text_match as tm
from domain.models.sigrid_models import EmpleadoRow, RecursoRow

#: Prefijo del codigo de los recursos de mano de obra.
PREFIJO_MANO_DE_OBRA = "MO/"


def fichas_de_recurso(
    empleados: Iterable[EmpleadoRow], recursos: Iterable[RecursoRow]
) -> list[EmpleadoRow]:
    """Las fichas de recurso (ver cabecera), en el orden de `recursos`."""
    fichas = list(empleados)
    ides_ficha = {f.ide for f in fichas}
    dnis_ficha = {tm.normalize_dni(f.dni) for f in fichas} - {""}
    out: list[EmpleadoRow] = []
    for r in recursos:
        if not (r.codigo or "").startswith(PREFIJO_MANO_DE_OBRA):
            continue
        dni = tm.normalize_dni(r.cif)
        if not dni or dni in dnis_ficha:
            continue
        if r.conide in ides_ficha:
            continue
        out.append(EmpleadoRow(
            ide=r.ide, codigo=r.codigo, nombre=r.nombre, dni=r.cif,
            reside=r.ide, empresa=r.empresa, fecbaj=r.fecbaj,
        ))
    return out
