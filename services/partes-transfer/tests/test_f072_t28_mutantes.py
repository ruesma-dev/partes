# tests/test_f072_t28_mutantes.py
"""F-072 · T28: tests que matan supervivientes de la campaña de mutación de
sv5 (`progress/mutacion_F-072.md`). Cada test nombra el superviviente.

Sin red: sigrid-api falso y datos FICTICIOS.
"""
from __future__ import annotations

import dataclasses

import httpx
import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_registro import motivo_partida_agrupada
from domain.models.registro_models import AccionLinea, LineaSigrid, PartidaHoja
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests import f072_comun as c


# ------------------ reglas_registro.py:134 (`donde`) ------------------ #

def test_t28_el_motivo_nombra_la_obra_solo_si_se_conoce():
    """`:134`: con `obra_cod`, « de la obra <cod>»; sin él, nada."""
    hojas = c.PRESUPUESTOS[c.VARO.ide]
    con = motivo_partida_agrupada(c.linea(1, 91012, None), hojas, "var", 29,
                                  obra_cod="VAR")
    sin = motivo_partida_agrupada(c.linea(1, 91012, None), hojas, "var", 29)
    assert con.endswith("la marca de una entrada de la obra VAR"), con
    assert "de la obra" not in sin, sin


# ------------------ reglas_registro.py:148 (`or 0`) ------------------ #

def test_t28_con_desde_0_la_partida_0_es_del_universo_var():
    """`:148`: `VAR_PARTIDA_DESDE=0` admite la partida de número 0 (R2)."""
    cero = PartidaHoja(ide=5, cod="0", res="CERO", es_hoja=True, activa=True)
    assert motivo_partida_agrupada(c.linea(1, 5, "var"), [cero], "var", 0,
                                   obra_cod="VAR") is None


# --------------- registro_pipeline.py:696 (por defecto) --------------- #

def test_t28_choques_sin_por_partida_no_mira_la_partida():
    """`:696`: por defecto (`por_partida=False`, como antes de F-072) una
    línea de otra partida también choca."""
    a = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=11,
                    fecha_int=c.FECHA, recurso_ide=501, hora_ide=c.HL,
                    paride=91012)
    ls = LineaSigrid(ide=1, reside=501, fecha_int=c.FECHA, horide=c.HL,
                     hora_codigo="HL01", can=8.0, tot=80.0, synckey=None,
                     nuestra=False, paride=91013)
    assert [x.ide for x in RegistroPipeline._choques([ls], a, set())] == [1]


# ------------- sigrid_write_client.py:505 (`paride` vacío) ------------- #

def test_t28_linea_sin_partida_en_sigrid_da_paride_none(monkeypatch):
    """`:505`: una fila con `paride` NULL es «sin partida» (`None`), no la
    partida 1."""
    def falso(url, headers=None, timeout=None, json=None):
        return httpx.Response(200, json={
            "ok": True, "truncated": False,
            "columns": ["ide", "reside", "fec", "horide", "hora", "can", "tot",
                        "synckey", "paride", "enlazada"],
            "rows": [[1, 501, c.FECHA, 1, "HL01", 8.0, 80.0, None, None, 0]]})
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="clave-de-test", database="bd")
    [ls] = cli.lineas_existentes(9, [501], [c.FECHA], con_partida=True)
    assert ls.paride is None


# ------------- registro_models.py:241 (`frozen=True`) ------------- #

def test_t28_la_partida_hoja_es_inmutable():
    h = PartidaHoja(ide=5, cod="29", res=None, es_hoja=True, activa=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        h.activa = False  # type: ignore[misc]
