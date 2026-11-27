# tests/test_f085_inicio_movido_sv4.py
"""F-085 · parte B en sv4: el inicio de la racha se recoloca.

  - R28: una escrita con `movida_de` = X y código distinto de `CIZ` deja X
    `omitido` con `inicio_movido` (mismo CAS que F-060 R28); con `CIZ`,
    `fin_movido` como hoy; aplicarla dos veces da lo mismo.
  - R29: con `MOVER_INICIO`, una incidencia `inicio` cuyo siguiente día que
    cuenta es de su misma clave no da `racha_desordenada`; con trabajo,
    otra clave o el interruptor apagado, como hoy (F-060 R10).
  - El ajuste `MOVER_INICIO` de sv4, apagado por defecto.

SQLite en memoria (`FabricaSesionSqlite`). Datos SINTÉTICOS.
"""
from __future__ import annotations

import logging
import unicodedata

import pytest
from application.services.racha_incidencia import (
    LIMITE_MOTIVO,
    MOTIVO_INICIO_MOVIDO,
    LineaHist,
    aviso_desordenada,
    motivo_inicio_movido,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import estados_sigrid
from tests.test_f025_deteccion import TABLA
from tests.test_f060_aprobacion_racha import (
    MOTIVO_X,
    _avisos,
    _con_ciz,
    _dia,
    _fabrica,
    _marcar,
    _resultado,
    _t,
    _v,
)

MOTIVO_INICIO_X = ("inicio_movido: el inicio de la incidencia (CIV, linea "
                   "9000) paso al dia 2026-10-04: este dia es intermedio")


# ------------------------------- puro -------------------------------- #

def test_f085_r28_motivo_exacto_y_largo() -> None:
    assert MOTIVO_INICIO_MOVIDO == "inicio_movido"
    assert motivo_inicio_movido("CIV", 9000, 20261004) == MOTIVO_INICIO_X
    largo = motivo_inicio_movido("C" * 300, 9000, 20261004)
    assert len(largo) <= LIMITE_MOTIVO and largo.startswith("inicio_movido")
    assert motivo_inicio_movido(None, 1, None) == (
        "inicio_movido: el inicio de la incidencia (?, linea 1) paso al dia "
        "?: este dia es intermedio")
    assert MOTIVO_INICIO_X.isascii()
    assert unicodedata.normalize("NFKD", MOTIVO_INICIO_X) == MOTIVO_INICIO_X


def _h(fecha_int, *, clave="V", horas=None, estado="registrado",
       incidencia=True, activa=True) -> LineaHist:
    return LineaHist(registro_id=fecha_int % 100, fecha_int=fecha_int,
                     es_incidencia=incidencia, clave=clave if incidencia
                     else None, horas=horas, activa=activa,
                     sigrid_estado=estado)


@pytest.mark.parametrize("hist, clave, esperado", [
    ([_h(20261005)], None, 20261005),               # sin clave, como hoy
    ([_h(20261005)], "V", None),                    # su misma clave
    ([_h(20261005, clave="B")], "V", 20261005),     # otra clave
    ([_h(20261005, incidencia=False, horas=8.0),
      _h(20261005)], "V", 20261005),                # trabajo ese dia
    ([_h(20261006)], "V", None),                    # salta el dia vacio
])
def test_f085_r29_aviso_desordenada_con_clave(hist, clave, esperado) -> None:
    assert aviso_desordenada(hist, 20261004, clave) == esperado


# ----------------------------- R29 (repo) ----------------------------- #

def _datos(fabrica, ids, *, mover_inicio=True) -> dict:
    return ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=TABLA, mover_ciz=True, mover_inicio=mover_inicio)


@pytest.mark.parametrize("mover_inicio, avisa", [(True, False),
                                                 (False, True)])
def test_f085_r29_inicio_de_su_misma_letra(mover_inicio, avisa) -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4)
    datos = _datos(f, [d4], mover_inicio=mover_inicio)
    assert [a["registro_id"] for a in _avisos(datos)] == ([d4] if avisa
                                                          else [])
    linea = next(l for l in datos["lineas"] if l["registro_id"] == d4)
    assert linea["incidencia_rol"] == "inicio"
    assert linea["racha_registro_ids"]            # su tramo delante (F-062)


def test_f085_r29_otra_letra_sigue_avisando() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4, letra="B")
    assert [a["registro_id"] for a in _avisos(_datos(f, [d4]))] == [d4]


def test_f085_r29_un_trabajo_sigue_avisando() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    assert [a["registro_id"] for a in _avisos(_datos(f, [t]))] == [t]


def test_f085_r29_por_defecto_apagado() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4)
    datos = ParteReviewRepository(f).lineas_para_registro(
        [d4], incidencias=TABLA, mover_ciz=True)
    assert [a["registro_id"] for a in _avisos(datos)] == [d4]


# ----------------------------- R28 (repo) ----------------------------- #

def _recolocado(fabrica):
    """X (dia 5) era el inicio (CIV, linea 9000); D (dia 4) se aprueba."""
    x = _con_ciz(fabrica, _v(fabrica, 5))
    d = _v(fabrica, 4)
    return x, d


def test_f085_r28_inicio_movido_deja_x_omitido() -> None:
    f = _fabrica()
    x, d = _recolocado(f)
    _marcar(f, _resultado(d, x, hora_codigo="CIV"))
    est = estados_sigrid(f, [x, d])
    assert est[d][0] == "registrado" and est[d][3] == 9000
    assert est[x][0] == "omitido" and est[x][1] == MOTIVO_INICIO_X
    assert est[x][3] == 9000                      # traza


def test_f085_r28_dos_veces_da_lo_mismo(caplog) -> None:
    f = _fabrica()
    x, d = _recolocado(f)
    _marcar(f, _resultado(d, x, hora_codigo="CIV"))
    antes = estados_sigrid(f, [x, d])
    with caplog.at_level(logging.WARNING):
        _marcar(f, _resultado(d, x, hora_codigo="CIV"))
    assert estados_sigrid(f, [x, d]) == antes
    assert "fin_movido_sin_cas" not in caplog.text


@pytest.mark.parametrize("cod", ["CIZ", " ciz "])
def test_f085_r28_con_ciz_fin_movido_como_hoy(cod) -> None:
    f = _fabrica()
    x = _con_ciz(f, _v(f, 3))
    d = _v(f, 4)
    _marcar(f, _resultado(d, x, hora_codigo=cod))
    assert estados_sigrid(f, [x])[x][1] == MOTIVO_X


def test_f085_r28_sin_cas_no_toca() -> None:
    f = _fabrica()
    x, d = _recolocado(f)
    _marcar(f, _resultado(d, x, ide=8888, hora_codigo="CIV"))
    assert estados_sigrid(f, [x])[x][0] == "registrado"


# ------------------------------ ajustes ------------------------------ #

def test_f085_settings_mover_inicio_apagado_por_defecto(monkeypatch) -> None:
    from config.settings import Settings
    campo = Settings.model_fields["mover_inicio"]
    assert campo.default is False and campo.alias == "MOVER_INICIO"


def test_f085_app_pasa_mover_inicio() -> None:
    from pathlib import Path
    fuente = (Path(__file__).resolve().parents[1] / "interface_adapters"
              / "web" / "app.py").read_text(encoding="utf-8")
    assert "mover_inicio=settings.mover_inicio" in fuente
    assert _dia(4) == "2026-10-04"
