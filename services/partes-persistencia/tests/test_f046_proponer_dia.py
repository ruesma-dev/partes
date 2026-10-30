# tests/test_f046_proponer_dia.py
"""F-046 · `proponer_dia`: el reparto ideal del dia con lo REAJUSTABLE
como ajustable (R1-R5) y los casos de aceptacion (R6-R9, [E] R9a-R9c).

Una linea congelada es reajustable (`registrado` o solo por parte
aprobado) o dura (`encolado`, `dedicacion`, ordinaria <= 0, pareja con
mas de una extra automatica). Las duras no cambian y cuentan; las
reajustables reciben su ideal como `CambioCongelada` (antes -> despues);
las libres, como `Ajuste` (igual que F-045). Datos sinteticos: obras
0678 y 0704 con ides 678 y 704; jornada 8 salvo que se diga otra cosa.
"""
from __future__ import annotations

import ast
import itertools
import random
from pathlib import Path

import pytest
from application.services import reparto_ponderado as modulo
from application.services.reparto_ponderado import (
    Ajuste,
    CambioCongelada,
    LineaDia,
    PropuestaDia,
    diferencias_ideal,
    proponer_dia,
    repartir_dia,
)

O678, O704 = 678, 704


def _o(rid, obra, horas, *, fija=False, reaj=False, horas_orig=None):
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="ordinaria",
                    horas=horas, horas_orig=horas_orig, fija=fija,
                    reajustable=reaj)


def _e(rid, obra, horas, *, fija=False, reaj=False, base_id=None,
       extra_auto=None):
    auto = (base_id is not None) if extra_auto is None else extra_auto
    return LineaDia(registro_id=rid, obra_ide=obra, tipo="extra",
                    horas=horas, fija=fija, reajustable=reaj,
                    extra_auto=auto, base_id=base_id)


def _aj(p: PropuestaDia) -> dict[int, tuple[float, float]]:
    return {a.registro_id: (a.horas_norm, a.extra_horas) for a in p.ajustes}


def _cb(p: PropuestaDia) -> list[tuple]:
    return [(c.registro_id, c.base_registro_id, c.tipo, c.antes, c.despues)
            for c in p.cambios]


# --------------------------- R6-R9 (J = 8) --------------------------- #

def test_f046_r6_caso_real_0678_registrada_y_0704_nueva():
    p = proponer_dia([
        _o(1, O678, 8.0, fija=True, reaj=True, horas_orig=4.0),
        _e(2, O678, -4.0, fija=True, reaj=True, base_id=1),
        _o(3, O704, 8.0)], 8.0)
    assert p.cuadra is True
    assert _aj(p) == {3: (5.5, 2.5)}
    assert _cb(p) == [(1, 1, "ordinaria", 8.0, 2.5),
                      (2, 1, "extra", -4.0, 1.5)]


def test_f046_r7_extra_nueva_de_una_base_registrada_sin_extra():
    p = proponer_dia([_o(1, O678, 8.0, fija=True, reaj=True),
                      _o(3, O704, 4.0)], 8.0)
    assert _aj(p) == {3: (2.5, 1.5)}
    assert _cb(p) == [(1, 1, "ordinaria", 8.0, 5.5),
                      (None, 1, "extra", 0.0, 2.5)]


def test_f046_r8_la_extra_queda_a_cero():
    p = proponer_dia([
        _o(1, O678, 8.0, fija=True, reaj=True, horas_orig=6.0),
        _e(2, O678, -2.0, fija=True, reaj=True, base_id=1),
        _o(3, O704, 2.0)], 8.0)
    assert _aj(p) == {}                       # 0704: 2 + 0, sin split
    assert _cb(p) == [(1, 1, "ordinaria", 8.0, 6.0),
                      (2, 1, "extra", -2.0, 0.0)]


