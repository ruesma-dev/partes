# tests/test_f002_credenciales_y_arranque.py
"""F-002 · eleccion de credencial, bucle de cola y composicion de sv5.

Aqui se cubren las decisiones que NO se ven en el camino feliz y que, mal
tomadas, solo fallan en produccion: elegir connection string en vez de
managed identity, tragarse un `SIGTERM`, o cablear los workers con un
pipeline distinto al del HTTP (y por tanto con otro lock).
"""
from __future__ import annotations

import signal

import pytest
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure import credenciales as cred
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from tests.dobles import (
    BlobServiceClientFake,
    QueueServiceClientFake,
    mensaje_json,
    parchear_blobs,
    parchear_colas,
)

CS_AZURITE = ("DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
              "AccountKey=xxx;QueueEndpoint=http://127.0.0.1:10001/"
              "devstoreaccount1;")


# ---------------------------- credenciales ------------------------------ #

def test_f002_deriva_el_endpoint_de_blob_desde_el_de_colas():
    """Azurite solo da QueueEndpoint; el de blob es el mismo host, puerto
    10000. Sin esto, en local no hay hand-off."""
    derivada = cred._derivar_blob_connection_string(CS_AZURITE)
    assert "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1" in derivada
    assert "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1" in derivada


def test_f002_si_ya_hay_endpoint_de_blob_se_respeta():
    cs = CS_AZURITE + "BlobEndpoint=http://otro:10000/cuenta;"
    assert cred._derivar_blob_connection_string(cs) == cs


def test_f002_sin_queue_endpoint_no_inventa_nada():
    cs = "AccountName=x;AccountKey=y;"
    assert "BlobEndpoint" not in cred._derivar_blob_connection_string(cs)


def test_f002_la_credencial_usa_el_client_id_de_la_identidad(monkeypatch):
    """En Container Apps hay varias identidades: sin AZURE_CLIENT_ID se
    puede coger la que no es."""
    vistos = {}

    class CredencialFake:
        def __init__(self, **kwargs):
            vistos.update(kwargs)

    monkeypatch.setattr(cred, "DefaultAzureCredential", CredencialFake)
    monkeypatch.setenv("AZURE_CLIENT_ID", "id-partes-dev")
    cred.build_credential()
    assert vistos == {"managed_identity_client_id": "id-partes-dev"}

    vistos.clear()
    monkeypatch.delenv("AZURE_CLIENT_ID")
    cred.build_credential()
    assert vistos == {"managed_identity_client_id": None}


