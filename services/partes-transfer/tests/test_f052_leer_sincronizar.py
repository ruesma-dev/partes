# tests/test_f052_leer_sincronizar.py
"""F-052 en sv5: lectura de `hmores` para sincronizar (R1-R3, R5; DA11, DA12).

- `origen_de`: partes, ciz, franquicia, ajena o manual, con el id leído de
  la synckey; coincide con `registro_de_synckey` (DA12).
- `lineas_sincronizar`: por obra o por recurso y fechas, pide el límite
  real (`max_rows` del cliente), ordena por `hmores.ide` y solo pasa de
  página si la página viene llena (DA11); `truncated` es error.
- `lineas_sincronizar_por_synckey`: lotes de `LOTE_COMPROBACION`, sin
  paginar.
- Ninguna lectura trae `tex`, nombres ni DNIs; todas son `/api/sql/read`.

Sin red: `httpx.post` del módulo cliente se sustituye por un falso.
"""
from __future__ import annotations

import re
from dataclasses import asdict, fields

import httpx
import pytest
from application.services.racha_ciz import registro_de_synckey
from domain.models.registro_models import LineaSincronizar
from infrastructure.sigrid import sigrid_write_client as modulo_cliente
from infrastructure.sigrid.sigrid_write_client import (
    LOTE_COMPROBACION,
    SigridWriteClient,
    origen_de,
)

CLAVE = "clave-de-test-f052"

COLUMNAS = ["ide", "hmoide", "parte_cod", "parte_est", "obride", "obra_cod",
            "reside", "fec", "horide", "hora_cod", "hora_ext", "paride",
            "partida_cod", "can", "tot", "synckey", "enlazada"]

#: Campos de R2, en el orden de la spec.
CAMPOS_R2 = ["hmores_ide", "hmoide", "parte_cod", "parte_est", "obra_ide",
             "obra_cod", "recurso_ide", "fecha_int", "hora_ide", "hora_cod",
             "hora_ext", "partida_ide", "partida_cod", "can", "tot",
             "enlazada", "origen", "registro_id", "ajuste_id"]


def _fila(ide: int, synckey: str | None = None, **cambios) -> list:
    base = {"ide": ide, "hmoide": 7001, "parte_cod": "PT26/00001",
            "parte_est": 1, "obride": 686, "obra_cod": "0686",
            "reside": 501, "fec": 20261014, "horide": 3, "hora_cod": "HL01",
            "hora_ext": 0, "paride": 11, "partida_cod": "P1", "can": 8.0,
            "tot": 120.0, "synckey": synckey, "enlazada": 0}
    base.update(cambios)
    return [base[c] for c in COLUMNAS]


