# tests/test_f072_guarda_reajuste_franquicia.py
"""F-072 · Enmienda (b) del 2026-11-21: reajuste y franquicia pasan la guarda.

Las extras nuevas del reajuste y la extra de la franquicia se preparan con
`RegistroPipeline.preparar`, así que en una obra agrupada pasan la guarda de
R36. Para que una entrada buena se escriba, `partida_metodo` (la marca de la
línea base, que manda sv4) viaja por `LineaReajusteIn`/`OpReajuste` y
`FranquiciaIn`/`PeticionFranquicia` hasta la `LineaEntrada`. Sin la marca, se
omite con `partida_agrupada:`. Fuera de las obras agrupadas, como siempre.

Sin red: `SigridFake` ampliado (`f072_comun`). Datos FICTICIOS.
"""
from __future__ import annotations

from application.pipelines.franquicia_pipeline import FranquiciaPipeline
from application.pipelines.reajuste_pipeline import ReajustePipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import OpReajuste, PeticionFranquicia
from interface_adapters.api.app import FranquiciaIn, LineaReajusteIn
from tests import f072_comun as c


def _pipes(cli=None):
    cli = cli or c.ClienteF072()
    st = c.SettingsF072()
    reg = RegistroPipeline(cliente=cli, settings=st)
    return (FranquiciaPipeline(cliente=cli, settings=st, registro=reg),
            ReajustePipeline(cliente=cli, settings=st, registro=reg), cli)


def _peticion(obra, partida, metodo):
    p = PeticionFranquicia(
        ajuste_id=7, recurso_ide=501, periodo="2026-11", inicio=20261016,
        fin=20261115, fecha_int=20261113, obra=obra, partida_ide=partida,
        partida_cod=None)
    if metodo is not None:
        # Como `FranquiciaIn.a_dominio`: atributo, no campo (F-056 §6).
        p.partida_metodo = metodo
    return p


def _op(obra, partida, metodo, rid=-3):
    return OpReajuste(registro_id=rid, despues=1.5, base_registro_id=3,
                      recurso_ide=501, fecha_int=c.FECHA, hora_ide=c.HE,
                      hora_codigo="HE01", partida_ide=partida,
                      obra_ide=obra.ide, obra_codigo=obra.codigo,
                      partida_metodo=metodo)


# ------------------------------- franquicia ------------------------------- #

def test_f072_franquicia_con_la_marca_de_la_entrada_se_prepara():
    fq, _re, cli = _pipes()
    prep = fq._preparar(_peticion(c.VARO, 91012, "var"))
    assert (prep.accion.accion, prep.accion.motivo) == ("escribir", None)
    assert prep.accion.paride == 91012
    assert cli.presupuestos_leidos == [9101]


def test_f072_franquicia_sin_marca_en_obra_agrupada_se_omite():
    fq, _re, _cli = _pipes()
    prep = fq._preparar(_peticion(c.VARO, 91012, None))
    assert prep.accion.accion == "omitir"
    assert prep.accion.motivo.startswith("partida_agrupada: sin entrada var")


def test_f072_franquicia_en_obra_normal_como_siempre():
    fq, _re, cli = _pipes()
    prep = fq._preparar(_peticion(c.NORMAL, None, None))
    assert prep.accion.accion == "escribir"
    assert cli.presupuestos_leidos == []


def test_f072_franquicia_in_lleva_la_marca_al_dominio():
    base = {"ajuste_id": 7, "recurso_ide": 501, "periodo": "2026-11",
            "inicio": 20261016, "fin": 20261115, "fecha_int": 20261113,
            "obra": {"ide": 9101, "codigo": "VAR"}, "partida_ide": 91012}
    assert FranquiciaIn(**base, partida_metodo="var").a_dominio(
    ).partida_metodo == "var"
    assert FranquiciaIn(**base).a_dominio().partida_metodo is None


# --------------------------------- reajuste -------------------------------- #

def test_f072_reajuste_extra_nueva_con_la_marca_se_prepara():
    _fq, re, cli = _pipes()
    prep = re._preparar_nuevas([_op(c.VARO, 91013, "var")])[-3]
    assert (prep.accion.accion, prep.accion.motivo) == ("escribir", None)
    assert prep.accion.paride == 91013
    assert cli.presupuestos_leidos == [9101]


def test_f072_reajuste_extra_nueva_sin_marca_se_omite():
    _fq, re, _cli = _pipes()
    prep = re._preparar_nuevas([_op(c.PV, 90011, None)])[-3]
    assert prep.accion.accion == "omitir"
    assert "sin entrada postventa" in prep.accion.motivo


def test_f072_reajuste_extra_nueva_en_obra_normal_como_siempre():
    _fq, re, cli = _pipes()
    prep = re._preparar_nuevas([_op(c.NORMAL, None, None)])[-3]
    assert prep.accion.accion == "escribir"
    assert cli.presupuestos_leidos == []


def test_f072_linea_reajuste_in_lleva_la_marca_al_dominio():
    linea = LineaReajusteIn(registro_id=-3, despues=1.5, base_registro_id=3,
                            partida_metodo="postventa")
    assert OpReajuste(**linea.model_dump()).partida_metodo == "postventa"
    assert LineaReajusteIn(registro_id=1, despues=1.0).partida_metodo is None
