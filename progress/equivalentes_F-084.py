# progress/equivalentes_F-084.py
"""F-084 · T10 (ciclo 2, RM5): comprobacion EJECUTABLE de los 7 supervivientes
que `progress/mutacion_F-084.md` propone como EQUIVALENTES. La aceptacion es
del humano y esta PENDIENTE.

Los 7 son de la familia `x is None` -> `not x` (o `is not None` -> veracidad):
solo se distinguen si `x` puede ser un valor FALSO distinto de `None`. Para
cada uno el script comprueba, contra el fuente ACTUAL:

  1. LOCALIZACION: la linea original esta UNA sola vez dentro de su funcion
     (por el AST); si el codigo cambia, la demostracion deja de valer y falla;
  2. DOMINIO, leido del codigo (AST, tipo o constantes no vacias): que el
     valor solo puede ser `None` o algo siempre verdadero;
  3. EMPIRICO: aplica el mutante en una copia del fuente (en memoria, sin
     tocar el fichero) y compara original y mutado en N casos con bordes
     (None, 0, -5, 1, "", cadenas ilegibles, fechas reales...): MISMA salida;
  4. CONTROL NEGATIVO: un mutante NO equivalente de la misma linea, en el
     mismo banco, tiene que dar alguna salida DISTINTA (el banco ve
     diferencias: no es un banco ciego).

Uso, con el python del `.venv` del repo, desde la carpeta de sv4:

    cd services/partes-front && python ../../progress/equivalentes_F-084.py

Sale con 0 si todo se cumple; si no, imprime el primer fallo y sale con 1.
Sin red ni PostgreSQL: SQLite en memoria (`tests/dobles.py`). Datos
sinteticos, sin DNIs ni nombres reales.
"""
from __future__ import annotations

import ast
import logging
import random
import sys
import types
from datetime import datetime
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
logging.disable(logging.CRITICAL)

PCP = "application/services/partes_con_problemas.py"
REPO = "infrastructure/database/parte_repository.py"
APP = "interface_adapters/web/app.py"
CONG = "application/services/congelacion.py"


def _falla(n, msg: str) -> None:
    print(f"FALLO superviviente #{n}: {msg}")
    sys.exit(1)


def _fuente(fichero: str) -> str:
    return (RAIZ / fichero).read_text(encoding="utf-8").replace("\r\n", "\n")


def _funcion(arbol: ast.AST, nombre: str, dentro: str | None = None):
    """La FunctionDef `nombre` (dentro de la funcion o clase `dentro`)."""
    raiz = arbol
    if dentro is not None:
        raiz = next(n for n in ast.walk(arbol)
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                    and n.name == dentro)
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


def _modulo(fuente: str, nombre: str, fichero: str) -> types.ModuleType:
    mod = types.ModuleType(nombre)
    mod.__file__ = str(RAIZ / fichero)   # app.py busca plantillas por aqui
    sys.modules[nombre] = mod            # `dataclass` busca su modulo ahi
    exec(compile(fuente, str(RAIZ / fichero), "exec"), mod.__dict__)
    return mod


def _retornos(fn) -> list[str]:
    return sorted(ast.unparse(r) for r in ast.walk(fn)
                  if isinstance(r, ast.Return))


def _sin_bool(clase) -> list[str]:
    return [f"{k.__name__}.{m}" for k in clase.__mro__ if k is not object
            for m in ("__bool__", "__len__") if m in vars(k)]


def _ok(n, ref: str, desc: str, casos: int) -> None:
    print(f"#{n} {ref}: equivalente ({desc}); {casos} casos iguales; "
          "control negativo distinguido")


# ===================== banco puro de `partes_con_problemas` ============== #

FECHAS = [None, 0, -5, 1, 20261123, 20261127, 20261130, 20261201, 99999999]
INSTANTES = [None, "", " ", "x", "2026-11-26T10:00:00+00:00",
             "2026-11-29T23:59:00", "2026-11-30T00:30:00+02:00",
             "2026-11-26T10:00:00Z", "0001-01-01T00:00:00",
             "2026-11-26T00:00:00"]


def _gen(azar: random.Random, i: int) -> dict:
    return dict(
        id=str(i), is_active=azar.random() < .5,
        deleted_at_utc=azar.choice([None, None, None, "", "2026-11-26"]),
        deleted_by=azar.choice([None, "", "retirado-sin-lineas"]),
        fecha_int=azar.choice(FECHAS), obra_ide=azar.choice([None, 0, 1]),
        obra_codigo=azar.choice(["A", "", None]),
        obra_numero_leido=azar.choice([None, "", "7"]),
        email_id=azar.choice(["e1", "e2", "", None]),
        email_received_datetime=azar.choice(INSTANTES),
        created_at_utc=azar.choice(INSTANTES),
        sustituido_por_id=azar.choice([None, None, "", "0", "1", "9"]),
        lineas_vivas=azar.randint(0, 1), es_futuro=azar.random() < .2)


