# tests/test_f002_mutantes.py
"""F-002 · lo que la campaña de mutación destapó como no comprobado (sv4).

Varias de estas líneas parecían cosmética y no lo son: un `ok` invertido
en una respuesta de error hace que el portal celebre un rechazo, un tope
corrido en uno reencola de más, y un truncado a 256 no cabe en una
columna de 255.
"""
from __future__ import annotations

import logging

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure import credenciales as cred
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer.transfer_queue_publisher import (
    TransferQueuePublisher,
)
from interface_adapters.web.app import build_app
from interface_adapters.workers.resultado_consumer import (
    construir_handler_resultados,
)
from tests.dobles import (
    BlobServiceClientFake,
    FabricaSesionSqlite,
    QueueServiceClientFake,
    estados_sigrid,
    mensaje_json,
    parchear_blobs,
    parchear_colas,
    sembrar_registros,
)

CS = "UseDevelopmentStorage=true"


def _cola(monkeypatch, **kwargs):
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    return ColaCliente(connection_string=CS, **kwargs), svc


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    return monkeypatch


def _settings() -> Settings:
    return Settings(_env_file=None)


# --------------------------- defaults de config ------------------------- #

def test_f002_los_defaults_de_cola_son_los_acordados():
    st = _settings()
    assert st.cola_visibility_s == 600      # margen para escribir en Sigrid
    assert st.cola_max_dequeue == 5         # reintentos antes de la DLQ


def test_f002_r9_por_defecto_se_reintenta_5_veces_antes_de_poison(monkeypatch):
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, dequeue_count=5,
                                 id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer-result", vistos.append)

    assert vistos == [{"peticion_id": "p1"}]
    assert svc.get_queue_client("q-transfer-result-poison").enviados == []


def test_f002_r9_en_el_intento_6_ya_va_a_poison(monkeypatch):
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, dequeue_count=6,
                                 id="m1")]]
    cola.on_agotado = cli.detener
    vistos: list[dict] = []

    cli.consumir("q-transfer-result", vistos.append)

    assert vistos == []
    assert len(svc.get_queue_client("q-transfer-result-poison").enviados) == 1


def test_f002_el_visibility_y_el_lote_por_defecto(monkeypatch):
    cli, svc = _cola(monkeypatch, poll_interval_s=0)
    cola = svc.get_queue_client("q-transfer-result")
    cola.on_agotado = cli.detener

    cli.consumir("q-transfer-result", lambda _p: None)

    assert cola.recepciones[0] == {"messages_per_page": 1,
                                   "visibility_timeout": 600}


def test_f002_el_sondeo_por_defecto_es_de_5_s(monkeypatch):
    esperas: list[tuple] = []
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    cli = ColaCliente(connection_string=CS)
    monkeypatch.setattr(
        mod_cola.time, "sleep",
        lambda s: esperas.append((s, cli._stop)) or cli.detener())
    svc.get_queue_client("q-transfer-result")

    cli.consumir("q-transfer-result", lambda _p: None)

    assert esperas == [(5, False)]


def test_f002_tras_procesar_un_mensaje_no_se_duerme(monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr(mod_cola.time, "sleep", esperas.append)
    cli, svc = _cola(monkeypatch)
    cola = svc.get_queue_client("q-transfer-result")
    cola.rondas = [[mensaje_json({"peticion_id": "p1"}, id="m1")]]

    cli.consumir("q-transfer-result", lambda _p: cli.detener())

    assert esperas == []


# ------------------------------- poison --------------------------------- #

def test_f002_r23_una_cola_sin_recuento_cuenta_cero(monkeypatch):
    """Storage puede no traer el atributo: inventar un 1 encendería el
    aviso del portal sin que haya nada parado."""
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())

    class PropsSinRecuento:
        pass

    svc.get_queue_client("q-transfer-poison").get_queue_properties = \
        lambda: PropsSinRecuento()
    cli = ColaCliente(connection_string=CS)
    assert cli.contar_aproximado("q-transfer-poison") == 0


def test_f002_r23_un_recuento_nulo_cuenta_cero(monkeypatch):
    svc = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    svc.get_queue_client("q-transfer-poison").mensajes_aprox = None
    cli = ColaCliente(connection_string=CS)
    assert cli.contar_aproximado("q-transfer-poison") == 0


def test_f002_r24_el_tope_por_defecto_son_32(monkeypatch):
    cli, svc = _cola(monkeypatch)
    poison = svc.get_queue_client("q-transfer-poison")
    poison.rondas = [[mensaje_json({"peticion_id": f"p{i}"}, id=f"m{i}")]
                     for i in range(40)]

    movidos = cli.mover("q-transfer-poison", "q-transfer")

    assert len(movidos) == 32


