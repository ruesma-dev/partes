# tests/test_f031_cliente_partes.py
"""F-031 · R1, R15, R24: lecturas nuevas de `SigridWriteClient`.

  - R1: `partes_del_periodo` trae TODOS los partes de obra y mes con su
    estado (`con.est`), por `ide` descendente, en UNA consulta.
  - R24: `partidas_de_lineas` trae la cuenta de cada partida pedida en UNA
    consulta (un `?` por partida); sin partidas, no lee.
  - R15/R24: un `truncated` o un error HTTP es una excepcion.

Ni una llamada real: `httpx.post` se sustituye por un doble. Datos
SINTETICOS.
"""
from __future__ import annotations

import httpx
import pytest
from domain.models.registro_models import ParteSigrid, PartidaCuenta
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient


class SigridApiFalso:
    """sigrid-api en memoria: una lista de filas por lectura; apunta lo
    pedido. `estado` permite simular un error HTTP."""

    def __init__(self, columnas, *respuestas, truncated=False,
                 estado=200) -> None:
        self.columnas = columnas
        self.respuestas = list(respuestas)
        self.truncated = truncated
        self.estado = estado
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        filas = self.respuestas.pop(0) if self.respuestas else []
        return httpx.Response(self.estado, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kw) -> SigridWriteClient:
    monkeypatch.setattr(modulo.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd",
                             **kw)


def _sql(texto: str) -> str:
    return " ".join(texto.split())


# ========================= R1 · partes_del_periodo ========================= #

COLS_PARTES = ["IDE", "cod", "est"]


def test_f031_r1_partes_del_periodo_una_consulta_con_estado(
        monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTES, [
        [912, "PT26/00350", 1], [905, "PT26/00004", 10],
        [901, "PT26/00002", None]])
    partes = _cliente(monkeypatch, falso, tip_parte=35).partes_del_periodo(
        10, 2026, 1)
    assert partes == [ParteSigrid(912, "PT26/00350", 1),
                      ParteSigrid(905, "PT26/00004", 10),
                      ParteSigrid(901, "PT26/00002", None)]
    (lectura,) = falso.lecturas
    assert _sql(lectura["sql"]) == (
        "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo "
        "JOIN con ON con.ide = hmo.ide "
        "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
        "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
        "ORDER BY hmo.ide DESC")
    assert lectura["parameters"] == [10, 2026, 1, 35]
    assert lectura["database"] == "bd"


def test_f031_r1_partes_del_periodo_convierte_tipos(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTES, [["912", "PT26/00350", "3"]])
    (p,) = _cliente(monkeypatch, falso, tip_parte=7).partes_del_periodo(
        "10", "2026", "1")
    assert (p.ide, p.est) == (912, 3)
    assert isinstance(p.ide, int) and isinstance(p.est, int)
    assert falso.lecturas[0]["parameters"] == [10, 2026, 1, 7]


def test_f031_r1_periodo_sin_partes_lista_vacia(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTES, [])
    assert _cliente(monkeypatch, falso).partes_del_periodo(10, 2026, 1) == []


def test_f031_r15_partes_truncado_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTES, [[1, "PT26/00001", 1]],
                           truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(monkeypatch, falso).partes_del_periodo(10, 2026, 1)


def test_f031_r15_partes_error_http_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTES, [], estado=500)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        _cliente(monkeypatch, falso).partes_del_periodo(10, 2026, 1)


# ======================= R24 · partidas_de_lineas ======================= #

COLS_PARTIDAS = ["ide", "COD", "caacod"]


def test_f031_r24_partidas_una_consulta_un_marcador_por_partida(
        monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTIDAS, [
        [300, "01.02", "0100.CIMO12"], [301, " 02.01 ", " 0100.CDQA01 "],
        [304, "11.01", None], [305, "12.01", ""]])
    out = _cliente(monkeypatch, falso).partidas_de_lineas(
        [301, 300, 0, None, 300, 304, 305])
    assert out == {
        300: PartidaCuenta(300, "01.02", "0100.CIMO12"),
        301: PartidaCuenta(301, "02.01", "0100.CDQA01"),
        304: PartidaCuenta(304, "11.01", None),
        305: PartidaCuenta(305, "12.01", None),
    }
    (lectura,) = falso.lecturas
    assert _sql(lectura["sql"]) == (
        "SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod "
        "FROM obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide "
        "AND ISNULL(p.caaide, 0) <> 0 WHERE p.ide IN (?,?,?,?)")
    assert lectura["parameters"] == [300, 301, 304, 305]


def test_f031_r24_partida_sin_codigo(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTIDAS, [["300", None, None]])
    out = _cliente(monkeypatch, falso).partidas_de_lineas(["300"])
    assert out == {300: PartidaCuenta(300, None, None)}


@pytest.mark.parametrize("parides", [[], [0, None]])
def test_f031_r24_sin_partidas_no_lee(monkeypatch, parides) -> None:
    falso = SigridApiFalso(COLS_PARTIDAS, [])
    assert _cliente(monkeypatch, falso).partidas_de_lineas(parides) == {}
    assert falso.lecturas == []


def test_f031_r24_partidas_truncado_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTIDAS, [[300, "01.02", None]],
                           truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(monkeypatch, falso).partidas_de_lineas([300])


def test_f031_r24_partidas_error_http_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_PARTIDAS, [], estado=503)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        _cliente(monkeypatch, falso).partidas_de_lineas([300])
