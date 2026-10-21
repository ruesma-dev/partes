# tests/test_f053_pipeline_pisado.py
"""F-053 · Pisar sin borrar en el pipeline de registro (R1, R5-R8, R10,
R12-R18) y en el doble `SigridFake` (design §7).

  - Doble: la op `anular` evalua el `UPDATE` de `stmt_anular_linea` como
    SQL Server (fila con esos valores, sin enlaces y con su parte En
    registro); no hay op `borrar`.
  - Pipeline: los ejemplos 1-6 de `requirements.md`, la precedencia de las
    omisiones (R8), `anuladas` por relectura (R12), el INFO de cada pisada
    (R13), la relectura que falla (R14) y la caracterizacion (R15-R18).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (obras,
codigos y personas inventados; ni nombres reales ni DNIs).
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import HoraRecurso, LineaEntrada, ObraEntrada
from tests.dobles import SettingsFake, SigridFake

FECHA = 20261015
REC = 501
HN, HE, CIV = 1, 2, 30
REGISTRO, CERRADO, IMPUTADO = 1, 3, 10
OBRA = 10
HMO = 900                     # PT26/00314


def _obra(ide=OBRA, cod="0100", empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = 77
    return o


def _h(horide, cod, defecto=False, pre=15.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=None, defecto=defecto)


HORAS = {REC: [_h(HN, "HL01", True), _h(HE, "HE01", pre=25.0),
               _h(CIV, "CIV", pre=0.0)]}


def _parte(ide, cod, est=REGISTRO, ano=2026, mes=10) -> dict:
    return {"ide": ide, "obride": OBRA, "ano": ano, "mes": mes, "cod": cod,
            "emp": 1, "est": est}


def _fila(ide, hmoide=HMO, *, reside=REC, horide=HN, synckey=None,
          fec=FECHA, can=8.0, enlazada=False, tex="manual") -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can,
            "tot": None if can is None else can * 15.0, "pos": 64,
            "synckey": synckey, "caaide": 702, "paride": 33, "tex": tex,
            "enlazada": enlazada}


def _cli(**kw) -> SigridFake:
    return SigridFake(obras={"0100": _obra()}, horas=HORAS, **kw)


def _anular(cli, ide=9001, *, reside=REC, fecha_int=FECHA, horide=HN,
            antes=8.0) -> dict:
    return cli.stmt_anular_linea(ide=ide, reside=reside, fecha_int=fecha_int,
                                 horide=horide, antes=antes)


# ============================ Doble (T3, §7) ============================ #

def test_f053_doble_sin_op_borrar() -> None:
    assert not hasattr(SigridFake, "stmt_borrar_linea")
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    with pytest.raises(AssertionError, match="op desconocida: borrar"):
        cli.escribir([{"op": "borrar", "ide": 9001}])
    assert cli.lineas == [_fila(9001)]


def test_f053_doble_anular_sentencia() -> None:
    assert _anular(_cli(), "9001", horide=None, antes=None) == {
        "op": "anular", "ide": 9001, "reside": REC, "fec": FECHA,
        "horide": 0, "antes": 0.0}


def test_f053_doble_anular_pone_a_cero_y_no_toca_nada_mas() -> None:
    previa = _fila(9001, synckey="porcentajes:7")
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[dict(previa)])
    assert cli.escribir([_anular(cli)]) == 1
    assert cli.lineas == [dict(previa, can=0.0, tot=0.0)]


@pytest.mark.parametrize("cambio", [
    {"ide": 9002}, {"reside": REC + 1}, {"fecha_int": FECHA + 1},
    {"horide": HE}, {"antes": 8.0011}, {"antes": 7.998}],
    ids=["otro-ide", "otro-recurso", "otro-dia", "otro-codigo",
         "can-cambio-arriba", "can-cambio-abajo"])
def test_f053_doble_anular_where_optimista(cambio) -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    assert cli.escribir([_anular(cli, **cambio)]) == 0
    assert cli.lineas == [_fila(9001)]


def test_f053_doble_anular_tolerancia_de_0_001() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    assert cli.escribir([_anular(cli, antes=8.0009)]) == 1
    assert cli.lineas[0]["can"] == 0


def test_f053_doble_anular_horide_y_can_nulos_son_0() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_fila(9001, horide=None, can=None)])
    assert cli.escribir([_anular(cli, horide=None, antes=None)]) == 1
    assert (cli.lineas[0]["can"], cli.lineas[0]["tot"]) == (0.0, 0.0)


def test_f053_doble_anular_no_toca_enlazadas_ni_partes_cerrados() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314"),
                       _parte(905, "PT26/00400", est=CERRADO)],
               lineas=[_fila(9001, enlazada=True), _fila(9002, 905)])
    assert cli.escribir([_anular(cli, 9001), _anular(cli, 9002),
                         _anular(cli, 9003)]) == 0
    assert [l["can"] for l in cli.lineas] == [8.0, 8.0]


def test_f053_doble_anular_dispara_el_cierre_de_la_ventana() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    assert cli.escribir([_anular(cli)]) == 0
    assert cli.partes[0]["est"] == CERRADO and cli.lineas[0]["can"] == 8.0


def test_f053_doble_lineas_traen_enlazada() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_fila(9001, enlazada=True), _fila(9002)])
    a, b = cli.lineas_existentes(HMO, [REC], [FECHA])
    assert (a.enlazada, b.enlazada) == (True, False)
    assert cli.lineas_por_ide([9001])[9001].enlazada is True
    sin_clave = _cli(lineas=[{k: v for k, v in _fila(9003).items()
                              if k != "enlazada"}])
    assert sin_clave.lineas_por_ide([9003])[9003].enlazada is False


# ================= Paso 7: que choca y que se omite (T4) ================= #

CLAVE = f"{REC}|{FECHA}|{HN}"
CLAVE_CIV = f"{REC}|{FECHA}|{CIV}"

MOTIVO_INC_9001 = (
    "incidencia_en_sigrid: la incidencia ya consta en Sigrid ese dia "
    "(linea 9001 del parte PT26/00314); no se duplica")
MOTIVO_ENL_9001 = (
    "linea_enlazada: la linea 9001 del parte PT26/00314 tiene ese dia las "
    "mismas horas y esta enlazada (albaran, factura, dedicacion o nomina); "
    "no se pone a 0. Corrigela en Sigrid")


def _lin(rid, fecha_int=FECHA, tipo="normal", horas=8.0) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int,
                        recurso_ide=REC, nombre=f"Persona {rid}",
                        tipo_hora=tipo, horas=horas)


def _inc(rid, fecha_int=FECHA) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int,
                        recurso_ide=REC, nombre=f"Persona {rid}",
                        es_incidencia=True, incidencia_rol="inicio",
                        hora_ide=CIV, hora_codigo="CIV")


def _pipeline(cli, lock=None) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(), lock=lock)


def _pf(cli, lineas):
    return _pipeline(cli).preflight(obra=_obra(), lineas=lineas)


def _accion(pf, rid):
    return next(a for a in pf.acciones if a.registro_id == rid)


def _abierto(*filas, cerrado=None) -> SigridFake:
    partes = [_parte(HMO, "PT26/00314")]
    if cerrado is not None:
        partes.append(_parte(905, "PT26/00400", est=cerrado))
    return _cli(partes=partes, lineas=[dict(f) for f in filas])


def test_f053_r5_linea_a_cero_no_es_conflicto_y_se_escribe() -> None:
    """Una manual a 0 (pisada antes) en el parte En registro no choca: la
    nueva se escribe sin conflicto ni pisadas."""
    cli = _abierto(_fila(9001, can=0.0))
    pf = _pf(cli, [_lin(1)])
    assert pf.conflictos == [] and _accion(pf, 1).accion == "escribir"
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [e["registro_id"] for e in r.escritas] == [1]
    assert r.pendientes_confirmacion == [] and r.omitidas == []


def test_f053_r5_ejemplo_2_solo_choca_la_que_tiene_horas() -> None:
    """Ejemplo 2: 9001 esta a 0 y `partes:501` tiene 8 h: al aprobar
    `partes:502` el conflicto solo lleva la de `partes:501`."""
    cli = _abierto(_fila(9001, can=0.0),
                   _fila(5001, synckey="partes:501", tex=""))
    (c,) = _pf(cli, [_lin(502)]).conflictos
    assert [ls.ide for ls in c.lineas] == [5001]
    assert c.clave == CLAVE and c.parte_cod == "PT26/00314"


def test_f053_r5_linea_a_cero_en_parte_cerrado_no_omite() -> None:
    """F-031 R11 solo protege horas: una linea a 0 en un parte cerrado no
    provoca `parte_cerrado`."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")],
               lineas=[_fila(9001, can=None), _fila(9002, can=0.0)])
    pf = _pf(cli, [_lin(1)])
    assert _accion(pf, 1).accion == "escribir" and pf.conflictos == []
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [(e["registro_id"], e["parte_cod"]) for e in r.escritas] == [
        (1, "PT26/00400")]