def test_f002_r24_el_tope_se_respeta_aunque_lleguen_de_dos_en_dos(monkeypatch):
    """El corte interno no es decorativo: si Storage devolviera lotes de
    mas de uno, sin el se moverian mas de los pedidos."""
    cli, svc = _cola(monkeypatch)
    poison = svc.get_queue_client("q-transfer-poison")
    poison.rondas = [[mensaje_json({"peticion_id": "p0"}, id="m0"),
                      mensaje_json({"peticion_id": "p1"}, id="m1")],
                     [mensaje_json({"peticion_id": "p2"}, id="m2"),
                      mensaje_json({"peticion_id": "p3"}, id="m3")]]

    movidos = cli.mover("q-transfer-poison", "q-transfer", maximo=3)

    assert len(movidos) == 3
    assert len(svc.get_queue_client("q-transfer").enviados) == 3


def test_f002_r24_al_reencolar_se_recibe_de_uno_en_uno(monkeypatch):
    """De uno en uno tambien aqui: cada mensaje se encola y se borra
    antes de tocar el siguiente."""
    cli, svc = _cola(monkeypatch)
    poison = svc.get_queue_client("q-transfer-poison")
    poison.rondas = [[mensaje_json({"peticion_id": "p0"}, id="m0")]]

    cli.mover("q-transfer-poison", "q-transfer")

    assert poison.recepciones[0]["messages_per_page"] == 1


def test_f002_r25_el_fallo_al_borrar_deja_traza_completa(monkeypatch, caplog):
    """Es un duplicado potencial en la DLQ: sin el traceback no hay por
    donde empezar a mirar."""
    cli, svc = _cola(monkeypatch)
    poison = svc.get_queue_client("q-transfer-poison")
    poison.rondas = [[mensaje_json({"peticion_id": "p0"}, id="m0")]]
    poison.fallo_delete = True

    with caplog.at_level(logging.WARNING):
        cli.mover("q-transfer-poison", "q-transfer")

    avisos = [r for r in caplog.records if "NO borrado" in r.getMessage()]
    assert avisos and avisos[0].exc_info is not None


# ------------------------------ endpoints ------------------------------- #

class PublisherFake:
    def publicar(self, _payload, usuario=None):
        return "peticion-1"


class ColaFake:
    def mover(self, _o, _d, maximo=32):
        return []

    def contar_aproximado(self, _c):
        return 0


def _app(repositorio, **kwargs):
    return TestClient(build_app(_settings(), repository=repositorio, **kwargs))


def test_f002_r5_el_rechazo_de_pisar_claves_dice_que_NO_fue_bien():
    """El portal decide por `ok`: un rechazo con ok=true se celebraria."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    cliente = _app(ParteReviewRepository(fabrica), publisher=PublisherFake())

    r = cliente.post("/api/aprobar/encolar",
                     json={"registro_ids": ids, "pisar_claves": ["k"]})

    assert r.status_code == 422
    assert r.json()["ok"] is False


def test_f002_r24_el_rechazo_de_una_cola_no_admitida_dice_que_NO_fue_bien():
    cliente = _app(ParteReviewRepository(FabricaSesionSqlite()),
                   cola_cliente=ColaFake())

    r = cliente.post("/api/admin/poison/reencolar", json={"cola": "q-otra"})

    assert r.status_code == 422
    assert r.json()["ok"] is False


class RepositorioRoto:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)

    def marcar_registros_sigrid(self, **_kw):
        raise RuntimeError("PostgreSQL caido")

    def marcar_registros_encolado(self, *_a, **_kw):
        raise RuntimeError("PostgreSQL caido")


class TransferClientFake:
    def ejecutar(self, _payload):
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": []}

    def preflight(self, _payload):
        return {"ok": True, "conflictos": []}


def _avisos_con_traza(caplog, fragmento: str) -> list:
    return [r for r in caplog.records
            if fragmento in r.getMessage() and r.exc_info is not None]


def test_f002_el_fallo_al_trazar_se_registra_con_traceback(caplog):
    """Se traga la excepción a propósito; sin el traceback en el log, el
    fallo desaparecería sin dejar nada que investigar."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    cliente = _app(RepositorioRoto(ParteReviewRepository(fabrica)),
                   transfer_client=TransferClientFake())

    with caplog.at_level(logging.WARNING):
        cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids})

    assert _avisos_con_traza(caplog, "no se pudo guardar la traza")


def test_f002_r2_el_fallo_al_marcar_encolado_se_registra_con_traceback(caplog):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    cliente = _app(RepositorioRoto(ParteReviewRepository(fabrica)),
                   publisher=PublisherFake())

    with caplog.at_level(logging.WARNING):
        cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    assert _avisos_con_traza(caplog, "no se pudo marcar 'encolado'")


def test_f002_r23_el_fallo_al_contar_poison_se_registra_con_traceback(caplog):
    class ColaQueNoCuenta:
        def contar_aproximado(self, _c):
            raise RuntimeError("storage caido")

        def mover(self, _o, _d, maximo=32):
            return []

    cliente = _app(ParteReviewRepository(FabricaSesionSqlite()),
                   cola_cliente=ColaQueNoCuenta())

    with caplog.at_level(logging.WARNING):
        cliente.get("/api/admin/poison")

    assert _avisos_con_traza(caplog, "no se pudo contar")


