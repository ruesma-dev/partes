# tests/dobles.py
"""Dobles en memoria del SDK de Azure Storage para la suite de sv5.

Ningun test toca la red: estos fakes sustituyen a `QueueServiceClient` y
`BlobServiceClient` por monkeypatch del simbolo importado en el modulo
adaptador, de modo que el codigo de produccion no lleva ningun parametro
que exista solo para los tests.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Callable, Optional


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
    agotarse llama a `on_agotado` (el test la usa para detener el bucle de
    consumo de forma determinista, sin dormir ni depender de relojes).
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self.rondas: list[list[MensajeFake]] = []
        self.enviados: list[str] = []
        self.borrados: list[str] = []
        self.recibidos: list[str] = []
        self.on_agotado: Optional[Callable[[], None]] = None
        self.fallo_delete = False
        self.fallo_send = False
        self.mensajes_aprox = 0

    # -- productor --
    def send_message(self, content: str):
        if self.fallo_send:
            raise RuntimeError(f"send KO en {self.nombre}")
        self.enviados.append(content)
        return SimpleNamespace(id=f"{self.nombre}-{len(self.enviados)}")

    # -- consumidor --
    def receive_messages(self, messages_per_page: int = 1,
                         visibility_timeout: int | None = None):
        if self.rondas:
            lote = self.rondas.pop(0)
            self.recibidos.extend(m.id for m in lote)
            return list(lote)
        if self.on_agotado is not None:
            self.on_agotado()
        return []

    def delete_message(self, msg, pop_receipt: str | None = None):
        if self.fallo_delete:
            raise RuntimeError(f"delete KO en {self.nombre}")
        self.borrados.append(getattr(msg, "id", str(msg)))

    def get_queue_properties(self):
        return SimpleNamespace(approximate_message_count=self.mensajes_aprox)

    # -- ayuda para los tests --
    @property
    def payloads_enviados(self) -> list[dict]:
        return [json.loads(c) for c in self.enviados]


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
        self._almacen[self._clave] = data

    def download_blob(self):
        if self._clave not in self._almacen:
            raise KeyError(f"blob inexistente: {self._clave}")
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
    """Sustituye `QueueServiceClient` en el modulo adaptador indicado."""
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "QueueServiceClient", _Factoria)
    return servicio


def parchear_blobs(monkeypatch, modulo, servicio: BlobServiceClientFake):
    """Sustituye `BlobServiceClient` en el modulo adaptador indicado."""
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "BlobServiceClient", _Factoria)
    return servicio
