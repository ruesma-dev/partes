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

import logging
from dataclasses import asdict

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.cuenta_analitica import (
    MOTIVO_CUENTA_AMBIGUA,
    MOTIVO_OBRA_SIN_CUENTA,
    MOTIVO_RECURSO_SIN_CUENTA,
)
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    PartidaCuenta,
    RecursoSigrid,
)
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
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
    (CEN_OBRA, 1, 704, "0100.CIDOS"), (CEN_OBRA, 1, 705, "0100. CIDOS"),
    (CEN_PRUEBAS, 1, 801, "0404.CIMO12"),
]


PARTIDAS = {
    300: PartidaCuenta(300, "01.02", "0100.CIMO12"),   # maquinista (CI)
    301: PartidaCuenta(301, "02.01", "0100.CDQA01"),   # coste directo (CD)
    302: PartidaCuenta(302, "09.01", "0100.CP00"),     # CP: no vale
    303: PartidaCuenta(303, "10.01", "0100.INGR"),     # ingreso: no vale
    304: PartidaCuenta(304, "11.01", None),            # sin cuenta
    305: PartidaCuenta(305, "12.01", "0100.CICO01"),   # la obra no la tiene
    306: PartidaCuenta(306, "13.01", "0100.CIDOS"),    # la obra tiene dos
}


def _cli(obra=None, partidas=None, **kw) -> SigridFake:
    obra = obra or _obra()
    kw.setdefault("cuentas", CUENTAS)
    return SigridFake(obras={obra.codigo: obra,
                             "0404": _obra(99, "0404", cenide=CEN_PRUEBAS)},
                      horas=HORAS,
                      partidas=PARTIDAS if partidas is None else partidas,
                      **kw)


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


# ===================== R21 · respaldo de la partida ===================== #

NOTA_300 = ("el recurso no tiene cuenta para esa hora: se usa la de la "
            "partida 01.02 (.CIMO12)")


def test_f031_r21_preflight_e_insert_con_la_cuenta_de_la_partida() -> None:
    cli = _cli()
    pf = _pipeline(cli).preflight(
        obra=_obra(), lineas=[_lin(1, 503, 300), _lin(2, 503, 301)])
    assert _caa(pf.acciones) == {
        1: (702, "0100.CIMO12", None, "partida", NOTA_300),
        2: (703, "0100.CDQA01", None, "partida",
            "el recurso no tiene cuenta para esa hora: se usa la de la "
            "partida 02.01 (.CDQA01)"),
    }
    assert all(a.caa_aviso is None for a in pf.acciones)
    r = _pipeline(cli).ejecutar(
        obra=_obra(), lineas=[_lin(1, 503, 300), _lin(2, 503, 301)])
    assert [(l["caaide"], l["paride"]) for l in cli.lineas] == \
        [(702, 300), (703, 301)]
    assert [e["caa_cod"] for e in r.escritas] == \
        ["0100.CIMO12", "0100.CDQA01"]


def test_f031_r21_modo_pruebas_al_centro_de_pruebas() -> None:
    cli = _cli()
    r = _pipeline(cli, obra_pruebas_forzar=True).ejecutar(
        obra=_obra(), lineas=[_lin(1, 503, 300)])
    assert cli.cuentas_leidas[0]["cenide"] == CEN_PRUEBAS
    assert [l["caaide"] for l in cli.lineas] == [801]
    assert [e["caa_cod"] for e in r.escritas] == ["0404.CIMO12"]


def test_f031_r21_obra_sin_esa_cuenta_o_ambigua_como_f021() -> None:
    pf = _pipeline(_cli()).preflight(
        obra=_obra(), lineas=[_lin(1, 503, 305), _lin(2, 503, 306)])
    caa = _caa(pf.acciones)
    assert caa[1][:4] == (0, None, MOTIVO_OBRA_SIN_CUENTA, "partida")
    assert caa[2][:4] == (0, None, MOTIVO_CUENTA_AMBIGUA, "partida")
    avisos = [a.caa_aviso for a in pf.acciones]
    assert avisos == [
        "la obra 0100 no tiene la cuenta analitica .CICO01: la linea ira "
        "sin cuenta",
        "la obra 0100 tiene varias cuentas .CIDOS: la linea ira sin cuenta"]
    assert "13.01" in caa[2][4]


def test_f031_r21_la_nota_no_lleva_nombres() -> None:
    pf = _pipeline(_cli()).preflight(obra=_obra(),
                                     lineas=[_lin(1, 503, 300)])
    assert "Persona" not in pf.acciones[0].caa_nota


# ========================= R20/R22 · el origen ========================= #

def test_f031_r20_r22_origen_recurso_y_ninguno() -> None:
    pf = _pipeline(_cli()).preflight(
        obra=_obra(), lineas=[_lin(1, 501, 300), _lin(2, 503, 302),
                              _lin(3, 503)])
    assert _caa(pf.acciones) == {
        1: (701, "0100.CIMO09", None, "recurso", None),
        2: (0, None, MOTIVO_RECURSO_SIN_CUENTA, None, None),
        3: (0, None, MOTIVO_RECURSO_SIN_CUENTA, None, None),
    }


