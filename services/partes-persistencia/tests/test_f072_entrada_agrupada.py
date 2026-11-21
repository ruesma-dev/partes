# tests/test_f072_entrada_agrupada.py
"""F-072 · `ResolutorEntradas`: la entrada de una obra agrupada (R14-R17, R19).

VAR con gemelas por membrete y trabajadores (F-023), postventa con ceros a la
izquierda y la empresa de la obra X, forma base con una y con varias
entradas, cada motivo de R17 (≤ 24 caracteres) y los fallos de lectura, que
suben sin cachearse. Sin red ni BBDD: Sigrid en memoria (`f072_comun`).
"""
from __future__ import annotations

import pytest

from application.services import entrada_agrupada as ea
from application.services.entrada_agrupada import ResolutorEntradas
from application.services.obras_agrupadas import POSTVENTA, VAR, Forma
from domain.models.sigrid_models import ObraRow
from tests import f072_comun as c


def _resolver(forma, parte, lookup=None, *, membrete=None, ajustes=c.AJUSTES,
              resolutor=None):
    lookup = lookup or c.LookupF072()
    matchers = c.proveedor(lookup).get()
    empresa_m, _ = matchers.empresas.resolver(membrete)
    indice = matchers.indice
    dnis = sorted({r.trabajador_dni_leido for r in parte.registros} - {None})
    discriminantes = [indice.empresas_con_recurso(d, c.HOY) for d in dnis]
    resolutor = resolutor or ResolutorEntradas(lookup=lookup, ajustes=ajustes)
    return resolutor.resolver(forma, parte, matchers, empresa_m, discriminantes)


def _clave(res):
    return (res.obra.ide, res.obra.method,
            None if res.partida is None else res.partida.ide, res.tipo)


# ---------------------------------- R14 --------------------------------- #

def test_f072_r14_var_elige_la_obra_var_por_los_trabajadores():
    res = _resolver(Forma(VAR, "29"), c.parte("V-29"))
    assert _clave(res) == (9101, "var", 91012, VAR)
    assert res.obra.score == 1.0 and res.obra.empresa == 1
    assert res.obra.codigo == "VAR"


def test_f072_r14_var_gemela_por_membrete():
    res = _resolver(Forma(VAR, "29"), c.parte("V-29", ("BEA VEINTIOCHO", c.DNI_B)),
                    membrete="PORSAN S.L.")
    assert _clave(res) == (9128, "var", 91281, VAR)


@pytest.mark.parametrize("resto, partida", [
    ("30", 91013), ("030", 91013), ("0029", 91012), ("32", 91016),
    ("32.1", 91016),
])
def test_f072_r14_var_casa_con_r7_y_r8(resto, partida):
    res = _resolver(Forma(VAR, resto), c.parte("x"))
    assert _clave(res) == (9101, "var", partida, VAR)


@pytest.mark.parametrize("resto", ["28", "31", "CP", "99", "05"])
def test_f072_r17_var_fuera_del_universo(resto):
    res = _resolver(Forma(VAR, resto), c.parte("x"))
    assert _clave(res) == (None, "var_fuera_universo", None, None)


def test_f072_r17_var_sin_obra_unica_en_la_empresa():
    """Trabajadores de dos empresas y sin membrete: la VAR es ambigua."""
    p = c.parte("V-29", ("ANA UNO", c.DNI_A), ("BEA VEINTIOCHO", c.DNI_B))
    res = _resolver(Forma(VAR, "29"), p)
    assert _clave(res) == (None, "agrupada_sin_obra", None, None)


# ---------------------------------- R15 --------------------------------- #

@pytest.mark.parametrize("resto, partida", [
    ("578", 90011), ("0578", 90011), ("654", 90012), ("100", 90013),
])
def test_f072_r15_postventa_casa_la_obra_x_con_ceros(resto, partida):
    res = _resolver(Forma(POSTVENTA, resto), c.parte("POST " + resto))
    assert _clave(res) == (9001, "postventa", partida, POSTVENTA)
    assert res.obra.codigo == "POSTV2" and res.obra.empresa == 1
    assert res.obra.score == 1.0


def test_f072_r15_postventa_toma_la_postventa_de_la_empresa_de_x():
    res = _resolver(Forma(POSTVENTA, "400"),
                    c.parte("POST 400", ("BEA VEINTIOCHO", c.DNI_B)))
    assert _clave(res) == (9028, "postventa", 90281, POSTVENTA)


@pytest.mark.parametrize("resto", ["999", "VAR", "POSTV2", ""])
def test_f072_r17_postventa_obra_no_casa_o_es_agrupada(resto):
    res = _resolver(Forma(POSTVENTA, resto or "  "), c.parte("x"))
    assert _clave(res) == (None, "postventa_obra_no_casa", None, None)


def test_f072_r17_postventa_sin_obra_de_postventa_en_la_empresa():
    lookup = c.LookupF072(obras=[o for o in c.OBRAS if o is not c.PV28])
    res = _resolver(Forma(POSTVENTA, "400"),
                    c.parte("x", ("BEA VEINTIOCHO", c.DNI_B)), lookup)
    assert _clave(res) == (None, "agrupada_sin_obra", None, None)


