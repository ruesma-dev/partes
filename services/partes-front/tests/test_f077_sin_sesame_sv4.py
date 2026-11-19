# tests/test_f077_sin_sesame_sv4.py
"""F-077 · R20–R22: sv4 deja de llamar a Sesame y solo lee la tabla.

  - R20: sin cliente de Sesame; `SESAME_API_*` y `SESAME_CACHE_TTL_S` ya no
    se leen (si siguen en un `.env`, se ignoran).
  - R21: `FESTIVOS_SESAME_ENABLED` (defecto `false`) es el interruptor de
    la tabla `festivos_trabajador`: verdadera ⇒ la cascada de F-032
    (`sesame`, `sin_fila`, `respaldo`); falsa ⇒ `sin_sesame` sin leerla.
    Log `[sesame][wiring] CABLEADO festivos=tabla (sv4 no llama a Sesame)`
    o `DESACTIVADO (FESTIVOS_SESAME_ENABLED=false)`. (capa: integracion)
  - R22: la vista de trabajador no pide ni pinta la jornada del contrato
    (fuera el badge «contrato:» y el aviso de divergencia); los KPI y los
    avisos de jornada salen del candef con los mismos numeros que antes de
    F-077 (fotografiados el 2026-11-18). (capa: integracion)

SQLite en memoria; cualquier peticion de red real hace fallar el test.
"""
from __future__ import annotations

import inspect
import logging
import re
from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from application.services.calendario_provider import CalendarioProvider
from config.settings import Settings
from infrastructure.database.orm_models import FestivoTrabajadorOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias

DNI = "12345678Z"            # el de `sembrar_dias`


@pytest.fixture
def base(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    for clave in ("FESTIVOS_SESAME_ENABLED", "SESAME_API_BASE_URL",
                  "SESAME_API_KEY", "SESAME_API_TIMEOUT_S",
                  "SESAME_CACHE_TTL_S", "SESAME_BASE_URL", "SESAME_TOKEN"):
        monkeypatch.delenv(clave, raising=False)

    def prohibido(*_a, **_kw):
        raise AssertionError("los tests no pueden tocar la red")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", prohibido)
    return monkeypatch


def _fabrica(con_fila: bool = True):
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-05-18", "horas": 8.0,
                            "candef": 8.0},
                           {"fecha": "2026-05-19", "horas": 6.0,
                            "candef": 8.0}])
    if con_fila:
        with fabrica.create_session() as s:
            s.add(FestivoTrabajadorOrm(
                dni_norm=DNI, ano=2026,
                festivos_json='{"2026-05-15": "San Isidro"}', n_festivos=1,
                leido_en_utc="2026-11-17T10:00:00Z"))
            s.commit()
    return fabrica


# --------------------------------- R20 ---------------------------------- #

def test_f077_r20_settings_sin_el_bloque_de_la_pasarela(base) -> None:
    base.setenv("SESAME_API_BASE_URL", "http://pasarela.ejemplo.test")
    base.setenv("SESAME_API_KEY", "clave-vieja-de-prueba")
    base.setenv("SESAME_CACHE_TTL_S", "5")
    s = Settings(_env_file=None)
    assert s.sesame_enabled is False
    for viejo in ("sesame_api_base_url", "sesame_api_key",
                  "sesame_api_timeout_s", "sesame_cache_ttl_s"):
        assert not hasattr(s, viejo)


def test_f077_r20_el_proveedor_no_tiene_cliente_ni_jornada() -> None:
    parametros = set(inspect.signature(CalendarioProvider).parameters)
    assert parametros == {"activo", "respaldo_holiday_name", "reloj",
                          "leer_festivos", "ttl_tabla_s"}
    assert not hasattr(CalendarioProvider, "jornada_contrato")
    p = CalendarioProvider(respaldo_holiday_name=lambda d: None)
    assert p.activo is False                     # defecto: apagado


# --------------------------------- R21 ---------------------------------- #

@pytest.mark.parametrize("valor, esperado", [
    ("true", True), ("1", True), ("false", False), ("0", False)])
def test_f077_r21_el_interruptor(base, valor, esperado) -> None:
    base.setenv("FESTIVOS_SESAME_ENABLED", valor)
    s = Settings(_env_file=None)
    assert s.festivos_sesame_enabled is esperado
    assert s.sesame_enabled is esperado


