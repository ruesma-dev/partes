# tests/test_f019_reglas.py
"""F-019 · ReglasRegistro con el interruptor MENSUALES_A_DEDICACION.

T1 (R1): tests de CARACTERIZACION escritos contra el codigo anterior a
F-019. Fijan lo que `ReglasRegistro` decide hoy para un mensual sin HE*,
un capataz MCAP+HECAP, un trabajador por horas, incidencias de inicio,
intermedio y fin, lineas sin recurso, sin horas y de tipo raro. Tienen que
seguir en verde con el interruptor apagado (el valor por defecto).

Sin red: tipos de hora sinteticos en memoria (codigos y precios
inventados, sin nombres reales ni DNIs).
"""
from __future__ import annotations

import pytest
from application.services.reglas_registro import (
    MOTIVO_INTERMEDIO,
    MOTIVO_SIN_CI,
    MOTIVO_SIN_CIZ,
    MOTIVO_SIN_EXTRA,
    MOTIVO_SIN_HORAS,
    MOTIVO_SIN_LABORABLE,
    MOTIVO_SIN_RECURSO,
    MOTIVO_TIPO,
    ReglasRegistro,
)
from domain.models.registro_models import HoraRecurso, LineaEntrada

FECHA = 20260302

# Tipos de hora (horide sinteticos).
HL, HE, CIV, CIZ, MENC, MCAP, HECAP = 1, 2, 3, 4, 5, 6, 7


def _h(horide: int, cod: str, pre: float = 10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre)


#: Recurso -> tipos de hora de su ficha (`reshor`).
HORAS = {
    # Trabajador por horas: HL + HE + incidencias.
    601: [_h(HL, "HL01", 12.0), _h(HE, "HE01", 15.0), _h(CIV, "CIV", 1.0),
          _h(CIZ, "CIZ", 2.0)],
    # Mensual sin HE* (encargado): solo su codigo mensual + incidencias.
    602: [_h(MENC, "MENC", 0.0), _h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)],
    # Capataz MCAP + HECAP: mensual que cobra sus extras.
    603: [_h(MCAP, "MCAP", 0.0), _h(HECAP, "HECAP", 18.0),
          _h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)],
    # Mensual sin codigos de incidencia.
    604: [_h(MENC, "MENC", 0.0)],
    # Mensual con incidencia de inicio pero sin CIZ.
    605: [_h(MENC, "MENC", 0.0), _h(CIV, "CIV", 1.0)],
}


def _lin(rid: int, recurso: int | None = 601, tipo: str | None = "normal",
         horas: float | None = 8.0, **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, tipo_hora=tipo, horas=horas,
                        nombre=f"Persona {rid}", **kw)


def _inc(rid: int, recurso: int | None = 602, rol: str | None = "inicio",
         **kw) -> LineaEntrada:
    kw.setdefault("hora_ide", CIV)
    kw.setdefault("hora_codigo", "CIV")
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, es_incidencia=True,
                        incidencia_rol=rol, incidencia_codigo="V",
                        nombre=f"Persona {rid}", **kw)


def _resumen(a) -> tuple:
    """Lo que decide la regla, sin los campos que copia de la linea."""
    return (a.accion, a.motivo, a.hora_ide, a.hora_codigo, a.can, a.pre,
            a.tot)


#: (caso, linea, decision de HOY). Es la caracterizacion de R1.
CASOS_HOY = [
    ("horas_ordinaria", _lin(1, 601, "normal", 8.0),
     ("escribir", None, HL, "HL01", 8.0, 12.0, 96.0)),
    ("horas_extra_negativa", _lin(2, 601, "extra", -1.5),
     ("escribir", None, HE, "HE01", -1.5, 15.0, -22.5)),
    ("horas_inc_inicio", _inc(3, 601, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_ordinaria", _lin(10, 602, "normal", 8.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
    ("mensual_extra", _lin(11, 602, "extra", 2.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
    ("mensual_inc_inicio", _inc(12, 602, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_inc_intermedio", _inc(13, 602, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("mensual_inc_fin", _inc(14, 602, "fin"),
     ("escribir", None, CIZ, "CIZ", 0.0, 2.0, 0.0)),
    ("mensual_inc_sin_rol", _inc(15, 602, None),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_sin_ci", _inc(16, 604, "inicio"),
     ("omitir", MOTIVO_SIN_CI, None, None, None, None, None)),
    ("mensual_sin_ciz", _inc(17, 605, "fin"),
     ("omitir", MOTIVO_SIN_CIZ, None, None, None, None, None)),
    ("mensual_ci_no_casa", _inc(18, 602, "inicio", hora_ide=None,
                                hora_codigo="CIX"),
     ("omitir", f"{MOTIVO_SIN_CI} (codigo leido: CIX)", None, None, None,
      None, None)),
    ("capataz_ordinaria", _lin(20, 603, "normal", 8.0),
     ("omitir", MOTIVO_SIN_LABORABLE, None, None, None, None, None)),
    ("capataz_extra", _lin(21, 603, "extra", 2.0),
     ("escribir", None, HECAP, "HECAP", 2.0, 18.0, 36.0)),
    ("capataz_inc_inicio", _inc(22, 603, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("capataz_inc_intermedio", _inc(23, 603, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("capataz_inc_fin", _inc(24, 603, "fin"),
     ("escribir", None, CIZ, "CIZ", 0.0, 2.0, 0.0)),
    ("sin_recurso", _lin(30, None, "normal", 8.0),
     ("omitir", MOTIVO_SIN_RECURSO, None, None, None, None, None)),
    ("sin_recurso_inc", _inc(31, None, "inicio"),
     ("omitir", MOTIVO_SIN_RECURSO, None, None, None, None, None)),
    ("sin_recurso_inc_intermedio", _inc(32, None, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("mensual_sin_horas", _lin(33, 602, "normal", 0.0),
     ("omitir", MOTIVO_SIN_HORAS, None, None, None, None, None)),
    ("mensual_horas_nulas", _lin(34, 602, "extra", None),
     ("omitir", MOTIVO_SIN_HORAS, None, None, None, None, None)),
    ("mensual_tipo_raro", _lin(35, 602, "nocturna", 8.0),
     ("omitir", f"{MOTIVO_TIPO}: 'nocturna'", None, None, None, None, None)),
    ("mensual_tipo_nulo", _lin(36, 602, None, 8.0),
     ("omitir", f"{MOTIVO_TIPO}: None", None, None, None, None, None)),
    ("mensual_tipo_mayusculas", _lin(37, 602, " Normal ", 8.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
]


# ============================ R1 · caracterizacion ============================ #

@pytest.mark.parametrize("caso,linea,esperado", CASOS_HOY,
                         ids=[c[0] for c in CASOS_HOY])
def test_f019_r1_caracterizacion_decision_de_hoy(caso, linea,
                                                 esperado) -> None:
    accion = ReglasRegistro(HORAS).decidir(linea)
    assert _resumen(accion) == esperado, caso
    assert accion.registro_id == linea.registro_id
    assert accion.recurso_ide == linea.recurso_ide


def test_f019_r1_caracterizacion_la_omision_previa_manda() -> None:
    """F-023: la verificacion del recurso manda sobre cualquier regla."""
    reglas = ReglasRegistro(HORAS, omisiones={40: "recurso de baja",
                                              41: "recurso de baja"})
    for linea in (_lin(40, 601, "normal", 8.0), _inc(41, 602, "inicio")):
        assert _resumen(reglas.decidir(linea)) == (
            "omitir", "recurso de baja", None, None, None, None, None)
