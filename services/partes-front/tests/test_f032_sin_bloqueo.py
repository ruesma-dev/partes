# tests/test_f032_sin_bloqueo.py
"""F-032 · R21–R24: sv4 ya no bloquea el registro por el calendario (DA17 = B).

Con un proveedor NO fiable (trabajador sin fila en `festivos_trabajador`,
o la tabla sin leer) el preflight lleva `aviso_sesame` en la obra
afectada, nunca `sesame_bloqueo`; `/api/aprobar/ejecutar` y
`/api/aprobar/encolar` registran o publican cada obra sin override,
`forzar_sin_sesame` se ignora y ninguna linea nueva se marca
`[SIN-SESAME]` (R21, R22). El dia de ajuste de F-056 se calcula con el
calendario resuelto aunque no sea fiable (R23). Una linea que YA lleve la
marca la conserva, con su badge (R24).

SQLite en memoria y dobles de sv5, del publisher y del calendario; sin red.
Datos sinteticos.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_dias
from tests.test_f003_r2_vistas_festivos import ProveedorFake
from tests.test_f022_aprobar_seleccion import (
    DNI_A,
    DNI_B,
    CalendarioFalso,
    PublisherFalso,
    Sv5Falso,
    _codigo,
    _escenario,
)
from tests.test_f046_aplicar import RecalculoFake
from tests.test_f056_decisiones import (
    CalendarioNoFiable,
    Sv5Franq,
    _acc_he,
    _decision,
    _dia15,
    _filas,
)

DIA = "2026-05-18"      # lunes laborable
MARCA = ("[SIN-SESAME] registrado con override: calendario de Sesame no "
         "disponible")
APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "TRANSFER_BASE_URL": "http://sv5.interno",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


class Sv5Simple:
    def __init__(self) -> None:
        self.ejecutadas: list[dict] = []

    def preflight(self, payload: dict) -> dict:
        return {"ok": True, "conflictos": [],
                "escribir": len(payload.get("lineas") or [])}

    def ejecutar(self, payload: dict) -> dict:
        self.ejecutadas.append(payload)
        return {"ok": True,
                "escritas": [{"registro_id": l["registro_id"], "hmoide": 1,
                              "hmores_ide": 2, "parte_cod": "P1"}
                             for l in payload["lineas"]],
                "omitidas": [], "ya_registradas": []}


def _un_trabajador(*, fiable=False, publisher="si"):
    """Un lunes de 8 h + 2 h extra de un trabajador SIN fila (no fiable)."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_dias(fabrica, [{"fecha": DIA, "horas": 8.0},
                                 {"fecha": DIA, "horas": 2.0,
                                  "tipo": "extra"}])
    sv5 = Sv5Simple()
    pub = PublisherFalso() if publisher == "si" else None
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=sv5, publisher=pub,
                    calendario_provider=ProveedorFake(
                        por_dni={"12345678Z": set()}, fiable=fiable))
    return TestClient(app), fabrica, ids, sv5, pub


def _dos_obras(*, no_fiables=(DNI_B,), publisher="si", sv5=None):
    """obr-10 con una linea de B (sin fila) y obr-20 con dos de A."""
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    sv5 = sv5 or Sv5Falso()
    pub = PublisherFalso() if publisher == "si" else None
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=sv5, publisher=pub,
                    calendario_provider=CalendarioFalso(no_fiables=no_fiables))
    return TestClient(app), fabrica, ids, sv5, pub


def _post(cliente, ruta, ids, **extra):
    return cliente.post(f"/api/aprobar/{ruta}",
                        json=dict({"registro_ids": ids}, **extra))


# ------------------------- R21, R22 · el preflight ---------------------- #

def test_f032_r21_preflight_sin_bloqueo_y_con_aviso(entorno) -> None:
    cliente, _f, ids, _sv5, _p = _un_trabajador()
    r = _post(cliente, "preflight", ids)
    assert r.status_code == 200
    datos = r.json()
    assert "sesame_bloqueo" not in datos
    assert datos["aviso_sesame"]


