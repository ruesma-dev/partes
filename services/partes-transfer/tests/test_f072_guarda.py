# tests/test_f072_guarda.py
"""F-072 · La guarda de sv5 en las obras agrupadas (R36, R37, R39).

Cuando la obra pedida es agrupada (`POSTVENTA_OBRA_COD` o `VAR_OBRA_COD`),
sv5 lee su presupuesto UNA vez por petición y, antes de escribir, omite la
línea sin la marca de su entrada, sin partida, con una partida que no es hoja
activa de esa obra o, en VAR, fuera del universo VAR. El motivo empieza por
`partida_agrupada:`, nombra la partida por su código, sin tildes y en 255
caracteres. En modo pruebas, igual, por la obra pedida. Si la lectura falla
(o viene `truncated`), la petición falla entera sin escribir.

Sin red: `SigridFake` ampliado (`f072_comun`) y un sigrid-api falso.
"""
from __future__ import annotations

import httpx
import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_registro import (
    MOTIVO_PARTIDA_AGRUPADA,
    motivo_partida_agrupada,
)
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests import f072_comun as c
from tests.dobles import SettingsFake


def _pf(obra, lineas, cli=None, **st):
    cli = cli or c.ClienteF072()
    pf = RegistroPipeline(cliente=cli, settings=c.SettingsF072(**st)).preflight(
        obra=obra, lineas=lineas)
    return {a.registro_id: (a.accion, a.motivo) for a in pf.acciones}, cli


# --------------------------------- R36 ---------------------------------- #

def test_f072_r36_la_entrada_buena_se_escribe():
    acc, cli = _pf(c.VARO, [c.linea(1, 91012, "var"), c.linea(2, 91013, "var")])
    assert acc == {1: ("escribir", None), 2: ("escribir", None)}
    assert cli.presupuestos_leidos == [9101]
    acc, _ = _pf(c.PV, [c.linea(1, 90011, "postventa")])
    assert acc == {1: ("escribir", None)}


@pytest.mark.parametrize("lin, trozo", [
    (c.linea(1, 91012, None), "sin entrada var"),
    (c.linea(1, 91012, "postventa"), "sin entrada var"),
    (c.linea(1, 91012, "manual"), "sin entrada var"),
    (c.linea(1, None, "var"), "sin partida"),
    (c.linea(1, 91015, "var"), "la partida 32 no es una partida activa"),
    (c.linea(1, 91014, "var"), "la partida 31 no es una partida activa"),
    (c.linea(1, 90011, "var", cod="0578B"),
     "la partida 0578B no es una partida activa"),
    (c.linea(1, 77777, "var"), "la partida 77777 no es una partida activa"),
    (c.linea(1, 91011, "var"), "la partida 28 esta fuera del universo VAR"),
], ids=["sin-marca", "otra-marca", "manual", "sin-partida", "capitulo",
        "de-baja", "de-otra-obra", "desconocida", "var-bajo-el-umbral"])
def test_f072_r36_omite_en_var(lin, trozo):
    acc, cli = _pf(c.VARO, [lin])
    accion, motivo = acc[1]
    assert accion == "omitir"
    assert motivo.startswith(f"{MOTIVO_PARTIDA_AGRUPADA}: "), motivo
    assert trozo in motivo, motivo
    assert cli.lineas == []


def test_f072_r36_omite_en_postventa():
    acc, _ = _pf(c.PV, [c.linea(1, 90015, "postventa"), c.linea(2, 90011),
                        c.linea(3, 90011, "postventa")])
    assert acc[1][0] == acc[2][0] == "omitir"
    assert "0700" in acc[1][1] and "sin entrada postventa" in acc[2][1]
    assert acc[3] == ("escribir", None)


def test_f072_r36_postventa_no_mira_el_umbral_var():
    """El universo VAR solo cuenta en la obra VAR: en postventa una hoja
    activa con número < desde vale."""
    pres = dict(c.PRESUPUESTOS)
    pres[c.PV.ide] = pres[c.PV.ide] + [
        c.PartidaHoja(90020, "05", "OBRA 05", True, True)]
    acc, _ = _pf(c.PV, [c.linea(1, 90020, "postventa")],
                 c.ClienteF072(presupuestos=pres))
    assert acc == {1: ("escribir", None)}


def test_f072_r36_una_sola_lectura_por_peticion():
    cli = c.ClienteF072()
    RegistroPipeline(cliente=cli, settings=c.SettingsF072()).ejecutar(
        obra=c.VARO, lineas=[c.linea(1, 91012, "var"), c.linea(2, 91013, "var"),
                             c.linea(3, 91012)])
    assert cli.presupuestos_leidos == [9101]
    assert sorted(l["paride"] for l in cli.lineas) == [91012, 91013]


def test_f072_r36_modo_pruebas_por_la_obra_pedida():
    acc, cli = _pf(c.VARO, [c.linea(1, 91012, "var"), c.linea(2, 91012)],
                   obra_pruebas_forzar=True)
    assert cli.presupuestos_leidos == [9101]
    assert acc[1] == ("escribir", None) and acc[2][0] == "omitir"
    RegistroPipeline(cliente=cli, settings=c.SettingsF072(
        obra_pruebas_forzar=True)).ejecutar(
        obra=c.VARO, lineas=[c.linea(1, 91012, "var")])
    assert [(l["paride"], l["tex"]) for l in cli.lineas] == [(91012, "PRUEBA-IA")]


