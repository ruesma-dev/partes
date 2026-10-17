# tests/test_f046_t22_bordes.py
"""F-046 T22 · bordes del reajuste en sv3 que la campana de mutacion dejo
sin vigilar (supervivientes de `progress/mutacion_F-046.md`).

  - `clase_linea` y `cambios_a_json` (reajuste_reparto);
  - `proponer_dia`: extra automatica huerfana, base sin trabajo,
    redondeo de la extra y tolerancias (reparto_ponderado);
  - el conciliador: `_lineas_dia` sin interruptor, contadores que el
    repositorio no informa, residual con reparto vivo y grupo presente
    sin repartir;
  - el repositorio: candado (clave, reloj, fallo al tomarlo), la
    materializacion (carreras, tolerancias, extra ya creada, log, error
    recortado) y `guardar_repartos` con la MISMA firma.

Repositorio real sobre SQLite en memoria; conciliador contra los dobles de
siempre. Datos SINTETICOS (ni nombres ni DNIs).
"""
from __future__ import annotations

import json
import logging

import pytest
from application.services.reajuste_reparto import (
    DURA,
    REAJUSTABLE,
    cambios_a_json,
    clase_linea,
)
from application.services.recurso_conciliador import RecursoConciliador
from application.services.reparto_ponderado import proponer_dia
from infrastructure.database import sqlalchemy_parte_repository as modulo
from infrastructure.database.orm_models import (
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from sqlalchemy import update
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    reshor_par,
    sembrar_lineas,
)
from tests.test_f045_conciliar import IndiceFijo
from tests.test_f046_candado import ConexionFalsa
from tests.test_f046_candado import _repo as _repo_candado
from tests.test_f046_conciliar import (
    FECHA,
    HORA_EXT,
    NUEVA,
    RECURSO,
    _c,
    _caso_real,
    _caso_real_ciclo,
    _conciliador,
    _fila,
    _reg,
    _reparto,
    _repartos,
)
from tests.test_f046_conciliar import _repo as _repo_sqlite
from tests.test_f046_proponer_dia import _aj, _cb, _e, _o


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


# ============================ reajuste_reparto ============================ #

@pytest.mark.parametrize("horas", [0.5, 1.0])
def test_f046_t22_ordinaria_registrada_con_menos_de_una_hora_es_reajustable(
        horas):
    """Solo la ordinaria SIN trabajo (<= 0) es dura; media hora no."""
    reg = {"tipo_hora": "normal", "horas": horas,
           "sigrid_estado": "registrado"}
    assert clase_linea(reg, congelada=True) == REAJUSTABLE
    assert clase_linea({**reg, "horas": 0.0}, congelada=True) == DURA


def test_f046_t22_cambios_a_json_ordena_claves_y_no_escapa():
    texto = cambios_a_json({"b": 1, "a": "año"})
    assert texto == '{"a":"año","b":1}'


# ============================== proponer_dia ============================== #

def test_f046_t22_extra_automatica_huerfana_pesa_en_su_obra():
    """Una extra automatica cuya base no esta en el dia (papelera) no es
    de ninguna pareja: pesa en su obra como cualquier extra."""
    p = proponer_dia([_o(1, 678, 4.0, fija=True, reaj=True),
                      _o(3, 704, 4.0),
                      _e(5, 704, 2.0, extra_auto=True)], 8.0)
    assert _aj(p) == {3: (5.0, -1.0)}
    assert _cb(p) == [(1, 1, "ordinaria", 4.0, 3.0),
                      (None, 1, "extra", 0.0, 1.0)]


def test_f046_t22_base_registrada_sin_trabajo_es_dura():
    """Base congelada con trabajado 0 (horas_orig 0): dura, cuenta sus
    horas y no se reajusta."""
    p = proponer_dia([_o(1, 678, 2.0, fija=True, reaj=True, horas_orig=0.0),
                      _o(3, 704, 8.0)], 8.0)
    assert _aj(p) == {3: (6.0, 2.0)}
    assert _cb(p) == []


def test_f046_t22_la_extra_del_cambio_va_a_2_decimales():
    p = proponer_dia([_o(1, 678, 8.0, fija=True, reaj=True,
                         horas_orig=4.125)], 4.0)
    assert _cb(p) == [(1, 1, "ordinaria", 8.0, 4.0),
                      (None, 1, "extra", 0.0, 0.12)]


def test_f046_t22_diferencia_de_eps_en_la_ordinaria_no_es_cambio():
    """Dia no laborable (J = 0): la base queda a 0 y tiene 1e-9 (= _EPS)."""
    p = proponer_dia([
        _o(1, 678, 1e-9, fija=True, reaj=True, horas_orig=4.0),
        _e(2, 678, 4.0, fija=True, reaj=True, base_id=1)], 0.0)
    assert p.cuadra and _cb(p) == []


