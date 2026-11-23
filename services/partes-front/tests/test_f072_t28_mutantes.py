# tests/test_f072_t28_mutantes.py
"""F-072 · T28: tests que matan supervivientes de la campaña de mutación de
sv4 (`progress/mutacion_F-072.md`). Cada test nombra el superviviente.

Sin red ni BBDD real: Sigrid simulado y SQLite. Datos FICTICIOS.
"""
from __future__ import annotations

import dataclasses

import pytest
from fastapi.testclient import TestClient

from application.services import catalogo_entradas as ce
from application.services import franquicia as fq
from config.settings import Settings
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import ObraOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite
from tests.test_f072_catalogo_entradas import (
    OBRAS,
    Obras,
    SigridCon,
    _cat,
    _p,
)
from tests.test_f072_endpoints import LookupF072, entorno  # noqa: F401

# ------------------ catalogo_entradas.py:41 (`frozen`) ------------------ #


def test_t28_la_entrada_es_inmutable():
    """`:41`: las `Entrada` se comparten desde la caché del catálogo."""
    cat, _s = _cat()
    e = cat.entradas()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.nombre = "OTRO"  # type: ignore[misc]


# ------------- catalogo_entradas.py:97 (TTL por defecto, 600 s) ------------- #

def test_t28_el_catalogo_caduca_a_los_600_s_por_defecto(monkeypatch):
    """`:97`: el TTL por defecto es el del catálogo de obras (600 s): a los
    600 s justos se vuelve a leer."""
    reloj = [1000.0]
    monkeypatch.setattr(ce.time, "time", lambda: reloj[0])
    s = SigridCon({9101: [_p(91012, "29", "VARIOS 29")]})
    cat = ce.CatalogoEntradas(obra_catalog=Obras(), sigrid_client=s,
                              ajustes=_cat()[0]._ajustes)
    cat.entradas()
    n = len(s.lecturas)
    reloj[0] = 1599.0
    cat.entradas()
    assert len(s.lecturas) == n
    reloj[0] = 1600.0
    cat.entradas()
    assert len(s.lecturas) == 2 * n


# ------------- catalogo_entradas.py:154 (orden por tipo y empresa) ------------- #

def test_t28_las_entradas_salen_por_tipo_y_empresa():
    """`:154`: por tipo y, dentro, por empresa, venga como venga la lista de
    obras."""
    cat, _s = _cat(Obras(list(reversed(OBRAS))))
    orden = list(dict.fromkeys((e.tipo, e.empresa) for e in cat.entradas()))
    assert orden == [("postventa", 1), ("postventa", 28), ("var", 1),
                     ("var", 28)]


# ------------- catalogo_entradas.py:179 (rótulo de postventa) ------------- #

def test_t28_el_nombre_de_postventa_es_el_de_la_partida_o_el_de_la_obra():
    """`:179`: el rótulo de la partida y, si no tiene, el nombre de la obra
    X."""
    pres = {9001: [_p(90010, "CD", "COSTES DIRECTOS"),
                   _p(90011, "0578B", "ROTULO DE LA PARTIDA", 90010),
                   _p(90013, "0100", None, 90010)]}
    cat, _s = _cat(sigrid=SigridCon(pres))
    assert cat.entrada(9001, 90011).nombre == "ROTULO DE LA PARTIDA"
    assert cat.entrada(9001, 90013).nombre == "OBRA CIEN"


# ------------- franquicia.py:246 y :250 (`or 0` de la clave) ------------- #

def _linea(**kw):
    base = {"recurso_ide": 501, "obra_ide": 9101, "partida_ide": 1,
            "partida_metodo": "var"}
    base.update(kw)
    return base


def test_t28_con_metodo_base_sin_recurso_no_toma_la_marca_del_recurso_1():
    """`:246`: una fila sin recurso no es del recurso 1."""
    datos = {"recurso_ide": None, "obra_ide": 9101, "partida_ide": 1}
    out = fq.con_metodo_base(datos, [_linea(recurso_ide=1)])
    assert "partida_metodo" not in out
    assert fq.con_metodo_base(datos, [_linea(recurso_ide=None)])[
        "partida_metodo"] == "var"


def test_t28_con_metodo_base_una_linea_sin_partida_no_es_la_partida_1():
    """`:250`: una línea sin partida no es la partida 1."""
    datos = {"recurso_ide": 501, "obra_ide": 9101, "partida_ide": 1}
    assert "partida_metodo" not in fq.con_metodo_base(
        datos, [_linea(partida_ide=None)])


# ------------- app.py:4234, :4267 y :4268 (parte nuevo) ------------- #

_NUEVO = {"empleado_ide": 77, "empleado_nombre": "Pepe Perez",
          "empleado_dni": "12345678Z", "empleado_reside": "501",
          "dias": ["2026-11-17"], "horas_ordinaria": 8, "horas_extra": 0}


def _portal(entorno, lookup=LookupF072):  # noqa: F811
    fabrica = FabricaSesionSqlite()
    entorno.setattr(app_mod, "SigridLookupClient", lookup)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), fabrica


def _doc(fabrica):
    with fabrica.create_session() as s:
        [doc] = s.query(ParteDocumentOrm).filter_by(fecha="2026-11-17").all()
        return doc.obra_codigo, doc.obra_nombre


def test_t28_parte_nuevo_en_obra_normal_guarda_su_codigo_y_nombre(entorno):  # noqa: F811
    """`:4267` y `:4268`: fuera de una entrada, el código y el nombre de la
    obra son los del cuerpo."""
    cliente, fabrica = _portal(entorno)
    r = cliente.post("/api/partes/nuevo", json=dict(
        _NUEVO, obra_ide=10, obra_codigo="0100", obra_nombre="Obra Uno"))
    assert r.status_code == 200, r.text
    assert _doc(fabrica) == ("0100", "Obra Uno")


class LookupConObraCero(LookupF072):
    def fetch_obras(self) -> list:
        return super().fetch_obras() + [ObraOption(0, "VAR", "VAR CERO", 1)]


def test_t28_parte_nuevo_obra_ide_0_no_es_una_obra_del_catalogo(entorno):  # noqa: F811
    """`:4234`: `obra_ide` 0 es «sin obra», como en el casado de partida del
    mismo endpoint: no se busca en el catálogo y manda el código."""
    cliente, fabrica = _portal(entorno, LookupConObraCero)
    r = cliente.post("/api/partes/nuevo", json=dict(
        _NUEVO, obra_ide=0, obra_codigo="0100", obra_nombre="Obra Uno"))
    assert r.status_code == 200, r.text
    assert _doc(fabrica) == ("0100", "Obra Uno")
