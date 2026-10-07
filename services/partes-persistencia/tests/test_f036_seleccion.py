# tests/test_f036_seleccion.py
"""F-036 · R3-R5, R7: el casado elige RECURSO persona (`IndicePersonas`).

  - `candidatos_nombre` (R3, R10): recursos persona de alta a la fecha, de
    la empresa del parte (sin empresa, de cualquiera) y con DNI del
    recurso.
  - `casar_por_dni` (R4, R5, R7): entre los recursos del DNI de alta y de
    la empresa del parte, con el desempate de siempre: uno solo; si no, el
    `reside` de la ficha del DNI de alta en esa empresa; si no, el unico
    enlazado a esa ficha. Sin candidato: `ambiguo`, `solo_baja` u
    `otra_empresa`; sin recursos persona: `desconocido`.

Todo SINTETICO.
"""
from __future__ import annotations

import pytest

from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import EmpleadoRow, RecursoRow

HOY = 20260915
DNI = "12345678Z"
OTRO = "87654321X"


def _ficha(ide, *, dni=DNI, empresa=1, fecbaj=0, reside=None):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=f"P {ide}", dni=dni,
                       reside=reside, empresa=empresa, fecbaj=fecbaj)


def _rec(ide, *, cla=1, cif=None, conide=None, empresa=1, fecbaj=0):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=f"MO/{ide}", nombre=f"R {ide}",
                      cla=cla)


def _res(indice, dni=DNI, empresa=1, fecha=HOY):
    r = indice.casar_por_dni(dni, empresa, fecha)
    return r.ide, r.motivo


# ======================= candidatos_nombre (R3) ======================== #

def test_f036_r3_candidatos_nombre_solo_persona_de_alta_empresa_y_con_dni(
) -> None:
    indice = IndicePersonas([_ficha(10), _ficha(11, dni=None)], [
        _rec(900, conide=10),                  # si: DNI por ficha
        _rec(901, cif=OTRO),                   # si: DNI por cif
        _rec(902, cif=None),                   # no: sin DNI (R3)
        _rec(903, conide=11),                  # no: ficha sin DNI ni cif
        _rec(904, cif=OTRO, cla=2),            # no: no es persona (R2)
        _rec(905, cif=OTRO, fecbaj=HOY),       # no: de baja ese dia
        _rec(906, cif=OTRO, empresa=28),       # no: otra empresa
        _rec(907, cif=OTRO, fecbaj=HOY + 1),   # si: baja futura
    ])
    assert [r.ide for r in indice.candidatos_nombre(1, HOY)] == \
        [900, 901, 907]


def test_f036_r3_candidatos_nombre_sin_empresa_de_cualquiera() -> None:
    indice = IndicePersonas([], [
        _rec(900, cif=DNI, empresa=1), _rec(901, cif=OTRO, empresa=28),
        _rec(902, cif=OTRO, empresa=None), _rec(903, cif=None, empresa=28)])
    assert [r.ide for r in indice.candidatos_nombre(None, HOY)] == \
        [900, 901, 902]


def test_f036_r3_candidatos_nombre_vacio() -> None:
    assert IndicePersonas([], []).candidatos_nombre(1, HOY) == []


# ========================= casar_por_dni (R4) ========================== #

def test_f036_r4_un_solo_candidato() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, conide=10), _rec(901, conide=10, empresa=28)])
    assert _res(indice) == (900, "ok")


def test_f036_r4_el_dni_leido_se_normaliza() -> None:
    indice = IndicePersonas([], [_rec(900, cif=DNI)])
    assert _res(indice, dni=" 12345678-z ") == (900, "ok")


def test_f036_r4_varios_desempata_el_reside_de_la_ficha_de_la_empresa(
) -> None:
    indice = IndicePersonas(
        [_ficha(10, reside=901), _ficha(11, empresa=28, reside=900)],
        [_rec(900, conide=10), _rec(901, conide=10), _rec(902, cif=DNI)])
    assert _res(indice) == (901, "ok")


def test_f036_r4_el_reside_que_no_es_candidato_no_vale_y_decide_la_ficha(
) -> None:
    """El `reside` de la ficha es de baja: entre el enlazado a la ficha y
    uno solo por `cif`, gana el unico enlazado a la ficha."""
    indice = IndicePersonas([_ficha(10, reside=905)], [
        _rec(905, conide=10, fecbaj=20210126), _rec(900, conide=10),
        _rec(901, cif=DNI)])
    assert _res(indice) == (900, "ok")


