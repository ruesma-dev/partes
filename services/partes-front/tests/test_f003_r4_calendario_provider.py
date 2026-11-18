# tests/test_f003_r4_calendario_provider.py
"""R4, R5, R6 · proveedor de calendario del portal (sv4).

El proveedor es quien DECIDE. Desde F-032 los festivos salen de la tabla
`festivos_trabajador` (los escribe sv3 al ingerir) y no de sesame-api: la
cascada de Sesame de F-003 (calendario por defecto en el 404, cache
caducada) desaparece y vive en `test_f032_provider_tabla.py`. Aqui quedan
los casos de F-003 que siguen valiendo con la tabla (festivo por DNI,
`dia()`, `fiable_para`), la jornada del contrato (que si sigue llamando a
Sesame) y el apagado (R7/R27).

Sin red: el cliente es un doble que cuenta llamadas. Sin reloj real: el
proveedor recibe su reloj por parametro.
"""
from __future__ import annotations

from datetime import date

import pytest
from application.services.calendario_provider import CalendarioProvider
from infrastructure.sesame.sesame_api_client import JornadaContrato


class ClienteFake:
    """Doble del `SesameApiClient`: solo `jornada` (R19 de F-032)."""

    def __init__(self, *, jornada=None,
                 fallo: Exception | None = None) -> None:
        self._jornada = jornada
        self.fallo = fallo
        self.llamadas: list[tuple] = []

    def festivos(self, dni: str, ano: int):
        raise AssertionError("sv4 no pide festivos a Sesame (F-032, R19)")

    def calendario_por_defecto(self, ano: int):
        raise AssertionError("ni el calendario por defecto (F-032, R19)")

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


def _fila(dni: str, festivos: dict, ano: int = 2026) -> dict:
    import json
    return {"id": 1, "dni_norm": dni, "ano": ano,
            "festivos_json": json.dumps(festivos),
            "leido_en_utc": "2026-11-17T10:00:00Z"}


SAN_ISIDRO = {"2026-05-15": "San Isidro"}


def _provider(cliente, *, filas=(), reloj=None,
              ttl: int = 21600) -> CalendarioProvider:
    return CalendarioProvider(
        cliente=cliente, respaldo_holiday_name=_respaldo,
        ttl_seconds=ttl, reloj=reloj or Reloj(),
        leer_festivos=lambda: list(filas),
    )


# ------------------------- R1/R2 · festivos por DNI --------------------- #

def test_f003_r4_usa_el_calendario_del_trabajador() -> None:
    p = _provider(ClienteFake(), filas=[_fila("12345678Z", SAN_ISIDRO)])
    nombre = p.holiday_name_para("12345678Z")
    assert nombre(date(2026, 5, 15)) == "San Isidro"
    assert nombre(date(2026, 5, 16)) is None


def test_f003_r4_cada_trabajador_lleva_su_calendario() -> None:
    p = _provider(ClienteFake(), filas=[
        _fila("12345678Z", SAN_ISIDRO),
        _fila("87654321X", {"2026-12-25": "Navidad"})])
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) == "San Isidro"
    assert p.holiday_name_para("87654321X")(date(2026, 5, 15)) is None
    assert p.holiday_name_para("87654321X")(date(2026, 12, 25)) == "Navidad"


def test_f003_r4_festivo_sin_nombre_sigue_siendo_festivo() -> None:
    """La vista pinta el punto si el nombre es truthy: un festivo sin
    nombre en Sesame no puede desaparecer del calendario."""
    p = _provider(ClienteFake(),
                  filas=[_fila("12345678Z", {"2026-05-15": None})])
    assert p.holiday_name_para("12345678Z")(date(2026, 5, 15)) == "Festivo"


def test_f003_r4_el_dni_se_normaliza_antes_de_buscar() -> None:
    p = _provider(ClienteFake(), filas=[_fila("12345678Z", SAN_ISIDRO)])
    assert p.holiday_name_para("12.345.678-z")(date(2026, 5, 15)) ==         "San Isidro"


# ------------------------------- dia() ---------------------------------- #

