# application/services/jornada_resolver.py
"""Jornada teorica (horas ordinarias esperadas por dia) del trabajador.

UN solo sitio con la regla, que el portal repetia en tres:

  - el KPI de CanDefecto de la vista trabajador,
  - los avisos de jornada incompleta de la matriz de obra,
  - la `jornada_sugerida` de `/api/sigrid/empleados`.

La regla es la de sv3 al reclasificar extras y NO cambia con F-003: el
`candef` de Sigrid manda si esta informado (estrictamente por encima del
minimo); si no, la jornada por defecto. Un `candef` de 0/1/2 significa
"Sigrid no lo tiene informado", no "este hombre trabaja dos horas": sin
el umbral, el dia entero se iria a horas extra.

F-003 deja aqui el ENCHUFE para la jornada real del contrato (Sesame).
Hoy no se puede: `GET /api/v1/jornada` de sesame-api devuelve el tipo de
jornada y si es reducida, pero NO las horas (peticion P1 del design). En
cuanto las exponga, la implementacion Sesame es un cambio local a esta
funcion mas el wiring, sin tocar los tres llamantes.
"""
from __future__ import annotations


def candef_valido(candef: float | str | None, *, minimo: float) -> bool:
    """True si Sigrid informa una jornada creible para el recurso.

    Es LA regla; `jornada_efectiva` y el KPI de la vista trabajador (que
    marca el valor como "asignado" cuando no sale de Sigrid) leen de aqui
    para no poder discrepar.
    """
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

    `candef` se tolera como texto (llega de Sigrid y de la BBDD) y como
    `None`. Cualquier valor no numerico se trata como no informado.
    """
    if not candef_valido(candef, minimo=minimo):
        return float(por_defecto)
    return float(candef)  # type: ignore[arg-type]
