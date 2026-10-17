# tests/test_f046_reajuste_pipeline.py
"""F-046 · `ReajustePipeline` de sv5 (R20, R22, R23-R29, [E] R47).

Contra `SigridReajusteFake` (tests/dobles_reajuste.py), que evalua el lote
como SQL Server: guardia, `UPDATE` optimista e `INSERT` condicionado, y
revierte el lote entero si la guardia salta. Sin red ni Sigrid; recursos,
partes, obras e ides SINTETICOS (ni nombres ni DNIs).
"""
from __future__ import annotations

import logging
import threading

import pytest
from application.pipelines.reajuste_pipeline import ReajustePipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reajuste_lineas import (
    MOTIVO_CAN_DISTINTA,
    MOTIVO_CHOQUE,
    MOTIVO_NO_REGISTRABLE,
)
from domain.models.registro_models import HoraRecurso, ObraEntrada, OpReajuste
from tests.dobles import SettingsFake
from tests.dobles_reajuste import SigridReajusteFake

FECHA = 20261014
HL, HE = 7, 9
OBRA, OBRA_PRUEBAS = 10, 404
HMO, HMO_PRUEBAS = 7001, 7404
NUEVA = 990000001


def _obra(ide, cod) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}", empresa=1)
    o.cenide = 77
    return o


def _linea(ide, rid, can, *, horide=HL, pre=20.0, hmoide=HMO, pos=64,
           enlazada=False, tex="", synckey=None) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": 501, "fec": FECHA,
            "horide": horide, "hora_codigo": None, "can": can, "pre": pre,
            "tot": round(can * pre, 2), "pos": pos,
            "synckey": synckey if synckey is not None else f"partes:{rid}",
            "caaide": 0, "tex": tex, "enlazada": enlazada}


def _sigrid(lineas, *, partes=None, horas=None, max_statements=15):
    return SigridReajusteFake(
        obras={"9999": _obra(OBRA, "9999"),
               "0404": _obra(OBRA_PRUEBAS, "0404")},
        horas=horas if horas is not None else {501: [
            HoraRecurso(HL, "HL01", None, 20.0, defecto=True),
            HoraRecurso(HE, "HE01", None, 25.0)]},
        partes=partes if partes is not None else [
            {"ide": HMO, "obride": OBRA, "ano": 2026, "mes": 10,
             "cod": "PT26/09001", "emp": 1, "est": 1},
            {"ide": HMO_PRUEBAS, "obride": OBRA_PRUEBAS, "ano": 2026,
             "mes": 10, "cod": "PT26/09404", "emp": 1, "est": 1}],
        lineas=lineas, max_statements=max_statements)


def _pipe(cli, *, pruebas=False, max_statements=15):
    st = SettingsFake(obra_pruebas_forzar=pruebas)
    st.sigrid_max_statements = max_statements
    reg = RegistroPipeline(cliente=cli, settings=st, lock=threading.Lock())
    return ReajustePipeline(cliente=cli, settings=st, registro=reg), reg


def _caso_real():
    """R6: 0678 registrada 8 + (-4); el reparto la deja en 2,5 + 1,5."""
    cli = _sigrid([_linea(4001, 11, 8.0, pos=64),
                   _linea(4002, 12, -4.0, horide=HE, pre=25.0, pos=128)])
    ops = [OpReajuste(11, despues=2.5, antes=8.0),
           OpReajuste(12, despues=1.5, antes=-4.0)]
    return cli, ops


def _nueva(despues=2.5, **kw) -> OpReajuste:
    args = {"registro_id": NUEVA, "despues": despues, "base_registro_id": 11,
            "recurso_ide": 501, "fecha_int": FECHA, "hora_ide": HE,
            "hora_codigo": "HE01", "partida_ide": 33, "partida_cod": "P-33",
            "obra_ide": OBRA, "obra_codigo": "9999"}
    args.update(kw)
    return OpReajuste(**args)


def _caso_extra_nueva(hmoide=HMO, obra=OBRA):
    """R7: 0678 registrada 8 sin extra; queda 5,5 y extra nueva 2,5."""
    cli = _sigrid([_linea(4001, 11, 8.0, pos=64, hmoide=hmoide)])
    ops = [OpReajuste(11, despues=5.5, antes=8.0),
           _nueva(obra_ide=obra, obra_codigo="9999" if obra == OBRA
                  else "0404")]
    return cli, ops


