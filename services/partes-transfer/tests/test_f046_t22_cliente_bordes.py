# tests/test_f046_t22_cliente_bordes.py
"""F-046 T22 · bordes del SQL del reajuste en `SigridWriteClient` que la
campana de mutacion dejo sin vigilar (`progress/mutacion_F-046.md`):

  - columnas NULL de Sigrid al leer (`reside`, `fec`, `horide`, `hmoide`,
    `obride`): 0 o None, nunca un ide inventado;
  - el INSERT de la extra: obra sin centro, partida 0 y `tot` a 2
    decimales;
  - `escribir_lote`: timeout del POST, confirmacion (`ok` Y `committed`)
    y lo que se recorta de los mensajes y del log.

Ni una llamada real: `httpx.post` se sustituye. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

import httpx
import pytest
from domain.models.registro_models import ObraEntrada
from tests.test_f046_cliente_reajuste import COLS_LINEAS, ApiFalsa, _cli


def _insertar(cli, obra, **kw):
    args = dict(hmoide=7001, obra=obra, reside=501, pos=64,
                fecha_int=20261014, horide=9, can=1.5, pre=10.0, paride=33,
                ano=2026, mes=10, synckey="partes:990000002", tex=None,
                caaide=0, base_ide=4001, base_synckey="partes:11",
                base_despues=6.5)
    args.update(kw)
    return cli.stmt_insertar_extra(**args)["parameters"]


def _obra(cenide="no"):
    o = ObraEntrada(ide=10, codigo="9999", nombre="obra sintetica",
                    empresa=1)
    if cenide != "no":
        o.cenide = cenide
    return o


# ----------------------------- lecturas ----------------------------- #

def test_f046_t22_lineas_para_reajuste_con_columnas_nulas(monkeypatch):
    api = ApiFalsa(COLS_LINEAS, [
        [4001, None, None, None, None, None, 8.0, 160.0, None, "partes:11",
         0]])
    ls = _cli(monkeypatch, api).lineas_para_reajuste(["partes:11"])[
        "partes:11"]
    assert (ls.reside, ls.fecha_int, ls.horide, ls.hmoide, ls.pre) == (
        0, 0, None, None, None)


def test_f046_t22_estados_de_partes_sin_obra(monkeypatch):
    api = ApiFalsa(["ide", "obride", "cod", "est"],
                   [[7001, None, "PT26/09001", 1]])
    out = _cli(monkeypatch, api).estados_de_partes([7001])
    assert out == {7001: {"cod": "PT26/09001", "est": 1, "obride": None}}


# ------------------------- INSERT de la extra ------------------------- #

def test_f046_t22_insertar_extra_obra_sin_centro_va_con_cenide_0(
        monkeypatch):
    cli = _cli(monkeypatch, ApiFalsa())
    assert _insertar(cli, _obra())[2] == 0            # sin el atributo
    assert _insertar(cli, _obra(None))[2] == 0        # atributo a None


def test_f046_t22_insertar_extra_sin_partida_va_con_paride_0(monkeypatch):
    cli = _cli(monkeypatch, ApiFalsa())
    assert _insertar(cli, _obra(77), paride=0)[4] == 0
    assert _insertar(cli, _obra(77), paride=None)[4] == 0


def test_f046_t22_insertar_extra_tot_redondeado_a_2_decimales(monkeypatch):
    cli = _cli(monkeypatch, ApiFalsa())
    params = _insertar(cli, _obra(77), can=0.5, pre=0.123)
    assert params[10] == 0.06


# ---------------------------- escribir_lote ---------------------------- #

class _ApiTimeout(ApiFalsa):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.timeouts: list = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.timeouts.append(timeout)
        return super().__call__(url, headers=headers, timeout=timeout,
                                json=json)


_OK = {"ok": True, "committed": True,
       "results": [{"operation": "UPDATE", "affected_rows": 1}]}
_ST = [{"sql": "UPDATE x SET a=1 WHERE b=1", "parameters": []}]


def test_f046_t22_escribir_lote_espera_60_s_mas_que_el_timeout(monkeypatch):
    api = _ApiTimeout(escritura=_OK)
    assert _cli(monkeypatch, api, timeout_s=30).escribir_lote(_ST) == [1]
    assert api.timeouts == [90.0]


def test_f046_t22_escribir_lote_ok_sin_committed_no_esta_confirmada(
        monkeypatch):
    api = ApiFalsa(escritura={"ok": True, "committed": False,
                              "results": [{"affected_rows": 1}]})
    with pytest.raises(RuntimeError, match="escritura no confirmada"):
        _cli(monkeypatch, api).escribir_lote(_ST)


def test_f046_t22_escribir_lote_error_http_recorta_a_500(monkeypatch):
    texto = "x" * 600
    monkeypatch.setattr(
        "infrastructure.sigrid.sigrid_write_client.httpx.post",
        lambda *a, **k: httpx.Response(500, text=texto))
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="clave-de-test", database="bd")
    with pytest.raises(RuntimeError) as err:
        cli.escribir_lote(_ST)
    assert str(err.value) == f"sigrid-api write HTTP 500: {'x' * 500}"


def test_f046_t22_escribir_lote_no_confirmada_recorta_a_400(monkeypatch):
    cuerpo = {"ok": False, "committed": False, "detalle": "y" * 600}
    api = ApiFalsa(escritura=cuerpo)
    with pytest.raises(RuntimeError) as err:
        _cli(monkeypatch, api).escribir_lote(_ST)
    assert str(err.value) == ("escritura no confirmada: "
                              + str(cuerpo)[:400])


def test_f046_t22_escribir_lote_sin_filas_recorta_a_400(monkeypatch):
    cuerpo = {"ok": True, "committed": True, "detalle": "z" * 600}
    api = ApiFalsa(escritura=cuerpo)
    with pytest.raises(RuntimeError) as err:
        _cli(monkeypatch, api).escribir_lote(_ST)
    assert str(err.value) == ("sigrid-api no devolvio las filas por "
                              "sentencia: " + str(cuerpo)[:400])


def test_f046_t22_escribir_lote_log_recorta_el_sql_a_150(monkeypatch,
                                                           caplog):
    sql = "UPDATE hmores SET can = 1 WHERE " + " OR ".join(
        f"ide = {i}" for i in range(100))
    api = ApiFalsa(escritura=_OK)
    with caplog.at_level(logging.INFO):
        _cli(monkeypatch, api).escribir_lote(
            [{"sql": sql, "parameters": [7]}])
    (texto,) = [r.getMessage() for r in caplog.records
                if "[sigrid-write] reajuste" in r.getMessage()]
    assert texto == f"[sigrid-write] reajuste {sql[:150]} | [7]"
