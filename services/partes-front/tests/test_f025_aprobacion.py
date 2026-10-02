# tests/test_f025_aprobacion.py
"""F-025 · la aprobacion deja fuera los dias con incidencia de dia
completo y horas (R9-R14, R23).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`),
`TestClient` y los dobles de sv5, publisher y calendario de F-022.
Personas, DNIs, obras y partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    persona_de,
)
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, estados_sigrid
from tests.test_f022_aprobar_seleccion import (
    CalendarioFalso,
    PublisherFalso,
    Sv5Falso,
)
from tests.test_f025_deteccion import TABLA

AHORA = "2026-03-02T08:00:00+00:00"
OBRA_10 = {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"}
OBRA_20 = {"ide": 20, "codigo": "0200", "nombre": "Obra Dos"}
DNI_A = "12345678Z"
DNI_B = "00000001R"

#: Las claves de cada linea del payload de sv5 (R33 de F-022, R14).
CLAVES_LINEA = {"registro_id", "fecha_int", "recurso_ide", "dni", "nombre",
                "tipo_hora", "es_incidencia", "horas", "hora_ide",
                "hora_codigo", "partida_ide", "partida_cod", "candef",
                "incidencia_codigo", "incidencia_rol"}


def sembrar(fabrica, lineas: list[dict], *, doc: str,
            fecha: str = "2026-03-02", obra: dict = OBRA_10,
            dni: str | None = DNI_A, empleado_ide: int | None = 77,
            nombre: str = "Persona A", doc_activo: bool = True) -> list[int]:
    """Un parte con lineas de una persona. Cada linea admite: `inc` (la
    letra), `ci` (codigo de hora de la incidencia), `tipo` (`normal` o
    `extra`), `horas`, `estado` (`sigrid_estado`) y `borrada`."""
    fint = int(fecha.replace("-", ""))
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=doc, source_filename="parte.pdf",
            source_mime_type="application/pdf", source_sha256="sha" + doc,
            fecha=fecha, fecha_int=fint, created_at_utc=AHORA,
            obra_ide=obra["ide"], obra_codigo=obra["codigo"],
            obra_nombre=obra["nombre"], is_active=doc_activo,
            deleted_at_utc=None if doc_activo else AHORA))
        ids: list[int] = []
        for i, linea in enumerate(lineas):
            es_inc = bool(linea.get("inc") or linea.get("ci"))
            tipo = linea.get("tipo", "normal")
            estado = linea.get("estado")
            reg = ParteRegistroOrm(
                document_id=doc, line_index=i, empleado_line_no=1,
                fecha=fecha, fecha_int=fint, obra_ide=obra["ide"],
                obra_codigo=obra["codigo"], obra_nombre=obra["nombre"],
                empleado_ide=empleado_ide, empleado_dni=dni,
                empleado_nombre=nombre, trabajador_nombre_leido=nombre,
                recurso_ide=501, recurso_cif=dni, tipo_hora=tipo,
                horas=linea.get("horas", 0.0 if es_inc else 8.0),
                es_incidencia=es_inc, incidencia_codigo=linea.get("inc"),
                hora_ide=1,
                hora_codigo=linea.get("ci") or (
                    "HE01" if tipo == "extra" else "HL01"),
                hora_candef=8.0, sigrid_estado=estado,
                sigrid_hmores_ide=9000 + i if estado == "registrado" else None,
                sigrid_parte_cod="PT26/00001" if estado == "registrado"
                else None,
                deleted_at_utc=AHORA if linea.get("borrada") else None)
            s.add(reg)
            s.flush()
            ids.append(reg.id)
        s.commit()
    return ids


def _viajan(datos: dict) -> list[int]:
    return [l["registro_id"] for l in datos["lineas"]]


# ===================================================================== #
# T4 · repositorio
# ===================================================================== #

def test_f025_r4_persona_es_el_dni_normalizado_o_la_clave() -> None:
    con_dni = ParteRegistroOrm(empleado_dni=" 1234-5678 z", empleado_ide=1)
    sin_dni = ParteRegistroOrm(empleado_dni=None, empleado_ide=9)
    vacio = ParteRegistroOrm(empleado_dni="  ", empleado_ide=None,
                             trabajador_nombre_leido="Pepe Leido")
    assert persona_de(con_dni) == "dni:12345678Z"
    assert persona_de(sin_dni) == "emp-9"
    assert persona_de(vacio) == "nom-PEPE_LEIDO"


def test_f025_r9_repo_bloqueo_excluye_con_su_motivo() -> None:
    fabrica = FabricaSesionSqlite()
    dia = sembrar(fabrica, [{"inc": "M"}, {"horas": 8.0}], doc="d1")
    otro = sembrar(fabrica, [{"horas": 8.0}], doc="d2", fecha="2026-03-03")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        dia + otro, incidencias=TABLA)
    assert _viajan(datos) == otro
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0,
                                  "incompatible": 2}
    detalle = datos["excluidas_detalle"]
    assert [d["registro_id"] for d in detalle] == dia
    assert {d["estado"] for d in detalle} == {"incompatible"}
    assert detalle[1]["motivo"] == (
        "Maternidad/Paternidad (M) es de día completo y ese día hay 8 h de "
        "trabajo: deja solo una de las dos")
    assert detalle[1]["nombre"] == "Persona A"
    assert detalle[1]["obra_codigo"] == "0100"
    assert [g["clave"] for g in datos["grupos"]] == ["obr-10"]


def test_f025_r9_repo_mira_lineas_no_pedidas_y_de_otras_obras() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"inc": "V"}], doc="d20", obra=OBRA_20)
    horas = sembrar(fabrica, [{"horas": 8.0}, {"tipo": "extra",
                                               "horas": 2.0}], doc="d10")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        horas, incidencias=TABLA)
    assert datos["lineas"] == [] and datos["grupos"] == []
    assert datos["excluidas"]["incompatible"] == 2


def test_f025_r9_repo_la_persona_es_el_dni_aunque_cambie_el_casado() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [{"ci": "CIE"}], doc="d1", dni="12345678-z",
            empleado_ide=None, nombre="Leido Distinto")
    horas = sembrar(fabrica, [{"horas": 8.0}], doc="d2", obra=OBRA_20)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        horas, incidencias=TABLA)
    assert datos["excluidas"].get("incompatible") == 1


@pytest.mark.parametrize("como", ["linea_borrada", "doc_en_papelera",
                                  "otra_persona", "otro_dia"])
def test_f025_r9_repo_lo_que_no_es_linea_activa_del_dia_no_cuenta(
        como) -> None:
    fabrica = FabricaSesionSqlite()
    kw = {"doc": "d-inc"}
    linea = {"inc": "M"}
    if como == "linea_borrada":
        linea["borrada"] = True
    elif como == "doc_en_papelera":
        kw["doc_activo"] = False
    elif como == "otra_persona":
        kw.update(dni=DNI_B, empleado_ide=88)
    else:
        kw["fecha"] = "2026-03-03"
    sembrar(fabrica, [linea], **kw)
    horas = sembrar(fabrica, [{"horas": 8.0}], doc="d-h")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        horas, incidencias=TABLA)
    assert _viajan(datos) == horas
    assert "incompatible" not in datos["excluidas"]


def test_f025_r9_repo_consulta_las_fechas_en_lotes(monkeypatch) -> None:
    monkeypatch.setattr(repo_mod, "LOTE_IDS_CONSULTA", 1)
    fabrica = FabricaSesionSqlite()
    pedidas = []
    for dia in ("2026-03-02", "2026-03-03", "2026-03-04"):
        sembrar(fabrica, [{"inc": "B"}], doc="i" + dia, fecha=dia,
                obra=OBRA_20)
        pedidas += sembrar(fabrica, [{"horas": 8.0}], doc="h" + dia,
                           fecha=dia)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        pedidas, incidencias=TABLA)
    assert datos["excluidas"]["incompatible"] == 3
    assert datos["lineas"] == []


def test_f025_r11_repo_aviso_viaja_y_se_lista_solo_la_extra() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "FJ"}, {"horas": 6.0},
                            {"tipo": "extra", "horas": 2.0}], doc="d1")
    otra = sembrar(fabrica, [{"horas": 8.0}], doc="d2", obra=OBRA_20)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        ids + otra, incidencias=TABLA)
    assert sorted(_viajan(datos)) == sorted(ids + otra)
    assert "incompatible" not in datos["excluidas"]
    g10, g20 = datos["grupos"]
    assert g10["avisos_incidencia"] == [{
        "registro_id": ids[2], "fecha": "2026-03-02", "nombre": "Persona A",
        "horas": 2.0,
        "motivo": "Permiso (FJ) y 2 h extra el mismo día: comprueba que "
                  "sean correctas"}]
    assert g20["avisos_incidencia"] == []


def test_f025_r13_repo_registrado_cuenta_solo_en_su_estado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "M"}, {"horas": 8.0,
                                           "estado": "registrado"},
                            {"tipo": "extra", "horas": 1.0}], doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=TABLA)
    assert datos["lineas"] == []
    assert datos["excluidas"] == {"registrado": 1, "borrado_sigrid": 0,
                                  "incompatible": 2}
    estados = {d["registro_id"]: d["estado"]
               for d in datos["excluidas_detalle"]}
    assert estados == {ids[0]: "incompatible", ids[1]: "registrado",
                       ids[2]: "incompatible"}


def test_f025_r13_repo_borrada_en_sigrid_cuenta_solo_en_su_estado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "M"}, {"horas": 8.0,
                                           "estado": "borrado_sigrid"}],
                  doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=TABLA)
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 1,
                                  "incompatible": 1}


def test_f025_r12_repo_incluir_borradas_no_levanta_el_bloqueo() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "M"}, {"horas": 8.0,
                                           "estado": "borrado_sigrid"}],
                  doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incluir_borradas=True, incidencias=TABLA)
    assert datos["lineas"] == []
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0,
                                  "incompatible": 2}


def test_f025_r14_repo_las_lineas_que_viajan_no_cambian_de_forma() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "AT"}, {"tipo": "extra", "horas": 2.0}],
                  doc="d1")
    repo = ParteReviewRepository(fabrica)
    con = repo.lineas_para_registro(ids, incidencias=TABLA)
    sin = repo.lineas_para_registro(ids)
    assert con["lineas"] == sin["lineas"]
    assert all(set(l) == CLAVES_LINEA for l in con["lineas"])
    for g in con["grupos"]:
        assert all("avisos_incidencia" not in l for l in g["lineas"])


def test_f025_r23_repo_sin_tabla_todo_como_antes() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar(fabrica, [{"inc": "M"}, {"horas": 8.0},
                            {"inc": "FJ"}, {"tipo": "extra", "horas": 2.0}],
                  doc="d1")
    datos = ParteReviewRepository(fabrica).lineas_para_registro(ids)
    assert _viajan(datos) == ids
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    assert datos["excluidas_detalle"] == []
    assert [g["avisos_incidencia"] for g in datos["grupos"]] == [[]]


# ===================================================================== #
# T5 · endpoints de la aprobacion (R9-R12, R14)
# ===================================================================== #

ENDPOINTS = ("/api/aprobar/preflight", "/api/aprobar/ejecutar",
             "/api/aprobar/encolar")


def _escenario_portal(fabrica) -> dict[str, list[int]]:
    """Persona A: dia 02 con M (obra 20) y horas (obra 10) en bloqueo; dia
    03 con FJ y 2 h extra en aviso (obra 10); dia 04 normal (obra 10).
    Persona B: dia 02 normal en la obra 10."""
    return {
        "inc_m": sembrar(fabrica, [{"inc": "M"}], doc="p-m", obra=OBRA_20),
        "bloq": sembrar(fabrica, [{"horas": 8.0},
                                  {"tipo": "extra", "horas": 1.0}],
                        doc="p-bloq"),
        "aviso": sembrar(fabrica, [{"inc": "FJ"}, {"horas": 6.0},
                                   {"tipo": "extra", "horas": 2.0}],
                         doc="p-aviso", fecha="2026-03-03"),
        "libre": sembrar(fabrica, [{"horas": 8.0}], doc="p-libre",
                         fecha="2026-03-04"),
        "otra": sembrar(fabrica, [{"horas": 8.0}], doc="p-otra", dni=DNI_B,
                        empleado_ide=88, nombre="Persona B"),
    }


@pytest.fixture
def portal25(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)

    def _levantar(*, publisher="si"):
        fabrica = FabricaSesionSqlite()
        ids = _escenario_portal(fabrica)
        sv5 = Sv5Falso()
        if publisher == "si":
            publisher = PublisherFalso()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        calendario_provider=CalendarioFalso())
        return TestClient(app), fabrica, ids, sv5, publisher
    return _levantar


def _enviadas(payloads) -> list[int]:
    return sorted(l["registro_id"] for p in payloads for l in p["lineas"])


def test_f025_r9_preflight_excluye_el_dia_en_bloqueo(portal25) -> None:
    cliente, _f, ids, sv5, _p = portal25()
    pedidas = ids["bloq"] + ids["libre"] + ids["otra"]
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": pedidas})
    assert r.status_code == 200
    cuerpo = r.json()
    assert _enviadas(sv5.preflights) == sorted(ids["libre"] + ids["otra"])
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0,
                                   "incompatible": 2}
    detalle = {d["registro_id"]: d for d in cuerpo["excluidas_detalle"]}
    assert set(detalle) == set(ids["bloq"])
    assert {d["estado"] for d in detalle.values()} == {"incompatible"}
    assert all("Maternidad/Paternidad (M) es de día completo" in d["motivo"]
               for d in detalle.values())
    listadas = {f["registro_id"] for g in cuerpo["grupos"]
                for f in g["listado"]}
    assert not listadas & set(ids["bloq"])


def test_f025_r11_preflight_lleva_los_avisos_por_grupo(portal25) -> None:
    cliente, _f, ids, sv5, _p = portal25()
    pedidas = ids["aviso"] + ids["libre"]
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": pedidas,
        "ambito": {"vista": "trabajador", "worker_key": "emp-77"}})
    assert r.status_code == 200
    assert _enviadas(sv5.preflights) == sorted(pedidas)
    (grupo,) = r.json()["grupos"]
    assert grupo["avisos_incidencia"] == [{
        "registro_id": ids["aviso"][2], "fecha": "2026-03-03",
        "nombre": "Persona A", "horas": 2.0,
        # El nombre es el de la tabla versionada: build_app la carga.
        "motivo": "Falta justificada o permiso (FJ) y 2 h extra el mismo "
                  "día: comprueba que sean correctas"}]
    assert "incompatible" not in r.json()["excluidas"]


def test_f025_r11_grupo_sin_avisos_lleva_lista_vacia(portal25) -> None:
    cliente, _f, ids, _sv5, _p = portal25()
    r = cliente.post("/api/aprobar/preflight",
                     json={"registro_ids": ids["libre"]})
    assert [g["avisos_incidencia"] for g in r.json()["grupos"]] == [[]]


def test_f025_r11_aviso_con_sv5_caido_sigue_en_el_grupo(portal25) -> None:
    cliente, _f, ids, sv5, _p = portal25()
    sv5._pf["0100"] = RuntimeError("sv5 caido")
    r = cliente.post("/api/aprobar/preflight",
                     json={"registro_ids": ids["aviso"]})
    (grupo,) = r.json()["grupos"]
    assert grupo["ok"] is False
    assert [a["registro_id"] for a in grupo["avisos_incidencia"]] == \
        [ids["aviso"][2]]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_f025_r10_todo_excluido_es_422_sin_llamar_a_sv5(portal25,
                                                        endpoint) -> None:
    cliente, fabrica, ids, sv5, publisher = portal25()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["libre"][0]).sigrid_estado = "registrado"
        s.commit()
    antes = estados_sigrid(fabrica, ids["bloq"] + ids["libre"])
    r = cliente.post(endpoint, json={
        "registro_ids": ids["bloq"] + ids["libre"]})
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["excluidas"] == {"registrado": 1, "borrado_sigrid": 0,
                                   "incompatible": 2}
    assert cuerpo["error"] == (
        "no hay lineas que registrar: 1 ya registrada(s) en Sigrid (no se "
        "reenvian) y 2 con una incidencia de día completo y horas el mismo "
        "día (corrige el día en el portal)")
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []
    assert estados_sigrid(fabrica, ids["bloq"] + ids["libre"]) == antes


def test_f025_r10_solo_incompatibles_nombra_solo_eso(portal25) -> None:
    cliente, _f, ids, _sv5, _p = portal25()
    r = cliente.post("/api/aprobar/preflight",
                     json={"registro_ids": ids["bloq"][:1]})
    assert r.status_code == 422
    assert r.json()["error"] == (
        "no hay lineas que registrar: 1 con una incidencia de día completo "
        "y horas el mismo día (corrige el día en el portal)")


def test_f025_r9_ejecutar_no_envia_ni_marca_el_bloqueo(portal25) -> None:
    cliente, fabrica, ids, sv5, _p = portal25()
    antes = estados_sigrid(fabrica, ids["bloq"])
    r = cliente.post("/api/aprobar/ejecutar", json={
        "registro_ids": ids["bloq"] + ids["libre"]})
    assert r.status_code == 200
    assert _enviadas(sv5.ejecutadas) == ids["libre"]
    assert r.json()["excluidas"]["incompatible"] == 2
    assert estados_sigrid(fabrica, ids["bloq"]) == antes
    assert estados_sigrid(fabrica, ids["libre"])[ids["libre"][0]][0] == \
        "registrado"


def test_f025_r9_encolar_no_publica_ni_marca_el_bloqueo(portal25) -> None:
    cliente, fabrica, ids, _sv5, publisher = portal25()
    antes = estados_sigrid(fabrica, ids["bloq"])
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": ids["bloq"] + ids["libre"] + ids["otra"]})
    assert r.status_code == 200
    assert _enviadas([p for p, _u in publisher.publicadas]) == sorted(
        ids["libre"] + ids["otra"])
    assert r.json()["excluidas"]["incompatible"] == 2
    assert estados_sigrid(fabrica, ids["bloq"]) == antes


def test_f025_r9_encolar_sin_colas_tampoco_lo_envia(portal25) -> None:
    cliente, _f, ids, sv5, _p = portal25(publisher=None)
    r = cliente.post("/api/aprobar/encolar", json={
        "registro_ids": ids["bloq"] + ids["libre"]})
    assert r.status_code == 200
    assert _enviadas(sv5.ejecutadas) == ids["libre"]
    assert r.json()["excluidas"]["incompatible"] == 2


@pytest.mark.parametrize("extra", [
    {"incluir_borradas": True},
    {"pisar_claves": ["k1"]},
    {"forzar_sin_sesame": True},
    {"incluir_borradas": True, "pisar_claves": ["k1"],
     "forzar_sin_sesame": True},
])
def test_f025_r12_ningun_override_levanta_la_exclusion(portal25,
                                                       extra) -> None:
    cliente, fabrica, ids, sv5, _p = portal25()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["bloq"][0]).sigrid_estado = \
            "borrado_sigrid"
        s.commit()
    for endpoint in ("/api/aprobar/preflight", "/api/aprobar/ejecutar"):
        r = cliente.post(endpoint, json=dict(
            {"registro_ids": ids["bloq"] + ids["libre"]}, **extra))
        assert r.status_code == 200, endpoint
        assert r.json()["excluidas"]["incompatible"] == \
            (2 if extra.get("incluir_borradas") else 1)
    assert not set(_enviadas(sv5.preflights + sv5.ejecutadas)) & \
        set(ids["bloq"])
    r = cliente.post("/api/aprobar/ejecutar", json=dict(
        {"registro_ids": ids["bloq"]}, **extra))
    assert r.status_code == 422


def test_f025_r14_el_payload_de_sv5_no_cambia_de_forma(portal25) -> None:
    payloads = []
    for endpoint in ENDPOINTS:
        # Un portal por endpoint: ejecutar deja las lineas `registrado`.
        cliente, _f, ids, sv5, publisher = portal25()
        pedidas = ids["bloq"] + ids["aviso"] + ids["libre"]
        cliente.post(endpoint, json={"registro_ids": pedidas})
        payloads += sv5.preflights + sv5.ejecutadas + [
            p for p, _u in publisher.publicadas]
    assert len(payloads) == 3
    for p in payloads:
        assert set(p) == {"obra", "lineas", "pisar_claves", "usuario"}
        assert all(set(l) == CLAVES_LINEA for l in p["lineas"])
        assert _enviadas([p]) == sorted(ids["aviso"] + ids["libre"])
