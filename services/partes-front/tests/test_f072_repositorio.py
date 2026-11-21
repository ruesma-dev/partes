# tests/test_f072_repositorio.py
"""F-072 · El repositorio de sv4 con entradas de obras agrupadas.

- R23: la clave de una línea con marca de entrada es
  `agr-<obra_ide>-<partida_ide>`; la de un documento, la común de sus líneas
  activas; con varias, «borrar obra» no lo mueve y deja un WARNING.
- R24: lista y detalle rotulan `Postv-<partida>` / `<VAR>-<partida>` con la
  descripción de la partida.
- R27, R29: cambiar a una entrada pone obra, partida y marca; salir de una
  entrada deja las partidas en `sin`, sin re-casar.
- R30: el alta manual con entrada reutiliza el documento del día, obra y
  entrada.
- R31: la extra del popup (y el alta en celda) copian partida y marca.
- R32: la partida de una línea con marca no se cambia (`PartidaFijaError`).
- R33: el payload de sv5 lleva `partida_metodo` en cada línea de entrada.

Sin red ni BBDD real: SQLite. Datos FICTICIOS.
"""
from __future__ import annotations

import logging

import pytest

from application.services.catalogo_entradas import Entrada
from infrastructure.database.orm_models import ParteDocumentOrm, ParteRegistroOrm
from infrastructure.database.parte_repository import (
    PartidaFijaError,
    obra_key_for_registro,
)
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f046_aplicar import _marcar
from tests.test_f056_decisiones import _repo

LOGGER = "infrastructure.database.parte_repository"
E29 = Entrada(tipo="var", obra_ide=9101, obra_codigo="VAR",
              obra_nombre="OBRAS VARIAS", empresa=1, partida_ide=91012,
              partida_cod="29", partida_res="VARIOS 29", partida_capitulo="CD",
              codigo="VAR-29", nombre="VARIOS 29")
E30 = Entrada(tipo="var", obra_ide=9101, obra_codigo="VAR",
              obra_nombre="OBRAS VARIAS", empresa=1, partida_ide=91013,
              partida_cod="030", partida_res="VARIOS 30", partida_capitulo="CD",
              codigo="VAR-030", nombre="VARIOS 30")
PV578 = Entrada(tipo="postventa", obra_ide=9001, obra_codigo="POSTV2",
                obra_nombre="POSTVENTA", empresa=1, partida_ide=90011,
                partida_cod="0578B", partida_res="RESIDENCIAL 578",
                partida_capitulo="CD", codigo="Postv-0578B",
                nombre="RESIDENCIAL 578")


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _en_entrada(fabrica, ids, e: Entrada):
    for rid in ids:
        _marcar(fabrica, rid, partida_ide=e.partida_ide,
                partida_cod=e.partida_cod, partida_res=e.partida_res,
                partida_capitulo=e.partida_capitulo,
                partida_match_method=e.tipo, partida_match_score=1.0)


def _parte(fabrica, e: Entrada | None, doc="d1", fecha="2026-11-16", n=1,
           **kw):
    obra = ({"obra_ide": e.obra_ide, "obra_codigo": e.obra_codigo}
            if e else {"obra_ide": 10, "obra_codigo": "0100"})
    ids = sembrar_parte(fabrica, [{"horas": 8.0}] * n, document_id=doc,
                        fecha=fecha, **obra, **kw)
    if e:
        _en_entrada(fabrica, ids, e)
    return ids


def _reg(fabrica, rid) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


# --------------------------------- R23 ---------------------------------- #

def test_f072_r23_clave_de_linea():
    r = ParteRegistroOrm(obra_ide=9101, obra_codigo="VAR", partida_ide=91012,
                         partida_match_method="var")
    assert obra_key_for_registro(r) == "agr-9101-91012"
    r.partida_match_method = "postventa"
    assert obra_key_for_registro(r) == "agr-9101-91012"
    for metodo in ("manual", "parte", "sin", None):
        r.partida_match_method = metodo
        assert obra_key_for_registro(r) == "obr-9101"
    r.partida_match_method, r.partida_ide = "var", None
    assert obra_key_for_registro(r) == "obr-9101"


