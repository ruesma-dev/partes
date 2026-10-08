# tests/test_f039_nombre_empresa.py
"""F-039 · nombre corto de la empresa en combos y Conciliar (solo sv4).

  - R1-R4: los cuatro endpoints con items de `empresa` (`/api/sigrid/obras`,
    `/api/sigrid/recursos`, `/api/conciliacion/buscar`,
    `/api/sigrid/empleados`) devuelven `empresa_nombre`: el nombre de
    `application/services/empresas.py`, o `""` sin empresa.
  - R5: un numero sin nombre en `NOMBRES_EMPRESA` es «Empresa N».
  - R6-R8: `empresaSufijo` de `static/app.js`, EJECUTADA con node.
  - R9-R10: texto de `app.js` (usos de `empresaSufijo`, sin nombres).
  - R11: los candidatos de Conciliar pintan el nombre con la misma funcion.
  - R12: ningun otro campo de esas respuestas cambia.

Sin red ni PostgreSQL: Sigrid simulado y SQLite en memoria (mismos dobles
que `tests/test_f035_endpoints.py`). Datos SINTETICOS: empresas 1 y 28 (con
nombre), 5 (sin nombre) y ninguna.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from application.services import empresas
from config.settings import Settings
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import (
    EmpleadoOption,
    ObraOption,
    RecursoOption,
)
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f035_endpoints import ENTORNO, SIGRID, LookupFalso

#: empresa -> nombre esperado (5 no tiene nombre; None, sin empresa).
ESPERADO = {1: "Ruesma", 28: "Porsan", 5: "Empresa 5", None: ""}

OBRAS = [ObraOption(ide=100 + i, codigo=f"07{i}", nombre=f"Obra {i}",
                    empresa=emp)
         for i, emp in enumerate(ESPERADO)]
RECURSOS = [RecursoOption(ide=900 + i, codigo=f"MO/000{i}",
                          nombre=f"PERSONA {i} RECURSO", dni=f"0000000{i}T",
                          empresa=emp, categoria="Oficial", candef=8.0)
            for i, emp in enumerate(ESPERADO)]
FICHAS = [EmpleadoOption(ide=10 + i, codigo=f"E1{i}", nombre=f"Ficha {i}",
                         dni=f"1000000{i}X", reside=900 + i, empresa=emp)
          for i, emp in enumerate(ESPERADO)]


class LookupF039(LookupFalso):
    def fetch_obras(self) -> list:
        return list(OBRAS)

    def fetch_empleados(self) -> list:
        return list(FICHAS)

    def fetch_recursos_activos(self) -> list:
        return list(RECURSOS)


def _sembrar(fabrica, leido: str, doc: str, empresa: int | None) -> None:
    ids = sembrar_parte(fabrica, [{"leido": leido}], document_id=doc,
                        empleado_ide=None, empleado_dni="",
                        empleado_nombre=None)
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, doc).empresa = empresa
        for rid in ids:
            s.get(ParteRegistroOrm, rid).empleado_match_method = "none"
        s.commit()


@pytest.fixture
def cliente(monkeypatch) -> TestClient:
    for clave, valor in {**ENTORNO, **SIGRID}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupF039)
    fabrica = FabricaSesionSqlite()
    # Tarjetas de Conciliar: sus partes fijan la empresa por defecto.
    _sembrar(fabrica, "Persona 1 Recurso", "d-porsan", 28)
    _sembrar(fabrica, "Persona 2 Recurso", "d-cinco", 5)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app)


def _por_empresa(items: list[dict]) -> dict:
    return {it["empresa"]: it for it in items}


def _items(cliente: TestClient, url: str) -> list[dict]:
    datos = cliente.get(url).json()
    assert datos["ok"] is True, datos
    return datos["items"]


# ============================ R1-R5 · API ============================== #

def test_f039_r1_obras_lleva_empresa_nombre(cliente) -> None:
    items = _por_empresa(_items(cliente, "/api/sigrid/obras"))
    assert {e: it["empresa_nombre"] for e, it in items.items()} == ESPERADO


def test_f039_r2_recursos_lleva_empresa_nombre(cliente) -> None:
    items = _por_empresa(_items(cliente, "/api/sigrid/recursos"))
    assert {e: it["empresa_nombre"] for e, it in items.items()} == ESPERADO


def test_f039_r2_recursos_filtrados_por_empresa(cliente) -> None:
    (item,) = _items(cliente, "/api/sigrid/recursos?empresa=28")
    assert (item["empresa"], item["empresa_nombre"]) == (28, "Porsan")


def test_f039_r3_buscar_lleva_empresa_nombre(cliente) -> None:
    items = _por_empresa(
        _items(cliente, "/api/conciliacion/buscar?q=recurso"))
    assert {e: it["empresa_nombre"] for e, it in items.items()} == ESPERADO


def test_f039_r4_empleados_lleva_empresa_nombre(cliente) -> None:
    items = _por_empresa(_items(cliente, "/api/sigrid/empleados"))
    assert {e: it["empresa_nombre"] for e, it in items.items()} == ESPERADO


@pytest.mark.parametrize(("numero", "nombre"), [
    (1, "Ruesma"), (28, "Porsan"), (5, "Empresa 5"), (0, "Empresa 0"),
    (None, ""),
])
def test_f039_r5_nombre_empresa_o_vacio(numero, nombre) -> None:
    assert empresas.nombre_empresa_o_vacio(numero) == nombre


def test_f039_r5_empresa_sin_nombre_es_empresa_n(cliente) -> None:
    for url in ("/api/sigrid/obras", "/api/sigrid/recursos",
                "/api/sigrid/empleados", "/api/conciliacion/buscar?q=persona"):
        assert _por_empresa(_items(cliente, url))[5]["empresa_nombre"] \
            == "Empresa 5", url


# ===================== R11 · candidatos de Conciliar ================== #

def _tarjeta(html: str, nombre: str) -> str:
    trozos = re.split(r'(?=<div class="recon-card )', html)
    (trozo,) = [t for t in trozos if f'data-nombre="{nombre}"' in t[:200]]
    return trozo


def _candidatos(tarjeta: str) -> dict[str, str]:
    """`data-empresa` -> HTML de la fila de cada candidato."""
    return dict(re.findall(r'<tr class="recon-cand" data-empresa="([^"]*)">'
                           r'(.*?)</tr>', tarjeta, re.S))


def test_f039_r11_candidatos_conciliar_con_nombre(cliente) -> None:
    html = cliente.get("/conciliacion").text
    porsan = _candidatos(_tarjeta(html, "Persona 1 Recurso"))
    assert "Porsan" in porsan["28"]
    cinco = _candidatos(_tarjeta(html, "Persona 2 Recurso"))
    assert "Empresa 5" in cinco["5"]


def test_f039_r11_misma_funcion_que_los_endpoints(cliente,
                                                  monkeypatch) -> None:
    # Si la funcion cambia, cambian a la vez la API y los candidatos.
    monkeypatch.setattr(app_mod, "nombre_empresa_o_vacio",
                        lambda n: f"<<{n}>>")
    obras = _por_empresa(_items(cliente, "/api/sigrid/obras"))
    assert obras[28]["empresa_nombre"] == "<<28>>"
    tarjeta = _tarjeta(cliente.get("/conciliacion").text, "Persona 1 Recurso")
    assert "&lt;&lt;28&gt;&gt;" in _candidatos(tarjeta)["28"]


# ===================== R12 · resto de campos intacto ================== #

def test_f039_r12_obras_resto_de_campos_intacto(cliente) -> None:
    assert _items(cliente, "/api/sigrid/obras") == [
        {"ide": o.ide, "codigo": o.codigo, "nombre": o.nombre,
         "empresa": o.empresa, "empresa_nombre": ESPERADO[o.empresa]}
        for o in OBRAS
    ]


@pytest.mark.parametrize(("url", "claves"), [
    ("/api/sigrid/recursos",
     {"ide", "codigo", "nombre", "dni", "empresa", "categoria", "candef",
      "jornada_sugerida", "guardar"}),
    ("/api/conciliacion/buscar?q=recurso",
     {"ide", "codigo", "nombre", "dni", "score", "empresa"}),
    ("/api/sigrid/empleados",
     {"ide", "codigo", "nombre", "dni", "reside", "categoria", "candef",
      "jornada_sugerida", "empresa"}),
])
def test_f039_r12_resto_de_campos_intacto(cliente, url, claves) -> None:
    items = _items(cliente, url)
    assert len(items) == len(ESPERADO)
    for it in items:
        assert set(it) == claves | {"empresa_nombre"}, url
    assert {it["empresa"] for it in items} == set(ESPERADO)
