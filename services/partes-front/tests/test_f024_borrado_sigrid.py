# tests/test_f024_borrado_sigrid.py
"""F-024 · estado `borrado_sigrid` en el portal (R10-R16, R22-R24).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (dobles.py) y
dobles del cliente de sv5. Codigos de parte, `ide` y recursos sinteticos.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADO_BORRADO_SIGRID,
    ESTADOS_CONGELANTES,
    MOTIVO_LINEA_REGISTRADA,
    es_registrado,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
)
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_parte

PARTE = "PT26/09001"
HMO = 7001


def _poner(fabrica, rid: int, **campos) -> None:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _leer(fabrica, rid: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        s.expunge(reg)
        return reg


def _montar(estados: list[str | None], **kw):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"estado": e} for e in estados], **kw)
    return ParteReviewRepository(fabrica), fabrica, ids


# ===================================================================== #
# T5 · congelacion (R13), ESTADOS_EN_VUELO (R15) y motivo (R16)
# ===================================================================== #

def test_f024_r10_congel_el_estado_cabe_en_la_columna() -> None:
    assert ESTADO_BORRADO_SIGRID == "borrado_sigrid"
    assert len(ESTADO_BORRADO_SIGRID) <= 16
    assert ParteRegistroOrm.__table__.c.sigrid_estado.type.length == 16


def test_f024_r13_congel_borrado_sigrid_no_congela_la_linea() -> None:
    for estado in (ESTADO_BORRADO_SIGRID, " Borrado_Sigrid "):
        assert motivo_congelacion_linea(
            doc_aprobado=False, sigrid_estado=estado) is None
    assert ESTADO_BORRADO_SIGRID not in ESTADOS_CONGELANTES
    assert tuple(ESTADOS_CONGELANTES) == ("encolado", "registrado")


def test_f024_r13_congel_borrado_sigrid_no_congela_el_documento() -> None:
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=[ESTADO_BORRADO_SIGRID, None]) is None


def test_f024_r13_congel_el_parte_aprobado_sigue_mandando() -> None:
    """`borrado_sigrid` no descongela un parte aprobado (F-004 R1)."""
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado=ESTADO_BORRADO_SIGRID) is not None


def test_f024_r13_congel_borrado_sigrid_no_bloquea_el_borrado_definitivo() -> None:
    assert es_registrado(ESTADO_BORRADO_SIGRID) is False
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.hard_delete_registro(registro_id=ids[0]) is True
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]) is None


def test_f024_r13_congel_la_linea_borrada_en_sigrid_se_puede_editar() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.update_registro(registro_id=ids[0], horas=6.0) is True
    assert _leer(fabrica, ids[0]).horas == 6.0


def test_f024_r13_congel_la_vista_no_pinta_candado() -> None:
    repo, _f, _ids = _montar([ESTADO_BORRADO_SIGRID])
    detalle = repo.get_parte("doc-f004")
    assert detalle.congelado_doc is None


def test_f024_r15_vuelo_borrado_sigrid_no_es_veredicto_final() -> None:
    assert ESTADO_BORRADO_SIGRID in repo_mod.ESTADOS_EN_VUELO


def test_f024_r15_vuelo_ya_registrada_devuelve_la_linea_a_registrado() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID, "omitido"])
    repo.marcar_registros_sigrid(escritas=[], omitidas=[],
                                 ya_registradas=ids, usuario="ana")
    estados = estados_sigrid(fabrica, ids)
    assert estados[ids[0]][0] == "registrado"
    assert estados[ids[1]][0] == "omitido"     # veredicto final: se respeta


def test_f024_r16_motivo_explica_la_via_nueva() -> None:
    texto = MOTIVO_LINEA_REGISTRADA
    assert "Comprobar en Sigrid" in texto
    assert "borra" in texto.lower()
    assert "aprob" in texto.lower()
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado") == texto



# ===================================================================== #
# T7 · repositorio: registrados_para_comprobar, aplicar_comprobacion_sigrid
# (R10-R12) y recuento_estados (R28)
# ===================================================================== #

AHORA = "2026-10-01T09:30:15.123456+00:00"


def _registrada(fabrica, rid: int, *, hmores: int | None, hmoide: int = HMO,
                parte: str = PARTE) -> None:
    _poner(fabrica, rid, sigrid_estado="registrado", sigrid_hmores_ide=hmores,
           sigrid_hmoide=hmoide, sigrid_parte_cod=parte,
           sigrid_registrado_at_utc="2026-09-30T10:42:08+00:00",
           sigrid_registrado_by="aprobador")


def _borrada(rid: int, **extra) -> dict:
    return dict({"registro_id": rid, "estado": "borrada", "hmores_ide": None,
                 "hmoide": HMO, "parte_cod": PARTE, "parte_existe": True,
                 "sin_synckey": False, "diferencias": [], "motivo": "x"},
                **extra)


def _presente(rid: int, **extra) -> dict:
    return dict({"registro_id": rid, "estado": "presente", "hmores_ide": None,
                 "hmoide": HMO, "parte_cod": PARTE, "parte_existe": True,
                 "sin_synckey": False, "diferencias": [], "motivo": None},
                **extra)


def test_f024_r17_repo_registrados_para_comprobar_solo_registrado() -> None:
    repo, fabrica, ids = _montar(
        ["registrado", None, ESTADO_BORRADO_SIGRID, " Registrado ",
         "registrado", "encolado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[3], sigrid_hmores_ide=4003)
    _poner(fabrica, ids[4], deleted_at_utc=AHORA)       # en la papelera
    _poner(fabrica, ids[0], es_incidencia=True, horas=None)
    filas = repo.registrados_para_comprobar(ids + [999999])
    assert sorted(f["registro_id"] for f in filas) == [ids[0], ids[3]]
    fila = next(f for f in filas if f["registro_id"] == ids[0])
    assert fila == {"registro_id": ids[0], "hmores_ide": 4001, "hmoide": HMO,
                    "recurso_ide": 501, "fecha_int": 20260302, "horas": None,
                    "es_incidencia": True}


def test_f024_r17_repo_registrados_para_comprobar_sin_ids_no_consulta() -> None:
    repo, _f, _ids = _montar(["registrado"])
    assert repo.registrados_para_comprobar([]) == []


def test_f024_r17_repo_registrados_para_comprobar_muchos_ids() -> None:
    """5000 ids (el tope de R17) no rompen la consulta."""
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    filas = repo.registrados_para_comprobar(list(range(ids[0], ids[0] + 5000)))
    assert [f["registro_id"] for f in filas] == [ids[0]]


def test_f024_r10_repo_borrada_pasa_a_borrado_sigrid_y_conserva_rastro() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [ids[0]], "actualizadas": []}
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "borrado_sigrid"
    assert reg.sigrid_motivo == (
        f"Borrada en Sigrid: la linea 4001 del parte {PARTE} ya no existe "
        "(comprobado 2026-10-01 09:30 UTC)")
    assert (reg.sigrid_parte_cod, reg.sigrid_hmoide, reg.sigrid_hmores_ide,
            reg.sigrid_registrado_at_utc, reg.sigrid_registrado_by) == (
        PARTE, HMO, 4001, "2026-09-30T10:42:08+00:00", "aprobador")


def test_f024_r10_repo_cabecera_borrada_tiene_su_motivo() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0], parte_existe=False, parte_cod=None)],
        {ids[0]: 4001}, AHORA)
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "borrado_sigrid"
    assert reg.sigrid_motivo == (
        f"Borrada en Sigrid: el parte {PARTE} ya no existe (linea 4001; "
        "comprobado 2026-10-01 09:30 UTC)")


def test_f024_r10_repo_el_motivo_cabe_en_la_columna() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001, parte="P" * 300)
    repo.aplicar_comprobacion_sigrid([_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    motivo = _leer(fabrica, ids[0]).sigrid_motivo
    assert len(motivo) == 255
    assert motivo.startswith("Borrada en Sigrid: la linea 4001 del parte PPP")


@pytest.mark.parametrize("estado_actual", ["encolado", "omitido",
                                           ESTADO_BORRADO_SIGRID, None])
def test_f024_r11_repo_si_ya_no_esta_registrada_no_se_toca(estado_actual) -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_estado=estado_actual, sigrid_motivo="previo")
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    reg = _leer(fabrica, ids[0])
    assert (reg.sigrid_estado, reg.sigrid_motivo) == (estado_actual, "previo")


def test_f024_r11_repo_si_cambio_su_hmores_ide_no_se_toca() -> None:
    """Se reaprobo entre la lectura y el veredicto: hay otra linea."""
    repo, fabrica, ids = _montar(["registrado", "registrado"])
    _registrada(fabrica, ids[0], hmores=4999)
    _registrada(fabrica, ids[1], hmores=None)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0]), _presente(ids[1], hmores_ide=4002)],
        {ids[0]: 4001, ids[1]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert _leer(fabrica, ids[0]).sigrid_estado == "registrado"
    assert _leer(fabrica, ids[1]).sigrid_hmores_ide is None


def test_f024_r11_repo_veredicto_no_enviado_o_desconocido_no_se_aplica() -> None:
    repo, fabrica, ids = _montar(["registrado", "registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _registrada(fabrica, ids[1], hmores=4002)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0]), _borrada(ids[1], estado="rara"), _borrada(999999)],
        {ids[1]: 4002, 999999: None}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert {_leer(fabrica, i).sigrid_estado for i in ids} == {"registrado"}


def test_f024_r10_repo_estado_guardado_se_compara_normalizado() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_estado=" Registrado ")
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out["borradas"] == [ids[0]]


@pytest.mark.parametrize("campo, valor", [
    ("hmores_ide", 4999), ("hmoide", 7002), ("parte_cod", "PT26/09002")])
def test_f024_r12_repo_presente_con_referencias_nuevas_las_actualiza(
        campo, valor) -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    veredicto = _presente(ids[0], hmores_ide=4001)
    veredicto[campo] = valor
    out = repo.aplicar_comprobacion_sigrid([veredicto], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": [ids[0]]}
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "registrado"
    assert getattr(reg, {"hmores_ide": "sigrid_hmores_ide",
                         "hmoide": "sigrid_hmoide",
                         "parte_cod": "sigrid_parte_cod"}[campo]) == valor
    assert (reg.sigrid_registrado_at_utc, reg.sigrid_registrado_by) == (
        "2026-09-30T10:42:08+00:00", "aprobador")


def test_f024_r12_repo_presente_igual_no_cuenta_como_actualizada() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_motivo="[SIN-SESAME] previo")
    out = repo.aplicar_comprobacion_sigrid(
        [_presente(ids[0], hmores_ide=4001)], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert _leer(fabrica, ids[0]).sigrid_motivo == "[SIN-SESAME] previo"


def test_f024_r12_repo_presente_sin_dato_no_borra_lo_guardado() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    out = repo.aplicar_comprobacion_sigrid(
        [_presente(ids[0], hmores_ide=None, hmoide=None, parte_cod=None)],
        {ids[0]: 4001}, AHORA)
    assert out["actualizadas"] == []
    reg = _leer(fabrica, ids[0])
    assert (reg.sigrid_hmores_ide, reg.sigrid_hmoide, reg.sigrid_parte_cod) \
        == (4001, HMO, PARTE)


def test_f024_r28_repo_recuento_estados() -> None:
    repo, _fabrica, ids = _montar(
        ["encolado", "registrado", " Registrado ", "omitido", None,
         ESTADO_BORRADO_SIGRID, "ENCOLADO"])
    out = repo.recuento_estados(ids + [999999])
    assert out == {"total": 7, "pendientes": 2, "estados": {
        "encolado": 2, "registrado": 2, "omitido": 1, "sin_estado": 1,
        "borrado_sigrid": 1}}


def test_f024_r28_repo_recuento_sin_ids() -> None:
    repo, _f, _ids = _montar(["encolado"])
    assert repo.recuento_estados([]) == {"total": 0, "pendientes": 0,
                                         "estados": {}}



# ===================================================================== #
# T10 · payload de registro: excluidas (R22), 422 sin lineas (R23) y
# `registro_ids` al encolar (R27)
# ===================================================================== #

from config.settings import Settings
from fastapi.testclient import TestClient
from interface_adapters.web.app import build_app


class PublisherFalso:
    def __init__(self) -> None:
        self.publicadas: list[tuple[dict, str | None]] = []

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        self.publicadas.append((payload, usuario))
        return f"peticion-{len(self.publicadas)}"


class Sv5RegistroFalso:
    def __init__(self) -> None:
        self.preflights: list[dict] = []
        self.ejecutadas: list[dict] = []
        self.comprobaciones: list[dict] = []

    def preflight(self, payload: dict) -> dict:
        self.preflights.append(payload)
        return {"ok": True, "conflictos": []}

    def ejecutar(self, payload: dict) -> dict:
        self.ejecutadas.append(payload)
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": []}

    def comprobar(self, payload: dict, *, timeout_s: float) -> dict:
        self.comprobaciones.append(payload)
        return {"ok": True, "veredictos": []}


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)

    def _levantar(estados, *, con_publisher=True):
        repo, fabrica, ids = _montar(estados)
        sv5 = Sv5RegistroFalso()
        publisher = PublisherFalso() if con_publisher else None
        app = build_app(Settings(_env_file=None), repository=repo,
                        transfer_client=sv5, publisher=publisher)
        return TestClient(app), fabrica, ids, sv5, publisher
    return _levantar


ESTADOS_MEZCLA = ["registrado", ESTADO_BORRADO_SIGRID, None, " Registrado ",
                  "encolado", "omitido", "error", "conflicto"]


def test_f024_r22_payload_repo_excluye_registrado_y_borrado_sigrid() -> None:
    repo, _f, ids = _montar(ESTADOS_MEZCLA)
    datos = repo.lineas_para_registro(ids)
    assert [l["registro_id"] for l in datos["lineas"]] == ids[2:3] + ids[4:]
    assert datos["excluidas"] == {"registrado": 2, "borrado_sigrid": 1}
    assert datos["obra"] == {"ide": 10, "codigo": "0100",
                             "nombre": "Obra Uno"}


def test_f024_r22_payload_repo_incluir_borradas() -> None:
    repo, _f, ids = _montar(ESTADOS_MEZCLA)
    datos = repo.lineas_para_registro(ids, incluir_borradas=True)
    assert [l["registro_id"] for l in datos["lineas"]] == (
        ids[1:3] + ids[4:])
    assert datos["excluidas"] == {"registrado": 2, "borrado_sigrid": 0}


def test_f024_r22_payload_repo_sin_ids() -> None:
    repo, _f, _ids = _montar([None])
    assert repo.lineas_para_registro([]) == {
        "obra": {}, "lineas": [],
        "excluidas": {"registrado": 0, "borrado_sigrid": 0}}


def test_f024_r22_payload_repo_la_obra_sale_de_las_lineas_que_viajan() -> None:
    repo, fabrica, ids = _montar(["registrado", None])
    _poner(fabrica, ids[0], obra_ide=99, obra_codigo="0999",
           obra_nombre="Otra")
    assert repo.lineas_para_registro(ids)["obra"]["ide"] == 10


def test_f024_r22_payload_preflight_devuelve_excluidas(portal) -> None:
    cliente, _f, ids, sv5, _p = portal(["registrado", ESTADO_BORRADO_SIGRID,
                                        None])
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["excluidas"] == {"registrado": 1, "borrado_sigrid": 1}
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == [ids[2]]
    assert "excluidas" not in sv5.preflights[0]


def test_f024_r22_payload_preflight_incluir_borradas(portal) -> None:
    cliente, _f, ids, sv5, _p = portal(["registrado", ESTADO_BORRADO_SIGRID])
    r = cliente.post("/api/aprobar/preflight",
                     json={"registro_ids": ids, "incluir_borradas": True})
    assert r.status_code == 200
    assert r.json()["excluidas"] == {"registrado": 1, "borrado_sigrid": 0}
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == [ids[1]]


def test_f024_r27_payload_encolar_devuelve_registro_ids(portal) -> None:
    cliente, fabrica, ids, _sv5, publisher = portal(
        [None, "registrado", ESTADO_BORRADO_SIGRID, "error"])
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["modo"] == "asincrono"
    assert cuerpo["registro_ids"] == [ids[0], ids[3]]
    assert cuerpo["encoladas"] == 2
    assert cuerpo["excluidas"] == {"registrado": 1, "borrado_sigrid": 1}
    payload, _u = publisher.publicadas[0]
    assert [l["registro_id"] for l in payload["lineas"]] == [ids[0], ids[3]]
    assert set(payload) == {"obra", "lineas", "pisar_claves", "usuario"}
    estados = estados_sigrid(fabrica, ids)
    assert [estados[i][0] for i in ids] == [
        "encolado", "registrado", ESTADO_BORRADO_SIGRID, "encolado"]


def test_f024_r22_payload_encolar_reaprobar_una_borrada(portal) -> None:
    cliente, fabrica, ids, _sv5, _pub = portal([ESTADO_BORRADO_SIGRID])
    r = cliente.post("/api/aprobar/encolar",
                     json={"registro_ids": ids, "incluir_borradas": True})
    assert r.status_code == 200
    assert r.json()["registro_ids"] == ids
    assert estados_sigrid(fabrica, ids)[ids[0]][0] == "encolado"


def test_f024_r22_payload_encolar_sincrono_devuelve_excluidas(portal) -> None:
    cliente, _f, ids, sv5, _p = portal([None, "registrado"],
                                       con_publisher=False)
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["modo"] == "sincrono"
    assert r.json()["excluidas"] == {"registrado": 1, "borrado_sigrid": 0}
    assert [l["registro_id"] for l in sv5.ejecutadas[0]["lineas"]] == [ids[0]]


def test_f024_r22_payload_ejecutar_devuelve_excluidas(portal) -> None:
    cliente, _f, ids, sv5, _p = portal([None, "registrado"])
    r = cliente.post("/api/aprobar/ejecutar",
                     json={"registro_ids": ids, "pisar_claves": ["k"]})
    assert r.status_code == 200
    assert r.json()["excluidas"] == {"registrado": 1, "borrado_sigrid": 0}
    assert [l["registro_id"] for l in sv5.ejecutadas[0]["lineas"]] == [ids[0]]
    assert sv5.ejecutadas[0]["pisar_claves"] == ["k"]


def test_f024_r22_payload_aprobar_todo_de_la_obra_excluye_registrado(
        portal) -> None:
    cliente, _f, ids, sv5, _p = portal([None, "registrado"])
    r = cliente.post("/api/aprobar/preflight",
                     json={"obra_key": "obr-10", "period": "2026-03",
                           "mode": "natural"})
    assert r.status_code == 200
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == [ids[0]]
    assert r.json()["excluidas"]["registrado"] == 1


@pytest.mark.parametrize("ruta", ["/api/aprobar/preflight",
                                  "/api/aprobar/encolar",
                                  "/api/aprobar/ejecutar"])
def test_f024_r23_payload_todo_excluido_es_422_con_el_motivo(portal,
                                                             ruta) -> None:
    cliente, _f, ids, sv5, publisher = portal(
        ["registrado", "registrado", ESTADO_BORRADO_SIGRID])
    r = cliente.post(ruta, json={"registro_ids": ids})
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert cuerpo["excluidas"] == {"registrado": 2, "borrado_sigrid": 1}
    assert "2 ya registrada(s) en Sigrid" in cuerpo["error"]
    assert "1 borrada(s) en Sigrid" in cuerpo["error"]
    assert "Reaprobar" in cuerpo["error"]
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []


def test_f024_r23_payload_solo_registradas_no_habla_de_borradas(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal(["registrado"])
    error = cliente.post("/api/aprobar/preflight",
                         json={"registro_ids": ids}).json()["error"]
    assert "1 ya registrada(s) en Sigrid" in error
    assert "borrada" not in error


def test_f024_r23_payload_sin_lineas_activas_mantiene_su_mensaje(portal) -> None:
    cliente, *_ = portal([None])
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": [999999]})
    assert r.status_code == 422
    assert r.json()["error"] == "no hay lineas activas que registrar"



# ===================================================================== #
# T12 · vistas de obra y de trabajador (R24, R26, R30)
# ===================================================================== #

import re

MOTIVO_BORRADA = ('Borrada en Sigrid: la linea 4001 del parte PT26/09001 '
                  'ya no existe (comprobado 2026-10-01 09:30 UTC)')
VISTAS = [("/obras/obr-10", "vista-obra"),
          ("/trabajadores/emp-77", "vista-trabajador")]


def _html_vistas(portal):
    estados = ["registrado", ESTADO_BORRADO_SIGRID, "encolado", None,
               " Registrado "]
    cliente, fabrica, ids, _sv5, _p = portal(estados)
    _poner(fabrica, ids[1], sigrid_motivo=MOTIVO_BORRADA,
           sigrid_parte_cod=PARTE, sigrid_hmores_ide=4001)
    return cliente, fabrica, ids


def _fila(html: str, rid: int) -> str:
    m = re.search(rf'<tr data-registro-id="{rid}".*?</tr>', html, re.DOTALL)
    assert m, f"no hay fila para {rid}"
    return m.group(0)


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r26_vista_cada_fila_lleva_su_estado(portal, ruta, origen) -> None:
    cliente, _f, ids = _html_vistas(portal)
    html = cliente.get(ruta).text
    esperados = ["registrado", "borrado_sigrid", "encolado", "", "registrado"]
    for rid, estado in zip(ids, esperados):
        assert f'data-sigrid-estado="{estado}"' in _fila(html, rid), rid


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r24_vista_pinta_la_borrada_con_reaprobar(portal, ruta,
                                                       origen) -> None:
    cliente, _f, ids = _html_vistas(portal)
    fila = _fila(cliente.get(ruta).text, ids[1])
    assert "borrada en Sigrid" in fila
    assert f'title="{MOTIVO_BORRADA}"' in fila
    boton = re.search(r'<button[^>]*data-incluir-borradas="1"[^>]*>', fila)
    assert boton, "falta el boton Reaprobar"
    assert "aprobar-linea" in boton.group(0)
    assert f'data-registro-id="{ids[1]}"' in boton.group(0)
    assert ">Reaprobar</button>" in fila
    assert 'class="row-congelada"' not in fila      # R13: no congela


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r24_vista_la_cabecera_avisa_de_cuantas(portal, ruta,
                                                     origen) -> None:
    cliente, fabrica, ids = _html_vistas(portal)
    _poner(fabrica, ids[3], sigrid_estado=" Borrado_Sigrid ")
    html = cliente.get(ruta).text
    aviso = re.search(r'<div class="alert warn borradas-sigrid-aviso".*?</div>',
                      html, re.DOTALL)
    assert aviso, "falta el aviso de cabecera"
    assert "<strong>2</strong>" in aviso.group(0)
    assert "Reaprobar" in aviso.group(0)


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r24_vista_sin_borradas_no_avisa(portal, ruta, origen) -> None:
    cliente, _f, _ids, _sv5, _p = portal(["registrado", None])
    assert "borradas-sigrid-aviso" not in cliente.get(ruta).text


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r26_vista_boton_comprobar_en_sigrid(portal, ruta, origen) -> None:
    cliente, _f, _ids = _html_vistas(portal)
    html = cliente.get(ruta).text
    boton = re.search(r'<button[^>]*id="comprobar-sigrid"[^>]*>', html)
    assert boton, "falta el boton"
    assert f'data-origen="{origen}"' in boton.group(0)
    assert "Comprobar en Sigrid" in html
    assert 'id="comprobar-sigrid-nota"' in html
    assert 'id="sigrid-aviso"' in html


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r26_vista_sin_registro_configurado_no_hay_boton(
        monkeypatch, ruta, origen) -> None:
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("TRANSFER_BASE_URL", raising=False)
    repo, _f, ids = _montar(["registrado"])
    app = build_app(Settings(_env_file=None), repository=repo)
    html = TestClient(app).get(ruta).text
    assert 'id="comprobar-sigrid"' not in html
    assert 'data-sigrid-estado="registrado"' in _fila(html, ids[0])


@pytest.mark.parametrize("ruta, origen", VISTAS)
def test_f024_r30_vista_el_tooltip_de_encolado_no_pide_recargar(
        portal, ruta, origen) -> None:
    cliente, _f, ids = _html_vistas(portal)
    html = cliente.get(ruta).text
    fila = _fila(html, ids[2])
    assert "encolado" in fila
    assert "Recarga en unos segundos" not in html
    assert "segundo plano" in fila



# ===================================================================== #
# T17 · supervivientes de la campana de mutacion (progress/mutacion_F-024.md)
# ===================================================================== #

@pytest.mark.parametrize("cod_guardado, cod_veredicto, hmoide, esperado", [
    pytest.param(None, "PT26/09002", None, "PT26/09002", id="del-veredicto"),
    pytest.param(None, None, 7003, "7003", id="del-hmoide"),
    pytest.param(None, None, None, "?", id="sin-nada"),
])
def test_f024_r10_repo_motivo_parte_de_respaldo(cod_guardado, cod_veredicto,
                                                hmoide, esperado) -> None:
    """La parte del motivo: la guardada, la del veredicto, el `hmoide` o
    `?` (mutantes 39 y 44)."""
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_parte_cod=cod_guardado, sigrid_hmoide=hmoide)
    repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0], parte_cod=cod_veredicto)], {ids[0]: 4001}, AHORA)
    assert _leer(fabrica, ids[0]).sigrid_motivo.startswith(
        f"Borrada en Sigrid: la linea 4001 del parte {esperado} ya no existe")


def test_f024_r11_repo_veredicto_sin_registro_id_no_se_aplica() -> None:
    """Un veredicto sin `registro_id` no se confunde con el id 1
    (mutante 59)."""
    repo, fabrica, ids = _montar(["registrado"])
    assert ids[0] == 1
    _registrada(fabrica, ids[0], hmores=4001)
    veredicto = _borrada(ids[0])
    del veredicto["registro_id"]
    out = repo.aplicar_comprobacion_sigrid([veredicto], {1: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert _leer(fabrica, ids[0]).sigrid_estado == "registrado"


def test_f024_r11_repo_lee_cada_linea_con_bloqueo_de_fila() -> None:
    """CAS en la misma transaccion (R11): en PostgreSQL la lectura lleva
    `FOR UPDATE`; SQLite lo ignora, asi que se espia la llamada
    (mutante 64)."""
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    llamadas: list[dict] = []
    original = fabrica.create_session

    def _sesion_espia():
        sesion = original()
        get = sesion.get

        def _get(modelo, ident, **kw):
            llamadas.append(kw)
            return get(modelo, ident, **kw)

        sesion.get = _get
        return sesion

    fabrica.create_session = _sesion_espia
    repo.aplicar_comprobacion_sigrid([_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert llamadas == [{"with_for_update": True}]


def test_f024_r17_repo_consulta_por_lotes_de_mil_ids() -> None:
    """Mutante 38: las lecturas por ids van en `IN` de 1000 como mucho."""
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    consultas: list[int] = []
    original = fabrica.create_session

    def _sesion_espia():
        sesion = original()
        execute = sesion.execute

        def _execute(*a, **kw):
            consultas.append(1)
            return execute(*a, **kw)

        sesion.execute = _execute
        return sesion

    fabrica.create_session = _sesion_espia
    assert repo_mod.LOTE_IDS_CONSULTA == 1000
    filas = repo.registrados_para_comprobar(list(range(1, 1002)))
    assert [f["registro_id"] for f in filas] == [ids[0]]
    assert len(consultas) == 2
