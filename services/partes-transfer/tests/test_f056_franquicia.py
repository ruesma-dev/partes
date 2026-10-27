# tests/test_f056_franquicia.py
"""F-056 · Franquicia de extras en sv5: modelos de dominio (T1) y regla
pura del ajuste (T2, `application/services/franquicia.py`).

Datos SINTETICOS: recursos, partes e ides inventados; ni nombres ni DNIs.
"""
from __future__ import annotations

from dataclasses import fields

import pytest

from domain.models.registro_models import (
    PREFIJO_FRANQUICIA,
    ObraEntrada,
    PeticionFranquicia,
    ResultadoFranquicia,
    VeredictoFranquicia,
    es_synckey_franquicia,
)


# ------------------------------- T1: modelos ------------------------------- #

def test_f056_modelos_prefijo_literal():
    """R31, DA14: la synckey del ajuste es `partes:franquicia:<id>`."""
    assert PREFIJO_FRANQUICIA == "partes:franquicia:"


@pytest.mark.parametrize("sk, esperado", [
    ("partes:franquicia:1", True),
    ("partes:franquicia:990560001", True),
    ("  partes:franquicia:7  ", True),
    ("partes:7", False),
    ("partes:7:ciz", False),
    ("porcentajes:franquicia:7", False),
    ("PARTES:FRANQUICIA:7", False),
    ("partes:franquicia", False),
    ("", False),
    (None, False),
])
def test_f056_modelos_es_synckey_franquicia(sk, esperado):
    assert es_synckey_franquicia(sk) is esperado


def test_f056_modelos_peticion_campos_y_defectos():
    """design §6: los campos de `FranquiciaIn`, con la obra como
    `ObraEntrada` y `extras_pendientes` 0 por defecto."""
    p = PeticionFranquicia(
        ajuste_id=5, recurso_ide=501, franquicia=8.0, periodo="2026-10",
        inicio=20260916, fin=20261015, fecha_int=20261015,
        obra=ObraEntrada(ide=10, codigo="9999"), partida_ide=33,
        partida_cod="01.01")
    assert [f.name for f in fields(p)] == [
        "ajuste_id", "recurso_ide", "franquicia", "periodo", "inicio", "fin",
        "fecha_int", "obra", "partida_ide", "partida_cod",
        "extras_pendientes", "usuario"]
    assert p.extras_pendientes == 0.0
    assert p.usuario is None
    assert p.ano == 2026 and p.mes == 10


def test_f056_modelos_peticion_ano_mes_del_dia_de_ajuste():
    """El parte es el del mes NATURAL del dia de ajuste (H1)."""
    p = PeticionFranquicia(
        ajuste_id=1, recurso_ide=1, franquicia=1.0, periodo="2026-01",
        inicio=20251216, fin=20260115, fecha_int=20251231,
        obra=ObraEntrada(ide=1), partida_ide=None, partida_cod=None)
    assert (p.ano, p.mes) == (2025, 12)


def test_f056_modelos_veredicto():
    v = VeredictoFranquicia("no_editable", "motivo")
    assert (v.accion, v.motivo) == ("no_editable", "motivo")
    assert VeredictoFranquicia("crear").motivo is None


def test_f056_modelos_resultado_campos_y_defectos():
    """design §6: la respuesta, en este orden y con defectos neutros."""
    r = ResultadoFranquicia(ok=True, accion="crear")
    assert [f.name for f in fields(r)] == [
        "ok", "accion", "extras", "objetivo", "actual", "hmores_ide",
        "hmoide", "parte_cod", "parte_estado", "complementario",
        "hora_codigo", "pre", "motivo", "escrita", "forzada_pruebas",
        "error"]
    assert r.extras == 0.0 and r.objetivo == 0.0
    assert r.actual is None and r.hmores_ide is None and r.hmoide is None
    assert r.parte_cod is None and r.parte_estado is None
    assert r.complementario is False and r.escrita is False
    assert r.forzada_pruebas is False
    assert r.hora_codigo is None and r.pre is None
    assert r.motivo is None and r.error is None


# ------------------------- T2: regla pura del ajuste ------------------------ #

from application.services import franquicia as fr  # noqa: E402
from application.services.parte_abierto import MOTIVO_PARTE_NO_ABIERTO  # noqa: E402
from application.services.pisado import MOTIVO_LINEA_ENLAZADA  # noqa: E402
from domain.models.registro_models import AccionLinea, LineaSigrid  # noqa: E402