def _fila(cli, sk):
    return next(f for f in cli.lineas if f["synckey"] == sk)


# ------------------------------- R20 --------------------------------- #

def test_f046_r20_comprobar_da_veredicto_por_linea_y_no_escribe():
    cli, ops = _caso_real()
    pipe, _ = _pipe(cli)
    r = pipe.comprobar(ops)
    assert r.ok
    assert [(v.registro_id, v.editable, v.ya_aplicada) for v in r.veredictos
            ] == [(11, True, False), (12, True, False)]
    assert cli.lotes == []


def test_f046_r20_comprobar_no_toma_el_lock():
    cli, ops = _caso_extra_nueva()
    pipe, reg = _pipe(cli)
    hecho = []
    reg.lock.acquire()
    try:
        hilo = threading.Thread(target=lambda: hecho.append(
            pipe.comprobar(ops)))
        hilo.start()
        hilo.join(timeout=5)
        assert hecho and hecho[0].ok, "comprobar espero al lock"
    finally:
        reg.lock.release()


def test_f046_r20_ejecutar_usa_el_mismo_lock_que_el_registro():
    cli, ops = _caso_extra_nueva()
    pipe, reg = _pipe(cli)
    assert pipe.lock is reg.lock
    cli.vigilar_lock(reg.lock)     # escribir_lote falla fuera del lock
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    assert cli.lock_en_lecturas and all(cli.lock_en_lecturas)


# ---------------------------- R24 / R6 / R7 ---------------------------- #

def test_f046_r24_caso_real_actualiza_can_y_tot():
    cli, ops = _caso_real()
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert r.ok and not r.ya_aplicada
    base, extra = _fila(cli, "partes:11"), _fila(cli, "partes:12")
    assert (base["can"], base["tot"]) == (2.5, 50.0)
    assert (extra["can"], extra["tot"]) == (1.5, 37.5)
    (lote,) = cli.lotes
    assert [s["op"] for s in lote] == ["guardia", "actualizar", "actualizar"]
    assert lote[0]["lineas"] == [(4001, "partes:11", 8.0),
                                 (4002, "partes:12", -4.0)]
    assert [(x["registro_id"], x["hmores_ide"], x["hmoide"], x["parte_cod"],
             x["can"], x["escrita"], x["nueva"]) for x in r.lineas] == [
        (11, 4001, HMO, "PT26/09001", 2.5, True, False),
        (12, 4002, HMO, "PT26/09001", 1.5, True, False)]


def test_f046_r24_extra_nueva_entra_en_el_parte_de_su_base():
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    base = _fila(cli, "partes:11")
    nueva = _fila(cli, f"partes:{NUEVA}")
    assert base["can"] == 5.5
    assert (nueva["hmoide"], nueva["reside"], nueva["fec"], nueva["horide"],
            nueva["can"], nueva["pre"], nueva["tot"], nueva["paride"],
            nueva["pos"], nueva["tex"]) == (HMO, 501, FECHA, HE, 2.5, 25.0,
                                            62.5, 33, 128, "")
    (lote,) = cli.lotes
    assert [s["op"] for s in lote] == ["guardia", "actualizar",
                                       "insertar_extra"]
    assert lote[0]["nuevas"] == [f"partes:{NUEVA}"]
    assert (lote[2]["base_ide"], lote[2]["base_synckey"],
            lote[2]["base_despues"]) == (4001, "partes:11", 5.5)
    fila = next(x for x in r.lineas if x["registro_id"] == NUEVA)
    assert (fila["hmores_ide"], fila["hmoide"], fila["parte_cod"],
            fila["nueva"], fila["escrita"]) == (nueva["ide"], HMO,
                                                "PT26/09001", True, True)


def test_f046_r22_extra_nueva_pasa_por_preparar_del_registro():
    """El recurso sin codigo de hora extra no la escribiria (R2 de las
    reglas): la nueva no es editable y nada se escribe."""
    cli, ops = _caso_extra_nueva()
    cli.horas = {501: [HoraRecurso(HL, "HL01", None, 20.0, defecto=True)]}
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok and cli.lotes == []
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not v.editable and v.motivo.startswith(MOTIVO_NO_REGISTRABLE)


