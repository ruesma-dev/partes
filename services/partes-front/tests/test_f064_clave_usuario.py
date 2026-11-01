# tests/test_f064_clave_usuario.py
"""F-064 · R1-R3: la clave de filtros que el servidor pinta en `<body>`.

La clave separa en el navegador los filtros de cada usuario sin dejar su
identidad en claro: son los 16 primeros hexadecimales del SHA-256 del actor
que resuelve `_resolver_identidad` (F-017). Se prueba la funcion pura de
`identidad.py` y el HTML real de `/partes` con `TestClient` (patron de
`test_f022_vistas_seleccion.py`). Sin red; BBDD en SQLite. Usuarios
inventados.
"""
from __future__ import annotations

import hashlib
import re

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.web.identidad import VARIABLES_DESPLIEGUE
from tests.dobles import FabricaSesionSqlite, sembrar_parte

ANA = "ana.prueba@ejemplo.test"
LUIS = "luis.prueba@ejemplo.test"
CABECERA = "X-MS-CLIENT-PRINCIPAL-NAME"


def _sha16(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _clave_filtros():
    # Import diferido: en la fase RED la funcion aun no existe y cada test
    # debe fallar por eso, no la coleccion entera.
    from interface_adapters.web.identidad import clave_filtros
    return clave_filtros


# ====================== R1 / R2 · la funcion pura ======================= #

def test_f064_r1_clave_16_hexadecimales_del_sha256() -> None:
    clave = _clave_filtros()(ANA, "cabecera-name")
    assert re.fullmatch(r"[0-9a-f]{16}", clave)
    assert clave == _sha16(ANA)


def test_f064_r1_clave_determinista_y_distinta_por_actor() -> None:
    clave_filtros = _clave_filtros()
    assert clave_filtros(ANA, "cabecera-name") == clave_filtros(
        ANA, "cabecera-token")
    assert clave_filtros(ANA, "cabecera-name") != clave_filtros(
        LUIS, "cabecera-name")


def test_f064_r2_sin_identidad_desplegado_da_clave_vacia() -> None:
    assert _clave_filtros()("sin-identidad", "sin-identidad-desplegado") == ""


def test_f064_r2_actor_vacio_da_clave_vacia() -> None:
    assert _clave_filtros()("", "local") == ""


def test_f064_r2_en_local_la_clave_sale_del_actor_local() -> None:
    assert _clave_filtros()("local:revisora", "local") == _sha16(
        "local:revisora")


# ======================= R1-R3 · el HTML real ========================== #

@pytest.fixture
def portal(monkeypatch):
    """Fabrica de clientes: cada uno con su app (la senal B de F-017 es
    estado de la app y no debe mezclar los casos)."""
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    for variable in VARIABLES_DESPLIEGUE:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("DEFAULT_REVIEWER", raising=False)

    def nuevo() -> TestClient:
        fabrica = FabricaSesionSqlite()
        sembrar_parte(fabrica, [{"estado": None}])
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app)
    return nuevo


def _atributo(html: str) -> str:
    m = re.search(r'<body[^>]*\sdata-filtros-usuario="([^"]*)"', html)
    assert m, "el <body> no lleva data-filtros-usuario"
    return m.group(1)


def test_f064_r1_r3_dos_usuarios_dos_claves_y_sin_el_actor(portal) -> None:
    html_ana = portal().get("/partes", headers={CABECERA: ANA}).text
    html_luis = portal().get("/partes", headers={CABECERA: LUIS}).text
    assert _atributo(html_ana) == _sha16(ANA)
    assert _atributo(html_luis) == _sha16(LUIS)
    assert _atributo(html_ana) != _atributo(html_luis)
    # R3: el actor en claro no llega al HTML por esta via.
    assert ANA not in html_ana and LUIS not in html_luis


def test_f064_r1_el_mismo_usuario_siempre_la_misma(portal) -> None:
    cliente = portal()
    a = _atributo(cliente.get("/partes", headers={CABECERA: ANA}).text)
    b = _atributo(cliente.get("/obras", headers={CABECERA: ANA}).text)
    assert a == b == _sha16(ANA)


def test_f064_r2_desplegado_sin_cabecera_atributo_vacio(
        portal, monkeypatch) -> None:
    monkeypatch.setenv("CONTAINER_APP_NAME", "ca-prueba")
    assert _atributo(portal().get("/partes").text) == ""


def test_f064_r2_local_sin_cabeceras_clave_del_actor_local(
        portal, monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_REVIEWER", "revisora")
    assert _atributo(portal().get("/partes").text) == _sha16(
        "local:revisora")
