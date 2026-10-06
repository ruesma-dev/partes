# tests/test_f031_estado_parte.py
"""F-031 · Regla pura del parte destino (`estado_parte.py`, design §7.1).

«Cerrado» = cualquier parte del periodo que NO esta En registro (Cerrado o
Imputado; humano, 2026-10-06). El elegido es el de mayor `ide` En registro;
si no hay ninguno, se propone uno nuevo. Hay complementario cuando el
periodo tiene algun parte cerrado. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.estado_parte import (
    MOTIVO_PARTE_CERRADO,
    aviso_de_parte,
    elegir_parte,
    motivo_choque,
    nombre_estado,
)
from domain.models.registro_models import ParteDestino, ParteSigrid

REG, CER, IMP = 1, 3, 10


def _elegir(partes):
    return elegir_parte(2026, 1, partes, est_registro=REG)


# ============================ R2 · el elegido ============================ #

def test_f031_r2_mayor_ide_en_registro_aunque_haya_cerrados_mayores() -> None:
    partes = [ParteSigrid(5, "PT26/00005", REG),
              ParteSigrid(9, "PT26/00009", CER),
              ParteSigrid(7, "PT26/00007", REG),
              ParteSigrid(12, "PT26/00012", IMP)]
    p = _elegir(partes)
    assert (p.ano, p.mes, p.existe, p.ide, p.cod, p.estado) == \
        (2026, 1, True, 7, "PT26/00007", REG)
    assert p.complementario is True
    # Por `ide` descendente, sea cual sea el orden de llegada.
    assert [x.ide for x in p.del_periodo] == [12, 9, 7, 5]
    assert p.cerrados == ["PT26/00012", "PT26/00009"]
    assert p.creado is False and p.aviso is None


def test_f031_r2_un_solo_parte_en_registro_no_es_complementario() -> None:
    p = _elegir([ParteSigrid(5, "PT26/00005", REG)])
    assert (p.existe, p.ide, p.cod, p.estado, p.complementario,
            p.cerrados) == (True, 5, "PT26/00005", REG, False, [])


def test_f031_r2_el_predicado_es_el_estado_de_registro_que_se_pasa() -> None:
    p = elegir_parte(2026, 1, [ParteSigrid(5, "PT26/00005", 7)],
                     est_registro=7)
    assert (p.existe, p.complementario) == (True, False)


# ========================= R3 · todos cerrados ========================= #

@pytest.mark.parametrize("est", [CER, IMP, 4])
def test_f031_r3_todos_cerrados_propone_complementario_nuevo(est) -> None:
    p = _elegir([ParteSigrid(4, "PT26/00004", est)])
    assert (p.existe, p.ide, p.cod, p.estado) == (False, None, None, None)
    assert (p.complementario, p.cerrados) == (True, ["PT26/00004"])
    assert p.del_periodo == [ParteSigrid(4, "PT26/00004", est)]


# =========================== R4 · sin partes =========================== #

def test_f031_r4_sin_partes_parte_nuevo_sin_complementario() -> None:
    p = _elegir([])
    assert p == ParteDestino(ano=2026, mes=1)
    assert (p.existe, p.estado, p.complementario, p.cerrados,
            p.del_periodo, p.aviso) == (False, None, False, [], [], None)


# ======================== R7 · nombres de estado ======================== #

def test_f031_r7_nombres_de_estado() -> None:
    kw = dict(est_cerrado=CER, est_imputado=IMP)
    assert nombre_estado(CER, **kw) == "Cerrado"
    assert nombre_estado(IMP, **kw) == "Imputado"
    assert nombre_estado(4, **kw) == "estado 4"
    assert nombre_estado(None, **kw) == "estado None"
    assert nombre_estado(8, est_cerrado=8, est_imputado=9) == "Cerrado"
    assert nombre_estado(9, est_cerrado=8, est_imputado=9) == "Imputado"


# ============================ R18 · el aviso ============================ #

def test_f031_r18_aviso_complementario_nuevo() -> None:
    p = _elegir([ParteSigrid(4, "PT26/00004", IMP)])
    p.cod = "PT26/00350"
    assert aviso_de_parte(p, {"PT26/00004": "Imputado"}) == (
        "el parte PT26/00004 (Imputado) de 01/2026 esta cerrado: las "
        "lineas van al parte complementario PT26/00350 (se creara)")


def test_f031_r18_aviso_complementario_existente_y_varios_cerrados() -> None:
    p = _elegir([ParteSigrid(4, "PT26/00004", IMP),
                 ParteSigrid(9, "PT26/00009", CER),
                 ParteSigrid(11, "PT26/00350", REG)])
    assert aviso_de_parte(p, {"PT26/00004": "Imputado",
                              "PT26/00009": "Cerrado"}) == (
        "los partes PT26/00009 (Cerrado), PT26/00004 (Imputado) de 01/2026 "
        "estan cerrados: las lineas van al parte complementario PT26/00350 "
        "(ya existe, en registro)")


def test_f031_r18_aviso_con_estado_sin_nombre() -> None:
    p = _elegir([ParteSigrid(4, "PT26/00004", 4)])
    p.cod = "PT26/00350"
    assert "PT26/00004 (estado ?)" in aviso_de_parte(p, {})


@pytest.mark.parametrize("partes", [
    [], [ParteSigrid(5, "PT26/00005", REG)],
    [ParteSigrid(5, "PT26/00005", REG), ParteSigrid(6, "PT26/00006", REG)],
])
def test_f031_r18_sin_cerrados_no_hay_aviso(partes) -> None:
    assert aviso_de_parte(_elegir(partes), {}) is None


# ========================= R11 · motivo del choque ========================= #

def test_f031_r11_motivo_choque_con_prefijo_y_sin_nombres() -> None:
    assert MOTIVO_PARTE_CERRADO == "parte_cerrado"
    texto = motivo_choque("PT26/00004", "Cerrado")
    assert texto == (
        "parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte "
        "PT26/00004 (Cerrado); no se registran")
    assert texto.startswith(MOTIVO_PARTE_CERRADO + ": ")
