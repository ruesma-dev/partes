# tests/test_f023_cliente_sigrid.py
"""F-023 · R2-R4: el cliente de lectura de Sigrid de sv3.

  - R2: maestros de TODAS las empresas, con su empresa y su baja
    (`con.emp`, `con.fecbaj`); obras una por `ide` (sin deduplicar por
    codigo: hay codigos en dos empresas) y las empresas de `auxemp`.
  - R3: todo listado se pagina: `ORDER BY` por clave unica y estable,
    `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY`, paginas de 5.000 pedidas con
    `max_rows` 5.001, hasta una pagina incompleta.
  - R4: `truncated: true` en una respuesta es una excepcion, nunca filas
    parciales.

Sin red: sigrid-api simulado con `httpx.MockTransport`, que sirve la tabla
por trozos igual que SQL Server con OFFSET/FETCH.
"""
from __future__ import annotations

import json

import httpx
import pytest

from domain.models.sigrid_models import EmpresaRow
from infrastructure.sigrid import sigrid_api_client as modulo
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

PAGINA = 5000


class SigridFalso:
    """sigrid-api en memoria: una tabla y lo que se le ha pedido."""

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
            "row_count": len(filas), "truncated": self.truncated,
        })


def _cliente(monkeypatch, falso: SigridFalso) -> SigridApiClient:
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridApiClient(base_url="http://sigrid.invalid",
                           function_key="clave-de-test", database="bd")


COLS_EMP = ["ide", "codigo", "nombre", "dni", "reside", "empresa", "fecbaj"]


def _empleados(n: int) -> list[list]:
    return [[i, f"E{i}", f"P {i}", None, None, 1, 0] for i in range(1, n + 1)]


# =============================== R3 ===================================== #

def test_f023_r3_encadena_paginas_hasta_una_incompleta(monkeypatch) -> None:
    falso = SigridFalso(COLS_EMP, _empleados(PAGINA + 3))
    filas = _cliente(monkeypatch, falso).fetch_empleados()
    assert len(filas) == PAGINA + 3
    assert [f.ide for f in filas[-3:]] == [PAGINA + 1, PAGINA + 2, PAGINA + 3]
    assert [p["parameters"] for p in falso.peticiones] == \
        [[0, PAGINA], [PAGINA, PAGINA]]


def test_f023_r3_max_rows_es_la_pagina_mas_una(monkeypatch) -> None:
    falso = SigridFalso(COLS_EMP, _empleados(3))
    _cliente(monkeypatch, falso).fetch_empleados()
    assert [p["max_rows"] for p in falso.peticiones] == [PAGINA + 1]


def test_f023_r3_una_pagina_justa_pide_la_siguiente(monkeypatch) -> None:
    """5.000 exactas no dicen si hay mas: se pide otra, que llega vacia."""
    falso = SigridFalso(COLS_EMP, _empleados(PAGINA))
    assert len(_cliente(monkeypatch, falso).fetch_empleados()) == PAGINA
    assert len(falso.peticiones) == 2


def test_f023_r3_tres_paginas(monkeypatch) -> None:
    falso = SigridFalso(COLS_EMP, _empleados(2 * PAGINA + 1))
    assert len(_cliente(monkeypatch, falso).fetch_empleados()) == \
        2 * PAGINA + 1
    assert [p["parameters"][-2] for p in falso.peticiones] == \
        [0, PAGINA, 2 * PAGINA]


def test_f023_r3_una_pagina_con_mas_filas_de_las_pedidas_es_error(
        monkeypatch) -> None:
    """Con FETCH NEXT 5.000 no pueden llegar 5.001: algo va mal."""
    class Desbocado(SigridFalso):
        def __call__(self, request):
            self.peticiones.append(json.loads(request.content))
            return httpx.Response(200, json={
                "ok": True, "columns": self.columnas, "rows": self.filas,
                "row_count": len(self.filas)})

    with pytest.raises(RuntimeError):
        _cliente(monkeypatch, Desbocado(COLS_EMP,
                                        _empleados(PAGINA + 1))).fetch_empleados()


