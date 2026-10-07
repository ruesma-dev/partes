# tests/test_f037_pareja.py
"""F-037 · R1-R3 y el plan de reversion: el nucleo puro de la pareja.

Una «pareja» es una base ordinaria y las extras automaticas que el calculo
de jornada saco de ella: `apply_extras_splits` clona en la extra los
cuatro campos `(document_id, line_index, empleado_line_no, fecha_int)` de
su base. Si un miembro esta congelado (ya viajo a Sigrid), la pareja entera
lo esta para el recalculo de sv3.

Sin base ni red: `pareja_extra` recibe la congelacion por linea ya
calculada con `esta_congelado`.
"""
from __future__ import annotations

from application.services.pareja_extra import (
    FilaPareja,
    PlanRevert,
    clave_pareja,
    claves_congeladas,
    es_miembro,
    plan_revert,
)

K = ("doc-1", 0, None, 20261001)


def _fila(rid: int, *, clave=K, extra_auto: bool = False,
          miembro: bool = True, congelada: bool = False) -> FilaPareja:
    return FilaPareja(registro_id=rid, clave=clave, extra_auto=extra_auto,
                      miembro=miembro, congelada=congelada)


# ============================ R1 · la clave ============================= #

def test_f037_r1_la_clave_son_los_cuatro_campos_en_orden() -> None:
    fila = {"document_id": "doc-9", "line_index": 3, "empleado_line_no": 2,
            "fecha_int": 20261002, "horas": 8.0, "registro_id": 77}
    assert clave_pareja(fila) == ("doc-9", 3, 2, 20261002)


def test_f037_r1_none_es_un_valor_mas() -> None:
    a = {"document_id": "doc-1", "line_index": 0, "empleado_line_no": None,
         "fecha_int": None}
    b = dict(a)
    assert clave_pareja(a) == clave_pareja(b) == ("doc-1", 0, None, None)


def test_f037_r1_falta_un_campo_cuenta_como_none() -> None:
    assert clave_pareja({"document_id": "d", "line_index": 1}) == \
        ("d", 1, None, None)


def test_f037_r1_cada_campo_distingue_la_pareja() -> None:
    base = {"document_id": "d", "line_index": 1, "empleado_line_no": 1,
            "fecha_int": 20261001}
    for campo, otro in (("document_id", "e"), ("line_index", 2),
                        ("empleado_line_no", 2), ("fecha_int", 20261002)):
        vecina = dict(base, **{campo: otro})
        assert clave_pareja(vecina) != clave_pareja(base), campo


# =========================== R2 · los miembros ========================== #

def test_f037_r2_la_extra_automatica_es_miembro() -> None:
    assert es_miembro(extra_auto=True, tipo_hora="extra") is True


def test_f037_r2_la_base_ordinaria_es_miembro() -> None:
    for tipo in ("", None, "normal", "NORMAL", "  Normal  "):
        assert es_miembro(extra_auto=False, tipo_hora=tipo) is True, tipo


def test_f037_r2_la_extra_explicita_no_es_miembro() -> None:
    """La de `crear_extra_desde` de sv4: misma clave, pero no es de la
    pareja; ni la congela ni la toca."""
    assert es_miembro(extra_auto=False, tipo_hora="extra") is False


def test_f037_r2_una_incidencia_no_es_miembro() -> None:
    assert es_miembro(extra_auto=False, tipo_hora="V") is False


def test_f037_r2_una_extra_explicita_congelada_no_congela_la_pareja() -> None:
    filas = [_fila(1), _fila(2, extra_auto=False, miembro=False,
                             congelada=True)]
    assert claves_congeladas(filas) == set()


# ========================= R3 · pareja congelada ======================== #

def test_f037_r3_congelada_por_la_base() -> None:
    assert claves_congeladas([_fila(1, congelada=True),
                              _fila(2, extra_auto=True)]) == {K}


def test_f037_r3_congelada_por_la_extra() -> None:
    assert claves_congeladas([_fila(1),
                              _fila(2, extra_auto=True, congelada=True)]) == {K}


def test_f037_r3_sin_nada_congelado_no_hay_pareja_congelada() -> None:
    assert claves_congeladas([_fila(1), _fila(2, extra_auto=True)]) == set()


def test_f037_r3_las_parejas_vecinas_no_se_influyen() -> None:
    otra_linea = ("doc-1", 1, None, 20261001)
    otro_dia = ("doc-1", 0, None, 20261002)
    otro_doc = ("doc-2", 0, None, 20261001)
    filas = [_fila(1, extra_auto=True, congelada=True)] + [
        _fila(10 + i, clave=c) for i, c in
        enumerate((otra_linea, otro_dia, otro_doc))
    ]
    assert claves_congeladas(filas) == {K}


# ============================ plan_revert ============================== #

def test_f037_plan_sin_nada_congelado_es_lo_de_siempre() -> None:
    plan = plan_revert([_fila(1), _fila(2, extra_auto=True)])
    assert plan == PlanRevert(borrar=(2,), restaurar=(1,), duplicadas=(),
                              congeladas=0, protegidas=0, dobles=())


def test_f037_r4_plan_base_protegida_por_su_extra_congelada() -> None:
    plan = plan_revert([_fila(1), _fila(2, extra_auto=True, congelada=True)])
    assert plan == PlanRevert(borrar=(), restaurar=(), duplicadas=(),
                              congeladas=1, protegidas=1, dobles=())


