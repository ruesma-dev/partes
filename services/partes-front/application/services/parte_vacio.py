# application/services/parte_vacio.py
"""F-061 · El parte que se queda sin líneas vivas se RETIRA.

Decisión del humano (2026-10-26): el parte como entidad no va a la papelera
de partes, «porque es confuso». Cuando se queda sin ninguna línea viva se
**retira**: `is_active = false`, `deleted_at_utc` a NULL y `deleted_by` con
la marca `sin-lineas` (DA7, sin DDL). No sale en `/partes` ni en la
papelera de partes, sus líneas siguen en «Líneas sueltas borradas» y su
sha256 queda libre (el índice único es parcial `WHERE is_active`).

La marca distingue al parte retirado del desactivado por el reemplazo de
sv3 (`_deactivate_same_day_obra`), que deja `deleted_by` a NULL: solo el
retirado vuelve al restaurar una línea y solo él se borra físicamente
cuando ya no le queda ninguna fila (DA3).

Módulo PURO (ni BBDD, ni ORM, ni FastAPI): lo usan el repositorio, el
portal y el script `limpiar_partes_vacios.py`.
"""
from __future__ import annotations

import json
from collections.abc import Iterable

from application.services.congelacion import ESTADO_ENCOLADO, vive_fuera

#: Prefijo de `deleted_by` de un parte retirado por quedarse sin líneas.
MARCA_RETIRADO = "sin-lineas"

#: Separador entre la marca y el actor, como el resto del portal.
_SEPARADOR = " · "

#: Longitud de `parte_documents.deleted_by` (`String(255)`).
_LARGO_DELETED_BY = 255

#: Partes de Sigrid que la limpieza nunca toca (lista cerrada, R16).
PARTES_SIGRID_PROTEGIDOS = frozenset({"PT26/00373", "PT26/00375",
                                      "PT26/00376"})

MOTIVO_DUPLICADO_ACTIVO = (
    "Ya hay un parte activo del mismo PDF (se volvió a procesar). "
    "Restaurar esto crearía un duplicado: elimínalo de la papelera."
)

#: Motivos de exclusión de la limpieza (R16), en orden de prioridad.
EXCLUSION_APROBADO = "aprobado"
EXCLUSION_VIVE_FUERA = "vive_fuera"
EXCLUSION_PROTEGIDO = "protegido"

#: Categorías de un parte vacío (R15).
CATEGORIA_TODAS_EN_PAPELERA = "todas_en_papelera"
CATEGORIA_SIN_FILAS_LEIDOS = "sin_filas_leidos"
CATEGORIA_SIN_FILAS_NADA_LEIDO = "sin_filas_nada_leido"
CATEGORIA_SIN_FILAS_MANUAL = "sin_filas_manual"


class DuplicadoActivoError(Exception):
    """Restaurar devolvería activo un parte cuyo sha256 ya tiene otro
    parte activo (R7). No es una congelación: el portal responde 409 con
    el motivo, sin escribir nada."""

    def __init__(self, motivo: str = MOTIVO_DUPLICADO_ACTIVO) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def marca_retirado(actor: str | None) -> str:
    """`deleted_by` de un parte retirado: la marca y, si lo hay, el actor."""
    if not actor:
        return MARCA_RETIRADO
    return (MARCA_RETIRADO + _SEPARADOR + actor)[:_LARGO_DELETED_BY]


def es_retirado(*, is_active: bool, deleted_at_utc: str | None,
                deleted_by: str | None) -> bool:
    """Inactivo, fuera de la papelera de partes y con la marca (DA7)."""
    return (not is_active and not deleted_at_utc
            and (deleted_by or "").startswith(MARCA_RETIRADO))


def _vive_fuera_o_encolada(estado: str | None) -> bool:
    return vive_fuera(estado) or (estado or "").strip().lower() == (
        ESTADO_ENCOLADO)


def motivo_exclusion_limpieza(*, aprobado: bool,
                              estados: Iterable[str | None],
                              partes_sigrid: Iterable[str | None],
                              ) -> str | None:
    """Por qué la limpieza no toca un parte vacío (R16), o None.

    `estados` son los `sigrid_estado` de TODAS sus filas (vivas o en la
    papelera) y `partes_sigrid`, sus `sigrid_parte_cod`.
    """
    if aprobado:
        return EXCLUSION_APROBADO
    if any(_vive_fuera_o_encolada(e) for e in estados):
        return EXCLUSION_VIVE_FUERA
    if any(p in PARTES_SIGRID_PROTEGIDOS for p in partes_sigrid):
        return EXCLUSION_PROTEGIDO
    return None


def categoria_vacio(*, filas: int, manual: bool,
                    empleados_leidos: int) -> str:
    """Categoría de un parte vacío para el informe (R15)."""
    if filas > 0:
        return CATEGORIA_TODAS_EN_PAPELERA
    if manual:
        return CATEGORIA_SIN_FILAS_MANUAL
    if empleados_leidos > 0:
        return CATEGORIA_SIN_FILAS_LEIDOS
    return CATEGORIA_SIN_FILAS_NADA_LEIDO


def empleados_leidos(raw_extraction_json: str | None) -> int:
    """Nº de empleados que traía la extracción guardada (`data.empleados`).

    Un JSON inválido, ausente o con otra forma da 0: el informe no se para
    por un parte raro.
    """
    try:
        envelope = json.loads(raw_extraction_json or "")
    except (TypeError, ValueError):
        return 0
    if not isinstance(envelope, dict):
        return 0
    data = envelope.get("data")
    if not isinstance(data, dict):
        return 0
    empleados = data.get("empleados")
    return len(empleados) if isinstance(empleados, list) else 0
