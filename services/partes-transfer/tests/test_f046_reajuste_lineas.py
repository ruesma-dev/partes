# tests/test_f046_reajuste_lineas.py
"""F-046 · veredictos puros del reajuste en Sigrid (R21, R22, R26).

`veredicto_existente` decide si una linea ya registrada se puede editar
(`UPDATE hmores`) y `veredicto_nueva` si una extra nueva se puede insertar.
Datos sinteticos: ni nombres ni DNIs; ides, recursos y codigos inventados.
"""
from __future__ import annotations

import pytest

from application.services.reajuste_lineas import (
    MOTIVO_BASE_NO_EDITABLE,
    MOTIVO_CAN_DISTINTA,
    MOTIVO_CHOQUE,
    MOTIVO_ENLAZADA,
    MOTIVO_NO_EXISTE,
    MOTIVO_NO_REGISTRABLE,
    MOTIVO_NUEVA_DISTINTA,
    MOTIVO_OTRA_OBRA,
    MOTIVO_PARCIAL,
    MOTIVO_PARTE_NO_EN_REGISTRO,
    TOL,
    veredicto_existente,
    veredicto_nueva,
)
from domain.models.registro_models import (
    AccionLinea,
    LineaSigrid,
    OpReajuste,
    VeredictoReajuste,
)

EN_REGISTRO = 1
CERRADO = 3


def _op(rid: int = 11, antes: float | None = 8.0,
        despues: float = 2.5, base: int | None = None) -> OpReajuste:
    return OpReajuste(registro_id=rid, antes=antes, despues=despues,
                      base_registro_id=base)


def _ls(can: float | None = 8.0, *, enlazada: bool = False,
        ide: int = 4001, rid: int = 11) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=501, fecha_int=20261014, horide=7,
                       hora_codigo="HL01", can=can, tot=None,
                       synckey=f"partes:{rid}", nuestra=True, pre=20.0,
                       hmoide=7001, enlazada=enlazada)


def _ex(op, linea, est=EN_REGISTRO) -> VeredictoReajuste:
    return veredicto_existente(op, linea, est, est_registro=EN_REGISTRO)


# ------------------------------ R21 --------------------------------- #

def test_f046_r21_existente_con_antes_es_editable():
    v = _ex(_op(), _ls(8.0))
    assert (v.registro_id, v.editable, v.ya_aplicada, v.motivo) == (
        11, True, False, None)


def test_f046_r21_tolerancia_de_una_milesima_en_antes():
    assert _ex(_op(antes=8.0), _ls(8.0 + TOL)).editable
    assert _ex(_op(antes=8.0), _ls(8.0 - TOL)).editable
    v = _ex(_op(antes=8.0), _ls(8.0 + 2 * TOL))
    assert not v.editable and v.motivo.startswith(MOTIVO_CAN_DISTINTA)


def test_f046_r21_tol_es_una_milesima():
    assert TOL == pytest.approx(0.001)


def test_f046_r21_sin_synckey_en_sigrid_no_es_editable():
    v = _ex(_op(), None)
    assert not v.editable and not v.ya_aplicada
    assert v.motivo.startswith(MOTIVO_NO_EXISTE)
    assert "partes:11" in v.motivo


def test_f046_r21_parte_cerrado_no_es_editable():
    v = _ex(_op(), _ls(8.0), est=CERRADO)
    assert not v.editable
    assert v.motivo.startswith(MOTIVO_PARTE_NO_EN_REGISTRO)


def test_f046_r21_parte_sin_estado_no_es_editable():
    v = _ex(_op(), _ls(8.0), est=None)
    assert not v.editable
    assert v.motivo.startswith(MOTIVO_PARTE_NO_EN_REGISTRO)


def test_f046_r21_linea_enlazada_no_es_editable():
    v = _ex(_op(), _ls(8.0, enlazada=True))
    assert not v.editable
    assert v.motivo.startswith(MOTIVO_ENLAZADA)


def test_f046_r21_can_distinta_dice_lo_que_hay_y_lo_esperado():
    v = _ex(_op(antes=8.0, despues=2.5), _ls(6.0))
    assert not v.editable and not v.ya_aplicada
    assert v.motivo.startswith(MOTIVO_CAN_DISTINTA)
    assert "6" in v.motivo and "8" in v.motivo


def test_f046_r21_can_nula_cuenta_como_cero():
    assert _ex(_op(antes=0.0, despues=1.5), _ls(None)).editable
    assert not _ex(_op(antes=8.0, despues=1.5), _ls(None)).editable


