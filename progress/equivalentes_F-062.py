# progress/equivalentes_F-062.py
"""F-062 · demostracion EJECUTABLE de los 3 mutantes equivalentes (RM5).

Los 3 supervivientes que `progress/mutacion_F-062.md` propone como
equivalentes. La aceptacion es del humano, pendiente. Mismo patron que
`progress/equivalentes_F-060.py`: para cada uno construye el modulo mutado
a partir del fuente ACTUAL, sustituyendo la linea original por la mutada.
Esa linea tiene que aparecer una sola vez en su AMBITO: el fichero entero o
la funcion de nivel superior indicada. Luego carga el mutado junto al
original y compara:

  sv4 (`racha_incidencia.py`):
      #1 (`f = int(l.fecha_int or 0)` de `viaja` en `racha_delante`).
      Diferencial puro: 50.000 llamadas a `racha_delante` con historicos
      al azar que incluyen fechas `None`, `0` y `1`, papelera, 1e-9 h e
      ids repetidos.
  sv5 (`registro_pipeline.py`), con `MOVER_CIZ` encendido sobre
      `SigridFake`:
      #4 (`int(a.recurso_ide or 0)` de `decidir_mismo_dia`, paso 6 bis,
      los `inicio` con CIZ hermano).
      #5 (`int(a.recurso_ide or 0)` de `decidir_fin`). Es el mismo
      mutante que el #11 de F-060, que el humano acepto el 2026-10-24
      («acepto»); F-062 solo partio la linea en dos.
      Diferencial del pipeline completo (`preflight` y `ejecutar`):
      `inicio` marcados con `ciz_mismo_dia` y `fin` con racha;
      recurso `REC`, `None`, `0` o `1` (el recurso 1 tiene horas propias);
      CIZ candidatos del recurso, del 1 o de otro, con synckey
      `partes:<i>`, `partes:<i>:ciz` o manual; partes cerrados,
      enlazadas y modo pruebas.

CONTROL de sensibilidad: cada diferencial corre tambien con el hermano
`and 0` de la misma linea, que SI cambia el comportamiento. Ese control
tiene que salir DISTINTO; si saliera igual, el diferencial seria ciego y
el script falla.

Si un equivalente difiere o un control no difiere, imprime el primer
contraejemplo y sale con 1; si no, con 0.

Uso, desde la raiz del repositorio, con el python del `.venv` del repo:

    cd services/partes-front
    python ../../progress/equivalentes_F-062.py sv4
    cd ../partes-transfer
    python ../../progress/equivalentes_F-062.py sv5

Sin red ni BBDD. Datos sinteticos. sv4 tarda ~10 s; sv5, ~30 s.
"""
from __future__ import annotations

import copy
import logging
import random
import sys
import types
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))

RI = "application/services/racha_incidencia.py"
RP = "application/pipelines/registro_pipeline.py"

_MISMO_DIA = "decidir_mismo_dia(\n                a.fecha_int, "
_FIN = "d = decidir_fin(a.fecha_int, "

#: servicio -> [(n, fichero, original, mutada, ambito, control)].
#: `ambito`: cabecera de la funcion de nivel superior que contiene la
#: linea (None = el fichero entero). `control`: la mutacion `and 0` de la
#: misma linea, que el diferencial TIENE que distinguir.
MUTANTES: dict[str, list[tuple]] = {
    "sv4": [
        (1, RI, "f = int(l.fecha_int or 0)", "f = int(l.fecha_int or 1)",
         "def racha_delante(", "f = int(l.fecha_int and 0)"),
    ],
    "sv5": [
        (4, RP, _MISMO_DIA + "int(a.recurso_ide or 0),",
         _MISMO_DIA + "int(a.recurso_ide or 1),", None,
         _MISMO_DIA + "int(a.recurso_ide and 0),"),
        (5, RP, _FIN + "int(a.recurso_ide or 0),",
         _FIN + "int(a.recurso_ide or 1),", None,
         _FIN + "int(a.recurso_ide and 0),"),
    ],
}

_n = 0


