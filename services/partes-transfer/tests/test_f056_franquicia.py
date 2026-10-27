# tests/test_f056_franquicia.py
"""F-056 · Franquicia de extras en sv5: modelos de dominio (T1) y regla
pura del ajuste (T2, `application/services/franquicia.py`).

Datos SINTETICOS: recursos, partes e ides inventados; ni nombres ni DNIs.
"""
from __future__ import annotations

from dataclasses import fields

import pytest

from domain.models.registro_models import (
    PREFIJO_FRANQUICIA,
    ObraEntrada,
    PeticionFranquicia,
    ResultadoFranquicia,
    VeredictoFranquicia,
    es_synckey_franquicia,
)


# ------------------------------- T1: modelos ------------------------------- #

def test_f056_modelos_prefijo_literal():
    """R31, DA14: la synckey del ajuste es `partes:franquicia:<id>`."""
    assert PREFIJO_FRANQUICIA == "partes:franquicia:"


@pytest.mark.parametrize("sk, esperado", [
    ("partes:franquicia:1", True),
    ("partes:franquicia:990560001", True),
    ("  partes:franquicia:7  ", True),
    ("partes:7", False),
    ("partes:7:ciz", False),
    ("porcentajes:franquicia:7", False),
    ("PARTES:FRANQUICIA:7", False),
    ("partes:franquicia", False),
    ("", False),
    (None, False),
])
def test_f056_modelos_es_synckey_franquicia(sk, esperado):
    assert es_synckey_franquicia(sk) is esperado


def test_f056_modelos_peticion_campos_y_defectos():
    """design §6: los campos de `FranquiciaIn`, con la obra como
    `ObraEntrada` y `extras_pendientes` 0 por defecto."""
    p = PeticionFranquicia(
        ajuste_id=5, recurso_ide=501, franquicia=8.0, periodo="2026-10",
        inicio=20260916, fin=20261015, fecha_int=20261015,
        obra=ObraEntrada(ide=10, codigo="9999"), partida_ide=33,
        partida_cod="01.01")
    assert [f.name for f in fields(p)] == [
        "ajuste_id", "recurso_ide", "franquicia", "periodo", "inicio", "fin",
        "fecha_int", "obra", "partida_ide", "partida_cod",
        "extras_pendientes", "usuario"]
    assert p.extras_pendientes == 0.0
    assert p.usuario is None
    assert p.ano == 2026 and p.mes == 10


def test_f056_modelos_peticion_ano_mes_del_dia_de_ajuste():
    """El parte es el del mes NATURAL del dia de ajuste (H1)."""
    p = PeticionFranquicia(
        ajuste_id=1, recurso_ide=1, franquicia=1.0, periodo="2026-01",
        inicio=20251216, fin=20260115, fecha_int=20251231,
        obra=ObraEntrada(ide=1), partida_ide=None, partida_cod=None)
    assert (p.ano, p.mes) == (2025, 12)


def test_f056_modelos_veredicto():
    v = VeredictoFranquicia("no_editable", "motivo")
    assert (v.accion, v.motivo) == ("no_editable", "motivo")
    assert VeredictoFranquicia("crear").motivo is None


def test_f056_modelos_resultado_campos_y_defectos():
    """design §6: la respuesta, en este orden y con defectos neutros."""
    r = ResultadoFranquicia(ok=True, accion="crear")
    assert [f.name for f in fields(r)] == [
        "ok", "accion", "extras", "objetivo", "actual", "hmores_ide",
        "hmoide", "parte_cod", "parte_estado", "complementario",
        "hora_codigo", "pre", "motivo", "escrita", "forzada_pruebas",
        "error"]
    assert r.extras == 0.0 and r.objetivo == 0.0
    assert r.actual is None and r.hmores_ide is None and r.hmoide is None
    assert r.parte_cod is None and r.parte_estado is None
    assert r.complementario is False and r.escrita is False
    assert r.forzada_pruebas is False
    assert r.hora_codigo is None and r.pre is None
    assert r.motivo is None and r.error is None