def test_f032_r22_preflight_fiable_sin_aviso(entorno) -> None:
    cliente, _f, ids, _sv5, _p = _un_trabajador(fiable=True)
    datos = _post(cliente, "preflight", ids).json()
    assert "aviso_sesame" not in datos
    assert "sesame_bloqueo" not in datos


def test_f032_r22_aviso_solo_en_la_obra_afectada(entorno) -> None:
    cliente, _f, ids, _sv5, _p = _dos_obras()
    cuerpo = _post(cliente, "preflight", ids["o10_b"] + ids["o20_a"]).json()
    o10, o20 = cuerpo["grupos"]
    assert o10["aviso_sesame"]
    assert "aviso_sesame" not in o20
    assert all("sesame_bloqueo" not in g for g in cuerpo["grupos"])
    assert "sesame_bloqueo" not in cuerpo


def test_f032_r22_lo_no_pedido_no_avisa(entorno) -> None:
    """La linea de B es de la misma obra, pero si no se pide no avisa."""
    cliente, _f, ids, _sv5, _p = _dos_obras()
    cuerpo = _post(cliente, "preflight", ids["o10_a"],
                   ambito={"vista": "obra", "obra_key": "obr-10",
                           "period": "2026-03", "mode": "nomina"}).json()
    assert "aviso_sesame" not in cuerpo


# ------------------------- R21 · ejecutar y encolar --------------------- #

def test_f032_r21_ejecutar_registra_sin_override_y_sin_marca(
        entorno, caplog) -> None:
    cliente, fabrica, ids, sv5, _p = _un_trabajador()
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, "ejecutar", ids)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert len(sv5.ejecutadas) == 1
    for rid in ids:
        estado, motivo, *_ = estados_sigrid(fabrica, ids)[rid]
        assert (estado, motivo) == ("registrado", None)
    assert "BLOQUEADO" not in caplog.text
    assert "FORZADO" not in caplog.text


def test_f032_r21_forzar_sin_sesame_se_ignora(entorno, caplog) -> None:
    cliente, fabrica, ids, sv5, _p = _un_trabajador()
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, "ejecutar", ids, forzar_sin_sesame=True)
    assert r.status_code == 200
    assert len(sv5.ejecutadas) == 1
    assert set(sv5.ejecutadas[0]) == {"obra", "lineas", "pisar_claves",
                                      "usuario"}
    assert [estados_sigrid(fabrica, ids)[i][1] for i in ids] == [None, None]
    assert "FORZADO" not in caplog.text


def test_f032_r21_encolar_publica_sin_override(entorno) -> None:
    cliente, fabrica, ids, _sv5, pub = _un_trabajador()
    antes = estados_sigrid(fabrica, ids)
    r = _post(cliente, "encolar", ids)
    assert r.status_code == 200, r.text
    assert len(pub.publicadas) == 1
    assert [estados_sigrid(fabrica, ids)[i][1] for i in ids] == \
        [antes[i][1] for i in ids]


def test_f032_r21_encolar_con_forzar_tambien_publica(entorno) -> None:
    """Antes era un 422 («el override no vale por la cola»)."""
    cliente, _f, ids, _sv5, pub = _un_trabajador()
    r = _post(cliente, "encolar", ids, forzar_sin_sesame=True)
    assert r.status_code == 200, r.text
    assert len(pub.publicadas) == 1


def test_f032_r21_encolar_sin_publisher_registra_sin_marca(entorno) -> None:
    cliente, fabrica, ids, sv5, _p = _un_trabajador(publisher=None)
    r = _post(cliente, "encolar", ids)
    assert r.status_code == 200
    assert r.json()["modo"] == "sincrono"
    assert len(sv5.ejecutadas) == 1
    assert [estados_sigrid(fabrica, ids)[i][:2] for i in ids] == \
        [("registrado", None)] * 2


