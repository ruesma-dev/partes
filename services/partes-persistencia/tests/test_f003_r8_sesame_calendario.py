# tests/test_f003_r8_sesame_calendario.py
"""R8 y R9 · el calendario laboral de sv3 con festivos de Sesame.

Aqui el festivo no es cosmetico: en un dia NO laborable el computo manda
TODAS las horas ordinarias a horas extra. Un festivo que falte se paga
como jornada normal, y uno de mas se paga como extra.

Por eso el adaptador nunca puede reventar (la persistencia del parte es
best-effort, R9) pero SI tiene que dejar constancia de cuando ha
resuelto a ciegas: esa es la senal `consumir_degradacion()` que sube el
parte a revision (R26).
"""
from __future__ import annotations

import logging

import httpx
import pytest

from infrastructure.calendario.sesame_calendario_laboral import (
    SesameCalendarioLaboral,
)
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    SesameApiClient,
)
from tests.dobles import CalendarioFake, transporte_json
from tests.fixtures_sesame import CALENDARIOS, FESTIVOS_DNI

SAN_ISIDRO = "2026-05-15"    # viernes
REYES = "2026-01-06"         # martes
SABADO = "2026-05-16"
DOMINGO = "2026-05-17"
LUNES = "2026-05-18"

CLAVE = "clave-de-prueba-no-es-un-secreto"


class ClienteFake:
    def __init__(self, *, festivos=None, por_defecto=None,
                 fallo: Exception | None = None) -> None:
        self._festivos = festivos
        self._por_defecto = por_defecto
        self.fallo = fallo
        self.llamadas: list[tuple] = []

    def festivos(self, dni: str, ano: int):
        self.llamadas.append(("festivos", dni, ano))
        if self.fallo:
            raise self.fallo
        return self._festivos

    def calendario_por_defecto(self, ano: int):
        self.llamadas.append(("por_defecto", ano))
        if self.fallo:
            raise self.fallo
        return self._por_defecto


class Reloj:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def avanza(self, s: float) -> None:
        self.t += s


def _adaptador(cliente, *, respaldo=None, reloj=None, ttl: int = 21600):
    return SesameCalendarioLaboral(
        cliente=cliente,
        respaldo=respaldo or CalendarioFake({REYES}),
        ttl_seconds=ttl, reloj=reloj or Reloj(),
    )


# ---------------------------- R8 · festivos ----------------------------- #

def test_f003_r8_el_festivo_del_trabajador_es_no_laborable() -> None:
    cal = _adaptador(ClienteFake(festivos=[FestivoDia(SAN_ISIDRO, "San Isidro")]))
    assert cal.es_no_laborable(SAN_ISIDRO, dni="12345678Z") is True
    assert cal.es_no_laborable(LUNES, dni="12345678Z") is False


def test_f003_r8_el_finde_se_calcula_en_local() -> None:
    """Sesame solo aporta festivos: sabado y domingo salen de la fecha."""
    cliente = ClienteFake(festivos=[])
    cal = _adaptador(cliente)
    assert cal.es_no_laborable(SABADO, dni="12345678Z") is True
    assert cal.es_no_laborable(DOMINGO, dni="12345678Z") is True
    assert cliente.llamadas == []       # ni se pregunta


def test_f003_r8_cada_trabajador_lleva_su_calendario() -> None:
    def por_dni(dni, _ano):
        return [FestivoDia(SAN_ISIDRO, "San Isidro")] if dni == "12345678Z" \
            else []

    cliente = ClienteFake()
    cliente.festivos = lambda dni, ano: por_dni(dni, ano)  # type: ignore
    cal = _adaptador(cliente)
    assert cal.es_no_laborable(SAN_ISIDRO, dni="12345678Z") is True
    assert cal.es_no_laborable(SAN_ISIDRO, dni="87654321X") is False


def test_f003_r8_el_dni_se_normaliza() -> None:
    cliente = ClienteFake(festivos=[])
    _adaptador(cliente).es_no_laborable(LUNES, dni="12.345.678-z")
    assert cliente.llamadas[0] == ("festivos", "12345678Z", 2026)


def test_f003_r8_sin_dni_usa_el_calendario_por_defecto() -> None:
    cliente = ClienteFake(por_defecto=[FestivoDia(REYES, "Reyes")])
    cal = _adaptador(cliente)
    assert cal.es_no_laborable(REYES, dni=None) is True
    assert cliente.llamadas == [("por_defecto", 2026)]


def test_f003_r8_dni_desconocido_cae_al_por_defecto() -> None:
    cliente = ClienteFake(festivos=None,
                          por_defecto=[FestivoDia(REYES, "Reyes")])
    cal = _adaptador(cliente)
    assert cal.es_no_laborable(REYES, dni="00000000X") is True
    assert cal.consumir_degradacion() is False   # Sesame respondio


def test_f003_r8_la_cache_evita_repetir_la_llamada() -> None:
    cliente = ClienteFake(festivos=[FestivoDia(SAN_ISIDRO, "San Isidro")])
    cal = _adaptador(cliente)
    for _ in range(20):
        cal.es_no_laborable(LUNES, dni="12345678Z")
    assert len(cliente.llamadas) == 1


def test_f003_r8_la_cache_es_por_dni_y_ano() -> None:
    cliente = ClienteFake(festivos=[])
    cal = _adaptador(cliente)
    cal.es_no_laborable("2026-05-18", dni="12345678Z")
    cal.es_no_laborable("2027-05-18", dni="12345678Z")
    cal.es_no_laborable("2026-05-18", dni="87654321X")
    assert [l[1:] for l in cliente.llamadas] == [
        ("12345678Z", 2026), ("12345678Z", 2027), ("87654321X", 2026)]


