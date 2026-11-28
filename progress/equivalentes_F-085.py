# progress/equivalentes_F-085.py
"""F-085 · T9 y T14: comprobacion EJECUTABLE de los 5 supervivientes de la
campana (`progress/mutacion_F-085.md`) que se proponen como EQUIVALENTES. Los
otros 4 (#3, #4, #6 y #7) los matan tests (ver `progress/impl_F-085.md`). La
aceptacion de los equivalentes es del humano.

Los 5 son de la familia `x is None` -> `not x` (o `x is not None` -> `x`):
solo se distinguen si `x` puede ser un valor FALSO distinto de `None`. Para
cada uno, contra el fuente ACTUAL, el script comprueba:

  1. LOCALIZACION: la linea original esta UNA sola vez dentro de su funcion
     (por el AST). Si el codigo cambia, la demostracion deja de valer y falla.
  2. DOMINIO, leido del codigo (AST, tipos sin `__bool__`/`__len__`,
     constantes no vacias): el valor solo puede ser `None` o algo siempre
     verdadero.
  3. EMPIRICO: aplica el mutante en una copia del fuente, en memoria y sin
     tocar el fichero, y compara original y mutado en muchos casos con
     bordes. La salida tiene que ser la misma; una excepcion tambien cuenta
     como salida.
  4. CONTROL NEGATIVO: un mutante NO equivalente de la misma linea, en el
     mismo banco, tiene que dar alguna salida DISTINTA (el banco ve
     diferencias: no es un banco ciego).

  #1 sv4 `conversion_clase.py:78`  `_letra`: `clase is not None` -> `clase`
  #2 sv4 `conversion_clase.py:89`  `decidir`: `error is not None` -> `error`
  #5 sv4 `parte_repository.py:3388` `set_registro_hora`:
                                   `clase.error is not None` -> `clase.error`
  #8 sv5 `racha_ciz.py:327`  `decidir_inicio`: `parte is not None` -> `parte`
  #9 sv5 `racha_ciz.py:324`  `decidir_inicio`: `previo is None` -> `not previo`

Uso, con el python del `.venv` del repo, desde la raiz de la copia:

    python progress/equivalentes_F-085.py

sv4 y sv5 tienen los dos un paquete `application`: la parte de sv5 corre en
un subproceso con su propia carpeta. Sale con 0 si todo se cumple; si no,
imprime el primer fallo y sale con 1. Sin red ni PostgreSQL: SQLite en
memoria (`tests/dobles.py`). Datos sinteticos, sin DNIs ni nombres reales.
"""
from __future__ import annotations

import ast
import dataclasses
import logging
import random
import subprocess
import sys
import types
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[1]
SV4 = RAIZ_REPO / "services" / "partes-front"
SV5 = RAIZ_REPO / "services" / "partes-transfer"
logging.disable(logging.CRITICAL)

CONV = "application/services/conversion_clase.py"
REPO = "infrastructure/database/parte_repository.py"
RACHA = "application/services/racha_ciz.py"


# ------------------------------ comunes ------------------------------- #

def _falla(n, msg: str) -> None:
    print(f"FALLO superviviente #{n}: {msg}")
    sys.exit(1)


def _fuente(raiz: Path, fichero: str) -> str:
    return (raiz / fichero).read_text(encoding="utf-8").replace("\r\n", "\n")


def _funcion(arbol: ast.AST, nombre: str, dentro: str | None = None):
    """La FunctionDef `nombre` (dentro de la clase `dentro`), unica."""
    raiz = arbol
    if dentro is not None:
        raiz = next(n for n in ast.walk(arbol)
                    if isinstance(n, ast.ClassDef) and n.name == dentro)
    encontradas = [n for n in ast.walk(raiz) if isinstance(n, ast.FunctionDef)
                   and n.name == nombre]
    if len(encontradas) != 1:
        raise LookupError(f"{nombre}: {len(encontradas)} definiciones")
    return encontradas[0]


