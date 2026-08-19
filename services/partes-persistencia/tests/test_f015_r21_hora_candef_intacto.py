# tests/test_f015_r21_hora_candef_intacto.py
"""R21 · `hora_candef` sigue siendo el candef REAL de Sigrid.

`parte_registros.hora_candef` es un dato de DIAGNOSTICO: dice que tenia
Sigrid en la hora por defecto del recurso cuando se concilio, y por eso
puede valer 0 o NULL. F-015 introduce dos numeros nuevos (el candef
efectivo y la jornada del dia) y la tentacion era guardar alguno de ellos
ahi: seria perder el unico rastro de lo que decia el ERP.

Ademas, F-015 no anade ni una columna a `parte_registros` (la huella de
56 columnas del guardian de F-010 no se mueve).
"""
from __future__ import annotations

import pytest
from application.services.recurso_conciliador import RecursoConciliador
from infrastructure.database.orm_models import Base
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
)

VIERNES = 20260320


def _splits(regs, *, candef):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()), jornada_ordinaria_horas=8.0,
        candef_minimo=2.0,
    )
    return conciliador._reclasificar_extras_jornada(
        regs, {r["registro_id"]: 501 for r in regs},
        indice_reshor(501, candef=candef),
    )


@pytest.mark.parametrize("candef", [None, 0.0, 1.0, 2.0, 9.0, 10.0])
def test_f015_r21_el_split_guarda_el_candef_crudo(candef) -> None:
    """Sea cual sea la jornada del dia aplicada, `hora_candef` es el de Sigrid."""
    splits = _splits([registro(1, fecha_int=VIERNES, horas=1.0)],
                     candef=candef)
    assert splits, "el caso deberia producir split"
    assert all(s["hora_candef"] == candef for s in splits)


def test_f015_r21_el_candef_crudo_no_es_ni_el_efectivo_ni_la_jornada() -> None:
    """Con candef 0 se calcula con 8, pero se persiste 0."""
    splits = _splits([registro(1, fecha_int=VIERNES, horas=6.0)], candef=0.0)
    assert splits[0]["hora_candef"] == 0.0
    assert splits[0]["horas_norm"] == 8.0


def test_f015_r21_con_candef_9_el_viernes_persiste_9_y_calcula_6() -> None:
    splits = _splits([registro(1, fecha_int=VIERNES, horas=4.0)], candef=9.0)
    assert splits[0]["hora_candef"] == 9.0
    assert splits[0]["horas_norm"] == 6.0


def test_f015_r21_las_claves_del_split_no_cambian() -> None:
    """El repositorio (`apply_extras_splits`) espera EXACTAMENTE estas."""
    splits = _splits([registro(1, fecha_int=VIERNES, horas=9.0)], candef=9.0)
    assert set(splits[0]) == {
        "normal_id", "horas_norm", "horas_orig", "extra_horas",
        "hora_ext_ide", "hora_ext_cod", "hora_ext_desc", "hora_ext_ext",
        "hora_candef",
    }


def test_f015_r21_parte_registros_sigue_teniendo_56_columnas() -> None:
    assert len(Base.metadata.tables["parte_registros"].columns) == 56
