# application/services/racha_incidencia.py
"""F-060 · Rol de cada incidencia en su racha (logica pura, sin BBDD).

En Sigrid una racha de incidencia (vacaciones, baja...) se registra con
su codigo CI* el primer dia y UN `CIZ` el ultimo (semantica 4). sv4 sabe
que dias trabajo o falto la persona (base `partes`, todas las obras) y
decide el rol de cada linea de incidencia del dia D; sv5 sabe que hay en
Sigrid y mueve el CIZ (no se duplica ni se borra). Aqui vive la parte de
sv4:

  - `ventana` (DA1): del dia 1 del mes anterior al de D hasta D - 1;
    `hasta_delante`: el ultimo dia del mes siguiente al de D.
  - Dia trabajado: alguna linea activa que no es incidencia con horas
    (|horas| > 0). Dia de incidencia X: no trabajado y con alguna
    incidencia activa de clave X. Un dia sin lineas activas, o solo con
    lineas a 0 h que no son incidencia, se salta.
  - `decidir` (R2-R5, R9): el ultimo dia que cuenta de la ventana decide:
    incidencia de la misma clave => `fin`; si no (trabajado, otra clave o
    nada) => `inicio`. Con `fin`, `racha_registro_ids` son las
    incidencias de esa clave de la racha hacia atras y hacia delante (sin
    el dia D) y las de la papelera de esa clave `registrado` o
    `encolado` de cualquier dia distinto de D entre el primero y el
    ultimo del tramo que forman la racha y D, tambien de los dias
    saltados (DA13): entre sus synckeys busca sv5 el CIZ.
  - `colapsar` (R7, R8): en una aprobacion, un solo `fin` por racha (el
    de mayor fecha) y un solo `inicio` por dia, persona y clave (el de
    menor `registro_id`); los demas, `intermedio`.
  - `aviso_desordenada` (R10): el siguiente dia que cuenta tras D tiene
    una incidencia ya registrada (DA7: aviso, nada se mueve hacia atras).
  - `clave_incidencia` (DA4): la letra de la tabla de F-025 o, si no la
    reconoce, el codigo de la incidencia o el de hora, normalizados.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from application.services.incidencias_horas import (
    TablaIncidencias,
    normalizar_codigo,
)

INICIO, FIN, INTERMEDIO = "inicio", "fin", "intermedio"

#: Estados de una linea de la papelera cuya synckey puede seguir en Sigrid.
ESTADOS_EN_SIGRID = ("registrado", "encolado")

#: Estado de una incidencia ya escrita (R10).
ESTADO_REGISTRADO = "registrado"

#: Prefijo del aviso de R10 y largo maximo de un motivo.
MOTIVO_DESORDENADA = "racha_desordenada"
LIMITE_MOTIVO = 255

#: Prefijo del motivo de la linea cuyo CIZ se movio a otro dia (R28).
MOTIVO_FIN_MOVIDO = "fin_movido"

#: Por debajo de esto, una cantidad de horas es cero (como F-025).
_EPSILON = 1e-9

#: Marca de un dia trabajado en `_dias`.
_TRABAJADO = "trabajado"


@dataclass(frozen=True)
class LineaHist:
    """Lo que la regla necesita de una linea del portal de la persona."""
    registro_id: int
    fecha_int: int
    es_incidencia: bool
    clave: str
    horas: float | None
    sigrid_estado: str | None
    activa: bool


@dataclass(frozen=True)
class DecisionRacha:
    rol: str                                 # inicio | fin
    racha_registro_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class LineaRol:
    """Una incidencia de la aprobacion con su rol de `decidir` (R7, R8)."""
    registro_id: int
    persona: str
    fecha_int: int
    clave: str
    rol: str
    racha_registro_ids: tuple[int, ...] = ()


def clave_incidencia(incidencia_codigo: str | None, hora_codigo: str | None,
                     tabla: TablaIncidencias | None) -> str:
    """DA4: la letra de la tabla; si no la reconoce (o no hay tabla), el
    codigo de la incidencia o, si falta, el de hora, normalizados."""
    if tabla is not None:
        clase = tabla.clase_de(incidencia_codigo, hora_codigo)
        if clase is not None:
            return clase.letra
    return (normalizar_codigo(incidencia_codigo)
            or normalizar_codigo(hora_codigo))


def _fecha(fecha_int: int) -> date:
    f = int(fecha_int)
    return date(f // 10000, (f // 100) % 100, f % 100)


def _entero(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def ventana(fecha_int: int) -> tuple[int, int]:
    """DA1: (dia 1 del mes anterior al de D, D - 1)."""
    d = _fecha(fecha_int)
    ano, mes = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    return ano * 10000 + mes * 100 + 1, _entero(d - timedelta(days=1))


def hasta_delante(fecha_int: int) -> int:
    """R9, R10: el ultimo dia del mes siguiente al de D."""
    d = _fecha(fecha_int)
    ano, mes = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return ano * 10000 + mes * 100 + calendar.monthrange(ano, mes)[1]


def _dias(hist: Iterable[LineaHist], desde: int,
          hasta: int) -> dict[int, object]:
    """Los dias que cuentan en [desde, hasta]: `_TRABAJADO` o el conjunto
    de claves de sus incidencias. Solo lineas activas (R5)."""
    trabajados: set[int] = set()
    claves: dict[int, set[str]] = {}
    for linea in hist:
        f = int(linea.fecha_int or 0)
        if not linea.activa or not desde <= f <= hasta:
            continue
        if linea.es_incidencia:
            claves.setdefault(f, set()).add(linea.clave)
        elif abs(float(linea.horas or 0.0)) > _EPSILON:
            trabajados.add(f)
    dias: dict[int, object] = dict(claves)
    for f in trabajados:
        dias[f] = _TRABAJADO
    return dias


def _de_la_racha(estado: object, clave: str) -> bool:
    return estado != _TRABAJADO and clave in estado  # type: ignore[operator]


def decidir(hist: Sequence[LineaHist], fecha_int: int,
            clave: str) -> DecisionRacha:
    """R2-R5, R9: el rol de una incidencia de clave `clave` del dia D."""
    desde, hasta = ventana(fecha_int)
    atras = _dias(hist, desde, hasta)
    previos = sorted(atras, reverse=True)
    if not previos or not _de_la_racha(atras[previos[0]], clave):
        return DecisionRacha(INICIO)
    racha: set[int] = set()
    for f in previos:
        if not _de_la_racha(atras[f], clave):
            break
        racha.add(f)
    delante = _dias(hist, int(fecha_int) + 1, hasta_delante(fecha_int))
    for f in sorted(delante):
        if not _de_la_racha(delante[f], clave):
            break
        racha.add(f)
    # DA13: la papelera viaja desde el primer dia hasta el ultimo del
    # tramo que forman la racha y D, tambien la de los dias saltados.
    d = int(fecha_int)
    primero, ultimo = min(racha | {d}), max(racha | {d})

    def viaja(l: LineaHist) -> bool:
        f = int(l.fecha_int or 0)
        if not l.es_incidencia or l.clave != clave:
            return False
        if l.activa:
            return f in racha
        return (primero <= f <= ultimo and f != d
                and (l.sigrid_estado or "") in ESTADOS_EN_SIGRID)

    ids = {l.registro_id for l in hist if viaja(l)}
    return DecisionRacha(FIN, tuple(sorted(ids)))


def colapsar(lineas: Sequence[LineaRol]) -> dict[int, str]:
    """R7, R8: el rol final de cada linea de la aprobacion.

    Dos `fin` son de la misma racha si son de la misma persona y clave y
    o son del mismo dia o uno esta en la racha del otro (y, por cadena,
    los que se tocan). De cada racha conserva el `fin` el de mayor fecha
    (empate: menor `registro_id`). De varios `inicio` del mismo dia,
    persona y clave, el de menor `registro_id`. Los demas, `intermedio`."""
    roles = {l.registro_id: l.rol for l in lineas}
    fines = [l for l in lineas if l.rol == FIN]
    padre = {l.registro_id: l.registro_id for l in fines}

    def raiz(i: int) -> int:
        while padre[i] != i:
            i = padre[i]
        return i

    for a in fines:
        for b in fines:
            if (a.registro_id < b.registro_id and a.persona == b.persona
                    and a.clave == b.clave
                    and (a.fecha_int == b.fecha_int
                         or a.registro_id in b.racha_registro_ids
                         or b.registro_id in a.racha_registro_ids)):
                padre[raiz(b.registro_id)] = raiz(a.registro_id)
    grupos: dict[int, list[LineaRol]] = {}
    for l in fines:
        grupos.setdefault(raiz(l.registro_id), []).append(l)
    inicios: dict[tuple[str, int, str], list[LineaRol]] = {}
    for l in lineas:
        if l.rol == INICIO:
            inicios.setdefault((l.persona, l.fecha_int, l.clave), []).append(l)
    for grupo in [*grupos.values(), *inicios.values()]:
        queda = max(grupo, key=lambda l: (l.fecha_int, -l.registro_id))
        for l in grupo:
            if l is not queda:
                roles[l.registro_id] = INTERMEDIO
    return roles


def aviso_desordenada(hist: Sequence[LineaHist],
                      fecha_int: int) -> int | None:
    """R10: la fecha del siguiente dia que cuenta tras D (hasta el ultimo
    del mes siguiente) si tiene alguna incidencia activa `registrado`;
    None si no."""
    delante = _dias(hist, int(fecha_int) + 1, hasta_delante(fecha_int))
    if not delante:
        return None
    siguiente = min(delante)
    hay = any(int(l.fecha_int or 0) == siguiente and l.activa
              and l.es_incidencia and l.sigrid_estado == ESTADO_REGISTRADO
              for l in hist)
    return siguiente if hay else None


def motivo_fin_movido(hmores_ide: object, fecha_int: object) -> str:
    """R28: el motivo de la linea X cuyo CIZ (`hmores_ide`) paso al dia D."""
    try:
        f = f"{int(fecha_int):08d}"
        dia = f"{f[:4]}-{f[4:6]}-{f[6:]}"
    except (TypeError, ValueError):
        dia = "?"
    return (f"{MOTIVO_FIN_MOVIDO}: el fin de la incidencia (CIZ, linea "
            f"{hmores_ide}) paso al dia {dia}")[:LIMITE_MOTIVO]


def motivo_desordenada(fecha_int: int) -> str:
    """R10: el texto del aviso (DA7: se corrige a mano)."""
    f = f"{int(fecha_int):08d}"
    return (f"{MOTIVO_DESORDENADA}: el {f[:4]}-{f[4:6]}-{f[6:]}, siguiente "
            "día con partes, ya tiene una incidencia registrada en Sigrid; "
            "esta línea no mueve su inicio ni su fin. Revisa la racha a "
            "mano")[:LIMITE_MOTIVO]
