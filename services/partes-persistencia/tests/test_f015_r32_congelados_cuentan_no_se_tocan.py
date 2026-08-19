# tests/test_f015_r32_congelados_cuentan_no_se_tocan.py
"""R32 · las lineas congeladas SUMAN en el dia pero no se modifican (DA3).

La decision D7 de F-012 decia «excluir del re-split lo registrado». Al
bajarlo a codigo, excluirlo de la LECTURA produce un error grave en los
dias mixtos: un trabajador con 8 h ya registradas en una obra y 2 h
pendientes en otra tendria, para el calculo, un dia de 2 h y se le
regalaria una segunda jornada completa.

La implementacion (DA3, confirmada por el humano) es: las congeladas
cuentan en el total del dia —su desglose ya conserva las horas— pero
nunca se recortan ni sirven de pivote. Y si el dia no se puede cuadrar sin
tocarlas, no se genera ningun split y se avisa: mejor un dia sin ajustar y
un WARNING que una linea de Sigrid modificada por detras.
"""
from __future__ import annotations

import logging

from application.services.recurso_conciliador import RecursoConciliador
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

LUNES = 20260316
VIERNES = 20260320


def _splits(regs, *, candef=8.0):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


def _resumen(splits):
    return [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits]


# --------------------------- el dia mixto ------------------------------- #

def test_f015_r32_las_horas_registradas_cuentan_en_el_total() -> None:
    """8 h registradas en una obra + 2 h pendientes en otra, jornada 8:
    el dia tiene 10 h, asi que sobran 2 y el ajuste cae en la pendiente."""
    regs = [registro(1, fecha_int=LUNES, horas=8.0,
                     sigrid_estado="registrado", obra_ide=10),
            registro(2, fecha_int=LUNES, horas=2.0, obra_ide=20)]
    assert _resumen(_splits(regs)) == [(2, 0.0, 2.0)]


def test_f015_r32_la_linea_congelada_nunca_es_el_pivote() -> None:
    """Jornada incompleta con la ultima linea congelada: la negativa sale
    sobre la que todavia se puede tocar."""
    regs = [registro(1, fecha_int=LUNES, horas=2.0),
            registro(2, fecha_int=LUNES, horas=4.0,
                     sigrid_estado="registrado")]
    assert _resumen(_splits(regs)) == [(1, 4.0, -2.0)]


def test_f015_r32_el_recorte_salta_la_linea_congelada() -> None:
    """Sobran 4 h y la de mayor id esta congelada: se recorta la anterior."""
    regs = [registro(1, fecha_int=LUNES, horas=8.0),
            registro(2, fecha_int=LUNES, horas=4.0,
                     sigrid_estado="encolado")]
    assert _resumen(_splits(regs)) == [(1, 4.0, 4.0)]


def test_f015_r32_un_documento_aprobado_congela_sus_lineas() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=8.0, doc_approved=True,
                     document_id="doc-a"),
            registro(2, fecha_int=LUNES, horas=2.0, document_id="doc-b")]
    assert _resumen(_splits(regs)) == [(2, 0.0, 2.0)]


# ------------------- el dia que no se puede cuadrar --------------------- #

def test_f015_r32_un_dia_entero_congelado_no_genera_splits(caplog) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert _splits(regs) == []
    assert "CONGELADAS" in caplog.text
    assert "recurso=501" in caplog.text
    assert "2026-03-16" in caplog.text