def test_f046_r9_con_la_0678_encolada_no_hay_propuesta():
    p = proponer_dia([
        _o(1, O678, 8.0, fija=True, horas_orig=4.0),
        _e(2, O678, -4.0, fija=True, base_id=1),
        _o(3, O704, 8.0)], 8.0)
    assert _cb(p) == []
    assert _aj(p) == {3: (0.0, 8.0)}          # F-045: 0 + 8


# ------------------------ [E] candef 9 (R9a-R9c) ------------------------ #

def test_f046_r9a_e_viernes_jornada_6():
    p = proponer_dia([_o(1, O678, 5.0), _o(2, O704, 4.0)], 6.0)
    assert _aj(p) == {1: (3.5, 1.5), 2: (2.5, 1.5)}
    assert _cb(p) == []


def test_f046_r9b_e_jueves_jornada_9_sin_splits():
    p = proponer_dia([_o(1, O678, 5.0), _o(2, O704, 4.0)], 9.0)
    assert p.cuadra and _aj(p) == {} and _cb(p) == []


def test_f046_r9c_e_reajuste_en_viernes():
    p = proponer_dia([
        _o(1, O678, 6.0, fija=True, reaj=True, horas_orig=5.0),
        _e(2, O678, -1.0, fija=True, reaj=True, base_id=1),
        _o(3, O704, 4.0)], 6.0)
    assert _aj(p) == {3: (2.5, 1.5)}
    assert _cb(p) == [(1, 1, "ordinaria", 6.0, 3.5),
                      (2, 1, "extra", -1.0, 1.5)]


# ------------------------------- R1 ------------------------------- #

def test_f046_r1_tipos_y_campos():
    c = CambioCongelada(None, 7, "extra", 0.0, 1.5)
    assert (c.registro_id, c.base_registro_id, c.tipo, c.antes,
            c.despues) == (None, 7, "extra", 0.0, 1.5)
    p = PropuestaDia(True, 0.5, (), (c,))
    with pytest.raises(AttributeError):
        p.cuadra = False  # type: ignore[misc]
    with pytest.raises(AttributeError):
        c.despues = 2.0  # type: ignore[misc]


def test_f046_r1_linea_dia_reajustable_por_defecto_falso():
    assert LineaDia(1, O678, "ordinaria", 8.0).reajustable is False


def test_f046_r1_sin_cambios_si_el_ideal_coincide():
    p = proponer_dia([_o(1, O678, 4.0, fija=True, reaj=True),
                      _o(2, O704, 4.0)], 8.0)
    assert p.cuadra and _cb(p) == [] and _aj(p) == {}


def test_f046_r1_solo_las_libres_dan_ajustes():
    p = proponer_dia([_o(1, O678, 8.0, fija=True, reaj=True),
                      _o(3, O704, 4.0)], 8.0)
    assert set(_aj(p)) == {3}
    assert all(isinstance(a, Ajuste) for a in p.ajustes)


def test_f046_r1_cambios_ordenados_por_base_y_tipo():
    p = proponer_dia([
        _o(5, O704, 8.0, fija=True, reaj=True),
        _o(1, O678, 8.0, fija=True, reaj=True),
        _o(9, 999, 4.0)], 8.0)
    assert [(c.base_registro_id, c.tipo) for c in p.cambios] == [
        (1, "ordinaria"), (1, "extra"), (5, "ordinaria"), (5, "extra")]


def test_f046_r1_extra_nueva_solo_si_no_es_cero():
    """Base reajustable partida (trabajo 6, ordinaria 5) sin su extra en el
    grupo: el ideal le da 6 de ordinaria y la extra sale 0, asi que cambia
    la ordinaria y NO nace extra nueva."""
    p = proponer_dia([_o(1, O678, 5.0, fija=True, reaj=True,
                         horas_orig=6.0),
                      _o(2, O704, 2.0)], 8.0)
    assert _cb(p) == [(1, 1, "ordinaria", 5.0, 6.0)]


# ------------------------------- R3 ------------------------------- #

