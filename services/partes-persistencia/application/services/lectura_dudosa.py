# application/services/lectura_dudosa.py
"""F-051 (R13-R17): ¿es dudosa la LECTURA que hizo sv2 de la tabla?

Caso que lo motiva: en una tabla de personal casi vacia (fin de semana) el
modelo de IA subio cada cifra una fila con confianza 95. sv3 caso bien a
cada persona por DNI, asi que el error no se ve en el casado: hay que
mirar el payload de sv2. Dos motivos, cada uno como mucho una vez:

  - `autocomprobacion_fila` (R13): una fila con horas cuyo
    `numero_linea_horas` (el "Nº" que el modelo leyo partiendo de la cifra)
    no coincide con su `numero_linea`. Si el campo no viene (partes
    anteriores a F-051 o un proveedor que lo omita), no salta (R16).
  - `tabla_dispersa` (R14, interruptor `REVISAR_TABLA_DISPERSA`): alguna
    fila con horas y alguna fila con trabajador (nombre o DNI) sin horas ni
    incidencia: es justo la tabla en la que se desplazan las cifras.

Puro sobre las filas tal como llegan de sv2 (R17): sin Sigrid, sin BBDD y
sin calendario. Las filas que no son dict se ignoran. La tolerancia de
tipos (numero como texto, coma decimal) es la del `ParteNormalizer`.
"""
from __future__ import annotations

from typing import Any

from domain.models.parte_records import MotivoLectura

MOTIVO_AUTOCOMPROBACION = "autocomprobacion_fila"
MOTIVO_TABLA_DISPERSA = "tabla_dispersa"


def _a_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _a_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _con_texto(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _tiene_horas(fila: dict[str, Any]) -> bool:
    """Ordinaria o extra no nula y distinta de 0 (la negativa cuenta)."""
    return bool(_a_float(fila.get("horas_ordinarias"))
                or _a_float(fila.get("horas_extraordinarias")))


def _tiene_trabajador(fila: dict[str, Any]) -> bool:
    return _con_texto(fila.get("nombre")) or _con_texto(fila.get("dni"))


def _tiene_incidencia(fila: dict[str, Any]) -> bool:
    inc = fila.get("incidencia")
    return isinstance(inc, dict) and (
        _con_texto(inc.get("codigo")) or _con_texto(inc.get("texto_leido")))


def _ordenadas(filas: list[int | None]) -> tuple[int | None, ...]:
    """Ascendentes, con las filas sin `numero_linea` al final."""
    return tuple(sorted(filas, key=lambda n: (n is None, n or 0)))


def detectar_lectura_dudosa(
    empleados_raw: list[Any], *, tabla_dispersa: bool
) -> list[MotivoLectura]:
    """Motivos de lectura dudosa de `empleados[]` de sv2, en orden fijo
    (autocomprobacion, tabla dispersa). Lista vacia = nada que objetar."""
    filas = [f for f in empleados_raw if isinstance(f, dict)]

    incoherentes: list[int | None] = []
    vacias: list[int | None] = []
    alguna_con_horas = False
    for fila in filas:
        numero = _a_int(fila.get("numero_linea"))
        if _tiene_horas(fila):
            alguna_con_horas = True
            autocomprobacion = _a_int(fila.get("numero_linea_horas"))
            if (numero is not None and autocomprobacion is not None
                    and autocomprobacion != numero):
                incoherentes.append(numero)
        elif _tiene_trabajador(fila) and not _tiene_incidencia(fila):
            vacias.append(numero)

    motivos: list[MotivoLectura] = []
    if incoherentes:
        motivos.append(MotivoLectura(MOTIVO_AUTOCOMPROBACION, _ordenadas(incoherentes)))
    if tabla_dispersa and alguna_con_horas and vacias:
        motivos.append(MotivoLectura(MOTIVO_TABLA_DISPERSA, _ordenadas(vacias)))
    return motivos
