# application/services/medicion_casado.py
"""F-036 · R24-R28: el nucleo PURO de la medicion del impacto.

Lo usa `medir_casado_recursos.py` (herramienta de consola de SOLO LECTURA)
antes de desplegar, para saber que cambiara:

  - `medir_maestro` (R24): por empresa, los recursos de alta a `hoy`:
    `persona` (`res.cla = 1`), de ellos `sin_dni` (no casan por nombre),
    `dni_solo_ficha` (`res.cif` vacio y ficha con DNI) y
    `cif_distinto_ficha` (los dos con DNI y distintos: DA1), y
    `mo_no_persona` (codigo `MO/` que no es persona: los que F-030 casaba
    y R2 deja fuera).
  - `medir_lineas` (R25-R26): por linea activa, que hara la pasada del
    conciliador con su recurso (`igual`, `cambia`, `pierde`, `gana`) y que
    daria el casado de F-036 con lo leido frente al guardado (`igual`,
    `otro_recurso`, `otra_persona`, `casado_nuevo`, `pierde_casado`). Solo
    informativo (DA2: lo ingerido no se re-casa). Las congeladas, aparte.
  - `resumir`, `csv_lineas` e `informe_markdown`: los recuentos y los
    textos del informe.

Sin red ni base. Nada de lo que sale lleva nombres ni DNIs (R27): ids,
empresa y categorias.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from application.services import text_match as tm
from application.services.casado_recurso import casar_trabajador
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import (
    IndicePersonas,
    de_alta,
    es_persona,
)
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import RecursoRow

#: Columnas de la tabla por empresa (R24), en orden.
COLUMNAS_MAESTRO = ("persona", "sin_dni", "dni_solo_ficha",
                    "cif_distinto_ficha", "mo_no_persona")
#: Columnas del CSV por linea (R27), en orden.
COLUMNAS_LINEA = ("registro_id", "document_id", "empresa", "recurso",
                  "casado")
#: Metodos guardados de una linea casada sin ficha (F-030/F-036). Es el
#: `METODOS_RECURSO` de `persist_parte_pipeline`: no se importa de alli
#: porque un servicio de aplicacion no depende de un pipeline (la
#: dependencia va al reves); el test
#: `test_f036_r26_metodos_recurso_iguales_que_el_pipeline` los mantiene iguales.
_METODOS_RECURSO = frozenset({"recurso_dni", "recurso_nombre"})


@dataclass(frozen=True)
class LineaMedida:
    """Lo que el script lee de una linea activa, sin mas."""

    registro_id: int
    document_id: str
    empresa: int | None              # la del parte
    obra_ide: int | None
    fecha_int: int | None
    dni_leido: str | None
    nombre_leido: str | None
    empleado_ide: int | None
    empleado_dni: str | None
    empleado_reside: int | None
    empleado_match_method: str | None
    recurso_ide: int | None
    congelada: bool


# =============================== R24 ===================================== #

def medir_maestro(
    indice: IndicePersonas, recursos: Iterable[RecursoRow], hoy: int
) -> list[dict]:
    """R24: una fila por empresa (la sin empresa al final)."""
    por_empresa: dict[int | None, Counter] = {}
    for r in recursos:
        if not de_alta(r.fecbaj, hoy):
            continue
        cuenta = por_empresa.setdefault(r.empresa, Counter())
        if not es_persona(r):
            if (r.codigo or "").startswith("MO/"):
                cuenta["mo_no_persona"] += 1
            continue
        cuenta["persona"] += 1
        ficha = indice.ficha_enlazada(r)
        dni_ficha = tm.normalize_dni(ficha.dni) if ficha is not None else ""
        cif = tm.normalize_dni(r.cif)
        if not indice.dni_de_recurso(r):
            cuenta["sin_dni"] += 1
        elif not cif:
            cuenta["dni_solo_ficha"] += 1
        elif dni_ficha and dni_ficha != cif:
            cuenta["cif_distinto_ficha"] += 1
    orden: list[int | None] = sorted(
        e for e in por_empresa if e is not None)
    if None in por_empresa:
        orden.append(None)
    return [
        {"empresa": e, **{c: por_empresa[e][c] for c in COLUMNAS_MAESTRO}}
        for e in orden
    ]


# ============================ R25 y R26 ================================== #

def medir_lineas(
    lineas: Iterable[LineaMedida],
    indice: IndicePersonas,
    matcher: EmpleadoMatcher,
    aliases: Mapping[str, dict],
    hoy: int,
) -> list[dict]:
    """R25-R26: una fila por linea, sin datos personales (R27)."""
    filas = []
    for linea in lineas:
        if linea.congelada:
            recurso = casado = "congelada"
        else:
            recurso = _recurso(linea, indice, hoy)
            casado = _casado(linea, indice, matcher, aliases, hoy)
        filas.append({
            "registro_id": linea.registro_id,
            "document_id": linea.document_id,
            "empresa": linea.empresa,
            "recurso": recurso,
            "casado": casado,
        })
    return filas


def _recurso(linea: LineaMedida, indice: IndicePersonas, hoy: int) -> str:
    """R25: lo que hara `elegir_recurso` en la pasada del conciliador."""
    empresa = indice.empresa_de_obra(linea.obra_ide)
    if empresa is None:
        empresa = linea.empresa
    nuevo = indice.elegir_recurso(
        linea.empleado_dni, linea.empleado_ide, linea.empleado_reside,
        empresa, linea.fecha_int or hoy,
    ).ide
    antes = linea.recurso_ide
    if nuevo == antes:
        return "igual"
    if nuevo is None:
        return "pierde"
    if antes is None:
        return "gana"
    return "cambia"


def _casado(
    linea: LineaMedida,
    indice: IndicePersonas,
    matcher: EmpleadoMatcher,
    aliases: Mapping[str, dict],
    hoy: int,
) -> str:
    """R26: el casado de F-036 con lo leido frente al guardado."""
    nuevo = casar_trabajador(
        dni_leido=linea.dni_leido, nombre_leido=linea.nombre_leido,
        alias=lambda: aliases.get(tm.normalize(linea.nombre_leido)),
        indice=indice, matcher=matcher, empresa=linea.empresa,
        fecha=linea.fecha_int or hoy,
    )
    antes_casado = (linea.empleado_ide is not None
                    or linea.empleado_match_method in _METODOS_RECURSO)
    ahora_casado = _casado_ok(nuevo)
    if not antes_casado:
        return "casado_nuevo" if ahora_casado else "igual"
    if not ahora_casado:
        return "pierde_casado"
    if tm.normalize_dni(linea.empleado_dni) != nuevo.dni:
        return "otra_persona"
    if linea.empleado_reside != nuevo.reside:
        return "otro_recurso"
    return "igual"


def _casado_ok(m: EmpleadoMatch) -> bool:
    """Todo casado de `casar_trabajador` lleva su recurso en `reside`."""
    return m.reside is not None


# ============================ el informe ================================= #

def resumir(filas: Iterable[dict]) -> dict[str, int]:
    """Recuentos de `medir_lineas` (las congeladas, aparte)."""
    cuenta: Counter = Counter()
    lineas = congeladas = 0
    for f in filas:
        lineas += 1
        if f["recurso"] == "congelada":
            congeladas += 1
            continue
        cuenta[f"recurso_{f['recurso']}"] += 1
        cuenta[f"casado_{f['casado']}"] += 1
    return {"lineas": lineas, "congeladas": congeladas, **cuenta}


def csv_lineas(filas: Iterable[dict]) -> str:
    """El CSV por linea, separado por `;` (el BOM lo pone quien escribe)."""
    salida = [";".join(COLUMNAS_LINEA)]
    for f in filas:
        salida.append(";".join(
            "" if f[c] is None else str(f[c]) for c in COLUMNAS_LINEA))
    return "\n".join(salida) + "\n"


def informe_markdown(
    maestro: list[dict], resumen: Mapping[str, int], momento: str
) -> str:
    """El informe en Markdown: resumen de lineas y tabla por empresa."""
    md = [
        "# Medicion del casado contra recursos (F-036)",
        "",
        f"Generado: {momento}. Solo lectura; sin nombres ni DNIs.",
        "",
        "## Lineas activas",
        "",
        "| recuento | lineas |",
        "|---|---|",
    ]
    md += [f"| {clave} | {valor} |" for clave, valor in resumen.items()]
    md += [
        "",
        "## Recursos de alta hoy, por empresa",
        "",
        "| empresa | " + " | ".join(COLUMNAS_MAESTRO) + " |",
        "|---" * (len(COLUMNAS_MAESTRO) + 1) + "|",
    ]
    for fila in maestro:
        empresa = ("(sin empresa)" if fila["empresa"] is None
                   else str(fila["empresa"]))
        md.append(f"| {empresa} | "
                  + " | ".join(str(fila[c]) for c in COLUMNAS_MAESTRO)
                  + " |")
    return "\n".join(md) + "\n"
