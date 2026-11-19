# tests/test_f032_provider_tabla.py
"""F-032 · R18–R20: `CalendarioProvider` lee los festivos de la tabla.

Encendido (F-077: `activo=True`, `FESTIVOS_SESAME_ENABLED`) el proveedor
resuelve con la cascada de lectura (DA19 = B) sobre `festivos_trabajador`:
fila del DNI ⇒ fuente `sesame`, fiable; sin fila o sin DNI ⇒ `sin_fila`,
respaldo `holidays`, NO fiable (solo enciende el aviso). sv4 no tiene
cliente de Sesame (R19 de F-032, R20 de F-077). Una lectura fallida usa el
respaldo como no fiable con un WARNING (R20). Las filas se cachean <= 60 s.
Apagado (`activo=False`): `sin_sesame`, como siempre (R27 de F-003).
"""
from __future__ import annotations

import logging
from datetime import date

import pytest

from application.services.calendario_provider import (
    FUENTES_FIABLES,
    CalendarioProvider,
)

DNI = "12345678Z"
OTRO = "87654321X"


class Tabla:
    """`list_festivos_trabajador` en memoria: lista de dicts."""

    def __init__(self, filas=None, fallo=None):
        self.filas = list(filas or [])
        self.fallo = fallo
        self.lecturas = 0

    def __call__(self):
        self.lecturas += 1
        if self.fallo is not None:
            raise self.fallo
        return list(self.filas)


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _fila(dni=DNI, ano=2026, json_='{"2026-05-15": "San Isidro"}', id_=1):
    return {"id": id_, "dni_norm": dni, "ano": ano, "festivos_json": json_,
            "leido_en_utc": "2026-11-17T10:00:00Z"}


def _respaldo(d: date) -> str | None:
    return "Asuncion (respaldo)" if d.isoformat() == "2026-08-15" else None


def _provider(tabla, *, reloj=None, ttl_tabla_s=60):
    return CalendarioProvider(
        activo=True,
        respaldo_holiday_name=_respaldo, leer_festivos=tabla,
        ttl_tabla_s=ttl_tabla_s, reloj=reloj or Reloj())


# --------------------------------- R18 ---------------------------------- #

def test_f032_r18_fila_del_dni_es_sesame_y_fiable():
    p = _provider(Tabla([_fila()]))
    assert p.holiday_name_para(DNI)(date(2026, 5, 15)) == "San Isidro"
    assert p.holiday_name_para(DNI)(date(2026, 8, 15)) is None
    assert p.fuente_para(DNI, 2026) == "sesame"
    assert p.fiable_para([(DNI, 2026)]) is True
    assert p.dia(date(2026, 5, 15), DNI).fiable is True


def test_f032_r18_dni_sin_normalizar_encuentra_su_fila():
    p = _provider(Tabla([_fila()]))
    assert p.holiday_name_para("12.345.678-z")(date(2026, 5, 15)) == \
        "San Isidro"


def test_f032_r18_festivo_sin_nombre_sigue_siendo_festivo():
    p = _provider(Tabla([_fila(json_='{"2026-05-15": null}')]))
    assert p.holiday_name_para(DNI)(date(2026, 5, 15)) == "Festivo"


def test_f032_r18_dni_sin_fila_es_sin_fila_con_respaldo_no_fiable():
    p = _provider(Tabla([_fila(dni=OTRO)]))
    nombre = p.holiday_name_para(DNI)
    assert nombre(date(2026, 8, 15)) == "Asuncion (respaldo)"
    assert nombre(date(2026, 5, 15)) is None
    assert p.fuente_para(DNI, 2026) == "sin_fila"
    assert p.fiable_para([(DNI, 2026)]) is False
    assert p.dia(date(2026, 8, 15), DNI).fiable is False


@pytest.mark.parametrize("dni", [None, ""])
def test_f032_r18_sin_dni_es_sin_fila_sin_leer_la_tabla(dni):
    tabla = Tabla([_fila()])
    p = _provider(tabla)
    assert p.holiday_name_para(dni)(date(2026, 8, 15)) == \
        "Asuncion (respaldo)"
    assert p.fuente_para(dni, 2026) == "sin_fila"
    assert p.fiable_para([(dni, 2026)]) is False
    assert tabla.lecturas == 0


def test_f032_r18_la_fila_de_otro_ano_no_vale():
    p = _provider(Tabla([_fila(ano=2025, json_='{"2025-05-15": null}')]))
    assert p.fuente_para(DNI, 2026) == "sin_fila"


