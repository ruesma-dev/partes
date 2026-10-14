# tests/test_f046_reajuste_reparto.py
"""F-046 · reglas puras del reajuste en sv3 (`reajuste_reparto`).

  - `clase_linea`: libre, reajustable o dura (glosario de requirements).
  - `firma_grupo`: huella del grupo, estable ante el orden y sensible a
    lineas, horas, `horas_orig`, estados y aprobacion (R13).
  - `decidir_grupo`: la maquina de estados de design §3 (R11-R15).
  - `cambios_a_json` / `json_a_cambios`: ida y vuelta del JSON.

Datos sinteticos, sin nombres ni DNIs.
"""
from __future__ import annotations

import pytest
from application.services.reajuste_reparto import (
    CONGELAR,
    DURA,
    LIBRE,
    MATERIALIZAR,
    PROPONER,
    REAJUSTABLE,
    RESIDUAL,
    RESIDUAL_MANTENER,
    cambios_a_json,
    clase_linea,
    decidir_grupo,
    firma_grupo,
    json_a_cambios,
)
from infrastructure.database.orm_models import ESTADOS_REPARTO


def _r(rid=1, *, tipo="normal", horas=8.0, estado=None, aprobado=False,
       horas_orig=None, extra_auto=False, borrada=None) -> dict:
    return {"registro_id": rid, "tipo_hora": tipo, "horas": horas,
            "sigrid_estado": estado, "doc_approved": aprobado,
            "horas_orig": horas_orig, "extra_auto": extra_auto,
            "deleted_at_utc": borrada}


# ------------------------------ clase_linea ------------------------------ #

def test_f046_clase_libre_si_no_esta_congelada():
    assert clase_linea(_r(estado="registrado"), congelada=False) == LIBRE


@pytest.mark.parametrize("estado", [None, "", "registrado", " Registrado ",
                                    "omitido", "error", "conflicto",
                                    "borrado_sigrid"])
def test_f046_clase_reajustable(estado):
    assert clase_linea(_r(estado=estado, aprobado=True),
                       congelada=True) == REAJUSTABLE


@pytest.mark.parametrize("estado", ["encolado", "dedicacion", "otro_raro"])
def test_f046_clase_dura_por_estado(estado):
    assert clase_linea(_r(estado=estado), congelada=True) == DURA


def test_f046_clase_dura_ordinaria_sin_horas():
    assert clase_linea(_r(horas=0.0, estado="registrado"),
                       congelada=True) == DURA
    assert clase_linea(_r(horas=None, estado="registrado"),
                       congelada=True) == DURA


def test_f046_clase_la_extra_negativa_no_es_dura_por_sus_horas():
    assert clase_linea(_r(tipo="extra", horas=-4.0, estado="registrado"),
                       congelada=True) == REAJUSTABLE


def test_f046_clase_dura_en_papelera():
    assert clase_linea(_r(estado="registrado", borrada="2026-10-14"),
                       congelada=True) == DURA


# ------------------------------ firma_grupo ------------------------------ #

def test_f046_r13_firma_estable_ante_el_orden():
    a, b = _r(1), _r(2, horas=4.0)
    assert firma_grupo([a, b]) == firma_grupo([b, a])
    assert len(firma_grupo([a, b])) == 64


@pytest.mark.parametrize("cambio", [
    {"horas": 7.5}, {"horas_orig": 4.0}, {"sigrid_estado": "registrado"},
    {"doc_approved": True}, {"tipo_hora": "extra"}, {"extra_auto": True},
    {"registro_id": 3},
])
def test_f046_r13_firma_sensible_a_cada_campo(cambio):
    base = [_r(1), _r(2, horas=4.0)]
    otro = [dict(base[0], **cambio), base[1]]
    assert firma_grupo(base) != firma_grupo(otro)


def test_f046_r13_firma_sensible_a_una_linea_de_mas():
    assert firma_grupo([_r(1)]) != firma_grupo([_r(1), _r(2)])


def test_f046_r13_firma_ignora_ruido_de_coma_flotante_y_mayusculas():
    assert firma_grupo([_r(1, horas=8.0, tipo="Normal ")]) == firma_grupo(
        [_r(1, horas=8.000000001, tipo="normal")])
    assert firma_grupo([_r(1, estado=" REGISTRADO")]) == firma_grupo(
        [_r(1, estado="registrado")])


def test_f046_r13_firma_trata_igual_none_y_vacio_en_el_estado():
    assert firma_grupo([_r(1, estado=None)]) == firma_grupo([_r(1, estado="")])


# ----------------------------- decidir_grupo ----------------------------- #

F = "a" * 64


def _fila(estado, firma=F) -> dict:
    return {"id": 9, "estado": estado, "firma": firma}


def test_f046_estados_del_orm():
    assert ESTADOS_REPARTO == ("pendiente", "aplicando", "aplicado",
                               "materializado", "rechazado", "mantenido",
                               "obsoleto")


@pytest.mark.parametrize("libres", [True, False])
def test_f046_r11_sin_fila_propone_si_hay_libres(libres):
    assert decidir_grupo(None, F, libres) == (PROPONER if libres
                                              else RESIDUAL)


def test_f046_r15_aplicado_se_materializa():
    for libres in (True, False):
        for firma in (F, "b" * 64):
            assert decidir_grupo(_fila("aplicado"), firma,
                                 libres) == MATERIALIZAR


def test_f046_r13_aplicando_no_se_toca():
    for libres in (True, False):
        for firma in (F, "b" * 64):
            assert decidir_grupo(_fila("aplicando"), firma,
                                 libres) == CONGELAR


@pytest.mark.parametrize("estado", ["rechazado", "mantenido"])
def test_f046_r14_rechazado_o_mantenido_con_firma_vigente_es_residual(estado):
    assert decidir_grupo(_fila(estado), F, True) == RESIDUAL_MANTENER
    assert decidir_grupo(_fila(estado), F, False) == RESIDUAL_MANTENER


@pytest.mark.parametrize("estado", ["rechazado", "mantenido"])
def test_f046_r13_rechazado_con_otra_firma_vuelve_a_proponer(estado):
    assert decidir_grupo(_fila(estado), "b" * 64, True) == PROPONER
    assert decidir_grupo(_fila(estado), "b" * 64, False) == RESIDUAL


@pytest.mark.parametrize("estado", ["pendiente", "materializado",
                                    "obsoleto"])
def test_f046_r13_pendiente_materializado_u_obsoleto_proponen(estado):
    assert decidir_grupo(_fila(estado), F, True) == PROPONER
    assert decidir_grupo(_fila(estado), "b" * 64, True) == PROPONER
    assert decidir_grupo(_fila(estado), F, False) == RESIDUAL


# ------------------------------- JSON ------------------------------- #

def test_f046_cambios_json_ida_y_vuelta():
    datos = {"ids_grupo": [3, 1], "cambios": [
        {"registro_id": None, "base_registro_id": 1, "tipo": "extra",
         "antes": 0.0, "despues": 2.5,
         "hora_ext": {"ide": 9, "cod": "HE01", "desc": "Extra", "ext": 1}}]}
    texto = cambios_a_json(datos)
    assert json_a_cambios(texto) == datos
    assert cambios_a_json(datos) == texto       # determinista


@pytest.mark.parametrize("texto", [None, "", "{}", "no-es-json", "[]"])
def test_f046_json_vacio_o_roto_es_un_reparto_sin_cambios(texto):
    assert json_a_cambios(texto) == {"ids_grupo": [], "cambios": []}
