# tests/test_f072_equivalencia_porcentajes.py
"""Equivalencia con porcentajes de las reglas P5 y VAR (F-072, R10, DA4).

partes reimplementa en su gemelo `obras_agrupadas.py` el casado de postventa
(`#regla-p5`, F-025) y el universo VAR (`#regla-var`, F-039) de
`porcentajes/services/dedicacion-transfer`, porque no hay canal entre los dos
proyectos (design §0). Este test los ata:

1. La tabla de casos de los tests de F-025 y F-039 de porcentajes da lo
   esperado en partes (siempre).
2. Con el repo `porcentajes` al lado de este, la MISMA tabla pasada por su
   `resolver_postventa` y su `es_partida_var`, en un subproceso (sus paquetes
   se llaman igual, `application`), da lo mismo. Sin el repo, se salta con
   motivo; con él, un fallo de importación es rojo, nunca un skip.

Diferencia conocida (design §2): con dos exactas, porcentajes toma la
primera por código crudo y partes la de menor `ide`. Ningún caso real la
tiene, y esta tabla no la incluye a propósito. El repo `porcentajes` solo se
lee.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[1]
GEMELO = RAIZ / "services/partes-persistencia/application/services/obras_agrupadas.py"
PORCENTAJES = RAIZ.parent / "porcentajes" / "services" / "dedicacion-transfer"

#: Casos P5 (F-025 R10-R11): (id, hojas [(cod, tipdes)], código de la obra,
#: código esperado o None). Hojas colgando de `CD`, ides 1, 2…
CASOS_P5 = (
    ("exacto_gana", [("0578B", 0), ("0578", 0)], "0578", "0578"),
    ("sufijo_letra", [("0578B", 0), ("0656", 0)], "0578", "0578B"),
    ("guion", [("0654-B", 0)], "0654", "0654-B"),
    ("mas_corto", [("0578AB", 0), ("0578C", 0)], "0578", "0578C"),
    ("menor_normalizado", [("0578-C", 0), ("0578B", 0)], "0578", "0578B"),
    ("orden_inverso", [("0578B", 0), ("0578C", 0)], "0578", "0578B"),
    ("normalizado", [("0578B", 0)], " 0578 ", "0578B"),
    ("minusculas", [("CPB", 0)], "cp", "CPB"),
    ("ceros", [("656", 0)], "0656", None),
    ("punto", [("CP.1", 0)], "CP", None),
    ("obra_capitulo_hija", [("0678.MO", 0)], "0678", None),
    ("digito", [("06561", 0)], "0656", None),
    ("letra_digito", [("0578B1", 0)], "0578", None),
    ("letra_punto", [("0578 B.", 0)], "0578", None),
    ("de_baja", [("0578", 1), ("0578B", 0)], "0578", "0578B"),
    ("todas_de_baja", [("0578", 1)], "0578", None),
    ("sin_codigo", [("0578B", 0)], None, None),
    ("vacio", [("0578B", 0)], "", None),
    ("descripcion_no", [("CI.7.5", 0)], "OT", None),
)

#: Casos VAR (F-039 R2): (cod, es_hoja, activa) con umbral 29.
CASOS_VAR = (
    ("29", True, True), ("30", True, True), ("100", True, True),
    ("029", True, True), ("29.1", True, True), ("29A", True, True),
    (" 29 ", True, True), ("28", True, True), ("05", True, True),
    ("CI.1.1", True, True), ("A29", True, True), (None, True, True),
    ("31", False, True), ("32", True, False), ("0", True, True),
)
ESPERADO_VAR = (True, True, True, True, True, True, True, False, False,
                False, False, False, False, False, False)
DESDE = 29


def _filas(hojas):
    filas = [{"ide": 100, "padide": 0, "pos": 0, "tip": 0, "cod": "CD",
              "res": "COSTES DIRECTOS", "tex": None, "tipdes": 0,
              "cosindide": None, "unimed": None}]
    filas += [{"ide": i, "padide": 100, "pos": i, "tip": 1, "cod": c,
               "res": f"PARTIDA {c}", "tex": None, "tipdes": t,
               "cosindide": None, "unimed": None}
              for i, (c, t) in enumerate(hojas, start=1)]
    return filas


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _partes() -> tuple[list, list]:
    """Resultados de partes: (código casado por caso P5, es_var por caso).

    Las hojas se construyen como las da el árbol de partidas de partes: el
    capítulo `CD` no es hoja y cada fila con `tipdes != 0` está de baja."""
    gemelo = _cargar(GEMELO, "obras_agrupadas_equivalencia")
    p5 = []
    for _id, hojas, obra, _esp in CASOS_P5:
        nodos = [SimpleNamespace(ide=f["ide"], cod=f["cod"],
                                 es_hoja=f["ide"] != 100,
                                 activa=f["tipdes"] == 0)
                 for f in _filas(hojas)]
        nodo = gemelo.casar_postventa(nodos, obra)
        p5.append(None if nodo is None else nodo.cod)
    var = [gemelo.es_partida_var(
        SimpleNamespace(ide=1, cod=c, es_hoja=h, activa=a), DESDE)
        for c, h, a in CASOS_VAR]
    return p5, var


#: Script del subproceso: corre DENTRO de porcentajes y devuelve JSON.
_SCRIPT = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from application.services.partida_catalog import PartidaNodo
from application.services.partida_resolver import (construir_catalogo,
                                                   resolver_postventa)
from application.services.universo_var import es_partida_var
datos = json.loads(sys.stdin.read())
p5 = []
for filas, obra in datos["p5"]:
    nodo = resolver_postventa(construir_catalogo(filas), obra, None)
    p5.append(None if nodo is None else nodo.cod)
var = [es_partida_var(PartidaNodo(ide=1, padide=0, cod=c, res=None, tex=None,
                                  es_hoja=h, activa=a), datos["desde"])
       for c, h, a in datos["var"]]
print(json.dumps({"p5": p5, "var": var}))
"""


def test_f072_r10_la_tabla_da_lo_esperado_en_partes():
    p5, var = _partes()
    assert p5 == [c[3] for c in CASOS_P5]
    assert tuple(var) == ESPERADO_VAR


def test_f072_r10_porcentajes_da_lo_mismo_que_partes():
    if not PORCENTAJES.is_dir():
        pytest.skip(f"sin el repo porcentajes al lado ({PORCENTAJES}): no "
                    "se puede comparar")
    entrada = json.dumps({
        "p5": [[_filas(h), o] for _i, h, o, _e in CASOS_P5],
        "var": [list(c) for c in CASOS_VAR], "desde": DESDE})
    r = subprocess.run([sys.executable, "-I", "-c", _SCRIPT, str(PORCENTAJES)],
                       input=entrada, capture_output=True, text=True,
                       cwd=str(PORCENTAJES), timeout=120, check=False)
    # Con el repo presente, cualquier fallo (importación incluida) es ROJO.
    assert r.returncode == 0, f"porcentajes no se pudo ejecutar:\n{r.stderr}"
    suyo = json.loads(r.stdout.strip().splitlines()[-1])
    p5, var = _partes()
    assert suyo["p5"] == p5, list(zip([c[0] for c in CASOS_P5], suyo["p5"], p5))
    assert suyo["var"] == list(var)
