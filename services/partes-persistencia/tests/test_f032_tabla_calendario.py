# tests/test_f032_tabla_calendario.py
"""F-032 · R13–R16: `TablaCalendarioLaboral`, el calendario del computo de
extras cuando Sesame esta cableado.

Fin de semana de la fecha; despues la cascada de lectura (DA19 = B): fila
del DNI en `festivos_trabajador` y, sin fila o sin DNI, el JSON de
siempre. Las filas se cachean <= 60 s y `olvidar()` vacia la cache (la
llama el refresco al guardar, R15). Una lectura fallida resuelve con el
JSON y un WARNING, sin senal de degradacion (R16). Nunca habla con Sesame.
"""
from __future__ import annotations

import logging

import pytest

from application.services.festivos_guardados import FilaFestivos
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)

DNI = "12345678Z"
OTRO = "87654321X"
JSON = "config/calendario_laboral.json"

MARTES = "2026-03-17"          # laborable en el JSON
JUEVES_SAN_JOSE = "2026-03-19"
ANO_NUEVO = "2026-01-01"       # festivo nacional del JSON (jueves)
SABADO = "2026-03-21"


class RepoFake:
    def __init__(self, filas=None, fallo=None):
        self.filas = dict(filas or {})
        self.fallo = fallo
        self.lecturas = 0

    def leer_todas(self):
        self.lecturas += 1
        if self.fallo is not None:
            raise self.fallo
        return dict(self.filas)


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _fila(dni=DNI, ano=2026, *fechas):
    return FilaFestivos(dni_norm=dni, ano=ano,
                        festivos={f: None for f in fechas},
                        leido_en_utc="t")


def _cal(repo, reloj=None, ttl_s=60):
    return TablaCalendarioLaboral(
        repositorio=repo, respaldo=JsonCalendarioLaboral(path=JSON),
        ttl_s=ttl_s, reloj=reloj or Reloj())


# --------------------------------- R13 ---------------------------------- #

def test_f032_r13_fin_de_semana_sin_leer_la_tabla():
    repo = RepoFake()
    assert _cal(repo).es_no_laborable(SABADO, dni=DNI) is True
    assert repo.lecturas == 0


def test_f032_r13_fila_del_dni_manda():
    repo = RepoFake({(DNI, 2026): _fila(DNI, 2026, JUEVES_SAN_JOSE)})
    cal = _cal(repo)
    assert cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI) is True
    assert cal.es_no_laborable(MARTES, dni=DNI) is False
    # El JSON dice que Ano Nuevo es festivo, pero la fila manda.
    assert cal.es_no_laborable(ANO_NUEVO, dni=DNI) is False


def test_f032_r13_dni_sin_normalizar_encuentra_su_fila():
    repo = RepoFake({(DNI, 2026): _fila(DNI, 2026, JUEVES_SAN_JOSE)})
    assert _cal(repo).es_no_laborable(JUEVES_SAN_JOSE,
                                      dni="1234-5678 z") is True


def test_f032_r13_dni_sin_fila_usa_el_json():
    repo = RepoFake({(OTRO, 2026): _fila(OTRO, 2026, JUEVES_SAN_JOSE)})
    cal = _cal(repo)
    assert cal.es_no_laborable(ANO_NUEVO, dni=DNI) is True
    assert cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI) is False


def test_f032_r13_la_fila_de_otro_ano_no_vale():
    repo = RepoFake({(DNI, 2025): _fila(DNI, 2025, "2025-03-19")})
    assert _cal(repo).es_no_laborable(ANO_NUEVO, dni=DNI) is True


@pytest.mark.parametrize("dni", [None, "", "  -  "])
def test_f032_r13_sin_dni_usa_el_json_sin_leer_la_tabla(dni):
    repo = RepoFake()
    cal = _cal(repo)
    assert cal.es_no_laborable(ANO_NUEVO, dni=dni) is True
    assert cal.es_no_laborable(MARTES, dni=dni) is False
    assert repo.lecturas == 0


@pytest.mark.parametrize("fecha", ["", "no", None, "2026-02-30"])
def test_f032_r13_fecha_invalida_es_laborable(fecha):
    repo = RepoFake()
    assert _cal(repo).es_no_laborable(fecha, dni=DNI) is False


