# tests/test_f085_conversion.py
"""F-085 · elegir un código de incidencia convierte la línea (sv4).

- R1: `es_codigo_incidencia` y `es_codigo_fin` (`clase_hora.py`) y la fuente
  de los ficheros que toca F-085 (nadie más decide «es CI*»).
- R2–R7: `conversion_clase.decidir` (puro) y `set_registro_hora` sobre
  SQLite en memoria: forma canónica, cambio de letra, vuelta atrás, CIZ y
  CI* sin letra, caracterización de F-066.
- R8–R11, R14: el endpoint `PATCH /api/registros/{id}/hora` con el
  `SigridLookupClient` REAL sobre un sigrid-api falso y una cola doble:
  guardas, respuesta, deshacer (`registro_clase`), recálculo compartido y
  lo que viaja a sv5.
- R13: `onChange` de `app.js` EJECUTADO en node (patrón de F-066).

Sin red ni PostgreSQL. Datos SINTÉTICOS (obra 0100, recurso 501).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from application.services import clase_hora, conversion_clase
from application.services.clase_hora import (
    es_codigo_fin,
    es_codigo_incidencia,
)
from application.services.conversion_clase import (
    MOTIVO_CIZ_NO_SE_ELIGE,
    ClaseNueva,
    decidir,
    motivo_sin_letra,
)
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import (
    _REG_UNDO_FIELDS,
    ParteReviewRepository,
)
from infrastructure.persistencia.recalculo_publisher import (
    MOTIVO_CODIGO_INCIDENCIA,
    MOTIVO_DESHACER_CODIGO_INCIDENCIA,
)
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f025_deteccion import TABLA
from tests.test_f042_recalculo_fecha import ColaFake
from tests.test_f066_set_registro_hora import (
    AUXHOR,
    COLS_AUXHOR,
    SigridLookupFalso,
)

SV4 = Path(__file__).resolve().parents[1]
APP_JS = SV4 / "static" / "app.js"
NODE = shutil.which("node")

#: `auxhor` de F-066 más los CI* (ides 20-23) para el desplegable.
AUXHOR_CI = AUXHOR + [
    [20, "CIA", "INCIDENCIA ACCIDENTE", 0, 0.0, 0.0],
    [21, "CIV", "INCIDENCIA VACACIONES", 0, 0.0, 0.0],
    [22, "CIZ", "FIN DE INCIDENCIA", 0, 0.0, 0.0],
    [23, "CIQ", "INCIDENCIA SIN LETRA", 0, 0.0, 0.0],
]
IDE = {"HL01": 1, "HEOF": 7, "SIN": 10, "CIA": 20, "CIV": 21, "CIZ": 22,
       "CIQ": 23}


class SigridConCi(SigridLookupFalso):
    """El cliente real con la red sustituida: `auxhor` con los CI*."""

    def _post_sql_read(self, *, sql, parameters, label, max_rows=None):
        if "FROM auxhor" in sql and parameters[-2] == 0:
            return list(COLS_AUXHOR), [list(f) for f in AUXHOR_CI]
        return [], []


# =============================== R1 ================================ #

@pytest.mark.parametrize("codigo, esperado", [
    ("CIA", True), (" cia ", True), ("CIV", True), ("CIQ", True),
    ("CIZ", False), (" ciz ", False), ("HLOF", False), ("HEOF", False),
    ("CI", False), (None, False), ("", False), ("   ", False)])
def test_f085_r1_es_codigo_incidencia(codigo, esperado) -> None:
    assert es_codigo_incidencia(codigo) is esperado


@pytest.mark.parametrize("codigo, esperado", [
    ("CIZ", True), (" ciz ", True), ("CIA", False), ("CIZZ", False),
    ("CI", False), (None, False), ("", False), ("HLOF", False)])
def test_f085_r1_es_codigo_fin(codigo, esperado) -> None:
    assert es_codigo_fin(codigo) is esperado


def test_f085_r1_constantes() -> None:
    assert clase_hora.PREFIJO_INCIDENCIA == "CI"
    assert clase_hora.CODIGO_FIN == "CIZ"


#: Los ficheros de sv4 que toca F-085 (fuera de `clase_hora.py`).
FICHEROS_F085 = [
    "application/services/conversion_clase.py",
    "infrastructure/database/parte_repository.py",
    "interface_adapters/web/app.py",
    "infrastructure/persistencia/recalculo_publisher.py",
]


@pytest.mark.parametrize("ruta", FICHEROS_F085)
def test_f085_r1_nadie_mas_decide_es_ci(ruta) -> None:
    fuente = (SV4 / ruta).read_text(encoding="utf-8")
    for prohibido in ('startswith("CI")', "startswith('CI')",
                      'startswith("CIZ")', '== "CIZ"', "== 'CIZ'",
                      '!= "CIZ"', "!= 'CIZ'", "LIKE 'CI%'"):
        assert prohibido not in fuente, (ruta, prohibido)


# ========================= R2-R7 · puro ============================ #

def _d(codigo, *, es_inc=False, letra=None, tipo="normal", tabla=TABLA):
    return decidir(es_incidencia=es_inc, incidencia_codigo=letra,
                   tipo_hora=tipo, codigo=codigo, tabla=tabla)


def test_f085_r2_puro_forma_canonica() -> None:
    c = _d("CIA")
    assert (c.error, c.es_incidencia, c.tipo_hora, c.incidencia_codigo,
            c.vaciar_horas, c.cambia) == (None, True, "AT", "AT", True, True)
    c = _d(" civ ", tipo="extra")
    assert (c.tipo_hora, c.incidencia_codigo, c.cambia) == ("V", "V", True)


def test_f085_r3_puro_otra_letra() -> None:
    c = _d("CIV", es_inc=True, letra="AT", tipo="AT")
    assert (c.es_incidencia, c.tipo_hora, c.incidencia_codigo, c.cambia,
            c.vaciar_horas) == (True, "V", "V", True, True)


def test_f085_r3_puro_misma_letra_no_cambia() -> None:
    c = _d("CIA", es_inc=True, letra="AT", tipo="AT")
    assert c.error is None and c.cambia is False
    assert (c.es_incidencia, c.tipo_hora, c.incidencia_codigo) == (
        True, "AT", "AT")
    c = _d("CIA", es_inc=True, letra=" at ", tipo="AT")
    assert c.cambia is False


@pytest.mark.parametrize("codigo, tipo", [
    ("HL01", "normal"), ("HEOF", "extra"), (" hecap ", "extra"),
    ("HENC", "normal")])
def test_f085_r4_puro_vuelta_atras(codigo, tipo) -> None:
    c = _d(codigo, es_inc=True, letra="AT", tipo="AT")
    assert (c.error, c.es_incidencia, c.tipo_hora, c.incidencia_codigo,
            c.vaciar_horas, c.cambia) == (None, False, tipo, None, True, True)


@pytest.mark.parametrize("es_inc", [False, True])
def test_f085_r5_puro_ciz_error(es_inc) -> None:
    for codigo in ("CIZ", " ciz "):
        c = _d(codigo, es_inc=es_inc, letra="AT" if es_inc else None)
        assert c.error == MOTIVO_CIZ_NO_SE_ELIGE and c.cambia is False
    assert MOTIVO_CIZ_NO_SE_ELIGE == (
        "El fin de incidencia (CIZ) lo pone el sistema al cerrar la racha: "
        "elige el código de la incidencia")


@pytest.mark.parametrize("codigo, tabla", [
    ("CIQ", TABLA), (" ciq ", TABLA), ("CIA", None)])
def test_f085_r6_puro_sin_letra_error(codigo, tabla) -> None:
    c = _d(codigo, tabla=tabla)
    assert c.error == motivo_sin_letra(codigo) and c.cambia is False
    assert motivo_sin_letra(" ciq ") == (
        "El código CIQ no está en la tabla de incidencias del portal")


@pytest.mark.parametrize("codigo, tipo_antes, tipo", [
    ("HEOF", "normal", "extra"), ("HL01", "extra", "normal"),
    (None, "extra", "extra"), ("", "normal", "normal"),
    ("CI", "extra", "normal"), ("MENC", "extra", "normal")])
def test_f085_r7_puro_regla_de_f066(codigo, tipo_antes, tipo) -> None:
    c = _d(codigo, tipo=tipo_antes)
    assert (c.error, c.es_incidencia, c.tipo_hora, c.incidencia_codigo,
            c.vaciar_horas, c.cambia) == (None, False, tipo, None, False,
                                          False)


def test_f085_r7_puro_incidencia_sin_codigo_no_cambia() -> None:
    c = _d(None, es_inc=True, letra="AT", tipo="AT")
    assert (c.es_incidencia, c.tipo_hora, c.incidencia_codigo, c.cambia) \
        == (True, "AT", "AT", False)


def test_f085_r2_puro_clase_es_inmutable() -> None:
    c = _d("CIA")
    assert isinstance(c, ClaseNueva)
    with pytest.raises(AttributeError):
        c.cambia = False   # type: ignore[misc]


def test_f085_puro_sin_e_s() -> None:
    import inspect
    fuente = inspect.getsource(conversion_clase)
    for prohibido in ("sqlalchemy", "httpx", "import os", "open("):
        assert prohibido not in fuente


# ======================= R2-R10 · repositorio ====================== #

CAMPOS = ("tipo_hora", "es_incidencia", "incidencia_codigo", "horas",
          "horas_orig", "extra_auto", "hora_ide", "hora_codigo",
          "hora_descripcion", "hora_ext", "hora_precio_coste",
          "hora_precio_nomina", "hora_match_method", "partida_cod",
          "recurso_ide", "fecha", "fecha_int", "obra_codigo", "document_id")


def _fila(fabrica, rid: int) -> dict:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        return {c: getattr(r, c) for c in CAMPOS}


def _poner(fabrica, rid: int, **valores) -> None:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        for k, v in valores.items():
            setattr(r, k, v)
        s.commit()


def _opcion(codigo):
    fila = next(f for f in AUXHOR_CI if f[1] == codigo)
    return dict(hora_ide=fila[0], hora_codigo=fila[1],
                hora_descripcion=fila[2], hora_ext=fila[3],
                hora_precio_coste=fila[4], hora_precio_nomina=fila[5])


def _guardar(repo, rid, codigo, tabla=TABLA):
    return repo.set_registro_hora(registro_id=rid, **_opcion(codigo),
                                  incidencias=tabla)


@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [
        {"tipo": "normal", "partida_cod": "01.01"},     # 0: base 8 h
        {"tipo": "extra", "horas": 2.0},                 # 1: extra
        {"tipo": "normal"},                              # 2: incidencia AT
    ], document_id="doc-f085")
    _poner(fabrica, ids[0], horas_orig=10.0)
    _poner(fabrica, ids[1], extra_auto=True)
    _poner(fabrica, ids[2], es_incidencia=True, tipo_hora="AT",
           incidencia_codigo="AT", horas=None, hora_codigo="CIA",
           hora_ide=20)
    return ParteReviewRepository(fabrica), fabrica, ids


def test_f085_r2_repo_convierte_a_forma_canonica(repo) -> None:
    repositorio, fabrica, ids = repo
    antes = _fila(fabrica, ids[0])
    res = _guardar(repositorio, ids[0], "CIA")
    fila = _fila(fabrica, ids[0])
    assert (fila["es_incidencia"], fila["tipo_hora"],
            fila["incidencia_codigo"], fila["horas"], fila["horas_orig"]) \
        == (True, "AT", "AT", None, None)
    assert (fila["hora_ide"], fila["hora_codigo"], fila["hora_descripcion"],
            fila["hora_match_method"]) == (
        20, "CIA", "INCIDENCIA ACCIDENTE", "manual")
    for c in ("partida_cod", "recurso_ide", "fecha", "fecha_int",
              "obra_codigo", "document_id"):
        assert fila[c] == antes[c], c
    assert res.clase_cambiada is True
    assert (res.tipo_hora, res.es_incidencia, res.incidencia_codigo) == (
        "AT", True, "AT")
    assert (res.recurso_ide, res.fecha_int) == (501, 20260302)
    assert res.document_id == "doc-f085"


def test_f085_r2_repo_extra_automatica_convertida_deja_de_serlo(repo) -> None:
    """Una extra automática convertida no debe ser miembro de la pareja de
    sv3 (la borraría): `extra_auto` queda falso."""
    repositorio, fabrica, ids = repo
    _guardar(repositorio, ids[1], "CIV")
    fila = _fila(fabrica, ids[1])
    assert (fila["es_incidencia"], fila["tipo_hora"], fila["extra_auto"],
            fila["horas"]) == (True, "V", False, None)


def test_f085_r3_repo_cambia_de_letra(repo) -> None:
    repositorio, fabrica, ids = repo
    res = _guardar(repositorio, ids[2], "CIV")
    fila = _fila(fabrica, ids[2])
    assert (fila["es_incidencia"], fila["tipo_hora"],
            fila["incidencia_codigo"], fila["hora_codigo"]) == (
        True, "V", "V", "CIV")
    assert res.clase_cambiada is True


def test_f085_r3_repo_misma_letra_no_es_cambio(repo) -> None:
    repositorio, fabrica, ids = repo
    res = _guardar(repositorio, ids[2], "CIA")
    assert res.clase_cambiada is False
    assert _fila(fabrica, ids[2])["tipo_hora"] == "AT"
    deshecho = repositorio.undo_last(actor="ana")
    assert deshecho["action"] == "registro_hora"


@pytest.mark.parametrize("codigo, tipo", [("HL01", "normal"),
                                          ("HEOF", "extra")])
def test_f085_r4_repo_vuelta_atras(repo, codigo, tipo) -> None:
    repositorio, fabrica, ids = repo
    res = _guardar(repositorio, ids[2], codigo)
    fila = _fila(fabrica, ids[2])
    assert (fila["es_incidencia"], fila["tipo_hora"],
            fila["incidencia_codigo"], fila["horas"]) == (
        False, tipo, None, None)
    assert res.clase_cambiada is True and res.es_incidencia is False


@pytest.mark.parametrize("codigo", ["CIZ", "CIQ"])
def test_f085_r5_r6_repo_error_no_toca(repo, codigo) -> None:
    repositorio, fabrica, ids = repo
    antes = {i: _fila(fabrica, i) for i in ids}
    with pytest.raises(ValueError):
        _guardar(repositorio, ids[0], codigo)
    with pytest.raises(ValueError):
        _guardar(repositorio, ids[2], codigo)
    assert {i: _fila(fabrica, i) for i in ids} == antes
    assert repositorio.count_undo() == 0


#: R7: lo que la base de la rama (ae0fac7) deja para cada código en una
#: línea normal (8 h) y en una extra (2 h, automática).
CARACTERIZACION = {
    ("HEOF", 0): ("extra", False, None, 8.0, 10.0),
    ("HL01", 0): ("normal", False, None, 8.0, 10.0),
    ("SIN", 0): ("normal", False, None, 8.0, 10.0),
    ("HEOF", 1): ("extra", False, None, 2.0, None),
    ("HL01", 1): ("normal", False, None, 2.0, None),
    ("SIN", 1): ("extra", False, None, 2.0, None),
}


@pytest.mark.parametrize("clave", sorted(CARACTERIZACION))
def test_f085_r7_repo_caracterizacion(repo, clave) -> None:
    repositorio, fabrica, ids = repo
    codigo, idx = clave
    opcion = (dict(hora_ide=10, hora_codigo=None, hora_descripcion="Sin",
                   hora_ext=0, hora_precio_coste=None,
                   hora_precio_nomina=None)
              if codigo == "SIN" else _opcion(codigo))
    res = repositorio.set_registro_hora(registro_id=ids[idx], **opcion,
                                        incidencias=TABLA)
    fila = _fila(fabrica, ids[idx])
    assert (fila["tipo_hora"], fila["es_incidencia"],
            fila["incidencia_codigo"], fila["horas"],
            fila["horas_orig"]) == CARACTERIZACION[clave]
    assert fila["hora_match_method"] == "manual"
    assert res.clase_cambiada is False
    assert repositorio.undo_last(actor="ana")["action"] == "registro_hora"


def test_f085_r7_repo_sin_tabla_y_sin_ci_como_f066(repo) -> None:
    """Quien llama sin tabla (F-066) sigue igual para un código de horas."""
    repositorio, fabrica, ids = repo
    assert repositorio.set_registro_hora(
        registro_id=ids[0], **_opcion("HEOF"))
    assert _fila(fabrica, ids[0])["tipo_hora"] == "extra"


def test_f085_r10_undo_fields_con_incidencia_codigo() -> None:
    assert "incidencia_codigo" in _REG_UNDO_FIELDS


@pytest.mark.parametrize("idx, codigo", [(0, "CIA"), (1, "CIV"),
                                         (2, "CIV"), (2, "HL01")])
def test_f085_r10_repo_deshacer_registro_clase(repo, idx, codigo) -> None:
    repositorio, fabrica, ids = repo
    antes = _fila(fabrica, ids[idx])
    assert _guardar(repositorio, ids[idx], codigo).clase_cambiada
    assert repositorio.count_undo() == 1          # una sola entrada
    deshecho = repositorio.undo_last(actor="ana")
    assert deshecho["action"] == "registro_clase"
    assert _fila(fabrica, ids[idx]) == antes
    assert deshecho["document_ids"] == ["doc-f085"]


def test_f085_r10_deshacer_registro_clase_otras_obras_del_dia() -> None:
    fabrica = FabricaSesionSqlite()
    (a,) = sembrar_parte(fabrica, [{"tipo": "normal"}], document_id="d-a")
    sembrar_parte(fabrica, [{"tipo": "normal"}], document_id="d-b",
                  obra_ide=20, obra_codigo="0200")
    sembrar_parte(fabrica, [{"tipo": "normal"}], document_id="d-c",
                  fecha="2026-03-03")
    repositorio = ParteReviewRepository(fabrica)
    _guardar(repositorio, a, "CIA")
    assert repositorio.undo_last(actor="ana")["document_ids"] == [
        "d-a", "d-b"]


def test_f085_r10_repo_inexistente(repo) -> None:
    repositorio, _f, _ids = repo
    assert not _guardar(repositorio, 999_999, "CIA")


# ==================== R8-R11 · endpoint y recálculo ================== #

@pytest.fixture
def portal(monkeypatch):
    for clave in ("PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.setenv(clave, "irrelevante-en-tests")
    monkeypatch.setenv("DEFAULT_REVIEWER", "ana")
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)

    def montar(sembrar, *, con_sigrid=True, cola=None, sin_cola=False):
        if con_sigrid:
            monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
            monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-prueba")
            monkeypatch.setenv("SIGRID_API_DATABASE", "ruesma_rep")
            monkeypatch.setattr(app_mod, "SigridLookupClient", SigridConCi)
        else:
            for clave in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY"):
                monkeypatch.delenv(clave, raising=False)
        fabrica = FabricaSesionSqlite()
        ids = sembrar(fabrica)
        cola = None if sin_cola else (cola or ColaFake())
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        cola_cliente=cola)
        return TestClient(app), fabrica, ids, cola

    return montar


def _base(fabrica):
    ids = sembrar_parte(fabrica, [{"tipo": "normal"}, {"tipo": "extra",
                                                       "horas": 2.0}],
                        document_id="doc-a")
    _poner(fabrica, ids[0], horas_orig=10.0)
    _poner(fabrica, ids[1], extra_auto=True)
    otra = sembrar_parte(fabrica, [{"tipo": "normal"}], document_id="doc-b",
                         obra_ide=20, obra_codigo="0200")
    return ids + otra


def _patch(cliente, rid, codigo):
    return cliente.patch(f"/api/registros/{rid}/hora",
                         json={"hora_ide": IDE[codigo]},
                         headers={"X-MS-CLIENT-PRINCIPAL-NAME": "rev@x.es"})


def _recalculos(cola) -> list[dict]:
    return [p for _q, p in cola.enviados]


def test_f085_r9_r11_convertir_responde_y_pide_recalculo(portal) -> None:
    cliente, fabrica, ids, cola = portal(_base)
    r = _patch(cliente, ids[0], "CIA")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["tipo_hora"], cuerpo["es_incidencia"],
            cuerpo["incidencia_codigo"], cuerpo["clase_cambiada"]) == (
        "AT", True, "AT", True)
    assert cuerpo["hora_codigo"] == "CIA" and cuerpo["registro_id"] == ids[0]
    assert cuerpo["recalculo"] == "pedido"
    (msg,) = _recalculos(cola)
    assert msg["motivo"] == MOTIVO_CODIGO_INCIDENCIA
    assert msg["document_id"] == "doc-a"
    # El pedido compartido marca los partes del (recurso, día): las dos obras.
    from infrastructure.database.orm_models import ParteDocumentOrm
    with fabrica.create_session() as s:
        pedidos = {s.get(ParteDocumentOrm, d).recalculo_pedido_id
                   for d in ("doc-a", "doc-b")}
    assert len(pedidos) == 1 and None not in pedidos


def test_f085_r9_sin_cambio_de_clase_no_pide_recalculo(portal) -> None:
    cliente, _f, ids, cola = portal(_base)
    r = _patch(cliente, ids[0], "HEOF")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["tipo_hora"], cuerpo["es_incidencia"],
            cuerpo["incidencia_codigo"], cuerpo["clase_cambiada"]) == (
        "extra", False, None, False)
    assert cuerpo.get("recalculo") is None
    assert _recalculos(cola) == []


def test_f085_r9_respuesta_sin_codigo_como_f066(portal) -> None:
    cliente, fabrica, ids, _cola = portal(_base)
    r = _patch(cliente, ids[1], "SIN")
    assert r.status_code == 200
    assert r.json()["tipo_hora"] == "normal"
    assert _fila(fabrica, ids[1])["tipo_hora"] == "extra"


def test_f085_r11_cola_caida_el_cambio_queda(portal) -> None:
    cliente, fabrica, ids, _cola = portal(
        _base, cola=ColaFake(error=RuntimeError("cola caida")))
    r = _patch(cliente, ids[0], "CIA")
    assert r.status_code == 200 and r.json()["recalculo"] == "fallo"
    assert _fila(fabrica, ids[0])["es_incidencia"] is True


def test_f085_r11_sin_cola(portal) -> None:
    cliente, fabrica, ids, _cola = portal(_base, sin_cola=True)
    r = _patch(cliente, ids[0], "CIA")
    assert r.status_code == 200 and r.json()["recalculo"] == "sin_cola"


@pytest.mark.parametrize("codigo, detalle", [
    ("CIZ", MOTIVO_CIZ_NO_SE_ELIGE),
    ("CIQ", "El código CIQ no está en la tabla de incidencias del portal")])
def test_f085_r5_r6_endpoint_400_sin_tocar(portal, codigo, detalle) -> None:
    cliente, fabrica, ids, cola = portal(_base)
    antes = {i: _fila(fabrica, i) for i in ids}
    r = _patch(cliente, ids[0], codigo)
    assert r.status_code == 400 and r.json()["detail"] == detalle
    assert {i: _fila(fabrica, i) for i in ids} == antes
    assert _recalculos(cola) == []


def test_f085_r8_guardas(portal) -> None:
    def sembrar(fabrica):
        return sembrar_parte(fabrica, [{"tipo": "normal",
                                        "estado": "registrado"}])
    cliente, _f, ids, cola = portal(sembrar)
    assert _patch(cliente, ids[0], "CIA").status_code == 409    # F-004
    assert _patch(cliente, 999_999, "CIA").status_code == 404
    assert _recalculos(cola) == []


def test_f085_r8_sin_sigrid_503(portal) -> None:
    cliente, _f, ids, _c = portal(_base, con_sigrid=False)
    assert _patch(cliente, ids[0], "CIA").status_code == 503


def test_f085_r8_recalculando_409(portal) -> None:
    from infrastructure.database.orm_models import ParteDocumentOrm

    def sembrar(fabrica):
        ids = _base(fabrica)
        with fabrica.create_session() as s:
            doc = s.get(ParteDocumentOrm, "doc-a")
            doc.recalculo_pedido_id = "p-1"
            doc.recalculo_pedido_at_utc = "2099-01-01T00:00:00+00:00"
            s.commit()
        return ids
    cliente, fabrica, ids, _c = portal(sembrar)
    antes = _fila(fabrica, ids[0])
    assert _patch(cliente, ids[0], "CIA").status_code == 409    # F-043
    assert _fila(fabrica, ids[0]) == antes


def test_f085_r8_varias_lineas_cada_una_su_regla(portal) -> None:
    def sembrar(fabrica):
        ids = sembrar_parte(fabrica, [{"tipo": "normal"}, {"tipo": "extra"},
                                      {"tipo": "normal"}])
        _poner(fabrica, ids[2], es_incidencia=True, tipo_hora="V",
               incidencia_codigo="V", horas=None)
        return ids
    # Sin cola: con ella, el recálculo pedido por la primera deja el parte
    # en espera (F-043) y las demás líneas del MISMO parte dan 409 hasta
    # que sv3 termina (ver el test siguiente y progress/impl_F-085.md).
    cliente, fabrica, ids, _c = portal(sembrar, sin_cola=True)
    for rid in ids:
        assert _patch(cliente, rid, "CIA").status_code == 200
    assert [(_fila(fabrica, r)["tipo_hora"],
             _fila(fabrica, r)["es_incidencia"]) for r in ids] == [
        ("AT", True)] * 3
    for rid in ids:
        assert _patch(cliente, rid, "HL01").status_code == 200
    assert [(_fila(fabrica, r)["tipo_hora"], _fila(fabrica, r)["horas"])
            for r in ids] == [("normal", None)] * 3


def test_f085_r8_varias_lineas_de_dias_distintos_con_cola(portal) -> None:
    """Una racha de varios días: cada día es un parte distinto y cada
    PATCH pide su recálculo (design §2: un pedido por llamada)."""
    def sembrar(fabrica):
        return [sembrar_parte(fabrica, [{"tipo": "normal"}],
                              document_id=f"d-{n}",
                              fecha=f"2026-03-0{n}")[0] for n in (2, 3, 4)]
    cliente, fabrica, ids, cola = portal(sembrar)
    for rid in ids:
        r = _patch(cliente, rid, "CIV")
        assert r.status_code == 200 and r.json()["recalculo"] == "pedido"
    assert [_fila(fabrica, r)["tipo_hora"] for r in ids] == ["V"] * 3
    assert [p["document_id"] for p in _recalculos(cola)] == [
        "d-2", "d-3", "d-4"]


def _entradas_deshacer(fabrica) -> list[str]:
    from infrastructure.database.orm_models import UndoLogOrm
    with fabrica.create_session() as s:
        return [u.action for u in s.query(UndoLogOrm).order_by(UndoLogOrm.id)]


def test_f085_r8_mismo_parte_con_cola_de_una_en_una(portal) -> None:
    """R8 enmendado (D16): con cola, N líneas del MISMO parte se cambian de
    una en una. Pedidos SECUENCIALES (deterministas): la primera se
    convierte y pide su recálculo; cada una de las demás da el 409 de
    F-043 sin tocar ni la línea ni el deshacer. En concurrencia real
    (`Promise.all`) podría pasar más de una antes de marcarse la espera;
    R8 lo admite, y por eso aquí no se afirma nada de la concurrencia."""
    from application.services.seguimiento_recalculo import (
        MOTIVO_RECALCULANDO,
    )

    def sembrar(fabrica):
        return sembrar_parte(fabrica, [{"tipo": "normal"}] * 3)
    cliente, fabrica, ids, cola = portal(sembrar)
    antes = {rid: _fila(fabrica, rid) for rid in ids}
    r = _patch(cliente, ids[0], "CIA")
    assert r.status_code == 200 and r.json()["clase_cambiada"] is True
    assert _fila(fabrica, ids[0])["tipo_hora"] == "AT"
    for rid in ids[1:]:
        r = _patch(cliente, rid, "CIA")
        assert r.status_code == 409
        assert r.json()["error"] == MOTIVO_RECALCULANDO
        assert _fila(fabrica, rid) == antes[rid]
    assert _entradas_deshacer(fabrica) == ["registro_clase"]
    assert len(_recalculos(cola)) == 1


def test_f085_r8_partes_distintos_del_mismo_dia_con_cola(portal) -> None:
    """Con cola, líneas de partes DISTINTOS (aquí el mismo día, de dos
    trabajadores) se convierten todas: cada una pide el recálculo de los
    partes de SU recurso y día, y la espera de un parte no frena al otro."""
    def sembrar(fabrica):
        return (sembrar_parte(fabrica, [{"tipo": "normal"}],
                              document_id="p-1", fecha="2026-03-02")
                + sembrar_parte(fabrica, [{"tipo": "normal"}],
                                document_id="p-2", fecha="2026-03-02",
                                empleado_ide=78, empleado_dni="00000002W",
                                empleado_nombre="Otra Persona",
                                recurso_ide=502))
    cliente, fabrica, ids, cola = portal(sembrar)
    for rid in ids:
        r = _patch(cliente, rid, "CIA")
        assert r.status_code == 200 and r.json()["recalculo"] == "pedido"
    assert [_fila(fabrica, r)["tipo_hora"] for r in ids] == ["AT", "AT"]
    assert _entradas_deshacer(fabrica) == ["registro_clase"] * 2
    assert [p["document_id"] for p in _recalculos(cola)] == ["p-1", "p-2"]


def test_f085_r10_r11_deshacer_por_el_endpoint(portal) -> None:
    cliente, fabrica, ids, cola = portal(_base)
    antes = _fila(fabrica, ids[0])
    assert _patch(cliente, ids[0], "CIA").status_code == 200
    cola.enviados.clear()
    # El recálculo pedido deja el parte en espera; sv3 lo daría por hecho.
    from infrastructure.database.orm_models import ParteDocumentOrm
    with fabrica.create_session() as s:
        for d in ("doc-a", "doc-b"):
            s.get(ParteDocumentOrm, d).recalculo_pedido_id = None
        s.commit()
    r = cliente.post("/api/undo")
    assert r.status_code == 200, r.text
    assert r.json()["action"] == "registro_clase"
    assert r.json()["recalculo"] == "pedido"
    assert _fila(fabrica, ids[0]) == antes
    (msg,) = _recalculos(cola)
    assert msg["motivo"] == MOTIVO_DESHACER_CODIGO_INCIDENCIA


def test_f085_r11_deshacer_registro_hora_no_pide(portal) -> None:
    cliente, _f, ids, cola = portal(_base)
    assert _patch(cliente, ids[0], "HEOF").status_code == 200
    r = cliente.post("/api/undo")
    assert r.json()["action"] == "registro_hora"
    assert "recalculo" not in r.json()
    assert _recalculos(cola) == []


def test_f085_r11_constantes_de_motivo() -> None:
    assert MOTIVO_CODIGO_INCIDENCIA == "codigo_incidencia"
    assert MOTIVO_DESHACER_CODIGO_INCIDENCIA == "deshacer_codigo_incidencia"


# ============================== R14 ================================ #

def test_f085_r14_convertida_se_pinta_y_viaja_como_incidencia(repo) -> None:
    repositorio, fabrica, ids = repo
    _guardar(repositorio, ids[0], "CIA")
    det = repositorio.get_obra("obr-10")
    (fila,) = det.rows
    (celda,) = [c for c in fila.cells if c.date_iso == "2026-03-02"]
    assert celda.has_inc is True and "AT" in celda.label
    # La base (8 h) ya no suma: solo queda la extra de 2 h.
    assert (celda.normal, celda.extra) == (0.0, 2.0)
    datos = repositorio.lineas_para_registro([ids[0]], incidencias=TABLA,
                                             mover_ciz=True)
    (linea,) = datos["lineas"]
    assert (linea["es_incidencia"], linea["tipo_hora"],
            linea["incidencia_codigo"], linea["horas"],
            linea["hora_codigo"], linea["incidencia_rol"]) == (
        True, "AT", "AT", None, "CIA", "inicio")


def test_f085_r14_plantillas_pintan_por_es_incidencia() -> None:
    for plantilla in ("obra_detail.html", "trabajador_detail.html"):
        texto = (SV4 / "templates" / plantilla).read_text(encoding="utf-8")
        assert "{% if r.es_incidencia %}" in texto


# ============================== R13 ================================ #

def _on_change() -> str:
    """`onChange` y, desde F-085 D16, su ayudante `avisoNoGuardadas`."""
    js = APP_JS.read_text(encoding="utf-8")
    trozos = []
    for nombre in ("avisoNoGuardadas", "onChange"):
        m = re.search(r"\n  function " + nombre + r"\([^)]*\) \{.*?\n  \}\n",
                      js, re.DOTALL)
        assert m, f"app.js no define {nombre}"
        trozos.append(m.group(0))
    return "".join(trozos)


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no está instalado: no se puede ejecutar el JS")
    with tempfile.TemporaryDirectory() as carpeta:
        fichero = Path(carpeta) / "programa.js"
        fichero.write_text(programa, encoding="utf-8")
        r = subprocess.run([NODE, str(fichero)], capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _ejecutar_on_change(respuestas, *, bulk=False):
    """`respuestas`: una por pedido; `{"_error": texto, "_status": n}` es
    una peticion que falla como `MotivoHttp.lanzarSiFalla` (Error con
    `status`). `alert` queda en `avisos` (F-085 D16)."""
    programa = """
