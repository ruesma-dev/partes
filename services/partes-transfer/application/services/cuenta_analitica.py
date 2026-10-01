# application/services/cuenta_analitica.py
"""F-021 · Cuenta analitica de una linea que sv5 escribe en Sigrid (pura).

Regla medida contra las lineas tecleadas a mano (99,64 % de coincidencia,
`progress/explore_F-021_sigrid.md`):

  - ORIGEN (R1-R2): la cuenta de la ficha del recurso para el tipo de hora
    que se ESCRIBE (`reshor.caaide`); si ese tipo no tiene, la de su tipo
    por defecto (`res.horide`). De ella solo vale la SUBCUENTA: el texto
    tras el primer punto del codigo `<centro>.<subcuenta>`.
  - DESTINO (R4): la cuenta `caa` del CENTRO DE LA OBRA destino, de su
    empresa, con esa subcuenta. Nunca el `ide` de la plantilla.
  - SIN CUENTA (R3, R5, R6): `caa_ide = 0` y la linea se escribe igual
    (R8). Solo se avisa cuando se puede arreglar en la obra (R5, R6).

Ni `res.caaide`, ni `emp.caaide`, ni la cuenta de la partida, ni
`auxhor.caacod` intervienen (R7): esta funcion no los recibe.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from domain.models.registro_models import HoraRecurso

MOTIVO_RECURSO_SIN_CUENTA = "recurso_sin_cuenta"   # R3 (sin aviso)
MOTIVO_OBRA_SIN_CUENTA = "obra_sin_cuenta"         # R5 (con aviso)
MOTIVO_CUENTA_AMBIGUA = "cuenta_ambigua"           # R6 (con aviso)


def subcuenta(cod: str | None) -> str | None:
    """Texto tras el PRIMER punto de `cod`, sin espacios a los lados.

    None si el codigo esta vacio, no tiene punto o no hay nada tras el."""
    # Sin punto, `partition` deja `resto` vacio: basta con mirar el resto.
    return (cod or "").partition(".")[2].strip() or None


def subcuenta_de_linea(horas: list[HoraRecurso],
                       horide: int | None) -> str | None:
    """R1: subcuenta de la plantilla del tipo de hora escrito; si no hay,
    R2: la del tipo por defecto del recurso. None si ninguna da (R3)."""
    for h in horas:
        if h.horide == horide:
            sub = subcuenta(h.caa_cod)
            if sub:
                return sub
    for h in horas:
        if h.defecto:
            sub = subcuenta(h.caa_cod)
            if sub:
                return sub
    return None


@dataclass(frozen=True)
class CuentaLinea:
    """Cuenta resuelta para una linea. `caa_ide = 0` = sin cuenta."""
    caa_ide: int
    caa_cod: str | None
    motivo: str | None      # None = cuenta resuelta
    aviso: str | None       # solo R5 y R6


def indexar_cuentas(
    filas: Iterable[tuple[int, str | None]]
) -> dict[str, list[tuple[int, str]]]:
    """Agrupa `(caaide, cod)` por la subcuenta de `cod` (misma `subcuenta`
    que el origen); descarta las que no tienen."""
    out: dict[str, list[tuple[int, str]]] = {}
    for ide, cod in filas:
        sub = subcuenta(cod)
        if sub:
            out.setdefault(sub, []).append((int(ide), str(cod).strip()))
    return out


def resolver_cuenta(sub: str | None,
                    cuentas: dict[str, list[tuple[int, str]]],
                    obra_cod: str | None) -> CuentaLinea:
    """R3-R6: la unica cuenta del centro de la obra con esa subcuenta."""
    if not sub:
        return CuentaLinea(0, None, MOTIVO_RECURSO_SIN_CUENTA, None)
    candidatas = cuentas.get(sub, [])
    if not candidatas:
        return CuentaLinea(
            0, None, MOTIVO_OBRA_SIN_CUENTA,
            f"la obra {obra_cod} no tiene la cuenta analitica .{sub}: la "
            f"linea ira sin cuenta")
    if len(candidatas) > 1:
        return CuentaLinea(
            0, None, MOTIVO_CUENTA_AMBIGUA,
            f"la obra {obra_cod} tiene varias cuentas .{sub}: la linea ira "
            f"sin cuenta")
    ide, cod = candidatas[0]
    return CuentaLinea(ide, cod, None, None)
