# application/services/reparto_aviso.py
"""F-046 · El aviso de reparto al aprobar (sv4, reglas puras).

Cuando el reparto ponderado de un dia (F-045) cambiaria lineas ya en
Sigrid o de parte aprobado, sv3 deja un reparto `pendiente` en
`reparto_pendiente`. Al aprobar lineas de ese dia, el portal lo ensena y
el humano decide: «Aplicar» (sv5 edita Sigrid y las lineas se registran
con el ideal) o «Mantener lo registrado» (lo libre se recalcula en
residual). Este modulo no lee ni escribe nada:

  - `bloque_repartos` (R30, R31): por reparto, el dia, sus lineas
    (antes -> despues, obra, parte de Sigrid) y si se puede aplicar.
  - `excluidas_por_reparto` (R32): las lineas que no viajan sin decision.
  - `payload_reajuste` (R33): lo que se manda a sv5 al aplicar (solo las
    `registrado` y las extras nuevas de base registrada; las solo
    aprobadas no van a sv5, DA11).

Una extra nueva aun no tiene `registro_id` hasta que se reserva al
aplicar; para la comprobacion previa usa `id_provisional(base)`, negativo,
que nunca existe en Sigrid (su synckey `partes:-N` no la escribe nadie).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping

from application.services.congelacion import CongeladoError

DECISION_APLICAR = "aplicar"
DECISION_MANTENER = "mantener"
DECISIONES = (DECISION_APLICAR, DECISION_MANTENER)

#: Estados del reparto que impiden registrar las lineas del grupo (R32).
ESTADO_PENDIENTE = "pendiente"
ESTADO_APLICANDO = "aplicando"
ESTADO_RECHAZADO = "rechazado"
ESTADOS_BLOQUEAN = (ESTADO_PENDIENTE, ESTADO_APLICANDO, ESTADO_RECHAZADO)

MOTIVO_PENDIENTE = (
    "reparto del dia pendiente de decidir: elige «Aplicar» o «Mantener lo "
    "registrado» en el aviso de aprobacion")
MOTIVO_APLICANDO = (
    "reajuste en Sigrid en curso o sin confirmar: vuelve a pulsar «Aplicar» "
    "para reintentarlo")
MOTIVO_RECHAZADO = (
    "se mantuvo lo registrado: falta el recalculo del dia antes de registrar")
MOTIVO_SIN_COMPROBAR = "no se pudo comprobar en Sigrid"

MOTIVO_APROBAR_CON_REPARTO = (
    "este parte tiene lineas de un dia con un reparto pendiente de decidir "
    "(o en curso): decide «Aplicar» o «Mantener lo registrado» al aprobar "
    "sus lineas antes de aprobar el parte")


class RepartoCambiadoError(CongeladoError):
    """R33, R35: el reparto ya no esta como cuando se ensento (otro usuario
    decidio, cambio una linea, hay lineas nuevas o un parte esta en
    espera). La capa web lo traduce a 409 (como toda `CongeladoError`)."""


class RepartoPendienteError(CongeladoError):
    """R36 (DA13): no se aprueba un documento con un reparto vivo."""

    def __init__(self) -> None:
        super().__init__(MOTIVO_APROBAR_CON_REPARTO)


#: `sigrid_estado` de una linea que esta en Sigrid (la edita sv5).
REGISTRADO = "registrado"

#: Campos de una extra nueva que el registro de sv5 necesita (R20).
_CAMPOS_NUEVA = ("recurso_ide", "fecha_int", "hora_ide", "hora_codigo",
                 "partida_ide", "partida_cod", "obra_ide", "obra_codigo")


def id_provisional(base_registro_id: int) -> int:
    """El `registro_id` con que se comprueba una extra nueva sin reserva."""
    return -int(base_registro_id)


def _en_sigrid(cambio: Mapping) -> bool:
    return (cambio.get("sigrid_estado") or "").strip().lower() == REGISTRADO


def _id_sv5(cambio: Mapping, reservas: Mapping | None) -> int:
    """El id con el que sv5 conoce la linea: el suyo o, si es nueva, el
    reservado (o el provisional, si aun no hay reserva)."""
    if cambio.get("registro_id") is not None:
        return int(cambio["registro_id"])
    base = int(cambio["base_registro_id"])
    reservado = (reservas or {}).get(str(base))
    return int(reservado) if reservado is not None else id_provisional(base)


def _fecha_iso(fecha_int) -> str | None:
    try:
        f = int(fecha_int)
    except (TypeError, ValueError):
        return None
    return f"{f // 10000:04d}-{(f // 100) % 100:02d}-{f % 100:02d}"


def bloque_repartos(filas: Iterable[Mapping],
                    veredictos: Mapping[int, Mapping]) -> list[dict]:
    """R30, R31: lo que el modal ensena por reparto.

    `veredictos[id]` = `{"error", "lineas": {id_sv5: {editable, motivo}}}`
    con lo que contesto sv5 `comprobar` (solo hay para los repartos con
    lineas en Sigrid). Una linea en Sigrid sin veredicto no es editable.
    Opciones: `pendiente` editable ⇒ aplicar y mantener; no editable ⇒ solo
    mantener; `aplicando` ⇒ reintentar aplicar; `rechazado` ⇒ ninguna (se
    espera al recalculo).
    """
    bloques: list[dict] = []
    for fila in filas:
        v = veredictos.get(fila["id"]) or {}
        por_linea = v.get("lineas") or {}
        lineas: list[dict] = []
        motivo: str | None = None
        if v.get("error"):
            motivo = f"{MOTIVO_SIN_COMPROBAR}: {v['error']}"
        for c in fila.get("cambios") or []:
            en_sigrid = _en_sigrid(c)
            if en_sigrid:
                r = por_linea.get(_id_sv5(c, fila.get("reservas")))
                editable = bool(r and r.get("editable"))
                motivo_linea = ((r or {}).get("motivo")
                                or (None if editable else MOTIVO_SIN_COMPROBAR))
            else:
                editable, motivo_linea = True, None
            if not editable and motivo is None:
                motivo = motivo_linea
            lineas.append({
                "registro_id": c.get("registro_id"),
                "base_registro_id": c.get("base_registro_id"),
                "nueva": c.get("registro_id") is None,
                "tipo": c.get("tipo"),
                "obra_codigo": c.get("obra_codigo"),
                "parte_cod": c.get("parte_cod"),
                "antes": c.get("antes"), "despues": c.get("despues"),
                "en_sigrid": en_sigrid, "editable": editable,
                "motivo": motivo_linea,
            })
        editable = motivo is None
        estado = fila.get("estado")
        if estado == ESTADO_RECHAZADO:
            opciones: list[str] = []
            motivo = MOTIVO_RECHAZADO
        elif estado == ESTADO_APLICANDO:
            opciones = [DECISION_APLICAR] if editable else []
        else:
            opciones = ([DECISION_APLICAR, DECISION_MANTENER] if editable
                        else [DECISION_MANTENER])
        bloques.append({
            "id": fila["id"], "estado": estado,
            "fecha": _fecha_iso(fila.get("fecha_int")),
            "recurso_ide": fila.get("recurso_ide"),
            "editable": editable, "motivo": motivo, "opciones": opciones,
            "error": fila.get("error"), "lineas": lineas,
        })
    return bloques


def excluidas_por_reparto(filas: Iterable[Mapping],
                          decisiones: Mapping[int, str]) -> dict[int, str]:
    """R32: `registro_id` -> motivo de las lineas de la peticion que NO
    viajan: las de un grupo con reparto `pendiente`, `aplicando` o
    `rechazado` cuya decision en esta peticion no es «Aplicar»."""
    motivos = {ESTADO_PENDIENTE: MOTIVO_PENDIENTE,
               ESTADO_APLICANDO: MOTIVO_APLICANDO,
               ESTADO_RECHAZADO: MOTIVO_RECHAZADO}
    out: dict[int, str] = {}
    for fila in filas:
        estado = fila.get("estado")
        if estado not in ESTADOS_BLOQUEAN:
            continue
        if decisiones.get(fila["id"]) == DECISION_APLICAR:
            continue
        for rid in fila.get("registro_ids") or []:
            out[int(rid)] = motivos[estado]
    return out


def payload_reajuste(fila: Mapping, reservas: Mapping | None) -> dict:
    """R33: las lineas de sv5 `/api/reajuste/*` de un reparto.

    Existentes en Sigrid: `registro_id`, «antes» y «despues». Extra nueva
    de base registrada: su id reservado (o el provisional) y lo que el
    registro necesita para escribirla. Lo que solo esta aprobado no va."""
    lineas: list[dict] = []
    for c in fila.get("cambios") or []:
        if not _en_sigrid(c):
            continue
        if c.get("registro_id") is not None:
            lineas.append({"registro_id": int(c["registro_id"]),
                           "antes": c["antes"], "despues": c["despues"]})
            continue
        linea = {"registro_id": _id_sv5(c, reservas),
                 "despues": c["despues"],
                 "base_registro_id": int(c["base_registro_id"])}
        linea.update({k: c.get(k) for k in _CAMPOS_NUEVA})
        lineas.append(linea)
    return {"lineas": lineas}
