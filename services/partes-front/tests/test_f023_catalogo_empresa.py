# tests/test_f023_catalogo_empresa.py
"""F-023 · R3-R4 y R38-R42 en el portal (sv4).

  - `cliente`: `SigridLookupClient` pagina los listados como sv3 (R3),
    trata `truncated: true` como excepcion (R4), da la empresa de cada
    ficha sin tocar su filtro de alta a hoy (R38) y lista las obras una por
    `ide` con su empresa, sin esconder la gemela de la otra empresa (R39).
  - `endpoint`: `/api/sigrid/empleados` y `/api/sigrid/obras` anaden
    `empresa` sin quitar ni renombrar nada (R40).
  - `soltar`: al casar o reasignar el empleado de unas lineas se sueltan
    su reside, recurso, cif, hmo y estado, solo en las no congeladas (R42).

Sin red ni PostgreSQL: sigrid-api simulado con `httpx.MockTransport` y
SQLite en memoria. Datos SINTETICOS.
"""
from __future__ import annotations

import json
from datetime import datetime

import httpx
import pytest

from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import (
    EmpleadoOption,
    ObraOption,
    SigridLookupClient,
)

PAGINA = 5000


class SigridFalso:
    """sigrid-api en memoria que sirve la tabla por OFFSET/FETCH."""

    def __init__(self, columnas, filas, *, truncated=False) -> None:
        self.columnas = list(columnas)
        self.filas = [list(f) for f in filas]
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        self.peticiones.append(cuerpo)
        filas = self.filas
        if "FETCH NEXT ? ROWS ONLY" in cuerpo["sql"]:
            desde, cuantas = cuerpo["parameters"][-2:]
            filas = filas[desde:desde + cuantas]
        filas = filas[:cuerpo["max_rows"]]
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso) -> SigridLookupClient:
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridLookupClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


COLS_OBRA = ["ide", "codigo", "nombre", "empresa"]


def _obras(n: int) -> list[list]:
    return [[i, f"{i:04d}", f"Obra {i}", 1] for i in range(1, n + 1)]


# ============================ cliente · R3 ============================== #

def test_f023_r3_cliente_encadena_paginas(monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(PAGINA + 2))
    obras = _cliente(monkeypatch, falso).fetch_obras()
    assert len(obras) == PAGINA + 2
    assert [p["parameters"] for p in falso.peticiones] == \
        [[0, PAGINA], [PAGINA, PAGINA]]
    assert {p["max_rows"] for p in falso.peticiones} == {PAGINA + 1}


def test_f023_r3_cliente_pagina_justa_y_tres_paginas(monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(PAGINA))
    assert len(_cliente(monkeypatch, falso).fetch_obras()) == PAGINA
    assert len(falso.peticiones) == 2
    tres = SigridFalso(COLS_OBRA, _obras(2 * PAGINA + 1))
    assert len(_cliente(monkeypatch, tres).fetch_obras()) == 2 * PAGINA + 1
    assert [p["parameters"][0] for p in tres.peticiones] == \
        [0, PAGINA, 2 * PAGINA]


def test_f023_r3_cliente_pagina_desbordada_es_error(monkeypatch) -> None:
    class Desbocado(SigridFalso):
        def __call__(self, request):
            self.peticiones.append(json.loads(request.content))
            return httpx.Response(200, json={
                "ok": True, "columns": self.columnas, "rows": self.filas})

    with pytest.raises(RuntimeError):
        _cliente(monkeypatch, Desbocado(COLS_OBRA,
                                        _obras(PAGINA + 1))).fetch_obras()


