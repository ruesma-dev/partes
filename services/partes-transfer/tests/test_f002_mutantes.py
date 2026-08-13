# tests/test_f002_mutantes.py
"""F-002 · lo que la campaña de mutación destapó como no comprobado (sv5).

La suite pasaba con estas líneas cambiadas, y varias de ellas SÍ tienen
consecuencia real: un `max_dequeue` corrido en uno manda a la DLQ una
petición que aún tenía reintentos, un `overwrite` a False rompe el
reproceso de un mensaje reentregado, y un `got` mal puesto hace que el
worker duerma teniendo trabajo. Aquí se fija cada una.
"""
from __future__ import annotations

import json

import pytest
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure import credenciales as cred
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from interface_adapters.queue.transfer_consumer import (
    _resultado_fallido,
    arrancar_workers_transfer,
)
from tests.dobles import (
    BlobServiceClientFake,
    QueueServiceClientFake,
    mensaje_json,
    parchear_blobs,
    parchear_colas,
)

CS = "UseDevelopmentStorage=true"


def _cola(monkeypatch, **kwargs):
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    return ColaCliente(connection_string=CS, **kwargs), svc


# ----------------------- valores por defecto reales --------------------- #

def test_f002_r9_por_defecto_se_reintenta_5_veces_antes_de_poison(monkeypatch):
    """El 5 no es decorativo: es cuantas veces se reintenta una petición
    antes de darla por muerta. Un mensaje EN su ultimo intento todavia se
    procesa."""
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, dequeue_count=5,
                                 id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer", vistos.append)

    assert vistos == [{"peticion_id": "p1"}]          # se proceso
    assert svc.get_queue_client("q-transfer-poison").enviados == []


def test_f002_r9_en_el_intento_6_ya_va_a_poison(monkeypatch):
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, dequeue_count=6,
                                 id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer", vistos.append)

    assert vistos == []
    assert len(svc.get_queue_client("q-transfer-poison").enviados) == 1


def test_f002_el_visibility_por_defecto_son_600_s(monkeypatch):
    """Es el margen que tiene una petición para escribir en Sigrid antes
    de que el mensaje reaparezca y se procese por duplicado."""
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.on_agotado = cli.detener

    cli.consumir("q-transfer", lambda _p: None)

    assert cola.recepciones[0]["visibility_timeout"] == 600


def test_f002_se_recibe_un_mensaje_cada_vez(monkeypatch):
    """De uno en uno: el visibility corre por mensaje, y ante SIGTERM se
    pierde como mucho el que estuviera en curso."""
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.on_agotado = cli.detener

    cli.consumir("q-transfer", lambda _p: None)

    assert cola.recepciones[0]["messages_per_page"] == 1


def test_f002_el_sondeo_por_defecto_es_de_5_s(monkeypatch):
    """Y ocurre cuando la cola esta vacia y NO se ha pedido parar: al
    reves, un worker ocioso quemaria CPU y cuota de Storage."""
    esperas: list[tuple] = []
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    cli = ColaCliente(connection_string=CS)
    monkeypatch.setattr(
        mod_cola.time, "sleep",
        lambda s: esperas.append((s, cli._stop)) or cli.detener())
    svc.get_queue_client("q-transfer")

    cli.consumir("q-transfer", lambda _p: None)

    assert esperas == [(5, False)]


def test_f002_tras_procesar_un_mensaje_no_se_duerme(monkeypatch):
    """Habiendo trabajo, el worker encadena; dormir aqui seria latencia
    regalada en un lote grande."""
    esperas: list[float] = []
    monkeypatch.setattr(mod_cola.time, "sleep", esperas.append)
    cli, svc = _cola(monkeypatch)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]

    def _handler(_p):
        cli.detener()

    cli.consumir("q-transfer", _handler)

    assert esperas == []


# ------------------------- contenido de lo escrito ---------------------- #

