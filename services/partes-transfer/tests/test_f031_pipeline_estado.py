# tests/test_f031_pipeline_estado.py
"""F-031 · A-C: el parte destino segun el estado de los partes del periodo.

sv5 nunca escribe en un parte que no este En registro («cerrado» = Cerrado
o Imputado, decision del humano del 2026-10-06): las lineas van a un parte
En registro de esa obra y mes (el complementario, reutilizado o nuevo);
duplicados y pisado se miran en TODOS los partes del periodo.

Primer bloque: caracterizacion EN VERDE contra el codigo anterior a F-031
(R4, R6, R10, R32, R33). Segundo bloque: lo nuevo (design §10).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (obras,
codigos y nombres inventados).
"""
from __future__ import annotations

import logging

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    RecursoSigrid,
)
from fastapi.testclient import TestClient
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
    synckey_de,
)
from interface_adapters.api.app import build_app
from interface_adapters.resultado_json import resultado_a_dict
from tests.dobles import SettingsFake, SigridFake

FECHA = 20260302
CEN_OBRA = 77
HL, HE, CIV, MENC = 1, 2, 3, 5
REGISTRO, CERRADO, IMPUTADO = 1, 3, 10


def _obra(ide=10, cod="0100", empresa=1, cenide=CEN_OBRA) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = cenide        # como lo deja el cliente real
    return o


def _h(horide, cod, caa=None, defecto=False, pre=10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=caa, defecto=defecto)


HORAS = {
    501: [_h(HL, "HL01", "00000.CIMO01", True), _h(HE, "HE01"),
          _h(CIV, "CIV", pre=0.0)],
    # Solo extra: sus ordinarias se OMITEN (R3 de las reglas).
    502: [_h(HE, "HE01")],
    # Sin ninguna cuenta (como Porsan, empresa 28).
    503: [_h(HL, "HL01", None, True), _h(HE, "HE01")],
    # Mensual: con el interruptor de F-019 encendido va a dedicacion.
    602: [_h(MENC, "MENC", pre=0.0)],
}

CUENTAS = [(CEN_OBRA, 1, 701, "0100.CIMO01")]


def _parte(ide, cod, est=REGISTRO, obride=10, emp=1, ano=2026,
           mes=3) -> dict:
    return {"ide": ide, "obride": obride, "ano": ano, "mes": mes,
            "cod": cod, "emp": emp, "est": est}


def _linea_sigrid(ide, hmoide, reside=501, horide=HL, synckey=None,
                  fec=FECHA) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": 8.0,
            "tot": 80.0, "pos": 64, "synckey": synckey, "caaide": 0}


def _cli(obra=None, **kw) -> SigridFake:
    obra = obra or _obra()
    kw.setdefault("cuentas", CUENTAS)
    return SigridFake(obras={obra.codigo: obra}, horas=HORAS, **kw)


def _lin(rid, recurso=501, tipo="normal", **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        tipo_hora=tipo, horas=8.0, **kw)


def _pipeline(cli, **st) -> RegistroPipeline:
    settings = SettingsFake()
    for k, v in st.items():
        setattr(settings, k, v)
    return RegistroPipeline(cliente=cli, settings=settings)


def _inserts_por_parte(cli) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for l in cli.lineas:
        if l.get("synckey"):
            out.setdefault(l["hmoide"], []).append(
                int(l["synckey"].split(":")[1]))
    return out


# =============== Caracterizacion (verde ANTES de F-031) =============== #

def test_f031_r4_periodo_sin_partes_crea_el_parte_como_hoy() -> None:
    cli = _cli()
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod, p.creado) == \
        (False, None, "PT26/00001", False)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (nuevo,) = cli.partes
    assert (nuevo["cod"], nuevo["obride"], nuevo["emp"]) == \
        ("PT26/00001", 10, 1)
    assert [e["parte_cod"] for e in r.escritas] == ["PT26/00001"]
    assert _inserts_por_parte(cli) == {nuevo["ide"]: [1]}


