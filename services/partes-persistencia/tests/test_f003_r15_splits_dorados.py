# tests/test_f003_r15_splits_dorados.py
"""R15 · el computo de extras produce EXACTAMENTE los mismos numeros.

F-003 cambia de DONDE salen los festivos (Sesame en vez del JSON) y de
donde sale la jornada (un resolutor unico), pero mientras sesame-api no
exponga la jornada del contrato en horas, ni un solo split puede moverse.

Estos son los casos dorados de `_reclasificar_extras_jornada`, escritos
contra el comportamiento vigente antes de tocar nada: si el refactor
altera un reparto, aqui salta.
"""
from __future__ import annotations

import pytest

from application.services.recurso_conciliador import RecursoConciliador
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

LUNES = 20260302     # 2026-03-02, laborable
DOMINGO = 20260301   # 2026-03-01, fin de semana
FESTIVO = 20260320   # 2026-03-20, viernes declarado festivo en los dobles


def _conciliador(*, calendario=None, jornada: float = 8.0,
                 candef_min: float = 2.0) -> RecursoConciliador:
    return RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=calendario, jornada_ordinaria_horas=jornada,
        candef_minimo=candef_min,
    )


def _splits(regs, *, candef=8.0, calendario=None, con_extra=True,
            jornada=8.0, candef_min=2.0):
    c = _conciliador(calendario=calendario, jornada=jornada,
                     candef_min=candef_min)
    return c._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef, con_extra=con_extra),
    )


# ------------------------- dia laborable: exceso ------------------------ #

def test_f003_r15_exceso_de_jornada_pasa_a_extra() -> None:
    """10 h ordinarias con jornada 8 -> 8 ordinarias + 2 extra."""
    regs = [registro(1, fecha_int=LUNES, horas=10.0)]
    splits = _splits(regs)
    assert splits == [{
        "normal_id": 1, "horas_norm": 8.0, "horas_orig": 10.0,
        "extra_horas": 2.0, "hora_ext_ide": 200, "hora_ext_cod": "HE01",
        "hora_ext_desc": "Hora extra", "hora_ext_ext": 1, "hora_candef": 8.0,
    }]


def test_f003_r15_exceso_recorta_desde_el_registro_de_mayor_id() -> None:
    """El recorte empieza por las ultimas horas del dia (id mayor)."""
    regs = [registro(1, fecha_int=LUNES, horas=5.0),
            registro(2, fecha_int=LUNES, horas=5.0)]
    splits = _splits(regs)
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits] == [(2, 3.0, 2.0)]


def test_f003_r15_exceso_desborda_al_siguiente_registro() -> None:
    """Si la ultima linea no cubre todo el exceso, se sigue por la anterior.

    5+5+5 = 15 h con jornada 8: sobran 7. La linea 3 aporta sus 5 enteras
    y la 2 pone las 2 que faltan; la 1 se queda intacta (no genera split).
    """
    regs = [registro(1, fecha_int=LUNES, horas=5.0),
            registro(2, fecha_int=LUNES, horas=5.0),
            registro(3, fecha_int=LUNES, horas=5.0)]
    splits = _splits(regs)
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits] == [(3, 0.0, 5.0), (2, 3.0, 2.0)]


# ------------------------ dia laborable: defecto ------------------------ #

def test_f003_r15_jornada_incompleta_genera_extra_negativa() -> None:
    """Viernes tipico: 6 h con jornada 8 -> ordinaria 8 y extra -2."""
    regs = [registro(1, fecha_int=LUNES, horas=6.0)]
    splits = _splits(regs)
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits] == [(1, 8.0, -2.0)]


def test_f003_r15_extras_explicitas_cuentan_en_el_total() -> None:
    """6 ordinarias + 4 extra con jornada 8: total 10, extra objetivo 2,
    sobran 2 de extra explicita -> se sube la ordinaria y extra -2."""
    regs = [registro(1, fecha_int=LUNES, horas=6.0),
            registro(2, fecha_int=LUNES, horas=4.0, tipo="extra")]
    splits = _splits(regs)
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits] == [(1, 8.0, -2.0)]


def test_f003_r15_dia_cuadrado_no_produce_split() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=8.0)]
    assert _splits(regs) == []


def test_f003_r15_dia_sin_ordinarias_no_se_normaliza() -> None:
    """Solo extras explicitas: se respeta el desglose del parte."""
    regs = [registro(1, fecha_int=LUNES, horas=4.0, tipo="extra")]
    assert _splits(regs) == []


