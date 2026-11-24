# tests/test_f083_ciz_solo_fin_de_racha.py
"""F-083 · Una racha de incidencia solo lleva CIZ en su ultimo dia (sv5).

Hoy `decidir_fin` y `decidir_mismo_dia` solo dan el fin por posterior si
ven un CIZ de la racha despues de D. Con F-083, CUALQUIER linea de la racha
en Sigrid en un dia posterior (mismo recurso, `can` nulo o 0 y, en pruebas,
la marca) deja el dia como intermedio: un CIZ cambiado a mano a CIV ya no
hace que el siguiente `fin` escriba un CIZ en medio (caso 0730).

  - Puro (`-k puro`): R1-R9, R19, R20.
  - Pipeline con `SigridFake` (`-k pipeline`): R10-R18.

Sin red ni BBDD. Datos SINTETICOS.
"""
from __future__ import annotations

import inspect
import unicodedata

import pytest
from application.services import racha_ciz
from application.services.racha_ciz import (
    LIMITE_MOTIVO,
    MOTIVO_POSTERIOR,
    MOTIVO_POSTERIOR_SIN_CIZ,
    MOTIVO_YA_EXISTE,
    DecisionFin,
    decidir_fin,
    decidir_mismo_dia,
    es_ciz_del_recurso,
    es_linea_de_la_racha,
    motivo_intermedio_ciz,
    motivo_intermedio_racha,
    ultima_posterior,
)
from application.services.reglas_registro import MOTIVO_INTERMEDIO
from domain.models.registro_models import LineaSigrid, ParteSigrid

RES, D = 77, 20261004
ABIERTO, CERRADO = 900, 800
PARTES = {ABIERTO: ParteSigrid(ide=ABIERTO, cod="PT26/00010", est=1),
          CERRADO: ParteSigrid(ide=CERRADO, cod="PT26/00009", est=3)}
MARCA = "PRUEBA-IA"


def _ls(ide: int, fec: int, *, reside: int = RES, hora: str | None = "CIZ",
        can: float | None = 0.0, hmoide: int = ABIERTO, enlazada=False,
        tex: str | None = None) -> LineaSigrid:
    return LineaSigrid(
        ide=ide, reside=reside, fecha_int=fec, horide=ide + 1000,
        hora_codigo=hora, can=can, tot=0.0, synckey=f"partes:{ide}",
        nuestra=True, hmoide=hmoide, enlazada=enlazada, tex=tex, pos=64)


def _nombre(est: int | None) -> str:
    return {3: "Cerrado"}.get(est, f"estado {est}")


def _fin(candidatas, *, marca=None) -> DecisionFin:
    return decidir_fin(D, RES, candidatas, partes=PARTES, est_registro=1,
                       marca_pruebas=marca, nombre_estado=_nombre)


def _mismo(candidatas, propia=None, *, marca=None) -> str | None:
    return decidir_mismo_dia(D, RES, candidatas, propia, marca_pruebas=marca)


# =============================== Puro =============================== #

# ------------------------- definiciones ------------------------- #

@pytest.mark.parametrize("cambio,esperado", [
    ({}, True), ({"hora": "CIV"}, True), ({"hora": None}, True),
    ({"hora": "HL01"}, True), ({"can": None}, True),
    ({"reside": RES + 1}, False), ({"can": 8.0}, False),
    ({"can": -0.5}, False)])
def test_f083_puro_es_linea_de_la_racha(cambio, esperado) -> None:
    assert es_linea_de_la_racha(_ls(1, D, **cambio), RES, None) is esperado


@pytest.mark.parametrize("tex,esperado", [
    (None, False), ("manual", False), (MARCA, True), (f"x {MARCA} y", True)])
def test_f083_puro_es_linea_de_la_racha_en_pruebas(tex, esperado) -> None:
    linea = _ls(1, D, hora="CIV", tex=tex)
    assert es_linea_de_la_racha(linea, RES, MARCA) is esperado
    assert es_linea_de_la_racha(linea, RES, None) is True
    assert es_linea_de_la_racha(linea, RES, "") is True


@pytest.mark.parametrize("cambio,esperado", [
    ({}, True), ({"hora": " ciz "}, True), ({"hora": "CIV"}, False),
    ({"hora": None}, False), ({"reside": RES + 1}, False),
    ({"can": 1.0}, False)])
def test_f083_puro_es_ciz_del_recurso_sin_cambios(cambio, esperado) -> None:
    assert es_ciz_del_recurso(_ls(1, D, **cambio), RES, None) is esperado


def test_f083_puro_ultima_posterior() -> None:
    a = _ls(1, D + 1, hora="CIV")
    b = _ls(2, D + 3, hora="CIV")
    c = _ls(3, D + 3, hora="CIV")
    z = _ls(4, D + 2)
    todas = [a, c, b, z, _ls(5, D), _ls(6, D - 1, hora="CIV")]
    assert ultima_posterior(todas, D, RES, None, solo_ciz=False) is c
    assert ultima_posterior(todas, D, RES, None, solo_ciz=True) is z
    assert ultima_posterior([_ls(5, D)], D, RES, None, solo_ciz=False) is None
    assert ultima_posterior([], D, RES, None, solo_ciz=True) is None
    # Acepta un iterable de una sola pasada.
    assert ultima_posterior(iter([a]), D, RES, None, solo_ciz=False) is a


