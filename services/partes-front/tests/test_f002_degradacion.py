# tests/test_f002_degradacion.py
"""F-002 · que pasa cuando algo de alrededor falla.

Ninguna de estas rutas se recorre en el camino feliz, y todas comparten
la misma regla: un fallo accesorio (guardar la traza, contar una cola,
un registro borrado a media peticion) NO puede tumbar lo principal —el
registro en Sigrid ya hecho, la respuesta al usuario o el portal entero—.
"""
from __future__ import annotations

import threading

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.workers.resultado_consumer import (
    arrancar_consumidor_resultados,
)
from tests.dobles import (
    FabricaSesionSqlite,
    estados_sigrid,
    sembrar_registros,
)


def _settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    return monkeypatch


# ------------------------ settings: interruptor ------------------------- #

def test_f002_r3_transfer_queue_enabled_reconoce_las_dos_formas(entorno):
    assert _settings().transfer_queue_enabled is False
    entorno.setenv("COLAS_CONNECTION_STRING", "UseDevelopmentStorage=true")
    assert Settings().transfer_queue_enabled is True
    entorno.delenv("COLAS_CONNECTION_STRING")
    entorno.setenv("COLAS_ACCOUNT_URL",
                   "https://stpartes.queue.core.windows.net")
    assert Settings().transfer_queue_enabled is True


# ------------------- repositorio: lineas que ya no estan ---------------- #

def test_f002_r14_un_registro_borrado_no_rompe_el_marcado_de_error():
    """Entre encolar y el resultado, alguien pudo borrar una linea."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)

    n = repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        registro_ids=ids + [999999], error_global="sigrid caido")

    assert n == 1
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "error"


def test_f002_r12_un_registro_borrado_no_rompe_el_marcado_de_omitidas():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)

    n = repositorio.marcar_registros_sigrid(
        escritas=[],
        omitidas=[{"registro_id": 999999, "motivo": "x"},
                  {"registro_id": ids[0], "motivo": "sin codigo"}],
        ya_registradas=[999999], usuario="ana")

    assert n == 1
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "omitido"


def test_f002_r12_un_registro_borrado_no_rompe_el_marcado_de_conflictos():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)

    n = repositorio.marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        conflictos=[{"clave": "k", "registros": [999999] + ids}])

    assert n == 1
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "conflicto"


def test_f002_r2_encolar_ignora_los_ids_que_ya_no_existen():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = ParteReviewRepository(fabrica)
    assert repositorio.marcar_registros_encolado(ids + [999999], "ana") == 1


# ------------------ endpoints: la traza es lo accesorio ----------------- #

class RepositorioRoto:
    """Repositorio cuyo marcado siempre falla."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)

    def marcar_registros_sigrid(self, **_kw):
        raise RuntimeError("PostgreSQL caido")

    def marcar_registros_encolado(self, *_a, **_kw):
        raise RuntimeError("PostgreSQL caido")


class TransferClientFake:
    def __init__(self, resultado):
        self.resultado = resultado

    def ejecutar(self, _payload):
        return self.resultado

    def preflight(self, _payload):
        return {"ok": True, "conflictos": []}


class PublisherFake:
    def publicar(self, _payload, usuario=None):
        return "peticion-1"


def _app(repositorio, *, publisher=None, transfer=None, cola=None):
    return TestClient(build_app(_settings(), repository=repositorio,
                                transfer_client=transfer, publisher=publisher,
                                cola_cliente=cola))


def test_f002_si_falla_la_traza_el_registro_hecho_no_se_pierde():
    """sv5 ya escribio en Sigrid: devolver 500 aqui haria creer al usuario
    que no se registro nada, y reintentaria."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = RepositorioRoto(ParteReviewRepository(fabrica))
    sv5 = TransferClientFake({"ok": True, "escritas": [
        {"registro_id": ids[0], "hmoide": 901}], "omitidas": [],
        "ya_registradas": []})

    r = _app(repositorio, transfer=sv5).post(
        "/api/aprobar/ejecutar", json={"registro_ids": ids})

    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_f002_r2_si_falla_el_marcado_la_peticion_sigue_encolada():
    """Ya esta en la cola: el resultado marcara las lineas al volver."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    repositorio = RepositorioRoto(ParteReviewRepository(fabrica))

    r = _app(repositorio, publisher=PublisherFake()).post(
        "/api/aprobar/encolar", json={"registro_ids": ids})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True and cuerpo["modo"] == "asincrono"


class ColaMediaRota:
    """Mueve mensajes, pero no sabe contar."""

    def __init__(self):
        self.movidos = ["m1", "m2"]

    def mover(self, _origen, _destino, maximo=32):
        return self.movidos

    def contar_aproximado(self, _cola):
        raise RuntimeError("storage caido")


def test_f002_r24_reencolar_informa_aunque_no_pueda_contar_lo_que_queda():
    """Lo importante es que se movieron; el restante es orientativo."""
    repositorio = ParteReviewRepository(FabricaSesionSqlite())

    r = _app(repositorio, cola=ColaMediaRota()).post(
        "/api/admin/poison/reencolar", json={"cola": "q-transfer"})

    assert r.status_code == 200
    assert r.json() == {"ok": True, "movidos": 2, "restantes_aprox": None}


# ---------------- consumidor: su caida no tumba el portal --------------- #

class ColaQueRevienta:
    def consumir(self, _nombre, _handler):
        raise RuntimeError("la cola se cayo")


class SettingsCola:
    blob_transfer = "transfer"
    cola_transfer = "q-transfer"
    cola_transfer_result = "q-transfer-result"
    default_reviewer = "ana"


def test_f002_r12_si_el_consumidor_revienta_el_portal_sigue_en_pie():
    """Corre dentro del proceso web: una excepcion suya no puede llevarse
    a uvicorn por delante."""
    hilo = arrancar_consumidor_resultados(
        repository=ParteReviewRepository(FabricaSesionSqlite()),
        cola=ColaQueRevienta(), blob=object(), settings=SettingsCola())
    hilo.join(5)

    assert isinstance(hilo, threading.Thread)
    assert not hilo.is_alive()
    assert threading.main_thread().is_alive()
