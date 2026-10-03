# tests/test_f019_pipeline.py
"""F-019 · el pipeline y el contrato de sv5 con la accion `dedicacion`.

R5 (Sigrid manda: una linea que iria a dedicacion y ya esta en Sigrid por
su synckey es `ya_registrado`), R6 (`dedicacion` no escribe, no abre parte,
no resuelve cuenta ni entra en conflictos), R7 (preflight con
`resumen.dedicacion`) y R8 (`dedicacion` en el resultado, por HTTP y por
`q-transfer-result`, y en el resultado fallido).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import json

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    ResultadoRegistro,
)
from fastapi.testclient import TestClient
from infrastructure.sigrid.sigrid_write_client import synckey_de
from interface_adapters.api.app import build_app
from interface_adapters.queue.transfer_consumer import _resultado_fallido
from interface_adapters.resultado_json import resultado_a_dict
from tests.dobles import SettingsFake, SigridFake
from tests.test_f002_transfer_consumer import PETICION_ID, Montaje, _peticion

FECHA = 20260302
OBRA = ObraEntrada(ide=10, codigo="0100", nombre="Obra Uno", empresa=1)
HL, HE, CIV, MENC, MCAP, HECAP = 1, 2, 3, 5, 6, 7


def _h(horide, cod, pre=10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre)


HORAS = {
    501: [_h(HL, "HL01"), _h(HE, "HE01", 15.0), _h(CIV, "CIV", 0.0)],
    602: [_h(MENC, "MENC", 0.0), _h(CIV, "CIV", 0.0)],      # mensual
    603: [_h(MCAP, "MCAP", 0.0), _h(HECAP, "HECAP", 18.0)],  # capataz
}


def _cli(**kw) -> SigridFake:
    o = ObraEntrada(ide=10, codigo="0100", nombre="Obra Uno", empresa=1)
    o.cenide = 0
    return SigridFake(obras={"0100": o}, horas=HORAS, **kw)


def _settings(encendido: bool | None) -> SettingsFake:
    st = SettingsFake()
    if encendido is not None:
        st.mensuales_a_dedicacion = encendido
    return st


def _pipeline(cli, encendido: bool | None = True) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=_settings(encendido))


def _lin(rid, recurso, tipo="normal", horas=8.0) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, tipo_hora=tipo, horas=horas,
                        nombre=f"Persona {rid}")


def _inc(rid, recurso) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, es_incidencia=True,
                        incidencia_rol="inicio", incidencia_codigo="V",
                        hora_ide=CIV, hora_codigo="CIV",
                        nombre=f"Persona {rid}")


def _lote() -> list[LineaEntrada]:
    """Lineas NUEVAS en cada llamada: el pipeline puede mutarlas."""
    return [_lin(1, 501), _lin(2, 602), _inc(3, 602), _lin(4, 603),
            _lin(5, 603, "extra", 2.0)]


ESPERADO_DEDICACION = [
    {"registro_id": 2, "recurso_ide": 602, "codigo_mes": "MENC"},
    {"registro_id": 3, "recurso_ide": 602, "codigo_mes": "MENC"},
    {"registro_id": 4, "recurso_ide": 603, "codigo_mes": "MCAP"},
]


# ============================ el pipeline lee el ajuste ======================== #

def test_f019_r1_el_pipeline_sin_ajuste_decide_como_siempre() -> None:
    """Un settings sin el atributo (los de antes de F-019) = apagado."""
    r = _pipeline(_cli(), encendido=None).ejecutar(obra=OBRA,
                                                   lineas=_lote())
    assert r.dedicacion == []
    assert {e["registro_id"] for e in r.escritas} == {1, 3, 5}
    assert {o["registro_id"] for o in r.omitidas} == {2, 4}


def test_f019_r1_el_pipeline_apagado_decide_como_siempre() -> None:
    r = _pipeline(_cli(), encendido=False).ejecutar(obra=OBRA,
                                                    lineas=_lote())
    assert r.dedicacion == []
    assert {e["registro_id"] for e in r.escritas} == {1, 3, 5}


def test_f019_r8_encendido_el_resultado_lleva_dedicacion() -> None:
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=OBRA, lineas=_lote())
    assert r.dedicacion == ESPERADO_DEDICACION
    # Solo se escriben la del trabajador por horas y la extra del capataz.
    assert [e["registro_id"] for e in r.escritas] == [1, 5]
    assert r.omitidas == [] and r.ya_registradas == []
    assert sorted(int(l["synckey"].split(":")[1]) for l in cli.lineas) == \
        [1, 5]


def test_f019_r8_solo_dedicacion_sin_nada_que_escribir() -> None:
    """La salida temprana de `registrar` tambien lleva la lista."""
    cli = _cli()
    r = _pipeline(cli).ejecutar(obra=OBRA, lineas=[_lin(2, 602),
                                                   _inc(3, 602)])
    assert r.ok is True
    assert r.dedicacion == ESPERADO_DEDICACION[:2]
    assert r.escritas == [] and cli.lineas == []


# ================================ R5 · Sigrid manda ============================ #

def test_f019_r5_si_ya_esta_en_sigrid_es_ya_registrado() -> None:
    cli = _cli()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4321, "hmoide": 700, "reside": 602,
                       "fec": FECHA, "horide": CIV, "hora_codigo": "CIV",
                       "can": 0.0, "tot": 0.0, "pos": 64,
                       "synckey": synckey_de(3)})
    pipeline = _pipeline(cli)
    pf = pipeline.preflight(obra=OBRA, lineas=_lote())
    por_id = {a.registro_id: a for a in pf.acciones}
    assert por_id[3].accion == "ya_registrado"
    assert por_id[3].hmores_ide == 4321
    assert por_id[3].motivo == ("ya registrada en Sigrid (linea 4321); no "
                                "se duplica")
    assert por_id[2].accion == "dedicacion"
    r = pipeline.ejecutar(obra=OBRA, lineas=_lote())
    assert r.ya_registradas == [3]
    assert [d["registro_id"] for d in r.dedicacion] == [2, 4]


def test_f019_r5_la_synckey_de_dedicacion_se_consulta() -> None:
    cli = _cli()
    _pipeline(cli).preflight(obra=OBRA, lineas=[_lin(2, 602)])
    assert "lineas_por_synckey" in cli.llamadas


# ================================== R6 · inerte ================================ #

def test_f019_r6_dedicacion_no_abre_parte_ni_escribe_ni_pide_cuenta() -> None:
    cli = _cli()
    o = cli.obras["0100"]
    o.cenide = 77
    pipeline = _pipeline(cli)
    pf = pipeline.preflight(obra=OBRA, lineas=[_lin(2, 602), _inc(3, 602)])
    assert pf.partes == [] and pf.conflictos == []
    assert all(a.caa_ide == 0 and a.caa_motivo is None for a in pf.acciones)
    pipeline.ejecutar(obra=OBRA, lineas=[_lin(2, 602), _inc(3, 602)])
    assert cli.partes == [] and cli.lineas == []
    assert cli.cuentas_leidas == []
    for llamada in ("partes_existentes", "siguiente_cod_pt", "escribir",
                    "lineas_existentes", "max_pos"):
        assert llamada not in cli.llamadas, llamada


def test_f019_r6_dedicacion_no_entra_en_conflictos() -> None:
    """Aunque el parte del mes tenga lineas de ese recurso y dia."""
    cli = _cli()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4000, "hmoide": 700, "reside": 602,
                       "fec": FECHA, "horide": MENC, "hora_codigo": "MENC",
                       "can": 8.0, "tot": 0.0, "pos": 64, "synckey": None})
    r = _pipeline(cli).ejecutar(obra=OBRA, lineas=[_lin(2, 602),
                                                   _lin(1, 501)])
    assert r.pendientes_confirmacion == []
    assert [d["registro_id"] for d in r.dedicacion] == [2]
    assert [e["registro_id"] for e in r.escritas] == [1]


# ============================== R7 · preflight HTTP ============================ #

def _api(cli, encendido=True) -> TestClient:
    return TestClient(build_app(SettingsFake(),
                                pipeline=_pipeline(cli, encendido)))


def _cuerpo(lineas: list[LineaEntrada]) -> dict:
    return {"obra": {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"},
            "lineas": [dict(l.__dict__) for l in lineas],
            "pisar_claves": [], "usuario": "ana"}


def test_f019_r7_el_preflight_cuenta_y_lista_las_de_dedicacion() -> None:
    r = _api(_cli()).post("/api/registro/preflight", json=_cuerpo(_lote()))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["resumen"] == {"escribir": 2, "omitir": 0,
                                 "ya_registrado": 0, "dedicacion": 3,
                                 "conflictos": 0}
    acciones = {a["registro_id"]: a for a in cuerpo["acciones"]}
    assert (acciones[2]["accion"], acciones[2]["codigo_mes"]) == (
        "dedicacion", "MENC")
    assert acciones[1]["codigo_mes"] is None


def test_f019_r7_apagado_el_resumen_es_el_de_siempre() -> None:
    """Sin lineas a dedicacion el resumen no cambia (contrato de F-002)."""
    r = _api(_cli(), encendido=False).post("/api/registro/preflight",
                                           json=_cuerpo(_lote()))
    assert r.json()["resumen"] == {"escribir": 3, "omitir": 2,
                                   "ya_registrado": 0, "conflictos": 0}


def test_f019_r7_n_dedicacion_cuenta_solo_las_de_dedicacion() -> None:
    pf = _pipeline(_cli()).preflight(obra=OBRA, lineas=_lote())
    assert (pf.n_dedicacion, pf.n_escribir, pf.n_omitir) == (3, 2, 0)


# ================================ R8 · el contrato ============================= #

def test_f019_r8_ejecutar_por_http_devuelve_dedicacion() -> None:
    r = _api(_cli()).post("/api/registro/ejecutar", json=_cuerpo(_lote()))
    assert r.status_code == 200
    assert r.json()["dedicacion"] == ESPERADO_DEDICACION


def test_f019_r8_resultado_a_dict_lleva_la_clave() -> None:
    r = ResultadoRegistro(ok=True, obra_destino=OBRA, forzada_pruebas=False,
                          dedicacion=[{"registro_id": 9, "recurso_ide": 1,
                                       "codigo_mes": "MX"}])
    assert resultado_a_dict(r)["dedicacion"] == [
        {"registro_id": 9, "recurso_ide": 1, "codigo_mes": "MX"}]
    vacio = ResultadoRegistro(ok=True, obra_destino=OBRA,
                              forzada_pruebas=False)
    assert resultado_a_dict(vacio)["dedicacion"] == []


def test_f019_r8_el_resultado_fallido_lleva_dedicacion_vacia() -> None:
    assert _resultado_fallido("boom")["dedicacion"] == []


def test_f019_r8_la_cola_publica_dedicacion(monkeypatch) -> None:
    lineas = [{"registro_id": 2, "fecha_int": FECHA, "recurso_ide": 602,
               "tipo_hora": "normal", "horas": 8.0},
              {"registro_id": 1, "fecha_int": FECHA, "recurso_ide": 501,
               "tipo_hora": "normal", "horas": 8.0}]
    m = Montaje(monkeypatch, _cli(), peticion=_peticion(lineas=lineas))
    m.settings.mensuales_a_dedicacion = True
    m.handler(m.mensaje)
    r = m.resultado_publicado()["resultado"]
    assert r["dedicacion"] == [{"registro_id": 2, "recurso_ide": 602,
                                "codigo_mes": "MENC"}]
    assert [e["registro_id"] for e in r["escritas"]] == [1]
    assert json.loads(json.dumps(r)) == r
    assert m.mensajes_resultado == [
        {"peticion_id": PETICION_ID,
         "blob": f"resultados/{PETICION_ID}.json"}]


@pytest.mark.parametrize("encendido", [False, None])
def test_f019_r8_la_cola_apagada_publica_dedicacion_vacia(monkeypatch,
                                                          encendido) -> None:
    lineas = [{"registro_id": 2, "fecha_int": FECHA, "recurso_ide": 602,
               "tipo_hora": "normal", "horas": 8.0}]
    m = Montaje(monkeypatch, _cli(), peticion=_peticion(lineas=lineas))
    if encendido is not None:
        m.settings.mensuales_a_dedicacion = encendido
    m.handler(m.mensaje)
    r = m.resultado_publicado()["resultado"]
    assert r["dedicacion"] == []
    assert [o["registro_id"] for o in r["omitidas"]] == [2]