# ------------------------------- R1 ------------------------------- #

def test_f083_puro_r1_ciz_posterior_como_hoy() -> None:
    d = _fin([_ls(7001, D + 2)])
    assert d == DecisionFin(tipo="intermedio",
                            motivo=motivo_intermedio_ciz(7001, D + 2))
    assert d.sin_ciz is False


def test_f083_puro_r1_ciz_posterior_manda_sobre_otra_posterior_mas_tarde(
) -> None:
    """Un CIZ posterior gana aunque haya un CIV aun mas adelante: el motivo
    es el de F-060 R14, del CIZ."""
    d = _fin([_ls(9, D + 5, hora="CIV"), _ls(7001, D + 2),
              _ls(7000, D + 1)])
    assert d.motivo == motivo_intermedio_ciz(7001, D + 2)
    assert d.sin_ciz is False


# ------------------------------- R2 ------------------------------- #

@pytest.mark.parametrize("hora", ["CIV", None, "HL01"])
def test_f083_puro_r2_otra_linea_posterior_hace_intermedio(hora) -> None:
    d = _fin([_ls(416319, 20261006, hora=hora)])
    assert d.tipo == "intermedio" and d.linea is None
    assert d.duplicados == 0
    assert d.motivo == motivo_intermedio_racha(416319, 20261006, hora)
    assert d.sin_ciz is True


def test_f083_puro_r2_nombra_la_ultima_por_fecha_e_ide() -> None:
    d = _fin([_ls(3, D + 2, hora="CIV"), _ls(5, D + 4, hora="CIV"),
              _ls(4, D + 4, hora="CIV"), _ls(9, D + 1, hora="CIV")])
    assert d.motivo == motivo_intermedio_racha(5, D + 4, "CIV")
    assert "linea 5 " in d.motivo and "2026-10-08" in d.motivo


# ------------------------------- R3 ------------------------------- #

@pytest.mark.parametrize("anterior", [
    _ls(10, D - 2),                          # se moveria
    _ls(10, D - 2, hmoide=CERRADO),          # parte cerrado
    _ls(10, D - 2, hmoide=555),              # parte que no se leyo
    _ls(10, D - 2, enlazada=True)])          # enlazada
def test_f083_puro_r3_posterior_antes_que_mover_enlazada_y_cerrado(
        anterior) -> None:
    d = _fin([anterior, _ls(20, D + 1, hora="CIV")])
    assert d.tipo == "intermedio" and d.linea is None and d.sin_ciz
    assert d.motivo == motivo_intermedio_racha(20, D + 1, "CIV")


def test_f083_puro_r3_con_duplicados_tampoco_se_mueve() -> None:
    d = _fin([_ls(10, D - 2), _ls(11, D - 1), _ls(20, D + 1, hora=None)])
    assert (d.tipo, d.duplicados, d.linea) == ("intermedio", 0, None)


# ------------------------------- R4 ------------------------------- #

@pytest.mark.parametrize("posterior", [
    _ls(20, D + 1, hora="CIV", enlazada=True),
    _ls(20, D + 1, hora="CIV", hmoide=CERRADO),
    _ls(20, D + 1, hora="CIV", hmoide=555)])
def test_f083_puro_r4_cuenta_enlazada_o_en_parte_cerrado(posterior) -> None:
    d = _fin([posterior])
    assert d.tipo == "intermedio" and d.sin_ciz is True


# ------------------------------- R5 ------------------------------- #

DESCARTES = [
    _ls(20, D + 1, hora="CIV", reside=RES + 1),   # otro recurso
    _ls(20, D + 1, hora="CIV", can=8.0),          # con horas
    _ls(20, D + 1, hora="CIV", can=-0.5),         # horas negativas
    _ls(20, D, hora="CIV"),                       # el mismo dia D
    _ls(20, D - 1, hora="CIV"),                   # anterior
]


@pytest.mark.parametrize("descarte", DESCARTES)
def test_f083_puro_r5_descartes_no_cuentan(descarte) -> None:
    assert _fin([descarte]) == DecisionFin(tipo="crear")
    anterior = _ls(10, D - 2)
    d = _fin([anterior, descarte])
    assert (d.tipo, d.linea, d.sin_ciz) == ("mover", anterior, False)


@pytest.mark.parametrize("descarte", DESCARTES)
def test_f083_puro_r5_descartes_en_el_mismo_dia(descarte) -> None:
    assert _mismo([descarte]) is None


def test_f083_puro_r5_en_pruebas_sin_marca_no_cuenta() -> None:
    sin = _ls(20, D + 1, hora="CIV", tex=None)
    con = _ls(21, D + 1, hora="CIV", tex=MARCA)
    assert _fin([sin], marca=MARCA) == DecisionFin(tipo="crear")
    assert _mismo([sin], marca=MARCA) is None
    assert _fin([con], marca=MARCA).sin_ciz is True
    assert _mismo([con], marca=MARCA) == MOTIVO_POSTERIOR_SIN_CIZ


