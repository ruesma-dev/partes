# tests/dobles.py
"""Dobles de la suite del portal (sv4). Ni red ni PostgreSQL.

Dos familias:

  - **Storage**: fakes de `QueueServiceClient` / `BlobServiceClient` que
    se inyectan por monkeypatch del simbolo importado en el modulo
    adaptador. Asi los tests ejercitan los adaptadores REALES de
    `infrastructure/azure/` sin que el codigo de produccion lleve ningun
    parametro que exista solo para los tests.
  - **BBDD**: SQLite en memoria con el MISMO ORM que usa PostgreSQL, para
    poder probar el marcado de las columnas `sigrid_*` de verdad.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace

from infrastructure.database.orm_models import (
    Base,
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ------------------------------- Storage ------------------------------- #

class MensajeFake:
    """Equivalente al `QueueMessage` del SDK (solo lo que usamos)."""

    def __init__(self, content: str, *, dequeue_count: int = 1,
                 id: str = "m1") -> None:
        self.content = content
        self.dequeue_count = dequeue_count
        self.id = id
        self.pop_receipt = f"pr-{id}"


def mensaje_json(payload: dict, *, dequeue_count: int = 1,
                 id: str = "m1") -> MensajeFake:
    return MensajeFake(json.dumps(payload, ensure_ascii=False),
                       dequeue_count=dequeue_count, id=id)


class QueueClientFake:
    """Cola en memoria.

    `rondas` es la secuencia de lotes que devolvera `receive_messages`. Al
    agotarse llama a `on_agotado`, con lo que los tests detienen el bucle
    de consumo de forma determinista, sin dormir ni mirar el reloj.
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self.rondas: list[list[MensajeFake]] = []
        self.enviados: list[str] = []
        self.borrados: list[str] = []
        self.on_agotado: Callable[[], None] | None = None
        self.recepciones: list[dict] = []
        self.fallo_delete = False
        self.fallo_send = False
        self.mensajes_aprox = 0

    def send_message(self, content: str):
        if self.fallo_send:
            raise RuntimeError(f"send KO en {self.nombre}")
        self.enviados.append(content)
        return SimpleNamespace(id=f"{self.nombre}-{len(self.enviados)}")

    def receive_messages(self, messages_per_page: int = 1,
                         visibility_timeout: int | None = None):
        # Se guardan los argumentos: el tamano de lote y el visibility no
        # son decorativos (uno acota lo que se pierde ante SIGTERM, el
        # otro cuanto tarda en reaparecer un mensaje fallido).
        self.recepciones.append({"messages_per_page": messages_per_page,
                                 "visibility_timeout": visibility_timeout})
        if self.rondas:
            return list(self.rondas.pop(0))
        if self.on_agotado is not None:
            self.on_agotado()
        return []

    def delete_message(self, msg, pop_receipt: str | None = None):
        if self.fallo_delete:
            raise RuntimeError(f"delete KO en {self.nombre}")
        self.borrados.append(getattr(msg, "id", str(msg)))

    def get_queue_properties(self):
        return SimpleNamespace(approximate_message_count=self.mensajes_aprox)

    @property
    def payloads_enviados(self) -> list[dict]:
        return [json.loads(c) for c in self.enviados]

    def cargar(self, mensajes: list[MensajeFake]) -> None:
        """Deja los mensajes disponibles de uno en uno (como la cola real)."""
        self.rondas = [[m] for m in mensajes]


class QueueServiceClientFake:
    def __init__(self) -> None:
        self.colas: dict[str, QueueClientFake] = {}
        self.creadas: list[str] = []

    def get_queue_client(self, nombre: str) -> QueueClientFake:
        return self.colas.setdefault(nombre, QueueClientFake(nombre))

    def create_queue(self, nombre: str) -> None:
        self.creadas.append(nombre)
        self.colas.setdefault(nombre, QueueClientFake(nombre))


class BlobClientFake:
    def __init__(self, almacen: dict, clave: tuple[str, str]) -> None:
        self._almacen = almacen
        self._clave = clave

    def upload_blob(self, data, overwrite: bool = False,
                    content_settings=None) -> None:
        if not overwrite and self._clave in self._almacen:
            # Igual que el SDK real: sin overwrite, subir dos veces el
            # mismo blob es un error.
            from azure.core.exceptions import ResourceExistsError
            raise ResourceExistsError(f"blob ya existe: {self._clave}")
        self._almacen[self._clave] = data

    def download_blob(self):
        if self._clave not in self._almacen:
            from azure.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"blob inexistente: {self._clave}")
        datos = self._almacen[self._clave]
        return SimpleNamespace(readall=lambda: datos)


class BlobServiceClientFake:
    def __init__(self) -> None:
        self.almacen: dict[tuple[str, str], bytes] = {}
        self.contenedores: list[str] = []

    def get_blob_client(self, container: str, blob: str) -> BlobClientFake:
        return BlobClientFake(self.almacen, (container, blob))

    def create_container(self, nombre: str) -> None:
        self.contenedores.append(nombre)


