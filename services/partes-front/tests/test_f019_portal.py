# tests/test_f019_portal.py
"""F-019 · la linea en dedicacion en el portal (R15-R24).

T5: `dedicacion` congela como `registrado` (R15) y no se borra
definitivamente (R16). T8: no viaja a sv5 al aprobar (R17) y el listado
del modal la ensena «a dedicacion» (R18). T9: «Retirar de dedicacion»
(R21-R24). T10: las vistas (R19) y «Marcar pendiente» (R20).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM, `TestClient` y
los dobles de sv5, publisher y calendario de F-022. Personas, obras y
partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADO_DEDICACION,
    MOTIVO_DOC_APROBADO,
    MOTIVO_DOC_DEDICACION,
    MOTIVO_DOC_ENCOLADO,
    MOTIVO_DOC_REGISTRADO,
    MOTIVO_HARD_DELETE_DEDICACION,
    MOTIVO_HARD_DELETE_REGISTRADO,
    MOTIVO_LINEA_DEDICACION,
    MOTIVO_LINEA_ENCOLADA,
    MOTIVO_LINEA_REGISTRADA,
    CongeladoError,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
    vive_fuera,
)
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import sembrar


# ========================== T5 · R15 · la congelacion ========================== #

@pytest.mark.parametrize("estado", ["dedicacion", " Dedicacion ",
                                    "DEDICACION"])
def test_f019_r15_dedicacion_congela_la_linea(estado) -> None:
    for aprobado in (False, True):
        assert motivo_congelacion_linea(
            doc_aprobado=aprobado, sigrid_estado=estado) == \
            MOTIVO_LINEA_DEDICACION


def test_f019_r15_el_motivo_dice_dedicacion_y_como_liberarla() -> None:
    assert ESTADO_DEDICACION == "dedicacion"
    for motivo in (MOTIVO_LINEA_DEDICACION, MOTIVO_DOC_DEDICACION):
        assert "dedicación" in motivo
        assert "«Retirar de dedicación»" in motivo


def test_f019_r15_prioridad_de_la_linea() -> None:
    """encolado > registrado > dedicacion > aprobado (no hay dos estados
    en una linea; la prioridad se ve en el documento)."""
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado="encolado") == MOTIVO_LINEA_ENCOLADA
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado="registrado") == \
        MOTIVO_LINEA_REGISTRADA


@pytest.mark.parametrize("estados,aprobado,esperado", [
    (["dedicacion"], False, MOTIVO_DOC_DEDICACION),
    (["dedicacion", None], True, MOTIVO_DOC_DEDICACION),
    (["registrado", "dedicacion"], False, MOTIVO_DOC_REGISTRADO),
    (["dedicacion", "encolado"], False, MOTIVO_DOC_ENCOLADO),
    ([None, "omitido"], True, MOTIVO_DOC_APROBADO),
    ([None, "omitido"], False, None),
])
def test_f019_r15_el_documento_con_una_linea_en_dedicacion(
        estados, aprobado, esperado) -> None:
    assert motivo_congelacion_documento(
        aprobado=aprobado, estados_lineas=estados) == esperado


def test_f019_r15_el_repositorio_rechaza_editar_la_linea() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "dedicacion"}], doc="d1")
    repo = ParteReviewRepository(fabrica)
    with pytest.raises(CongeladoError) as error:
        repo.update_registro(registro_id=rid, horas=4.0)
    assert error.value.motivo == MOTIVO_LINEA_DEDICACION
    with pytest.raises(CongeladoError):
        repo.soft_delete_registro(registro_id=rid, by="ana")


# =================== T5 · R16 · no se borra definitivamente ==================== #

@pytest.mark.parametrize("estado,esperado", [
    ("dedicacion", True), (" Dedicacion ", True), ("registrado", True),
    ("encolado", False), ("omitido", False), ("borrado_sigrid", False),
    (None, False), ("", False),
])
def test_f019_r16_vive_fuera(estado, esperado) -> None:
    assert vive_fuera(estado) is esperado


def test_f019_r16_hard_delete_de_una_linea_en_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "dedicacion", "borrada": True}],
                     doc="d1")
    repo = ParteReviewRepository(fabrica)
    with pytest.raises(CongeladoError) as error:
        repo.hard_delete_registro(registro_id=rid)
    assert error.value.motivo == MOTIVO_HARD_DELETE_DEDICACION
    assert "dedicación" in MOTIVO_HARD_DELETE_DEDICACION
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, rid) is not None


def test_f019_r16_hard_delete_de_registrada_sigue_con_su_motivo() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": "registrado", "borrada": True}],
                     doc="d1")
    with pytest.raises(CongeladoError) as error:
        ParteReviewRepository(fabrica).hard_delete_registro(registro_id=rid)
    assert error.value.motivo == MOTIVO_HARD_DELETE_REGISTRADO


def test_f019_r16_hard_delete_del_documento_con_linea_en_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"estado": "dedicacion"}, {}], doc="d1",
            doc_activo=False)
    with pytest.raises(CongeladoError) as error:
        ParteReviewRepository(fabrica).hard_delete_document(
            document_id="d1")
    assert error.value.motivo == MOTIVO_HARD_DELETE_DEDICACION


def test_f019_r16_vaciar_la_papelera_respeta_dedicacion() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"estado": "dedicacion"}], doc="d1", doc_activo=False)
    sembrar(fabrica, [{}], doc="d2", doc_activo=False)
    (suelta,) = sembrar(fabrica, [{"estado": "dedicacion", "borrada": True}],
                        doc="d3")
    (libre,) = sembrar(fabrica, [{"borrada": True}], doc="d4")
    resultado = ParteReviewRepository(fabrica).vaciar_papelera()
    assert resultado == {"documentos": 1, "registros": 1, "omitidos": 2}
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, suelta) is not None
        assert s.get(ParteRegistroOrm, libre) is None


# ================ T8 · R17 · no viaja a sv5 · R18 · el listado ================ #

from application.services.reparto_obras import (  # noqa: E402
    GrupoObra,
    listado_grupo,
    totales,
)
from config.settings import Settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from interface_adapters.web.app import build_app  # noqa: E402
from tests.test_f022_aprobar_seleccion import (  # noqa: E402
    CalendarioFalso,
    PublisherFalso,
    Sv5Falso,
)

MOTIVO_EXCLUIDA = ("enviada a dedicación: para reenviarla, «Retirar de "
                   "dedicación»")


def test_f019_r17_repo_la_linea_en_dedicacion_no_viaja() -> None:
    fabrica = FabricaSesionSqlite()
    ded, libre, reg = sembrar(fabrica, [{"estado": "dedicacion"}, {},
                                        {"estado": "registrado"}], doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        [ded, libre, reg])
    assert [l["registro_id"] for l in datos["lineas"]] == [libre]
    assert datos["excluidas"] == {"registrado": 1, "borrado_sigrid": 0,
                                  "dedicacion": 1}
    detalle = {d["registro_id"]: d for d in datos["excluidas_detalle"]}
    assert (detalle[ded]["estado"], detalle[ded]["motivo"]) == (
        "dedicacion", MOTIVO_EXCLUIDA)
    assert detalle[reg]["estado"] == "registrado"


def test_f019_r17_repo_sin_ninguna_no_aparece_la_clave() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{}], doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(ids)
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "x", "PG_ADMIN_PASSWORD": "x",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)

    def _levantar(lineas: list[dict]):
        fabrica = FabricaSesionSqlite()
        ids = sembrar(fabrica, lineas, doc="d1")
        sv5, publisher = Sv5Falso(), PublisherFalso()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        calendario_provider=CalendarioFalso())
        return TestClient(app), fabrica, ids, sv5, publisher
    return _levantar


@pytest.mark.parametrize("ruta", ["/api/aprobar/preflight",
                                  "/api/aprobar/ejecutar",
                                  "/api/aprobar/encolar"])
def test_f019_r17_si_solo_hay_dedicacion_el_422_lo_dice(portal, ruta) -> None:
    cliente, _f, ids, sv5, publisher = portal([{"estado": "dedicacion"},
                                               {"estado": "dedicacion"}])
    r = cliente.post(ruta, json={"registro_ids": ids})
    assert r.status_code == 422
    assert r.json()["error"] == (
        "no hay lineas que registrar: 2 enviada(s) a dedicación (para "
        "reenviarlas, «Retirar de dedicación»)")
    assert r.json()["excluidas"]["dedicacion"] == 2
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []


def test_f019_r17_con_otras_lineas_viajan_solo_las_otras(portal) -> None:
    cliente, _f, ids, _sv5, publisher = portal([{"estado": "dedicacion"},
                                                {}])
    r = cliente.post("/api/aprobar/encolar", json={"registro_ids": ids})
    assert r.status_code == 200
    assert r.json()["excluidas"]["dedicacion"] == 1
    ((payload, _usuario),) = publisher.publicadas
    assert [l["registro_id"] for l in payload["lineas"]] == [ids[1]]


def test_f019_r17_el_motivo_combina_con_las_demas_exclusiones(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal([{"estado": "dedicacion"},
                                         {"estado": "registrado"}])
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    assert r.json()["error"] == (
        "no hay lineas que registrar: 1 ya registrada(s) en Sigrid (no se "
        "reenvian) y 1 enviada(s) a dedicación (para reenviarlas, «Retirar "
        "de dedicación»)")


def _grupo() -> GrupoObra:
    lineas = [
        {"registro_id": 1, "fecha_int": 20260302, "nombre": "A",
         "tipo_hora": "normal", "horas": 8.0, "hora_codigo": "MENC"},
        {"registro_id": 2, "fecha_int": 20260302, "nombre": "A",
         "es_incidencia": True, "horas": 0.0, "hora_codigo": "CIV"},
        {"registro_id": 3, "fecha_int": 20260302, "nombre": "B",
         "tipo_hora": "normal", "horas": 8.0, "hora_codigo": "HL01"},
    ]
    return GrupoObra(clave="obr-10", obra={"codigo": "0100"}, lineas=lineas,
                     estado_previo={1: "omitido"})


def test_f019_r18_el_listado_las_ensena_a_dedicacion() -> None:
    motivo = "recurso mensual (MENC): sus horas van a dedicacion, no a Sigrid"
    pf = {"ok": True, "conflictos": [], "acciones": [
        {"registro_id": 1, "accion": "dedicacion", "codigo_mes": "MENC",
         "motivo": motivo},
        {"registro_id": 2, "accion": "dedicacion", "codigo_mes": "MENC",
         "motivo": None},
        {"registro_id": 3, "accion": "escribir", "can": 8.0,
         "hora_codigo": "HL01"}]}
    filas = {f["registro_id"]: f for f in listado_grupo(_grupo(), pf)}
    assert (filas[1]["estado"], filas[1]["motivo"]) == ("dedicacion", motivo)
    assert (filas[2]["estado"], filas[2]["motivo"]) == (
        "dedicacion", "va a dedicación: no se escribe en Sigrid")
    assert filas[3]["estado"] == "nuevo"
    t = totales(list(filas.values()))
    assert t["por_estado"] == {"dedicacion": 2, "nuevo": 1}
    assert (t["horas_ordinarias"], t["incidencias"]) == (8.0, 0)



# ============== T9 · R21-R24 · «Retirar de dedicacion» y reaprobar ============= #

from infrastructure.database.orm_models import (  # noqa: E402
    DedicacionBandejaOrm,
)
from tests.test_f019_bandeja import (  # noqa: E402
    _filas,
    _marcar,
    sembrar_mensual,
)

PERSONA = {"vista": "trabajador", "worker_key": "emp-77"}


@pytest.fixture
def publicado(monkeypatch):
    """Un mensual con sus tres lineas publicadas en la bandeja, una linea
    libre suya, otra `registrado` suya y una de otra persona; y el portal."""
    for clave, valor in {"PG_PASSWORD": "x", "PG_ADMIN_PASSWORD": "x",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    fabrica = FabricaSesionSqlite()
    ded = sembrar_mensual(fabrica)
    repo = ParteReviewRepository(fabrica)
    _marcar(repo, ded)
    libre, reg = sembrar(fabrica, [{}, {"estado": "registrado"}], doc="d2",
                         empleado_ide=77, fecha="2026-03-05")
    (ajena,) = sembrar(fabrica, [{"estado": "dedicacion"}], doc="d3",
                       empleado_ide=88, dni="00000001R",
                       nombre="Persona B")
    app = build_app(Settings(_env_file=None), repository=repo,
                    transfer_client=Sv5Falso(), publisher=PublisherFalso(),
                    calendario_provider=CalendarioFalso())
    return {"cliente": TestClient(app), "fabrica": fabrica, "repo": repo,
            "ded": ded, "libre": libre, "reg": reg, "ajena": ajena}


def _retirar(p, ids, ambito=PERSONA):
    cuerpo = {"registro_ids": ids}
    if ambito is not None:
        cuerpo["ambito"] = ambito
    return p["cliente"].post("/api/dedicacion/retirar", json=cuerpo)


def _estado(fabrica, rid) -> tuple:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        return (r.sigrid_estado, r.sigrid_motivo, r.sigrid_registrado_by)


def test_f019_r21_retirar_libera_la_linea_y_retira_la_fila(publicado) -> None:
    p = publicado
    r = _retirar(p, p["ded"][:2])
    assert r.status_code == 200
    assert r.json() == {"ok": True, "retiradas": 2, "no_aplica": 0}
    filas = _filas(p["fabrica"])
    for rid in p["ded"][:2]:
        assert _estado(p["fabrica"], rid) == (
            None, "retirada de dedicación", "local:ana")
        f = filas[rid]
        assert (f["vigente"], f["version"], f["retirado_por"]) == (
            False, 2, "local:ana")
        assert f["retirado_at_utc"] == f["actualizado_at_utc"]
        assert f["retirado_at_utc"] > f["enviado_at_utc"]
    # La tercera sigue publicada.
    assert (filas[p["ded"][2]]["vigente"], filas[p["ded"][2]]["version"]) \
        == (True, 1)
    assert _estado(p["fabrica"], p["ded"][2])[0] == "dedicacion"


def test_f019_r21_un_id_ajeno_rechaza_todo_sin_tocar_nada(publicado) -> None:
    p = publicado
    antes = _filas(p["fabrica"])
    r = _retirar(p, [p["ded"][0], p["ajena"]])
    assert r.status_code == 422
    assert r.json()["fuera_de_ambito"] == 1
    assert _filas(p["fabrica"]) == antes
    assert _estado(p["fabrica"], p["ded"][0])[0] == "dedicacion"
    assert _estado(p["fabrica"], p["ajena"])[0] == "dedicacion"


@pytest.mark.parametrize("cuerpo", [
    {"registro_ids": [1]},                                  # sin ambito
    {"registro_ids": ["x"], "ambito": PERSONA},             # ids malos
    {"registro_ids": [], "ambito": PERSONA},                # sin ids
    {"registro_ids": [1], "ambito": {"vista": "otra"}},
])
def test_f019_r21_peticiones_invalidas_son_422(publicado, cuerpo) -> None:
    p = publicado
    antes = _filas(p["fabrica"])
    r = p["cliente"].post("/api/dedicacion/retirar", json=cuerpo)
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert _filas(p["fabrica"]) == antes


def test_f019_r22_las_que_no_estan_en_dedicacion_no_se_tocan(publicado) -> None:
    p = publicado
    antes = {i: _estado(p["fabrica"], i) for i in (p["libre"], p["reg"])}
    r = _retirar(p, [p["ded"][0], p["libre"], p["reg"]])
    assert r.json() == {"ok": True, "retiradas": 1, "no_aplica": 2}
    assert {i: _estado(p["fabrica"], i) for i in (p["libre"], p["reg"])} \
        == antes


def test_f019_r22_repo_cuenta_lo_que_no_aplica() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    repo = ParteReviewRepository(fabrica)
    _marcar(repo, ids[:1])
    assert repo.retirar_de_dedicacion([ids[0], ids[1], 99999], "eva") == {
        "retiradas": 1, "no_aplica": 2}
    assert repo.retirar_de_dedicacion([], "eva") == {
        "retiradas": 0, "no_aplica": 0}


def test_f019_r21_repo_una_linea_sin_fila_se_libera_igual() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar(fabrica, [{"estado": " Dedicacion "}], doc="d1")
    repo = ParteReviewRepository(fabrica)
    assert repo.retirar_de_dedicacion([rid], "eva") == {
        "retiradas": 1, "no_aplica": 0}
    assert _estado(fabrica, rid) == (None, "retirada de dedicación", "eva")
    assert _filas(fabrica) == {}


def test_f019_r23_reaprobar_tras_retirar_vuelve_a_publicar(publicado) -> None:
    p = publicado
    rid = p["ded"][0]
    assert _retirar(p, [rid]).status_code == 200
    # Libre: se edita y viaja otra vez a sv5.
    p["repo"].update_registro(registro_id=rid, horas=7.0)
    datos = p["repo"].lineas_para_registro([rid])
    assert [l["registro_id"] for l in datos["lineas"]] == [rid]
    _marcar(p["repo"], [rid], usuario="eva")
    f = _filas(p["fabrica"])[rid]
    assert (f["vigente"], f["version"], f["horas"], f["enviado_por"],
            f["retirado_por"]) == (True, 3, 7.0, "eva", None)
    assert _estado(p["fabrica"], rid)[0] == "dedicacion"


def test_f019_r23_reaprobar_con_el_interruptor_apagado_sigue_las_reglas(
        publicado) -> None:
    """Retirada y reaprobada sin dedicacion en el resultado: la linea queda
    como digan las reglas de siempre y la fila sigue retirada."""
    p = publicado
    rid = p["ded"][0]
    _retirar(p, [rid])
    p["repo"].marcar_registros_sigrid(
        escritas=[], omitidas=[{"registro_id": rid, "motivo": "mensual"}],
        ya_registradas=[], usuario="ana")
    assert _estado(p["fabrica"], rid)[:2] == ("omitido", "mensual")
    assert _filas(p["fabrica"])[rid]["vigente"] is False


def test_f019_r24_el_autor_es_el_actor_de_la_peticion(publicado) -> None:
    p = publicado
    r = p["cliente"].post(
        "/api/dedicacion/retirar",
        json={"registro_ids": [p["ded"][1]], "ambito": PERSONA},
        headers={"X-MS-CLIENT-PRINCIPAL-NAME": "Eva@Ruesma.es"})
    assert r.status_code == 200
    with p["fabrica"].create_session() as s:
        fila = s.get(DedicacionBandejaOrm, p["ded"][1])
        autor = fila.retirado_por
    assert autor == _estado(p["fabrica"], p["ded"][1])[2]
    assert autor not in (None, "")
