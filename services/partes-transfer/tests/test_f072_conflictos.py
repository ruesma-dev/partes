# tests/test_f072_conflictos.py
"""F-072 · R38: en una obra agrupada solo choca la misma partida (DA8).

Dos entradas de la misma obra agrupada (VAR-29 y VAR-30) son dos obras para
el trabajador: sus líneas del mismo recurso, día y código de hora NO chocan
(ni conflicto, ni `parte_cerrado` de R11 de F-031, ni las omisiones de F-053
antes del conflicto). Con la MISMA partida, sí, como hoy. En las demás obras
la partida no cuenta, como siempre. La partida de la línea de Sigrid
(`hmores.paride`) solo se lee cuando hace falta (`con_partida`).

Sin red: `SigridFake` ampliado (`f072_comun`) y un sigrid-api falso.
"""
from __future__ import annotations

import httpx
import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.pisado import choques
from domain.models.registro_models import AccionLinea, LineaSigrid
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests import f072_comun as c

REGISTRO, CERRADO = 1, 3


def _parte(obra, est=REGISTRO, ide=900):
    return {"ide": ide, "obride": obra.ide, "ano": 2026, "mes": 11,
            "cod": f"PT26/{ide:05d}", "emp": 1, "est": est}


def _fila(paride, *, ide=7001, hmoide=900, enlazada=False):
    return {"ide": ide, "hmoide": hmoide, "reside": 501, "fec": c.FECHA,
            "horide": c.HL, "hora_codigo": "HL01", "can": 8.0, "tot": 80.0,
            "pos": 64, "synckey": "partes:999", "caaide": 0,
            "paride": paride, "tex": None, "enlazada": enlazada}


def _pf(obra, partida, metodo, *, est=REGISTRO, existente=91013,
        enlazada=False):
    cli = c.ClienteF072(partes=[_parte(obra, est)],
                        lineas=[_fila(existente, enlazada=enlazada)])
    pf = RegistroPipeline(cliente=cli, settings=c.SettingsF072()).preflight(
        obra=obra, lineas=[c.linea(1, partida, metodo)])
    return pf, cli


# ------------------------------ conflicto ------------------------------- #

def test_f072_r38_otra_entrada_del_dia_no_es_conflicto():
    pf, cli = _pf(c.VARO, 91012, "var")
    assert pf.conflictos == []
    assert pf.acciones[0].accion == "escribir"
    assert cli.con_partida_pedida == [True]


def test_f072_r38_la_misma_entrada_si_es_conflicto():
    pf, _cli = _pf(c.VARO, 91012, "var", existente=91012)
    assert [x.registros for x in pf.conflictos] == [[1]]
    assert [ls.ide for ls in pf.conflictos[0].lineas] == [7001]


def test_f072_r38_en_una_obra_normal_la_partida_no_cuenta():
    pf, cli = _pf(c.NORMAL, 300, "parte")
    assert [x.registros for x in pf.conflictos] == [[1]]
    assert cli.con_partida_pedida == [False]


# ------------------------- parte cerrado (R11) -------------------------- #

def test_f072_r38_parte_cerrado_con_otra_entrada_no_omite():
    pf, _cli = _pf(c.VARO, 91012, "var", est=CERRADO)
    assert pf.acciones[0].accion == "escribir"


def test_f072_r38_parte_cerrado_con_la_misma_entrada_omite():
    pf, _cli = _pf(c.VARO, 91012, "var", est=CERRADO, existente=91012)
    assert pf.acciones[0].accion == "omitir"
    assert pf.acciones[0].motivo.startswith("parte_cerrado")


def test_f072_r38_parte_cerrado_en_obra_normal_como_hoy():
    pf, _cli = _pf(c.NORMAL, 300, "parte", est=CERRADO)
    assert pf.acciones[0].accion == "omitir"


# ------------------------- F-053: sin pisado ---------------------------- #

def test_f072_r38_linea_enlazada_de_otra_entrada_no_omite():
    pf, _cli = _pf(c.VARO, 91012, "var", enlazada=True)
    assert pf.acciones[0].accion == "escribir" and pf.conflictos == []


def test_f072_r38_linea_enlazada_de_la_misma_entrada_omite():
    pf, _cli = _pf(c.VARO, 91012, "var", enlazada=True, existente=91012)
    assert pf.acciones[0].accion == "omitir"
    assert "enlazada" in pf.acciones[0].motivo


# ------------------------------ ejecutar -------------------------------- #

def test_f072_r38_ejecutar_escribe_sin_pisar_la_otra_entrada():
    cli = c.ClienteF072(partes=[_parte(c.VARO)], lineas=[_fila(91013)])
    r = RegistroPipeline(cliente=cli, settings=c.SettingsF072()).ejecutar(
        obra=c.VARO, lineas=[c.linea(1, 91012, "var")])
    assert r.ok, r
    assert sorted((x["paride"], x["can"]) for x in cli.lineas) == [
        (91012, 8.0), (91013, 8.0)]