def parchear_colas(monkeypatch, modulo, servicio: QueueServiceClientFake):
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "QueueServiceClient", _Factoria)
    return servicio


def parchear_blobs(monkeypatch, modulo, servicio: BlobServiceClientFake):
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "BlobServiceClient", _Factoria)
    return servicio


# --------------------------------- BBDD -------------------------------- #

class FabricaSesionSqlite:
    """`SessionFactory` equivalente sobre SQLite en memoria.

    Misma interfaz que la de produccion (`engine` + `create_session`) y el
    MISMO ORM, asi que el repositorio se ejercita de verdad. Se usa
    `StaticPool` con una unica conexion compartida para que la base viva
    mientras dure el test.
    """

    def __init__(self) -> None:
        from sqlalchemy.pool import StaticPool
        self.engine = create_engine(
            "sqlite://", future=True, poolclass=StaticPool,
            connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self._sessionmaker = sessionmaker(bind=self.engine,
                                          expire_on_commit=False, future=True)

    def create_session(self):
        return self._sessionmaker()


def sembrar_registros(fabrica: FabricaSesionSqlite, *,
                      cantidad: int = 2,
                      document_id: str = "doc-1") -> list[int]:
    """Crea un parte con `cantidad` registros y devuelve sus ids."""
    ahora = "2026-03-02T08:00:00+00:00"
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=document_id, source_filename="parte.pdf",
            source_mime_type="application/pdf", source_sha256="sha" + document_id,
            fecha="2026-03-02", fecha_int=20260302, created_at_utc=ahora,
            obra_ide=10, obra_codigo="0100", obra_nombre="Obra Uno"))
        ids: list[int] = []
        for i in range(cantidad):
            reg = ParteRegistroOrm(
                document_id=document_id, line_index=i, fecha="2026-03-02",
                fecha_int=20260302, obra_ide=10, obra_codigo="0100",
                obra_nombre="Obra Uno", empleado_dni=f"1234567{i}A",
                empleado_nombre=f"Trabajador {i}", recurso_ide=501 + i,
                tipo_hora="normal", horas=8.0, hora_ide=1, hora_codigo="HL01")
            s.add(reg)
            s.flush()
            ids.append(reg.id)
        s.commit()
    return ids


def sembrar_dias(
    fabrica: FabricaSesionSqlite,
    dias: list[dict],
    *,
    document_id: str = "doc-cal",
    empleado_ide: int = 77,
    empleado_dni: str = "12345678Z",
    empleado_nombre: str = "Pepe Perez",
    obra_ide: int = 10,
    obra_codigo: str = "0100",
) -> list[int]:
    """Siembra un trabajador con una linea por dia (F-003).

    Cada elemento de `dias` es `{"fecha": "YYYY-MM-DD", "horas": 6.0,
    "candef": 8.0, "tipo": "normal"}`. Sirve para las vistas que evaluan
    festivos y jornada incompleta, donde lo que importa es la fecha y las
    horas ordinarias de cada dia.
    """
    ahora = "2026-03-02T08:00:00+00:00"
    primera = dias[0]["fecha"] if dias else "2026-01-01"
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=document_id, source_filename="parte.pdf",
            source_mime_type="application/pdf",
            source_sha256="sha" + document_id,
            fecha=primera, fecha_int=int(primera.replace("-", "")),
            created_at_utc=ahora, obra_ide=obra_ide, obra_codigo=obra_codigo,
            obra_nombre="Obra Uno"))
        ids: list[int] = []
        for i, d in enumerate(dias):
            fecha = str(d["fecha"])
            reg = ParteRegistroOrm(
                document_id=document_id, line_index=i, fecha=fecha,
                fecha_int=int(fecha.replace("-", "")), obra_ide=obra_ide,
                obra_codigo=obra_codigo, obra_nombre="Obra Uno",
                empleado_ide=empleado_ide, empleado_dni=empleado_dni,
                empleado_nombre=empleado_nombre,
                trabajador_nombre_leido=empleado_nombre,
                recurso_ide=501, recurso_cif=empleado_dni,
                tipo_hora=str(d.get("tipo") or "normal"),
                horas=float(d.get("horas", 8.0)),
                hora_candef=d.get("candef"),
                hora_ide=1, hora_codigo="HL01")
            s.add(reg)
            s.flush()
            ids.append(reg.id)
        s.commit()
    return ids


def estados_sigrid(fabrica: FabricaSesionSqlite,
                   ids: list[int]) -> dict[int, tuple]:
    """Estado + motivo + ides de Sigrid de cada registro."""
    with fabrica.create_session() as s:
        out = {}
        for i in ids:
            r = s.get(ParteRegistroOrm, i)
            out[i] = (r.sigrid_estado, r.sigrid_motivo, r.sigrid_hmoide,
                      r.sigrid_hmores_ide, r.sigrid_parte_cod)
        return out
