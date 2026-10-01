# tests/test_f022_aprobar_seleccion.py
"""F-022 · aprobar solo lo seleccionado: repositorio y endpoints de sv4.

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`) y
dobles de sv5, del publisher y del calendario. Obras, personas, DNIs y
codigos de parte SINTETICOS.

Bloques (los `-k` de tasks.md): `repo` (T2), `ambito` (T5), `preflight`
(T6), `ejecutar` (T7) y `encolar` (T8).
"""
from __future__ import annotations

import pytest
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

# Tres obras: dos con `obra_ide` y una solo con codigo. Sus claves
# (`obra_key_for_registro`) ordenadas: cod-0300 < obr-10 < obr-20.
OBRA_10 = {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"}
OBRA_20 = {"ide": 20, "codigo": "0200", "nombre": "Obra Uno"}
OBRA_300 = {"ide": None, "codigo": "0300", "nombre": "Obra Uno"}


def _sembrar(fabrica, obra: dict, estados: list, *, doc: str,
             fecha: str = "2026-03-02", **kw) -> list[int]:
    return sembrar_parte(fabrica, [{"estado": e} for e in estados],
                         document_id=doc, fecha=fecha,
                         obra_ide=obra["ide"], obra_codigo=obra["codigo"],
                         **kw)


def _tres_obras():
    """obr-20: [nueva, error]; obr-10: [nueva, registrado];
    cod-0300: [borrado_sigrid, nueva]. Todas de la persona emp-77."""
    fabrica = FabricaSesionSqlite()
    a = _sembrar(fabrica, OBRA_20, [None, "error"], doc="doc-a")
    b = _sembrar(fabrica, OBRA_10, [None, "registrado"], doc="doc-b",
                 fecha="2026-03-03")
    c = _sembrar(fabrica, OBRA_300, ["borrado_sigrid", None], doc="doc-c",
                 fecha="2026-03-04")
    return ParteReviewRepository(fabrica), fabrica, a, b, c


# ===================================================================== #
# T2 · repositorio: registro_ids_de_trabajador, grupos, excluidas_detalle
# ===================================================================== #

def test_f022_r10_repo_ids_de_trabajador_son_los_de_su_tabla() -> None:
    repo, fabrica, a, b, c = _tres_obras()
    otra = _sembrar(fabrica, OBRA_10, [None], doc="doc-otra",
                    empleado_ide=88, empleado_dni="00000001R")
    papelera = _sembrar(fabrica, OBRA_10, [None], doc="doc-pap",
                        doc_en_papelera=True)
    borrada = sembrar_parte(fabrica, [{"borrada": True}], document_id="doc-bo",
                            obra_ide=10, obra_codigo="0100")
    ids = repo.registro_ids_de_trabajador("emp-77")
    assert sorted(ids) == sorted(a + b + c)
    assert ids == [v.id for v in repo.get_worker("emp-77").registros]
    assert not set(ids) & set(otra + papelera + borrada)


def test_f022_r10_repo_ids_de_trabajador_inexistente_es_lista_vacia() -> None:
    repo, *_ = _tres_obras()
    assert repo.registro_ids_de_trabajador("emp-999") == []


def test_f022_r14_repo_grupos_uno_por_obra_en_orden_de_clave() -> None:
    repo, _f, a, b, c = _tres_obras()
    datos = repo.lineas_para_registro(a + b + c)
    grupos = datos["grupos"]
    assert [g["clave"] for g in grupos] == ["cod-0300", "obr-10", "obr-20"]
    assert [g["obra"] for g in grupos] == [OBRA_300, OBRA_10, OBRA_20]
    # Solo viajan las lineas que pasan F-024 R22 (sin registrado ni
    # borrado_sigrid), cada una en el grupo de SU obra.
    assert [[l["registro_id"] for l in g["lineas"]] for g in grupos] == [
        [c[1]], [b[0]], [a[0], a[1]]]
    assert grupos[2]["estado_previo"] == {a[0]: "", a[1]: "error"}
    assert grupos[1]["estado_previo"] == {b[0]: ""}


def test_f022_r14_repo_grupos_con_borradas_incluidas() -> None:
    repo, _f, _a, _b, c = _tres_obras()
    grupos = repo.lineas_para_registro(c, incluir_borradas=True)["grupos"]
    assert len(grupos) == 1
    assert [l["registro_id"] for l in grupos[0]["lineas"]] == c
    assert grupos[0]["estado_previo"] == {c[0]: "borrado_sigrid", c[1]: ""}


def test_f022_r14_repo_el_estado_previo_va_normalizado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, [" Error ", "ENCOLADO"], doc="doc-n")
    grupos = ParteReviewRepository(fabrica).lineas_para_registro(ids)["grupos"]
    assert grupos[0]["estado_previo"] == {ids[0]: "error", ids[1]: "encolado"}


