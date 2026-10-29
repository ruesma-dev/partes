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


# ------------- T9, T23: el campo EXTENDIDO de franquicia (DA29-DA31) ------------- #
# `defext` tip 33 / `conext.valn` (design §2 H7, H8). Codigos y valores
# INVENTADOS salvo el `cod` `10`, que es el del ajuste real.

SQL_DEFINICION = (
    "SELECT defext.ide AS ide, defext.camtip AS camtip FROM defext "
    "WHERE defext.tip = 33 AND defext.cod = ?")

SQL_VALORES = (
    "SELECT con.ide AS reside, conext.ide AS extide, conext.valn AS valor "
    "FROM con LEFT JOIN conext ON conext.conide = con.ide AND conext.cod = ? "
    "WHERE con.tip = 33 AND con.ide IN ({})")


def test_f056_r39_definicion_campo_ext_sql_y_parametros(monkeypatch):
    """R39, R47: la definicion, SOLO de tip 33 y con el `cod` como
    PARAMETRO (nunca interpolado)."""
    api = ApiFalsa(["ide", "camtip"], [[49, 1]])
    assert _cli(monkeypatch, api).definicion_campo_ext("10") == [
        {"ide": 49, "camtip": 1}]
    assert len(api.posts) == 1
    url, cuerpo = api.posts[0]
    assert url == "http://sigrid.invalid/api/sql/read"
    assert _sql(cuerpo["sql"]) == SQL_DEFINICION
    assert cuerpo["parameters"] == ["10"]
    assert "'10'" not in cuerpo["sql"]


def test_f056_r38_definicion_campo_ext_devuelve_todas_las_filas(monkeypatch):
    """R38: 0 o varias filas las juzga `motivo_definicion`, no el cliente."""
    api = ApiFalsa(["ide", "camtip"], [])
    assert _cli(monkeypatch, api).definicion_campo_ext("10") == []
    api = ApiFalsa(["ide", "camtip"], [[49, 1], [50, 6]])
    assert _cli(monkeypatch, api).definicion_campo_ext("10") == [
        {"ide": 49, "camtip": 1}, {"ide": 50, "camtip": 6}]


@pytest.mark.parametrize("api", [
    ApiFalsa(["ide", "camtip"], [[49, 1]], truncated=True),
    ApiFalsa(["ide", "camtip"], [], estado=503)])
def test_f056_r39_definicion_campo_ext_fallo_es_excepcion(monkeypatch, api):
    with pytest.raises(RuntimeError):
        _cli(monkeypatch, api).definicion_campo_ext("10")


def test_f056_r47_r48_valores_campo_ext_sql_y_parametros(monkeypatch):
    """R47: solo `con` de tip 33 y `conext` con ese `cod`; R48: por
    `res.ide` (`con.ide`), nunca por DNI. `reside` -> lista de `valn` de
    sus filas CON `extide`; un recurso sin fila sale con []."""
    api = ApiFalsa(["reside", "extide", "valor"], [
        [501, 7001, 8], [502, None, None], [503, 7003, None]])
    cli = _cli(monkeypatch, api)
    assert cli.valores_campo_ext([503, 502, 501, 501, 0], "10") == {
        501: [8], 502: [], 503: [None]}
    assert len(api.posts) == 1
    _, cuerpo = api.posts[0]
    assert _sql(cuerpo["sql"]) == SQL_VALORES.format("?,?,?")
    assert cuerpo["parameters"] == ["10", 501, 502, 503]
    sql = cuerpo["sql"].lower()
    assert "dni" not in sql and "cif" not in sql and "tip = 42" not in sql


def test_f056_r2_valores_campo_ext_varias_filas_de_un_recurso(monkeypatch):
    """R2: dos filas del mismo recurso salen las dos (las juzga
    `lectura_de`: `invalida`)."""
    api = ApiFalsa(["reside", "extide", "valor"], [
        [501, 7001, 8], [501, 7002, 20]])
    assert _cli(monkeypatch, api).valores_campo_ext([501], "10") == {
        501: [8, 20]}


