# tests/test_f003_r10_wiring_sv3.py
"""R10 y R8 · el cableado del calendario en sv3.

Con Sesame SIN configurar, sv3 sigue con `JsonCalendarioLaboral` exacto:
la feature se mergea apagada. Con Sesame configurado, el mismo puerto lo
sirve `TablaCalendarioLaboral` (F-032: los festivos guardados en
`festivos_trabajador`, con el JSON de respaldo), y el computo de extras
manda las horas ordinarias de un festivo del trabajador a horas extra sin
enterarse de que ha cambiado la fuente.

`construir_calendario` esta separada del `build_app` a proposito: el
`build_app` de sv3 monta la SessionFactory contra PostgreSQL y no se
puede levantar en la suite, pero el cableado del calendario si tiene que
estar cubierto.
"""
from __future__ import annotations

import logging

import pytest
from application.services.recurso_conciliador import RecursoConciliador
from config.settings import Settings
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from application.services.festivos_guardados import FilaFestivos
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)
from interface_adapters.api.app import construir_calendario
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

VIERNES_FESTIVO = 20260515   # 2026-05-15, festivo de San Isidro
LUNES = 20260518


class _RepoFestivos:
    """`festivos_trabajador` en memoria (F-032)."""

    def __init__(self, filas=None) -> None:
        self.filas = dict(filas or {})

    def leer_todas(self):
        return dict(self.filas)


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


# ------------------------- la propiedad del settings -------------------- #

def test_f003_r10_sesame_enabled_exige_las_dos_variables(entorno) -> None:
    assert Settings(_env_file=None).sesame_enabled is False

    entorno.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    assert Settings(_env_file=None).sesame_enabled is False

    entorno.setenv("SESAME_API_KEY", "clave-de-prueba")
    assert Settings(_env_file=None).sesame_enabled is True


def test_f003_r10_valores_en_blanco_no_activan_sesame(entorno) -> None:
    entorno.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    entorno.setenv("SESAME_API_KEY", "   ")
    assert Settings(_env_file=None).sesame_enabled is False


# ------------------------------- el wiring ------------------------------ #

def test_f003_r10_sin_configurar_se_cablea_el_json_de_siempre(
        entorno, caplog) -> None:
    with caplog.at_level(logging.INFO):
        cal = construir_calendario(Settings(_env_file=None))
    assert isinstance(cal, JsonCalendarioLaboral)
    assert not isinstance(cal, TablaCalendarioLaboral)
    assert "[sesame][wiring] DESACTIVADO" in caplog.text


def test_f003_r10_el_json_no_ofrece_senal_de_degradacion(entorno) -> None:
    """El conciliador la busca por duck-typing: el JSON no la necesita."""
    cal = construir_calendario(Settings(_env_file=None))
    assert getattr(cal, "consumir_degradacion", None) is None


def test_f003_r8_configurado_se_cablea_sesame_con_el_json_de_respaldo(
        entorno, caplog) -> None:
    entorno.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    entorno.setenv("SESAME_API_KEY", "clave-de-prueba")
    with caplog.at_level(logging.INFO):
        cal = construir_calendario(Settings(_env_file=None), _RepoFestivos())
    assert isinstance(cal, TablaCalendarioLaboral)
    assert isinstance(cal._respaldo, JsonCalendarioLaboral)
    assert "[sesame][wiring] CABLEADO" in caplog.text


def test_f003_r8_el_log_de_wiring_no_lleva_la_clave(entorno, caplog) -> None:
    entorno.setenv("SESAME_API_BASE_URL", "http://sesame.interno:8006")
    entorno.setenv("SESAME_API_KEY", "clave-secretisima-de-prueba")
    with caplog.at_level(logging.INFO):
        construir_calendario(Settings(_env_file=None), _RepoFestivos())
    assert "clave-secretisima-de-prueba" not in caplog.text
    # La longitud se comprueba EN LA LINEA DE WIRING, no en cualquier
    # linea del log: el cliente escribe su propio `key_len` al
    # instanciarse y taparia un fallo aqui.
    wiring = [m for m in caplog.messages if "[sesame][wiring]" in m]
    assert len(wiring) == 1
    assert "key_len=27" in wiring[0]
    assert "clave-secretisima-de-prueba" not in wiring[0]


# ---------------- R8 · el efecto en el computo de extras ---------------- #

def _splits(regs, calendario):
    c = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=calendario, jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )
    return c._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs}, indice_reshor(501))


def test_f003_r8_el_festivo_del_trabajador_manda_las_horas_a_extra() -> None:
    regs = [registro(1, fecha_int=VIERNES_FESTIVO, horas=8.0,
                     dni="12345678Z")]
    splits = _splits(regs, CalendarioFake({"12345678Z": {"2026-05-15"}}))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (0.0, 8.0)]


def test_f003_r8_para_quien_no_tiene_ese_festivo_es_dia_normal() -> None:
    """Mismo dia, otro trabajador: jornada incompleta, no dia festivo."""
    regs = [registro(1, fecha_int=VIERNES_FESTIVO, horas=8.0,
                     dni="87654321X")]
    splits = _splits(regs, CalendarioFake({"12345678Z": {"2026-05-15"}}))
    assert splits == []       # 8 h con jornada 8: cuadra


def test_f003_r8_el_dni_del_grupo_llega_al_puerto() -> None:
    calendario = CalendarioFake(set())
    regs = [registro(1, fecha_int=LUNES, horas=8.0, dni=None),
            registro(2, fecha_int=LUNES, horas=2.0, dni="12345678Z")]
    _splits(regs, calendario)
    assert calendario.consultas == [("2026-05-18", "12345678Z")]


def test_f003_r10_sin_calendario_cableado_no_hay_regla_de_festivos() -> None:
    regs = [registro(1, fecha_int=VIERNES_FESTIVO, horas=8.0)]
    assert _splits(regs, None) == []


def test_f003_r8_el_json_de_respaldo_sigue_valiendo() -> None:
    """Con el JSON puro, el 1 de enero es festivo nacional."""
    cal = JsonCalendarioLaboral(path="config/calendario_laboral.json")
    regs = [registro(1, fecha_int=20260101, horas=8.0)]
    splits = _splits(regs, cal)
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (0.0, 8.0)]


def test_f003_r8_el_adaptador_de_sesame_encaja_en_el_conciliador() -> None:
    """Extremo a extremo con el adaptador REAL (F-032: la tabla, sin red)."""
    repo = _RepoFestivos({("12345678Z", 2026): FilaFestivos(
        dni_norm="12345678Z", ano=2026,
        festivos={"2026-05-15": "San Isidro"}, leido_en_utc="t")})
    cal = TablaCalendarioLaboral(repositorio=repo,
                                 respaldo=CalendarioFake(set()))
    regs = [registro(1, fecha_int=VIERNES_FESTIVO, horas=8.0,
                     dni="12345678Z")]
    assert [(s["horas_norm"], s["extra_horas"]) for s in _splits(regs, cal)] \
        == [(0.0, 8.0)]
