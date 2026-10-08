# tests/test_f040_seleccion.py
"""F-040 · R1, R10, R11: la identidad de quien no tiene DNI en sv3.

  - `clave_persona`: el DNI del recurso; sin el, `emp:<conide>` (con ficha
    enlazada en el maestro) o `res:<res.ide>` (sin ella).
  - `casar_por_clave`: `res:N` -> `elegir_sin_dni`; `emp:N` -> el camino
    por ficha de `elegir_recurso` (ficha ausente: `desconocido`); otra
    clave -> `casar_por_dni`.
  - R1: `candidatos_nombre` ya no exige DNI del recurso.
  - R10: `elegir_recurso` sin DNI, sin ficha y con `preferido` ->
    `elegir_sin_dni(preferido)`; con DNI, o sin DNI y con ficha, como hoy.
  - R11: en el conciliador, `con_dni`, `solo_baja` y `otra_empresa` dejan
    la linea sin recurso y su parte a revision.

Todo SINTETICO.
"""
from __future__ import annotations

import logging
from datetime import date

import pytest

from application.services.recurso_conciliador import (
    MOTIVOS_SIN_RECURSO_A_REVISAR,
    RecursoConciliador,
)
from application.services.seleccion_sigrid import (
    IndicePersonas,
    ResolucionRecurso,
)
from domain.models.sigrid_models import EmpleadoRow, ObraRow, RecursoRow
from tests.dobles import (
    LookupFake,
    RepositorioFake,
    recurso_persona,
    registro,
    reshor_par,
)

HOY = 20260915
DNI = "12345678Z"
EMPRESA = 28


def _ficha(ide, *, dni=None, empresa=EMPRESA, reside=None, fecbaj=0):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=f"F {ide}", dni=dni,
                       reside=reside, empresa=empresa, fecbaj=fecbaj)


def _rec(ide, *, cif=None, conide=None, empresa=EMPRESA, fecbaj=0, cla=1):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=f"MO/{ide}", nombre=f"R {ide}",
                      cla=cla)


# ============================ clave_persona ============================ #

def test_f040_clave_persona_dni_ficha_o_recurso() -> None:
    indice = IndicePersonas(
        [_ficha(10, dni=DNI), _ficha(11)],
        [_rec(900, conide=10), _rec(901, cif=" 87654321x "),
         _rec(902, conide=11), _rec(903), _rec(904, conide=99, cif="")])
    claves = {r.ide: indice.clave_persona(r) for r in indice.recursos}
    assert claves == {
        900: DNI,              # DNI de la ficha
        901: "87654321X",      # res.cif normalizado
        902: "emp:11",         # ficha enlazada sin DNI
        903: "res:903",        # sin ficha
        904: "res:904",        # conide a una ficha que no esta: sin ficha
    }


# ============================ casar_por_clave ========================== #

def _indice_claves() -> IndicePersonas:
    return IndicePersonas(
        [_ficha(11, reside=921), _ficha(12, reside=None),
         _ficha(13, dni=DNI, reside=930)],
        [_rec(903),                                   # res: sin ficha
         _rec(920, conide=11), _rec(921, conide=11),  # emp:11, reside 921
         _rec(922, conide=12),                        # emp:12, uno solo
         _rec(930, conide=13)])                       # con DNI


@pytest.mark.parametrize("clave, empresa, esperado", [
    ("res:903", EMPRESA, (903, "ok")),
    ("res:903", 1, (None, "otra_empresa")),
    ("res:930", EMPRESA, (None, "con_dni")),
    ("res:999", EMPRESA, (None, "desconocido")),
    ("emp:11", EMPRESA, (921, "ok")),          # desempata el reside
    ("emp:12", EMPRESA, (922, "ok")),
    ("emp:12", 1, (None, "otra_empresa")),
    ("emp:99", EMPRESA, (None, "desconocido")),  # ficha fuera del maestro
    (DNI, EMPRESA, (930, "ok")),
    ("00000000T", EMPRESA, (None, "desconocido")),
])
def test_f040_casar_por_clave(clave, empresa, esperado) -> None:
    res = _indice_claves().casar_por_clave(clave, empresa, HOY)
    assert (res.ide, res.motivo) == esperado


# ============================ R1 · candidatos ========================== #

def test_f040_r1_candidatos_nombre_incluye_los_sin_dni() -> None:
    indice = IndicePersonas([_ficha(10, dni=DNI), _ficha(11)], [
        _rec(900, conide=10),                  # si: DNI por ficha
        _rec(901, cif=DNI),                    # si: DNI por cif
        _rec(902),                             # si (R1): sin DNI
        _rec(903, conide=11),                  # si (R1): ficha sin DNI
        _rec(904, cla=2),                      # no: no es persona
        _rec(905, fecbaj=HOY),                 # no: de baja ese dia
        _rec(906, empresa=1),                  # no: otra empresa
        _rec(907, fecbaj=HOY + 1),             # si: baja futura
    ])
    assert [r.ide for r in indice.candidatos_nombre(EMPRESA, HOY)] == \
        [900, 901, 902, 903, 907]
    assert [r.ide for r in indice.candidatos_nombre(None, HOY)] == \
        [900, 901, 902, 903, 906, 907]


