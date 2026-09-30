# application/services/empleado_matcher.py
"""Casa el trabajador leido del parte por SIMILITUD DE NOMBRE (R24).

Desde F-023 el casado por DNI no vive aqui: la ficha de un DNI se elige en
`seleccion_sigrid.IndicePersonas.elegir_ficha` con la empresa del parte y
la baja a la fecha (R17-R21), y los alias en el pipeline (R23). Este
matcher solo resuelve el ultimo recurso, el nombre, y SOLO entre las
fichas candidatas que le pasan (las de R17: de alta a la fecha del parte y
de la empresa del parte).

Nunca elige al azar: si la mejor ficha es de un DNI con varias fichas
candidatas, o empata con la de otra persona, devuelve `nombre_ambiguo`.
"""
from __future__ import annotations

import logging

from application.services import text_match as tm
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import EmpleadoRow

logger = logging.getLogger(__name__)


def _persona(e: EmpleadoRow) -> str:
    """Identidad de persona: el DNI normalizado o, sin DNI, la ficha."""
    return tm.normalize_dni(e.dni) or f"ficha:{e.ide}"


class EmpleadoMatcher:
    def __init__(self, *, min_score: float = 0.55) -> None:
        self._min_score = float(min_score)

    def match_nombre(
        self,
        *,
        nombre: str | None,
        candidatas: list[EmpleadoRow],
    ) -> EmpleadoMatch:
        """R24: la ficha candidata de nombre mas parecido, si alcanza el
        umbral y no hay ambiguedad de persona."""
        if not candidatas or not tm.normalize(nombre):
            return EmpleadoMatch()
        puntuadas = sorted(
            ((tm.name_similarity(nombre, e.nombre), e) for e in candidatas),
            key=lambda par: par[0], reverse=True,
        )
        mejor, ficha = puntuadas[0]
        if mejor < self._min_score:
            return EmpleadoMatch()
        persona = _persona(ficha)
        suyas = [e for e in candidatas if _persona(e) == persona]
        empatadas = [e for score, e in puntuadas if score >= mejor]
        if len(suyas) > 1 or any(_persona(e) != persona for e in empatadas):
            return EmpleadoMatch(method="nombre_ambiguo")
        return self.to_match(ficha, mejor, "nombre")

    @staticmethod
    def to_match(e: EmpleadoRow, score: float, method: str) -> EmpleadoMatch:
        return EmpleadoMatch(
            ide=e.ide,
            codigo=e.codigo,
            nombre=e.nombre,
            dni=e.dni,
            reside=e.reside,
            score=round(score, 4),
            method=method,
        )
