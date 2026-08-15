# tests/dobles.py
"""Dobles de la suite de persistencia (sv3). Ni red ni PostgreSQL.

  - `RepositorioFake`: lo que el `RecursoConciliador` le pide, en memoria,
    apuntando lo que se le manda escribir (splits, review_required...).
  - `CalendarioFake`: implementacion del `CalendarioLaboralPort` con una
    lista de dias no laborables y una senal de degradacion controlable,
    para ejercitar la regla de festivos sin Sesame ni JSON.
  - `transporte_json`: `httpx.MockTransport` que responde con lo que se le
    diga por ruta, para probar el cliente Sesame SIN red (R19).
"""
from __future__ import annotations

import json
from typing import Any, Callable

import httpx
from domain.models.sigrid_models import ReshorRow
from domain.ports.calendario_laboral_port import CalendarioLaboralPort

# ------------------------------ calendario ------------------------------ #

class CalendarioFake(CalendarioLaboralPort):
    """Calendario controlado por lista de fechas (y por DNI si hace falta).

    `no_laborables` puede ser un conjunto de fechas ISO (aplica a todos) o
    un dict `{dni: {fechas}}`. `degradados` son las fechas cuya resolucion
    se declara degradada a traves de `consumir_degradacion()`, la misma
    senal que ofrece `SesameCalendarioLaboral`.
    """

    def __init__(
        self,
        no_laborables: set[str] | dict[str | None, set[str]] | None = None,
        *,
        degradados: set[str] | None = None,
        con_senal: bool = True,
    ) -> None:
        self._no_lab = no_laborables or set()
        self._degradados = degradados or set()
        self._con_senal = con_senal
        self._flag = False
        self.consultas: list[tuple[str, str | None]] = []

    def es_no_laborable(
        self,
        fecha_iso: str,
        *,
        dni: str | None = None,
        localizacion: str | None = None,
        convenio: str | None = None,
    ) -> bool:
        self.consultas.append((fecha_iso, dni))
        self._flag = fecha_iso in self._degradados
        if isinstance(self._no_lab, dict):
            return fecha_iso in self._no_lab.get(dni, set())
        return fecha_iso in self._no_lab

    def consumir_degradacion(self) -> bool:
        if not self._con_senal:
            raise AttributeError("este doble no ofrece la senal")
        valor = self._flag
        self._flag = False
        return valor


class CalendarioSinSenal(CalendarioFake):
    """Calendario que NO ofrece `consumir_degradacion` (como el JSON)."""

    def __init__(self, no_laborables: set[str] | None = None) -> None:
        super().__init__(no_laborables, con_senal=False)

    consumir_degradacion = None  # type: ignore[assignment]


# ------------------------------ repositorio ----------------------------- #

class RepositorioFake:
    """Lo que el `RecursoConciliador` necesita del repositorio."""

    def __init__(self, registros: list[dict] | None = None) -> None:
        self.registros = registros or []
        self.splits: list[dict] = []
        self.matches: list[dict] = []
        self.revertidos = 0
        self.review_required: list[list[str]] = []

    def revert_extras_auto(self) -> int:
        self.revertidos += 1
        return 0

    def fetch_registros_para_recurso(self) -> list[dict]:
        return list(self.registros)

    def apply_recurso_matches(self, updates: list[dict]) -> int:
        self.matches.extend(updates)
        return len(updates)

    def apply_extras_splits(self, splits: list[dict]) -> int:
        self.splits.extend(splits)
        return len(splits)

    def marcar_review_required(self, document_ids) -> int:
        ids = sorted({str(d) for d in document_ids if d})
        self.review_required.append(ids)
        return len(ids)


class LookupFake:
    """Maestros de Sigrid en memoria (recursos, reshor y hmo por obra)."""

    def __init__(self, *, recursos=None, reshor=None, hmo=None) -> None:
        self._recursos = recursos or []
        self._reshor = reshor or []
        self._hmo = hmo or {}

    def fetch_recursos(self):
        return list(self._recursos)

    def fetch_reshor(self):
        return list(self._reshor)

    def fetch_hmo_obra(self, obra_ide: int):
        return list(self._hmo.get(obra_ide, []))


def reshor_par(reside: int, *, candef: float | None = 8.0,
               con_extra: bool = True) -> list[ReshorRow]:
    """Par (hora ordinaria, hora extra) del recurso, como lo da Sigrid."""
    filas = [ReshorRow(reside=reside, horide=100, cod="HL01",
                       res="Hora laborable", ext=0, candef=candef, pre=None)]
    if con_extra:
        filas.append(ReshorRow(reside=reside, horide=200, cod="HE01",
                               res="Hora extra", ext=1, candef=None, pre=None))
    return filas


def indice_reshor(reside: int, *, candef: float | None = 8.0,
                  con_extra: bool = True) -> dict[int, dict]:
    """El `reshor_idx` ya digerido que consume `_reclasificar_extras_jornada`."""
    filas = reshor_par(reside, candef=candef, con_extra=con_extra)
    return {
        reside: {
            "ord": filas[0],
            "ext": filas[1] if con_extra else None,
            "candef": candef,
            "incidencias": {},
        }
    }


def registro(registro_id: int, *, fecha_int: int, horas: float,
             tipo: str = "normal", dni: str | None = "12345678Z",
             document_id: str = "doc-1", obra_ide: int | None = 10) -> dict:
    """Un registro tal como lo devuelve `fetch_registros_para_recurso`."""
    return {
        "registro_id": registro_id,
        "document_id": document_id,
        "obra_ide": obra_ide,
        "empleado_ide": 1,
        "empleado_reside": 501,
        "empleado_dni": dni,
        "fecha_int": fecha_int,
        "tipo_hora": tipo,
        "hora_ide": None,
        "hora_codigo": None,
        "categoria": None,
        "horas": horas,
    }


# --------------------------------- HTTP --------------------------------- #

def transporte_json(
    rutas: dict[str, Any] | Callable[[httpx.Request], httpx.Response],
    *,
    registro_llamadas: list[httpx.Request] | None = None,
) -> httpx.MockTransport:
    """`MockTransport` que responde por ruta.

    `rutas` mapea `path` -> respuesta, que puede ser un dict (200 con ese
    JSON), una tupla `(status, dict)` o un `httpx.Response` ya hecho. Si
    la ruta no esta, responde 404 con el cuerpo de FastAPI.
    """

    def responder(request: httpx.Request) -> httpx.Response:
        if registro_llamadas is not None:
            registro_llamadas.append(request)
        if callable(rutas):
            return rutas(request)
        valor = rutas.get(request.url.path)
        if valor is None:
            return httpx.Response(404, json={"detail": "no encontrado"})
        if isinstance(valor, httpx.Response):
            return valor
        if isinstance(valor, tuple):
            status, cuerpo = valor
            if isinstance(cuerpo, str):
                return httpx.Response(status, text=cuerpo)
            return httpx.Response(status, json=cuerpo)
        return httpx.Response(200, content=json.dumps(valor).encode("utf-8"),
                              headers={"content-type": "application/json"})

    return httpx.MockTransport(responder)