# ------------------------------ el candef ------------------------------- #

@pytest.mark.parametrize("candef, norm, extra", [
    (None, 8.0, -2.0),   # no informado -> jornada por defecto 8
    (0.0, 8.0, -2.0),    # 0 -> no informado
    (2.0, 8.0, -2.0),    # <= minimo -> no informado
    (2.5, 2.5, 3.5),     # valido: manda Sigrid
    (6.0, 6.0, 0.0),     # valido y justo: extra 0 explicita
])
def test_f003_r15_candef_efectivo(candef, norm, extra) -> None:
    """6 h trabajadas contra distintos CanDefecto del recurso."""
    regs = [registro(1, fecha_int=LUNES, horas=6.0)]
    splits = _splits(regs, candef=candef)
    if extra == 0.0:
        assert splits == []
        return
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [
        (norm, extra)]
    assert splits[0]["hora_candef"] == candef


def test_f003_r15_candef_real_se_persiste_tal_cual() -> None:
    """El split guarda el candef REAL de Sigrid (diagnostico), no el
    efectivo: si Sigrid dice 0, en la BBDD queda 0."""
    regs = [registro(1, fecha_int=LUNES, horas=10.0)]
    splits = _splits(regs, candef=0.0)
    assert splits[0]["hora_candef"] == 0.0
    assert splits[0]["horas_norm"] == 8.0   # pero calcula con 8


# --------------------------- dia no laborable --------------------------- #

def test_f003_r15_domingo_manda_todo_lo_ordinario_a_extra() -> None:
    regs = [registro(1, fecha_int=DOMINGO, horas=6.0)]
    splits = _splits(regs, calendario=CalendarioFake({"2026-03-01"}))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [(0.0, 6.0)]


def test_f003_r15_festivo_manda_todo_lo_ordinario_a_extra() -> None:
    regs = [registro(1, fecha_int=FESTIVO, horas=8.0)]
    splits = _splits(regs, calendario=CalendarioFake({"2026-03-20"}))
    assert [(s["horas_norm"], s["extra_horas"]) for s in splits] == [(0.0, 8.0)]


def test_f003_r15_sin_calendario_el_festivo_es_dia_normal() -> None:
    """Sin calendario cableado, el 20 de marzo es un viernes cualquiera."""
    regs = [registro(1, fecha_int=FESTIVO, horas=8.0)]
    assert _splits(regs, calendario=None) == []


def test_f003_r15_no_laborable_sin_horas_ordinarias_no_produce_split() -> None:
    regs = [registro(1, fecha_int=DOMINGO, horas=4.0, tipo="extra")]
    assert _splits(regs, calendario=CalendarioFake({"2026-03-01"})) == []


# ---------------------- recurso sin codigo de extra --------------------- #

def test_f003_r15_recurso_sin_hora_extra_no_se_normaliza() -> None:
    """Mensuales tipo encargado: se respetan las horas del parte."""
    regs = [registro(1, fecha_int=LUNES, horas=10.0)]
    assert _splits(regs, con_extra=False) == []


def test_f003_r15_recurso_sin_reshor_no_se_normaliza() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0)]
    c = _conciliador()
    assert c._reclasificar_extras_jornada(
        regs, {1: 501}, {}) == []


# ----------------------------- agrupacion ------------------------------- #

def test_f003_r15_agrupa_por_recurso_y_dia_across_obras() -> None:
    """4 h en una obra + 6 h en otra el mismo dia = 10 h -> 2 de extra."""
    regs = [registro(1, fecha_int=LUNES, horas=4.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=6.0, obra_ide=20)]
    splits = _splits(regs)
    assert [(s["normal_id"], s["horas_norm"], s["extra_horas"])
            for s in splits] == [(2, 4.0, 2.0)]


def test_f003_r15_dias_distintos_no_se_mezclan() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=6.0),
            registro(2, fecha_int=LUNES + 1, horas=6.0)]
    splits = _splits(regs)
    assert sorted((s["normal_id"], s["extra_horas"]) for s in splits) == [
        (1, -2.0), (2, -2.0)]


def test_f003_r15_registro_sin_recurso_resuelto_se_ignora() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0)]
    c = _conciliador()
    assert c._reclasificar_extras_jornada(
        regs, {}, indice_reshor(501)) == []
