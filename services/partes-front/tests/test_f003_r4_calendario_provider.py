# tests/test_f003_r4_calendario_provider.py
"""R4, R5, R6 · proveedor de calendario del portal (sv4).

El proveedor es quien DECIDE: el cliente solo traduce HTTP. Aqui se
ejercita la cascada de degradacion (DNI -> calendario por defecto ->
caduco -> respaldo), la cache por (DNI x ano) y la fuente de cada
resolucion, que es lo que sostiene el aviso de las vistas (R22) y el
bloqueo del registro (R23/R24).

Sin red: el cliente es un doble que cuenta llamadas. Sin reloj real: el
proveedor recibe su reloj por parametro.
"""
from __future__ import annotations

import logging
from datetime import date

import pytest
from application.services.calendario_provider import CalendarioProvider
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    JornadaContrato,
)

REYES = FestivoDia(fecha="2026-01-06", nombre="Reyes")
SAN_ISIDRO = FestivoDia(fecha="2026-05-15", nombre="San Isidro")
NAVIDAD = FestivoDia(fecha="2026-12-25", nombre="Navidad")


class ClienteFake:
    """Doble del `SesameApiClient` que cuenta llamadas y sabe reventar."""

    def __init__(self, *, festivos=None, por_defecto=None, jornada=None,
                 fallo: Exception | None = None) -> None:
        self._festivos = festivos
        self._por_defecto = por_defecto
        self._jornada = jornada
        self.fallo = fallo
        self.llamadas: list[tuple] = []

    def festivos(self, dni: str, ano: int):
        self.llamadas.append(("festivos", dni, ano))
        if self.fallo:
            raise self.fallo
        if callable(self._festivos):
            return self._festivos(dni, ano)
        return self._festivos

    def calendario_por_defecto(self, ano: int):
        self.llamadas.append(("por_defecto", ano))
        if self.fallo:
            raise self.fallo
        return self._por_defecto

    def jornada(self, dni: str):
        self.llamadas.append(("jornada", dni))
        if self.fallo:
            raise self.fallo
        return self._jornada


class Reloj:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def avanza(self, segundos: float) -> None:
        self.t += segundos


def _respaldo(d: date) -> str | None:
    """El respaldo actual de sv4 (libreria `holidays`), aqui reducido a
    un unico dia para que se note cuando se usa."""
    return "Festivo del respaldo" if d.isoformat() == "2026-08-15" else None


def _provider(cliente, *, reloj=None, ttl: int = 21600) -> CalendarioProvider:
    return CalendarioProvider(
        cliente=cliente, respaldo_holiday_name=_respaldo,
        ttl_seconds=ttl, reloj=reloj or Reloj(),
    )


# ------------------------- R1/R2 · festivos por DNI --------------------- #

def test_f003_r4_usa_el_calendario_del_trabajador() -> None:
    p = _provider(ClienteFake(festivos=[REYES, SAN_ISIDRO]))
    nombre = p.holiday_name_para("12345678Z")
    assert nombre(date(2026, 5, 15)) == "San Isidro"
    assert nombre(date(2026, 5, 16)) is None


def test_f003_r4_cada_trabajador_lleva_su_calendario() -> None:
    def por_dni(dni: str, _ano: int):
        return [SAN_ISIDRO] if dni == "12345678Z" else [NAVIDAD]

    p = _provider(ClienteFake(festivos=por_dni))
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) == "San Isidro"
    assert p.holiday_name_para("87654321X")(date(2026, 5, 15)) is None
    assert p.holiday_name_para("87654321X")(date(2026, 12, 25)) == "Navidad"


def test_f003_r4_festivo_sin_nombre_sigue_siendo_festivo() -> None:
    """La vista pinta el punto si el nombre es truthy: un festivo sin
    nombre en Sesame no puede desaparecer del calendario."""
    p = _provider(ClienteFake(festivos=[FestivoDia("2026-05-15", None)]))
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) == "Festivo"


def test_f003_r4_el_dni_se_normaliza_antes_de_preguntar() -> None:
    cliente = ClienteFake(festivos=[])
    p = _provider(cliente)
    p.holiday_name_para("12.345.678-z")(date(2026, 5, 15))
    assert cliente.llamadas[0] == ("festivos", "12345678Z", 2026)


# ------------------------ R4 · cascada al por defecto ------------------- #

def test_f003_r4_sin_dni_va_al_calendario_por_defecto() -> None:
    cliente = ClienteFake(por_defecto=[REYES])
    p = _provider(cliente)
    assert p.holiday_name_para(None)(date(2026, 1, 6)) == "Reyes"
    assert cliente.llamadas == [("por_defecto", 2026)]


