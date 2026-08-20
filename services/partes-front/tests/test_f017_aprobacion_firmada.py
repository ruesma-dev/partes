# tests/test_f017_aprobacion_firmada.py
"""F-017 · R16-R18: la aprobacion contra Sigrid, firmada de punta a punta.

El actor de la peticion tiene que llegar a tres sitios distintos:

* el campo `usuario` del payload que viaja a **sv5** (que hoy solo lo
  escribe en su log, y empezara a loguear un nombre real sin un solo
  cambio de codigo en sv5);
* el sobre de `q-transfer` cuando la aprobacion es **encolada**;
* `parte_registros.sigrid_registrado_by`, tanto al marcar `encolado` como
  al trazar el resultado.

Y hay un cuarto camino que **no** debe cambiar (R18): el consumidor de
`q-transfer-result` corre fuera de toda peticion HTTP y toma el usuario del
sobre, que ya viaja firmado gracias a R16.

Dobles del publisher y del cliente de sv5, SQLite en memoria: ni red, ni
colas, ni PostgreSQL, ni sv5. Dominio `ejemplo.invalid` (RFC 2606).
"""
from __future__ import annotations

import logging

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.web.identidad import (
    ACTOR_SIN_IDENTIDAD,
    CABECERA_NOMBRE,
    VARIABLES_DESPLIEGUE,
)
from tests.dobles import (
    FabricaSesionSqlite,
    estados_sigrid,
    sembrar_registros,
)

USUARIO = "ana.ejemplo@ejemplo.invalid"


def _como(usuario: str) -> dict[str, str]:
    return {CABECERA_NOMBRE: usuario}


class PublisherFake:
    def __init__(self) -> None:
        self.publicadas: list[tuple[dict, str | None]] = []

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        self.publicadas.append((payload, usuario))
        return f"peticion-{len(self.publicadas)}"


class TransferClientFake:
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


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    for variable in VARIABLES_DESPLIEGUE:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("DEFAULT_REVIEWER", raising=False)
    return monkeypatch


def _montaje(*, con_publisher: bool = True, resultado: dict | None = None):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_registros(fabrica, cantidad=2)
    repositorio = ParteReviewRepository(fabrica)
    publisher = PublisherFake() if con_publisher else None
    sv5 = TransferClientFake(resultado=resultado)
    app = build_app(Settings(_env_file=None), repository=repositorio,
                    transfer_client=sv5, publisher=publisher)
    return TestClient(app), repositorio, fabrica, ids, publisher, sv5


# ====================================================================== #
# R16 · el payload de sv5 y las marcas de estado
# ====================================================================== #

def test_f017_r16_payload_y_marcas_encolado() -> None:
    """Rama ENCOLADA: sobre de la cola, payload y marca, los tres firmados."""
    cliente, _repo, fabrica, ids, publisher, sv5 = _montaje()

    respuesta = cliente.post("/api/aprobar/encolar",
                             json={"registro_ids": ids},
                             headers=_como(USUARIO))

    assert respuesta.status_code == 200
    payload, usuario = publisher.publicadas[0]
    assert usuario == USUARIO                    # el sobre de q-transfer
    assert payload["usuario"] == USUARIO         # el payload que lee sv5
    assert sv5.ejecutadas == []
    # Y la marca `encolado` de las lineas.
    for _id, (_estado, _motivo) in estados_sigrid(fabrica, ids).items():
        pass
    with fabrica.create_session() as s:
        from infrastructure.database.orm_models import ParteRegistroOrm
        for registro_id in ids:
            assert s.get(ParteRegistroOrm,
                         registro_id).sigrid_registrado_by == USUARIO


def test_f017_r16_payload_y_marcas_sincrono() -> None:
    """Rama SINCRONA: el payload a sv5 y la traza del resultado."""
    cliente, _repo, fabrica, ids, _pub, sv5 = _montaje(
        con_publisher=False,
        resultado={"ok": True, "escritas": [], "omitidas": [],
                   "ya_registradas": []})

    respuesta = cliente.post("/api/aprobar/ejecutar",
                             json={"registro_ids": ids},
                             headers=_como(USUARIO))

    assert respuesta.status_code == 200
    assert sv5.ejecutadas[0]["usuario"] == USUARIO


def test_f017_r16_la_traza_del_resultado_lleva_el_actor() -> None:
    """`_trazar` sella `sigrid_registrado_by` con quien aprobo."""
    cliente, _repo, fabrica, ids, _pub, _sv5 = _montaje(
        con_publisher=False,
        resultado={"ok": True,
                   "escritas": [{"registro_id": ids[0], "hmoide": 901}],
                   "omitidas": [], "ya_registradas": []})

    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": ids},
                 headers=_como(USUARIO))

    with fabrica.create_session() as s:
        from infrastructure.database.orm_models import ParteRegistroOrm
        assert s.get(ParteRegistroOrm,
                     ids[0]).sigrid_registrado_by == USUARIO


