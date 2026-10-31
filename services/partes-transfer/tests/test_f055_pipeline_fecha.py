# tests/test_f055_pipeline_fecha.py
"""F-055 · paso 2a de `RegistroPipeline.preparar`: la linea sin fecha
valida se omite antes de leer nada de Sigrid (R3-R7, R10, R11, R15).

Contra `SigridFake` (tests/dobles.py). Las fechas validas son de 2026 y ya
pasadas (validas cualquier dia que corra la suite); los tests del limite
superior fijan `RegistroPipeline._hoy`. Datos SINTETICOS.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date

import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import franquicia as fr
from application.services.reajuste_lineas import MOTIVO_NO_REGISTRABLE
from domain.models.registro_models import RecursoSigrid
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests import test_f056_pipeline as f056
from tests.test_f002_pipeline_fases import OBRA, _linea, _pipeline, _sigrid
from tests.test_f046_reajuste_pipeline import NUEVA
from tests.test_f046_t22_pipeline_bordes import _comprobar_nueva

HOY = date(2026, 10, 31)
SIN = "fecha_no_valida: la linea no tiene fecha; corrige la fecha en el " \
      "portal y reaprueba"
MES13 = "fecha_no_valida: 20261340 no es una fecha del calendario; " \
        "corrige la fecha en el portal y reaprueba"
DE2016 = "fecha_no_valida: 15/03/2016 es anterior al 01/01/2026; corrige " \
         "la fecha en el portal y reaprueba"


@pytest.fixture
def hoy_fijo(monkeypatch):
    """`hoy` = 31/10/2026 para los casos del limite superior."""
    monkeypatch.setattr(RegistroPipeline, "_hoy", staticmethod(lambda: HOY),
                        raising=False)


def _acc(pf, rid):
    return next(a for a in pf.acciones if a.registro_id == rid)


def _espia(cli, metodo: str) -> list:
    """Lo que se pide en cada llamada a `metodo` del doble."""
    pedidos: list = []
    original = getattr(cli, metodo)

    def espia(arg, *a, **kw):
        pedidos.append(sorted(x for x in arg if x) if arg is not None
                       else None)
        return original(arg, *a, **kw)
    setattr(cli, metodo, espia)
    return pedidos


# ------------------------------- R3 ------------------------------- #

def test_f055_r3_preflight_omite() -> None:
    cli = _sigrid()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[_linea(1, fecha_int=0)])
    a = _acc(pf, 1)
    assert (a.accion, a.motivo) == ("omitir", SIN)
    assert pf.partes == [] and pf.conflictos == []
    assert (pf.n_escribir, pf.n_omitir, pf.n_ya) == (0, 1, 0)


def test_f055_r3_no_synckey_ni_conflictos() -> None:
    """Una ajena del recurso el 15/03/2016 en un parte de ese periodo:
    hoy daria conflicto; con la guarda ni se mira."""
    ajena = {"ide": 3001, "hmoide": 800, "reside": 501, "fec": 20160315,
             "horide": 1, "hora_codigo": None, "can": 8.0, "pre": 10.0,
             "tot": 80.0, "pos": 64, "synckey": None, "caaide": 0,
             "paride": 0, "tex": "", "enlazada": False}
    cli = _sigrid(partes=[{"ide": 800, "obride": 10, "ano": 2016, "mes": 3,
                           "cod": "PT16/00001", "emp": 1, "est": 1}],
                  lineas=[dict(ajena)])
    claves = _espia(cli, "lineas_por_synckey")
    pf = _pipeline(cli).preflight(
        obra=OBRA, lineas=[_linea(1, fecha_int=20160315),
                           _linea(2, fecha_int=0)])
    assert [(a.accion, a.motivo) for a in pf.acciones] == [
        ("omitir", DE2016), ("omitir", SIN)]
    assert pf.conflictos == [] and pf.partes == []
    assert all(synckey_de(1) not in c and synckey_de(2) not in c
               for c in claves)
    assert cli.periodos_leidos == [] and cli.lineas_leidas == []
    assert cli.lineas == [ajena]


def test_f055_r3_racha_y_hermano() -> None:
    """Con `MOVER_CIZ`: un `fin` y un `inicio` con `ciz_mismo_dia`, ambos
    con fecha 0: ni se busca la racha ni se mueve ni hay hermano."""
    from tests import test_f060_pipeline_mover as f060
    cli = f060._cli(f060._fila(7001, fec=20261003, rid=3))
    fin = f060._fin(4, 0, racha=[3])
    ini = f060._ini(5, 0, racha=[6])
    ini.ciz_mismo_dia = True
    r = f060._pipe(cli).ejecutar(obra=f060._obra(), lineas=[fin, ini])
    assert r.ok and r.escritas == []
    assert [(o["registro_id"], o["motivo"]) for o in r.omitidas] == [
        (4, SIN), (5, SIN)]
    assert cli.racha_leidas == [] and cli.estados_leidos == []
    assert "escribir" not in cli.llamadas
    pf = f060._pipe(cli).preflight(obra=f060._obra(), lineas=[
        f060._fin(4, 0, racha=[3]), ini])
    assert all(a.mover is None and a.fin_mismo_dia is None
               for a in pf.acciones)
    assert cli.lineas[0]["fec"] == 20261003


# ------------------------------- R4 ------------------------------- #

@pytest.mark.parametrize("caso", [
    "no_existe", "otra_empresa", "baja", "sin_recurso_ni_dni",
    "sin_horas", "dni_sin_recurso"])
def test_f055_r4_manda_sobre_recurso(caso) -> None:
    recursos = {"no_existe": {},
                "otra_empresa": {501: RecursoSigrid(501, 2, None, None)},
                "baja": {501: RecursoSigrid(501, 1, 20250101, None)}}
    cli = _sigrid(recursos=recursos.get(caso))
    linea = _linea(1, fecha_int=0)
    if caso == "sin_recurso_ni_dni":
        linea.recurso_ide = None
    if caso == "dni_sin_recurso":
        linea.recurso_ide, linea.dni = None, "00000000T"
    if caso == "sin_horas":
        linea.horas = 0.0
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea])
    assert (_acc(pf, 1).accion, _acc(pf, 1).motivo) == ("omitir", SIN)


def test_f055_r4_mensual_no_va_a_dedicacion() -> None:
    from tests import test_f019_pipeline as f019
    cli = f019._cli()
    linea = f019._lin(2, 602)
    linea.fecha_int = 0
    r = f019._pipeline(cli, encendido=True).ejecutar(obra=f019.OBRA,
                                                     lineas=[linea])
    assert r.dedicacion == []
    assert r.omitidas == [{"registro_id": 2, "motivo": SIN}]


# ------------------------------- R5 ------------------------------- #

def test_f055_r5_no_lee_sigrid() -> None:
    cli = _sigrid(alta_protegida=True)
    por_dni = _espia(cli, "recursos_por_dni")
    datos = _espia(cli, "datos_recursos")
    horas = _espia(cli, "horas_de_recursos")
    sin_rec = _linea(1, fecha_int=0)
    sin_rec.recurso_ide, sin_rec.dni = None, "00000000T"
    r = _pipeline(cli).ejecutar(obra=OBRA, lineas=[
        sin_rec, _linea(2, fecha_int=20261340, recurso_ide=502)])
    assert r.ok and r.escritas == []
    assert por_dni == [] and datos == []
    assert all(h == [] for h in horas)
    assert cli.periodos_leidos == [] and cli.altas == []
    assert cli.partes == [] and cli.lineas == []
    assert "siguiente_cod_pt" not in cli.llamadas


# ------------------------------- R6 ------------------------------- #

def _resumen(cli, r):
    return (r.ok, r.escritas, [o for o in r.omitidas
                               if o["registro_id"] < 100],
            r.ya_registradas, r.pisadas, r.anuladas,
            [asdict(c) for c in r.pendientes_confirmacion],
            [(p["cod"], p["ano"], p["mes"]) for p in cli.partes],
            cli.lineas)


def test_f055_r6_mezcla(caplog) -> None:
    def lote():
        return [_linea(1), _linea(2, tipo_hora="extra", horas=2.0),
                _linea(3, recurso_ide=777)]
    recursos = {501: RecursoSigrid(501, 1, None, None),
                777: RecursoSigrid(777, 2, None, None)}
    sola_cli = _sigrid(recursos=dict(recursos))
    sola = _pipeline(sola_cli).ejecutar(obra=OBRA, lineas=lote())
    pf_sola = _pipeline(_sigrid(recursos=dict(recursos))).preflight(
        obra=OBRA, lineas=lote())

    mezcla_cli = _sigrid(recursos=dict(recursos))
    invalidas = [_linea(101, fecha_int=0), _linea(102, fecha_int=20261340),
                 _linea(103, fecha_int=20160315, recurso_ide=777)]
    caplog.clear()
    with caplog.at_level("WARNING"):
        mezcla = _pipeline(mezcla_cli).ejecutar(obra=OBRA,
                                                lineas=lote() + invalidas)
    mensajes = list(caplog.messages)
    pf_mezcla = _pipeline(_sigrid(recursos=dict(recursos))).preflight(
        obra=OBRA, lineas=lote() + invalidas)

    assert _resumen(mezcla_cli, mezcla) == _resumen(sola_cli, sola)
    assert [o["registro_id"] for o in mezcla.omitidas
            if o["registro_id"] > 100] == [101, 102, 103]
    assert [asdict(a) for a in pf_mezcla.acciones[:3]] == [
        asdict(a) for a in pf_sola.acciones]
    assert [asdict(p) for p in pf_mezcla.partes] == [
        asdict(p) for p in pf_sola.partes]
    # El WARNING del paso 2c cuenta solo la del recurso (la 3).
    recurso = [m for m in mensajes if "omitidas por el recurso" in m]
    assert len(recurso) == 1 and ": 1 linea(s)" in recurso[0]
    assert "101" not in recurso[0] and "103" not in recurso[0]


# ------------------------------- R7 ------------------------------- #

def test_f055_r7_ejecutar_sin_validas() -> None:
    cli = _sigrid()
    r = _pipeline(cli).ejecutar(obra=OBRA, lineas=[
        _linea(1, fecha_int=0), _linea(2, fecha_int=0)])
    assert r.ok is True and r.escritas == []
    assert r.omitidas == [{"registro_id": 1, "motivo": SIN},
                          {"registro_id": 2, "motivo": SIN}]
    assert "escribir" not in cli.llamadas
    assert cli.partes == [] and cli.lineas == []


# ------------------------------- R10 ------------------------------ #

def test_f055_r10_reajuste_extra_nueva() -> None:
    r, llamadas = _comprobar_nueva(fecha_int=20261340)
    assert llamadas  # pasa por `preparar` (el paso 2a la omite)
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not r.ok and not v.editable
    assert v.motivo.startswith(MOTIVO_NO_REGISTRABLE)
    assert "fecha_no_valida" in v.motivo


def test_f055_r10_reajuste_extra_nueva_no_escribe() -> None:
    from tests.test_f046_reajuste_pipeline import (
        _caso_extra_nueva,
        _nueva,
        _pipe,
    )
    cli, ops = _caso_extra_nueva()
    ops[1] = _nueva(fecha_int=20160315)
    antes = [dict(f) for f in cli.lineas]
    r = _pipe(cli)[0].ejecutar(ops, usuario="admin@test")
    assert not r.ok
    assert cli.lineas == antes


# ------------------------------- R11 ------------------------------ #

def test_f055_r11_warning_sin_nombres(caplog) -> None:
    cli = _sigrid()
    lineas = [_linea(7, fecha_int=0), _linea(3, fecha_int=20261340),
              _linea(5)]
    for l in lineas:
        l.nombre, l.dni = "Nombre Ficticio Apellido", "12345678Z"
    with caplog.at_level("WARNING"):
        _pipeline(cli).preflight(obra=OBRA, lineas=lineas)
    avisos = [r for r in caplog.records if "sin fecha valida" in r.getMessage()]
    assert [r.getMessage() for r in avisos] == [
        "[registro] obra=0100 lineas sin fecha valida=2 registro_ids=[3, 7]"]
    assert avisos[0].levelname == "WARNING"
    assert "Ficticio" not in caplog.text and "12345678Z" not in caplog.text


def test_f055_r11_sin_invalidas_no_hay_warning(caplog) -> None:
    with caplog.at_level("WARNING"):
        _pipeline(_sigrid()).preflight(obra=OBRA, lineas=[_linea(1)])
    assert "sin fecha valida" not in caplog.text


# ---------------------- R1 en el pipeline (hoy) ---------------------- #

def test_f055_r1_pipeline_usa_hoy(hoy_fijo) -> None:
    pf = _pipeline(_sigrid()).preflight(obra=OBRA, lineas=[
        _linea(1, fecha_int=20270101), _linea(2, fecha_int=20270102)])
    assert _acc(pf, 1).accion == "escribir"
    assert _acc(pf, 2).motivo == (
        "fecha_no_valida: 02/01/2027 es posterior al 01/01/2027; corrige "
        "la fecha en el portal y reaprueba")


def test_f055_hoy_real_es_la_fecha_utc() -> None:
    from datetime import datetime, timezone
    antes = datetime.now(timezone.utc).date()
    valor = RegistroPipeline._hoy()
    despues = datetime.now(timezone.utc).date()
    assert valor in (antes, despues)
    assert type(valor) is date


# ------------------------------- R15 ------------------------------ #

def _franquicia(fecha, partes=None):
    cli = f056._cli(partes=partes)
    pipe, _lock = f056._pipe(cli)
    return cli, pipe, f056._pet(fecha=fecha)


@pytest.mark.parametrize("metodo", ["comprobar", "ejecutar"])
def test_f055_r15_franquicia_posterior_no_editable(metodo, hoy_fijo) -> None:
    cli, pipe, pet = _franquicia(20270102, partes=[
        f056._parte(), f056._parte(ide=950, cod="PT27/00001", mes=1)])
    cli.partes[1]["ano"] = 2027
    cli.alta_protegida = True
    r = getattr(pipe, metodo)(pet)
    assert (r.ok, r.accion, r.escrita) == (False, fr.NO_EDITABLE, False)
    assert "fecha_no_valida" in r.motivo
    assert "escribir" not in cli.llamadas
    assert cli.altas == []


@pytest.mark.parametrize("metodo", ["comprobar", "ejecutar"])
def test_f055_r15_franquicia_hoy_mas_30_se_ajusta(metodo, hoy_fijo) -> None:
    cli, pipe, pet = _franquicia(20261130, partes=[
        f056._parte(), f056._parte(ide=950, cod="PT26/00315", mes=11)])
    r = getattr(pipe, metodo)(pet)
    assert (r.ok, r.accion) == (True, fr.CREAR)
    assert r.escrita is (metodo == "ejecutar")
    if metodo == "ejecutar":
        assert f056._ajuste(cli)[0]["fec"] == 20261130

