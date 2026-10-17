# tests/test_f046_t22_pipeline_bordes.py
"""F-046 T22 · bordes de `ReajustePipeline` que la campana de mutacion
dejo sin vigilar (supervivientes de `progress/mutacion_F-046.md`).

Cada test dice que comportamiento observable fija: valores por defecto de
la configuracion, que extras nuevas llegan a `preparar`, que cuenta como
choque, lineas sin parte, motivos, el log de rechazo y el texto del
descuadre. Contra `SigridReajusteFake`; datos SINTETICOS (ni nombres ni
DNIs).
"""
from __future__ import annotations

import logging
import types

from application.pipelines.reajuste_pipeline import (
    MOTIVO_SIN_BASE,
    ReajustePipeline,
)
from application.services.reajuste_lineas import (
    MOTIVO_BASE_NO_EDITABLE,
    MOTIVO_CHOQUE,
    MOTIVO_NO_REGISTRABLE,
    MOTIVO_PARTE_NO_EN_REGISTRO,
)
from domain.models.registro_models import (
    HoraRecurso,
    OpReajuste,
    ResultadoReajuste,
    VeredictoReajuste,
)
from tests.test_f046_reajuste_pipeline import (
    HE,
    HL,
    NUEVA,
    OBRA,
    _caso_extra_nueva,
    _caso_real,
    _fila,
    _linea,
    _nueva,
    _pipe,
    _sigrid,
)


def _pipe_sin_ajustes(cli):
    """Reajuste con una configuracion SIN los ajustes que lee (`est`,
    tope de sentencias, modo pruebas, paso de `pos`): usa sus defectos."""
    _, reg = _pipe(cli)
    return ReajustePipeline(cliente=cli, settings=types.SimpleNamespace(),
                            registro=reg)


# ------------------- defectos de la configuracion ------------------- #

def test_f046_t22_sin_ajustes_el_parte_en_registro_es_el_estado_1():
    """`est_parte_activo` por defecto = 1 (En registro)."""
    cli, ops = _caso_real()
    r = _pipe_sin_ajustes(cli).ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    assert _fila(cli, "partes:11")["can"] == 2.5


def test_f046_t22_sin_ajustes_no_es_modo_pruebas():
    cli, ops = _caso_real()
    r = _pipe_sin_ajustes(cli).comprobar(ops)
    assert r.ok and r.forzada_pruebas is False


def test_f046_t22_sin_ajustes_el_tope_del_lote_es_15_sentencias():
    """14 lineas + guardia = 15 sentencias caben; 15 + guardia no."""
    def caso(n):
        cli = _sigrid([_linea(4000 + i, 100 + i, 8.0, pos=64 * (i + 1))
                       for i in range(n)])
        ops = [OpReajuste(100 + i, despues=4.0, antes=8.0)
               for i in range(n)]
        return _pipe_sin_ajustes(cli).comprobar(ops)
    assert caso(14).ok
    r = caso(15)
    assert not r.ok
    assert all(v.motivo.endswith("16 sentencias y el tope es 15")
               for v in r.veredictos)


def test_f046_t22_sin_ajustes_la_extra_nueva_va_64_posiciones_despues():
    cli, ops = _caso_extra_nueva()
    r = _pipe_sin_ajustes(cli).ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    assert _fila(cli, f"partes:{NUEVA}")["pos"] == 64 + 64


# --------------- que extras nuevas llegan a `preparar` --------------- #

def _espiar_preparar(reg):
    llamadas: list = []
    original = reg.preparar

    def espia(*, obra, lineas):
        llamadas.append((obra.ide, obra.codigo,
                         [l.registro_id for l in lineas]))
        return original(obra=obra, lineas=lineas)
    reg.preparar = espia
    return llamadas


def _comprobar_nueva(**kw):
    cli = _sigrid([_linea(4001, 11, 8.0, pos=64)])
    pipe, reg = _pipe(cli)
    llamadas = _espiar_preparar(reg)
    r = pipe.comprobar([OpReajuste(11, despues=5.5, antes=8.0),
                        _nueva(**kw)])
    return r, llamadas


def test_f046_t22_nueva_sin_fecha_no_se_prepara_y_no_es_editable():
    r, llamadas = _comprobar_nueva(fecha_int=None)
    assert llamadas == []
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not r.ok and not v.editable
    assert v.motivo == f"{MOTIVO_NO_REGISTRABLE} (sin decision)"


