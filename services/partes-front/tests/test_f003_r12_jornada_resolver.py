# tests/test_f003_r12_jornada_resolver.py
"""R12 · sv4 obtiene la jornada teorica de UN solo resolutor.

La regla del `candef` estaba repetida en tres sitios del portal
(`trabajador_detail`, `obra_detail` y `_sugerida` de
`/api/sigrid/empleados`). Estos tests fijan la regla y comprueban que los
tres usos dan exactamente lo mismo que antes del refactor: la feature
F-003 prepara el enchufe de Sesame, no cambia ningun numero (R15).
"""
from __future__ import annotations

import pytest
from application.services.jornada_resolver import jornada_efectiva
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias


@pytest.mark.parametrize(
    "candef, esperado",
    [
        (None, 8.0),        # Sigrid no informa -> jornada por defecto
        (0.0, 8.0),         # 0 = no informado
        (2.0, 8.0),         # <= minimo -> no valido
        (1.5, 8.0),
        (2.5, 2.5),         # > minimo -> manda Sigrid
        (7.0, 7.0),
        (8.0, 8.0),
        (9.5, 9.5),
    ],
)
def test_f003_r12_regla_candef(candef, esperado) -> None:
    assert jornada_efectiva(candef, minimo=2.0, por_defecto=8.0) == esperado


def test_f003_r12_umbral_es_estricto() -> None:
    """Exactamente el minimo NO es valido; un pelo por encima si."""
    assert jornada_efectiva(2.0, minimo=2.0, por_defecto=8.0) == 8.0
    assert jornada_efectiva(2.01, minimo=2.0, por_defecto=8.0) == 2.01


def test_f003_r12_acepta_texto_y_basura() -> None:
    """El candef llega de Sigrid y de la BBDD: puede venir como texto."""
    assert jornada_efectiva("7.5", minimo=2.0, por_defecto=8.0) == 7.5
    assert jornada_efectiva("", minimo=2.0, por_defecto=8.0) == 8.0
    assert jornada_efectiva("no-numero", minimo=2.0, por_defecto=8.0) == 8.0


def test_f003_r12_respeta_los_parametros() -> None:
    """Ni el minimo ni la jornada por defecto estan cableados dentro."""
    assert jornada_efectiva(None, minimo=1.0, por_defecto=6.5) == 6.5
    assert jornada_efectiva(1.0, minimo=1.0, por_defecto=6.5) == 6.5
    assert jornada_efectiva(3.0, minimo=4.0, por_defecto=6.5) == 6.5


# --------------- los tres usos del portal, contra el mismo -------------- #

@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


class CatalogoEmpleadosFake:
    """Doble del catalogo de Sigrid para `/api/sigrid/empleados`."""

    enabled = True

    def __init__(self, items) -> None:
        self._items = items

    def list(self):
        return self._items


def _monta(entorno, dias):
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, dias)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), app


def test_f003_r12_kpi_de_la_vista_trabajador_usa_la_regla(entorno) -> None:
    """candef 2.0 (<= minimo) -> se muestra 8 h marcado como 'asignado'."""
    cliente, _app = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 8.0, "candef": 2.0},
    ])
    html = cliente.get("/trabajadores/emp-77").text
    assert "candef-asignado" in html
    assert "8 h" in html


def test_f003_r12_kpi_respeta_el_candef_valido(entorno) -> None:
    """candef 7 (> minimo) -> manda Sigrid y NO se marca 'asignado'."""
    cliente, _app = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 7.0, "candef": 7.0},
    ])
    html = cliente.get("/trabajadores/emp-77").text
    assert "candef-asignado" not in html
    assert "7 h" in html


def test_f003_r12_aviso_de_jornada_incompleta_usa_la_regla(entorno) -> None:
    """El 2026-03-02 es lunes: 6 h con jornada efectiva 8 esta incompleto.

    Con candef 2.0 la jornada efectiva es 8 (no 2): sin la regla, 6 h
    quedarian POR ENCIMA de la jornada y no habria aviso.
    """
    cliente, _app = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 6.0, "candef": 2.0},
    ])
    html = cliente.get("/trabajadores/emp-77").text
    assert "cal-warn" in html

    cliente2, _ = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 6.0, "candef": 5.0},
    ])
    # candef 5 valido y 6 h por encima: ningun aviso.
    assert "cal-warn" not in cliente2.get("/trabajadores/emp-77").text


def test_f003_r12_matriz_de_obra_usa_la_regla(entorno) -> None:
    cliente, _app = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 6.0, "candef": 2.0},
    ])
    html = cliente.get("/obras/obr-10?period=2026-03&modo=natural").text
    assert "mx-warn" in html


def test_f003_r12_jornada_sugerida_del_lookup_usa_la_regla(entorno) -> None:
    from types import SimpleNamespace

    from interface_adapters.web import app as modulo_app

    catalogo = CatalogoEmpleadosFake([
        SimpleNamespace(ide=1, codigo="E1", nombre="A", dni="1A", reside=1,
                        categoria="Oficial", candef=None),
        SimpleNamespace(ide=2, codigo="E2", nombre="B", dni="2B", reside=2,
                        categoria="Peon", candef=2.0),
        SimpleNamespace(ide=3, codigo="E3", nombre="C", dni="3C", reside=3,
                        categoria="Peon", candef=7.5),
    ])
    entorno.setattr(modulo_app, "EmpleadoCatalog",
                    lambda **_kw: catalogo)
    cliente, _app = _monta(entorno, [
        {"fecha": "2026-03-02", "horas": 8.0, "candef": 8.0},
    ])
    datos = cliente.get("/api/sigrid/empleados").json()
    assert [i["jornada_sugerida"] for i in datos["items"]] == [8.0, 8.0, 7.5]