@pytest.mark.parametrize("metodo, args, orden, columnas", [
    ("fetch_empleados", (), "con.ide", COLS_EMP),
    ("fetch_obras", (), "con.ide", ["ide", "codigo", "nombre", "empresa"]),
    ("fetch_recursos", (), "res.ide", ["ide", "cif", "conide"]),
    ("fetch_empresas", (), "auxemp.ide", ["numemp", "nombre"]),
    ("fetch_reshor", (), "reshor.ide", ["reside", "horide"]),
    ("fetch_tipos_hora", (), "auxhor.ide", ["ide"]),
    ("fetch_partidas_obra", (77,), "obrparpar.ide", ["ide"]),
    ("fetch_hmo_obra", (77,), "hmo.ide", ["ide"]),
])
def test_f023_r3_cada_listado_pagina_por_su_clave(
        monkeypatch, metodo, args, orden, columnas) -> None:
    falso = SigridFalso(columnas, [])
    getattr(_cliente(monkeypatch, falso), metodo)(*args)
    (peticion,) = falso.peticiones
    sql = " ".join(peticion["sql"].split())
    assert sql.endswith(
        f"ORDER BY {orden} OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert sql.count("ORDER BY") == 1
    assert peticion["parameters"] == [*args, 0, PAGINA]
    assert peticion["max_rows"] == PAGINA + 1


# =============================== R4 ===================================== #

@pytest.mark.parametrize("metodo, args", [
    ("fetch_empleados", ()), ("fetch_obras", ()), ("fetch_recursos", ()),
    ("fetch_empresas", ()), ("fetch_reshor", ()), ("fetch_tipos_hora", ()),
    ("fetch_partidas_obra", (77,)), ("fetch_hmo_obra", (77,)),
])
def test_f023_r4_truncated_es_una_excepcion(monkeypatch, metodo, args) -> None:
    falso = SigridFalso(COLS_EMP, _empleados(3), truncated=True)
    with pytest.raises(RuntimeError, match="truncad"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)


def test_f023_r4_truncated_false_o_ausente_no_molesta(monkeypatch) -> None:
    falso = SigridFalso(COLS_EMP, _empleados(3), truncated=False)
    assert len(_cliente(monkeypatch, falso).fetch_empleados()) == 3


# =============================== R2 ===================================== #

def test_f023_r2_empleados_de_todas_las_empresas_con_empresa_y_baja(
        monkeypatch) -> None:
    falso = SigridFalso(COLS_EMP, [
        [10, "E10", "Uno", "00000001R", 900, 1, 0],
        [11, "E11", "Uno", "00000001R", 902, 31, 20260101],
    ])
    filas = _cliente(monkeypatch, falso).fetch_empleados()
    assert [(f.ide, f.empresa, f.fecbaj) for f in filas] == \
        [(10, 1, 0), (11, 31, 20260101)]
    sql = " ".join(falso.peticiones[0]["sql"].split())
    assert "con.emp AS empresa" in sql and "con.fecbaj AS fecbaj" in sql
    assert "WHERE" not in sql              # sin filtro de SIGRID_EMPRESA


def test_f023_r2_el_cliente_ya_no_acepta_empresa() -> None:
    with pytest.raises(TypeError):
        SigridApiClient(base_url="http://x", function_key="k",
                        database="bd", empresa=1)   # type: ignore[call-arg]


def test_f023_r2_recursos_con_empresa_y_baja_del_concepto(monkeypatch) -> None:
    falso = SigridFalso(
        ["ide", "cif", "conide", "restipide", "restip_cod", "restip_res",
         "horide_def", "empresa", "fecbaj"],
        [[900, "00000001R", 10, 3, "OF1", "Oficial", 100, 1, 20210126]])
    (r,) = _cliente(monkeypatch, falso).fetch_recursos()
    assert (r.ide, r.conide, r.empresa, r.fecbaj) == (900, 10, 1, 20210126)
    sql = " ".join(falso.peticiones[0]["sql"].split())
    assert "JOIN con rc ON rc.ide = res.ide" in sql
    assert "rc.emp AS empresa" in sql and "rc.fecbaj AS fecbaj" in sql


def test_f023_r2_obras_una_por_ide_con_su_empresa(monkeypatch) -> None:
    """Las gemelas (mismo codigo, dos empresas) salen las dos."""
    falso = SigridFalso(["ide", "codigo", "nombre", "empresa"], [
        [100, "0100", "Norte", 1],
        [200, "0100", "Sur", 28],
        [200, "0100", "Sur", 28],          # fila repetida: una por ide
        [300, None, "Sin codigo", 1],
        [None, "0400", "Sin ide", 1],
    ])
    obras = _cliente(monkeypatch, falso).fetch_obras()
    assert [(o.ide, o.codigo, o.empresa) for o in obras] == \
        [(100, "0100", 1), (200, "0100", 28)]
    sql = " ".join(falso.peticiones[0]["sql"].split())
    assert "con.emp AS empresa" in sql


def test_f023_r2_empresas_de_auxemp(monkeypatch) -> None:
    falso = SigridFalso(["numemp", "nombre", "fecbaj", "desact"], [
        [1, "UNO", 0, 0], [28, "VEINTIOCHO", None, None], [None, "x", 0, 0]])
    assert _cliente(monkeypatch, falso).fetch_empresas() == [
        EmpresaRow(numemp=1, nombre="UNO", fecbaj=0, desact=0),
        EmpresaRow(numemp=28, nombre="VEINTIOCHO", fecbaj=None, desact=None),
    ]
    sql = " ".join(falso.peticiones[0]["sql"].split())
    assert "FROM auxemp" in sql
    assert "auxemp.numemp AS numemp" in sql


def test_f023_tipos_de_hora_ordenados_por_ext_y_codigo(monkeypatch) -> None:
    """Paginar obliga a ordenar por `auxhor.ide`; el orden de negocio
    (normales antes que extras, por codigo) se rehace en Python."""
    falso = SigridFalso(
        ["ide", "codigo", "descripcion", "ext", "pre", "prenom"],
        [[1, "HL02", "b", 0, None, None], [2, "HE01", "c", 1, None, None],
         [3, "HL01", "a", 0, None, None], [4, None, "d", 0, None, None]])
    tipos = _cliente(monkeypatch, falso).fetch_tipos_hora()
    assert [t.ide for t in tipos] == [4, 3, 1, 2]


def test_f023_r2_las_empresas_leidas_no_se_pueden_alterar() -> None:
    """`EmpresaRow` es un DTO inmutable, como el resto de filas de Sigrid."""
    import dataclasses

    fila = EmpresaRow(numemp=1, nombre="UNO")
    with pytest.raises(dataclasses.FrozenInstanceError):
        fila.desact = 1  # type: ignore[misc]
    assert {fila, EmpresaRow(numemp=1, nombre="UNO")} == {fila}