class SigridApiPaginas:
    """sigrid-api en memoria: devuelve, por orden, las páginas dadas y
    apunta cada petición (url y cuerpo)."""

    def __init__(self, paginas: list[list[list]], *,
                 truncated: bool = False) -> None:
        self.paginas = list(paginas)
        self.truncated = truncated
        self.urls: list[str] = []
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.urls.append(url)
        self.lecturas.append(json)
        filas = self.paginas.pop(0) if self.paginas else []
        return httpx.Response(200, json={
            "ok": True, "columns": COLUMNAS, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso, **kwargs) -> SigridWriteClient:
    monkeypatch.setattr(modulo_cliente.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key=CLAVE, database="ruesma", **kwargs)


# ------------------------------ origen_de -------------------------------- #

@pytest.mark.parametrize("synckey, esperado", [
    ("partes:12", ("partes", 12, None)),
    ("  partes:12 ", ("partes", 12, None)),
    ("partes:12:ciz", ("ciz", 12, None)),
    ("partes:franquicia:7", ("franquicia", None, 7)),
    ("porcentajes:77", ("ajena", None, None)),
    ("otra:cosa", ("ajena", None, None)),
    ("partes:abc", ("ajena", None, None)),
    ("partes:franquicia:x", ("ajena", None, None)),
    ("partes:x:ciz", ("ajena", None, None)),
    (None, ("manual", None, None)),
    ("", ("manual", None, None)),
    ("   ", ("manual", None, None)),
])
def test_f052_r2_origen_de(synckey, esperado) -> None:
    assert origen_de(synckey) == esperado


MUESTRA_SYNCKEYS = ["partes:1", "partes:42", " partes:9 ", "partes:3:ciz",
                    "partes:franquicia:5", "porcentajes:77", "partes:abc",
                    "partes:", "", None, "manual", "partes:12:ciz:otra"]


@pytest.mark.parametrize("synckey", MUESTRA_SYNCKEYS)
def test_f052_r2_origen_de_coincide_con_registro_de_synckey(synckey) -> None:
    """DA12: el `registro_id` de `partes` es el de `registro_de_synckey`; el
    de `ciz`, el de su inicio; ningún otro origen es un registro."""
    origen, registro_id, _ajuste = origen_de(synckey)
    if origen == "partes":
        assert registro_id == registro_de_synckey(synckey)
    elif origen == "ciz":
        assert registro_de_synckey(synckey) is None
        base = (synckey or "").strip()[:-len(":ciz")]
        assert registro_id == registro_de_synckey(base)
    else:
        assert registro_id is None
        assert registro_de_synckey(synckey) is None


# -------------------------- lineas_sincronizar --------------------------- #

def _sql(falso, i: int = 0) -> str:
    return falso.lecturas[i]["sql"]


def test_f052_r1_por_obra_lee_obra_y_fechas_hasta_el_limite(monkeypatch) -> None:
    falso = SigridApiPaginas([[_fila(1, "partes:5")]])
    cli = _cliente(monkeypatch, falso, max_rows=1234)
    out = cli.lineas_sincronizar(obra_ide=686, desde=20261001,
                                 hasta=20261031)
    assert len(out) == 1 and len(falso.lecturas) == 1
    cuerpo = falso.lecturas[0]
    assert falso.urls == ["http://sigrid.invalid/api/sql/read"]
    assert cuerpo["database"] == "ruesma"
    assert cuerpo["max_rows"] == 1234
    sql = cuerpo["sql"]
    assert "hmores.obride = ?" in sql and "hmores.reside = ?" not in sql
    assert "hmores.fec BETWEEN ? AND ?" in sql
    assert re.search(r"ORDER BY hmores\.ide OFFSET \? ROWS FETCH NEXT \? "
                     r"ROWS ONLY$", sql)
    assert cuerpo["parameters"] == [686, 20261001, 20261031, 0, 1234]


def test_f052_r1_por_recurso_lee_reside(monkeypatch) -> None:
    falso = SigridApiPaginas([[]])
    cli = _cliente(monkeypatch, falso)
    assert cli.lineas_sincronizar(recurso_ide=501, desde=20260916,
                                  hasta=20261015) == []
    sql = _sql(falso)
    assert "hmores.reside = ?" in sql and "hmores.obride = ?" not in sql
    assert falso.lecturas[0]["parameters"] == [501, 20260916, 20261015, 0,
                                               500_000]


@pytest.mark.parametrize("kwargs", [{}, {"obra_ide": 1, "recurso_ide": 2}])
def test_f052_r1_exige_obra_o_recurso_y_no_los_dos(monkeypatch,
                                                   kwargs) -> None:
    falso = SigridApiPaginas([])
    cli = _cliente(monkeypatch, falso)
    with pytest.raises(ValueError):
        cli.lineas_sincronizar(desde=20261001, hasta=20261031, **kwargs)
    assert falso.lecturas == []


def test_f052_r3_pasa_de_pagina_solo_si_viene_llena(monkeypatch) -> None:
    falso = SigridApiPaginas([[_fila(1), _fila(2)], [_fila(3), _fila(4)],
                              [_fila(5)]])
    cli = _cliente(monkeypatch, falso, max_rows=2)
    out = cli.lineas_sincronizar(obra_ide=686, desde=20261001,
                                 hasta=20261031)
    assert [l.hmores_ide for l in out] == [1, 2, 3, 4, 5]
    assert [c["parameters"][3:] for c in falso.lecturas] == [
        [0, 2], [2, 2], [4, 2]]
    assert all(c["max_rows"] == 2 for c in falso.lecturas)


def test_f052_r3_pagina_justa_no_es_error(monkeypatch) -> None:
    """Una página llena obliga a mirar la siguiente; vacía, se acaba."""
    falso = SigridApiPaginas([[_fila(1), _fila(2)], []])
    cli = _cliente(monkeypatch, falso, max_rows=2)
    out = cli.lineas_sincronizar(obra_ide=686, desde=20261001,
                                 hasta=20261031)
    assert [l.hmores_ide for l in out] == [1, 2]
    assert len(falso.lecturas) == 2


def test_f052_r3_pagina_incompleta_no_vuelve_a_leer(monkeypatch) -> None:
    falso = SigridApiPaginas([[_fila(1)], [_fila(2)]])
    cli = _cliente(monkeypatch, falso, max_rows=2)
    cli.lineas_sincronizar(obra_ide=686, desde=20261001, hasta=20261031)
    assert len(falso.lecturas) == 1


def test_f052_r3_truncated_es_error_sin_parciales(monkeypatch) -> None:
    falso = SigridApiPaginas([[_fila(1)]], truncated=True)
    cli = _cliente(monkeypatch, falso)
    with pytest.raises(RuntimeError, match="truncada"):
        cli.lineas_sincronizar(obra_ide=686, desde=20261001,
                               hasta=20261031)


def test_f052_r2_cada_linea_trae_las_columnas_de_r2(monkeypatch) -> None:
    falso = SigridApiPaginas([[
        _fila(10, "partes:5", enlazada=1, hora_ext=1, can=2.5, tot=40.0),
        _fila(11, "partes:5:ciz", horide=None, paride=None,
              partida_cod=None, hora_cod="CIZ", can=None, tot=None),
        _fila(12, "partes:franquicia:3", parte_est=3),
        _fila(13, "porcentajes:77"), _fila(14, None)]])
    cli = _cliente(monkeypatch, falso)
    out = cli.lineas_sincronizar(recurso_ide=501, desde=20261001,
                                 hasta=20261031)
    assert [f.name for f in fields(LineaSincronizar)] == CAMPOS_R2
    assert asdict(out[0]) == {
        "hmores_ide": 10, "hmoide": 7001, "parte_cod": "PT26/00001",
        "parte_est": 1, "obra_ide": 686, "obra_cod": "0686",
        "recurso_ide": 501, "fecha_int": 20261014, "hora_ide": 3,
        "hora_cod": "HL01", "hora_ext": 1, "partida_ide": 11,
        "partida_cod": "P1", "can": 2.5, "tot": 40.0, "enlazada": True,
        "origen": "partes", "registro_id": 5, "ajuste_id": None}
    assert (out[1].origen, out[1].registro_id, out[1].hora_ide,
            out[1].partida_ide, out[1].can) == ("ciz", 5, None, None, None)
    assert (out[2].origen, out[2].ajuste_id, out[2].parte_est) == (
        "franquicia", 3, 3)
    assert [l.origen for l in out[3:]] == ["ajena", "manual"]
    assert out[4].enlazada is False


def test_f052_r1_la_lectura_no_trae_tex_nombres_ni_dni(monkeypatch) -> None:
    falso = SigridApiPaginas([[], []])
    cli = _cliente(monkeypatch, falso)
    cli.lineas_sincronizar(obra_ide=686, desde=20261001, hasta=20261031)
    cli.lineas_sincronizar_por_synckey(["partes:1"])
    for cuerpo in falso.lecturas:
        sql = cuerpo["sql"].lower()
        assert not re.search(r"\btex\b", sql)
        assert "dni" not in sql and ".res " not in sql and "nom" not in sql
        assert "dvaproide" in sql


# --------------------- lineas_sincronizar_por_synckey --------------------- #

def test_f052_r1_por_synckey_en_lotes_sin_paginar(monkeypatch) -> None:
    claves = [f"partes:{i}" for i in range(450)] + ["partes:1", "", None]
    falso = SigridApiPaginas([[_fila(1, "partes:1")], [], []])
    cli = _cliente(monkeypatch, falso)
    out = cli.lineas_sincronizar_por_synckey(claves)
    assert LOTE_COMPROBACION == 200
    assert [len(c["parameters"]) for c in falso.lecturas] == [200, 200, 50]
    todas = [k for c in falso.lecturas for k in c["parameters"]]
    assert todas == sorted({f"partes:{i}" for i in range(450)})
    for cuerpo in falso.lecturas:
        assert "hmores.synckey IN (" in cuerpo["sql"]
        assert "OFFSET" not in cuerpo["sql"]
    assert [(l.hmores_ide, l.registro_id) for l in out] == [(1, 1)]


def test_f052_r1_por_synckey_sin_claves_no_lee(monkeypatch) -> None:
    falso = SigridApiPaginas([])
    cli = _cliente(monkeypatch, falso)
    assert cli.lineas_sincronizar_por_synckey(["", None]) == []
    assert falso.lecturas == []


def test_f052_r3_por_synckey_truncated_es_error(monkeypatch) -> None:
    falso = SigridApiPaginas([[_fila(1, "partes:1")]], truncated=True)
    cli = _cliente(monkeypatch, falso)
    with pytest.raises(RuntimeError):
        cli.lineas_sincronizar_por_synckey(["partes:1"])