def test_f037_r5_plan_extra_protegida_por_su_base_congelada() -> None:
    plan = plan_revert([_fila(1, congelada=True), _fila(2, extra_auto=True)])
    assert plan == PlanRevert(borrar=(), restaurar=(), duplicadas=(),
                              congeladas=1, protegidas=1, dobles=())


def test_f037_r6_plan_borra_los_duplicados_de_una_extra_congelada() -> None:
    plan = plan_revert([
        _fila(1),
        _fila(2, extra_auto=True, congelada=True),
        _fila(3, extra_auto=True),
        _fila(4, extra_auto=True),
    ])
    assert plan == PlanRevert(borrar=(3, 4), restaurar=(), duplicadas=(3, 4),
                              congeladas=1, protegidas=1, dobles=())


def test_f037_r6_con_base_y_extra_congeladas_el_duplicado_se_borra() -> None:
    plan = plan_revert([
        _fila(1, congelada=True),
        _fila(2, extra_auto=True, congelada=True),
        _fila(3, extra_auto=True),
    ])
    assert plan.borrar == plan.duplicadas == (3,)
    assert (plan.congeladas, plan.protegidas) == (2, 0)


def test_f037_r7_plan_dos_extras_congeladas_no_se_borran_y_se_avisan() -> None:
    plan = plan_revert([
        _fila(1),
        _fila(2, extra_auto=True, congelada=True),
        _fila(3, extra_auto=True, congelada=True),
    ])
    assert plan.borrar == ()
    assert plan.dobles == ((K, 2),)
    assert plan.congeladas == 2


def test_f037_r7_una_sola_extra_congelada_no_es_doble() -> None:
    plan = plan_revert([_fila(2, extra_auto=True, congelada=True)])
    assert plan.dobles == ()


def test_f037_r7_la_base_congelada_no_cuenta_como_extra_doble() -> None:
    plan = plan_revert([_fila(1, congelada=True),
                        _fila(2, extra_auto=True, congelada=True)])
    assert plan.dobles == ()


def test_f037_r7_dobles_por_orden_de_registro_id_y_con_su_cuenta() -> None:
    k2 = ("doc-1", 1, None, 20261001)
    plan = plan_revert([
        _fila(9, clave=k2, extra_auto=True, congelada=True),
        _fila(1, extra_auto=True, congelada=True),
        _fila(2, extra_auto=True, congelada=True),
        _fila(3, extra_auto=True, congelada=True),
        _fila(10, clave=k2, extra_auto=True, congelada=True),
    ])
    assert plan.dobles == ((K, 3), (k2, 2))


def test_f037_r8_parejas_vecinas_se_revierten_como_siempre() -> None:
    libre = ("doc-1", 1, None, 20261001)
    plan = plan_revert([
        _fila(1),
        _fila(2, extra_auto=True, congelada=True),
        _fila(3, clave=libre),
        _fila(4, clave=libre, extra_auto=True),
    ])
    assert plan.borrar == (4,)
    assert plan.restaurar == (3,)
    assert plan.duplicadas == ()


def test_f037_r2_plan_extra_explicita_de_la_misma_clave_no_cuenta() -> None:
    """Una extra explicita congelada no protege la base, y una no congelada
    no es un duplicado (el plan solo ve lo que trae la consulta, pero el
    nucleo no se fia)."""
    plan = plan_revert([
        _fila(1),
        _fila(2, extra_auto=False, miembro=False, congelada=True),
        _fila(3, extra_auto=True),
    ])
    assert plan.restaurar == (1,)
    assert plan.borrar == (3,)
    assert plan.duplicadas == ()


def test_f037_plan_es_determinista_por_registro_id() -> None:
    filas = [_fila(5, extra_auto=True), _fila(1), _fila(3, extra_auto=True),
             _fila(2, clave=("x", 0, None, 1))]
    plan = plan_revert(filas)
    assert plan.borrar == (3, 5)
    assert plan.restaurar == (1, 2)
    assert plan_revert(reversed(filas)) == plan


def test_f037_plan_duplicadas_en_orden_de_registro_id() -> None:
    plan = plan_revert([
        _fila(7, extra_auto=True),
        _fila(2, extra_auto=True, congelada=True),
        _fila(4, extra_auto=True),
    ])
    assert plan.duplicadas == (4, 7)


def test_f037_plan_vacio() -> None:
    assert plan_revert([]) == PlanRevert(borrar=(), restaurar=(),
                                         duplicadas=(), congeladas=0,
                                         protegidas=0, dobles=())


# ================= refuerzo tras la campana de mutacion ================= #
# `FilaPareja` y `PlanRevert` son valores: el plan se calcula y luego se
# aplica, y nada en medio puede cambiarlo. Los mutantes `frozen=False`
# sobrevivian porque ningun test lo miraba.

def test_f037_fila_pareja_es_inmutable_y_hashable() -> None:
    import dataclasses

    import pytest

    fila = _fila(1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fila.congelada = True  # type: ignore[misc]
    assert {fila, _fila(1)} == {fila}


def test_f037_plan_revert_es_inmutable_y_hashable() -> None:
    import dataclasses

    import pytest

    plan = plan_revert([_fila(1), _fila(2, extra_auto=True)])
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.borrar = ()  # type: ignore[misc]
    assert {plan, plan_revert([_fila(1), _fila(2, extra_auto=True)])} == {plan}
