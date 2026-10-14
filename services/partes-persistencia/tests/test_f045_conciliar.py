# tests/test_f045_conciliar.py
"""F-045 · el reparto ponderado dentro de `RecursoConciliador`.

Dos niveles: `_reclasificar_extras_jornada` con dobles en memoria (lo que
no cambia, R20-R21; la papelera, R27; las claves del split, R28; el log,
R30) y `conciliar_todos` con el repositorio REAL sobre SQLite en memoria
(el caso real congelado, R24-R25; dos pasadas seguidas, R29). Todo
sintetico: obras 10, 20 y 30 (o 678/704 para el caso real), recurso 501.
"""
from __future__ import annotations

import logging
import random

from sqlalchemy import select

from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import ResolucionRecurso
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    indice_reshor,
    registro,
    reshor_par,
    sembrar_lineas,
)

RECURSO = 501
LUNES = 20260302          # laborable, jornada 8 (candef 8)
SABADO = 20260307         # no laborable en los dobles
DNI = "12345678Z"         # el sintetico de `dobles.registro`
CLAVES_SPLIT = {
    "normal_id", "horas_norm", "horas_orig", "extra_horas", "hora_ext_ide",
    "hora_ext_cod", "hora_ext_desc", "hora_ext_ext", "hora_candef",
}


def _splits(regs, *, con_extra=True, ride=None):
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake({"2026-03-07", "2026-03-08"}),
        jornada_ordinaria_horas=8.0, candef_minimo=2.0,
    )
    ride_por_reg = ride if ride is not None else {
        r["registro_id"]: RECURSO for r in regs}
    return conciliador._reclasificar_extras_jornada(
        regs, ride_por_reg, indice_reshor(RECURSO, con_extra=con_extra))


def _resumen(splits):
    return sorted((s["normal_id"], s["horas_norm"], s["extra_horas"])
                  for s in splits)


# --------------------------- integracion basica ------------------------- #

def test_f045_r11_el_conciliador_reparte_entre_obras() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=4.0, obra_ide=20,
                     document_id="doc-2")]
    assert _resumen(_splits(regs)) == [(1, 5.5, 4.5), (2, 2.5, 1.5)]


def test_f045_r22_el_conciliador_reparte_el_residuo_de_lo_congelado(
) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=4.0, obra_ide=10,
                     sigrid_estado="registrado"),
            registro(2, fecha_int=LUNES, horas=6.0, obra_ide=20),
            registro(3, fecha_int=LUNES, horas=2.0, obra_ide=30)]
    assert _resumen(_splits(regs)) == [(2, 3.0, 3.0), (3, 1.0, 1.0)]


def test_f045_r28_el_split_tiene_las_claves_de_siempre() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=7.75, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=2.0, obra_ide=20)]
    splits = _splits(regs)
    assert all(set(s) == CLAVES_SPLIT for s in splits)
    assert {(s["hora_ext_ide"], s["hora_ext_cod"], s["hora_candef"])
            for s in splits} == {(200, "HE01", 8.0)}
    assert _resumen(splits) == [(1, 6.25, 1.5), (2, 1.75, 0.25)]
    for s in splits:
        assert (s["horas_norm"] / 0.25).is_integer()
        assert (s["extra_horas"] / 0.25).is_integer()
        assert s["horas_norm"] + s["extra_horas"] == s["horas_orig"]


# ------------------------- lo que no cambia ----------------------------- #

def test_f045_r20_dia_no_laborable_todo_a_extra(caplog) -> None:
    regs = [registro(1, fecha_int=SABADO, horas=6.0, obra_ide=10),
            registro(2, fecha_int=SABADO, horas=4.0, obra_ide=20)]
    with caplog.at_level(logging.INFO):
        assert _resumen(_splits(regs)) == [(1, 0.0, 6.0), (2, 0.0, 4.0)]
    assert "dia NO laborable" in caplog.text


