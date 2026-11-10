# tests/test_f052_repositorio.py
"""F-052 en sv4: lecturas del repositorio para sincronizar (R7, R12).

- `lineas_para_sincronizar`: las líneas activas del ámbito (obra
  `obr-{ide}` o persona `rec-{R}`, F-050) con fecha en el periodo; fuera la
  papelera y los partes inactivos. Periodo de nómina y natural.
- `donde_estan` (R12, DA16): `papelera`, `parte_reemplazado` (parte
  desactivado por la reingesta de sv3), `otro_ambito` o `no_existe`.

SQLite en memoria con el ORM real; datos sintéticos.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from application.services.calendar_builder import period_bounds
from application.services.seguimiento_recalculo import MOTIVO_RECALCULANDO
from application.services.sincronizacion import LineaPortal
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    RepartoPendienteOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import (
    MOTIVO_REPARTO_SINCRONIZAR,
    MOTIVO_SINCRONIZAR_CAMBIO,
    ParteReviewRepository,
    _mismas_horas,
)
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-10-20T08:00:00+00:00"


def _doc(s, did: str, *, obra_ide: int | None = 686, activo: bool = True,
         deleted_by: str | None = None,
         deleted_at: str | None = None) -> None:
    s.add(ParteDocumentOrm(
        id=did, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + did,
        fecha="2026-10-14", fecha_int=20261014, created_at_utc=AHORA,
        obra_ide=obra_ide, obra_codigo="0686", obra_nombre="Obra",
        is_active=activo, deleted_by=deleted_by, deleted_at_utc=deleted_at))


def _reg(s, did: str, fecha_int: int, **cambios) -> int:
    base = dict(document_id=did, line_index=0, fecha=str(fecha_int),
                fecha_int=fecha_int, obra_ide=686, obra_codigo="0686",
                obra_nombre="Obra", empleado_ide=77, recurso_ide=501,
                tipo_hora="normal", horas=8.0, hora_ide=3,
                hora_codigo="HL01", partida_ide=11, partida_cod="P1")
    base.update(cambios)
    reg = ParteRegistroOrm(**base)
    s.add(reg)
    s.flush()
    return reg.id


@pytest.fixture
def repo():
    fabrica = FabricaSesionSqlite()
    return fabrica, ParteReviewRepository(fabrica)


def _sembrar(fabrica) -> dict[str, int]:
    ids: dict[str, int] = {}
    with fabrica.create_session() as s:
        _doc(s, "a")
        _doc(s, "otra", obra_ide=999)
        _doc(s, "inactivo", activo=False)
        ids["sep16"] = _reg(s, "a", 20260916)
        ids["oct01"] = _reg(s, "a", 20261001)
        ids["oct15"] = _reg(s, "a", 20261015, tipo_hora="extra",
                            sigrid_estado="registrado",
                            sigrid_hmores_ide=9001, sigrid_hmoide=7001,
                            sigrid_motivo="m")
        ids["oct16"] = _reg(s, "a", 20261016, hora_ext=1, horas=None)
        ids["oct31"] = _reg(s, "a", 20261031, es_incidencia=True,
                            hora_codigo="CIV")
        ids["nov01"] = _reg(s, "a", 20261101)
        ids["papelera"] = _reg(s, "a", 20261010, deleted_at_utc=AHORA)
        ids["inactivo"] = _reg(s, "inactivo", 20261010)
        ids["otra_obra"] = _reg(s, "otra", 20261010, obra_ide=999)
        ids["reside"] = _reg(s, "otra", 20261011, obra_ide=999,
                             recurso_ide=None, empleado_reside=501)
        ids["sin_casar"] = _reg(s, "otra", 20261012, obra_ide=999,
                                empleado_ide=None,
                                trabajador_nombre_leido="Leido")
        ids["otro_recurso"] = _reg(s, "otra", 20261013, obra_ide=999,
                                   recurso_ide=502)
        s.commit()
    return ids


def _ids(lineas) -> list[int]:
    return [l.registro_id for l in lineas]


@pytest.mark.parametrize("modo, esperados", [
    ("natural", ["oct01", "oct15", "oct16", "oct31"]),
    ("nomina", ["sep16", "oct01", "oct15"]),
])
def test_f052_r7_obra_en_el_periodo_sin_papelera(repo, modo,
                                                 esperados) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    desde, hasta = period_bounds(2026, 10, modo)
    lineas = r.lineas_para_sincronizar(
        obra_ide=686, desde=int(desde.strftime("%Y%m%d")),
        hasta=int(hasta.strftime("%Y%m%d")))
    assert _ids(lineas) == sorted(ids[k] for k in esperados)


def test_f052_r7_persona_rec_por_recurso_y_reside_casada(repo) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    lineas = r.lineas_para_sincronizar(recurso_ide=501, desde=20261001,
                                       hasta=20261031)
    assert _ids(lineas) == sorted(
        ids[k] for k in ("oct01", "oct15", "oct16", "oct31", "otra_obra",
                         "reside"))


def test_f052_r7_linea_portal_con_lo_que_compara(repo) -> None:
    fabrica, r = repo
    ids = _sembrar(fabrica)
    por_id = {l.registro_id: l for l in r.lineas_para_sincronizar(
        recurso_ide=501, desde=20261001, hasta=20261031)}
    assert por_id[ids["oct15"]] == LineaPortal(
        registro_id=ids["oct15"], fecha_int=20261015, recurso_ide=501,
        obra_ide=686, horas=8.0, extra=True, es_incidencia=False,
        hora_codigo="HL01", partida_ide=11, partida_cod="P1",
        sigrid_estado="registrado", sigrid_motivo="m",
        sigrid_hmores_ide=9001, sigrid_hmoide=7001)
    assert por_id[ids["oct16"]].extra is True
    assert por_id[ids["oct16"]].horas is None
    assert por_id[ids["oct01"]].extra is False
    assert por_id[ids["oct31"]].es_incidencia is True
    assert por_id[ids["reside"]].recurso_ide == 501
    assert por_id[ids["reside"]].obra_ide == 999


@pytest.mark.parametrize("kwargs", [{}, {"obra_ide": 1, "recurso_ide": 2}])
def test_f052_r7_exige_obra_o_recurso(repo, kwargs) -> None:
    _f, r = repo
    with pytest.raises(ValueError):
        r.lineas_para_sincronizar(desde=20261001, hasta=20261031, **kwargs)


def test_f052_r7_sin_lineas_lista_vacia(repo) -> None:
    _f, r = repo
    assert r.lineas_para_sincronizar(obra_ide=686, desde=20261001,
                                     hasta=20261031) == []


# ------------------------------ donde_estan ------------------------------ #

def test_f052_r12_donde_estan(repo) -> None:
    fabrica, r = repo
    with fabrica.create_session() as s:
        _doc(s, "vivo")
        _doc(s, "en_papelera", activo=False, deleted_by="ana",
             deleted_at=AHORA)
        _doc(s, "retirado", activo=False, deleted_by="retirado:ana")
        _doc(s, "reemplazado", activo=False)
        viva = _reg(s, "vivo", 20261014)
        borrada = _reg(s, "vivo", 20261014, deleted_at_utc=AHORA)
        doc_papelera = _reg(s, "en_papelera", 20261014)
        retirado = _reg(s, "retirado", 20261014, deleted_at_utc=AHORA)
        reemplazado = _reg(s, "reemplazado", 20261014)
        s.commit()
    assert r.donde_estan([viva, borrada, doc_papelera, retirado,
                          reemplazado, 99999, viva]) == {
        viva: "otro_ambito", borrada: "papelera",
        doc_papelera: "papelera", retirado: "papelera",
        reemplazado: "parte_reemplazado", 99999: "no_existe"}


def test_f052_r12_donde_estan_sin_ids(repo) -> None:
    _f, r = repo
    assert r.donde_estan([]) == {}


# ============ T9 · escrituras de las acciones (R19-R22, DA15) ============ #

ACCION_AT = "2026-11-03T09:30:00+00:00"


def _fila(fabrica, rid: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


def _sembrar_acciones(fabrica, *, aprobado: bool = True,
                      en_espera: bool = False) -> dict[str, int]:
    """Un parte (aprobado por defecto) con líneas de cada estado."""
    ids: dict[str, int] = {}
    with fabrica.create_session() as s:
        _doc(s, "d")
        _doc(s, "inactivo", activo=False)
        s.flush()
        doc = s.get(ParteDocumentOrm, "d")
        doc.approved = aprobado
        if en_espera:
            doc.recalculo_pedido_id = "pedido-1"
            doc.recalculo_pedido_at_utc = datetime.now(
                timezone.utc).isoformat()
        ids["error"] = _reg(s, "d", 20261014, sigrid_estado="error",
                            sigrid_motivo="timeout de sv5")
        ids["vacio"] = _reg(s, "d", 20261015, recurso_ide=502)
        ids["borrado"] = _reg(s, "d", 20261016, recurso_ide=503,
                              sigrid_estado="borrado_sigrid",
                              sigrid_hmores_ide=9016)
        ids["reg"] = _reg(s, "d", 20261020, sigrid_estado="registrado",
                          sigrid_hmores_ide=9020, sigrid_hmoide=7001,
                          horas_orig=9.0)
        ids["reg2"] = _reg(s, "d", 20261021, sigrid_estado="registrado",
                           sigrid_hmores_ide=9021, sigrid_hmoide=7001)
        ids["papelera"] = _reg(s, "d", 20261022, sigrid_estado="error",
                               deleted_at_utc=AHORA)
        ids["inactivo"] = _reg(s, "inactivo", 20261023, sigrid_estado="error")
        s.commit()
    return ids


def _marca(rid: int, estado: str | None, *, visto: int | None = None,
           hmores: int = 9100) -> dict:
    return {"registro_id": rid, "estado_visto": estado,
            "hmores_ide_visto": visto, "hmores_ide": hmores, "hmoide": 7100,
            "parte_cod": "PT26/00100"}


def _trae(rid: int, *, vistas: float = 8.0, nuevas: float = 6.0,
          visto: int | None = 9020) -> dict:
    return {"registro_id": rid, "horas_vistas": vistas,
            "horas_nuevas": nuevas, "hmores_ide_visto": visto}


# ------------------------- aplicar_marcar_registrada ---------------------- #

def test_f052_r19_marcar_registrada_escribe_estado_y_referencias(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    res = r.aplicar_marcar_registrada(
        [_marca(ids["error"], "error"),
         _marca(ids["vacio"], None, hmores=9101),
         _marca(ids["borrado"], "borrado_sigrid", visto=9016, hmores=9102)],
        actor="ana@x", ahora_iso=ACCION_AT)
    assert res == {"aplicados": sorted([ids["error"], ids["vacio"],
                                        ids["borrado"]]), "descartados": []}
    f = _fila(fabrica, ids["error"])
    assert (f.sigrid_estado, f.sigrid_hmores_ide, f.sigrid_hmoide,
            f.sigrid_parte_cod) == ("registrado", 9100, 7100, "PT26/00100")
    assert f.sigrid_registrado_by == "ana@x"
    assert f.sigrid_registrado_at_utc == ACCION_AT
    assert f.sigrid_motivo == (
        "Sincronizado con Sigrid: estado error→registrado · ana@x · "
        "2026-11-03")
    assert _fila(fabrica, ids["vacio"]).sigrid_motivo.startswith(
        "Sincronizado con Sigrid: estado sin estado→registrado")
    assert _fila(fabrica, ids["borrado"]).sigrid_hmores_ide == 9102


@pytest.mark.parametrize("clave, item, motivo", [
    ("error", lambda i: _marca(i, "omitido"), "cambió"),
    ("borrado", lambda i: _marca(i, "borrado_sigrid", visto=1), "cambió"),
    ("papelera", lambda i: _marca(i, "error"), "papelera"),
    ("inactivo", lambda i: _marca(i, "error"), "papelera"),
    ("reg", lambda i: _marca(i, "registrado", visto=9020), "no se marca"),
])
def test_f052_r19_marcar_registrada_cas_descarta_sin_escribir(
        repo, clave, item, motivo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    antes = _fila(fabrica, ids[clave])
    res = r.aplicar_marcar_registrada([item(ids[clave])], actor="ana",
                                      ahora_iso=ACCION_AT)
    assert res["aplicados"] == []
    assert [d["registro_id"] for d in res["descartados"]] == [ids[clave]]
    assert motivo in res["descartados"][0]["motivo"]
    despues = _fila(fabrica, ids[clave])
    assert (despues.sigrid_estado, despues.sigrid_hmores_ide,
            despues.sigrid_motivo, despues.sigrid_registrado_by) == (
        antes.sigrid_estado, antes.sigrid_hmores_ide, antes.sigrid_motivo,
        antes.sigrid_registrado_by)


def test_f052_r19_marcar_registrada_id_que_no_existe(repo) -> None:
    _f, r = repo
    res = r.aplicar_marcar_registrada([_marca(99999, "error")], actor="ana",
                                      ahora_iso=ACCION_AT)
    assert res == {"aplicados": [], "descartados": [
        {"registro_id": 99999, "motivo": "la línea ya no existe"}]}


def test_f052_r19_marcar_registrada_mezcla_aplica_lo_que_cuadra(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    res = r.aplicar_marcar_registrada(
        [_marca(ids["error"], "error"), _marca(ids["vacio"], "error")],
        actor="ana", ahora_iso=ACCION_AT)
    assert res["aplicados"] == [ids["error"]]
    assert [d["registro_id"] for d in res["descartados"]] == [ids["vacio"]]
    assert _fila(fabrica, ids["vacio"]).sigrid_estado is None


# ------------------------- aplicar_traer_de_sigrid ------------------------ #

def test_f052_r20_traer_horas_aunque_este_congelada(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)            # parte aprobado + registrado
    res = r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor="ana@x",
                                    ahora_iso=ACCION_AT)
    assert res == {"aplicados": [ids["reg"]], "descartados": [],
                   "documentos": ["d"], "pares": [(501, 20261020)]}
    f = _fila(fabrica, ids["reg"])
    assert f.horas == 6.0
    assert f.horas_orig == 9.0                  # sv3 no recalcula lo congelado
    assert f.sigrid_estado == "registrado"
    assert f.sigrid_hmores_ide == 9020
    assert f.sigrid_motivo == (
        "Sincronizado con Sigrid: horas 8→6 · ana@x · 2026-11-03")


def test_f052_r20_traer_anulada_deja_cero(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    res = r.aplicar_traer_de_sigrid(
        [_trae(ids["reg"], nuevas=0.0)], actor="ana", ahora_iso=ACCION_AT)
    assert res["aplicados"] == [ids["reg"]]
    assert _fila(fabrica, ids["reg"]).horas == 0.0
    assert "horas 8→0" in _fila(fabrica, ids["reg"]).sigrid_motivo


@pytest.mark.parametrize("clave, item, motivo", [
    ("reg", lambda i: _trae(i, vistas=7.0), "cambió"),
    ("reg", lambda i: _trae(i, visto=1), "cambió"),
    ("error", lambda i: _trae(i, visto=None), "registrado"),
    ("papelera", lambda i: _trae(i, visto=None), "papelera"),
    ("inactivo", lambda i: _trae(i, visto=None), "papelera"),
])
def test_f052_r20_traer_cas_descarta_sin_escribir(repo, clave, item,
                                                  motivo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    antes = _fila(fabrica, ids[clave])
    res = r.aplicar_traer_de_sigrid([item(ids[clave])], actor="ana",
                                    ahora_iso=ACCION_AT)
    assert res["aplicados"] == [] and res["documentos"] == []
    assert res["pares"] == []
    assert [d["registro_id"] for d in res["descartados"]] == [ids[clave]]
    assert motivo in res["descartados"][0]["motivo"]
    despues = _fila(fabrica, ids[clave])
    assert (despues.horas, despues.sigrid_motivo) == (antes.horas,
                                                      antes.sigrid_motivo)


def test_f052_r20_traer_id_que_no_existe(repo) -> None:
    _f, r = repo
    res = r.aplicar_traer_de_sigrid([_trae(99999)], actor="ana",
                                    ahora_iso=ACCION_AT)
    assert res["descartados"] == [{"registro_id": 99999,
                                   "motivo": "la línea ya no existe"}]


def test_f052_r21_traer_parte_en_espera_descarta(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica, en_espera=True)
    res = r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor="ana",
                                    ahora_iso=ACCION_AT)
    assert res["aplicados"] == []
    assert res["descartados"] == [{"registro_id": ids["reg"],
                                   "motivo": MOTIVO_RECALCULANDO}]
    assert _fila(fabrica, ids["reg"]).horas == 8.0


@pytest.mark.parametrize("estado, bloquea", [
    ("pendiente", True), ("aplicando", True), ("rechazado", True),
    ("aplicado", False), ("obsoleto", False)])
def test_f052_r21_traer_dia_con_reparto_que_bloquea(repo, estado,
                                                     bloquea) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    with fabrica.create_session() as s:
        s.add(RepartoPendienteOrm(recurso_ide=501, fecha_int=20261020,
                                  estado=estado, firma="f", cambios="{}"))
        s.commit()
    res = r.aplicar_traer_de_sigrid(
        [_trae(ids["reg"]), _trae(ids["reg2"], visto=9021)], actor="ana",
        ahora_iso=ACCION_AT)
    if bloquea:
        assert res["aplicados"] == [ids["reg2"]]
        assert res["descartados"] == [{"registro_id": ids["reg"],
                                       "motivo": MOTIVO_REPARTO_SINCRONIZAR}]
        assert _fila(fabrica, ids["reg"]).horas == 8.0
    else:
        assert res["aplicados"] == [ids["reg"], ids["reg2"]]
    assert res["pares"] == sorted({(501, f) for f in (
        [20261021] if bloquea else [20261020, 20261021])})


def test_f052_r20_traer_sin_deshacer(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor="ana",
                              ahora_iso=ACCION_AT)
    r.aplicar_marcar_registrada([_marca(ids["error"], "error")],
                                actor="ana", ahora_iso=ACCION_AT)
    with fabrica.create_session() as s:
        assert s.query(UndoLogOrm).count() == 0


def test_f052_r22_motivo_cabe_en_255(repo) -> None:
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    actor = "x" * 400
    r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor=actor,
                              ahora_iso=ACCION_AT)
    r.aplicar_marcar_registrada([_marca(ids["error"], "error")],
                                actor=actor, ahora_iso=ACCION_AT)
    assert len(_fila(fabrica, ids["reg"]).sigrid_motivo) == 255
    assert len(_fila(fabrica, ids["error"]).sigrid_motivo) == 255


def test_f052_r22_motivo_cambio_formato() -> None:
    assert MOTIVO_SINCRONIZAR_CAMBIO.format(
        cambio="horas 8→6", actor="ana", fecha="2026-11-03") == (
        "Sincronizado con Sigrid: horas 8→6 · ana · 2026-11-03")


# ------------------------- documentos_de_los_dias ------------------------- #

def test_f052_r23_documentos_de_los_dias(repo) -> None:
    fabrica, r = repo
    with fabrica.create_session() as s:
        for did in ("a", "b", "c", "papelera", "inactivo", "otro_dia"):
            _doc(s, did, activo=did != "inactivo")
        _reg(s, "a", 20261020)
        _reg(s, "b", 20261020, obra_ide=999)
        _reg(s, "c", 20261021, recurso_ide=777)
        _reg(s, "papelera", 20261020, deleted_at_utc=AHORA)
        _reg(s, "inactivo", 20261020)
        _reg(s, "otro_dia", 20261022)
        s.commit()
    assert r.documentos_de_los_dias([(501, 20261020), (777, 20261021)]) == [
        "a", "b", "c"]
    assert r.documentos_de_los_dias([]) == []


# ------------- supervivientes de la mutación (mutacion_F-052.md) -------- #

@pytest.mark.parametrize("a, b, iguales", [
    (None, None, True), (None, 8.0, False), (8.0, None, False),
    (8.0, 8.0, True), (1e-9, 0.0, False), (0.0, 1e-9, False)])
def test_f052_r20_cas_de_horas_mismas_horas(a, b, iguales) -> None:
    """El CAS de `traer` (R20): NULL solo casa con NULL y la tolerancia
    es estricta (mutantes 19-23)."""
    assert _mismas_horas(a, b) is iguales


def test_f052_r20_traer_horas_nulas_en_la_base_no_casan_con_lo_visto(
        repo) -> None:
    """Si la base tiene horas NULL y el usuario vio 8, la línea cambió
    (mutante 19: sin la guarda revienta con `float(None)`)."""
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["reg"]).horas = None
        s.commit()
    res = r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor="ana",
                                    ahora_iso=ACCION_AT)
    assert res["aplicados"] == []
    assert "cambió" in res["descartados"][0]["motivo"]


def test_f052_r12_donde_estan_parte_con_solo_una_marca_de_borrado(
        repo) -> None:
    """Un parte inactivo con `deleted_by` O `deleted_at_utc` (no los dos)
    está en la papelera; reemplazado es solo sin ninguno (mutante 24)."""
    fabrica, r = repo
    with fabrica.create_session() as s:
        _doc(s, "solo_by", activo=False, deleted_by="retirado:ana")
        _doc(s, "solo_at", activo=False, deleted_at=AHORA)
        solo_by = _reg(s, "solo_by", 20261014)
        solo_at = _reg(s, "solo_at", 20261014)
        s.commit()
    assert r.donde_estan([solo_by, solo_at]) == {solo_by: "papelera",
                                                  solo_at: "papelera"}


class _SesionQueApunta:
    """Sesión mínima: apunta cada `get` y no encuentra nada."""

    def __init__(self) -> None:
        self.gets: list[tuple[int, dict]] = []

    def get(self, _modelo, ide, **kwargs):
        self.gets.append((ide, kwargs))


def test_f052_r20_bloqueo_for_update_en_orden_de_id() -> None:
    """R20: cada línea se lee con SELECT ... FOR UPDATE y en orden de id
    (sin interbloqueos). SQLite no bloquea, así que se mira la llamada
    (mutante 25: `with_for_update=False`)."""
    sesion = _SesionQueApunta()
    out = ParteReviewRepository._bloquear_para_sincronizar(
        sesion, [{"registro_id": 7}, {"registro_id": 3}])
    assert sesion.gets == [(3, {"with_for_update": True}),
                           (7, {"with_for_update": True})]
    assert [m for _i, _r, m in out] == ["la línea ya no existe"] * 2


def test_f052_r20_traer_a_linea_sin_estado_lo_dice(repo) -> None:
    """Sin estado de Sigrid, el descarte dice «sin estado» (mutante 26)."""
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    res = r.aplicar_traer_de_sigrid([_trae(ids["vacio"], visto=None)],
                                    actor="ana", ahora_iso=ACCION_AT)
    assert res["aplicados"] == []
    assert "«sin estado»" in res["descartados"][0]["motivo"]


def test_f052_r23_traer_linea_sin_recurso_no_da_par_de_dia(repo) -> None:
    """Sin recurso (ni `recurso_ide` ni `empleado_reside`) la línea se
    trae pero no aporta (recurso, fecha) al recálculo del día (mutante
    27: `and` -> `or` revienta con `int(None)`)."""
    fabrica, r = repo
    ids = _sembrar_acciones(fabrica)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["reg"]).recurso_ide = None
        s.commit()
    res = r.aplicar_traer_de_sigrid([_trae(ids["reg"])], actor="ana",
                                    ahora_iso=ACCION_AT)
    assert res["aplicados"] == [ids["reg"]]
    assert res["documentos"] == ["d"] and res["pares"] == []
