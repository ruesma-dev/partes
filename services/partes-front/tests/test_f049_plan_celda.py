# tests/test_f049_plan_celda.py
"""F-049 · núcleo puro del editor de celda de la matriz de obra.

`application/services/edicion_celda.py` decide, sin base ni red, qué hace
un guardado de la celda: qué líneas cambian, qué parejas automáticas de
F-037 se materializan, qué líneas nuevas se crean y desde qué plantilla, y
cuándo la petición es inválida (422) o la celda cambió desde que se abrió
(409). Casos E1–E10 de `requirements.md`; datos sintéticos.
"""
from __future__ import annotations

import dataclasses
import math

import pytest

from application.services.edicion_celda import (
    EPSILON,
    EXTRA,
    MOTIVO_CELDA_CAMBIADA,
    ORDINARIA,
    Cambio,
    CeldaInvalida,
    LineaCelda,
    PlanCelda,
    planificar_celda,
    plantilla,
    validar_horas,
)

DOC = "doc-y"
K1 = (DOC, 0, 1, 20261014)
K2 = (DOC, 1, 1, 20261014)


def _l(id_: int, tipo: str, horas: float, *, congelada: bool = False,
       extra_auto: bool = False, con_orig: bool = False, clave=None,
       doc: str = DOC) -> LineaCelda:
    return LineaCelda(id=id_, tipo=tipo, horas=horas, congelada=congelada,
                      extra_auto=extra_auto, con_orig=con_orig,
                      clave=clave if clave is not None else (doc, id_, 1, 1),
                      document_id=doc)


def _plan(celda, cambios, nueva_ordinaria=None, nueva_extra=None, *,
          admite_nuevas: bool = True) -> PlanCelda:
    return planificar_celda(celda, cambios, nueva_ordinaria, nueva_extra,
                            admite_nuevas=admite_nuevas)


def _error(celda, cambios, nueva_ordinaria=None, nueva_extra=None, *,
           admite_nuevas: bool = True) -> CeldaInvalida:
    with pytest.raises(CeldaInvalida) as exc:
        _plan(celda, cambios, nueva_ordinaria, nueva_extra,
              admite_nuevas=admite_nuevas)
    return exc.value


# =========================== ejemplos E1-E10 =========================== #

def test_f049_e1_solo_ordinaria_crea_la_extra_sin_tocar_la_ordinaria():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=2.0)
    assert plan.cambios == ()
    assert plan.materializar == ()
    assert plan.plantilla_id == 1
    assert (plan.crear_ordinaria, plan.crear_extra) == (None, 2.0)
    assert plan.documentos == (DOC,)


def test_f049_e2_solo_extra_crea_la_ordinaria_y_cambia_la_extra():
    plan = _plan([_l(1, EXTRA, 10.0)], [Cambio(1, 10.0, 2.0)],
                 nueva_ordinaria=8.0)
    assert plan.cambios == ((1, 2.0),)
    assert plan.materializar == ()
    assert plan.plantilla_id == 1
    assert (plan.crear_ordinaria, plan.crear_extra) == (8.0, None)
    assert plan.documentos == (DOC,)


def test_f049_e3_solo_extra_sin_ordinaria_nueva():
    plan = _plan([_l(1, EXTRA, 10.0)], [Cambio(1, 10.0, 2.0)])
    assert plan.cambios == ((1, 2.0),)
    assert (plan.crear_ordinaria, plan.crear_extra) == (None, None)
    assert plan.documentos == (DOC,)


def test_f049_e4_cambiar_la_extra_de_jornada_materializa_la_pareja():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=K1)]
    plan = _plan(celda, [Cambio(1, 8.0, 8.0), Cambio(2, 2.0, 3.0)])
    assert plan.cambios == ((2, 3.0),)
    assert plan.materializar == ((1, 8.0), (2, 3.0))
    assert plan.documentos == (DOC,)


def test_f049_e5_cambiar_la_base_materializa_la_pareja_con_su_valor():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=K1)]
    plan = _plan(celda, [Cambio(1, 8.0, 7.0), Cambio(2, 2.0, 2.0)])
    assert plan.cambios == ((1, 7.0),)
    assert plan.materializar == ((1, 7.0), (2, 2.0))