EST = 1


def _accion(accion="escribir", codigo="HE01", motivo=None) -> AccionLinea:
    return AccionLinea(registro_id=0, accion=accion, ano=2026, mes=10,
                       fecha_int=20261015, recurso_ide=501, hora_ide=9,
                       hora_codigo=codigo, motivo=motivo)


def _ls(can, *, enlazada=False, ide=7001) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=501, fecha_int=20261015, horide=9,
                       hora_codigo="HE01", can=can, tot=None,
                       synckey="partes:franquicia:5", hmoide=900,
                       enlazada=enlazada)


@pytest.mark.parametrize("extras, x, esperado", [
    (6.0, 8.0, -6.0),        # menos que la franquicia: queda a 0
    (10.0, 8.0, -8.0),       # mas: se resta X
    (8.0, 8.0, -8.0),        # justo X
    (0.0, 8.0, 0.0),         # sin extras: sin ajuste
    (-3.0, 8.0, 0.0),        # neto negativo (ajustes manuales): sin ajuste
    (5.0, 0.0, 0.0),         # franquicia 0 (sin vigente, R19): a 0
    (2.345, 8.0, -2.35),     # dos decimales (ROUND_HALF_EVEN de round)
    (7.126, 7.125, -7.12),   # min y luego redondeo
    (0.004, 8.0, 0.0),       # redondea a 0, sin «-0.0»
])
def test_f056_r24_ajuste_objetivo(extras, x, esperado):
    a = fr.ajuste_objetivo(extras, x)
    assert a == esperado
    assert str(a) != "-0.0"


@pytest.mark.parametrize("extras", [-5.0, 0.0, 0.5, 3.0, 7.99, 8.0, 12.5, 40])
@pytest.mark.parametrize("x", [0.0, 0.5, 8.0, 20.0])
def test_f056_r24_ajuste_objetivo_propiedades(extras, x):
    """design §9: A en [-X, 0]; E <= 0 => 0; E >= X => -X; E < X => -E."""
    a = fr.ajuste_objetivo(extras, x)
    assert -x - 1e-9 <= a <= 0.0
    if extras <= 0:
        assert a == 0.0
    elif extras >= x:
        assert a == round(-x, 2) + 0.0
    else:
        assert a == round(-extras, 2)


def test_f056_r28_sin_linea_y_objetivo_cero_es_sin_ajuste():
    v = fr.veredicto(None, None, 0.0, est_registro=EST, accion=_accion())
    assert (v.accion, v.motivo) == (fr.SIN_AJUSTE, None)
    v = fr.veredicto(None, None, -0.0004, est_registro=EST, accion=_accion())
    assert v.accion == fr.SIN_AJUSTE


def test_f056_r24_sin_linea_y_objetivo_es_crear():
    v = fr.veredicto(None, None, -6.0, est_registro=EST, accion=_accion())
    assert (v.accion, v.motivo) == (fr.CREAR, None)
    v = fr.veredicto(None, None, -0.002, est_registro=EST, accion=_accion())
    assert v.accion == fr.CREAR


@pytest.mark.parametrize("can", [-6.0, -6.0009, -5.9991])
def test_f056_r28_linea_que_ya_vale_a_es_ya_aplicado(can):
    v = fr.veredicto(_ls(can), EST, -6.0, est_registro=EST,
                     accion=_accion())
    assert (v.accion, v.motivo) == (fr.YA_APLICADO, None)


def test_f056_r28_ya_aplicado_antes_que_parte_cerrado_o_enlazada():
    """Lo ya escrito se reconoce aunque luego cerraran o enlazaran."""
    v = fr.veredicto(_ls(-6.0, enlazada=True), 3, -6.0, est_registro=EST,
                     accion=_accion())
    assert v.accion == fr.YA_APLICADO


@pytest.mark.parametrize("can", [-6.0, 0.0, None, -8.002])
def test_f056_r25_linea_distinta_es_actualizar(can):
    v = fr.veredicto(_ls(can), EST, -8.0, est_registro=EST, accion=_accion())
    assert (v.accion, v.motivo) == (fr.ACTUALIZAR, None)


def test_f056_r25_a_cero_con_linea_es_actualizar_no_sin_ajuste():
    """R19, regla F-053: la linea existente queda a 0, no se borra."""
    v = fr.veredicto(_ls(-6.0), EST, 0.0, est_registro=EST, accion=_accion())
    assert v.accion == fr.ACTUALIZAR