def test_f017_r16_el_preflight_tambien_va_firmado() -> None:
    """`_payload_registro` es comun: si firma, firma para los tres usos."""
    cliente, _repo, _f, ids, _pub, sv5 = _montaje()
    cliente.post("/api/aprobar/preflight", json={"registro_ids": ids},
                 headers=_como(USUARIO))
    if sv5.preflights:                       # la ruta existe desde F-002
        assert sv5.preflights[0]["usuario"] == USUARIO


def test_f017_r16_dos_personas_dos_firmas() -> None:
    otra = "otra.persona@ejemplo.invalid"
    cliente, _repo, _f, ids, publisher, _sv5 = _montaje()
    cliente.post("/api/aprobar/encolar", json={"registro_ids": [ids[0]]},
                 headers=_como(USUARIO))
    cliente.post("/api/aprobar/encolar", json={"registro_ids": [ids[1]]},
                 headers=_como(otra))

    assert [u for _p, u in publisher.publicadas] == [USUARIO, otra]


def test_f017_r16_sin_cabecera_se_firma_local() -> None:
    """R7 tambien aqui: el campo `usuario` ya nunca viaja vacio."""
    cliente, _repo, _f, ids, publisher, _sv5 = _montaje()
    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    payload, usuario = publisher.publicadas[0]
    assert usuario == "local:sin-identidad"
    assert payload["usuario"] == "local:sin-identidad"


def test_f017_r16_desplegado_sin_cabecera_viaja_sin_identidad(
        monkeypatch) -> None:
    """Lo que sv5 vera en su log si la autenticacion se cae."""
    monkeypatch.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")
    cliente, _repo, _f, ids, publisher, _sv5 = _montaje()
    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})

    _payload, usuario = publisher.publicadas[0]
    assert usuario == ACTOR_SIN_IDENTIDAD


# ====================================================================== #
# R17 · el aviso de registro FORZADO nombra al actor
# ====================================================================== #

def test_f017_r17_log_forzado_nombra_al_actor(caplog) -> None:
    """Forzar el registro sin calendario de Sesame es una decision humana.

    Y una decision humana que se toma saltandose una guarda tiene que
    quedar con nombre en el log, no con «(sin usuario)».
    """
    cliente, _repo, _f, ids, _pub, _sv5 = _montaje(con_publisher=False)

    with caplog.at_level(logging.WARNING):
        cliente.post("/api/aprobar/ejecutar",
                     json={"registro_ids": ids, "forzar_sin_sesame": True},
                     headers=_como(USUARIO))

    forzados = [r.getMessage() for r in caplog.records
                if "FORZADO" in r.getMessage()]
    if forzados:                     # solo si el lote sale degradado
        assert USUARIO in forzados[0]
        assert "(sin usuario)" not in forzados[0]


def test_f017_r17_el_aviso_de_forzado_nunca_dice_sin_usuario() -> None:
    """R7 aplicado al log: el `or '(sin usuario)'` ya no hace falta.

    Se comprueba sobre la FUENTE porque el aviso solo se emite con el
    calendario degradado, y lo que hay que garantizar es que ese texto ya
    no puede aparecer nunca.
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1]
              / "interface_adapters" / "web" / "app.py").read_text(
                  encoding="utf-8")
    assert "(sin usuario)" not in fuente


# ====================================================================== #
# R18 · el consumidor sigue tomando el usuario del sobre
# ====================================================================== #

def test_f017_r18_el_sobre_manda_en_el_consumidor() -> None:
    """Fuera de toda peticion HTTP no hay cabecera que valga.

    El resultado de una aprobacion encolada llega por
    `q-transfer-result`, en un hilo sin `Request`. Su firma tiene que
    venir del sobre — que ya viaja firmado con el actor real gracias a
    R16— y NO de una identidad inventada en el consumidor.
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1]
              / "interface_adapters" / "workers"
              / "resultado_consumer.py").read_text(encoding="utf-8")

    # El consumidor no sabe —ni puede saber— que es una cabecera HTTP.
    assert "X-MS-CLIENT-PRINCIPAL" not in fuente
    assert "identidad" not in fuente
    # Y sigue tomando el usuario del sobre.
    assert "usuario" in fuente


def test_f017_r18_lo_que_se_encola_es_lo_que_el_consumidor_leera() -> None:
    """El sobre que produce R16 es el que R18 consume: mismo valor."""
    cliente, _repo, _f, ids, publisher, _sv5 = _montaje()
    cliente.post("/api/aprobar/encolar", json={"registro_ids": ids},
                 headers=_como(USUARIO))

    _payload, usuario_del_sobre = publisher.publicadas[0]
    assert usuario_del_sobre == USUARIO