def test_f032_r18_fiable_para_basta_una_sin_fila():
    p = _provider(Tabla([_fila()]))
    assert p.fiable_para([(DNI, 2026), (OTRO, 2026)]) is False
    assert p.fiable_para([]) is True


def test_f032_r18_fuentes_fiables():
    assert FUENTES_FIABLES == frozenset({"sesame", "sin_sesame"})


def test_f032_r18_una_fila_mal_formada_se_omite_con_warning(caplog):
    p = _provider(Tabla([_fila(json_="roto", id_=7),
                         _fila(dni=OTRO, id_=8)]))
    with caplog.at_level(logging.WARNING):
        assert p.fuente_para(DNI, 2026) == "sin_fila"
        assert p.fuente_para(OTRO, 2026) == "sesame"
    assert "id=7" in caplog.text
    assert DNI not in caplog.text


def test_f032_r18_sin_lector_de_tabla_todo_es_sin_fila():
    p = CalendarioProvider(activo=True,
                           respaldo_holiday_name=_respaldo, reloj=Reloj())
    assert p.fuente_para(DNI, 2026) == "sin_fila"


# --------------------------------- R19 ---------------------------------- #

def test_f032_r19_sv4_no_tiene_a_quien_pedir_festivos():
    """F-077 (R20): sin cliente; el proveedor solo lee la tabla."""
    p = _provider(Tabla([]))
    for d in (date(2026, 5, 15), date(2026, 5, 16)):
        p.holiday_name_para(DNI)(d)
        p.holiday_name_para(None)(d)
        p.dia(d, DNI)
    assert p.fiable_para([(DNI, 2026), (None, 2026)]) is False
    assert not hasattr(p, "_cliente")
    assert not hasattr(p, "jornada_contrato")


# --------------------------------- R20 ---------------------------------- #

def test_f032_r20_lectura_fallida_respaldo_no_fiable_con_warning(caplog):
    p = _provider(Tabla(fallo=RuntimeError(f"bbdd {DNI}")))
    with caplog.at_level(logging.WARNING):
        assert p.holiday_name_para(DNI)(date(2026, 8, 15)) == \
            "Asuncion (respaldo)"
        assert p.fuente_para(DNI, 2026) == "respaldo"
        assert p.fiable_para([(DNI, 2026)]) is False
    avisos = [r.getMessage() for r in caplog.records
              if r.levelno == logging.WARNING]
    assert avisos and all(DNI not in a for a in avisos)


def test_f032_r20_la_lectura_se_recupera():
    tabla = Tabla(fallo=RuntimeError("caida"))
    p = _provider(tabla)
    assert p.fuente_para(DNI, 2026) == "respaldo"
    tabla.fallo = None
    tabla.filas = [_fila()]
    assert p.fuente_para(DNI, 2026) == "sesame"


def test_f032_r20_cache_de_60_s():
    reloj = Reloj()
    tabla = Tabla([_fila()])
    p = _provider(tabla, reloj=reloj)
    for _ in range(10):
        p.holiday_name_para(DNI)(date(2026, 5, 15))
        p.fiable_para([(DNI, 2026), (OTRO, 2026)])
    assert tabla.lecturas == 1
    reloj.t += 59.9
    p.fuente_para(DNI, 2026)
    assert tabla.lecturas == 1
    reloj.t += 0.1
    p.fuente_para(DNI, 2026)
    assert tabla.lecturas == 2


def test_f032_r20_el_ttl_de_la_tabla_por_defecto_es_60():
    reloj = Reloj()
    tabla = Tabla([_fila()])
    p = CalendarioProvider(activo=True,
                           respaldo_holiday_name=_respaldo,
                           leer_festivos=tabla, reloj=reloj)
    p.fuente_para(DNI, 2026)
    reloj.t += 59
    p.fuente_para(DNI, 2026)
    reloj.t += 1
    p.fuente_para(DNI, 2026)
    assert tabla.lecturas == 2


# ------------------------------- apagado -------------------------------- #

def test_f032_r27_apagado_es_sin_sesame_y_no_lee_la_tabla():
    tabla = Tabla([_fila()])
    p = CalendarioProvider(activo=False, respaldo_holiday_name=_respaldo,
                           leer_festivos=tabla, reloj=Reloj())
    assert p.activo is False
    assert p.fuente_para(DNI, 2026) == "sin_sesame"
    assert p.holiday_name_para(DNI)(date(2026, 8, 15)) == \
        "Asuncion (respaldo)"
    assert p.holiday_name_para(DNI)(date(2026, 5, 15)) is None
    assert p.fiable_para([(DNI, 2026), (None, 2026)]) is True
    assert tabla.lecturas == 0