def test_f003_r4_dia_describe_finde_festivo_y_laborable() -> None:
    p = _provider(ClienteFake(), filas=[_fila("12345678Z", SAN_ISIDRO)])
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
    """La tabla solo aporta festivos: sabado y domingo salen de la fecha."""
    cliente = ClienteFake()
    p = _provider(cliente, filas=[_fila("12345678Z", {})])
    assert p.dia(date(2026, 5, 17), "12345678Z").fin_de_semana is True
    assert cliente.llamadas == []


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


def test_f003_r4_jornada_que_falla_no_revienta() -> None:
    p = _provider(ClienteFake(fallo=ValueError("cliente roto")))
    assert p.jornada_contrato("12345678Z") is None


@pytest.mark.parametrize("ttl", [0, -1])
def test_f003_r6_ttl_no_positivo_no_cachea_la_jornada(ttl) -> None:
    cliente = ClienteFake(jornada=JornadaContrato("Parcial", True, "Indef"))
    p = _provider(cliente, ttl=ttl)
    p.jornada_contrato("12345678Z")
    p.jornada_contrato("12345678Z")
    assert len(cliente.llamadas) == 2


def test_f003_r6_justo_en_el_ttl_la_jornada_ya_ha_caducado() -> None:
    """El limite es cerrado: a los TTL segundos exactos se refresca."""
    reloj = Reloj()
    cliente = ClienteFake(jornada=JornadaContrato("Parcial", True, "Indef"))
    p = _provider(cliente, reloj=reloj, ttl=100)
    p.jornada_contrato("12345678Z")
    reloj.avanza(99)
    p.jornada_contrato("12345678Z")
    assert len(cliente.llamadas) == 1
    reloj.avanza(1)
    p.jornada_contrato("12345678Z")
    assert len(cliente.llamadas) == 2


# ------------------- R7/R27 · Sesame no configurado --------------------- #

def test_f003_r7_sin_cliente_todo_sale_del_respaldo() -> None:
    p = _provider(None)
    nombre = p.holiday_name_para("12345678Z")
    assert nombre(date(2026, 8, 15)) == "Festivo del respaldo"
    assert nombre(date(2026, 5, 15)) is None
    assert p.jornada_contrato("12345678Z") is None
    assert p.activo is False


def test_f003_r27_sin_cliente_no_hay_degradacion() -> None:
    """Sin Sesame configurado no se avisa de nada: es el estado actual."""
    p = _provider(None)
    assert p.fiable_para([("12345678Z", 2026), (None, 2026)]) is True
    assert p.dia(date(2026, 5, 15), "12345678Z").fiable is True


# ------------------------------ fiable_para ----------------------------- #

def test_f003_r4_fiable_para_lote_vacio_es_fiable() -> None:
    assert _provider(ClienteFake()).fiable_para([]) is True


def test_f003_r4_fiable_para_basta_una_sin_fila() -> None:
    p = _provider(ClienteFake(), filas=[_fila("12345678Z", SAN_ISIDRO)])
    assert p.fiable_para([("12345678Z", 2026)]) is True
    assert p.fiable_para([("12345678Z", 2026), ("11111111A", 2026)]) is False


def test_f003_r4_fiable_para_no_repite_consultas() -> None:
    lecturas = []

    def leer():
        lecturas.append(1)
        return [_fila("12345678Z", SAN_ISIDRO)]

    p = CalendarioProvider(cliente=ClienteFake(),
                           respaldo_holiday_name=_respaldo, reloj=Reloj(),
                           leer_festivos=leer)
    p.fiable_para([("12345678Z", 2026), ("12345678Z", 2026),
                   ("12.345.678 Z", 2026)])
    assert len(lecturas) == 1


def test_f003_r4_el_dia_resuelto_es_inmutable() -> None:
    """Viaja a la plantilla y al JSON: nadie lo retoca por el camino."""
    import dataclasses

    dia = _provider(ClienteFake()).dia(date(2026, 5, 18), None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        dia.festivo = True     # type: ignore[misc]


def test_f003_r4_un_dia_es_fiable_mientras_no_se_diga_lo_contrario() -> None:
    """El valor por defecto importa: un `DiaCalendario` construido sin
    hablar de fiabilidad no puede salir marcado como degradado y
    disparar avisos que nadie ha pedido."""
    from application.services.calendario_provider import DiaCalendario

    dia = DiaCalendario(fecha="2026-05-18", laborable=True,
                        fin_de_semana=False, festivo=False,
                        festivo_nombre=None)
    assert dia.fiable is True