def test_f046_r3_extra_explicita_reajustable_no_cambia_pero_pesa():
    p = proponer_dia([_o(1, O678, 4.0, fija=True, reaj=True),
                      _e(2, O678, 2.0, fija=True, reaj=True,
                         extra_auto=False),
                      _o(3, O704, 6.0)], 8.0)
    assert all(c.registro_id != 2 for c in p.cambios)
    # 0678 pesa 4 + 2 = 6 y 0704 6: 4 h cada una.
    assert _aj(p) == {3: (4.0, 2.0)}
    assert _cb(p) == []


def test_f046_r3_dura_ni_cambia_ni_pesa_y_cuenta():
    p = proponer_dia([_o(1, O678, 3.0, fija=True),       # dura (encolada)
                      _o(2, O704, 4.0, fija=True, reaj=True),
                      _o(3, 999, 4.0)], 8.0)
    # J' = 8 - 3 = 5 entre 704 (4) y 999 (4): 2,5 y 2,5.
    assert _cb(p) == [(2, 2, "ordinaria", 4.0, 2.5),
                      (None, 2, "extra", 0.0, 1.5)]
    assert _aj(p) == {3: (2.5, 1.5)}


def test_f046_r3_pareja_con_dos_extras_automaticas_es_dura():
    p = proponer_dia([
        _o(1, O678, 8.0, fija=True, reaj=True, horas_orig=4.0),
        _e(2, O678, -4.0, fija=True, reaj=True, base_id=1),
        _e(4, O678, 0.0, fija=True, reaj=True, base_id=1),
        _o(3, O704, 8.0)], 8.0)
    assert _cb(p) == []
    assert _aj(p) == {3: (0.0, 8.0)}


def test_f046_r3_pareja_con_un_miembro_duro_es_dura_entera():
    """Base registrada y su extra encolada: la pareja no se toca."""
    p = proponer_dia([
        _o(1, O678, 8.0, fija=True, reaj=True, horas_orig=4.0),
        _e(2, O678, -4.0, fija=True, base_id=1),           # dura
        _o(3, O704, 8.0)], 8.0)
    assert _cb(p) == []


def test_f046_r3_ordinaria_reajustable_sin_trabajo_es_dura():
    p = proponer_dia([_o(1, O678, 0.0, fija=True, reaj=True),
                      _o(3, O704, 10.0)], 8.0)
    assert _cb(p) == [] and _aj(p) == {3: (8.0, 2.0)}


def test_f046_r3_extra_automatica_huerfana_no_cambia():
    p = proponer_dia([_e(2, O678, -1.0, fija=True, reaj=True, base_id=77),
                      _o(1, O678, 8.0, fija=True, reaj=True),
                      _o(3, O704, 4.0)], 8.0)
    assert all(c.registro_id != 2 for c in p.cambios)


# ------------------------------- R4 ------------------------------- #

def test_f046_r4_si_no_cuadra_con_las_duras_no_hay_nada():
    p = proponer_dia([_o(1, O678, 10.0, fija=True),         # dura
                      _o(2, O704, 4.0, fija=True, reaj=True),
                      _o(3, 999, 4.0)], 8.0)
    assert p.cuadra is False
    assert p.ajustes == () and p.cambios == ()


def test_f046_r4_dia_no_laborable_todo_a_extra():
    p = proponer_dia([_o(1, O678, 8.0, fija=True, reaj=True),
                      _o(3, O704, 4.0)], 0.0)
    assert _aj(p) == {3: (0.0, 4.0)}
    assert _cb(p) == [(1, 1, "ordinaria", 8.0, 0.0),
                      (None, 1, "extra", 0.0, 8.0)]


# ---------------------------- R2 (propiedades) ---------------------------- #