def test_f022_r14_repo_los_planos_de_hoy_no_cambian() -> None:
    repo, _f, a, b, c = _tres_obras()
    datos = repo.lineas_para_registro(a + b + c)
    viajan = sorted(l["registro_id"] for g in datos["grupos"]
                    for l in g["lineas"])
    assert sorted(l["registro_id"] for l in datos["lineas"]) == viajan
    assert datos["excluidas"] == {"registrado": 1, "borrado_sigrid": 1}
    # R33: el estado previo no se cuela en las lineas del payload.
    for g in datos["grupos"]:
        for linea in g["lineas"]:
            assert "estado_previo" not in linea
            assert linea in datos["lineas"]


def test_f022_r14_repo_sin_lineas_no_hay_grupos() -> None:
    repo, _f, _a, b, _c = _tres_obras()
    assert repo.lineas_para_registro([])["grupos"] == []
    # Todo excluido: tampoco hay grupos.
    assert repo.lineas_para_registro([b[1]])["grupos"] == []


def test_f022_r14_repo_grupo_sin_obra_identificada_va_con_obra_vacia() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, {"ide": None, "codigo": None, "nombre": None},
                   [None], doc="doc-s")
    grupos = ParteReviewRepository(fabrica).lineas_para_registro(ids)["grupos"]
    assert grupos[0]["clave"] == "nom-OBRA_UNO"
    assert grupos[0]["obra"] == {}


def test_f022_r26_repo_excluidas_detalle() -> None:
    repo, fabrica, _a, b, c = _tres_obras()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, c[0]).sigrid_parte_cod = "PT26/00007"
        s.commit()
    detalle = repo.lineas_para_registro(b + c)["excluidas_detalle"]
    assert [d["registro_id"] for d in detalle] == [b[1], c[0]]
    reg, bor = detalle
    assert reg == {
        "registro_id": b[1], "fecha_int": 20260303, "nombre": "Pepe Perez",
        "obra_codigo": "0100", "horas": 8.0, "hora_codigo": "HL01",
        "estado": "registrado", "parte_cod": "PT26/00001",
        "motivo": "ya registrada en Sigrid (parte PT26/00001): no se reenvia",
    }
    assert bor["estado"] == "borrado_sigrid"
    assert bor["parte_cod"] == "PT26/00007"
    assert bor["motivo"] == (
        "borrada en Sigrid: para reenviarla marca «Incluir las borradas en "
        "Sigrid» o usa «Reaprobar»")


def test_f022_r26_repo_excluida_sin_parte_conocido() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, ["registrado"], doc="doc-x")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).sigrid_parte_cod = None
        s.commit()
    detalle = ParteReviewRepository(fabrica).lineas_para_registro(ids)[
        "excluidas_detalle"]
    assert detalle[0]["motivo"] == ("ya registrada en Sigrid (parte ?): no "
                                    "se reenvia")


def test_f022_r26_repo_con_borradas_incluidas_no_hay_detalle_de_ellas() -> None:
    repo, _f, _a, _b, c = _tres_obras()
    assert repo.lineas_para_registro(
        c, incluir_borradas=True)["excluidas_detalle"] == []
