# tests/test_f031_mutantes.py
"""F-031 · Tests que cierran los supervivientes de la primera campana de
mutacion (`progress/mutacion_F-031.md`, anexo). Cada test nombra el
mutante que mata (numero de la campana del 2026-10-06 10:57).

Sin red: `SigridFake`, lectores y `httpx.post` simulados. Datos SINTETICOS.
"""
from __future__ import annotations

import dataclasses

import httpx
import pytest

import comprobar_asiento_analitico as herramienta
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.cuenta_analitica import OrigenSubcuenta
from comprobar_asiento_analitico import CUADRA, DESCUADRE, comparar
from config.settings import Settings
from domain.models.registro_models import (
    AccionLinea,
    LineaSigrid,
    ParteDestino,
    ParteSigrid,
    PartidaCuenta,
)
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests.dobles import SettingsFake
from tests.test_f031_pipeline_cuenta_partida import (
    PARTIDAS,
    _caa,
)
from tests.test_f031_pipeline_cuenta_partida import _cli as _cli_cuenta
from tests.test_f031_pipeline_cuenta_partida import _lin as _lin_cuenta
from tests.test_f031_pipeline_cuenta_partida import _obra as _obra_cuenta
from tests.test_f031_pipeline_estado import (
    CERRADO,
    FECHA,
    HE,
    HL,
    IMPUTADO,
    REGISTRO,
    _cli,
    _lin,
    _linea_sigrid,
    _obra,
    _parte,
    _pipeline,
)


# ---------------------- registro_pipeline: cuenta ---------------------- #

def test_m5_sin_partida_no_toma_la_partida_1() -> None:
    """`partidas.get(int(a.paride or 0))`: una linea sin partida no puede
    heredar la partida de `ide` 1 que pidio otra linea."""
    partidas = {**PARTIDAS, 1: PartidaCuenta(1, "00.01", "0100.CIMO12")}
    pf = _pipeline_cuenta(_cli_cuenta(partidas=partidas)).preflight(
        obra=_obra_cuenta(), lineas=[_lin_cuenta(1, 503, 1),
                                     _lin_cuenta(2, 503)])
    caa = _caa(pf.acciones)
    assert caa[1][3] == "partida" and caa[2][3] is None


def _pipeline_cuenta(cli) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake())


# ---------------------- registro_pipeline: paso 7 ---------------------- #

def test_m15_periodo_sin_escribir_no_lee_lineas() -> None:
    """`if not grupo or not parte.del_periodo`: si todo el periodo ya esta
    registrado (synckey), no se leen las lineas de sus partes."""
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)],
               lineas=[_linea_sigrid(4001, 800, synckey=synckey_de(1))])
    _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    assert cli.lineas_leidas == []


def _sin_ajustes_de_estado() -> SettingsFake:
    st = SettingsFake()
    for nombre in ("est_parte_activo", "est_parte_cerrado",
                   "est_parte_imputado"):
        delattr(st, nombre)
    return st


def test_m26_m29_m31_settings_sin_ajustes_usa_1_3_10() -> None:
    """Los defectos de `getattr` (un settings anterior a F-031)."""
    cli = _cli(partes=[_parte(900, "PT26/00009"),
                       _parte(800, "PT26/00004", est=CERRADO),
                       _parte(801, "PT26/00005", est=IMPUTADO)])
    pf = RegistroPipeline(cliente=cli, settings=_sin_ajustes_de_estado()
                          ).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.ide, p.estado) == (900, REGISTRO)
    assert "PT26/00005 (Imputado), PT26/00004 (Cerrado)" in p.aviso


def _accion(**kw) -> AccionLinea:
    base = dict(registro_id=1, accion="escribir", ano=2026, mes=3,
                fecha_int=FECHA, recurso_ide=501, hora_ide=HL)
    base.update(kw)
    return AccionLinea(**base)


def _ls(ide, horide, reside=501, synckey=None) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=reside, fecha_int=FECHA,
                       horide=horide, hora_codigo=None, can=8.0, tot=80.0,
                       synckey=synckey)


def test_m32_linea_sin_tipo_no_choca_con_el_tipo_1() -> None:
    """`int(ls.horide or 0)`: una linea de Sigrid sin tipo (None) no es la
    del tipo 1."""
    assert RegistroPipeline._choques([_ls(1, None)], _accion(hora_ide=1),
                                     set()) == []


def test_m41_accion_sin_tipo_no_choca_con_el_tipo_1() -> None:
    assert RegistroPipeline._choques([_ls(1, 1)], _accion(hora_ide=None),
                                     set()) == []
    assert [x.ide for x in RegistroPipeline._choques(
        [_ls(1, None)], _accion(hora_ide=None), set())] == [1]


def test_m39_otra_linea_nuestra_tambien_choca() -> None:
    """`not (ls.synckey and ls.synckey in mias)`: una linea con synckey de
    OTRO registro nuestro no es «nuestra» para esta accion."""
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)],
               lineas=[_linea_sigrid(4000, 800, synckey=synckey_de(99))])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    assert pf.acciones[0].accion == "omitir"


