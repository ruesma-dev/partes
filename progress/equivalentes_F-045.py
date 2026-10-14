# progress/equivalentes_F-045.py
"""F-045 · demostracion EJECUTABLE de los mutantes equivalentes (RM5).

Para cada superviviente de `progress/mutacion_F-045.md` construye el modulo
mutado a partir del fuente (sustituyendo la linea original por la mutada),
lo carga junto al original y compara sus salidas sobre un corpus de dias
con horas de parte reales: medias, cuartos y centesimas de 2 decimales,
jornadas 0/6/7,75/8/8,4/9, lineas congeladas, extras explicitas, parejas
base/extra automatica y extras automaticas reclasificadas. Si alguna salida
difiere, el mutante NO es equivalente y se imprime el primer contraejemplo.

Uso, desde la raiz del repositorio:

    cd services/partes-persistencia
    <python del .venv del repo> ../../progress/equivalentes_F-045.py

Sale con 0 si los 8 son equivalentes en el corpus y con 1 si alguno no lo
es (imprime el contraejemplo). Tarda unos 45 s.

Sin red ni BBDD. Datos sinteticos.
"""
from __future__ import annotations

import logging
import random
import sys
import types
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))

from application.services import recurso_conciliador as rc_orig
from application.services import reparto_ponderado as rp_orig
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

RP = "application/services/reparto_ponderado.py"
RC = "application/services/recurso_conciliador.py"

#: (fichero, linea original, linea mutada) de cada superviviente.
MUTANTES: list[tuple[str, str, str]] = [
    # La guarda del dia NO laborable (la seguida de `jornada = 0.0`).
    (RC, ("                if total_ord <= 1e-9:\n                    continue\n"
          "                jornada = 0.0"),
         ("                if total_ord < 1e-9:\n                    continue\n"
          "                jornada = 0.0")),
    (RP, "round(valor / paso)) <= _TOLERANCIA",
         "round(valor / paso)) < _TOLERANCIA"),
    (RP, "return round(unidades * paso, 6)", "return round(unidades * paso, 7)"),
    (RP, "if p.peso > 0]", "if p.peso >= 0]"),
    (RP, "if abs(cuota - ln.horas) > _EPS:", "if abs(cuota - ln.horas) >= _EPS:"),
    (RP, "(abs(residuo) > _EPS and not por_obra)",
         "(abs(residuo) >= _EPS and not por_obra)"),
    (RP, "if residuo < -_EPS or", "if residuo <= -_EPS or"),
    (RP, "if ln.fija and abs(despues_ln - ln.horas) > _EPS:",
         "if ln.fija and abs(despues_ln - ln.horas) >= _EPS:"),
]

_n = 0


def _mutar(fichero: str, original: str, mutada: str) -> types.ModuleType:
    global _n
    fuente = (RAIZ / fichero).read_text(encoding="utf-8")
    assert fuente.count(original) == 1, (fichero, original)
    _n += 1
    nombre = f"_mutante_{_n}"
    modulo = types.ModuleType(nombre)
    sys.modules[nombre] = modulo
    # exec deliberado: el fuente es el del propio repositorio con UNA
    # sustitucion conocida, no entrada externa.
    exec(compile(fuente.replace(original, mutada), nombre, "exec"),  # noqa: S102
         modulo.__dict__)
    return modulo


_REJILLAS = ([k / 2 for k in range(25)], [k / 4 for k in range(49)],
             [round(k / 100, 2) for k in range(1201)])
_JORNADAS = (0.0, 6.0, 7.75, 8.0, 8.4, 9.0)


def _dia(azar: random.Random, mod) -> list:
    rejilla = azar.choice(_REJILLAS)
    lineas = []
    for rid in range(1, azar.randint(1, 6) + 1):
        tipo = "ordinaria" if azar.random() < 0.75 else "extra"
        horas = azar.choice(rejilla)
        if tipo == "extra" and azar.random() < 0.2:
            horas = -horas
        fija = azar.random() < 0.3
        lineas.append(mod.LineaDia(
            registro_id=rid, obra_ide=azar.choice((10, 20, 30, None)),
            tipo=tipo, horas=horas,
            horas_orig=(azar.choice(rejilla)
                        if tipo == "ordinaria" and fija
                        and azar.random() < 0.5 else None),
            fija=fija, extra_auto=tipo == "extra" and azar.random() < 0.4,
            base_id=azar.randint(1, 6) if azar.random() < 0.5 else None))
    return lineas


def _comparar_reparto(mod, casos: int = 20000) -> str | None:
    azar = random.Random(20261014)
    for _ in range(casos):
        jornada = azar.choice(_JORNADAS)
        dia_o = _dia(random.Random(semilla := azar.random()), rp_orig)
        dia_m = _dia(random.Random(semilla), mod)
        for f in ("repartir_dia", "diferencias_ideal"):
            a = getattr(rp_orig, f)(dia_o, jornada)
            b = getattr(mod, f)(dia_m, jornada)
            if repr(a) != repr(b):
                return f"{f}({dia_o}, {jornada}): {a} != {b}"
        pesos = [p.horas for p in dia_o]
        if rp_orig.elegir_paso(jornada, pesos) != mod.elegir_paso(
                jornada, pesos):
            return f"elegir_paso({jornada}, {pesos})"
    return None


def _splits(mod, regs, festivos) -> tuple:
    conciliador = mod.RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set(festivos)),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0)
    registro_log: list[str] = []

    class _H(logging.Handler):
        def emit(self, r):
            registro_log.append(r.getMessage())

    h = _H()
    mod.logger.addHandler(h)
    mod.logger.setLevel(logging.INFO)
    try:
        splits = conciliador._reclasificar_extras_jornada(
            regs, {r["registro_id"]: 501 for r in regs},
            indice_reshor(501, candef=azar_candef))
    finally:
        mod.logger.removeHandler(h)
    return splits, registro_log


azar_candef = 8.0


def _comparar_conciliador(mod, casos: int = 3000) -> str | None:
    global azar_candef
    azar = random.Random(20261015)
    for _ in range(casos):
        rejilla = azar.choice(_REJILLAS)
        azar_candef = azar.choice((8.0, 9.0))
        fecha = azar.choice((20260316, 20260319, 20260320, 20260321))
        regs = [registro(
            i, fecha_int=fecha, horas=azar.choice(rejilla),
            tipo=azar.choice(("normal", "normal", "extra", "Vacaciones(V)")),
            obra_ide=azar.choice((10, 20)),
            sigrid_estado="registrado" if azar.random() < 0.2 else None)
            for i in range(1, azar.randint(1, 4) + 1)]
        # El sabado 21 nunca es laborable; el viernes 20, festivo a veces.
        festivos = {"2026-03-21"} | (
            {"2026-03-20"} if azar.random() < 0.3 else set())
        a = _splits(rc_orig, regs, festivos)
        b = _splits(mod, regs, festivos)
        if a != b:
            return f"{regs}: {a} != {b}"
    return None


def main() -> int:
    fallos = 0
    for fichero, original, mutada in MUTANTES:
        mod = _mutar(fichero, original, mutada)
        error = (_comparar_reparto(mod) if fichero == RP
                 else _comparar_conciliador(mod))
        estado = "EQUIVALENTE" if error is None else "DISTINTO"
        print(f"{estado}: {fichero}: {original.strip()} -> {mutada.strip()}")
        if error is not None:
            fallos += 1
            print(f"    contraejemplo: {error[:400]}")
    print(f"{len(MUTANTES)} mutantes, {fallos} distintos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
