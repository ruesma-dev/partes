# application/services/empleado_matcher.py
"""Casa el trabajador leido del parte por SIMILITUD DE NOMBRE (R24).

Desde F-023 el casado por DNI no vive aqui, y desde F-036 tampoco el
alias: los dos los resuelve `casado_recurso.casar_trabajador` contra los
recursos persona (`seleccion_sigrid.IndicePersonas.casar_por_dni`). Este
matcher solo resuelve el ultimo paso, el nombre, y SOLO entre los
candidatos que le pasan (`IndicePersonas.candidatos_nombre`: recursos
persona de alta a la fecha del parte, de su empresa y con DNI).

F-036 (R10-R12): cada candidato es una persona (el DNI del recurso) con
uno o varios nombres (el del recurso, `con.res`, y el de su ficha); puntua
el MAXIMO de ellos. Gana la persona de mayor puntuacion si llega al umbral
y ninguna OTRA persona la empata o la supera; si no, `nombre_ambiguo`.
Varios recursos de una misma persona no son ambiguedad: cual de ellos se
imputa lo decide quien llama. Nunca elige al azar.
"""
from __future__ import annotations

import logging

from application.services import text_match as tm
from domain.models.parte_records import EmpleadoMatch
from domain.models.sigrid_models import EmpleadoRow

logger = logging.getLogger(__name__)

#: Un candidato por nombre: (persona, nombres que puntuan).
Candidato = tuple[str, tuple[str | None, ...]]


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
        candidatos: list[Candidato],
    ) -> tuple[str | None, float, str]:
        """R10-R12: la persona de nombre mas parecido.

        Devuelve `(persona, puntuacion, "nombre")`, `(None, 0.0,
        "nombre_ambiguo")` si otra persona empata o supera a la mejor, o
        `(None, 0.0, "none")` si no hay nombre, candidatos o nadie llega
        al umbral. Un candidato sin ningun nombre no puntua.
        """
        if not tm.normalize(nombre):
            return None, 0.0, "none"
        por_persona: dict[str, float] = {}
        for persona, nombres in candidatos:
            puntos = [tm.name_similarity(nombre, n) for n in nombres if n]
            if not puntos:
                continue
            por_persona[persona] = max(max(puntos),
                                       por_persona.get(persona, 0.0))
        if not por_persona:
            return None, 0.0, "none"
        ganadora = max(por_persona, key=por_persona.__getitem__)
        mejor = por_persona[ganadora]
        if mejor < self._min_score:
            return None, 0.0, "none"
        if any(p != ganadora and puntos >= mejor
               for p, puntos in por_persona.items()):
            return None, 0.0, "nombre_ambiguo"
        return ganadora, round(mejor, 4), "nombre"

    def match_nombre_fichas(
        self,
        *,
        nombre: str | None,
        candidatas: list[EmpleadoRow],
    ) -> EmpleadoMatch:
        """R24 (F-023) sobre fichas: TRANSITORIO hasta que el pipeline
        delegue en `casar_trabajador` (F-036 T7), que lo retira."""
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
