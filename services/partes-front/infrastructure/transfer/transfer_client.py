# infrastructure/transfer/transfer_client.py
"""Cliente del microservicio partes-transfer (sv5).

sv4 NUNCA escribe en Sigrid: construye las lineas a registrar y delega en
este servicio, que aplica las reglas y escribe (o avisa de conflictos).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TransferClient:
    def __init__(self, *, base_url: str, timeout_s: float = 120.0) -> None:
        if not base_url:
            raise ValueError("TransferClient requiere base_url")
        self._base = base_url.rstrip("/")
        self._timeout = float(timeout_s)

    def _post(self, ruta: str, payload: dict[str, Any],
              timeout_s: float | None = None) -> dict[str, Any]:
        url = f"{self._base}{ruta}"
        plazo = self._timeout if timeout_s is None else float(timeout_s)
        try:
            r = httpx.post(url, json=payload, timeout=plazo)
        except httpx.ConnectError:
            # El servicio no esta arrancado / puerto cerrado: mensaje util
            # en la pantalla en vez de un 500 con traceback.
            logger.warning("[transfer] sin conexion con %s", url)
            return {"ok": False, "error": (
                f"no se puede conectar con el servicio de registro "
                f"(partes-transfer) en {self._base}. Arrancalo con "
                f"'python main.py' en el proyecto partes-transfer.")}
        except httpx.TimeoutException:
            logger.warning("[transfer] timeout en %s", url)
            return {"ok": False, "error": (
                f"el servicio de registro no respondio en "
                f"{plazo:.0f}s ({self._base}).")}
        except httpx.HTTPError as exc:
            logger.warning("[transfer] error de red en %s: %s", url, exc)
            return {"ok": False, "error": f"error de red hacia {self._base}: {exc}"}
        if r.status_code >= 400:
            logger.warning("[transfer] %s HTTP %s: %s", ruta, r.status_code,
                           r.text[:300])
            try:
                body = r.json()
            except Exception:  # noqa: BLE001
                body = {}
            return {"ok": False,
                    "error": body.get("error") or f"HTTP {r.status_code}"}
        return r.json()

    def preflight(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/api/registro/preflight", payload)

    def ejecutar(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/api/registro/ejecutar", payload)

    def comprobar(self, payload: dict[str, Any], *,
                  timeout_s: float) -> dict[str, Any]:
        """F-024: siguen en Sigrid estas lineas? Solo lectura en sv5. Con
        su propio plazo, mas corto que el del registro: quien pregunta es
        una vista que espera."""
        return self._post("/api/registro/comprobar", payload,
                          timeout_s=timeout_s)

    # ----------------------- F-046: reajuste ----------------------- #
    def _post_reajuste(self, ruta: str, payload: dict[str, Any],
                       timeout_s: float | None = None) -> dict[str, Any]:
        """Como `_post`, pero distingue «sv5 dijo que no» (nada escrito) de
        «no se sabe» (`sin_respuesta: True`, R34): timeout, error de red a
        mitad o un 5xx (sv5 contesta 502 cuando no puede decir que paso
        en Sigrid). Sin conexion la peticion no llego a salir: es un no."""
        url = f"{self._base}{ruta}"
        plazo = self._timeout if timeout_s is None else float(timeout_s)
        try:
            r = httpx.post(url, json=payload, timeout=plazo)
        except httpx.ConnectError:
            logger.warning("[transfer] sin conexion con %s", url)
            return {"ok": False, "error": (
                f"no se puede conectar con el servicio de registro "
                f"(partes-transfer) en {self._base}")}
        except httpx.TimeoutException:
            logger.warning("[transfer] timeout en %s", url)
            return {"ok": False, "sin_respuesta": True, "error": (
                f"el servicio de registro no respondio en {plazo:.0f}s: "
                f"no se sabe si el reajuste llego a Sigrid")}
        except httpx.HTTPError as exc:
            logger.warning("[transfer] error de red en %s: %s", url, exc)
            return {"ok": False, "sin_respuesta": True,
                    "error": f"error de red hacia {self._base}: {exc}"}
        if r.status_code >= 400:
            logger.warning("[transfer] %s HTTP %s: %s", ruta, r.status_code,
                           r.text[:300])
            try:
                body = r.json()
            except Exception:  # noqa: BLE001
                body = {}
            out = {"ok": False,
                   "error": body.get("error") or f"HTTP {r.status_code}"}
            if r.status_code >= 500:
                out["sin_respuesta"] = True
            return out
        return r.json()

    def reajuste_comprobar(self, payload: dict[str, Any], *,
                           timeout_s: float | None = None
                           ) -> dict[str, Any]:
        """F-046 (R30): se pueden reajustar estas lineas? Solo lectura."""
        return self._post_reajuste("/api/reajuste/comprobar", payload,
                                   timeout_s=timeout_s)

    def reajuste_ejecutar(self, payload: dict[str, Any]) -> dict[str, Any]:
        """F-046 (R33): el reajuste en Sigrid (HTTP sincrono, nunca cola)."""
        return self._post_reajuste("/api/reajuste/ejecutar", payload)

    # ------------------ F-056: franquicia de extras ------------------ #
    def franquicia_recursos(self, recurso_ides: list[int], *,
                            timeout_s: float | None = None
                            ) -> dict[str, Any]:
        """R43: la franquicia de esos recursos (solo lectura en sv5, UNA
        llamada por preflight o vista). Un fallo, un 404 de un sv5 anterior
        o un timeout es `ok: false` y el portal avisa (R44)."""
        return self._post("/api/franquicia/recursos",
                          {"recurso_ides": [int(i) for i in recurso_ides]},
                          timeout_s=timeout_s)

    def franquicia_comprobar(self, payload: dict[str, Any], *,
                             timeout_s: float | None = None
                             ) -> dict[str, Any]:
        """R9, R14: E y A estimados (solo lectura en sv5)."""
        return self._post("/api/franquicia/comprobar", payload,
                          timeout_s=timeout_s)

    def franquicia_ejecutar(self, payload: dict[str, Any]) -> dict[str, Any]:
        """R17, R19: la linea de ajuste en Sigrid (HTTP sincrono, nunca
        cola). Distingue «no se sabe» (`sin_respuesta`) como el reajuste:
        el reintento es seguro (sv5 es idempotente por la synckey)."""
        return self._post_reajuste("/api/franquicia/ejecutar", payload)
