# tests/test_f003_r1_sesame_client.py
"""R1 y R20 · cliente HTTP de sesame-api en el portal (sv4).

Todo con `httpx.MockTransport`: ni una peticion de red (R19). Las
respuestas son las del contrato real de sesame-api (`fixtures_sesame`).
"""
from __future__ import annotations

import logging

import httpx
import pytest
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    JornadaContrato,
    SesameApiClient,
)
from tests.fixtures_sesame import (
    CALENDARIOS,
    FESTIVOS_DNI,
    JORNADA,
    NO_ENCONTRADO,
    UPSTREAM_KO,
)

CLAVE = "clave-de-prueba-no-es-un-secreto"


def _cliente(responder, *, base_url: str = "http://sesame.interno:8006",
             api_key: str = CLAVE) -> SesameApiClient:
    return SesameApiClient(base_url=base_url, api_key=api_key,
                           transport=httpx.MockTransport(responder))


def _fijo(cuerpo, status: int = 200, *, capturadas: list | None = None):
    def responder(request: httpx.Request) -> httpx.Response:
        if capturadas is not None:
            capturadas.append(request)
        if isinstance(cuerpo, str):
            return httpx.Response(status, text=cuerpo)
        return httpx.Response(status, json=cuerpo)
    return responder


# ------------------------------ construccion ---------------------------- #

def test_f003_r1_exige_base_url_y_clave() -> None:
    with pytest.raises(ValueError):
        SesameApiClient(base_url="", api_key=CLAVE)
    with pytest.raises(ValueError):
        SesameApiClient(base_url="http://x", api_key="")


def test_f003_r1_normaliza_la_base_url() -> None:
    capturadas: list[httpx.Request] = []
    c = _cliente(_fijo(FESTIVOS_DNI, capturadas=capturadas),
                 base_url="http://sesame.interno:8006/")
    c.festivos("12345678Z", 2026)
    assert str(capturadas[0].url).startswith(
        "http://sesame.interno:8006/api/v1/festivos")


# -------------------------------- festivos ------------------------------ #

def test_f003_r1_festivos_manda_dni_y_ano_y_la_clave_en_cabecera() -> None:
    capturadas: list[httpx.Request] = []
    c = _cliente(_fijo(FESTIVOS_DNI, capturadas=capturadas))
    c.festivos("12345678Z", 2026)

    peticion = capturadas[0]
    assert peticion.url.path == "/api/v1/festivos"
    assert dict(peticion.url.params) == {"dni": "12345678Z", "ano": "2026"}
    assert peticion.headers["x-api-key"] == CLAVE
    assert peticion.method == "GET"


def test_f003_r1_festivos_devuelve_solo_los_del_ano_pedido() -> None:
    """La respuesta trae un festivo de 2027: no es del ano consultado."""
    c = _cliente(_fijo(FESTIVOS_DNI))
    assert c.festivos("12345678Z", 2026) == [
        FestivoDia(fecha="2026-01-01", nombre="Ano Nuevo"),
        FestivoDia(fecha="2026-05-15", nombre="San Isidro"),
    ]


def test_f003_r1_festivos_404_devuelve_none_no_lista_vacia() -> None:
    """Distinguir "este DNI no esta en Sesame" de "no tiene festivos" es
    lo que permite caer al calendario por defecto (R4) en vez de dar el
    ano por laborable entero."""
    c = _cliente(_fijo(NO_ENCONTRADO, 404))
    assert c.festivos("00000000X", 2026) is None


def test_f003_r1_festivos_lista_vacia_es_lista_vacia() -> None:
    c = _cliente(_fijo({"ok": True, "total": 0, "data": []}))
    assert c.festivos("12345678Z", 2026) == []


def test_f003_r1_festivos_tolera_fechas_basura() -> None:
    c = _cliente(_fijo({"ok": True, "data": [
        {"fecha": "2026-01-01", "nombre": "Bueno"},
        {"fecha": None, "nombre": "Sin fecha"},
        {"nombre": "Sin clave fecha"},
        "no-es-un-objeto",
        {"fecha": "2026-03-19"},          # sin nombre
    ]}))
    assert c.festivos("12345678Z", 2026) == [
        FestivoDia(fecha="2026-01-01", nombre="Bueno"),
        FestivoDia(fecha="2026-03-19", nombre=None),
    ]


# -------------------------- calendario por defecto ---------------------- #

def test_f003_r1_calendario_por_defecto_toma_el_marcado() -> None:
    c = _cliente(_fijo(CALENDARIOS))
    assert c.calendario_por_defecto(2026) == [
        FestivoDia(fecha="2026-01-06", nombre="Reyes"),
        FestivoDia(fecha="2026-12-25", nombre="Navidad"),
    ]


def test_f003_r1_calendario_por_defecto_sin_marcado_es_none() -> None:
    """Sin calendario por defecto no hay dato fiable: el proveedor tiene
    que enterarse para caer al respaldo, no creerse un ano sin festivos."""
    sin_defecto = {"ok": True, "data": [
        dict(CALENDARIOS["data"][0]),
    ]}
    c = _cliente(_fijo(sin_defecto))
    assert c.calendario_por_defecto(2026) is None


