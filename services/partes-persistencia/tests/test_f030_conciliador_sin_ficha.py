# tests/test_f030_conciliador_sin_ficha.py
"""F-030 · R14-R15: el conciliador de sv3 con una linea casada por recurso.

Tests de CARACTERIZACION (T1): pasan contra el codigo de hoy, sin tocar
`recurso_conciliador.py`. Una linea casada contra una «ficha de recurso»
(recurso `MO/` con `res.cif` y sin ficha `emp`) llega con `empleado_ide`
NULL, `empleado_dni` = `res.cif` y `empleado_reside` = `res.ide`. El
conciliador ya resuelve su recurso por `res.cif` (F-023 R25-R29): lo
asigna, deja `ok`/`sin_parte`, pisa categoria y hora con ese recurso y lo
mete en el reparto de extras con el `candef` de su ficha de horas y el
calendario pedido con su DNI.

Todo SINTETICO; el indice llega por `indice_provider`, como en produccion.
"""
from __future__ import annotations

from datetime import date

from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import HmoRow, ObraRow, RecursoRow
from tests.dobles import (
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    registro,
    reshor_par,
)

CIF = "09876543B"            # DNI de la persona SIN ficha de empleado
FECHA = 20260915             # martes
OBRA_28 = ObraRow(ide=724, codigo="0724", nombre="Obra Porsan", empresa=28)
OBRA_1 = ObraRow(ide=725, codigo="0724", nombre="Obra Ruesma", empresa=1)

#: La ficha de recurso de la 28: `MO/`, `cif` y `conide` vacio.
REC_28 = RecursoRow(ide=950, cif=CIF, conide=None, restip_res="PEON",
                    horide_def=100, empresa=28, fecbaj=0)
#: Otro recurso de la misma persona en la empresa 1 (no compite en la 28).
REC_1 = RecursoRow(ide=951, cif=CIF, conide=None, restip_res="OFICIAL",
                   horide_def=100, empresa=1, fecbaj=0)


def _indice(recursos=(REC_28, REC_1)) -> IndicePersonas:
    return IndicePersonas([], recursos, [OBRA_28, OBRA_1])


def _linea(rid=1, *, metodo="recurso_dni", obra_ide=724, horas=8.0,
           fecha=FECHA, **extra) -> dict:
    r = registro(rid, fecha_int=fecha, horas=horas, dni=CIF,
                 obra_ide=obra_ide)
    r.update(empleado_ide=None, empleado_reside=950,
             empleado_match_method=metodo, hora_ide=None, **extra)
    return r


def _conciliador(repo, indice=None, *, hmo=None, candef=8.0,
                 calendario=None) -> RecursoConciliador:
    indice = indice or _indice()
    return RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(950, candef=candef)
                          + reshor_par(951), hmo=hmo or {}),
        indice_provider=lambda: indice,
        calendario=calendario,
        hoy=lambda: date(2026, 9, 15),
    )


def _update(repo, rid) -> dict:
    return next(u for u in repo.matches if u["registro_id"] == rid)


# ============================ R14 · el recurso ========================== #

def test_f030_r14_linea_recurso_dni_con_parte_queda_ok_en_su_recurso() -> None:
    repo = RepositorioFake([_linea()])
    hmo = {724: [HmoRow(ide=7001, reside=950, ano=2026, mes=9)]}
    _conciliador(repo, hmo=hmo).conciliar_todos()
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["recurso_cif"], u["hmo_ide"],
            u["parte_estado"]) == (950, CIF, 7001, "ok")
    # Pisa categoria y hora con las del recurso, como con ficha.
    assert (u["categoria"], u["hora_ide"], u["hora_codigo"],
            u["hora_candef"]) == ("PEON", 100, "HL01", 8.0)
    assert repo.review_required == []


def test_f030_r14_linea_recurso_nombre_sin_parte_queda_sin_parte() -> None:
    repo = RepositorioFake([_linea(metodo="recurso_nombre")])
    _conciliador(repo).conciliar_todos()
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["hmo_ide"], u["parte_estado"]) == \
        (950, None, "sin_parte")


def test_f030_r14_la_empresa_de_la_obra_elige_entre_sus_recursos() -> None:
    """El mismo `cif` en la 1 y en la 28: la obra de la 1 se queda con el
    de la 1 y la de la 28 con el de la 28."""
    repo = RepositorioFake([_linea(1), _linea(2, obra_ide=725)])
    _conciliador(repo).conciliar_todos()
    assert _update(repo, 1)["recurso_ide"] == 950
    assert _update(repo, 2)["recurso_ide"] == 951


def test_f030_r14_recurso_de_baja_a_la_fecha_queda_sin_recurso() -> None:
    baja = RecursoRow(ide=950, cif=CIF, conide=None, empresa=28,
                      fecbaj=FECHA)
    repo = RepositorioFake([_linea()])
    _conciliador(repo, _indice(recursos=(baja,))).conciliar_todos()
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["parte_estado"]) == (None, "sin_recurso")
    assert repo.review_required == [["doc-1"]]


def test_f030_r14_linea_congelada_no_cambia_de_recurso() -> None:
    repo = RepositorioFake([_linea(1, recurso_ide=950,
                                   sigrid_estado="registrado"),
                            _linea(2)])
    _conciliador(repo).conciliar_todos()
    assert [u["registro_id"] for u in repo.matches] == [2]


# ===================== R15 · extras por jornada ========================= #

def test_f030_r15_el_candef_sale_de_la_ficha_de_horas_del_recurso() -> None:
    """10 h un martes con candef 9 del recurso: 1 h pasa a extra."""
    repo = RepositorioFake([_linea(horas=10.0)])
    _conciliador(repo, candef=9.0).conciliar_todos()
    (split,) = repo.splits
    assert (split["normal_id"], split["horas_norm"], split["extra_horas"]) \
        == (1, 9.0, 1.0)
    assert split["hora_candef"] == 9.0


def test_f030_r15_el_calendario_se_pide_con_el_dni_de_la_linea() -> None:
    """Festivo para ESE DNI: todo lo ordinario pasa a extra."""
    calendario = CalendarioFake({CIF: {"2026-09-15"}})
    repo = RepositorioFake([_linea(horas=8.0)])
    _conciliador(repo, calendario=calendario).conciliar_todos()
    assert ("2026-09-15", CIF) in calendario.consultas
    (split,) = repo.splits
    assert (split["horas_norm"], split["extra_horas"]) == (0.0, 8.0)