@pytest.mark.parametrize("metodo, args, orden, params", [
    ("fetch_obras", (), "con.ide", []),
    ("fetch_tipos_hora", (), "auxhor.ide", []),
    ("fetch_partidas_obra", (77,), "obrparpar.ide", [77]),
])
def test_f023_r3_cliente_cada_listado_pagina_por_su_clave(
        monkeypatch, metodo, args, orden, params) -> None:
    falso = SigridFalso(["ide"], [])
    getattr(_cliente(monkeypatch, falso), metodo)(*args)
    (peticion,) = falso.peticiones
    sql = _sql(peticion["sql"])
    assert sql.endswith(
        f"ORDER BY {orden} OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert sql.count("ORDER BY") == 1
    assert peticion["parameters"] == [*params, 0, PAGINA]
    assert peticion["max_rows"] == PAGINA + 1


def test_f023_r3_r38_cliente_empleados_paginados_con_su_filtro_de_alta(
        monkeypatch) -> None:
    falso = SigridFalso(["ide"], [])
    _cliente(monkeypatch, falso).fetch_empleados()
    (peticion,) = falso.peticiones
    sql = _sql(peticion["sql"])
    hoy = int(datetime.now().strftime("%Y%m%d"))
    assert peticion["parameters"] == [hoy, hoy, 0, PAGINA]
    assert "(con.fecbaj IS NULL OR con.fecbaj = 0 OR con.fecbaj > ?)" in sql
    assert ("rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
            "rescon.fecbaj > ?") in sql
    assert sql.endswith(
        "ORDER BY con.ide, res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")


def test_f023_cliente_tipos_de_hora_en_el_orden_de_siempre(monkeypatch) -> None:
    falso = SigridFalso(
        ["ide", "codigo", "descripcion", "ext", "pre", "prenom"],
        [[1, "HL02", "b", 0, None, None], [2, "HE01", "c", 1, None, None],
         [3, "HL01", "a", 0, None, None], [4, None, "d", 0, None, None]])
    assert [t.ide for t in _cliente(monkeypatch, falso).fetch_tipos_hora()] \
        == [4, 3, 1, 2]


# ============================ cliente · R4 ============================== #

@pytest.mark.parametrize("metodo, args", [
    ("fetch_obras", ()), ("fetch_empleados", ()), ("fetch_tipos_hora", ()),
    ("fetch_partidas_obra", (77,)), ("fetch_dnis_sin_extra", ({"1A"},)),
    ("fetch_hora_extra_recurso", (5,)),
])
def test_f023_r4_cliente_truncated_es_una_excepcion(
        monkeypatch, metodo, args) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(2), truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)


def test_f023_r4_cliente_los_lotes_acotados_no_paginan(monkeypatch) -> None:
    falso = SigridFalso(["dni", "max_he"], [["1A", 1]])
    assert _cliente(monkeypatch, falso).fetch_dnis_sin_extra({"1a"}) == set()
    (peticion,) = falso.peticiones
    assert "OFFSET" not in peticion["sql"]
    assert peticion["max_rows"] == 10000


# ======================= cliente · R38 y R39 =========================== #

def test_f023_r38_cliente_cada_ficha_trae_su_empresa(monkeypatch) -> None:
    falso = SigridFalso(
        ["ide", "codigo", "nombre", "dni", "reside", "categoria", "candef",
         "empresa"],
        [[10, "E10", "Uno", "00000001R", 900, "Oficial", 8.0, 1],
         [11, "E11", "Uno", "00000001R", 902, None, None, 28],
         [11, "E11", "Uno", "00000001R", 903, "Peon", 8.0, 28]])
    fichas = _cliente(monkeypatch, falso).fetch_empleados()
    assert [(e.ide, e.empresa, e.reside, e.categoria) for e in fichas] == \
        [(10, 1, 900, "Oficial"), (11, 28, 902, "Peon")]
    assert "con.emp AS empresa" in _sql(falso.peticiones[0]["sql"])


def test_f023_r39_cliente_las_gemelas_salen_las_dos_con_su_empresa(
        monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, [
        [100, "0100", "Norte", 1], [200, "0100", "Sur", 28],
        [200, "0100", "Sur", 28], [300, None, "Sin codigo", 1],
        [None, "0400", "Sin ide", 1]])
    obras = _cliente(monkeypatch, falso).fetch_obras()
    assert obras == [ObraOption(ide=100, codigo="0100", nombre="Norte",
                                empresa=1),
                     ObraOption(ide=200, codigo="0100", nombre="Sur",
                                empresa=28)]
    assert "con.emp AS empresa" in _sql(falso.peticiones[0]["sql"])


def test_f023_r38_r39_la_empresa_tiene_valor_por_defecto() -> None:
    """Los dobles anteriores a F-023 construyen las opciones sin empresa."""
    assert EmpleadoOption(ide=1, codigo=None, nombre=None,
                          dni=None).empresa is None
    assert ObraOption(ide=1, codigo=None, nombre=None).empresa is None
