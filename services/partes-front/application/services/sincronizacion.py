# application/services/sincronizacion.py
"""F-052 · Comparacion pura entre las lineas del portal y las de Sigrid.

Una sincronizacion (obra o persona, periodo visible) lee las lineas del
portal (base `partes`) y las de Sigrid (sv5 `POST /api/sincronizar/leer`) y
las clasifica aqui, sin E/S, en UNA de las 12 clases de R8 (design §3).

Casado (glosario): por synckey (`origen = partes` y su `registro_id`, que
pone sv5: sv4 no conoce el formato) y, sin ella, el respaldo de F-024: la
fila del `sigrid_hmores_ide` guardado, sin synckey, mismo recurso y fecha y
(si el portal lo sabe) mismo parte.

Prioridad: `encolado` (en vuelo, no se compara) y `dedicacion` (no viaja)
antes que el casado; despues, casada o no, segun el estado del portal.

`firma` es la huella de lo que el usuario vio de un item (clase y valores
de los dos lados): `aplicar` (R18) solo toca los items cuya firma no cambio.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, fields
from typing import Any

CLASES: tuple[str, ...] = (
    "igual", "distinta", "anulada_en_sigrid", "borrada_en_sigrid",
    "en_sigrid_sin_registrar", "pendiente", "no_viaja", "en_vuelo",
    "solo_sigrid_nuestra", "solo_sigrid_ajena", "solo_sigrid_manual",
    "solo_sigrid_auxiliar")

#: R16 (design §4): acciones hacia el portal por clase. `restaurar` solo se
#: ofrece si la linea esta en la papelera (`acciones_de`).
ACCIONES_POR_CLASE: dict[str, tuple[str, ...]] = {
    "igual": (), "distinta": ("traer_de_sigrid",),
    "anulada_en_sigrid": ("traer_de_sigrid",),
    "borrada_en_sigrid": ("a_papelera", "reaprobar"),
    "en_sigrid_sin_registrar": ("marcar_registrada",),
    "pendiente": ("reaprobar",), "no_viaja": (), "en_vuelo": (),
    "solo_sigrid_nuestra": ("restaurar",), "solo_sigrid_ajena": (),
    "solo_sigrid_manual": (), "solo_sigrid_auxiliar": ()}

#: R9: diferencia de horas por debajo de la cual no se avisa (la de F-024).
TOLERANCIA_HORAS = 0.005

#: DA14: motivos de `omitido` por los que sv5 pide reaprobar.
MOTIVOS_REAPROBAR: tuple[str, ...] = ("parte_no_abierto", "pisada_no_anulada")

#: Estados del portal (`sigrid_estado` normalizado).
REGISTRADO = "registrado"
BORRADO_SIGRID = "borrado_sigrid"
ENCOLADO = "encolado"
DEDICACION = "dedicacion"
OMITIDO = "omitido"

#: Origen de Sigrid (sv5) -> clase de la linea que no casa (DA12).
_CLASE_SOLO_SIGRID = {
    "partes": "solo_sigrid_nuestra", "ciz": "solo_sigrid_auxiliar",
    "franquicia": "solo_sigrid_auxiliar", "ajena": "solo_sigrid_ajena",
    "manual": "solo_sigrid_manual"}


@dataclass(frozen=True)
class LineaPortal:
    """Lo que la sincronizacion necesita de una linea del portal."""
    registro_id: int
    fecha_int: int | None
    recurso_ide: int | None
    obra_ide: int | None
    horas: float | None
    extra: bool
    es_incidencia: bool
    hora_codigo: str | None
    partida_ide: int | None
    partida_cod: str | None
    sigrid_estado: str | None
    sigrid_motivo: str | None
    sigrid_hmores_ide: int | None
    sigrid_hmoide: int | None


@dataclass(frozen=True)
class LineaSigridSync:
    """Una linea de Sigrid tal como la devuelve sv5 (R2)."""
    hmores_ide: int
    hmoide: int | None
    parte_cod: str | None
    parte_est: int | None
    obra_ide: int | None
    obra_cod: str | None
    recurso_ide: int | None
    fecha_int: int | None
    hora_ide: int | None
    hora_cod: str | None
    hora_ext: int | None
    partida_ide: int | None
    partida_cod: str | None
    can: float | None
    tot: float | None
    enlazada: bool
    origen: str
    registro_id: int | None = None
    ajuste_id: int | None = None

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> LineaSigridSync:
        """Del JSON de sv5; las claves que sobren se ignoran."""
        return cls(**{f.name: d.get(f.name) for f in fields(cls)})


@dataclass(frozen=True)
class Diferencia:
    campo: str
    portal: Any
    sigrid: Any


@dataclass
class ItemSync:
    """Un item del resultado: una linea del portal, de Sigrid o las dos."""
    clase: str
    registro_id: int | None
    portal: LineaPortal | None = None
    sigrid: LineaSigridSync | None = None
    diferencias: list[Diferencia] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    a_cero: bool = False
    #: R12: donde esta la linea del portal de un `solo_sigrid_nuestra`.
    donde: str | None = None
    #: R10: `registrado` sin pareja; lo confirma la comprobacion de F-024.
    por_confirmar: bool = False
    #: Segunda linea de Sigrid con la synckey de una linea ya casada.
    repetida: bool = False


def _estado(p: LineaPortal) -> str:
    return (p.sigrid_estado or "").strip().lower()


def _cod(valor: str | None) -> str:
    return (valor or "").strip().upper()


def _cero(valor: float | None) -> bool:
    return abs(float(valor or 0.0)) <= TOLERANCIA_HORAS


def _clase_hora(extra: bool) -> str:
    return "extra" if extra else "ordinaria"


def _prefijo_motivo(motivo: str | None) -> str:
    """Como agrupa el modal (F-034): lo de antes de los primeros dos puntos
    o el motivo entero; sin motivo, `omitido`."""
    return (motivo or "").split(":", 1)[0].strip() or OMITIDO


def comparar(p: LineaPortal,
             s: LineaSigridSync) -> tuple[list[Diferencia], list[str]]:
    """R9: diferencias `{campo, portal, sigrid}` y notas de una pareja.

    Horas con tolerancia y clase de hora, no en incidencias; el codigo de
    hora con la misma clase es nota (las reglas de sv5 lo cambian). Recurso
    y obra solo si el portal los sabe; la partida por ide si los dos lo
    tienen y, si no, por codigo."""
    difs: list[Diferencia] = []
    notas: list[str] = []
    clase_distinta = False
    if not p.es_incidencia:
        if abs(float(p.horas or 0.0) - float(s.can or 0.0)) > TOLERANCIA_HORAS:
            difs.append(Diferencia("horas", p.horas, s.can))
        if s.hora_ext is not None and bool(s.hora_ext) != bool(p.extra):
            clase_distinta = True
            difs.append(Diferencia("clase_hora", _clase_hora(p.extra),
                                   _clase_hora(bool(s.hora_ext))))
    if not clase_distinta and _cod(p.hora_codigo) != _cod(s.hora_cod):
        notas.append(f"código de hora: {p.hora_codigo} en el portal, "
                     f"{s.hora_cod} en Sigrid")
    pi, si = p.partida_ide or None, s.partida_ide or None
    if pi is not None and si is not None:
        partida_distinta = pi != si
    else:
        partida_distinta = _cod(p.partida_cod) != _cod(s.partida_cod)
    if partida_distinta:
        difs.append(Diferencia("partida", p.partida_cod or pi,
                               s.partida_cod or si))
    if p.recurso_ide is not None and p.recurso_ide != s.recurso_ide:
        difs.append(Diferencia("recurso", p.recurso_ide, s.recurso_ide))
    if p.fecha_int != s.fecha_int:
        difs.append(Diferencia("fecha", p.fecha_int, s.fecha_int))
    if p.obra_ide is not None and p.obra_ide != s.obra_ide:
        difs.append(Diferencia("obra", p.obra_ide, s.obra_ide))
    return difs, notas


def _respaldo(p: LineaPortal, s: LineaSigridSync | None) -> bool:
    """El respaldo estricto de F-024 (R3 de F-024)."""
    return (s is not None and s.origen == "manual"
            and p.recurso_ide is not None and s.recurso_ide == p.recurso_ide
            and s.fecha_int == p.fecha_int
            and (p.sigrid_hmoide is None or s.hmoide == p.sigrid_hmoide))


def _item_portal(p: LineaPortal, s: LineaSigridSync | None,
                 notas: list[str]) -> ItemSync:
    estado = _estado(p)
    item = ItemSync(clase="", registro_id=p.registro_id, portal=p, sigrid=s,
                    notas=list(notas))
    if estado == ENCOLADO:
        item.clase = "en_vuelo"
    elif estado == DEDICACION:
        item.clase = "no_viaja"
        if s is not None:
            item.notas.append(f"aparece en Sigrid (línea {s.hmores_ide})")
    elif s is not None:
        item.diferencias, notas_cmp = comparar(p, s)
        item.notas.extend(notas_cmp)
        if estado != REGISTRADO:
            item.clase = "en_sigrid_sin_registrar"
        elif (not p.es_incidencia and not _cero(p.horas)
              and _cero(s.can)):
            item.clase = "anulada_en_sigrid"
        else:
            item.clase = "distinta" if item.diferencias else "igual"
    elif estado == REGISTRADO:
        item.clase, item.por_confirmar = "borrada_en_sigrid", True
    elif estado == BORRADO_SIGRID:
        item.clase = "borrada_en_sigrid"
    elif estado == OMITIDO:
        prefijo = _prefijo_motivo(p.sigrid_motivo)
        item.clase = ("pendiente" if prefijo in MOTIVOS_REAPROBAR
                      else "no_viaja")
        if item.clase == "no_viaja":
            item.notas.append(prefijo)
    else:
        item.clase = "pendiente"
    return item


def clasificar(portal: Iterable[LineaPortal],
               sigrid: Iterable[LineaSigridSync]) -> list[ItemSync]:
    """R8: un item por linea; primero las del portal (por id) y luego las de
    Sigrid sin pareja (por `hmores.ide`)."""
    lineas_p = sorted(portal, key=lambda p: p.registro_id)
    lineas_s = sorted(sigrid, key=lambda s: s.hmores_ide)
    por_registro: dict[int, LineaSigridSync] = {}
    for s in lineas_s:
        if s.origen == "partes" and s.registro_id is not None:
            por_registro.setdefault(s.registro_id, s)
    por_ide = {s.hmores_ide: s for s in lineas_s}
    usadas: set[int] = set()
    items: list[ItemSync] = []
    for p in lineas_p:
        s = por_registro.get(p.registro_id)
        notas: list[str] = []
        if s is None and p.sigrid_hmores_ide is not None:
            candidata = por_ide.get(int(p.sigrid_hmores_ide))
            if candidata is not None and candidata.hmores_ide not in usadas \
                    and _respaldo(p, candidata):
                s = candidata
                notas.append(f"casada por la línea {s.hmores_ide} "
                             "(sin synckey en Sigrid)")
        if s is not None:
            usadas.add(s.hmores_ide)
        items.append(_item_portal(p, s, notas))
    for s in lineas_s:
        if s.hmores_ide in usadas:
            continue
        item = ItemSync(clase=_CLASE_SOLO_SIGRID.get(s.origen,
                                                     "solo_sigrid_ajena"),
                        registro_id=s.registro_id, sigrid=s,
                        a_cero=_cero(s.can)
                        and not _cod(s.hora_cod).startswith("CI"))
        casada = por_registro.get(s.registro_id) if s.origen == "partes" \
            else None
        if casada is not None and casada.hmores_ide in usadas:
            item.repetida = True
            item.notas.append(f"synckey repetida: la línea {s.registro_id} "
                              f"ya casa con la {casada.hmores_ide}")
        items.append(item)
    return items


def acciones_de(item: ItemSync) -> tuple[str, ...]:
    """R16: las acciones de la clase; `restaurar`, solo desde la papelera."""
    if item.clase == "solo_sigrid_nuestra" and (
            item.donde != "papelera" or item.repetida):
        return ()
    return ACCIONES_POR_CLASE[item.clase]


def firma(item: ItemSync) -> str:
    """R18: sha256 (16 hex) del JSON canonico de clase y los dos lados."""
    datos = {"clase": item.clase,
             "portal": asdict(item.portal) if item.portal else None,
             "sigrid": asdict(item.sigrid) if item.sigrid else None}
    texto = json.dumps(datos, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def item_a_dict(item: ItemSync) -> dict[str, Any]:
    """El item tal como viaja al navegador (R13)."""
    return {
        "clase": item.clase, "registro_id": item.registro_id,
        "hmores_ide": item.sigrid.hmores_ide if item.sigrid else None,
        "portal": asdict(item.portal) if item.portal else None,
        "sigrid": asdict(item.sigrid) if item.sigrid else None,
        "diferencias": [asdict(d) for d in item.diferencias],
        "notas": list(item.notas), "a_cero": item.a_cero,
        "donde": item.donde, "acciones": list(acciones_de(item)),
        "firma": firma(item)}


def resumen(items: Iterable[ItemSync]) -> dict[str, Any]:
    """R13: recuento por clase (las 12, en orden) y de lineas a 0 (DA13)."""
    por_clase = {c: 0 for c in CLASES}
    total = a_cero = 0
    for it in items:
        por_clase[it.clase] += 1
        total += 1
        a_cero += 1 if it.a_cero else 0
    return {"total": total, "por_clase": por_clase, "a_cero": a_cero}