var recargas = 0, pedidos = [], avisos = [];
function alert(m) { avisos.push(m); }
var window = { location: { reload: function () {
  recargas += 1; } } };
var current = { textContent: "antes" };
var row = { querySelector: function () { return current; } };
var select = { value: "20", disabled: false, title: "",
  getAttribute: function () { return "5"; },
  closest: function () { return row; },
  classList: { add: function () {}, remove: function () {} } };
var RESPUESTAS = %s;
function flash() {}
function patchHora(id, v) { pedidos.push(id);
  var r = RESPUESTAS[pedidos.length - 1];
  if (r && r._error) { var e = new Error(r._error); e.status = r._status;
    return Promise.reject(e); }
  return Promise.resolve(r); }
%s
%s
onChange({ target: select });
setTimeout(function () {
  console.log(JSON.stringify({ recargas: recargas, pedidos: pedidos,
    texto: current.textContent, avisos: avisos, titulo: select.title }));
}, 50);
""" % (json.dumps(respuestas),
       ("var PartidaSel = { has: function () { return true; },"
        " count: function () { return %d; },"
        " ids: function () { return %s; } };"
        % (len(respuestas),
           json.dumps([str(5 + i) for i in range(len(respuestas))])))
       if bulk else "",
       _on_change())
    return _node(programa)


def test_f085_r13_js_recarga_con_clase_cambiada() -> None:
    out = _ejecutar_on_change([{"hora_codigo": "CIA", "hora_descripcion": "X",
                                "clase_cambiada": True}])
    assert out["recargas"] == 1


def test_f085_r13_js_sin_cambio_de_clase_como_hoy() -> None:
    out = _ejecutar_on_change([{"hora_codigo": "HEOF",
                                "hora_descripcion": "Extra",
                                "clase_cambiada": False}])
    assert out == {"recargas": 0, "pedidos": ["5"],
                   "texto": "HEOF · Extra", "avisos": [], "titulo": ""}
    out = _ejecutar_on_change([{"hora_codigo": "HEOF",
                                "hora_descripcion": "Extra"}])
    assert out["recargas"] == 0


def test_f085_r13_js_varias_con_alguna_cambiada() -> None:
    out = _ejecutar_on_change([{"clase_cambiada": False},
                               {"clase_cambiada": True}], bulk=True)
    assert out["recargas"] == 1 and out["pedidos"] == ["5", "6"]
    assert out["avisos"] == []


#: El texto real del 409 de F-043 (R38), como lo manda el servidor.
ESPERA_409 = "El parte se está recalculando (extras): espera a que termine."


def test_f085_r13_d16_fallo_parcial_avisa_y_recarga() -> None:
    """D16: una se guarda (y cambia de clase) y dos dan el 409 de F-043:
    el aviso nombra las dos que fallaron, con el texto del servidor, y se
    recarga (el `alert` bloquea: la recarga espera a que se lea)."""
    out = _ejecutar_on_change([
        {"clase_cambiada": True},
        {"_error": ESPERA_409, "_status": 409},
        {"_error": ESPERA_409, "_status": 409}], bulk=True)
    assert out["pedidos"] == ["5", "6", "7"]
    (aviso,) = out["avisos"]
    assert aviso.startswith("2 de 3 línea(s) no se han guardado")
    assert f"{ESPERA_409} (líneas 6, 7)" in aviso
    assert "5" not in aviso.split("guardado", 1)[1].replace(
        "(líneas 6, 7)", "")
    assert out["recargas"] == 1


def test_f085_r13_d16_motivos_distintos_por_separado() -> None:
    out = _ejecutar_on_change([
        {"clase_cambiada": False},
        {"_error": ESPERA_409, "_status": 409},
        {"_error": "Linea congelada", "_status": 409}], bulk=True)
    (aviso,) = out["avisos"]
    assert f"{ESPERA_409} (línea 6)" in aviso
    assert "Linea congelada (línea 7)" in aviso
    assert out["recargas"] == 1


def test_f085_r13_d16_todas_fallan_avisa_y_no_recarga() -> None:
    out = _ejecutar_on_change([
        {"_error": ESPERA_409, "_status": 409},
        {"_error": ESPERA_409, "_status": 409}], bulk=True)
    (aviso,) = out["avisos"]
    assert aviso.startswith("2 de 2 línea(s) no se han guardado")
    assert f"{ESPERA_409} (líneas 5, 6)" in aviso
    assert out["recargas"] == 0
    assert out["titulo"] == ESPERA_409


def test_f085_r13_d16_una_sola_que_falla_como_hoy() -> None:
    """Sin selección múltiple no hay fallo parcial: como hoy (F-004 R16),
    el error en el `title` del selector y sin `alert` ni recarga."""
    out = _ejecutar_on_change([{"_error": ESPERA_409, "_status": 409}])
    assert out["avisos"] == [] and out["recargas"] == 0
    assert out["titulo"] == ESPERA_409 and out["texto"] == "antes"