# ------------------------------ puro y SQL ------------------------------ #

def _accion(paride):
    return AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=11,
                       fecha_int=c.FECHA, recurso_ide=501, hora_ide=c.HL,
                       paride=paride)


def _ls(paride):
    return LineaSigrid(ide=1, reside=501, fecha_int=c.FECHA, horide=c.HL,
                       hora_codigo="HL01", can=8.0, tot=80.0, synckey=None,
                       nuestra=False, paride=paride)


def test_f072_r38_choques_por_partida():
    assert choques([_ls(91013)], _accion(91012), set()) != []
    assert choques([_ls(91013)], _accion(91012), set(), por_partida=True) == []
    assert choques([_ls(91012)], _accion(91012), set(), por_partida=True) != []
    assert choques([_ls(None)], _accion(91012), set(), por_partida=True) == []


class SigridApiFalso:
    def __init__(self):
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        return httpx.Response(200, json={
            "ok": True, "truncated": False,
            "columns": ["ide", "reside", "fec", "horide", "hora", "can", "tot",
                        "synckey", "paride", "enlazada"],
            "rows": [[1, 501, c.FECHA, 1, "HL01", 8.0, 80.0, None, 91012, 0]]})


@pytest.mark.parametrize("con_partida, paride", [(True, 91012),
                                                 (False, None)])
def test_f072_r38_lineas_existentes_lee_la_partida_solo_si_se_pide(
        monkeypatch, con_partida, paride):
    falso = SigridApiFalso()
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="clave-de-test", database="bd")
    [ls] = cli.lineas_existentes(9, [501], [c.FECHA], con_partida=con_partida)
    assert ls.paride == paride
    assert ("hmores.paride" in falso.lecturas[0]["sql"]) is con_partida


# ----------------- reajuste: extras nuevas (D2 (a), R38) ----------------- #

def _fila_reajuste(ide, synckey, horide, can, paride, obra):
    return {"ide": ide, "hmoide": obra.ide * 100, "reside": 501,
            "fec": c.FECHA, "horide": horide,
            "hora_codigo": "HE01" if horide == c.HE else "HL01", "can": can,
            "tot": can * 10, "pos": ide, "synckey": synckey, "caaide": 0,
            "paride": paride, "tex": None, "enlazada": False}


def _reajuste(obra, partida, metodo, ajena):
    """La base (`partes:3`, ordinaria) y una extra AJENA del mismo recurso,
    día y código de hora con la partida `ajena`; se pide la extra nueva de
    la base en `partida`."""
    from application.pipelines.reajuste_pipeline import ReajustePipeline
    from domain.models.registro_models import OpReajuste

    parte = {"ide": obra.ide * 100, "obride": obra.ide, "ano": 2026,
             "mes": 11, "cod": "PT26/00900", "emp": 1, "est": REGISTRO}
    cli = c.ClienteF072(partes=[parte], lineas=[
        _fila_reajuste(7001, "partes:3", c.HL, 8.0, partida, obra),
        _fila_reajuste(7002, "porcentajes:x", c.HE, 1.0, ajena, obra)])
    st = c.SettingsF072()
    re = ReajustePipeline(cliente=cli, settings=st,
                          registro=RegistroPipeline(cliente=cli, settings=st))
    r = re.comprobar([
        OpReajuste(registro_id=3, antes=8.0, despues=7.0),
        OpReajuste(registro_id=-3, despues=1.0, base_registro_id=3,
                   recurso_ide=501, fecha_int=c.FECHA, hora_ide=c.HE,
                   hora_codigo="HE01", partida_ide=partida,
                   obra_ide=obra.ide, obra_codigo=obra.codigo,
                   partida_metodo=metodo)])
    return {v.registro_id: v for v in r.veredictos}[-3], cli


def test_f072_r38_d2a_reajuste_otra_entrada_del_dia_no_choca():
    nueva, cli = _reajuste(c.VARO, 91012, "var", ajena=91013)
    assert (nueva.editable, nueva.motivo) == (True, None)
    assert cli.con_partida_pedida == [True]


def test_f072_r38_d2a_reajuste_la_misma_entrada_si_choca():
    nueva, _cli = _reajuste(c.VARO, 91012, "var", ajena=91012)
    assert not nueva.editable and "lineas 7002" in nueva.motivo


def test_f072_r38_d2a_reajuste_en_obra_normal_la_partida_no_cuenta():
    nueva, cli = _reajuste(c.NORMAL, 300, "parte", ajena=301)
    assert not nueva.editable and "lineas 7002" in nueva.motivo
    assert cli.con_partida_pedida == [False]