def test_f002_los_mensajes_se_escriben_legibles(monkeypatch):
    """Sin `ensure_ascii=False`, un nombre con eñe queda como \\uXXXX y el
    mensaje deja de poder leerse de un vistazo en el portal de Azure."""
    cli, svc = _cola(monkeypatch)
    cli.enviar("q-transfer", {"peticion_id": "p1", "obra": "Peñón"})
    assert "Peñón" in svc.get_queue_client("q-transfer").enviados[0]


def test_f002_r8_el_blob_se_puede_reescribir(monkeypatch):
    """Una reentrega vuelve a publicar el resultado de la misma petición:
    sin `overwrite`, el reproceso fallaria siempre."""
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    cli = BlobCliente(connection_string=CS)
    cli.subir("transfer", "resultados/p1.json", b'{"n": 1}')
    cli.subir("transfer", "resultados/p1.json", b'{"n": 2}')
    assert cli.descargar("transfer", "resultados/p1.json") == b'{"n": 2}'


def test_f002_r14_el_resultado_fallido_no_inventa_borrados():
    """Decir que se borro una linea cuando el registro fallo entero seria
    mentir sobre una operacion destructiva."""
    fallido = _resultado_fallido("sigrid caido")
    assert fallido["borradas"] == 0
    assert fallido["ok"] is False
    assert fallido["escritas"] == []


def test_f002_r6_el_sobre_de_resultado_se_escribe_legible(monkeypatch):
    """Mismo motivo que el mensaje: el blob se lee a mano cuando algo va
    mal."""
    from application.pipelines.registro_pipeline import RegistroPipeline
    from interface_adapters.queue.transfer_consumer import (
        construir_handler_transfer,
    )
    from tests.dobles import SettingsFake
    from tests.test_f002_pipeline_fases import _sigrid

    svc_blob = parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    blob = BlobCliente(connection_string=CS)
    cola = ColaCliente(connection_string=CS, poll_interval_s=0)
    settings = SettingsFake()
    handler = construir_handler_transfer(
        pipeline=RegistroPipeline(cliente=_sigrid(), settings=settings),
        blob=blob, cola=cola, settings=settings)
    blob.subir("transfer", "peticiones/p1.json", json.dumps({
        "peticion_id": "p1", "usuario": "Begoña",
        "obra": {"ide": 10, "codigo": "0100"},
        "lineas": [{"registro_id": 1, "fecha_int": 20260302,
                    "recurso_ide": 501, "tipo_hora": "normal", "horas": 8.0}],
    }).encode("utf-8"))

    handler({"peticion_id": "p1", "blob": "peticiones/p1.json"})

    crudo = svc_blob.almacen[("transfer", "resultados/p1.json")]
    assert "Begoña" in crudo.decode("utf-8")


# ---------------------------- pool de workers --------------------------- #

def test_f002_r18_sin_transfer_workers_declarado_arranca_uno(monkeypatch):
    """Una configuración antigua sin la clave no puede quedarse sin
    consumir la cola, ni levantar mas hilos de los pedidos."""
    class SettingsSinWorkers:
        cola_transfer = "q-transfer"

    colas = [type("ColaEspia", (), {
        "consumir": lambda self, _n, _h: None})() for _ in range(4)]
    hilos = arrancar_workers_transfer(
        pipeline=object(), settings=SettingsSinWorkers(),
        fabrica_cola=lambda: colas.pop(0), fabrica_blob=lambda: object())
    for h in hilos:
        h.join(5)

    assert len(hilos) == 1


# ------------------------------ credenciales ---------------------------- #

def test_f002_el_endpoint_derivado_conserva_la_url_entera():
    """`split('=', 1)` y no mas: un endpoint con '=' en la query se
    truncaria y el hand-off apuntaria a un host que no existe."""
    cs = ("AccountName=devstoreaccount1;"
          "QueueEndpoint=http://127.0.0.1:10001/dev?sig=abc=;")
    derivada = cred._derivar_blob_connection_string(cs)
    assert "BlobEndpoint=http://127.0.0.1:10000/dev?sig=abc=" in derivada


def test_f002_cola_cliente_sin_argumentos_no_adivina():
    with pytest.raises(ValueError):
        ColaCliente(None, None)
