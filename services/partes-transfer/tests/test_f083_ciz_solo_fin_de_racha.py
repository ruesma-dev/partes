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


def test_f083_puro_r2_con_un_iterador() -> None:
    """T6 (encargo del reviewer): la firma promete `Iterable`. Con un
    iterador de un solo uso, las dos lecturas (CIZ posterior y linea de la
    racha posterior) tienen que ver todas las candidatas."""
    lista = [_ls(5, D - 2), _ls(31, D + 3, hora="CIV")]
    d = _fin(iter(lista))
    assert d.tipo == "intermedio" and d.sin_ciz is True
    assert d.motivo == motivo_intermedio_racha(31, D + 3, "CIV")
    assert d == _fin(lista)


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


# ========================= Pipeline (R10-R18) ========================= #
# Con `SigridFake` y los ayudantes de F-062: obra 0100, recurso 501, parte
# de octubre En registro (901). d1-d3 = 1-3 de octubre de 2026.

from tests.test_f062_ciz_mismo_dia import (  # noqa: E402
    H_CIV,
    H_CIZ,
    HMO_OCT,
    _acc,
    _cli,
    _ejecutar,
    _espiar,
    _fila,
    _pipe,
    _por_sk,
)
from tests.test_f062_ciz_mismo_dia import _fin as _linea_fin  # noqa: E402
from tests.test_f062_ciz_mismo_dia import _inicio as _linea_inicio  # noqa: E402
from tests.test_f062_ciz_mismo_dia import _obra as _obra_f062  # noqa: E402
from application.pipelines.registro_pipeline import RegistroPipeline  # noqa: E402,I001

D1, D2, D3 = 20261001, 20261002, 20261003


def _aprobar_juntos(cli, **kw):
    """d1 `inicio` (sin hermano: su fin viaja), d2 `intermedio`, d3 `fin`."""
    lineas = [_linea_inicio(1, D1, [2, 3], ciz=False), _linea_fin(2, D2),
              _linea_fin(3, D3, [1, 2])]
    lineas[1].incidencia_rol = "intermedio"
    return _ejecutar(cli, lineas, **kw)


def _a_mano_a_civ(cli, synckey: str) -> None:
    """Administracion cambia a mano en Sigrid el CIZ de esa linea a CIV."""
    (fila,) = [f for f in cli.lineas if f["synckey"] == synckey]
    fila["horide"] = H_CIV


def _caso_0730(**kw):
    cli = _cli()
    _aprobar_juntos(cli, **kw)
    _a_mano_a_civ(cli, "partes:3")
    return cli


def _filas(cli) -> dict[str, tuple]:
    return {f["synckey"]: (f["ide"], f["fec"], f["horide"])
            for f in cli.lineas}


def _motivo(r) -> str:
    (o,) = r.omitidas
    return o["motivo"]


# ------------------------------- R13 ------------------------------- #

def test_f083_pipeline_r13_caso_0730() -> None:
    cli = _cli()
    r0 = _aprobar_juntos(cli)
    assert sorted((e["registro_id"], e["hora_codigo"])
                  for e in r0.escritas) == [(1, "CIV"), (3, "CIZ")]
    _a_mano_a_civ(cli, "partes:3")
    antes = _filas(cli)
    ide3 = antes["partes:3"][0]
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
    assert r.escritas == [] and enviadas == []
    assert [o["registro_id"] for o in r.omitidas] == [2]
    assert _motivo(r) == (
        "dia intermedio de la incidencia: solo se registran el inicio y el "
        f"fin (la racha sigue en Sigrid el dia 2026-10-03, linea {ide3} con "
        "CIV, sin CIZ despues; no se escribe un fin en medio)")
    assert "partes:2" not in _por_sk(cli)
    assert "partes:2:ciz" not in _por_sk(cli)
    assert _filas(cli) == antes
    assert antes["partes:1"][2] == H_CIV and antes["partes:3"][2] == H_CIV


# ------------------------------- R14 ------------------------------- #

def test_f083_pipeline_r14_regresion_con_el_ciz_en_su_sitio() -> None:
    cli = _cli()
    _aprobar_juntos(cli)
    antes = _filas(cli)
    ide3 = antes["partes:3"][0]
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
    assert r.escritas == [] and enviadas == []
    assert _motivo(r) == (
        "dia intermedio de la incidencia: solo se registran el inicio y el "
        f"fin (el fin, CIZ linea {ide3}, ya esta el dia 2026-10-03)")
    assert _filas(cli) == antes and antes["partes:3"][2] == H_CIZ


# ------------------------------- R15 ------------------------------- #

def test_f083_pipeline_r15_inicio_desordenado_sin_hermano() -> None:
    cli = _cli(_fila(7001, fec=D3, rid=3, horide=H_CIV))
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(1, D1, [2, 3])])
    (e,) = r.escritas
    assert (e["registro_id"], e["hora_codigo"]) == (1, "CIV")
    assert "ciz_hmores_ide" not in e
    assert [s["op"] for s in enviadas] == ["insert"]
    assert sorted(_por_sk(cli)) == ["partes:1", "partes:3"]
    assert _por_sk(cli)["partes:3"]["horide"] == H_CIV


