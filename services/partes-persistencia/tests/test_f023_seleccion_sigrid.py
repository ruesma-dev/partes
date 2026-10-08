# tests/test_f023_seleccion_sigrid.py
"""F-023 · reglas puras de seleccion contra los maestros de Sigrid (sv3).

`application/services/seleccion_sigrid.py` concentra lo que decide F-023
sin tocar red ni base: que es «de alta» (R1), que obra gana entre las que
comparten codigo (R9-R13), que ficha de empleado casa con un DNI (R17-R21)
y que recurso se imputa en una linea (R25-R28).

Todo con valores SINTETICOS: DNIs, ides y codigos inventados. El caso
guia (una ficha de alta que apunta a un recurso de baja desde 2021 y otro
recurso de alta en la misma empresa) se reproduce con numeros de juguete.
"""
from __future__ import annotations

import pytest

from application.services.seleccion_sigrid import (
    IndicePersonas,
    Resolucion,
    ResolucionRecurso,
    de_alta,
    elegir_obra,
    elegir_por_nombre,
)
from domain.models.sigrid_models import EmpleadoRow, ObraRow
from tests.dobles import recurso_persona

HOY = 20260915
DNI = "12345678Z"
OTRO_DNI = "87654321X"


def _ficha(ide, *, dni=DNI, empresa=1, fecbaj=0, reside=None, nombre=None):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre or f"P {ide}",
                       dni=dni, reside=reside, empresa=empresa, fecbaj=fecbaj)


def _recurso(ide, *, conide=None, cif=None, empresa=1, fecbaj=0):
    return recurso_persona(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj)


def _obra(ide, codigo, empresa, nombre=None):
    return ObraRow(ide=ide, codigo=codigo, nombre=nombre or f"Obra {ide}",
                   empresa=empresa)


# ============================== R1 · alta =============================== #

@pytest.mark.parametrize("fecbaj, esperado", [
    (None, True),          # NULL: nunca dado de baja
    (0, True),             # 0: la codificacion de Sigrid de «sin baja»
    (HOY + 1, True),       # baja futura: aun de alta ese dia
    (HOY, False),          # el mismo dia de la baja ya no esta de alta
    (HOY - 1, False),
    (20210126, False),
])
def test_f023_r1_de_alta_segun_con_fecbaj(fecbaj, esperado) -> None:
    assert de_alta(fecbaj, HOY) is esperado


# ====================== R9-R13 · obras con el codigo ===================== #

GEMELA_1 = _obra(100, "0100", 1, "Residencial Norte")
GEMELA_28 = _obra(200, "0100", 28, "Nave Sur")
UNICA = _obra(300, "0300", 1)


def test_f023_r9_con_membrete_gana_la_obra_de_esa_empresa() -> None:
    obra, motivo = elegir_obra([GEMELA_1, GEMELA_28], 28, [], None, 0.55)
    assert obra is GEMELA_28
    assert motivo == "codigo_membrete"


def test_f023_r9_con_membrete_y_una_sola_obra_el_metodo_es_codigo() -> None:
    obra, motivo = elegir_obra([UNICA], 1, [], None, 0.55)
    assert obra is UNICA
    assert motivo == "codigo"


def test_f023_r10_membrete_de_otra_empresa_no_casa() -> None:
    obra, motivo = elegir_obra([UNICA], 28, [], None, 0.55)
    assert obra is None
    assert motivo == "codigo_otra_empresa"


def test_f023_r10_el_membrete_manda_sobre_los_trabajadores() -> None:
    """Aunque los trabajadores senalen la 1, el membrete dice 28."""
    obra, motivo = elegir_obra([UNICA], 28, [frozenset({1})], None, 0.55)
    assert (obra, motivo) == (None, "codigo_otra_empresa")


def test_f023_r9_dos_obras_del_codigo_en_la_misma_empresa_es_ambiguo() -> None:
    otra = _obra(101, "0100", 1)
    obra, motivo = elegir_obra([GEMELA_1, otra], 1, [], None, 0.55)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_sin_membrete_una_sola_obra_casa_por_codigo() -> None:
    obra, motivo = elegir_obra([UNICA], None, [frozenset({28})], None, 0.55)
    assert (obra, motivo) == (UNICA, "codigo")