def test_f046_t22_nueva_sin_recurso_no_se_prepara():
    r, llamadas = _comprobar_nueva(recurso_ide=None)
    assert llamadas == []
    assert not r.ok


def test_f046_t22_nueva_sin_obra_no_se_prepara():
    r, llamadas = _comprobar_nueva(obra_ide=None, obra_codigo=None)
    assert llamadas == []
    assert not r.ok


def test_f046_t22_nueva_con_solo_el_ide_de_obra_se_prepara():
    _r, llamadas = _comprobar_nueva(obra_codigo=None)
    assert llamadas == [(OBRA, None, [NUEVA])]


def test_f046_t22_nueva_con_solo_el_codigo_de_obra_se_prepara():
    _r, llamadas = _comprobar_nueva(obra_ide=None)
    assert llamadas == [(None, "9999", [NUEVA])]


def test_f046_t22_nueva_no_registrable_no_busca_choques():
    """Si el registro no la escribiria, no se leen los partes del periodo
    (no hay choques que buscar)."""
    cli, ops = _caso_extra_nueva()
    cli.horas = {501: [HoraRecurso(HL, "HL01", None, 20.0, defecto=True)]}
    pipe, _ = _pipe(cli)
    r = pipe.comprobar(ops)
    assert not r.ok
    assert cli.periodos_leidos == []


# ----------------------------- choques ----------------------------- #

def test_f046_t22_linea_ajena_de_otro_codigo_de_hora_no_choca():
    cli, ops = _caso_extra_nueva()
    cli.lineas.append(_linea(4100, 0, 1.0, horide=HL, synckey=""))
    pipe, _ = _pipe(cli)
    assert pipe.comprobar(ops).ok


def test_f046_t22_otra_linea_nuestra_fuera_del_reajuste_choca():
    """Una linea con synckey de partes que NO esta en este reajuste es
    ajena a el: choca igual que una sin synckey."""
    cli, ops = _caso_extra_nueva()
    cli.lineas.append(_linea(4100, 777, 1.0, horide=HE))
    pipe, _ = _pipe(cli)
    r = pipe.comprobar(ops)
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not r.ok and v.motivo.startswith(MOTIVO_CHOQUE)
    assert "4100" in v.motivo


def test_f046_t22_linea_ajena_sin_codigo_de_hora_no_choca_con_el_codigo_1():
    """Una linea ajena sin `horide` no es del codigo de hora de la extra,
    aunque ese codigo tenga ide 1."""
    cli, _ = _caso_extra_nueva()
    cli.horas = {501: [HoraRecurso(HL, "HL01", None, 20.0, defecto=True),
                       HoraRecurso(1, "HE01", None, 25.0)]}
    cli.lineas.append(_linea(4100, 0, 1.0, horide=None, synckey=""))
    ops = [OpReajuste(11, despues=5.5, antes=8.0), _nueva(hora_ide=1)]
    pipe, _ = _pipe(cli)
    assert pipe.comprobar(ops).ok


# ----------------------- lineas sin parte (hmoide) ----------------------- #

def _con_parte_1(can_b):
    """Parte de ide 1 En registro con la linea 11; la 12 sin parte."""
    return _sigrid(
        [_linea(4001, 11, 8.0, hmoide=1),
         _linea(4002, 12, can_b, horide=HE, pre=25.0, pos=128,
                hmoide=None)],
        partes=[{"ide": 1, "obride": OBRA, "ano": 2026, "mes": 10,
                 "cod": "PT26/00001", "emp": 1, "est": 1}])


def test_f046_t22_linea_sin_parte_no_es_editable():
    cli = _con_parte_1(-4.0)
    pipe, _ = _pipe(cli)
    r = pipe.comprobar([OpReajuste(11, despues=2.5, antes=8.0),
                        OpReajuste(12, despues=1.5, antes=-4.0)])
    assert not r.ok
    v = r.veredictos[1]
    assert not v.editable
    assert v.motivo == f"{MOTIVO_PARTE_NO_EN_REGISTRO} (estado None)"


def test_f046_t22_linea_sin_parte_ya_aplicada_sale_con_hmoide_0_sin_parte():
    """R26 va antes que el estado del parte: la linea sin parte que ya
    tiene «despues» cuenta como aplicada, y sale sin codigo de parte."""
    cli = _con_parte_1(1.5)
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar([OpReajuste(11, despues=2.5, antes=8.0),
                       OpReajuste(12, despues=1.5, antes=-4.0)],
                      usuario="admin@test")
    assert r.ok, r
    assert [(x["registro_id"], x["hmoide"], x["parte_cod"], x["escrita"])
            for x in r.lineas] == [(11, 1, "PT26/00001", True),
                                   (12, 0, None, False)]


