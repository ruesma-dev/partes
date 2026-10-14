# tests/test_f046_conciliar.py
"""F-046 · el reajuste en sv3: repositorio (R15-R17, guardar, vigentes) y
conciliador (R10-R14, R19, [E] R46).

El repositorio se ejercita de verdad contra SQLite en memoria
(`FabricaSesionSqlite`, mismo ORM que produccion); el conciliador, contra
`RepositorioFake` y `LookupFake`. Datos sinteticos: ni nombres ni DNIs
reales (el DNI de las semillas es el sintetico de siempre).
"""
from __future__ import annotations

import json
import logging

import pytest
from application.services.reajuste_reparto import cambios_a_json
from infrastructure.database.orm_models import (
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, sembrar_lineas

FECHA = 20260320
RECURSO = 501
HORA_EXT = {"ide": 9, "cod": "HE01", "desc": "Hora extra", "ext": 1}
NUEVA = 990000001


# ============================ repositorio ============================ #

def _repo(fabrica) -> SqlAlchemyParteRepository:
    return SqlAlchemyParteRepository(fabrica)  # type: ignore[arg-type]


def _marcar(fabrica, rid, **campos) -> None:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _reparto(fabrica, *, estado="aplicado", cambios=None, resultado=None,
             firma="f" * 64, recurso=RECURSO, fecha=FECHA, decidido=True):
    with fabrica.create_session() as s:
        fila = RepartoPendienteOrm(
            recurso_ide=recurso, fecha_int=fecha, estado=estado,
            firma=firma, cambios=cambios_a_json(cambios or {
                "ids_grupo": [], "cambios": []}),
            resultado=None if resultado is None else json.dumps(resultado),
            decision="aplicar" if decidido else None,
            decidido_por="admin@test" if decidido else None,
            decidido_at_utc="2026-10-14T10:00:00+00:00" if decidido else None,
            creado_at_utc="2026-10-14T09:00:00+00:00",
            actualizado_at_utc="2026-10-14T09:00:00+00:00")
        s.add(fila)
        s.commit()
        return fila.id


def _fila(fabrica, rid_reparto) -> RepartoPendienteOrm:
    with fabrica.create_session() as s:
        return s.get(RepartoPendienteOrm, rid_reparto)


def _reg(fabrica, rid) -> ParteRegistroOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


def _c(rid, base, tipo, antes, despues, **kw) -> dict:
    d = {"registro_id": rid, "base_registro_id": base, "tipo": tipo,
         "antes": antes, "despues": despues, "sigrid_estado": "registrado"}
    d.update(kw)
    return d


def _caso_real(fabrica):
    """0678 registrada 8 + (-4) con horas_orig 4 (R6)."""
    base, extra = sembrar_lineas(fabrica, [
        {"horas": 8.0, "horas_orig": 4.0, "estado": "registrado",
         "recurso_ide": RECURSO},
        {"horas": -4.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado", "line_index": 0, "recurso_ide": RECURSO},
    ], fecha="2026-03-20")
    cambios = {"ids_grupo": [base, extra], "cambios": [
        _c(base, base, "ordinaria", 8.0, 2.5),
        _c(extra, base, "extra", -4.0, 1.5)]}
    return base, extra, cambios


def test_f046_r15_materializa_los_valores_despues(fabrica):
    base, extra, cambios = _caso_real(fabrica)
    rid = _reparto(fabrica, cambios=cambios, resultado={"reservas": {}})
    res = _repo(fabrica).materializar_repartos()
    assert res == {"materializados": 1, "descuadrados": 0}
    assert (_reg(fabrica, base).horas, _reg(fabrica, base).horas_orig) == (
        2.5, 4.0)
    assert _reg(fabrica, extra).horas == 1.5
    fila = _fila(fabrica, rid)
    assert fila.estado == "materializado" and fila.materializado_at_utc


def test_f046_r15_horas_orig_de_la_base_si_era_nulo(fabrica):
    (base,) = sembrar_lineas(fabrica, [
        {"horas": 8.0, "estado": "registrado", "recurso_ide": RECURSO}])
    _marcar(fabrica, base, sigrid_hmores_ide=4001, sigrid_hmoide=7001,
            sigrid_parte_cod="PT26/09001")
    cambios = {"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT)]}
    _reparto(fabrica, cambios=cambios, resultado={
        "reservas": {str(base): NUEVA},
        "sv5": {"ok": True, "lineas": [
            {"registro_id": base, "hmores_ide": 4001, "hmoide": 7001,
             "parte_cod": "PT26/09001", "nueva": False},
            {"registro_id": NUEVA, "hmores_ide": 4555, "hmoide": 7001,
             "parte_cod": "PT26/09001", "nueva": True}]}})
    assert _repo(fabrica).materializar_repartos()["materializados"] == 1
    b = _reg(fabrica, base)
    assert (b.horas, b.horas_orig) == (5.5, 8.0)
    n = _reg(fabrica, NUEVA)
    assert n is not None
    assert (n.tipo_hora, n.horas, n.extra_auto, n.hora_ide, n.hora_codigo,
            n.hora_descripcion, n.hora_ext, n.hora_match_method) == (
        "extra", 2.5, True, 9, "HE01", "Hora extra", 1, "extra_jornada")
    # R15: clonada de su base como `apply_extras_splits`.
    assert (n.document_id, n.line_index, n.fecha_int, n.obra_ide,
            n.recurso_ide, n.empleado_dni) == (
        b.document_id, b.line_index, b.fecha_int, b.obra_ide, b.recurso_ide,
        b.empleado_dni)
    # R17: nace registrada con lo que devolvio sv5 y la firma del decisor.
    assert (n.sigrid_estado, n.sigrid_hmores_ide, n.sigrid_hmoide,
            n.sigrid_parte_cod, n.sigrid_registrado_by,
            n.sigrid_registrado_at_utc) == (
        "registrado", 4555, 7001, "PT26/09001", "admin@test",
        "2026-10-14T10:00:00+00:00")


def test_f046_r17_extra_nueva_de_base_solo_aprobada_nace_sin_estado(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}], aprobado=True)
    cambios = {"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5, sigrid_estado=None),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT,
           sigrid_estado=None)]}
    _reparto(fabrica, cambios=cambios, resultado={
        "reservas": {str(base): NUEVA}, "sv5": None})
    assert _repo(fabrica).materializar_repartos()["materializados"] == 1
    n = _reg(fabrica, NUEVA)
    assert (n.sigrid_estado, n.sigrid_hmores_ide, n.horas) == (None, None,
                                                               2.5)