# ------------------------------- R16 ------------------------------- #

def test_f083_pipeline_r16_reaprobar_es_idempotente() -> None:
    cli = _caso_0730()
    antes = _filas(cli)
    enviadas = _espiar(cli)
    motivos = []
    for _ in range(3):
        r = _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
        assert r.escritas == []
        motivos.append(_motivo(r))
    assert enviadas == [] and len(set(motivos)) == 1
    assert "la racha sigue en Sigrid" in motivos[0]
    assert _filas(cli) == antes


# ------------------------------- R17 ------------------------------- #

def test_f083_pipeline_r17_preflight_omite_sin_escribir() -> None:
    cli = _caso_0730()
    antes = _filas(cli)
    enviadas = _espiar(cli)
    pf = _pipe(cli).preflight(obra=_obra_f062(), lineas=[_linea_fin(2, D2, [1, 3])])
    a = _acc(pf, 2)
    assert a.accion == "omitir" and a.mover is None
    assert "la racha sigue en Sigrid el dia 2026-10-03" in a.motivo
    assert (pf.n_escribir, pf.n_omitir) == (0, 1)
    assert enviadas == [] and _filas(cli) == antes


# ------------------------------- R10 ------------------------------- #

def test_f083_pipeline_r10_warning_del_fin(caplog) -> None:
    cli = _caso_0730()
    caplog.clear()
    with caplog.at_level("INFO"):
        r = _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
    avisos = [rec for rec in caplog.records
              if "racha_fin_no_ciz" in rec.getMessage()]
    assert [(rec.levelname, rec.getMessage()) for rec in avisos] == [
        ("WARNING", "[registro] racha_fin_no_ciz registro_id=2 "
                    f"motivo={_motivo(r)}")]
    assert "Persona" not in caplog.text


def test_f083_pipeline_r10_sin_warning_con_ciz_posterior(caplog) -> None:
    cli = _cli()
    _aprobar_juntos(cli)
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
    assert "racha_fin_no_ciz" not in caplog.text


# ------------------------------- R11 ------------------------------- #

def test_f083_pipeline_r11_warning_del_inicio(caplog) -> None:
    cli = _cli(_fila(7001, fec=D3, rid=3, horide=H_CIV))
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_linea_inicio(1, D1, [2, 3])])
    info = [rec for rec in caplog.records
            if "ciz_mismo_dia_omitido" in rec.getMessage()]
    aviso = [rec for rec in caplog.records
             if "racha_fin_no_ciz" in rec.getMessage()]
    assert [(rec.levelname, rec.getMessage()) for rec in info] == [
        ("INFO", "[registro] ciz_mismo_dia_omitido registro_id=1 "
                 "motivo=posterior_sin_ciz")]
    assert [(rec.levelname, rec.getMessage()) for rec in aviso] == [
        ("WARNING", "[registro] racha_fin_no_ciz registro_id=1 "
                    "motivo=posterior_sin_ciz")]
    assert "Persona" not in caplog.text


@pytest.mark.parametrize("fila", [
    _fila(7001, fec=D3, rid=3),                    # CIZ posterior
    _fila(7001, fec=D1, sk="partes:1:ciz")])       # hermano ya escrito
def test_f083_pipeline_r11_sin_warning_en_los_demas_motivos(fila,
                                                            caplog) -> None:
    cli = _cli(fila)
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_linea_inicio(1, D1, [2, 3])])
    assert "ciz_mismo_dia_omitido" in caplog.text
    assert "racha_fin_no_ciz" not in caplog.text


# ------------------------------- R12 ------------------------------- #

def test_f083_pipeline_r12_mismas_lecturas_que_hoy() -> None:
    cli = _caso_0730()
    cli.racha_leidas.clear()
    cli.estados_leidos.clear()
    _ejecutar(cli, [_linea_fin(2, D2, [1, 3])])
    assert cli.racha_leidas == [["partes:1", "partes:1:ciz", "partes:3",
                                 "partes:3:ciz"]]
    assert cli.estados_leidos == [[HMO_OCT]]


def test_f083_pipeline_r12_inicio_mismas_lecturas_que_hoy() -> None:
    cli = _cli(_fila(7001, fec=D3, rid=3, horide=H_CIV))
    _ejecutar(cli, [_linea_inicio(1, D1, [2, 3])])
    assert cli.racha_leidas == [["partes:1:ciz", "partes:2", "partes:2:ciz",
                                 "partes:3", "partes:3:ciz"]]
    assert cli.estados_leidos == []


# ------------------------- H1 (RM7) ------------------------- #
# Pasada de evidencias, hallazgo H1: la puerta de F-083 (paso 6 bis,
# `_ciz_de_racha`) va ANTES de los conflictos (paso 7). Con un `fin` que
# F-083 omite, el paso 7 no lo ve: ni lee sus lineas existentes ni lo
# ofrece como conflicto.

