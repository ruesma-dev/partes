# tests/test_f056_choques.py
"""F-056 · R31: la linea de ajuste de una franquicia no choca con nada.

Una `HE*` negativa el dia de ajuste (synckey `partes:franquicia:<id>`)
tiene el mismo recurso, dia y codigo de hora que la extra real de ese dia
(H2). Sin R31 el registro ofreceria pisarla (o pisaria la extra real al
revisar el ajuste) y, en un parte cerrado, omitiria la extra como
`parte_cerrado`. Se vigilan los DOS `_choques` (registro via
`pisado.choques` y reajuste) y el preflight de registro de punta a punta.

Sin red: `SigridFake` / `SigridReajusteFake`. Datos SINTETICOS.
"""
from __future__ import annotations

import threading

from application.pipelines.reajuste_pipeline import ReajustePipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.pisado import choques
from domain.models.registro_models import (
    AccionLinea,
    HoraRecurso,
    LineaEntrada,
    LineaSigrid,
    ObraEntrada,
    OpReajuste,
)
from tests.dobles import SettingsFake, SigridFake
from tests.dobles_reajuste import SigridReajusteFake

FECHA = 20261015
REC = 501
HN, HE = 1, 2
OBRA, HMO, HMO_CERRADO = 10, 900, 899
SK_AJUSTE = "partes:franquicia:5"


def _obra() -> ObraEntrada:
    o = ObraEntrada(ide=OBRA, codigo="0100", nombre="Obra 0100", empresa=1)
    o.cenide = 77
    return o


HORAS = {REC: [HoraRecurso(HN, "HL01", None, 15.0, defecto=True),
               HoraRecurso(HE, "HE01", None, 25.0)]}


def _parte(ide, cod, est=1) -> dict:
    return {"ide": ide, "obride": OBRA, "ano": 2026, "mes": 10, "cod": cod,
            "emp": 1, "est": est}


def _fila(ide, *, hmoide=HMO, horide=HE, can=-6.0, synckey=SK_AJUSTE,
          pre=25.0) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": REC, "fec": FECHA,
            "horide": horide, "hora_codigo": None, "can": can, "pre": pre,
            "tot": round(can * pre, 2), "pos": 64, "synckey": synckey,
            "caaide": 0, "paride": 33, "tex": "", "enlazada": False}


def _ls(synckey, can=-6.0) -> LineaSigrid:
    return LineaSigrid(ide=7001, reside=REC, fecha_int=FECHA, horide=HE,
                       hora_codigo="HE01", can=can, tot=None, synckey=synckey)


def _accion() -> AccionLinea:
    return AccionLinea(registro_id=11, accion="escribir", ano=2026, mes=10,
                       fecha_int=FECHA, recurso_ide=REC, hora_ide=HE,
                       hora_codigo="HE01", can=-3.0, pre=25.0)


# ------------------------------ pisado.choques ------------------------------ #

def test_f056_r31_pisado_choques_ignora_el_ajuste():
    assert choques([_ls(SK_AJUSTE)], _accion(), set()) == []


def test_f056_r31_pisado_choques_ignora_el_ajuste_con_espacios():
    assert choques([_ls(f" {SK_AJUSTE} ")], _accion(), set()) == []


def test_f056_r31_pisado_choques_sigue_viendo_las_demas():
    """Solo se excluye el prefijo de franquicia: una manual, una de otro
    registro de `partes` o una ajena siguen chocando."""
    otras = [_ls(None), _ls("partes:77"), _ls("porcentajes:3"),
             _ls("partes:franquicia")]
    assert choques(otras, _accion(), set()) == otras


# --------------------------- ReajustePipeline._choques ---------------------- #

def _reajuste(lineas, partes=None):
    cli = SigridReajusteFake(
        obras={"0100": _obra()}, horas=HORAS,
        partes=partes or [_parte(HMO, "PT26/00314")], lineas=lineas)
    st = SettingsFake()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=threading.Lock())
    return ReajustePipeline(cliente=cli, settings=st, registro=reg), cli


