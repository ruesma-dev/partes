# tests/test_f036_maestro.py
"""F-036 · R1-R3: el maestro de recursos de sv3 sabe que es «persona».

  - R1: `res.cla` se lee en la lectura paginada de recursos y llega a
    `RecursoRow.cla` (NULL -> None).
  - R2: solo `cla = 1` es recurso persona: el casado, `elegir_recurso` y
    `empresas_con_recurso` no proponen otro; `recurso()` y `recursos`
    siguen viendo todos (el conciliador pisa categoria y hora por ide).
  - R3: un recurso persona sin DNI del recurso no es candidato por nombre
    y el proveedor lo cuenta en un INFO. F-040 cambio el INFO: desde
    entonces se PROPONEN por nombre (no casan solos).

Sin red: `_post_sql_read` parcheado. Todo SINTETICO.
"""
from __future__ import annotations

import logging

import pytest

from application.services import seleccion_sigrid as sel
from application.services.seleccion_sigrid import IndicePersonas
from application.services.sigrid_matcher_provider import SigridMatcherProvider
from domain.models.sigrid_models import EmpleadoRow, ObraRow, RecursoRow
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

HOY = 20260915
DNI = "12345678Z"

COLS = ["ide", "cif", "conide", "restipide", "restip_cod", "restip_res",
        "horide_def", "empresa", "fecbaj", "codigo", "nombre", "cla"]


def _cliente(monkeypatch, filas: list[list]) -> tuple[SigridApiClient, list]:
    cliente = SigridApiClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")
    pedidos: list[dict] = []

    def falso(*, sql, parameters, label, max_rows=None):
        pedidos.append({"sql": sql, "parameters": parameters})
        return COLS, filas if parameters[-2] == 0 else []

    monkeypatch.setattr(cliente, "_post_sql_read", falso)
    return cliente, pedidos


# =============================== R1 ===================================== #

def test_f036_r1_el_sql_de_recursos_lee_res_cla(monkeypatch) -> None:
    cliente, pedidos = _cliente(monkeypatch, [])
    cliente.fetch_recursos()
    sql = " ".join(pedidos[0]["sql"].split())
    assert "res.cla AS cla" in sql


def test_f036_r1_fetch_recursos_mapea_cla(monkeypatch) -> None:
    cliente, _ = _cliente(monkeypatch, [
        [900, "00000001R", 10, 3, "OF1", "Oficial", 100, 1, 0, "MO/1", "P", 1],
        [901, None, None, None, None, None, None, 1, 0, "MAQ/1", "Grua", 2],
        [902, None, None, None, None, None, None, 1, 0, "X/1", "Nulo", None],
    ])
    recursos = cliente.fetch_recursos()
    assert [(r.ide, r.cla) for r in recursos] == \
        [(900, 1), (901, 2), (902, None)]


def test_f036_r1_recurso_row_cla_por_defecto_none() -> None:
    assert RecursoRow(ide=1, cif=None, conide=None).cla is None



# =============================== R2 ===================================== #

def _ficha(ide, *, dni=DNI, empresa=1, fecbaj=0, reside=None):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=f"P {ide}", dni=dni,
                       reside=reside, empresa=empresa, fecbaj=fecbaj)


def _rec(ide, *, cla=1, cif=None, conide=None, empresa=1, fecbaj=0,
         codigo=None, nombre=None):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=codigo, nombre=nombre, cla=cla)


def test_f036_r2_cla_persona_es_uno() -> None:
    assert sel.CLA_PERSONA == 1


@pytest.mark.parametrize("cla, esperado", [
    (1, True), (0, False), (2, False), (None, False), (3, False),
])
def test_f036_r2_es_persona_solo_cla_1(cla, esperado) -> None:
    assert sel.es_persona(_rec(1, cla=cla)) is esperado


@pytest.mark.parametrize("cla", [0, 2, None])
def test_f036_r2_elegir_recurso_no_propone_un_recurso_que_no_es_persona(
        cla) -> None:
    """El unico recurso del DNI (por `cif` y por ficha) no es de persona:
    para la eleccion la persona no tiene recursos."""
    indice = IndicePersonas(
        [_ficha(10)], [_rec(900, cla=cla, cif=DNI, conide=10)])
    res = indice.elegir_recurso(DNI, 10, 900, 1, HOY)
    assert (res.ide, res.motivo) == (None, "desconocido")


def test_f036_r2_entre_dos_recursos_el_de_persona_sin_ambiguedad() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, cla=2, conide=10), _rec(901, cla=1, conide=10)])
    res = indice.elegir_recurso(DNI, 10, None, 1, HOY)
    assert (res.ide, res.motivo) == (901, "ok")