def test_f003_r4_dni_desconocido_cae_al_por_defecto() -> None:
    """404 de Sesame: responde y el dato del por defecto es fiable."""
    cliente = ClienteFake(festivos=None, por_defecto=[REYES])
    p = _provider(cliente)
    assert p.holiday_name_para("00000000X")(date(2026, 1, 6)) == "Reyes"
    assert cliente.llamadas == [("festivos", "00000000X", 2026),
                                ("por_defecto", 2026)]
    assert p.fiable_para([("00000000X", 2026)]) is True


def test_f003_r4_sin_por_defecto_cae_al_respaldo() -> None:
    cliente = ClienteFake(festivos=None, por_defecto=None)
    p = _provider(cliente)
    nombre = p.holiday_name_para("00000000X")
    assert nombre(date(2026, 8, 15)) == "Festivo del respaldo"
    assert p.fiable_para([("00000000X", 2026)]) is False


# ---------------------- R5 · stale-while-error y respaldo --------------- #

def test_f003_r5_reutiliza_la_cache_caducada_si_sesame_falla(caplog) -> None:
    reloj = Reloj()
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, reloj=reloj, ttl=100)
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) == "San Isidro"

    reloj.avanza(101)
    cliente.fallo = RuntimeError("sesame-api respondio 502")
    with caplog.at_level(logging.WARNING):
        assert (p.holiday_name_para("12345678Z")(date(2026, 5, 15))
                == "San Isidro")
    assert "caducad" in caplog.text.lower()
    assert p.fiable_para([("12345678Z", 2026)]) is False


def test_f003_r5_sin_cache_previa_usa_el_respaldo(caplog) -> None:
    cliente = ClienteFake(fallo=RuntimeError("sesame-api no responde"))
    p = _provider(cliente)
    with caplog.at_level(logging.WARNING):
        nombre = p.holiday_name_para("12345678Z")
        assert nombre(date(2026, 8, 15)) == "Festivo del respaldo"
        assert nombre(date(2026, 5, 15)) is None
    assert "respaldo" in caplog.text.lower()
    assert p.fiable_para([("12345678Z", 2026)]) is False


def test_f003_r5_ninguna_vista_revienta_por_un_fallo_de_sesame() -> None:
    """Cualquier excepcion del cliente, no solo RuntimeError."""
    p = _provider(ClienteFake(fallo=ValueError("cliente roto")))
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) is None
    assert p.dia(date(2026, 5, 15), "12345678Z").fiable is False
    assert p.jornada_contrato("12345678Z") is None


def test_f003_r5_la_degradacion_no_se_queda_pegada() -> None:
    """Cuando Sesame vuelve, la resolucion vuelve a ser fiable."""
    cliente = ClienteFake(festivos=[SAN_ISIDRO],
                          fallo=RuntimeError("caido"))
    p = _provider(cliente)
    assert p.fiable_para([("12345678Z", 2026)]) is False
    cliente.fallo = None
    assert p.fiable_para([("12345678Z", 2026)]) is True


# ------------------------------ R6 · cache TTL -------------------------- #

def test_f003_r6_no_repite_la_llamada_dentro_del_ttl() -> None:
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, ttl=21600)
    nombre = p.holiday_name_para("12345678Z")
    for _ in range(30):
        nombre(date(2026, 5, 15))
        nombre(date(2026, 5, 16))
    assert len(cliente.llamadas) == 1


def test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar() -> None:
    reloj = Reloj()
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, reloj=reloj, ttl=100)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    reloj.avanza(99)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    assert len(cliente.llamadas) == 1
    reloj.avanza(2)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    assert len(cliente.llamadas) == 2


def test_f003_r6_la_cache_es_por_dni_y_por_ano() -> None:
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    p.holiday_name_para("12345678Z")(date(2027, 5, 15))
    p.holiday_name_para("87654321X")(date(2026, 5, 15))
    assert [l[1:] for l in cliente.llamadas] == [
        ("12345678Z", 2026), ("12345678Z", 2027), ("87654321X", 2026)]


# ------------------------------- dia() ---------------------------------- #

def test_f003_r4_dia_describe_finde_festivo_y_laborable() -> None:
    p = _provider(ClienteFake(festivos=[SAN_ISIDRO]))
    # 2026-05-15 es viernes y festivo.
    festivo = p.dia(date(2026, 5, 15), "12345678Z")
    assert (festivo.fecha, festivo.laborable, festivo.fin_de_semana,
            festivo.festivo, festivo.festivo_nombre) == (
        "2026-05-15", False, False, True, "San Isidro")
    # 2026-05-16 es sabado.
    sabado = p.dia(date(2026, 5, 16), "12345678Z")
    assert (sabado.laborable, sabado.fin_de_semana, sabado.festivo) == (
        False, True, False)
    # 2026-05-18 es lunes normal.
    lunes = p.dia(date(2026, 5, 18), "12345678Z")
    assert (lunes.laborable, lunes.fin_de_semana, lunes.festivo) == (
        True, False, False)


