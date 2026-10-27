# tests/test_f056_franquicia.py
"""F-056 · Franquicia de extras en sv5: modelos de dominio (T1, T8) y regla
pura del ajuste (T2, T8: `application/services/franquicia.py`).

Enmienda 2026-10-27 (DA1 = C): X es un campo de `res` que solo lee sv5; la
peticion ya no la trae (R41), `leer_valor` decide su estado (R2) y el
veredicto no escribe con una franquicia desconocida (R42). Los nombres de
columna de estos tests son INVENTADOS: el campo real aun no existe.

Datos SINTETICOS: recursos, partes e ides inventados; ni nombres ni DNIs.
"""
from __future__ import annotations

from dataclasses import fields

import pytest

from domain.models.registro_models import (
    PREFIJO_FRANQUICIA,
    EstadoFranquicias,
    LecturaFranquicia,
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
    `ObraEntrada` y `extras_pendientes` 0 por defecto. R41: sin X."""
    p = PeticionFranquicia(
        ajuste_id=5, recurso_ide=501, periodo="2026-10",
        inicio=20260916, fin=20261015, fecha_int=20261015,
        obra=ObraEntrada(ide=10, codigo="9999"), partida_ide=33,
        partida_cod="01.01")
    assert [f.name for f in fields(p)] == [
        "ajuste_id", "recurso_ide", "periodo", "inicio", "fin",
        "fecha_int", "obra", "partida_ide", "partida_cod",
        "extras_pendientes", "usuario"]
    assert p.extras_pendientes == 0.0
    assert p.usuario is None
    assert p.ano == 2026 and p.mes == 10


def test_f056_modelos_peticion_ano_mes_del_dia_de_ajuste():
    """El parte es el del mes NATURAL del dia de ajuste (H1)."""
    p = PeticionFranquicia(
        ajuste_id=1, recurso_ide=1, periodo="2026-01",
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
        "error", "franquicia", "franquicia_estado"]
    assert r.extras == 0.0 and r.objetivo == 0.0
    assert r.actual is None and r.hmores_ide is None and r.hmoide is None
    assert r.parte_cod is None and r.parte_estado is None
    assert r.complementario is False and r.escrita is False
    assert r.forzada_pruebas is False
    assert r.hora_codigo is None and r.pre is None
    assert r.motivo is None and r.error is None
    assert r.franquicia is None and r.franquicia_estado is None


def test_f056_modelos_lectura_y_estado_de_franquicias():
    """design §4: la lectura de un recurso y el estado global."""
    lec = LecturaFranquicia("activa", 8.0)
    assert (lec.estado, lec.franquicia, lec.motivo) == ("activa", 8.0, None)
    assert [f.name for f in fields(lec)] == ["estado", "franquicia", "motivo"]
    e = EstadoFranquicias("ok", None, {501: lec})
    assert (e.estado, e.motivo, e.recursos) == ("ok", None, {501: lec})
    assert EstadoFranquicias("apagada").recursos == {}
    assert EstadoFranquicias("apagada").motivo is None


# ------------------------- T2: regla pura del ajuste ------------------------ #

from application.services import franquicia as fr
from application.services.parte_abierto import MOTIVO_PARTE_NO_ABIERTO
from application.services.pisado import MOTIVO_LINEA_ENLAZADA
from domain.models.registro_models import AccionLinea, LineaSigrid

EST = 1
ACT = LecturaFranquicia("activa", 8.0)


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
    v = fr.veredicto(None, None, 0.0, est_registro=EST, franquicia=ACT, accion=_accion())
    assert (v.accion, v.motivo) == (fr.SIN_AJUSTE, None)
    v = fr.veredicto(None, None, -0.0004, est_registro=EST, franquicia=ACT, accion=_accion())
    assert v.accion == fr.SIN_AJUSTE


def test_f056_r24_sin_linea_y_objetivo_es_crear():
    v = fr.veredicto(None, None, -6.0, est_registro=EST, franquicia=ACT, accion=_accion())
    assert (v.accion, v.motivo) == (fr.CREAR, None)
    v = fr.veredicto(None, None, -0.002, est_registro=EST, franquicia=ACT, accion=_accion())
    assert v.accion == fr.CREAR


@pytest.mark.parametrize("can", [-6.0, -6.0009, -5.9991])
def test_f056_r28_linea_que_ya_vale_a_es_ya_aplicado(can):
    v = fr.veredicto(_ls(can), EST, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion())
    assert (v.accion, v.motivo) == (fr.YA_APLICADO, None)


def test_f056_r28_ya_aplicado_antes_que_parte_cerrado_o_enlazada():
    """Lo ya escrito se reconoce aunque luego cerraran o enlazaran."""
    v = fr.veredicto(_ls(-6.0, enlazada=True), 3, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion())
    assert v.accion == fr.YA_APLICADO


@pytest.mark.parametrize("can", [-6.0, 0.0, None, -8.002])
def test_f056_r25_linea_distinta_es_actualizar(can):
    v = fr.veredicto(_ls(can), EST, -8.0, est_registro=EST, franquicia=ACT, accion=_accion())
    assert (v.accion, v.motivo) == (fr.ACTUALIZAR, None)


def test_f056_r25_a_cero_con_linea_es_actualizar_no_sin_ajuste():
    """R19, regla F-053: la linea existente queda a 0, no se borra."""
    v = fr.veredicto(_ls(-6.0), EST, 0.0, est_registro=EST, franquicia=ACT, accion=_accion())
    assert v.accion == fr.ACTUALIZAR


def test_f056_r27_parte_no_en_registro_no_es_editable():
    v = fr.veredicto(_ls(-6.0), 3, -8.0, est_registro=EST, franquicia=ACT, accion=_accion(),
                     parte_cod="PT26/00042")
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(f"{MOTIVO_PARTE_NO_ABIERTO}: ")
    assert "PT26/00042" in v.motivo and "estado 3" in v.motivo


def test_f056_r27_linea_enlazada_no_es_editable():
    v = fr.veredicto(_ls(-6.0, enlazada=True), EST, -8.0, est_registro=EST, franquicia=ACT,
                     accion=_accion(), parte_cod="PT26/00042")
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(f"{MOTIVO_LINEA_ENLAZADA}: ")
    assert "7001" in v.motivo


def test_f056_r27_parte_cerrado_prevalece_sobre_enlazada():
    v = fr.veredicto(_ls(-6.0, enlazada=True), 10, -8.0, est_registro=EST, franquicia=ACT,
                     accion=_accion())
    assert v.motivo.startswith(MOTIVO_PARTE_NO_ABIERTO)


def test_f056_r30_sin_decision_del_registro_no_es_editable():
    v = fr.veredicto(None, None, -6.0, est_registro=EST, franquicia=ACT, accion=None)
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(fr.MOTIVO_NO_REGISTRABLE)


def test_f056_r30_recurso_omitido_lleva_su_motivo():
    """F-023: el motivo de la verificacion del recurso viaja tal cual."""
    v = fr.veredicto(_ls(-6.0), EST, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion("omitir", motivo="recurso de baja"))
    assert v.accion == fr.NO_EDITABLE
    assert "recurso de baja" in v.motivo
    assert v.motivo.startswith(fr.MOTIVO_NO_REGISTRABLE)


@pytest.mark.parametrize("codigo", ["HL01", "CIZ", "M01", None, ""])
def test_f056_r30_codigo_que_no_es_he_no_es_editable(codigo):
    v = fr.veredicto(None, None, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion(codigo=codigo))
    assert v.accion == fr.NO_EDITABLE
    assert v.motivo.startswith(fr.MOTIVO_SIN_HE)


@pytest.mark.parametrize("codigo", ["HE01", "he02", "HE"])
def test_f056_r30_codigo_he_si_es_editable(codigo):
    v = fr.veredicto(None, None, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion(codigo=codigo))
    assert v.accion == fr.CREAR


def test_f056_r30_dedicacion_no_es_editable():
    """F-019: un mensual con el interruptor va a dedicacion, no a Sigrid."""
    v = fr.veredicto(None, None, -6.0, est_registro=EST, franquicia=ACT,
                     accion=_accion("dedicacion"))
    assert v.accion == fr.NO_EDITABLE


def test_f056_motivos_cortos_y_sin_tildes():
    largos = fr.veredicto(None, None, -1.0, est_registro=EST, franquicia=ACT,
                          accion=_accion("omitir", motivo="x" * 400))
    assert len(largos.motivo) <= fr.LIMITE_MOTIVO
    for m in (fr.MOTIVO_NO_REGISTRABLE, fr.MOTIVO_SIN_HE):
        assert m.isascii()


@pytest.mark.parametrize("periodo", ["2026-10", "2027-01"])
def test_f056_r24_texto_ajuste_sin_cifras(periodo):
    """DA26: el `tex` no lleva cifras (nunca queda desfasado al recalcular)
    ni nombres ni DNIs."""
    assert fr.texto_ajuste(periodo) == f"Ajuste franquicia extras {periodo}"


def test_f056_acciones_literales():
    assert (fr.CREAR, fr.ACTUALIZAR, fr.YA_APLICADO, fr.SIN_AJUSTE,
            fr.NO_EDITABLE) == ("crear", "actualizar", "ya_aplicado",
                                "sin_ajuste", "no_editable")
    assert fr.TOL == 0.001


# --------------------- T8: franquicia en el campo de res --------------------- #

def test_f056_r38_campo_re():
    for bueno in ("FranqHE", "_x", "a" * 128, "campo_prueba_1"):
        assert fr.CAMPO_RE.match(bueno), bueno
    for malo in ("", "1campo", "a];DROP TABLE res;--", "campo x", " campo",
                 "campo ", "a" * 129, "res.campo", "[campo]", "c\u00e1mpo",
                 "campo\n"):
        assert not fr.CAMPO_RE.match(malo), malo


def test_f056_r38_tipos_numericos_son_los_de_la_spec():
    """design §4: exactamente estos nueve (sin `bigint`: decision del
    lider del 2026-10-27; un tipo fuera de la lista es `no_disponible`)."""
    assert fr.TIPOS_NUMERICOS == frozenset({
        "decimal", "numeric", "float", "real", "int", "smallint", "tinyint",
        "money", "smallmoney"})


@pytest.mark.parametrize("tipo, esperado", [
    ("decimal", True), ("NUMERIC", True), ("Float", True), ("real", True),
    ("int", True), ("smallint", True), ("tinyint", True), ("money", True),
    ("SmallMoney", True), (" int ", True),
    ("bigint", False), ("varchar", False), ("nvarchar", False),
    ("bit", False), ("datetime", False), ("", False), (None, False)])
def test_f056_r38_es_tipo_numerico(tipo, esperado):
    assert fr.es_tipo_numerico(tipo) is esperado


def test_f056_r2_estados_y_tope_literales():
    assert (fr.APAGADA, fr.NO_DISPONIBLE, fr.OK) == (
        "apagada", "no_disponible", "ok")
    assert (fr.ACTIVA, fr.INACTIVA, fr.INVALIDA) == (
        "activa", "inactiva", "invalida")
    assert fr.MAX_FRANQUICIA_H == 200.0


@pytest.mark.parametrize("valor, estado, x", [
    (None, "inactiva", 0.0),
    (0, "inactiva", 0.0),
    (0.0, "inactiva", 0.0),
    ("0", "inactiva", 0.0),
    (8, "activa", 8.0),
    (7.5, "activa", 7.5),
    (7.126, "activa", 7.13),
    ("12.5", "activa", 12.5),
    (200, "activa", 200.0),
    (0.001, "activa", 0.0),
])
def test_f056_r2_leer_valor_validos(valor, estado, x):
    lec = fr.leer_valor(valor)
    assert (lec.estado, lec.franquicia, lec.motivo) == (estado, x, None)
    assert str(lec.franquicia) != "-0.0"


def test_f056_r2_leer_valor_decimal_de_sql_server():
    from decimal import Decimal
    assert fr.leer_valor(Decimal("8.50")).franquicia == 8.5


@pytest.mark.parametrize("valor", [
    -1, -0.01, 200.01, 1000, "x", "8h", float("nan"), float("inf"),
    True, [8], {}])
def test_f056_r2_leer_valor_invalidos(valor):
    """DA24: negativo, > 200 h o no convertible: `invalida`, sin X."""
    lec = fr.leer_valor(valor)
    assert (lec.estado, lec.franquicia) == ("invalida", None)
    assert lec.motivo and lec.motivo.isascii()
    assert len(lec.motivo) <= fr.LIMITE_MOTIVO


@pytest.mark.parametrize("lectura, prefijo", [
    (LecturaFranquicia("invalida", None, "valor -1"), "franquicia_invalida"),
    (LecturaFranquicia("no_disponible", None, "columna ausente"),
     "franquicia_no_disponible"),
    (LecturaFranquicia("apagada", None), "franquicia_apagada"),
    (None, "franquicia_no_disponible"),
])
def test_f056_r42_franquicia_desconocida_no_es_editable(lectura, prefijo):
    """R42: «no se sabe» nunca es X = 0, y va ANTES que todo lo demas
    (incluso con la linea ya aplicada o sin decision del registro)."""
    for linea, accion in ((None, _accion()), (_ls(-6.0), _accion()),
                          (_ls(-6.0), None)):
        v = fr.veredicto(linea, EST, -6.0, est_registro=EST,
                         franquicia=lectura, accion=accion)
        assert v.accion == fr.NO_EDITABLE
        assert v.motivo.startswith(f"{prefijo}: ")
    if lectura is not None and lectura.motivo:
        assert lectura.motivo in fr.veredicto(
            None, None, -6.0, est_registro=EST, franquicia=lectura,
            accion=_accion()).motivo


def test_f056_r42_inactiva_con_linea_es_actualizar_a_cero():
    ina = LecturaFranquicia("inactiva", 0.0)
    v = fr.veredicto(_ls(-6.0), EST, 0.0, est_registro=EST, franquicia=ina,
                     accion=_accion())
    assert v.accion == fr.ACTUALIZAR
    v = fr.veredicto(None, None, 0.0, est_registro=EST, franquicia=ina,
                     accion=_accion())
    assert v.accion == fr.SIN_AJUSTE
