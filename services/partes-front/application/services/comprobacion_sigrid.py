# application/services/comprobacion_sigrid.py
"""F-024 · ¿Siguen en Sigrid las lineas que el portal da por registradas?

Administracion puede borrar en Sigrid lineas que escribio sv5. El portal
lo detecta al abrir la vista de una obra o de una persona (en segundo
plano, desde el navegador) o con el boton «Comprobar en Sigrid»:

  vista/boton -> POST /api/sigrid/comprobar -> ComprobacionSigrid
     -> RegistroComprobaciones (antimartilleo por id, R19)
     -> sv5 /api/registro/comprobar (solo lectura, lotes de 500)
     -> repositorio.aplicar_comprobacion_sigrid (CAS por linea)

sv4 no lee Sigrid ni conoce el formato del `synckey`: eso es de sv5.
"""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RegistroComprobaciones:
    """Antimartilleo (R19): un id comprobado o EN CURSO no vuelve a sv5
    sin `forzar` hasta pasados `ttl_s` segundos en este proceso.

    Se sella al RESERVAR, no al terminar: asi un id en curso no se envia
    dos veces y un lote fallido no se reintenta en cada recarga contra un
    sv5 caido. Seguro entre hilos; purga las entradas caducadas en cada
    reserva para no crecer sin limite.
    """

    def __init__(self, *, ttl_s: float,
                 reloj: Callable[[], float] = time.monotonic) -> None:
        self._ttl = float(ttl_s)
        self._reloj = reloj
        self._lock = threading.Lock()
        self._sellos: dict[int, float] = {}

    def reservar(self, ids: Iterable[int], *, forzar: bool) -> list[int]:
        """Los ids que hay que enviar a sv5 (en el orden recibido, sin
        repetir); quedan sellados con la hora de ahora."""
        with self._lock:
            ahora = self._reloj()
            self._sellos = {i: t for i, t in self._sellos.items()
                            if ahora - t < self._ttl}
            nuevos = [i for i in dict.fromkeys(int(x) for x in ids)
                      if forzar or i not in self._sellos]
            for i in nuevos:
                self._sellos[i] = ahora
            return nuevos

    def vigentes(self) -> int:
        """Ids sellados ahora mismo (diagnostico y tests)."""
        with self._lock:
            return len(self._sellos)


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class ComprobacionSigrid:
    """Comprueba en Sigrid (via sv5) las lineas `registrado` de unos ids.

    Un lote solo se aplica si sv5 responde `ok` con un veredicto por cada
    linea enviada; si no, ese lote no cambia nada y la comprobacion SE PARA
    (R14): lo que no se envio queda como estaba y el TTL evita reintentar
    en cada recarga contra un sv5 caido.
    """

    def __init__(self, *, repository, transfer_client, lote: int,
                 timeout_s: float, recientes: RegistroComprobaciones,
                 reloj_utc: Callable[[], datetime] = _ahora_utc) -> None:
        self._repo = repository
        self._sv5 = transfer_client
        self._lote = int(lote)
        self._timeout = float(timeout_s)
        self._recientes = recientes
        self._reloj_utc = reloj_utc

    def comprobar_ids(self, registro_ids: list[int], *, origen: str,
                      forzar: bool = False) -> dict[str, Any]:
        candidatas = self._repo.registrados_para_comprobar(registro_ids)
        por_id = {int(c["registro_id"]): c for c in candidatas}
        reservadas = self._recientes.reservar(list(por_id), forzar=forzar)
        res: dict[str, Any] = {
            "ok": True, "comprobadas": 0,
            "recientes": len(por_id) - len(reservadas),
            "borradas": 0, "borradas_ids": [], "actualizadas": 0,
            "sin_synckey": 0, "con_diferencias": [], "fallidos": 0,
        }
        for i in range(0, len(reservadas), self._lote):
            trozo = reservadas[i:i + self._lote]
            try:
                resp = self._sv5.comprobar(
                    {"lineas": [por_id[r] for r in trozo]},
                    timeout_s=self._timeout)
            except Exception as exc:  # noqa: BLE001
                resp = {"ok": False, "error": f"error llamando a sv5: {exc}"}
            veredictos = {int(v["registro_id"]): v
                          for v in (resp.get("veredictos") or [])
                          if isinstance(v, dict)
                          and v.get("registro_id") is not None}
            faltan = [r for r in trozo if r not in veredictos]
            if not resp.get("ok") or faltan:
                res["ok"] = False
                res["fallidos"] = len(reservadas) - i
                res["error"] = (resp.get("error") if not resp.get("ok")
                                else f"sv5 no dio veredicto de {len(faltan)} "
                                     "linea(s)") or "sv5 no respondio ok"
                break
            aplicado = self._repo.aplicar_comprobacion_sigrid(
                [veredictos[r] for r in trozo],
                {r: por_id[r]["hmores_ide"] for r in trozo},
                self._reloj_utc().isoformat())
            res["comprobadas"] += len(trozo)
            res["borradas"] += len(aplicado["borradas"])
            res["borradas_ids"].extend(aplicado["borradas"])
            res["actualizadas"] += len(aplicado["actualizadas"])
            for r in trozo:
                v = veredictos[r]
                if v.get("sin_synckey"):
                    res["sin_synckey"] += 1
                if v.get("diferencias"):
                    res["con_diferencias"].append(
                        {"registro_id": r, "diferencias": v["diferencias"]})
        logger.info(
            "[comprobacion-sigrid] origen=%s forzar=%s pedidas=%s "
            "registrado=%s recientes=%s comprobadas=%s borradas=%s "
            "actualizadas=%s sin_synckey=%s con_diferencias=%s fallidos=%s "
            "ok=%s", origen, forzar, len(set(registro_ids)), len(por_id),
            res["recientes"], res["comprobadas"], res["borradas"],
            res["actualizadas"], res["sin_synckey"],
            len(res["con_diferencias"]), res["fallidos"], res["ok"])
        return res