def test_f031_r20_r22_las_no_escribir_quedan_sin_origen() -> None:
    omitida = _lin(1, 503, 300)
    omitida.horas = 0.0                  # sin horas: se omite
    pf = _pipeline(_cli()).preflight(obra=_obra(), lineas=[omitida])
    assert _caa(pf.acciones) == {1: (0, None, None, None, None)}


# ====================== R23 · el contrato del preflight ====================== #

def test_f031_r23_accion_lleva_origen_y_nota() -> None:
    pf = _pipeline(_cli()).preflight(obra=_obra(),
                                     lineas=[_lin(1, 503, 300)])
    d = asdict(pf.acciones[0])
    assert (d["caa_origen"], d["caa_nota"]) == ("partida", NOTA_300)
    assert (d["caa_motivo"], d["caa_aviso"]) == (None, None)


def test_f031_r23_el_json_del_preflight_incluye_origen_y_nota() -> None:
    api = TestClient(build_app(SettingsFake(),
                               pipeline=_pipeline(_cli())))
    lineas = [_lin(1, 503, 300), _lin(2, 501, 300)]
    r = api.post("/api/registro/preflight", json={
        "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra 0100"},
        "lineas": [dict(l.__dict__) for l in lineas]})
    assert r.status_code == 200
    acciones = {a["registro_id"]: a for a in r.json()["acciones"]}
    assert (acciones[1]["caa_origen"], acciones[1]["caa_nota"]) == \
        ("partida", NOTA_300)
    assert (acciones[2]["caa_origen"], acciones[2]["caa_nota"]) == \
        ("recurso", None)


# ========================= R24 · lectura de partidas ========================= #

def test_f031_r24_una_lectura_solo_con_las_que_hacen_falta() -> None:
    cli = _cli()
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)
    pipeline.ejecutar(obra=_obra(), lineas=[
        _lin(1, 503, 301), _lin(2, 503, 300), _lin(3, 501, 302),
        _lin(4, 503), _lin(5, 503, 301)])
    assert cli.partidas_leidas == [{"parides": [300, 301],
                                    "bajo_lock": False}]


@pytest.mark.parametrize("lineas", [
    [_lin(1, 501, 300)],                 # el recurso ya da subcuenta
    [_lin(1, 503)],                      # sin partida
    [],                                  # nada que escribir
])
def test_f031_r24_sin_necesidad_no_lee_partidas(lineas) -> None:
    cli = _cli()
    _pipeline(cli).preflight(obra=_obra(), lineas=lineas)
    assert cli.partidas_leidas == []
    assert "partidas_de_lineas" not in cli.llamadas


def test_f031_r24_omitidas_no_piden_partida() -> None:
    cli = _cli()
    omitida = _lin(1, 503, 300)
    omitida.horas = 0.0                  # sin horas: se omite
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[omitida])
    assert pf.acciones[0].accion == "omitir"
    assert cli.partidas_leidas == []


def test_f031_r24_fallo_al_leer_partidas_tumba_la_peticion() -> None:
    cli = _cli()
    cli.fallo_partidas = RuntimeError("sigrid-api devolvio una respuesta "
                                      "truncada")
    with pytest.raises(RuntimeError, match="truncada"):
        _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1, 503, 300)])
    with pytest.raises(RuntimeError, match="truncada"):
        _pipeline(cli).ejecutar(obra=_obra(),
                                lineas=[_lin(1, 503, 300), _lin(2, 501)])
    assert "escribir" not in cli.llamadas and cli.lineas == []


# ======================= R25 · una lectura de cuentas ======================= #

def test_f031_r25_una_lectura_de_cuentas_con_ambos_origenes() -> None:
    cli = _cli()
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1, 501, 300), _lin(2, 503, 300), _lin(3, 503, 301)])
    (lectura,) = cli.cuentas_leidas
    assert (lectura["cenide"], lectura["empresa"], lectura["subcuentas"]) \
        == (CEN_OBRA, 1, ["CDQA01", "CIMO09", "CIMO12"])
    assert [l["caaide"] for l in cli.lineas] == [701, 702, 703]


# ============================ R26 · el log ============================ #

def test_f031_r26_info_origen_cuenta_sin_nombres(caplog) -> None:
    lineas = [_lin(1, 501, 300), _lin(2, 503, 300), _lin(3, 503, 302),
              _lin(4, 503)]
    lineas[0].dni = "12345678Z"
    recursos = {501: RecursoSigrid(501, 1, None, "12345678Z"),
                503: RecursoSigrid(503, 1, None, None)}
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(_cli(recursos=recursos)).preflight(obra=_obra(),
                                                     lineas=lineas)
    (msg,) = [r for r in caplog.records
              if "origen cuenta" in r.getMessage()]
    assert msg.levelno == logging.INFO
    assert msg.getMessage() == ("[registro] origen cuenta obra=0100 "
                                "recurso=1 partida=1 ninguna=2")
    (f021,) = [r.getMessage() for r in caplog.records
               if "cuentas obra=" in r.getMessage()]
    assert f021 == ("[registro] cuentas obra=0100 ok=2 recurso_sin_cuenta=2 "
                    "obra_sin_cuenta=0 cuenta_ambigua=0")
    texto = caplog.text
    assert "Persona" not in texto and "12345678Z" not in texto