def test_f003_r4_el_finde_se_calcula_en_local() -> None:
    """Sesame solo aporta festivos: sabado y domingo salen de la fecha."""
    cliente = ClienteFake(festivos=[])
    p = _provider(cliente)
    assert p.dia(date(2026, 5, 17), "12345678Z").fin_de_semana is True
    assert len(cliente.llamadas) == 1   # y aun asi resuelve festivos


# ---------------------------- jornada del contrato ---------------------- #

def test_f003_r4_jornada_del_contrato_se_cachea() -> None:
    cliente = ClienteFake(jornada=JornadaContrato("Parcial", True, "Indef"))
    p = _provider(cliente)
    assert p.jornada_contrato("12345678Z").reducida is True
    assert p.jornada_contrato("12345678Z").reducida is True
    assert len(cliente.llamadas) == 1


def test_f003_r4_jornada_sin_dni_no_pregunta() -> None:
    cliente = ClienteFake(jornada=JornadaContrato("Parcial", True, "Indef"))
    p = _provider(cliente)
    assert p.jornada_contrato(None) is None
    assert cliente.llamadas == []


# ------------------- R7/R27 · Sesame no configurado --------------------- #

def test_f003_r7_sin_cliente_todo_sale_del_respaldo() -> None:
    p = _provider(None)
    nombre = p.holiday_name_para("12345678Z")
    assert nombre(date(2026, 8, 15)) == "Festivo del respaldo"
    assert nombre(date(2026, 5, 15)) is None
    assert p.jornada_contrato("12345678Z") is None
    assert p.activo is False


def test_f003_r27_sin_cliente_no_hay_degradacion() -> None:
    """Sin Sesame configurado no se bloquea nada: es el estado actual."""
    p = _provider(None)
    assert p.fiable_para([("12345678Z", 2026), (None, 2026)]) is True
    assert p.dia(date(2026, 5, 15), "12345678Z").fiable is True


# ------------------------------ fiable_para ----------------------------- #

def test_f003_r4_fiable_para_lote_vacio_es_fiable() -> None:
    assert _provider(ClienteFake(festivos=[])).fiable_para([]) is True


def test_f003_r4_fiable_para_basta_una_degradada() -> None:
    def por_dni(dni: str, _ano: int):
        if dni == "11111111A":
            raise RuntimeError("502")
        return [SAN_ISIDRO]

    p = _provider(ClienteFake(festivos=por_dni))
    assert p.fiable_para([("12345678Z", 2026)]) is True
    assert p.fiable_para([("12345678Z", 2026), ("11111111A", 2026)]) is False


def test_f003_r4_fiable_para_no_repite_consultas(monkeypatch) -> None:
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente)
    p.fiable_para([("12345678Z", 2026), ("12345678Z", 2026),
                   ("12.345.678 Z", 2026)])
    assert len(cliente.llamadas) == 1


@pytest.mark.parametrize("ttl", [0, -1])
def test_f003_r6_ttl_no_positivo_no_cachea(ttl) -> None:
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, ttl=ttl)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    assert len(cliente.llamadas) == 2


def test_f003_r6_un_ttl_de_un_segundo_si_cachea() -> None:
    """Cualquier TTL positivo cachea; el corte esta en 0, no en 1."""
    reloj = Reloj()
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, reloj=reloj, ttl=1)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    assert len(cliente.llamadas) == 1


def test_f003_r6_justo_en_el_ttl_la_entrada_ya_ha_caducado() -> None:
    """El limite es cerrado: a los TTL segundos exactos se refresca."""
    reloj = Reloj()
    cliente = ClienteFake(festivos=[SAN_ISIDRO])
    p = _provider(cliente, reloj=reloj, ttl=100)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    reloj.avanza(100)
    p.holiday_name_para("12345678Z")(date(2026, 5, 15))
    assert len(cliente.llamadas) == 2


def test_f003_r4_el_dia_resuelto_es_inmutable() -> None:
    """Viaja a la plantilla y al JSON: nadie lo retoca por el camino."""
    import dataclasses

    dia = _provider(ClienteFake(festivos=[])).dia(date(2026, 5, 18), None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        dia.festivo = True     # type: ignore[misc]


def test_f003_r4_un_dia_es_fiable_mientras_no_se_diga_lo_contrario() -> None:
    """El valor por defecto importa: un `DiaCalendario` construido sin
    hablar de fiabilidad no puede salir marcado como degradado y
    disparar bloqueos que nadie ha pedido."""
    from application.services.calendario_provider import DiaCalendario

    dia = DiaCalendario(fecha="2026-05-18", laborable=True,
                        fin_de_semana=False, festivo=False,
                        festivo_nombre=None)
    assert dia.fiable is True