def test_f032_r21_ejecutar_varias_obras_todas_se_envian(entorno) -> None:
    cliente, fabrica, ids, sv5, _p = _dos_obras()
    r = _post(cliente, "ejecutar", ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 200, r.text
    assert [_codigo(p) for p in sv5.ejecutadas] == ["0100", "0200"]
    cuerpo = r.json()
    assert all("bloqueado_sesame" not in g for g in cuerpo["grupos"])
    assert estados_sigrid(fabrica, ids["o10_b"])[ids["o10_b"][0]][:2] == \
        ("registrado", None)


def test_f032_r21_ejecutar_todos_no_fiables_no_es_422(entorno) -> None:
    cliente, _f, ids, sv5, _p = _dos_obras(no_fiables=(DNI_A, DNI_B))
    r = _post(cliente, "ejecutar", ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 200, r.text
    assert len(sv5.ejecutadas) == 2


def test_f032_r21_encolar_varias_obras_todas_se_publican(entorno) -> None:
    cliente, _f, ids, _sv5, pub = _dos_obras(no_fiables=(DNI_A, DNI_B))
    r = _post(cliente, "encolar", ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 200, r.text
    assert [_codigo(p) for p, _u in pub.publicadas] == ["0100", "0200"]
    assert all(g["estado"] == "encolado" for g in r.json()["grupos"])


# ------------------------- R23 · dia de ajuste de F-056 ----------------- #

@pytest.fixture
def portal_franq(entorno):
    entorno.setenv("HOLIDAYS_ENABLED", "false")
    fabrica = FabricaSesionSqlite()

    def _montar(sv5):
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=None,
                        recalculo_publisher=RecalculoFake(),
                        calendario_provider=CalendarioNoFiable())
        return TestClient(app)
    return fabrica, _montar


def test_f032_r23_dia_de_ajuste_con_calendario_no_fiable(portal_franq) -> None:
    fabrica, montar = portal_franq
    ids = _dia15(fabrica)
    sv5 = Sv5Franq(acciones=[_acc_he(2.0)])
    r = _post(montar(sv5), "preflight", ids)
    assert r.status_code == 200, r.text
    [it] = r.json()["franquicias"]["items"]
    assert (it["dia"], it["ajustable"]) == ("2026-10-15", True)
    assert "Sesame" not in (it.get("motivo") or "")
    assert sv5.franq_comprobadas != []


def test_f032_r23_ajustar_con_calendario_no_fiable_se_decide(
        portal_franq) -> None:
    fabrica, montar = portal_franq
    ids = _dia15(fabrica)
    r = _post(montar(Sv5Franq()), "ejecutar", ids,
              franquicias=_decision("ajustar"))
    assert r.status_code == 200, r.text
    [f] = _filas(fabrica)
    assert (f.estado, f.fecha_int, f.obra_codigo) == (
        "decidido", 20261015, "0100")


# ------------------------- R24 · lo ya marcado -------------------------- #

def test_f032_r24_una_linea_ya_marcada_conserva_texto_y_badge(
        entorno) -> None:
    cliente, fabrica, ids, _sv5, _p = _un_trabajador()
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            reg.sigrid_estado = "registrado"
            reg.sigrid_motivo = MARCA
        s.commit()
    trabajador = cliente.get("/trabajadores/rec-501?modo=natural").text
    obra = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "badge-sin-sesame" in trabajador
    assert "badge-sin-sesame" in obra
    assert estados_sigrid(fabrica, ids)[ids[0]][1] == MARCA


# ------------------------- R21, R22 · el modal (app.js) ----------------- #

def test_f032_r21_el_modal_no_tiene_bloqueo_ni_casilla() -> None:
    js = APP_JS.read_text(encoding="utf-8")
    for retirado in ("bloqueoSesameHtml", "ap-forzar-sesame",
                     "forzar_sin_sesame", "sesame_bloqueo",
                     "Bloqueado: Sesame no disponible"):
        assert retirado not in js, retirado


def test_f032_r22_el_grupo_pinta_el_aviso_sesame() -> None:
    js = APP_JS.read_text(encoding="utf-8")
    inicio = js.index("function grupoHtml(")
    cuerpo = js[inicio:js.index("\n  }\n", inicio)]
    assert "g.aviso_sesame" in cuerpo
    assert "ap-warn" in cuerpo
