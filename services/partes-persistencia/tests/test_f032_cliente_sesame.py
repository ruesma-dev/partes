# tests/test_f032_cliente_sesame.py
"""F-032 · R17: el cliente de sesame-api de sv3 sigue cubierto sin el
adaptador de F-003.

El adaptador de F-003 (`sesame_calendario_laboral.py`) y su test se retiran
(R17), pero el cliente `SesameApiClient` NO: ahora lo usa el refresco de la
ingesta. Aqui se trasladan, tal cual, los tres tests de F-003 que fijaban
el cliente contra el contrato real y su gemelo de sv4, y se anade el
refresco con el cliente REAL sobre `httpx.MockTransport` (sin red): 404 ⇒
`sin_calendario`; cualquier error de Sesame ⇒ fallo (R5–R8).
"""
from __future__ import annotations

import datetime as dt

import httpx
import pytest

from application.services.refresco_festivos import (
    RefrescoFestivos,
    ResultadoRefresco,
)
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    JornadaContrato,
    SesameApiClient,
)
from tests.dobles import transporte_json
from tests.fixtures_sesame import CALENDARIOS, FESTIVOS_DNI, NO_ENCONTRADO

CLAVE = "clave-de-prueba-no-es-un-secreto"
DNI = "12345678Z"


# ------------- trasladados de test_f003_r8_sesame_calendario ------------ #

def test_f003_r8_el_cliente_de_sv3_habla_el_contrato_real() -> None:
    """Cliente REAL de sv3 sobre `MockTransport`: sin red (R19)."""
    peticiones: list[httpx.Request] = []
    cliente = SesameApiClient(
        base_url="http://sesame.interno:8006", api_key=CLAVE,
        transport=transporte_json({
            "/api/v1/festivos": FESTIVOS_DNI,
            "/api/v1/calendarios-festivos": CALENDARIOS,
        }, registro_llamadas=peticiones))

    assert cliente.festivos("12345678Z", 2026) == [
        FestivoDia("2026-01-01", "Ano Nuevo"),
        FestivoDia("2026-05-15", "San Isidro"),
    ]
    assert cliente.calendario_por_defecto(2026) == [
        FestivoDia("2026-01-06", "Reyes"),
        FestivoDia("2026-12-25", "Navidad"),
    ]
    assert peticiones[0].headers["x-api-key"] == CLAVE


@pytest.mark.parametrize("tipo, valores, campo", [
    (FestivoDia, {"fecha": "2026-05-15", "nombre": "San Isidro"}, "fecha"),
    (JornadaContrato,
     {"tipo": "Parcial", "reducida": True, "tipo_contrato": "Indefinido"},
     "reducida"),
])
def test_f003_r8_los_datos_del_cliente_son_inmutables(
        tipo, valores, campo) -> None:
    """El cliente es GEMELO del de sv4 y tiene que seguir siendolo tambien
    en esto."""
    import dataclasses

    instancia = tipo(**valores)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instancia, campo, "otro")


def test_f003_r8_el_cliente_de_sv3_es_gemelo_del_de_sv4() -> None:
    """Duplicacion TOLERADA (adaptadores por servicio), no divergencia:
    quien toque uno tiene que tocar el otro. Se comparan los cuerpos de
    la clase, sin el docstring del modulo (que si difiere)."""
    import inspect
    from pathlib import Path

    ruta_sv4 = (Path(__file__).resolve().parents[2] / "partes-front"
                / "infrastructure" / "sesame" / "sesame_api_client.py")
    codigo_sv4 = ruta_sv4.read_text(encoding="utf-8")

    for objeto in (SesameApiClient, FestivoDia):
        fuente = inspect.getsource(objeto)
        assert fuente in codigo_sv4, (
            f"{objeto.__name__} ha divergido entre sv3 y sv4: la "
            "duplicacion es tolerada, la divergencia no."
        )


# ------------------ el refresco con el cliente real --------------------- #

class _Repo:
    def __init__(self):
        self.filas: dict = {}

    def leer_todas(self):
        return dict(self.filas)

    def guardar(self, fila):
        self.filas[(fila.dni_norm, fila.ano)] = fila


def _refrescar(respuesta):
    llamadas: list[httpx.Request] = []
    cliente = SesameApiClient(
        base_url="http://sesame.interno:8006", api_key=CLAVE,
        transport=transporte_json({"/api/v1/festivos": respuesta},
                                  registro_llamadas=llamadas))
    repo = _Repo()
    res = RefrescoFestivos(
        cliente=cliente, repositorio=repo, minimo=1,
        ahora_utc=lambda: dt.datetime(2026, 11, 17, tzinfo=dt.timezone.utc),
    ).refrescar([DNI], {2026})
    return res, repo, llamadas


def test_f032_r4_el_refresco_guarda_lo_que_responde_sesame():
    res, repo, llamadas = _refrescar(FESTIVOS_DNI)
    assert res == ResultadoRefresco(1, 0, 0, 0)
    # Solo los del ano: el 2027-01-01 de la respuesta no entra.
    assert dict(repo.filas[(DNI, 2026)].festivos) == {
        "2026-01-01": "Ano Nuevo", "2026-05-15": "San Isidro"}
    assert [r.url.path for r in llamadas] == ["/api/v1/festivos"]


def test_f032_r5_el_404_real_es_sin_calendario():
    res, repo, llamadas = _refrescar((404, NO_ENCONTRADO))
    assert res == ResultadoRefresco(0, 0, 1, 0)
    assert repo.filas == {}
    # Y no se pide el calendario por defecto (DA19 = B).
    assert [r.url.path for r in llamadas] == ["/api/v1/festivos"]


@pytest.mark.parametrize("respuesta", [
    (400, {"detail": "peticion mala"}),
    (401, {"detail": "x-api-key invalida"}),
    (500, "<html>error</html>"),
    (502, {"ok": False, "error": "x"}),
    {"data": []},                       # sin `ok`: no se da por buena
])
def test_f032_r8_cualquier_error_de_sesame_es_fallo(respuesta):
    res, repo, _ = _refrescar(respuesta)
    assert res == ResultadoRefresco(0, 0, 0, 1)
    assert repo.filas == {}
