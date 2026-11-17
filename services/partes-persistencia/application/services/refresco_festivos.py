# application/services/refresco_festivos.py
"""Refresco de los festivos de cada trabajador al ingerir un parte (F-032).

sv3 es el UNICO que pide festivos a sesame-api, y solo aqui: al ingerir un
parte nuevo, para cada DNI distinto de sus lineas y cada ano de la semana
ISO de su fecha (design §5.4, DA15). Las pasadas de conciliacion y los
recalculos leen la tabla `festivos_trabajador`, nunca a Sesame (R14).

Por cada (DNI, ano), `cliente.festivos(dni, ano)`:

  - lista con al menos `minimo` festivos de ese ano ⇒ upsert con
    `leido_en_utc` y `al_guardar()` (invalida la cache de la tabla, R15);
  - ``None`` (404: Sesame no conoce el DNI) ⇒ `sin_calendario`: no se
    escribe ni se borra nada (R5, DA19 = B);
  - excepcion, plazo o lista incompleta ⇒ fallo: con fila previa, esta se
    conserva (`conservadas`, R7); sin ella, `sin_dato` (R8), que el
    pipeline convierte en `review_required`.

Nunca pide el calendario por defecto ni lanza (R9). Sus logs dan recuentos
y anos, nunca DNIs (R3): ni siquiera el texto de una excepcion, que podria
traer el DNI en la URL o en el cuerpo de error.

`cliente` y `repositorio` van por duck-typing (`festivos(dni, ano)`;
`leer_todas()` y `guardar(fila)`).
"""
from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from application.services.festivos_guardados import FilaFestivos, del_ano

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[festivos]"


@dataclass(frozen=True)
class ResultadoRefresco:
    """Recuento del refresco de un parte, por (DNI, ano)."""
    guardadas: int
    conservadas: int
    sin_calendario: int
    sin_dato: int


def anos_de_semana(fecha: _dt.date | str) -> set[int]:
    """Anos del lunes y del domingo de la semana ISO de ``fecha``."""
    if isinstance(fecha, str):
        fecha = _dt.date.fromisoformat(fecha[:10])
    lunes = fecha - _dt.timedelta(days=fecha.weekday())
    domingo = lunes + _dt.timedelta(days=6)
    return {lunes.year, domingo.year}


class RefrescoFestivos:
    def __init__(
        self,
        *,
        cliente: Any,
        repositorio: Any,
        minimo: int,
        ahora_utc: Callable[[], _dt.datetime],
        al_guardar: Callable[[], None] = lambda: None,
    ) -> None:
        self._cliente = cliente
        self._repositorio = repositorio
        self._minimo = int(minimo)
        self._ahora_utc = ahora_utc
        self._al_guardar = al_guardar

    def refrescar(self, dnis: Iterable[str | None],
                  anos: Iterable[int]) -> ResultadoRefresco:
        guardadas = conservadas = sin_calendario = sin_dato = 0
        previas: dict | None = None
        claves = sorted({(d, int(a)) for d in dnis if d for a in anos})
        for dni, ano in claves:
            estado = self._uno(dni, ano)
            if estado == "guardada":
                guardadas += 1
                continue
            if estado == "sin_calendario":
                sin_calendario += 1
                continue
            if previas is None:
                previas = self._previas()
            if (dni, ano) in previas:
                conservadas += 1
            else:
                sin_dato += 1
        resultado = ResultadoRefresco(guardadas, conservadas, sin_calendario,
                                      sin_dato)
        logger.info(
            "%s refresco guardadas=%s conservadas=%s sin_calendario=%s "
            "sin_dato=%s", _LOG_PREFIX, guardadas, conservadas,
            sin_calendario, sin_dato,
        )
        return resultado

    # ------------------------------------------------------------- #
    def _uno(self, dni: str, ano: int) -> str:
        """``guardada``, ``sin_calendario`` o ``fallo`` para ese (DNI, ano)."""
        try:
            lista = self._cliente.festivos(dni, ano)
        except Exception as exc:  # noqa: BLE001 - nunca lanza (R9)
            logger.warning("%s Sesame fallo en un DNI del ano %s: %s",
                           _LOG_PREFIX, ano, type(exc).__name__)
            return "fallo"
        if lista is None:
            return "sin_calendario"
        try:
            festivos = del_ano(((f.fecha, f.nombre) for f in lista), ano)
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s respuesta ilegible de Sesame en el ano %s: %s",
                           _LOG_PREFIX, ano, type(exc).__name__)
            return "fallo"
        if len(festivos) < self._minimo:
            logger.warning(
                "%s calendario incompleto en el ano %s: %s festivo(s), "
                "minimo %s; no se guarda", _LOG_PREFIX, ano, len(festivos),
                self._minimo,
            )
            return "fallo"
        try:
            leido = self._ahora_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._repositorio.guardar(FilaFestivos(
                dni_norm=dni, ano=ano, festivos=festivos, leido_en_utc=leido))
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s no se pudo guardar una fila del ano %s: %s",
                           _LOG_PREFIX, ano, type(exc).__name__)
            return "fallo"
        try:
            self._al_guardar()
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s al_guardar fallo: %s", _LOG_PREFIX,
                           type(exc).__name__)
        return "guardada"

    def _previas(self) -> dict:
        """Claves con fila; si la tabla no se puede leer, ninguna (⇒ R8)."""
        try:
            return dict(self._repositorio.leer_todas())
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s no se pudo leer la tabla de festivos: %s",
                           _LOG_PREFIX, type(exc).__name__)
            return {}
