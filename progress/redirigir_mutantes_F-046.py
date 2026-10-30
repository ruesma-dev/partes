# progress/redirigir_mutantes_F-046.py
"""F-046 · re-evaluacion DIRIGIDA de mutantes de la campana (evidencia del
informe `progress/mutacion_F-046.md`): los que quedaron en `timeout` y, con
los tests nuevos, los supervivientes.

Con 6 workers la suite completa de sv4 tarda ~860 s por ejecucion (linea
base medida por la propia campana) y los tests de F-046 van casi al final:
un mutante que solo matan esos tests puede pasar del timeout de 1300 s por
pura contencion, sin colgarse. Este script lo comprueba mutante a mutante:

  1. extrae `git archive <sha>` del servicio a un directorio temporal
     (nunca toca el arbol real);
  2. regenera los mutantes de esa linea con `harness.mutacion` y elige el
     que tiene EXACTAMENTE la descripcion del log (fichero, linea, operador,
     texto original -> mutado);
  3. aplica el mutante y ejecuta los tests `test_f046_*` de ese servicio
     (sin `-x`, para contar los fallos), y deshace;
  4. imprime una fila por mutante: descripcion, fallos y veredicto.

Uso (desde la raiz del repositorio):
    python progress/redirigir_mutantes_F-046.py <log> [sha] [veredicto] [arbol]
`veredicto`: `timeout` (defecto) o `superviviente`. Con `arbol`, los
`tests/` del servicio se toman del arbol de trabajo (tests nuevos aun sin
commitear) y el codigo de produccion del `sha`.
Sale con 1 si algun mutante NO muere con los tests dirigidos.
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from harness.mutacion import aplicar_mutante, generar_mutantes

PATRON = (r"^\[\d+/\d+\]\s+{veredicto}\s+(?P<desc>(?P<fichero>[^:]+):"
          r"(?P<linea>\d+) .*)$")


def _servicio(fichero: str) -> str:
    partes = fichero.split("/")
    return "/".join(partes[:2])


def _extraer(sha: str, servicio: str, destino: Path) -> None:
    datos = subprocess.run(["git", "archive", sha, servicio], cwd=RAIZ,
                           capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(datos)) as tar:
        tar.extractall(destino, filter="data")


def _evaluar(raiz: Path, servicio: str, fichero: str, linea: int,
             desc: str) -> tuple[int, int]:
    ruta = raiz / fichero
    fuente = ruta.read_text(encoding="utf-8")
    candidatos = [m for m in generar_mutantes(fuente, {linea}, fichero)
                  if m.descripcion() == desc]
    if len(candidatos) != 1:
        raise SystemExit(f"no se encuentra el mutante: {desc}")
    ruta.write_text(aplicar_mutante(fuente, candidatos[0]), encoding="utf-8")
    try:
        tests = sorted(str(p.relative_to(raiz / servicio))
                       for p in (raiz / servicio / "tests").glob(
                           "test_f046_*.py"))
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p",
                 "no:cacheprovider", *tests], cwd=raiz / servicio,
                capture_output=True, text=True, timeout=900, check=False)
        except subprocess.TimeoutExpired:
            return (-1, 0)          # colgado: lo cuenta `main`
        m = re.search(r"(\d+) failed", r.stdout)
        p = re.search(r"(\d+) passed", r.stdout)
        return (int(m.group(1)) if m else 0, int(p.group(1)) if p else 0)
    finally:
        ruta.write_text(fuente, encoding="utf-8")


def main() -> int:
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    sha = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    veredicto = sys.argv[3] if len(sys.argv) > 3 else "timeout"
    arbol = len(sys.argv) > 4 and sys.argv[4] == "arbol"
    patron = re.compile(PATRON.format(veredicto=veredicto))
    filas = [m.groupdict() for l in log.splitlines()
             if (m := patron.match(l.strip()))]
    vivos = 0
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        extraidos: set[str] = set()
        for f in filas:
            servicio = _servicio(f["fichero"])
            if servicio not in extraidos:
                _extraer(sha, servicio, raiz)
                if arbol:
                    shutil.copytree(RAIZ / servicio / "tests",
                                    raiz / servicio / "tests",
                                    dirs_exist_ok=True)
                extraidos.add(servicio)
            fallos, pasan = _evaluar(raiz, servicio, f["fichero"],
                                     int(f["linea"]), f["desc"])
            resultado = ("COLGADO (>900 s)" if fallos < 0
                         else "MUERTO" if fallos else "VIVO")
            vivos += fallos == 0
            print(f"| {f['desc']} | {fallos} fallos, {pasan} pasan | "
                  f"{resultado} |", flush=True)
    print(f"{len(filas)} mutantes ({veredicto}) re-evaluados; vivos: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    raise SystemExit(main())
