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


# ===================== fichas_de_recurso · R4 =========================== #

import application.services.fichas_de_recurso as fdr  # noqa: E402
from domain.models.sigrid_models import EmpleadoRow  # noqa: E402

CIF_P = "09876543B"     # persona SIN ficha de empleado (empresa 28)
CIF_Q = "08765432C"     # otra persona sin ficha (empresa 28)
DNI_E = "11111111H"     # persona CON ficha de empleado (empresa 28)

FICHA_E = EmpleadoRow(ide=10, codigo="E10", nombre="EVA FICHA", dni=DNI_E,
                      reside=900, empresa=28, fecbaj=0)


def _rec(ide, cif, *, codigo=None, conide=None, nombre="APELLIDOS, NOMBRE",
         empresa=28, fecbaj=0) -> RecursoRow:
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=codigo or f"MO/{ide}",
                      nombre=nombre)


def test_f030_r4_fichas_de_recurso_la_ficha_es_el_recurso() -> None:
    r = _rec(950, CIF_P, nombre="GOMEZ RUIZ, PEDRO", fecbaj=20261231)
    assert fdr.fichas_de_recurso([FICHA_E], [r]) == [EmpleadoRow(
        ide=950, codigo="MO/950", nombre="GOMEZ RUIZ, PEDRO", dni=CIF_P,
        reside=950, empresa=28, fecbaj=20261231)]


def test_f030_r4_fichas_de_recurso_el_dni_es_el_cif_tal_cual() -> None:
    (f,) = fdr.fichas_de_recurso([], [_rec(950, " 09876543-b ")])
    assert f.dni == " 09876543-b "


def test_f030_r4_fichas_de_recurso_solo_mano_de_obra() -> None:
    assert fdr.PREFIJO_MANO_DE_OBRA == "MO/"
    recursos = [_rec(950, CIF_P, codigo="MQ/950"),
                _rec(951, CIF_Q, codigo="XMO/951")]
    assert fdr.fichas_de_recurso([], recursos) == []
    sin_codigo = RecursoRow(ide=952, cif=CIF_P, conide=None, empresa=28)
    assert fdr.fichas_de_recurso([], [sin_codigo]) == []


def test_f030_r4_fichas_de_recurso_sin_cif_no_es_ficha() -> None:
    assert fdr.fichas_de_recurso([], [_rec(950, None), _rec(951, ""),
                                      _rec(952, " - ")]) == []


def test_f030_r4_fichas_de_recurso_con_ficha_por_dni_no_es_ficha() -> None:
    """Hay una ficha `emp` con ese DNI (normalizado, de cualquier empresa
    y de alta o de baja): esa persona casa por su ficha."""
    de_baja_otra = EmpleadoRow(ide=11, codigo="E11", nombre="X",
                               dni="08765432-c", reside=None, empresa=1,
                               fecbaj=20200101)
    recursos = [_rec(950, DNI_E), _rec(951, CIF_Q)]
    assert fdr.fichas_de_recurso([FICHA_E, de_baja_otra], recursos) == []


def test_f030_r4_fichas_de_recurso_con_conide_a_una_ficha_no_es_ficha(
) -> None:
    assert fdr.fichas_de_recurso([FICHA_E], [_rec(950, CIF_P,
                                                  conide=10)]) == []


def test_f030_r4_fichas_de_recurso_conide_que_no_es_ficha_si_es_ficha(
) -> None:
    (f,) = fdr.fichas_de_recurso([FICHA_E], [_rec(950, CIF_P, conide=999)])
    assert f.ide == 950


def test_f030_r4_fichas_de_recurso_de_baja_y_de_otra_empresa_tambien() -> None:
    """De todas las empresas y estados: `elegir_ficha` filtra alta y
    empresa y da los mismos motivos que con fichas de empleado."""
    recursos = [_rec(950, CIF_P, fecbaj=20200101),
                _rec(951, CIF_Q, empresa=1)]
    assert [f.ide for f in fdr.fichas_de_recurso([], recursos)] == [950, 951]


def test_f030_r4_fichas_de_recurso_ficha_sin_dni_no_tapa_nada() -> None:
    sin_dni = EmpleadoRow(ide=12, codigo="E12", nombre="Y", dni=None,
                          reside=None, empresa=28, fecbaj=0)
    assert [f.ide for f in fdr.fichas_de_recurso([sin_dni],
                                                 [_rec(950, CIF_P)])] == [950]