#: Lecturas del preflight del caso 0730, en orden: sin `lineas_existentes`.
LECTURAS_H1 = ["obra_por_ide", "datos_recursos", "horas_de_recursos",
               "partes_del_periodo", "lineas_por_synckey", "lineas_de_racha",
               "estados_de_partes"]


@pytest.mark.parametrize("ajena", [False, True])
def test_f083_pipeline_h1_puerta_antes_de_los_conflictos(ajena) -> None:
    """H1 / RM7: caso 0730 con el parte de octubre ya con lineas.

    Si la puerta bajara detras del paso 7 (`_lineas_existentes`), el `fin`
    omitido por F-083 pasaria por la lectura de conflictos y, con una linea
    ajena del recurso ese dia, el paso 7 decidiria por F-083 (conflicto u
    omision con otro motivo). Se comparan las lecturas exactas del preflight
    y de la ejecucion, la lista de conflictos y el motivo."""
    cli = _caso_0730()
    if ajena:                       # CIZ manual del recurso el dia D2
        cli.lineas.append(_fila(7100, fec=D2))
    antes = _filas(cli)
    enviadas = _espiar(cli)
    lineas = [_linea_fin(2, D2, [1, 3])]
    cli.llamadas.clear()
    cli.lineas_leidas.clear()
    pf = _pipe(cli).preflight(obra=_obra_f062(), lineas=lineas)
    a = _acc(pf, 2)
    assert a.accion == "omitir" and pf.conflictos == []
    assert "la racha sigue en Sigrid el dia 2026-10-03" in a.motivo
    assert cli.lineas_leidas == []
    assert cli.llamadas == LECTURAS_H1
    cli.llamadas.clear()
    r = _ejecutar(cli, lineas)
    assert r.escritas == [] and enviadas == []
    assert "la racha sigue en Sigrid el dia 2026-10-03" in _motivo(r)
    assert cli.lineas_leidas == [] and "lineas_existentes" not in cli.llamadas
    assert _filas(cli) == antes


# ------------------------------- R18 ------------------------------- #
# Sentencias de la base de la rama (011bc2a; el codigo de sv5 es el mismo
# en 4a614d3), capturadas con el doble antes de F-083.

def _insert(fec, horide, pos, synckey, pre) -> dict:
    return {"op": "insert", "hmoide": HMO_OCT, "reside": 501, "pos": pos,
            "fec": fec, "horide": horide, "can": 0.0, "pre": pre, "tot": 0.0,
            "paride": 0, "ano": 2026, "mes": 10, "synckey": synckey,
            "tex": None, "caaide": 0, "guarda_hmoide": HMO_OCT,
            "pisadas": []}


BASE_R13_JUNTOS = [_insert(D1, H_CIV, 64, "partes:1", 2.0),
                   _insert(D3, H_CIZ, 128, "partes:3", 3.5)]
BASE_R13_REAPROBAR = [_insert(D2, H_CIZ, 192, "partes:2", 3.5)]
BASE_R15 = [_insert(D1, H_CIV, 256, "partes:1", 2.0)]


def _apagado(cli, lineas, como: str):
    from tests.dobles import SettingsFake
    if como == "sin_ajuste":
        pipe = RegistroPipeline(cliente=cli, settings=SettingsFake())
    else:
        pipe = _pipe(cli, mover=False)
    return pipe.ejecutar(obra=_obra_f062(), lineas=lineas)


@pytest.mark.parametrize("como", ["mover_ciz_false", "sin_ajuste"])
def test_f083_pipeline_r18_apagado_caso_0730_como_la_base(como) -> None:
    cli = _cli()
    enviadas = _espiar(cli)
    lineas = [_linea_inicio(1, D1, [2, 3], ciz=False), _linea_fin(2, D2),
              _linea_fin(3, D3, [1, 2])]
    lineas[1].incidencia_rol = "intermedio"
    _apagado(cli, lineas, como)
    assert enviadas == BASE_R13_JUNTOS
    _a_mano_a_civ(cli, "partes:3")
    enviadas.clear()
    cli.racha_leidas.clear()
    r = _apagado(cli, [_linea_fin(2, D2, [1, 3])], como)
    assert enviadas == BASE_R13_REAPROBAR
    assert [e["hora_codigo"] for e in r.escritas] == ["CIZ"]
    assert cli.racha_leidas == [] and cli.estados_leidos == []


@pytest.mark.parametrize("como", ["mover_ciz_false", "sin_ajuste"])
def test_f083_pipeline_r18_apagado_inicio_como_la_base(como, caplog) -> None:
    cli = _cli(_fila(7001, fec=D3, rid=3, horide=H_CIV))
    enviadas = _espiar(cli)
    with caplog.at_level("INFO"):
        _apagado(cli, [_linea_inicio(1, D1, [2, 3])], como)
    assert enviadas == BASE_R15
    assert cli.racha_leidas == [] and cli.estados_leidos == []
    assert "racha_fin_no_ciz" not in caplog.text