# ------------------------------- R6 ------------------------------- #

def test_f083_puro_r6_sin_posteriores_lo_de_hoy() -> None:
    assert _fin([]) == DecisionFin(tipo="crear")
    a, b = _ls(10, D - 2), _ls(11, D - 1)
    assert _fin([a, b]) == DecisionFin(tipo="mover", linea=b, duplicados=1)
    assert _fin([_ls(10, D - 2, enlazada=True)]).tipo == "enlazada"
    assert _fin([_ls(10, D - 2, hmoide=CERRADO)]).tipo == "parte_cerrado"
    # Un CIV anterior (el inicio) no cambia nada.
    assert _fin([_ls(9, D - 3, hora="CIV")]) == DecisionFin(tipo="crear")


# ------------------------------- R7 ------------------------------- #

def test_f083_puro_r7_sin_ciz_por_defecto_falso() -> None:
    assert DecisionFin(tipo="crear").sin_ciz is False
    for cand in ([], [_ls(10, D - 2)], [_ls(10, D - 2, enlazada=True)],
                 [_ls(10, D - 2, hmoide=CERRADO)], [_ls(7, D + 1)]):
        assert _fin(cand).sin_ciz is False
    assert _fin([_ls(7, D + 1, hora="CIV")]).sin_ciz is True


# ------------------------------- R8 ------------------------------- #

@pytest.mark.parametrize("hora", ["CIV", None])
def test_f083_puro_r8_inicio_sin_hermano_si_la_racha_sigue(hora) -> None:
    assert MOTIVO_POSTERIOR_SIN_CIZ == "posterior_sin_ciz"
    assert _mismo([_ls(20, D + 2, hora=hora)]) == MOTIVO_POSTERIOR_SIN_CIZ


@pytest.mark.parametrize("posterior", [
    _ls(20, D + 1, hora="CIV", enlazada=True),
    _ls(20, D + 1, hora="CIV", hmoide=CERRADO)])
def test_f083_puro_r8_cuenta_enlazada_o_cerrada(posterior) -> None:
    assert _mismo([posterior]) == MOTIVO_POSTERIOR_SIN_CIZ


# ------------------------------- R9 ------------------------------- #

PROPIA = _ls(99, D)
CIZ_POST = _ls(30, D + 2)
CIV_POST = _ls(31, D + 3, hora="CIV")


@pytest.mark.parametrize("candidatas,propia,esperado", [
    ([CIZ_POST, CIV_POST], PROPIA, MOTIVO_YA_EXISTE),
    ([CIV_POST], PROPIA, MOTIVO_YA_EXISTE),
    ([], PROPIA, MOTIVO_YA_EXISTE),
    ([CIZ_POST, CIV_POST], None, MOTIVO_POSTERIOR),
    ([CIV_POST, CIZ_POST], None, MOTIVO_POSTERIOR),
    ([CIZ_POST], None, MOTIVO_POSTERIOR),
    ([CIV_POST], None, MOTIVO_POSTERIOR_SIN_CIZ),
    ([], None, None),
])
def test_f083_puro_r9_orden(candidatas, propia, esperado) -> None:
    assert _mismo(candidatas, propia) == esperado
    assert _mismo(iter(candidatas), propia) == esperado


# ------------------------------- R19 ------------------------------- #

def test_f083_puro_r19_motivo_exacto() -> None:
    assert motivo_intermedio_racha(416319, 20261120, "CIV") == (
        "dia intermedio de la incidencia: solo se registran el inicio y el "
        "fin (la racha sigue en Sigrid el dia 2026-11-20, linea 416319 con "
        "CIV, sin CIZ despues; no se escribe un fin en medio)")
    assert "sin codigo" in motivo_intermedio_racha(1, 20261120, None)
    assert "sin codigo" in motivo_intermedio_racha(1, 20261120, "")


def test_f083_puro_r19_prefijo_tildes_y_largo() -> None:
    corto = motivo_intermedio_racha(416319, 20261120, "CIV")
    largo = motivo_intermedio_racha(416319, 20261120, "X" * 400)
    for texto in (corto, largo):
        assert texto.startswith(MOTIVO_INTERMEDIO)
        assert texto.split(":")[0] == MOTIVO_INTERMEDIO.split(":")[0]
        assert texto.isascii()
        assert unicodedata.normalize("NFKD", texto) == texto
        assert len(texto) <= LIMITE_MOTIVO
    assert len(largo) == LIMITE_MOTIVO
    assert len(corto) < LIMITE_MOTIVO


# ------------------------------- R20 ------------------------------- #

def test_f083_puro_r20_regla_pura() -> None:
    fuente = inspect.getsource(racha_ciz)
    for prohibido in ("httpx", "_read(", "escribir(", "DELETE", "import os",
                      "lineas_de_racha", "estados_de_partes"):
        assert prohibido not in fuente


def test_f083_puro_r20_el_cliente_no_borra() -> None:
    from infrastructure.sigrid import sigrid_write_client
    assert "DELETE" not in inspect.getsource(sigrid_write_client).upper()
