# tests/test_f048_conciliar.py
"""F-048 · el registro sumado se reparte como cualquier ordinaria (R8-R18).

Ciclo completo sin red ni PostgreSQL: JSON de sv2 sintetico =>
`ParteNormalizer` => `save_parte` => `RecursoConciliador.conciliar_todos`
con el repositorio REAL sobre SQLite en memoria y los dobles de
`tests/dobles.py` (calendario, lookup y `reshor` del recurso 501). El
conciliador, `reparto_ponderado.py` y la jornada de F-015 no cambian: estos
tests demuestran que la suma en la ingesta basta (design §6, DA2 opcion A).

Semana del lunes 2026-03-16 al domingo 2026-03-22 (sabado y domingo no
laborables). Candef 8 => J = 8 de lunes a viernes; candef 9 => J = 9 de
lunes a jueves y 6 el ultimo laborable (F-015). «a + b» = `normal` a +
`extra_auto` b. Peticion del humano (2026-10-15): «por dia solo hay una
fila de extras y otra de ordinarias»: los casos 1, 2 y 4 + 2 dejan
EXACTAMENTE dos lineas activas.
"""
from __future__ import annotations

import pytest
from application.services.parte_normalizer import ParteNormalizer
from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import ResolucionRecurso
from domain.models.parte_records import EmpleadoMatch, ObraMatch
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from sqlalchemy import select
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    reshor_par,
    sembrar_lineas,
)

RECURSO = 501
DNI = "12345678Z"          # el sintetico de `dobles`
JUEVES = "19/03/2026"
VIERNES = "20/03/2026"
SABADO = "21/03/2026"
FINDE = {"2026-03-21", "2026-03-22"}


class IndiceFijo:
    """Siempre el recurso 501 (como en los tests de F-037 y F-045)."""

    recursos: tuple = ()

    def empresa_de_obra(self, obra_ide):
        return None

    def elegir_recurso(self, *args, **kwargs):
        return ResolucionRecurso(ide=RECURSO, motivo="ok")


def _fila(ordinarias=None, extras=None, **extra) -> dict:
    fila = {"nombre": "Persona Uno", "numero_linea": 1,
            "horas_ordinarias": ordinarias,
            "horas_extraordinarias": extras,
            "codigo_hora_ordinaria": "HL01", "codigo_hora_extra": "HE01"}
    fila.update(extra)
    return fila


def _ingerir(fabrica, *filas: dict, fecha: str = JUEVES, obra_ide: int = 10,
             document_id: str = "doc-a") -> None:
    """Lo que hace sv3 con un parte: normalizar, casar (aqui, a mano: el
    trabajador sintetico) y guardar."""
    parte = ParteNormalizer().normalize(
        {"cabecera": {"fecha": fecha, "obra_numero": str(obra_ide)},
         "empleados": list(filas)}, email_text="marzo 2026")
    parte.obra = ObraMatch(ide=obra_ide, codigo=f"{obra_ide:04d}",
                           method="codigo")
    for reg in parte.registros:
        reg.empleado = EmpleadoMatch(ide=1, codigo="E1", dni=DNI,
                                     reside=RECURSO, method="dni")
    SqlAlchemyParteRepository(fabrica).save_parte(  # type: ignore[arg-type]
        document_id=document_id, parte=parte, meta={}, context={},
        raw_extraction_json="{}", raw_context_json="{}",
        review_required=False)


def _conciliar(fabrica, *, candef: float = 8.0, festivos=()) -> dict:
    return RecursoConciliador(
        repository=SqlAlchemyParteRepository(fabrica),  # type: ignore[arg-type]
        lookup=LookupFake(reshor=reshor_par(RECURSO, candef=candef)),
        calendario=CalendarioFake(FINDE | set(festivos)),
        indice_provider=lambda: IndiceFijo(),
    ).conciliar_todos()


def _lineas(fabrica, document_id: str = "doc-a") -> list[tuple]:
    """(tipo, horas, horas_orig, horas_extra_leidas, extra_auto) de las
    lineas ACTIVAS del parte, base antes que su extra automatica."""
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.tipo_hora, ParteRegistroOrm.horas,
                   ParteRegistroOrm.horas_orig,
                   ParteRegistroOrm.horas_extra_leidas,
                   ParteRegistroOrm.extra_auto)
            .where(ParteRegistroOrm.document_id == document_id,
                   ParteRegistroOrm.deleted_at_utc.is_(None))
            .order_by(ParteRegistroOrm.line_index,
                      ParteRegistroOrm.extra_auto)).all()
    return [tuple(f) for f in filas]


