# tests/test_backlog_columnas_partes.py
"""Adaptación de partes en `harness/backlog.py`: columnas «Spec» y «Pendiente».

No viene de arnes-base (allí `backlog.py` y `tests/test_backlog_md.py` son
arnés puro y se pisan al actualizar). Partes las añadió antes de la 1.8.0 y se
reaplicaron sobre el tablero de la 1.10.1: «Spec» (campo `spec`) en las
columnas abiertas y «Pendiente» (campo `pendiente`) en Done, más sus líneas en
el «Detalle». Si una actualización del arnés las pisa, estos tests se ponen en
rojo: hay que volver a portarlas sobre el `backlog.py` nuevo.

Trabajan sobre un backlog sintético, nunca sobre el `features.json` real.
"""

from __future__ import annotations

from harness import backlog


def _f(fid: str, estado: str, **extra: object) -> dict:
    datos = {"id": fid, "title": f"Título {fid}", "status": estado,
             "priority": 1, "rigor": "estandar", "branch": None,
             "description": "Descripción."}
    datos.update(extra)
    return datos


def _seccion(texto: str, titulo: str) -> str:
    inicio = texto.index(f"## {titulo}\n")
    fin = texto.find("\n## ", inicio + 1)
    return texto[inicio:] if fin == -1 else texto[inicio:fin]


def _cabecera(seccion: str) -> list[str]:
    linea = next(l for l in seccion.splitlines() if l.startswith("| #"))
    return [c.strip() for c in linea.strip("|").split("|")]


def test_las_columnas_abiertas_llevan_spec() -> None:
    texto = backlog.construir({"features": [
        _f("F-001", "pending", spec="sin spec"),
        _f("F-002", "spec_ready", spec="aprobada 2026-11-01"),
        _f("F-003", "blocked", spec="en dev"),
        _f("F-004", "in_progress", spec="aprobada"),
        _f("F-005", "todo", spec="en redacción"),
        _f("F-006", "in_review", spec="aprobada"),
    ]})

    for titulo, fid, valor in (
        ("Backlog", "F-001", "sin spec"),
        ("Spec aprobada", "F-002", "aprobada 2026-11-01"),
        ("Blocked", "F-003", "en dev"),
        ("In progress", "F-004", "aprobada"),
        ("To do", "F-005", "en redacción"),
        ("Review", "F-006", "aprobada"),
    ):
        seccion = _seccion(texto, titulo)
        assert "Spec" in _cabecera(seccion), titulo
        fila = next(l for l in seccion.splitlines() if l.startswith(f"| {fid} "))
        assert f"| {valor} |" in fila, titulo
        assert "Pendiente" not in _cabecera(seccion), titulo


def test_done_lleva_pendiente_y_no_spec() -> None:
    texto = backlog.construir({"features": [
        _f("F-010", "done", spec="aprobada", pendiente="M2 en el portal"),
    ]})

    seccion = _seccion(texto, "Done")
    cabecera = _cabecera(seccion)
    assert "Pendiente" in cabecera
    assert "Spec" not in cabecera
    fila = next(l for l in seccion.splitlines() if l.startswith("| F-010 "))
    assert "| M2 en el portal |" in fila


def test_el_detalle_repite_spec_y_pendiente() -> None:
    texto = backlog.construir({"features": [
        _f("F-020", "pending", spec="sin spec"),
        _f("F-021", "done", pendiente="desplegar | verificar"),
    ]})

    detalle = texto[texto.index("## Detalle"):]
    assert "**Spec**: sin spec" in detalle
    # El texto libre se escapa como cualquier celda.
    assert "**Pendiente**: desplegar \\| verificar" in detalle


def test_sin_los_campos_las_celdas_salen_vacias_y_el_detalle_no_los_nombra() -> None:
    texto = backlog.construir({"features": [
        _f("F-030", "pending"),
        _f("F-031", "done"),
    ]})

    assert "**Spec**" not in texto
    assert "**Pendiente**" not in texto
    fila = next(l for l in _seccion(texto, "Backlog").splitlines()
                if l.startswith("| F-030 "))
    celdas = [c.strip() for c in fila.strip("|").split("|")]
    indice = _cabecera(_seccion(texto, "Backlog")).index("Spec")
    assert celdas[indice] == ""
