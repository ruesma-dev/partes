# tests/test_f035_recursos_cliente.py
"""F-035 · R1-R4: el catalogo de RECURSOS ACTIVOS del cliente de sigrid-api.

  - R1: una consulta paginada por `res.ide` con el filtro de alta F-023 a
    hoy sobre el concepto del recurso (`rescon`).
  - R2: cada recurso lleva su codigo/nombre/empresa, el DNI (`res.cif` o,
    vacio, el de la ficha enlazada) y los datos de la ficha (o nulos).
  - R3: el recurso que sigue sin DNI no se ofrece.
  - R4: solo recursos de clase persona (`res.cla = 1`), filtrado en SQL.

Sin red: sigrid-api simulado con `httpx.MockTransport`. Datos SINTETICOS.
"""
from __future__ import annotations

import logging
from datetime import datetime

from infrastructure.sigrid.sigrid_lookup_client import RecursoOption
from tests.test_f023_catalogo_empresa import SigridFalso, _cliente, _sql

PAGINA = 5000

COLS = ["ide", "codigo", "nombre", "empresa", "cif", "empleado_ide",
        "empleado_codigo", "empleado_nombre", "empleado_dni", "categoria",
        "candef"]

#: Cinco recursos (todos clase persona: la clase la filtra el SQL):
#: 1) cif y ficha, 2) sin cif y ficha con DNI, 3) cif sin ficha,
#: 4) sin cif ni ficha (fuera, R3), 5) sin cif y ficha sin DNI (fuera, R3).
FILAS = [
    [901, "MO/0001", "Uno Recurso", 1, "00000001R", 11, "E11", "Uno Ficha",
     "00000001R", "Oficial", 8.0],
    [902, "MO/0002", "Dos Recurso", 28, " ", 12, "E12", "Dos Ficha",
     "00000002W", None, None],
    [902, "MO/0002", "Dos Recurso", 28, " ", 12, "E12", "Dos Ficha",
     "00000002W", "Peon", 7.5],
    [903, "MO/0037", "Tres Solo Recurso", 28, "00000003A", None, None, None,
     None, "Peon", 8.0],
    [904, "MO/0004", "Cuatro Sin Dni", 1, None, None, None, None, None,
     None, None],
    [905, "MO/0005", "Cinco Ficha Sin Dni", 1, "", 15, "E15", "Cinco",
     "  ", None, None],
]


def _recursos(monkeypatch, filas=FILAS):
    falso = SigridFalso(COLS, filas)
    return _cliente(monkeypatch, falso).fetch_recursos_activos(), falso


# ================================ R1 ==================================== #

def test_f035_r1_una_consulta_paginada_por_res_ide_con_alta_a_hoy(
        monkeypatch) -> None:
    _, falso = _recursos(monkeypatch, [])
    (peticion,) = falso.peticiones
    sql = _sql(peticion["sql"])
    hoy = int(datetime.now().strftime("%Y%m%d"))
    assert peticion["parameters"] == [hoy, 0, PAGINA]
    assert peticion["max_rows"] == PAGINA + 1
    assert ("(rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
            "rescon.fecbaj > ?)") in sql
    assert sql.endswith(
        "ORDER BY res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert sql.count("ORDER BY") == 1


def test_f035_r1_encadena_paginas(monkeypatch) -> None:
    filas = [[i, f"MO/{i}", f"R{i}", 1, f"{i:08d}Z", None, None, None,
              None, None, None] for i in range(1, PAGINA + 3)]
    recursos, falso = _recursos(monkeypatch, filas)
    assert len(recursos) == PAGINA + 2
    assert [p["parameters"][1:] for p in falso.peticiones] == \
        [[0, PAGINA], [PAGINA, PAGINA]]


def test_f035_r1_la_ficha_enlazada_es_la_de_res_conide(monkeypatch) -> None:
    _, falso = _recursos(monkeypatch, [])
    sql = _sql(falso.peticiones[0]["sql"])
    assert "LEFT JOIN emp ON emp.ide = res.conide AND res.conide > 0" in sql
    assert "rescon.emp AS empresa" in sql
    assert "res.cif AS cif" in sql


# ================================ R2 ==================================== #

def test_f035_r2_con_ficha_y_sin_ficha(monkeypatch) -> None:
    recursos, _ = _recursos(monkeypatch)
    por_ide = {r.ide: r for r in recursos}
    assert por_ide[901] == RecursoOption(
        ide=901, codigo="MO/0001", nombre="Uno Recurso", dni="00000001R",
        empresa=1, empleado_ide=11, empleado_codigo="E11",
        empleado_nombre="Uno Ficha", empleado_dni="00000001R",
        categoria="Oficial", candef=8.0)
    assert por_ide[903] == RecursoOption(
        ide=903, codigo="MO/0037", nombre="Tres Solo Recurso",
        dni="00000003A", empresa=28, categoria="Peon", candef=8.0)


def test_f035_r2_sin_cif_el_dni_es_el_de_la_ficha(monkeypatch) -> None:
    recursos, _ = _recursos(monkeypatch)
    dos = next(r for r in recursos if r.ide == 902)
    assert dos.dni == "00000002W"
    assert dos.empleado_dni == "00000002W"
    assert dos.nombre == "Dos Recurso"   # el nombre es el del recurso


def test_f035_r2_el_cif_manda_sobre_la_ficha(monkeypatch) -> None:
    filas = [[906, "MO/6", "Seis", 1, "00000006Y", 16, "E16", "Seis",
              "6Y", None, None]]
    (seis,), _ = _recursos(monkeypatch, filas)
    assert (seis.dni, seis.empleado_dni) == ("00000006Y", "6Y")


def test_f035_r2_una_opcion_por_recurso_que_completa_categoria(
        monkeypatch) -> None:
    recursos, _ = _recursos(monkeypatch)
    assert [r.ide for r in recursos] == [901, 902, 903]
    dos = next(r for r in recursos if r.ide == 902)
    assert (dos.categoria, dos.candef) == ("Peon", 7.5)


# ================================ R3 ==================================== #

def test_f035_r3_sin_dni_ni_en_la_ficha_no_se_ofrece(monkeypatch,
                                                      caplog) -> None:
    with caplog.at_level(logging.INFO):
        recursos, _ = _recursos(monkeypatch)
    ides = {r.ide for r in recursos}
    assert 904 not in ides and 905 not in ides
    assert any("sin DNI" in m and "2" in m for m in caplog.messages)


# ================================ R4 ==================================== #

def test_f035_r4_solo_clase_persona_en_el_sql(monkeypatch) -> None:
    _, falso = _recursos(monkeypatch, [])
    sql = _sql(falso.peticiones[0]["sql"])
    assert "WHERE res.cla = 1 AND" in sql