def _vista(filas) -> list:
    return [(c.doc.id, c.motivos, c.sustituto and c.sustituto.id)
            for c in filas]


def _salidas_pcp(mod, kws: list[dict]) -> tuple:
    """Todas las salidas publicas; una excepcion tambien es una salida."""
    try:
        return _salidas_pcp_sin_red(mod, kws)
    except Exception as exc:  # noqa: BLE001
        return ("excepcion", type(exc).__name__)


def _salidas_pcp_sin_red(mod, kws: list[dict]) -> tuple:
    docs = [mod.DocProblema(**k) for k in kws]
    por_id = {d.id: d for d in docs}
    activos = [d for d in docs if d.is_active]
    return (
        [mod.motivos_activo(d) for d in docs],
        [mod.fecha_posterior_al_correo(k["fecha_int"],
                                       k["email_received_datetime"])
         for k in kws],
        [(s.id if (s := mod.elegir_sustituto(d, por_id, activos)) else None)
         for d in docs],
        _vista(mod.clasificar(docs)),
        mod.resumen(mod.clasificar(docs)),
    )


def _banco_pcp(n, original, mutado, negativo, casos: int = 5000) -> None:
    azar = random.Random(20261127 + n)
    distinto = False
    for caso in range(casos):
        kws = [_gen(azar, i) for i in range(azar.randint(0, 5))]
        a = _salidas_pcp(original, kws)
        if a != _salidas_pcp(mutado, kws):
            _falla(n, f"caso {caso}: original y mutado difieren ({kws})")
        distinto = distinto or a != _salidas_pcp(negativo, kws)
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")


def pcp() -> None:
    fuente = _fuente(PCP)
    arbol = ast.parse(fuente)
    original = _modulo(fuente, "pcp_original", PCP)

    # --- #1 pcp:144 `_fecha_valida` -------------------------------------- #
    n, orig = 1, "return fecha_int is not None and fecha_int > 0"
    usos = [nd for nd in ast.walk(arbol) if isinstance(nd, ast.Call)
            and isinstance(nd.func, ast.Name) and nd.func.id == "_fecha_valida"]
    padres = {id(h): p for p in ast.walk(arbol) for h in ast.iter_child_nodes(p)}
    if not usos or any(not (isinstance(padres[id(u)], ast.UnaryOp)
                            and isinstance(padres[id(u)].op, ast.Not))
                       for u in usos):
        _falla(n, "algun llamador de `_fecha_valida` no la usa con `not`")
    fuera = [p for p in RAIZ.rglob("*.py") if "tests" not in p.parts
             and p.as_posix() != (RAIZ / PCP).as_posix()
             and "_fecha_valida" in p.read_text(encoding="utf-8")
             and "partes_con_problemas" in p.read_text(encoding="utf-8")]
    if fuera:
        _falla(n, f"`_fecha_valida` de F-084 se usa fuera: {fuera}")
    mut = _modulo(_mutar(n, fuente, "_fecha_valida", orig,
                         "return fecha_int and fecha_int > 0"), "pcp_m1", PCP)
    neg = _modulo(_mutar(n, fuente, "_fecha_valida", orig,
                         "return fecha_int is not None and fecha_int >= 0"),
                  "pcp_n1", PCP)
    for v in (None, 0, -5, 1, 20261123):     # misma decision bajo `not`
        if (not original._fecha_valida(v)) != (not mut._fecha_valida(v)):
            _falla(n, f"`not _fecha_valida({v!r})` cambia")
    _banco_pcp(n, original, mut, neg)
    _ok(n, f"{PCP}:144", f"{len(usos)} llamadores, todos bajo `not`", 5000)

    # --- #2 pcp:174 `recibido is None` ----------------------------------- #
    n = 2
    fn = _funcion(arbol, "_instante")
    if _retornos(fn) != sorted([
            "return None",
            "return momento.replace(tzinfo=timezone.utc)",
            "return momento.astimezone(timezone.utc)"]):
        _falla(n, f"`_instante` devuelve otra cosa: {_retornos(fn)}")
    asig = [ast.unparse(a.value) for a in ast.walk(fn)
            if isinstance(a, ast.Assign)
            and any(getattr(t, "id", None) == "momento" for t in a.targets)]
    if asig != ["datetime.fromisoformat(_texto(iso))"]:
        _falla(n, f"`momento` ya no es un datetime.fromisoformat: {asig}")
    if _sin_bool(datetime) or not bool(datetime.min):
        _falla(n, "un datetime puede ser falso")
    mut = _modulo(_mutar(n, fuente, "fecha_posterior_al_correo",
                         "if recibido is None:", "if not recibido:"),
                  "pcp_m2", PCP)
    neg = _modulo(_mutar(n, fuente, "fecha_posterior_al_correo",
                         "if recibido is None:", "if recibido is not None:"),
                  "pcp_n2", PCP)
    _banco_pcp(n, original, mut, neg)
    _ok(n, f"{PCP}:174", "None o datetime, siempre verdadero", 5000)

    # --- #3 pcp:244 `sustituto is None` ---------------------------------- #
    n = 3
    llamadas = [nd for nd in ast.walk(arbol) if isinstance(nd, ast.Call)
                and getattr(nd.func, "id", None) == "motivo_sustituido"]
    if [ast.unparse(c.args[1]) for c in llamadas] != ["sustituto"]:
        _falla(n, "`motivo_sustituido` tiene otros llamadores")
    clas = _funcion(arbol, "clasificar")
    origen = [ast.unparse(a.value) for a in ast.walk(clas)
              if isinstance(a, ast.Assign)
              and any(getattr(t, "id", None) == "sustituto" for t in a.targets)]
    if origen != ["elegir_sustituto(d, por_id, activos)"]:
        _falla(n, f"`sustituto` ya no sale de elegir_sustituto: {origen}")
    if _retornos(_funcion(arbol, "elegir_sustituto")) != sorted([
            "return por_id.get(_texto(d.sustituido_por_id))", "return None",
            "return None", "return c", "return candidatos[0]"]):
        _falla(n, "`elegir_sustituto` devuelve otra cosa")
    if _sin_bool(original.DocProblema):
        _falla(n, "DocProblema define __bool__ o __len__")
    mut = _modulo(_mutar(n, fuente, "motivo_sustituido",
                         "if sustituto is None:", "if not sustituto:"),
                  "pcp_m3", PCP)
    neg = _modulo(_mutar(n, fuente, "motivo_sustituido",
                         "if sustituto is None:", "if True:"), "pcp_n3", PCP)
    _banco_pcp(n, original, mut, neg)
    _ok(n, f"{PCP}:244", "None o DocProblema, siempre verdadero", 5000)


