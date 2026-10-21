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
          fec=FECHA, can=8.0, enlazada=False, tex="nota-adm") -> dict:
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


# ============ Paso 9: anular en vez de borrar y relectura (T5) ============ #

def _espiar(cli) -> list[dict]:
    """Apunta cada sentencia que llega a `escribir`."""
    enviadas: list[dict] = []
    original = cli.escribir
    cli.escribir = lambda sts: (enviadas.extend(sts), original(sts))[1]
    return enviadas


def _pisar(cli, lineas=None, claves=(CLAVE,), lock=None):
    return _pipeline(cli, lock=lock).ejecutar(
        obra=_obra(), lineas=lineas or [_lin(501)], pisar_claves=set(claves))


def _sk(cli) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for fila in cli.lineas:
        if (fila.get("synckey") or "").startswith("partes:"):
            out.setdefault(fila["hmoide"], []).append(
                int(fila["synckey"].split(":")[1]))
    return out


def test_f053_r1_ejemplo_1_pisar_pone_a_cero_y_no_borra() -> None:
    """Ejemplo 1: la manual 9001 queda en Sigrid a 0 h / 0 EUR con su `tex`
    y su cuenta; entra `partes:501`; `anuladas = 1`."""
    previa = _fila(9001)
    cli = _abierto(previa)
    enviadas = _espiar(cli)
    r = _pisar(cli)
    assert [s["op"] for s in enviadas] == ["anular", "insert"]
    assert enviadas[0] == {"op": "anular", "ide": 9001, "reside": REC,
                           "fec": FECHA, "horide": HN, "antes": 8.0}
    assert enviadas[1]["pisadas"] == [9001]
    assert cli.lineas[0] == dict(previa, can=0.0, tot=0.0)
    assert _sk(cli) == {HMO: [501]}
    assert r.pisadas == [CLAVE] and r.anuladas == 1
    assert [e["registro_id"] for e in r.escritas] == [501]
    assert r.omitidas == []