def test_f045_r21_recurso_sin_codigo_extra_no_reparte(caplog) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=4.0, obra_ide=20)]
    assert _splits(regs, con_extra=False) == []


def test_f045_r21_las_incidencias_ni_pesan_ni_restan() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=8.0, obra_ide=20,
                     tipo="Vacaciones(V)")]
    assert _resumen(_splits(regs)) == [(1, 8.0, 2.0)]


def test_f045_r21_laborable_sin_ordinarias_no_se_normaliza() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=4.0, tipo="extra",
                     obra_ide=10),
            registro(2, fecha_int=LUNES, horas=3.0, tipo="extra",
                     obra_ide=20)]
    assert _splits(regs) == []


def test_f045_r21_la_linea_sin_recurso_no_entra_en_el_dia() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=4.0, obra_ide=20)]
    assert _resumen(_splits(regs, ride={1: RECURSO})) == [(1, 8.0, 2.0)]


def test_f045_r26_la_congelada_por_pareja_es_fija() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=8.0, obra_ide=10,
                     congelada_por_pareja=True),
            registro(2, fecha_int=LUNES, horas=2.0, obra_ide=20)]
    assert _resumen(_splits(regs)) == [(2, 0.0, 2.0)]


# ------------------------------ papelera -------------------------------- #

def test_f045_r27_la_papelera_ni_pesa_ni_recibe_split() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=4.0, obra_ide=20,
                     deleted_at_utc="2026-03-03T10:00:00+00:00")]
    assert _resumen(_splits(regs)) == [(1, 8.0, 2.0)]


def test_f045_r27_la_papelera_no_cuenta_aunque_este_congelada() -> None:
    regs = [registro(1, fecha_int=LUNES, horas=6.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=8.0, obra_ide=20,
                     sigrid_estado="registrado",
                     deleted_at_utc="2026-03-03T10:00:00+00:00")]
    assert _resumen(_splits(regs)) == [(1, 8.0, -2.0)]


def test_f045_r27_la_lectura_trae_papelera_y_clave_de_pareja() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = sembrar_lineas(fabrica, [
        {"horas": 8.0, "horas_orig": 10.0, "line_index": 3,
         "empleado_line_no": 2},
        {"horas": 2.0, "tipo": "extra", "extra_auto": True,
         "line_index": 3, "empleado_line_no": 2}])
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, extra).deleted_at_utc = "2026-03-21T08:00Z"
        s.commit()
    filas = {f["registro_id"]: f for f in SqlAlchemyParteRepository(
        fabrica).fetch_registros_para_recurso()}  # type: ignore[arg-type]
    assert (filas[base]["horas_orig"], filas[base]["extra_auto"],
            filas[base]["deleted_at_utc"]) == (10.0, False, None)
    assert (filas[extra]["extra_auto"], filas[extra]["deleted_at_utc"]) == (
        True, "2026-03-21T08:00Z")
    assert {(f["line_index"], f["empleado_line_no"])
            for f in filas.values()} == {(3, 2)}


# ------------------------------- R30 log -------------------------------- #

def test_f045_r30_info_del_reparto_con_dos_obras(caplog) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=10.0, obra_ide=10),
            registro(2, fecha_int=LUNES, horas=4.0, obra_ide=20)]
    with caplog.at_level(logging.INFO):
        _splits(regs)
    linea = next(m for m in caplog.messages if "reparto 2026-03-02" in m)
    assert "recurso=501" in linea
    assert "jornada=8.00" in linea and "paso=0.50" in linea
    assert "obras=2" in linea and "lineas=2" in linea
    assert DNI not in caplog.text


def test_f045_r30_info_con_dos_lineas_de_una_obra(caplog) -> None:
    regs = [registro(1, fecha_int=LUNES, horas=6.0),
            registro(2, fecha_int=LUNES, horas=4.0)]
    with caplog.at_level(logging.INFO):
        _splits(regs)
    assert any("obras=1 lineas=2" in m for m in caplog.messages)