def test_f046_t22_diferencia_de_eps_en_la_extra_no_es_cambio():
    p = proponer_dia([
        _o(1, 678, 8.0, fija=True, reaj=True, horas_orig=8.0),
        _e(2, 678, 1e-9, fija=True, reaj=True, base_id=1)], 8.0)
    assert p.cuadra and _cb(p) == []


# =============================== conciliador =============================== #

def _reg_dia(rid, **kw) -> dict:
    d = {"registro_id": rid, "tipo_hora": "normal", "horas": 8.0,
         "horas_orig": None, "sigrid_estado": "registrado", "obra_ide": 678,
         "document_id": "doc-1", "line_index": 0, "empleado_line_no": None,
         "extra_auto": False}
    d.update(kw)
    return d


def test_f046_t22_lineas_dia_sin_interruptor_nada_es_reajustable():
    regs = [_reg_dia(1)]
    (por_defecto,) = RecursoConciliador._lineas_dia(regs)
    (apagado,) = RecursoConciliador._lineas_dia(regs, reajuste=False)
    (encendido,) = RecursoConciliador._lineas_dia(regs, reajuste=True)
    assert (por_defecto.fija, por_defecto.reajustable) == (True, False)
    assert apagado.reajustable is False
    assert encendido.reajustable is True


def test_f046_t22_contadores_que_el_repositorio_no_informa_son_0():
    class RepoMudo(RepositorioFake):
        def materializar_repartos(self):
            self.orden.append("materializar")
            return {}

        def guardar_repartos(self, propuestas, mantenidos):
            self.orden.append("guardar")
            return {}
    res = _conciliador(RepoMudo([])).conciliar_todos()
    assert {k: res[k] for k in ("repartos_propuestos",
                                "repartos_materializados",
                                "repartos_mantenidos",
                                "repartos_descuadrados")} == {
        "repartos_propuestos": 0, "repartos_materializados": 0,
        "repartos_mantenidos": 0, "repartos_descuadrados": 0}


def test_f046_t22_sin_libres_con_reparto_vivo_pasa_a_obsoleto(fabrica):
    """R12: si lo libre ya esta en Sigrid, el grupo va en residual y el
    pendiente que habia pasa a obsoleto."""
    _caso_real_ciclo(fabrica)
    c = _conciliador(fabrica)
    c.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["pendiente"]
    with fabrica.create_session() as s:
        s.execute(update(ParteRegistroOrm)
                  .where(ParteRegistroOrm.obra_ide == 704)
                  .values(sigrid_estado="registrado", recurso_ide=RECURSO))
        s.commit()
    c.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["obsoleto"]


def test_f046_t22_grupo_presente_sin_repartir_no_toca_su_reparto(fabrica):
    """El recurso pierde su codigo de hora extra: la pasada no reparte el
    grupo, pero el grupo existe y su pendiente no pasa a obsoleto."""
    _caso_real_ciclo(fabrica)
    _conciliador(fabrica).conciliar_todos()
    sin_extra = RecursoConciliador(
        repository=_repo_sqlite(fabrica),
        lookup=LookupFake(reshor=reshor_par(RECURSO, con_extra=False)),
        calendario=CalendarioFake(set()),
        indice_provider=lambda: IndiceFijo(), reajuste=True)
    sin_extra.conciliar_todos()
    assert [r.estado for r in _repartos(fabrica)] == ["pendiente"]


# ============================ repositorio: candado ============================ #

def test_f046_t22_la_clave_del_candado_no_cambia():
    """Dos revisiones de sv3 vivas a la vez (despliegue) deben pedir la
    MISMA clave: cambiarla rompe la exclusion entre ellas."""
    assert modulo.CLAVE_CANDADO_CONCILIAR == 460460001


def test_f046_t22_la_espera_se_mide_desde_que_se_empieza(monkeypatch):
    """El reloj monotono no empieza en 0: lo que cuenta es lo transcurrido."""
    con = ConexionFalsa([False, False, False, True])
    repo, _, reloj = _repo_candado(monkeypatch, con, espera=10.0)
    reloj.t = 100000.0
    with repo.candado_pasada():
        pass
    assert reloj.esperas == [0.5, 1.0, 2.0]


