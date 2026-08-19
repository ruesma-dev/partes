# tests/test_f015_r17_tabla_caida_o_vacia_sv4.py
"""R17 en sv4 · la tabla de excepciones no puede tumbar una vista.

`empleado_jornada` es un accesorio del portal: sin ella, la jornada de
cada dia se sabe derivar del candef. Si la lectura falla, la vista se
sirve igual —nivel 1 de la resiliencia de F-003: informar, no caerse— y
queda un WARNING. Con la tabla VACIA, que es como va a estar mucho
tiempo, no puede haber ni aviso ni diferencia.
"""
from __future__ import annotations

import logging
from datetime import date

import pytest
from application.services.jornada_provider import JornadaEmpleadoProvider
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias

VIERNES = date(2026, 3, 20)
DNI = "12345678Z"


def _que_revienta():
    raise RuntimeError("BBDD caida")


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


# ------------------------------ tabla caida ----------------------------- #

def test_f015_r17_sv4_un_fallo_de_lectura_devuelve_none(caplog) -> None:
    proveedor = JornadaEmpleadoProvider(_que_revienta)
    with caplog.at_level(logging.WARNING):
        assert proveedor.excepcion_para(DNI, VIERNES) is None


def test_f015_r17_sv4_un_fallo_de_lectura_deja_un_warning(caplog) -> None:
    proveedor = JornadaEmpleadoProvider(_que_revienta)
    with caplog.at_level(logging.WARNING):
        proveedor.excepcion_para(DNI, VIERNES)
    assert "empleado_jornada" in caplog.text
    assert "BBDD caida" in caplog.text


def test_f015_r17_sv4_el_fallo_se_avisa_una_vez(caplog) -> None:
    """Una matriz de obra pregunta por cada celda: un aviso por celda
    llenaria el log del portal."""
    proveedor = JornadaEmpleadoProvider(_que_revienta)
    with caplog.at_level(logging.WARNING):
        for dia in range(16, 21):
            proveedor.excepcion_para(DNI, date(2026, 3, dia))
    assert len([m for m in caplog.messages if "empleado_jornada" in m]) == 1


def test_f015_r17_sv4_si_la_lectura_se_recupera_se_vuelve_a_avisar(
        caplog) -> None:
    """Un fallo de hoy no puede silenciar el de la semana que viene."""
    estado = {"falla": True}
    reloj = {"t": 0.0}

    def _cargar():
        if estado["falla"]:
            raise RuntimeError("BBDD caida")
        return []

    proveedor = JornadaEmpleadoProvider(
        _cargar, ttl_seconds=1, reloj=lambda: reloj["t"])
    with caplog.at_level(logging.WARNING):
        proveedor.excepcion_para(DNI, VIERNES)
        estado["falla"] = False
        reloj["t"] += 10
        proveedor.excepcion_para(DNI, VIERNES)
        estado["falla"] = True
        reloj["t"] += 10
        proveedor.excepcion_para(DNI, VIERNES)
    assert len([m for m in caplog.messages if "empleado_jornada" in m]) == 2


# ------------------------------ tabla vacia ----------------------------- #

def test_f015_r17_sv4_la_tabla_vacia_no_avisa_de_nada(caplog) -> None:
    proveedor = JornadaEmpleadoProvider(lambda: [])
    with caplog.at_level(logging.WARNING):
        assert proveedor.excepcion_para(DNI, VIERNES) is None
    assert "empleado_jornada" not in caplog.text


def test_f015_r17_sv4_una_fila_de_otro_tampoco_avisa(caplog) -> None:
    proveedor = JornadaEmpleadoProvider(lambda: [
        {"dni_norm": "00000000T", "jornada_semanal": 48.0,
         "desde": "2026-01-01"},
    ])
    with caplog.at_level(logging.WARNING):
        assert proveedor.excepcion_para(DNI, VIERNES) is None
    assert "empleado_jornada" not in caplog.text


# --------------------------- la vista se sirve -------------------------- #

def test_f015_r17_sv4_la_vista_del_trabajador_se_sirve_con_la_tabla_caida(
        entorno) -> None:
    """Nivel 1 de D2: un portal caido por una tabla accesoria seria peor."""
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-03-20", "horas": 6.0,
                            "candef": 8.0}])
    app = build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(fabrica),
        jornada_provider=JornadaEmpleadoProvider(_que_revienta),
    )
    cliente = TestClient(app)
    assert cliente.get(
        "/trabajadores/emp-77?modo=natural").status_code == 200


def test_f015_r17_sv4_la_matriz_de_obra_se_sirve_con_la_tabla_caida(
        entorno) -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": "2026-03-20", "horas": 6.0,
                            "candef": 8.0}])
    app = build_app(
        Settings(_env_file=None),
        repository=ParteReviewRepository(fabrica),
        jornada_provider=JornadaEmpleadoProvider(_que_revienta),
    )
    cliente = TestClient(app)
    assert cliente.get(
        "/obras/obr-10?period=2026-03&modo=natural").status_code == 200


# ================= refuerzo tras la campana de mutacion ================= #
# El proveedor de sv4 tiene el mismo codigo de descarte y de conteo que el
# de sv3, y los mismos huecos: nadie comprobaba cuantas filas se tiraban ni
# que una fila mala no cambiase los avisos del portal.

