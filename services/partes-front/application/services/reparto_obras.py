# application/services/reparto_obras.py
"""F-022 · reparto de una aprobacion en una peticion por obra (puro).

sv5 recibe UNA obra por peticion (`PeticionIn`): sus lineas acaban en el
parte de esa obra. Antes de F-022 un lote de varias obras viajaba entero
con la obra de la primera linea; ahora sv4 lo parte en grupos por obra
(`obra_key_for_registro`) y aqui vive lo que no necesita ni HTTP ni BBDD:

  - `repartir_claves` (R19): las claves de conflicto que pisar llegan con
    el prefijo de su grupo, porque la clave de sv5 no lleva la obra.
  - `agregar_preflight` / `agregar_ejecucion` (R16, R17, R22): los campos
    planos de siempre a partir de las respuestas por grupo. Con un grupo,
    la respuesta tal cual; con varios, sin «todo o nada» (DA16).
"""
from __future__ import annotations

from dataclasses import dataclass, field

SEPARADOR_CLAVE = "::"
#: DA19: con mas filas que esto en el listado, el modal pliega las obras.
UMBRAL_PLEGADO = 40

#: Lo que solo tiene sentido por grupo y no sube a los campos planos.
CLAVES_DE_GRUPO = ("clave", "obra", "registro_ids", "listado")


@dataclass
class GrupoObra:
    """Las lineas de una aprobacion que viajan con UNA obra."""

    clave: str
    obra: dict
    lineas: list[dict]
    estado_previo: dict[int, str] = field(default_factory=dict)

    @property
    def registro_ids(self) -> list[int]:
        return [l["registro_id"] for l in self.lineas]


def repartir_claves(pisar: list[str],
                    claves_grupo: list[str]) -> dict[str, list[str]] | None:
    """R19: `"<grupo>::<clave>"` va al grupo; un grupo desconocido se
    ignora. Una clave SIN prefijo solo es inequivoca con un unico grupo:
    con varios devuelve None (el endpoint responde 422)."""
    reparto: dict[str, list[str]] = {c: [] for c in claves_grupo}
    for bruta in pisar:
        texto = str(bruta)
        grupo, separador, clave = texto.partition(SEPARADOR_CLAVE)
        if separador:
            if grupo in reparto:
                reparto[grupo].append(clave)
            continue
        if len(claves_grupo) != 1:
            return None
        reparto[claves_grupo[0]].append(texto)
    return reparto


def _etiqueta(grupo: dict) -> str:
    """Como se nombra una obra en un mensaje: su codigo o su clave."""
    return (grupo.get("obra") or {}).get("codigo") or grupo.get("clave")


def _concatenar(grupos: list[dict], campo: str) -> list:
    return [x for g in grupos for x in (g.get(campo) or [])]


def _errores(grupos: list[dict]) -> str:
    return "; ".join(f"{_etiqueta(g)}: {g.get('error') or 'error desconocido'}"
                     for g in grupos)


def _sin_claves_de_grupo(grupo: dict) -> dict:
    return {k: v for k, v in grupo.items() if k not in CLAVES_DE_GRUPO}


def sumar_totales(lista: list[dict]) -> dict:
    """R25: los `totales` de varias obras, sumados."""
    por_estado: dict[str, int] = {}
    lineas = incidencias = 0
    ordinarias = extra = 0.0
    for t in lista:
        lineas += t.get("lineas") or 0
        incidencias += t.get("incidencias") or 0
        ordinarias += t.get("horas_ordinarias") or 0.0
        extra += t.get("horas_extra") or 0.0
        for estado, n in (t.get("por_estado") or {}).items():
            por_estado[estado] = por_estado.get(estado, 0) + n
    return {"lineas": lineas, "por_estado": por_estado,
            "horas_ordinarias": round(ordinarias, 2),
            "horas_extra": round(extra, 2), "incidencias": incidencias}


def agregar_preflight(evaluados: list[dict]) -> dict:
    """R16, R17: los campos planos del preflight a partir de los grupos.

    `ok` si ALGUN grupo se pudo evaluar; obra destino y modo pruebas, los
    del primero que se evaluo; `sesame_bloqueo` si algun grupo lo tiene.
    """
    if len(evaluados) == 1:
        return _sin_claves_de_grupo(evaluados[0])
    evaluables = [g for g in evaluados if g.get("ok")]
    plano: dict = {"ok": bool(evaluables)}
    for campo in ("partes", "acciones", "conflictos", "avisos_calendario"):
        plano[campo] = _concatenar(evaluados, campo)
    resumen: dict[str, float] = {}
    for g in evaluados:
        for clave, valor in (g.get("resumen") or {}).items():
            if isinstance(valor, (int, float)):
                resumen[clave] = resumen.get(clave, 0) + valor
    plano["resumen"] = resumen
    if evaluables:
        plano["obra_destino"] = evaluables[0].get("obra_destino")
        plano["forzada_pruebas"] = evaluables[0].get("forzada_pruebas")
    else:
        plano["error"] = "ninguna obra se pudo evaluar: " + _errores(evaluados)
    bloqueos = [g["sesame_bloqueo"] for g in evaluados
                if g.get("sesame_bloqueo")]
    if bloqueos:
        plano["sesame_bloqueo"] = bloqueos[0]
    plano["totales"] = sumar_totales([g.get("totales") or {}
                                      for g in evaluados])
    return plano


