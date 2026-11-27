# application/services/conversion_clase.py
"""F-085 · qué clase toma una línea al elegirle un código de hora (sv4).

Hasta F-085, elegir un código de incidencia (CIA, CIV...) en una línea de
horas solo guardaba el código: la línea seguía `normal` con sus horas y sv5
escribía un HL* (caso 0678, 18/11/2026). Desde F-085, `decidir` dice qué
hace `set_registro_hora` con la clase de la línea:

  1. `CIZ` (el fin) no se elige: lo pone el sistema al cerrar la racha
     (`MOTIVO_CIZ_NO_SE_ELIGE`, R5).
  2. Un código de incidencia sin letra en la tabla de F-025
     (`config/incidencias.yaml`) no se sabe convertir (`motivo_sin_letra`,
     R6).
  3. Con letra: la forma canónica de la ingesta y del alta a mano
     (`es_incidencia`, `tipo_hora` = `incidencia_codigo` = letra, horas
     vacías). Es un cambio de clase si no era incidencia o la letra
     difiere (R2, R3; revoca F-066 R14).
  4. Una incidencia con un código de horas (F-066 le da clase) vuelve a
     ser una línea de horas, con las horas vacías (R4, D3).
  5. Si no, la regla de F-066 tal cual (R7): el código da `extra` o
     `normal`; sin código, o en una incidencia sin código, nada cambia.

Puro, sin E/S: lo llaman el endpoint (para el 400 antes de tocar nada) y
el repositorio (con el estado de la línea, dentro de su transacción).
"""
from __future__ import annotations

from dataclasses import dataclass

from application.services.clase_hora import (
    es_codigo_fin,
    es_codigo_incidencia,
    tipo_hora_de_codigo,
)
from application.services.incidencias_horas import (
    TablaIncidencias,
    normalizar_codigo,
)

#: R5: el fin de la racha no se elige en el desplegable.
MOTIVO_CIZ_NO_SE_ELIGE = (
    "El fin de incidencia (CIZ) lo pone el sistema al cerrar la racha: "
    "elige el código de la incidencia")


def motivo_sin_letra(codigo: str | None) -> str:
    """R6: el código de incidencia no está en la tabla del portal."""
    return (f"El código {normalizar_codigo(codigo)} no está en la tabla de "
            "incidencias del portal")


@dataclass(frozen=True)
class ClaseNueva:
    """La clase que toma la línea. Con `error`, no se toca nada."""

    es_incidencia: bool
    tipo_hora: str | None
    incidencia_codigo: str | None
    vaciar_horas: bool = False   # `horas` y `horas_orig` a nulo
    cambia: bool = False         # cambio de clase (deshacer y recálculo)
    error: str | None = None


def error_de_codigo(codigo: str | None,
                    tabla: TablaIncidencias | None) -> str | None:
    """Pasos 1 y 2: por qué ese código no se puede guardar, o None."""
    if es_codigo_fin(codigo):
        return MOTIVO_CIZ_NO_SE_ELIGE
    if es_codigo_incidencia(codigo) and _letra(codigo, tabla) is None:
        return motivo_sin_letra(codigo)
    return None


def _letra(codigo: str | None, tabla: TablaIncidencias | None) -> str | None:
    if tabla is None:
        return None
    clase = tabla.por_sigrid.get(normalizar_codigo(codigo))
    return clase.letra if clase is not None else None


def decidir(*, es_incidencia: bool, incidencia_codigo: str | None,
            tipo_hora: str | None, codigo: str | None,
            tabla: TablaIncidencias | None) -> ClaseNueva:
    """R2-R7: la clase de la línea tras elegir `codigo` (design §2)."""
    actual = ClaseNueva(es_incidencia=bool(es_incidencia),
                        tipo_hora=tipo_hora,
                        incidencia_codigo=incidencia_codigo)
    error = error_de_codigo(codigo, tabla)
    if error is not None:
        return ClaseNueva(es_incidencia=actual.es_incidencia,
                          tipo_hora=tipo_hora,
                          incidencia_codigo=incidencia_codigo, error=error)
    if es_codigo_incidencia(codigo):
        letra = _letra(codigo, tabla)
        cambia = (not es_incidencia
                  or normalizar_codigo(incidencia_codigo) != letra)
        if not cambia:
            return actual
        return ClaseNueva(es_incidencia=True, tipo_hora=letra,
                          incidencia_codigo=letra, vaciar_horas=True,
                          cambia=True)
    tipo = tipo_hora_de_codigo(codigo)
    if tipo is None:
        return actual
    if es_incidencia:
        return ClaseNueva(es_incidencia=False, tipo_hora=tipo,
                          incidencia_codigo=None, vaciar_horas=True,
                          cambia=True)
    return ClaseNueva(es_incidencia=False, tipo_hora=tipo,
                      incidencia_codigo=incidencia_codigo)
