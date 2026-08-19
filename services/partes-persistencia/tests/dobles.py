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


def es_laborable_fake(
    no_laborables: object = (),
    *,
    registro: list[str] | None = None,
    finde_laborable: bool = False,
) -> Callable[[Any], bool]:
    """`es_laborable(date) -> bool` para el resolutor de jornada (F-015).

    El resolutor recibe el calendario ya LIGADO al DNI como callable, asi
    que en sus tests no hace falta ni puerto ni doble de clase: una
    lista de fechas ISO no laborables basta. `registro`, si se pasa,
    apunta cada fecha consultada (para comprobar que no se pregunta de
    mas). Con `finde_laborable` se simula la situacion sin calendario
    cableado (D11), donde sabado y domingo son dias como los demas.
    """
    fuera = {str(f) for f in no_laborables}

    def _es_laborable(d) -> bool:
        if registro is not None:
            registro.append(d.isoformat())
        if not finde_laborable and d.weekday() >= 5:
            return False
        return d.isoformat() not in fuera

    return _es_laborable


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
             document_id: str = "doc-1", obra_ide: int | None = 10,
             sigrid_estado: str | None = None,
             doc_approved: bool = False) -> dict:
    """Un registro tal como lo devuelve `fetch_registros_para_recurso`.

    `sigrid_estado` y `doc_approved` son lo que F-015 anadio a la lectura
    para saber que lineas estan CONGELADAS (F-004): las que ya viajaron a
    Sigrid o cuyo parte esta aprobado.
    """
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
        "sigrid_estado": sigrid_estado,
        "doc_approved": doc_approved,
    }


# --------------------------- BBDD en memoria ---------------------------- #

class FabricaSesionSqlite:
    """`SessionFactory` equivalente sobre SQLite en memoria.

    Misma interfaz que la de produccion (`engine` + `create_session`) y el
    MISMO ORM, asi que el repositorio se ejercita de verdad. Vale para el
    DML (leer registros, revertir extras); el DDL de arranque NO se prueba
    aqui porque SQLite no admite `ADD COLUMN IF NOT EXISTS` (ver
    `test_f010_r7_initialize_sv3.py`).
    """

    def __init__(self) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from infrastructure.database.orm_models import Base

        self.engine = create_engine(
            "sqlite://", future=True, poolclass=StaticPool,
            connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self._sessionmaker = sessionmaker(
            bind=self.engine, expire_on_commit=False, future=True)

    def create_session(self):
        return self._sessionmaker()


def sembrar_lineas(fabrica, lineas: list[dict], *, document_id: str = "doc-1",
                   aprobado: bool = False, fecha: str = "2026-03-20",
                   obra_ide: int | None = 10) -> list[int]:
    """Un parte con esas lineas en la base de memoria.

    Cada linea admite `horas`, `horas_orig`, `tipo` (`normal`/`extra`),
    `extra_auto` y `estado` (`sigrid_estado`).
    """
    from infrastructure.database.orm_models import (
        ParteDocumentOrm,
        ParteRegistroOrm,
    )

    ahora = "2026-03-20T08:00:00+00:00"
    fint = int(fecha.replace("-", ""))
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=document_id, source_filename="parte.pdf",
            source_mime_type="application/pdf",
            source_sha256="sha" + document_id, fecha=fecha, fecha_int=fint,
            created_at_utc=ahora, obra_ide=obra_ide, obra_codigo="0100",
            obra_nombre="Obra Uno", approved=aprobado))
        ids: list[int] = []
        for i, linea in enumerate(lineas):
            reg = ParteRegistroOrm(
                document_id=document_id, line_index=i, fecha=fecha,
                fecha_int=fint, obra_ide=obra_ide, obra_codigo="0100",
                obra_nombre="Obra Uno", empleado_dni="12345678Z",
                empleado_reside=501, tipo_hora=str(linea.get("tipo")
                                                  or "normal"),
                horas=linea.get("horas"), horas_orig=linea.get("horas_orig"),
                extra_auto=bool(linea.get("extra_auto")),
                sigrid_estado=linea.get("estado"),
                hora_ide=1, hora_codigo="HL01")
            s.add(reg)
            s.flush()
            ids.append(reg.id)
        s.commit()
    return ids


def estado_lineas(fabrica, ids: list[int]) -> dict[int, tuple]:
    """(existe, horas, horas_orig, extra_auto) de cada linea."""
    from infrastructure.database.orm_models import ParteRegistroOrm

    with fabrica.create_session() as s:
        out: dict[int, tuple] = {}
        for i in ids:
            r = s.get(ParteRegistroOrm, i)
            out[i] = ((False, None, None, None) if r is None
                      else (True, r.horas, r.horas_orig, r.extra_auto))
        return out


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


# ------------------------- excepciones de jornada ----------------------- #

class JornadasFake:
    """Doble del `JornadaEmpleadoPort` (F-015).

    `filas` son las excepciones que devuelve; `fallo`, la excepcion que
    lanza en su lugar (para ejercitar R17: la tabla caida no puede tumbar
    la conciliacion). `llamadas` cuenta las lecturas, que es como se
    comprueba que la tabla se lee UNA vez por pasada y no una por
    registro.
    """

    def __init__(self, filas=None, *, fallo: Exception | None = None) -> None:
        self.filas = list(filas or [])
        self.fallo = fallo
        self.llamadas = 0

    def fetch_jornadas(self):
        self.llamadas += 1
        if self.fallo is not None:
            raise self.fallo
        return list(self.filas)


def sembrar_jornadas(fabrica, filas: list[dict]) -> list[int]:
    """Filas de `empleado_jornada` en la base de memoria (F-015).

    Cada elemento admite `dni_norm`, `jornada_semanal`, `patron` (7 valores
    L..D), `desde`, `hasta`, `origen` e `is_active`.
    """
    from infrastructure.database.orm_models import EmpleadoJornadaOrm

    dias = ("h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom")
    ids: list[int] = []
    with fabrica.create_session() as s:
        for f in filas:
            patron = f.get("patron") or [None] * 7
            fila = EmpleadoJornadaOrm(
                dni_norm=f.get("dni_norm", "12345678Z"),
                jornada_semanal=f.get("jornada_semanal"),
                desde=f.get("desde", "2026-01-01"),
                hasta=f.get("hasta"),
                origen=f.get("origen", "manual"),
                nota=f.get("nota"),
                is_active=bool(f.get("is_active", True)),
                created_at_utc="2026-08-19T00:00:00Z",
                **dict(zip(dias, patron)),
            )
            s.add(fila)
            s.flush()
            ids.append(fila.id)
        s.commit()
    return ids
