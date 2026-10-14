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


# ============================ conciliador ============================ #
# Ciclo completo: `conciliar_todos` con el repositorio REAL sobre SQLite.

from application.services.jornada_resolver import DetalleJornada  # noqa: E402
from application.services.recurso_conciliador import (  # noqa: E402
    RecursoConciliador,
)
from sqlalchemy import select  # noqa: E402
from tests.dobles import (  # noqa: E402
    CalendarioFake,
    LookupFake,
    RepositorioFake,
    reshor_par,
)
from tests.test_f045_conciliar import IndiceFijo  # noqa: E402

LUNES = 20260302
DNI_SINTETICO = "12345678Z"


def _conciliador(fabrica_o_repo, *, reajuste=True) -> RecursoConciliador:
    repo = (SqlAlchemyParteRepository(fabrica_o_repo)
            if isinstance(fabrica_o_repo, FabricaSesionSqlite)
            else fabrica_o_repo)
    return RecursoConciliador(
        repository=repo, lookup=LookupFake(reshor=reshor_par(RECURSO)),
        calendario=CalendarioFake(set()),
        indice_provider=lambda: IndiceFijo(), reajuste=reajuste)


def _horas(fabrica) -> dict[int, tuple]:
    with fabrica.create_session() as s:
        return {f.id: (f.obra_ide, f.tipo_hora, f.horas, f.horas_orig,
                       f.extra_auto)
                for f in s.execute(select(ParteRegistroOrm)).scalars()}


def _repartos(fabrica) -> list[RepartoPendienteOrm]:
    with fabrica.create_session() as s:
        return list(s.execute(select(RepartoPendienteOrm).order_by(
            RepartoPendienteOrm.id)).scalars())


def _caso_real_ciclo(fabrica):
    """0678 en Sigrid con 8 + (-4) (trabajo 4) y 0704 nueva con 8 (R6)."""
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


def _extras_auto(horas, obra):
    return [h for h in horas.values() if h[0] == obra and h[4]]


# ------------------------------- R10 ------------------------------- #

def test_f046_r10_apagado_es_f045_y_no_toca_reparto_pendiente(fabrica):
    base, extra, nueva = _caso_real_ciclo(fabrica)
    res = _conciliador(fabrica, reajuste=False).conciliar_todos()
    h = _horas(fabrica)
    assert h[base][2] == 8.0 and h[extra][2] == -4.0
    assert h[nueva][2:4] == (0.0, 8.0)                 # F-045: 0 + 8
    assert _repartos(fabrica) == []
    assert not any(k.startswith("repartos_")
                   and k != "repartos_con_congeladas" for k in res)


def test_f046_r10_apagado_no_llama_a_nada_del_reajuste():
    repo = RepositorioFake([])
    _conciliador(repo, reajuste=False).conciliar_todos()
    assert not {"vigentes", "materializar", "guardar"} & set(repo.orden)


def test_f046_r10_por_defecto_apagado():
    c = RecursoConciliador(repository=RepositorioFake([]),
                           lookup=LookupFake())
    assert c._reajuste is False


# ------------------------------- R11 ------------------------------- #

def test_f046_r11_propone_y_aplica_el_ideal_a_lo_libre(fabrica, caplog):
    base, extra, nueva = _caso_real_ciclo(fabrica)
    with caplog.at_level(logging.INFO):
        res = _conciliador(fabrica).conciliar_todos()
    h = _horas(fabrica)
    assert h[nueva][2:4] == (5.5, 8.0)                 # 0704: 5,5 + 2,5
    assert [x[2] for x in _extras_auto(h, 704)] == [2.5]
    assert h[base][2] == 8.0 and h[extra][2] == -4.0   # congeladas intactas
    (rep,) = _repartos(fabrica)
    assert (rep.estado, rep.recurso_ide, rep.fecha_int) == (
        "pendiente", RECURSO, LUNES)
    datos = json.loads(rep.cambios)
    assert sorted(datos["ids_grupo"]) == sorted([base, extra, nueva])
    assert [(c["registro_id"], c["tipo"], c["antes"], c["despues"],
             c["sigrid_estado"], c["obra_ide"], c["document_id"])
            for c in datos["cambios"]] == [
        (base, "ordinaria", 8.0, 2.5, "registrado", 678, "doc-678"),
        (extra, "extra", -4.0, 1.5, "registrado", 678, "doc-678")]
    assert res["repartos_propuestos"] == 1
    assert DNI_SINTETICO not in caplog.text
    assert any("propuesto" in m and f"registro {base} 8.00 -> 2.50" in m
               for m in caplog.messages)