def test_f023_r11_los_trabajadores_eligen_la_gemela() -> None:
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None, [frozenset({28}), frozenset({28})],
        None, 0.55)
    assert (obra, motivo) == (GEMELA_28, "codigo_trabajadores")


def test_f023_r11_solo_discrimina_quien_esta_en_una_de_esas_empresas() -> None:
    """{1, 28} no discrimina; {28, 31} si (la 31 no tiene esa obra); el
    vacio (sin recursos de alta) tampoco cuenta."""
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None,
        [frozenset({1, 28}), frozenset({28, 31}), frozenset()],
        None, 0.55)
    assert (obra, motivo) == (GEMELA_28, "codigo_trabajadores")


def test_f023_r13_discriminantes_que_discrepan_es_ambiguo() -> None:
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None, [frozenset({1}), frozenset({28})],
        "Nave Sur", 0.55)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_r13_empresa_senalada_con_dos_obras_del_codigo_es_ambiguo() -> None:
    otra_28 = _obra(201, "0100", 28)
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28, otra_28], None, [frozenset({28})], None, 0.55)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_r12_sin_discriminantes_decide_el_nombre() -> None:
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None, [frozenset({1, 28})], "nave sur", 0.55)
    assert (obra, motivo) == (GEMELA_28, "codigo_nombre")


def test_f023_r12_el_nombre_tiene_que_superar_el_umbral() -> None:
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None, [], "nave sur", 1.01)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_r12_el_umbral_se_alcanza_con_la_puntuacion_justa() -> None:
    """`nombre` exacto puntua 1.0: con umbral 1.0 casa (>=, no >)."""
    obra, motivo = elegir_obra(
        [GEMELA_1, GEMELA_28], None, [], "Nave Sur", 1.0)
    assert (obra, motivo) == (GEMELA_28, "codigo_nombre")


def test_f023_r13_gemelas_con_el_mismo_nombre_empatan() -> None:
    a = _obra(100, "0100", 1, "Mismo Nombre")
    b = _obra(200, "0100", 28, "Mismo Nombre")
    obra, motivo = elegir_obra([a, b], None, [], "Mismo Nombre", 0.55)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_r13_sin_nombre_ni_discriminantes_es_ambiguo() -> None:
    obra, motivo = elegir_obra([GEMELA_1, GEMELA_28], None, [], None, 0.55)
    assert (obra, motivo) == (None, "codigo_ambiguo")


def test_f023_sin_candidatas_no_hay_obra() -> None:
    assert elegir_obra([], None, [], "x", 0.55) == (None, "none")
    assert elegir_obra([], 1, [], "x", 0.55) == (None, "none")


# =================== R11 (entrada) · empresas con recurso =============== #

def test_f023_r11_empresas_con_recurso_de_alta_a_la_fecha() -> None:
    indice = IndicePersonas(
        [_ficha(10, empresa=1), _ficha(11, empresa=31)],
        [_recurso(900, conide=10, empresa=1, fecbaj=20210126),   # baja
         _recurso(901, conide=10, empresa=1),
         _recurso(902, conide=11, empresa=31),
         _recurso(903, cif=DNI, empresa=28),                     # por cif
         _recurso(904, conide=99, empresa=5)])                   # ajeno
    assert indice.empresas_con_recurso(DNI, HOY) == frozenset({1, 28, 31})
    # Con el DNI escrito de otra forma (guion, minusculas) es el mismo.
    assert indice.empresas_con_recurso("12345678-z", HOY) == \
        frozenset({1, 28, 31})


def test_f023_r11_sin_dni_o_sin_recursos_no_hay_empresas() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(900, conide=10,
                                                    fecbaj=HOY)])
    assert indice.empresas_con_recurso(None, HOY) == frozenset()
    assert indice.empresas_con_recurso(DNI, HOY) == frozenset()   # de baja
    assert indice.empresas_con_recurso(OTRO_DNI, HOY) == frozenset()