def test_f045_r30_una_sola_linea_no_ensucia_el_log(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _splits([registro(1, fecha_int=LUNES, horas=10.0)])
    assert not any("reparto" in m for m in caplog.messages)


# ---------------- ciclo completo sobre la base de memoria --------------- #

class IndiceFijo:
    """Siempre el recurso 501 (como en los tests de F-037)."""

    recursos: list = []

    def empresa_de_obra(self, obra_ide):  # noqa: ARG002
        return None

    def elegir_recurso(self, *args, **kwargs):  # noqa: ARG002
        return ResolucionRecurso(ide=RECURSO, motivo="ok")


def _conciliador(fabrica) -> RecursoConciliador:
    return RecursoConciliador(
        repository=SqlAlchemyParteRepository(fabrica),
        lookup=LookupFake(reshor=reshor_par(RECURSO)),
        calendario=CalendarioFake(set()),
        indice_provider=lambda: IndiceFijo(),
    )


def _filas(fabrica) -> list[tuple]:
    with fabrica.create_session() as s:
        return [tuple(f) for f in s.execute(
            select(ParteRegistroOrm.id, ParteRegistroOrm.obra_ide,
                   ParteRegistroOrm.tipo_hora, ParteRegistroOrm.horas,
                   ParteRegistroOrm.horas_orig, ParteRegistroOrm.extra_auto)
            .order_by(ParteRegistroOrm.id)).all()]


def _caso_real(fabrica) -> tuple[int, int, int]:
    """0678 ya en Sigrid con 8 + (-4) (trabajo 4) y 0704 con 8 nueva. Lo
    congelado conserva su recurso (F-023 R30): sin el, no estaria en el dia."""
    base, extra = sembrar_lineas(fabrica, [
        {"horas": 8.0, "horas_orig": 4.0, "estado": "registrado",
         "line_index": 0, "recurso_ide": RECURSO},
        {"horas": -4.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado", "line_index": 0, "recurso_ide": RECURSO}],
        document_id="doc-678", obra_ide=678, fecha="2026-03-02")
    (nueva,) = sembrar_lineas(fabrica, [{"horas": 8.0}],
                              document_id="doc-704", obra_ide=704,
                              fecha="2026-03-02")
    return base, extra, nueva


def test_f045_r24_caso_real_congelado_sigue_0_mas_8(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    base, extra, nueva = _caso_real(fabrica)
    with caplog.at_level(logging.INFO):
        resumen = _conciliador(fabrica).conciliar_todos()
    filas = {f[0]: f for f in _filas(fabrica)}
    assert filas[base][3:5] == (8.0, 4.0)
    assert filas[extra][3] == -4.0
    assert filas[nueva][3:5] == (0.0, 8.0)
    nuevas = [f for f in filas.values() if f[0] > nueva]
    assert [(f[1], f[2], f[3], f[5]) for f in nuevas] == [
        (704, "extra", 8.0, True)]
    assert resumen["extras_reclasificadas"] == 1
    assert "NO se puede cuadrar" not in caplog.text


def test_f045_r25_caso_real_avisa_y_cuenta(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    base, extra, _ = _caso_real(fabrica)
    with caplog.at_level(logging.INFO):
        resumen = _conciliador(fabrica).conciliar_todos()
    assert resumen["repartos_con_congeladas"] == 1
    aviso = next(m for m in caplog.messages if "reparto ideal" in m)
    assert "2026-03-02" in aviso and "recurso=501" in aviso
    assert f"registro {base} 8.00 -> 2.50" in aviso
    assert f"registro {extra} -4.00 -> 1.50" in aviso
    assert DNI not in caplog.text
    final = next(m for m in caplog.messages if "registros=" in m)
    assert "repartos_con_congeladas=1" in final


def test_f045_r25_el_contador_es_de_cada_pasada() -> None:
    fabrica = FabricaSesionSqlite()
    _caso_real(fabrica)
    conciliador = _conciliador(fabrica)
    conciliador.conciliar_todos()
    assert conciliador.conciliar_todos()["repartos_con_congeladas"] == 1


def test_f045_r25_sin_diferencias_ni_aviso_ni_cuenta(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 4.0, "estado": "registrado",
                              "recurso_ide": RECURSO}],
                   document_id="doc-a", obra_ide=10, fecha="2026-03-02")
    sembrar_lineas(fabrica, [{"horas": 4.0}], document_id="doc-b",
                   obra_ide=20, fecha="2026-03-02")
    with caplog.at_level(logging.WARNING):
        resumen = _conciliador(fabrica).conciliar_todos()
    assert resumen["repartos_con_congeladas"] == 0
    assert "reparto ideal" not in caplog.text


def test_f045_r25_sin_congeladas_ni_se_mide(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 10.0}], document_id="doc-a",
                   obra_ide=10, fecha="2026-03-02")
    sembrar_lineas(fabrica, [{"horas": 4.0}], document_id="doc-b",
                   obra_ide=20, fecha="2026-03-02")
    with caplog.at_level(logging.WARNING):
        resumen = _conciliador(fabrica).conciliar_todos()
    assert resumen["repartos_con_congeladas"] == 0
    assert "reparto ideal" not in caplog.text


def test_f045_r29_dos_pasadas_dan_lo_mismo() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 6.0}, {"horas": 4.0}],
                   document_id="doc-a", obra_ide=10, fecha="2026-03-02")
    sembrar_lineas(fabrica, [{"horas": 5.0}], document_id="doc-b",
                   obra_ide=20, fecha="2026-03-02")
    conciliador = _conciliador(fabrica)
    primera = conciliador.conciliar_todos()
    tras_primera = _filas(fabrica)
    segunda = conciliador.conciliar_todos()
    tras_segunda = _filas(fabrica)
    assert primera["extras_reclasificadas"] == segunda[
        "extras_reclasificadas"] == 3
    # Las extra_auto se recrean con id nuevo: se compara sin el id.
    assert sorted(f[1:] for f in tras_primera) == sorted(
        f[1:] for f in tras_segunda)
    ordinarias = sorted(f[3] for f in tras_segunda
                        if f[2] == "normal")
    assert ordinarias == [2.0, 2.5, 3.5]


