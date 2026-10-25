# application/services/relectura_cabecera.py
"""F-058 · Reglas puras de la relectura de la cabecera (sv2).

Si la lectura primaria trae trabajadores y su cabecera sale vacía (sin obra
ni fecha) o su obra no existe en Sigrid, el pipeline relee el documento con
otro proveedor (``design.md`` §4.4). Aquí solo se decide, sin red ni IA:

- ``motivo_relectura``: si hay que releer y por qué (``cabecera_vacia`` u
  ``obra_inexistente``), en ese orden y sin consultar Sigrid con la cabecera
  vacía (R2–R4).
- ``resultado_relectura``: si la cabecera releída es útil (``aplicada``) o
  no (``vacia`` / ``no_casa``), con como mucho una consulta más (R8).

La existencia de una obra llega como ``ExisteObra``: ``True``/``False`` o
``None`` («no se sabe», R9), que nunca cuenta como inexistente. No es la
conciliación de sv3: no elige obra ni empresa (R11).
"""
from __future__ import annotations

import unicodedata
from typing import Any, Callable, Mapping

MOTIVO_CABECERA_VACIA = "cabecera_vacia"
MOTIVO_OBRA_INEXISTENTE = "obra_inexistente"

RESULTADO_APLICADA = "aplicada"
RESULTADO_VACIA = "vacia"
RESULTADO_NO_CASA = "no_casa"
RESULTADO_ERROR = "error"

#: Dice si existe una obra con ese código: True / False / None = «no se sabe».
ExisteObra = Callable[[str], bool | None]


def es_vacio(valor: object) -> bool:
    """``None`` o una cadena con solo espacios (R5)."""
    return valor is None or (isinstance(valor, str) and not valor.strip())


def clave_obra(codigo: object) -> str:
    """Clave con la que se compara un código de obra.

    Sin acentos, en mayúsculas y sin espacios ni guiones; si queda solo de
    dígitos, sin ceros a la izquierda (``"00672"`` → ``"672"``, ``"000"`` →
    ``"0"``). ``""`` si el código es vacío.
    """
    if es_vacio(codigo):
        return ""
    texto = unicodedata.normalize("NFKD", str(codigo))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = "".join(texto.upper().split()).replace("-", "")
    if texto.isdigit():
        return texto.lstrip("0") or "0"
    return texto


def _cabecera(data: Mapping[str, Any]) -> Mapping[str, Any] | None:
    cabecera = data.get("cabecera")
    return cabecera if isinstance(cabecera, Mapping) else None


def obra_de(data: Mapping[str, Any]) -> Any:
    """``cabecera.obra_numero`` tal cual, o ``None`` sin cabecera."""
    cabecera = _cabecera(data)
    return None if cabecera is None else cabecera.get("obra_numero")


def cabecera_vacia(data: Mapping[str, Any]) -> bool:
    """Obra y fecha vacías; sin cabecera (o no es un dict) también."""
    cabecera = _cabecera(data)
    if cabecera is None:
        return True
    return es_vacio(cabecera.get("obra_numero")) and es_vacio(cabecera.get("fecha"))


def con_trabajadores(data: Mapping[str, Any]) -> bool:
    """``empleados`` es una lista con al menos un elemento."""
    empleados = data.get("empleados")
    return isinstance(empleados, list) and len(empleados) >= 1


def motivo_relectura(data: Mapping[str, Any], existe: ExisteObra) -> str | None:
    """Motivo para releer la lectura primaria, o ``None`` (R2–R4).

    Sin trabajadores no hay motivo; con la cabecera vacía, ``cabecera_vacia``
    sin llamar a ``existe``; con obra, ``obra_inexistente`` solo si ``existe``
    responde ``False`` (``None`` es «no se sabe», R9).
    """
    if not con_trabajadores(data):
        return None
    if cabecera_vacia(data):
        return MOTIVO_CABECERA_VACIA
    obra = obra_de(data)
    if es_vacio(obra):
        return None
    if existe(obra) is False:
        return MOTIVO_OBRA_INEXISTENTE
    return None


def resultado_relectura(
    motivo: str,
    data_relectura: Mapping[str, Any],
    existe: ExisteObra,
    obra_primaria: object,
) -> str:
    """Si la relectura es útil (``aplicada``) o no (R8, R12, R13, R16).

    ``cabecera_vacia``: útil si la cabecera releída no es vacía; nunca
    consulta. ``obra_inexistente``: sin obra releída, ``vacia``; con la misma
    clave que la primaria, ``no_casa`` sin consultar; si no, ``aplicada``
    solo si ``existe`` responde ``True``.
    """
    if motivo == MOTIVO_CABECERA_VACIA:
        if cabecera_vacia(data_relectura):
            return RESULTADO_VACIA
        return RESULTADO_APLICADA
    obra = obra_de(data_relectura)
    if es_vacio(obra):
        return RESULTADO_VACIA
    if clave_obra(obra) == clave_obra(obra_primaria):
        return RESULTADO_NO_CASA
    if existe(obra) is True:
        return RESULTADO_APLICADA
    return RESULTADO_NO_CASA
