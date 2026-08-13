# tests/test_f002_workers.py
"""F-002 · pool de consumidores de `q-transfer` en sv5 (R18, R21, R22).

Lo que se demuestra aqui es el reparto de trabajo entre fases: varias
peticiones PREPARAN a la vez (fase de datos maestros) mientras la fase de
escritura sigue pasando de una en una por el lock. El solapamiento se
comprueba con una barrera, no con relojes: si las preparaciones no
coincidieran en el tiempo, la barrera expiraria y el test fallaria.
"""
from __future__ import annotations

import json
import threading

from application.pipelines.registro_pipeline import RegistroPipeline
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from interface_adapters.queue.transfer_consumer import (
    arrancar_workers_transfer,
    construir_handler_transfer,
)
from tests.dobles import (
    BlobServiceClientFake,
    QueueServiceClientFake,
    SettingsFake,
    parchear_blobs,
    parchear_colas,
)
from tests.test_f002_pipeline_fases import _sigrid


def _peticion(pid: str, *, registro_id: int, recurso_ide: int = 501,
              dia: int = 2) -> dict:
    return {
        "peticion_id": pid,
        "usuario": "ana",
        "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
        "lineas": [{"registro_id": registro_id, "fecha_int": 20260300 + dia,
                    "recurso_ide": recurso_ide, "tipo_hora": "normal",
                    "horas": 8.0}],
        "pisar_claves": [],
    }


class Banco:
    """Un handler compartido y varias peticiones en el blob."""

    def __init__(self, monkeypatch, cli, peticiones: dict[str, dict]):
        self.svc_cola = parchear_colas(monkeypatch, mod_cola,
                                       QueueServiceClientFake())
        parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
        self.blob = BlobCliente(connection_string="UseDevelopmentStorage=true")
        self.cola = ColaCliente(connection_string="UseDevelopmentStorage=true",
                                poll_interval_s=0)
        self.settings = SettingsFake()
        self.pipeline = RegistroPipeline(cliente=cli, settings=self.settings)
        self.handler = construir_handler_transfer(
            pipeline=self.pipeline, blob=self.blob, cola=self.cola,
            settings=self.settings)
        for pid, cuerpo in peticiones.items():
            self.blob.subir("transfer", f"peticiones/{pid}.json",
                            json.dumps(cuerpo).encode("utf-8"))

    def procesar_en_paralelo(self, ids: list[str]) -> list[BaseException]:
        errores: list[BaseException] = []

        def _uno(pid: str):
            try:
                self.handler({"peticion_id": pid,
                              "blob": f"peticiones/{pid}.json"})
            except BaseException as exc:  # noqa: BLE001
                errores.append(exc)

        hilos = [threading.Thread(target=_uno, args=(p,)) for p in ids]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(15)
        return errores

    @property
    def publicados(self) -> list[str]:
        return [m["peticion_id"] for m in self.svc_cola.get_queue_client(
            "q-transfer-result").payloads_enviados]


def test_f002_r18_las_preparaciones_de_peticiones_distintas_solapan():
    """R18: tres peticiones coinciden en la fase de preparacion."""
    cli = _sigrid()
    cli.barrera = threading.Barrier(3, timeout=10)
    import pytest
    monkeypatch = pytest.MonkeyPatch()
    try:
        banco = Banco(monkeypatch, cli, {
            f"p{i}": _peticion(f"p{i}", registro_id=i, dia=i)
            for i in (1, 2, 3)})
        errores = banco.procesar_en_paralelo(["p1", "p2", "p3"])
    finally:
        monkeypatch.undo()

    # Si no hubieran solapado, la barrera habria expirado (BrokenBarrier).
    assert errores == []
    assert sorted(banco.publicados) == ["p1", "p2", "p3"]
    # Y la escritura, pese al solapamiento, siguio siendo de una en una.
    assert cli.max_concurrencia.get("escribir") == 1
    assert len(cli.lineas) == 3


def test_f002_r19_la_escritura_no_solapa_aunque_la_preparacion_si(monkeypatch):
    """R19: el paralelismo se queda en la puerta del lock."""
    cli = _sigrid(latencia_escritura=0.05)
    cli.barrera = threading.Barrier(3, timeout=10)
    banco = Banco(monkeypatch, cli, {
        f"p{i}": _peticion(f"p{i}", registro_id=i, dia=i) for i in (1, 2, 3)})
    cli.vigilar_lock(banco.pipeline.lock)

    assert banco.procesar_en_paralelo(["p1", "p2", "p3"]) == []
    assert cli.max_concurrencia.get("escribir") == 1
    assert cli.max_concurrencia.get("horas_de_recursos") == 3