def test_f046_r22_linea_ajena_del_mismo_codigo_bloquea_la_nueva():
    cli, ops = _caso_extra_nueva()
    cli.lineas.append(_linea(4100, 0, 1.0, horide=HE, synckey=""))
    pipe, _ = _pipe(cli)
    r = pipe.comprobar(ops)
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not r.ok and not v.editable
    assert v.motivo.startswith(MOTIVO_CHOQUE) and "4100" in v.motivo


def test_f046_r22_linea_ajena_en_parte_cerrado_no_cuenta_como_choque():
    """R22 mira los partes En registro del periodo."""
    cli, ops = _caso_extra_nueva()
    cli.partes.append({"ide": 7002, "obride": OBRA, "ano": 2026, "mes": 10,
                       "cod": "PT26/09002", "emp": 1, "est": 3})
    cli.lineas.append(_linea(4100, 0, 1.0, horide=HE, synckey="",
                             hmoide=7002))
    pipe, _ = _pipe(cli)
    assert pipe.comprobar(ops).ok


def test_f046_r22_base_que_no_viene_en_el_reajuste_no_es_editable():
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    r = pipe.comprobar([ops[1]])
    (v,) = r.veredictos
    assert not r.ok and not v.editable


# -------------------------------- R23 / R25 -------------------------------- #

def test_f046_r23_una_linea_no_editable_y_no_se_escribe_nada():
    cli, ops = _caso_real()
    ops[1] = OpReajuste(12, despues=1.5, antes=-3.0)       # «antes» falso
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok and r.lineas == []
    assert cli.lotes == []
    assert [(v.registro_id, v.editable) for v in r.veredictos] == [
        (11, True), (12, False)]
    assert r.veredictos[1].motivo.startswith(MOTIVO_CAN_DISTINTA)
    assert _fila(cli, "partes:11")["can"] == 8.0


def test_f046_r25_si_alguien_toca_sigrid_entre_leer_y_escribir_no_queda_nada():
    cli, ops = _caso_real()

    def tocar(fake):
        _fila(fake, "partes:12")["can"] = -3.0
    cli.antes_de_escribir = tocar
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok and "descuadrado" in r.error
    assert _fila(cli, "partes:11")["can"] == 8.0
    assert len(cli.lotes) == 1


def test_f046_r25_lineas_desaparecidas_son_descuadre_sin_escritura():
    cli, ops = _caso_real()

    def borrar_todo(fake):
        fake.lineas = []
    cli.antes_de_escribir = borrar_todo
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok and "descuadre" in r.error
    assert cli.lineas == []


def test_f046_r23_fallo_de_lectura_sube_como_excepcion():
    cli, ops = _caso_real()
    cli.fallo_partes = RuntimeError("sigrid caido")
    pipe, _ = _pipe(cli)
    with pytest.raises(RuntimeError, match="sigrid caido"):
        pipe.ejecutar([ops[0], _nueva()], usuario="admin@test")
    assert cli.lotes == []


# ------------------------------- R26 --------------------------------- #

def test_f046_r26_repetir_ejecutar_es_ya_aplicada_sin_escribir():
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli)
    primero = pipe.ejecutar(ops, usuario="admin@test")
    segundo = pipe.ejecutar(ops, usuario="admin@test")
    assert primero.ok and not primero.ya_aplicada
    assert segundo.ok and segundo.ya_aplicada
    assert len(cli.lotes) == 1
    assert [(x["registro_id"], x["hmores_ide"], x["escrita"])
            for x in segundo.lineas] == [
        (x["registro_id"], x["hmores_ide"], False) for x in primero.lineas]


def test_f046_r26_comprobar_tras_aplicar_dice_ya_aplicada():
    cli, ops = _caso_real()
    pipe, _ = _pipe(cli)
    pipe.ejecutar(ops, usuario="admin@test")
    r = pipe.comprobar(ops)
    assert r.ok and r.ya_aplicada
    assert all(v.ya_aplicada for v in r.veredictos)


# ------------------------------- R27 --------------------------------- #

