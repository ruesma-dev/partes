# tests/test_f030_casado_recurso.py
"""F-030 · R4-R13: casar al trabajador contra la «ficha de recurso».

Humano, 2026-10-05: «el proceso es el mismo que con empleado pero contra la
ficha de recurso cuando no esta la de empleado». Una ficha de recurso es un
recurso `MO/` con `res.cif`, sin ninguna ficha `emp` con ese DNI y cuyo
`res.conide` no es una ficha; se trata como una ficha de empleado mas
(DNI = `res.cif`, nombre = `con.res`, empresa y baja las del recurso) y se
casa con el MISMO codigo: `IndicePersonas.elegir_ficha`,
`fichas_candidatas` y `EmpleadoMatcher.match_nombre`.

Familias, por el nombre de los tests: `lectura` (el cliente de Sigrid),
`fichas_de_recurso` (la construccion), `proveedor` y los requisitos del
casado (`r5`...`r13`). Proveedor REAL sobre un Sigrid en memoria y
repositorio falso. Todo SINTETICO: ni DNIs, ni nombres, ni codigos reales.
"""
from __future__ import annotations

import json

import httpx

from domain.models.sigrid_models import RecursoRow
from infrastructure.sigrid import sigrid_api_client as modulo
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

# ============================ lectura · R4 ============================== #


class SigridFalso:
    """sigrid-api en memoria con una sola pagina."""

    def __init__(self, columnas, filas) -> None:
        self.columnas = list(columnas)
        self.filas = [list(f) for f in filas]
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": self.filas,
            "row_count": len(self.filas), "truncated": False})


COLS_RES = ["ide", "cif", "conide", "restipide", "restip_cod", "restip_res",
            "horide_def", "empresa", "fecbaj", "codigo", "nombre"]


def test_f030_r4_lectura_recursos_con_codigo_y_nombre(monkeypatch) -> None:
    falso = SigridFalso(COLS_RES, [
        [950, "09876543B", None, 3, "PE", "PEON", 100, 28, 0, "MO/0950",
         "APELLIDO OTRO, NOMBRE"],
        [951, None, 10, None, None, None, None, 1, None, None, None],
    ])
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    cli = SigridApiClient(base_url="http://sigrid.invalid",
                          function_key="clave-de-test", database="bd")
    recursos = cli.fetch_recursos()
    assert recursos == [
        RecursoRow(ide=950, cif="09876543B", conide=None, restipide=3,
                   restip_cod="PE", restip_res="PEON", horide_def=100,
                   empresa=28, fecbaj=0, codigo="MO/0950",
                   nombre="APELLIDO OTRO, NOMBRE"),
        RecursoRow(ide=951, cif=None, conide=10, empresa=1),
    ]
    (peticion,) = falso.peticiones
    sql = " ".join(peticion["sql"].split())
    # En la MISMA lectura paginada: sin una segunda consulta.
    assert "rc.cod AS codigo" in sql and "rc.res AS nombre" in sql
    assert sql.endswith(
        "ORDER BY res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")


def test_f030_r4_lectura_recurso_row_sin_codigo_ni_nombre_por_defecto(
) -> None:
    r = RecursoRow(ide=1, cif=None, conide=None)
    assert (r.codigo, r.nombre) == (None, None)