# ===================== repositorio (SQLite en memoria) =================== #

def _constantes_no_vacias(n, mod, nombres: list[str]) -> None:
    for nombre in nombres:
        valor = getattr(mod, nombre)
        if not (isinstance(valor, str) and valor.strip()):
            _falla(n, f"{nombre} no es una cadena no vacia")


def repo() -> None:
    from types import SimpleNamespace as NS

    import application.services.congelacion as cg
    import application.services.partes_con_problemas as pp
    from dobles import FabricaSesionSqlite
    from infrastructure.database.orm_models import ParteDocumentOrm
    from test_f084_recuperar import _sembrar

    fuente = _fuente(REPO)
    original = _modulo(fuente, "repo_original", REPO)

    # --- #4 repo:4910 `_insignia_congelado` ------------------------------ #
    n = 4
    fn = _funcion(ast.parse(_fuente(CONG)), "motivo_congelacion_documento")
    nombres = ["MOTIVO_DOC_ENCOLADO", "MOTIVO_DOC_REGISTRADO",
               "MOTIVO_DOC_DEDICACION", "MOTIVO_DOC_APROBADO"]
    if _retornos(fn) != sorted(["return None"]
                               + [f"return {x}" for x in nombres]):
        _falla(n, f"motivo_congelacion_documento: {_retornos(fn)}")
    _constantes_no_vacias(n, cg, nombres)
    args = ("_insignia_congelado", "if motivo is None:")
    mut = _modulo(_mutar(n, fuente, *args, "if not motivo:",
                         "ParteReviewRepository"), "repo_m4", REPO)
    neg = _modulo(_mutar(n, fuente, *args, "if motivo is not None:",
                         "ParteReviewRepository"), "repo_n4", REPO)
    estados = [None, "", "pendiente", "encolado", "registrado", "dedicacion",
               "ERROR", " Registrado "]
    casos, distinto = 0, False
    for aprobado in (None, False, True, 0, 1):
        for a in estados:
            for b in estados:
                for regs in ([], [a], [a, b]):
                    doc = NS(approved=aprobado,
                             registros=[NS(sigrid_estado=e) for e in regs])
                    o = original.ParteReviewRepository._insignia_congelado(doc)
                    if o != mut.ParteReviewRepository._insignia_congelado(doc):
                        _falla(n, f"{aprobado} {regs}: difieren")
                    distinto = distinto or (
                        o != neg.ParteReviewRepository._insignia_congelado(doc))
                    casos += 1
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(n, f"{REPO}:4910", "None o 4 constantes no vacias", casos)

    # --- #5 repo:5035 `recuperar_parte` (motivo no recuperable) ---------- #
    n = 5
    fn = _funcion(ast.parse(_fuente(PCP)), "motivo_no_recuperable")
    nombres = ["MOTIVO_NO_REC_ACTIVO", "MOTIVO_NO_REC_PAPELERA",
               "MOTIVO_NO_REC_RETIRADO"]
    if _retornos(fn) != sorted(["return None"]
                               + [f"return {x}" for x in nombres]):
        _falla(n, f"motivo_no_recuperable: {_retornos(fn)}")
    _constantes_no_vacias(n, pp, nombres)
    args = ("recuperar_parte", "if motivo is not None:")
    mut = _modulo(_mutar(n, fuente, *args, "if motivo:",
                         "ParteReviewRepository"), "repo_m5", REPO)
    neg = _modulo(_mutar(n, fuente, *args, "if motivo is None:",
                         "ParteReviewRepository"), "repo_n5", REPO)
    estados = [
        dict(activo=True), dict(activo=False),
        dict(activo=False, deleted_at="2026-11-26T10:00:00+00:00"),
        dict(activo=True, deleted_at="2026-11-26T10:00:00+00:00"),
        dict(activo=False, deleted_by="retirado-sin-lineas"),
        dict(activo=False, sustituido_por_id="otro"),
        dict(activo=False, aprobado=True),
        dict(activo=False, fecha=None),
        dict(activo=False, lineas=[]),
        dict(activo=False, lineas=[{"estado": "registrado"}]),
    ]
    from application.services.parte_vacio import MARCA_RETIRADO
    estados[4]["deleted_by"] = MARCA_RETIRADO
    fechas = [(None, None), ("2026-11-25", 20261125), ("2026-11-23", 20261123)]

    def resultado(mod, kw, fecha) -> tuple:
        fabrica = FabricaSesionSqlite()
        _sembrar(fabrica, "doc", **kw)
        r = mod.ParteReviewRepository(fabrica)
        try:
            salida = r.recuperar_parte(document_id="doc", fecha_iso=fecha[0],
                                       fecha_int=fecha[1], actor="a@b.es")
        except Exception as exc:  # noqa: BLE001
            salida = (type(exc).__name__, getattr(exc, "motivo", None))
        try:
            fantasma = r.recuperar_parte(document_id="no-existe")
        except Exception as exc:  # noqa: BLE001
            fantasma = type(exc).__name__
        with fabrica.create_session() as s:
            d = s.get(ParteDocumentOrm, "doc")
            estado = (bool(d.is_active), d.fecha)
        return salida, fantasma, estado

    casos, distinto = 0, False
    for kw in estados:
        for fecha in fechas:
            o = resultado(original, kw, fecha)
            if o != resultado(mut, kw, fecha):
                _falla(n, f"{kw} {fecha}: difieren")
            distinto = distinto or o != resultado(neg, kw, fecha)
            casos += 1
    if not distinto:
        _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(n, f"{REPO}:5035", "None o 3 constantes no vacias", casos)