def _mutar(n, fuente: str, funcion: str, original: str, mutada: str,
           dentro: str | None = None) -> str:
    """El fuente con `original` -> `mutada` SOLO dentro de `funcion`."""
    fn = _funcion(ast.parse(fuente), funcion, dentro)
    lineas = fuente.split("\n")
    trozo = "\n".join(lineas[fn.lineno - 1:fn.end_lineno])
    if trozo.count(original) != 1:
        _falla(n, f"`{original.strip()}` no esta una sola vez en {funcion}")
    lineas[fn.lineno - 1:fn.end_lineno] = trozo.replace(
        original, mutada).split("\n")
    return "\n".join(lineas)


def _modulo(raiz: Path, fuente: str, nombre: str,
            fichero: str) -> types.ModuleType:
    mod = types.ModuleType(nombre)
    mod.__file__ = str(raiz / fichero)
    sys.modules[nombre] = mod            # `dataclass` busca su modulo ahi
    exec(compile(fuente, str(raiz / fichero), "exec"), mod.__dict__)
    return mod


def _sin_bool(clase) -> list[str]:
    """Los `__bool__`/`__len__` de la clase y sus bases (vacio = siempre
    verdadera)."""
    return [f"{k.__name__}.{m}" for k in clase.__mro__ if k is not object
            for m in ("__bool__", "__len__") if m in vars(k)]


def _salida(f, *a, **kw):
    """La salida de `f`, o la excepcion (tipo y texto) como salida."""
    try:
        r = f(*a, **kw)
    except Exception as exc:  # noqa: BLE001
        return ("EXC", type(exc).__name__, str(exc))
    if dataclasses.is_dataclass(r) and not isinstance(r, type):
        return (type(r).__name__, dataclasses.astuple(r))
    return r


def _ok(n, ref: str, desc: str, casos: int) -> None:
    print(f"#{n} {ref}: equivalente ({desc}); {casos} casos iguales; "
          "control negativo distinguido")


# ================================ sv4 ================================= #

CODIGOS = [None, "", " ", "C", "CI", "ci", " CI ", "CIA", " cia ", "cIa",
           "CIV", "CIB", "CIP", "CIF", "CIH", "CIM", "CIZ", " ciz ", "Ciz",
           "CIQ", "CIX", "CIAA", "CIZZ", "HL01", "hl01", "HLOF", "HEOF",
           "heof", "HENC", "HE", "H", "X", "0", "ZCI", "C I A"]