def test_f049_e6_ordinaria_a_cero_es_un_cambio_a_cero():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 0.0)])
    assert plan.cambios == ((1, 0.0),)
    assert plan.crear_ordinaria is None and plan.crear_extra is None


def test_f049_e8_sabado_solo_extra_crea_la_ordinaria():
    plan = _plan([_l(1, EXTRA, 4.0)], [Cambio(1, 4.0, 4.0)],
                 nueva_ordinaria=4.0)
    assert plan.cambios == ()
    assert plan.crear_ordinaria == 4.0
    assert plan.plantilla_id == 1


def test_f049_e9_celda_de_f050_solo_cambia_la_linea_editada():
    celda = [_l(1, ORDINARIA, 8.0), _l(2, EXTRA, 2.0)]
    plan = _plan(celda, [Cambio(1, 8.0, 8.0), Cambio(2, 2.0, 3.0)])
    assert plan.cambios == ((2, 3.0),)
    assert plan.materializar == ()
    assert plan.plantilla_id == 1


def test_f049_e10_solo_extra_de_la_ia_crea_la_ordinaria_desde_ella():
    plan = _plan([_l(7, EXTRA, 2.0)], [Cambio(7, 2.0, 2.0)],
                 nueva_ordinaria=8.0)
    assert plan.plantilla_id == 7
    assert plan.crear_ordinaria == 8.0


def test_f049_r6_sin_cambios_ni_nuevas_el_plan_no_tiene_nada():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)])
    assert plan.cambios == () and plan.materializar == ()
    assert plan.crear_ordinaria is None and plan.crear_extra is None
    assert plan.hay_algo is False
    assert plan.documentos == ()


def test_f049_r6_hay_algo_con_cambio_o_con_nueva():
    assert _plan([_l(1, ORDINARIA, 8.0)],
                 [Cambio(1, 8.0, 7.0)]).hay_algo is True
    assert _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=1.0).hay_algo is True
    assert _plan([_l(1, EXTRA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_ordinaria=1.0).hay_algo is True


def test_f049_r7_horas_vacias_valen_lo_de_antes():
    plan = _plan([_l(1, ORDINARIA, 8.0), _l(2, EXTRA, 2.0)],
                 [Cambio(1, 8.0, None), Cambio(2, 2.0, 3.0)])
    assert plan.cambios == ((2, 3.0),)


def test_f049_r7_extra_nueva_a_cero_no_crea():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=0.0)
    assert plan.crear_extra is None
    assert plan.hay_algo is False


def test_f049_r12_antes_con_ruido_de_coma_flotante_vale():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0 + 1e-12, 7.0)])
    assert plan.cambios == ((1, 7.0),)


def test_f049_r12_cambio_igual_salvo_ruido_no_es_cambio():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0 + 1e-12)])
    assert plan.cambios == ()


# ===================== R18 · materializar solo lo tocado ================ #

def test_f049_r18_solo_se_materializa_la_pareja_tocada():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=K1),
             _l(3, ORDINARIA, 4.0, con_orig=True, clave=K2),
             _l(4, EXTRA, 1.0, extra_auto=True, clave=K2)]
    plan = _plan(celda, [Cambio(1, 8.0, 8.0), Cambio(2, 2.0, 2.5),
                         Cambio(3, 4.0, 4.0), Cambio(4, 1.0, 1.0)])
    assert plan.materializar == ((1, 8.0), (2, 2.5))


def test_f049_r18_la_congelada_de_la_pareja_no_se_materializa():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1, congelada=True),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=K1)]
    plan = _plan(celda, [Cambio(2, 2.0, 3.0)])
    assert plan.cambios == ((2, 3.0),)
    assert plan.materializar == ((2, 3.0),)


def test_f049_r18_cambiar_una_linea_que_no_es_de_pareja_no_materializa():
    """Una ordinaria sin `horas_orig` ni `extra_auto` no es miembro."""
    celda = [_l(1, ORDINARIA, 8.0, clave=K1),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=K2)]
    plan = _plan(celda, [Cambio(1, 8.0, 7.0), Cambio(2, 2.0, 2.0)])
    assert plan.materializar == ()