def test_f023_r11_un_recurso_sin_empresa_no_cuenta() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(900, conide=10,
                                                    empresa=None)])
    assert indice.empresas_con_recurso(DNI, HOY) == frozenset()


# ================== R17-R21 · la ficha de empleado por DNI =============== #

def test_f023_r18_una_ficha_de_alta_en_la_empresa_casa() -> None:
    indice = IndicePersonas([_ficha(10, empresa=1), _ficha(11, empresa=28)],
                            [])
    assert indice.elegir_ficha(DNI, 28, HOY) == Resolucion(11, "ok")
    assert indice.ficha(11).empresa == 28


def test_f023_r19_dos_fichas_de_alta_en_la_empresa_es_ambiguo() -> None:
    indice = IndicePersonas([_ficha(10), _ficha(11)], [])
    assert indice.elegir_ficha(DNI, 1, HOY) == Resolucion(None, "ambiguo")


def test_f023_r20_solo_fichas_de_baja() -> None:
    indice = IndicePersonas([_ficha(10, fecbaj=HOY - 1),
                             _ficha(11, empresa=28, fecbaj=HOY)], [])
    assert indice.elegir_ficha(DNI, 1, HOY) == Resolucion(None, "solo_baja")
    assert indice.elegir_ficha(DNI, None, HOY) == \
        Resolucion(None, "solo_baja")


def test_f023_r21_solo_de_alta_en_otra_empresa() -> None:
    indice = IndicePersonas([_ficha(10, empresa=28),
                             _ficha(11, empresa=1, fecbaj=HOY - 1)], [])
    assert indice.elegir_ficha(DNI, 1, HOY) == \
        Resolucion(None, "otra_empresa")


def test_f023_r17_sin_empresa_del_parte_compiten_todas() -> None:
    indice = IndicePersonas([_ficha(10, empresa=28)], [])
    assert indice.elegir_ficha(DNI, None, HOY) == Resolucion(10, "ok")
    dos = IndicePersonas([_ficha(10, empresa=28), _ficha(11, empresa=1)], [])
    assert dos.elegir_ficha(DNI, None, HOY) == Resolucion(None, "ambiguo")


def test_f023_r17_la_ficha_de_baja_no_compite() -> None:
    """Una ficha de baja y otra de alta en la misma empresa: casa la de
    alta, no hay ambiguedad."""
    indice = IndicePersonas([_ficha(10, fecbaj=HOY - 1), _ficha(11)], [])
    assert indice.elegir_ficha(DNI, 1, HOY) == Resolucion(11, "ok")


def test_f023_dni_desconocido_o_vacio() -> None:
    indice = IndicePersonas([_ficha(10)], [])
    assert indice.elegir_ficha(OTRO_DNI, 1, HOY) == \
        Resolucion(None, "desconocido")
    assert indice.elegir_ficha(None, 1, HOY) == \
        Resolucion(None, "desconocido")
    assert indice.elegir_ficha("  ", 1, HOY) == \
        Resolucion(None, "desconocido")


def test_f023_ficha_y_recurso_por_ide() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(900, conide=10)])
    assert indice.ficha(10).ide == 10
    assert indice.ficha(99) is None
    assert indice.recurso(900).ide == 900
    assert indice.recurso(None) is None
    assert [r.ide for r in indice.recursos] == [900]


def test_f023_empresa_de_obra() -> None:
    indice = IndicePersonas([], [], obras=[GEMELA_28, UNICA])
    assert indice.empresa_de_obra(200) == 28
    assert indice.empresa_de_obra(300) == 1
    assert indice.empresa_de_obra(999) is None
    assert indice.empresa_de_obra(None) is None


# ================= R25-R28 · el recurso de cada linea =================== #

