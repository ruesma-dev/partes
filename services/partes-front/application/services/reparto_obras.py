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
