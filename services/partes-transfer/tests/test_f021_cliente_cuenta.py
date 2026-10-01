# tests/test_f021_cliente_cuenta.py
"""F-021 · R9-R11 y R14: lecturas y sentencia de `SigridWriteClient`.

  - R9: `horas_de_recursos` trae, en la MISMA consulta, el codigo de la
    cuenta de `reshor.caaide` y si la fila es el tipo por defecto.
  - R10-R11: `cuentas_de_centro` es UNA lectura filtrada por centro,
    empresa y subcuentas; un fallo o un `truncated` es una excepcion.
  - R14: el `INSERT INTO hmores` lleva `caaide` como PARAMETRO
    (obligatorio, DA9) en lugar del literal 0.

Ni una llamada real: `httpx.post` se sustituye por un doble. Datos
SINTETICOS.
"""
from __future__ import annotations

import httpx
import pytest

from domain.models.registro_models import HoraRecurso, ObraEntrada
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


def _cliente(monkeypatch, falso) -> SigridWriteClient:
    monkeypatch.setattr(modulo.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


# ======================= R9 · horas_de_recursos ======================= #

COLS_HORAS = ["reside", "horide", "cod", "res", "pre", "caacod", "defecto"]


def test_f021_r9_horas_traen_la_cuenta_y_el_defecto(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_HORAS, [
        [501, 11, "HL01 ", "Laborable", 10.0, "00000.LAB", 1],
        [501, 13, "CIV", "Vacaciones", None, None, 0],
        [502, 12, "HE01", "Extra", 15.5, " 00000.EXT ", 0],
        [502, 14, "HL02", "Otra", 9.0, "", None],
    ])
    horas = _cliente(monkeypatch, falso).horas_de_recursos([502, 501, 501])
    assert horas == {
        501: [HoraRecurso(11, "HL01", "Laborable", 10.0, "00000.LAB", True),
              HoraRecurso(13, "CIV", "Vacaciones", 0.0, None, False)],
        502: [HoraRecurso(12, "HE01", "Extra", 15.5, "00000.EXT", False),
              HoraRecurso(14, "HL02", "Otra", 9.0, None, False)],
    }
    assert isinstance(horas[501][0].defecto, bool)


def test_f021_r9_horas_misma_consulta_con_cuenta_y_defecto(
        monkeypatch) -> None:
    falso = SigridApiFalso(COLS_HORAS, [])
    _cliente(monkeypatch, falso).horas_de_recursos([502, 501])
    (lectura,) = falso.lecturas
    assert _sql(lectura["sql"]) == (
        "SELECT reshor.reside AS reside, reshor.horide AS horide, "
        "auxhor.cod AS cod, auxhor.res AS res, reshor.pre AS pre, "
        "cc.cod AS caacod, "
        "CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END AS defecto "
        "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
        "LEFT JOIN res ON res.ide = reshor.reside "
        "LEFT JOIN con cc ON cc.ide = reshor.caaide "
        "AND ISNULL(reshor.caaide, 0) <> 0 "
        "WHERE reshor.reside IN (?,?) ORDER BY reshor.reside, auxhor.cod")
    assert lectura["parameters"] == [501, 502]


def test_f021_r9_horas_sin_recursos_no_lee(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_HORAS)
    assert _cliente(monkeypatch, falso).horas_de_recursos([None, 0]) == {}
    assert falso.lecturas == []


# ===================== R10-R11 · cuentas_de_centro ===================== #

COLS_CUENTAS = ["caaide", "cod"]


def test_f021_r10_una_lectura_por_centro_empresa_y_subcuentas(
        monkeypatch) -> None:
    falso = SigridApiFalso(COLS_CUENTAS, [
        [701, "0404.LAB"], [702, "0404.EXT "], [703, "0404 . LAB"]])
    cuentas = _cliente(monkeypatch, falso).cuentas_de_centro(
        77, 1, ["LAB", "EXT", "LAB", None, ""])
    assert cuentas == {"LAB": [(701, "0404.LAB"), (703, "0404 . LAB")],
                       "EXT": [(702, "0404.EXT")]}
    (lectura,) = falso.lecturas
    assert _sql(lectura["sql"]) == (
        "SELECT a.ide AS caaide, c.cod AS cod FROM caa a "
        "JOIN con c ON c.ide = a.ide WHERE a.cenide = ? AND c.emp = ? "
        "AND LTRIM(RTRIM(SUBSTRING(c.cod, CHARINDEX('.', c.cod) + 1, 24))) "
        "IN (?,?)")
    assert lectura["parameters"] == [77, 1, "EXT", "LAB"]


def test_f021_r10_el_filtro_sql_solo_acota(monkeypatch) -> None:
    """Un codigo sin punto que el SQL dejara pasar (SUBSTRING desde 1) no
    entra en la regla: la agrupacion la rehace `indexar_cuentas`."""
    falso = SigridApiFalso(COLS_CUENTAS, [[701, "LAB"], [702, "0404.LAB"]])
    assert _cliente(monkeypatch, falso).cuentas_de_centro(77, 1, ["LAB"]) \
        == {"LAB": [(702, "0404.LAB")]}


def test_f021_r10_los_parametros_son_enteros(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_CUENTAS, [])
    _cliente(monkeypatch, falso).cuentas_de_centro("77", "28", ["X"])
    assert falso.lecturas[0]["parameters"] == [77, 28, "X"]


def test_f021_r10_sin_subcuentas_no_lee(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_CUENTAS)
    assert _cliente(monkeypatch, falso).cuentas_de_centro(
        77, 1, [None, ""]) == {}
    assert falso.lecturas == []


def test_f021_r11_cuentas_truncated_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_CUENTAS, [[701, "0404.LAB"]], truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(monkeypatch, falso).cuentas_de_centro(77, 1, ["LAB"])


def test_f021_r11_cuentas_error_http_es_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(COLS_CUENTAS, [], estado=500)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        _cliente(monkeypatch, falso).cuentas_de_centro(77, 1, ["LAB"])


# ======================= R14 · stmt_insert_linea ======================= #

OBRA = ObraEntrada(ide=200, codigo="0404", nombre="Pruebas", empresa=1)
setattr(OBRA, "cenide", 77)

ARGS = dict(hmoide=900, obra=OBRA, reside=501, pos=128, fecha_int=20260915,
            horide=11, can=8.0, pre=10.5, paride=33, ano=2026, mes=9,
            synckey="partes:1", tex=None)


def _insert(**extra) -> dict:
    cli = SigridWriteClient(base_url="http://x", function_key="k",
                            database="bd")
    return cli.stmt_insert_linea(**{**ARGS, **extra})


def test_f021_r14_caaide_es_un_parametro_del_insert() -> None:
    st = _insert(caaide=701)
    assert _sql(st["sql"]) == (
        "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
        "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
        "tex, synckey) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ? "
        "FROM hmores WITH (UPDLOCK, HOLDLOCK)")
    assert st["parameters"] == [900, 501, 77, 200, 33, 128, 20260915, 11,
                                8.0, 10.5, 84.0, 2026, 9, 701, "", "partes:1"]
    assert _sql(st["sql"]).count("?") == len(st["parameters"])


def test_f021_r8_r14_sin_cuenta_se_escribe_cero_como_parametro() -> None:
    st = _insert(caaide=0, tex="PRUEBA-IA")
    assert st["parameters"][13:] == [0, "PRUEBA-IA", "partes:1"]


def test_f021_r14_caaide_se_convierte_a_entero() -> None:
    valor = _insert(caaide="701")["parameters"][13]
    assert valor == 701 and isinstance(valor, int)


def test_f021_r14_caaide_es_obligatorio() -> None:
    """DA9: un 0 por defecto esconderia una llamada que lo olvide."""
    with pytest.raises(TypeError):
        _insert()