def _caso_guia() -> IndicePersonas:
    """Ficha de alta de la empresa 1 cuyo `reside` (900) esta de baja
    desde 2021; la misma persona tiene otro recurso de alta en la 1 (901)
    y otro en la 31 (902), enlazado a su ficha de la 31."""
    return IndicePersonas(
        [_ficha(10, empresa=1, reside=900), _ficha(11, empresa=31,
                                                  reside=902)],
        [_recurso(900, conide=10, cif=DNI, empresa=1, fecbaj=20210126),
         _recurso(901, conide=10, cif=DNI, empresa=1),
         _recurso(902, conide=11, empresa=31)])


def test_f023_r25_r27_caso_guia_queda_el_recurso_de_alta() -> None:
    res = _caso_guia().elegir_recurso(DNI, 10, 900, 1, HOY)
    assert res.ide == 901
    assert res.motivo == "ok"
    assert (res.descartados_baja, res.descartados_otra_empresa) == (1, 1)


def test_f023_r27_el_reside_de_la_ficha_nunca_fuera_de_candidatos() -> None:
    """Ni de baja (900), ni de otra empresa (902), ni de otra persona."""
    indice = IndicePersonas(
        [_ficha(10, empresa=1), _ficha(20, dni=OTRO_DNI)],
        [_recurso(900, conide=10, fecbaj=HOY - 1),
         _recurso(950, conide=20)])
    assert indice.elegir_recurso(DNI, 10, 900, 1, HOY).ide is None
    assert indice.elegir_recurso(DNI, 10, 950, 1, HOY).ide is None
    assert _caso_guia().elegir_recurso(DNI, 10, 902, 1, HOY).ide == 901


def test_f023_r26_varios_candidatos_gana_el_reside_de_la_ficha() -> None:
    indice = IndicePersonas(
        [_ficha(10)], [_recurso(901, conide=10), _recurso(903, cif=DNI)])
    assert indice.elegir_recurso(DNI, 10, 903, 1, HOY) == \
        ResolucionRecurso(903, "ok")


def test_f023_r26_si_no_el_unico_con_conide_de_la_ficha_casada() -> None:
    indice = IndicePersonas(
        [_ficha(10)], [_recurso(901, conide=10), _recurso(903, cif=DNI)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY) == \
        ResolucionRecurso(901, "ok")


def test_f023_r26_si_quedan_varios_es_ambiguo() -> None:
    indice = IndicePersonas(
        [_ficha(10)], [_recurso(901, conide=10), _recurso(902, conide=10)])
    res = indice.elegir_recurso(DNI, 10, None, 1, HOY)
    assert (res.ide, res.motivo) == (None, "ambiguo")
    sin_conide = IndicePersonas(
        [_ficha(10)], [_recurso(901, cif=DNI), _recurso(902, cif=DNI)])
    assert sin_conide.elegir_recurso(DNI, 10, None, 1, HOY).motivo == \
        "ambiguo"


def test_f023_r25_candidatos_de_todas_las_fichas_del_dni() -> None:
    """La ficha casada es la de la 1, pero el recurso de la 28 cuelga de
    la ficha de la 28 de la misma persona: es candidato en la 28."""
    indice = IndicePersonas(
        [_ficha(10, empresa=1), _ficha(11, empresa=28)],
        [_recurso(902, conide=11, empresa=28)])
    assert indice.elegir_recurso(DNI, 10, None, 28, HOY).ide == 902


def test_f023_r25_sin_dni_solo_la_ficha_casada() -> None:
    indice = IndicePersonas(
        [_ficha(10, dni=None), _ficha(11, dni=None)],
        [_recurso(901, conide=10), _recurso(902, conide=11)])
    assert indice.elegir_recurso(None, 10, None, 1, HOY).ide == 901


def test_f023_r25_con_dni_sin_fichas_cargadas_vale_la_ficha_casada() -> None:
    """Sin maestro de empleados (conciliador sin proveedor), el enlace
    `conide` a la ficha casada sigue valiendo, y el `cif` tambien."""
    indice = IndicePersonas([], [_recurso(901, conide=10)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY).ide == 901
    por_cif = IndicePersonas([], [_recurso(903, cif="12345678-z")])
    assert por_cif.elegir_recurso(DNI, None, None, 1, HOY).ide == 903


def test_f023_r25_sin_empresa_compiten_todas() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(902, conide=10,
                                                    empresa=31)])
    assert indice.elegir_recurso(DNI, 10, None, None, HOY).ide == 902


