# progress/equivalentes_F-061.py
"""F-061 · demostración EJECUTABLE del mutante equivalente #1.

Superviviente #1 de `progress/mutacion_F-061.md`:
`parte_repository.py`, `_borrar_retirados_sin_filas`, `.limit(1)` →
`.limit(2)` en la consulta «¿le queda alguna fila?». Se lee con `.first()`,
que devuelve la primera fila o None: con `LIMIT 1` o `LIMIT 2` es None si y
solo si el parte no tiene ninguna fila. Cambia como mucho una fila leída de
más, no la decisión. La aceptación es del humano: está pendiente.

El script construye el módulo mutado a partir del fuente ACTUAL, sustituyendo
`.limit(1)` por `.limit(2)` SOLO dentro de `_borrar_retirados_sin_filas`
(tiene que aparecer una vez en ese ámbito), y compara original y mutado
sobre SQLite en memoria: partes retirados con 0, 1, 2 y 3 filas (vivas o en
la papelera), retirados con otra marca, activos, desactivados por sv3 y de
la papelera de partes, barriendo todos (`ids=None`) y por ids sueltos.

CONTROL de sensibilidad: el mismo diferencial con `.limit(0)` (que hace
`.first()` siempre None) TIENE que salir distinto; si saliera igual, el
diferencial sería ciego y el script falla.

Uso, desde la raíz del repositorio (o del worktree):
    python progress/equivalentes_F-061.py
Sale con 0 si el mutante es equivalente y el control lo distingue; si no,
imprime el contraejemplo y sale con 1.
"""
from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

RAIZ_SV4 = Path(__file__).resolve().parents[1] / "services" / "partes-front"
sys.path.insert(0, str(RAIZ_SV4))
sys.path.insert(0, str(RAIZ_SV4 / "tests"))

from dobles import FabricaSesionSqlite, sembrar_parte  # noqa: E402
from infrastructure.database import parte_repository as original  # noqa: E402
from infrastructure.database.orm_models import ParteDocumentOrm  # noqa: E402
from sqlalchemy import select  # noqa: E402

FUENTE = Path(original.__file__).read_text(encoding="utf-8")
INICIO = "    def _borrar_retirados_sin_filas("
FIN = "    def hard_delete_registro("


def _mutado(sustituto: str, nombre: str):
    i, j = FUENTE.index(INICIO), FUENTE.index(FIN)
    ambito = FUENTE[i:j]
    assert ambito.count(".limit(1)") == 1, "la línea no es única en su ámbito"
    fuente = FUENTE[:i] + ambito.replace(".limit(1)", sustituto) + FUENTE[j:]
    spec = importlib.util.spec_from_loader(nombre, loader=None)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo          # `@dataclass` lo busca ahí
    exec(compile(fuente, original.__file__, "exec"), modulo.__dict__)
    return modulo


# (nº de filas, cuántas en la papelera, estado del parte)
ESTADOS = ("retirado", "retirado_otro", "activo", "sv3", "papelera")


def _escenario(combo) -> FabricaSesionSqlite:
    fabrica = FabricaSesionSqlite()
    for k, (filas, borradas, estado) in enumerate(combo):
        did = f"d{k}"
        lineas = [{"borrada": n < borradas} for n in range(filas)]
        sembrar_parte(fabrica, lineas, document_id=did)
        with fabrica.create_session() as s:
            doc = s.get(ParteDocumentOrm, did)
            if estado == "retirado":
                doc.is_active, doc.deleted_by = False, "sin-lineas · ana"
            elif estado == "retirado_otro":
                doc.is_active, doc.deleted_by = False, "ana"
            elif estado == "sv3":
                doc.is_active, doc.deleted_by = False, None
            elif estado == "papelera":
                doc.is_active = False
                doc.deleted_at_utc = "2026-10-26T00:00:00+00:00"
            s.commit()
    return fabrica


def _resultado(modulo, combo, ids) -> tuple:
    fabrica = _escenario(combo)
    with fabrica.create_session() as s:
        n = modulo.ParteReviewRepository._borrar_retirados_sin_filas(s, ids)
        s.commit()
        quedan = sorted(s.execute(select(ParteDocumentOrm.id)).scalars())
    return n, quedan


def _casos():
    partes = [(f, b, e) for f in range(4) for b in range(f + 1)
              for e in ESTADOS]
    for combo in itertools.combinations(partes, 2):
        ids_posibles = [None, [], ["d0"], ["d1"], ["d0", "d1", "nada"]]
        for ids in ids_posibles:
            yield combo, ids


def main() -> int:
    mutado = _mutado(".limit(2)", "parte_repository_mutado")
    control = _mutado(".limit(0)", "parte_repository_control")
    casos = 0
    control_distinto = False
    for combo, ids in _casos():
        casos += 1
        base = _resultado(original, combo, ids)
        mut = _resultado(mutado, combo, ids)
        if mut != base:
            print(f"DIFIERE el mutante: {combo} ids={ids}: {base} != {mut}")
            return 1
        if not control_distinto and _resultado(control, combo, ids) != base:
            control_distinto = True
    if not control_distinto:
        print("CONTROL CIEGO: .limit(0) no cambia nada; el diferencial no vale")
        return 1
    print(f"#1 equivalente en {casos} casos; el control .limit(0) difiere.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
