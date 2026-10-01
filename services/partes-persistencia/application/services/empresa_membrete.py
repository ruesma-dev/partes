# application/services/empresa_membrete.py
"""Traduce el texto del membrete del parte a una empresa de Sigrid (F-023).

sv2 copia el membrete tal cual (R5). `auxemp` no trae CIF y su nombre
oficial no es lo que imprime el logotipo, asi que la traduccion es una
tabla VERSIONADA de alias por `numemp` (`config/empresas_membrete.yaml`,
DA3) que mantiene el humano. Es determinista a proposito: nada de
similitud difusa contra `auxemp.res`.

R7: casa si el texto normalizado contiene, como PALABRAS COMPLETAS, un
alias de exactamente una empresa valida (existe en `auxemp`, sin baja ni
desactivada). R8: sin texto, sin alias o con alias de varias empresas, la
empresa del membrete queda desconocida y se loguea el texto leido.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from application.services import text_match as tm
from domain.models.sigrid_models import EmpresaRow

logger = logging.getLogger(__name__)


def parsear_alias(datos: Any) -> dict[int, list[str]]:
    """Valida el contenido del YAML de alias: `{numemp: [alias, ...]}`.

    Un fichero mal escrito revienta el arranque (ValueError) en vez de
    dejar la tabla vacia en silencio. Los alias en blanco se descartan.
    """
    if datos is None:
        return {}
    if not isinstance(datos, dict):
        raise ValueError("la tabla de alias debe ser un mapa numemp -> lista")
    salida: dict[int, list[str]] = {}
    for clave, alias in datos.items():
        try:
            numemp = int(clave)
        except (TypeError, ValueError):
            raise ValueError(
                f"numemp no numerico en la tabla de alias: {clave!r}"
            ) from None
        if not isinstance(alias, list) or not all(
            isinstance(a, str) for a in alias
        ):
            raise ValueError(
                f"los alias de {numemp} deben ser una lista de textos"
            )
        salida[numemp] = [a for a in alias if a.strip()]
    return salida


class ResolutorEmpresa:
    """Empresa del membrete a partir del texto leido por sv2."""

    def __init__(
        self, alias: dict[int, list[str]], empresas: Iterable[EmpresaRow]
    ) -> None:
        validas = {
            e.numemp for e in empresas if not e.fecbaj and not e.desact
        }
        self._validas = validas
        # alias normalizado -> numemp (de TODA la tabla, valida o no, para
        # distinguir «ese alias es de una empresa que ya no vale»).
        self._alias: list[tuple[str, int]] = []
        for numemp, textos in alias.items():
            if numemp not in validas:
                logger.warning(
                    "[empresa-membrete] la tabla de alias trae la empresa %s, "
                    "que no esta en auxemp o esta de baja o desactivada: sus "
                    "alias no casaran.", numemp,
                )
            for texto in textos:
                self._alias.append((tm.normalize(texto), numemp))

    def resolver(self, texto: str | None) -> tuple[int | None, str]:
        """`(numemp, "membrete")` o `(None, motivo)` con motivo `sin_texto`,
        `sin_alias`, `varias` o `empresa_no_valida`."""
        normal = tm.normalize(texto)
        if not normal:
            return None, "sin_texto"
        rodeado = f" {normal} "
        encontradas = {
            numemp for alias, numemp in self._alias
            if f" {alias} " in rodeado
        }
        validas = encontradas & self._validas
        if len(validas) == 1:
            (numemp,) = validas
            return numemp, "membrete"
        if validas:
            motivo = "varias"
        elif encontradas:
            motivo = "empresa_no_valida"
        else:
            motivo = "sin_alias"
        logger.info(
            "[empresa-membrete] empresa del membrete desconocida (%s): "
            "texto leido=%r", motivo, texto,
        )
        return None, motivo
