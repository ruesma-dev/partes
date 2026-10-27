# tests/test_f056_cliente.py
"""F-056 · Lo nuevo de `SigridWriteClient` para la franquicia (T4) y su
doble en `tests/dobles.py`.

  - `synckey_franquicia(id)`: `partes:franquicia:<id>` (R31, DA14);
  - `extras_del_periodo` (R23, DA3): UNA lectura agregada a `sql/read`
    con el SQL y los parametros exactos; `truncated` es una excepcion;
  - el doble: la misma suma sobre sus filas y la op `actualizar` de
    `stmt_actualizar_linea` en `escribir` (a 0 sin borrar).

Ni una llamada real: `httpx.post` se sustituye. Datos SINTETICOS.
"""
from __future__ import annotations

import httpx
import pytest

from domain.models.registro_models import PREFIJO_FRANQUICIA, HoraRecurso
from infrastructure.sigrid import sigrid_write_client as modulo
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
    synckey_franquicia,
)
from tests.dobles import SigridFake


class ApiFalsa:
    def __init__(self, columnas, filas, *, truncated=False, estado=200):
        self.columnas, self.filas = columnas, filas
        self.truncated, self.estado = truncated, estado
        self.posts: list[tuple[str, dict]] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.posts.append((url, json))
        return httpx.Response(self.estado, json={
            "ok": True, "columns": self.columnas, "rows": self.filas,
            "truncated": self.truncated})


def _cli(monkeypatch, api) -> SigridWriteClient:
    monkeypatch.setattr(modulo.httpx, "post", api)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


# ------------------------------ synckey ------------------------------ #

@pytest.mark.parametrize("ajuste_id, esperado", [
    (5, "partes:franquicia:5"), ("990560001", "partes:franquicia:990560001")])
def test_f056_r31_synckey_franquicia(ajuste_id, esperado):
    assert synckey_franquicia(ajuste_id) == esperado
    assert SigridWriteClient.synckey_franquicia(ajuste_id) == esperado
    assert esperado.startswith(PREFIJO_FRANQUICIA)


def test_f056_r31_synckey_franquicia_no_admite_no_enteros():
    with pytest.raises(ValueError):
        synckey_franquicia("x")


# -------------------------- extras_del_periodo -------------------------- #

SQL_EXTRAS = (
    "SELECT ISNULL(SUM(h.can), 0) AS extras FROM hmores h "
    "JOIN auxhor a ON a.ide = h.horide WHERE h.reside = ? "
    "AND h.fec BETWEEN ? AND ? AND a.cod LIKE 'HE%' "
    "AND ISNULL(h.synckey, '') <> ?")


def test_f056_r23_extras_del_periodo_sql_y_parametros(monkeypatch):
    api = ApiFalsa(["extras"], [[6.5]])
    e = _cli(monkeypatch, api).extras_del_periodo(
        501, 20260916, 20261015, "partes:franquicia:5")
    assert e == 6.5 and isinstance(e, float)
    assert len(api.posts) == 1
    url, cuerpo = api.posts[0]
    assert url == "http://sigrid.invalid/api/sql/read"
    assert _sql(cuerpo["sql"]) == SQL_EXTRAS
    assert cuerpo["parameters"] == [501, 20260916, 20261015,
                                    "partes:franquicia:5"]
    assert cuerpo["database"] == "bd"
    assert "DELETE" not in cuerpo["sql"].upper()


@pytest.mark.parametrize("filas", [[[None]], [], [[0]]])
def test_f056_r23_extras_del_periodo_sin_extras_es_cero(monkeypatch, filas):
    api = ApiFalsa(["extras"], filas)
    assert _cli(monkeypatch, api).extras_del_periodo(
        1, 20260916, 20261015, "partes:franquicia:1") == 0.0


def test_f056_r23_extras_del_periodo_negativo(monkeypatch):
    """DA3: la suma es NETA (ajustes manuales negativos incluidos)."""
    api = ApiFalsa(["extras"], [[-3.25]])
    assert _cli(monkeypatch, api).extras_del_periodo(
        1, 20260916, 20261015, "partes:franquicia:1") == -3.25


def test_f056_r23_extras_del_periodo_truncated_es_excepcion(monkeypatch):
    api = ApiFalsa(["extras"], [[6.0]], truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cli(monkeypatch, api).extras_del_periodo(
            1, 20260916, 20261015, "partes:franquicia:1")


def test_f056_r23_extras_del_periodo_http_error_es_excepcion(monkeypatch):
    api = ApiFalsa(["extras"], [], estado=500)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        _cli(monkeypatch, api).extras_del_periodo(
            1, 20260916, 20261015, "partes:franquicia:1")


# ------------------------------- el doble ------------------------------- #

HL, HE, HE2 = 1, 2, 3


def _fila(ide, *, reside=501, fec=20261001, horide=HE, can=3.0,
          synckey=None, hmoide=900) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can, "pre": 25.0,
            "tot": None, "pos": 64, "synckey": synckey, "caaide": 0,
            "tex": "", "enlazada": False}


