# application/services/obra_sigrid.py
"""F-058 · Consulta de obra en el momento contra sigrid-api (DA10 = B).

``ComprobadorObra.consultar`` pregunta, por cada página que lo necesite y sin
caché, si hay en Sigrid alguna obra con la clave del código leído (R7). Mide
la duración con un reloj monotónico y deja un INFO ``[obra-sigrid]`` con el
``document_id``, el resultado y los milisegundos, sin el código ni la clave
(R10): con esas líneas se miden los tiempos en Log Analytics (M4).

Nunca lanza: si la consulta falla, se trunca o pasa del tope
(``OBRA_EXISTE_TIMEOUT_S``), el resultado es «no se sabe» (``existe=None``)
con un WARNING que solo lleva el tipo del error (R9, DA12 = A).

No es la conciliación de sv3: no elige obra ni empresa (R11).
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from domain.models.clave_obra import clave_obra
from domain.ports.existencia_obra_port import ExistenciaObraPort

logger = logging.getLogger(__name__)

#: DA12 = A: tope por defecto de la consulta de obra, en segundos.
TIMEOUT_OBRA_DEFECTO_S = 5.0


@dataclass(frozen=True)
class ConsultaObra:
    #: ``True`` / ``False``, o ``None`` = «no se sabe» (clave vacía o fallo).
    existe: bool | None
    #: Duración de la consulta en ms (también si falla; 0 si no se hizo).
    ms: int
    #: Tipo de la excepción si falló; ``None`` si no.
    error_tipo: str | None


class ComprobadorObra:
    """Consulta de obra sin estado ni caché: una llamada por consulta."""

    def __init__(
        self,
        *,
        client: ExistenciaObraPort,
        timeout_s: float = TIMEOUT_OBRA_DEFECTO_S,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._client = client
        self._timeout_s = float(timeout_s)
        self._reloj = reloj

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    def consultar(self, codigo: object, *, document_id: str | None) -> ConsultaObra:
        clave = clave_obra(codigo)
        if not clave:
            return ConsultaObra(existe=None, ms=0, error_tipo=None)
        doc = document_id or "-"
        inicio = self._reloj()
        try:
            existe = bool(self._client.existe_obra(clave, timeout_s=self._timeout_s))
        except Exception as exc:  # noqa: BLE001 - R9: la consulta nunca tumba la extracción
            ms = self._ms_desde(inicio)
            tipo = type(exc).__name__
            logger.warning(
                "[obra-sigrid] document_id=%s resultado=error error=%s ms=%d",
                doc, tipo, ms,
            )
            return ConsultaObra(existe=None, ms=ms, error_tipo=tipo)
        ms = self._ms_desde(inicio)
        logger.info(
            "[obra-sigrid] document_id=%s resultado=%s ms=%d",
            doc, "existe" if existe else "no_existe", ms,
        )
        return ConsultaObra(existe=existe, ms=ms, error_tipo=None)

    def _ms_desde(self, inicio: float) -> int:
        return round((self._reloj() - inicio) * 1000)