def test_f015_r17_sv4_las_filas_mal_formadas_se_ignoran_y_se_cuentan(
        caplog) -> None:
    proveedor = JornadaEmpleadoProvider(lambda: [
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
        {"dni_norm": DNI, "jornada_semanal": None, "desde": "2026-01-01",
         "h_lun": 7.0, "h_mar": 7.0, "h_mie": None, "h_jue": None,
         "h_vie": None, "h_sab": None, "h_dom": None},
        {"dni_norm": "", "jornada_semanal": 42.0, "desde": "2026-01-01"},
    ])
    with caplog.at_level(logging.WARNING):
        excepcion = proveedor.excepcion_para(DNI, VIERNES)
    avisos = [m for m in caplog.messages if "mal formadas" in m]
    assert len(avisos) == 1
    # Prefijo exacto: un contador con el signo cambiado ("-2 fila(s)")
    # colaria con un `in`.
    assert avisos[0].startswith("[jornada-excepciones] 2 fila(s)")
    # La fila buena sigue en pie.
    assert excepcion is not None and excepcion.semanal == 48.0


def test_f015_r17_sv4_sin_filas_malas_no_se_avisa(caplog) -> None:
    proveedor = JornadaEmpleadoProvider(lambda: [
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
    ])
    with caplog.at_level(logging.WARNING):
        proveedor.excepcion_para(DNI, VIERNES)
    assert "mal formadas" not in caplog.text


def test_f015_r17_sv4_una_fila_sin_jornada_ni_patron_se_ignora() -> None:
    """Una fila creada a medias por SQL no puede volverse una excepcion
    vacia que tape la regla del mapa."""
    proveedor = JornadaEmpleadoProvider(lambda: [
        {"dni_norm": DNI, "jornada_semanal": None, "desde": "2026-01-01"},
    ])
    assert proveedor.excepcion_para(DNI, VIERNES) is None


def test_f015_r17_sv4_con_dos_vigencias_solapadas_gana_la_mas_reciente(
) -> None:
    proveedor = JornadaEmpleadoProvider(lambda: [
        {"dni_norm": DNI, "jornada_semanal": 48.0, "desde": "2026-01-01"},
        {"dni_norm": DNI, "jornada_semanal": 30.0, "desde": "2026-03-01"},
    ])
    assert proveedor.excepcion_para(DNI, VIERNES).semanal == 30.0


def test_f015_r17_sv4_la_fila_del_proveedor_es_inmutable() -> None:
    import dataclasses

    from application.services.jornada_provider import JornadaEmpleadoRow

    fila = JornadaEmpleadoRow(dni_norm=DNI, jornada_semanal=48.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fila.jornada_semanal = 1.0


# --------- la cache del proveedor: TTL y deduplicacion del aviso -------- #
# Mas huecos que destapo la campana en la copia de sv4: el TTL por defecto,
# que un TTL de 0 o 1 signifiquen lo que dicen, y que el flag `_avisado`
# haga su trabajo cuando la cache NO lo esta tapando.

def test_f015_r17_sv4_el_ttl_por_defecto_del_proveedor_es_600(
        entorno) -> None:
    """Espejo del de sv3 y del `JORNADA_CACHE_TTL_S` del settings."""
    proveedor = JornadaEmpleadoProvider(lambda: [])
    assert proveedor._ttl == 600
    assert Settings(_env_file=None).jornada_cache_ttl_s == 600


def test_f015_r17_sv4_un_ttl_de_cero_desactiva_la_cache() -> None:
    """TTL 0 = "no caches": cada consulta relee. Si se tomase como "cachea
    para siempre", una excepcion recien cargada no se veria hasta reiniciar
    el portal."""
    llamadas: list[int] = []

    def _cargar():
        llamadas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(_cargar, ttl_seconds=0)
    for _ in range(3):
        proveedor.excepcion_para(DNI, VIERNES)
    assert len(llamadas) == 3


def test_f015_r17_sv4_un_ttl_de_uno_si_cachea() -> None:
    llamadas: list[int] = []
    reloj = {"t": 1000.0}

    def _cargar():
        llamadas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(
        _cargar, ttl_seconds=1, reloj=lambda: reloj["t"])
    for _ in range(3):
        proveedor.excepcion_para(DNI, VIERNES)
    assert len(llamadas) == 1


def test_f015_r17_sv4_el_aviso_no_se_repite_aunque_la_cache_no_lo_tape(
        caplog) -> None:
    """Con TTL 0 la tabla se relee en cada consulta; el aviso sigue siendo
    UNO. Sin el flag, una matriz de obra llenaria el log."""
    llamadas: list[int] = []

    def _cargar():
        llamadas.append(1)
        raise RuntimeError("BBDD caida")

    proveedor = JornadaEmpleadoProvider(_cargar, ttl_seconds=0)
    with caplog.at_level(logging.WARNING):
        for dia in range(16, 21):
            proveedor.excepcion_para(DNI, date(2026, 3, dia))
    assert len(llamadas) == 5            # se releyo de verdad
    assert len([m for m in caplog.messages
                if "empleado_jornada" in m]) == 1
