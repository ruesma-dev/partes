# tests/test_f015_r23_degradado_review.py
"""R23 · el calendario degradado que decide el ultimo laborable marca el parte.

F-003 (R26) ya dejaba `review_required` en los partes cuyo computo se hizo
con el calendario a ciegas. F-015 hace que el calendario decida MAS cosas:
para saber si un dia es el ultimo laborable de su semana se consultan
tambien los dias siguientes. Si alguna de esas consultas salio del
respaldo o de la cache caducada, el reparto de horas puede estar mal y el
parte tiene que quedar senalado igual que antes.

Lo que NO se hace es inventar un tercer regimen de resiliencia: es la
misma senal (`consumir_degradacion`), el mismo acumulador y el mismo
`marcar_review_required` de F-003.
"""
from __future__ import annotations

from application.services.recurso_conciliador import RecursoConciliador
from tests.dobles import (
    CalendarioFake,
    CalendarioSinSenal,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

LUNES = 20260316
JUEVES = 20260319
VIERNES = 20260320


def _conciliador(calendario):
    return RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=calendario, jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )


def _degradados(calendario, regs, *, candef=9.0):
    conciliador = _conciliador(calendario)
    conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )
    return conciliador._docs_degradados


def test_f015_r23_un_viernes_degradado_marca_el_parte_del_jueves() -> None:
    """El jueves se calcula mirando si el viernes es laborable: si ESA
    consulta salio degradada, el reparto del jueves tampoco es de fiar."""
    calendario = CalendarioFake(set(), degradados={"2026-03-20"})
    regs = [registro(1, fecha_int=JUEVES, horas=9.0, document_id="doc-7")]
    assert _degradados(calendario, regs) == {"doc-7"}


def test_f015_r23_un_calendario_fiable_no_marca_nada() -> None:
    calendario = CalendarioFake(set())
    regs = [registro(1, fecha_int=JUEVES, horas=9.0, document_id="doc-7")]
    assert _degradados(calendario, regs) == set()


def test_f015_r23_la_degradacion_del_propio_dia_sigue_marcando(
) -> None:
    """El caso de F-003, intacto."""
    calendario = CalendarioFake(set(), degradados={"2026-03-16"})
    regs = [registro(1, fecha_int=LUNES, horas=9.0, document_id="doc-7")]
    assert _degradados(calendario, regs) == {"doc-7"}


def test_f015_r23_solo_se_consulta_hasta_el_primer_laborable_posterior(
) -> None:
    """El lunes no llega a mirar el viernes: en cuanto ve que el martes es
    laborable, ya sabe que no es el ultimo. Menos consultas y menos
    superficie de degradacion."""
    calendario = CalendarioFake(set(), degradados={"2026-03-20"})
    regs = [registro(1, fecha_int=LUNES, horas=9.0, document_id="doc-7")]
    assert _degradados(calendario, regs) == set()


def test_f015_r23_se_marcan_todos_los_partes_del_grupo() -> None:
    calendario = CalendarioFake(set(), degradados={"2026-03-20"})
    regs = [registro(1, fecha_int=JUEVES, horas=5.0, document_id="doc-a"),
            registro(2, fecha_int=JUEVES, horas=5.0, document_id="doc-b")]
    assert _degradados(calendario, regs) == {"doc-a", "doc-b"}


def test_f015_r23_el_marcado_llega_al_repositorio() -> None:
    """`conciliar_todos` cierra el circuito con `marcar_review_required`."""
    repositorio = RepositorioFake([
        registro(1, fecha_int=LUNES, horas=9.0, document_id="doc-7"),
    ])
    conciliador = RecursoConciliador(
        repository=repositorio, lookup=LookupFake(),
        calendario=CalendarioFake(set(), degradados={"2026-03-20"}),
    )
    conciliador._docs_degradados = {"doc-7"}
    assert conciliador._marcar_partes_degradados() == 1
    assert repositorio.review_required == [["doc-7"]]


def test_f015_r23_un_calendario_sin_senal_no_rompe_el_calculo() -> None:
    """El JSON de respaldo no ofrece `consumir_degradacion` (duck-typing)."""
    calendario = CalendarioSinSenal(set())
    regs = [registro(1, fecha_int=VIERNES, horas=6.0)]
    conciliador = _conciliador(calendario)
    assert conciliador._reclasificar_extras_jornada(
        regs, {1: 501}, indice_reshor(501, candef=9.0)) == []
    assert conciliador._docs_degradados == set()


def test_f015_r23_con_candef_8_no_se_consultan_los_dias_siguientes() -> None:
    """Regresion barata (R11): sin regla que aplicar no hay consultas de
    mas, asi que un viernes degradado NO marca el parte del lunes."""
    calendario = CalendarioFake(set(), degradados={"2026-03-20"})
    regs = [registro(1, fecha_int=LUNES, horas=8.0, document_id="doc-7")]
    assert _degradados(calendario, regs, candef=8.0) == set()
