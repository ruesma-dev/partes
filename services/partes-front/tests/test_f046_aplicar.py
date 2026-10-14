# tests/test_f046_aplicar.py
"""F-046 · «Aplicar» / «Mantener lo registrado» en sv4 (R32-R35, R38).

Repositorio contra SQLite en memoria (`FabricaSesionSqlite`, el mismo ORM
que produccion): CAS sobre `reparto_pendiente.estado`, comprobaciones
antes de aplicar, reserva de ids y exclusion de las lineas sin decision.
Datos sinteticos: el DNI y el nombre son los ficticios de `dobles`.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from application.services.reparto_aviso import (
    MOTIVO_PENDIENTE,
    RepartoCambiadoError,
)
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

FECHA = 20260302
RECURSO = 501


@pytest.fixture
def fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _repo(fabrica) -> ParteReviewRepository:
    return ParteReviewRepository(fabrica)  # type: ignore[arg-type]


def _marcar(fabrica, rid, **campos):
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _dia(fabrica, *, nueva=False):
    """0678 registrada 8 + (-4) y 0704 libre (ya con el ideal 5,5 + 2,5
    que dejo sv3). Con `nueva`, la 0678 no tiene extra (R7)."""
    lineas = [{"estado": "registrado", "horas": 8.0}]
    if not nueva:
        lineas.append({"estado": "registrado", "horas": -4.0,
                       "tipo": "extra"})
    ids678 = sembrar_parte(fabrica, lineas, document_id="doc-678",
                           obra_ide=678, obra_codigo="0678")
    libre, libre_extra = sembrar_parte(
        fabrica, [{"horas": 5.5}, {"horas": 2.5, "tipo": "extra"}],
        document_id="doc-704", obra_ide=704, obra_codigo="0704")
    _marcar(fabrica, libre_extra, extra_auto=True)
    if not nueva:
        _marcar(fabrica, ids678[1], extra_auto=True)
    return ids678, libre, libre_extra


def _cambio(rid, base, tipo, antes, despues, estado="registrado", **kw):
    d = {"registro_id": rid, "base_registro_id": base, "tipo": tipo,
         "antes": antes, "despues": despues, "sigrid_estado": estado,
         "obra_codigo": "0678", "obra_ide": 678, "document_id": "doc-678"}
    d.update(kw)
    return d


def _reparto(fabrica, cambios, ids_grupo, *, estado="pendiente",
             resultado=None) -> int:
    with fabrica.create_session() as s:
        fila = RepartoPendienteOrm(
            recurso_ide=RECURSO, fecha_int=FECHA, estado=estado,
            firma="f" * 64,
            cambios=json.dumps({"ids_grupo": ids_grupo, "cambios": cambios}),
            resultado=resultado, creado_at_utc="x", actualizado_at_utc="x")
        s.add(fila)
        s.commit()
        return fila.id


def _caso_real(fabrica):
    (base, extra), libre, libre_extra = _dia(fabrica)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 2.5),
                             _cambio(extra, base, "extra", -4.0, 1.5)],
                   [base, extra, libre])
    return rid, base, extra, libre, libre_extra


def _fila(fabrica, rid) -> RepartoPendienteOrm:
    with fabrica.create_session() as s:
        return s.get(RepartoPendienteOrm, rid)


# ------------------------------- lectura ------------------------------- #

def test_f046_r30_repositorio_repartos_de_registros(fabrica):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    (f,) = _repo(fabrica).repartos_de_registros([libre, libre_extra])
    assert (f["id"], f["estado"], f["recurso_ide"], f["fecha_int"]) == (
        rid, "pendiente", RECURSO, FECHA)
    assert sorted(f["registro_ids"]) == sorted([libre, libre_extra])
    assert [(c["registro_id"], c["parte_cod"]) for c in f["cambios"]] == [
        (base, "PT26/00001"), (extra, "PT26/00001")]
    assert f["document_ids"] == ["doc-678", "doc-704"]


def test_f046_r30_repositorio_sin_reparto_vivo_no_hay_nada(fabrica):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "obsoleto"
        s.commit()
    assert _repo(fabrica).repartos_de_registros([libre]) == []


def test_f046_r30_repositorio_completa_la_extra_nueva_con_su_base(fabrica):
    (base,), libre, _le = _dia(fabrica, nueva=True)
    _marcar(fabrica, base, partida_ide=33, partida_cod="P-33")
    _reparto(fabrica, [
        _cambio(base, base, "ordinaria", 8.0, 5.5),
        _cambio(None, base, "extra", 0.0, 2.5,
                hora_ext={"ide": 9, "cod": "HE01", "desc": "x", "ext": 1})],
        [base, libre])
    (f,) = _repo(fabrica).repartos_de_registros([libre])
    nueva = f["cambios"][1]
    assert (nueva["recurso_ide"], nueva["fecha_int"], nueva["partida_ide"],
            nueva["partida_cod"], nueva["obra_ide"], nueva["obra_codigo"],
            nueva["hora_ide"], nueva["hora_codigo"], nueva["parte_cod"]) == (
        RECURSO, FECHA, 33, "P-33", 678, "0678", 9, "HE01", "PT26/00001")


def test_f046_r37_repositorio_registros_con_reparto(fabrica):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    repo = _repo(fabrica)
    assert repo.registros_con_reparto([base, extra, libre, libre_extra,
                                       otro]) == {base, extra, libre,
                                                  libre_extra}
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "mantenido"
        s.commit()
    assert repo.registros_con_reparto([base, libre]) == set()


# ------------------------------- R33 ------------------------------- #

def test_f046_r33_repositorio_iniciar_pasa_a_aplicando(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    f = _repo(fabrica).iniciar_aplicacion(rid, actor="admin@test")
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decision, fila.decidido_por) == (
        "aplicando", "aplicar", "admin@test")
    assert fila.decidido_at_utc
    assert f["id"] == rid and f["reservas"] == {}


def test_f046_r33_repositorio_cas_mantener_tras_aplicar_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    with pytest.raises(RepartoCambiadoError):
        repo.rechazar_reparto(rid, actor="b")
    assert _fila(fabrica, rid).estado == "aplicando"


def test_f046_r33_repositorio_cas_aplicar_tras_mantener_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.rechazar_reparto(rid, actor="a")
    with pytest.raises(RepartoCambiadoError):
        repo.iniciar_aplicacion(rid, actor="b")
    assert _fila(fabrica, rid).estado == "rechazado"


@pytest.mark.parametrize("estado", ["aplicado", "materializado",
                                    "obsoleto", "mantenido"])
def test_f046_r33_repositorio_solo_se_aplica_lo_pendiente(fabrica, estado):
    rid, *_ = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = estado
        s.commit()
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r34_repositorio_reintento_desde_aplicando_conserva_reservas(
        fabrica):
    (base,), libre, _le = _dia(fabrica, nueva=True)
    rid = _reparto(fabrica, [_cambio(base, base, "ordinaria", 8.0, 5.5),
                             _cambio(None, base, "extra", 0.0, 2.5)],
                   [base, libre])
    repo = _repo(fabrica)
    primero = repo.iniciar_aplicacion(rid, actor="a")
    segundo = repo.iniciar_aplicacion(rid, actor="a")
    assert primero["reservas"] == segundo["reservas"]
    (reservado,) = primero["reservas"].values()
    assert reservado > libre                  # mas alla de los ids vivos
    assert json.loads(_fila(fabrica, rid).resultado)["reservas"] == {
        str(base): reservado}


def test_f046_r33_repositorio_linea_cambiada_es_409_sin_tocar_nada(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, horas=7.0)
    with pytest.raises(RepartoCambiadoError, match="cambi"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")
    assert _fila(fabrica, rid).estado == "pendiente"


def test_f046_r33_repositorio_estado_cambiado_es_409(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, sigrid_estado="borrado_sigrid")
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_linea_nueva_en_el_grupo_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    sembrar_parte(fabrica, [{"horas": 2.0}], document_id="doc-nuevo")
    with pytest.raises(RepartoCambiadoError, match="nuevas"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_linea_del_grupo_en_la_papelera_es_409(fabrica):
    rid, base, *_ = _caso_real(fabrica)
    _marcar(fabrica, base, deleted_at_utc="2026-03-03T00:00:00+00:00")
    with pytest.raises(RepartoCambiadoError):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_documento_en_espera_es_409(fabrica):
    rid, *_ = _caso_real(fabrica)
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, "doc-704")
        doc.recalculo_pedido_id = "p-1"
        doc.recalculo_pedido_at_utc = datetime.now(timezone.utc).isoformat()
        s.commit()
    with pytest.raises(RepartoCambiadoError, match="recalcul"):
        _repo(fabrica).iniciar_aplicacion(rid, actor="a")


def test_f046_r33_repositorio_cerrar_ok_es_aplicado_con_la_respuesta(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=True, sv5={"ok": True,
                                                     "lineas": [1]},
                                  error=None, actor="a") == "aplicado"
    fila = _fila(fabrica, rid)
    assert fila.estado == "aplicado" and fila.error is None
    assert json.loads(fila.resultado) == {"reservas": {},
                                          "sv5": {"ok": True, "lineas": [1]}}


def test_f046_r34_repositorio_rechazo_de_sv5_vuelve_a_pendiente(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=False, sv5={"ok": False},
                                  error="no editable", actor="a") == \
        "pendiente"
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.error) == ("pendiente", "no editable")


def test_f046_r34_repositorio_sin_respuesta_sigue_aplicando(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    assert repo.cerrar_aplicacion(rid, ok=None, sv5=None, error="timeout",
                                  actor="a") == "aplicando"
    assert (_fila(fabrica, rid).estado, _fila(fabrica, rid).error) == (
        "aplicando", "timeout")


# ------------------------------- R35 / R38 ------------------------------- #

def test_f046_r35_repositorio_mantener_pasa_a_rechazado_y_firma(fabrica):
    rid, *_ = _caso_real(fabrica)
    f = _repo(fabrica).rechazar_reparto(rid, actor="admin@test")
    fila = _fila(fabrica, rid)
    assert (fila.estado, fila.decision, fila.decidido_por) == (
        "rechazado", "mantener", "admin@test")
    # Los partes de sus lineas NO congeladas, para pedir el recalculo.
    assert f["documentos_libres"] == ["doc-704"]


def test_f046_r35_repositorio_mantener_dos_veces_es_idempotente(fabrica):
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.rechazar_reparto(rid, actor="a")
    repo.rechazar_reparto(rid, actor="a")
    assert _fila(fabrica, rid).estado == "rechazado"


def test_f046_r38_repositorio_la_decision_no_entra_en_undo_log(fabrica):
    from infrastructure.database.orm_models import UndoLogOrm
    rid, *_ = _caso_real(fabrica)
    repo = _repo(fabrica)
    repo.iniciar_aplicacion(rid, actor="a")
    repo.cerrar_aplicacion(rid, ok=True, sv5=None, error=None, actor="a")
    with fabrica.create_session() as s:
        assert s.query(UndoLogOrm).count() == 0


# ------------------------------- R32 ------------------------------- #

def test_f046_r32_repositorio_sin_decision_no_viajan(fabrica):
    rid, base, extra, libre, libre_extra = _caso_real(fabrica)
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x",
                            fecha="2026-03-03")
    datos = _repo(fabrica).lineas_para_registro([libre, libre_extra, otro])
    assert [l["registro_id"] for l in datos["lineas"]] == [otro]
    assert datos["excluidas"]["reparto_pendiente"] == 2
    motivos = {d["registro_id"]: (d["estado"], d["motivo"])
               for d in datos["excluidas_detalle"]}
    assert motivos[libre] == ("reparto_pendiente", MOTIVO_PENDIENTE)


def test_f046_r32_repositorio_con_decision_aplicar_viajan(fabrica):
    rid, _b, _e, libre, libre_extra = _caso_real(fabrica)
    datos = _repo(fabrica).lineas_para_registro(
        [libre, libre_extra], repartos_decididos=frozenset({rid}))
    assert sorted(l["registro_id"] for l in datos["lineas"]) == sorted(
        [libre, libre_extra])
    assert "reparto_pendiente" not in datos["excluidas"]


def test_f046_r32_repositorio_aplicado_ya_no_excluye(fabrica):
    rid, _b, _e, libre, _le = _caso_real(fabrica)
    with fabrica.create_session() as s:
        s.get(RepartoPendienteOrm, rid).estado = "aplicado"
        s.commit()
    datos = _repo(fabrica).lineas_para_registro([libre])
    assert [l["registro_id"] for l in datos["lineas"]] == [libre]


def test_f046_r32_repositorio_sin_reparto_igual_que_siempre(fabrica):
    (otro,) = sembrar_parte(fabrica, [{"horas": 8.0}], document_id="doc-x")
    datos = _repo(fabrica).lineas_para_registro([otro])
    assert "reparto_pendiente" not in datos["excluidas"]
    assert [l["registro_id"] for l in datos["lineas"]] == [otro]
