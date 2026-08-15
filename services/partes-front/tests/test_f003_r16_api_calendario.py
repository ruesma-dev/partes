# tests/test_f003_r16_api_calendario.py
"""R16 · `GET /api/calendario`, el calendario que consume el JS.

Lo necesita «+ Nuevo» para marcar festivos y domingos en su rejilla de
dias antes de crear lineas. Devuelve un dia por fecha del rango y un
campo raiz `fiable`, que es lo que permite al front avisar cuando el
calendario sale del respaldo en vez de Sesame (R22).
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app

from tests.dobles import FabricaSesionSqlite, sembrar_dias
from tests.test_f003_r2_vistas_festivos import ProveedorFake

SAN_ISIDRO = "2026-05-15"     # viernes
FIESTA_DEFECTO = "2026-05-14"  # jueves


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _cliente(entorno, proveedor) -> TestClient:
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": SAN_ISIDRO, "horas": 8.0}])
    return TestClient(build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(fabrica),
        calendario_provider=proveedor))


def _proveedor(**kw) -> ProveedorFake:
    kw.setdefault("por_dni", {"12345678Z": {SAN_ISIDRO}})
    kw.setdefault("por_defecto", {FIESTA_DEFECTO})
    return ProveedorFake(**kw)


# --------------------------- forma de la respuesta ---------------------- #

def test_f003_r16_devuelve_un_dia_por_fecha_del_rango(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    datos = cliente.get(
        "/api/calendario?desde=2026-05-11&hasta=2026-05-17").json()
    assert datos["ok"] is True
    assert [d["fecha"] for d in datos["data"]] == [
        f"2026-05-{n}" for n in range(11, 18)]


def test_f003_r16_cada_dia_trae_los_cinco_campos(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    dia = cliente.get(
        "/api/calendario?desde=2026-05-15&hasta=2026-05-15&dni=12345678Z"
    ).json()["data"][0]
    assert dia == {
        "fecha": SAN_ISIDRO, "laborable": False, "fin_de_semana": False,
        "festivo": True, "festivo_nombre": "Fiesta de prueba",
    }


def test_f003_r16_el_domingo_sale_como_fin_de_semana(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    dia = cliente.get(
        "/api/calendario?desde=2026-05-17&hasta=2026-05-17").json()["data"][0]
    assert (dia["fin_de_semana"], dia["laborable"], dia["festivo"]) == (
        True, False, False)


def test_f003_r16_un_lunes_normal_es_laborable(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    dia = cliente.get(
        "/api/calendario?desde=2026-05-11&hasta=2026-05-11").json()["data"][0]
    assert (dia["laborable"], dia["festivo"], dia["fin_de_semana"]) == (
        True, False, False)


# ------------------------------- el DNI --------------------------------- #

def test_f003_r16_con_dni_usa_el_calendario_de_ese_trabajador(
        entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    datos = cliente.get(
        f"/api/calendario?desde={SAN_ISIDRO}&hasta={SAN_ISIDRO}"
        "&dni=12345678Z").json()
    assert datos["data"][0]["festivo"] is True


def test_f003_r16_sin_dni_usa_el_calendario_por_defecto(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    con_defecto = cliente.get(
        f"/api/calendario?desde={FIESTA_DEFECTO}&hasta={FIESTA_DEFECTO}"
    ).json()["data"][0]
    sin_defecto = cliente.get(
        f"/api/calendario?desde={SAN_ISIDRO}&hasta={SAN_ISIDRO}"
    ).json()["data"][0]
    assert con_defecto["festivo"] is True     # fiesta del por defecto
    assert sin_defecto["festivo"] is False    # esa es solo de Pepe


def test_f003_r16_un_dni_desconocido_no_revienta(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    r = cliente.get(
        f"/api/calendario?desde={SAN_ISIDRO}&hasta={SAN_ISIDRO}"
        "&dni=99999999Z")
    assert r.status_code == 200
    assert r.json()["data"][0]["festivo"] is False


# ------------------------------ validacion ------------------------------ #

@pytest.mark.parametrize("query", [
    "desde=no-es-fecha&hasta=2026-05-15",
    "desde=2026-05-15&hasta=maniana",
    "desde=2026-13-01&hasta=2026-13-02",
    "desde=2026-05-15&hasta=2026-05-14",     # al reves
])
def test_f003_r16_fechas_invalidas_dan_422(entorno, query) -> None:
    cliente = _cliente(entorno, _proveedor())
    r = cliente.get(f"/api/calendario?{query}")
    assert r.status_code == 422
    # El `ok` tambien importa: el JS mira `d.ok` antes que el status.
    assert r.json()["ok"] is False


def test_f003_r16_tolera_una_fecha_con_hora(entorno) -> None:
    """Un `datetime` ISO se recorta a la fecha, como en el resto del
    monorepo: quien llame desde JS con `toISOString()` no se queda fuera."""
    cliente = _cliente(entorno, _proveedor())
    r = cliente.get("/api/calendario?desde=2026-05-15T00:00:00"
                    "&hasta=2026-05-15T23:59:59")
    assert r.status_code == 200
    assert [d["fecha"] for d in r.json()["data"]] == [SAN_ISIDRO]


def test_f003_r16_rango_de_62_dias_pasa(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    r = cliente.get("/api/calendario?desde=2026-01-01&hasta=2026-03-03")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 62


def test_f003_r16_rango_de_63_dias_da_422(entorno) -> None:
    """Sin tope, un cliente pidiendo diez anos tumbaria el proveedor."""
    cliente = _cliente(entorno, _proveedor())
    r = cliente.get("/api/calendario?desde=2026-01-01&hasta=2026-03-04")
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert "62" in r.json()["error"]


def test_f003_r16_faltan_parametros_da_422(entorno) -> None:
    cliente = _cliente(entorno, _proveedor())
    assert cliente.get("/api/calendario").status_code == 422


# ------------------------- R22 · el campo `fiable` ---------------------- #

def test_f003_r16_fiable_true_cuando_todo_sale_de_sesame(entorno) -> None:
    cliente = _cliente(entorno, _proveedor(fiable=True))
    datos = cliente.get(
        "/api/calendario?desde=2026-05-11&hasta=2026-05-17").json()
    assert datos["fiable"] is True


def test_f003_r16_fiable_false_si_alguna_resolucion_degrado(entorno) -> None:
    cliente = _cliente(entorno, _proveedor(fiable=False))
    datos = cliente.get(
        "/api/calendario?desde=2026-05-11&hasta=2026-05-17").json()
    assert datos["fiable"] is False
    assert datos["ok"] is True          # se sirve igual (nivel 1)
    assert len(datos["data"]) == 7


def test_f003_r16_con_sesame_apagado_responde_con_el_respaldo(
        entorno) -> None:
    """R7/R27 extremo a extremo: proveedor REAL sin cliente. El 1 de enero
    es festivo para la libreria `holidays` y `fiable` sigue siendo true,
    porque con la feature apagada no hay nada degradado que avisar."""
    from application.services.calendario_provider import CalendarioProvider

    proveedor = CalendarioProvider(
        cliente=None,
        respaldo_holiday_name=lambda d: (
            "Ano Nuevo" if d.isoformat() == "2026-01-01" else None),
    )
    datos = _cliente(entorno, proveedor).get(
        "/api/calendario?desde=2026-01-01&hasta=2026-01-02").json()
    assert datos["fiable"] is True
    assert [d["festivo"] for d in datos["data"]] == [True, False]
    assert datos["data"][0]["festivo_nombre"] == "Ano Nuevo"


def test_f003_r16_rango_a_caballo_de_dos_anos(entorno) -> None:
    """La cache es por (DNI x ano): el rango puede cruzar el 31/12."""
    cliente = _cliente(entorno, _proveedor())
    datos = cliente.get(
        "/api/calendario?desde=2026-12-30&hasta=2027-01-02").json()
    assert [d["fecha"] for d in datos["data"]] == [
        "2026-12-30", "2026-12-31", "2027-01-01", "2027-01-02"]
