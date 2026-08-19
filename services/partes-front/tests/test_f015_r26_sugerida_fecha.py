# tests/test_f015_r26_sugerida_fecha.py
"""R26 · «+ Nuevo» puede pedir la jornada de UN dia concreto.

`GET /api/sigrid/empleados` alimenta el desplegable de «+ Nuevo» y trae
`jornada_sugerida` (el candef efectivo) para prerrellenar las horas. Con
F-015 eso ya no es toda la verdad: el viernes de un trabajador de la
cuadrilla son 6 h, no 9. Se anade `jornada_dia` **solo** cuando la
peticion trae `fecha`, para que la respuesta de siempre siga siendo
compatible byte a byte con la que consume el JS de hoy.

Y una fecha mal escrita responde 422, nunca 500: es un desplegable, no
puede tumbar el portal.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web import app as modulo_app
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite
from tests.test_f015_r24_avisos import CalendarioFake

LUNES = "2026-03-16"
VIERNES = "2026-03-20"
SABADO = "2026-03-21"


@dataclass(frozen=True)
class EmpleadoDoble:
    ide: int
    codigo: str
    nombre: str
    dni: str
    reside: int | None
    categoria: str | None
    candef: float | None


EMPLEADOS = [
    EmpleadoDoble(1, "E001", "Trabajador Uno", "12345678Z", 501, "Peon", 9.0),
    EmpleadoDoble(2, "E002", "Trabajador Dos", "00000000T", 502, "Oficial", 8.0),
    EmpleadoDoble(3, "E003", "Trabajador Tres", "11111111H", 503, None, None),
]


class CatalogoDoble:
    def __init__(self, **_kw) -> None:
        self.enabled = True

    def list(self):
        return list(EMPLEADOS)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(modulo_app, "EmpleadoCatalog", CatalogoDoble)
    return monkeypatch


@pytest.fixture
def cliente():
    app = build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(FabricaSesionSqlite()),
        calendario_provider=CalendarioFake(),
    )
    return TestClient(app)


def _items(cliente, params=""):
    respuesta = cliente.get("/api/sigrid/empleados" + params)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    return cuerpo["items"]


# ------------------------- sin `fecha`: como hoy ------------------------ #

def test_f015_r26_sin_fecha_las_claves_son_las_de_siempre(cliente) -> None:
    for item in _items(cliente):
        assert set(item) == {
            "ide", "codigo", "nombre", "dni", "reside", "categoria",
            "candef", "jornada_sugerida",
        }


def test_f015_r26_sin_fecha_la_jornada_sugerida_no_cambia(cliente) -> None:
    sugeridas = {i["ide"]: i["jornada_sugerida"] for i in _items(cliente)}
    assert sugeridas == {1: 9.0, 2: 8.0, 3: 8.0}


# -------------------------- con `fecha` valida -------------------------- #

def test_f015_r26_con_fecha_se_anade_la_jornada_del_dia(cliente) -> None:
    for item in _items(cliente, f"?fecha={VIERNES}"):
        assert "jornada_dia" in item


def test_f015_r26_el_viernes_de_la_cuadrilla_son_seis_horas(cliente) -> None:
    dias = {i["ide"]: i["jornada_dia"] for i in _items(cliente,
                                                      f"?fecha={VIERNES}")}
    assert dias == {1: 6.0, 2: 8.0, 3: 8.0}


def test_f015_r26_el_lunes_es_el_candef(cliente) -> None:
    dias = {i["ide"]: i["jornada_dia"] for i in _items(cliente,
                                                      f"?fecha={LUNES}")}
    assert dias == {1: 9.0, 2: 8.0, 3: 8.0}


def test_f015_r26_la_jornada_sugerida_sigue_siendo_el_candef(cliente) -> None:
    """`jornada_sugerida` NO cambia de significado: lo nuevo es un campo
    aparte, para no romper a quien ya la consume."""
    item = _items(cliente, f"?fecha={VIERNES}")[0]
    assert (item["jornada_sugerida"], item["jornada_dia"]) == (9.0, 6.0)


def test_f015_r26_un_sabado_no_tiene_jornada_ordinaria(cliente) -> None:
    dias = {i["ide"]: i["jornada_dia"] for i in _items(cliente,
                                                      f"?fecha={SABADO}")}
    assert set(dias.values()) == {0.0}


# -------------------------- con `fecha` invalida ------------------------ #

@pytest.mark.parametrize("fecha", ["ayer", "2026-13-01", "20/03/2026", "2026"])
def test_f015_r26_una_fecha_mal_escrita_responde_422(cliente, fecha) -> None:
    respuesta = cliente.get(f"/api/sigrid/empleados?fecha={fecha}")
    assert respuesta.status_code == 422
    assert respuesta.json()["ok"] is False


def test_f015_r26_una_fecha_vacia_se_trata_como_ausente(cliente) -> None:
    for item in _items(cliente, "?fecha="):
        assert "jornada_dia" not in item


def test_f015_r26_nunca_se_devuelve_un_500(cliente) -> None:
    for fecha in ("", "x", "2026-02-30", "0000-00-00"):
        assert cliente.get(
            f"/api/sigrid/empleados?fecha={fecha}").status_code in (200, 422)


# ================= refuerzo tras la campana de mutacion ================= #
# El recorte `str(fecha)[:10]` no lo probaba nadie con una fecha ISO LARGA,
# que es justo lo que manda un `<input type="datetime-local">` o cualquier
# cliente que envie un instante en vez de un dia.

def test_f015_r26_una_fecha_con_hora_se_recorta_al_dia(cliente) -> None:
    dias = {i["ide"]: i["jornada_dia"]
            for i in _items(cliente, "?fecha=2026-03-20T08:30:00")}
    assert dias == {1: 6.0, 2: 8.0, 3: 8.0}


def test_f015_r26_una_fecha_con_zona_horaria_tambien(cliente) -> None:
    dias = {i["ide"]: i["jornada_dia"]
            for i in _items(cliente, "?fecha=2026-03-16T00:00:00%2B01:00")}
    assert dias == {1: 9.0, 2: 8.0, 3: 8.0}


def test_f015_r26_la_fecha_recortada_es_la_del_dia_pedido(cliente) -> None:
    """Sin el recorte, un instante del viernes se leeria como otra cosa (o
    reventaria) y «+ Nuevo» prerrellenaria las horas del dia equivocado."""
    con_hora = {i["ide"]: i["jornada_dia"]
                for i in _items(cliente, "?fecha=2026-03-20T23:59:59")}
    sin_hora = {i["ide"]: i["jornada_dia"]
                for i in _items(cliente, "?fecha=2026-03-20")}
    assert con_hora == sin_hora
