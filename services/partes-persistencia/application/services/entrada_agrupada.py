# application/services/entrada_agrupada.py
"""F-072 · La ENTRADA de una obra agrupada en la ingesta (R14-R17, R19).

Una entrada es la obra agrupada de una empresa (`POSTVENTA_OBRA_COD` o
`VAR_OBRA_COD`) más una de sus partidas. `ResolutorEntradas` la casa a partir
de la forma del «Nº OBRA» (`leer_forma` del gemelo, que el pipeline ya ha
leído) con las reglas puras de `obras_agrupadas`:

- VAR con resto (R14): la obra VAR se elige entre las de su código como
  cualquier obra (F-023: membrete y trabajadores) y el resto se casa con el
  universo VAR (`es_partida_var` + `casar_var`).
- Postventa con resto (R15): el resto es la obra X (casado de siempre, con
  ceros a la izquierda); la obra de postventa es la de la empresa de X, y la
  partida, la de `casar_postventa` sobre el código de Sigrid de X.
- Forma base (R16): cada partida leída distinta y no vacía es un resto; vale
  si todas dan la misma entrada.

Sin entrada, la obra queda sin casar con un motivo de R17: nunca se elige al
azar ni se cae al casado normal. Los presupuestos se cachean con TTL; un
fallo de lectura (o `truncated`, que el cliente ya trata como error) NO se
cachea y sube (R19): el parte no se guarda y el mensaje se reintenta.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from application.services.obras_agrupadas import (
    POSTVENTA,
    VAR,
    Ajustes,
    Forma,
    casar_postventa,
    casar_var,
    es_partida_var,
)
from application.services.partida_catalog import PartidaNodo, build_arbol_partidas
from domain.models.parte_records import ObraMatch

logger = logging.getLogger(__name__)

#: R17: motivos de un parte con forma de entrada y sin entrada (≤ 24).
POSTVENTA_OBRA_NO_CASA = "postventa_obra_no_casa"
AGRUPADA_SIN_OBRA = "agrupada_sin_obra"
POSTVENTA_SIN_PARTIDA = "postventa_sin_partida"
VAR_FUERA_UNIVERSO = "var_fuera_universo"
AGRUPADA_SIN_ENTRADA = "agrupada_sin_entrada"
AGRUPADA_VARIAS_ENTRADAS = "agrupada_varias_entradas"
MOTIVOS: tuple[str, ...] = (
    POSTVENTA_OBRA_NO_CASA, AGRUPADA_SIN_OBRA, POSTVENTA_SIN_PARTIDA,
    VAR_FUERA_UNIVERSO, AGRUPADA_SIN_ENTRADA, AGRUPADA_VARIAS_ENTRADAS,
)


@dataclass(frozen=True)
class ResultadoEntrada:
    """La obra del parte y, con entrada, su partida y su tipo (la marca).
    Sin entrada, `obra` no tiene `ide` y su `method` es el motivo (R17)."""

    obra: ObraMatch
    partida: PartidaNodo | None = None
    tipo: str | None = None

    @property
    def clave(self) -> tuple[int | None, int | None]:
        return (self.obra.ide, None if self.partida is None else self.partida.ide)


def _sin(motivo: str) -> ResultadoEntrada:
    return ResultadoEntrada(obra=ObraMatch(method=motivo))


def _obra(o: Any, metodo: str) -> ObraMatch:
    return ObraMatch(ide=o.ide, codigo=o.codigo, nombre=o.nombre, score=1.0,
                     method=metodo, empresa=o.empresa)


class ResolutorEntradas:
    """Casa la entrada de un parte con forma de obra agrupada."""

    def __init__(self, *, lookup: Any, ajustes: Ajustes,
                 ttl_seconds: int = 600) -> None:
        self._lookup = lookup
        self.ajustes = ajustes
        self._ttl = int(ttl_seconds)
        self._lock = threading.RLock()
        self._cache: dict[int, tuple[float, dict[int, PartidaNodo]]] = {}

    # ------------------------------------------------------------------ #
    def resolver(self, forma: Forma, parte: Any, matchers: Any,
                 empresa_m: int | None, discriminantes: list) -> ResultadoEntrada:
        if forma.resto:
            return self._con_resto(forma.tipo, forma.resto, matchers,
                                   empresa_m, discriminantes)
        restos = sorted({(r.partida or "").strip() for r in parte.registros}
                        - {""})
        if not restos:
            return _sin(AGRUPADA_SIN_ENTRADA)
        resultados = [self._con_resto(forma.tipo, resto, matchers, empresa_m,
                                      discriminantes) for resto in restos]
        con_entrada = {r.clave for r in resultados if r.partida is not None}
        if len(con_entrada) == 1 and all(r.partida is not None
                                         for r in resultados):
            return resultados[0]
        if con_entrada:
            return _sin(AGRUPADA_VARIAS_ENTRADAS)
        motivos = {r.obra.method for r in resultados}
        return _sin(motivos.pop() if len(motivos) == 1 else AGRUPADA_SIN_ENTRADA)

    # ------------------------------------------------------------------ #
    def _con_resto(self, tipo: str, resto: str, matchers: Any,
                   empresa_m: int | None, discriminantes: list) -> ResultadoEntrada:
        if tipo == VAR:
            return self._var(resto, matchers, empresa_m, discriminantes)
        return self._postventa(resto, matchers, empresa_m, discriminantes)

    def _var(self, resto, matchers, empresa_m, discriminantes) -> ResultadoEntrada:
        obra = matchers.obra.match(codigo=self.ajustes.var_cod, nombre=None,
                                   empresa_membrete=empresa_m,
                                   discriminantes=discriminantes)
        if obra.ide is None:
            return _sin(AGRUPADA_SIN_OBRA)
        desde = int(self.ajustes.var_desde or 0)
        universo = [h for h in self._hojas(obra.ide).values()
                    if es_partida_var(h, desde)]
        partida = casar_var(universo, resto)
        if partida is None:
            return _sin(VAR_FUERA_UNIVERSO)
        obra.method, obra.score = VAR, 1.0
        return ResultadoEntrada(obra=obra, partida=partida, tipo=VAR)

    def _postventa(self, resto, matchers, empresa_m,
                   discriminantes) -> ResultadoEntrada:
        x = matchers.obra.match(codigo=resto, nombre=None,
                                empresa_membrete=empresa_m,
                                discriminantes=discriminantes)
        if x.ide is None or self.ajustes.tipo_de(x.codigo) is not None:
            return _sin(POSTVENTA_OBRA_NO_CASA)
        de_empresa = [o for o in matchers.obra.obras_de_codigo(
            self.ajustes.postventa_cod) if o.empresa == x.empresa]
        if len(de_empresa) != 1:
            return _sin(AGRUPADA_SIN_OBRA)
        pv = de_empresa[0]
        partida = casar_postventa(self._hojas(pv.ide), x.codigo)
        if partida is None:
            return _sin(POSTVENTA_SIN_PARTIDA)
        return ResultadoEntrada(obra=_obra(pv, POSTVENTA), partida=partida,
                                tipo=POSTVENTA)

    # ------------------------------------------------------------------ #
    def _hojas(self, obra_ide: int) -> dict[int, PartidaNodo]:
        """Árbol del presupuesto de la obra agrupada (cacheado con TTL). Un
        fallo de lectura sube sin cachearse (R19)."""
        ahora = time.time()
        with self._lock:
            hit = self._cache.get(obra_ide)
            if hit is not None and (ahora - hit[0]) < self._ttl:
                return hit[1]
        nodos = build_arbol_partidas(self._lookup.fetch_partidas_obra(obra_ide))
        with self._lock:
            self._cache[obra_ide] = (ahora, nodos)
        logger.info("[entrada-agrupada] presupuesto obra=%s nodos=%s",
                    obra_ide, len(nodos))
        return nodos
