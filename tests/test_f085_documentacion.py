# tests/test_f085_documentacion.py
"""F-085 · R33: la documentación del código de incidencia que convierte la
línea (parte A) y del inicio de la racha que se recoloca (parte B).

- `docs/ARCHITECTURE.md`, semántica 3: `es_codigo_incidencia`, la
  conversión, `MOTIVO_CODIGO_INCIDENCIA` y lo manual en sv3.
- `docs/referencia/partes-proyecto.md`: §3.5 y §4.4.

`azure-apps/partes.md` va en un commit aparte de otro repositorio: no se
comprueba aquí.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _texto(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8")


def _semantica(n: int) -> str:
    texto = _texto("docs/ARCHITECTURE.md")
    m = re.search(rf"^{n}\. \*\*", texto, re.MULTILINE)
    assert m, f"falta la semántica {n}"
    fin = re.search(rf"^{n + 1}\. \*\*", texto[m.end():], re.MULTILINE)
    return texto[m.start():m.end() + fin.start()]


def test_f085_r33_arquitectura_semantica_3_parte_a() -> None:
    seccion = _semantica(3)
    for palabra in ("F-085", "es_codigo_incidencia", "es_codigo_fin",
                    "conversion_clase.py", "registro_clase",
                    "codigo_incidencia", "MOTIVO_CODIGO_INCIDENCIA",
                    "hora_match_method", "hora_manual_respetada"):
        assert palabra in seccion, palabra


def test_f085_r33_referencia_parte_a() -> None:
    texto = _texto("docs/referencia/partes-proyecto.md")
    s35 = texto[texto.index("### 3.5"):texto.index("### 4.1")]
    assert "F-085" in s35 and "vuelve a" in s35
    s44 = texto[texto.index("### 4.4"):texto.index("### 4.5")]
    assert "Elegir el código de la incidencia en el portal (F-085)" in s44
