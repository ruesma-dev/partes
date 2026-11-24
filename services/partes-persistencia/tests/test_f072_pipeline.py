# tests/test_f072_pipeline.py
"""F-072 · El casado de la ingesta con obras agrupadas y su guardado
(R14-R19, R42, R43; R3 con todo apagado).

`PersistPartePipeline._match` lee la forma SOLO de `obra_numero_leido` (R43):
lo que es exactamente una marca es forma base (R42, la antigua `POSTV`); si
la clave de lo leído es el código de una obra real no agrupada, gana esa obra
con un WARNING `marca_colisiona` (R42, `150702-V`); si no, `leer_forma`. Con
entrada, `save_parte` escribe la partida y la marca en cada línea.

Sin red: Sigrid en memoria (`f072_comun`); el guardado, sobre SQLite.
"""
from __future__ import annotations

import logging

import pytest

from application.pipelines.persist_parte_pipeline import PersistParteRequest
from domain.models.parte_records import EntradaPartida, ObraMatch
from infrastructure.database.orm_models import ParteDocumentOrm, ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests import f072_comun as c
from tests.dobles import FabricaSesionSqlite

LOGGER = "application.pipelines.persist_parte_pipeline"


def _casar(p, **kw):
    pipe = c.pipeline(**kw)
    pipe._match(p)
    p.review = pipe._compute_review_required(p)   # type: ignore[attr-defined]
    return p


def _obra(p):
    return (p.obra.ide, p.obra.method)


# ------------------------------ con entrada ------------------------------ #

@pytest.mark.parametrize("leido", ["V-29", "v29", "29 V", "VAR 29", "V.29"])
def test_f072_r14_var_con_entrada(leido):
    p = _casar(c.parte(leido))
    assert _obra(p) == (9101, "var")
    assert p.entrada == EntradaPartida(ide=91012, cod="29", res="VARIOS 29",
                                       capitulo="CD", tipo="var")
    assert (p.empresa, p.review) == (1, False)


@pytest.mark.parametrize("leido", ["POST 578", "post-578", "578/POST",
                                   "Postventá 578", "POSTVENTA 0578",
                                   "POSTV2 578"])
def test_f072_r15_postventa_con_entrada(leido):
    p = _casar(c.parte(leido))
    assert _obra(p) == (9001, "postventa")
    assert (p.entrada.ide, p.entrada.cod, p.entrada.tipo) == (
        90011, "0578B", "postventa")
    assert p.review is False


def test_f072_r16_forma_base_con_la_partida_leida():
    p = _casar(c.parte("VAR", partidas=["29"]))
    assert _obra(p) == (9101, "var") and p.entrada.ide == 91012


# ------------------------------ sin entrada ------------------------------ #

@pytest.mark.parametrize("leido, motivo", [
    ("V-31", "var_fuera_universo"), ("POST 999", "postventa_obra_no_casa"),
    ("VAR", "agrupada_sin_entrada"), ("POSTV2", "agrupada_sin_entrada"),
])
def test_f072_r17_sin_entrada_sin_obra_y_a_revision(leido, motivo, caplog):
    p = _casar(c.parte(leido))
    assert _obra(p) == (None, motivo)
    assert p.entrada is None
    assert p.review is True


def test_f072_r17_sin_entrada_la_empresa_es_la_del_membrete():
    p = _casar(c.parte("V-31", membrete="RUESMA"))
    assert (p.empresa, p.empresa_origen) == (1, "membrete")


# ------------------------------- sin forma ------------------------------- #

def test_f072_sin_forma_el_casado_de_siempre():
    p = _casar(c.parte("100"))
    assert _obra(p) == (100, "codigo_padded") and p.entrada is None


@pytest.mark.parametrize("ajustes, entradas", [(c.APAGADO, True),
                                               (c.AJUSTES, False)])
def test_f072_r3_apagado_una_marca_se_casa_como_siempre(ajustes, entradas):
    p = _casar(c.parte("V-29"), ajustes=ajustes, entradas=entradas)
    assert p.obra.ide is None and p.obra.method not in (
        "var", "var_fuera_universo") and p.entrada is None
    p = _casar(c.parte("VAR"), ajustes=ajustes, entradas=entradas)
    assert _obra(p) == (9101, "codigo_trabajadores") and p.entrada is None


# --------------------------------- R18 ----------------------------------- #

def test_f072_r18_casado_normal_a_una_obra_agrupada_es_forma_base():
    """Sin número y por el nombre «OBRAS VARIAS»: daría la VAR; sin partida
    leída no hay entrada y va a revisión."""
    p = _casar(c.parte(None, nombre_obra="OBRAS VARIAS", membrete="RUESMA"))
    assert _obra(p) == (None, "agrupada_sin_entrada")
    p = _casar(c.parte(None, nombre_obra="OBRAS VARIAS", membrete="RUESMA",
                       partidas=["29"]))
    assert _obra(p) == (9101, "var") and p.entrada.ide == 91012


# --------------------------------- R42 ----------------------------------- #