def test_f045_r29_no_depende_del_orden_de_los_registros() -> None:
    regs = [registro(i, fecha_int=LUNES, horas=h, obra_ide=o)
            for i, (h, o) in enumerate(
                [(6.0, 10), (3.5, 10), (5.0, 20), (2.25, 30), (1.0, 20)],
                start=1)]
    esperado = _resumen(_splits(regs))
    azar = random.Random(20261014)
    for _ in range(20):
        copia = list(regs)
        azar.shuffle(copia)
        assert _resumen(_splits(copia)) == esperado


# ================= refuerzo tras la campana de mutacion ================= #

def test_f045_r25_el_contador_empieza_en_cero() -> None:
    """Fuera de `conciliar_todos` (que lo vacia), un conciliador recien
    construido cuenta desde 0."""
    conciliador = RecursoConciliador(
        repository=RepositorioFake(), lookup=LookupFake(),
        calendario=CalendarioFake(set()),
    )
    regs = [registro(1, fecha_int=LUNES, horas=8.0, obra_ide=678,
                     sigrid_estado="registrado", horas_orig=4.0),
            registro(2, fecha_int=LUNES, horas=8.0, obra_ide=704)]
    conciliador._reclasificar_extras_jornada(
        regs, {1: RECURSO, 2: RECURSO}, indice_reshor(RECURSO))
    assert conciliador._repartos_con_congeladas == 1


def test_f045_r20_sabado_sin_horas_ordinarias_no_se_toca(caplog) -> None:
    with caplog.at_level(logging.INFO):
        assert _splits([registro(1, fecha_int=SABADO, horas=0.0)]) == []
    assert "dia NO laborable" not in caplog.text