def test_f002_los_endpoints_internos_no_salen_en_la_documentacion():
    """Son de uso interno del portal; publicarlos en /docs invita a
    llamarlos desde fuera."""
    cliente = _app(ParteReviewRepository(FabricaSesionSqlite()),
                   publisher=PublisherFake(), cola_cliente=ColaFake())
    rutas = cliente.get("/openapi.json").json()["paths"]
    for ruta in ("/api/aprobar/encolar", "/api/admin/poison",
                 "/api/admin/poison/reencolar"):
        assert ruta not in rutas


def test_f002_con_repositorio_inyectado_las_tablas_se_dan_por_listas():
    """Las crea la fábrica del test; marcarlas como no listas haría que
    las vistas avisaran de una base sin migrar que sí existe."""
    app = build_app(_settings(),
                    repository=ParteReviewRepository(FabricaSesionSqlite()))
    assert app.state.tables_ready is True


# ------------------------------ repositorio ----------------------------- #

def test_f002_r14_el_motivo_del_error_cabe_en_la_columna():
    """`sigrid_motivo` es VARCHAR(255): 256 caracteres reventaria el
    INSERT en PostgreSQL (SQLite lo tragaria y nadie se enteraria)."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)

    repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        registro_ids=ids, error_global="E" * 400)

    assert len(estados_sigrid(fabrica, ids)[ids[0]][1]) == 255


def test_f002_r12_el_motivo_del_conflicto_cabe_en_la_columna():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)

    repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        conflictos=[{"clave": "k", "registros": ids, "parte_cod": "P" * 400}])

    assert len(estados_sigrid(fabrica, ids)[ids[0]][1]) == 255


def test_f002_r12_el_recuento_cuenta_las_ya_registradas():
    """El número que devuelve es lo que se registra en el log de la
    operación: contarlo al revés (o de dos en dos) miente sobre cuántas
    líneas se tocaron."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=3)
    repositorio = ParteReviewRepository(fabrica)
    repositorio.marcar_registros_encolado(ids, usuario="ana")

    n = repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=ids, usuario="ana")

    assert n == 3


# --------------------------- consumidor / publisher --------------------- #

class SettingsCola:
    blob_transfer = "transfer"
    cola_transfer = "q-transfer"
    cola_transfer_result = "q-transfer-result"
    default_reviewer = "revisor-por-defecto"


def test_f002_r12_sin_usuario_en_el_sobre_se_usa_el_revisor_por_defecto(
        monkeypatch):
    """Un sobre antiguo o sin usuario no puede dejar la traza sin firmar."""
    import json as _json

    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    blob = BlobCliente(connection_string=CS)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)
    handler = construir_handler_resultados(
        repository=repositorio, blob=blob, settings=SettingsCola())
    blob.subir("transfer", "resultados/p1.json", _json.dumps({
        "peticion_id": "p1", "registro_ids": ids,
        "resultado": {"ok": True, "escritas": [
            {"registro_id": ids[0], "hmoide": 901}],
            "omitidas": [], "ya_registradas": []},
    }).encode("utf-8"))

    handler({"peticion_id": "p1", "blob": "resultados/p1.json"})

    with fabrica.create_session() as s:
        from infrastructure.database.orm_models import ParteRegistroOrm
        assert s.get(ParteRegistroOrm,
                     ids[0]).sigrid_registrado_by == "revisor-por-defecto"


def test_f002_r1_la_peticion_se_escribe_legible(monkeypatch):
    """El blob de la petición se lee a mano cuando algo falla."""
    parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    svc_blob = parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    publisher = TransferQueuePublisher(
        cola=ColaCliente(connection_string=CS),
        blob=BlobCliente(connection_string=CS),
        cola_transfer="q-transfer", contenedor="transfer")

    pid = publisher.publicar(
        {"obra": {"nombre": "Peñón"}, "lineas": []}, usuario="Begoña")

    crudo = svc_blob.almacen[("transfer", f"peticiones/{pid}.json")]
    texto = crudo.decode("utf-8")
    assert "Peñón" in texto and "Begoña" in texto


def test_f002_los_mensajes_se_escriben_legibles(monkeypatch):
    cli, svc = _cola(monkeypatch)
    cli.enviar("q-transfer", {"peticion_id": "p1", "obra": "Peñón"})
    assert "Peñón" in svc.get_queue_client("q-transfer").enviados[0]


def test_f002_el_blob_se_puede_reescribir(monkeypatch):
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    cli = BlobCliente(connection_string=CS)
    cli.subir("transfer", "peticiones/p1.json", b'{"n": 1}')
    cli.subir("transfer", "peticiones/p1.json", b'{"n": 2}')
    assert cli.descargar("transfer", "peticiones/p1.json") == b'{"n": 2}'


def test_f002_el_endpoint_derivado_conserva_la_url_entera():
    cs = ("AccountName=devstoreaccount1;"
          "QueueEndpoint=http://127.0.0.1:10001/dev?sig=abc=;")
    derivada = cred._derivar_blob_connection_string(cs)
    assert "BlobEndpoint=http://127.0.0.1:10000/dev?sig=abc=" in derivada
