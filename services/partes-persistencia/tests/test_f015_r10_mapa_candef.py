# tests/test_f015_r10_mapa_candef.py
"""R10 · la jornada SEMANAL se deriva del candef por un mapa configurable.

El mapa (`JORNADA_SEMANAL_POR_CANDEF`, por defecto `8:40,9:42`) es lo
unico que sabe que un recurso de candef 9 hace 42 h a la semana y no 45.
Dos propiedades que sostienen el resto de la feature:

  - un candef VALIDO pero fuera del mapa cae a jornada PLANA (`5 x c`),
    que es exactamente el comportamiento anterior a F-015: nadie empeora
    por no estar en el mapa;
  - una cadena mal formada revienta al PARSEAR (en el cableado), nunca en
    caliente: un mapa invalido en produccion cambiaria el reparto de
    horas en silencio.

Sin red, sin BBDD: `parsear_mapa_semanal` y `jornada_semanal_de` son
funciones puras.
"""
from __future__ import annotations

import pytest
from application.services.jornada_resolver import (
    jornada_semanal_de,
    parsear_mapa_semanal,
)


# ---------------------------- el parseo --------------------------------- #

def test_f015_r10_mapa_por_defecto_se_parsea() -> None:
    assert parsear_mapa_semanal("8:40,9:42") == {8.0: 40.0, 9.0: 42.0}


def test_f015_r10_mapa_tolera_espacios_y_decimales() -> None:
    assert parsear_mapa_semanal(" 8 : 40 , 7.5:37.5 ") == {
        8.0: 40.0, 7.5: 37.5}


def test_f015_r10_mapa_de_un_solo_par() -> None:
    assert parsear_mapa_semanal("9:42") == {9.0: 42.0}


@pytest.mark.parametrize("texto", [
    "",             # cadena vacia
    "   ",
    "8:40,9",       # par sin ':'
    "x:40",         # clave no numerica
    "8:cuarenta",   # valor no numerico
    "8:40,8:41",    # clave repetida
    "8:40,,9:42",   # par vacio
    "0:40",         # candef fuera de rango
    "8:0",          # semanal fuera de rango
    "8:200",        # mas de 24*7
    "8:40:9",       # tres campos
])
def test_f015_r10_mapa_mal_formado_es_error(texto: str) -> None:
    """ValueError al PARSEAR: el cableado lo convierte en fallo de arranque."""
    with pytest.raises(ValueError):
        parsear_mapa_semanal(texto)


def test_f015_r10_el_error_dice_que_cadena_fallo() -> None:
    with pytest.raises(ValueError) as exc:
        parsear_mapa_semanal("8:40,8:41")
    assert "8" in str(exc.value)


# ------------------------- la jornada semanal --------------------------- #

MAPA = {8.0: 40.0, 9.0: 42.0}


@pytest.mark.parametrize("candef, semanal, origen", [
    (8.0, 40.0, "mapa"),
    (9.0, 42.0, "mapa"),
    (10.0, 50.0, "plana"),    # valido pero fuera del mapa -> 5 x c
    (7.0, 35.0, "plana"),
])
def test_f015_r10_jornada_semanal_del_mapa(candef, semanal, origen) -> None:
    assert jornada_semanal_de(candef, mapa=MAPA) == (semanal, origen)


def test_f015_r10_un_mapa_ampliado_saca_el_candef_de_la_jornada_plana() -> None:
    """Con `8:40,9:42,10:48`, el candef 10 deja de ser 'plana'."""
    mapa = parsear_mapa_semanal("8:40,9:42,10:48")
    assert jornada_semanal_de(10.0, mapa=mapa) == (48.0, "mapa")


def test_f015_r10_mapa_vacio_deja_todo_en_jornada_plana() -> None:
    assert jornada_semanal_de(9.0, mapa={}) == (45.0, "plana")


# ------------------- el aviso de candef fuera del mapa ------------------ #

def _splits_con(candef, fechas):
    """Splits de un recurso con ese candef en esos dias (mismo recurso)."""
    from application.services.recurso_conciliador import RecursoConciliador
    from tests.dobles import (
        CalendarioFake,
        LookupFake,
        RepositorioFake,
        indice_reshor,
        registro,
    )

    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )
    regs = [registro(i + 1, fecha_int=f, horas=4.0)
            for i, f in enumerate(fechas)]
    return conciliador, conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


def test_f015_r10_un_candef_fuera_del_mapa_avisa(caplog) -> None:
    """Nadie empeora, pero conviene saber que hay un regimen sin mapear."""
    import logging
    with caplog.at_level(logging.WARNING):
        _splits_con(10.0, [20260320])
    assert "fuera del mapa" in caplog.text
    assert "candef=10" in caplog.text
    assert "recurso=501" in caplog.text


def test_f015_r10_el_aviso_va_una_vez_por_recurso_y_pasada(caplog) -> None:
    """Dos dias del mismo recurso fuera del mapa: UN aviso, no dos."""
    import logging
    with caplog.at_level(logging.WARNING):
        _splits_con(10.0, [20260316, 20260317, 20260318])
    avisos = [m for m in caplog.messages if "fuera del mapa" in m]
    assert len(avisos) == 1


def test_f015_r10_un_candef_del_mapa_no_avisa(caplog) -> None:
    import logging
    for candef in (8.0, 9.0):
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            _splits_con(candef, [20260320])
        assert "fuera del mapa" not in caplog.text


def test_f015_r10_un_candef_no_informado_no_avisa(caplog) -> None:
    """Cae a la jornada por defecto (8), que SI esta en el mapa."""
    import logging
    with caplog.at_level(logging.WARNING):
        _splits_con(0.0, [20260320])
    assert "fuera del mapa" not in caplog.text


def test_f015_r10_conciliar_todos_reinicia_los_avisos(caplog) -> None:
    """Los acumuladores son de la pasada, como `_docs_degradados`."""
    import logging
    conciliador, _ = _splits_con(10.0, [20260320])
    assert conciliador._avisados_mapa == {501}
    conciliador.conciliar_todos()
    assert conciliador._avisados_mapa == set()


# ================= refuerzo tras la campana de mutacion ================= #
# Los bordes del rango de horas del mapa no estaban fijados: sobrevivian
# mutantes que movian el limite inferior (0 -> 1) y el superior (24*7).

@pytest.mark.parametrize("texto, esperado", [
    ("1:5", {1.0: 5.0}),          # valores pequenos: validos
    ("0.5:2.5", {0.5: 2.5}),
    ("24:168", {24.0: 168.0}),    # 24 h/dia x 7: el limite superior, CERRADO
])
def test_f015_r10_los_bordes_del_rango_se_aceptan(texto, esperado) -> None:
    assert parsear_mapa_semanal(texto) == esperado


@pytest.mark.parametrize("texto", [
    "8:169",     # una hora por encima de 24*7
    "169:40",    # el candef tambien tiene tope
    "8:-1",
    "-8:40",
])
def test_f015_r10_pasarse_del_rango_es_error(texto) -> None:
    with pytest.raises(ValueError):
        parsear_mapa_semanal(texto)


def test_f015_r10_el_error_de_rango_dice_que_valor_y_que_par() -> None:
    with pytest.raises(ValueError) as exc:
        parsear_mapa_semanal("8:200")
    mensaje = str(exc.value)
    assert "200" in mensaje and "8:200" in mensaje
