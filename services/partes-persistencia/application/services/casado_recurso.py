# application/services/casado_recurso.py
"""F-036: casa el trabajador leido contra los RECURSOS persona (R4-R14).

El casado de la ingesta elige recurso, de la misma lista que despues usa
el conciliador (`IndicePersonas`, recursos con `res.cla = 1`): los de alta
a la fecha del parte, de la empresa del parte (sin empresa, de cualquiera)
y con DNI del recurso (el de su ficha y, si no, `res.cif`; DA1).

Orden (el de siempre): DNI leido -> alias aprendido -> similitud de
nombre. Un DNI con recursos persona pero sin candidato unico CIERRA la
linea sin casar (`dni_<motivo>`), sin seguir al alias ni al nombre (R5).

Lo que se guarda (R13-R14): con ficha enlazada (`res.conide`), los datos
de la ficha; sin ella, el codigo y el nombre del recurso con
`recurso_dni`/`recurso_nombre` (los metodos que sv4 ya da por casados).
En los dos casos `dni` = DNI del recurso y `reside` = `res.ide`, para que
el conciliador (`elegir_recurso`) confirme el mismo recurso (R15).

Funcion pura: sin red ni base. El alias llega como funcion para no
consultar la base cuando el DNI ya decide.
"""
from __future__ import annotations

from collections.abc import Callable

from application.services import text_match as tm
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import RecursoRow

#: Motivos de `casar_por_dni` que cierran la linea sin casar (R5).
_MOTIVOS_QUE_CIERRAN = frozenset({"ambiguo", "solo_baja", "otra_empresa"})


def casar_trabajador(
    *,
    dni_leido: str | None,
    nombre_leido: str | None,
    alias: Callable[[], dict | None] | None,
    indice: IndicePersonas,
    matcher: EmpleadoMatcher,
    empresa: int | None,
    fecha: int,
) -> EmpleadoMatch:
    """R4-R14: el casado de una linea (ver cabecera)."""
    # 1. DNI leido (R4-R6).
    if dni_leido:
        res = indice.casar_por_dni(dni_leido, empresa, fecha)
        if res.motivo == "ok":
            return _a_match(indice, indice.recurso(res.ide), 1.0, "dni")
        if res.motivo in _MOTIVOS_QUE_CIERRAN:
            return EmpleadoMatch(method=f"dni_{res.motivo}")
    # 2. Alias aprendido (R8).
    datos = alias() if alias is not None else None
    if datos is not None:
        return _casar_alias(datos, indice, empresa, fecha)
    # 3. Similitud de nombre (R10-R12).
    return _casar_nombre(nombre_leido, indice, matcher, empresa, fecha)


def _casar_alias(
    datos: dict, indice: IndicePersonas, empresa: int | None, fecha: int
) -> EmpleadoMatch:
    """R8: el DNI del alias o, vacio, el de su ficha; resuelto como R4-R5."""
    dni = tm.normalize_dni(datos.get("dni"))
    if not dni:
        ficha = indice.ficha(datos.get("ide"))
        dni = tm.normalize_dni(ficha.dni) if ficha is not None else ""
    if not dni:
        return EmpleadoMatch(method="alias_no_valido")
    res = indice.casar_por_dni(dni, empresa, fecha)
    if res.motivo == "ok":
        return _a_match(indice, indice.recurso(res.ide), 1.0, "alias")
    if res.motivo == "desconocido":
        return EmpleadoMatch(method="alias_no_valido")
    return EmpleadoMatch(method=f"dni_{res.motivo}")


def _casar_nombre(
    nombre: str | None,
    indice: IndicePersonas,
    matcher: EmpleadoMatcher,
    empresa: int | None,
    fecha: int,
) -> EmpleadoMatch:
    """R10-R12: la persona de nombre mas parecido entre los candidatos y,
    de sus recursos, el que da `casar_por_dni` (R11)."""
    candidatos = []
    for r in indice.candidatos_nombre(empresa, fecha):
        ficha = indice.ficha_enlazada(r)
        nombres = (r.nombre, ficha.nombre if ficha is not None else None)
        candidatos.append((indice.dni_de_recurso(r), nombres))
    persona, score, metodo = matcher.match_nombre(
        nombre=nombre, candidatos=candidatos)
    if persona is None:
        return EmpleadoMatch(method=metodo)
    res = indice.casar_por_dni(persona, empresa, fecha)
    if res.motivo != "ok":
        return EmpleadoMatch(method="nombre_ambiguo")
    return _a_match(indice, indice.recurso(res.ide), score, "nombre")


def _a_match(
    indice: IndicePersonas, r: RecursoRow | None, score: float, paso: str
) -> EmpleadoMatch:
    """R13-R14: la linea casada con el recurso `r`."""
    assert r is not None   # `casar_por_dni` solo da ides del indice
    ficha = indice.ficha_enlazada(r)
    if ficha is not None:
        ide, codigo, nombre, metodo = ficha.ide, ficha.codigo, ficha.nombre, paso
    else:
        ide, codigo, nombre = None, r.codigo, r.nombre
        metodo = "recurso_dni" if paso == "dni" else "recurso_nombre"
    return EmpleadoMatch(
        ide=ide, codigo=codigo, nombre=nombre,
        dni=indice.dni_de_recurso(r), reside=r.ide,
        score=round(score, 4), method=metodo,
    )
