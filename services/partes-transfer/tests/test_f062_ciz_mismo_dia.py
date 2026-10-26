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