def test_f049_r18_la_base_sola_con_orig_es_miembro():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1)]
    plan = _plan(celda, [Cambio(1, 8.0, 9.0)])
    assert plan.materializar == ((1, 9.0),)


def test_f049_r18_otra_linea_de_la_misma_clave_tambien_se_materializa():
    """R18: «las no congeladas de la celda con esa clave», sin más."""
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=K1),
             _l(2, EXTRA, 2.0, clave=K1)]
    plan = _plan(celda, [Cambio(1, 8.0, 7.0), Cambio(2, 2.0, 2.0)])
    assert plan.materializar == ((1, 7.0), (2, 2.0))


def test_f049_r18_documentos_sin_repetir_en_orden():
    celda = [_l(1, ORDINARIA, 8.0, con_orig=True, clave=("d2", 0, 1, 1),
                doc="d2"),
             _l(2, EXTRA, 2.0, extra_auto=True, clave=("d2", 0, 1, 1),
                doc="d2"),
             _l(3, EXTRA, 1.0, doc="d1")]
    plan = _plan(celda, [Cambio(1, 8.0, 8.0), Cambio(2, 2.0, 2.5),
                         Cambio(3, 1.0, 1.5)])
    assert plan.cambios == ((2, 2.5), (3, 1.5))
    assert plan.documentos == ("d2", "d1")


def test_f049_r18_documento_de_la_materializada_y_de_la_plantilla():
    """Orden: cambios, materializadas y plantilla (si se crea)."""
    k = ("d3", 0, 1, 1)
    celda = [_l(2, ORDINARIA, 1.0, doc="d1"),
             _l(4, ORDINARIA, 8.0, con_orig=True, clave=k, doc="d3"),
             _l(6, ORDINARIA, 2.0, con_orig=True, clave=k, doc="d4")]
    plan = _plan(celda, [Cambio(2, 1.0, 1.0), Cambio(4, 8.0, 7.0),
                         Cambio(6, 2.0, 2.0)], nueva_extra=1.0)
    assert plan.cambios == ((4, 7.0),)
    assert plan.materializar == ((4, 7.0), (6, 2.0))
    assert plan.plantilla_id == 2
    assert plan.documentos == ("d3", "d4", "d1")


def test_f049_r18_sin_crear_la_plantilla_no_aporta_documento():
    plan = _plan([_l(2, ORDINARIA, 1.0, doc="d1"),
                  _l(4, EXTRA, 8.0, doc="d3")],
                 [Cambio(2, 1.0, 1.0), Cambio(4, 8.0, 7.0)])
    assert plan.plantilla_id == 2
    assert plan.documentos == ("d3",)


# ============================ R19 · plantilla =========================== #

def test_f049_r19_plantilla_primera_no_congelada_ordinaria_antes():
    celda = [_l(1, EXTRA, 2.0), _l(5, ORDINARIA, 8.0, congelada=True),
             _l(9, ORDINARIA, 3.0), _l(7, ORDINARIA, 1.0)]
    assert plantilla(celda).id == 7


def test_f049_r19_plantilla_extra_si_no_hay_ordinaria_libre():
    celda = [_l(4, EXTRA, 2.0), _l(3, EXTRA, 1.0),
             _l(1, ORDINARIA, 8.0, congelada=True)]
    assert plantilla(celda).id == 3


def test_f049_r19_sin_libres_no_hay_plantilla():
    assert plantilla([_l(1, ORDINARIA, 8.0, congelada=True)]) is None
    assert plantilla([]) is None


def test_f049_r19_el_plan_lleva_la_plantilla_aunque_no_cree():
    plan = _plan([_l(3, EXTRA, 1.0), _l(8, ORDINARIA, 8.0)],
                 [Cambio(3, 1.0, 2.0), Cambio(8, 8.0, 8.0)])
    assert plan.plantilla_id == 8


# ============================== errores ================================= #

def test_f049_r11_sin_lineas_es_422():
    e = _error([_l(1, ORDINARIA, 8.0)], [])
    assert e.status == 422