def test_f046_r11_extra_nueva_lleva_su_hora_extra(fabrica):
    (base,) = sembrar_lineas(fabrica, [
        {"horas": 8.0, "estado": "registrado", "recurso_ide": RECURSO}],
        document_id="doc-678", obra_ide=678, fecha="2026-03-02")
    sembrar_lineas(fabrica, [{"horas": 4.0}], document_id="doc-704",
                   obra_ide=704, fecha="2026-03-02")
    _conciliador(fabrica).conciliar_todos()
    (rep,) = _repartos(fabrica)
    cambios = json.loads(rep.cambios)["cambios"]
    assert [(c["registro_id"], c["base_registro_id"], c["tipo"], c["antes"],
             c["despues"]) for c in cambios] == [
        (base, base, "ordinaria", 8.0, 5.5), (None, base, "extra", 0.0, 2.5)]
    assert cambios[1]["hora_ext"] == {"ide": 200, "cod": "HE01",
                                      "desc": "Hora extra", "ext": 1}
    assert cambios[1]["extra_auto"] is True


# ------------------------------- R12 ------------------------------- #

def test_f046_r12_sin_ordinarias_libres_no_propone(fabrica):
    _caso_real_ciclo(fabrica)
    with fabrica.create_session() as s:      # la 0704 tambien en Sigrid
        for r in s.execute(select(ParteRegistroOrm).where(
                ParteRegistroOrm.obra_ide == 704)).scalars():
            r.sigrid_estado = "registrado"
            r.recurso_ide = RECURSO
        s.commit()
    res = _conciliador(fabrica).conciliar_todos()
    assert _repartos(fabrica) == [] and res["repartos_propuestos"] == 0


# ------------------------------- R13 ------------------------------- #

def test_f046_r13_dos_pasadas_con_la_misma_firma_no_tocan_el_reparto(
        fabrica):
    _b, _e, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    (antes,) = _repartos(fabrica)
    res = c.conciliar_todos()
    (despues,) = _repartos(fabrica)
    assert (antes.id, antes.actualizado_at_utc) == (
        despues.id, despues.actualizado_at_utc)
    assert res["repartos_propuestos"] == 0
    assert _horas(fabrica)[nueva][2] == 5.5            # el ideal, otra vez


def test_f046_r13_si_el_dia_cambia_el_pendiente_pasa_a_obsoleto(fabrica):
    _b, _e, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, nueva).horas_orig = None
        s.get(ParteRegistroOrm, nueva).horas = 6.0     # cambian las horas
        s.commit()
    c.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["obsoleto", "pendiente"]


def test_f046_r13_aplicando_no_se_toca_y_lo_libre_va_al_ideal(fabrica):
    """Pesos 4 (trabajo de la 0678) y 6 (la 0704 cambiada): la 0704 recibe
    5 y la congelada no se toca; la fila sigue `aplicando`."""
    base, _e, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        s.query(RepartoPendienteOrm).one().estado = "aplicando"
        s.get(ParteRegistroOrm, nueva).horas_orig = None
        s.get(ParteRegistroOrm, nueva).horas = 6.0
        s.commit()
    c.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["aplicando"]
    h = _horas(fabrica)
    assert h[base][2] == 8.0
    assert h[nueva][2:4] == (5.0, 6.0)


def test_f046_r13_un_reparto_cuyo_grupo_desaparece_pasa_a_obsoleto(fabrica):
    _b, _e, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        for r in s.execute(select(ParteRegistroOrm)).scalars():
            r.deleted_at_utc = "2026-03-03T10:00:00+00:00"
        s.commit()
    c.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["obsoleto"]


# ------------------------------- R14 ------------------------------- #

def test_f046_r14_rechazado_reparte_en_residual_y_pasa_a_mantenido(fabrica):
    _b, _e, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        s.query(RepartoPendienteOrm).one().estado = "rechazado"
        s.commit()
    res = c.conciliar_todos()
    assert _horas(fabrica)[nueva][2:4] == (0.0, 8.0)   # residual: 0 + 8
    assert [r.estado for r in _repartos(fabrica)] == ["mantenido"]
    assert res["repartos_mantenidos"] == 1
    res = c.conciliar_todos()                          # sigue mantenido
    assert [r.estado for r in _repartos(fabrica)] == ["mantenido"]
    assert _horas(fabrica)[nueva][2] == 0.0
    assert res["repartos_mantenidos"] == 0


# ------------------------------- R15 ------------------------------- #

def test_f046_r15_aplicado_se_materializa_antes_de_repartir(fabrica):
    base, extra, nueva = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        rep = s.query(RepartoPendienteOrm).one()
        rep.estado = "aplicado"
        rep.resultado = json.dumps({"reservas": {}, "sv5": {"lineas": []}})
        s.commit()
    res = c.conciliar_todos()
    h = _horas(fabrica)
    assert (h[base][2], h[base][3], h[extra][2]) == (2.5, 4.0, 1.5)
    assert h[nueva][2] == 5.5                          # residual = ideal
    assert res["repartos_materializados"] == 1
    assert res["repartos_descuadrados"] == 0
    # Tras materializar, el dia ya es el ideal: el reparto queda obsoleto
    # y no nace otro.
    assert [r.estado for r in _repartos(fabrica)] == ["obsoleto"]