def test_f053_r5_horas_en_parte_cerrado_siguen_omitiendo() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")],
               lineas=[_fila(9001, can=-1.5)])
    a = _accion(_pf(cli, [_lin(1)]), 1)
    assert a.accion == "omitir" and a.motivo.startswith("parte_cerrado: ")


def test_f053_r6_ejemplo_3_incidencia_que_ya_consta() -> None:
    """Ejemplo 3: `CIV` del portal y ya hay una `CIV` manual (sin horas)
    ese dia: `omitido` sin conflicto ni sentencias."""
    cli = _abierto(_fila(9001, horide=CIV, can=0.0))
    pf = _pf(cli, [_inc(1)])
    a = _accion(pf, 1)
    assert (a.accion, a.motivo) == ("omitir", MOTIVO_INC_9001)
    assert pf.conflictos == []
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_inc(1)],
                                pisar_claves={CLAVE_CIV})
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_INC_9001}]
    assert r.escritas == [] and r.pisadas == []
    assert "escribir" not in cli.llamadas


def test_f053_r6_incidencia_contra_otra_del_portal_tambien() -> None:
    cli = _abierto(_fila(9001, horide=CIV, can=0.0, synckey="partes:480"),
                   _fila(9002, horide=CIV, can=0.0))
    a = _accion(_pf(cli, [_inc(1)]), 1)
    assert a.motivo == (
        "incidencia_en_sigrid: la incidencia ya consta en Sigrid ese dia "
        "(lineas 9001, 9002 del parte PT26/00314); no se duplica")