def _simple(fabrica, document_id: str = "doc-a") -> list[tuple]:
    """Solo (tipo, horas, extra_auto)."""
    return [(t, h, a) for t, h, _, _, a in _lineas(fabrica, document_id)]


def _caso(*filas, fecha=JUEVES, candef=8.0, festivos=()) -> list[tuple]:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, *filas, fecha=fecha)
    _conciliar(fabrica, candef=candef, festivos=festivos)
    return _simple(fabrica)


def _dos(normal: float, extra: float | None = None) -> list[tuple]:
    out = [("normal", normal, False)]
    if extra is not None:
        out.append(("extra", extra, True))
    return out


# ------------------------------ casos reales ---------------------------- #

def test_f048_r9_caso_1_solo_10_extras_da_8_mas_2() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(None, 10), fecha=JUEVES)
    _conciliar(fabrica)
    assert _lineas(fabrica) == [("normal", 8.0, 10.0, 10.0, False),
                                ("extra", 2.0, None, None, True)]


def test_f048_r10_caso_2_cuatro_mas_cinco_da_8_mas_1() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(4, 5), fecha=VIERNES)
    _conciliar(fabrica)
    assert _lineas(fabrica) == [("normal", 8.0, 9.0, 5.0, False),
                                ("extra", 1.0, None, None, True)]


@pytest.mark.parametrize(("ordinarias", "extras", "esperado"), [
    (None, 10, (8.0, 2.0)),
    (4, 5, (8.0, 1.0)),
    (4, 2, (8.0, -2.0)),
], ids=["caso-1", "caso-2", "4+2"])
def test_f048_r9_r11_exactamente_dos_lineas_una_normal_y_una_extra_auto(
        ordinarias, extras, esperado) -> None:
    """Peticion del humano: por dia, una fila de ordinarias y otra de
    extras; nunca tres lineas (como el 8 + (-4) + 5 de hoy)."""
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(ordinarias, extras), fecha=VIERNES)
    _conciliar(fabrica)
    lineas = _lineas(fabrica)
    assert len(lineas) == 2
    (normal, extra) = lineas
    assert (normal[0], normal[4]) == ("normal", False)
    assert (extra[0], extra[4]) == ("extra", True)
    assert (normal[1], extra[1]) == esperado
    assert sum(1 for t, *_, auto in lineas if t == "extra" and not auto) == 0


# ------------------------------ R11 y R12 ------------------------------- #

def test_f048_r11_no_llega_cuatro_mas_dos_da_8_menos_2() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(4, 2))
    _conciliar(fabrica)
    assert _lineas(fabrica) == [("normal", 8.0, 6.0, 2.0, False),
                                ("extra", -2.0, None, None, True)]


def test_f048_r11_solo_6_extras_da_8_menos_2_sin_umbral() -> None:
    """DA4: sin umbral, como 6 ordinarias hoy."""
    assert _caso(_fila(None, 6)) == _dos(8.0, -2.0)


def test_f048_r12_justo_la_jornada_sin_split() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(6, 2))
    _conciliar(fabrica)
    assert _lineas(fabrica) == [("normal", 8.0, None, 2.0, False)]


def test_f048_r12_solo_8_extras_sin_split() -> None:
    assert _caso(_fila(None, 8)) == _dos(8.0)


# --------------------------------- R13 ---------------------------------- #

@pytest.mark.parametrize(("fecha", "fila", "esperado"), [
    (VIERNES, _fila(4, 5), _dos(6.0, 3.0)),
    (VIERNES, _fila(None, 10), _dos(6.0, 4.0)),
    (JUEVES, _fila(4, 5), _dos(9.0)),
    (JUEVES, _fila(None, 10), _dos(9.0, 1.0)),
], ids=["viernes-4+5", "viernes-solo-10", "jueves-4+5", "jueves-solo-10"])
def test_f048_r13_candef_9(fecha, fila, esperado) -> None:
    assert _caso(fila, fecha=fecha, candef=9.0) == esperado


