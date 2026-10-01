# tests/test_f021_pipeline_cuenta.py
"""F-021 · R8, R10-R18: la cuenta analitica en el pipeline de sv5.

`preparar` resuelve la cuenta de cada accion `escribir` (fuera del lock,
tras las reglas) con UNA lectura de las cuentas del centro de la obra
destino; `registrar` la copia al `INSERT` y a `escritas`. Una linea sin
cuenta se escribe igual con `caaide = 0`.

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (centros,
subcuentas y nombres inventados).
"""
from __future__ import annotations

import logging

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
)
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests.dobles import SettingsFake, SigridFake

FECHA = 20260302
CEN_OBRA, CEN_PRUEBAS = 77, 88
HL, HE, CIV, CIZ = 1, 2, 3, 4


def _obra(ide, cod, cenide, empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    setattr(o, "cenide", cenide)        # como lo deja el cliente real
    return o


def _h(horide, cod, caa=None, defecto=False) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=10.0,
                       caa_cod=caa, defecto=defecto)


HORAS = {
    # Cuenta por tipo de hora; las incidencias sin cuenta (van al defecto).
    501: [_h(HL, "HL01", "00000.LAB", True), _h(HE, "HE01", "00000.EXT"),
          _h(CIV, "CIV"), _h(CIZ, "CIZ")],
    # La obra no tiene su subcuenta (R5).
    502: [_h(HL, "HL01", "00000.SINOBRA", True), _h(HE, "HE01")],
    # Recurso sin ninguna cuenta (empresa sin analitica, R3).
    503: [_h(HL, "HL01", None, True), _h(HE, "HE01")],
    # Dos cuentas del centro con la misma subcuenta (R6).
    504: [_h(HL, "HL01", "00000.DOS", True), _h(HE, "HE01")],
    # Mensual sin HE: se OMITE; su cuenta no debe pedirse (R10, R16).
    505: [_h(HL, "HL01", "00000.ZZZ", True)],
}

CUENTAS = [
    (CEN_OBRA, 1, 701, "0100.LAB"), (CEN_OBRA, 1, 702, "0100.EXT"),
    (CEN_OBRA, 1, 703, "0100.DOS"), (CEN_OBRA, 1, 704, "0100. DOS"),
    (CEN_OBRA, 1, 705, "0100.ZZZ"),
    (CEN_OBRA, 28, 709, "0100.LAB"),          # otra empresa: no vale
    (CEN_PRUEBAS, 1, 801, "0404.LAB"), (CEN_PRUEBAS, 1, 802, "0404.EXT"),
]


def _cli(obra=None, **kw) -> SigridFake:
    obra = obra or _obra(10, "0100", CEN_OBRA)
    return SigridFake(obras={obra.codigo: obra,
                             "0404": _obra(99, "0404", CEN_PRUEBAS)},
                      horas=HORAS, cuentas=CUENTAS, **kw)


def _lin(rid, recurso=501, tipo="normal", **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        tipo_hora=tipo, horas=8.0, **kw)


def _incidencia(rid, recurso=501) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        es_incidencia=True, incidencia_rol="inicio",
                        hora_ide=CIV, hora_codigo="CIV")


def _pipeline(cli, **st) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(**st))


def _caa(acciones) -> dict:
    return {a.registro_id: (a.caa_ide, a.caa_cod, a.caa_motivo)
            for a in acciones}


TODAS = [_lin(1), _lin(2, tipo="extra"), _lin(3, 502), _lin(4, 503),
         _lin(5, 504), _lin(6, 505), _incidencia(7)]


# ======================= R12-R13 · preparar y preflight ======================= #

def test_f021_r13_el_preflight_trae_la_cuenta_de_cada_accion() -> None:
    pf = _pipeline(_cli()).preflight(obra=_obra(10, "0100", CEN_OBRA),
                                     lineas=list(TODAS))
    assert _caa(pf.acciones) == {
        1: (701, "0100.LAB", None),                   # R1 ordinarias
        2: (702, "0100.EXT", None),                   # R1 extras
        3: (0, None, MOTIVO_OBRA_SIN_CUENTA),         # R5
        4: (0, None, MOTIVO_RECURSO_SIN_CUENTA),      # R3
        5: (0, None, MOTIVO_CUENTA_AMBIGUA),          # R6
        6: (0, None, None),                           # omitir (R16)
        7: (701, "0100.LAB", None),                   # R2 incidencia
    }
    avisos = {a.registro_id: a.caa_aviso for a in pf.acciones}
    assert avisos[1] is None and avisos[4] is None and avisos[6] is None
    assert avisos[3] == ("la obra 0100 no tiene la cuenta analitica "
                         ".SINOBRA: la linea ira sin cuenta")
    assert avisos[5] == ("la obra 0100 tiene varias cuentas .DOS: la "
                         "linea ira sin cuenta")