def _parte_destino() -> ParteDestino:
    return ParteDestino(ano=2026, mes=3, existe=True, ide=900,
                        cod="PT26/00005")


def test_m49_el_conflicto_lleva_el_recurso() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005")],
               lineas=[_linea_sigrid(4001, 900)])
    (c,) = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)]).conflictos
    assert c.recurso_ide == 501


def test_m57_m55_conflicto_de_accion_sin_recurso_ni_tipo() -> None:
    """Defensivo: una accion sin recurso ni tipo da recurso 0 y su contexto
    son las lineas con tipo."""
    ps = ParteSigrid(900, "PT26/00005", REGISTRO)
    lineas = [_ls(1, None, reside=None), _ls(2, 1, reside=None)]
    pipeline = _pipeline(_cli())
    (c,) = pipeline._conflictos(
        _parte_destino(), [_accion(recurso_ide=None, hora_ide=None)],
        [(ps, lineas)], set())
    assert c.recurso_ide == 0
    assert [x.ide for x in c.lineas] == [1]
    assert [x.ide for x in c.contexto] == [2]


def test_m52_linea_sin_tipo_es_contexto_del_tipo_1() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005")],
               lineas=[_linea_sigrid(4001, 900),
                       _linea_sigrid(4002, 900, horide=None)])
    (c,) = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)]).conflictos
    assert [x.ide for x in c.lineas] == [4001]
    assert [x.ide for x in c.contexto] == [4002]


# -------------------------- modelos inmutables -------------------------- #

@pytest.mark.parametrize("objeto, campo", [
    (OrigenSubcuenta("CIMO09", "recurso", None), "sub"),           # m66
    (ParteSigrid(1, "PT26/00001", 1), "est"),                      # m113
    (PartidaCuenta(300, "01.02", "0100.CIMO12"), "caa_cod"),       # m121
])
def test_m66_m113_m121_valores_inmutables(objeto, campo) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(objeto, campo, None)


# ----------------------------- herramienta ----------------------------- #

def test_m70_la_diferencia_se_redondea_a_la_millonesima() -> None:
    """Una diferencia por debajo de la millonesima es ruido de coma
    flotante: 0,0100004 se lee como 0,01 y cuadra."""
    assert comparar({"0696.CIMO09": 0.0100004}, {}, 1) == CUADRA
    assert comparar({"0696.CIMO09": 0.010001}, {}, 1) == DESCUADRE


class _Settings:
    sigrid_api_base_url = "http://sigrid.invalid"
    sigrid_api_function_key = "clave-de-test"
    sigrid_api_database = "bd"
    sigrid_api_timeout_s = 5.0
    tip_parte_trabajo = 35
    est_parte_activo = 1
    est_parte_cerrado = 3
    est_parte_imputado = 10


ARGS = ["--empresa", "1", "--obra", "0696", "--ano", "2026", "--mes", "1"]


@pytest.mark.parametrize("quitar", ["--empresa", "--obra", "--ano", "--mes"])
def test_m107_m110_m111_m112_argumentos_obligatorios(monkeypatch,
                                                     quitar) -> None:
    def post(*a, **k):
        raise AssertionError("no debe leer nada sin argumentos")

    monkeypatch.setattr(modulo_cliente.httpx, "post", post)
    i = ARGS.index(quitar)
    with pytest.raises(SystemExit):
        herramienta.main(ARGS[:i] + ARGS[i + 2:], settings=_Settings())


def test_main_sin_settings_lee_la_configuracion(monkeypatch, tmp_path,
                                                capsys) -> None:
    """Sin `settings`, `main` construye `Settings()` (aqui sin `.env`)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    urls: list[str] = []

    def post(url, headers=None, timeout=None, json=None):
        urls.append(url)
        return httpx.Response(200, json={"ok": True, "columns": ["ide"],
                                         "rows": [], "truncated": False})

    monkeypatch.setattr(modulo_cliente.httpx, "post", post)
    assert herramienta.main(ARGS) == 0
    assert urls == ["http://sigrid.invalid/api/sql/read"]
    assert capsys.readouterr().out.strip() == \
        "La obra 0696 no existe en la empresa 1"


# ------------------------------- settings ------------------------------- #

def test_m116_m118_estados_por_defecto_y_por_entorno(monkeypatch,
                                                     tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    for var in ("EST_PARTE_ACTIVO", "EST_PARTE_CERRADO",
                "EST_PARTE_IMPUTADO"):
        monkeypatch.delenv(var, raising=False)
    st = Settings(_env_file=None)
    assert (st.est_parte_activo, st.est_parte_cerrado,
            st.est_parte_imputado) == (1, 3, 10)
    monkeypatch.setenv("EST_PARTE_CERRADO", "30")
    monkeypatch.setenv("EST_PARTE_IMPUTADO", "40")
    st = Settings(_env_file=None)
    assert (st.est_parte_cerrado, st.est_parte_imputado) == (30, 40)


# Guarda: el doble de los tests anteriores sigue sin cambiar de tipo.
def test_choques_ignora_otros_tipos() -> None:
    assert RegistroPipeline._choques([_ls(1, HE)], _accion(), set()) == []