def test_f002_la_connection_string_manda_sobre_la_identidad(monkeypatch):
    """En local (Azurite) NO se debe intentar autenticar contra Azure."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    monkeypatch.setattr(cred, "build_credential",
                        lambda: pytest.fail("no debia pedir credencial"))
    cli = cred.construir_cola_cliente(
        connection_string=CS_AZURITE,
        account_url="https://stpartes.queue.core.windows.net")
    assert isinstance(cli, ColaCliente)
    cli.enviar("q-transfer", {"peticion_id": "p1"})
    assert svc.get_queue_client("q-transfer").enviados


def test_f002_sin_connection_string_se_usa_la_identidad(monkeypatch):
    parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    pedidas = []
    monkeypatch.setattr(cred, "build_credential",
                        lambda: pedidas.append(1) or "credencial")
    cli = cred.construir_cola_cliente(
        connection_string=None,
        account_url="https://stpartes.queue.core.windows.net/",
        max_dequeue=9)
    assert isinstance(cli, ColaCliente)
    assert pedidas == [1]


def test_f002_el_blob_hereda_la_connection_string_de_las_colas(monkeypatch):
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    monkeypatch.setattr(cred, "build_credential",
                        lambda: pytest.fail("no debia pedir credencial"))
    cli = cred.construir_blob_cliente(
        connection_string=None, account_url=None,
        colas_connection_string=CS_AZURITE)
    assert isinstance(cli, BlobCliente)


def test_f002_el_blob_tambien_puede_ir_por_identidad(monkeypatch):
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    pedidas = []
    monkeypatch.setattr(cred, "build_credential",
                        lambda: pedidas.append(1) or "credencial")
    cli = cred.construir_blob_cliente(
        connection_string=None,
        account_url="https://stpartes.blob.core.windows.net")
    assert isinstance(cli, BlobCliente)
    assert pedidas == [1]


# ------------------------- adaptadores: bordes -------------------------- #

def test_f002_cola_por_account_url_recorta_la_barra(monkeypatch):
    svc = QueueServiceClientFake()
    registrado = {}

    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return svc

        def __new__(cls, *args, **kwargs):
            registrado.update(kwargs)
            return svc

    monkeypatch.setattr(mod_cola, "QueueServiceClient", _Factoria)
    ColaCliente("https://stpartes.queue.core.windows.net/", "cred")
    assert registrado["account_url"] == "https://stpartes.queue.core.windows.net"


def test_f002_blob_por_account_url(monkeypatch):
    svc = BlobServiceClientFake()
    registrado = {}

    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return svc

        def __new__(cls, *args, **kwargs):
            registrado.update(kwargs)
            return svc

    monkeypatch.setattr(mod_blob, "BlobServiceClient", _Factoria)
    BlobCliente("https://stpartes.blob.core.windows.net", "cred")
    assert registrado["account_url"] == "https://stpartes.blob.core.windows.net"


def test_f002_asegurar_colas_es_idempotente(monkeypatch):
    """Arrancar dos veces contra el mismo Azurite no puede reventar."""
    from azure.core.exceptions import ResourceExistsError
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())

    def _ya_existe(_nombre):
        raise ResourceExistsError("ya existe")

    svc.create_queue = _ya_existe
    ColaCliente(connection_string=CS_AZURITE).asegurar_colas(["q-transfer"])


def test_f002_asegurar_contenedores_es_idempotente(monkeypatch):
    from azure.core.exceptions import ResourceExistsError
    svc = parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())

    def _ya_existe(_nombre):
        raise ResourceExistsError("ya existe")

    svc.create_container = _ya_existe
    BlobCliente(connection_string=CS_AZURITE).asegurar_contenedores(["transfer"])


def test_f002_sigterm_detiene_el_consumo_tras_el_mensaje_actual(monkeypatch):
    """Container Apps manda SIGTERM al reiniciar o redesplegar: hay que
    salir limpio, no a mitad de una escritura en Sigrid."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    manejadores = {}
    monkeypatch.setattr(mod_cola.signal, "signal",
                        lambda sig, fn: manejadores.setdefault(sig, fn))
    cli = ColaCliente(connection_string=CS_AZURITE, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]

    def _handler(_p):
        manejadores[signal.SIGTERM](signal.SIGTERM, None)   # llega el SIGTERM

    cli.consumir("q-transfer", _handler)

    assert cola.borrados == ["m1"]      # el mensaje en curso se completo


def test_f002_sin_hilo_principal_el_manejador_de_senal_se_ignora(monkeypatch):
    """Los workers son hilos: alli `signal.signal` lanza ValueError y eso
    no puede impedir que el worker consuma."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())

    def _no_se_puede(_sig, _fn):
        raise ValueError("signal only works in main thread")

    monkeypatch.setattr(mod_cola.signal, "signal", _no_se_puede)
    cli = ColaCliente(connection_string=CS_AZURITE, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]
    cola.on_agotado = cli.detener
    vistos = []

    cli.consumir("q-transfer", vistos.append)

    assert vistos == [{"peticion_id": "p1"}]


def test_f002_al_detener_no_se_procesa_el_resto_del_lote(monkeypatch):
    """Con SIGTERM a mitad de un lote, los que quedan se dejan en la cola
    (reaparecen): mejor reprocesar que perder."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    cli = ColaCliente(connection_string=CS_AZURITE, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1"),
                    mensaje_json({"peticion_id": "p2"}, id="m2")]]
    vistos = []

    def _handler(payload):
        vistos.append(payload)
        cli.detener()

    cli.consumir("q-transfer", _handler)

    assert [v["peticion_id"] for v in vistos] == ["p1"]
    assert cola.borrados == ["m1"]