def test_f021_r12_se_resuelve_en_preparar_tras_las_reglas() -> None:
    ctx = _pipeline(_cli()).preparar(obra=_obra(10, "0100", CEN_OBRA),
                                     lineas=[_lin(1), _lin(6, 505)])
    assert [(a.accion, a.caa_ide) for a in ctx.acciones] == \
        [("escribir", 701), ("omitir", 0)]


def test_f021_r12_preflight_y_ejecutar_obtienen_la_misma_cuenta() -> None:
    obra = _obra(10, "0100", CEN_OBRA)
    pf = _pipeline(_cli()).preflight(obra=obra, lineas=list(TODAS))
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=obra, lineas=list(TODAS))
    esperado = {a.registro_id: a.caa_ide for a in pf.acciones
                if a.accion == "escribir"}
    escrito = {int(l["synckey"].split(":")[1]): l["caaide"]
               for l in cli.lineas}
    assert escrito == esperado
    assert {e["registro_id"]: e["caa_cod"] for e in r.escritas} == \
        {a.registro_id: a.caa_cod for a in pf.acciones
         if a.accion == "escribir"}


def test_f021_r12_la_lectura_de_cuentas_va_fuera_del_lock() -> None:
    cli = _cli()
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)
    pipeline.ejecutar(obra=_obra(10, "0100", CEN_OBRA), lineas=[_lin(1)])
    assert [c["bajo_lock"] for c in cli.cuentas_leidas] == [False]


# ============================ R10 · una sola lectura ============================ #

def test_f021_r10_una_lectura_por_peticion_con_centro_empresa_y_subs() -> None:
    cli = _cli()
    _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                            lineas=list(TODAS))
    (lectura,) = cli.cuentas_leidas
    # Solo subcuentas de acciones `escribir`: la ZZZ de la omitida no.
    assert (lectura["cenide"], lectura["empresa"], lectura["subcuentas"]) \
        == (CEN_OBRA, 1, ["DOS", "EXT", "LAB", "SINOBRA"])


def test_f021_r10_sin_subcuentas_no_se_lee(caplog) -> None:
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                                lineas=[_lin(4, 503), _lin(6, 505)])
    assert cli.cuentas_leidas == []
    assert "cuentas_de_centro" not in cli.llamadas
    assert [l["caaide"] for l in cli.lineas] == [0]           # R8
    assert [e["caa_cod"] for e in r.escritas] == [None]


def test_f021_r10_sin_nada_que_escribir_no_se_lee(caplog) -> None:
    cli = _cli()
    with caplog.at_level(logging.INFO):
        pf = _pipeline(cli).preflight(obra=_obra(10, "0100", CEN_OBRA),
                                      lineas=[_lin(6, 505)])
    assert cli.cuentas_leidas == []
    assert _caa(pf.acciones) == {6: (0, None, None)}
    assert "cuentas obra=" not in caplog.text


def test_f021_r5_obra_sin_centro_no_lee_y_avisa() -> None:
    cli = _cli(obra=_obra(10, "0100", 0))
    pf = _pipeline(cli).preflight(obra=_obra(10, "0100", 0),
                                  lineas=[_lin(1), _lin(4, 503)])
    assert cli.cuentas_leidas == []
    assert _caa(pf.acciones) == {1: (0, None, MOTIVO_OBRA_SIN_CUENTA),
                                 4: (0, None, MOTIVO_RECURSO_SIN_CUENTA)}
    assert ".LAB" in pf.acciones[0].caa_aviso


def test_f021_r5_obra_sin_atributo_cenide_es_sin_centro() -> None:
    """Una obra que no trae `cenide` (no deberia pasar) no lee ni falla."""
    obra = ObraEntrada(ide=10, codigo="0100", nombre="Obra", empresa=1)
    cli = SigridFake(obras={"0100": obra}, horas=HORAS, cuentas=CUENTAS)
    pf = _pipeline(cli).preflight(obra=obra, lineas=[_lin(1)])
    assert cli.cuentas_leidas == []
    assert pf.acciones[0].caa_motivo == MOTIVO_OBRA_SIN_CUENTA


# ============================ R11 · fallo de lectura ============================ #

def test_f021_r11_fallo_al_leer_cuentas_no_escribe_nada() -> None:
    cli = _cli()
    cli.fallo_cuentas = RuntimeError("sigrid-api caida")
    with pytest.raises(RuntimeError, match="sigrid-api caida"):
        _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                                lineas=[_lin(1), _lin(4, 503)])
    assert cli.lineas == [] and cli.partes == []
    assert "escribir" not in cli.llamadas


def test_f021_r11_fallo_al_leer_cuentas_tumba_el_preflight() -> None:
    cli = _cli()
    cli.fallo_cuentas = RuntimeError("truncada")
    with pytest.raises(RuntimeError, match="truncada"):
        _pipeline(cli).preflight(obra=_obra(10, "0100", CEN_OBRA),
                                 lineas=[_lin(1)])


# ======================= R8, R14-R15 · escritura y escritas ======================= #

