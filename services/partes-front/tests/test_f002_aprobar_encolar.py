# tests/test_f002_aprobar_encolar.py
"""F-002 · endpoint `POST /api/aprobar/encolar` del portal (R1-R5, R14).

`build_app` recibe sus colaboradores por parametro, asi que la app se
levanta con repositorio sobre SQLite en memoria y dobles del publisher y
del cliente HTTP de sv5: ni PostgreSQL, ni red, ni Storage.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_registros


class PublisherFake:
    def __init__(self) -> None:
        self.publicadas: list[tuple[dict, str | None]] = []

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        self.publicadas.append((payload, usuario))
        return f"peticion-{len(self.publicadas)}"


class TransferClientFake:
    """Doble del cliente HTTP de sv5."""

    def __init__(self, resultado: dict | None = None,
                 preflight: dict | None = None) -> None:
        self.resultado = resultado or {"ok": True, "escritas": [],
                                       "omitidas": [], "ya_registradas": []}
        self._preflight = preflight or {"ok": True, "conflictos": []}
        self.ejecutadas: list[dict] = []
        self.preflights: list[dict] = []

    def ejecutar(self, payload: dict) -> dict:
        self.ejecutadas.append(payload)
        return self.resultado

    def preflight(self, payload: dict) -> dict:
        self.preflights.append(payload)
        return self._preflight


def _settings() -> Settings:
    """Configuracion SIN leer el `.env` del desarrollador.

    Es deliberado: con el `.env` en juego, la suite pasaba o fallaba
    segun lo que cada maquina tuviera configurado (un TRANSFER_BASE_URL
    real cambiaba el cableado de la app).
    """
    return Settings(_env_file=None)


@pytest.fixture
def entorno(monkeypatch):
    """Configuracion minima; ningun valor real ni secreto."""
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def montaje(entorno):
    """Devuelve (cliente, repositorio, fabrica, ids, publisher, sv5)."""
    def _montar(*, con_publisher: bool = True, resultado: dict | None = None):
        fabrica = FabricaSesionSqlite()
        ids = sembrar_registros(fabrica, cantidad=2)
        repositorio = ParteReviewRepository(fabrica)
        publisher = PublisherFake() if con_publisher else None
        sv5 = TransferClientFake(resultado=resultado)
        app = build_app(_settings(), repository=repositorio,
                        transfer_client=sv5, publisher=publisher)
        return TestClient(app), repositorio, fabrica, ids, publisher, sv5
    return _montar


# ------------------------------ R1 / R2 -------------------------------- #

def test_f002_r1_encolar_responde_asincrono_sin_esperar_a_sigrid(montaje):
    cliente, _repo, _f, ids, publisher, sv5 = montaje()

    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert cuerpo["modo"] == "asincrono"
    assert cuerpo["peticion_id"] == "peticion-1"
    assert cuerpo["encoladas"] == 2
    # No se llamo a sv5 por HTTP: de eso se encarga la cola.
    assert sv5.ejecutadas == []
    payload, usuario = publisher.publicadas[0]
    # F-017: el TestClient no manda cabeceras de Easy Auth, asi que el
    # sobre viaja firmado como sesion local. Lo que este test comprueba
    # sigue siendo lo mismo: que el sobre va firmado, y con quien.
    assert usuario == "local:ana"
    assert [x["registro_id"] for x in payload["lineas"]] == ids


def test_f002_r2_encolar_deja_las_lineas_en_encolado(montaje):
    cliente, _repo, fabrica, ids, _pub, _sv5 = montaje()

    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    for estado, motivo, *_ in estados_sigrid(fabrica, ids).values():
        assert estado == "encolado"
        assert motivo is None


def test_f002_encolar_sin_lineas_activas_responde_422(montaje):
    cliente, *_ = montaje()
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": [999999]})
    assert r.status_code == 422
    assert r.json()["ok"] is False


# -------------------------------- R5 ----------------------------------- #

def test_f002_r5_pisar_claves_no_entra_por_la_cola(montaje):
    """R5: pisar es destructivo; se rechaza y se manda al camino sincrono."""
    cliente, _repo, fabrica, ids, publisher, _sv5 = montaje()

    r = cliente.post("/api/aprobar/encolar",
                     json={"registro_ids": ids,
                           "pisar_claves": ["501|20260302|1"]})

    assert r.status_code == 422
    assert "ejecutar" in r.json()["error"]
    assert publisher.publicadas == []
    # Y no se ha tocado el estado de ninguna linea.
    assert all(e[0] is None for e in estados_sigrid(fabrica, ids).values())


def test_f002_r5_ejecutar_sigue_registrando_de_forma_sincrona(montaje):
    """R5: el pisado conserva su endpoint y su traza en la misma peticion."""
    cliente, _repo, fabrica, ids, _pub, sv5 = montaje()
    sv5.resultado = {
        "ok": True,
        "escritas": [{"registro_id": ids[0], "hmoide": 901,
                      "parte_cod": "PT26/00001"}],
        "omitidas": [], "ya_registradas": [], "pisadas": ["501|20260302|1"],
    }

    r = cliente.post("/api/aprobar/ejecutar",
                     json={"registro_ids": ids,
                           "pisar_claves": ["501|20260302|1"]})

    assert r.status_code == 200
    assert sv5.ejecutadas[0]["pisar_claves"] == ["501|20260302|1"]
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "registrado"


# -------------------------------- R4 ----------------------------------- #

def test_f002_r4_preflight_sigue_siendo_http_sincrono(montaje):
    cliente, _repo, _f, ids, _pub, sv5 = montaje()

    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})

    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(sv5.preflights) == 1


# ------------------------------ R3 / R14 -------------------------------- #

def test_f002_r3_sin_colas_configuradas_registra_en_sincrono(montaje):
    """R3: sin publisher, el endpoint degrada al flujo HTTP de siempre."""
    cliente, _repo, fabrica, ids, _pub, sv5 = montaje(con_publisher=False)
    sv5.resultado = {"ok": True,
                     "escritas": [{"registro_id": ids[0], "hmoide": 901,
                                   "parte_cod": "PT26/00001"}],
                     "omitidas": [{"registro_id": ids[1],
                                   "motivo": "sin codigo de hora"}],
                     "ya_registradas": []}

    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["modo"] == "sincrono"
    assert cuerpo["ok"] is True
    assert [e["registro_id"] for e in cuerpo["escritas"]] == [ids[0]]
    assert len(sv5.ejecutadas) == 1
    estados = estados_sigrid(fabrica, ids)
    assert estados[ids[0]][0] == "registrado"
    assert estados[ids[1]][0] == "omitido"
    # Nunca se quedan en 'encolado': no hay cola que las recoja.
    assert all(e[0] != "encolado" for e in estados.values())


def test_f002_r3_el_fallback_nunca_pisa_conflictos(montaje):
    """Sin colas se registra en sincrono, pero SIN pisar nada (R5/R10)."""
    cliente, _repo, _f, ids, _pub, sv5 = montaje(con_publisher=False)
    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert sv5.ejecutadas[0]["pisar_claves"] == []


def test_f002_r14_el_fallback_marca_error_si_sv5_falla(montaje):
    """R14: tambien por el camino sincrono el fallo global queda trazado."""
    cliente, _repo, fabrica, ids, _pub, _sv5 = montaje(
        con_publisher=False,
        resultado={"ok": False, "error": "sigrid-api devolvio 500"})

    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    assert r.json()["ok"] is False
    for estado, motivo, *_ in estados_sigrid(fabrica, ids).values():
        assert estado == "error"
        assert "sigrid-api devolvio 500" in motivo


def test_f002_r12_el_camino_sincrono_marca_los_conflictos(montaje):
    """Un conflicto devuelto por sv5 deja la linea en 'conflicto'."""
    cliente, _repo, fabrica, ids, _pub, sv5 = montaje(con_publisher=False)
    sv5.resultado = {"ok": True, "escritas": [], "omitidas": [],
                     "ya_registradas": [],
                     "pendientes_confirmacion": [
                         {"clave": "501|20260302|1", "registros": [ids[0]],
                          "parte_cod": "PT26/00001"}]}

    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "conflicto"


def test_f002_r3_sin_sv5_ni_colas_el_endpoint_avisa(entorno):
    """Sin TRANSFER_BASE_URL no hay a donde registrar: 503, no 500."""
    # Vacia, no ausente: el `.env` del desarrollador tambien la define y
    # `Settings` lo lee.
    entorno.setenv("TRANSFER_BASE_URL", "")  # sin destino sincrono
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=1)
    app = build_app(_settings(), repository=ParteReviewRepository(fabrica),
                    transfer_client=None, publisher=None)

    r = TestClient(app).post("/api/aprobar/encolar",
                             json={"registro_ids": ids})

    assert r.status_code == 503
    assert r.json()["ok"] is False