def test_f046_r27_demasiadas_lineas_para_un_lote_no_son_editables():
    lineas = [_linea(4000 + i, 100 + i, 8.0, pos=64 * (i + 1))
              for i in range(3)]
    cli = _sigrid(lineas, max_statements=3)
    ops = [OpReajuste(100 + i, despues=4.0, antes=8.0) for i in range(3)]
    pipe, _ = _pipe(cli, max_statements=3)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert not r.ok and cli.lotes == []
    assert all(not v.editable and "demasiadas lineas" in v.motivo
               for v in r.veredictos)


def test_f046_r27_justo_en_el_tope_cabe():
    lineas = [_linea(4000 + i, 100 + i, 8.0, pos=64 * (i + 1))
              for i in range(2)]
    cli = _sigrid(lineas, max_statements=3)
    ops = [OpReajuste(100 + i, despues=4.0, antes=8.0) for i in range(2)]
    pipe, _ = _pipe(cli, max_statements=3)
    assert pipe.ejecutar(ops, usuario="admin@test").ok


# ------------------------------- R28 --------------------------------- #

def test_f046_r28_modo_pruebas_extra_nueva_en_0404_con_marca():
    cli = _sigrid([_linea(4001, 11, 8.0, pos=64, hmoide=HMO_PRUEBAS,
                          tex="PRUEBA-IA")])
    ops = [OpReajuste(11, despues=5.5, antes=8.0), _nueva()]
    pipe, _ = _pipe(cli, pruebas=True)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    assert r.forzada_pruebas
    nueva = _fila(cli, f"partes:{NUEVA}")
    assert (nueva["hmoide"], nueva["tex"]) == (HMO_PRUEBAS, "PRUEBA-IA")
    assert _fila(cli, "partes:11")["tex"] == "PRUEBA-IA"


def test_f046_r28_actualizar_no_cambia_tex():
    cli = _sigrid([_linea(4001, 11, 8.0, tex="texto de administracion")])
    pipe, _ = _pipe(cli, pruebas=True)
    assert pipe.ejecutar([OpReajuste(11, despues=6.0, antes=8.0)],
                         usuario="admin@test").ok
    assert _fila(cli, "partes:11")["tex"] == "texto de administracion"


def test_f046_r28_base_real_en_modo_pruebas_no_admite_nueva():
    """En pruebas la nueva iria a la 0404 y su base esta en otra obra."""
    cli, ops = _caso_extra_nueva()
    pipe, _ = _pipe(cli, pruebas=True)
    r = pipe.comprobar(ops)
    assert not r.ok
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not v.editable


# ------------------------------- R29 --------------------------------- #

def test_f046_r29_log_por_linea_sin_nombres(caplog):
    cli, ops = _caso_real()
    pipe, _ = _pipe(cli)
    with caplog.at_level(logging.INFO):
        pipe.ejecutar(ops, usuario="admin@test")
    textos = [r.getMessage() for r in caplog.records
              if "[reajuste]" in r.getMessage()]
    assert any("registro=11 ide=4001 antes=8.00 despues=2.50 "
               "usuario=admin@test" in t for t in textos), textos
    assert any("registro=12 ide=4002 antes=-4.00 despues=1.50" in t
               for t in textos), textos


# ------------------------------ [E] R47 ------------------------------ #

def test_f046_r47_e_extra_a_cero_es_update_nunca_delete():
    """R8: la extra -2 pasa a 0. El doble falla si recibe un borrado o si
    alguien llama a `stmt_borrar_linea`."""
    cli = _sigrid([_linea(4001, 11, 8.0),
                   _linea(4002, 12, -2.0, horide=HE, pre=25.0, pos=128)])
    ops = [OpReajuste(11, despues=6.0, antes=8.0),
           OpReajuste(12, despues=0.0, antes=-2.0)]
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar(ops, usuario="admin@test")
    assert r.ok, r
    extra = _fila(cli, "partes:12")
    assert (extra["can"], extra["tot"]) == (0.0, 0.0)
    assert len(cli.lineas) == 2
    ops_lote = {s["op"] for lote in cli.lotes for s in lote}
    assert ops_lote <= {"guardia", "actualizar", "insertar_extra"}


def test_f046_r47_e_el_pipeline_no_conoce_el_borrado():
    import inspect

    from application.pipelines import reajuste_pipeline
    fuente = inspect.getsource(reajuste_pipeline)
    assert "stmt_borrar_linea" not in fuente
    assert "DELETE" not in fuente.upper()
