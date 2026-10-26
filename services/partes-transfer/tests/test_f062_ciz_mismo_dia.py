# tests/test_f062_ciz_mismo_dia.py
"""F-062 · El inicio de una incidencia escribe CI* y CIZ el mismo dia (sv5).

  - Puro: `synckey_ciz_de`, `registro_de_synckey` con el sufijo `:ciz`
    (R20), `es_ciz_del_recurso` y `decidir_mismo_dia` (R11).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services import racha_ciz
from application.services.racha_ciz import (
    MOTIVO_POSTERIOR,
    MOTIVO_YA_EXISTE,
    decidir_mismo_dia,
    es_ciz_del_recurso,
    registro_de_synckey,
)
from domain.models.registro_models import LineaSigrid
from infrastructure.sigrid.sigrid_write_client import (
    SUFIJO_CIZ,
    synckey_ciz_de,
    synckey_de,
)

REC = 501
D = 20261004
H_CIV, H_CIZ = 30, 40


def _ls(ide, fec, *, reside=REC, hora="CIZ", can=0.0, tex=None,
        sk=None) -> LineaSigrid:
    return LineaSigrid(
        ide=ide, reside=reside, fecha_int=fec,
        horide=H_CIZ if hora == "CIZ" else H_CIV, hora_codigo=hora, can=can,
        tot=0.0, synckey=sk or f"partes:{ide}", nuestra=True, hmoide=901,
        tex=tex, pos=64)


# =============================== Puro =============================== #

def test_f062_r20_puro_synckey_ciz_de() -> None:
    assert SUFIJO_CIZ == ":ciz"
    assert synckey_ciz_de(7) == "partes:7:ciz"
    assert synckey_ciz_de("12") == "partes:12:ciz"
    assert synckey_ciz_de(7) == synckey_de(7) + SUFIJO_CIZ


@pytest.mark.parametrize("sk,esperado", [
    ("partes:7:ciz", None), ("partes:7", 7), (" partes:12 ", 12),
    ("partes:7:CIZ", None), ("partes:x", None), (None, None), ("", None),
    ("otro:7", None)])
def test_f062_r20_puro_registro_de_synckey_con_sufijo(sk, esperado) -> None:
    assert registro_de_synckey(sk) == esperado


def test_f062_r20_puro_registro_de_synckey_sufijo_explicito() -> None:
    """El sufijo se trata a proposito, no por el `ValueError` de `int`."""
    import inspect
    fuente = inspect.getsource(racha_ciz.registro_de_synckey)
    assert "SUFIJO_CIZ" in fuente


@pytest.mark.parametrize("cambio,esperado", [
    ({}, True), ({"reside": REC + 1}, False), ({"hora": "CIV"}, False),
    ({"can": 1.0}, False), ({"can": None}, True)])
def test_f062_r11_puro_es_ciz_del_recurso(cambio, esperado) -> None:
    assert es_ciz_del_recurso(_ls(1, D, **cambio), REC, None) is esperado


def test_f062_r11_puro_es_ciz_del_recurso_minusculas_y_blancos() -> None:
    ls = _ls(1, D)
    ls.hora_codigo = " ciz "
    assert es_ciz_del_recurso(ls, REC, None) is True


@pytest.mark.parametrize("tex,esperado", [
    (None, False), ("", False), ("x PRUEBA-IA x", True)])
def test_f062_r11_puro_es_ciz_del_recurso_en_pruebas(tex, esperado) -> None:
    assert es_ciz_del_recurso(_ls(1, D, tex=tex), REC,
                              "PRUEBA-IA") is esperado


def test_f062_r11_puro_sin_nada_se_escribe() -> None:
    assert decidir_mismo_dia(D, REC, [], None, marca_pruebas=None) is None


def test_f062_r11_puro_propia_ya_existe() -> None:
    propia = _ls(9, D, sk=synckey_ciz_de(4))
    assert decidir_mismo_dia(D, REC, [], propia,
                             marca_pruebas=None) == MOTIVO_YA_EXISTE == (
        "ya_existe")


def test_f062_r11_puro_ya_existe_manda_sobre_posterior() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1)], _ls(9, D),
                             marca_pruebas=None) == "ya_existe"


def test_f062_r11_puro_ciz_posterior() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 2)], None,
                             marca_pruebas=None) == MOTIVO_POSTERIOR == (
        "posterior")


@pytest.mark.parametrize("linea", [
    _ls(5, D), _ls(5, D - 1), _ls(5, D + 1, reside=REC + 1),
    _ls(5, D + 1, hora="CIV"), _ls(5, D + 1, can=2.0)])
def test_f062_r11_puro_lo_que_no_es_ciz_posterior_no_cuenta(linea) -> None:
    assert decidir_mismo_dia(D, REC, [linea], None,
                             marca_pruebas=None) is None


def test_f062_r11_puro_en_pruebas_sin_marca_no_cuenta() -> None:
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1)], None,
                             marca_pruebas="PRUEBA-IA") is None
    assert decidir_mismo_dia(D, REC, [_ls(5, D + 1, tex="PRUEBA-IA")], None,
                             marca_pruebas="PRUEBA-IA") == "posterior"


# ======================= Contrato y reglas (R6-R8) ======================= #

from application.pipelines.registro_pipeline import RegistroPipeline  # noqa: E402
from application.services.reglas_registro import ReglasRegistro  # noqa: E402
from domain.models.registro_models import (  # noqa: E402
    AccionLinea,
    FinMismoDia,
    LineaEntrada,
)
from fastapi.testclient import TestClient  # noqa: E402
from interface_adapters.api.app import build_app  # noqa: E402
from interface_adapters.queue import transfer_consumer  # noqa: E402
from tests.dobles import SettingsFake, SigridFake  # noqa: E402
from tests.test_f060_pipeline_mover import (  # noqa: E402
    HMO_OCT,
    HMO_SEP,
    HORAS,
    OBRA,
    _h,
    _obra,
    _parte,
    _PipelineEspia,
)

HN = 1
PRE_CIZ, PRE_CIV = 3.5, 2.0
HORAS_F062 = {REC: [_h(HN, "HL01", 15.0), _h(2, "HE01", 25.0),
                    _h(H_CIV, "CIV", PRE_CIV), _h(H_CIZ, "CIZ", PRE_CIZ)]}


def _inicio(rid, fecha_int, racha=(), *, ciz=True, rol="inicio",
            rec=REC) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int, recurso_ide=rec,
                        nombre=f"Persona {rid}", es_incidencia=True,
                        incidencia_codigo="V", incidencia_rol=rol,
                        hora_ide=H_CIV, hora_codigo="CIV",
                        racha_registro_ids=list(racha), ciz_mismo_dia=ciz)


def test_f062_r6_contrato_modelos_con_defecto() -> None:
    assert LineaEntrada(registro_id=1, fecha_int=D).ciz_mismo_dia is False
    acc = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=10,
                      fecha_int=D)
    assert acc.fin_mismo_dia is None
    fin = FinMismoDia(horide=H_CIZ, hora_codigo="CIZ", pre=1.0)
    assert (fin.caa_ide, fin.caa_cod) == (0, None)


PETICION = {
    "obra": {"ide": OBRA, "codigo": "0100", "nombre": "Obra Uno"},
    "lineas": [
        {"registro_id": 4, "fecha_int": D, "recurso_ide": REC,
         "es_incidencia": True, "incidencia_rol": "inicio",
         "hora_ide": H_CIV, "hora_codigo": "CIV",
         "racha_registro_ids": [5, 6], "ciz_mismo_dia": True},
        {"registro_id": 5, "fecha_int": D + 1, "recurso_ide": REC,
         "tipo_hora": "normal", "horas": 8.0}],
    "pisar_claves": [], "usuario": "ana",
}


def test_f062_r6_contrato_http_trae_ciz_mismo_dia() -> None:
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    r = TestClient(app).post("/api/registro/ejecutar", json=PETICION)
    assert r.status_code == 200
    assert [l.ciz_mismo_dia for l in espia.lineas] == [True, False]
    assert espia.lineas[0].racha_registro_ids == [5, 6]


def test_f062_r6_contrato_cola_trae_ciz_mismo_dia() -> None:
    _o, lineas = transfer_consumer._a_dominio(PETICION)
    assert [l.ciz_mismo_dia for l in lineas] == [True, False]


def test_f062_r8_contrato_payload_viejo_sin_la_clave() -> None:
    viejo = {"obra": PETICION["obra"],
             "lineas": [{"registro_id": 4, "fecha_int": D}]}
    _o, lineas = transfer_consumer._a_dominio(viejo)
    assert lineas[0].ciz_mismo_dia is False
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    TestClient(app).post("/api/registro/ejecutar", json=viejo)
    assert espia.lineas[0].ciz_mismo_dia is False


def test_f062_r6_reglas_el_inicio_lleva_su_ciz_hermano() -> None:
    a = ReglasRegistro(HORAS_F062, mover_ciz=True).decidir(_inicio(4, D))
    assert (a.accion, a.hora_codigo, a.hora_ide, a.can, a.tot) == (
        "escribir", "CIV", H_CIV, 0.0, 0.0)
    assert a.fin_mismo_dia == FinMismoDia(horide=H_CIZ, hora_codigo="CIZ",
                                          pre=PRE_CIZ)


def test_f062_r6_reglas_codigo_ciz_en_minusculas() -> None:
    horas = {REC: [_h(H_CIV, "CIV"), _h(H_CIZ, "ciz", PRE_CIZ)]}
    a = ReglasRegistro(horas, mover_ciz=True).decidir(_inicio(4, D))
    assert a.fin_mismo_dia.horide == H_CIZ


def test_f062_r7_recurso_sin_ciz_solo_el_ci_y_warning(caplog) -> None:
    horas = {REC: [_h(H_CIV, "CIV", PRE_CIV)]}
    with caplog.at_level("WARNING"):
        a = ReglasRegistro(horas, mover_ciz=True).decidir(_inicio(4, D))
    assert (a.accion, a.hora_codigo, a.fin_mismo_dia) == ("escribir", "CIV",
                                                          None)
    avisos = [r.getMessage() for r in caplog.records
              if "sin_ciz_mismo_dia" in r.getMessage()]
    assert avisos == ["[registro] sin_ciz_mismo_dia registro_id=4"]
    assert all(r.levelname == "WARNING" for r in caplog.records
               if "sin_ciz_mismo_dia" in r.getMessage())
    assert "Persona" not in caplog.text


@pytest.mark.parametrize("mover,ciz,rol", [
    (False, True, "inicio"), (True, False, "inicio"), (True, True, None),
    (True, True, "INICIO_X")])
def test_f062_r8_sin_hermano(mover, ciz, rol, caplog) -> None:
    with caplog.at_level("WARNING"):
        a = ReglasRegistro(HORAS_F062, mover_ciz=mover).decidir(
            _inicio(4, D, ciz=ciz, rol=rol))
    assert (a.accion, a.hora_codigo, a.fin_mismo_dia) == ("escribir", "CIV",
                                                          None)
    assert "sin_ciz_mismo_dia" not in caplog.text


def test_f062_r8_rol_inicio_con_blancos_y_mayusculas() -> None:
    a = ReglasRegistro(HORAS_F062, mover_ciz=True).decidir(
        _inicio(4, D, rol=" Inicio "))
    assert a.fin_mismo_dia is not None


def test_f062_r8_mover_ciz_apagado_por_defecto_en_las_reglas() -> None:
    a = ReglasRegistro(HORAS_F062).decidir(_inicio(4, D))
    assert a.fin_mismo_dia is None


@pytest.mark.parametrize("rol,accion,codigo", [
    ("fin", "escribir", "CIZ"), ("intermedio", "omitir", None)])
def test_f062_r8_fin_e_intermedio_no_llevan_hermano(rol, accion,
                                                    codigo) -> None:
    a = ReglasRegistro(HORAS_F062, mover_ciz=True).decidir(
        _inicio(4, D, rol=rol))
    assert (a.accion, a.hora_codigo, a.fin_mismo_dia) == (accion, codigo,
                                                          None)


def _st(*, mover=True, pruebas=False) -> SettingsFake:
    st = SettingsFake(obra_pruebas_forzar=pruebas)
    st.mover_ciz = mover
    return st


def _cli(*filas, partes=None) -> SigridFake:
    return SigridFake(
        obras={"0100": _obra(), "0404": _obra(cod="0404")},
        horas={k: list(v) for k, v in HORAS_F062.items()},
        partes=partes if partes is not None else [
            _parte(HMO_SEP, "PT26/00009", mes=9),
            _parte(HMO_OCT, "PT26/00010")],
        lineas=[dict(f) for f in filas])


def _pipe(cli, *, mover=True, pruebas=False, lock=None) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=_st(mover=mover,
                                                      pruebas=pruebas),
                            lock=lock)


def _pf(cli, lineas, **kw):
    return _pipe(cli, **kw).preflight(obra=_obra(), lineas=lineas)


def _acc(pf, rid) -> AccionLinea:
    return next(a for a in pf.acciones if a.registro_id == rid)


@pytest.mark.parametrize("mover", [True, False])
def test_f062_r6_preparar_pasa_mover_ciz_a_las_reglas(mover) -> None:
    a = _acc(_pf(_cli(), [_inicio(4, D)], mover=mover), 4)
    assert a.accion == "escribir"
    assert (a.fin_mismo_dia is not None) is mover


def test_f062_r8_settings_sin_el_ajuste_es_apagado() -> None:
    pipe = RegistroPipeline(cliente=_cli(), settings=SettingsFake())
    a = _acc(pipe.preflight(obra=_obra(), lineas=[_inicio(4, D)]), 4)
    assert a.fin_mismo_dia is None


# ================================ Doble ================================ #

def _stmt_inicio(cli, *, hmoide=HMO_OCT, rid=4, fecha_int=D, pos=64) -> dict:
    return cli.stmt_insert_inicio_con_fin(
        hmoide=hmoide, obra=_obra(), reside=REC, fecha_int=fecha_int,
        paride=33, ano=fecha_int // 10000, mes=(fecha_int // 100) % 100,
        tex="nota", pos=pos, horide=H_CIV, pre=PRE_CIV, caaide=702,
        synckey=synckey_de(rid), pos_fin=pos + 64, horide_fin=H_CIZ,
        pre_fin=PRE_CIZ, caaide_fin=703, synckey_fin=synckey_ciz_de(rid))


def test_f062_doble_inserta_dos_filas_con_ide_consecutivo() -> None:
    cli = _cli()
    assert cli.escribir([_stmt_inicio(cli)]) == 2
    ci, ciz = cli.lineas
    assert ciz["ide"] == ci["ide"] + 1
    assert (ci["synckey"], ci["horide"], ci["pre"], ci["caaide"],
            ci["pos"]) == ("partes:4", H_CIV, PRE_CIV, 702, 64)
    assert (ciz["synckey"], ciz["horide"], ciz["pre"], ciz["caaide"],
            ciz["pos"]) == ("partes:4:ciz", H_CIZ, PRE_CIZ, 703, 128)
    for f in (ci, ciz):
        assert (f["hmoide"], f["reside"], f["fec"], f["can"], f["tot"],
                f["paride"], f["ano"], f["mes"], f["tex"]) == (
            HMO_OCT, REC, D, 0.0, 0.0, 33, 2026, 10, "nota")


def test_f062_doble_parte_cerrado_ninguna_fila() -> None:
    cli = _cli(partes=[_parte(HMO_OCT, "PT26/00010", est=3)])
    assert cli.escribir([_stmt_inicio(cli)]) == 0
    assert cli.lineas == []


def test_f062_doble_parte_inexistente_ninguna_fila() -> None:
    cli = _cli(partes=[])
    assert cli.escribir([_stmt_inicio(cli)]) == 0 and cli.lineas == []


def test_f062_doble_hermano_ya_existe_solo_el_ci() -> None:
    previo = {"ide": 7001, "hmoide": HMO_OCT, "reside": REC, "fec": D,
              "horide": H_CIZ, "can": 0.0, "tot": 0.0, "pos": 10,
              "synckey": "partes:4:ciz"}
    cli = _cli(previo)
    assert cli.escribir([_stmt_inicio(cli)]) == 1
    assert [f["synckey"] for f in cli.lineas] == ["partes:4:ciz", "partes:4"]


def test_f062_doble_cuenta_para_el_cierre_en_la_ventana() -> None:
    cli = _cli()
    cli.cerrar_al_escribir = {HMO_OCT: 3}
    assert cli.escribir([_stmt_inicio(cli)]) == 0 and cli.lineas == []


# ===================== Paso 4b · cuenta del hermano (R9) ===================== #

from domain.models.registro_models import HoraRecurso, PartidaCuenta  # noqa: E402


def _hc(horide, cod, caa=None, pre=0.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre, caa_cod=caa,
                       defecto=False)


def _cli_cuentas(*, caa_ciz="R.CIZ1", partida=None) -> SigridFake:
    cli = _cli()
    cli.horas[REC] = [_hc(H_CIV, "CIV", "R.CIV1", PRE_CIV),
                      _hc(H_CIZ, "CIZ", caa_ciz, PRE_CIZ)]
    cli.cuentas = [(77, 1, 702, "C.CIV1"), (77, 1, 703, "C.CIZ1"),
                   (77, 1, 704, "C.CI55")]
    if partida is not None:
        cli.partidas = {33: partida}
    return cli


def _inicio_partida(rid=4, fecha_int=D, **kw) -> LineaEntrada:
    linea = _inicio(rid, fecha_int, **kw)
    linea.partida_ide = 33
    return linea


def test_f062_r9_cuenta_del_hermano_la_del_codigo_ciz() -> None:
    cli = _cli_cuentas()
    a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert (a.caa_ide, a.caa_cod) == (702, "C.CIV1")
    assert (a.fin_mismo_dia.caa_ide, a.fin_mismo_dia.caa_cod) == (703,
                                                                 "C.CIZ1")
    # R9: en la MISMA lectura de cuentas.
    assert [c["subcuentas"] for c in cli.cuentas_leidas] == [["CIV1",
                                                             "CIZ1"]]


def test_f062_r9_respaldo_de_la_partida_en_la_misma_lectura() -> None:
    cli = _cli_cuentas(caa_ciz=None,
                       partida=PartidaCuenta(ide=33, cod="P33",
                                             caa_cod="P.CI55"))
    a = _acc(_pf(cli, [_inicio_partida()]), 4)
    assert (a.caa_ide, a.caa_origen) == (702, "recurso")
    assert (a.fin_mismo_dia.caa_ide, a.fin_mismo_dia.caa_cod) == (704,
                                                                 "C.CI55")
    assert [p["parides"] for p in cli.partidas_leidas] == [[33]]
    assert [c["subcuentas"] for c in cli.cuentas_leidas] == [["CI55",
                                                             "CIV1"]]


def test_f062_r9_sin_cuenta_el_hermano_va_con_cero() -> None:
    cli = _cli_cuentas(caa_ciz=None)
    a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert a.caa_ide == 702
    assert (a.fin_mismo_dia.caa_ide, a.fin_mismo_dia.caa_cod) == (0, None)


def test_f062_r9_sin_hermano_no_pide_su_subcuenta() -> None:
    cli = _cli_cuentas()
    _pf(cli, [_inicio(4, D, ciz=False)])
    assert [c["subcuentas"] for c in cli.cuentas_leidas] == [["CIV1"]]


def test_f062_r9_los_recuentos_del_log_no_cuentan_el_hermano(caplog) -> None:
    cli = _cli_cuentas()
    with caplog.at_level("INFO"):
        _pf(cli, [_inicio(4, D)])
    assert ("[registro] cuentas obra=0100 ok=1 recurso_sin_cuenta=0 "
            "obra_sin_cuenta=0 cuenta_ambigua=0") in caplog.text
    assert ("[registro] origen cuenta obra=0100 recurso=1 partida=0 "
            "ninguna=0") in caplog.text


# ================= Pasos 6, 6 bis y 7 (R10-R12, R17, R18) ================= #

def _fila(ide, *, fec=D, sk=None, rid=None, hmoide=HMO_OCT, horide=H_CIZ,
          can=0.0, tex=None, reside=REC, pos=192, enlazada=False) -> dict:
    """Una linea de Sigrid. `sk` manda; si no, `partes:<rid>`; sin los dos,
    manual (sin synckey)."""
    if sk is None and rid is not None:
        sk = synckey_de(rid)
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can, "tot": 0.0,
            "pos": pos, "synckey": sk, "caaide": 703, "paride": 33,
            "tex": tex, "enlazada": enlazada, "ano": fec // 10000,
            "mes": (fec // 100) % 100, "obride": OBRA, "cenide": 77}


def _fin(rid, fecha_int, racha=(), *, rec=REC) -> LineaEntrada:
    return _inicio(rid, fecha_int, racha, ciz=False, rol="fin", rec=rec)


def test_f062_r10_ci_ya_registrado_sin_hermano_ni_lectura() -> None:
    cli = _cli(_fila(7001, rid=4, horide=H_CIV))
    a = _acc(_pf(cli, [_inicio(4, D, [5])]), 4)
    assert (a.accion, a.fin_mismo_dia) == ("ya_registrado", None)
    assert cli.racha_leidas == []


def test_f062_r10_ci_omitido_en_el_paso_7_sin_hermano() -> None:
    """Un CIV manual el dia D: el CI* se omite (`incidencia_en_sigrid`) y
    con el su hermano."""
    cli = _cli(_fila(7100, horide=H_CIV))
    a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert a.accion == "omitir"
    assert a.motivo.startswith("incidencia_en_sigrid: ")
    assert a.fin_mismo_dia is None


def test_f062_r11_una_lectura_con_el_tramo_y_la_propia() -> None:
    cli = _cli()
    a = _acc(_pf(cli, [_inicio(4, D, [5, 6])]), 4)
    assert a.fin_mismo_dia is not None and a.fin_mismo_dia.horide == H_CIZ
    assert cli.racha_leidas == [["partes:4:ciz", "partes:5", "partes:5:ciz",
                                 "partes:6", "partes:6:ciz"]]
    assert cli.estados_leidos == []          # sin `fin`, no hacen falta


def test_f062_r11_sin_tramo_lee_solo_la_propia() -> None:
    cli = _cli()
    _pf(cli, [_inicio(4, D)])
    assert cli.racha_leidas == [["partes:4:ciz"]]


def test_f062_r11_la_misma_lectura_que_los_fines() -> None:
    cli = _cli(_fila(7001, fec=D + 10, rid=13, reside=REC + 1))
    cli.horas[REC + 1] = list(HORAS_F062[REC])
    pf = _pf(cli, [_inicio(4, D, [5]), _fin(14, D + 11, [13], rec=REC + 1)])
    assert len(cli.racha_leidas) == 1 and len(cli.estados_leidos) == 1
    assert cli.racha_leidas[0] == ["partes:13", "partes:13:ciz",
                                   "partes:4:ciz", "partes:5",
                                   "partes:5:ciz"]
    assert cli.estados_leidos == [[HMO_OCT]]
    assert _acc(pf, 14).mover.ide == 7001
    assert _acc(pf, 4).fin_mismo_dia is not None


@pytest.mark.parametrize("fila", [
    _fila(7001, fec=D + 2, rid=6),
    _fila(7001, fec=D + 1, sk="partes:5:ciz")])
def test_f062_r11_ciz_posterior_sin_hermano(fila, caplog) -> None:
    cli = _cli(fila)
    with caplog.at_level("INFO"):
        a = _acc(_pf(cli, [_inicio(4, D, [5, 6])]), 4)
    assert (a.accion, a.hora_codigo, a.fin_mismo_dia) == ("escribir", "CIV",
                                                          None)
    assert ("[registro] ciz_mismo_dia_omitido registro_id=4 "
            "motivo=posterior") in caplog.text
    assert "Persona" not in caplog.text


def test_f062_r11_propia_ya_existe_sin_hermano(caplog) -> None:
    """El CI* no esta (borrado en Sigrid) pero su hermano si."""
    cli = _cli(_fila(7001, sk="partes:4:ciz"))
    with caplog.at_level("INFO"):
        a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert (a.accion, a.fin_mismo_dia) == ("escribir", None)
    assert ("[registro] ciz_mismo_dia_omitido registro_id=4 "
            "motivo=ya_existe") in caplog.text


@pytest.mark.parametrize("fila", [
    _fila(7001, fec=D + 1, rid=5, reside=REC + 1),
    _fila(7001, fec=D + 1, rid=5, horide=H_CIV),
    _fila(7001, fec=D + 1, rid=5, can=4.0),
    _fila(7001, fec=D - 1, rid=5)])
def test_f062_r11_lo_que_no_es_ciz_posterior_no_lo_impide(fila,
                                                          caplog) -> None:
    cli = _cli(fila)
    with caplog.at_level("INFO"):
        a = _acc(_pf(cli, [_inicio(4, D, [5])]), 4)
    assert a.fin_mismo_dia is not None
    assert "ciz_mismo_dia_omitido" not in caplog.text


@pytest.mark.parametrize("tex,hermano", [(None, True), ("PRUEBA-IA", False)])
def test_f062_r11_en_pruebas_solo_cuenta_con_la_marca(tex, hermano) -> None:
    cli = _cli(_fila(7001, fec=D + 1, rid=5, tex=tex))
    pipe = _pipe(cli, pruebas=True)
    a = _acc(pipe.preflight(obra=_obra(), lineas=[_inicio(4, D, [5])]), 4)
    assert (a.fin_mismo_dia is not None) is hermano


def test_f062_r11_apagado_no_lee() -> None:
    cli = _cli(_fila(7001, fec=D + 1, rid=5))
    _pf(cli, [_inicio(4, D, [5])], mover=False)
    assert cli.racha_leidas == []


def test_f062_r12_ciz_ajeno_el_dia_d_sin_hermano(caplog) -> None:
    cli = _cli(_fila(7100))                 # CIZ manual, sin synckey
    with caplog.at_level("INFO"):
        a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert (a.accion, a.hora_codigo, a.fin_mismo_dia) == ("escribir", "CIV",
                                                          None)
    assert ("[registro] ciz_mismo_dia_omitido registro_id=4 "
            "motivo=ciz_en_sigrid") in caplog.text


def test_f062_r12_ciz_ajeno_en_un_parte_cerrado_del_periodo() -> None:
    cli = _cli(_fila(7100, hmoide=HMO_SEP + 50),
               partes=[_parte(HMO_SEP + 50, "PT26/00008", est=3),
                       _parte(HMO_OCT, "PT26/00010")])
    a = _acc(_pf(cli, [_inicio(4, D)]), 4)
    assert (a.accion, a.fin_mismo_dia) == ("escribir", None)


def test_f062_r12_ciz_de_otra_synckey_nuestra_tambien_cuenta() -> None:
    cli = _cli(_fila(7100, rid=99))
    assert _acc(_pf(cli, [_inicio(4, D)]), 4).fin_mismo_dia is None


@pytest.mark.parametrize("fila", [
    _fila(7100, horide=HN, can=8.0), _fila(7100, fec=D + 1),
    _fila(7100, reside=REC + 1)])
def test_f062_r12_otra_hora_otro_dia_u_otro_recurso_no_cuenta(fila) -> None:
    cli = _cli(fila)
    assert _acc(_pf(cli, [_inicio(4, D)]), 4).fin_mismo_dia is not None


def test_f062_r17_preflight_igual_con_y_sin_hermano() -> None:
    respuestas = []
    for ciz in (True, False):
        cli = _cli()
        app = build_app(_st(), pipeline=_pipe(cli))  # type: ignore[arg-type]
        cuerpo = dict(PETICION, lineas=[dict(PETICION["lineas"][0],
                                             ciz_mismo_dia=ciz),
                                        PETICION["lineas"][1]])
        r = TestClient(app).post("/api/registro/preflight", json=cuerpo)
        assert r.status_code == 200
        respuestas.append(r.json())
    con, sin = respuestas
    assert con == sin
    assert con["resumen"] == {"escribir": 2, "omitir": 0, "ya_registrado": 0,
                              "conflictos": 0}
    assert all("fin_mismo_dia" not in a for a in con["acciones"])
    assert [(a["registro_id"], a["hora_codigo"]) for a in con["acciones"]]         == [(4, "CIV"), (5, "HL01")]


def test_f062_r17_el_hermano_no_es_una_accion() -> None:
    pf = _pf(_cli(), [_inicio(4, D)])
    assert (pf.n_escribir, pf.n_omitir, pf.n_ya, len(pf.acciones)) == (
        1, 0, 0, 1)


def test_f062_r18_el_fin_mueve_el_hermano_del_inicio() -> None:
    cli = _cli(_fila(7001, fec=D, rid=4, horide=H_CIV),
               _fila(7002, fec=D, sk="partes:4:ciz"))
    a = _acc(_pf(cli, [_fin(5, D + 1, [4])]), 5)
    assert a.accion == "escribir" and a.mover.ide == 7002
    assert cli.racha_leidas == [["partes:4", "partes:4:ciz"]]


def test_f062_r18_hermano_posterior_es_intermedio() -> None:
    cli = _cli(_fila(7002, fec=D + 2, sk="partes:6:ciz"))
    a = _acc(_pf(cli, [_fin(5, D + 1, [4, 6])]), 5)
    assert a.accion == "omitir" and "2026-10-06" in a.motivo


# ============ Paso 9, relectura y escenarios (R13, R15, R16, R19-R23) ============ #

HMO_NOV = 902


def _espiar(cli) -> list[dict]:
    enviadas: list[dict] = []
    original = cli.escribir
    cli.escribir = lambda sts: (enviadas.extend(sts), original(sts))[1]
    return enviadas


def _ejecutar(cli, lineas, **kw):
    return _pipe(cli, **kw).ejecutar(obra=_obra(), lineas=lineas)


def _por_sk(cli) -> dict[str, dict]:
    return {f["synckey"]: f for f in cli.lineas}


def _trabajo(rid, fecha_int) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int, recurso_ide=REC,
                        nombre=f"Persona {rid}", tipo_hora="normal",
                        horas=8.0, hora_ide=HN)


def test_f062_r13_una_sentencia_con_las_dos_filas() -> None:
    cli = _cli()
    enviadas = _espiar(cli)
    linea = _inicio(4, D)
    linea.partida_ide = 33
    r = _ejecutar(cli, [linea])
    (st,) = enviadas
    assert st["op"] == "insert_inicio_con_fin"
    ci, ciz = st["filas"]
    assert (ci["synckey"], ci["horide"], ci["pre"], ci["pos"]) == (
        "partes:4", H_CIV, PRE_CIV, 64)
    assert (ciz["synckey"], ciz["horide"], ciz["pre"], ciz["pos"]) == (
        "partes:4:ciz", H_CIZ, PRE_CIZ, 128)
    assert (ci["paride"], ci["fec"], ci["tex"]) == (33, D, None)
    assert st["guarda_hmoide"] == HMO_OCT and r.ok


def test_f062_r13_cuentas_de_cada_fila() -> None:
    cli = _cli_cuentas()
    enviadas = _espiar(cli)
    _ejecutar(cli, [_inicio(4, D)])
    ci, ciz = enviadas[0]["filas"]
    assert (ci["caaide"], ciz["caaide"]) == (702, 703)


def test_f062_r13_pos_comparte_contador_con_los_insert() -> None:
    cli = _cli(_fila(7001, fec=D - 3, rid=900, horide=HN, can=8.0, pos=640,
                     reside=REC + 9))
    _ejecutar(cli, [_inicio(4, D), _trabajo(5, D + 1)])
    sk = _por_sk(cli)
    assert (sk["partes:4"]["pos"], sk["partes:4:ciz"]["pos"],
            sk["partes:5"]["pos"]) == (704, 768, 832)


def test_f062_r13_en_pruebas_las_dos_filas_llevan_la_marca() -> None:
    cli = _cli()
    r = _pipe(cli, pruebas=True).ejecutar(obra=_obra(cod="0404"),
                                          lineas=[_inicio(4, D)])
    assert r.ok
    assert [f["tex"] for f in cli.lineas] == ["PRUEBA-IA", "PRUEBA-IA"]


def test_f062_r15_escrita_con_ciz_hmores_ide() -> None:
    cli = _cli()
    r = _ejecutar(cli, [_inicio(4, D)])
    (e,) = r.escritas
    sk = _por_sk(cli)
    assert e["hmores_ide"] == sk["partes:4"]["ide"]
    assert e["ciz_hmores_ide"] == sk["partes:4:ciz"]["ide"] == (
        e["hmores_ide"] + 1)
    assert e["hora_codigo"] == "CIV" and "movida_de" not in e
    assert r.omitidas == [] and r.ya_registradas == []


def test_f062_r15_relectura_en_una_sola_lectura() -> None:
    cli = _cli()
    pedidas: list[list[str]] = []
    original = cli.lineas_por_synckey

    def espia(claves):
        pedidas.append(sorted(claves))
        return original(claves)
    cli.lineas_por_synckey = espia
    _ejecutar(cli, [_inicio(4, D), _trabajo(5, D + 1)])
    assert pedidas[-1] == ["partes:4", "partes:4:ciz", "partes:5"]


def test_f062_r15_hermano_que_no_esta_warning(caplog) -> None:
    cli = _cli()
    original = cli.escribir

    def escribir(sts):
        n = original(sts)
        cli.lineas[:] = [f for f in cli.lineas
                         if f["synckey"] != "partes:4:ciz"]
        return n
    cli.escribir = escribir
    with caplog.at_level("INFO"):
        r = _ejecutar(cli, [_inicio(4, D)])
    (e,) = r.escritas
    assert e["registro_id"] == 4 and "ciz_hmores_ide" not in e
    avisos = [x for x in caplog.records
              if "ciz_mismo_dia_no_escrito" in x.getMessage()]
    assert [(x.levelname, x.getMessage()) for x in avisos] == [
        ("WARNING", "[registro] ciz_mismo_dia_no_escrito registro_id=4")]
    assert "ciz mismo dia ide=" not in caplog.text


def test_f062_r15_hermano_en_otro_parte_no_cuenta(caplog) -> None:
    cli = _cli()
    original = cli.escribir

    def escribir(sts):
        n = original(sts)
        _por_sk(cli)["partes:4:ciz"]["hmoide"] = HMO_SEP
        return n
    cli.escribir = escribir
    with caplog.at_level("WARNING"):
        (e,) = _ejecutar(cli, [_inicio(4, D)]).escritas
    assert "ciz_hmores_ide" not in e
    assert "ciz_mismo_dia_no_escrito registro_id=4" in caplog.text


def test_f062_r15_ci_no_confirmado_lo_decide_el_ci(caplog) -> None:
    cli = _cli()
    cli.cerrar_al_escribir = {HMO_OCT: 3}
    with caplog.at_level("INFO"):
        r = _ejecutar(cli, [_inicio(4, D)])
    assert r.escritas == [] and cli.lineas == []
    (o,) = r.omitidas
    assert o["motivo"].startswith("parte_no_abierto: el parte PT26/00010")
    assert "ciz_mismo_dia_no_escrito" not in caplog.text


def test_f062_r16_info_del_hermano_escrito_sin_nombres(caplog) -> None:
    cli = _cli()
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_inicio(4, D)])
    ciz = _por_sk(cli)["partes:4:ciz"]
    escritos = [x.getMessage() for x in caplog.records
                if "ciz mismo dia" in x.getMessage()]
    assert escritos == [f"[registro] ciz mismo dia ide={ciz['ide']} "
                        f"hmoide={HMO_OCT} fecha={D} registro_id=4"]
    assert "Persona" not in caplog.text


def test_f062_r16_sin_hermano_no_hay_info(caplog) -> None:
    cli = _cli()
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_inicio(4, D, ciz=False)])
    assert "ciz mismo dia" not in caplog.text
    assert "ciz_mismo_dia" not in caplog.text


def test_f062_r17_el_resultado_no_cuenta_el_hermano() -> None:
    r = _ejecutar(_cli(), [_inicio(4, D)])
    assert [e["registro_id"] for e in r.escritas] == [4]
    assert r.omitidas == [] and r.ya_registradas == []
    assert r.pendientes_confirmacion == [] and r.pisadas == []


def test_f062_r19_escenario_dia_a_dia(caplog) -> None:
    """M2: V 1-4 y trabajo el 5, aprobados de uno en uno. CIV + CIZ el 1;
    el CIZ (el mismo `ide`) pasa al 2, 3 y 4; el 5 no lo toca."""
    cli = _cli()
    r1 = _ejecutar(cli, [_inicio(1, 20261001, [])])
    (e1,) = r1.escritas
    iz = e1["ciz_hmores_ide"]
    with caplog.at_level("INFO"):
        r2 = _ejecutar(cli, [_fin(2, 20261002, [1])])
    (e2,) = r2.escritas
    assert "movida_de" not in e2 and e2["hmores_ide"] == iz
    assert (f"[registro] ciz movido ide={iz} hmoide={HMO_OCT}->{HMO_OCT} "
            "fecha=20261001->20261002 synckey=partes:1:ciz->partes:2"
            ) in caplog.text
    r3 = _ejecutar(cli, [_fin(3, 20261003, [1, 2])])
    assert [(e["movida_de"], e["hmores_ide"]) for e in r3.escritas] == [
        (2, iz)]
    r4 = _ejecutar(cli, [_fin(4, 20261004, [1, 2, 3])])
    assert [(e["movida_de"], e["hmores_ide"]) for e in r4.escritas] == [
        (3, iz)]
    _ejecutar(cli, [_trabajo(5, 20261005)])
    sk = _por_sk(cli)
    assert sorted(sk) == ["partes:1", "partes:4", "partes:5"]
    assert (sk["partes:4"]["ide"], sk["partes:4"]["fec"],
            sk["partes:4"]["horide"]) == (iz, 20261004, H_CIZ)
    assert sk["partes:1"]["horide"] == H_CIV
    assert len([f for f in cli.lineas if f["horide"] == H_CIZ]) == 1


def test_f062_r19_info_del_movido_normal_sigue_igual(caplog) -> None:
    cli = _cli(_fila(7001, fec=20261002, rid=2))
    with caplog.at_level("INFO"):
        _ejecutar(cli, [_fin(3, 20261003, [1, 2])])
    assert ("[registro] ciz movido ide=7001 hmoide=901->901 "
            "fecha=20261002->20261003 registro_id=2->3") in caplog.text


def test_f062_r21_un_dia_y_trabajo_el_hermano_no_se_toca() -> None:
    """M1: V el 1 y 8 h el 2: CIV y CIZ el 1; el 2 escribe su HL."""
    cli = _cli()
    _ejecutar(cli, [_inicio(1, 20261001)])
    r = _ejecutar(cli, [_trabajo(2, 20261002)])
    assert [e["hora_codigo"] for e in r.escritas] == ["HL01"]
    sk = _por_sk(cli)
    assert sk["partes:1:ciz"]["fec"] == 20261001
    assert sorted(sk) == ["partes:1", "partes:1:ciz", "partes:2"]


def test_f062_r21_cambio_de_mes_mueve_el_hermano_de_parte() -> None:
    """M3: V el 31 y el 1 del mes siguiente: el hermano (mismo `ide`) pasa
    al parte del otro mes y el 31 conserva su CI*."""
    cli = _cli(partes=[_parte(HMO_OCT, "PT26/00010"),
                       _parte(HMO_NOV, "PT26/00011", mes=11)])
    (e1,) = _ejecutar(cli, [_inicio(31, 20261031)]).escritas
    assert e1["hmoide"] == HMO_OCT
    (e2,) = _ejecutar(cli, [_fin(32, 20261101, [31])]).escritas
    assert "movida_de" not in e2 and e2["hmores_ide"] == e1["ciz_hmores_ide"]
    sk = _por_sk(cli)
    assert (sk["partes:32"]["hmoide"], sk["partes:32"]["fec"],
            sk["partes:32"]["mes"]) == (HMO_NOV, 20261101, 11)
    assert sk["partes:31"]["hmoide"] == HMO_OCT
    assert "partes:31:ciz" not in sk


def test_f062_r21_todo_de_una_vez_sin_hermano() -> None:
    """M4: sv4 manda 1 inicio SIN `ciz_mismo_dia` (su fin viaja, R2), 2 y
    3 intermedio y 4 fin: CIV el 1 y CIZ el 4, ninguna `:ciz`."""
    cli = _cli()
    lineas = [_inicio(1, 20261001, [2, 3, 4], ciz=False),
              _fin(2, 20261002), _fin(3, 20261003),
              _fin(4, 20261004, [1, 2, 3])]
    lineas[1].incidencia_rol = lineas[2].incidencia_rol = "intermedio"
    r = _ejecutar(cli, lineas)
    assert sorted((e["registro_id"], e["hora_codigo"])
                  for e in r.escritas) == [(1, "CIV"), (4, "CIZ")]
    assert sorted(_por_sk(cli)) == ["partes:1", "partes:4"]


def test_f062_r11_escenario_desordenado(caplog) -> None:
    """M5: V 1-3; se aprueba el 2 (CIZ el 2), luego el 1 (solo CIV:
    `posterior`) y luego el 3 (el CIZ pasa al 3)."""
    cli = _cli()
    (e2,) = _ejecutar(cli, [_fin(2, 20261002, [1, 3])]).escritas
    with caplog.at_level("INFO"):
        r1 = _ejecutar(cli, [_inicio(1, 20261001, [2, 3])])
    assert [e["hora_codigo"] for e in r1.escritas] == ["CIV"]
    assert "ciz_hmores_ide" not in r1.escritas[0]
    assert "motivo=posterior" in caplog.text
    (e3,) = _ejecutar(cli, [_fin(3, 20261003, [1, 2])]).escritas
    assert (e3["movida_de"], e3["hmores_ide"]) == (2, e2["hmores_ide"])
    assert sorted(_por_sk(cli)) == ["partes:1", "partes:3"]


def test_f062_r26_borrado_sigrid_reaprobado_no_duplica_el_hermano() -> None:
    """Administracion borro el CI* del 1 (su hermano sigue): al reaprobar
    se reescribe el CI* y el hermano no (`ya_existe`)."""
    cli = _cli(_fila(7002, fec=20261001, sk="partes:1:ciz"))
    enviadas = _espiar(cli)
    (e,) = _ejecutar(cli, [_inicio(1, 20261001)]).escritas
    assert [s["op"] for s in enviadas] == ["insert"]
    assert "ciz_hmores_ide" not in e
    assert len([f for f in cli.lineas if f["horide"] == H_CIZ]) == 1


def test_f062_r26_borrado_sigrid_con_el_hermano_ya_movido() -> None:
    cli = _cli(_fila(7002, fec=20261003, rid=3))
    (e,) = _ejecutar(cli, [_inicio(1, 20261001, [2, 3])]).escritas
    assert e["hora_codigo"] == "CIV" and "ciz_hmores_ide" not in e
    assert len(cli.lineas) == 2


def test_f062_r13_carrera_el_hermano_ya_entro_solo_el_ci() -> None:
    """Otra escritura pone `partes:4:ciz` entre la lectura y el INSERT: el
    `NOT EXISTS` deja solo el CI*."""
    cli = _cli()
    original = cli.escribir

    def escribir(sts):
        cli.lineas.append(_fila(7300, sk="partes:4:ciz"))
        return original(sts)
    cli.escribir = escribir
    r = _ejecutar(cli, [_inicio(4, D)])
    assert [e["registro_id"] for e in r.escritas] == [4]
    assert len([f for f in cli.lineas
                if f["synckey"] == "partes:4:ciz"]) == 1


def test_f062_r13_reentrega_es_ya_registrado() -> None:
    cli = _cli()
    _ejecutar(cli, [_inicio(4, D)])
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_inicio(4, D)])
    assert r.ya_registradas == [4] and r.escritas == [] and enviadas == []
    assert len(cli.lineas) == 2


def test_f062_r22_racha_sin_hermano_el_fin_crea_su_ciz() -> None:
    """DA6: un inicio escrito antes de encender (solo CI*): su `fin` crea
    el CIZ como R16 de F-060."""
    cli = _cli(_fila(7001, fec=20261001, rid=1, horide=H_CIV))
    enviadas = _espiar(cli)
    (e,) = _ejecutar(cli, [_fin(2, 20261002, [1])]).escritas
    assert [s["op"] for s in enviadas] == ["insert"]
    assert "movida_de" not in e
    assert _por_sk(cli)["partes:2"]["horide"] == H_CIZ


def test_f062_r23_hermano_en_parte_cerrado_se_omite() -> None:
    cli = _cli(_fila(7002, fec=20260930, sk="partes:30:ciz", hmoide=HMO_SEP),
               partes=[_parte(HMO_SEP, "PT26/00009", mes=9, est=3),
                       _parte(HMO_OCT, "PT26/00010")])
    r = _ejecutar(cli, [_fin(31, 20261001, [30])])
    assert r.escritas == []
    (o,) = r.omitidas
    assert o["motivo"].startswith("ciz_en_parte_cerrado: ")
    assert "linea 7002" in o["motivo"]
    assert _por_sk(cli)["partes:30:ciz"]["fec"] == 20260930


def test_f062_r19_en_pruebas_mueve_el_hermano_con_marca() -> None:
    cli = _cli(_fila(7002, fec=20261001, sk="partes:1:ciz", tex="PRUEBA-IA"))
    r = _pipe(cli, pruebas=True).ejecutar(
        obra=_obra(cod="0404"), lineas=[_fin(2, 20261002, [1])])
    (e,) = r.escritas
    assert e["hmores_ide"] == 7002 and "movida_de" not in e


def test_f062_r19_en_pruebas_sin_marca_crea_otro() -> None:
    cli = _cli(_fila(7002, fec=20261001, sk="partes:1:ciz"))
    r = _pipe(cli, pruebas=True).ejecutar(
        obra=_obra(cod="0404"), lineas=[_fin(2, 20261002, [1])])
    (e,) = r.escritas
    assert e["hmores_ide"] != 7002
    assert _por_sk(cli)["partes:1:ciz"]["fec"] == 20261001
