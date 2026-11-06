# tests/test_f066_clase_hora.py
"""F-066 en sv4: la lista de códigos excluidos y la regla de extra (R1–R6).

- `es_excluido` / `es_hora_extra` / `tipo_hora_de_codigo`: tablas (R1, R2).
- Las cuatro funciones se derivan de `PREFIJO_EXTRA` y `CODIGOS_EXCLUIDOS`
  (R3, con `monkeypatch`).
- `condicion_sql_extra`: texto exacto y columna validada (R4).
- `sincronizacion.es_hora_extra` es la misma función y un excluido en
  Sigrid no es extra al comparar (R5).
- R6 (ningún otro fichero de sv4 implementa la regla) vive en
  `test_f066_usos_sv4.py`: cierra al cambiar esos usos (T7).

Sin red ni base de datos.
"""
from __future__ import annotations

import pytest

from application.services import clase_hora
from application.services.clase_hora import (
    CODIGOS_EXCLUIDOS,
    PREFIJO_EXTRA,
    condicion_sql_extra,
    es_excluido,
    es_hora_extra,
    tipo_hora_de_codigo,
)

# --------------------------------- R1 ----------------------------------- #

def test_f066_r1_constantes() -> None:
    assert PREFIJO_EXTRA == "HE"
    assert CODIGOS_EXCLUIDOS == ("HENC",)


@pytest.mark.parametrize("codigo, esperado", [
    ("HENC", True), (" henc ", True), ("Henc", True),
    ("HEOF", False), ("MENC", False), ("HENCX", False),
    (None, False), ("", False), ("   ", False),
])
def test_f066_r1_excluidos(codigo, esperado) -> None:
    assert es_excluido(codigo) is esperado


# --------------------------------- R2 ----------------------------------- #

@pytest.mark.parametrize("codigo, esperado", [
    ("HECAP", True), ("HEGR", True), (" heof ", True), ("HEPE", True),
    ("HEAA", True), ("HEOM", True),
    ("HENC", False), (" henc ", False),
    ("HL01", False), ("MENC", False), ("CI01", False), ("H", False),
    ("XHE", False),
    (None, None), ("", None), ("   ", None),
])
def test_f066_r2_regla_extra(codigo, esperado) -> None:
    assert es_hora_extra(codigo) is esperado


@pytest.mark.parametrize("codigo, esperado", [
    ("HEOF", "extra"), (" hecap", "extra"), ("HENC", "normal"),
    ("HL01", "normal"), ("MENC", "normal"),
    (None, None), ("", None), ("  ", None),
])
def test_f066_r2_tipo_hora_de_codigo(codigo, esperado) -> None:
    assert tipo_hora_de_codigo(codigo) == esperado


# --------------------------------- R3 ----------------------------------- #

def test_f066_r3_derivadas_del_prefijo(monkeypatch) -> None:
    monkeypatch.setattr(clase_hora, "PREFIJO_EXTRA", "XX")
    assert es_hora_extra("XX01") is True
    assert es_hora_extra("HEOF") is False
    assert tipo_hora_de_codigo("XX01") == "extra"
    assert tipo_hora_de_codigo("HEOF") == "normal"
    assert "LIKE 'XX%'" in condicion_sql_extra("auxhor.cod")
    assert "'HE%'" not in condicion_sql_extra("auxhor.cod")


def test_f066_r3_derivadas_de_la_lista(monkeypatch) -> None:
    monkeypatch.setattr(clase_hora, "CODIGOS_EXCLUIDOS", ("HEOF", "HEGR"))
    assert es_excluido("HEOF") is True and es_excluido("HENC") is False
    assert es_hora_extra("HEOF") is False
    assert es_hora_extra("HENC") is True
    assert tipo_hora_de_codigo("HEGR") == "normal"
    assert tipo_hora_de_codigo("HENC") == "extra"
    assert "NOT IN ('HEOF', 'HEGR')" in condicion_sql_extra("auxhor.cod")
    assert "HENC" not in condicion_sql_extra("auxhor.cod")


def test_f066_r3_lista_vacia(monkeypatch) -> None:
    monkeypatch.setattr(clase_hora, "CODIGOS_EXCLUIDOS", ())
    assert es_hora_extra("HENC") is True
    assert condicion_sql_extra("c") == "UPPER(LTRIM(RTRIM(c))) LIKE 'HE%'"


# --------------------------------- R4 ----------------------------------- #

def test_f066_r4_condicion_sql_texto_exacto() -> None:
    assert condicion_sql_extra("auxhor.cod") == (
        "UPPER(LTRIM(RTRIM(auxhor.cod))) LIKE 'HE%' AND "
        "UPPER(LTRIM(RTRIM(auxhor.cod))) NOT IN ('HENC')")


@pytest.mark.parametrize("columna", ["cod", "auxhor.cod", "a_1.b_2", "_x"])
def test_f066_r4_columna_valida(columna) -> None:
    assert columna in condicion_sql_extra(columna)


@pytest.mark.parametrize("columna", [
    "", " ", "cod;DROP TABLE x", "cod --", "a.b.c", "1cod", "cod)",
    "auxhor.cod OR 1=1", "a.", ".a", "cod\n",
])
def test_f066_r4_columna_invalida(columna) -> None:
    with pytest.raises(ValueError):
        condicion_sql_extra(columna)


# --------------------------------- R5 ----------------------------------- #

def test_f066_r5_sincronizacion_misma_funcion() -> None:
    from application.services import sincronizacion
    assert sincronizacion.es_hora_extra is es_hora_extra


def test_f066_r5_sincronizacion_excluido_no_es_extra() -> None:
    from application.services.sincronizacion import (
        LineaPortal, LineaSigridSync, comparar)
    p = LineaPortal(registro_id=1, fecha_int=20220421, recurso_ide=501,
                    obra_ide=640, horas=4.0, extra=False,
                    es_incidencia=False, hora_codigo="HENC", partida_ide=11,
                    partida_cod="P1", sigrid_estado="registrado",
                    sigrid_motivo=None, sigrid_hmores_ide=None,
                    sigrid_hmoide=None)
    s = LineaSigridSync(hmores_ide=9, hmoide=7, parte_cod="PT",
                        parte_est=1, obra_ide=640, obra_cod="0640",
                        recurso_ide=501, fecha_int=20220421, hora_ide=63,
                        hora_cod="HENC", hora_ext=0, partida_ide=11,
                        partida_cod="P1", can=4.0, tot=4.0, enlazada=False,
                        origen="manual", registro_id=None, ajuste_id=None)
    difs, _ = comparar(p, s)
    assert [d.campo for d in difs] == []
    # Con la portal extra, la de Sigrid (excluida) es ordinaria ⇒ diferencia.
    from dataclasses import replace
    difs, _ = comparar(replace(p, extra=True), s)
    assert [(d.campo, d.portal, d.sigrid) for d in difs] == [
        ("clase_hora", "extra", "ordinaria")]
