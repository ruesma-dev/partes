# application/services/pareja_extra.py
"""F-037: la base y sus extras automaticas se congelan juntas (sv3).

`apply_extras_splits` parte una linea ordinaria (la «base») en sus horas
de jornada y una `extra_auto` con el exceso, clonando en la extra los
cuatro campos de la clave de pareja: `(document_id, line_index,
empleado_line_no, fecha_int)`. Base y extras de una misma clave son una
«pareja».

`esta_congelado` responde por UNA linea (¿ya viajo a Sigrid?). El
recalculo de sv3, en cambio, trata la pareja entera: si un miembro esta
congelado, ninguno se revierte ni se vuelve a partir. Sin esto, con la
extra `registrado` y la base `omitido`, cada pasada restauraba la base, la
volvia a partir y creaba otra `extra_auto` (incidencia de la obra 0678,
01-03/10/2026). La regla por linea NO cambia (DA1): esto solo refina el
recalculo, que solo hace sv3.

Nucleo puro: sin base ni red. Recibe la congelacion por linea ya calculada
con `esta_congelado`, para que esa regla siga escrita una sola vez.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

#: `(document_id, line_index, empleado_line_no, fecha_int)`.
Clave = tuple[Any, Any, Any, Any]

_CAMPOS_CLAVE = ("document_id", "line_index", "empleado_line_no", "fecha_int")


def clave_pareja(fila: Mapping[str, Any]) -> Clave:
    """R1: la clave de pareja de una fila; `None` es un valor mas."""
    return tuple(fila.get(c) for c in _CAMPOS_CLAVE)  # type: ignore[return-value]


def es_miembro(*, extra_auto: bool, tipo_hora: str | None) -> bool:
    """R2: miembro de la pareja = extra automatica o base ordinaria.

    Una extra explicita (`extra_auto` falso y `tipo_hora` extra, p. ej. la
    de `crear_extra_desde` de sv4) o una incidencia comparten la clave pero
    no son de la pareja: ni la congelan ni se ven afectadas.
    """
    if extra_auto:
        return True
    return (tipo_hora or "").strip().lower() in ("", "normal")


@dataclass(frozen=True)
class FilaPareja:
    """Lo que el nucleo necesita de una fila de `parte_registros`."""

    registro_id: int
    clave: Clave
    extra_auto: bool
    miembro: bool
    congelada: bool          # `esta_congelado(...)` de la propia fila


def claves_congeladas(filas: Iterable[FilaPareja]) -> set[Clave]:
    """R3: claves con algun MIEMBRO congelado por si mismo."""
    return {f.clave for f in filas if f.miembro and f.congelada}


@dataclass(frozen=True)
class PlanRevert:
    """Que hace la reversion de extras con cada fila (R4-R8)."""

    borrar: tuple[int, ...]       # extra_auto a borrar (incluye duplicadas)
    restaurar: tuple[int, ...]    # bases: horas = horas_orig
    duplicadas: tuple[int, ...]   # subconjunto de `borrar` (R6)
    congeladas: int               # congeladas por si mismas (log de siempre)
    protegidas: int               # respetadas por su pareja (R8)
    dobles: tuple[tuple[Clave, int], ...]  # (clave, n) con n > 1 extras
    #                                       congeladas (R7)


def plan_revert(filas: Iterable[FilaPareja]) -> PlanRevert:
    """El plan de `revert_extras_auto`, en orden de `registro_id`.

    1. Fila congelada por si misma: no se toca.
    2. Miembro de una pareja congelada: si es `extra_auto` y la pareja ya
       tiene una extra congelada, es un duplicado y se borra (R6); si no,
       se respeta (R4 la base, R5 la extra de una base congelada).
    3. Resto, como siempre: `extra_auto` se borra, la base se restaura.
    """
    ordenadas = sorted(filas, key=lambda f: f.registro_id)
    congeladas_k = claves_congeladas(ordenadas)
    extras_congeladas = Counter(
        f.clave for f in ordenadas if f.extra_auto and f.congelada
    )
    borrar: list[int] = []
    restaurar: list[int] = []
    duplicadas: list[int] = []
    congeladas = 0
    protegidas = 0
    for f in ordenadas:
        if f.congelada:
            congeladas += 1
            continue
        if f.miembro and f.clave in congeladas_k:
            if f.extra_auto and extras_congeladas[f.clave]:
                borrar.append(f.registro_id)
                duplicadas.append(f.registro_id)
            else:
                protegidas += 1
            continue
        if f.extra_auto:
            borrar.append(f.registro_id)
        else:
            restaurar.append(f.registro_id)
    dobles = tuple((k, n) for k, n in extras_congeladas.items() if n > 1)
    return PlanRevert(
        borrar=tuple(borrar),
        restaurar=tuple(restaurar),
        duplicadas=tuple(duplicadas),
        congeladas=congeladas,
        protegidas=protegidas,
        dobles=dobles,
    )


# --------------------------------------------------------------------- #
# F-069: la pasada lee una vez, calcula en memoria y escribe en UNA
# transaccion. Las extras de una pareja se reutilizan en el sitio (mismo
# `id`) en vez de borrarse y crearse de nuevo.
# --------------------------------------------------------------------- #

#: R13: lo que decide el revert y el split de un miembro de la pareja. Si
#: cambia entre la lectura y la escritura, la pareja no se toca.
CAMPOS_HUELLA = (
    "registro_id", "horas", "horas_orig", "tipo_hora", "extra_auto",
    "sigrid_estado", "deleted_at_utc", "doc_approved", "doc_activo",
)

_CAMPOS_HORAS = ("horas", "horas_orig")
_CAMPOS_BOOL = ("extra_auto", "doc_approved", "doc_activo")


def vista_revertida(filas: list[dict], plan: PlanRevert) -> list[dict]:
    """R7, R11: las filas tal como quedarian tras `plan`, sin escribir.

    Copia de `filas` (en su orden) sin las de `plan.borrar` y con
    `horas = horas_orig`, `horas_orig = None` en las de `plan.restaurar`.
    No muta la entrada.
    """
    borrar = set(plan.borrar)
    restaurar = set(plan.restaurar)
    out: list[dict] = []
    for fila in filas:
        rid = fila.get("registro_id")
        if rid in borrar:
            continue
        copia = dict(fila)
        if rid in restaurar:
            copia["horas"] = copia.get("horas_orig")
            copia["horas_orig"] = None
        out.append(copia)
    return out


def _valor_huella(campo: str, valor: Any) -> Any:
    if campo in _CAMPOS_HORAS:
        return None if valor is None else round(float(valor), 6)
    if campo in _CAMPOS_BOOL:
        return bool(valor)
    return valor


def huellas_por_clave(
    filas: Iterable[Mapping[str, Any]],
) -> dict[Clave, frozenset[tuple]]:
    """R13: por clave de pareja, el conjunto de huellas de sus MIEMBROS.

    Las horas se redondean a 6 decimales (un float de ida y vuelta no es
    un cambio) y los booleanos se normalizan. Una clave sin miembros no
    tiene huella.
    """
    por_clave: dict[Clave, set[tuple]] = {}
    for fila in filas:
        if not es_miembro(extra_auto=bool(fila.get("extra_auto")),
                          tipo_hora=fila.get("tipo_hora")):
            continue
        huella = tuple(_valor_huella(c, fila.get(c)) for c in CAMPOS_HUELLA)
        por_clave.setdefault(clave_pareja(fila), set()).add(huella)
    return {k: frozenset(v) for k, v in por_clave.items()}


def emparejar_extras(
    splits: list[dict], candidatas: list[int],
) -> tuple[list[tuple[dict, int | None]], list[int]]:
    """R3, R5: que extra existente reutiliza cada split de una pareja.

    Splits por `normal_id` ascendente y candidatas por `id` ascendente: el
    k-esimo split sin `id` propio reutiliza la k-esima candidata. Un split
    con `id` (F-046) va con `None` (extra nueva con ese id) y no consume
    candidata; los splits sin candidata tambien van con `None`. Devuelve
    los pares, en orden de `normal_id`, y las candidatas sobrantes (a
    borrar), por id.
    """
    libres = sorted(candidatas)
    pares: list[tuple[dict, int | None]] = []
    for s in sorted(splits, key=lambda s: s["normal_id"]):
        if s.get("id") is not None or not libres:
            pares.append((s, None))
        else:
            pares.append((s, libres.pop(0)))
    return pares, libres


@dataclass(frozen=True)
class LecturaPasada:
    """Lo que `leer_pasada` entrega a la pasada (design §3).

    `registros`: la vista revertida, lo que hoy devolvia
    `fetch_registros_para_recurso` tras el revert. `huellas`: por clave,
    las del estado CRUDO leido (antes del revert en memoria).
    """

    registros: list[dict]
    huellas: dict[Clave, frozenset]
