# application/services/franquicia.py
"""F-056 · Franquicia de extras en sv4 (reglas puras).

Un trabajador con franquicia X (campo extendido del recurso en Sigrid que
solo lee sv5, DA1 = C, DA21, DA29) no cobra las primeras X horas extra de cada mes de nomina
(16 -> 15). sv5 calcula E, X y A y escribe la linea `HE*` negativa; sv4
decide CUANDO preguntar, A QUE dia, obra y partida, guarda la decision
humana (`franquicia_ajuste`) y orquesta. Este modulo no lee ni escribe:

  - `periodo_de` / `periodo_de_clave` (R4): el mes de nomina de una fecha
    o de su clave `YYYY-MM` (el mes del dia 15), sobre `calendar_builder`;
  - `dia_de_ajuste` (R5): el ultimo dia del periodo con jornada > 0;
  - `elegir_obra` (R7) y `varios_recursos` (R12);
  - `candidatos` (R9-R12, R44; DA7: una linea del DIA DE AJUSTE de un
    recurso con franquicia `activa`, o un ajuste ya existente del periodo);
  - `extras_pendientes` (R9): las extras `HE*` que esta aprobacion
    escribiria (acciones `escribir` del preflight de sv5);
  - `bloque_franquicias` (R9-R14): lo que pinta el modal;
  - `validar_decisiones` (R15) y `payload_franquicia` (design §6).

La formula de A y la regla «activa» NO viven aqui (DA15, DA21): son de sv5.
Motivos sin tildes, como el resto de mensajes de la API del portal.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from application.services.calendar_builder import (
    MODE_NOMINA,
    period_bounds,
    period_of,
)
from application.services.congelacion import CongeladoError

#: Estados de `franquicia_ajuste` (los mismos que `ESTADOS_FRANQUICIA` del
#: ORM; aqui sin importar infraestructura).
DECIDIDO = "decidido"
APLICADO = "aplicado"
RECHAZADO = "rechazado"
ERROR = "error"
ESTADOS = (DECIDIDO, APLICADO, RECHAZADO, ERROR)
#: R10: un ajuste en estos estados sale en el aviso con cualquier linea.
ESTADOS_VIVOS = (APLICADO, DECIDIDO, ERROR)

#: R15: decisiones del modal.
AJUSTAR = "ajustar"
NO_AJUSTAR = "no_ajustar"
RECALCULAR = "recalcular"
MANTENER = "mantener"
DECISIONES = (AJUSTAR, NO_AJUSTAR, RECALCULAR, MANTENER)

#: Tipo de cada candidato del aviso.
NUEVO = "nuevo"              # R9: franquicia activa y sin fila
EXISTENTE = "existente"      # R10: fila aplicado | decidido | error
TIPO_RECHAZADO = "rechazado"  # R11: solo informa
INVALIDA = "invalida"        # R11: franquicia invalida, solo informa

#: Estados de franquicia de sv5 (R2) que este modulo distingue.
_ACTIVA = "activa"
_INVALIDA = "invalida"

#: Acciones de sv5 que escriben (crear) o editan (actualizar) la linea.
_ESCRIBEN = ("crear", "actualizar")

AVISO_NO_COMPROBADA = "no se ha podido comprobar la franquicia: "
MOTIVO_VARIOS_RECURSOS = (
    "el trabajador tiene extras con mas de un recurso en el periodo: no se "
    "ajusta (DA16)")
MOTIVO_SIN_OBRA = (
    "sin lineas de trabajo en el periodo: no hay obra para el ajuste")
MOTIVO_INVALIDA = (
    "franquicia invalida en Sigrid (negativa, mayor de 200 h o no "
    "numerica): no se ajusta")
MOTIVO_RECHAZADO = (
    "se decidio no ajustar este periodo (se puede ajustar desde la vista "
    "del trabajador)")
MOTIVO_SIN_RESPUESTA = "sin respuesta de Sigrid al comprobar el ajuste"
MOTIVO_YA_APLICADO = "ya aplicado: la linea de ajuste ya vale lo que toca"
MOTIVO_SIN_EXTRAS = "sin extras por encima de la franquicia: nada que ajustar"

_RE_PERIODO = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class DecisionInvalida(ValueError):
    """R15: el bloque `franquicias` de la peticion no vale (422)."""


class AjusteCambiadoError(CongeladoError):
    """R15, R18: el ajuste ya no esta como cuando se enseno (otro usuario
    decidio, la decision no cuadra con su estado o quedan lineas en cola).
    La capa web lo traduce a 409, como toda `CongeladoError`."""


@dataclass(frozen=True)
class Periodo:
    """Mes de nomina: `clave` `YYYY-MM` (el mes del dia 15), 16 -> 15."""
    clave: str
    inicio: date
    fin: date

    @property
    def inicio_int(self) -> int:
        return fecha_a_int(self.inicio)

    @property
    def fin_int(self) -> int:
        return fecha_a_int(self.fin)


@dataclass(frozen=True)
class DiaAjuste:
    """R5, R6: el dia de ajuste de un (recurso, periodo); `motivo` si no se
    puede calcular (calendario de Sesame no fiable)."""
    fecha: date | None
    motivo: str | None = None


def fecha_a_int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def fecha_de_int(valor) -> date | None:
    """`YYYYMMDD` -> fecha (None si no es una fecha)."""
    try:
        fi = int(valor or 0)
        return date(fi // 10000, (fi // 100) % 100, fi % 100)
    except (TypeError, ValueError):
        return None


def periodo_de(d: date) -> Periodo:
    """R4: el mes de nomina de la fecha REAL de la linea."""
    ano, mes = period_of(d, MODE_NOMINA)
    inicio, fin = period_bounds(ano, mes, MODE_NOMINA)
    return Periodo(f"{ano:04d}-{mes:02d}", inicio, fin)


def periodo_de_clave(clave: str | None) -> Periodo | None:
    """`YYYY-MM` -> su periodo de nomina; None si la clave no vale."""
    m = _RE_PERIODO.match(str(clave or ""))
    if m is None:
        return None
    ano, mes = int(m.group(1)), int(m.group(2))
    inicio, fin = period_bounds(ano, mes, MODE_NOMINA)
    return Periodo(f"{ano:04d}-{mes:02d}", inicio, fin)


def clave_de(recurso_ide: int, periodo: str) -> str:
    """La clave de un (recurso, periodo) en el bloque y las decisiones."""
    return f"{int(recurso_ide)}|{periodo}"


def dia_de_ajuste(periodo: Periodo,
                  jornada_de: Callable[[date], float]) -> date | None:
    """R5: el ultimo dia del periodo con `jornada_de(d) > 0` (None si no
    hay ninguno)."""
    d = periodo.fin
    while d >= periodo.inicio:
        if float(jornada_de(d) or 0.0) > 0.0:
            return d
        d -= timedelta(days=1)
    return None


# ------------------------------- obra (R7) -------------------------------- #

def _es_trabajo(linea: Mapping) -> bool:
    """Linea de trabajo: no incidencia, con horas y con obra."""
    return (not linea.get("es_incidencia")
            and float(linea.get("horas") or 0.0) > 0.0
            and bool(linea.get("obra_ide") or linea.get("obra_codigo")))


def _es_extra(linea: Mapping) -> bool:
    return (linea.get("tipo_hora") or "") == "extra"


def _obra(linea: Mapping) -> tuple:
    return (linea.get("obra_ide"), str(linea.get("obra_codigo") or ""))


def lineas_del_recurso(lineas: Iterable[Mapping],
                       recurso_ide: int) -> list[Mapping]:
    """DA32, R7, R48: solo las lineas del recurso del ajuste. Las de otro
    recurso de la misma persona (otra empresa) no eligen la obra: sv5
    rechazaria esa obra para este recurso (F-023, R30). El dia de ajuste,
    en cambio, sigue siendo de la persona (DA6)."""
    rec = int(recurso_ide)
    return [x for x in lineas if int(x.get("recurso_ide") or 0) == rec]


def elegir_obra(lineas_dia: Iterable[Mapping],
                lineas_periodo: Iterable[Mapping]) -> dict | None:
    """R7: la obra de mas horas del recurso el dia de ajuste (desempate:
    mas extras del periodo y menor codigo); sin lineas de trabajo ese dia,
    el ULTIMO dia del periodo que las tenga. La partida, la de su linea de
    mas horas en esa obra ese dia (desempate: menor `registro_id`)."""
    periodo = [x for x in lineas_periodo if _es_trabajo(x)]
    base = [x for x in lineas_dia if _es_trabajo(x)]
    if not base:
        if not periodo:
            return None
        ultimo = max(int(x.get("fecha_int") or 0) for x in periodo)
        base = [x for x in periodo if int(x.get("fecha_int") or 0) == ultimo]
    horas: dict[tuple, float] = {}
    for x in base:
        horas[_obra(x)] = horas.get(_obra(x), 0.0) + float(x["horas"])
    extras: dict[tuple, float] = {}
    for x in periodo:
        if _es_extra(x):
            extras[_obra(x)] = extras.get(_obra(x), 0.0) + float(x["horas"])
    obra = min(horas, key=lambda o: (-horas[o], -extras.get(o, 0.0), o[1]))
    linea = min((x for x in base if _obra(x) == obra),
                key=lambda x: (-float(x["horas"]),
                               int(x.get("registro_id") or 0)))
    return {"obra_ide": linea.get("obra_ide"),
            "obra_codigo": linea.get("obra_codigo"),
            "partida_ide": linea.get("partida_ide"),
            "partida_cod": linea.get("partida_cod")}


def varios_recursos(lineas_periodo: Iterable[Mapping]) -> bool:
    """R12, DA16: extras (con horas) de mas de un recurso en el periodo."""
    recursos = {int(x.get("recurso_ide") or 0) for x in lineas_periodo
                if _es_extra(x) and float(x.get("horas") or 0.0) != 0.0}
    return len(recursos) > 1


# --------------------------- extras pendientes ---------------------------- #

def extras_pendientes(grupos_evaluados: Iterable[Mapping], recurso_ide: int,
                      periodo: Periodo) -> float:
    """R9: las horas `HE*` que esta aprobacion ESCRIBIRIA en el periodo
    (acciones `escribir` del preflight de sv5, netas): sv5 aun no las ve
    en Sigrid y `comprobar` las suma a E para el A estimado."""
    total = 0.0
    for g in grupos_evaluados:
        for a in g.get("acciones") or []:
            if (a.get("accion") == "escribir"
                    and int(a.get("recurso_ide") or 0) == int(recurso_ide)
                    and (a.get("hora_codigo") or "").upper().startswith("HE")
                    and periodo.inicio_int <= int(a.get("fecha_int") or 0)
                    <= periodo.fin_int):
                total += float(a.get("can") or 0.0)
    return round(total, 2)


# ------------------------------- candidatos -------------------------------- #

def candidatos(lineas: Iterable[Mapping],
               filas: Mapping[tuple[int, str], Mapping],
               franquicias: Mapping[int, Mapping] | None,
               dia_de: Callable[[tuple[int, str]], DiaAjuste]) -> list[dict]:
    """R9-R12, R44 y DA7: los (recurso, periodo) del aviso.

    `lineas` son las de la aprobacion; `filas`, las de `franquicia_ajuste`
    por `(recurso_ide, periodo)`; `franquicias`, el mapa de sv5 `/recursos`
    (`{ide: {franquicia, estado}}`) o None si no se pudo comprobar (R44:
    entonces solo salen los ajustes ya existentes); `dia_de`, el dia de
    ajuste de una clave (solo se pide cuando hace falta).

    Un ajuste `aplicado`/`decidido`/`error` sale con cualquier linea del
    periodo (R10), `rechazado` solo informa (R11). Sin fila, solo dispara
    una linea del DIA DE AJUSTE de un recurso con franquicia `activa` (R9)
    o `invalida` (R11, con motivo); con el calendario no fiable (R6), el
    candidato sale sin dia y con el motivo."""
    claves: dict[tuple[int, str], list[Mapping]] = {}
    for x in lineas:
        d = fecha_de_int(x.get("fecha_int"))
        rec = int(x.get("recurso_ide") or 0)
        if d is None or rec <= 0:
            continue
        claves.setdefault((rec, periodo_de(d).clave), []).append(x)
    out: list[dict] = []
    for (rec, clave_p) in sorted(claves):
        grupo = claves[(rec, clave_p)]
        fila = filas.get((rec, clave_p))
        lec = (franquicias or {}).get(rec) or {}
        base = {"clave": clave_de(rec, clave_p), "recurso_ide": rec,
                "periodo": periodo_de_clave(clave_p), "fila": fila,
                "franquicia": lec.get("franquicia"),
                "franquicia_estado": lec.get("estado"),
                "dni": grupo[0].get("dni"), "nombre": grupo[0].get("nombre"),
                "registro_ids": sorted({int(x["registro_id"]) for x in grupo
                                        if x.get("registro_id")}),
                "dia": None, "motivo": None}
        if fila is not None:
            base["dia"] = fecha_de_int(fila.get("fecha_int"))
            if fila.get("estado") in ESTADOS_VIVOS:
                out.append(dict(base, tipo=EXISTENTE))
            elif fila.get("estado") == RECHAZADO:
                out.append(dict(base, tipo=TIPO_RECHAZADO,
                                motivo=MOTIVO_RECHAZADO))
            continue
        if franquicias is None or lec.get("estado") not in (_ACTIVA,
                                                            _INVALIDA):
            continue
        dia = dia_de((rec, clave_p))
        if dia.motivo is None and (dia.fecha is None or not any(
                fecha_de_int(x.get("fecha_int")) == dia.fecha
                for x in grupo)):
            continue
        tipo = NUEVO if lec.get("estado") == _ACTIVA else INVALIDA
        motivo = dia.motivo or (MOTIVO_INVALIDA if tipo == INVALIDA
                                else None)
        out.append(dict(base, tipo=tipo, dia=dia.fecha, motivo=motivo))
    return out


# ----------------------------- bloque (R9-R14) ----------------------------- #

def _motivo_sv5(sv5: Mapping | None) -> str | None:
    """Por que lo que dijo sv5 no deja ajustar (None si deja)."""
    if sv5 is None:
        return MOTIVO_SIN_RESPUESTA
    if not sv5.get("ok"):
        return sv5.get("motivo") or sv5.get("error") or MOTIVO_SIN_RESPUESTA
    accion = sv5.get("accion")
    if accion == "ya_aplicado":
        return MOTIVO_YA_APLICADO
    if accion == "sin_ajuste":
        return MOTIVO_SIN_EXTRAS
    if accion not in _ESCRIBEN:
        return f"respuesta de Sigrid no esperada ({accion})"
    return None


def _item(c: Mapping, v: Mapping) -> dict:
    sv5 = v.get("sv5")
    prop = v.get("propuesta") or c.get("fila") or {}
    fila = c.get("fila") or {}
    informativo = c["tipo"] in (TIPO_RECHAZADO, INVALIDA)
    motivo = c.get("motivo") or v.get("motivo")
    if motivo is None and not informativo:
        motivo = _motivo_sv5(sv5)
    ajustable = not informativo and motivo is None
    if not ajustable:
        decisiones: list[str] = []
    elif c["tipo"] == NUEVO:
        decisiones = [AJUSTAR, NO_AJUSTAR]
    else:
        decisiones = [RECALCULAR, MANTENER]
    dia = c.get("dia") or fecha_de_int(prop.get("fecha_int"))
    obra = ({"ide": prop.get("obra_ide"), "codigo": prop.get("obra_codigo")}
            if (prop.get("obra_ide") or prop.get("obra_codigo")) else None)
    sv5 = sv5 or {}
    periodo = c["periodo"]
    return {
        "clave": c["clave"], "recurso_ide": c["recurso_ide"],
        "periodo": periodo.clave, "inicio": periodo.inicio.isoformat(),
        "fin": periodo.fin.isoformat(), "nombre": c.get("nombre"),
        "tipo": c["tipo"], "id": fila.get("id"), "estado": fila.get("estado"),
        "dia": None if dia is None else dia.isoformat(), "obra": obra,
        "partida_cod": prop.get("partida_cod"),
        "franquicia": sv5.get("franquicia", c.get("franquicia")),
        "franquicia_estado": sv5.get("franquicia_estado",
                                     c.get("franquicia_estado")),
        "franquicia_usada": fila.get("franquicia"),
        "extras": sv5.get("extras"),
        "extras_pendientes": float(v.get("pendientes") or 0.0),
        "objetivo": sv5.get("objetivo"), "actual": sv5.get("actual"),
        "parte_cod": sv5.get("parte_cod") or fila.get("parte_cod"),
        "accion": sv5.get("accion"), "ajustable": ajustable,
        "pide_decision": ajustable, "decisiones": decisiones,
        "motivo": motivo,
        # R15: las lineas de la aprobacion de este (recurso, periodo); el
        # modal manda la decision con la llamada que las lleva.
        "registro_ids": list(c.get("registro_ids") or []),
    }


def bloque_franquicias(cands: Iterable[Mapping],
                       veredictos: Mapping[str, Mapping],
                       aviso: str | None) -> dict:
    """R9-R14, R44: el bloque `franquicias` del preflight.

    `veredictos[clave]` lleva la `propuesta` (dia, obra, partida), lo que
    respondio sv5 `comprobar` (`sv5`, None si fallo), `pendientes` y un
    `motivo` propio (R12) que manda sobre sv5. Solo pide decision (R13) lo
    que se puede ajustar o recalcular."""
    return {"aviso": None if not aviso else AVISO_NO_COMPROBADA + aviso,
            "items": [_item(c, veredictos.get(c["clave"]) or {})
                      for c in cands]}


# ---------------------------- decisiones (R15) ---------------------------- #

#: DA28, R45: lo que la vista de trabajador puede decidir (no ofrece «No
#: ajustar» ni «Mantener»).
DECISIONES_VISTA = (AJUSTAR, RECALCULAR)


def _decision(d) -> tuple[int, str, str]:
    """R15, R45: UNA decision `{recurso_ide, periodo, decision}` ->
    `(recurso, periodo, decision)`: formato, recurso >= 1, periodo
    `YYYY-MM` y decision conocida; si no, `DecisionInvalida` (422)."""
    if not isinstance(d, dict):
        raise DecisionInvalida("franquicias no validas")
    try:
        rec = d["recurso_ide"]
        if isinstance(rec, bool):
            raise TypeError(rec)
        rec = int(rec)
    except (KeyError, TypeError, ValueError):
        raise DecisionInvalida(
            "franquicias no validas: falta el recurso") from None
    periodo = periodo_de_clave(d.get("periodo"))
    if rec <= 0 or periodo is None:
        raise DecisionInvalida("franquicias no validas: recurso o periodo")
    decision = d.get("decision")
    if decision not in DECISIONES:
        raise DecisionInvalida(
            f"decision de franquicia no valida ({decision!r})")
    return rec, periodo.clave, decision


def decision_vista(crudo) -> tuple[int, str, str]:
    """R45 (DA28): la decision de la vista de trabajador; solo `ajustar` o
    `recalcular`. `DecisionInvalida` (422) si no."""
    rec, periodo, decision = _decision(crudo)
    if decision not in DECISIONES_VISTA:
        raise DecisionInvalida(
            f"desde la vista solo se puede ajustar o recalcular ({decision!r})")
    return rec, periodo, decision


def validar_decisiones(crudo, claves_validas: Iterable[str]
                       ) -> list[tuple[int, str, str]]:
    """R15: `[{recurso_ide, periodo, decision}]` -> `[(recurso, periodo,
    decision)]`. Formato, decision conocida, clave de la seleccion y sin
    repetidas; si no, `DecisionInvalida` (422)."""
    if crudo is None:
        return []
    if not isinstance(crudo, list):
        raise DecisionInvalida("franquicias no validas")
    validas = set(claves_validas)
    out: list[tuple[int, str, str]] = []
    vistas: set[str] = set()
    for d in crudo:
        rec, periodo_clave, decision = _decision(d)
        clave = clave_de(rec, periodo_clave)
        if clave not in validas:
            raise DecisionInvalida(
                f"la franquicia {clave} no es de las lineas seleccionadas")
        if clave in vistas:
            raise DecisionInvalida(f"la franquicia {clave} esta repetida")
        vistas.add(clave)
        out.append((rec, periodo_clave, decision))
    return out


# ------------------------------ payload (§6) ------------------------------ #

def payload_franquicia(datos: Mapping, *, extras_pendientes: float = 0.0,
                       usuario: str | None = None) -> dict:
    """design §6: la peticion de sv5 `comprobar`/`ejecutar` a partir de una
    fila de `franquicia_ajuste` (o de una propuesta sin fila: `ajuste_id`
    0, solo para comprobar). Sin X (R41: la lee sv5)."""
    periodo = periodo_de_clave(datos.get("periodo"))
    if periodo is None:
        raise ValueError(f"periodo no valido: {datos.get('periodo')!r}")
    return {
        "ajuste_id": int(datos.get("id") or 0),
        "recurso_ide": int(datos["recurso_ide"]),
        "periodo": periodo.clave, "inicio": periodo.inicio_int,
        "fin": periodo.fin_int, "fecha_int": int(datos.get("fecha_int") or 0),
        "obra": {"ide": datos.get("obra_ide"),
                 "codigo": datos.get("obra_codigo")},
        "partida_ide": datos.get("partida_ide"),
        "partida_cod": datos.get("partida_cod"),
        "extras_pendientes": float(extras_pendientes or 0.0),
        "usuario": usuario,
    }


# ------------------------- vista de trabajador (R20) ------------------------ #

#: R17, R20: aplicar una fila `decidido`/`error` (no es una decision).
ACCION_APLICAR = "aplicar"

#: R20: la accion que admite cada estado de la fila en la vista.
_ACCION_VISTA = {DECIDIDO: [ACCION_APLICAR], ERROR: [ACCION_APLICAR],
                 APLICADO: [RECALCULAR], RECHAZADO: [AJUSTAR]}


def vista_franquicia(periodo: Periodo, recursos: Iterable[int],
                     filas: Mapping[tuple[int, str], Mapping],
                     franquicias: Mapping[int, Mapping] | None,
                     aviso: str | None) -> dict | None:
    """R20, R44: el ajuste del periodo de cada recurso del trabajador.

    Sale un recurso con fila (cualquier estado) o, sin fila, con franquicia
    `activa` (admite `ajustar`). `franquicias` es el mapa de sv5 `/recursos`
    (None si no se pudo comprobar: entonces solo salen las filas, y el
    aviso). None si no hay nada que ensenar."""
    items = []
    for rec in sorted({int(r) for r in recursos}):
        fila = filas.get((rec, periodo.clave))
        lec = (franquicias or {}).get(rec) or {}
        if fila is None and lec.get("estado") != _ACTIVA:
            continue
        fila = fila or {}
        dia = fecha_de_int(fila.get("fecha_int"))
        items.append({
            "recurso_ide": rec, "periodo": periodo.clave,
            "id": fila.get("id"), "estado": fila.get("estado"),
            "x_usada": fila.get("franquicia"),
            "x_actual": lec.get("franquicia"), "x_estado": lec.get("estado"),
            "extras": fila.get("extras"), "ajuste": fila.get("ajuste"),
            "dia": None if dia is None else dia.isoformat(),
            "obra_codigo": fila.get("obra_codigo"),
            "partida_cod": fila.get("partida_cod"),
            "parte_cod": fila.get("parte_cod"),
            "decidido_por": fila.get("decidido_por"),
            "aplicado_por": fila.get("aplicado_por"),
            "error": fila.get("error"),
            "acciones": list(_ACCION_VISTA.get(fila.get("estado"),
                                               [AJUSTAR])),
        })
    if not items and not aviso:
        return None
    return {"periodo": periodo.clave,
            "aviso": None if not aviso else AVISO_NO_COMPROBADA + aviso,
            "items": items}