def test_f023_r25_la_baja_se_mira_a_la_fecha_de_la_linea() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(901, conide=10,
                                                    fecbaj=20260801)])
    assert indice.elegir_recurso(DNI, 10, None, 1, 20260731).ide == 901
    assert indice.elegir_recurso(DNI, 10, None, 1, 20260801).ide is None


def test_f023_r28_r29_solo_de_baja() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(900, conide=10,
                                                    fecbaj=HOY - 1)])
    assert indice.elegir_recurso(DNI, 10, 900, 1, HOY) == \
        ResolucionRecurso(None, "solo_baja", 1, 0)


def test_f023_r28_r29_solo_de_otra_empresa() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _recurso(902, conide=10, empresa=31),
        _recurso(900, conide=10, fecbaj=HOY - 1)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY) == \
        ResolucionRecurso(None, "otra_empresa", 1, 1)


def test_f023_r28_un_recurso_de_baja_de_otra_empresa_cuenta_como_baja() -> None:
    indice = IndicePersonas([_ficha(10)], [
        _recurso(901, conide=10),
        _recurso(902, conide=10, empresa=31, fecbaj=HOY - 1)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY) == \
        ResolucionRecurso(901, "ok", 1, 0)


def test_f023_r25_persona_sin_recursos_es_desconocido() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(950, conide=20)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY) == \
        ResolucionRecurso(None, "desconocido")
    # F-040 (R10; opcion A del humano 2026-10-08): sin DNI, sin ficha y con
    # preferido manda `elegir_sin_dni`: 950 es persona, sin DNI, de alta y
    # de la empresa, asi que se conserva. Sin preferido sigue desconocido.
    assert indice.elegir_recurso(None, None, 950, 1, HOY) == \
        ResolucionRecurso(950, "ok")
    assert indice.elegir_recurso(None, None, None, 1, HOY) == \
        ResolucionRecurso(None, "desconocido")


def test_f023_r25_el_mismo_recurso_por_conide_y_por_cif_cuenta_una_vez() -> None:
    indice = IndicePersonas([_ficha(10)], [_recurso(901, conide=10,
                                                    cif=DNI)])
    assert indice.elegir_recurso(DNI, 10, None, 1, HOY) == \
        ResolucionRecurso(901, "ok", 0, 0)


# ================ R12 / R14 · eleccion por nombre de obra ================ #

def test_f023_r14_una_sola_obra_que_llega_al_umbral_casa() -> None:
    assert elegir_por_nombre([GEMELA_28], "nave sur", 0.55) == \
        (GEMELA_28, "nombre")


def test_f023_r14_empate_de_la_mejor_puntuacion_es_nombre_ambiguo() -> None:
    a = _obra(100, "0100", 1, "Mismo Nombre")
    b = _obra(200, "0200", 28, "Mismo Nombre")
    assert elegir_por_nombre([a, b, UNICA], "mismo nombre", 0.55) == \
        (None, "nombre_ambiguo")


def test_f023_r14_por_debajo_del_umbral_o_sin_nombre_no_casa() -> None:
    assert elegir_por_nombre([GEMELA_28], "nave sur", 1.01) == (None, "none")
    assert elegir_por_nombre([GEMELA_28], None, 0.55) == (None, "none")
    assert elegir_por_nombre([GEMELA_28], " ,. ", 0.55) == (None, "none")
    assert elegir_por_nombre([], "nave sur", 0.55) == (None, "none")


def test_f023_r14_gana_la_mejor_aunque_no_sea_la_primera() -> None:
    assert elegir_por_nombre([GEMELA_1, GEMELA_28], "nave sur", 0.55) == \
        (GEMELA_28, "nombre")
