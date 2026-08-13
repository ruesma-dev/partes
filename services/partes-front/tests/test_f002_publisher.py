# tests/test_f002_publisher.py
"""F-002 · publicacion en `q-transfer` y traza `sigrid_*` en sv4.

R1 (blob + mensaje), R2 (marcado 'encolado'), R12 (marcado del
resultado), R13 (idempotencia) y R14 (error global).

Sin red ni PostgreSQL: adaptadores reales de Storage sobre fakes del SDK
y el repositorio real sobre SQLite en memoria con el MISMO ORM.
"""
from __future__ import annotations

import json

import pytest
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure import cola_cliente as mod_cola
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.azure.cola_cliente import ColaCliente
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.transfer.transfer_queue_publisher import (
    TransferQueuePublisher,
)
from tests.dobles import (
    BlobServiceClientFake,
    FabricaSesionSqlite,
    QueueServiceClientFake,
    estados_sigrid,
    parchear_blobs,
    parchear_colas,
    sembrar_registros,
)

PAYLOAD = {
    "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
    "lineas": [
        {"registro_id": 1, "fecha_int": 20260302, "recurso_ide": 501,
         "tipo_hora": "normal", "horas": 8.0},
        {"registro_id": 2, "fecha_int": 20260302, "recurso_ide": 502,
         "tipo_hora": "extra", "horas": 2.0},
    ],
    "pisar_claves": [],
    "usuario": "ana",
}


@pytest.fixture
def publisher(monkeypatch):
    svc_cola = parchear_colas(monkeypatch, mod_cola, QueueServiceClientFake())
    parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
    blob = BlobCliente(connection_string="UseDevelopmentStorage=true")
    cola = ColaCliente(connection_string="UseDevelopmentStorage=true",
                       poll_interval_s=0)
    pub = TransferQueuePublisher(cola=cola, blob=blob,
                                 cola_transfer="q-transfer",
                                 contenedor="transfer")
    pub._svc_cola = svc_cola          # atajo para las aserciones del test
    pub._blob = blob
    return pub


# ------------------------------ R1: publicar ---------------------------- #

def test_f002_r1_publica_el_blob_y_el_mensaje_con_la_referencia(publisher):
    peticion_id = publisher.publicar(PAYLOAD, usuario="ana")

    mensajes = publisher._svc_cola.get_queue_client(
        "q-transfer").payloads_enviados
    assert mensajes == [{"peticion_id": peticion_id,
                         "blob": f"peticiones/{peticion_id}.json"}]

    sobre = json.loads(publisher._blob.descargar(
        "transfer", f"peticiones/{peticion_id}.json").decode("utf-8"))
    assert sobre["peticion_id"] == peticion_id
    assert sobre["usuario"] == "ana"
    assert sobre["creado_at_utc"]
    assert sobre["obra"] == PAYLOAD["obra"]
    assert sobre["lineas"] == PAYLOAD["lineas"]


def test_f002_r5_el_payload_publicado_nunca_lleva_pisar_claves(publisher):
    """R5/R10: pisar es humano y sincrono; jamas viaja por la cola."""
    peticion_id = publisher.publicar(
        dict(PAYLOAD, pisar_claves=["501|20260302|1"]), usuario="ana")
    sobre = json.loads(publisher._blob.descargar(
        "transfer", f"peticiones/{peticion_id}.json").decode("utf-8"))
    assert sobre["pisar_claves"] == []


def test_f002_r1_cada_peticion_lleva_su_identificador(publisher):
    ids = {publisher.publicar(PAYLOAD, usuario="ana") for _ in range(3)}
    assert len(ids) == 3


def test_f002_r1_si_el_blob_falla_no_se_encola_nada(monkeypatch, publisher):
    """El mensaje nunca puede referirse a un blob que no existe."""
    def _revienta(*_a, **_k):
        raise RuntimeError("storage caido")

    monkeypatch.setattr(publisher._blob, "subir", _revienta)
    with pytest.raises(RuntimeError):
        publisher.publicar(PAYLOAD, usuario="ana")
    assert publisher._svc_cola.get_queue_client("q-transfer").enviados == []


# --------------------- R2/R12/R13/R14: traza sigrid_* ------------------- #

@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    return ParteReviewRepository(fabrica), fabrica


def test_f002_r2_marca_encolado_las_lineas_de_la_peticion(repo):
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=3)

    n = repositorio.marcar_registros_encolado(ids, usuario="ana")

    assert n == 3
    for estado, motivo, *_ in estados_sigrid(fabrica, ids).values():
        assert estado == "encolado"
        assert motivo is None