def test_f002_r21_el_orden_de_publicacion_no_esta_garantizado(monkeypatch):
    """R21: la peticion lenta en preparar publica DESPUES de la rapida."""
    cli = _sigrid()
    cli.retardo_por_recurso = {501: 0.3}     # la lenta usa el recurso 501
    banco = Banco(monkeypatch, cli, {
        "lenta": _peticion("lenta", registro_id=1, recurso_ide=501, dia=2),
        "rapida": _peticion("rapida", registro_id=2, recurso_ide=502, dia=3),
    })

    # 'lenta' se encola PRIMERO y aun asi publica la ultima.
    assert banco.procesar_en_paralelo(["lenta", "rapida"]) == []
    assert banco.publicados == ["rapida", "lenta"]


def test_f002_r22_el_fallo_de_una_peticion_no_afecta_a_las_demas(monkeypatch):
    """R22: una peticion rota no arrastra a las que van con ella."""
    cli = _sigrid()
    banco = Banco(monkeypatch, cli, {
        "p1": _peticion("p1", registro_id=1, dia=2),
        "p3": _peticion("p3", registro_id=3, dia=4),
    })
    # 'p2' no tiene blob: su handler relanza (fallo de infraestructura).
    errores = banco.procesar_en_paralelo(["p1", "p2", "p3"])

    assert len(errores) == 1
    assert sorted(banco.publicados) == ["p1", "p3"]
    assert len(cli.lineas) == 2


# --------------------------- arranque del pool -------------------------- #

class ColaEspia:
    """Sustituto de ColaCliente para observar el arranque de los hilos."""

    def __init__(self) -> None:
        self.consumida: str | None = None
        self.arrancado = threading.Event()
        self.suelta = threading.Event()
        self.reventar = False

    def consumir(self, nombre: str, handler) -> None:
        self.consumida = nombre
        self.arrancado.set()
        if self.reventar:
            raise RuntimeError("la cola se cayo al arrancar")
        self.suelta.wait(5)


def _arrancar(workers: int, colas: list, blobs: list, **kwargs):
    settings = SettingsFake(transfer_workers=workers)
    return arrancar_workers_transfer(
        pipeline=RegistroPipeline(cliente=_sigrid(), settings=settings),
        settings=settings,
        fabrica_cola=lambda: colas.pop(0),
        fabrica_blob=lambda: blobs.pop(0),
        **kwargs)


def test_f002_r18_el_pool_lanza_un_hilo_por_worker_con_sus_propios_clientes():
    """R18: N hilos daemon, cada uno con SU cliente (el SDK no se comparte)."""
    colas = [ColaEspia() for _ in range(3)]
    blobs = [object() for _ in range(3)]
    hilos = _arrancar(3, list(colas), blobs)
    try:
        for c in colas:
            assert c.arrancado.wait(5), "un worker no arranco"
        assert len(hilos) == 3
        assert all(h.daemon for h in hilos)
        assert all(c.consumida == "q-transfer" for c in colas)
        assert len({id(c) for c in colas}) == 3
    finally:
        for c in colas:
            c.suelta.set()
        for h in hilos:
            h.join(5)


def test_f002_r18_el_pool_nunca_baja_de_un_hilo():
    colas = [ColaEspia()]
    hilos = _arrancar(0, list(colas), [object()])
    try:
        assert colas[0].arrancado.wait(5)
        assert len(hilos) == 1
    finally:
        colas[0].suelta.set()
        for h in hilos:
            h.join(5)


def test_f002_r22_un_worker_que_revienta_no_tumba_a_los_demas():
    """R22: el pool sobrevive a la caida del bucle de un worker."""
    colas = [ColaEspia(), ColaEspia()]
    colas[0].reventar = True
    hilos = _arrancar(2, list(colas), [object(), object()])
    try:
        assert colas[0].arrancado.wait(5)
        assert colas[1].arrancado.wait(5)
        hilos[0].join(5)
        assert not hilos[0].is_alive()       # murio el suyo, no el proceso
        assert hilos[1].is_alive()           # el otro sigue consumiendo
    finally:
        for c in colas:
            c.suelta.set()
        for h in hilos:
            h.join(5)