def test_f056_r40_valores_campo_ext_en_lotes(monkeypatch):
    ides = list(range(1, modulo.LOTE_RECURSOS + 3))
    api = ApiFalsa(["reside", "extide", "valor"], [])
    _cli(monkeypatch, api).valores_campo_ext(ides, "10")
    assert [len(c["parameters"]) for _, c in api.posts] == [
        modulo.LOTE_RECURSOS + 1, 3]
    assert [c["parameters"][0] for _, c in api.posts] == ["10", "10"]
    assert api.posts[1][1]["parameters"][1:] == [modulo.LOTE_RECURSOS + 1,
                                                 modulo.LOTE_RECURSOS + 2]


def test_f056_r39_valores_campo_ext_sin_recursos_no_lee(monkeypatch):
    api = ApiFalsa(["reside", "extide", "valor"], [])
    assert _cli(monkeypatch, api).valores_campo_ext([], "10") == {}
    assert _cli(monkeypatch, api).valores_campo_ext([0, None], "10") == {}
    assert api.posts == []


def test_f056_r39_valores_campo_ext_truncated_es_excepcion(monkeypatch):
    api = ApiFalsa(["reside", "extide", "valor"], [[501, 7001, 8]],
                   truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cli(monkeypatch, api).valores_campo_ext([501], "10")


def test_f056_t23_el_cliente_ya_no_lee_columnas_de_res():
    """DA29: lo hecho para una columna de `res` se quita (design §4)."""
    for nombre in ("tipo_columna_res", "valores_campo_res"):
        assert not hasattr(SigridWriteClient, nombre), nombre
        assert not hasattr(SigridFake, nombre), nombre


# ------------------------ T9, T23: el doble del campo ------------------------ #

def test_f056_doble_definicion_campo_ext():
    """Solo tip 33 y ese `cod`: el `cod` `10` de tip 42 no cuenta (R47)."""
    cli = _fake([])
    assert cli.definicion_campo_ext("10") == []
    cli.defext = [{"ide": 26, "tip": 42, "cod": "10", "camtip": 6},
                  {"ide": 49, "tip": 33, "cod": "10", "camtip": 1},
                  {"ide": 51, "tip": 33, "cod": "11", "camtip": 1}]
    assert cli.definicion_campo_ext("10") == [{"ide": 49, "camtip": 1}]
    assert cli.definiciones_leidas == ["10", "10"]
    cli.fallo_definicion = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        cli.definicion_campo_ext("10")


def test_f056_doble_valores_campo_ext():
    """Como el cliente real: solo `con` de tip 33 (un ide de tip 42 no
    sale), filas de ese `cod`, recurso sin fila => []."""
    cli = _fake([])
    cli.con_tipos = {501: 33, 502: 33, 503: 33, 900: 42}
    cli.conext = [
        {"ide": 1, "conide": 501, "cod": "10", "valn": 8},
        {"ide": 2, "conide": 503, "cod": "10", "valn": None},
        {"ide": 3, "conide": 502, "cod": "11", "valn": 5},
        {"ide": 4, "conide": 900, "cod": "10", "valn": 99}]
    assert cli.valores_campo_ext([502, 501, 503, 900, 999], "10") == {
        501: [8], 502: [], 503: [None]}
    assert cli.valores_leidos == [([501, 502, 503, 900, 999], "10")]
    cli.fallo_valores = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        cli.valores_campo_ext([501], "10")


def test_f056_doble_poner_franquicia():
    """El atajo de los tests: recurso de tip 33 con una fila del `cod`."""
    cli = _fake([])
    cli.poner_franquicia(501, 8, cod="10")
    cli.poner_franquicia(502, None, cod="10")
    cli.poner_franquicia(503, cod="10")              # sin fila
    assert cli.valores_campo_ext([501, 502, 503], "10") == {
        501: [8], 502: [None], 503: []}
