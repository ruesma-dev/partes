# application/services/casado_recurso.py
"""F-036: casa el trabajador leido contra los RECURSOS persona (R4-R14).

El casado de la ingesta elige recurso, de la misma lista que despues usa
el conciliador (`IndicePersonas`, recursos con `res.cla = 1`): los de alta
a la fecha del parte y de su empresa (sin empresa, de cualquiera), con o
sin DNI del recurso (el de su ficha y, si no, `res.cif`; DA1). F-040: quien
no tiene DNI compite por su clave de persona y, si gana, solo se PROPONE
(`nombre_sin_dni`); su alias aprendido si casa (R7-R8).

Orden (el de siempre): DNI leido -> alias aprendido -> similitud de
nombre. Un DNI con recursos persona pero sin candidato unico CIERRA la
linea sin casar (`dni_<motivo>`), sin seguir al alias ni al nombre (R5); y
tambien el de una persona que Sigrid conoce (ficha o recurso) sin ningun
recurso persona (`dni_sin_recurso`, R6, decision del humano 2026-10-07).
Solo un DNI que Sigrid no conoce sigue al alias y al nombre.

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
from application.services.seleccion_sigrid import (
    PREFIJO_FICHA,
    PREFIJO_RECURSO,
    IndicePersonas,
)
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import RecursoRow

#: F-040 (R3, DA1): gana por nombre una persona SIN DNI: se propone en
#: Conciliar, no se casa (sin `ide` ni `reside`; la linea sube a revision).
METODO_NOMBRE_SIN_DNI = "nombre_sin_dni"

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
    candidatos: Callable[[], list[RecursoRow]] | None = None,
) -> EmpleadoMatch:
    """R4-R14: el casado de una linea (ver cabecera).

    `candidatos` da los candidatos por nombre ya calculados (el pipeline los
    calcula una vez por parte); sin el, `indice.candidatos_nombre`."""
    # 1. DNI leido (R4-R6).
    if dni_leido:
        res = indice.casar_por_dni(dni_leido, empresa, fecha)
        if res.motivo == "ok":
            return _a_match(indice, indice.recurso(res.ide), 1.0, "dni")
        if res.motivo in _MOTIVOS_QUE_CIERRAN:
            return EmpleadoMatch(method=f"dni_{res.motivo}")
        # R6 (humano, 2026-10-07, opcion A): una persona que Sigrid conoce
        # pero sin ningun recurso persona tampoco sigue al alias ni al
        # nombre, que podrian casar a OTRA persona: a Conciliar.
        if indice.dni_conocido(dni_leido):
            return EmpleadoMatch(method="dni_sin_recurso")
    # 2. Alias aprendido (R8).
    datos = alias() if alias is not None else None
    if datos is not None:
        return _casar_alias(datos, indice, empresa, fecha)
    # 3. Similitud de nombre (R10-R12).
    if candidatos is None:
        recursos = indice.candidatos_nombre(empresa, fecha)
    else:
        recursos = candidatos()
    return _casar_nombre(nombre_leido, recursos, indice, matcher, empresa,
                         fecha)


def _casar_alias(
    datos: dict, indice: IndicePersonas, empresa: int | None, fecha: int
) -> EmpleadoMatch:
    """R8: el DNI del alias o, vacio, el de su ficha; resuelto como R4-R5.

    F-040 (R7-R8): si tampoco, el DNI del recurso de su `recurso_ide`; y
    sin ningun DNI, por su clave de persona (`_casar_alias_sin_dni`)."""
    dni = tm.normalize_dni(datos.get("dni"))
    if not dni:
        ficha = indice.ficha(datos.get("ide"))
        dni = tm.normalize_dni(ficha.dni) if ficha is not None else ""
    if not dni:
        recurso = indice.recurso(datos.get("recurso_ide"))
        dni = indice.dni_de_recurso(recurso) if recurso is not None else ""
    if not dni:
        return _casar_alias_sin_dni(datos, indice, empresa, fecha)
    res = indice.casar_por_dni(dni, empresa, fecha)
    if res.motivo == "ok":
        return _a_match(indice, indice.recurso(res.ide), 1.0, "alias")
    if res.motivo == "desconocido":
        return EmpleadoMatch(method="alias_no_valido")
    return EmpleadoMatch(method=f"dni_{res.motivo}")


def _casar_alias_sin_dni(
    datos: dict, indice: IndicePersonas, empresa: int | None, fecha: int
) -> EmpleadoMatch:
    """F-040 (R8): el alias de quien no tiene DNI, por su clave: `res:` con
    `recurso_ide`; si no, `emp:` con ficha. `ok` casa con score 1.0
    (`alias` con ficha, `recurso_nombre` sin ella); cualquier otro motivo
    es `alias_no_valido`, sin seguir al nombre."""
    if datos.get("recurso_ide") is not None:
        clave = f"{PREFIJO_RECURSO}{datos['recurso_ide']}"
    elif datos.get("ide") is not None:
        clave = f"{PREFIJO_FICHA}{datos['ide']}"
    else:
        return EmpleadoMatch(method="alias_no_valido")
    res = indice.casar_por_clave(clave, empresa, fecha)
    if res.motivo != "ok":
        return EmpleadoMatch(method="alias_no_valido")
    return _a_match(indice, indice.recurso(res.ide), 1.0, "alias")


def _casar_nombre(
    nombre: str | None,
    recursos: list[RecursoRow],
    indice: IndicePersonas,
    matcher: EmpleadoMatcher,
    empresa: int | None,
    fecha: int,
) -> EmpleadoMatch:
    """R10-R12: la persona de nombre mas parecido entre los candidatos y,
    de sus recursos, el que da `casar_por_dni` (R11). F-040 (R2-R4): la
    persona es su clave (`clave_persona`); si gana una sin DNI, se propone
    (`nombre_sin_dni`) y no se casa."""
    candidatos = []
    for r in recursos:
        ficha = indice.ficha_enlazada(r)
        nombres = (r.nombre, ficha.nombre if ficha is not None else None)
        candidatos.append((indice.clave_persona(r), nombres))
    persona, score, metodo = matcher.match_nombre(
        nombre=nombre, candidatos=candidatos)
    if persona is None:
        return EmpleadoMatch(method=metodo)
    if persona.startswith((PREFIJO_FICHA, PREFIJO_RECURSO)):
        # F-040 (R3, DA1): sin DNI nada confirma la identidad salvo el
        # nombre leido: se PROPONE en Conciliar, no se casa.
        return EmpleadoMatch(method=METODO_NOMBRE_SIN_DNI)
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
        # F-040 (R12): sin DNI del recurso, NULL y no cadena vacia.
        dni=indice.dni_de_recurso(r) or None, reside=r.ide,
        score=score, method=metodo,
    )
