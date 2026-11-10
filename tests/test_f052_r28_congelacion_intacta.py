# tests/test_f052_r28_congelacion_intacta.py
"""Guardián de raíz de F-052 (R28): la regla de congelación no cambia.

`traer_de_sigrid` (R20) escribe horas en líneas congeladas por
`registrado`. Esa excepción vive SOLO en el método del repositorio de sv4
que aplica la sincronización (`aplicar_traer_de_sigrid`), igual que la
materialización de F-046 en sv3: la regla de congelación de sv4
(`congelacion.py::motivo_congelacion_linea`) y la de sv3
(`recurso_conciliador.py::esta_congelado`) no saben nada de sincronizar y
siguen congelando `registrado`. Complementa al guardián de F-024
(`test_f024_borrado_no_congela_gemelos.py`), que vigila que las dos reglas
digan lo mismo.

Cada regla se evalúa en un SUBPROCESO con `cwd` en su servicio (los dos
paquetes se llaman `application`). Lo demás es lectura estática del código.
Sin red ni BBDD.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SV3 = RAIZ / "services" / "partes-persistencia"
SV4 = RAIZ / "services" / "partes-front"
CONGELACION_SV4 = SV4 / "application" / "services" / "congelacion.py"
CONGELACION_SV3 = (SV3 / "application" / "services"
                   / "recurso_conciliador.py")
REPOSITORIO = SV4 / "infrastructure" / "database" / "parte_repository.py"

#: Los ficheros (fuera de los tests) que pueden nombrar el método que
#: salta la congelación: el que lo define y el orquestador que lo llama.
DUENOS_DE_TRAER = {
    "infrastructure/database/parte_repository.py",
    "application/services/sincronizar_ambito.py",
}

_SV3 = """
import json
from application.services.recurso_conciliador import esta_congelado
print(json.dumps([esta_congelado(e, a) for e in ("registrado", " Registrado ")
                  for a in (False, True)]))
"""

_SV4 = """
import json
from application.services.congelacion import motivo_congelacion_linea
print(json.dumps([motivo_congelacion_linea(doc_aprobado=a, sigrid_estado=e)
                  is not None for e in ("registrado", " Registrado ")
                  for a in (False, True)]))
"""


def _evaluar(servicio: Path, codigo: str) -> list[bool]:
    salida = subprocess.run(
        [sys.executable, "-c", codigo], cwd=servicio, capture_output=True,
        text=True, timeout=60, check=False)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout.strip().splitlines()[-1])


def _funciones(ruta: Path) -> dict[str, ast.FunctionDef]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(arbol)
            if isinstance(n, ast.FunctionDef)}


def _llama_a(funcion: ast.AST, nombre: str) -> bool:
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", None)
               == nombre for n in ast.walk(funcion))


def _asigna_horas(funcion: ast.AST) -> bool:
    return any(isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Attribute) and t.attr == "horas"
        for t in n.targets) for n in ast.walk(funcion))


def test_f052_r28_registrado_sigue_congelando_en_sv3_y_sv4() -> None:
    assert _evaluar(SV4, _SV4) == [True] * 4
    assert _evaluar(SV3, _SV3) == [True] * 4


def test_f052_r28_las_reglas_no_conocen_la_sincronizacion() -> None:
    for ruta in (CONGELACION_SV4, CONGELACION_SV3):
        texto = ruta.read_text(encoding="utf-8").lower()
        assert "sincroniz" not in texto, ruta.name
        assert "traer_de_sigrid" not in texto, ruta.name


def test_f052_r28_la_excepcion_vive_solo_en_aplicar_traer_de_sigrid() -> None:
    """De los métodos del repositorio que firman «Sincronizado con Sigrid»,
    solo `aplicar_traer_de_sigrid` cambia horas, y no pasa por la guarda
    de edición (`_exigir_reg_editable`): esa es la excepción de R20."""
    funciones = _funciones(REPOSITORIO)
    firman = {n for n, f in funciones.items()
              if _llama_a(f, "_motivo_sincronizar")}
    assert firman == {"aplicar_marcar_registrada", "aplicar_traer_de_sigrid"}
    assert {n for n in firman if _asigna_horas(funciones[n])} == {
        "aplicar_traer_de_sigrid"}
    assert not _llama_a(funciones["aplicar_traer_de_sigrid"],
                        "_exigir_reg_editable")


def test_f052_r28_solo_el_orquestador_llama_al_metodo_que_salta() -> None:
    usan = {ruta.relative_to(SV4).as_posix()
            for ruta in SV4.rglob("*.py")
            if "tests" not in ruta.relative_to(SV4).parts
            and ".venv" not in ruta.parts
            and "aplicar_traer_de_sigrid" in ruta.read_text(encoding="utf-8")}
    assert usan == DUENOS_DE_TRAER