def test_f036_r2_el_filtro_vale_por_cif_y_por_ficha() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, cla=0, cif=DNI), _rec(901, cla=2, conide=10),
        _rec(902, cla=1, cif=DNI, empresa=28)])
    res = indice.elegir_recurso(DNI, 10, None, None, HOY)
    assert (res.ide, res.motivo) == (902, "ok")


def test_f036_r2_empresas_con_recurso_solo_de_persona() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, cla=2, conide=10, empresa=1),
        _rec(901, cla=None, cif=DNI, empresa=31),
        _rec(902, cla=1, cif=DNI, empresa=28)])
    assert indice.empresas_con_recurso(DNI, HOY) == frozenset({28})


def test_f036_r2_recurso_por_ide_y_recursos_siguen_viendo_todos() -> None:
    no_persona = _rec(900, cla=2, conide=10)
    persona = _rec(901, cla=1, conide=10)
    indice = IndicePersonas([_ficha(10)], [no_persona, persona],
                            [ObraRow(ide=1, codigo="1", nombre="O", empresa=1)])
    assert indice.recurso(900) is no_persona
    assert indice.recursos == [no_persona, persona]


# ======================= DNI del recurso (DA1) ========================== #

@pytest.mark.parametrize("dni_ficha, cif, esperado", [
    (DNI, "87654321X", DNI),            # DA1: manda el de la ficha
    (" 12345678-z ", None, DNI),        # normalizado
    (None, "87654321x", "87654321X"),   # ficha sin DNI: el cif
    ("", " 87654321-X", "87654321X"),
    (None, None, ""),                   # ninguno
    ("", "", ""),
])
def test_f036_da1_dni_de_recurso_ficha_y_si_no_cif(dni_ficha, cif,
                                                   esperado) -> None:
    indice = IndicePersonas([_ficha(10, dni=dni_ficha)],
                            [_rec(900, cif=cif, conide=10)])
    assert indice.dni_de_recurso(indice.recurso(900)) == esperado


def test_f036_da1_dni_de_recurso_sin_ficha_enlazada_es_el_cif() -> None:
    r_sin = _rec(900, cif="87654321-x", conide=None)
    r_fuera = _rec(901, cif="87654321X", conide=555)    # 555 no esta
    indice = IndicePersonas([_ficha(10)], [r_sin, r_fuera])
    assert indice.dni_de_recurso(r_sin) == "87654321X"
    assert indice.dni_de_recurso(r_fuera) == "87654321X"


def test_f036_ficha_enlazada_por_conide() -> None:
    ficha = _ficha(10)
    indice = IndicePersonas([ficha], [
        _rec(900, conide=10), _rec(901, conide=None), _rec(902, conide=77)])
    assert indice.ficha_enlazada(indice.recurso(900)) is ficha
    assert indice.ficha_enlazada(indice.recurso(901)) is None
    assert indice.ficha_enlazada(indice.recurso(902)) is None


# =============================== R3 ===================================== #

class _Lookup:
    def __init__(self, empleados, recursos) -> None:
        self._e, self._r = empleados, recursos

    def fetch_empleados(self):
        return list(self._e)

    def fetch_obras(self):
        return []

    def fetch_tipos_hora(self):
        return []

    def fetch_recursos(self):
        return list(self._r)

    def fetch_empresas(self):
        return []


def test_f036_r3_el_proveedor_cuenta_los_recursos_persona_sin_dni(
        caplog) -> None:
    recursos = [
        _rec(900, cif=None, conide=None),             # persona sin DNI
        _rec(901, cif="", conide=10),                 # ficha sin DNI: sin
        _rec(902, cif=DNI),                           # con DNI
        _rec(903, cla=2, cif=None),                   # no es persona
        _rec(904, cif=None, conide=11),               # DNI por ficha
        _rec(905, cif=None, conide=None),             # persona sin DNI
    ]
    fichas = [_ficha(10, dni=None), _ficha(11, dni="87654321X")]
    proveedor = SigridMatcherProvider(
        lookup=_Lookup(fichas, recursos), empleado_min_score=0.55,
        obra_min_score=0.55, default_hora_normal_cod=None,
        default_hora_extra_cod=None)
    with caplog.at_level(logging.INFO):
        proveedor.get()
    lineas = [r.getMessage() for r in caplog.records
              if "sin DNI" in r.getMessage()]
    assert lineas == [(
        "[matcher-provider] recursos persona sin DNI (se proponen por "
        "nombre, no casan solos): 3 de 5")]