def _mutar(fichero: str, original: str, mutada: str,
           ambito: str | None) -> types.ModuleType:
    global _n
    fuente = (RAIZ / fichero).read_text(encoding="utf-8")
    if ambito is None:
        assert fuente.count(original) == 1, (fichero, original)
        mutado = fuente.replace(original, mutada)
    else:
        # La funcion de nivel superior: de su cabecera a la siguiente.
        assert fuente.count("\n" + ambito) == 1, (fichero, ambito)
        i = fuente.index("\n" + ambito)
        j = fuente.find("\ndef ", i + 1)
        j = len(fuente) if j < 0 else j
        trozo = fuente[i:j]
        assert trozo.count(original) == 1, (fichero, ambito, original)
        mutado = fuente[:i] + trozo.replace(original, mutada) + fuente[j:]
    assert mutado != fuente
    _n += 1
    nombre = f"_mutante_{_n}"
    modulo = types.ModuleType(nombre)
    sys.modules[nombre] = modulo
    # exec deliberado: el fuente es el del propio repositorio con UNA
    # sustitucion conocida, no entrada externa.
    exec(compile(mutado, nombre, "exec"), modulo.__dict__)  # noqa: S102
    return modulo


# =============================== sv4 =============================== #

_FECHAS = (None, 0, 1, 20260930, 20261001, 20261002, 20261003, 20261004,
           20261005, 20261006, 20261007, 20261031, 20261101, 20261102,
           20261130, 20261201)


def _hist(azar: random.Random, mod) -> list:
    out = []
    for _ in range(azar.randint(0, 12)):
        es_inc = azar.random() < 0.7
        out.append(mod.LineaHist(
            registro_id=azar.randint(1, 9), fecha_int=azar.choice(_FECHAS),
            es_incidencia=es_inc,
            clave=azar.choice(("V", "V", "B")) if es_inc else "",
            horas=azar.choice((0.0, 1e-9, None, 8.0, -2.0)),
            sigrid_estado=azar.choice((None, "registrado", "encolado",
                                       "omitido", "pendiente")),
            activa=azar.random() < 0.7))
    return out


def _comparar_sv4(orig, mod, casos: int = 50000) -> str | None:
    azar = random.Random(20261026)
    con_tramo = raras = 0
    for _ in range(casos):
        semilla = azar.random()
        h_o = _hist(random.Random(semilla), orig)
        h_m = _hist(random.Random(semilla), mod)
        d = azar.choice(_FECHAS[3:])
        clave = azar.choice(("V", "B"))
        a = orig.racha_delante(h_o, d, clave)
        b = mod.racha_delante(h_m, d, clave)
        if a != b:
            return f"racha_delante({h_o}, {d}, {clave}): {a} != {b}"
        con_tramo += bool(a)
        raras += bool(a) and any(l.fecha_int in (None, 0, 1) for l in h_o)
    print(f"    racha_delante: {casos} llamadas, {con_tramo} con tramo, "
          f"{raras} con tramo y alguna fecha None/0/1")
    return None


def _sv4() -> int:
    from application.services import racha_incidencia as orig
    fallos = 0
    for n, fichero, original, mutada, ambito, control in MUTANTES["sv4"]:
        error = _comparar_sv4(orig, _mutar(fichero, original, mutada, ambito))
        fallos += _informe(n, fichero, original, mutada, error)
        error = _comparar_sv4(orig, _mutar(fichero, original, control, ambito))
        fallos += _control(n, control, error)
    return fallos


# =============================== sv5 =============================== #

def _escenario(azar: random.Random):
    """Un `SigridFake` con 0-5 lineas candidatas y 1-3 lineas a aprobar."""
    from tests import test_f062_ciz_mismo_dia as t
    d = azar.randint(20261002, 20261027)
    filas = []
    for i in range(azar.randint(0, 5)):
        fec = azar.choice((d - 1, d, d + 1, d + 1, d + 2, 20260930))
        rid = azar.randint(1, 6)
        filas.append(t._fila(
            7000 + i, fec=fec,
            sk=azar.choice((f"partes:{rid}", f"partes:{rid}",
                            f"partes:{rid}:ciz", None)),
            hmoide=azar.choice((t.HMO_OCT, t.HMO_OCT, t.HMO_OCT, t.HMO_SEP,
                                0, None)),
            horide=azar.choice((t.H_CIZ, t.H_CIZ, t.H_CIZ, t.H_CIV)),
            can=azar.choice((0.0, 0.0, 0.0, None, 1.0)),
            tex=azar.choice((None, "PRUEBA-IA")),
            enlazada=azar.random() < 0.1,
            pos=azar.choice((None, 64, 192)),
            reside=azar.choice((t.REC, t.REC, t.REC, 1, 999))))
    partes = [t._parte(t.HMO_SEP, "PT26/00009", mes=9,
                       est=azar.choice((1, 3))),
              t._parte(t.HMO_OCT, "PT26/00010",
                       est=azar.choice((1, 1, 3)))]
    cli = t._cli(*filas, partes=partes)
    cli.horas[1] = list(cli.horas[t.REC])      # el recurso 1 es real
    lineas = []
    for j in range(azar.randint(1, 3)):
        racha = sorted(azar.sample(range(1, 7), azar.randint(0, 4)))
        rec = azar.choice((t.REC, t.REC, t.REC, None, 0, 1))
        if azar.random() < 0.6:
            linea = t._inicio(100 + j, d + j, racha, rec=rec)
        else:
            linea = t._fin(100 + j, d + j, racha, rec=rec)
        lineas.append(linea)
    if azar.random() < 0.3:
        lineas.append(t._trabajo(200, d))
    return cli, lineas, azar.random() < 0.2


