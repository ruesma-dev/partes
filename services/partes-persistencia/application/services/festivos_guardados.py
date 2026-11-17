# application/services/festivos_guardados.py
"""Festivos de cada trabajador guardados en `festivos_trabajador` (F-032).

Cascada de lectura (DA19 = B) y formato de `festivos_json`, en un modulo
PURO (solo biblioteca estandar):

  - DNI no vacio con fila ⇒ esa fila, fuente ``sesame``.
  - Sin fila, o sin DNI ⇒ ``(None, "sin_fila")``: el llamante usa SU
    respaldo de siempre (sv3 el JSON local; sv4 ``holidays``). Sin DNI no
    se lee la tabla.

``festivos_json`` es ``{fecha ISO: nombre o null}`` con solo dias de su
ano y claves ordenadas.

GEMELO (DA20, lista cerrada de ``CLAUDE.md``): vive igual en sv3
(``partes-persistencia``) y sv4 (``partes-front``). Lo vigila
``tests/test_f032_festivos_guardados_gemelos.py``. Quien toque una copia
cambia LAS DOS en la misma feature.

El DNI es un dato personal: ningun mensaje de error de este modulo lo
lleva (R3).
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

FUENTE_SESAME = "sesame"
FUENTE_SIN_FILA = "sin_fila"


@dataclass(frozen=True)
class FilaFestivos:
    """Una fila de `festivos_trabajador`: los festivos de un (DNI, ano)."""
    dni_norm: str
    ano: int
    festivos: Mapping[str, str | None]
    leido_en_utc: str


def _fecha_del_ano(valor: Any, ano: int) -> str | None:
    """La fecha ISO ``YYYY-MM-DD`` si ``valor`` es un dia valido de ``ano``."""
    if not isinstance(valor, str):
        return None
    try:
        dia = _dt.date.fromisoformat(valor[:10])
    except ValueError:
        return None
    return dia.isoformat() if dia.year == ano else None


def _nombre(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def del_ano(pares: Iterable[tuple[Any, Any]], ano: int) -> dict[str, str | None]:
    """``{fecha ISO: nombre}`` de los pares ``(fecha, nombre)`` de ``ano``.

    Descarta fechas de otro ano o imposibles; recorta la hora de un ISO
    con hora y deja ``None`` un nombre vacio. Ordenado por fecha.
    """
    out: dict[str, str | None] = {}
    for fecha, nombre in pares:
        dia = _fecha_del_ano(fecha, ano)
        if dia is not None:
            out[dia] = _nombre(nombre)
    return dict(sorted(out.items()))


def a_json(festivos: Mapping[str, str | None]) -> str:
    """El texto de ``festivos_json``: claves ordenadas, tildes tal cual."""
    return json.dumps(dict(festivos), ensure_ascii=False, sort_keys=True)


def fila_de(
    dni_norm: str, ano: int, festivos_json: str, leido_en_utc: str
) -> FilaFestivos:
    """Una fila leida de la tabla; ``ValueError`` si esta mal formada.

    Mal formada: sin DNI, ano no entero positivo, JSON que no es un objeto,
    una clave que no es un dia ISO exacto de ``ano`` o un nombre que no es
    texto ni null.
    """
    if not isinstance(dni_norm, str) or not dni_norm:
        raise ValueError("fila de festivos sin DNI")
    if isinstance(ano, bool) or not isinstance(ano, int) or ano <= 0:
        raise ValueError(f"fila de festivos con ano invalido: {ano!r}")
    try:
        datos = json.loads(festivos_json)
    except (TypeError, ValueError) as exc:
        raise ValueError("festivos_json no es JSON") from exc
    if not isinstance(datos, dict):
        raise ValueError("festivos_json no es un objeto")
    festivos: dict[str, str | None] = {}
    for fecha, nombre in datos.items():
        if _fecha_del_ano(fecha, ano) != fecha:
            raise ValueError(f"festivos_json con una fecha invalida: {fecha!r}")
        if nombre is not None and not isinstance(nombre, str):
            raise ValueError(f"festivos_json con un nombre invalido en {fecha}")
        festivos[fecha] = nombre
    return FilaFestivos(dni_norm=dni_norm, ano=ano,
                        festivos=dict(sorted(festivos.items())),
                        leido_en_utc=str(leido_en_utc))


def elegir(
    dni_norm: str | None,
    ano: int,
    leer: Callable[[str, int], FilaFestivos | None],
) -> tuple[FilaFestivos | None, str]:
    """La cascada de lectura (DA19 = B).

    ``leer(dni_norm, ano)`` da la fila o ``None``; si lanza, el error sube
    tal cual y el llamante decide (respaldo + WARNING).
    """
    if not dni_norm:
        return None, FUENTE_SIN_FILA
    fila = leer(dni_norm, ano)
    if fila is None:
        return None, FUENTE_SIN_FILA
    return fila, FUENTE_SESAME