def test_f056_r27_parte_no_en_registro_no_es_editable():
    v = fr.veredicto(_ls(-6.0), 3, -8.0, est_registro=EST, accion=_accion(),
                     parte_cod="PT26/00042")
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(f"{MOTIVO_PARTE_NO_ABIERTO}: ")
    assert "PT26/00042" in v.motivo and "estado 3" in v.motivo


def test_f056_r27_linea_enlazada_no_es_editable():
    v = fr.veredicto(_ls(-6.0, enlazada=True), EST, -8.0, est_registro=EST,
                     accion=_accion(), parte_cod="PT26/00042")
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(f"{MOTIVO_LINEA_ENLAZADA}: ")
    assert "7001" in v.motivo


def test_f056_r27_parte_cerrado_prevalece_sobre_enlazada():
    v = fr.veredicto(_ls(-6.0, enlazada=True), 10, -8.0, est_registro=EST,
                     accion=_accion())
    assert v.motivo.startswith(MOTIVO_PARTE_NO_ABIERTO)


def test_f056_r30_sin_decision_del_registro_no_es_editable():
    v = fr.veredicto(None, None, -6.0, est_registro=EST, accion=None)
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(fr.MOTIVO_NO_REGISTRABLE)


def test_f056_r30_recurso_omitido_lleva_su_motivo():
    """F-023: el motivo de la verificacion del recurso viaja tal cual."""
    v = fr.veredicto(_ls(-6.0), EST, -6.0, est_registro=EST,
                     accion=_accion("omitir", motivo="recurso de baja"))
    assert v.accion == fr.NO_EDITABLE
    assert "recurso de baja" in v.motivo
    assert v.motivo.startswith(fr.MOTIVO_NO_REGISTRABLE)


@pytest.mark.parametrize("codigo", ["HL01", "CIZ", "M01", None, ""])
def test_f056_r30_codigo_que_no_es_he_no_es_editable(codigo):
    v = fr.veredicto(None, None, -6.0, est_registro=EST,
                     accion=_accion(codigo=codigo))
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(fr.MOTIVO_SIN_HE)


@pytest.mark.parametrize("codigo", ["HE01", "he02", "HE"])
def test_f056_r30_codigo_he_si_es_editable(codigo):
    v = fr.veredicto(None, None, -6.0, est_registro=EST,
                     accion=_accion(codigo=codigo))
    assert v.accion == fr.CREAR


def test_f056_r30_dedicacion_no_es_editable():
    """F-019: un mensual con el interruptor va a dedicacion, no a Sigrid."""
    v = fr.veredicto(None, None, -6.0, est_registro=EST,
                     accion=_accion("dedicacion"))
    assert v.accion == fr.NO_EDITABLE


def test_f056_motivos_cortos_y_sin_tildes():
    largos = fr.veredicto(None, None, -1.0, est_registro=EST,
                          accion=_accion("omitir", motivo="x" * 400))
    assert len(largos.motivo) <= fr.LIMITE_MOTIVO
    for m in (fr.MOTIVO_NO_REGISTRABLE, fr.MOTIVO_SIN_HE):
        assert m.isascii()


@pytest.mark.parametrize("periodo, a, x, esperado", [
    ("2026-10", -6.0, 8.0,
     "Ajuste franquicia extras 2026-10: -6 h (franquicia 8 h)"),
    ("2026-11", -7.5, 7.5,
     "Ajuste franquicia extras 2026-11: -7,5 h (franquicia 7,5 h)"),
    ("2026-12", -2.25, 10.0,
     "Ajuste franquicia extras 2026-12: -2,25 h (franquicia 10 h)"),
    ("2027-01", 0.0, 0.0,
     "Ajuste franquicia extras 2027-01: 0 h (franquicia 0 h)"),
    ("2027-01", -0.0, 3.0,
     "Ajuste franquicia extras 2027-01: 0 h (franquicia 3 h)"),
])
def test_f056_r24_texto_ajuste(periodo, a, x, esperado):
    """design §6, DA13: sin nombres ni DNIs."""
    assert fr.texto_ajuste(periodo, a, x) == esperado


def test_f056_acciones_literales():
    assert (fr.CREAR, fr.ACTUALIZAR, fr.YA_APLICADO, fr.SIN_AJUSTE,
            fr.NO_EDITABLE) == ("crear", "actualizar", "ya_aplicado",
                                "sin_ajuste", "no_editable")
    assert fr.TOL == 0.001
