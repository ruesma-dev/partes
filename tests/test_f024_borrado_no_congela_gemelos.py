# tests/test_f024_borrado_no_congela_gemelos.py
"""Guardian de raiz de F-024 (R13): sv3 y sv4 dicen lo mismo de cada estado.

La congelacion vive en dos reglas que deben coincidir: la de sv4
(`application/services/congelacion.py::motivo_congelacion_linea`, la que
pinta el candado y rechaza la edicion) y la de sv3
(`application/services/recurso_conciliador.py::esta_congelado`, la que
decide si el recalculo de la ingesta puede tocar una linea). F-024 anade
`borrado_sigrid`, que NO congela: si sv3 lo congelase, la reconciliacion de
recursos de F-023 no podria corregir el recurso de las lineas que
Administracion borro en Sigrid antes de reaprobarlas (DA10).

Los dos paquetes se llaman `application`, asi que cada regla se evalua en
un SUBPROCESO con `cwd` en su servicio: importarlas en el mismo proceso
mezclaria los modulos. Sin red ni BBDD.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

#: Raiz del repositorio: este fichero es `<raiz>/tests/test_f024_...py`.
RAIZ = Path(__file__).resolve().parents[1]
SV3 = RAIZ / "services" / "partes-persistencia"
SV4 = RAIZ / "services" / "partes-front"

#: Estados de `sigrid_estado` que se comparan (con un parte sin aprobar).
ESTADOS = [None, "", "encolado", "registrado", "omitido", "error",
           "conflicto", "borrado_sigrid", " Borrado_Sigrid ", " Registrado "]

_SV3 = """
import json, sys
from application.services.recurso_conciliador import esta_congelado
estados = json.loads(sys.argv[1])
print(json.dumps([esta_congelado(e, False) for e in estados]))
"""

_SV4 = """
import json, sys
from application.services.congelacion import motivo_congelacion_linea
estados = json.loads(sys.argv[1])
print(json.dumps([motivo_congelacion_linea(doc_aprobado=False,
                                           sigrid_estado=e) is not None
                  for e in estados]))
"""


def _evaluar(servicio: Path, codigo: str) -> list[bool]:
    salida = subprocess.run(
        [sys.executable, "-c", codigo, json.dumps(ESTADOS)],
        cwd=servicio, capture_output=True, text=True, timeout=60,
        check=False)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def congelados() -> dict[str, dict]:
    return {
        "sv3": dict(zip(map(repr, ESTADOS), _evaluar(SV3, _SV3))),
        "sv4": dict(zip(map(repr, ESTADOS), _evaluar(SV4, _SV4))),
    }


def test_f024_r13_borrado_sigrid_no_congela_en_sv3_ni_en_sv4(congelados) -> None:
    for servicio in ("sv3", "sv4"):
        assert congelados[servicio][repr("borrado_sigrid")] is False, servicio
        assert congelados[servicio][repr(" Borrado_Sigrid ")] is False, servicio


def test_f024_r13_sv3_y_sv4_coinciden_en_todos_los_estados(congelados) -> None:
    assert congelados["sv3"] == congelados["sv4"]


def test_f024_r13_la_tabla_no_es_trivial(congelados) -> None:
    """Si las dos reglas devolvieran siempre lo mismo (todo libre o todo
    congelado), coincidirian sin decir nada."""
    assert congelados["sv4"][repr("registrado")] is True
    assert congelados["sv4"][repr("encolado")] is True
    assert congelados["sv4"][repr(None)] is False