def test_f072_r17_postventa_con_varias_obras_de_postventa_en_la_empresa():
    otra = ObraRow(ide=9002, codigo="POSTV2", nombre="OTRA", empresa=1)
    lookup = c.LookupF072(obras=c.OBRAS + (otra,))
    res = _resolver(Forma(POSTVENTA, "578"), c.parte("x"), lookup)
    assert _clave(res) == (None, "agrupada_sin_obra", None, None)
    assert lookup.llamadas == []


def test_f072_r17_postventa_sin_partida_que_case():
    o700 = ObraRow(ide=700, codigo="0700", nombre="Sin partida", empresa=1)
    res = _resolver(Forma(POSTVENTA, "700"), c.parte("x"),
                    c.LookupF072(obras=c.OBRAS + (o700,)))
    assert _clave(res) == (None, "postventa_sin_partida", None, None)


# ---------------------------------- R16 --------------------------------- #

def test_f072_r16_base_con_una_entrada_en_las_partidas():
    p = c.parte("VAR", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                partidas=["29", " 29 "])
    assert _clave(_resolver(Forma(VAR, ""), p)) == (9101, "var", 91012, VAR)


def test_f072_r16_base_postventa():
    p = c.parte("POSTV2", partidas=["0578"])
    assert _clave(_resolver(Forma(POSTVENTA, ""), p)) == (
        9001, "postventa", 90011, POSTVENTA)


def test_f072_r16_base_con_dos_entradas_va_a_revision():
    p = c.parte("VAR", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                partidas=["29", "030"])
    assert _clave(_resolver(Forma(VAR, ""), p)) == (
        None, "agrupada_varias_entradas", None, None)


def test_f072_r16_base_con_una_entrada_y_un_fallo_va_a_revision():
    p = c.parte("VAR", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                partidas=["29", "31"])
    assert _clave(_resolver(Forma(VAR, ""), p))[1] == "agrupada_varias_entradas"


@pytest.mark.parametrize("partidas", [[None], [""], ["  "]])
def test_f072_r16_base_sin_partida_leida(partidas):
    p = c.parte("VAR", partidas=partidas)
    assert _clave(_resolver(Forma(VAR, ""), p)) == (
        None, "agrupada_sin_entrada", None, None)


def test_f072_r16_base_con_todas_fallidas_por_el_mismo_motivo():
    p = c.parte("VAR", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                partidas=["31", "28"])
    assert _clave(_resolver(Forma(VAR, ""), p))[1] == "var_fuera_universo"


def test_f072_r16_base_con_fallos_de_motivos_distintos():
    o700 = ObraRow(ide=700, codigo="0700", nombre="Sin partida", empresa=1)
    p = c.parte("POSTV2", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                partidas=["999", "700"])
    res = _resolver(Forma(POSTVENTA, ""), p, c.LookupF072(obras=c.OBRAS + (o700,)))
    assert _clave(res)[1] == "agrupada_sin_entrada"


# ---------------------------------- R17 --------------------------------- #

def test_f072_r17_los_motivos_caben_en_obra_match_method():
    for motivo in ea.MOTIVOS:
        assert len(motivo) <= 24, motivo
    assert set(ea.MOTIVOS) == {
        "postventa_obra_no_casa", "agrupada_sin_obra", "postventa_sin_partida",
        "var_fuera_universo", "agrupada_sin_entrada",
        "agrupada_varias_entradas"}


# ---------------------------------- R19 --------------------------------- #

@pytest.mark.parametrize("error", [RuntimeError("sigrid-api caido"),
                                   RuntimeError("respuesta truncated")])
def test_f072_r19_un_fallo_de_lectura_sube_y_no_se_cachea(error):
    lookup = c.LookupF072(error=error)
    resolutor = ResolutorEntradas(lookup=lookup, ajustes=c.AJUSTES)
    with pytest.raises(RuntimeError):
        _resolver(Forma(VAR, "29"), c.parte("x"), lookup, resolutor=resolutor)
    lookup.error = None
    res = _resolver(Forma(VAR, "29"), c.parte("x"), lookup, resolutor=resolutor)
    assert _clave(res) == (9101, "var", 91012, VAR)
    assert lookup.llamadas == [9101, 9101]


def test_f072_r14_el_presupuesto_se_cachea_con_ttl():
    lookup = c.LookupF072()
    resolutor = ResolutorEntradas(lookup=lookup, ajustes=c.AJUSTES)
    for resto in ("29", "030"):
        _resolver(Forma(VAR, resto), c.parte("x"), lookup, resolutor=resolutor)
    assert lookup.llamadas == [9101]
    caducado = ResolutorEntradas(lookup=lookup, ajustes=c.AJUSTES, ttl_seconds=0)
    for resto in ("29", "030"):
        _resolver(Forma(VAR, resto), c.parte("x"), lookup, resolutor=caducado)
    assert lookup.llamadas == [9101, 9101, 9101]


# ----------------------- ObraMatcher.obras_de_codigo --------------------- #

def test_f072_obras_de_codigo_por_codigo_normalizado():
    matchers = c.proveedor(c.LookupF072()).get()
    assert {o.ide for o in matchers.obra.obras_de_codigo("postv2")} == {9001, 9028}
    assert matchers.obra.obras_de_codigo("NADA") == []
    assert matchers.obra.obras_de_codigo(None) == []
    assert [o.ide for o in matchers.obra.obras_de_clave("150702V")] == [7001]
