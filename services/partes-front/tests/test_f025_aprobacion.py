# tests/test_f025_aprobacion.py
"""F-025 · la aprobacion deja fuera los dias con incidencia de dia
completo y horas (R9-R14, R23).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`),
`TestClient` y los dobles de sv5, publisher y calendario de F-022.
Personas, DNIs, obras y partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import (
    ParteReviewRepository,
    persona_de,
)
from tests.dobles import FabricaSesionSqlite
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