def test_f002_cola_vacia_espera_antes_de_volver_a_preguntar(monkeypatch):
    """Sin espera, un worker ocioso quemaria CPU y cuota de Storage."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    esperas = []
    monkeypatch.setattr(mod_cola.time, "sleep", esperas.append)
    cli = ColaCliente(connection_string=CS_AZURITE, poll_interval_s=7)
    cola = svc.get_queue_client("q-transfer")
    vueltas = {"n": 0}

    def _vacia():
        vueltas["n"] += 1
        if vueltas["n"] >= 2:
            cli.detener()

    cola.on_agotado = _vacia
    cli.consumir("q-transfer", lambda _p: None)

    assert esperas == [7]


# --------------------------- composicion (main) ------------------------- #

def test_f002_r7_el_main_comparte_un_solo_lock_entre_http_y_workers(monkeypatch):
    """La garantia entera de R7 depende de esto: si el HTTP y los workers
    usaran pipelines distintos, cada uno tendria su lock y las escrituras
    se solaparian."""
    import main as entrypoint
    from application.pipelines.registro_pipeline import RegistroPipeline
    from tests.dobles import SettingsFake, SigridFake

    settings = SettingsFake(transfer_workers=2)
    settings.colas_connection_string = CS_AZURITE
    settings.colas_account_url = None
    settings.blobs_connection_string = None
    settings.blobs_account_url = None

    parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    arrancados = {}
    monkeypatch.setattr(
        entrypoint, "arrancar_workers_transfer",
        lambda **kw: arrancados.update(kw) or [])

    pipeline = RegistroPipeline(cliente=SigridFake(), settings=settings)
    entrypoint._arrancar_consumo(settings, pipeline)

    assert arrancados["pipeline"] is pipeline
    assert arrancados["settings"] is settings
    # Cada worker recibe SUS clientes: el SDK no se comparte entre hilos.
    assert arrancados["fabrica_cola"]() is not arrancados["fabrica_cola"]()
    assert arrancados["fabrica_blob"]() is not arrancados["fabrica_blob"]()


def test_f002_el_main_crea_colas_y_contenedor_en_local(monkeypatch):
    """Con Azurite (connection string) hay que crearlos: arranca vacio."""
    import main as entrypoint
    from application.pipelines.registro_pipeline import RegistroPipeline
    from tests.dobles import SettingsFake, SigridFake

    settings = SettingsFake()
    settings.colas_connection_string = CS_AZURITE
    settings.colas_account_url = None
    settings.blobs_connection_string = None
    settings.blobs_account_url = None

    svc_cola = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    svc_blob = parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    monkeypatch.setattr(entrypoint, "arrancar_workers_transfer",
                        lambda **kw: [])

    entrypoint._arrancar_consumo(
        settings, RegistroPipeline(cliente=SigridFake(), settings=settings))

    assert svc_cola.creadas == ["q-transfer", "q-transfer-poison",
                                "q-transfer-result", "q-transfer-result-poison"]
    assert svc_blob.contenedores == ["transfer"]


def test_f002_en_la_nube_no_se_intenta_crear_la_infraestructura(monkeypatch):
    """En Azure las colas las crea el script de infra; el servicio no
    deberia necesitar permisos de gestion para arrancar."""
    import main as entrypoint
    from application.pipelines.registro_pipeline import RegistroPipeline
    from tests.dobles import SettingsFake, SigridFake

    settings = SettingsFake()
    settings.colas_connection_string = None
    settings.colas_account_url = "https://stpartes.queue.core.windows.net"
    settings.blobs_connection_string = None
    settings.blobs_account_url = "https://stpartes.blob.core.windows.net"

    svc_cola = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    svc_blob = parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    monkeypatch.setattr(cred, "build_credential", lambda: "credencial")
    monkeypatch.setattr(entrypoint, "arrancar_workers_transfer",
                        lambda **kw: [])

    entrypoint._arrancar_consumo(
        settings, RegistroPipeline(cliente=SigridFake(), settings=settings))

    assert svc_cola.creadas == []
    assert svc_blob.contenedores == []