def test_f003_r8_al_expirar_el_ttl_vuelve_a_preguntar() -> None:
    reloj = Reloj()
    cliente = ClienteFake(festivos=[])
    cal = _adaptador(cliente, reloj=reloj, ttl=100)
    cal.es_no_laborable(LUNES, dni="12345678Z")
    reloj.avanza(101)
    cal.es_no_laborable(LUNES, dni="12345678Z")
    assert len(cliente.llamadas) == 2


# --------------------------- R9 · degradacion --------------------------- #

def test_f003_r9_si_sesame_falla_usa_la_cache_caducada(caplog) -> None:
    reloj = Reloj()
    cliente = ClienteFake(festivos=[FestivoDia(SAN_ISIDRO, "San Isidro")])
    cal = _adaptador(cliente, reloj=reloj, ttl=100)
    assert cal.es_no_laborable(SAN_ISIDRO, dni="12345678Z") is True

    reloj.avanza(101)
    cliente.fallo = RuntimeError("sesame-api respondio 502")
    with caplog.at_level(logging.WARNING):
        assert cal.es_no_laborable(SAN_ISIDRO, dni="12345678Z") is True
    assert cal.consumir_degradacion() is True


def test_f003_r9_sin_cache_previa_usa_el_respaldo(caplog) -> None:
    cliente = ClienteFake(fallo=RuntimeError("sesame-api no responde"))
    cal = _adaptador(cliente, respaldo=CalendarioFake({REYES}))
    with caplog.at_level(logging.WARNING):
        assert cal.es_no_laborable(REYES, dni="12345678Z") is True
        assert cal.es_no_laborable(SAN_ISIDRO, dni="12345678Z") is False
    assert "respaldo" in caplog.text.lower()
    assert cal.consumir_degradacion() is True


def test_f003_r9_nunca_propaga_una_excepcion() -> None:
    """La persistencia del parte NO puede fallar por Sesame."""
    class RespaldoRoto(CalendarioFake):
        def es_no_laborable(self, *_a, **_kw):
            raise RuntimeError("hasta el respaldo esta roto")

    cal = _adaptador(ClienteFake(fallo=ValueError("cliente roto")),
                     respaldo=RespaldoRoto())
    assert cal.es_no_laborable(LUNES, dni="12345678Z") is False
    assert cal.consumir_degradacion() is True


def test_f003_r9_una_fecha_invalida_no_revienta() -> None:
    cal = _adaptador(ClienteFake(festivos=[]))
    assert cal.es_no_laborable("no-es-fecha", dni="12345678Z") is False
    assert cal.es_no_laborable("", dni="12345678Z") is False


def test_f003_r9_sin_calendario_por_defecto_cae_al_respaldo() -> None:
    cal = _adaptador(ClienteFake(festivos=None, por_defecto=None),
                     respaldo=CalendarioFake({REYES}))
    assert cal.es_no_laborable(REYES, dni="00000000X") is True
    assert cal.consumir_degradacion() is True


# ---------------------- R26 · la senal de degradacion ------------------- #

def test_f003_r26_la_senal_se_consume_y_se_resetea() -> None:
    cliente = ClienteFake(fallo=RuntimeError("caido"))
    cal = _adaptador(cliente)
    cal.es_no_laborable(LUNES, dni="12345678Z")
    assert cal.consumir_degradacion() is True
    assert cal.consumir_degradacion() is False


def test_f003_r26_una_resolucion_buena_apaga_la_senal() -> None:
    cliente = ClienteFake(festivos=[])
    cal = _adaptador(cliente)
    cal.es_no_laborable(LUNES, dni="12345678Z")
    assert cal.consumir_degradacion() is False


def test_f003_r26_el_finde_no_es_una_resolucion_degradada() -> None:
    """El sabado sale de la fecha: no hace falta Sesame para saberlo."""
    cal = _adaptador(ClienteFake(fallo=RuntimeError("caido")))
    assert cal.es_no_laborable(SABADO, dni="12345678Z") is True
    assert cal.consumir_degradacion() is False


# ------------------- el cliente gemelo, contra el contrato -------------- #

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


def test_f003_r8_el_adaptador_funciona_con_el_cliente_real() -> None:
    """Cascada completa sin dobles del cliente: solo sin red."""
    cliente = SesameApiClient(
        base_url="http://sesame.interno:8006", api_key=CLAVE,
        transport=transporte_json({"/api/v1/festivos": FESTIVOS_DNI}))
    cal = _adaptador(cliente, respaldo=CalendarioFake(set()))
    assert cal.es_no_laborable("2026-01-01", dni="12345678Z") is True
    assert cal.es_no_laborable(LUNES, dni="12345678Z") is False
    assert cal.consumir_degradacion() is False


@pytest.mark.parametrize("respuesta", [(502, {"ok": False, "error": "x"}),
                                       (500, "<html>error</html>")])
def test_f003_r9_un_sesame_roto_no_tumba_la_persistencia(respuesta) -> None:
    cliente = SesameApiClient(
        base_url="http://sesame.interno:8006", api_key=CLAVE,
        transport=transporte_json({"/api/v1/festivos": respuesta}))
    cal = _adaptador(cliente, respaldo=CalendarioFake({REYES}))
    assert cal.es_no_laborable(REYES, dni="12345678Z") is True
    assert cal.consumir_degradacion() is True