def test_f046_r21_extra_negativa_editable():
    v = _ex(_op(rid=12, antes=-4.0, despues=1.5), _ls(-4.0, rid=12))
    assert v.editable and not v.ya_aplicada


# ------------------------------ R26 --------------------------------- #

def test_f046_r26_existente_ya_con_despues_es_ya_aplicada():
    v = _ex(_op(antes=8.0, despues=2.5), _ls(2.5))
    assert (v.editable, v.ya_aplicada, v.motivo) == (True, True, None)


def test_f046_r26_ya_aplicada_aunque_el_parte_se_cerrase_despues():
    """Lo escrito por un `ejecutar` cuyo cliente no recibio respuesta
    (timeout) se reconoce aunque luego cerraran el parte: no hay nada que
    escribir y sv4 tiene que poder materializarlo."""
    v = _ex(_op(antes=8.0, despues=2.5), _ls(2.5), est=CERRADO)
    assert v.ya_aplicada and v.editable


def test_f046_r26_ya_aplicada_a_cero():
    v = _ex(_op(antes=-2.0, despues=0.0), _ls(0.0))
    assert v.ya_aplicada


# ------------------------------ R22 --------------------------------- #

def _base_ok() -> VeredictoReajuste:
    return VeredictoReajuste(registro_id=11, editable=True)


def _accion(accion: str = "escribir", motivo: str | None = None):
    return AccionLinea(registro_id=990000001, accion=accion, ano=2026,
                       mes=10, fecha_int=20261014, motivo=motivo,
                       recurso_ide=501, hora_ide=9, hora_codigo="HE01",
                       can=2.5, pre=25.0, tot=62.5)


def _nueva(**kw) -> VeredictoReajuste:
    args = dict(existente=None, base=_base_ok(), accion=_accion(),
                choques=[], misma_obra=True)
    args.update(kw)
    return veredicto_nueva(_op(rid=990000001, antes=None, despues=2.5,
                               base=11), **args)


def test_f046_r22_nueva_con_todo_en_regla_es_editable():
    v = _nueva()
    assert (v.registro_id, v.editable, v.ya_aplicada, v.motivo) == (
        990000001, True, False, None)


def test_f046_r22_nueva_ya_existente_con_despues_es_ya_aplicada():
    v = _nueva(existente=_ls(2.5, rid=990000001),
               base=VeredictoReajuste(11, editable=True, ya_aplicada=True))
    assert (v.editable, v.ya_aplicada) == (True, True)


def test_f046_r22_nueva_ya_existente_con_otra_cantidad_no_es_editable():
    v = _nueva(existente=_ls(1.0, rid=990000001))
    assert not v.editable and v.motivo.startswith(MOTIVO_NUEVA_DISTINTA)


def test_f046_r22_base_no_editable_arrastra_a_la_nueva():
    base = VeredictoReajuste(11, editable=False, motivo="x")
    v = _nueva(base=base)
    assert not v.editable and v.motivo.startswith(MOTIVO_BASE_NO_EDITABLE)


def test_f046_r22_base_aplicada_sin_la_nueva_es_estado_parcial():
    base = VeredictoReajuste(11, editable=True, ya_aplicada=True)
    v = _nueva(base=base)
    assert not v.editable and v.motivo.startswith(MOTIVO_PARCIAL)


@pytest.mark.parametrize("accion", [None, "omitir", "dedicacion",
                                    "ya_registrado"])
def test_f046_r22_nueva_que_preparar_no_escribe_no_es_editable(accion):
    a = None if accion is None else _accion(accion, motivo="por las reglas")
    v = _nueva(accion=a)
    assert not v.editable and v.motivo.startswith(MOTIVO_NO_REGISTRABLE)
    if a is not None:
        assert "por las reglas" in v.motivo


def test_f046_r22_nueva_con_linea_ajena_del_mismo_codigo_no_es_editable():
    ajena = LineaSigrid(ide=4100, reside=501, fecha_int=20261014, horide=9,
                        hora_codigo="HE01", can=1.0, tot=None, synckey=None)
    v = _nueva(choques=[ajena])
    assert not v.editable and v.motivo.startswith(MOTIVO_CHOQUE)
    assert "4100" in v.motivo


def test_f046_r22_nueva_en_otra_obra_que_su_base_no_es_editable():
    v = _nueva(misma_obra=False)
    assert not v.editable and v.motivo.startswith(MOTIVO_OTRA_OBRA)