def test_f046_r16_descuadre_se_cuenta(fabrica):
    base, extra, _n = _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    with fabrica.create_session() as s:
        rep = s.query(RepartoPendienteOrm).one()
        rep.estado = "aplicado"
        rep.resultado = json.dumps({"reservas": {}})
        s.get(ParteRegistroOrm, extra).horas = -3.0
        s.commit()
    res = c.conciliar_todos()
    assert res["repartos_descuadrados"] == 1
    assert _horas(fabrica)[base][2] == 8.0
    assert [r.estado for r in _repartos(fabrica)] == ["aplicado"]


# ------------------------------- R18 ------------------------------- #

def test_f046_r18_la_pasada_entera_va_bajo_el_candado():
    repo = RepositorioFake([])
    _conciliador(repo).conciliar_todos()
    assert repo.orden[0] == "candado" and repo.orden[-1] == "suelta"
    assert (repo.orden.index("revert") < repo.orden.index("materializar")
            < repo.orden.index("fetch") < repo.orden.index("guardar"))
    assert repo.candados == 1


def test_f046_r18_con_el_interruptor_apagado_tambien_hay_candado():
    repo = RepositorioFake([])
    _conciliador(repo, reajuste=False).conciliar_todos()
    assert repo.orden[0] == "candado" and repo.orden[-1] == "suelta"


def test_f046_r18_sin_candado_a_tiempo_la_pasada_lanza():
    class RepoSinCandado(RepositorioFake):
        def candado_pasada(self):
            raise TimeoutError("candado ocupado")
    repo = RepoSinCandado([])
    with pytest.raises(TimeoutError):
        _conciliador(repo).conciliar_todos()
    assert repo.orden == []


def test_f046_r18_repositorio_sin_candado_sigue_funcionando():
    """Los dobles anteriores a F-046 no lo tienen: sin el, la pasada corre
    como siempre (en produccion el repositorio real siempre lo tiene)."""
    class RepoAntiguo:
        def __init__(self):
            self.inner = RepositorioFake([])

        def __getattr__(self, nombre):
            if nombre == "candado_pasada":
                raise AttributeError(nombre)
            return getattr(self.inner, nombre)
    res = _conciliador(RepoAntiguo(), reajuste=False).conciliar_todos()
    assert res["registros"] == 0


# ------------------------------- R19 ------------------------------- #

def test_f046_r19_contadores_del_reajuste():
    repo = RepositorioFake([])
    repo.resultado_materializar = {"materializados": 2, "descuadrados": 1}
    res = _conciliador(repo).conciliar_todos()
    assert {k: res[k] for k in ("repartos_propuestos",
                                "repartos_materializados",
                                "repartos_mantenidos",
                                "repartos_descuadrados")} == {
        "repartos_propuestos": 0, "repartos_materializados": 2,
        "repartos_mantenidos": 0, "repartos_descuadrados": 1}


# ----------------------------- [E] R46 ----------------------------- #

def test_f046_r46_e_la_propuesta_usa_la_jornada_de_detalle_jornada(fabrica):
    """R9c en el conciliador: con `_detalle_jornada` dando J = 6, A
    registrada 6 + (-1) (trabajo 5) y B nueva 4: B 2,5 + 1,5 y A 6 -> 3,5,
    -1 -> 1,5."""
    base, extra = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 5.0, "estado": "registrado",
         "line_index": 0, "recurso_ide": RECURSO},
        {"horas": -1.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado", "line_index": 0, "recurso_ide": RECURSO}],
        document_id="doc-a", obra_ide=678, fecha="2026-03-02")
    (b,) = sembrar_lineas(fabrica, [{"horas": 4.0}], document_id="doc-b",
                          obra_ide=704, fecha="2026-03-02")
    c = _conciliador(fabrica)
    c._detalle_jornada = lambda *a, **k: DetalleJornada(
        horas=6.0, candef_efectivo=9.0, semanal=42.0, origen="mapa",
        ultimo_laborable=True)
    c.conciliar_todos()
    assert _horas(fabrica)[b][2] == 2.5
    (rep,) = _repartos(fabrica)
    assert [(x["registro_id"], x["antes"], x["despues"])
            for x in json.loads(rep.cambios)["cambios"]] == [
        (base, 6.0, 3.5), (extra, -1.0, 1.5)]


def test_f046_r46_e_los_modulos_nuevos_no_importan_jornada_resolver():
    import ast
    from pathlib import Path

    from application.services import reajuste_reparto, reparto_ponderado
    for mod in (reajuste_reparto, reparto_ponderado):
        arbol = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        nombres = {n.module for n in ast.walk(arbol)
                   if isinstance(n, ast.ImportFrom)}
        nombres |= {a.name for n in ast.walk(arbol)
                    if isinstance(n, ast.Import) for a in n.names}
        assert not any("jornada_resolver" in (m or "") for m in nombres)
