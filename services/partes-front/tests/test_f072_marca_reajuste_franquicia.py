# tests/test_f072_marca_reajuste_franquicia.py
"""F-072 · Enmienda (b) del 2026-11-21: sv4 manda la marca de la línea base
en el reajuste y en la franquicia.

sv5 aplica la guarda de R36 también a las extras nuevas del reajuste y a la
extra de la franquicia, así que sv4 les manda `partida_metodo`: la marca de
entrada (`postventa` | `var`) de la línea base. Solo viaja una marca de
entrada: con cualquier otro método (o ninguno) el payload es el de antes de
F-072, y en una obra agrupada sv5 lo omite igual que sin marca.

- Franquicia: `elegir_obra` toma la marca de la línea elegida; la fila
  guardada (`franquicia_ajuste`, sin columna nueva, DA5) la recupera de una
  línea del recurso en el periodo con la misma obra y partida
  (`con_metodo_base`), también al aplicar.
- Reajuste: `_reparto_dict` completa la extra nueva con la marca de su base y
  `payload_reajuste` la manda.

Sin red ni BBDD real: SQLite y un sv5 falso. Datos FICTICIOS.
"""
from __future__ import annotations

import pytest

from application.services import franquicia as fq
from application.services.reparto_aviso import payload_reajuste
from infrastructure.database.orm_models import ParteRegistroOrm
from tests.dobles import sembrar_parte
from tests.test_f046_aplicar import _cambio, _marcar, _reparto
from tests.test_f056_decisiones import (  # noqa: F401  (fixtures)
    EJECUTAR_OK,
    REC,
    Sv5Franq,
    _repo,
    entorno,
    fabrica,
    portal,
)


def _l(rid, *, obra=9101, cod="VAR", partida=91012, pcod="29", metodo="var",
       horas=8.0, fecha=20261015):
    return {"registro_id": rid, "fecha_int": fecha, "recurso_ide": REC,
            "tipo_hora": "normal", "es_incidencia": False, "horas": horas,
            "obra_ide": obra, "obra_codigo": cod, "partida_ide": partida,
            "partida_cod": pcod, "partida_metodo": metodo}


# ------------------------------ franquicia ------------------------------- #

def test_f072_elegir_obra_lleva_la_marca_de_la_linea_elegida():
    dia = [_l(1)]
    assert fq.elegir_obra(dia, dia) == {
        "obra_ide": 9101, "obra_codigo": "VAR", "partida_ide": 91012,
        "partida_cod": "29", "partida_metodo": "var"}


@pytest.mark.parametrize("metodo", [None, "parte", "manual", "sin"])
def test_f072_elegir_obra_sin_marca_de_entrada_como_antes(metodo):
    dia = [_l(1, obra=10, cod="0100", partida=33, pcod="01.01",
              metodo=metodo)]
    assert fq.elegir_obra(dia, dia) == {
        "obra_ide": 10, "obra_codigo": "0100", "partida_ide": 33,
        "partida_cod": "01.01"}


def _datos(**kw):
    return dict({"id": 7, "recurso_ide": REC, "periodo": "2026-10",
                 "fecha_int": 20261015, "obra_ide": 9101,
                 "obra_codigo": "VAR", "partida_ide": 91012,
                 "partida_cod": "29"}, **kw)


def test_f072_payload_franquicia_manda_la_marca_de_entrada():
    assert fq.payload_franquicia(_datos(partida_metodo="var"))[
        "partida_metodo"] == "var"
    assert fq.payload_franquicia(_datos(partida_metodo="postventa"))[
        "partida_metodo"] == "postventa"
    for otra in (None, "parte", "manual"):
        assert "partida_metodo" not in fq.payload_franquicia(
            _datos(partida_metodo=otra))


def test_f072_con_metodo_base_recupera_la_marca_de_la_linea():
    lineas = [_l(1, fecha=20261001, metodo="var"),
              _l(2, obra=10, cod="0100", partida=33, metodo="parte"),
              _l(3, partida=91013, pcod="030", metodo="var")]
    assert fq.con_metodo_base(_datos(), lineas)["partida_metodo"] == "var"
    # Otra partida, otra obra u otro recurso no cuentan.
    otra = [_l(3, partida=91013), _l(4, obra=9001, cod="POSTV2"),
            dict(_l(5), recurso_ide=999)]
    assert "partida_metodo" not in fq.con_metodo_base(_datos(), otra)
    # Sin marca de entrada en la base, nada.
    assert "partida_metodo" not in fq.con_metodo_base(
        _datos(), [_l(1, metodo="sin")])
    # Sin partida en la fila, nada.
    assert "partida_metodo" not in fq.con_metodo_base(
        _datos(partida_ide=None), [_l(1)])


