# application/services/obras_agrupadas.py
"""Obras agrupadas (F-072): postventa y obras varias (VAR) como entradas.

Una **obra agrupada** es la de código `POSTVENTA_OBRA_COD` o `VAR_OBRA_COD`
de una empresa; una **entrada** es esa obra más una de sus partidas
(`Postv-<p>`, `VAR-<p>`). Aquí viven solo las reglas puras, reimplementadas
de porcentajes (`docs/ARCHITECTURE.md#regla-p5` y `#regla-var`, F-025 y
F-039) y vigiladas por `tests/test_f072_equivalencia_porcentajes.py`:

- casado de postventa (`casar_postventa`): código exacto o seguido solo de
  letras, sobre las hojas activas;
- universo VAR (`es_partida_var`) y casado de la partida leída (`casar_var`);
- lectura de la marca del «Nº OBRA» con sus variantes (`leer_forma`).

GEMELO byte-idéntico en sv2, sv3, sv4 y sv5 (lista cerrada de `CLAUDE.md`,
DA4; lo vigila `tests/test_f072_obras_agrupadas_gemelos.py`). Solo
biblioteca estándar: sv5 no tiene `text_match`. Las hojas llegan por duck
typing (`ide`, `cod`, `es_hoja`, `activa`).
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

#: Marcas de entrada: el `partida_match_method` de sus líneas.
POSTVENTA = "postventa"
VAR = "var"
MARCAS_ENTRADA: tuple[str, ...] = (POSTVENTA, VAR)

_NUMERO = re.compile(r"[0-9]+")
#: Separadores admitidos entre la marca y el resto (R41).
_SEP = r"[\s\-./]"


def _sin_tildes(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(cod: Any) -> str:
    """Código comparable: mayúsculas, sin acentos, espacios ni guiones (el
    `normalize_code` de porcentajes)."""
    if not cod:
        return ""
    return _sin_tildes(str(cod)).upper().replace(" ", "").replace("-", "")


def clave(x: Any) -> str:
    """Clave de lo leído para comparar con marcas y códigos (R42):
    mayúsculas, sin tildes ni separadores (espacios, guion, punto, barra)."""
    if not x:
        return ""
    return re.sub(_SEP, "", _sin_tildes(str(x)).upper())


def _nodos(hojas: Any) -> list:
    """Acepta una lista de hojas o el dict `ide -> nodo` del árbol."""
    if isinstance(hojas, dict):
        return list(hojas.values())
    return list(hojas or ())


def _activas(hojas: Any) -> list:
    return [h for h in _nodos(hojas) if h.es_hoja and h.activa]


def casar_postventa(hojas: Any, codigo_obra: Any) -> Any:
    """Hoja de la obra de postventa que corresponde a la obra `codigo_obra`
    (R4-R6): la de código normalizado igual entero o, sin ella, la del
    código seguido solo de letras, la más corta y, a igualdad, la menor.
    Solo hojas activas; entre iguales, la de menor `ide`."""
    cod = normalizar(codigo_obra)
    if not cod:
        return None
    candidatas = _activas(hojas)
    exactas = [h for h in candidatas if normalizar(h.cod) == cod]
    if exactas:
        return min(exactas, key=lambda h: h.ide)
    con_letras = [h for h in candidatas
                  if normalizar(h.cod).startswith(cod)
                  and normalizar(h.cod)[len(cod):].isalpha()]
    if not con_letras:
        return None
    return min(con_letras, key=lambda h: (len(normalizar(h.cod)),
                                          normalizar(h.cod), h.ide))


def numero_inicial(cod: Any) -> int | None:
    """Los dígitos con que empieza el código, sin espacios alrededor, como
    número (`029` → 29, `29.1` → 29); `None` sin dígito inicial."""
    m = _NUMERO.match(str(cod or "").strip())
    return int(m.group()) if m else None


def es_partida_var(hoja: Any, desde: int) -> bool:
    """Universo VAR (R7): hoja activa con número inicial ≥ `desde`."""
    numero = numero_inicial(hoja.cod)
    return bool(hoja.es_hoja and hoja.activa and numero is not None
                and numero >= desde)


def casar_var(partidas_var: Iterable[Any], leido: Any) -> Any:
    """Partida VAR de lo leído (R8): la de código normalizado igual (entre
    varias, la de menor `ide`); si no, la ÚNICA con el mismo número inicial
    (`29` → `029`). Con varias o ninguna, `None`."""
    objetivo = normalizar(leido)
    if not objetivo:
        return None
    partidas = _nodos(partidas_var)
    iguales = [p for p in partidas if normalizar(p.cod) == objetivo]
    if iguales:
        return min(iguales, key=lambda p: p.ide)
    numero = numero_inicial(leido)
    if numero is None:
        return None
    mismo = [p for p in partidas if numero_inicial(p.cod) == numero]
    return mismo[0] if len(mismo) == 1 else None


@dataclass(frozen=True)
class Marcas:
    """Marcas del papel de cada tipo: el código de la obra y sus alias."""

    postventa: tuple[str, ...]
    var: tuple[str, ...]


def _lista(texto: Any) -> tuple[str, ...]:
    return tuple(t.strip().upper() for t in str(texto or "").split(",")
                 if t.strip())


def marcas_de(*, postventa_cod: Any, postventa_alias: Any, var_cod: Any,
              var_alias: Any) -> Marcas:
    """Marcas desde la configuración (R1): el código y los alias (lista
    separada por comas). Sin código, el tipo está apagado y sus alias no
    cuentan (DA11)."""
    def _de(cod: Any, alias: Any) -> tuple[str, ...]:
        cod = str(cod or "").strip().upper()
        if not cod:
            return ()
        return tuple(dict.fromkeys((cod,) + _lista(alias)))
    return Marcas(postventa=_de(postventa_cod, postventa_alias),
                  var=_de(var_cod, var_alias))


@dataclass(frozen=True)
class Forma:
    """Forma leída del «Nº OBRA»: el tipo y el resto (vacío = forma base)."""

    tipo: str
    resto: str


def _ordenadas(marcas: Marcas) -> list[tuple[str, str]]:
    """(clave de la marca, tipo), de la más larga a la más corta."""
    pares = {(clave(m), POSTVENTA) for m in marcas.postventa}
    pares |= {(clave(m), VAR) for m in marcas.var}
    return sorted((p for p in pares if p[0]), key=lambda p: (-len(p[0]), p))


def _resto_valido(marca: str, sep: str, resto: str) -> bool:
    """Sin separador, o con una marca de una letra, el resto empieza por
    dígito (R41)."""
    if not sep or len(marca) == 1:
        return resto[:1].isdigit()
    return True


def leer_forma(leido: Any, marcas: Marcas) -> Forma | None:
    """Forma del «Nº OBRA» (R9, R41), o `None` si no hay marca.

    Lo que es exactamente una marca (sin tildes ni separadores) es la forma
    base. Si no, se prueba la marca delante y luego detrás, de la más larga
    a la más corta, con separador ninguno, espacios, guion, punto o barra.
    Una marca de una letra nunca va sola y su resto empieza por dígito.
    """
    texto = _sin_tildes(str(leido or "")).upper().strip()
    if not texto:
        return None
    ordenadas = _ordenadas(marcas)
    exacta = clave(texto)
    for marca, tipo in ordenadas:
        if exacta == marca:
            return Forma(tipo=tipo, resto="") if len(marca) > 1 else None
    for patron in (r"^{m}(?P<sep>{s}*)(?P<resto>[^\s\-./].*)$",
                   r"^(?P<resto>.*[^\s\-./])(?P<sep>{s}*){m}$"):
        for marca, tipo in ordenadas:
            m = re.match(patron.format(m=re.escape(marca), s=_SEP), texto)
            if m and _resto_valido(marca, m.group("sep"), m.group("resto")):
                return Forma(tipo=tipo, resto=m.group("resto").strip())
    return None


def es_obra_agrupada(codigo: Any, *, postventa: str | None,
                     var: str | None) -> str | None:
    """Tipo de la obra si su código es el de una obra agrupada; si no, o
    con el tipo apagado, `None`."""
    cod = normalizar(codigo)
    if not cod:
        return None
    if normalizar(postventa) == cod:
        return POSTVENTA
    if normalizar(var) == cod:
        return VAR
    return None


def codigo_entrada(tipo: str, var_cod: str | None, partida_cod: Any) -> str:
    """Rótulo de una entrada (R24): `Postv-<p>` o `<VAR_OBRA_COD>-<p>`."""
    if tipo == POSTVENTA:
        return f"Postv-{partida_cod}"
    return f"{var_cod}-{partida_cod}"