def test_f072_r42_un_codigo_real_gana_con_warning(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        p = _casar(c.parte("150702-V"))
    assert _obra(p) == (7001, "codigo") and p.entrada is None
    avisos = [r.getMessage() for r in caplog.records if r.name == LOGGER]
    assert any("marca_colisiona" in m for m in avisos), avisos


def test_f072_r42_lo_que_es_exactamente_una_marca_es_forma_base():
    """`POSTV` es alias de postventa: forma base aunque exista la obra
    antigua `POSTV` (DA13)."""
    p = _casar(c.parte("POSTV"))
    assert _obra(p) == (None, "agrupada_sin_entrada")
    p = _casar(c.parte("POSTV", partidas=["578"]))
    assert _obra(p) == (9001, "postventa") and p.entrada.ide == 90011


def test_f072_r42_sin_marca_no_avisa(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        _casar(c.parte("100"))
    assert not any("marca_colisiona" in r.getMessage() for r in caplog.records)


# --------------------------------- R43 ----------------------------------- #

def test_f072_r43_la_marca_solo_sale_del_numero_de_obra():
    """Una «VAR 29» en el nombre de la obra o una incidencia V no cuentan."""
    p = c.parte("100", nombre_obra="VAR 29")
    p.registros[0].es_incidencia = True
    p.registros[0].tipo_hora = "V"
    p.registros[0].incidencia.codigo = "V"
    p.registros[0].partida = "V 29"
    p = _casar(p)
    assert _obra(p) == (100, "codigo_padded") and p.entrada is None


# --------------------------------- R19 ----------------------------------- #

def test_f072_r19_fallo_de_lectura_no_persiste_y_sube(monkeypatch):
    repo = c.RepoF072()
    pipe = c.pipeline(c.LookupF072(error=RuntimeError("truncated")), repo=repo)
    monkeypatch.setattr(pipe._normalizer, "normalize",
                        lambda data, email_text=None: c.parte("V-29"))
    with pytest.raises(RuntimeError):
        pipe.run(PersistParteRequest(filename="p.pdf",
                                     mime_type="application/pdf",
                                     file_bytes=b"", extraction_envelope={},
                                     context={}))
    assert repo.guardados == []


# ------------------------------- guardado -------------------------------- #

def _guardar(fabrica, p, document_id):
    SqlAlchemyParteRepository(fabrica).save_parte(   # type: ignore[arg-type]
        document_id=document_id, parte=p, meta={}, context={},
        raw_extraction_json="{}", raw_context_json="{}", review_required=False)


def _lineas(fabrica, document_id):
    with fabrica.create_session() as s:
        return [(r.obra_ide, r.partida, r.partida_ide, r.partida_cod,
                 r.partida_res, r.partida_capitulo, r.partida_match_method,
                 r.partida_match_score)
                for r in s.query(ParteRegistroOrm).filter_by(
                    document_id=document_id).order_by(ParteRegistroOrm.id)]


def test_f072_r14_save_parte_escribe_la_entrada_en_cada_linea():
    fabrica = FabricaSesionSqlite()
    p = _casar(c.parte("VAR", ("ANA UNO", c.DNI_A), ("ANA UNO", c.DNI_A),
                       partidas=["29", None]))
    _guardar(fabrica, p, "doc-var")
    assert _lineas(fabrica, "doc-var") == [
        (9101, "29", 91012, "29", "VARIOS 29", "CD", "var", 1.0),
        (9101, None, 91012, "29", "VARIOS 29", "CD", "var", 1.0)]
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, "doc-var")
        assert (doc.obra_ide, doc.obra_codigo, doc.obra_match_method,
                doc.obra_numero_leido) == (9101, "VAR", "var", "VAR")


def test_f072_save_parte_sin_entrada_como_siempre():
    fabrica = FabricaSesionSqlite()
    p = _casar(c.parte("100", partidas=["03.09"]))
    _guardar(fabrica, p, "doc-n")
    assert _lineas(fabrica, "doc-n") == [
        (100, "03.09", None, None, None, None, None, None)]


def test_f072_save_parte_dos_entradas_del_mismo_dia_no_se_pisan():
    """Mismo día, misma obra agrupada y mismo trabajador, entradas distintas:
    son dos partes, no un reemplazo (la identidad incluye la entrada)."""
    fabrica = FabricaSesionSqlite()
    _guardar(fabrica, _casar(c.parte("V-29")), "doc-29")
    _guardar(fabrica, _casar(c.parte("V-30")), "doc-30")
    _guardar(fabrica, _casar(c.parte("V 29")), "doc-29b")
    with fabrica.create_session() as s:
        activos = {d.id for d in s.query(ParteDocumentOrm).filter_by(
            is_active=True)}
    assert activos == {"doc-30", "doc-29b"}


def test_f072_entrada_partida_del_dominio():
    e = EntradaPartida(ide=1, cod="29", res="X", capitulo="CD", tipo="var")
    assert e.tipo == "var" and ObraMatch().ide is None


# ------------------------------- cableado -------------------------------- #

def _settings(monkeypatch, **entorno):
    from config.settings import Settings

    for nombre in ("POSTVENTA_OBRA_COD", "POSTVENTA_ALIAS", "VAR_OBRA_COD",
                   "VAR_ALIAS", "VAR_PARTIDA_DESDE"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setenv("PG_PASSWORD", "x")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "x")
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None)


def test_f072_construir_entradas_encendido_con_sigrid(monkeypatch):
    from application.services.entrada_agrupada import ResolutorEntradas
    from interface_adapters.api.app import construir_entradas

    cliente = object()
    st = _settings(monkeypatch, VAR_OBRA_COD="VAR", VAR_PARTIDA_DESDE="29")
    res = construir_entradas(st, cliente)
    assert isinstance(res, ResolutorEntradas)
    assert res._lookup is cliente and res.ajustes.var_desde == 29


def test_f072_r3_construir_entradas_apagado_o_sin_sigrid(monkeypatch):
    from interface_adapters.api.app import construir_entradas

    assert construir_entradas(_settings(monkeypatch), object()) is None
    st = _settings(monkeypatch, POSTVENTA_OBRA_COD="POSTV2")
    assert construir_entradas(st, None) is None