def test_f056_r31_reajuste_choques_ignora_el_ajuste():
    pipe, _cli = _reajuste([_fila(7001)])
    assert pipe._choques(_accion(), _obra(), set()) == []


def test_f056_r31_reajuste_choques_sigue_viendo_una_manual():
    pipe, _cli = _reajuste([_fila(7001, synckey=None, can=2.0)])
    assert [ls.ide for ls in pipe._choques(_accion(), _obra(), set())] == [
        7001]


def test_f056_r31_reajuste_extra_nueva_no_choca_con_el_ajuste():
    """F-046 R22: la extra que nace de una base registrada es editable
    aunque el dia ya tenga la linea de ajuste del recurso."""
    base = _fila(7000, horide=HN, can=8.0, synckey="partes:11", pre=15.0)
    pipe, _cli = _reajuste([base, _fila(7001)])
    r = pipe.comprobar([
        OpReajuste(11, despues=6.0, antes=8.0),
        OpReajuste(990000001, despues=2.0, base_registro_id=11,
                   recurso_ide=REC, fecha_int=FECHA, hora_ide=HE,
                   hora_codigo="HE01", partida_ide=33, partida_cod="01",
                   obra_ide=OBRA, obra_codigo="0100")])
    assert [(v.editable, v.motivo) for v in r.veredictos] == [
        (True, None), (True, None)]


# ------------------------ preflight de registro (R31) ----------------------- #

def _registro(lineas, partes):
    cli = SigridFake(obras={"0100": _obra()}, horas=HORAS, partes=partes,
                     lineas=lineas)
    return RegistroPipeline(cliente=cli, settings=SettingsFake()), cli


def _extra(rid=11) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA, recurso_ide=REC,
                        tipo_hora="extra", horas=-3.0, hora_ide=HE,
                        hora_codigo="HE01", partida_ide=33, partida_cod="01")


def test_f056_r31_preflight_no_ofrece_pisar_el_ajuste():
    pipe, _cli = _registro([_fila(7001)], [_parte(HMO, "PT26/00314")])
    pf = pipe.preflight(obra=_obra(), lineas=[_extra()])
    assert pf.conflictos == []
    assert [(a.registro_id, a.accion) for a in pf.acciones] == [
        (11, "escribir")]


def test_f056_r31_preflight_no_omite_por_el_ajuste_en_parte_cerrado():
    pipe, _cli = _registro(
        [_fila(7001, hmoide=HMO_CERRADO)],
        [_parte(HMO_CERRADO, "PT26/00300", est=3),
         _parte(HMO, "PT26/00314")])
    pf = pipe.preflight(obra=_obra(), lineas=[_extra()])
    assert pf.conflictos == []
    assert [(a.accion, a.motivo) for a in pf.acciones] == [
        ("escribir", None)]


def test_f056_r31_registro_escribe_la_extra_y_no_toca_el_ajuste():
    ajuste = _fila(7001)
    pipe, cli = _registro([dict(ajuste)], [_parte(HMO, "PT26/00314")])
    r = pipe.ejecutar(obra=_obra(), lineas=[_extra()])
    assert [e["registro_id"] for e in r.escritas] == [11]
    assert r.pisadas == [] and r.pendientes_confirmacion == []
    assert cli.lineas[0] == ajuste


def test_f056_r31_sin_ajuste_la_extra_del_dia_si_choca():
    """Control: la misma linea con synckey de otro registro SI choca (el
    test anterior no pasa por casualidad)."""
    pipe, _cli = _registro([_fila(7001, synckey="partes:77")],
                           [_parte(HMO, "PT26/00314")])
    pf = pipe.preflight(obra=_obra(), lineas=[_extra()])
    assert [c.lineas[0].ide for c in pf.conflictos] == [7001]
