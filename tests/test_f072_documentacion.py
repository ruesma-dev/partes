# tests/test_f072_documentacion.py
"""F-072 · R40: la documentación de las obras agrupadas.

- `docs/ARCHITECTURE.md` gana la semántica 24 «Obras agrupadas (F-072)».
- La lista cerrada de duplicaciones de `CLAUDE.md` incluye el gemelo
  `obras_agrupadas.py` (DA4) y el test que lo vigila.
- `harness/servicios.json` hace depender sv2, sv4 y sv5 de la copia de sv3,
  para que la caché de suites no salte un servicio cuando cambia el gemelo.
- `infra/README_partes.md` documenta las variables.

`azure-apps/partes.md` va en un commit aparte de otro repositorio: no se
comprueba aquí.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GEMELO = "application/services/obras_agrupadas.py"
VARIABLES = ("POSTVENTA_OBRA_COD", "POSTVENTA_ALIAS", "VAR_OBRA_COD",
             "VAR_ALIAS", "VAR_PARTIDA_DESDE")


def _texto(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8")


def test_f072_r40_arquitectura_semantica_24():
    texto = _texto("docs/ARCHITECTURE.md")
    m = re.search(r"^24\. \*\*Obras agrupadas \(F-072", texto, re.MULTILINE)
    assert m, "falta la semántica 24 «Obras agrupadas (F-072)»"
    seccion = texto[m.start():texto.index("\n## ", m.start())]
    for palabra in ("agr-", "partida_match_method", "leer_forma",
                    "partida_agrupada", "por_partida", GEMELO):
        assert palabra in seccion, palabra


def test_f072_r40_lista_cerrada_con_el_gemelo():
    texto = _texto("CLAUDE.md")
    inicio = texto.index("LÍMITE DE SERVICIO")
    fin = texto.index("Solo crece con una decisión así", inicio)
    lista = texto[inicio:fin]
    assert GEMELO in lista
    assert "test_f072_obras_agrupadas_gemelos.py" in lista
    assert "F-072" in lista and "DA4" in lista


def test_f072_servicios_dependen_del_gemelo():
    servicios = {s["nombre"]: s for s in json.loads(
        _texto("harness/servicios.json"))["servicios"]}
    fuente = f"services/partes-persistencia/{GEMELO}"
    for nombre in ("sv2-extraccion", "sv4-front", "sv5-transfer"):
        assert fuente in servicios[nombre].get("depende_de", []), nombre


def test_f072_variables_en_la_guia_de_infra():
    texto = _texto("infra/README_partes.md")
    assert "F-072" in texto
    for variable in VARIABLES:
        assert variable in texto, variable
