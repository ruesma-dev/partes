# application/services/reajuste_reparto.py
"""F-046 · Reglas puras del reajuste del reparto en sv3.

Cuando el reparto ideal de un dia (F-045) cambiaria lineas congeladas,
sv3 deja la decision al humano en `reparto_pendiente` (design §3). Este
modulo no lee ni escribe nada; lo usa `RecursoConciliador`:

  - `clase_linea`: libre (no congelada), reajustable (congelada en
    `registrado` o solo por parte aprobado: sin estado, `omitido`,
    `error`, `conflicto`, `borrado_sigrid`) o dura (`encolado`,
    `dedicacion`, cualquier estado desconocido, ordinaria sin horas o en
    la papelera). La pareja con mas de una extra automatica la endurece
    `proponer_dia`, que es quien ve la pareja entera.
  - `firma_grupo`: huella del (recurso, dia) para saber si cambio (R13).
  - `decidir_grupo`: que hace la pasada con el grupo segun su reparto
    vigente (R11-R15).
  - `cambios_a_json` / `json_a_cambios`: el JSON de la columna `cambios`.

La congelacion la sigue decidiendo `esta_congelado` (y su pareja, F-037):
`clase_linea` la recibe hecha y solo distingue QUE congelada es.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping

from infrastructure.database.orm_models import (
    REPARTO_APLICADO,
    REPARTO_APLICANDO,
    REPARTO_MANTENIDO,
    REPARTO_RECHAZADO,
)

LIBRE = "libre"
REAJUSTABLE = "reajustable"
DURA = "dura"

#: `sigrid_estado` de una congelada que el reajuste puede cambiar: ya en
#: Sigrid (`registrado`, se edita por sv5) o solo de parte aprobado.
ESTADOS_REAJUSTABLES: frozenset[str] = frozenset(
    {"", "registrado", "omitido", "error", "conflicto", "borrado_sigrid"})

#: Que hace la pasada con el grupo (`decidir_grupo`).
MATERIALIZAR = "materializar"        # aplicado: lo hace `materializar_repartos`
CONGELAR = "congelar"                # aplicando: ni la fila ni lo congelado
RESIDUAL_MANTENER = "residual_mantener"   # rechazado/mantenido vigente
PROPONER = "proponer"                # calcular el ideal y, si cambia, pendiente
RESIDUAL = "residual"                # sin libres: modo F-045 (R12)


def _estado(reg: Mapping) -> str:
    return (reg.get("sigrid_estado") or "").strip().lower()


def _tipo(reg: Mapping) -> str:
    return (reg.get("tipo_hora") or "").strip().lower()


def clase_linea(reg: Mapping, *, congelada: bool) -> str:
    """La clase de una linea del grupo; `congelada` = `_congelado(reg)`."""
    if not congelada:
        return LIBRE
    if reg.get("deleted_at_utc"):
        return DURA
    if _tipo(reg) in ("", "normal") and (reg.get("horas") or 0.0) <= 0:
        return DURA
    return REAJUSTABLE if _estado(reg) in ESTADOS_REAJUSTABLES else DURA


def _num(valor) -> str:
    """Horas a texto estable: 4 decimales (como la escala de F-045)."""
    return "" if valor is None else f"{float(valor):.4f}"


def firma_grupo(regs: Iterable[Mapping]) -> str:
    """R13: sha256 de las tuplas ordenadas (registro_id, tipo de hora,
    extra automatica, horas, horas_orig, estado en Sigrid, parte aprobado)
    del grupo. No depende del orden de entrada."""
    tuplas = sorted(
        (int(r["registro_id"]), _tipo(r), bool(r.get("extra_auto")),
         _num(r.get("horas")), _num(r.get("horas_orig")), _estado(r),
         bool(r.get("doc_approved")))
        for r in regs)
    texto = json.dumps(tuplas, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def decidir_grupo(fila: Mapping | None, firma: str, hay_libres: bool) -> str:
    """La maquina de design §3 para UN grupo, segun su reparto vigente.

    `aplicado` ⇒ MATERIALIZAR y `aplicando` ⇒ CONGELAR, pase lo que pase
    (R13: nunca a obsoleto). `rechazado`/`mantenido` con la misma firma ⇒
    RESIDUAL_MANTENER (R14). Lo demas ⇒ PROPONER si hay alguna ordinaria
    libre y RESIDUAL si no (R12)."""
    estado = (fila or {}).get("estado")
    if estado == REPARTO_APLICADO:
        return MATERIALIZAR
    if estado == REPARTO_APLICANDO:
        return CONGELAR
    if (estado in (REPARTO_RECHAZADO, REPARTO_MANTENIDO)
            and (fila or {}).get("firma") == firma):
        return RESIDUAL_MANTENER
    return PROPONER if hay_libres else RESIDUAL


def es_rechazado(fila: Mapping | None) -> bool:
    """R14: el reparto lo rechazo el humano y la pasada aun no lo ha
    repartido en residual (pasara a `mantenido`)."""
    return (fila or {}).get("estado") == REPARTO_RECHAZADO


def cambios_a_json(datos: Mapping) -> str:
    """`{ids_grupo, cambios[]}` a texto determinista (claves ordenadas)."""
    return json.dumps(datos, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def json_a_cambios(texto: str | None) -> dict:
    """La columna `cambios` de vuelta; vacia o ilegible = sin cambios."""
    vacio = {"ids_grupo": [], "cambios": []}
    try:
        datos = json.loads(texto or "")
    except (TypeError, ValueError):
        return vacio
    if not isinstance(datos, dict):
        return vacio
    return {"ids_grupo": list(datos.get("ids_grupo") or []),
            "cambios": list(datos.get("cambios") or [])}