def _sin_duras(semilla: int):
    """Un dia sin duras: libres, reajustables sueltas y parejas
    reajustables (base + una extra automatica)."""
    rnd = random.Random(semilla)
    lineas: list[LineaDia] = []
    rid = 1
    for obra in rnd.sample([O678, O704, 900, 901], rnd.randint(1, 3)):
        for _ in range(rnd.randint(1, 2)):
            horas = rnd.choice([1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0])
            clase = rnd.choice(["libre", "suelta", "pareja"])
            if clase == "libre":
                lineas.append(_o(rid, obra, horas))
                rid += 1
            elif clase == "suelta":
                lineas.append(_o(rid, obra, horas, fija=True, reaj=True))
                rid += 1
            else:
                corte = rnd.choice([0.5, 1.0, 2.0, 4.0])
                lineas.append(_o(rid, obra, corte, fija=True, reaj=True,
                                 horas_orig=horas))
                lineas.append(_e(rid + 1, obra, round(horas - corte, 2),
                                 fija=True, reaj=True, base_id=rid))
                rid += 2
    return lineas


@pytest.mark.parametrize("semilla", range(300))
def test_f046_r2_sin_duras_los_cambios_son_los_de_diferencias_ideal(semilla):
    lineas = _sin_duras(semilla)
    jornada = random.Random(semilla).choice([0.0, 6.0, 8.0, 9.0])
    p = proponer_dia(lineas, jornada)
    existentes = {(c.registro_id, c.antes, c.despues) for c in p.cambios
                  if c.registro_id is not None}
    assert existentes == set(diferencias_ideal(lineas, jornada))


@pytest.mark.parametrize("semilla", range(300))
def test_f046_r1_propiedad_el_dia_suma_la_jornada(semilla):
    lineas = _sin_duras(semilla)
    jornada = random.Random(semilla + 1).choice([6.0, 8.0, 9.0])
    p = proponer_dia(lineas, jornada)
    if not p.cuadra:
        return
    ordinarias = {ln.registro_id: ln.horas for ln in lineas
                  if ln.tipo == "ordinaria"}
    for a in p.ajustes:
        ordinarias[a.registro_id] = a.horas_norm
    for c in p.cambios:
        if c.tipo == "ordinaria":
            ordinarias[c.registro_id] = c.despues
    assert sum(ordinarias.values()) == pytest.approx(jornada, abs=1e-9)
    # Lo trabajado de cada pareja se conserva: ordinaria + extra.
    for base in (ln for ln in lineas if ln.tipo == "ordinaria" and ln.fija):
        trabajado = base.horas_orig if base.horas_orig is not None \
            else base.horas
        extra = next((c.despues for c in p.cambios
                      if c.base_registro_id == base.registro_id
                      and c.tipo == "extra"), None)
        if extra is None:
            extra = sum(ln.horas for ln in lineas
                        if ln.base_id == base.registro_id)
        assert ordinarias[base.registro_id] + extra == pytest.approx(
            trabajado, abs=1e-9)


def test_f046_r2_sin_congeladas_es_repartir_dia():
    for horas in itertools.product([2.0, 4.0, 6.5, 10.0], repeat=2):
        lineas = [_o(1, O678, horas[0]), _o(2, O704, horas[1])]
        p = proponer_dia(lineas, 8.0)
        r = repartir_dia(lineas, 8.0)
        assert (p.cuadra, p.paso, p.ajustes, p.cambios) == (
            r.cuadra, r.paso, r.ajustes, ())


def test_f046_r2_las_duras_igual_que_las_fijas_de_repartir_dia():
    """Con todas las congeladas duras, los ajustes son los de F-045."""
    lineas = [_o(1, O678, 8.0, fija=True, horas_orig=4.0),
              _e(2, O678, -4.0, fija=True, base_id=1),
              _o(3, O704, 6.0), _o(4, 999, 3.0)]
    p, r = proponer_dia(lineas, 8.0), repartir_dia(lineas, 8.0)
    assert (p.cuadra, p.ajustes, p.cambios) == (r.cuadra, r.ajustes, ())


# ------------------------------- R5 ------------------------------- #

def test_f046_r5_el_modulo_sigue_siendo_puro():
    arbol = ast.parse(Path(modulo.__file__).read_text(encoding="utf-8"))
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")
    prohibidos = ("infrastructure", "sqlalchemy", "httpx", "requests",
                  "socket", "jornada_resolver")
    assert not any(p in m for m in importados for p in prohibidos), importados
