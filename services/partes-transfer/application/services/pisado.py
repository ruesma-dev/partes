# application/services/pisado.py
"""F-053 · Pisar sin borrar: que linea de Sigrid choca y que se dice
cuando no se puede pisar (regla pura, design §5).

Regla del humano: en Sigrid no se borra. Pisar un conflicto confirmado
pone la linea existente a 0 (`can = 0`, `tot = 0`, `stmt_anular_linea`)
y escribe la nueva. De ahi:

  - `choques` (R5, DA5): solo choca una linea CON HORAS; una a 0 (pisada
    antes o anulada a mano) no es conflicto ni omision `parte_cerrado`.
    Excepcion: si la linea a escribir es una incidencia (semantica 4,
    siempre sin horas), cuenta la linea, no `can`.
  - `motivo_incidencia_en_sigrid` (R6, DA6): incidencia contra la misma
    incidencia; ponerla a 0 no cambia nada y pisarla la duplicaria.
  - `motivo_linea_enlazada` (R7, DA4): la linea que choca esta enlazada
    (albaran, factura, dedicacion o nomina) y no se pone a 0.
  - `origen_linea` (R13): `partes`, `ajena` o `manual`, para el INFO de
    cada pisada a 0.
  - F-056 (R31): la linea de ajuste de una franquicia
    (`partes:franquicia:<id>`) no choca con nada: ni se ofrece para pisar
    ni deja `parte_cerrado` a la extra real del dia.

Motivos sin tildes como el resto de sv5, sin nombres ni DNIs y de 255
caracteres como mucho (`sigrid_motivo` de sv4). No lee ni escribe; solo
importa de `domain`: el prefijo `partes:` se repite aqui a proposito y un
test lo ata al `PREFIJO_SYNCKEY` del cliente.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from domain.models.registro_models import (
    AccionLinea,
    LineaSigrid,
    es_synckey_franquicia,
)

#: Prefijo del motivo de una incidencia que ya consta en Sigrid (R6).
MOTIVO_INCIDENCIA_EN_SIGRID = "incidencia_en_sigrid"

#: Prefijo del motivo de un choque con una linea enlazada (R7).
MOTIVO_LINEA_ENLAZADA = "linea_enlazada"

#: Largo maximo de un motivo (`parte_registro.sigrid_motivo` de sv4); el
#: mismo que `parte_abierto.LIMITE_MOTIVO` (lo fija un test).
LIMITE_MOTIVO = 255

#: Prefijo de las synckeys de este proyecto (`PREFIJO_SYNCKEY` del cliente).
PREFIJO_PARTES = "partes:"


def tiene_horas(ls: LineaSigrid) -> bool:
    """`can` no nulo y distinto de 0: el `ISNULL(p.can, 0) <> 0` de F-034
    R4 (una linea con horas negativas tambien tiene horas)."""
    return ls.can is not None and float(ls.can) != 0


def es_incidencia(hora_codigo: str | None) -> bool:
    """Codigo de hora de incidencia (`CI*`, semantica 4)."""
    return (hora_codigo or "").strip().upper().startswith("CI")


def choques(lineas: Iterable[LineaSigrid], accion: AccionLinea,
            mias: set[str]) -> list[LineaSigrid]:
    """Lineas AJENAS del mismo recurso, dia y CODIGO DE HORA que la accion
    (pisar las ordinarias de un dia no toca sus extra) y, salvo que la
    accion sea una incidencia, con horas (R5). F-056 (R31): nunca la linea
    de ajuste de una franquicia."""
    incidencia = es_incidencia(accion.hora_codigo)
    return [ls for ls in lineas
            if ls.reside == accion.recurso_ide
            and ls.fecha_int == accion.fecha_int
            and int(ls.horide or 0) == int(accion.hora_ide or 0)
            and not (ls.synckey and ls.synckey in mias)
            and not es_synckey_franquicia(ls.synckey)
            and (incidencia or tiene_horas(ls))]


def origen_linea(synckey: str | None) -> str:
    """R13: `partes` (escrita por este proyecto), `ajena` (otra synckey,
    p. ej. `porcentajes:`) o `manual` (sin synckey)."""
    sk = (synckey or "").strip()
    if not sk:
        return "manual"
    return "partes" if sk.startswith(PREFIJO_PARTES) else "ajena"


def nombrar_lineas(ides: Sequence[int]) -> tuple[str, bool]:
    """«linea 9001» o «lineas 9001, 9002» (ordenadas, sin repetir) y si es
    plural, para concordar el resto del motivo."""
    unicos = sorted({int(i) for i in ides})
    if len(unicos) > 1:
        return "lineas " + ", ".join(str(i) for i in unicos), True
    return f"linea {unicos[0] if unicos else '?'}", False


def motivo_incidencia_en_sigrid(ides: Sequence[int],
                                parte_cod: str | None) -> str:
    """R6, R11: la incidencia ya esta en Sigrid ese dia; no se duplica."""
    lineas, _plural = nombrar_lineas(ides)
    return (f"{MOTIVO_INCIDENCIA_EN_SIGRID}: la incidencia ya consta en "
            f"Sigrid ese dia ({lineas} del parte {parte_cod or '?'}); no se "
            f"duplica")[:LIMITE_MOTIVO]


def motivo_linea_enlazada(ides: Sequence[int], parte_cod: str | None) -> str:
    """R7, R11: la linea que choca esta enlazada; no se pone a 0."""
    lineas, plural = nombrar_lineas(ides)
    n = "n" if plural else ""
    return (f"{MOTIVO_LINEA_ENLAZADA}: {'las' if plural else 'la'} {lineas} "
            f"del parte {parte_cod or '?'} tiene{n} ese dia las mismas "
            f"horas y esta{n} enlazada{'s' if plural else ''} (albaran, "
            f"factura, dedicacion o "
            f"nomina); no se pone{n} a 0. Corrige{'las' if plural else 'la'} "
            f"en Sigrid")[:LIMITE_MOTIVO]