def test_f021_r14_r15_insert_con_caaide_y_escritas_con_caa_cod() -> None:
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                                lineas=list(TODAS))
    caaide = {int(l["synckey"].split(":")[1]): l["caaide"]
              for l in cli.lineas}
    assert caaide == {1: 701, 2: 702, 3: 0, 4: 0, 5: 0, 7: 701}
    assert {e["registro_id"]: e["caa_cod"] for e in r.escritas} == {
        1: "0100.LAB", 2: "0100.EXT", 3: None, 4: None, 5: None,
        7: "0100.LAB"}
    assert [o["registro_id"] for o in r.omitidas] == [6]


def test_f021_r8_sin_cuenta_la_linea_se_escribe_igual() -> None:
    """Ninguno de los tres motivos de «sin cuenta» omite ni bloquea."""
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                                lineas=[_lin(3, 502), _lin(4, 503),
                                        _lin(5, 504)])
    assert sorted(e["registro_id"] for e in r.escritas) == [3, 4, 5]
    assert [l["caaide"] for l in cli.lineas] == [0, 0, 0]
    assert r.omitidas == [] and r.pendientes_confirmacion == []


def test_f021_r4_la_cuenta_es_de_la_empresa_de_la_obra() -> None:
    """La cuenta `709` (mismo centro y subcuenta, empresa 28) no cuenta."""
    cli = _cli()
    _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                            lineas=[_lin(1)])
    assert [l["caaide"] for l in cli.lineas] == [701]
    assert cli.cuentas_leidas[0]["empresa"] == 1


# ===================== R16-R17 · ya registradas y pisado ===================== #

PARTE = {"ide": 900, "obride": 10, "ano": 2026, "mes": 3,
         "cod": "PT26/00005", "emp": 1}


def test_f021_r16_ya_registrada_no_se_reescribe_ni_se_actualiza() -> None:
    previa = {"ide": 4001, "hmoide": 900, "reside": 501, "fec": FECHA,
              "horide": HL, "pos": 64, "synckey": synckey_de(1),
              "caaide": 0}
    cli = _cli(partes=[PARTE], lineas=[dict(previa)])
    r = _pipeline(cli).ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                                lineas=[_lin(1)])
    assert r.ya_registradas == [1] and r.escritas == []
    assert cli.lineas == [previa]                 # misma synckey, caaide 0
    assert "escribir" not in cli.llamadas


def test_f021_r17_al_pisar_la_linea_nueva_lleva_la_cuenta() -> None:
    ajena = {"ide": 4000, "hmoide": 900, "reside": 501, "fec": FECHA,
             "horide": HL, "pos": 64, "can": 8.0, "tot": 80.0,
             "synckey": None, "caaide": 0}
    cli = _cli(partes=[PARTE], lineas=[dict(ajena)])
    pipeline = _pipeline(cli)
    pf = pipeline.preflight(obra=_obra(10, "0100", CEN_OBRA),
                            lineas=[_lin(1)])
    (conflicto,) = pf.conflictos
    assert conflicto.clave == f"501|{FECHA}|{HL}"   # la clave no cambia
    r = pipeline.ejecutar(obra=_obra(10, "0100", CEN_OBRA),
                          lineas=[_lin(1)], pisar_claves={conflicto.clave})
    assert r.pisadas == [conflicto.clave] and r.borradas == 1
    (nueva,) = cli.lineas
    assert (nueva["synckey"], nueva["caaide"]) == (synckey_de(1), 701)


# ============================ modo pruebas ============================ #

def test_f021_modo_pruebas_usa_el_centro_de_la_obra_de_pruebas() -> None:
    cli = _cli()
    r = _pipeline(cli, obra_pruebas_forzar=True).ejecutar(
        obra=_obra(10, "0100", CEN_OBRA), lineas=[_lin(1), _lin(2, tipo="extra")])
    assert r.forzada_pruebas is True
    assert cli.cuentas_leidas[0]["cenide"] == CEN_PRUEBAS
    assert [l["caaide"] for l in cli.lineas] == [801, 802]
    assert [e["caa_cod"] for e in r.escritas] == ["0404.LAB", "0404.EXT"]


# ============================ R18 · log por motivo ============================ #

def test_f021_r18_log_por_motivo_sin_datos_personales(caplog) -> None:
    lineas = list(TODAS)
    lineas[0].dni = "12345678Z"
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(_cli()).preflight(obra=_obra(10, "0100", CEN_OBRA),
                                    lineas=lineas)
    (msg,) = [r.getMessage() for r in caplog.records
              if "cuentas obra=" in r.getMessage()]
    assert msg == ("[registro] cuentas obra=0100 ok=3 recurso_sin_cuenta=1 "
                   "obra_sin_cuenta=1 cuenta_ambigua=1")
    assert all(r.levelno == logging.INFO for r in caplog.records
               if "cuentas obra=" in r.getMessage())
    assert "Persona" not in msg and "12345678Z" not in msg
