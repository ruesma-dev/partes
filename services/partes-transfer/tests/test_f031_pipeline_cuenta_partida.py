# tests/test_f031_pipeline_cuenta_partida.py
"""F-031 · D: la cuenta analitica en el pipeline (manda el recurso).

La cuenta sigue saliendo de la ficha de horas del recurso (F-021, R20);
solo si el recurso no da subcuenta se usa la de la partida, y solo si es
de coste (`CI*`/`CD*`, R21). Si tampoco, la linea va sin cuenta (R22).

Primer bloque: caracterizacion EN VERDE contra el codigo anterior a F-031
(R20, R22). Segundo bloque: lo nuevo (R21, R23-R26).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

from types import SimpleNamespace

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.cuenta_analitica import MOTIVO_RECURSO_SIN_CUENTA
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    RecursoSigrid,
)
from tests.dobles import SettingsFake, SigridFake

FECHA = 20260302
CEN_OBRA, CEN_PRUEBAS = 77, 88
HL, HE = 1, 2


def _obra(ide=10, cod="0100", empresa=1, cenide=CEN_OBRA) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = cenide        # como lo deja el cliente real
    return o


def _h(horide, cod, caa=None, defecto=False) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=10.0,
                       caa_cod=caa, defecto=defecto)


HORAS = {
    # Con cuenta en la ficha (oficial).
    501: [_h(HL, "HL01", "00000.CIMO09", True), _h(HE, "HE01")],
    # Sin ninguna cuenta en la ficha.
    503: [_h(HL, "HL01", None, True), _h(HE, "HE01")],
}

CUENTAS = [
    (CEN_OBRA, 1, 701, "0100.CIMO09"), (CEN_OBRA, 1, 702, "0100.CIMO12"),
    (CEN_OBRA, 1, 703, "0100.CDQA01"),
    (CEN_PRUEBAS, 1, 801, "0404.CIMO12"),
]


def _partida(ide, cod, caa_cod):
    """Duck-typing de `PartidaCuenta` (ide, cod, caa_cod)."""
    return SimpleNamespace(ide=ide, cod=cod, caa_cod=caa_cod)


PARTIDAS = {
    300: _partida(300, "01.02", "0100.CIMO12"),     # maquinista (CI)
    301: _partida(301, "02.01", "0100.CDQA01"),     # coste directo (CD)
    302: _partida(302, "09.01", "0100.CP00"),       # CP: no vale
    303: _partida(303, "10.01", "0100.INGR"),       # ingreso: no vale
    304: _partida(304, "11.01", None),              # sin cuenta
}


def _cli(obra=None, partidas=None, **kw) -> SigridFake:
    obra = obra or _obra()
    kw.setdefault("cuentas", CUENTAS)
    cli = SigridFake(obras={obra.codigo: obra,
                            "0404": _obra(99, "0404", cenide=CEN_PRUEBAS)},
                     horas=HORAS, **kw)
    cli.partidas = dict(PARTIDAS if partidas is None else partidas)
    return cli


def _lin(rid, recurso=501, partida=None, **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        tipo_hora="normal", horas=8.0, partida_ide=partida,
                        partida_cod=(PARTIDAS[partida].cod if partida
                                     in PARTIDAS else None), **kw)


def _pipeline(cli, **st) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(**st))


def _caa(acciones) -> dict:
    return {a.registro_id: (a.caa_ide, a.caa_cod, a.caa_motivo,
                            getattr(a, "caa_origen", None),
                            getattr(a, "caa_nota", None))
            for a in acciones}


# =============== Caracterizacion (verde ANTES de F-031) =============== #

def test_f031_r20_la_cuenta_del_recurso_manda_aunque_la_partida_tenga_otra(
) -> None:
    cli = _cli()
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1, 501, 300)])
    (ide, cod, motivo, _origen, nota) = _caa(pf.acciones)[1]
    assert (ide, cod, motivo, nota) == (701, "0100.CIMO09", None, None)
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1, 501, 300)])
    assert [(l["caaide"], l["paride"]) for l in cli.lineas] == [(701, 300)]


def test_f031_r22_porsan_sin_cuenta_ni_nota() -> None:
    obra = _obra(20, "0724", empresa=28, cenide=0)
    cli = _cli(obra=obra, cuentas=[],
               recursos={503: RecursoSigrid(503, 28, 0, None)})
    lineas = [_lin(1, 503), _lin(2, 503, 303), _lin(3, 503, 304)]
    pf = _pipeline(cli).preflight(obra=obra, lineas=lineas)
    assert _caa(pf.acciones) == {
        i: (0, None, MOTIVO_RECURSO_SIN_CUENTA, None, None)
        for i in (1, 2, 3)}
    assert all(a.caa_aviso is None for a in pf.acciones)
    assert cli.cuentas_leidas == []
