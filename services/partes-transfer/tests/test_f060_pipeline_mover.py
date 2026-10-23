# tests/test_f060_pipeline_mover.py
"""F-060 · El CIZ de la racha se mueve en el pipeline de registro (R13-R27)
y en el doble `SigridFake` (design §5, §8).

  - Contrato y ajustes: `racha_registro_ids` llega por los dos canales
    (HTTP y cola) y `MOVER_CIZ` va apagado por defecto (R26, DA11).
  - Doble: `lineas_de_racha` y la op `mover` evaluan el `UPDATE` de
    `stmt_mover_linea` como SQL Server (WHERE optimista y guardas).
  - Pipeline: paso 6 bis (R13-R19, R25, R26) y paso 9 (R20-R24) con el
    ejemplo del humano dia a dia, el cambio de mes, la carrera y la
    reentrega.

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from config.settings import Settings
from domain.models.registro_models import (
    AccionLinea,
    HoraRecurso,
    LineaEntrada,
    LineaSigrid,
    ObraEntrada,
)
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
from interface_adapters.queue import transfer_consumer
from tests.dobles import SettingsFake, SigridFake

OBRA = 10
REC = 501
HN, CIV, CIZ = 1, 30, 40
HMO_SEP, HMO_OCT = 900, 901          # partes de septiembre y octubre
REGISTRO, CERRADO = 1, 3


def _obra(ide=OBRA, cod="0100", empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = 77
    return o


def _h(horide, cod, pre=0.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=None, defecto=False)


HORAS = {REC: [_h(HN, "HL01", 15.0), _h(2, "HE01", 25.0), _h(CIV, "CIV"),
               _h(CIZ, "CIZ")]}


# ------------------------- contrato y ajustes ------------------------- #

ENTORNO_MINIMO = {
    "SIGRID_API_BASE_URL": "http://sigrid.invalido",
    "SIGRID_API_FUNCTION_KEY": "clave-de-test",
}


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    for k, v in ENTORNO_MINIMO.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("MOVER_CIZ", raising=False)
    monkeypatch.chdir(tmp_path)
    return monkeypatch


def test_f060_r26_settings_mover_ciz_apagado_por_defecto(entorno) -> None:
    assert Settings().mover_ciz is False


@pytest.mark.parametrize("valor,esperado", [("true", True), ("1", True),
                                            ("false", False), ("0", False)])
def test_f060_r26_settings_mover_ciz_del_entorno(entorno, valor,
                                                 esperado) -> None:
    entorno.setenv("MOVER_CIZ", valor)
    assert Settings().mover_ciz is esperado


def test_f060_contrato_modelos_con_defecto() -> None:
    a = LineaEntrada(registro_id=1, fecha_int=20261004)
    b = LineaEntrada(registro_id=2, fecha_int=20261004)
    assert a.racha_registro_ids == [] and b.racha_registro_ids == []
    a.racha_registro_ids.append(9)
    assert b.racha_registro_ids == []          # sin lista compartida
    acc = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=10,
                      fecha_int=20261004)
    assert acc.mover is None
    ls = LineaSigrid(ide=1, reside=REC, fecha_int=20261004, horide=CIZ,
                     hora_codigo="CIZ", can=0.0, tot=0.0, synckey=None)
    assert ls.tex is None and ls.pos is None


class _PipelineEspia:
    """Apunta las lineas que le llegan (HTTP y cola) sin tocar Sigrid."""

    def __init__(self) -> None:
        self.lineas: list[LineaEntrada] = []

    def ejecutar(self, *, obra, lineas, pisar_claves=None, usuario=None):
        from domain.models.registro_models import ResultadoRegistro
        self.lineas.extend(lineas)
        return ResultadoRegistro(ok=True, obra_destino=obra,
                                 forzada_pruebas=False)


PETICION = {
    "obra": {"ide": OBRA, "codigo": "0100", "nombre": "Obra Uno"},
    "lineas": [
        {"registro_id": 4, "fecha_int": 20261004, "recurso_ide": REC,
         "es_incidencia": True, "incidencia_rol": "fin",
         "racha_registro_ids": [2, 3]},
        {"registro_id": 5, "fecha_int": 20261005, "recurso_ide": REC,
         "tipo_hora": "normal", "horas": 8.0}],
    "pisar_claves": [], "usuario": "ana",
}


def test_f060_contrato_http_trae_racha_registro_ids() -> None:
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    r = TestClient(app).post("/api/registro/ejecutar", json=PETICION)
    assert r.status_code == 200
    assert [l.racha_registro_ids for l in espia.lineas] == [[2, 3], []]


def test_f060_contrato_cola_trae_racha_registro_ids() -> None:
    _obra_d, lineas = transfer_consumer._a_dominio(PETICION)
    assert [l.racha_registro_ids for l in lineas] == [[2, 3], []]


def test_f060_contrato_payload_viejo_sin_la_clave() -> None:
    """Un sv4 anterior a F-060 no manda la clave: lista vacia (R26)."""
    viejo = {"obra": PETICION["obra"],
             "lineas": [{"registro_id": 4, "fecha_int": 20261004}]}
    _obra_d, lineas = transfer_consumer._a_dominio(viejo)
    assert lineas[0].racha_registro_ids == []
    espia = _PipelineEspia()
    app = build_app(SettingsFake(), pipeline=espia)  # type: ignore[arg-type]
    TestClient(app).post("/api/registro/ejecutar", json=viejo)
    assert espia.lineas[0].racha_registro_ids == []


# ================================ Doble ================================ #

def _parte(ide, cod, est=REGISTRO, ano=2026, mes=10) -> dict:
    return {"ide": ide, "obride": OBRA, "ano": ano, "mes": mes, "cod": cod,
            "emp": 1, "est": est}


def _fila(ide, *, fec=20261003, rid=3, hmoide=HMO_OCT, horide=CIZ,
          can=0.0, tex=None, enlazada=False, pos=192,
          reside=REC) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can, "tot": 0.0,
            "pos": pos, "synckey": f"partes:{rid}", "caaide": 702,
            "paride": 33, "tex": tex, "enlazada": enlazada, "ano": 2026,
            "mes": int(str(fec)[4:6]), "obride": OBRA, "cenide": 77}


def _cli(*filas, partes=None) -> SigridFake:
    return SigridFake(
        obras={"0100": _obra()}, horas=HORAS,
        partes=partes if partes is not None else [
            _parte(HMO_SEP, "PT26/00009", mes=9),
            _parte(HMO_OCT, "PT26/00010")],
        lineas=[dict(f) for f in filas])


def _stmt_mover(cli, linea, *, hmoide=HMO_OCT, fecha_int=20261004, rid=4,
                pos=192) -> dict:
    return cli.stmt_mover_linea(
        linea=linea, destino=_obra(), hmoide=hmoide, pos=pos,
        fecha_int=fecha_int, synckey=f"partes:{rid}", paride=34, caaide=703,
        ano=fecha_int // 10000, mes=(fecha_int // 100) % 100)


def test_f060_doble_lineas_de_racha_como_el_cliente() -> None:
    cli = _cli(_fila(7001, tex="PRUEBA-IA"), _fila(7002, rid=2, horide=CIV,
                                                   enlazada=True))
    out = cli.lineas_de_racha(["partes:3", "partes:2", "partes:9", None])
    a, b = out["partes:3"], out["partes:2"]
    assert set(out) == {"partes:3", "partes:2"}
    # El codigo de hora sale de `auxhor` (aqui, de los tipos del recurso).
    assert (a.ide, a.hora_codigo, a.tex, a.pos, a.hmoide, a.enlazada) == (
        7001, "CIZ", "PRUEBA-IA", 192, HMO_OCT, False)
    assert (b.hora_codigo, b.enlazada) == ("CIV", True)
    assert cli.racha_leidas == [["partes:2", "partes:3", "partes:9"]]


def test_f060_doble_estados_de_partes() -> None:
    cli = _cli(partes=[_parte(HMO_SEP, "PT26/00009", mes=9, est=CERRADO),
                       _parte(HMO_OCT, "PT26/00010")])
    assert cli.estados_de_partes([HMO_OCT, HMO_SEP, 555, None]) == {
        HMO_SEP: {"cod": "PT26/00009", "est": CERRADO, "obride": OBRA},
        HMO_OCT: {"cod": "PT26/00010", "est": REGISTRO, "obride": OBRA}}


def test_f060_doble_mover_actualiza_la_misma_fila() -> None:
    cli = _cli(_fila(7001, tex="nota"))
    linea = cli.lineas_de_racha(["partes:3"])["partes:3"]
    assert cli.escribir([_stmt_mover(cli, linea)]) == 1
    (fila,) = cli.lineas
    assert (fila["ide"], fila["fec"], fila["synckey"], fila["hmoide"],
            fila["paride"], fila["caaide"], fila["pos"]) == (
        7001, 20261004, "partes:4", HMO_OCT, 34, 703, 192)
    assert (fila["can"], fila["tot"], fila["tex"], fila["horide"]) == (
        0.0, 0.0, "nota", CIZ)


def test_f060_doble_mover_cambia_de_parte_y_mes() -> None:
    cli = _cli(_fila(7001, fec=20260930, hmoide=HMO_SEP))
    linea = cli.lineas_de_racha(["partes:3"])["partes:3"]
    assert cli.escribir([_stmt_mover(cli, linea, fecha_int=20261001,
                                     pos=256)]) == 1
    (fila,) = cli.lineas
    assert (fila["hmoide"], fila["fec"], fila["ano"], fila["mes"],
            fila["pos"]) == (HMO_OCT, 20261001, 2026, 10, 256)


@pytest.mark.parametrize("cambio", [
    {"can": 1.0}, {"enlazada": True}, {"synckey": "partes:99"},
    {"fec": 20261002}, {"horide": CIV}, {"reside": 999},
])
def test_f060_doble_mover_where_optimista(cambio) -> None:
    """Si la fila cambio desde que se leyo, 0 filas y nada se toca."""
    cli = _cli(_fila(7001))
    linea = cli.lineas_de_racha(["partes:3"])["partes:3"]
    cli.lineas[0].update(cambio)
    antes = [dict(f) for f in cli.lineas]
    assert cli.escribir([_stmt_mover(cli, linea)]) == 0
    assert cli.lineas == antes


@pytest.mark.parametrize("cerrado", [HMO_SEP, HMO_OCT])
def test_f060_doble_mover_guarda_de_origen_y_de_destino(cerrado) -> None:
    cli = _cli(_fila(7001, fec=20260930, hmoide=HMO_SEP))
    linea = cli.lineas_de_racha(["partes:3"])["partes:3"]
    next(p for p in cli.partes if p["ide"] == cerrado)["est"] = CERRADO
    antes = [dict(f) for f in cli.lineas]
    assert cli.escribir([_stmt_mover(cli, linea, fecha_int=20261001)]) == 0
    assert cli.lineas == antes


def test_f060_doble_mover_cuenta_para_el_cierre_en_la_ventana() -> None:
    """Como `insert` y `anular`: el cierre de F-034 puede caer antes."""
    cli = _cli(_fila(7001))
    linea = cli.lineas_de_racha(["partes:3"])["partes:3"]
    cli.cerrar_al_escribir = {HMO_OCT: CERRADO}
    assert cli.escribir([_stmt_mover(cli, linea)]) == 0
    assert cli.lineas[0]["fec"] == 20261003


# ======================= Pipeline · paso 6 bis ======================= #

def _st(*, mover=True, pruebas=False) -> SettingsFake:
    st = SettingsFake(obra_pruebas_forzar=pruebas)
    st.mover_ciz = mover
    return st


def _pipe(cli, *, mover=True, pruebas=False, lock=None) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=_st(mover=mover,
                                                      pruebas=pruebas),
                            lock=lock)


def _fin(rid, fecha_int, racha=(), *, rec=REC) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int, recurso_ide=rec,
                        nombre=f"Persona {rid}", es_incidencia=True,
                        incidencia_codigo="V", incidencia_rol="fin",
                        hora_ide=CIV, hora_codigo="CIV",
                        racha_registro_ids=list(racha))


def _ini(rid, fecha_int, racha=()) -> LineaEntrada:
    linea = _fin(rid, fecha_int, racha)
    linea.incidencia_rol = "inicio"
    return linea


def _trabajo(rid, fecha_int) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int,
                        recurso_ide=REC, nombre=f"Persona {rid}",
                        tipo_hora="normal", horas=8.0, hora_ide=HN)


def _pf(cli, lineas, **kw):
    return _pipe(cli, **kw).preflight(obra=_obra(), lineas=lineas)


def _acc(pf, rid) -> AccionLinea:
    return next(a for a in pf.acciones if a.registro_id == rid)


def test_f060_r13_mueve_el_ciz_de_la_racha_con_una_lectura() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    pf = _pf(cli, [_fin(4, 20261004, [1, 2, 3])])
    a = _acc(pf, 4)
    assert a.accion == "escribir" and a.hora_codigo == "CIZ"
    assert a.mover is not None and a.mover.ide == 7001
    assert cli.racha_leidas == [["partes:1", "partes:2", "partes:3"]]
    assert cli.estados_leidos == [[HMO_OCT]]


def test_f060_r13_una_sola_lectura_para_todas_las_acciones() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3),
               _fila(7101, fec=20261013, rid=13, reside=REC + 1))
    otro = _fin(14, 20261014, [13], rec=REC + 1)
    cli.horas[REC + 1] = HORAS[REC]
    pf = _pf(cli, [_fin(4, 20261004, [3]), otro, _trabajo(5, 20261005)])
    assert len(cli.racha_leidas) == 1 and len(cli.estados_leidos) == 1
    assert cli.racha_leidas[0] == ["partes:13", "partes:3"]
    assert _acc(pf, 4).mover.ide == 7001 and _acc(pf, 14).mover.ide == 7101
    assert _acc(pf, 5).mover is None


def test_f060_r13_solo_el_ciz_del_mismo_recurso() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3, reside=999))
    a = _acc(_pf(cli, [_fin(4, 20261004, [3])]), 4)
    assert a.accion == "escribir" and a.mover is None


def test_f060_r13_sin_candidatas_no_lee_partes() -> None:
    cli = _cli()
    a = _acc(_pf(cli, [_fin(4, 20261004, [3])]), 4)
    assert a.accion == "escribir" and a.mover is None
    assert cli.racha_leidas == [["partes:3"]] and cli.estados_leidos == []


def test_f060_r13_despues_de_la_idempotencia() -> None:
    """Una `fin` que ya esta en Sigrid es `ya_registrado`: no se busca su
    racha."""
    cli = _cli(_fila(7001, fec=20261003, rid=3),
               _fila(7002, fec=20261004, rid=4))
    a = _acc(_pf(cli, [_fin(4, 20261004, [3])]), 4)
    assert a.accion == "ya_registrado" and a.mover is None
    assert cli.racha_leidas == []


def test_f060_r13_dentro_del_lock_al_registrar() -> None:
    import threading
    lock = threading.Lock()
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    cli.vigilar_lock(lock)
    r = _pipe(cli, lock=lock).ejecutar(obra=_obra(),
                                       lineas=[_fin(4, 20261004, [3])])
    assert r.ok and [e["registro_id"] for e in r.escritas] == [4]
    assert "lineas_de_racha" in cli.llamadas


def test_f060_r13_solo_las_acciones_ciz() -> None:
    """Un inicio (CI*) con ids no busca nada."""
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    pf = _pf(cli, [_ini(4, 20261004, [3])])
    assert _acc(pf, 4).hora_codigo == "CIV" and _acc(pf, 4).mover is None
    assert cli.racha_leidas == []


def test_f060_r14_ciz_posterior_es_intermedio() -> None:
    cli = _cli(_fila(7001, fec=20261006, rid=6))
    pf = _pf(cli, [_fin(4, 20261004, [3, 5, 6])])
    a = _acc(pf, 4)
    assert a.accion == "omitir" and a.mover is None
    assert a.motivo.startswith("dia intermedio de la incidencia")
    assert "2026-10-06" in a.motivo and a.caa_ide == 0


def test_f060_r14_al_ejecutar_no_escribe_nada() -> None:
    cli = _cli(_fila(7001, fec=20261006, rid=6))
    r = _pipe(cli).ejecutar(obra=_obra(), lineas=[_fin(4, 20261004, [6])])
    assert r.escritas == [] and [o["registro_id"] for o in r.omitidas] == [4]
    assert "escribir" not in cli.llamadas
    assert cli.lineas[0]["fec"] == 20261006


def test_f060_r15_duplicados_warning_sin_nombres(caplog) -> None:
    cli = _cli(_fila(7001, fec=20261002, rid=2),
               _fila(7002, fec=20261003, rid=3))
    with caplog.at_level("WARNING"):
        pf = _pf(cli, [_fin(4, 20261004, [2, 3])])
    assert _acc(pf, 4).mover.ide == 7002
    avisos = [r.getMessage() for r in caplog.records
              if "ciz_duplicados" in r.getMessage()]
    assert avisos == ["[registro] ciz_duplicados registro_id=4 ide=7002 "
                      "duplicados=1"]
    assert "Persona" not in caplog.text


def test_f060_r15_sin_duplicados_no_avisa(caplog) -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    with caplog.at_level("WARNING"):
        _pf(cli, [_fin(4, 20261004, [3])])
    assert "ciz_duplicados" not in caplog.text


def test_f060_r17_ciz_en_parte_cerrado_se_omite() -> None:
    cli = _cli(_fila(7001, fec=20260930, rid=3, hmoide=HMO_SEP),
               partes=[_parte(HMO_SEP, "PT26/00009", mes=9, est=CERRADO),
                       _parte(HMO_OCT, "PT26/00010")])
    r = _pipe(cli).ejecutar(obra=_obra(), lineas=[_fin(4, 20261001, [3])])
    assert r.escritas == []
    (o,) = r.omitidas
    assert o["motivo"].startswith("ciz_en_parte_cerrado: ")
    assert "PT26/00009 (Cerrado)" in o["motivo"]
    assert len(cli.lineas) == 1 and cli.lineas[0]["fec"] == 20260930


def test_f060_r18_ciz_enlazado_se_omite() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3, enlazada=True))
    r = _pipe(cli).ejecutar(obra=_obra(), lineas=[_fin(4, 20261004, [3])])
    assert r.escritas == []
    (o,) = r.omitidas
    assert o["motivo"].startswith("linea_enlazada: ")
    assert "linea 7001" in o["motivo"] and "PT26/00010" in o["motivo"]
    assert len(cli.lineas) == 1


def _cli_pruebas(*filas) -> SigridFake:
    cli = _cli(*filas)
    cli.obras["0404"] = _obra(cod="0404")
    return cli


def test_f060_r19_en_pruebas_sin_marca_no_se_mueve() -> None:
    cli = _cli_pruebas(_fila(7001, fec=20261003, rid=3, tex=None))
    a = _acc(_pf(cli, [_fin(4, 20261004, [3])], pruebas=True), 4)
    assert a.accion == "escribir" and a.mover is None


def test_f060_r19_en_pruebas_con_marca_se_mueve() -> None:
    cli = _cli_pruebas(_fila(7001, fec=20261003, rid=3, tex="PRUEBA-IA"))
    a = _acc(_pf(cli, [_fin(4, 20261004, [3])], pruebas=True), 4)
    assert a.mover is not None and a.mover.ide == 7001


def test_f060_r19_fuera_de_pruebas_la_marca_da_igual() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3, tex=None))
    assert _acc(_pf(cli, [_fin(4, 20261004, [3])]), 4).mover.ide == 7001


def test_f060_r25_preflight_consultivo_no_escribe() -> None:
    cli = _cli(_fila(7001, fec=20261006, rid=6),
               _fila(7002, fec=20261013, rid=13))
    pf = _pf(cli, [_fin(4, 20261004, [6]), _fin(14, 20261014, [13])])
    assert _acc(pf, 4).accion == "omitir"
    assert _acc(pf, 14).mover.ide == 7002
    assert "escribir" not in cli.llamadas
    assert [f["fec"] for f in cli.lineas] == [20261006, 20261013]


@pytest.mark.parametrize("mover,racha", [(False, [3]), (True, [])])
def test_f060_r26_apagado_o_sin_ids_como_hoy(mover, racha) -> None:
    """Apagado (o sin ids): el `fin` escribe un CIZ nuevo aunque la racha
    ya tenga uno, y no se lee nada de mas."""
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    pf = _pf(cli, [_fin(4, 20261004, racha)], mover=mover)
    assert _acc(pf, 4).accion == "escribir" and _acc(pf, 4).mover is None
    assert cli.racha_leidas == [] and cli.estados_leidos == []
    r = _pipe(cli, mover=mover).ejecutar(obra=_obra(),
                                         lineas=[_fin(4, 20261004, racha)])
    assert [e["registro_id"] for e in r.escritas] == [4]
    assert "movida_de" not in r.escritas[0]
    assert sorted(f["fec"] for f in cli.lineas) == [20261003, 20261004]


def test_f060_r26_settings_sin_el_ajuste_es_apagado() -> None:
    cli = _cli(_fila(7001, fec=20261003, rid=3))
    pipe = RegistroPipeline(cliente=cli, settings=SettingsFake())
    a = _acc(pipe.preflight(obra=_obra(), lineas=[_fin(4, 20261004, [3])]),
             4)
    assert a.mover is None and cli.racha_leidas == []
