# application/services/edicion_celda.py
"""F-049: plan de guardado de una celda de la matriz de obra (sv4).

La celda son las líneas de horas activas de una (obra, trabajador, fecha)
(`_celda` del repositorio). El popup del doble clic manda TODAS sus líneas
no congeladas con el valor que tenían al abrirse (`antes`) y el nuevo, más
la ordinaria y la extra «(nueva)» que falten. Este módulo decide, sin base
ni red, qué se escribe:

  - `cambios`: las líneas cuyo valor cambia (a 0 se quedan a 0, DA5);
  - `materializar`: las no congeladas de cada pareja automática de F-037
    tocada (`horas_orig` NULL y `extra_auto` falso): lo escrito pasa a
    ser «lo del parte» para sv3, que ya no restaura la base desde
    `horas_orig` ni borra la extra en su pasada (DA3);
  - `crear_ordinaria` / `crear_extra` desde la `plantilla` (R19, DA6);
  - `documentos`: los partes que se tocan, para el recálculo (R23).

Y cuándo la petición no vale: 422 si está mal formada o fuera de rango
(R11, R13, R35) y 409 si la celda cambió desde que se abrió (R12). La
congelación (R14), la espera del recálculo (R15) y el reparto `aplicando`
(R33) los mira antes el repositorio, en su misma sesión.

Núcleo puro: no importa nada del portal ni de la base.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

#: Tipos de línea de la celda (los del `t` de `data-regs`).
ORDINARIA, EXTRA = "n", "e"

#: Tolerancia de comparación de horas (el popup trabaja con medias horas).
EPSILON = 1e-9

#: Rangos de DA10.
MAX_HORAS = 24.0

MOTIVO_CELDA_CAMBIADA = ("La celda ha cambiado desde que la abriste: "
                         "recarga la página.")
MOTIVO_SIN_LINEAS = "No hay líneas que guardar."
MOTIVO_REPETIDAS = "La petición repite líneas de la celda."
MOTIVO_NO_NUMERO = "Las horas tienen que ser un número."
MOTIVO_RANGO_ORDINARIA = "Las horas ordinarias tienen que estar entre 0 y 24."
MOTIVO_RANGO_EXTRA = "Las horas extra tienen que estar entre −24 y 24."
MOTIVO_ORDINARIA_NUEVA = ("La ordinaria nueva tiene que ser mayor que 0 y "
                          "como mucho 24.")
MOTIVO_SIN_TRABAJADOR = ("Esta fila no tiene trabajador: se pueden editar "
                         "sus líneas, pero no añadirle otras.")


class CeldaInvalida(ValueError):
    """Petición rechazada; `str(e)` es el motivo para el usuario."""

    def __init__(self, motivo: str, status: int) -> None:
        super().__init__(motivo)
        self.status = status


@dataclass(frozen=True)
class LineaCelda:
    """Lo que el plan necesita de una línea de la celda."""

    id: int
    tipo: str                 # ORDINARIA | EXTRA
    horas: float
    congelada: bool
    extra_auto: bool
    con_orig: bool            # `horas_orig` no es NULL (base de F-037)
    clave: tuple              # clave de pareja de F-037
    document_id: str


@dataclass(frozen=True)
class Cambio:
    """Una línea enviada por el popup; `horas` None vale `antes` (R7)."""

    id: int
    antes: float
    horas: float | None


@dataclass(frozen=True)
class PlanCelda:
    cambios: tuple[tuple[int, float], ...]
    materializar: tuple[tuple[int, float], ...]
    plantilla_id: int | None
    crear_ordinaria: float | None
    crear_extra: float | None
    documentos: tuple[str, ...]

    @property
    def hay_algo(self) -> bool:
        """False si el guardado no escribe nada (R6: ni undo ni recálculo)."""
        return bool(self.cambios or self.materializar
                    or self.crear_ordinaria is not None
                    or self.crear_extra is not None)


def _numero(horas: object) -> float:
    if isinstance(horas, bool) or not isinstance(horas, (int, float)):
        raise CeldaInvalida(MOTIVO_NO_NUMERO, 422)
    valor = float(horas)
    if not math.isfinite(valor):
        raise CeldaInvalida(MOTIVO_NO_NUMERO, 422)
    return valor


def validar_horas(tipo: str, horas: object, *, nueva: bool = False) -> float:
    """R13 (DA10): ordinaria en [0, 24] (la nueva, en (0, 24]); extra en
    [−24, 24]. Lo que no es un número finito, 422."""
    valor = _numero(horas)
    if tipo == ORDINARIA:
        if nueva and not 0.0 < valor <= MAX_HORAS:
            raise CeldaInvalida(MOTIVO_ORDINARIA_NUEVA, 422)
        if not 0.0 <= valor <= MAX_HORAS:
            raise CeldaInvalida(MOTIVO_RANGO_ORDINARIA, 422)
        return valor
    if not -MAX_HORAS <= valor <= MAX_HORAS:
        raise CeldaInvalida(MOTIVO_RANGO_EXTRA, 422)
    return valor


def plantilla(celda: Sequence[LineaCelda]) -> LineaCelda | None:
    """R19: la primera no congelada por (ordinaria antes, `id`)."""
    libres = [linea for linea in celda if not linea.congelada]
    if not libres:
        return None
    return min(libres, key=lambda l: (l.tipo != ORDINARIA, l.id))


def _sin_repetir(valores) -> tuple:
    return tuple(dict.fromkeys(valores))


def planificar_celda(
    celda: Sequence[LineaCelda],
    cambios: Sequence[Cambio],
    nueva_ordinaria: float | None,
    nueva_extra: float | None,
    *,
    admite_nuevas: bool,
) -> PlanCelda:
    """El plan del guardado (design §4), o `CeldaInvalida`.

    Orden de las comprobaciones: forma (R11), rangos (R13), fila sin
    trabajador (R35), celda cambiada (R12: ids, `antes` y nuevas)."""
    if not cambios:
        raise CeldaInvalida(MOTIVO_SIN_LINEAS, 422)
    ids = [c.id for c in cambios]
    if len(set(ids)) != len(ids):
        raise CeldaInvalida(MOTIVO_REPETIDAS, 422)

    por_id = {linea.id: linea for linea in celda}
    valores: dict[int, float] = {}
    for c in cambios:
        horas = c.antes if c.horas is None else c.horas
        linea = por_id.get(c.id)
        if linea is None:
            _numero(horas)
            continue
        valores[c.id] = validar_horas(linea.tipo, horas)

    crear_ordinaria = None
    if nueva_ordinaria is not None:
        crear_ordinaria = validar_horas(ORDINARIA, nueva_ordinaria,
                                        nueva=True)
    crear_extra = None
    if nueva_extra is not None:
        crear_extra = validar_horas(EXTRA, nueva_extra)
        if crear_extra == 0.0:
            crear_extra = None          # DA5: una nueva a 0 no crea
    if not admite_nuevas and (crear_ordinaria is not None
                              or crear_extra is not None):
        raise CeldaInvalida(MOTIVO_SIN_TRABAJADOR, 422)

    libres = [linea for linea in celda if not linea.congelada]
    if set(ids) != {linea.id for linea in libres}:
        raise CeldaInvalida(MOTIVO_CELDA_CAMBIADA, 409)
    for c in cambios:
        if abs(_numero(c.antes) - por_id[c.id].horas) > EPSILON:
            raise CeldaInvalida(MOTIVO_CELDA_CAMBIADA, 409)
    tipos = {linea.tipo for linea in celda}
    if ((crear_ordinaria is not None and ORDINARIA in tipos)
            or (crear_extra is not None and EXTRA in tipos)):
        raise CeldaInvalida(MOTIVO_CELDA_CAMBIADA, 409)

    cambiadas = [linea for linea in libres
                 if abs(valores[linea.id] - linea.horas) > EPSILON]
    tocadas = {linea.clave for linea in cambiadas
               if linea.extra_auto or linea.con_orig}
    materializadas = [linea for linea in libres if linea.clave in tocadas]
    # Hay al menos una libre (los ids no son vacíos y son las libres), así
    # que siempre hay plantilla.
    base = plantilla(libres)
    documentos = [linea.document_id for linea in cambiadas]
    documentos += [linea.document_id for linea in materializadas]
    if crear_ordinaria is not None or crear_extra is not None:
        documentos.append(base.document_id)
    return PlanCelda(
        cambios=tuple((l.id, valores[l.id]) for l in cambiadas),
        materializar=tuple((l.id, valores[l.id]) for l in materializadas),
        plantilla_id=base.id,
        crear_ordinaria=crear_ordinaria,
        crear_extra=crear_extra,
        documentos=_sin_repetir(documentos),
    )
