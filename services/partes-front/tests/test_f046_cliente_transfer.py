# tests/test_f046_cliente_transfer.py
"""F-046 · cliente de sv5 para el reajuste (R20, R33, R34).

Lo importante es la diferencia entre «sv5 dijo que no» (nada escrito: el
reparto vuelve a `pendiente`) y «no se sabe» (`sin_respuesta`: sigue
`aplicando` y el reintento es seguro). Sin red: `httpx.post` sustituido.
"""
from __future__ import annotations

import httpx
import pytest
from infrastructure.persistencia.recalculo_publisher import MOTIVO_REAJUSTE
from infrastructure.transfer import transfer_client as modulo
from infrastructure.transfer.transfer_client import TransferClient


def _cliente(monkeypatch, respuesta) -> tuple[TransferClient, list]:
    llamadas: list = []

    def post(url, json=None, timeout=None):
        llamadas.append((url, json, timeout))
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(modulo.httpx, "post", post)
    return TransferClient(base_url="http://sv5.invalid", timeout_s=30), \
        llamadas


def test_f046_r33_ejecutar_va_a_la_ruta_de_reajuste(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, httpx.Response(
        200, json={"ok": True, "lineas": []}))
    assert cli.reajuste_ejecutar({"lineas": [1]}) == {"ok": True,
                                                      "lineas": []}
    ((url, cuerpo, plazo),) = llamadas
    assert url == "http://sv5.invalid/api/reajuste/ejecutar"
    assert cuerpo == {"lineas": [1]} and plazo == 30


def test_f046_r30_comprobar_con_su_plazo(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, httpx.Response(
        200, json={"ok": True}))
    cli.reajuste_comprobar({"lineas": []}, timeout_s=5)
    ((url, _c, plazo),) = llamadas
    assert url.endswith("/api/reajuste/comprobar") and plazo == 5


def test_f046_r34_rechazo_de_sv5_no_es_sin_respuesta(monkeypatch):
    cli, _ = _cliente(monkeypatch, httpx.Response(
        200, json={"ok": False, "error": "no editable"}))
    r = cli.reajuste_ejecutar({})
    assert r == {"ok": False, "error": "no editable"}


def test_f046_r34_422_es_un_no(monkeypatch):
    cli, _ = _cliente(monkeypatch, httpx.Response(
        422, json={"detail": "x"}))
    r = cli.reajuste_ejecutar({})
    assert r["ok"] is False and "sin_respuesta" not in r


@pytest.mark.parametrize("respuesta", [
    httpx.ReadTimeout("lento"),
    httpx.RemoteProtocolError("cortado"),
    httpx.Response(502, json={"ok": False, "error": "a medias"}),
    httpx.Response(500, text="boom"),
])
def test_f046_r34_sin_respuesta_cuando_no_se_sabe(monkeypatch, respuesta):
    cli, _ = _cliente(monkeypatch, respuesta)
    r = cli.reajuste_ejecutar({})
    assert r["ok"] is False and r["sin_respuesta"] is True and r["error"]


def test_f046_r34_sin_conexion_es_un_no(monkeypatch):
    cli, _ = _cliente(monkeypatch, httpx.ConnectError("cerrado"))
    r = cli.reajuste_ejecutar({})
    assert r["ok"] is False and "sin_respuesta" not in r


def test_f046_r33_motivo_del_recalculo():
    assert MOTIVO_REAJUSTE == "reajuste_reparto"