def _correr(mod_pipe, cli, lineas, pruebas: bool) -> str:
    from tests import test_f062_ciz_mismo_dia as t
    pipe = mod_pipe.RegistroPipeline(
        cliente=cli, settings=t._st(mover=True, pruebas=pruebas), lock=None)
    salida = []
    for fase in ("preflight", "ejecutar"):
        try:
            r = getattr(pipe, fase)(obra=t._obra(),
                                    lineas=copy.deepcopy(lineas))
            salida.append(repr(r))
        except Exception as exc:  # noqa: BLE001 - se compara tal cual
            salida.append(f"{type(exc).__name__}: {exc}")
    salida.append(repr(sorted(cli.lineas, key=lambda f: f["ide"])))
    return "\n".join(salida)


def _comparar_pipeline(orig, mod, casos: int = 4000,
                       contar: bool = True) -> str | None:
    azar = random.Random(20261026)
    hermanos = sin_recurso = 0
    for _ in range(casos):
        cli, lineas, pruebas = _escenario(azar)
        a = _correr(orig, copy.deepcopy(cli), lineas, pruebas)
        b = _correr(mod, copy.deepcopy(cli), lineas, pruebas)
        if a != b:
            return f"{lineas}\n--- original ---\n{a}\n--- mutante ---\n{b}"
        hermanos += "'ciz_hmores_ide'" in a
        sin_recurso += any(not l.recurso_ide for l in lineas)
    if contar:
        print(f"    pipeline: {casos} escenarios, {hermanos} con un CIZ "
              f"hermano escrito, {sin_recurso} con alguna linea sin recurso "
              f"o con recurso 0")
    return None


def _sv5() -> int:
    from application.pipelines import registro_pipeline as orig
    logging.disable(logging.CRITICAL)     # los WARNING/INFO del pipeline
    fallos = 0
    for n, fichero, original, mutada, ambito, control in MUTANTES["sv5"]:
        error = _comparar_pipeline(orig, _mutar(fichero, original, mutada,
                                                ambito))
        fallos += _informe(n, fichero, original, mutada, error)
        error = _comparar_pipeline(orig, _mutar(fichero, original, control,
                                                ambito), contar=False)
        fallos += _control(n, control, error)
    return fallos


def _informe(n, fichero, original, mutada, error) -> int:
    estado = "EQUIVALENTE" if error is None else "DISTINTO"
    print(f"{estado}: #{n} {fichero}: {' '.join(original.split())} -> "
          f"{' '.join(mutada.split())}")
    if error is not None:
        print(f"    contraejemplo: {error[:1500]}")
    return 0 if error is None else 1


def _control(n, control, error) -> int:
    """El control `and 0` TIENE que distinguirse (diferencial no ciego)."""
    if error is None:
        print(f"    CONTROL CIEGO: #{n} {' '.join(control.split())} no se "
              f"distingue: el diferencial no demuestra nada")
        return 1
    print(f"    control #{n} ({' '.join(control.split())}): distinto, "
          f"como debe")
    return 0


def main() -> int:
    servicio = sys.argv[1] if len(sys.argv) > 1 else ""
    if servicio not in MUTANTES:
        print("uso: equivalentes_F-062.py sv4|sv5 (desde la carpeta del "
              "servicio)")
        return 2
    fallos = _sv4() if servicio == "sv4" else _sv5()
    print(f"{len(MUTANTES[servicio])} mutantes, {fallos} distintos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