def test_f003_r1_calendario_por_defecto_usa_la_ruta_de_calendarios() -> None:
    capturadas: list[httpx.Request] = []
    c = _cliente(_fijo(CALENDARIOS, capturadas=capturadas))
    c.calendario_por_defecto(2026)
    assert capturadas[0].url.path == "/api/v1/calendarios-festivos"
    assert capturadas[0].headers["x-api-key"] == CLAVE


# -------------------------------- jornada ------------------------------- #

def test_f003_r1_jornada_del_contrato() -> None:
    c = _cliente(_fijo(JORNADA))
    assert c.jornada("12345678Z") == JornadaContrato(
        tipo="Parcial", reducida=True, tipo_contrato="Indefinido")


def test_f003_r1_jornada_404_es_none() -> None:
    c = _cliente(_fijo(NO_ENCONTRADO, 404))
    assert c.jornada("00000000X") is None


def test_f003_r1_jornada_sin_datos_es_none() -> None:
    c = _cliente(_fijo({"ok": True, "empleado": "X", "data": None}))
    assert c.jornada("12345678Z") is None


# ------------------------------- errores -------------------------------- #

@pytest.mark.parametrize("metodo, args", [
    ("festivos", ("12345678Z", 2026)),
    ("calendario_por_defecto", (2026,)),
    ("jornada", ("12345678Z",)),
])
def test_f003_r1_error_502_del_upstream_sube_como_runtimeerror(
        metodo, args) -> None:
    c = _cliente(_fijo(UPSTREAM_KO, 502))
    with pytest.raises(RuntimeError, match="502"):
        getattr(c, metodo)(*args)


def test_f003_r1_clave_invalida_sube_como_runtimeerror() -> None:
    c = _cliente(_fijo({"detail": "x-api-key invalida"}, 401))
    with pytest.raises(RuntimeError, match="401"):
        c.festivos("12345678Z", 2026)


def test_f003_r1_respuesta_no_json_sube_como_runtimeerror() -> None:
    c = _cliente(_fijo("<html>502 Bad Gateway</html>"))
    with pytest.raises(RuntimeError, match="no JSON"):
        c.festivos("12345678Z", 2026)


def test_f003_r1_ok_false_con_200_sube_como_runtimeerror() -> None:
    c = _cliente(_fijo({"ok": False, "error": "algo raro"}))
    with pytest.raises(RuntimeError, match="ok=false"):
        c.festivos("12345678Z", 2026)


def test_f003_r1_una_respuesta_sin_ok_no_se_da_por_buena() -> None:
    """Sin el campo `ok` no es una respuesta de sesame-api: puede ser un
    proxy o un servicio distinto en esa URL. No se interpreta."""
    c = _cliente(_fijo({"data": [{"fecha": "2026-05-15"}]}))
    with pytest.raises(RuntimeError, match="ok=false"):
        c.festivos("12345678Z", 2026)


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 502, 503])
def test_f003_r1_cualquier_status_de_error_sube(status) -> None:
    """400 incluido: el limite es 400, no 401."""
    c = _cliente(_fijo({"detail": "no"}, status))
    with pytest.raises(RuntimeError, match=str(status)):
        c.festivos("12345678Z", 2026)


def test_f003_r1_el_error_lleva_el_cuerpo_de_la_respuesta() -> None:
    """Sin el cuerpo, diagnosticar un 502 de un proxy es imposible."""
    c = _cliente(_fijo("gateway timeout tras 30s", 504))
    with pytest.raises(RuntimeError, match="gateway timeout"):
        c.festivos("12345678Z", 2026)


@pytest.mark.parametrize("tipo", [FestivoDia, JornadaContrato])
def test_f003_r1_los_datos_son_inmutables(tipo) -> None:
    """Van a vivir en una cache compartida entre peticiones: que nadie
    pueda cambiarlos desde una vista."""
    import dataclasses

    valores = {c.name: None for c in dataclasses.fields(tipo)}
    instancia = tipo(**valores)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instancia, dataclasses.fields(tipo)[0].name, "otro")


def test_f003_r1_error_de_red_sube_como_runtimeerror() -> None:
    def revienta(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("conexion rechazada")

    c = _cliente(revienta)
    with pytest.raises(RuntimeError, match="no se pudo consultar"):
        c.festivos("12345678Z", 2026)


# ------------------------- R20 · nunca la clave ------------------------- #

def test_f003_r20_el_log_de_instanciacion_no_lleva_la_clave(caplog) -> None:
    with caplog.at_level(logging.INFO):
        SesameApiClient(base_url="http://sesame.interno:8006",
                        api_key=CLAVE)
    texto = caplog.text
    assert CLAVE not in texto
    assert f"key_len={len(CLAVE)}" in texto


def test_f003_r20_los_errores_no_llevan_la_clave(caplog) -> None:
    c = _cliente(_fijo(UPSTREAM_KO, 502))
    with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError) as exc:
        c.festivos("12345678Z", 2026)
    assert CLAVE not in str(exc.value)
    assert CLAVE not in caplog.text


def test_f003_r20_el_cuerpo_del_error_se_recorta() -> None:
    c = _cliente(_fijo("x" * 5000, 500))
    with pytest.raises(RuntimeError) as exc:
        c.festivos("12345678Z", 2026)
    assert len(str(exc.value)) < 500