def test_f072_r36_las_obras_normales_no_leen_presupuesto():
    acc, cli = _pf(c.NORMAL, [c.linea(1, None), c.linea(2, 300, "parte")])
    assert acc == {1: ("escribir", None), 2: ("escribir", None)}
    assert cli.presupuestos_leidos == []


def test_f072_r3_sin_ajustes_la_obra_var_como_siempre():
    cli = c.ClienteF072()
    pf = RegistroPipeline(cliente=cli, settings=SettingsFake()).preflight(
        obra=c.VARO, lineas=[c.linea(1, None)])
    assert pf.acciones[0].accion == "escribir"
    assert cli.presupuestos_leidos == []


def test_f072_r36_la_omision_del_recurso_manda():
    """Una línea ya omitida por el recurso conserva su motivo (F-023)."""
    from domain.models.registro_models import RecursoSigrid

    cli = c.ClienteF072(recursos={501: RecursoSigrid(501, 28, 0, None)})
    acc, _ = _pf(c.VARO, [c.linea(1, 91012)], cli)
    assert acc[1][0] == "omitir"
    assert not acc[1][1].startswith(MOTIVO_PARTIDA_AGRUPADA)


# ---------------------------- motivo puro ------------------------------- #

def test_f072_r36_motivo_sin_tildes_y_como_mucho_255():
    hojas = c.PRESUPUESTOS[c.VARO.ide]
    largo = "Ñandú-" * 80
    m = motivo_partida_agrupada(c.linea(1, 123, "var", cod=largo), hojas,
                                "var", 29, obra_cod="VAR")
    assert len(m) <= 255 and m.isascii(), m
    assert m.startswith("partida_agrupada: la partida Nandu-")
    assert motivo_partida_agrupada(c.linea(1, 91012, "var"), hojas, "var", 29,
                                   obra_cod="VAR") is None
    assert motivo_partida_agrupada(c.linea(1, 91011, "var"), hojas, "var", 28,
                                   obra_cod="VAR") is None


# --------------------------------- R37 ---------------------------------- #

@pytest.mark.parametrize("error", [RuntimeError("sigrid-api caido"),
                                   RuntimeError("respuesta truncada")])
def test_f072_r37_si_la_lectura_falla_no_se_escribe_nada(error):
    cli = c.ClienteF072()
    cli.fallo_presupuesto = error
    pipe = RegistroPipeline(cliente=cli, settings=c.SettingsF072())
    with pytest.raises(RuntimeError):
        pipe.preflight(obra=c.VARO, lineas=[c.linea(1, 91012, "var")])
    with pytest.raises(RuntimeError):
        pipe.ejecutar(obra=c.VARO, lineas=[c.linea(1, 91012, "var")])
    assert cli.lineas == [] and cli.partes == []


# --------------------------------- R39 ---------------------------------- #

class SigridApiFalso:
    def __init__(self, filas=(), truncated=False):
        self.filas = list(filas)
        self.truncated = truncated
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        return httpx.Response(200, json={
            "ok": True, "columns": ["IDE", "COD", "RES", "TIPDES", "HIJOS"],
            "rows": self.filas, "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kw):
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd", **kw)


def test_f072_r39_partidas_de_obra_pide_el_max_rows_y_parametriza(monkeypatch):
    falso = SigridApiFalso(filas=[[1, "CD", "COSTES", 0, 1],
                                  [2, " 29 ", "VARIOS", 0, 0],
                                  [3, "31", "BAJA", 1, 0]])
    hojas = _cliente(monkeypatch, falso, max_rows=4321).partidas_de_obra(9101)
    assert falso.lecturas[0]["max_rows"] == 4321
    assert falso.lecturas[0]["parameters"] == [9101]
    assert "obrparpar" in falso.lecturas[0]["sql"]
    assert [(h.ide, h.cod, h.es_hoja, h.activa) for h in hojas] == [
        (1, "CD", False, True), (2, "29", True, True), (3, "31", True, False)]


def test_f072_r39_partidas_de_obra_truncada_es_error(monkeypatch):
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(monkeypatch, SigridApiFalso(truncated=True)).partidas_de_obra(1)


# ------------------------- R33: la marca por HTTP ------------------------ #

def test_f072_r33_la_marca_llega_por_http_a_la_linea():
    """`LineaIn` (registro por HTTP) lleva `partida_metodo` a la
    `LineaEntrada`; sin ella, None (un sv4 anterior a F-072)."""
    from domain.models.registro_models import LineaEntrada
    from interface_adapters.api.app import LineaIn

    con = LineaIn(registro_id=1, partida_ide=91012, partida_metodo="var")
    assert LineaEntrada(**con.model_dump()).partida_metodo == "var"
    assert LineaEntrada(**LineaIn(registro_id=2).model_dump()
                        ).partida_metodo is None


def test_f072_r36_modo_pruebas_obra_pedida_solo_por_codigo():
    """En modo pruebas, una obra pedida sin `ide` se busca por su código; si
    Sigrid no la conoce, no es agrupada y no hay guarda."""
    sin_ide = c.obra(None, "VAR")
    acc, cli = _pf(sin_ide, [c.linea(1, 91012)], obra_pruebas_forzar=True)
    assert cli.presupuestos_leidos == [9101] and acc[1][0] == "omitir"
    desconocida = c.obra(None, "NO-EXISTE")
    acc, cli = _pf(desconocida, [c.linea(1, 91012)], obra_pruebas_forzar=True)
    assert cli.presupuestos_leidos == [] and acc[1] == ("escribir", None)