def test_f046_r15_materializar_dos_veces_es_idempotente(fabrica):
    base, extra, cambios = _caso_real(fabrica)
    rid = _reparto(fabrica, cambios=cambios, resultado={"reservas": {}})
    repo = _repo(fabrica)
    repo.materializar_repartos()
    with fabrica.create_session() as s:      # alguien lo vuelve a aplicado
        s.get(RepartoPendienteOrm, rid).estado = "aplicado"
        s.commit()
    assert repo.materializar_repartos() == {"materializados": 1,
                                            "descuadrados": 0}
    assert _reg(fabrica, base).horas == 2.5
    assert _reg(fabrica, extra).horas == 1.5


def test_f046_r16_linea_que_no_esta_ni_antes_ni_despues_no_toca_nada(
        fabrica, caplog):
    base, extra, cambios = _caso_real(fabrica)
    _marcar(fabrica, extra, horas=-3.0)          # ni -4 ni 1,5
    rid = _reparto(fabrica, cambios=cambios, resultado={"reservas": {}})
    with caplog.at_level(logging.ERROR):
        res = _repo(fabrica).materializar_repartos()
    assert res == {"materializados": 0, "descuadrados": 1}
    assert _reg(fabrica, base).horas == 8.0      # la base NO se toco
    fila = _fila(fabrica, rid)
    assert fila.estado == "aplicado" and "descuadr" in (fila.error or "")
    assert any("reparto" in r.getMessage() and r.levelno == logging.ERROR
               for r in caplog.records)