def _fake(lineas) -> SigridFake:
    return SigridFake(
        horas={501: [HoraRecurso(HL, "HL01", None, 15.0, defecto=True),
                     HoraRecurso(HE, "HE01", None, 25.0)],
               502: [HoraRecurso(HE2, "he07", None, 30.0)]},
        partes=[{"ide": 900, "obride": 10, "ano": 2026, "mes": 10,
                 "cod": "PT26/00001", "emp": 1, "est": 1}],
        lineas=lineas)


def test_f056_doble_extras_del_periodo_como_el_sql():
    cli = _fake([
        _fila(1, can=3.0),                                   # cuenta
        _fila(2, can=-1.5, synckey="manual-adm"),            # cuenta (neta)
        _fila(3, can=4.0, horide=HL),                        # no es HE
        _fila(4, can=5.0, reside=502, horide=HE2),           # otro recurso
        _fila(5, can=7.0, fec=20260915),                     # fuera
        _fila(6, can=2.0, fec=20260916),                     # borde inicio
        _fila(7, can=1.0, fec=20261015),                     # borde fin
        _fila(8, can=-8.0, synckey="partes:franquicia:5"),   # el ajuste
        _fila(9, can=None),                                  # nula
    ])
    assert cli.extras_del_periodo(501, 20260916, 20261015,
                                  "partes:franquicia:5") == 4.5
    assert cli.extras_leidas == [(501, 20260916, 20261015,
                                  "partes:franquicia:5")]


def test_f056_doble_extras_del_periodo_codigo_en_minusculas():
    """`LIKE 'HE%'` con la collation de Sigrid no distingue mayusculas."""
    cli = _fake([_fila(1, reside=502, horide=HE2, can=2.0)])
    assert cli.extras_del_periodo(502, 20260916, 20261015, "x") == 2.0


def test_f056_doble_extras_del_periodo_fallo():
    cli = _fake([])
    cli.fallo_extras = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        cli.extras_del_periodo(501, 20260916, 20261015, "x")


def test_f056_doble_actualizar_pone_can_y_tot_sin_borrar():
    cli = _fake([_fila(8, can=-6.0, synckey="partes:franquicia:5")])
    st = cli.stmt_actualizar_linea(ide=8, synckey="partes:franquicia:5",
                                   antes=-6.0, despues=0.0, est_registro=1)
    assert cli.escribir([st]) == 1
    assert len(cli.lineas) == 1
    assert (cli.lineas[0]["can"], cli.lineas[0]["tot"]) == (0.0, 0.0)


def test_f056_doble_actualizar_optimista_y_con_guarda():
    """El `WHERE` de `stmt_actualizar_linea`: synckey, `can` leido, parte
    En registro y sin enlaces; si no, 0 filas."""
    cli = _fake([_fila(8, can=-6.0, synckey="partes:franquicia:5")])
    mal_can = cli.stmt_actualizar_linea(
        ide=8, synckey="partes:franquicia:5", antes=-5.0, despues=-8.0,
        est_registro=1)
    mala_sk = cli.stmt_actualizar_linea(
        ide=8, synckey="partes:franquicia:6", antes=-6.0, despues=-8.0,
        est_registro=1)
    assert cli.escribir([mal_can, mala_sk]) == 0
    cli.lineas[0]["enlazada"] = True
    bien = cli.stmt_actualizar_linea(
        ide=8, synckey="partes:franquicia:5", antes=-6.0, despues=-8.0,
        est_registro=1)
    assert cli.escribir([bien]) == 0
    cli.lineas[0]["enlazada"] = False
    cli.partes[0]["est"] = 3
    assert cli.escribir([bien]) == 0
    cli.partes[0]["est"] = 1
    assert cli.escribir([bien]) == 1
    assert (cli.lineas[0]["can"], cli.lineas[0]["tot"]) == (-8.0, -200.0)


def test_f056_doble_lineas_para_reajuste_trae_pre_hmoide_y_enlace():
    cli = _fake([_fila(8, can=-6.0, synckey="partes:franquicia:5")])
    cli.lineas[0]["enlazada"] = True
    ls = cli.lineas_para_reajuste(["partes:franquicia:5", "partes:1"])
    assert list(ls) == ["partes:franquicia:5"]
    l8 = ls["partes:franquicia:5"]
    assert (l8.ide, l8.can, l8.pre, l8.hmoide, l8.enlazada) == (
        8, -6.0, 25.0, 900, True)