def test_f046_t22_si_falla_al_pedir_el_candado_no_intenta_soltarlo(
        monkeypatch):
    class ConexionRota(ConexionFalsa):
        def execute(self, sentencia, params=None):
            sql = str(sentencia)
            self.sentencias.append((sql, dict(params or {})))
            if "pg_try_advisory_lock" in sql:
                raise RuntimeError("conexion perdida")
            return super().execute(sentencia, params)
    con = ConexionRota([])
    repo, _, _ = _repo_candado(monkeypatch, con)
    with pytest.raises(RuntimeError, match="conexion perdida"), \
            repo.candado_pasada():
        pass
    assert not any("unlock" in s for s, _ in con.sentencias)
    assert con.cerrada and not con.invalidada


# ========================= repositorio: materializar ========================= #

def test_f046_t22_reparto_inexistente_o_que_ya_no_es_aplicado_se_salta(
        fabrica):
    """Entre listar y materializar, otro proceso puede cambiarlo: se salta
    sin tocar nada ni anotar error (no es un descuadre)."""
    base, _extra, _cambios = _caso_real(fabrica)
    malo = {"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 1.0, 2.0)]}         # descuadraria
    rid = _reparto(fabrica, estado="pendiente", cambios=malo,
                   resultado={"reservas": {}})
    repo = _repo_sqlite(fabrica)
    assert repo._materializar_uno(rid) is True
    assert repo._materializar_uno(rid + 1000) is True
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.error) == ("pendiente", None)
    assert _reg(fabrica, base).horas == 8.0


def test_f046_t22_si_otro_proceso_gana_el_cas_no_se_escribe_nada(
        fabrica, monkeypatch):
    base, extra, cambios = _caso_real(fabrica)
    rid = _reparto(fabrica, cambios=cambios, resultado={"reservas": {}})
    repo = _repo_sqlite(fabrica)
    original = repo._plan_materializar

    def plan_con_carrera(session, *args):
        plan, motivo = original(session, *args)
        plan.append(lambda: session.execute(
            update(RepartoPendienteOrm).where(RepartoPendienteOrm.id == rid)
            .values(estado="aplicando")))
        return plan, motivo
    monkeypatch.setattr(repo, "_plan_materializar", plan_con_carrera)
    assert repo._materializar_uno(rid) is True
    assert _fila(fabrica, rid).estado == "aplicado"     # todo revertido
    assert (_reg(fabrica, base).horas, _reg(fabrica, extra).horas) == (
        8.0, -4.0)


def test_f046_t22_linea_ya_en_despues_dentro_de_la_tolerancia(fabrica):
    """1e-6 h de «despues» (0) cuenta como ya puesta: no es descuadre."""
    (base,) = sembrar_lineas(fabrica, [{"horas": 1e-6,
                                        "estado": "registrado"}])
    _reparto(fabrica, cambios={"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 4.0, 0.0)]}, resultado={"reservas": {}})
    assert _repo_sqlite(fabrica).materializar_repartos() == {
        "materializados": 1, "descuadrados": 0}
    assert _reg(fabrica, base).horas == 1e-6


def test_f046_t22_linea_en_antes_dentro_de_la_tolerancia_se_pone(fabrica):
    """1e-6 h de «antes» (0) cuenta como «antes»: se pone «despues»."""
    (base,) = sembrar_lineas(fabrica, [{"horas": 1e-6,
                                        "estado": "registrado"}])
    _reparto(fabrica, cambios={"ids_grupo": [base], "cambios": [
        _c(base, base, "extra", 0.0, 5.0)]}, resultado={"reservas": {}})
    assert _repo_sqlite(fabrica).materializar_repartos() == {
        "materializados": 1, "descuadrados": 0}
    assert _reg(fabrica, base).horas == 5.0


def _con_extra_ya_creada(fabrica, horas_hecha, despues):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}], aprobado=True)
    (hecha,) = sembrar_lineas(fabrica, [{"horas": horas_hecha,
                                         "tipo": "extra"}],
                              document_id="doc-2")
    _reparto(fabrica, cambios={"ids_grupo": [base], "cambios": [
        _c(None, base, "extra", 0.0, despues, hora_ext=HORA_EXT,
           sigrid_estado=None)]},
        resultado={"reservas": {str(base): hecha}, "sv5": None})
    return base, hecha


def test_f046_t22_extra_nueva_ya_creada_con_sus_horas_no_es_descuadre(
        fabrica):
    """Reintento: la extra reservada ya existe con «despues»."""
    _base, hecha = _con_extra_ya_creada(fabrica, 2.5, 2.5)
    assert _repo_sqlite(fabrica).materializar_repartos() == {
        "materializados": 1, "descuadrados": 0}
    assert _reg(fabrica, hecha).horas == 2.5