def test_f072_r23_borrar_obra_de_una_entrada(fabrica):
    _parte(fabrica, E29, "d29")
    _parte(fabrica, E30, "d30")
    _parte(fabrica, None, "dn")
    assert _repo(fabrica).soft_delete_obra(obra_key="agr-9101-91012") == (1, 0)
    with fabrica.create_session() as s:
        activos = {d.id for d in s.query(ParteDocumentOrm).filter_by(
            is_active=True)}
    assert activos == {"d30", "dn"}
    assert _repo(fabrica).soft_delete_obra(obra_key="obr-10") == (1, 0)


def test_f072_r23_documento_mixto_no_se_mueve_y_avisa(fabrica, caplog):
    a, b = _parte(fabrica, E29, "dm", n=2)
    _en_entrada(fabrica, [b], E30)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        assert _repo(fabrica).soft_delete_obra(
            obra_key="agr-9101-91012") == (0, 0)
    assert any("dm" in r.getMessage() for r in caplog.records)
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "dm").is_active


# --------------------------------- R24 ---------------------------------- #

def test_f072_r24_lista_y_detalle_rotulan_la_entrada(fabrica):
    _parte(fabrica, E29, "d29")
    _parte(fabrica, PV578, "dpv")
    _parte(fabrica, None, "dn")
    filas = {r.obra_key: (r.obra_codigo, r.obra_nombre, r.obra_ide)
             for r in _repo(fabrica).list_obras()}
    assert filas["agr-9101-91012"] == ("VAR-29", "VARIOS 29", 9101)
    assert filas["agr-9001-90011"] == ("Postv-0578B", "RESIDENCIAL 578", 9001)
    assert filas["obr-10"][0] == "0100"
    det = _repo(fabrica).get_obra("agr-9101-91012")
    assert (det.obra_codigo, det.obra_nombre, det.obra_ide) == (
        "VAR-29", "VARIOS 29", 9101)


# ------------------------------ R27 y R29 ------------------------------- #

def test_f072_r27_cambiar_a_una_entrada(fabrica):
    ids = _parte(fabrica, None, "d1", n=2)
    _marcar(fabrica, ids[0], partida_ide=33, partida_cod="01.01",
            partida_match_method="parte")
    obj = _repo(fabrica).update_parte_obra(
        document_id="d1", obra_ide=9101, obra_codigo="VAR",
        obra_nombre="OBRAS VARIAS", entrada=E29)
    assert obj == []
    for rid in ids:
        r = _reg(fabrica, rid)
        assert (r.obra_ide, r.partida_ide, r.partida_cod, r.partida_res,
                r.partida_capitulo, r.partida_match_method,
                r.partida_match_score) == (9101, 91012, "29", "VARIOS 29",
                                           "CD", "var", 1.0)
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "d1").obra_codigo == "VAR"


def test_f072_r29_salir_de_una_entrada_deja_las_partidas_en_sin(fabrica):
    [rid] = _parte(fabrica, E29, "d29")
    _marcar(fabrica, rid, partida="29")
    obj = _repo(fabrica).update_parte_obra(
        document_id="d29", obra_ide=10, obra_codigo="0100",
        obra_nombre="Obra Uno")
    assert [(o["registro_id"], o["objetivo_cod"]) for o in obj] == [
        (rid, None)]
    r = _reg(fabrica, rid)
    assert (r.partida_ide, r.partida_match_method) == (None, "sin")


def test_f072_r27_sin_entrada_como_siempre(fabrica):
    [rid] = _parte(fabrica, None, "d1")
    _marcar(fabrica, rid, partida="01.01", partida_ide=33,
            partida_match_method="parte")
    obj = _repo(fabrica).update_parte_obra(
        document_id="d1", obra_ide=20, obra_codigo="0200", obra_nombre="Dos")
    assert [(o["objetivo_cod"], o["metodo_previo"]) for o in obj] == [
        ("01.01", "parte")]
    assert _reg(fabrica, rid).partida_match_method is None


# --------------------------------- R30 ---------------------------------- #

