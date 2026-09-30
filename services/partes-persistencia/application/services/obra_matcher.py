# application/services/obra_matcher.py
"""Casa una obra leida (codigo y/o nombre) contra el maestro ``obr`` de
Sigrid. Prioridad: codigo exacto > codigo con ceros a la izquierda >
nombre por similitud.

Los partes escriben el numero de obra sin ceros ('672'), pero en Sigrid
el codigo suele ir con ceros a 4 digitos ('0672'). Por eso, si el codigo
leido es numerico y no casa tal cual, se prueban variantes con/ sin ceros.

F-023: un codigo puede existir en DOS empresas (las «gemelas»). Todas las
obras del codigo compiten y decide `seleccion_sigrid.elegir_obra` (R9-R13)
con la empresa del membrete y los trabajadores del parte. Sin codigo, el
nombre se limita a la empresa del membrete si se conoce y un empate es
`nombre_ambiguo` (R14).
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable

from application.services import text_match as tm
from application.services.seleccion_sigrid import (
    elegir_obra,
    elegir_por_nombre,
)
from domain.models.parte_records import ObraMatch
from domain.models.sigrid_models import ObraRow

logger = logging.getLogger(__name__)


def _code_candidates(code_norm: str) -> list[str]:
    """Variantes de un codigo para tolerar ceros a la izquierda."""
    out = [code_norm]
    if code_norm.isdigit():
        # Sin ceros a la izquierda y rellenado a 3/4/5 digitos.
        stripped = code_norm.lstrip("0") or "0"
        for variant in (stripped, stripped.zfill(3),
                        stripped.zfill(4), stripped.zfill(5)):
            if variant not in out:
                out.append(variant)
    return out


class ObraMatcher:
    def __init__(
        self,
        *,
        obras: list[ObraRow],
        min_score: float = 0.55,
    ) -> None:
        self._obras = obras
        self._min_score = float(min_score)
        self._by_codigo: dict[str, list[ObraRow]] = defaultdict(list)
        for o in obras:
            cod_n = tm.normalize_code(o.codigo)
            if cod_n:
                self._by_codigo[cod_n].append(o)
        logger.info(
            "[obra-matcher] %s obras (cod=%s) min_score=%s",
            len(obras), len(self._by_codigo), self._min_score,
        )

    def _candidatas(self, cod_n: str) -> tuple[list[ObraRow], bool] | None:
        """Obras del codigo exacto o, si no hay, de la primera variante con
        ceros que tenga alguna; el booleano dice si hizo falta variante.
        None si ninguna variante del codigo existe."""
        for i, cand in enumerate(_code_candidates(cod_n)):
            obras = self._by_codigo.get(cand)
            if obras:
                return obras, i > 0
        return None

    def match(
        self,
        *,
        codigo: str | None,
        nombre: str | None,
        empresa_membrete: int | None = None,
        discriminantes: Iterable[frozenset[int]] = (),
    ) -> ObraMatch:
        cod_n = tm.normalize_code(codigo)
        hallado = self._candidatas(cod_n) if cod_n else None
        if hallado is not None:
            candidatas, padded = hallado
            obra, metodo = elegir_obra(
                candidatas, empresa_membrete, list(discriminantes),
                nombre, self._min_score,
            )
            if obra is None:
                return ObraMatch(method=metodo)
            if not padded:
                return self._to_match(obra, 1.0, metodo)
            if metodo == "codigo":
                metodo = "codigo_padded"
            return self._to_match(obra, 0.98, metodo)

        # R14: sin codigo que case, por nombre; limitado a la empresa del
        # membrete si se conoce.
        pool = [
            o for o in self._obras
            if empresa_membrete is None or o.empresa == empresa_membrete
        ]
        obra, motivo = elegir_por_nombre(pool, nombre, self._min_score)
        if obra is None:
            return ObraMatch(method=motivo)
        return self._to_match(
            obra, tm.name_similarity(nombre, obra.nombre), "nombre"
        )

    @staticmethod
    def _to_match(o: ObraRow, score: float, method: str) -> ObraMatch:
        return ObraMatch(
            ide=o.ide,
            codigo=o.codigo,
            nombre=o.nombre,
            score=round(score, 4),
            method=method,
            empresa=o.empresa,
        )
