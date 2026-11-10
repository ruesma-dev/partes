# tests/test_f052_vistas.py
"""F-052 en sv4: el botón «Sincronizar con Sigrid» en las vistas (R7, R15,
R27, R30).

- R7: botón en la vista de obra (`obr-`) y de persona (`rec-`), con lo
  que el navegador manda como `ambito` (vista, clave, periodo y modo), y
  el contenedor del panel de resultado.
- R15: deshabilitado, con el motivo, en las claves que no leen Sigrid
  (`cod-`, `nom-`, `sin-obra`; `emp-`, `nom-`, `sin-trabajador`).
- R30: sin `TRANSFER_BASE_URL` no se pinta.
- R27: abrir la vista no llama a sv5 (solo el botón); «Comprobar en
  Sigrid» (F-024) sigue en su sitio.

SQLite en memoria con el repositorio real y un doble de sv5; datos
sintéticos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    worker_key_for_registro,
)
from interface_adapters.web.app import build_app
from jinja2 import Environment, FileSystemLoader
from tests.dobles import FabricaSesionSqlite, sembrar_parte

PLANTILLAS = Path(__file__).resolve().parents[1] / "templates"


class Sv5Mudo:
    """Doble de sv5: apunta cualquier llamada (R27: al abrir, ninguna)."""

    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def __getattr__(self, nombre):
        def _llamada(*_a, **_k):
            self.llamadas.append(nombre)
            return {"ok": True}
        return _llamada


@pytest.fixture
def vista(monkeypatch):
    """`_abrir(url, **sembrar) -> (html, sv5)`."""
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("TRANSFER_BASE_URL", raising=False)

    def _abrir(url_de, *, con_sv5=True, **sembrar):
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, [{"estado": "registrado"}], **sembrar)
        with fabrica.create_session() as s:
            clave = worker_key_for_registro(s.get(ParteRegistroOrm, ids[0]))
        sv5 = Sv5Mudo() if con_sv5 else None
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5)
        r = TestClient(app).get(url_de(clave))
        assert r.status_code == 200, r.text
        return r.text, sv5
    return _abrir


def _boton(html: str) -> str | None:
    m = re.search(r'<button[^>]*id="sincronizar-sigrid"[^>]*>', html,
                  re.DOTALL)
    return m.group(0) if m else None


def _obra(_clave: str, obra_key: str = "obr-10") -> str:
    return f"/obras/{obra_key}?period=2026-03&modo=natural"


def _persona(clave: str) -> str:
    return f"/trabajadores/{clave}?period=2026-03&modo=natural"


def test_f052_r7_boton_en_la_vista_de_obra(vista) -> None:
    html, _ = vista(_obra)
    b = _boton(html)
    assert b is not None and "disabled" not in b
    for attr in ('data-vista="obra"', 'data-obra-key="obr-10"',
                 'data-period="2026-03"', 'data-mode="natural"'):
        assert attr in b
    assert "Sincronizar con Sigrid" in html
    assert 'id="sincronizar-panel"' in html


def test_f052_r7_boton_en_la_vista_de_persona(vista) -> None:
    html, _ = vista(_persona)
    b = _boton(html)
    assert b is not None and "disabled" not in b
    for attr in ('data-vista="trabajador"', 'data-worker-key="rec-501"',
                 'data-period="2026-03"', 'data-mode="natural"'):
        assert attr in b
    assert 'id="sincronizar-panel"' in html


def test_f052_r15_obra_sin_ide_boton_deshabilitado_con_motivo(vista) -> None:
    html, _ = vista(lambda c: _obra(c, "cod-0100"), obra_ide=None)
    b = _boton(html)
    assert b is not None and "disabled" in b
    assert "la obra no esta casada con una obra de Sigrid" in b


@pytest.mark.parametrize("sembrar, prefijo", [
    ({"recurso_ide": None}, "emp-"),
    ({"recurso_ide": None, "empleado_ide": None}, "nom-"),
])
def test_f052_r15_persona_sin_recurso_boton_deshabilitado(vista, sembrar,
                                                          prefijo) -> None:
    claves: list[str] = []

    def _url(clave: str) -> str:
        claves.append(clave)
        return _persona(clave)

    html, _ = vista(_url, **sembrar)
    assert claves[0].startswith(prefijo)
    b = _boton(html)
    assert b is not None and "disabled" in b
    assert "la persona no esta casada con un recurso de Sigrid" in b


@pytest.mark.parametrize("url", [_obra, _persona])
def test_f052_r30_sin_transfer_no_hay_boton(vista, url) -> None:
    html, _ = vista(url, con_sv5=False)
    assert _boton(html) is None
    assert 'id="sincronizar-panel"' not in html


@pytest.mark.parametrize("url", [_obra, _persona])
def test_f052_r27_abrir_la_vista_no_llama_a_sv5(vista, url) -> None:
    html, sv5 = vista(url)
    assert sv5.llamadas == []
    assert 'id="comprobar-sigrid"' in html          # F-024 sigue igual


@pytest.mark.parametrize("plantilla", ["obra_detail.html",
                                       "trabajador_detail.html"])
def test_f052_plantillas_parsean(plantilla) -> None:
    env = Environment(loader=FileSystemLoader(str(PLANTILLAS)))
    env.parse(env.loader.get_source(env, plantilla)[0])
