# tests/test_f017_entorno.py
"""F-017 · R5c: como sabe el proceso si esta desplegado.

Sin variable de configuracion nueva y sin tocar Azure. Dos senales en `OR`:

* **A** — una de las `CONTAINER_APP_*` que la plataforma inyecta.
  **Verificada en el contenedor real** en T0 (2026-08-20): las cuatro
  existen en `ca-sv4-front`. Ya no es un supuesto de plataforma.
* **B** — haber atendido ya alguna peticion con cabecera de Easy Auth desde
  el arranque. Es la red de seguridad de A (`design.md` §4.1).

Lo que este fichero protege es la **asimetria** del fallo: creerse local
estando desplegado ensucia datos de produccion con firmas `local:…`;
creerse desplegado estando en local solo genera WARNINGs inocuos. La senal
B solo puede empujar hacia el lado seguro, y eso se comprueba aqui.

El entorno se FABRICA (`senal_de_despliegue` recibe un `Mapping`), no se
toca el del proceso.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.web.identidad import (
    ACTOR_SIN_IDENTIDAD,
    CABECERA_NOMBRE,
    PREFIJO_LOCAL,
    VARIABLES_DESPLIEGUE,
    senal_de_despliegue,
)
from tests.dobles import FabricaSesionSqlite, sembrar_parte

USUARIO = "ana.ejemplo@ejemplo.invalid"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    for variable in VARIABLES_DESPLIEGUE:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("DEFAULT_REVIEWER", raising=False)
    return monkeypatch


# ====================================================================== #
# Senal A · el entorno del proceso
# ====================================================================== #

def test_f017_r5c_las_cuatro_variables_declaradas() -> None:
    """Las que T0 confirmo en el contenedor, ni una mas ni una menos."""
    assert set(VARIABLES_DESPLIEGUE) == {
        "CONTAINER_APP_NAME", "CONTAINER_APP_REVISION",
        "CONTAINER_APP_REPLICA_NAME", "CONTAINER_APP_HOSTNAME"}


@pytest.mark.parametrize("variable", VARIABLES_DESPLIEGUE)
def test_f017_r5c_deteccion_de_despliegue(variable: str) -> None:
    """Cualquiera de las cuatro, ella sola, prueba el despliegue."""
    assert senal_de_despliegue({variable: "un-valor"}) == variable


def test_f017_r5c_entorno_vacio_no_es_despliegue() -> None:
    assert senal_de_despliegue({}) is None


def test_f017_r5c_un_entorno_normal_de_puesto_local_no_es_despliegue() -> None:
    """Variables corrientes de un portatil: ninguna prueba nada."""
    assert senal_de_despliegue({
        "PATH": "/usr/bin", "HOME": "/home/quien",
        "DEFAULT_REVIEWER": "ana", "PG_PASSWORD": "x",
        "CONTAINER_APP_COSA_INVENTADA": "no-cuenta",
    }) is None


@pytest.mark.parametrize("valor", ["", "   "])
def test_f017_r5c_una_variable_vacia_no_prueba_nada(valor: str) -> None:
    """Presente pero en blanco es indistinguible de ausente."""
    assert senal_de_despliegue({"CONTAINER_APP_NAME": valor}) is None


def test_f017_r5c_devuelve_el_NOMBRE_y_no_el_valor() -> None:
    """R9 y `/whoami` tienen que poder decir POR QUE se cree desplegado.

    Y ademas: el valor podria ser informacion del despliegue; el nombre de
    la variable, no.
    """
    assert senal_de_despliegue(
        {"CONTAINER_APP_NAME": "ca-sv4-front"}) == "CONTAINER_APP_NAME"


def test_f017_r5c_con_varias_presentes_gana_la_primera_declarada() -> None:
    """Resultado estable: dos replicas del mismo despliegue dicen lo mismo."""
    entorno = {v: "x" for v in VARIABLES_DESPLIEGUE}
    assert senal_de_despliegue(entorno) == VARIABLES_DESPLIEGUE[0]


# ====================================================================== #
# Senal B · la evidencia acumulada
# ====================================================================== #

def test_f017_r5c_la_cabecera_vista_es_senal_suficiente() -> None:
    """Sin ninguna variable, haber visto una cabecera ya lo prueba."""
    assert senal_de_despliegue({}, cabecera_vista=True) == "cabecera-vista"


def test_f017_r5c_la_senal_a_manda_sobre_la_b() -> None:
    """A es estable desde el arranque; B solo existe por si A falla."""
    assert senal_de_despliegue(
        {"CONTAINER_APP_NAME": "x"}, cabecera_vista=True
    ) == "CONTAINER_APP_NAME"


def test_f017_r5c_sin_ninguna_senal_no_hay_despliegue() -> None:
    assert senal_de_despliegue({}, cabecera_vista=False) is None


# ====================================================================== #
# La asimetria del fallo (design.md §4.1)
# ====================================================================== #

def _montaje(*, settings=None):
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-entorno")
    repositorio = ParteReviewRepository(fabrica)
    app = build_app(settings or Settings(_env_file=None),
                    repository=repositorio)
    return TestClient(app), fabrica


def _aprobado_por(fabrica) -> str | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, "doc-entorno").approved_by


def test_f017_r5c_la_senal_b_se_aprende_y_corrige_a(monkeypatch) -> None:
    """El agujero de A, cerrado: tras un usuario autenticado ya no hay `local:`.

    Escenario: la plataforma deja de inyectar `CONTAINER_APP_*` (o cambia
    de nombre) y la senal A no llega. La PRIMERA peticion autenticada
    demuestra que hay un Easy Auth delante; desde entonces, una peticion
    sin cabecera ya NO se firma como sesion local.
    """
    cliente, fabrica = _montaje()
    assert senal_de_despliegue(dict()) is None      # A no llega

    # 1) Un usuario autenticado entra: se aprende la senal B.
    cliente.get("/whoami", headers={CABECERA_NOMBRE: USUARIO})

    # 2) Y ahora llega una peticion SIN cabecera: no puede caer en `local:`.
    datos = cliente.get("/whoami").json()
    assert datos["entorno"] == "desplegado"
    assert datos["senal_despliegue"] == "cabecera-vista"
    assert datos["actor"] == ACTOR_SIN_IDENTIDAD
    assert not datos["actor"].startswith(PREFIJO_LOCAL)


def test_f017_r5c_antes_de_ver_ninguna_cabecera_el_proceso_es_local() -> None:
    """La senal B no se presume: hay que haberla ganado."""
    cliente, _ = _montaje()
    datos = cliente.get("/whoami").json()
    assert datos["entorno"] == "local"
    assert datos["senal_despliegue"] is None
    assert datos["actor"].startswith(PREFIJO_LOCAL)


def test_f017_r5c_la_senal_b_tambien_llega_a_la_columna() -> None:
    """No es cosmetica de `/whoami`: cambia lo que se SELLA."""
    cliente, fabrica = _montaje()
    cliente.get("/whoami", headers={CABECERA_NOMBRE: USUARIO})
    cliente.post("/documents/doc-entorno/approve", follow_redirects=False)
    assert _aprobado_por(fabrica) == ACTOR_SIN_IDENTIDAD


def test_f017_r5c_creerse_desplegado_en_local_es_inocuo(monkeypatch) -> None:
    """La otra direccion del fallo: molesta, pero no ensucia nada.

    Alguien exporta `CONTAINER_APP_NAME` en su puesto. Consecuencia: se
    sella `sin-identidad` en vez de `local:…` y salen WARNINGs. Ninguna
    fila queda firmada con un origen falso, que es lo unico grave.
    """
    monkeypatch.setenv("CONTAINER_APP_NAME", "me-lo-he-inventado")
    monkeypatch.setenv("DEFAULT_REVIEWER", "ana")
    cliente, fabrica = _montaje(settings=Settings(_env_file=None))
    cliente.post("/documents/doc-entorno/approve", follow_redirects=False)

    sellado = _aprobado_por(fabrica)
    assert sellado == ACTOR_SIN_IDENTIDAD
    assert "ana" not in sellado
    # Lo importante: NO ha quedado una firma que afirme un origen falso.
    assert not sellado.startswith(PREFIJO_LOCAL)


def test_f017_r5c_una_cabecera_valida_manda_sobre_el_entorno() -> None:
    """Desplegado o no, si hay identidad real es la que se sella."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")
        cliente, fabrica = _montaje()
        cliente.post("/documents/doc-entorno/approve",
                     headers={CABECERA_NOMBRE: USUARIO},
                     follow_redirects=False)
    assert _aprobado_por(fabrica) == USUARIO