def _alta(fabrica, e, dias=("2026-11-16",)):
    return _repo(fabrica).crear_parte_manual(
        obra_ide=e.obra_ide, obra_codigo=e.obra_codigo,
        obra_nombre=e.obra_nombre, empleado_ide=77, empleado_codigo=None,
        empleado_nombre="Pepe Perez", empleado_dni="12345678Z",
        empleado_reside=501, categoria="PEON", dias=list(dias),
        horas_ordinaria=8.0, horas_extra=0.0, entrada=e)


def test_f072_r30_alta_manual_con_entrada(fabrica):
    _parte(fabrica, E29, "d29")
    _parte(fabrica, E30, "d30")
    assert _alta(fabrica, E29)["documentos"] == 0
    with fabrica.create_session() as s:
        nuevas = s.query(ParteRegistroOrm).filter_by(document_id="d29").all()
        assert len(nuevas) == 2
        assert {(r.partida_ide, r.partida_match_method) for r in nuevas} == {
            (91012, "var")}
    assert _alta(fabrica, PV578)["documentos"] == 1
    assert _alta(fabrica, E29, ("2026-11-17",))["documentos"] == 1


# --------------------------------- R31 ---------------------------------- #

def test_f072_r31_la_extra_del_popup_copia_partida_y_marca(fabrica):
    [rid] = _parte(fabrica, E29, "d29")
    nuevo = _repo(fabrica).crear_extra_desde(registro_id=rid, horas=2.0)
    r = _reg(fabrica, nuevo)
    assert (r.partida_ide, r.partida_cod, r.partida_res, r.partida_capitulo,
            r.partida_match_method, r.partida_match_score) == (
        91012, "29", "VARIOS 29", "CD", "var", 1.0)
    assert obra_key_for_registro(r) == "agr-9101-91012"


def test_f072_r31_la_extra_del_popup_sin_entrada_como_antes(fabrica):
    [rid] = _parte(fabrica, None, "dn")
    _marcar(fabrica, rid, partida_ide=33, partida_match_method="parte")
    r = _reg(fabrica, _repo(fabrica).crear_extra_desde(registro_id=rid,
                                                       horas=2.0))
    assert (r.partida_ide, r.partida_match_method) == (None, None)


# --------------------------------- R32 ---------------------------------- #

def test_f072_r32_la_partida_de_una_entrada_es_fija(fabrica):
    [rid] = _parte(fabrica, E29, "d29")
    with pytest.raises(PartidaFijaError, match="partida fija: cambia la "
                       "entrada del parte"):
        _repo(fabrica).set_registro_partida(
            registro_id=rid, partida_ide=91013, partida_cod="030",
            partida_res=None, partida_capitulo=None)
    assert _reg(fabrica, rid).partida_ide == 91012
    [otro] = _parte(fabrica, None, "dn")
    assert _repo(fabrica).set_registro_partida(
        registro_id=otro, partida_ide=33, partida_cod="01.01",
        partida_res=None, partida_capitulo=None)


# --------------------------------- R33 ---------------------------------- #

def test_f072_r33_payload_con_la_marca_y_una_peticion_por_entrada(fabrica):
    a = _parte(fabrica, E29, "d29")
    b = _parte(fabrica, E30, "d30")
    n = _parte(fabrica, None, "dn")
    p = _repo(fabrica).lineas_para_registro(a + b + n)
    grupos = {g["clave"]: g for g in p["grupos"]}
    assert set(grupos) == {"agr-9101-91012", "agr-9101-91013", "obr-10"}
    assert grupos["agr-9101-91012"]["obra"]["codigo"] == "VAR"
    [l29] = grupos["agr-9101-91012"]["lineas"]
    assert (l29["partida_ide"], l29["partida_metodo"]) == (91012, "var")
    [ln] = grupos["obr-10"]["lineas"]
    assert "partida_metodo" not in ln


def test_f072_r31_el_alta_en_celda_clona_partida_y_marca():
    """El alta en celda (F-049) clona de su plantilla `_CAMPOS_CLON_CELDA`,
    que ya incluye la partida y la marca: una entrada sigue siéndolo."""
    from infrastructure.database.parte_repository import (
        _CAMPOS_CLON_CELDA,
        _CAMPOS_PARTIDA_ENTRADA,
    )
    assert set(_CAMPOS_PARTIDA_ENTRADA) <= set(_CAMPOS_CLON_CELDA)
