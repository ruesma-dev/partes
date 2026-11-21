# tests/test_f072_conciliacion.py
"""F-072 · Conciliación de partidas, clones y jornada con entradas (R20-R22).

- R20: la conciliación no toca las líneas con marca de entrada (como las
  `manual`), y las líneas SIN marca de una obra agrupada quedan en `sin`,
  sin casado por categoría ni por partida leída (ni se lee su presupuesto).
- R21: la extra que sv3 crea (`_campos_extra`) clona partida y marca.
- R22: la unidad del reparto F-045 es la obra de Sigrid: dos entradas de
  una obra agrupada pesan como una obra.

Sin red ni BBDD real: dobles en memoria y el ORM sobre SQLite.
"""
from __future__ import annotations

from application.services.partida_conciliador import PartidaConciliador
from application.services.reparto_ponderado import LineaDia, repartir_dia
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests import f072_comun as c
from tests.dobles import FabricaSesionSqlite


class RepoPartidas:
    def __init__(self, registros):
        self.registros = registros
        self.updates: list[dict] = []

    def fetch_registros_para_partida(self):
        return list(self.registros)

    def apply_partida_matches(self, updates):
        self.updates.extend(updates)
        return len(updates)


class LookupPartidas:
    def __init__(self):
        self.llamadas: list[int] = []

    def fetch_partidas_obra(self, obra_ide):
        self.llamadas.append(obra_ide)
        return c.PRESUPUESTOS.get(obra_ide, [])


def _reg(rid, obra_ide, obra_codigo, metodo=None, leida=None):
    return {"registro_id": rid, "obra_ide": obra_ide, "obra_codigo": obra_codigo,
            "categoria": "PEON", "nombre": "ANA UNO",
            "partida_match_method": metodo, "partida_leida": leida}


def _conciliar(registros, ajustes=c.AJUSTES):
    repo, lookup = RepoPartidas(registros), LookupPartidas()
    PartidaConciliador(repository=repo, lookup=lookup,
                       ajustes=ajustes).conciliar_todos()
    return {u["registro_id"]: u for u in repo.updates}, lookup


# ---------------------------------- R20 --------------------------------- #

def test_f072_r20_la_marca_de_entrada_no_se_toca():
    updates, lookup = _conciliar([_reg(1, 9101, "VAR", "var"),
                                  _reg(2, 9001, "POSTV2", "postventa"),
                                  _reg(3, 9101, "VAR", "manual")])
    assert updates == {} and lookup.llamadas == []


def test_f072_r20_sin_marca_en_obra_agrupada_queda_en_sin():
    updates, lookup = _conciliar([_reg(1, 9101, "VAR", None, leida="29"),
                                  _reg(2, 9001, "postv2", "parte"),
                                  _reg(3, 9128, " VAR ", "sin")])
    assert {r: u["partida_match_method"] for r, u in updates.items()} == {
        1: "sin", 2: "sin", 3: "sin"}
    assert all(u["partida_ide"] is None for u in updates.values())
    assert lookup.llamadas == []


def test_f072_r20_las_obras_normales_como_siempre():
    """La obra POSTV antigua (no agrupada) se concilia como cualquier obra."""
    updates, lookup = _conciliar([_reg(1, 9201, "POSTV", None, leida="0578B")])
    assert lookup.llamadas == [9201]
    assert updates[1]["partida_match_method"] == "sin"


def test_f072_r3_apagado_la_obra_var_se_concilia_como_siempre():
    updates, lookup = _conciliar([_reg(1, 9101, "VAR", None, leida="29")],
                                 ajustes=c.APAGADO)
    assert lookup.llamadas == [9101]
    assert updates[1]["partida_match_method"] == "parte"
    assert updates[1]["partida_ide"] == 91012


def test_f072_r20_sin_ajustes_es_como_antes_de_f072():
    repo, lookup = RepoPartidas([_reg(1, 9101, "VAR", None, leida="29")]), \
        LookupPartidas()
    PartidaConciliador(repository=repo, lookup=lookup).conciliar_todos()
    assert repo.updates[0]["partida_match_method"] == "parte"


def test_f072_r20_el_repositorio_devuelve_el_codigo_de_obra():
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)   # type: ignore[arg-type]
    pipe = c.pipeline()
    p = c.parte("V-29")
    pipe._match(p)
    repo.save_parte(document_id="d1", parte=p, meta={}, context={},
                    raw_extraction_json="{}", raw_context_json="{}",
                    review_required=False)
    filas = repo.fetch_registros_para_partida()
    assert [(f["obra_ide"], f["obra_codigo"], f["partida_match_method"])
            for f in filas] == [(9101, "VAR", "var")]


# ---------------------------------- R21 --------------------------------- #

def test_f072_r21_la_extra_automatica_clona_partida_y_marca():
    normal = ParteRegistroOrm(
        document_id="d", line_index=0, obra_ide=9101, obra_codigo="VAR",
        partida="29", partida_ide=91012, partida_cod="29",
        partida_res="VARIOS 29", partida_capitulo="CD",
        partida_match_method="var", partida_match_score=1.0)
    s = {"extra_horas": 2.0, "hora_ext_ide": 2, "hora_ext_cod": "HE01",
         "hora_ext_desc": "Hora extra", "hora_ext_ext": 1, "hora_candef": 8.0}
    campos = SqlAlchemyParteRepository._campos_extra(normal, s)
    assert {k: campos[k] for k in (
        "obra_ide", "partida", "partida_ide", "partida_cod", "partida_res",
        "partida_capitulo", "partida_match_method", "partida_match_score")} == {
        "obra_ide": 9101, "partida": "29", "partida_ide": 91012,
        "partida_cod": "29", "partida_res": "VARIOS 29",
        "partida_capitulo": "CD", "partida_match_method": "var",
        "partida_match_score": 1.0}


# ---------------------------------- R22 --------------------------------- #

def test_f072_r22_dos_entradas_de_una_obra_agrupada_son_una_obra():
    """6 h en VAR-29 y 6 h en VAR-30 (misma obra VAR) con jornada de 8: una
    sola obra en el reparto; la jornada cuadra como en cualquier obra."""
    lineas = [LineaDia(registro_id=1, obra_ide=9101, tipo="ordinaria", horas=6),
              LineaDia(registro_id=2, obra_ide=9101, tipo="ordinaria", horas=6)]
    res = repartir_dia(lineas, 8.0)
    assert res.cuadra and res.n_obras == 1
    assert sum(a.horas_norm for a in res.ajustes) == 8.0
    assert sum(a.extra_horas for a in res.ajustes) == 4.0
