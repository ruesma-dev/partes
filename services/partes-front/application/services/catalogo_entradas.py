# application/services/catalogo_entradas.py
"""F-072 (R25): las entradas de las obras agrupadas que ofrece el portal.

Una ENTRADA es una obra agrupada (postventa o VAR) más una partida suya, y
el portal la trata como una obra: el selector la ofrece y el cambio de obra
la pone. Por empresa:

  - con UNA obra VAR (`VAR_OBRA_COD`), cada partida suya del universo VAR
    (hoja activa con número inicial ≥ `VAR_PARTIDA_DESDE`, R7);
  - con UNA obra de postventa (`POSTVENTA_OBRA_COD`), cada obra NO agrupada
    de la empresa que case con una hoja activa suya (R4-R6, con un índice
    equivalente a `casar_postventa`, no un bucle obras × hojas);
  - con varias o ninguna, nada de ese tipo (WARNING si son varias).

Caché con el TTL del catálogo de obras. Un fallo de lectura deja `[]` con
WARNING y no se cachea: las obras normales siguen. Las reglas son las del
gemelo `obras_agrupadas.py`; aquí solo se arma el catálogo.
"""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from application.services.obras_agrupadas import (
    POSTVENTA,
    VAR,
    Ajustes,
    codigo_entrada,
    es_partida_var,
    normalizar,
)
from application.services.partida_catalog import build_arbol_partidas

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Entrada:
    """Una entrada: la obra agrupada, la partida y su rótulo (R24)."""
    tipo: str
    obra_ide: int
    obra_codigo: str | None
    obra_nombre: str | None
    empresa: int | None
    partida_ide: int
    partida_cod: str | None
    partida_res: str | None
    partida_capitulo: str | None
    codigo: str
    nombre: str | None


class IndicePostventa:
    """`casar_postventa` por índice: el código normalizado igual entero y, si
    no, el código seguido solo de letras (la más corta; a igualdad, la de
    menor código y luego la de menor `ide`). Solo hojas activas."""

    def __init__(self, hojas: Any) -> None:
        nodos = hojas.values() if isinstance(hojas, dict) else hojas
        self._exactas: dict[str, Any] = {}
        self._con_letras: dict[str, Any] = {}
        for h in nodos:
            if not (h.es_hoja and h.activa):
                continue
            cod = normalizar(h.cod)
            if not cod:
                continue
            previa = self._exactas.get(cod)
            if previa is None or h.ide < previa.ide:
                self._exactas[cod] = h
            for corte in range(len(cod) - 1, 0, -1):
                if not cod[corte:].isalpha():
                    break
                base = cod[:corte]
                previa = self._con_letras.get(base)
                if previa is None or _orden(h) < _orden(previa):
                    self._con_letras[base] = h

    def casar(self, codigo_obra: Any) -> Any:
        cod = normalizar(codigo_obra)
        if not cod:
            return None
        return self._exactas.get(cod) or self._con_letras.get(cod)


def _orden(h: Any) -> tuple:
    cod = normalizar(h.cod)
    return (len(cod), cod, h.ide)


class CatalogoEntradas:
    def __init__(self, *, obra_catalog: Any, sigrid_client: Any,
                 ajustes: Ajustes, ttl_seconds: int = 600) -> None:
        self._obras = obra_catalog
        self._sigrid = sigrid_client
        self._ajustes = ajustes
        self._ttl = int(ttl_seconds)
        self._lock = threading.RLock()
        self._items: list[Entrada] = []
        self._por_clave: dict[tuple[int, int], Entrada] = {}
        self._cargado_en: float | None = None

    @property
    def ajustes(self) -> Ajustes:
        return self._ajustes

    # ------------------------------------------------------------------ #
    def entradas(self) -> list[Entrada]:
        self._refrescar()
        return list(self._items)

    def entrada(self, obra_ide: Any, partida_ide: Any) -> Entrada | None:
        """La entrada `(obra agrupada, partida)` si está en el catálogo."""
        if not obra_ide or not partida_ide:
            return None
        self._refrescar()
        return self._por_clave.get((int(obra_ide), int(partida_ide)))

    # ------------------------------------------------------------------ #
    def _refrescar(self) -> None:
        if self._sigrid is None or not self._ajustes.activo:
            return
        with self._lock:
            ahora = time.time()
            if (self._cargado_en is not None
                    and (ahora - self._cargado_en) < self._ttl):
                return
            try:
                items = self._construir(self._obras.list())
            except Exception as exc:  # noqa: BLE001
                logger.warning("[entradas] no se pudo leer el catalogo de "
                               "entradas; se queda vacio: %r", exc)
                self._items, self._por_clave = [], {}
                self._cargado_en = None
                return
            self._items = items
            self._por_clave = {(e.obra_ide, e.partida_ide): e for e in items}
            self._cargado_en = ahora
            logger.info("[entradas] catalogo cargado: %s entradas",
                        len(items))

    def _construir(self, obras: Iterable[Any]) -> list[Entrada]:
        obras = list(obras)
        agrupadas: dict[tuple[str, Any], list[Any]] = {}
        normales: dict[Any, list[Any]] = {}
        for o in obras:
            tipo = self._ajustes.tipo_de(o.codigo)
            if tipo:
                agrupadas.setdefault((tipo, o.empresa), []).append(o)
            elif o.ide is not None:
                normales.setdefault(o.empresa, []).append(o)
        out: list[Entrada] = []
        for (tipo, empresa), lista in sorted(
                agrupadas.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
            if len(lista) != 1:
                logger.warning(
                    "[entradas] empresa=%s tiene varias obras %s (%s): sin "
                    "entradas de ese tipo", empresa, tipo,
                    ", ".join(str(o.ide) for o in lista))
                continue
            agr = lista[0]
            hojas = build_arbol_partidas(
                self._sigrid.fetch_partidas_obra(int(agr.ide)))
            if tipo == VAR:
                desde = int(self._ajustes.var_desde or 0)
                out.extend(self._entrada(VAR, agr, h, h.res)
                           for h in sorted(hojas.values(), key=lambda h: h.ide)
                           if es_partida_var(h, desde))
            else:
                indice = self._indice_postventa(hojas)
                vistas: set[int] = set()
                for x in sorted(normales.get(empresa, []),
                                key=lambda o: (normalizar(o.codigo), o.ide)):
                    h = indice.casar(x.codigo)
                    if h is None or h.ide in vistas:
                        continue
                    vistas.add(h.ide)
                    out.append(self._entrada(POSTVENTA, agr, h,
                                             h.res or x.nombre))
        return out

    @staticmethod
    def _indice_postventa(hojas: Any) -> IndicePostventa:
        return IndicePostventa(hojas)

    def _entrada(self, tipo: str, agr: Any, h: Any,
                 nombre: str | None) -> Entrada:
        return Entrada(
            tipo=tipo, obra_ide=int(agr.ide), obra_codigo=agr.codigo,
            obra_nombre=agr.nombre, empresa=agr.empresa, partida_ide=int(h.ide),
            partida_cod=h.cod, partida_res=h.res,
            partida_capitulo=h.capitulo_cod,
            codigo=codigo_entrada(tipo, self._ajustes.var_cod, h.cod),
            nombre=nombre)