def test_f036_r4_sin_ficha_ok_no_hay_desempate_por_ficha() -> None:
    """Dos fichas del DNI en la empresa (`elegir_ficha` ambiguo): ni
    `reside` ni ficha desempatan dos recursos."""
    indice = IndicePersonas(
        [_ficha(10, reside=900), _ficha(11, reside=900)],
        [_rec(900, conide=10), _rec(901, conide=11)])
    assert _res(indice) == (None, "ambiguo")


def test_f036_r4_ficha_de_otra_empresa_no_desempata() -> None:
    """La ficha del DNI es de la 28; en la 1 hay dos recursos por `cif`:
    `elegir_ficha` no da `ok` en la 1 y el `reside` no se usa."""
    indice = IndicePersonas([_ficha(10, empresa=28, reside=900)], [
        _rec(900, cif=DNI), _rec(901, cif=DNI)])
    assert _res(indice) == (None, "ambiguo")


def test_f036_r4_sin_empresa_compiten_todas() -> None:
    indice = IndicePersonas([], [_rec(900, cif=DNI, empresa=28)])
    assert _res(indice, empresa=None) == (900, "ok")


# ========================= casar_por_dni (R5) ========================== #

def test_f036_r5_dos_candidatos_sin_desempate_ambiguo() -> None:
    indice = IndicePersonas([], [_rec(900, cif=DNI), _rec(901, cif=DNI)])
    assert _res(indice) == (None, "ambiguo")


def test_f036_r5_solo_de_baja() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, conide=10, fecbaj=HOY), _rec(901, cif=DNI, fecbaj=1)])
    assert _res(indice) == (None, "solo_baja")


def test_f036_r5_de_alta_solo_en_otra_empresa() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _rec(900, conide=10, empresa=28), _rec(901, cif=DNI, fecbaj=1)])
    assert _res(indice) == (None, "otra_empresa")


@pytest.mark.parametrize("recursos", [
    [],
    [RecursoRow(ide=900, cif=DNI, conide=None, empresa=1, fecbaj=0, cla=2)],
    [RecursoRow(ide=900, cif=OTRO, conide=None, empresa=1, fecbaj=0, cla=1)],
])
def test_f036_r5_r6_sin_recursos_persona_desconocido(recursos) -> None:
    indice = IndicePersonas([_ficha(10)], recursos)
    assert _res(indice) == (None, "desconocido")


@pytest.mark.parametrize("dni", [None, "", "  "])
def test_f036_r6_sin_dni_desconocido(dni) -> None:
    indice = IndicePersonas([], [_rec(900, cif=None)])
    assert _res(indice, dni=dni) == (None, "desconocido")


# =============================== R7 ===================================== #

def test_f036_r7_ficha_en_a_y_recurso_sin_enlazar_en_b() -> None:
    """Ficha en la 1 (con su recurso enlazado) y recurso persona sin
    enlazar con `res.cif` = DNI en la 28: el parte de la 28 casa por ese."""
    indice = IndicePersonas([_ficha(10, empresa=1, reside=900)], [
        _rec(900, conide=10, empresa=1), _rec(950, cif=DNI, empresa=28)])
    assert _res(indice, empresa=28) == (950, "ok")
    assert _res(indice, empresa=1) == (900, "ok")


# ====================== dni_conocido (R6, opcion A) ===================== #

@pytest.mark.parametrize("fichas, recursos, dni, esperado", [
    # ficha de cualquier empresa y estado
    ([_ficha(10, empresa=28, fecbaj=20200101)], [], DNI, True),
    # recurso de cualquier clase con ese cif
    ([], [_rec(900, cif=DNI, cla=2)], DNI, True),
    ([], [_rec(900, cif=DNI, cla=None, fecbaj=1, empresa=31)], DNI, True),
    # normalizado
    ([_ficha(10)], [], " 12345678-z ", True),
    # desconocido
    ([_ficha(10, dni=OTRO)], [_rec(900, cif=OTRO, cla=2)], DNI, False),
    ([], [], DNI, False),
    ([_ficha(10, dni=None)], [_rec(900, cif=None)], None, False),
    ([_ficha(10, dni="")], [_rec(900, cif="")], "", False),
])
def test_f036_r6_dni_conocido(fichas, recursos, dni, esperado) -> None:
    assert IndicePersonas(fichas, recursos).dni_conocido(dni) is esperado