def test_f053_r1_cada_pisada_con_lo_que_se_leyo() -> None:
    """Dos pisadas (manual con horas negativas y una ajena) de dos partes
    En registro: una sentencia `anular` por pisada con su `can` leido."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314"), _parte(905, "PT26/00400")],
               lineas=[_fila(9001, can=-2.0),
                       _fila(9002, 905, synckey="porcentajes:7")])
    enviadas = _espiar(cli)
    r = _pisar(cli)
    anular = [s for s in enviadas if s["op"] == "anular"]
    assert [(s["ide"], s["antes"]) for s in anular] == [(9002, 8.0),
                                                        (9001, -2.0)]
    assert r.anuladas == 2
    assert [(l["ide"], l["can"]) for l in cli.lineas[:2]] == [(9001, 0.0),
                                                              (9002, 0.0)]


def test_f053_r1_sin_confirmar_no_se_anula_nada() -> None:
    cli = _abierto(_fila(9001))
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(501)])
    assert [c.clave for c in r.pendientes_confirmacion] == [CLAVE]
    assert r.anuladas == 0 and "escribir" not in cli.llamadas
    assert cli.lineas == [_fila(9001)]


def test_f053_r12_anuladas_por_relectura_no_por_sentencia() -> None:
    """La pisada cambio a 6 h en la ventana: el `UPDATE` no entra, la nueva
    tampoco (F-034 R4) y `anuladas` = 0."""
    cli = _abierto(_fila(9001))
    original = cli.escribir

    def escribir(sts):
        cli.lineas[0]["can"] = 6.0      # Administracion, en la ventana
        return original(sts)
    cli.escribir = escribir
    r = _pisar(cli)
    assert r.anuladas == 0 and r.escritas == []
    assert cli.lineas[0]["can"] == 6.0 and _sk(cli) == {}


def test_f053_r12_pisada_ausente_al_releer_cuenta_como_anulada() -> None:
    cli = _abierto(_fila(9001))
    original = cli.escribir

    def escribir(sts):
        n = original(sts)
        cli.lineas = [l for l in cli.lineas if l["ide"] != 9001]
        return n
    cli.escribir = escribir
    assert _pisar(cli).anuladas == 1


def test_f053_r12_json_de_los_dos_canales_lleva_anuladas() -> None:
    from interface_adapters.queue.transfer_consumer import _resultado_fallido
    from interface_adapters.resultado_json import resultado_a_dict

    d = resultado_a_dict(_pisar(_abierto(_fila(9001))))
    assert d["anuladas"] == 1 and "borradas" not in d
    fallido = _resultado_fallido("sigrid caido")
    assert fallido["anuladas"] == 0 and "borradas" not in fallido
    assert set(fallido) - {"error"} <= set(d)


def test_f053_r13_info_por_pisada_sin_nombres_ni_tex(caplog) -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_fila(9001), _fila(9002, synckey="partes:480"),
                       _fila(9003, synckey="porcentajes:7")])
    with caplog.at_level("INFO"):
        r = _pisar(cli)
    assert r.anuladas == 3
    infos = sorted(rec.getMessage() for rec in caplog.records
                   if rec.getMessage().startswith("[registro] pisada a 0"))
    assert infos == [
        "[registro] pisada a 0 ide=9001 hmoide=900 can_antes=8.0 "
        "origen=manual registro_id=501",
        "[registro] pisada a 0 ide=9002 hmoide=900 can_antes=8.0 "
        "origen=partes registro_id=501",
        "[registro] pisada a 0 ide=9003 hmoide=900 can_antes=8.0 "
        "origen=ajena registro_id=501"]
    assert all(rec.levelname == "INFO" for rec in caplog.records
               if rec.getMessage().startswith("[registro] pisada a 0"))
    assert "Persona" not in caplog.text and "nota-adm" not in caplog.text
    assert "anuladas=3" in caplog.text and "borradas" not in caplog.text


def test_f053_r13_sin_info_si_no_se_anula(caplog) -> None:
    cli = _abierto(_fila(9001))
    cli.cerrar_al_escribir = {HMO: CERRADO}
    with caplog.at_level("INFO"):
        _pisar(cli)
    assert "pisada a 0" not in caplog.text


def test_f053_r13_varios_registros_del_mismo_conflicto(caplog) -> None:
    """Dos lineas del portal con la misma clave: un conflicto, una
    pisada; el INFO nombra los dos `registro_id`."""
    cli = _abierto(_fila(9001))
    with caplog.at_level("INFO"):
        r = _pisar(cli, lineas=[_lin(501, horas=4.0), _lin(502, horas=4.0)])
    assert r.anuladas == 1
    assert ("[registro] pisada a 0 ide=9001 hmoide=900 can_antes=8.0 "
            "origen=manual registro_id=501,502") in caplog.text


def test_f053_r14_falla_la_relectura_por_ide() -> None:
    cli = _abierto(_fila(9001))

    def falla(_ides):
        raise RuntimeError("sigrid-api caido al releer")
    cli.lineas_por_ide = falla
    with pytest.raises(RuntimeError, match="caido al releer"):
        _pisar(cli)


def test_f053_r1_todo_bajo_el_lock() -> None:
    import threading
    lock = threading.Lock()
    cli = _abierto(_fila(9001))
    cli.vigilar_lock(lock)
    assert _pisar(cli, lock=lock).anuladas == 1
    assert cli.ides_leidos == [[9001]]


# ============ Relectura: la pisada que no se puso a 0 (T6, R10) ============ #

MOTIVO_NO_ANULADA_9001 = (
    "pisada_no_anulada: la linea 9001 del parte PT26/00314 cambio antes de "
    "ponerla a 0; no se registra. Vuelve a aprobar para revisar el "
    "conflicto")


def test_f053_r10_motivo_texto_exacto() -> None:
    from application.services.parte_abierto import (
        MOTIVO_PISADA_NO_ANULADA,
        motivo_pisada_no_anulada,
    )
    assert MOTIVO_PISADA_NO_ANULADA == "pisada_no_anulada"
    assert motivo_pisada_no_anulada([9001], "PT26/00314") == (
        MOTIVO_NO_ANULADA_9001)
    assert motivo_pisada_no_anulada([9002, 9001], None) == (
        "pisada_no_anulada: las lineas 9001, 9002 del parte ? cambiaron "
        "antes de ponerlas a 0; no se registra. Vuelve a aprobar para "
        "revisar el conflicto")


@pytest.mark.parametrize("cod", ["PT26/" + "9" * 400, "x" * 300],
                         ids=["codigo-400", "texto-300"])
def test_f053_r10_r11_motivo_cabe_en_255(cod) -> None:
    from application.services.parte_abierto import motivo_pisada_no_anulada
    m = motivo_pisada_no_anulada([9001], cod)
    assert len(m) == 255 and m.startswith("pisada_no_anulada: la linea 9001")
    corto = motivo_pisada_no_anulada([9001], "PT26/00314")
    assert len(corto) < 255 and corto.isascii()


def test_f053_r10_pisadas_no_anuladas_solo_vivas_en_partes_abiertos() -> None:
    from application.services.parte_abierto import pisadas_no_anuladas
    from domain.models.registro_models import LineaSigrid

    def viva(ide, hmoide):
        return LineaSigrid(ide=ide, reside=REC, fecha_int=FECHA, horide=HN,
                           hora_codigo=None, can=8.0, tot=None, synckey=None,
                           hmoide=hmoide)
    vivas = {9001: viva(9001, HMO), 9002: viva(9002, 905),
             9003: viva(9003, 999), 9005: viva(9005, HMO)}
    estados = {HMO: REGISTRO, 905: CERRADO}
    assert pisadas_no_anuladas([9005, 9001, 9002, 9003, 9004], vivas,
                               estados, est_registro=REGISTRO) == [9005, 9001]
    assert pisadas_no_anuladas([9001], vivas, estados, est_registro=7) == []
    assert pisadas_no_anuladas([], vivas, estados,
                               est_registro=REGISTRO) == []


def test_f053_r10_ejemplo_5_la_pisada_cambio_en_la_ventana(caplog) -> None:
    """Ejemplo 5: Administracion cambia 9001 a 6 h entre la lectura y la
    escritura: el `UPDATE` afecta 0 filas, la nueva no entra y sale
    `pisada_no_anulada`; reaprobar vuelve a ensenar el conflicto con 6 h."""
    cli = _abierto(_fila(9001))
    original = cli.escribir

    def escribir(sts):
        cli.lineas[0]["can"] = 6.0
        return original(sts)
    cli.escribir = escribir
    with caplog.at_level("INFO"):
        r = _pisar(cli)
    assert r.escritas == [] and r.anuladas == 0
    assert r.omitidas == [{"registro_id": 501,
                           "motivo": MOTIVO_NO_ANULADA_9001}]
    (w,) = [rec for rec in caplog.records
            if rec.getMessage().startswith("[registro] pisada no anulada")]
    assert w.levelname == "WARNING"
    assert w.getMessage() == (
        "[registro] pisada no anulada obra=0100 periodo=2026/10 "
        "ides=[9001] registro_ids=[501]")
    assert not [rec for rec in caplog.records if rec.levelname == "ERROR"]
    assert "Persona" not in caplog.text
    cli.escribir = original
    (c,) = _pf(cli, [_lin(501)]).conflictos
    assert [(ls.ide, ls.can) for ls in c.lineas] == [(9001, 6.0)]


def test_f053_r10_pisada_enlazada_en_la_ventana() -> None:
    cli = _abierto(_fila(9001))
    original = cli.escribir

    def escribir(sts):
        cli.lineas[0]["enlazada"] = True
        return original(sts)
    cli.escribir = escribir
    (om,) = _pisar(cli).omitidas
    assert om["motivo"] == MOTIVO_NO_ANULADA_9001


def test_f053_r10_parte_de_la_pisada_cerrado_manda_parte_no_abierto() -> None:
    """F-034 R11 prevalece: si el parte de la pisada se cerro, el motivo es
    `parte_no_abierto`, no `pisada_no_anulada`."""
    cli = _abierto(_fila(9001))
    cli.cerrar_al_escribir = {HMO: CERRADO}
    (om,) = _pisar(cli).omitidas
    assert om["motivo"].startswith(
        "parte_no_abierto: el parte PT26/00314 ya no esta En registro "
        "(Cerrado)")


def test_f053_r10_pisada_viva_en_otro_parte_abierto_nombra_ese_parte() -> None:
    """La pisada vive en PT26/00400 (En registro) y cambio: el motivo nombra
    su parte, no el elegido."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314"), _parte(905, "PT26/00400")],
               lineas=[_fila(9001, 905)])
    original = cli.escribir

    def escribir(sts):
        cli.lineas[0]["can"] = 7.5
        return original(sts)
    cli.escribir = escribir
    (om,) = _pisar(cli).omitidas
    assert om["motivo"].startswith(
        "pisada_no_anulada: la linea 9001 del parte PT26/00400 cambio ")


def test_f053_r10_sin_pisada_viva_sigue_no_escrita(caplog) -> None:
    """La pisada si se puso a 0 pero la nueva no entro sin parte cerrado
    que lo explique: `no_escrita` de F-034 y su ERROR."""
    cli = _abierto(_fila(9001))
    original = cli.escribir
    cli.escribir = lambda sts: original(
        [s for s in sts if s["op"] != "insert"])
    with caplog.at_level("INFO"):
        r = _pisar(cli)
    (om,) = r.omitidas
    assert om["motivo"].startswith("no_escrita: ")
    assert r.anuladas == 1
    assert [rec for rec in caplog.records if rec.levelname == "ERROR"]
    assert "pisada no anulada" not in caplog.text