def test_f053_r6_incidencia_sin_choque_se_escribe() -> None:
    """Horas `HL01` o `HE01` ese dia: no chocan con la `CIV`."""
    cli = _abierto(_fila(9001, horide=HN), _fila(9002, horide=HE))
    pf = _pf(cli, [_inc(1)])
    assert _accion(pf, 1).accion == "escribir" and pf.conflictos == []


def test_f053_r6_la_omision_no_lleva_cuenta() -> None:
    cli = _abierto(_fila(9001, horide=CIV, can=0.0))
    a = _accion(_pf(cli, [_inc(1)]), 1)
    assert (a.caa_ide, a.caa_cod, a.caa_motivo, a.caa_aviso, a.caa_origen,
            a.caa_nota) == (0, None, None, None, None, None)


def test_f053_r7_ejemplo_4_choque_con_linea_enlazada() -> None:
    """Ejemplo 4: la que choca tiene `hdereside <> 0`: `omitido`, sin
    conflicto; nada se anula aunque se pida pisar."""
    cli = _abierto(_fila(9001, enlazada=True))
    pf = _pf(cli, [_lin(1)])
    a = _accion(pf, 1)
    assert (a.accion, a.motivo) == ("omitir", MOTIVO_ENL_9001)
    assert pf.conflictos == []
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_ENL_9001}]
    assert "escribir" not in cli.llamadas
    assert cli.lineas == [_fila(9001, enlazada=True)]


def test_f053_r7_basta_una_enlazada_y_solo_se_nombran_las_enlazadas() -> None:
    cli = _abierto(_fila(9001), _fila(9002, enlazada=True),
                   _fila(9003, enlazada=True))
    a = _accion(_pf(cli, [_lin(1)]), 1)
    assert a.motivo.startswith(
        "linea_enlazada: las lineas 9002, 9003 del parte PT26/00314 tienen ")


def test_f053_r7_enlazada_a_cero_no_choca() -> None:
    cli = _abierto(_fila(9001, can=0.0, enlazada=True))
    pf = _pf(cli, [_lin(1)])
    assert _accion(pf, 1).accion == "escribir" and pf.conflictos == []


def test_f053_r7_enlazada_con_otro_codigo_es_contexto() -> None:
    """R17: una enlazada de OTRO codigo ese dia no impide el conflicto."""
    cli = _abierto(_fila(9001), _fila(9002, horide=HE, enlazada=True))
    (c,) = _pf(cli, [_lin(1)]).conflictos
    assert [ls.ide for ls in c.lineas] == [9001]
    assert [ls.ide for ls in c.contexto] == [9002]


def test_f053_r8_parte_cerrado_prevalece_sobre_incidencia() -> None:
    cli = _abierto(_fila(9001, horide=CIV, can=0.0),
                   _fila(9002, 905, horide=CIV, can=0.0), cerrado=CERRADO)
    a = _accion(_pf(cli, [_inc(1)]), 1)
    assert a.motivo.startswith("parte_cerrado: ")


def test_f053_r8_parte_cerrado_prevalece_sobre_enlazada() -> None:
    cli = _abierto(_fila(9001, enlazada=True), _fila(9002, 905),
                   cerrado=IMPUTADO)
    a = _accion(_pf(cli, [_lin(1)]), 1)
    assert a.motivo.startswith("parte_cerrado: ")


def test_f053_r8_incidencia_prevalece_sobre_enlazada() -> None:
    cli = _abierto(_fila(9001, horide=CIV, can=0.0, enlazada=True))
    assert _accion(_pf(cli, [_inc(1)]), 1).motivo == MOTIVO_INC_9001


def test_f053_r8_enlazada_prevalece_sobre_conflicto() -> None:
    """Una enlazada y otra sin enlazar: ni conflicto parcial ni pisado; la
    linea de otro dia sigue su camino."""
    cli = _abierto(_fila(9001), _fila(9002, enlazada=True))
    pf = _pf(cli, [_lin(1), _lin(2, fecha_int=FECHA + 1)])
    assert _accion(pf, 1).motivo.startswith("linea_enlazada: ")
    assert _accion(pf, 2).accion == "escribir"
    assert pf.conflictos == []


def test_f053_r8_la_enlazada_de_un_parte_cerrado_sin_horas_no_cuenta() -> None:
    """R7 solo mira choques En registro y R11 solo horas."""
    cli = _abierto(_fila(9002, 905, can=0.0, enlazada=True),
                   cerrado=CERRADO)
    assert _accion(_pf(cli, [_lin(1)]), 1).accion == "escribir"