def test_f046_t22_extra_nueva_ya_creada_dentro_de_la_tolerancia(fabrica):
    _con_extra_ya_creada(fabrica, 1e-6, 0.0)
    assert _repo_sqlite(fabrica).materializar_repartos() == {
        "materializados": 1, "descuadrados": 0}


def test_f046_t22_extra_materializada_no_es_incidencia(fabrica):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}], aprobado=True)
    _reparto(fabrica, cambios={"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5, sigrid_estado=None),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT,
           sigrid_estado=None)]},
        resultado={"reservas": {str(base): NUEVA}, "sv5": None})
    _repo_sqlite(fabrica).materializar_repartos()
    assert _reg(fabrica, NUEVA).es_incidencia is False


def test_f046_t22_log_de_materializacion_nombra_la_extra_nueva(fabrica,
                                                                caplog):
    (base,) = sembrar_lineas(fabrica, [{"horas": 8.0}], aprobado=True)
    rid = _reparto(fabrica, cambios={"ids_grupo": [base], "cambios": [
        _c(base, base, "ordinaria", 8.0, 5.5, sigrid_estado=None),
        _c(None, base, "extra", 0.0, 2.5, hora_ext=HORA_EXT,
           sigrid_estado=None)]},
        resultado={"reservas": {str(base): NUEVA}, "sv5": None})
    with caplog.at_level(logging.INFO):
        _repo_sqlite(fabrica).materializar_repartos()
    (texto,) = [r.getMessage() for r in caplog.records
                if f"reparto {rid} materializado" in r.getMessage()]
    assert texto.endswith(f": ordinaria {base} 8.0 -> 5.5, "
                          f"extra nueva 0.0 -> 2.5")


def test_f046_t22_error_de_descuadre_recortado_a_255(fabrica):
    """`error` es VARCHAR(255): un motivo largo se recorta."""
    enorme = 10 ** 300
    rid = _reparto(fabrica, cambios={"ids_grupo": [], "cambios": [
        _c(None, enorme, "extra", 0.0, 2.5)]}, resultado={"reservas": {}})
    assert _repo_sqlite(fabrica).materializar_repartos()["descuadrados"] == 1
    error = _fila(fabrica, rid).error
    assert len(error) == 255
    assert error.startswith("descuadre al materializar: sin id reservado")


# ======================= repositorio: guardar (misma firma) ======================= #

def _guardar(fabrica, estado, cambios):
    _reparto(fabrica, estado=estado, firma="a" * 64)
    _repo_sqlite(fabrica).guardar_repartos([{
        "recurso_ide": RECURSO, "fecha_int": FECHA,
        "firma": "a" * 64, "cambios": cambios}], [])
    with fabrica.create_session() as s:
        return [f.estado for f in s.query(RepartoPendienteOrm).order_by(
            RepartoPendienteOrm.id)]


@pytest.mark.parametrize("estado,esperado", [
    ("pendiente", ["obsoleto"]),
    ("materializado", ["obsoleto"]),
    ("rechazado", ["rechazado"]),
    ("mantenido", ["mantenido"]),
])
def test_f046_t22_sin_propuesta_misma_firma(estado, esperado):
    """R13/R14 sin propuesta y con la MISMA firma: el pendiente o el
    materializado pasan a obsoleto; el rechazo del humano se respeta."""
    assert _guardar(FabricaSesionSqlite(), estado, None) == esperado


@pytest.mark.parametrize("estado", ["rechazado", "mantenido",
                                    "materializado"])
def test_f046_t22_con_propuesta_misma_firma_nace_otro_pendiente(estado):
    """Con propuesta y la MISMA firma, solo un `pendiente` se queda; lo
    demas pasa a obsoleto y nace el pendiente."""
    fabrica = FabricaSesionSqlite()
    _base, _extra, cambios = _caso_real(fabrica)
    assert _guardar(fabrica, estado, cambios) == ["obsoleto", "pendiente"]


def test_f046_t22_la_extra_nueva_se_enriquece_desde_su_base(fabrica):
    base, _extra, _cambios = _caso_real(fabrica)
    _repo_sqlite(fabrica).guardar_repartos([{
        "recurso_ide": RECURSO, "fecha_int": FECHA,
        "firma": "a" * 64, "cambios": {"ids_grupo": [base], "cambios": [
            _c(None, base, "extra", 0.0, 2.5)]}}], [])
    (rep,) = _repartos(fabrica)
    (c,) = json.loads(rep.cambios)["cambios"]
    assert (c["document_id"], c["obra_codigo"]) == ("doc-1", "0100")
    assert "hmores_ide" not in c