# ===================== portal: POST /api/partes/{id}/recuperar =========== #

def portal() -> None:
    from config.settings import Settings
    from dobles import FabricaSesionSqlite
    from fastapi.testclient import TestClient
    from infrastructure.database.parte_repository import ParteReviewRepository
    from test_f084_portal import ColaFake
    from test_f084_recuperar import _sembrar

    import os
    os.environ.setdefault("PG_PASSWORD", "irrelevante-en-tests")
    os.environ.setdefault("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    os.environ.pop("COLA_PERSISTENCIA", None)

    fuente = _fuente(APP)
    arbol = ast.parse(fuente)

    # --- dominio #6: `_parse_fecha_to_iso_int` --------------------------- #
    fn = _funcion(arbol, "_parse_fecha_to_iso_int")
    rets = [r.value for r in ast.walk(fn) if isinstance(r, ast.Return)]
    nones = [r for r in rets if isinstance(r, ast.Constant) and r.value is None]
    tuplas = [r for r in rets if isinstance(r, ast.Tuple) and len(r.elts) == 2]
    if len(rets) != len(nones) + len(tuplas) or len(tuplas) != 1:
        _falla(6, "`_parse_fecha_to_iso_int` devuelve otra cosa que None "
               "o una tupla de 2")
    # --- dominio #7: `ParteReviewRepository.recuperar_parte` ------------- #
    fn = _funcion(ast.parse(_fuente(REPO)), "recuperar_parte",
                  "ParteReviewRepository")
    rets = [r.value for r in ast.walk(fn) if isinstance(r, ast.Return)]
    dicts = [r for r in rets if isinstance(r, ast.Dict)]
    if (len(rets) != 2 or len(dicts) != 1
            or [ast.literal_eval(k) for k in dicts[0].keys]
            != ["document_id", "fecha"]
            or not any(isinstance(r, ast.Constant) and r.value is None
                       for r in rets)):
        _falla(7, "`recuperar_parte` devuelve otra cosa que None o "
               "{document_id, fecha}")
    otras = [p for p in RAIZ.rglob("*.py") if "tests" not in p.parts
             and "def recuperar_parte" in p.read_text(encoding="utf-8")]
    if sorted(p.relative_to(RAIZ).as_posix() for p in otras) != sorted(
            [REPO, APP]):
        _falla(7, f"hay otras implementaciones de recuperar_parte: {otras}")

    variantes = {
        "orig": fuente,
        "m6": _mutar(6, fuente, "recuperar_parte", "if parsed is None:",
                     "if not parsed:", "build_app"),
        "n6": _mutar(6, fuente, "recuperar_parte", "if parsed is None:",
                     "if parsed:", "build_app"),
        "m7": _mutar(7, fuente, "recuperar_parte", "if res is None:",
                     "if not res:", "build_app"),
        "n7": _mutar(7, fuente, "recuperar_parte", "if res is None:",
                     "if res is not None:", "build_app"),
    }
    fechas = [None, "", " ", "x", "31/02/2026", "00/00/0000", "2026-13-01",
              "2026-11-25", "25/11/2026", " 23/11/2026 ", "2026-1-1",
              "1/1/1", "0001-01-01", "99/99/9999", "2026/11/25", "25-11-2026"]
    estados = [dict(activo=False), dict(activo=True),
               dict(activo=False, deleted_at="2026-11-26T10:00:00+00:00"),
               dict(activo=False, aprobado=True)]
    salidas: dict[str, list] = {}
    for nombre, texto in variantes.items():
        mod = _modulo(texto, f"app_{nombre}", APP)
        fabrica = FabricaSesionSqlite()       # una base por variante, mismos
        for i in range(len(fechas)):          # partes sembrados en todas
            for j, kw in enumerate(estados):
                _sembrar(fabrica, f"doc-{i}-{j}", sha=f"sha-{i}-{j}",
                         obra_ide=1000 + 10 * i + j,
                         obra_codigo=f"O{i}-{j}", **kw)
        cliente = TestClient(mod.build_app(
            Settings(_env_file=None, graph_key="clave-de-pruebas"),
            repository=ParteReviewRepository(fabrica),
            cola_cliente=ColaFake()), raise_server_exceptions=False)
        lista = []
        for i, fecha in enumerate(fechas):
            for j in range(len(estados)):
                for doc in (f"doc-{i}-{j}", f"no-existe-{i}-{j}"):
                    cuerpo = {} if fecha is None else {"fecha": fecha}
                    r = cliente.post(f"/api/partes/{doc}/recuperar",
                                     json=cuerpo, headers={
                                         "X-MS-CLIENT-PRINCIPAL-NAME":
                                             "revisora@ejemplo.es"})
                    lista.append((r.status_code, r.text))
        with fabrica.create_session() as s:   # y el estado final de la base
            from infrastructure.database.orm_models import ParteDocumentOrm
            lista.append(sorted(
                (d.id, bool(d.is_active), d.fecha) for d in s.query(
                    ParteDocumentOrm).all()))
        salidas[nombre] = lista
    casos = len(salidas["orig"]) - 1
    for n in (6, 7):
        if salidas[f"m{n}"] != salidas["orig"]:
            _falla(n, "original y mutado difieren por HTTP")
        if salidas[f"n{n}"] == salidas["orig"]:
            _falla(n, "el control negativo no se distingue: banco ciego")
    _ok(6, f"{APP}:2284", "None o tupla de 2, siempre verdadera", casos)
    _ok(7, f"{APP}:2300", "None o dict de 2 claves, siempre verdadero",
        casos)


def main() -> int:
    pcp()
    repo()
    portal()
    print("7/7 equivalentes demostrados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