def test_f046_r16_extra_nueva_sin_reserva_es_descuadre(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0, "estado": "registrado"}])
    cambios = {"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT)]}
    _reparto(fabrica, cambios=cambios, resultado={"reservas": {}})
    assert _repo(fabrica).materializar_repartos()["descuadrados"] == 1
    assert _reg(fabrica, base).horas == 8.0


def test_f046_r17_base_registrada_sin_respuesta_de_sv5_es_descuadre(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0, "estado": "registrado"}])
    cambios = {"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT)]}
    _reparto(fabrica, cambios=cambios, resultado={
        "reservas": {str(base): NUEVA}, "sv5": {"ok": True, "lineas": []}})
    assert _repo(fabrica).materializar_repartos()["descuadrados"] == 1
    assert _reg(fabrica, NUEVA) is None


def test_f046_r15_solo_materializa_los_aplicados(fabrica):
    base, _extra, cambios = _caso_real(fabrica)
    for estado in ("pendiente", "aplicando", "rechazado", "obsoleto"):
        _reparto(fabrica, estado=estado, cambios=cambios,
                 resultado={"reservas": {}})
    assert _repo(fabrica).materializar_repartos() == {
        "materializados": 0, "descuadrados": 0}
    assert _reg(fabrica, base).horas == 8.0


def test_f046_r15_apply_extras_splits_admite_id_y_sigrid(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}])
    n = _repo(fabrica).apply_extras_splits([{
        "normal_id": base, "horas_norm": 5.5, "horas_orig": 8.0,
        "extra_horas": 2.5, "hora_ext_ide": 9, "hora_ext_cod": "HE01",
        "hora_ext_desc": "Hora extra", "hora_ext_ext": 1, "hora_candef": 8.0,
        "id": NUEVA, "sigrid": {"sigrid_estado": "registrado",
                                "sigrid_hmores_ide": 4555}}])
    assert n == 1
    e = _reg(fabrica, NUEVA)
    assert (e.horas, e.sigrid_estado, e.sigrid_hmores_ide) == (
        2.5, "registrado", 4555)


def test_f046_r15_apply_extras_splits_sin_id_igual_que_siempre(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}])
    _repo(fabrica).apply_extras_splits([{
        "normal_id": base, "horas_norm": 6.0, "horas_orig": 8.0,
        "extra_horas": 2.0, "hora_ext_ide": 9, "hora_ext_cod": "HE01",
        "hora_ext_desc": "x", "hora_ext_ext": 1, "hora_candef": 8.0}])
    with fabrica.create_session() as s:
        extra = s.query(ParteRegistroOrm).filter(
            ParteRegistroOrm.extra_auto.is_(True)).one()
        assert extra.id != NUEVA and extra.sigrid_estado is None


# ------------------------------ guardar ------------------------------ #

def _prop(firma, cambios=None, recurso=RECURSO, fecha=FECHA) -> dict:
    return {"recurso_ide": recurso, "fecha_int": fecha, "firma": firma,
            "cambios": cambios}


def _estados(fabrica) -> list[tuple[int, str, str]]:
    with fabrica.create_session() as s:
        return [(f.id, f.estado, f.firma[:1]) for f in s.query(
            RepartoPendienteOrm).order_by(RepartoPendienteOrm.id)]


def test_f046_r11_guardar_crea_el_pendiente_con_sus_cambios(fabrica):
    base, extra, cambios = _caso_real(fabrica)
    _marcar(fabrica, base, sigrid_hmores_ide=4001)
    res = _repo(fabrica).guardar_repartos([_prop("a" * 64, cambios)], [])
    assert res == {"propuestos": 1, "obsoletos": 0, "mantenidos": 0}
    ((rid, estado, firma),) = _estados(fabrica)
    assert (estado, firma) == ("pendiente", "a")
    datos = json.loads(_fila(fabrica, rid).cambios)
    assert datos["ids_grupo"] == [base, extra]
    c0 = datos["cambios"][0]
    # Enriquecido desde `parte_registros` (obra, documento, linea Sigrid).
    assert (c0["obra_codigo"], c0["document_id"], c0["hmores_ide"]) == (
        "0100", "doc-1", 4001)
    assert (c0["antes"], c0["despues"]) == (8.0, 2.5)


