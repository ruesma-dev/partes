# tests/test_f015_r15_calendario_no_registros.py
"""R15 · quien decide el ultimo laborable es el CALENDARIO, no la BBDD.

La tentacion era mirar los registros ("el ultimo dia con horas de la
semana"). Seria un error: una ausencia, una incidencia, un parte que solo
llega hasta el miercoles o una semana partida entre dos meses cambiarian
el reparto de un dia a otro segun QUE se haya persistido todavia, y el
mismo dia daria dos resultados distintos en dos pasadas.

La firma del resolutor ya lo impide (no recibe registros); estos tests lo
fijan como propiedad observable, tambien en el conciliador de sv3.
"""
from __future__ import annotations

import inspect
from datetime import date

from application.services import jornada_resolver
from application.services.jornada_resolver import jornada_dia
from tests.dobles import es_laborable_fake

MAPA = {8.0: 40.0, 9.0: 42.0}

LUNES = date(2026, 3, 16)
JUEVES = date(2026, 3, 19)
VIERNES = date(2026, 3, 20)

# Semana partida entre dos meses: 2026-06-29 (L) ... 2026-07-03 (V).
L_JUNIO = date(2026, 6, 29)
M_JUNIO = date(2026, 6, 30)
X_JULIO = date(2026, 7, 1)
V_JULIO = date(2026, 7, 3)


def _jornada(d, no_laborables=()):
    return jornada_dia(d, candef=9.0, minimo=2.0, por_defecto=8.0,
                       mapa=MAPA, es_laborable=es_laborable_fake(no_laborables))


# ------------------------- la firma no admite datos --------------------- #

def test_f015_r15_el_resolutor_no_recibe_registros_ni_repositorio() -> None:
    """Funcion pura: solo fecha, candef, mapa, calendario y excepcion."""
    parametros = set(inspect.signature(jornada_resolver.jornada_dia)
                     .parameters)
    assert parametros == {
        "d", "candef", "minimo", "por_defecto", "mapa", "es_laborable",
        "excepcion",
    }


def test_f015_r15_el_resolutor_no_importa_nada_de_infraestructura() -> None:
    fuente = inspect.getsource(jornada_resolver)
    for prohibido in ("sqlalchemy", "requests", "httpx", "session",
                      "repository", "logging"):
        assert prohibido not in fuente.lower(), (
            f"el resolutor tiene que seguir siendo puro: aparece {prohibido!r}"
        )


# ----------------------- misma semana, mismos numeros ------------------- #

def test_f015_r15_una_ausencia_el_viernes_no_mueve_el_resto() -> None:
    """Escenario I: el viernes sigue siendo el ultimo laborable aunque no
    tenga horas; el jueves NO recibe el resto."""
    assert _jornada(JUEVES) == 9.0
    assert _jornada(VIERNES) == 6.0


def test_f015_r15_un_parte_que_solo_llega_al_martes_no_cambia_nada() -> None:
    """Escenario H: la jornada del lunes es la misma se hayan persistido o
    no los dias siguientes (el resolutor ni los ve)."""
    assert _jornada(LUNES) == 9.0


# --------------------- semana partida entre dos meses ------------------- #

def test_f015_r15_semana_partida_entre_meses_se_resuelve_igual() -> None:
    """Escenario G: 30/06 y 01/07 son de la MISMA semana; el resto cae el
    viernes 03/07, este ese dia en el mismo parte o en otro."""
    assert _jornada(M_JUNIO) == 9.0
    assert _jornada(X_JULIO) == 9.0
    assert _jornada(V_JULIO) == 6.0
    assert _jornada(L_JUNIO) == 9.0


def test_f015_r15_el_ultimo_de_junio_no_es_ultimo_laborable_por_ser_fin_de_mes(
) -> None:
    """El mes no pinta nada: la unidad es la SEMANA (lunes a domingo)."""
    assert _jornada(M_JUNIO) != 6.0


# ------------------- lo mismo, ya dentro del conciliador ---------------- #

def _splits(regs, *, candef=9.0, no_laborables=()):
    from application.services.recurso_conciliador import RecursoConciliador
    from tests.dobles import (
        CalendarioFake,
        LookupFake,
        RepositorioFake,
        indice_reshor,
    )

    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set(no_laborables)),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


def _resumen(splits):
    return sorted((s["normal_id"], s["horas_norm"], s["extra_horas"])
                  for s in splits)


def test_f015_r15_el_viernes_da_lo_mismo_con_y_sin_el_jueves() -> None:
    """Escenario I: que el jueves este o no persistido no toca el viernes."""
    from tests.dobles import registro

    solo_viernes = [registro(2, fecha_int=20260320, horas=4.0)]
    con_jueves = [registro(1, fecha_int=20260319, horas=9.0),
                  registro(2, fecha_int=20260320, horas=4.0)]
    del_viernes = [s for s in _splits(con_jueves) if s["normal_id"] == 2]
    assert _resumen(_splits(solo_viernes)) == _resumen(del_viernes)


def test_f015_r15_dos_partes_distintos_dan_lo_mismo_que_uno() -> None:
    """Escenario G: 30/06 y 01/07 son de la misma semana aunque lleguen en
    partes distintos y en meses distintos."""
    from tests.dobles import registro

    juntos = [registro(1, fecha_int=20260630, horas=4.0, document_id="doc-a"),
              registro(2, fecha_int=20260701, horas=4.0, document_id="doc-b")]
    por_separado = (
        _splits([juntos[0]]) + _splits([juntos[1]])
    )
    assert _resumen(_splits(juntos)) == _resumen(por_separado)


def test_f015_r15_un_viernes_de_incidencia_no_pasa_el_resto_al_jueves() -> None:
    """El viernes sigue siendo el ultimo laborable aunque no tenga horas."""
    from tests.dobles import registro

    regs = [registro(1, fecha_int=20260319, horas=9.0)]
    assert _splits(regs) == []