def test_f015_r32_no_alcanza_para_recortar_sin_tocar_lo_congelado(
        caplog) -> None:
    """Sobran 4 h pero solo hay 1 h no congelada: no se toca nada."""
    regs = [registro(1, fecha_int=LUNES, horas=1.0),
            registro(2, fecha_int=LUNES, horas=11.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert _splits(regs) == []
    assert "CONGELADAS" in caplog.text


def test_f015_r32_sin_pivote_libre_no_hay_extra_negativa(caplog) -> None:
    """Jornada incompleta con TODAS las ordinarias congeladas."""
    regs = [registro(1, fecha_int=LUNES, horas=6.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert _splits(regs) == []
    assert "CONGELADAS" in caplog.text


def test_f015_r32_el_dia_no_laborable_tampoco_toca_lo_congelado(
        caplog) -> None:
    """Un sabado con horas ya registradas: no se mandan a extra."""
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake({"2026-03-21"}),
    )
    regs = [registro(1, fecha_int=20260321, horas=6.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert conciliador._reclasificar_extras_jornada(
            regs, {1: 501}, indice_reshor(501)) == []
    assert "CONGELADAS" in caplog.text


# ---------------------- regresion: sin congelados ----------------------- #

def test_f015_r32_un_dia_sin_congelados_da_lo_mismo_que_antes() -> None:
    """Los dorados de F-003, con la lectura nueva: nada cambia."""
    assert _resumen(_splits([registro(1, fecha_int=LUNES, horas=10.0)])) == [
        (1, 8.0, 2.0)]
    assert _resumen(_splits([registro(1, fecha_int=LUNES, horas=6.0)])) == [
        (1, 8.0, -2.0)]
    assert _splits([registro(1, fecha_int=LUNES, horas=8.0)]) == []


def test_f015_r32_los_registros_sin_las_claves_nuevas_no_estan_congelados(
) -> None:
    """Un registro antiguo (sin `sigrid_estado` ni `doc_approved`) se
    comporta como no congelado: la lectura nueva no puede romper a quien
    construya el dict a mano."""
    reg = {"registro_id": 1, "document_id": "doc-1", "obra_ide": 10,
           "empleado_dni": "12345678Z", "fecha_int": LUNES,
           "tipo_hora": "normal", "horas": 10.0}
    assert _resumen(_splits([reg])) == [(1, 8.0, 2.0)]


def test_f015_r32_una_extra_explicita_congelada_no_se_toca() -> None:
    """4 ordinarias + 4 extra registradas, jornada 8: la ordinaria sube a 8
    y la extra automatica compensa; la extra ya registrada sigue igual."""
    regs = [registro(1, fecha_int=LUNES, horas=4.0),
            registro(2, fecha_int=LUNES, horas=4.0, tipo="extra",
                     sigrid_estado="registrado")]
    splits = _splits(regs)
    assert _resumen(splits) == [(1, 8.0, -4.0)]
    assert all(s["normal_id"] != 2 for s in splits)


# ================= refuerzo tras la campana de mutacion ================= #
# Los BORDES de la guarda "no se puede cuadrar sin tocar lo congelado" no
# estaban fijados: sobrevivian mutantes que movian `>` a `>=`, `<` a `<=` o
# el 0 a 1, y cada uno de ellos decide entre ajustar un dia o no tocarlo.

def test_f015_r32_con_lo_justo_para_recortar_si_se_ajusta(caplog) -> None:
    """Sobran 2 h y hay EXACTAMENTE 2 h no congeladas: se ajusta."""
    regs = [registro(1, fecha_int=LUNES, horas=2.0),
            registro(2, fecha_int=LUNES, horas=8.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        splits = _splits(regs)
    assert _resumen(splits) == [(1, 0.0, 2.0)]
    assert "CONGELADAS" not in caplog.text


def test_f015_r32_una_hora_menos_de_la_necesaria_ya_no_se_ajusta(
        caplog) -> None:
    """Sobran 3 h y solo hay 2 h ajustables: no se toca nada."""
    regs = [registro(1, fecha_int=LUNES, horas=2.0),
            registro(2, fecha_int=LUNES, horas=9.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert _splits(regs) == []
    assert "CONGELADAS" in caplog.text


def test_f015_r32_un_dia_que_cuadra_no_dispara_la_guarda(caplog) -> None:
    """`delta == 0`: no hay nada que ajustar, y eso NO es un dia bloqueado
    por lo congelado. No puede salir el aviso."""
    regs = [registro(1, fecha_int=LUNES, horas=8.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        assert _splits(regs) == []
    assert "CONGELADAS" not in caplog.text


def test_f015_r32_falta_UNA_hora_y_hay_pivote_libre(caplog) -> None:
    """`delta = -1` con una linea ajustable: se sube y se compensa."""
    regs = [registro(1, fecha_int=LUNES, horas=7.0)]
    with caplog.at_level(logging.WARNING):
        assert _resumen(_splits(regs)) == [(1, 8.0, -1.0)]
    assert "CONGELADAS" not in caplog.text


def test_f015_r32_el_aviso_dice_cuantas_horas_faltaban(caplog) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=1.0),
            registro(2, fecha_int=LUNES, horas=11.0,
                     sigrid_estado="registrado")]
    with caplog.at_level(logging.WARNING):
        _splits(regs)
    aviso = next(m for m in caplog.messages if "CONGELADAS" in m)
    assert "faltan 4.00 h" in aviso
    assert "hay 1.00" in aviso