def test_f072_repositorio_da_el_metodo_de_cada_linea(fabrica):
    [rid] = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="d-var",
                          fecha="2026-10-15", obra_ide=9101,
                          obra_codigo="VAR")
    _marcar(fabrica, rid, partida_ide=91012, partida_cod="29",
            partida_match_method="var")
    [x] = _repo(fabrica).lineas_trabajador_periodo(REC, 20260916, 20261015)
    assert (x["partida_ide"], x["partida_metodo"]) == (91012, "var")


def _sembrar_entrada(fabrica, metodo="var"):
    ids = sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 2.0,
                                                   "tipo": "extra"}],
                        document_id="d15-var", fecha="2026-10-15",
                        obra_ide=9101, obra_codigo="VAR")
    for rid in ids:
        _marcar(fabrica, rid, partida_ide=91012, partida_cod="29",
                partida_match_method=metodo)
    return ids


@pytest.mark.parametrize("metodo, esperado", [("var", "var"), ("sin", None)])
def test_f072_aplicar_franquicia_manda_la_marca_de_la_base(
        fabrica, portal, entorno, metodo, esperado):
    entorno.setenv("VAR_OBRA_COD", "VAR")
    entorno.setenv("VAR_PARTIDA_DESDE", "29")
    _sembrar_entrada(fabrica, metodo)
    f = _repo(fabrica).decidir_ajuste(
        REC, "2026-10", "ajustar",
        {"fecha_int": 20261015, "obra_ide": 9101, "obra_codigo": "VAR",
         "partida_ide": 91012, "partida_cod": "29"}, actor="eva")
    cliente, sv5 = portal(sv5=Sv5Franq(ejecutar=dict(EJECUTAR_OK)))
    r = cliente.post(f"/api/franquicia/{f['id']}/aplicar")
    assert r.status_code == 200, r.text
    [p] = sv5.franq_ejecutadas
    assert p.get("partida_metodo") == esperado
    assert (p["obra"]["codigo"], p["partida_ide"]) == ("VAR", 91012)


# ------------------------------- reajuste -------------------------------- #

def test_f072_reparto_completa_la_extra_nueva_con_la_marca(fabrica):
    base, libre = sembrar_parte(fabrica, [{"horas": 8.0, "estado":
                                           "registrado"}, {"horas": 1.0}],
                                document_id="doc-var", obra_ide=9101,
                                obra_codigo="VAR")
    _marcar(fabrica, base, partida_ide=91012, partida_cod="29",
            partida_match_method="var")
    _reparto(fabrica, [
        _cambio(base, base, "ordinaria", 8.0, 5.5),
        _cambio(None, base, "extra", 0.0, 2.5, obra_ide=9101,
                obra_codigo="VAR",
                hora_ext={"ide": 9, "cod": "HE01", "desc": "x", "ext": 1})],
        [base, libre])
    (f,) = _repo(fabrica).repartos_de_registros([libre])
    assert f["cambios"][1]["partida_metodo"] == "var"
    [nueva] = [x for x in payload_reajuste(f, {})["lineas"]
               if x.get("base_registro_id")]
    assert (nueva["partida_ide"], nueva["partida_metodo"]) == (91012, "var")


def test_f072_reparto_sin_marca_de_entrada_el_payload_de_siempre(fabrica):
    base, libre = sembrar_parte(fabrica, [{"horas": 8.0, "estado":
                                           "registrado"}, {"horas": 1.0}],
                                document_id="doc-n", obra_ide=678,
                                obra_codigo="0678")
    _marcar(fabrica, base, partida_ide=33, partida_cod="P-33",
            partida_match_method="parte")
    _reparto(fabrica, [_cambio(None, base, "extra", 0.0, 2.5,
                               hora_ext={"ide": 9, "cod": "HE01"})],
             [base, libre])
    (f,) = _repo(fabrica).repartos_de_registros([libre])
    assert "partida_metodo" not in f["cambios"][0]
    [nueva] = payload_reajuste(f, {})["lineas"]
    assert "partida_metodo" not in nueva


def test_f072_orm_sin_columna_nueva():
    """DA5: la marca vive en `partida_match_method`; no hay columna nueva."""
    assert "partida_metodo" not in ParteRegistroOrm.__table__.columns