def test_f032_r13_fecha_con_hora_se_normaliza():
    repo = RepoFake({(DNI, 2026): _fila(DNI, 2026, JUEVES_SAN_JOSE)})
    assert _cal(repo).es_no_laborable(JUEVES_SAN_JOSE + "T08:00:00",
                                      dni=DNI) is True


# --------------------------------- R15 ---------------------------------- #

def test_f032_r15_cache_de_60_s():
    reloj = Reloj()
    repo = RepoFake({(DNI, 2026): _fila(DNI, 2026, JUEVES_SAN_JOSE)})
    cal = _cal(repo, reloj)
    cal.es_no_laborable(MARTES, dni=DNI)
    cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI)
    assert repo.lecturas == 1
    reloj.t += 59.9
    cal.es_no_laborable(MARTES, dni=DNI)
    assert repo.lecturas == 1
    reloj.t += 0.1                       # 60 s justos: caducada
    cal.es_no_laborable(MARTES, dni=DNI)
    assert repo.lecturas == 2


def test_f032_r15_el_ttl_por_defecto_es_60():
    reloj = Reloj()
    repo = RepoFake()
    cal = TablaCalendarioLaboral(repositorio=repo,
                                 respaldo=JsonCalendarioLaboral(path=JSON),
                                 reloj=reloj)
    cal.es_no_laborable(MARTES, dni=DNI)
    reloj.t += 59
    cal.es_no_laborable(MARTES, dni=DNI)
    assert repo.lecturas == 1
    reloj.t += 1
    cal.es_no_laborable(MARTES, dni=DNI)
    assert repo.lecturas == 2


def test_f032_r15_olvidar_fuerza_la_relectura():
    repo = RepoFake()
    cal = _cal(repo)
    assert cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI) is False
    repo.filas[(DNI, 2026)] = _fila(DNI, 2026, JUEVES_SAN_JOSE)
    assert cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI) is False  # cache
    cal.olvidar()
    assert cal.es_no_laborable(JUEVES_SAN_JOSE, dni=DNI) is True
    assert repo.lecturas == 2


# --------------------------------- R16 ---------------------------------- #

def test_f032_r16_lectura_fallida_usa_el_json_con_warning(caplog):
    repo = RepoFake(fallo=RuntimeError(f"bbdd caida {DNI}"))
    cal = _cal(repo)
    with caplog.at_level(logging.WARNING):
        assert cal.es_no_laborable(ANO_NUEVO, dni=DNI) is True
        assert cal.es_no_laborable(MARTES, dni=DNI) is False
    avisos = [r.getMessage() for r in caplog.records
              if r.levelno == logging.WARNING]
    assert avisos and all(DNI not in a for a in avisos)


def test_f032_r16_sin_senal_de_degradacion():
    cal = _cal(RepoFake())
    assert not hasattr(cal, "consumir_degradacion")


def test_f032_r16_respaldo_que_falla_es_laborable(caplog):
    class RespaldoRoto:
        def es_no_laborable(self, *a, **k):
            raise OSError("json")

    cal = TablaCalendarioLaboral(repositorio=RepoFake(),
                                 respaldo=RespaldoRoto(), reloj=Reloj())
    with caplog.at_level(logging.WARNING):
        assert cal.es_no_laborable(MARTES, dni=DNI) is False
    assert "respaldo" in caplog.text


def test_f032_r13_el_respaldo_recibe_la_fecha_y_los_argumentos():
    class RespaldoEspia:
        def __init__(self):
            self.llamadas = []

        def es_no_laborable(self, fecha, **kw):
            self.llamadas.append((fecha, kw))
            return True

    espia = RespaldoEspia()
    cal = TablaCalendarioLaboral(repositorio=RepoFake(), respaldo=espia,
                                 reloj=Reloj())
    assert cal.es_no_laborable(MARTES + "T00:00:00", dni=DNI,
                               localizacion="L", convenio="C") is True
    assert espia.llamadas == [(MARTES, {"dni": DNI, "localizacion": "L",
                                        "convenio": "C"})]