def test_f049_r11_ids_repetidos_es_422():
    e = _error([_l(1, ORDINARIA, 8.0)],
               [Cambio(1, 8.0, 7.0), Cambio(1, 8.0, 6.0)])
    assert e.status == 422


@pytest.mark.parametrize("horas", [24.01, -0.01, 25.0, -1.0])
def test_f049_r13_ordinaria_fuera_de_rango_es_422(horas):
    e = _error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, horas)])
    assert e.status == 422


@pytest.mark.parametrize("horas", [0.0, 24.0, 7.5])
def test_f049_r13_ordinaria_en_los_bordes_vale(horas):
    assert _plan([_l(1, ORDINARIA, 8.0)],
                 [Cambio(1, 8.0, horas)]).cambios == ((1, horas),)


@pytest.mark.parametrize("horas", [24.01, -24.01, 30.0])
def test_f049_r13_extra_fuera_de_rango_es_422(horas):
    e = _error([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, horas)])
    assert e.status == 422


@pytest.mark.parametrize("horas", [-24.0, 24.0, -1.0, 0.0])
def test_f049_r13_extra_en_los_bordes_vale(horas):
    assert _plan([_l(1, EXTRA, 2.0)],
                 [Cambio(1, 2.0, horas)]).cambios == ((1, horas),)


@pytest.mark.parametrize("horas", [math.nan, math.inf, -math.inf])
def test_f049_r13_no_finito_es_422(horas):
    e = _error([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, horas)])
    assert e.status == 422


@pytest.mark.parametrize("nueva", [0.0, -1.0, 24.5, math.nan])
def test_f049_r13_ordinaria_nueva_no_positiva_o_fuera_es_422(nueva):
    e = _error([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, 2.0)],
               nueva_ordinaria=nueva)
    assert e.status == 422


def test_f049_r13_ordinaria_nueva_de_24_vale():
    assert _plan([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, 2.0)],
                 nueva_ordinaria=24.0).crear_ordinaria == 24.0


@pytest.mark.parametrize("nueva", [24.5, -24.5, math.inf])
def test_f049_r13_extra_nueva_fuera_es_422(nueva):
    e = _error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
               nueva_extra=nueva)
    assert e.status == 422


def test_f049_r13_extra_nueva_negativa_vale():
    assert _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=-1.0).crear_extra == -1.0


def test_f049_r13_rango_antes_que_celda_cambiada():
    """Orden del design §4: 422 de rango antes que el 409 de R12."""
    e = _error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 7.0, 30.0)])
    assert e.status == 422


def test_f049_r13_id_ajeno_con_valor_no_finito_es_422():
    e = _error([_l(1, ORDINARIA, 8.0)],
               [Cambio(1, 8.0, 8.0), Cambio(99, 1.0, math.nan)])
    assert e.status == 422


@pytest.mark.parametrize("valor", [True, "8", None, [8]])
def test_f049_r13_validar_horas_rechaza_lo_que_no_es_numero(valor):
    with pytest.raises(CeldaInvalida) as exc:
        validar_horas(ORDINARIA, valor, nueva=False)
    assert exc.value.status == 422


def test_f049_r13_validar_horas_devuelve_float():
    assert validar_horas(ORDINARIA, 8, nueva=False) == 8.0
    assert isinstance(validar_horas(EXTRA, 2, nueva=True), float)


def test_f049_r35_sin_trabajador_no_admite_nuevas():
    e = _error([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, 2.0)],
               nueva_ordinaria=8.0, admite_nuevas=False)
    assert e.status == 422
    e = _error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
               nueva_extra=1.0, admite_nuevas=False)
    assert e.status == 422


def test_f049_r35_sin_trabajador_si_edita_sus_lineas():
    plan = _plan([_l(1, EXTRA, 2.0)], [Cambio(1, 2.0, 3.0)],
                 admite_nuevas=False)
    assert plan.cambios == ((1, 3.0),)


def test_f049_r35_extra_nueva_a_cero_sin_trabajador_no_es_error():
    plan = _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=0.0, admite_nuevas=False)
    assert plan.hay_algo is False