def test_f031_r6_un_parte_en_registro_se_reutiliza() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005")])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod) == (True, 900, "PT26/00005")
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1), _lin(2)])
    assert len(cli.partes) == 1                       # no crea otro
    assert _inserts_por_parte(cli) == {900: [1, 2]}
    assert {e["parte_cod"] for e in r.escritas} == {"PT26/00005"}


def test_f031_r10_synckey_en_un_parte_cerrado_es_ya_registrado() -> None:
    previa = _linea_sigrid(4001, 900, synckey=synckey_de(1))
    cli = _cli(partes=[_parte(900, "PT26/00004", est=IMPUTADO)],
               lineas=[dict(previa)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.ya_registradas == [1] and r.escritas == []
    assert cli.lineas == [previa] and len(cli.partes) == 1
    assert "escribir" not in cli.llamadas


def _decisiones(cli, lineas, **st) -> dict:
    pf = _pipeline(cli, **st).preflight(obra=_obra(), lineas=lineas)
    return {a.registro_id: (a.accion, a.motivo, a.caa_ide)
            for a in pf.acciones}


def _lote_r32() -> list[LineaEntrada]:
    return [_lin(1, 502, partida_ide=300, partida_cod="01.02"),
            _lin(2, 602, partida_ide=300, partida_cod="01.02")]


def test_f031_r32_omitir_y_dedicacion_no_dependen_del_estado() -> None:
    sin_parte = _decisiones(_cli(), _lote_r32(),
                            mensuales_a_dedicacion=True)
    cerrado = _decisiones(
        _cli(partes=[_parte(900, "PT26/00004", est=CERRADO)],
             lineas=[_linea_sigrid(4000, 900, reside=502),
                     _linea_sigrid(4002, 900, reside=602, horide=MENC)]),
        _lote_r32(), mensuales_a_dedicacion=True)
    assert cerrado == sin_parte
    assert [d[0] for d in cerrado.values()] == ["omitir", "dedicacion"]


def test_f031_r32_ya_registrado_no_depende_del_estado() -> None:
    for est in (REGISTRO, CERRADO, IMPUTADO):
        cli = _cli(partes=[_parte(900, "PT26/00004", est=est)],
                   lineas=[_linea_sigrid(4001, 900,
                                         synckey=synckey_de(1))])
        assert _decisiones(cli, [_lin(1, partida_ide=300)])[1][0] == \
            "ya_registrado"


def test_f031_r33_empresa_28_sin_cerrados_ni_cuentas_como_hoy() -> None:
    obra = _obra(20, "0724", empresa=28, cenide=0)
    cli = _cli(obra=obra, cuentas=[],
               recursos={503: RecursoSigrid(503, 28, 0, None)},
               partes=[_parte(950, "PT26/00121", obride=20, emp=28)])
    r = _pipeline(cli).ejecutar(obra=obra, lineas=[_lin(1, 503)])
    assert _inserts_por_parte(cli) == {950: [1]}
    assert [l["caaide"] for l in cli.lineas] == [0]
    assert len(cli.partes) == 1 and r.pendientes_confirmacion == []
    assert cli.cuentas_leidas == []


# ======================= Lo nuevo de F-031 (design §10) ======================= #

class SigridConSql(SigridFake):
    """`SigridFake` cuyas sentencias llevan ademas el SQL REAL del cliente
    (los constructores de sentencias no tocan la red) y que apunta todo lo
    que se manda a `escribir` (R5, R31)."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.real = SigridWriteClient(base_url="http://sigrid.invalid",
                                      function_key="clave-de-test",
                                      database="bd")
        self.enviadas: list[dict] = []

    def stmts_crear_parte(self, **kw):
        (s,) = super().stmts_crear_parte(**kw)
        s["sqls"] = [x["sql"] for x in self.real.stmts_crear_parte(**kw)]
        return [s]

    def stmt_insert_linea(self, **kw):
        s = super().stmt_insert_linea(**kw)
        s["sqls"] = [self.real.stmt_insert_linea(**kw)["sql"]]
        return s

    def stmt_borrar_linea(self, ide):
        s = super().stmt_borrar_linea(ide)
        s["sqls"] = [self.real.stmt_borrar_linea(ide)["sql"]]
        return s

    def escribir(self, statements):
        self.enviadas.extend(dict(s) for s in statements)
        return super().escribir(statements)


def _cli_sql(**kw) -> SigridConSql:
    kw.setdefault("cuentas", CUENTAS)
    return SigridConSql(obras={"0100": _obra()}, horas=HORAS, **kw)


def _acciones(pf) -> dict:
    return {a.registro_id: (a.accion, a.motivo) for a in pf.acciones}


MOTIVO_CERRADO_4 = ("parte_cerrado: ya hay horas de ese recurso, dia y tipo "
                    "en el parte PT26/00004 (Cerrado); no se registran")


# ---------------------- R1 · una lectura por periodo ---------------------- #

def test_f031_r1_una_lectura_de_partes_por_periodo_con_escribir() -> None:
    cli = _cli()
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260415), _lin(3, fecha_int=20260416),
        _lin(4, 502, fecha_int=20260510)])       # omitida: su mes no
    assert cli.periodos_leidos == [(10, 2026, 3), (10, 2026, 4)]
    assert [(p.ano, p.mes) for p in pf.partes] == [(2026, 3), (2026, 4)]


def test_f031_r1_sin_escribir_no_lee_partes() -> None:
    cli = _cli()
    _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1, 502)])
    assert cli.periodos_leidos == []


# ------------------------ R2 · el elegido y R18 ------------------------ #

def test_f031_r2_cerrado_de_mayor_ide_y_uno_en_registro() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005"),
                       _parte(905, "PT26/00009", est=CERRADO)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod, p.estado, p.complementario,
            p.cerrados) == (True, 900, "PT26/00005", REGISTRO, True,
                            ["PT26/00009"])
    assert p.aviso == (
        "el parte PT26/00009 (Cerrado) de 03/2026 esta cerrado: las lineas "
        "van al parte complementario PT26/00005 (ya existe, en registro)")
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert _inserts_por_parte(cli) == {900: [1]} and len(cli.partes) == 2


def test_f031_r7_en_registro_sale_del_ajuste() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005", est=1),
                       _parte(901, "PT26/00006", est=7)])
    pf = _pipeline(cli, est_parte_activo=7).preflight(obra=_obra(),
                                                      lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.ide, p.cerrados) == (901, ["PT26/00005"])
    assert "PT26/00005 (estado 1)" in p.aviso


def test_f031_r7_nombres_de_estado_desde_el_ajuste() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00004", est=8)])
    pf = _pipeline(cli, est_parte_cerrado=8).preflight(obra=_obra(),
                                                       lineas=[_lin(1)])
    assert "PT26/00004 (Cerrado)" in pf.partes[0].aviso


# ------------------- R3 · complementario nuevo y R5 ------------------- #

@pytest.mark.parametrize("est, nombre", [(CERRADO, "Cerrado"),
                                         (IMPUTADO, "Imputado")])
def test_f031_r3_todos_cerrados_crea_complementario(est, nombre) -> None:
    cli = _cli_sql(partes=[_parte(800, "PT26/00004", est=est),
                           _parte(700, "PT26/00002", est=est, mes=2)],
                   lineas=[_linea_sigrid(4000, 800, fec=20260310)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod, p.estado, p.complementario,
            p.cerrados) == (False, None, "PT26/00005", None, True,
                            ["PT26/00004"])
    assert p.aviso == (
        f"el parte PT26/00004 ({nombre}) de 03/2026 esta cerrado: las "
        f"lineas van al parte complementario PT26/00005 (se creara)")
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    nuevo = cli.partes[-1]
    assert (nuevo["cod"], nuevo.get("est", REGISTRO), nuevo["mes"]) == \
        ("PT26/00005", REGISTRO, 3)
    (crear,) = [s for s in cli.enviadas if s["op"] == "crear_parte"]
    assert crear["desc"] == "Parte Obra 0100"
    assert _inserts_por_parte(cli) == {nuevo["ide"]: [1]}
    (rp,) = r.partes
    assert (rp.existe, rp.creado, rp.ide, rp.cod, rp.estado) == \
        (True, True, nuevo["ide"], "PT26/00005", REGISTRO)
    # R5: nada va al parte cerrado (ni lineas, ni borrados, ni cabecera).
    assert all(s.get("hmoide") != 800 for s in cli.enviadas)
    assert cli.lineas[0]["ide"] == 4000 and len(cli.lineas) == 2


def test_f031_r4_sin_partes_no_es_complementario_ni_avisa() -> None:
    pf = _pipeline(_cli()).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.complementario, p.aviso, p.cerrados, p.del_periodo,
            p.estado) == (False, None, [], [], None)


def test_f031_r6_un_parte_en_registro_sin_aviso() -> None:
    pf = _pipeline(_cli(partes=[_parte(900, "PT26/00005")])).preflight(
        obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.complementario, p.aviso, p.estado) == (False, None, REGISTRO)


def test_f031_r5_r31_ni_partes_cerrados_ni_asientos_ni_estados() -> None:
    cli = _cli_sql(
        partes=[_parte(800, "PT26/00004", est=IMPUTADO),
                _parte(810, "PT26/00006"), _parte(805, "PT26/00005")],
        lineas=[_linea_sigrid(4000, 800, fec=20260303),
                _linea_sigrid(4001, 805, fec=20260304)])
    lineas = lambda: [_lin(1), _lin(2, fecha_int=20260303),  # noqa: E731
                      _lin(3, fecha_int=20260304)]
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=lineas())
    claves = {c.clave for c in pf.conflictos}
    _pipeline(cli).ejecutar(obra=_obra(), lineas=lineas(),
                            pisar_claves=claves)
    assert {s["op"] for s in cli.enviadas} == {"insert", "borrar"}
    assert {s["hmoide"] for s in cli.enviadas if s["op"] == "insert"} == \
        {810}
    assert [s["ide"] for s in cli.enviadas if s["op"] == "borrar"] == [4001]
    sqls = " ".join(q for s in cli.enviadas for q in s["sqls"]).lower()
    assert "update" not in sqls
    for tabla in ("asa", "apa", "apu", "asi"):
        assert f" {tabla} " not in f" {sqls} ".replace("(", " ")


def test_f031_r31_crear_parte_solo_inserta_cabecera_en_registro() -> None:
    cli = _cli_sql(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (crear,) = [s for s in cli.enviadas if s["op"] == "crear_parte"]
    assert [q.split()[0:3] for q in crear["sqls"]] == \
        [["INSERT", "INTO", "con"], ["INSERT", "INTO", "hmo"]]
    real = cli.real.stmts_crear_parte(obra=_obra(), ano=2026, mes=3,
                                      cod="PT26/00005", desc="d")
    assert real[0]["parameters"][2] == REGISTRO        # est del nuevo


# ----------------------- R8 · reutiliza el complementario ----------------------- #

def test_f031_r8_la_segunda_aprobacion_reutiliza_el_complementario() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=IMPUTADO)])
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(2, fecha_int=20260303)])
    assert len(cli.partes) == 2
    comp = cli.partes[-1]["ide"]
    assert _inserts_por_parte(cli) == {comp: [1, 2]}


# ------------------------- R9 · relectura del creado ------------------------- #

@pytest.mark.parametrize("campo, valor", [("est_al_crear", CERRADO),
                                          ("cod_al_crear", "PT26/09999")])
def test_f031_r9_relectura_que_no_cuadra_no_inserta(campo, valor) -> None:
    cli = _cli_sql(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    setattr(cli, campo, valor)
    with pytest.raises(RuntimeError, match="PT26/00005"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [s["op"] for s in cli.enviadas] == ["crear_parte"]
    assert cli.lineas == []


# --------------------- R11, R14 · choque con un cerrado --------------------- #

def test_f031_r11_r14_choque_con_parte_cerrado_se_omite() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)],
               lineas=[_linea_sigrid(4000, 800)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260303)])
    a1 = pf.acciones[0]
    assert (a1.accion, a1.motivo) == ("omitir", MOTIVO_CERRADO_4)
    assert (a1.caa_ide, a1.caa_cod, a1.caa_motivo, a1.caa_aviso,
            a1.caa_origen, a1.caa_nota) == (0, None, None, None, None, None)
    assert pf.acciones[1].accion == "escribir"
    assert pf.acciones[1].caa_ide == 701
    assert pf.conflictos == []
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260303)])
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_CERRADO_4}]
    assert [e["registro_id"] for e in r.escritas] == [2]
    assert [l["ide"] for l in cli.lineas if l["hmoide"] == 800] == [4000]


def test_f031_r11_otro_tipo_de_hora_no_choca() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)],
               lineas=[_linea_sigrid(4000, 800, horide=HE)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    assert pf.acciones[0].accion == "escribir"


def test_f031_r11_prevalece_sobre_r12() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO),
                       _parte(900, "PT26/00005")],
               lineas=[_linea_sigrid(4000, 800), _linea_sigrid(4001, 900)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    assert _acciones(pf) == {1: ("omitir", MOTIVO_CERRADO_4)}
    assert pf.conflictos == []


# ------------------- R12, R13 · choque en otro En registro ------------------- #

def test_f031_r12_choque_en_otro_parte_en_registro_es_conflicto() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005"),
                       _parte(905, "PT26/00006")],
               lineas=[_linea_sigrid(4001, 900)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (c,) = pf.conflictos
    assert (c.clave, c.parte_cod) == (f"501|{FECHA}|{HL}", "PT26/00005")
    assert [ls.ide for ls in c.lineas] == [4001]
    assert pf.partes[0].ide == 905
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.escritas == [] and [x.clave for x in
                                 r.pendientes_confirmacion] == [c.clave]
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={c.clave})
    assert (r.pisadas, r.borradas) == ([c.clave], 1)
    assert _inserts_por_parte(cli) == {905: [1]}


def test_f031_r12_conflicto_en_el_elegido_con_contexto() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005"),
                       _parte(800, "PT26/00004", est=CERRADO)],
               lineas=[_linea_sigrid(4001, 900),
                       _linea_sigrid(4002, 900, horide=HE),
                       _linea_sigrid(4003, 800, horide=HE)])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (c,) = pf.conflictos
    assert c.parte_cod == "PT26/00005"
    assert [ls.ide for ls in c.contexto] == [4002]


def test_f031_r13_pisar_no_borra_lineas_de_un_parte_cerrado() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=IMPUTADO)],
               lineas=[_linea_sigrid(4000, 800)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={f"501|{FECHA}|{HL}"})
    assert (r.pisadas, r.borradas, r.escritas) == ([], 0, [])
    assert [l["ide"] for l in cli.lineas] == [4000]


# ------------------------- R15 · lecturas que fallan ------------------------- #

@pytest.mark.parametrize("fallo", ["fallo_partes", "fallo_lineas"])
def test_f031_r15_fallo_de_lectura_tumba_la_peticion(fallo) -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    setattr(cli, fallo, RuntimeError("sigrid-api devolvio una respuesta "
                                     "truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    with pytest.raises(RuntimeError, match="truncada"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert "escribir" not in cli.llamadas and cli.lineas == []


# --------------------- R16 · mismo paso, preflight = ejecutar --------------------- #

def _escenario() -> SigridFake:
    return _cli(partes=[_parte(800, "PT26/00004", est=CERRADO),
                        _parte(900, "PT26/00005")],
                lineas=[_linea_sigrid(4000, 800),
                        _linea_sigrid(4001, 900, fec=20260303)])


def _lote_r16() -> list[LineaEntrada]:
    return [_lin(1), _lin(2, fecha_int=20260303),
            _lin(3, fecha_int=20260304)]


def test_f031_r16_preflight_y_ejecutar_coinciden_y_bajo_lock() -> None:
    pf = _pipeline(_escenario()).preflight(obra=_obra(), lineas=_lote_r16())
    cli = _escenario()
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)
    r = pipeline.ejecutar(obra=_obra(), lineas=_lote_r16())
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_CERRADO_4}]
    assert [c.clave for c in r.pendientes_confirmacion] == \
        [c.clave for c in pf.conflictos]
    assert [e["registro_id"] for e in r.escritas] == \
        [a.registro_id for a in pf.acciones if a.accion == "escribir"
         and a.registro_id not in pf.conflictos[0].registros]
    assert [(p.cod, p.complementario) for p in r.partes] == \
        [(p.cod, p.complementario) for p in pf.partes]
    assert "partes_del_periodo" in cli.llamadas
    assert sorted(cli.lineas_leidas) == [800, 900]


# ------------------------- R17 · el contrato del parte ------------------------- #

CLAVES_PARTE = {"ano", "mes", "existe", "ide", "cod", "creado", "estado",
                "complementario", "cerrados", "del_periodo", "aviso"}


def test_f031_r17_partes_del_preflight_http() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=IMPUTADO)])
    api = TestClient(build_app(SettingsFake(), pipeline=_pipeline(cli)))
    r = api.post("/api/registro/preflight", json={
        "obra": {"ide": 10, "codigo": "0100", "nombre": "Obra 0100"},
        "lineas": [dict(_lin(1).__dict__)]})
    assert r.status_code == 200
    (p,) = r.json()["partes"]
    assert set(p) == CLAVES_PARTE
    assert (p["ano"], p["mes"], p["existe"], p["ide"], p["cod"],
            p["creado"]) == (2026, 3, False, None, "PT26/00005", False)
    assert (p["estado"], p["complementario"], p["cerrados"]) == \
        (None, True, ["PT26/00004"])
    assert p["del_periodo"] == [{"ide": 800, "cod": "PT26/00004",
                                 "est": IMPUTADO}]
    assert p["aviso"].startswith("el parte PT26/00004 (Imputado)")


def test_f031_r17_partes_del_resultado() -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (p,) = resultado_a_dict(r)["partes"]
    assert set(p) == CLAVES_PARTE
    assert (p["existe"], p["creado"], p["cod"], p["estado"],
            p["complementario"]) == (True, True, "PT26/00005", REGISTRO,
                                     True)


# ------------------------------- R19 · el log ------------------------------- #

def test_f031_r19_info_por_periodo_sin_nombres(caplog) -> None:
    cli = _cli(partes=[_parte(800, "PT26/00004", est=CERRADO),
                       _parte(801, "PT26/00003", est=IMPUTADO)],
               lineas=[_linea_sigrid(4000, 800)],
               recursos={501: RecursoSigrid(501, 1, None, "12345678Z")})
    lineas = [_lin(1, dni="12345678Z"), _lin(2, fecha_int=20260303),
              _lin(3, fecha_int=20260402)]
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(cli).preflight(obra=_obra(), lineas=lineas)
    msgs = [r for r in caplog.records
            if r.getMessage().startswith("[registro] parte obra=")]
    assert [m.getMessage() for m in msgs] == [
        "[registro] parte obra=0100 periodo=2026/03 elegido=PT26/00005 "
        "estado=None complementario=si cerrados=2 omitidas_cerrado=1",
        "[registro] parte obra=0100 periodo=2026/04 elegido=PT26/00005 "
        "estado=None complementario=no cerrados=0 omitidas_cerrado=0"]
    assert all(m.levelno == logging.INFO for m in msgs)
    assert "Persona" not in caplog.text and "12345678Z" not in caplog.text


def test_f031_r19_estado_del_elegido_existente(caplog) -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005")])
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    assert ("[registro] parte obra=0100 periodo=2026/03 elegido=PT26/00005 "
            "estado=1 complementario=no cerrados=0 omitidas_cerrado=0") \
        in caplog.text
