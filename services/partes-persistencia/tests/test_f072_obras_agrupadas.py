# tests/test_f072_obras_agrupadas.py
"""F-072 · Reglas puras de las obras agrupadas (R4-R9, R41).

Casado de postventa (regla P5 de porcentajes, F-025), universo VAR (F-039) y
lectura de la forma del «Nº OBRA» con sus variantes (enmienda del humano del
2026-11-20). Sin red ni BBDD: hojas construidas aquí con datos ficticios.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.services.obras_agrupadas import (
    POSTVENTA,
    VAR,
    Forma,
    Marcas,
    casar_postventa,
    casar_var,
    clave,
    codigo_entrada,
    es_obra_agrupada,
    es_partida_var,
    leer_forma,
    marcas_de,
    normalizar,
    numero_inicial,
)
from application.services.partida_catalog import build_arbol_partidas


def _hoja(ide, cod, *, hoja=True, activa=True, res=None):
    return SimpleNamespace(ide=ide, cod=cod, res=res or f"PARTIDA {cod}",
                           es_hoja=hoja, activa=activa)


def _hojas(*codigos):
    return [_hoja(i, c) for i, c in enumerate(codigos, start=1)]


def _cod(hojas, codigo):
    h = casar_postventa(hojas, codigo)
    return None if h is None else h.cod


# ------------------------------- normalizar ------------------------------ #

def test_f072_normalizar_mayusculas_sin_tildes_espacios_ni_guiones():
    assert normalizar(" 0654-b ") == "0654B"
    assert normalizar("Postventá 5") == "POSTVENTA5"
    assert normalizar("29.1") == "29.1"
    assert normalizar(None) == "" and normalizar("") == ""


# ---------------------------------- R4 ---------------------------------- #

def test_f072_r4_exacta_entera_gana():
    assert _cod(_hojas("0578B", "0578"), "0578") == "0578"


def test_f072_r4_ceros_a_la_izquierda_no_casan():
    assert _cod(_hojas("656"), "0656") is None
    assert _cod(_hojas("0656"), "656") is None


def test_f072_r4_se_compara_normalizado():
    assert _cod(_hojas("0578B"), " 0578 ") == "0578B"
    assert _cod(_hojas("CPB"), "cp") == "CPB"


def test_f072_r4_sin_codigo_no_casa():
    assert _cod(_hojas("0578"), None) is None
    assert _cod(_hojas("0578"), "  ") is None


# ---------------------------------- R5 ---------------------------------- #

def test_f072_r5_sin_exacta_casa_el_sufijo_de_letras():
    assert _cod(_hojas("0578B", "0656"), "0578") == "0578B"


def test_f072_r5_el_guion_no_cuenta():
    assert _cod(_hojas("0654-B"), "0654") == "0654-B"


def test_f072_r5_gana_la_mas_corta_y_a_igualdad_la_menor_normalizada():
    assert _cod(_hojas("0578AB", "0578C"), "0578") == "0578C"
    assert _cod(_hojas("0578-C", "0578B"), "0578") == "0578B"


@pytest.mark.parametrize("partida, obra", [
    ("CP.1", "CP"), ("0678.MO", "0678"), ("06561", "0656"),
    ("0578B1", "0578"), ("0578 B.", "0578"),
], ids=["punto", "obra-capitulo", "digito", "letra-digito", "letra-punto"])
def test_f072_r5_prefijo_seguido_de_otra_cosa_no_casa(partida, obra):
    assert _cod(_hojas(partida), obra) is None


def test_f072_r5_ni_descripcion_ni_nombre():
    hojas = [_hoja(1, "CI.7.5", res="OT"), _hoja(2, "0611", res="191105")]
    assert _cod(hojas, "OT") is None
    assert _cod(hojas, "191105") is None


# ---------------------------------- R6 ---------------------------------- #

def test_f072_r6_ni_capitulo_ni_de_baja():
    hojas = [_hoja(1, "0578", hoja=False), _hoja(2, "0578", activa=False),
             _hoja(3, "0578B", activa=False)]
    assert casar_postventa(hojas, "0578") is None


def test_f072_r6_no_depende_del_orden_de_las_filas():
    directo = [_hoja(1, "0578C"), _hoja(2, "0578B")]
    assert _cod(directo, "0578") == _cod(list(reversed(directo)), "0578") \
        == "0578B"


def test_f072_r6_con_varias_exactas_gana_la_de_menor_ide():
    hojas = [_hoja(9, "0578"), _hoja(4, "05 78"), _hoja(7, "0578")]
    assert casar_postventa(hojas, "0578").ide == 4
    assert casar_postventa(list(reversed(hojas)), "0578").ide == 4


def test_f072_r6_a_igual_sufijo_gana_la_de_menor_ide():
    hojas = [_hoja(8, "0578B"), _hoja(3, "0578-B")]
    assert casar_postventa(hojas, "0578").ide == 3


def test_f072_r6_acepta_el_arbol_de_partidas():
    """Con los nodos reales de `build_arbol_partidas` (dict por ide)."""
    filas = [SimpleNamespace(ide=100, padide=0, cod="CD", res="COSTES DIRECTOS",
                             tex=None, tipdes=0),
             SimpleNamespace(ide=1, padide=100, cod="0578B", res="X",
                             tex=None, tipdes=0),
             SimpleNamespace(ide=2, padide=100, cod="0578", res="X",
                             tex=None, tipdes=1)]
    nodos = build_arbol_partidas(filas)
    assert casar_postventa(nodos, "0578").ide == 1
    assert casar_postventa(nodos, "CD") is None


# ---------------------------------- R7 ---------------------------------- #

@pytest.mark.parametrize("cod, numero", [
    ("29", 29), ("30", 30), ("100", 100), ("029", 29), ("29.1", 29),
    ("29A", 29), (" 29 ", 29), ("28", 28), ("05", 5), ("0", 0),
    ("CI.1.1", None), ("A29", None), ("", None), ("   ", None), (None, None),
])
def test_f072_r7_numero_inicial(cod, numero):
    assert numero_inicial(cod) == numero


@pytest.mark.parametrize("cod, hoja, activa, es_var", [
    ("29", True, True, True), ("30", True, True, True),
    ("100", True, True, True), ("029", True, True, True),
    ("29.1", True, True, True), ("29A", True, True, True),
    ("28", True, True, False), ("05", True, True, False),
    ("CI.1.1", True, True, False), (None, True, True, False),
    ("31", False, True, False), ("32", True, False, False),
], ids=lambda v: repr(v))
def test_f072_r7_es_partida_var(cod, hoja, activa, es_var):
    assert es_partida_var(_hoja(1, cod, hoja=hoja, activa=activa), 29) \
        is es_var


def test_f072_r7_el_umbral_es_inclusivo_y_es_el_que_se_pasa():
    assert es_partida_var(_hoja(1, "29"), 29) is True
    assert es_partida_var(_hoja(1, "29"), 30) is False
    assert es_partida_var(_hoja(1, "0"), 0) is True


# ---------------------------------- R8 ---------------------------------- #

def test_f072_r8_igual_normalizado():
    vs = _hojas("29", "029", "30")
    assert casar_var(vs, "29").ide == 1
    assert casar_var(vs, "029").ide == 2
    assert casar_var(_hojas("29A"), "29a").ide == 1


def test_f072_r8_sin_igual_la_unica_con_el_mismo_numero_inicial():
    assert casar_var(_hojas("029", "30"), "29").cod == "029"
    assert casar_var(_hojas("29", "30"), "0029").cod == "29"


def test_f072_r8_varias_o_ninguna_none():
    assert casar_var(_hojas("029", "29.1"), "0029") is None
    assert casar_var(_hojas("30"), "29") is None
    assert casar_var(_hojas("30"), "ABC") is None
    assert casar_var(_hojas("30"), "") is None
    assert casar_var([], "29") is None


def test_f072_r8_d1c_el_segundo_paso_solo_si_lo_leido_es_solo_un_numero():
    """D1 (c), humano 2026-11-23: sin igual, la única con el mismo número
    inicial SOLO si lo leído es solo un número; `29.3` o `29A` sin su
    partida exacta van a revisión (`None`)."""
    assert casar_var(_hojas("29.1", "30"), "29.3") is None
    assert casar_var(_hojas("29", "30"), "29A") is None
    assert casar_var(_hojas("29", "30"), "29-B") is None
    assert casar_var(_hojas("29.1", "30"), " 29 ").cod == "29.1"
    assert casar_var(_hojas("029", "30"), "0029").cod == "029"


def test_f072_r8_con_varias_iguales_gana_la_de_menor_ide():
    vs = [_hoja(7, "29"), _hoja(3, "2 9")]
    assert casar_var(vs, "29").ide == 3


# ------------------------------ R9 y R41 -------------------------------- #

MARCAS = Marcas(postventa=("POSTV2", "POSTVENTA", "POSTV", "POST"),
                var=("VAR", "V"))


@pytest.mark.parametrize("leido, tipo, resto", [
    ("V29", VAR, "29"), ("v-29", VAR, "29"), ("V.29", VAR, "29"),
    ("V/29", VAR, "29"), ("29 V", VAR, "29"), ("29V", VAR, "29"),
    ("V 29", VAR, "29"), ("V - 29", VAR, "29"), ("VAR 29", VAR, "29"),
    ("VAR-29", VAR, "29"), ("var29", VAR, "29"), ("29/VAR", VAR, "29"),
    ("VAR 29.1", VAR, "29.1"), ("V-29A", VAR, "29A"),
    ("POST578", POSTVENTA, "578"), ("post-578", POSTVENTA, "578"),
    ("578/POST", POSTVENTA, "578"), ("Postventá 578", POSTVENTA, "578"),
    ("POSTVENTA 578", POSTVENTA, "578"), ("POSTVENTA-0578B", POSTVENTA, "0578B"),
    ("POSTV 0578", POSTVENTA, "0578"), ("0578 POSTVENTA", POSTVENTA, "0578"),
    ("POSTV2 0578", POSTVENTA, "0578"), ("POSTVENTA CP", POSTVENTA, "CP"),
    ("POSTV2", POSTVENTA, ""), ("postv2", POSTVENTA, ""),
    ("POSTV", POSTVENTA, ""), ("Post-V2", POSTVENTA, ""),
    ("POSTVENTA", POSTVENTA, ""), ("VAR", VAR, ""), (" var ", VAR, ""),
    ("150702-V", VAR, "150702"),
])
def test_f072_r41_valen(leido, tipo, resto):
    assert leer_forma(leido, MARCAS) == Forma(tipo=tipo, resto=resto)


@pytest.mark.parametrize("leido", [
    "V", " v ", "V-", "VALENCIA 3", "POSTE", "0578", "", None, "   ",
    "ABC V", "VA 29", "V-ABC", "-29", "POSTVENTAS 3", "PV 29", "29 VA",
])
def test_f072_r41_no_valen(leido):
    assert leer_forma(leido, MARCAS) is None


def test_f072_r41_gana_la_marca_mas_larga():
    """`POSTVENTA 578` es la marca `POSTVENTA`, no `POST` con resto
    `VENTA 578` (que tampoco valdría: sin separador, empieza por letra)."""
    assert leer_forma("POSTVENTA578", MARCAS) == Forma(POSTVENTA, "578")
    solo_post = Marcas(postventa=("POST", "POSTVENTA"), var=())
    assert leer_forma("POSTVENTA 578", solo_post) == Forma(POSTVENTA, "578")


def test_f072_r41_sin_separador_el_resto_empieza_por_digito():
    assert leer_forma("POSTCP", MARCAS) is None
    assert leer_forma("POST CP", MARCAS) == Forma(POSTVENTA, "CP")
    assert leer_forma("CPPOST", MARCAS) is None
    assert leer_forma("CP POST", MARCAS) == Forma(POSTVENTA, "CP")


def test_f072_r41_alias_de_una_letra_solo_con_resto_que_empieza_por_digito():
    assert leer_forma("V CP", MARCAS) is None
    assert leer_forma("CP V", MARCAS) is None
    assert leer_forma("VAR CP", MARCAS) == Forma(VAR, "CP")


def test_f072_r41_sin_marcas_configuradas_no_hay_forma():
    assert leer_forma("VAR 29", Marcas(postventa=(), var=())) is None
    assert leer_forma("V29", Marcas(postventa=("POSTV2",), var=())) is None


def test_f072_r9_delante_antes_que_detras():
    """Con marca delante y detrás, la de delante manda (orden determinista)."""
    assert leer_forma("V 29 POST", MARCAS) == Forma(VAR, "29 POST")


# --------------------------- configuración ------------------------------ #

def test_f072_marcas_de_codigo_y_alias():
    m = marcas_de(postventa_cod=" POSTV2 ", postventa_alias="POSTVENTA, postv ,POST,",
                  var_cod="VAR", var_alias="V")
    assert m == Marcas(postventa=("POSTV2", "POSTVENTA", "POSTV", "POST"),
                       var=("VAR", "V"))


def test_f072_marcas_de_sin_codigo_ignora_los_alias():
    m = marcas_de(postventa_cod="", postventa_alias="POST", var_cod=None,
                  var_alias="V")
    assert m == Marcas(postventa=(), var=())


def test_f072_clave_quita_tildes_y_separadores():
    assert clave("150702-V") == "150702V"
    assert clave(" Post.v/2 ") == "POSTV2"
    assert clave(None) == ""


def test_f072_es_obra_agrupada():
    assert es_obra_agrupada("postv2", postventa="POSTV2", var="VAR") == POSTVENTA
    assert es_obra_agrupada(" VAR ", postventa="POSTV2", var="VAR") == VAR
    assert es_obra_agrupada("POSTV", postventa="POSTV2", var="VAR") is None
    assert es_obra_agrupada("VAR", postventa=None, var=None) is None
    assert es_obra_agrupada("", postventa="", var="") is None
    assert es_obra_agrupada(None, postventa="POSTV2", var="VAR") is None


def test_f072_codigo_entrada():
    assert codigo_entrada(POSTVENTA, "VAR", "0578") == "Postv-0578"
    assert codigo_entrada(VAR, "VAR", "29") == "VAR-29"


# ------------- T28: supervivientes de la campaña de mutación ------------- #
# Van aquí (y no en un fichero aparte) para que las cuatro copias del gemelo
# los ejecuten por `test_f072_obras_agrupadas_copia.py`.

def test_t28_r41_basta_con_que_el_resto_empiece_por_digito():
    """`_resto_valido` (`:218`): mira el PRIMER carácter del resto, no los
    dos primeros: `2.1` y `5B` empiezan por dígito."""
    assert leer_forma("V 2.1", MARCAS) == Forma(VAR, "2.1")
    assert leer_forma("POST5B", MARCAS) == Forma(POSTVENTA, "5B")


def test_t28_una_marca_que_es_solo_separadores_no_cuenta():
    """`_ordenadas` (`:211`): un alias que se queda vacío al quitarle los
    separadores (`-`) no es marca; si contara, casaría cualquier código."""
    m = marcas_de(postventa_cod="POSTV2", postventa_alias="-", var_cod=None,
                  var_alias=None)
    assert leer_forma("0578", m) is None
    assert leer_forma("POSTV2 0578", m) == Forma(POSTVENTA, "0578")


def test_t28_var_desde_admite_el_entero_0():
    """`_desde` (`:178`): un `0` entero es un umbral válido, no «vacío»."""
    from application.services.obras_agrupadas import ajustes_de
    assert ajustes_de(postventa_cod=None, var_cod="VAR",
                      var_desde=0).var_desde == 0


def test_t28_los_valores_del_gemelo_son_inmutables():
    """`Marcas` (`:125`), `Ajustes` (`:152`) y `Forma` (`:199`) son
    `frozen`: se comparten entre peticiones y cachés."""
    import dataclasses
    from application.services.obras_agrupadas import ajustes_de
    ajustes = ajustes_de(postventa_cod="POSTV2", var_cod="VAR", var_desde="29")
    for valor, campo in ((MARCAS, "var"), (ajustes, "var_desde"),
                         (Forma(VAR, "29"), "resto")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(valor, campo, None)
