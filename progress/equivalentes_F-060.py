# progress/equivalentes_F-060.py
"""F-060 · demostracion EJECUTABLE de los 6 mutantes equivalentes (RM5).

Los 6 supervivientes que el humano acepto como equivalentes (2026-10-24,
«acepto») en `progress/mutacion_F-060.md`. Para cada uno construye el
modulo mutado a partir del fuente ACTUAL (sustituyendo la linea original
por la mutada, que tiene que aparecer una sola vez), lo carga junto al
original y compara:

  sv4 (`racha_incidencia.py`), diferencial puro: #4 (`_dias`), #6 (el
      `f = int(l.fecha_int or 0)` de `viaja` en `decidir`; con T17 (DA13)
      la condicion de la linea 172 paso a esa funcion; es tambien el
      superviviente 1 de `progress/mutacion_F-060_enmienda.md`, T23),
      #7 (`colapsar`) y
      #8 (`aviso_desordenada`). 20.000 entradas al azar por mutante con
      fechas `None`/`0`/`1`, papelera, 1e-9 h e ids repetidos, sobre
      `decidir`, `aviso_desordenada` y `colapsar`.
  sv5 (`registro_pipeline.py`), ejercitando la rama:
      #11 (`int(a.recurso_ide or 0)` del paso 6 bis) y #12 (`int(ls.hmoide
      or 0)` del `pos` del paso 9): diferencial del pipeline completo
      (`preflight` y `ejecutar` con `MOVER_CIZ` encendido sobre
      `SigridFake`) con CIZ candidatos de otro recurso o del recurso 1,
      lineas sin recurso o con recurso 0, partes sin `hmoide` o con
      `hmoide` 0, cerrados, enlazadas y modo pruebas.
      #12, ademas, la invariante que lo hace equivalente: `decidir_fin`
      con `partes` construido como en `registro_pipeline.py` (solo
      `hmoide` verdaderos, `estados_de_partes` que puede no devolver
      alguno) NUNCA da `mover` con una linea sin `hmoide`.

Si alguna salida difiere (o la invariante falla), imprime el primer
contraejemplo y sale con 1; si no, con 0.

Uso, desde la raiz del repositorio, con el python del `.venv` del repo:

    cd services/partes-front
    python ../../progress/equivalentes_F-060.py sv4
    cd ../partes-transfer
    python ../../progress/equivalentes_F-060.py sv5

Sin red ni BBDD. Datos sinteticos. sv4 tarda unos segundos; sv5, ~1 min.
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

#: servicio -> [(n, fichero, linea original, linea mutada)].
MUTANTES: dict[str, list[tuple[int, str, str, str]]] = {
    "sv4": [
        (4, RI, "f = int(linea.fecha_int or 0)",
         "f = int(linea.fecha_int or 1)"),
        (6, RI, "f = int(l.fecha_int or 0)", "f = int(l.fecha_int or 1)"),
        (7, RI, "if (a.registro_id < b.registro_id and a.persona == b.persona",
         "if (a.registro_id <= b.registro_id and a.persona == b.persona"),
        (8, RI, "hay = any(int(l.fecha_int or 0) == siguiente and l.activa",
         "hay = any(int(l.fecha_int or 1) == siguiente and l.activa"),
    ],
    "sv5": [
        (11, RP, "d = decidir_fin(a.fecha_int, int(a.recurso_ide or 0), "
                 "candidatas,",
         "d = decidir_fin(a.fecha_int, int(a.recurso_ide or 1), candidatas,"),
        (12, RP, "pos = (int(ls.pos) if int(ls.hmoide or 0) == hmoide",
         "pos = (int(ls.pos) if int(ls.hmoide or 1) == hmoide"),
    ],
}

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


# =============================== sv4 =============================== #

_FECHAS = (None, 0, 1, 20260930, 20261001, 20261002, 20261003, 20261004,
           20261005, 20261006, 20261031, 20261102, 20261130, 20261201)


def _hist(azar: random.Random, mod) -> list:
    out = []
    for _ in range(azar.randint(0, 9)):
        es_inc = azar.random() < 0.6
        out.append(mod.LineaHist(
            registro_id=azar.randint(1, 8), fecha_int=azar.choice(_FECHAS),
            es_incidencia=es_inc,
            clave=azar.choice(("V", "B")) if es_inc else "",
            horas=azar.choice((0.0, 1e-9, None, 8.0, -2.0)),
            sigrid_estado=azar.choice((None, "registrado", "encolado",
                                       "omitido", "pendiente")),
            activa=azar.random() < 0.75))
    return out


def _roles(azar: random.Random, mod) -> list:
    return [mod.LineaRol(
        registro_id=azar.randint(1, 6),
        persona=azar.choice(("dni:A", "dni:B")),
        fecha_int=azar.choice(_FECHAS[3:]),
        clave=azar.choice(("V", "B")),
        rol=azar.choice(("inicio", "fin", "intermedio")),
        racha_registro_ids=tuple(sorted(azar.sample(range(1, 7),
                                                    azar.randint(0, 3)))))
        for _ in range(azar.randint(0, 6))]


def _comparar_sv4(orig, mod, casos: int = 20000) -> str | None:
    azar = random.Random(20261024)
    for _ in range(casos):
        semilla = azar.random()
        h_o = _hist(random.Random(semilla), orig)
        h_m = _hist(random.Random(semilla), mod)
        d = azar.choice(_FECHAS[3:])
        clave = azar.choice(("V", "B"))
        a, b = orig.decidir(h_o, d, clave), mod.decidir(h_m, d, clave)
        if repr(a) != repr(b):
            return f"decidir({h_o}, {d}, {clave}): {a} != {b}"
        a, b = orig.aviso_desordenada(h_o, d), mod.aviso_desordenada(h_m, d)
        if a != b:
            return f"aviso_desordenada({h_o}, {d}): {a} != {b}"
        r_o = _roles(random.Random(semilla), orig)
        r_m = _roles(random.Random(semilla), mod)
        a, b = orig.colapsar(r_o), mod.colapsar(r_m)
        if a != b:
            return f"colapsar({r_o}): {a} != {b}"
    return None


def _sv4() -> int:
    from application.services import racha_incidencia as orig
    fallos = 0
    for n, fichero, original, mutada in MUTANTES["sv4"]:
        error = _comparar_sv4(orig, _mutar(fichero, original, mutada))
        fallos += _informe(n, fichero, original, mutada, error)
    return fallos


# =============================== sv5 =============================== #

def _escenario(azar: random.Random):
    """Un `SigridFake` con 0-4 lineas candidatas y 1-3 lineas a aprobar."""
    from tests import test_f060_pipeline_mover as t
    d = azar.randint(20261002, 20261028)
    filas = []
    for i in range(azar.randint(0, 4)):
        fec = azar.choice((d - 2, d - 1, d - 1, d - 1, d + 1, 20260930))
        filas.append(t._fila(
            7000 + i, fec=fec, rid=azar.randint(1, 6),
            hmoide=azar.choice((t.HMO_OCT, t.HMO_OCT, t.HMO_OCT, t.HMO_SEP,
                                0, None)),
            horide=azar.choice((t.CIZ, t.CIZ, t.CIZ, t.CIV)),
            can=azar.choice((0.0, 0.0, 0.0, None, 1.0)),
            tex=azar.choice((None, "PRUEBA-IA")),
            enlazada=azar.random() < 0.1,
            pos=azar.choice((None, 64, 192)),
            reside=azar.choice((t.REC, t.REC, t.REC, 1, 999))))
    partes = [t._parte(t.HMO_SEP, "PT26/00009", mes=9,
                       est=azar.choice((t.REGISTRO, t.CERRADO))),
              t._parte(t.HMO_OCT, "PT26/00010",
                       est=azar.choice((t.REGISTRO, t.REGISTRO, t.CERRADO)))]
    cli = t._cli(*filas, partes=partes)
    lineas = []
    for j in range(azar.randint(1, 3)):
        racha = sorted(azar.sample(range(1, 7), azar.randint(0, 6)))
        linea = t._fin(100 + j, d + j, racha)
        linea.recurso_ide = azar.choice((t.REC, t.REC, t.REC, None, 0, 1))
        if azar.random() < 0.2:
            linea.incidencia_rol = "inicio"
        lineas.append(linea)
    if azar.random() < 0.3:
        lineas.append(t._trabajo(200, d))
    return cli, lineas, azar.random() < 0.2


def _correr(mod_pipe, cli, lineas, pruebas: bool) -> str:
    from tests import test_f060_pipeline_mover as t
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


def _comparar_pipeline(orig, mod, casos: int = 5000) -> str | None:
    azar = random.Random(20261025)
    movidos = sin_recurso = 0
    for _ in range(casos):
        cli, lineas, pruebas = _escenario(azar)
        a = _correr(orig, copy.deepcopy(cli), lineas, pruebas)
        b = _correr(mod, copy.deepcopy(cli), lineas, pruebas)
        if a != b:
            return f"{lineas}\n--- original ---\n{a}\n--- mutante ---\n{b}"
        movidos += "'movida_de'" in a
        sin_recurso += any(not l.recurso_ide and l.racha_registro_ids
                           for l in lineas)
    print(f"    pipeline: {casos} escenarios, {movidos} con un CIZ movido, "
          f"{sin_recurso} con un fin con racha y sin recurso")
    return None


def _invariante_12(casos: int = 200000) -> str | None:
    """`decidir_fin` con `partes` como lo construye el pipeline: un
    `mover` siempre trae una linea con `hmoide` verdadero."""
    from application.services.racha_ciz import MOVER, decidir_fin
    from domain.models.registro_models import LineaSigrid, ParteSigrid
    azar = random.Random(20261026)
    con_sin_parte = movidas = 0
    for _ in range(casos):
        d = azar.randint(20261002, 20261028)
        candidatas = [LineaSigrid(
            ide=7000 + i, reside=azar.choice((501, 501, 1)),
            fecha_int=azar.choice((d - 2, d - 1, d + 1)), horide=40,
            hora_codigo=azar.choice(("CIZ", "CIZ", "CIV")),
            can=azar.choice((0.0, None, 1.0)), tot=0.0,
            synckey=f"partes:{i}", hmoide=azar.choice((None, 0, 900, 901)),
            enlazada=azar.random() < 0.1)
            for i in range(azar.randint(0, 4))]
        for ls in candidatas:
            ls.tex = azar.choice((None, "PRUEBA-IA"))
            ls.pos = 64
        # registro_pipeline.py: hmoides solo verdaderos; estados_de_partes
        # devuelve los que existen (aqui, alguno puede faltar).
        hmoides = {int(ls.hmoide) for ls in candidatas if ls.hmoide}
        partes = {h: ParteSigrid(ide=h, cod=f"PT26/{h}",
                                 est=azar.choice((1, 1, 3)))
                  for h in hmoides if azar.random() < 0.9}
        con_sin_parte += any(not ls.hmoide for ls in candidatas)
        r = decidir_fin(d, 501, candidatas, partes=partes, est_registro=1,
                        marca_pruebas=azar.choice((None, "PRUEBA-IA")))
        if r.tipo == MOVER:
            movidas += 1
            if not r.linea.hmoide:
                return f"mover sin hmoide: {candidatas} {partes} -> {r}"
    print(f"    invariante #12: {casos} llamadas, {con_sin_parte} con algun "
          f"CIZ sin parte, {movidas} mover, todas con hmoide verdadero")
    return None


def _sv5() -> int:
    from application.pipelines import registro_pipeline as orig
    logging.disable(logging.CRITICAL)     # los WARNING/INFO del pipeline
    fallos = 0
    for n, fichero, original, mutada in MUTANTES["sv5"]:
        error = _comparar_pipeline(orig, _mutar(fichero, original, mutada))
        if error is None and n == 12:
            error = _invariante_12()
        fallos += _informe(n, fichero, original, mutada, error)
    return fallos


def _informe(n, fichero, original, mutada, error) -> int:
    estado = "EQUIVALENTE" if error is None else "DISTINTO"
    print(f"{estado}: #{n} {fichero}: {original.strip()} -> {mutada.strip()}")
    if error is not None:
        print(f"    contraejemplo: {error[:1500]}")
    return 0 if error is None else 1


def main() -> int:
    servicio = sys.argv[1] if len(sys.argv) > 1 else ""
    if servicio not in MUTANTES:
        print("uso: equivalentes_F-060.py sv4|sv5 (desde la carpeta del "
              "servicio)")
        return 2
    fallos = _sv4() if servicio == "sv4" else _sv5()
    print(f"{len(MUTANTES[servicio])} mutantes, {fallos} distintos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