def sv4() -> None:
    sys.path.insert(0, str(SV4))
    sys.path.insert(0, str(SV4 / "tests"))
    from application.services import conversion_clase as conv_orig
    from application.services.incidencias_horas import ClaseIncidencia
    from test_f025_deteccion import TABLA
    tablas = [TABLA, None]
    codigos = CODIGOS + sorted(TABLA.por_sigrid)

    fuente = _fuente(SV4, CONV)
    arbol = ast.parse(fuente)

    # --- #1 `_letra`: `clase` es una ClaseIncidencia o None ------------- #
    n = 1
    if _sin_bool(ClaseIncidencia):
        _falla(n, f"ClaseIncidencia define {_sin_bool(ClaseIncidencia)}")
    tipos = {type(v) for v in TABLA.por_sigrid.values()}
    if tipos != {ClaseIncidencia}:
        _falla(n, f"por_sigrid guarda {tipos}")
    fn = _funcion(arbol, "_letra")
    gets = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and isinstance(c.func, ast.Attribute) and c.func.attr == "get"]
    if len(gets) != 1 or len(gets[0].args) != 1:
        _falla(n, "`clase` no sale de un solo `por_sigrid.get(x)` sin defecto")
    linea = "return clase.letra if clase is not None else None"
    mut = _modulo(SV4, _mutar(n, fuente, "_letra", linea,
                              "return clase.letra if clase else None"),
                  "conv_m1", CONV)
    neg = _modulo(SV4, _mutar(n, fuente, "_letra", linea,
                              "return clase.letra if clase is None else None"),
                  "conv_n1", CONV)
    casos, distinto = 0, False
    for t in tablas:
        for c in codigos:
            o = _salida(conv_orig._letra, c, t)
            if o != _salida(mut._letra, c, t):
                _falla(n, f"{c!r}: difieren")
            distinto = distinto or o != _salida(neg._letra, c, t)
            casos += 1
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(n, f"{CONV}:78", "None o ClaseIncidencia sin __bool__/__len__", casos)

    # --- #2 `decidir`: `error` es None o una cadena no vacia ------------ #
    n = 2
    fn = _funcion(arbol, "error_de_codigo")
    rets = sorted(ast.unparse(r.value) for r in ast.walk(fn)
                  if isinstance(r, ast.Return))
    if rets != sorted(["None", "MOTIVO_CIZ_NO_SE_ELIGE",
                       "motivo_sin_letra(codigo)"]):
        _falla(n, f"error_de_codigo devuelve {rets}")
    if not conv_orig.MOTIVO_CIZ_NO_SE_ELIGE.strip():
        _falla(n, "MOTIVO_CIZ_NO_SE_ELIGE vacio")
    if any(not conv_orig.motivo_sin_letra(c) for c in codigos):
        _falla(n, "motivo_sin_letra puede dar una cadena vacia")
    mut = _modulo(SV4, _mutar(n, fuente, "decidir", "if error is not None:",
                              "if error:"), "conv_m2", CONV)
    neg = _modulo(SV4, _mutar(n, fuente, "decidir", "if error is not None:",
                              "if error is None:"), "conv_n2", CONV)
    estados = [(e, l, t) for e in (False, True)
               for l in (None, "", "AT", "at", "V", "X")
               for t in (None, "", "normal", "extra", "AT", "V")]
    casos, distinto = 0, False
    for tabla in tablas:
        for c in codigos:
            for e, l, t in estados:
                kw = dict(es_incidencia=e, incidencia_codigo=l, tipo_hora=t,
                          codigo=c, tabla=tabla)
                o = _salida(conv_orig.decidir, **kw)
                if o != _salida(mut.decidir, **kw):
                    _falla(n, f"{kw}: difieren")
                distinto = distinto or o != _salida(neg.decidir, **kw)
                casos += 1
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(n, f"{CONV}:89", "None o un motivo no vacio", casos)

    # --- #5 `set_registro_hora`: `clase.error` del dominio de #2 -------- #
    n = 5
    from dobles import FabricaSesionSqlite, sembrar_parte
    from infrastructure.database import parte_repository as repo_orig
    from infrastructure.database.orm_models import (
        ParteRegistroOrm,
        UndoLogOrm,
    )
    rfuente = _fuente(SV4, REPO)
    fn = _funcion(ast.parse(rfuente), "set_registro_hora",
                  "ParteReviewRepository")
    asign = [a for a in ast.walk(fn) if isinstance(a, ast.Assign)
             and [ast.unparse(x) for x in a.targets] == ["clase"]]
    if (len(asign) != 1 or not isinstance(asign[0].value, ast.Call)
            or ast.unparse(asign[0].value.func) != "decidir_clase"):
        _falla(n, "`clase` no sale de una sola llamada a `decidir_clase`")
    if "decidir as decidir_clase" not in rfuente:
        _falla(n, "`decidir_clase` no es `conversion_clase.decidir`")
    dc = _funcion(arbol, "decidir")
    errores = [k for k in ast.walk(dc) if isinstance(k, ast.keyword)
               and k.arg == "error"]
    if [ast.unparse(k.value) for k in errores] != ["error"]:
        _falla(n, "`ClaseNueva.error` no sale solo de `error_de_codigo`")
    args = ("set_registro_hora", "if clase.error is not None:")
    mut = _modulo(SV4, _mutar(n, rfuente, *args, "if clase.error:",
                              "ParteReviewRepository"), "repo_m5", REPO)
    neg = _modulo(SV4, _mutar(n, rfuente, *args, "if clase.error is None:",
                              "ParteReviewRepository"), "repo_n5", REPO)
    CAMPOS = ("es_incidencia", "tipo_hora", "incidencia_codigo", "horas",
              "horas_orig", "extra_auto", "hora_codigo", "hora_ide",
              "hora_match_method")

    def sembrar(fabrica):
        ids = sembrar_parte(fabrica, [{"tipo": "normal"}, {"tipo": "extra",
                                                           "horas": 2.0},
                                      {"tipo": "normal"}],
                            document_id="doc-eq")
        with fabrica.create_session() as s:
            s.get(ParteRegistroOrm, ids[0]).horas_orig = 10.0
            s.get(ParteRegistroOrm, ids[1]).extra_auto = True
            r = s.get(ParteRegistroOrm, ids[2])
            r.es_incidencia, r.tipo_hora = True, "AT"
            r.incidencia_codigo, r.horas, r.hora_codigo = "AT", None, "CIA"
            s.commit()
        return ids

    def resultado(mod, rid_idx, codigo, tabla) -> tuple:
        fabrica = FabricaSesionSqlite()
        ids = sembrar(fabrica)
        repo = mod.ParteReviewRepository(fabrica)
        salida = _salida(repo.set_registro_hora, registro_id=ids[rid_idx],
                         hora_ide=7, hora_codigo=codigo,
                         hora_descripcion="d", hora_ext=0,
                         hora_precio_coste=1.0, hora_precio_nomina=1.0,
                         incidencias=tabla)
        with fabrica.create_session() as s:
            filas = [tuple(getattr(s.get(ParteRegistroOrm, i), c)
                           for c in CAMPOS) for i in ids]
            undo = [(u.action, u.description)
                    for u in s.query(UndoLogOrm).order_by(UndoLogOrm.id)]
        return salida, filas, undo

    casos, distinto = 0, False
    for tabla in tablas:
        for c in codigos:
            for idx in (0, 1, 2):
                o = resultado(repo_orig, idx, c, tabla)
                if o != resultado(mut, idx, c, tabla):
                    _falla(n, f"{c!r} linea {idx}: difieren")
                distinto = distinto or o != resultado(neg, idx, c, tabla)
                casos += 1
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(n, f"{REPO}:3388", "None o un motivo no vacio (#2)", casos)