def test_f077_r21_por_defecto_apagado(base) -> None:
    assert Settings(_env_file=None).festivos_sesame_enabled is False


def test_f077_r21_valor_no_booleano_no_arranca(base) -> None:
    base.setenv("FESTIVOS_SESAME_ENABLED", "quizas")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f077_r21_encendido_cascada_de_la_tabla_y_log(base, caplog) -> None:
    base.setenv("FESTIVOS_SESAME_ENABLED", "true")
    with caplog.at_level(logging.INFO):
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(_fabrica()))
    p = app.state.calendario_provider
    assert p.activo is True
    assert p.fuente_para(DNI, 2026) == "sesame"
    assert p.holiday_name_para(DNI)(date(2026, 5, 15)) == "San Isidro"
    assert p.fuente_para("87654321X", 2026) == "sin_fila"
    assert p.fiable_para([("87654321X", 2026)]) is False
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert wiring == ["[sesame][wiring] CABLEADO festivos=tabla "
                      "(sv4 no llama a Sesame)"]


def test_f077_r21_apagado_sin_sesame_sin_leer_la_tabla(base, caplog) -> None:
    lecturas = []
    repo = ParteReviewRepository(_fabrica())
    original = repo.list_festivos_trabajador

    def leer():
        lecturas.append(1)
        return original()

    repo.list_festivos_trabajador = leer          # type: ignore[method-assign]
    with caplog.at_level(logging.INFO):
        app = build_app(Settings(_env_file=None), repository=repo)
    p = app.state.calendario_provider
    assert p.activo is False
    assert p.fuente_para(DNI, 2026) == "sin_sesame"
    assert p.holiday_name_para(DNI)(date(2026, 5, 15)) is None
    assert lecturas == []
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert wiring[0].startswith(
        "[sesame][wiring] DESACTIVADO (FESTIVOS_SESAME_ENABLED=false)")


def test_f077_r21_el_respaldo_si_la_tabla_falla(base) -> None:
    def rota():
        raise RuntimeError("bbdd caida")

    p = CalendarioProvider(activo=True, respaldo_holiday_name=lambda d: None,
                           leer_festivos=rota)
    assert p.fuente_para(DNI, 2026) == "respaldo"


# --------------------------------- R22 ---------------------------------- #

class _ProveedorSinJornada(CalendarioProvider):
    """Si la vista buscara un atributo que el proveedor no tiene (p. ej. la
    jornada del contrato, retirada por F-077), el test revienta: no se
    redefine ningun metodo que ya no exista en produccion."""

    def __getattr__(self, nombre):
        raise AssertionError(f"la vista pide {nombre!r} al proveedor")


#: Los KPI de la vista para las dos lineas sembradas (8 h y 6 h, candef 8)
#: tal como salian ANTES de F-077 (fotografia del 2026-11-18, `dev`).
KPI_ANTES = ["14 h", "0 h", "8 h", "0", "2"]


@pytest.mark.parametrize("activo", [True, False])
def test_f077_r22_vista_sin_contrato_y_con_los_mismos_kpi(base,
                                                          activo) -> None:
    fabrica = _fabrica()
    proveedor = _ProveedorSinJornada(
        activo=activo, respaldo_holiday_name=lambda d: None,
        leer_festivos=ParteReviewRepository(fabrica).list_festivos_trabajador)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=proveedor)
    r = TestClient(app).get("/trabajadores/rec-501?modo=natural")
    assert r.status_code == 200
    html = r.text
    assert "contrato:" not in html
    assert "jornada-contrato" not in html
    assert "jornada-divergencia" not in html
    assert "contrato reducida" not in html
    grid = html[html.index('<div class="stat-grid">'):]
    assert re.findall(r'class="stat-value[^"]*"[^>]*>([^<]*)',
                      grid)[:5] == KPI_ANTES
    assert re.findall(r'jornada-semanal[^>]*>([^<]*)', html) == [
        "40 h h/sem"]
    assert re.findall(r'jornada-ultimo[^>]*>([^<]*)', html) == [
        "ultimo laborable: 8 h h"]