def test_f002_r2_encolar_limpia_el_motivo_de_un_intento_anterior(repo):
    """Reaprobar una linea omitida no debe dejar el motivo viejo a la vista."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[{"registro_id": ids[0], "motivo": "sin horas"}],
        ya_registradas=[], usuario="ana")

    repositorio.marcar_registros_encolado(ids, usuario="ana")

    estado, motivo, *_ = estados_sigrid(fabrica, ids)[ids[0]]
    assert (estado, motivo) == ("encolado", None)


def test_f002_r12_marca_el_resultado_por_linea(repo):
    """R12: escritas, omitidas, ya_registradas y conflictos, cada uno al suyo."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=4)
    repositorio.marcar_registros_encolado(ids, usuario="ana")

    repositorio.marcar_registros_sigrid(
        escritas=[{"registro_id": ids[0], "hmoide": 901, "hmores_ide": 5001,
                   "parte_cod": "PT26/00001"}],
        omitidas=[{"registro_id": ids[1], "motivo": "sin codigo de hora"}],
        ya_registradas=[ids[2]],
        conflictos=[{"clave": "501|20260302|1", "registros": [ids[3]],
                     "parte_cod": "PT26/00001"}],
        usuario="ana")

    estados = estados_sigrid(fabrica, ids)
    assert estados[ids[0]] == ("registrado", None, 901, 5001, "PT26/00001")
    assert estados[ids[1]][0] == "omitido"
    assert estados[ids[1]][1] == "sin codigo de hora"
    assert estados[ids[2]][0] == "registrado"
    assert estados[ids[3]][0] == "conflicto"
    assert "confirmar" in (estados[ids[3]][1] or "").lower()


def test_f002_r12_ya_registrada_saca_la_linea_de_encolado(repo):
    """La linea encolada que vuelve como 'ya registrada' no puede
    quedarse en 'encolado' para siempre."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio.marcar_registros_encolado(ids, usuario="ana")

    repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=ids, usuario="ana")

    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "registrado"


def test_f002_r13_aplicar_el_mismo_resultado_dos_veces_no_cambia_nada(repo):
    """R13: la reentrega del mensaje deja exactamente el mismo estado."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=4)
    repositorio.marcar_registros_encolado(ids, usuario="ana")
    argumentos = {
        "escritas": [{"registro_id": ids[0], "hmoide": 901,
                      "hmores_ide": 5001, "parte_cod": "PT26/00001"}],
        "omitidas": [{"registro_id": ids[1], "motivo": "sin codigo de hora"}],
        "ya_registradas": [ids[2]],
        "conflictos": [{"clave": "501|20260302|1", "registros": [ids[3]]}],
        "usuario": "ana",
    }

    repositorio.marcar_registros_sigrid(**argumentos)
    primera = estados_sigrid(fabrica, ids)
    repositorio.marcar_registros_sigrid(**argumentos)
    segunda = estados_sigrid(fabrica, ids)

    assert primera == segunda


def test_f002_r14_error_global_marca_todas_las_lineas_de_la_peticion(repo):
    """R14: con ok=false, la peticion entera queda en 'error' con motivo."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=3)
    repositorio.marcar_registros_encolado(ids, usuario="ana")

    n = repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        registro_ids=ids, error_global="sigrid-api devolvio 500")

    assert n == 3
    for estado, motivo, *_ in estados_sigrid(fabrica, ids).values():
        assert estado == "error"
        assert "sigrid-api devolvio 500" in motivo


def test_f002_r14_el_error_global_es_idempotente(repo):
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=2)
    argumentos = {"escritas": [], "omitidas": [], "ya_registradas": [],
                  "usuario": "ana", "registro_ids": ids,
                  "error_global": "sigrid-api devolvio 500"}

    repositorio.marcar_registros_sigrid(**argumentos)
    primera = estados_sigrid(fabrica, ids)
    repositorio.marcar_registros_sigrid(**argumentos)

    assert estados_sigrid(fabrica, ids) == primera


def test_f002_r12_una_linea_inexistente_no_rompe_el_marcado(repo):
    """Un registro borrado entre el encolado y el resultado no puede
    tumbar la traza de los demas."""
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=1)

    n = repositorio.marcar_registros_sigrid(
        escritas=[{"registro_id": 999999, "hmoide": 1},
                  {"registro_id": ids[0], "hmoide": 901,
                   "parte_cod": "PT26/00001"}],
        omitidas=[], ya_registradas=[], usuario="ana")

    assert n == 1
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "registrado"


def test_f002_r12_el_marcado_sin_novedades_no_toca_nada(repo):
    repositorio, fabrica = repo
    ids = sembrar_registros(fabrica, cantidad=2)
    assert repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana") == 0
    assert all(e[0] is None for e in estados_sigrid(fabrica, ids).values())