# ================================ sv5 ================================= #

def sv5() -> None:
    sys.path.insert(0, str(SV5))
    from application.services import racha_ciz as racha_orig
    from domain.models.registro_models import LineaSigrid, ParteSigrid
    for k in (LineaSigrid, ParteSigrid):
        if _sin_bool(k):
            _falla(8, f"{k.__name__} define {_sin_bool(k)}")

    fuente = _fuente(SV5, RACHA)
    arbol = ast.parse(fuente)
    # Dominio de #9: `previo` es el primer valor de `inicio_previo`, que
    # solo devuelve `None` o `primera` (una de las `candidatas`, LineaSigrid).
    fn = _funcion(arbol, "inicio_previo")
    rets = sorted(ast.unparse(r.value) for r in ast.walk(fn)
                  if isinstance(r, ast.Return))
    primeros = sorted({r.split(",")[0].strip("( ") for r in rets})
    if primeros != ["None", "primera"]:
        _falla(9, f"inicio_previo devuelve {rets}")
    # Dominio de #8: `parte` sale de `partes.get(...)`: en el pipeline,
    # `partes` es `{h: ParteSigrid(...)}` (registro_pipeline, paso 6 bis).
    di = _funcion(arbol, "decidir_inicio")
    if "parte = partes.get(int(previo.hmoide or 0))" not in ast.unparse(di):
        _falla(8, "`parte` no sale de `partes.get`")
    pipe = _fuente(SV5, "application/pipelines/registro_pipeline.py")
    if pipe.count("partes = {h: ParteSigrid(ide=h, cod=d.get(\"cod\"), "
                  "est=d.get(\"est\"))") != 1:
        _falla(8, "el pipeline ya no construye `partes` con ParteSigrid")

    variantes = {
        "m8": _mutar(8, fuente, "decidir_inicio",
                     "cod = parte.cod if parte is not None else None",
                     "cod = parte.cod if parte else None"),
        "n8": _mutar(8, fuente, "decidir_inicio",
                     "cod = parte.cod if parte is not None else None",
                     "cod = parte.cod if parte is None else None"),
        "m9": _mutar(9, fuente, "decidir_inicio", "if previo is None:",
                     "if not previo:"),
        "n9": _mutar(9, fuente, "decidir_inicio", "if previo is None:",
                     "if previo is not None:"),
    }
    mods = {k: _modulo(SV5, v, f"racha_{k}", RACHA)
            for k, v in variantes.items()}

    azar = random.Random(85)
    D, RES = 20261018, 501
    codigos = ["CIV", "civ", " CIV ", "CIA", "CIZ", None, ""]

    def linea(i: int) -> LineaSigrid:
        hora = azar.choice(["CIV", "CIV", "CIZ", "CIZ", "CIA", "HL01", None,
                            " civ "])
        sk = azar.choice([f"partes:{i}", f"partes:{i}:ciz", "manual", None,
                          f"partes:{i}"])
        return LineaSigrid(
            ide=7000 + i, reside=azar.choice([RES, RES, RES, RES + 1]),
            fecha_int=D + azar.randint(-3, 9), horide=30,
            hora_codigo=hora, can=azar.choice([0.0, 0.0, None, 8.0]),
            tot=0.0, synckey=sk, nuestra=True,
            hmoide=azar.choice([901, 901, 905, 555, None, 0]),
            enlazada=azar.random() < .15,
            tex=azar.choice([None, None, "PRUEBA-IA", "otro"]))

    casos, salidas = 0, {k: [] for k in ("o", *mods)}
    def racha() -> list[LineaSigrid]:
        """Una racha con inicio previo (CIV `partes:<i>` tras D y su CIZ
        en su dia o despues), con parte, enlace y marca al azar."""
        f = D + azar.randint(1, 4)
        hmo = azar.choice([901, 905, 555, None, 0])
        tex = azar.choice([None, "PRUEBA-IA"])
        return [LineaSigrid(ide=8000, reside=RES, fecha_int=f, horide=30,
                            hora_codigo="CIV", can=0.0, tot=0.0,
                            synckey="partes:80", nuestra=True, hmoide=hmo,
                            enlazada=azar.random() < .2, tex=tex),
                LineaSigrid(ide=8001, reside=RES,
                            fecha_int=f + azar.randint(0, 5), horide=40,
                            hora_codigo="CIZ", can=0.0, tot=0.0,
                            synckey="partes:81", nuestra=True, hmoide=hmo,
                            tex=tex)]

    while casos < 4000:
        cands = [linea(i) for i in range(azar.randint(0, 6))]
        if casos % 2:
            cands = racha() + cands[:2]
        partes = {h: ParteSigrid(ide=h, cod=c, est=e) for h, c, e in
                  azar.sample([(901, "PT26/00010", 1),
                               (905, "PT26/00008", 3),
                               (555, None, None), (0, "", 1)],
                              azar.randint(0, 4))}
        kw = dict(partes=partes, est_registro=1,
                  marca_pruebas=azar.choice([None, None, "PRUEBA-IA"]))
        args = (D, RES, azar.choice(codigos), cands)
        salidas["o"].append(_salida(racha_orig.decidir_inicio, *args, **kw))
        for k, m in mods.items():
            salidas[k].append(_salida(m.decidir_inicio, *args, **kw))
        casos += 1
    movidos = sum(1 for s in salidas["o"] if s[1][0] == "mover")
    cerrados = sum(1 for s in salidas["o"] if s[1][0] == "parte_cerrado")
    if movidos < 50 or cerrados < 50:
        _falla(8, f"banco pobre: {movidos} mover, {cerrados} parte_cerrado")
    for n in (8, 9):
        if salidas[f"m{n}"] != salidas["o"]:
            _falla(n, "original y mutado difieren")
        if salidas[f"n{n}"] == salidas["o"]:
            _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(9, f"{RACHA}:324", "None o una LineaSigrid sin __bool__/__len__",
        casos)
    _ok(8, f"{RACHA}:327", "None o un ParteSigrid sin __bool__/__len__",
        casos)


def main() -> int:
    if sys.argv[1:] == ["sv5"]:
        sv5()
        return 0
    sv4()
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "sv5"],
                       cwd=SV5)
    if r.returncode != 0:
        return 1
    print("5/5 equivalentes demostrados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
