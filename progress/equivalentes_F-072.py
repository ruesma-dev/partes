# progress/equivalentes_F-072.py
"""F-072 · T28: comprobacion EJECUTABLE de los 13 supervivientes que
`progress/mutacion_F-072.md` propone como EQUIVALENTES. La aceptacion es del
humano, pendiente.

Todos son de la misma familia: el mutante cambia una comparacion con `None`
(`x is None`, `x is not None`) por la veracidad de `x` (`not x`, `x`). Solo
se distinguen si `x` puede ser un valor FALSO distinto de `None` (`0`, `""`,
un contenedor vacio, un objeto con `__bool__` o `__len__`). Para cada uno el
script comprueba, contra el fuente ACTUAL:

  1. que la linea original sigue ahi, una sola vez en su fichero (si el
     codigo cambia, la demostracion deja de valer y el script falla);
  2. que el dominio de `x` en ese punto no tiene valores falsos distintos de
     `None`:
     - TIPO: `x` es `None` o una instancia de una clase SIN `__bool__` ni
       `__len__` en su MRO (salvo `object`): toda instancia es verdadera.
       Se comprueba la clase y una instancia;
     - TUPLA: `x` es `None` o una tupla de 2 (siempre verdadera);
     - TIPO_DE: `x` sale de `Ajustes.tipo_de`, que solo da `POSTVENTA`,
       `VAR` (cadenas no vacias) o `None`: se recorre con 2.000 codigos al
       azar y los bordes (`""`, `None`, `0`, espacios, guiones);
     - BORRADO: `deleted_at_utc` solo se escribe con `None` o con
       `datetime.now(timezone.utc).isoformat()` (nunca vacia): se recorren
       TODAS las asignaciones de `deleted_at_utc` del codigo de los cinco
       servicios y cada una tiene que ser de una lista cerrada.

Uso, con el python del `.venv` del repo, desde la carpeta del servicio:

    cd services/partes-api          && python ../../progress/equivalentes_F-072.py sv2
    cd services/partes-persistencia && python ../../progress/equivalentes_F-072.py sv3
    cd services/partes-front        && python ../../progress/equivalentes_F-072.py sv4
    cd services/partes-transfer     && python ../../progress/equivalentes_F-072.py sv5

Sale con 0 si todo se cumple; si no, imprime el primer fallo y sale con 1.
Sin red ni BBDD. Tarda menos de un segundo por servicio.
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
SERVICIOS = RAIZ.parent

PP = "application/pipelines/persist_parte_pipeline.py"
EA = "application/services/entrada_agrupada.py"

#: servicio -> [(n, fichero, original, mutada, familia, dato)].
#: `dato`: para TIPO, (modulo, clase, constructor de una instancia).
MUTANTES: dict[str, list[tuple]] = {
    "sv2": [
        (1, "application/services/obra_sigrid.py",
         "if self._marcas is not None and leer_forma(codigo, self._marcas):",
         "if self._marcas and leer_forma(codigo, self._marcas):", "TIPO",
         ("application.services.obras_agrupadas", "Marcas",
          lambda m: m.Marcas(postventa=(), var=()))),
    ],
    "sv3": [
        (19, PP, "if forma is None:", "if not forma:", "TIPO",
         ("application.services.obras_agrupadas", "Forma",
          lambda m: m.Forma(tipo="", resto=""))),
        (20, PP, "if tipo is not None:", "if tipo:", "TIPO_DE", None),
        (21, PP, "None if parte.entrada is None else parte.entrada.cod)",
         "None if not parte.entrada else parte.entrada.cod)", "TIPO",
         ("domain.models.parte_records", "EntradaPartida",
          lambda m: m.EntradaPartida(ide=0, cod=None, res=None,
                                     capitulo=None, tipo=""))),
        (23, EA, "if len(con_entrada) == 1 and all(r.partida is not None",
         "if len(con_entrada) == 1 and all(r.partida", "TIPO",
         ("application.services.partida_catalog", "PartidaNodo",
          lambda m: m.PartidaNodo(ide=0, padide=None, cod=None, res=None,
                                  tex=None))),
        (26, EA, "partida = casar_var(universo, resto)\n        if partida is None:",
         "partida = casar_var(universo, resto)\n        if not partida:", "TIPO",
         ("application.services.partida_catalog", "PartidaNodo",
          lambda m: m.PartidaNodo(ide=0, padide=None, cod="", res=None,
                                  tex=None))),
        (34, "application/services/partida_conciliador.py",
         "if (self._ajustes is not None", "if (self._ajustes", "TIPO",
         ("application.services.obras_agrupadas", "Ajustes",
          lambda m: m.ajustes_de(postventa_cod=None, var_cod=None,
                                 var_desde=None))),
        (36, "infrastructure/database/sqlalchemy_parte_repository.py",
         "    if entrada is None:\n        return {}",
         "    if not entrada:\n        return {}", "TIPO",
         ("domain.models.parte_records", "EntradaPartida",
          lambda m: m.EntradaPartida(ide=0, cod=None, res=None,
                                     capitulo=None, tipo=""))),
    ],
    "sv4": [
        (12, "infrastructure/database/parte_repository.py",
         "claves = {obra_key_for_registro(r) for r in doc.registros\n"
         "                  if r.deleted_at_utc is None}",
         "claves = {obra_key_for_registro(r) for r in doc.registros\n"
         "                  if not r.deleted_at_utc}", "BORRADO", None),
        (13, "infrastructure/database/parte_repository.py",
         "if r.deleted_at_utc is None}:", "if not r.deleted_at_utc}:",
         "BORRADO", None),
        (14, "infrastructure/database/parte_repository.py",
         "        if entrada is not None:\n            partida_ide, partida_cod",
         "        if entrada:\n            partida_ide, partida_cod", "TIPO",
         ("application.services.catalogo_entradas", "Entrada",
          lambda m: m.Entrada(tipo="", obra_ide=0, obra_codigo=None,
                              obra_nombre=None, empresa=None, partida_ide=0,
                              partida_cod=None, partida_res=None,
                              partida_capitulo=None, codigo="",
                              nombre=None))),
        (15, "interface_adapters/web/app.py",
         "            if entrada is None:\n                raise HTTPException(",
         "            if not entrada:\n                raise HTTPException(",
         "TIPO",
         ("application.services.catalogo_entradas", "Entrada",
          lambda m: m.Entrada(tipo="", obra_ide=0, obra_codigo=None,
                              obra_nombre=None, empresa=None, partida_ide=0,
                              partida_cod=None, partida_res=None,
                              partida_capitulo=None, codigo="",
                              nombre=None))),
    ],
    "sv5": [
        (37, "application/pipelines/registro_pipeline.py",
         "        if agrupada is not None:\n            tipo, origen = agrupada",
         "        if agrupada:\n            tipo, origen = agrupada", "TUPLA",
         None),
    ],
}

#: Las unicas formas de escribir `deleted_at_utc` en el codigo de los
#: servicios (sin tests). `now_iso` y `ahora` son siempre
#: `datetime.now(timezone.utc).isoformat()`; `doc.deleted_at_utc` copia uno
#: de esos valores.
_BORRADO_RHS = {"None", "now_iso", "ahora", "doc.deleted_at_utc"}


def _falla(n: int, msg: str) -> None:
    print(f"FALLO superviviente #{n}: {msg}")
    sys.exit(1)


def _sin_falsedad(cls: type) -> list[str]:
    return [f"{k.__name__}.{nombre}" for k in cls.__mro__ if k is not object
            for nombre in ("__bool__", "__len__") if nombre in vars(k)]


def _tipo(n: int, dato: tuple) -> None:
    import importlib
    modulo = importlib.import_module(dato[0])
    cls = getattr(modulo, dato[1])
    if _sin_falsedad(cls):
        _falla(n, f"{dato[1]} define {_sin_falsedad(cls)}")
    inst = dato[2](modulo)
    if not isinstance(inst, cls) or not bool(inst):
        _falla(n, f"una instancia de {dato[1]} es falsa")


def _tipo_de(n: int) -> None:
    from application.services.obras_agrupadas import POSTVENTA, VAR, ajustes_de
    azar = random.Random(20261123)
    alfabeto = "VARPOSTV2 -.0"
    bordes = [None, "", " ", "0", 0, "-", "VAR", "POSTV2", " var ", "post-v2"]
    for aj in (ajustes_de(postventa_cod="POSTV2", var_cod="VAR", var_desde="29"),
               ajustes_de(postventa_cod=None, var_cod=None, var_desde=None)):
        for cod in bordes + ["".join(azar.choice(alfabeto)
                                     for _ in range(azar.randint(0, 8)))
                             for _ in range(2000)]:
            t = aj.tipo_de(cod)
            if t not in (POSTVENTA, VAR, None):
                _falla(n, f"tipo_de({cod!r}) = {t!r}")
    if not (POSTVENTA and VAR):
        _falla(n, "POSTVENTA o VAR es una cadena vacia")


def _borrado(n: int) -> None:
    vistas = 0
    for py in sorted(SERVICIOS.glob("*/**/*.py")):
        if "tests" in py.parts or ".venv" in py.parts:
            continue
        texto = py.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"deleted_at_utc\s*=(?!=)\s*([^,\n)]+)", texto):
            rhs = m.group(1).strip()
            vistas += 1
            if rhs not in _BORRADO_RHS:
                _falla(n, f"{py}: deleted_at_utc = {rhs}")
            if rhs in ("now_iso", "ahora"):
                # La ULTIMA asignacion de ese nombre antes de usarlo.
                previas = list(re.finditer(rf"\b{rhs}\s*=(?!=)\s*(.+)",
                                           texto[:m.start()]))
                if not previas or previas[-1].group(1).strip() != (
                        "datetime.now(timezone.utc).isoformat()"):
                    _falla(n, f"{py}: {rhs} no es un isoformat() ahi")
    if not vistas:
        _falla(n, "no se ha encontrado ninguna escritura de deleted_at_utc")


def main(servicio: str) -> int:
    for n, fichero, original, mutada, familia, dato in MUTANTES[servicio]:
        fuente = (RAIZ / fichero).read_text(encoding="utf-8").replace("\r\n", "\n")
        if fuente.count(original) != 1:
            _falla(n, f"la linea original no esta una sola vez en {fichero}")
        if original == mutada:
            _falla(n, "original y mutada son iguales")
        if familia == "TIPO":
            _tipo(n, dato)
        elif familia == "TIPO_DE":
            _tipo_de(n)
        elif familia == "BORRADO":
            _borrado(n)
        elif familia == "TUPLA":
            if "-> tuple[str, ObraEntrada] | None:" not in fuente \
                    or "return (tipo, origen) if tipo else None" not in fuente:
                _falla(n, "_obra_agrupada ya no da una tupla de 2 o None")
        print(f"#{n} {fichero}: equivalente ({familia})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