def agregar_ejecucion(ejecutados: list[dict]) -> dict:
    """R22: el resultado plano de registrar varias obras, una a una.

    `ok` solo si TODAS fueron bien (un grupo bloqueado por Sesame llega con
    `ok` falso); `parcial` si unas si y otras no. No hay «todo o nada»:
    lo escrito en una obra no se deshace porque otra falle (DA16).
    """
    if len(ejecutados) == 1:
        return dict(_sin_claves_de_grupo(ejecutados[0]), parcial=False)
    bien = [g for g in ejecutados if g.get("ok")]
    ok = len(bien) == len(ejecutados)
    plano: dict = {"ok": ok, "parcial": not ok and bool(bien)}
    for campo in ("escritas", "omitidas", "ya_registradas", "pisadas",
                  "pendientes_confirmacion", "partes"):
        plano[campo] = _concatenar(ejecutados, campo)
    plano["borradas"] = sum(int(g.get("borradas") or 0) for g in ejecutados)
    if bien:
        plano["obra_destino"] = bien[0].get("obra_destino")
        plano["forzada_pruebas"] = bien[0].get("forzada_pruebas")
    if not ok:
        plano["error"] = _errores([g for g in ejecutados if not g.get("ok")])
    return plano


# --------------------------------------------------------------------- #
# DA19 · el listado del modal: lo que sv5 hara de verdad con cada linea.
# --------------------------------------------------------------------- #

#: Estados del listado en los que la linea SE ESCRIBE (o se escribira si
#: el humano pisa el conflicto): son los que suman horas (R25).
ESTADOS_ESCRITURA = ("nuevo", "reaprobacion", "conflicto")

#: `sigrid_estado` previos que hacen de la escritura una reaprobacion.
ESTADOS_REAPROBACION = ("borrado_sigrid", "error", "omitido", "conflicto",
                        "encolado")

#: Orden de los tipos dentro de un mismo dia y trabajador.
ORDEN_TIPOS = ("ordinaria", "extra", "incidencia")


def _tipo(linea: dict) -> str:
    if linea.get("es_incidencia"):
        return "incidencia"
    if (linea.get("tipo_hora") or "").strip().lower() == "extra":
        return "extra"
    return "ordinaria"


def _estado(accion: dict, conflicto: dict | None,
            previo: str) -> tuple[str, str]:
    """R24 para un grupo que sv5 pudo evaluar."""
    if conflicto is not None:
        return "conflicto", (
            "ya hay una linea en Sigrid con el mismo codigo de hora (parte "
            f"{conflicto.get('parte_cod') or '?'}): decide si se pisa")
    if accion.get("accion") == "omitir":
        return "omitida", (accion.get("motivo")
                           or "las reglas de registro la omiten")
    if accion.get("accion") == "ya_registrado":
        return "ya_registrada", (accion.get("motivo")
                                 or "ya estaba en Sigrid: no se duplica")
    if previo in ESTADOS_REAPROBACION:
        return "reaprobacion", f"antes: {previo}"
    return "nuevo", ""


def listado_grupo(grupo: GrupoObra, pf: dict) -> list[dict]:
    """R23, R24: una fila por linea del grupo con lo que se escribira.

    Cruza por `registro_id` con las `acciones` y los `conflictos` del
    preflight de sv5: codigo de hora, partida, recurso y horas salen de la
    accion si los trae (las reglas de sv5 pueden cambiarlos) y, si no, de
    la linea. Si el preflight del grupo fallo, nada se registra.
    """
    acciones = {a.get("registro_id"): a for a in (pf.get("acciones") or [])}
    en_conflicto: dict = {}
    for c in pf.get("conflictos") or []:
        for rid in c.get("registros") or []:
            en_conflicto.setdefault(rid, c)
    filas = []
    for linea in grupo.lineas:
        rid = linea["registro_id"]
        accion = acciones.get(rid) or {}
        if pf.get("ok"):
            estado, motivo = _estado(accion, en_conflicto.get(rid),
                                     grupo.estado_previo.get(rid, ""))
        else:
            estado = "no_se_registra"
            motivo = str(pf.get("error") or "no se pudo evaluar la obra")
        horas = linea.get("horas")
        if estado in ESTADOS_ESCRITURA and accion.get("can") is not None:
            horas = accion["can"]
        filas.append({
            "registro_id": rid,
            "fecha_int": linea.get("fecha_int"),
            "nombre": linea.get("nombre"),
            "tipo": _tipo(linea),
            "hora_codigo": accion.get("hora_codigo") or linea.get("hora_codigo"),
            "horas": horas,
            "partida_cod": accion.get("partida_cod") or linea.get("partida_cod"),
            "recurso_ide": accion.get("recurso_ide") or linea.get("recurso_ide"),
            "estado": estado,
            "motivo": motivo,
        })
    # `fecha_int` siempre es entero: el repositorio pone 0 si falta.
    filas.sort(key=lambda f: (f["fecha_int"], (f["nombre"] or "").lower(),
                              ORDEN_TIPOS.index(f["tipo"]), f["registro_id"]))
    return filas


def totales(listado: list[dict]) -> dict:
    """R25: lineas por estado y lo que se ESCRIBIRA (horas ordinarias,
    horas extra e incidencias); lo omitido o ya registrado no suma."""
    por_estado: dict[str, int] = {}
    ordinarias = extra = 0.0
    incidencias = 0
    for fila in listado:
        por_estado[fila["estado"]] = por_estado.get(fila["estado"], 0) + 1
        if fila["estado"] not in ESTADOS_ESCRITURA:
            continue
        if fila["tipo"] == "incidencia":
            incidencias += 1
        elif fila["tipo"] == "extra":
            extra += float(fila["horas"] or 0.0)
        else:
            ordinarias += float(fila["horas"] or 0.0)
    return {"lineas": len(listado), "por_estado": por_estado,
            "horas_ordinarias": round(ordinarias, 2),
            "horas_extra": round(extra, 2), "incidencias": incidencias}