def test_f046_r13_misma_firma_no_toca_el_pendiente(fabrica):
    _b, _e, cambios = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.guardar_repartos([_prop("a" * 64, cambios)], [])
    antes = _estados(fabrica)
    res = repo.guardar_repartos([_prop("a" * 64, cambios)], [])
    assert res == {"propuestos": 0, "obsoletos": 0, "mantenidos": 0}
    assert _estados(fabrica) == antes


def test_f046_r13_otra_firma_obsoleta_y_crea_otro(fabrica):
    _b, _e, cambios = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.guardar_repartos([_prop("a" * 64, cambios)], [])
    res = repo.guardar_repartos([_prop("b" * 64, cambios)], [])
    assert res == {"propuestos": 1, "obsoletos": 1, "mantenidos": 0}
    assert [(e, f) for _i, e, f in _estados(fabrica)] == [
        ("obsoleto", "a"), ("pendiente", "b")]


def test_f046_r13_sin_cambios_el_vivo_pasa_a_obsoleto(fabrica):
    for estado in ("pendiente", "rechazado", "mantenido", "materializado"):
        fabrica = FabricaSesionSqlite()
        _reparto(fabrica, estado=estado, firma="a" * 64)
        res = _repo(fabrica).guardar_repartos([_prop("b" * 64)], [])
        assert res["obsoletos"] == 1, estado
        assert [e for _i, e, _f in _estados(fabrica)] == ["obsoleto"]


@pytest.mark.parametrize("estado", ["aplicando", "aplicado"])
def test_f046_r13_aplicando_o_aplicado_nunca_pasan_a_obsoleto(fabrica,
                                                              estado):
    _b, _e, cambios = _caso_real(fabrica)
    _reparto(fabrica, estado=estado, firma="a" * 64)
    res = _repo(fabrica).guardar_repartos(
        [_prop("b" * 64, cambios), _prop("c" * 64)], [])
    assert res == {"propuestos": 0, "obsoletos": 0, "mantenidos": 0}
    assert [e for _i, e, _f in _estados(fabrica)] == [estado]


def test_f046_r14_guardar_pasa_rechazados_a_mantenido(fabrica):
    r1 = _reparto(fabrica, estado="rechazado")
    r2 = _reparto(fabrica, estado="pendiente", fecha=FECHA + 1)
    res = _repo(fabrica).guardar_repartos([], [r1, r2])
    assert res == {"propuestos": 0, "obsoletos": 0, "mantenidos": 1}
    assert _fila(fabrica, r1).estado == "mantenido"
    assert _fila(fabrica, r2).estado == "pendiente"     # CAS: no era rechazado


def test_f046_r13_vigentes_excluye_obsoletos(fabrica):
    _reparto(fabrica, estado="obsoleto", firma="a" * 64)
    viva = _reparto(fabrica, estado="pendiente", firma="b" * 64)
    _reparto(fabrica, estado="mantenido", fecha=FECHA + 1)
    vig = _repo(fabrica).repartos_vigentes()
    assert set(vig) == {(RECURSO, FECHA), (RECURSO, FECHA + 1)}
    assert (vig[(RECURSO, FECHA)]["id"], vig[(RECURSO, FECHA)]["estado"],
            vig[(RECURSO, FECHA)]["firma"]) == (viva, "pendiente", "b" * 64)


def test_f046_r39_sin_tabla_no_hay_nombres(fabrica):
    _b, _e, cambios = _caso_real(fabrica)
    _repo(fabrica).guardar_repartos([_prop("a" * 64, cambios)], [])
    with fabrica.create_session() as s:
        texto = s.query(RepartoPendienteOrm).one().cambios
    assert "12345678Z" not in texto and "nombre" not in texto


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()
