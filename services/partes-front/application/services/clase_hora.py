# application/services/clase_hora.py
"""F-066: la clase de una hora de Sigrid (extra u ordinaria) por su código.

Único sitio de sv4 donde viven la regla y la lista de códigos excluidos
(DA1); el SQL (`condicion_sql_extra`) y el Python se derivan de las dos
constantes de abajo, así que cambiarlas basta para todo sv4.

- **Regla de extra**: un código no excluido es extra si, sin espacios a los
  lados y en mayúsculas, empieza por `PREFIJO_EXTRA`. Sin código (None,
  vacío o espacios) la clase no se sabe (`None`).
- **`auxhor.ext` no decide nada**: está a 0 en todos los códigos de Sigrid
  (M1 de F-066, 2026-11-06); se guarda como dato informativo.

Sin E/S: regla de dominio pura, como `congelacion.py`. sv3 y sv5 tendrán su
propio sitio único en F-067.

F-085 (R1): también es el único sitio de sv4 que decide si un código es de
incidencia (`es_codigo_incidencia`: empieza por `PREFIJO_INCIDENCIA` y no
es el fin) o el fin de una racha (`es_codigo_fin`: `CODIGO_FIN`).
`tipo_hora_de_codigo` no cambia: un CI* lo convierte `conversion_clase`.
"""
from __future__ import annotations

import re

#: Prefijo de las horas extra en `auxhor.cod` (HECAP, HEGR, HEOF, HEPE...).
PREFIJO_EXTRA = "HE"

#: F-085 (R1): prefijo de los códigos de incidencia de `auxhor` (CIA, CIV...).
PREFIJO_INCIDENCIA = "CI"

#: F-085 (R1): código del fin de una racha de incidencia; lo pone el sistema.
CODIGO_FIN = "CIZ"

#: Códigos de `auxhor` que la app no usa: no se ofrecen, no se asignan, no
#: se eligen ni cuentan como extra. Decisión del humano del 2026-11-06
#: («HENC no debe ser tenido en cuenta por la app»): `HENC` «HORA
#: ENCARGADO» (`auxhor` ide 63) empieza por `HE` sin ser extra; 1 uso manual
#: de 2022 en `hmores` y 0 filas en `reshor` (M1).
CODIGOS_EXCLUIDOS: tuple[str, ...] = ("HENC",)

#: Columna SQL admisible: identificador o `tabla.columna`.
_COLUMNA = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?")


def _normaliza(codigo: str | None) -> str:
    return (codigo or "").strip().upper()


def es_excluido(codigo: str | None) -> bool:
    """R1: si el código es uno de los que la app no usa."""
    cod = _normaliza(codigo)
    return bool(cod) and cod in CODIGOS_EXCLUIDOS


def es_hora_extra(codigo: str | None) -> bool | None:
    """R2: True si es extra, False si es ordinaria o excluido, None sin
    código."""
    cod = _normaliza(codigo)
    if not cod:
        return None
    if es_excluido(cod):
        return False
    return cod.startswith(PREFIJO_EXTRA)


def es_codigo_fin(codigo: str | None) -> bool:
    """F-085 (R1): True solo para `CODIGO_FIN`, sin espacios y en
    mayúsculas."""
    return _normaliza(codigo) == CODIGO_FIN


def es_codigo_incidencia(codigo: str | None) -> bool:
    """F-085 (R1): True si, normalizado, empieza por `PREFIJO_INCIDENCIA`,
    es más largo que el prefijo y no es el fin (`CIZ`)."""
    cod = _normaliza(codigo)
    return (len(cod) > len(PREFIJO_INCIDENCIA)
            and cod.startswith(PREFIJO_INCIDENCIA)
            and not es_codigo_fin(cod))


def tipo_hora_de_codigo(codigo: str | None) -> str | None:
    """El `tipo_hora` del portal para un código: `extra`, `normal` o None
    si no se sabe (sin código)."""
    extra = es_hora_extra(codigo)
    if extra is None:
        return None
    return "extra" if extra else "normal"


def condicion_sql_extra(columna: str) -> str:
    """R4: el predicado T-SQL de `es_hora_extra` sobre `columna`.

    Solo lleva constantes de este módulo y una columna validada como
    identificador (`ValueError` si no): nada de lo que llega de fuera entra
    en el SQL."""
    if not isinstance(columna, str) or not _COLUMNA.fullmatch(columna):
        raise ValueError(f"columna SQL no válida: {columna!r}")
    expr = f"UPPER(LTRIM(RTRIM({columna})))"
    condicion = f"{expr} LIKE '{PREFIJO_EXTRA}%'"
    if CODIGOS_EXCLUIDOS:
        lista = ", ".join(f"'{c}'" for c in CODIGOS_EXCLUIDOS)
        condicion += f" AND {expr} NOT IN ({lista})"
    return condicion