# ------------------------- motivos y resultado ------------------------- #

def test_f046_t22_nueva_cuya_base_no_viene_dice_por_que():
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    (v,) = pipe.comprobar([ops[1]]).veredictos
    assert v.motivo == f"{MOTIVO_BASE_NO_EDITABLE}: {MOTIVO_SIN_BASE}"


def test_f046_t22_comprobar_editable_sin_aplicar_no_es_ya_aplicada():
    cli, ops = _caso_real()
    pipe, _ = _pipe(cli)
    r = pipe.comprobar(ops)
    assert r.ok and r.ya_aplicada is False


def test_f046_t22_nueva_sin_partida_entra_con_paride_0():
    cli, _ = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar([OpReajuste(11, despues=5.5, antes=8.0),
                       _nueva(partida_ide=None, partida_cod=None)],
                      usuario="admin@test")
    assert r.ok, r
    assert _fila(cli, f"partes:{NUEVA}")["paride"] == 0


def test_f046_t22_defectos_del_resultado_y_del_veredicto():
    r = ResultadoReajuste(ok=True)
    assert (r.ya_aplicada, r.forzada_pruebas, r.error) == (False, False,
                                                           None)
    v = VeredictoReajuste(1, editable=True)
    assert (v.ya_aplicada, v.motivo) == (False, None)


# ------------------------------ el log ------------------------------ #

def test_f046_t22_log_de_rechazo_nombra_solo_las_no_editables(caplog):
    cli, ops = _caso_real()
    ops[1] = OpReajuste(12, despues=1.5, antes=-3.0)
    pipe, _ = _pipe(cli)
    with caplog.at_level(logging.WARNING):
        pipe.ejecutar(ops, usuario="admin@test")
    (texto,) = [r.getMessage() for r in caplog.records
                if "[reajuste] rechazado:" in r.getMessage()]
    assert "1 de 2 linea(s)" in texto
    assert "registro=12:" in texto and "registro=11:" not in texto


def test_f046_t22_log_de_rechazo_nombra_como_mucho_10(caplog):
    """12 lineas que no estan en Sigrid: el log nombra las 10 primeras."""
    cli = _sigrid([])
    ops = [OpReajuste(100 + i, despues=4.0, antes=8.0) for i in range(12)]
    pipe, _ = _pipe(cli)
    with caplog.at_level(logging.WARNING):
        r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok
    (texto,) = [x.getMessage() for x in caplog.records
                if "[reajuste] rechazado:" in x.getMessage()]
    assert "12 de 12 linea(s)" in texto
    assert texto.count("registro=") == 10
    assert "registro=109:" in texto and "registro=110:" not in texto


# --------------------- el descuadre de filas --------------------- #

def test_f046_t22_descuadre_dice_filas_y_esperadas():
    """Guardia 0 filas, cada `UPDATE` 1: si nada se escribe, el error
    muestra lo que devolvio Sigrid frente a lo esperado."""
    cli, ops = _caso_real()

    def borrar_todo(fake):
        fake.lineas = []
    cli.antes_de_escribir = borrar_todo
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok
    assert r.error == ("descuadre en Sigrid: filas [0, 0, 0], esperadas "
                       "[0, 1, 1]")


def test_f046_t22_lote_que_cuadra_no_avisa(caplog):
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    with caplog.at_level(logging.WARNING):
        assert pipe.ejecutar(ops, usuario="admin@test").ok
    assert not [x for x in caplog.records
                if "pese al aviso" in x.getMessage()]



# ------------------------ tolerancia (R21/R26) ------------------------ #

def test_f046_t22_la_tolerancia_incluye_el_borde():
    """`can` a exactamente TOL (+ ruido) de «despues» cuenta como igual."""
    from application.services import reajuste_lineas as rl
    from domain.models.registro_models import LineaSigrid
    borde = rl.TOL + rl._RUIDO
    ls = LineaSigrid(ide=1, reside=501, fecha_int=20261014, horide=HL,
                     hora_codigo=None, can=borde, tot=None,
                     synckey="partes:11")
    v = rl.veredicto_existente(OpReajuste(11, despues=0.0, antes=8.0), ls,
                               1, est_registro=1)
    assert v.editable and v.ya_aplicada
