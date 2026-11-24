# progress/equivalentes_F-083.py
"""F-083 · T6: comprobacion EJECUTABLE de los 2 supervivientes que
`progress/mutacion_F-083.md` propone como EQUIVALENTES. La aceptacion es del
humano, aceptada el 2026-11-24.

Los dos son de la familia `x is not None` -> `x` en `decidir_fin`
(`racha_ciz.py`): `ultima` (linea 189) y `sigue` (linea 196), ambos el
resultado de `ultima_posterior`. Solo se distinguen si ese resultado puede
ser un valor FALSO distinto de `None`. El script comprueba, contra el fuente
ACTUAL:

  1. que cada linea original esta una sola vez en `racha_ciz.py` (si el
     codigo cambia, la demostracion deja de valer y el script falla);
  2. DOMINIO (por el AST): `ultima_posterior` solo tiene dos `return`:
     `return None` y `return max(posteriores, ...)`, y `posteriores` es una
     lista por comprension sobre `candidatas`; es decir, devuelve `None` o
     una de las lineas candidatas (`LineaSigrid`);
  3. TIPO: `LineaSigrid` no define `__bool__` ni `__len__` en su MRO (salvo
     `object`): toda instancia es verdadera, incluso con todos los campos a
     0, "" o None;
  4. EMPIRICO: aplica cada mutante sobre una copia del fuente (en memoria,
     sin tocar el fichero) y compara `decidir_fin` original y mutado sobre
     5.000 casos al azar con bordes (`ide` 0, fecha 0, `can` None, codigo
     None o "", `tex` vacio, marca de pruebas), con listas y con
     iteradores: tienen que dar la MISMA decision.

Uso, con el python del `.venv` del repo, desde la carpeta de sv5:

    cd services/partes-transfer && python ../../progress/equivalentes_F-083.py

Sale con 0 si todo se cumple; si no, imprime el primer fallo y sale con 1.
Sin red ni BBDD. Tarda menos de un segundo.
"""
from __future__ import annotations

import ast
import dataclasses
import random
import sys
import types
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))

FICHERO = "application/services/racha_ciz.py"

#: (n, original, mutada) tal como las da `progress/mutacion_F-083.md`.
MUTANTES = [
    (1, "    if ultima is not None:\n", "    if ultima:\n"),
    (2, "    if sigue is not None:\n", "    if sigue:\n"),
]


def _falla(n: int | str, msg: str) -> None:
    print(f"FALLO superviviente #{n}: {msg}")
    sys.exit(1)


def _dominio(fuente: str) -> None:
    arbol = ast.parse(fuente)
    fn = next((f for f in arbol.body if isinstance(f, ast.FunctionDef)
               and f.name == "ultima_posterior"), None)
    if fn is None:
        _falla("1-2", "no esta `ultima_posterior`")
    retornos = [ast.unparse(r) for r in ast.walk(fn)
                if isinstance(r, ast.Return)]
    esperados = ["return None",
                 "return max(posteriores, key=lambda ls: (ls.fecha_int, ls.ide))"]
    if sorted(retornos) != sorted(esperados):
        _falla("1-2", f"`ultima_posterior` devuelve otra cosa: {retornos}")
    asignas = [n for n in ast.walk(fn) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "posteriores"
                       for t in n.targets)]
    if len(asignas) != 1 or not isinstance(asignas[0].value, ast.ListComp) \
            or ast.unparse(asignas[0].value.elt) != "ls" \
            or ast.unparse(asignas[0].value.generators[0].iter) != "candidatas":
        _falla("1-2", "`posteriores` ya no es [ls for ls in candidatas ...]")


def _tipo() -> None:
    from domain.models.registro_models import LineaSigrid
    malos = [f"{k.__name__}.{m}" for k in LineaSigrid.__mro__
             if k is not object for m in ("__bool__", "__len__")
             if m in vars(k)]
    if malos:
        _falla("1-2", f"LineaSigrid define {malos}")
    vacia = LineaSigrid(ide=0, reside=0, fecha_int=0, horide=None,
                        hora_codigo="", can=None, tot=None, synckey="")
    if not bool(vacia):
        _falla("1-2", "una LineaSigrid vacia es falsa")


def _modulo(fuente: str, nombre: str) -> types.ModuleType:
    mod = types.ModuleType(nombre)
    sys.modules[nombre] = mod  # `dataclass` busca su modulo ahi
    exec(compile(fuente, f"<{nombre}>", "exec"), mod.__dict__)
    return mod


def _empirico(n: int, original: types.ModuleType,
              mutado: types.ModuleType) -> None:
    from domain.models.registro_models import LineaSigrid, ParteSigrid
    azar = random.Random(20261124 + n)
    res, d = 77, 20261004
    partes = {900: ParteSigrid(ide=900, cod="PT26/00010", est=1),
              800: ParteSigrid(ide=800, cod="", est=3)}
    for caso in range(5000):
        marca = azar.choice([None, "", "PRUEBA-IA"])
        cands = [LineaSigrid(
            ide=azar.choice([0, 1, 2, 3, 416319]),
            reside=azar.choice([res, res, res + 1]),
            fecha_int=azar.choice([0, d - 2, d - 1, d, d + 1, d + 3]),
            horide=None,
            hora_codigo=azar.choice(["CIZ", " ciz ", "CIV", "", None]),
            can=azar.choice([None, 0, 0.0, 8.0]),
            tot=None, synckey=azar.choice([None, "", "partes:1"]),
            hmoide=azar.choice([None, 0, 900, 800]),
            enlazada=azar.random() < 0.2,
            tex=azar.choice([None, "", "PRUEBA-IA x"]))
            for _ in range(azar.randint(0, 5))]
        for como in (list, iter):
            args = dict(partes=partes, est_registro=1, marca_pruebas=marca)
            a = original.decidir_fin(d, res, como(cands), **args)
            b = mutado.decidir_fin(d, res, como(cands), **args)
            # Clases `DecisionFin` distintas (un modulo cada una): se
            # comparan los campos.
            if dataclasses.astuple(a) != dataclasses.astuple(b):
                _falla(n, f"caso {caso} ({como.__name__}): {a} != {b}")


def main() -> int:
    fuente = (RAIZ / FICHERO).read_text(encoding="utf-8").replace("\r\n", "\n")
    _dominio(fuente)
    _tipo()
    original = _modulo(fuente, "racha_ciz_original")
    for n, linea, mutada in MUTANTES:
        if fuente.count(linea) != 1:
            _falla(n, f"la linea original no esta una sola vez en {FICHERO}")
        mutado = _modulo(fuente.replace(linea, mutada), f"racha_ciz_m{n}")
        _empirico(n, original, mutado)
        print(f"#{n} {FICHERO}: {linea.strip()} -> {mutada.strip()}: "
              f"equivalente (None o LineaSigrid, siempre verdadera)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