def test_f048_r13_candef_9_viernes_festivo() -> None:
    """Viernes festivo: el jueves es el ultimo laborable (J 6) y el viernes
    va todo a extra."""
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(4, 5), fecha=JUEVES, document_id="doc-a")
    _ingerir(fabrica, _fila(None, 10), fecha=VIERNES, document_id="doc-b")
    _conciliar(fabrica, candef=9.0, festivos={"2026-03-20"})
    assert _simple(fabrica, "doc-a") == _dos(6.0, 3.0)
    assert _simple(fabrica, "doc-b") == _dos(0.0, 10.0)


# --------------------------------- R14 ---------------------------------- #

def test_f048_r14_sabado_cuatro_mas_cinco_todo_a_extra() -> None:
    """DA3: mismos importes que hoy (0 + 4 + 5 explicita), una linea menos."""
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(4, 5), fecha=SABADO)
    _conciliar(fabrica)
    assert _lineas(fabrica) == [("normal", 0.0, 9.0, 5.0, False),
                                ("extra", 9.0, None, None, True)]


def test_f048_r14_sabado_solo_10() -> None:
    assert _caso(_fila(None, 10), fecha=SABADO) == _dos(0.0, 10.0)


# ---------------------------- R15 a R17 (F-045) ------------------------- #

def _dos_obras(fila_a: dict, fila_b: dict):
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, fila_a, obra_ide=10, document_id="doc-a")
    _ingerir(fabrica, fila_b, obra_ide=20, document_id="doc-b")
    _conciliar(fabrica)
    return _simple(fabrica, "doc-a"), _simple(fabrica, "doc-b")


def test_f048_r15_dos_obras_cuatro_mas_cinco_y_tres() -> None:
    assert _dos_obras(_fila(4, 5), _fila(3, None)) == (
        _dos(6.0, 3.0), _dos(2.0, 1.0))


def test_f048_r16_dos_obras_solo_extras() -> None:
    assert _dos_obras(_fila(None, 6), _fila(None, 4)) == (
        _dos(5.0, 1.0), _dos(3.0, 1.0))


def test_f048_r17_mixto_ordinarias_y_solo_extras() -> None:
    """DA5: la fila solo extra pesa y recibe jornada."""
    assert _dos_obras(_fila(8, None), _fila(None, 2)) == (
        _dos(6.5, 1.5), _dos(1.5, 0.5))


# --------------------------------- R18 ---------------------------------- #

def test_f048_r18_congelada_fija_y_el_sumado_recibe_lo_que_queda() -> None:
    """La obra 30 ya esta en Sigrid con 4 ordinarias: queda fija y el
    registro sumado (solo 10 extras) recibe J - 4 = 4 (modo residual)."""
    fabrica = FabricaSesionSqlite()
    (congelada,) = sembrar_lineas(
        fabrica, [{"horas": 4.0, "estado": "registrado",
                   "recurso_ide": RECURSO}],
        document_id="doc-c", obra_ide=30, fecha="2026-03-19")
    _ingerir(fabrica, _fila(None, 10))
    _conciliar(fabrica)
    assert _simple(fabrica, "doc-c") == [("normal", 4.0, False)]
    assert _lineas(fabrica) == [("normal", 4.0, 10.0, 10.0, False),
                                ("extra", 6.0, None, None, True)]
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, congelada).horas == 4.0


# ------------------------------ estabilidad ----------------------------- #

def test_f048_r8_dos_pasadas_dan_lo_mismo() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(4, 5))
    _conciliar(fabrica)
    primera = _lineas(fabrica)
    _conciliar(fabrica)
    assert _lineas(fabrica) == primera == [
        ("normal", 8.0, 9.0, 5.0, False), ("extra", 1.0, None, None, True)]


def test_f048_r8_la_extra_auto_nace_con_horas_extra_leidas_nula() -> None:
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(None, 10))
    _conciliar(fabrica)
    with fabrica.create_session() as s:
        autos = s.execute(select(ParteRegistroOrm.horas_extra_leidas)
                          .where(ParteRegistroOrm.extra_auto.is_(True))
                          ).scalars().all()
    assert autos == [None]


def test_f048_r3_extra_negativa_leida_sigue_explicita() -> None:
    """DA8: 10 ordinarias y -2 extras leidas: la -2 no se suma."""
    fabrica = FabricaSesionSqlite()
    _ingerir(fabrica, _fila(10, -2))
    _conciliar(fabrica)
    tipos = [(t, a, leidas) for t, _, _, leidas, a in _lineas(fabrica)]
    assert ("extra", False, None) in tipos
    assert all(leidas is None for _, _, leidas in tipos)