def test_f049_r12_falta_una_libre_es_409():
    e = _error([_l(1, ORDINARIA, 8.0), _l(2, EXTRA, 1.0)],
               [Cambio(1, 8.0, 7.0)])
    assert e.status == 409
    assert str(e) == MOTIVO_CELDA_CAMBIADA


def test_f049_r12_sobra_un_id_ajeno_es_409():
    e = _error([_l(1, ORDINARIA, 8.0)],
               [Cambio(1, 8.0, 7.0), Cambio(2, 1.0, 1.0)])
    assert e.status == 409


def test_f049_r12_enviar_una_congelada_es_409():
    e = _error([_l(1, ORDINARIA, 8.0), _l(2, EXTRA, 1.0, congelada=True)],
               [Cambio(1, 8.0, 7.0), Cambio(2, 1.0, 1.0)])
    assert e.status == 409


def test_f049_r12_antes_obsoleto_es_409():
    e = _error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 7.0, 6.0)])
    assert e.status == 409
    assert str(e) == MOTIVO_CELDA_CAMBIADA


def test_f049_r12_celda_vacia_es_409():
    e = _error([], [Cambio(1, 8.0, 7.0)])
    assert e.status == 409


@pytest.mark.parametrize("congelada", [False, True])
def test_f049_r12_ordinaria_nueva_con_ordinaria_presente_es_409(congelada):
    celda = [_l(1, ORDINARIA, 8.0, congelada=congelada), _l(2, EXTRA, 1.0)]
    cambios = [Cambio(2, 1.0, 1.0)]
    if not congelada:
        cambios.append(Cambio(1, 8.0, 8.0))
    e = _error(celda, cambios, nueva_ordinaria=1.0)
    assert e.status == 409


def test_f049_r12_extra_nueva_con_extra_presente_es_409():
    e = _error([_l(1, ORDINARIA, 8.0), _l(2, EXTRA, 1.0)],
               [Cambio(1, 8.0, 8.0), Cambio(2, 1.0, 1.0)], nueva_extra=1.0)
    assert e.status == 409


def test_f049_r11_mensajes_legibles():
    assert str(_error([_l(1, ORDINARIA, 8.0)], []))
    assert str(_error([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 30.0)]))


def test_f049_celda_invalida_es_value_error_con_status():
    e = CeldaInvalida("motivo", 409)
    assert isinstance(e, ValueError)
    assert (str(e), e.status) == ("motivo", 409)


# ================ bordes exactos (los mata la mutación) ================= #

def test_f049_r12_tolerancia_de_antes_en_el_borde_exacto():
    """Una diferencia de exactamente `EPSILON` aún es «igual» (`>`)."""
    plan = _plan([_l(1, ORDINARIA, 0.0)], [Cambio(1, EPSILON, 0.0)])
    assert plan.cambios == ()


def test_f049_r12_cambio_en_el_borde_exacto_no_es_cambio():
    plan = _plan([_l(1, ORDINARIA, 0.0)], [Cambio(1, 0.0, EPSILON)])
    assert plan.cambios == ()
    assert _plan([_l(1, ORDINARIA, 0.0)],
                 [Cambio(1, 0.0, 2 * EPSILON)]).cambios == ((1, 2e-9),)


def test_f049_r7_extra_nueva_minima_si_crea():
    assert _plan([_l(1, ORDINARIA, 8.0)], [Cambio(1, 8.0, 8.0)],
                 nueva_extra=EPSILON).crear_extra == EPSILON


@pytest.mark.parametrize("valor", [
    LineaCelda(id=1, tipo=ORDINARIA, horas=1.0, congelada=False,
               extra_auto=False, con_orig=False, clave=(), document_id="d"),
    Cambio(1, 1.0, 2.0),
    PlanCelda(cambios=(), materializar=(), plantilla_id=1,
              crear_ordinaria=None, crear_extra=None, documentos=()),
])
def test_f049_los_datos_del_plan_son_inmutables(valor):
    with pytest.raises(dataclasses.FrozenInstanceError):
        valor.id = 2


def test_f049_r13_validar_horas_por_defecto_no_es_nueva():
    assert validar_horas(ORDINARIA, 0.0) == 0.0
    with pytest.raises(CeldaInvalida):
        validar_horas(ORDINARIA, 0.0, nueva=True)