# ======================= R10 · elegir_recurso ========================== #

def test_f040_r10_sin_dni_sin_ficha_con_preferido_es_elegir_sin_dni() -> None:
    indice = IndicePersonas([], [_rec(903), _rec(904, cif=DNI),
                                 _rec(905, fecbaj=HOY)])
    for dni in (None, "", "  "):
        assert indice.elegir_recurso(dni, None, 903, EMPRESA, HOY) == \
            ResolucionRecurso(903, "ok")
    assert indice.elegir_recurso(None, None, 903, 1, HOY) == \
        ResolucionRecurso(None, "otra_empresa")
    assert indice.elegir_recurso(None, None, 904, EMPRESA, HOY) == \
        ResolucionRecurso(None, "con_dni")
    assert indice.elegir_recurso(None, None, 905, EMPRESA, HOY) == \
        ResolucionRecurso(None, "solo_baja")


def test_f040_r10_sin_preferido_sigue_desconocido() -> None:
    indice = IndicePersonas([], [_rec(903)])
    assert indice.elegir_recurso(None, None, None, EMPRESA, HOY) == \
        ResolucionRecurso(None, "desconocido")


def test_f040_r10_con_dni_no_cambia() -> None:
    """Con DNI el preferido solo desempata entre los del DNI."""
    indice = IndicePersonas([], [_rec(903), _rec(904, cif=DNI)])
    assert indice.elegir_recurso(DNI, None, 903, EMPRESA, HOY) == \
        ResolucionRecurso(904, "ok")


def test_f040_r10_sin_dni_con_ficha_va_por_conide() -> None:
    """Con ficha (aunque sin DNI) manda `conide`, no `elegir_sin_dni`."""
    indice = IndicePersonas([_ficha(11)], [_rec(903), _rec(920, conide=11)])
    assert indice.elegir_recurso(None, 11, 903, EMPRESA, HOY) == \
        ResolucionRecurso(920, "ok")


# ========================= R11 · conciliador =========================== #

OBRAS = [ObraRow(ide=10, codigo="0010", nombre="Obra", empresa=EMPRESA)]


def test_f040_r11_con_dni_a_revision() -> None:
    assert "con_dni" in MOTIVOS_SIN_RECURSO_A_REVISAR
    assert MOTIVOS_SIN_RECURSO_A_REVISAR == frozenset(
        {"ambiguo", "solo_baja", "otra_empresa", "con_dni"})


def _conciliar(reside: int | None, recursos) -> RepositorioFake:
    linea = registro(1, fecha_int=HOY, horas=8.0, dni=None)
    linea.update(empleado_ide=None, empleado_reside=reside)
    repo = RepositorioFake([linea])
    indice = IndicePersonas([], recursos, OBRAS)
    RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(903)),
        indice_provider=lambda: indice,
        hoy=lambda: date(2026, 9, 15),
    ).conciliar_todos()
    return repo


def test_f040_r10_r11_linea_sin_dni_conserva_su_recurso() -> None:
    repo = _conciliar(903, [_rec(903)])
    (u,) = repo.matches
    assert (u["recurso_ide"], u["parte_estado"]) == (903, "sin_parte")
    assert repo.review_required == []


@pytest.mark.parametrize("recurso, motivo", [
    (recurso_persona(ide=903, cif=DNI, conide=None, empresa=EMPRESA,
                     fecbaj=0), "con_dni"),
    (recurso_persona(ide=903, cif=None, conide=None, empresa=EMPRESA,
                     fecbaj=HOY), "solo_baja"),
    (recurso_persona(ide=903, cif=None, conide=None, empresa=1, fecbaj=0),
     "otra_empresa"),
])
def test_f040_r11_sin_recurso_y_a_revision(recurso, motivo, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        repo = _conciliar(903, [recurso])
    (u,) = repo.matches
    assert (u["recurso_ide"], u["parte_estado"]) == (None, "sin_recurso")
    assert repo.review_required == [["doc-1"]]
    assert motivo in caplog.text


def test_f040_r11_desconocido_sin_recurso_y_sin_revision() -> None:
    repo = _conciliar(903, [_rec(903, cla=0)])
    (u,) = repo.matches
    assert (u["recurso_ide"], u["parte_estado"]) == (None, "sin_recurso")
    assert repo.review_required == []
