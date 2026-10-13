# tests/test_f043_portal_fecha.py
"""F-043 · el portal: rotulo, confirmacion y parte «en espera».

- R1: «Fecha del parte» en las cabeceras y en cada `.fecha-edit`.
- R5-R11: confirmar el cambio de fecha con el alcance del parte.
- R18-R26, R40: espera de un solo parte, aviso no modal, sondeo y
  «Actualizar» que conserva la vista; nada recarga solo.

Las funciones puras de `static/app.js` se EJECUTAN con node (se saltan
sin node); el cableado se lee del fuente. Sin red. Datos sinteticos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_SV4 = Path(__file__).resolve().parents[1]
PLANTILLAS = RAIZ_SV4 / "templates"
APP_JS = RAIZ_SV4 / "static" / "app.js"
STYLES = RAIZ_SV4 / "static" / "styles.css"

TITULO = "Es la fecha del PARTE: cambiarla mueve todas sus líneas y trabajadores"


def _fuente(nombre: str) -> str:
    return (PLANTILLAS / nombre).read_text(encoding="utf-8")


def _inputs_fecha(fuente: str) -> list[str]:
    """Cada etiqueta `<input ...>` con la clase `fecha-edit`."""
    return [m.group(0) for m in re.finditer(r"<input\b[^>]*>", fuente,
                                            re.DOTALL)
            if re.search(r'class="[^"]*\bfecha-edit\b', m.group(0))]


# ================================ R1 =================================== #

@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f043_r1_la_cabecera_dice_fecha_del_parte(plantilla) -> None:
    fuente = _fuente(plantilla)
    assert f'<th title="{TITULO}">Fecha del parte</th>' in fuente
    assert "<th>Fecha</th>" not in fuente


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html",
                                       "parte_detail.html"])
def test_f043_r1_cada_fecha_edit_lo_explica(plantilla) -> None:
    inputs = _inputs_fecha(_fuente(plantilla))
    assert len(inputs) == 1, inputs
    for etiqueta in inputs:
        assert f'title="{TITULO}"' in etiqueta
        assert 'aria-label="Fecha del parte"' in etiqueta


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html",
                                       "parte_detail.html"])
def test_f043_r1_r37_las_plantillas_parsean(plantilla) -> None:
    from jinja2 import Environment, FileSystemLoader

    entorno = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    entorno.parse(entorno.loader.get_source(entorno, plantilla)[0])
