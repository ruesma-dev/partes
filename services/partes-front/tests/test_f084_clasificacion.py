# tests/test_f084_clasificacion.py
"""F-084 · R6-R10: clasificacion de los partes con problemas (modulo puro).

`application/services/partes_con_problemas.py` no toca BBDD, ORM ni
FastAPI: recibe `DocProblema` (datos simples) y decide los motivos, el
sustituto de un sustituido y si un parte cuenta para el aviso. Datos
sinteticos, sin nombres ni DNIs.
"""
from __future__ import annotations

import dataclasses

import pytest

from application.services import partes_con_problemas as pp
from application.services.parte_vacio import MARCA_RETIRADO
from application.services.partes_con_problemas import (
    MOTIVO_FECHA_FUTURA,
    MOTIVO_FECHA_POSTERIOR_CORREO,
    MOTIVO_SIN_FECHA,
    MOTIVO_SIN_LINEAS,
    MOTIVO_SIN_OBRA,
    MOTIVO_SIN_RASTRO,
    MOTIVO_SUSTITUIDO,
    MOTIVO_SUSTITUIDO_MISMO_ENVIO,
    ChoqueRecuperarError,
    DocProblema,
    NoRecuperableError,
)


def _doc(id_: str = "d1", **cambios) -> DocProblema:
    base = dict(
        id=id_, is_active=True, deleted_at_utc=None, deleted_by=None,
        fecha_int=20261123, obra_ide=10, obra_codigo="0100",
        obra_numero_leido="100", email_id="correo-1",
        email_received_datetime="2026-11-26T09:56:00Z",
        created_at_utc="2026-11-26T10:00:00+00:00",
        sustituido_por_id=None, lineas_vivas=2, es_futuro=False)
    base.update(cambios)
    return DocProblema(**base)


def _sustituido(id_: str = "s1", **cambios) -> DocProblema:
    return _doc(id_, is_active=False, **cambios)


# ============================== R6 · activos ============================= #

def test_f084_r6_un_parte_sano_no_tiene_motivos() -> None:
    assert pp.motivos_activo(_doc()) == ()


@pytest.mark.parametrize("cambios, motivo", [
    ({"obra_ide": None}, MOTIVO_SIN_OBRA),
    ({"fecha_int": None}, MOTIVO_SIN_FECHA),
    ({"fecha_int": 0}, MOTIVO_SIN_FECHA),
    ({"fecha_int": -1}, MOTIVO_SIN_FECHA),
    ({"es_futuro": True}, MOTIVO_FECHA_FUTURA),
    ({"fecha_int": 20261128}, MOTIVO_FECHA_POSTERIOR_CORREO),
    ({"lineas_vivas": 0}, MOTIVO_SIN_LINEAS),
])
def test_f084_r6_cada_motivo_salta_solo(cambios, motivo) -> None:
    assert pp.motivos_activo(_doc(**cambios)) == (motivo,)


def test_f084_r6_los_motivos_salen_en_orden_y_sin_repetir() -> None:
    d = _doc(obra_ide=None, fecha_int=20261230, es_futuro=True,
             lineas_vivas=0)
    assert pp.motivos_activo(d) == (
        MOTIVO_SIN_OBRA, MOTIVO_FECHA_FUTURA,
        MOTIVO_FECHA_POSTERIOR_CORREO, MOTIVO_SIN_LINEAS)
    d2 = _doc(obra_ide=None, fecha_int=None, lineas_vivas=0)
    assert pp.motivos_activo(d2) == (
        MOTIVO_SIN_OBRA, MOTIVO_SIN_FECHA, MOTIVO_SIN_LINEAS)


def test_f084_r6_el_orden_de_motivos_es_el_de_la_spec() -> None:
    assert pp.ORDEN_MOTIVOS == (
        MOTIVO_SIN_OBRA, MOTIVO_SIN_FECHA, MOTIVO_FECHA_FUTURA,
        MOTIVO_FECHA_POSTERIOR_CORREO, MOTIVO_SIN_LINEAS,
        MOTIVO_SUSTITUIDO_MISMO_ENVIO, MOTIVO_SIN_RASTRO, MOTIVO_SUSTITUIDO)
    assert set(pp.TEXTOS) == set(pp.ORDEN_MOTIVOS)
    assert all(pp.TEXTOS[m].strip() for m in pp.ORDEN_MOTIVOS)


@pytest.mark.parametrize("fecha_int, recibido, esperado", [
    (20261126, "2026-11-26T09:56:00Z", False),       # el mismo dia
    (20261127, "2026-11-26T09:56:00Z", False),       # margen de un dia
    (20261128, "2026-11-26T09:56:00Z", True),        # pasado el margen
    (20261201, "2026-11-30T23:30:00Z", False),       # cambio de mes
    (20261202, "2026-11-30T23:30:00Z", True),
    # Hora local española del 1/12 a las 00:30 = 30/11 23:30 UTC.
    (20261202, "2026-12-01T00:30:00+01:00", True),
    (20270101, "2026-12-31T08:00:00+00:00", False),  # cambio de ano
    (20261128, "2026-11-26T09:56:00", True),         # sin zona: UTC
    (20261128, None, False),                         # sin correo
    (20261128, "", False),
    (20261128, "no es una fecha", False),            # ilegible
    (None, "2026-11-26T09:56:00Z", False),           # sin fecha
    (0, "2026-11-26T09:56:00Z", False),
])
def test_f084_r6_fecha_posterior_al_correo(fecha_int, recibido,
                                           esperado) -> None:
    assert pp.fecha_posterior_al_correo(fecha_int, recibido) is esperado


def test_f084_r6_correo_ilegible_no_salta_en_motivos() -> None:
    d = _doc(fecha_int=20261230, email_received_datetime="xx")
    assert pp.motivos_activo(d) == ()


# =========================== R9 · fuera de la pestaña ==================== #

def test_f084_r9_papelera_y_retirado_no_son_sustituidos() -> None:
    assert pp.es_sustituido(_sustituido()) is True
    assert pp.es_sustituido(_doc()) is False                       # activo
    assert pp.es_sustituido(_sustituido(
        deleted_at_utc="2026-11-26T11:00:00+00:00")) is False      # papelera
    assert pp.es_sustituido(_sustituido(
        deleted_by=MARCA_RETIRADO + " · alguien")) is False        # F-061
    # Un `deleted_by` cualquiera sin hora de borrado ni marca no lo saca.
    assert pp.es_sustituido(_sustituido(deleted_by="otra cosa")) is True


def test_f084_r9_clasificar_no_lista_papelera_ni_retirados() -> None:
    docs = [
        _sustituido("papelera", deleted_at_utc="2026-11-26T11:00:00+00:00"),
        _sustituido("retirado", deleted_by=MARCA_RETIRADO),
        _doc("papelera-activo", obra_ide=None,
             deleted_at_utc="2026-11-26T11:00:00+00:00"),
        _doc("sano"),
    ]
    assert pp.clasificar(docs) == []


# ======================= R7 / R8 · sustituidos =========================== #

def test_f084_r8_con_sustituido_por_id_el_sustituto_es_ese() -> None:
    nuevo = _doc("n1", email_id="otro", created_at_utc="2026-11-27T00:00Z")
    trampa = _doc("n2", created_at_utc="2026-11-26T10:01:00+00:00")
    viejo = _sustituido("s1", sustituido_por_id="n1")
    por_id = {d.id: d for d in (nuevo, trampa, viejo)}
    assert pp.elegir_sustituto(viejo, por_id, [nuevo, trampa]) is nuevo
    assert pp.motivo_sustituido(viejo, nuevo) == MOTIVO_SUSTITUIDO


def test_f084_r8_si_el_sustituto_ya_no_existe_no_hay_rastro() -> None:
    otro = _doc("n2", created_at_utc="2026-11-26T11:00:00+00:00")
    viejo = _sustituido("s1", sustituido_por_id="desaparecido")
    assert pp.elegir_sustituto(viejo, {"n2": otro}, [otro]) is None
    assert pp.motivo_sustituido(viejo, None) == MOTIVO_SIN_RASTRO


def test_f084_r8_el_sustituto_por_id_puede_estar_inactivo() -> None:
    nuevo = _sustituido("n1", sustituido_por_id="n3")
    viejo = _sustituido("s1", sustituido_por_id="n1")
    assert pp.elegir_sustituto(viejo, {"n1": nuevo}, []) is nuevo


def test_f084_r8_pista_retroactiva_el_mas_antiguo_posterior() -> None:
    viejo = _sustituido("s1", email_id="correo-1",
                        created_at_utc="2026-11-26T10:00:00+00:00")
    anterior = _doc("a0", email_id="x",
                    created_at_utc="2026-11-26T09:00:00+00:00")
    tarde = _doc("a2", email_id="y",
                 created_at_utc="2026-11-26T12:00:00+00:00")
    pronto = _doc("a1", email_id="z",
                  created_at_utc="2026-11-26T11:00:00+00:00")
    activos = [anterior, tarde, pronto]
    s = pp.elegir_sustituto(viejo, {}, activos)
    assert s is pronto
    assert pp.motivo_sustituido(viejo, s) == MOTIVO_SUSTITUIDO


def test_f084_r8_pista_retroactiva_prefiere_el_del_mismo_envio() -> None:
    viejo = _sustituido("s1", email_id="correo-1",
                        created_at_utc="2026-11-26T10:00:00+00:00")
    pronto = _doc("a1", email_id="z",
                  created_at_utc="2026-11-26T10:30:00+00:00")
    mismo_tarde = _doc("a3", email_id="correo-1",
                       created_at_utc="2026-11-26T12:00:00+00:00")
    mismo = _doc("a2", email_id="correo-1",
                 created_at_utc="2026-11-26T10:01:39+00:00")
    s = pp.elegir_sustituto(viejo, {}, [pronto, mismo_tarde, mismo])
    assert s is mismo
    assert pp.motivo_sustituido(viejo, s) == MOTIVO_SUSTITUIDO_MISMO_ENVIO


def test_f084_r8_pista_retroactiva_misma_fecha_y_obra() -> None:
    viejo = _sustituido("s1", created_at_utc="2026-11-26T10:00:00+00:00")
    candidatos = [
        _doc("f", fecha_int=20261124, created_at_utc="2026-11-26T11:00Z"),
        _doc("o", obra_codigo="0200", created_at_utc="2026-11-26T11:00Z"),
        _sustituido("i", created_at_utc="2026-11-26T11:00Z"),  # no activo
        _doc("s1", created_at_utc="2026-11-26T11:00Z"),        # el mismo id
    ]
    assert pp.elegir_sustituto(viejo, {}, candidatos) is None
    assert pp.motivo_sustituido(viejo, None) == MOTIVO_SIN_RASTRO


def test_f084_r8_sin_codigo_de_obra_compara_el_numero_leido() -> None:
    viejo = _sustituido("s1", obra_codigo=None, obra_numero_leido="777",
                        created_at_utc="2026-11-26T10:00:00+00:00")
    casado = _doc("c", obra_codigo="0777", obra_numero_leido="777",
                  created_at_utc="2026-11-26T11:00:00+00:00")
    otro_num = _doc("n", obra_codigo=None, obra_numero_leido="778",
                    created_at_utc="2026-11-26T11:00:00+00:00")
    bueno = _doc("b", obra_codigo=None, obra_numero_leido=" 777 ",
                 created_at_utc="2026-11-26T12:00:00+00:00")
    assert pp.elegir_sustituto(viejo, {}, [casado, otro_num, bueno]) is bueno


def test_f084_r8_sin_fecha_ni_obra_no_hay_pista() -> None:
    cand = _doc("c", created_at_utc="2026-11-26T11:00:00+00:00")
    sin_fecha = _sustituido("s1", fecha_int=None,
                            created_at_utc="2026-11-26T10:00:00+00:00")
    sin_obra = _sustituido("s2", obra_codigo=None, obra_numero_leido=None,
                           created_at_utc="2026-11-26T10:00:00+00:00")
    sin_obra_c = _doc("c2", obra_codigo=None, obra_numero_leido=None,
                      created_at_utc="2026-11-26T11:00:00+00:00")
    assert pp.elegir_sustituto(sin_fecha, {}, [cand]) is None
    assert pp.elegir_sustituto(sin_obra, {}, [cand, sin_obra_c]) is None


def test_f084_r7_mismo_envio_exige_correo_igual_y_no_vacio() -> None:
    assert pp.mismo_envio(_doc(email_id="a"), _doc(email_id="a")) is True
    assert pp.mismo_envio(_doc(email_id="a"), _doc(email_id="b")) is False
    assert pp.mismo_envio(_doc(email_id=None), _doc(email_id=None)) is False
    assert pp.mismo_envio(_doc(email_id=""), _doc(email_id="")) is False
    assert pp.mismo_envio(_doc(email_id="  "), _doc(email_id="  ")) is False


def test_f084_r7_un_sustituido_tiene_exactamente_un_motivo() -> None:
    nuevo = _doc("n1", email_id="correo-1",
                 created_at_utc="2026-11-26T11:00:00+00:00")
    viejo = _sustituido("s1", email_id="correo-1", sustituido_por_id="n1",
                        obra_ide=None, lineas_vivas=0)
    [fila] = pp.clasificar([nuevo, viejo])
    assert fila.doc is viejo
    assert fila.motivos == (MOTIVO_SUSTITUIDO_MISMO_ENVIO,)
    assert fila.sustituto is nuevo
    sin_correo = _sustituido("s2", email_id=None, sustituido_por_id="n1")
    [fila2] = pp.clasificar([nuevo, sin_correo])
    assert fila2.motivos == (MOTIVO_SUSTITUIDO,)


# ========================== clasificar y R10 ============================= #

def test_f084_r10_cuenta_para_aviso_todo_menos_sustituido() -> None:
    assert pp.cuenta_para_aviso([MOTIVO_SUSTITUIDO]) is False
    assert pp.cuenta_para_aviso([]) is False
    for m in pp.ORDEN_MOTIVOS:
        if m != MOTIVO_SUSTITUIDO:
            assert pp.cuenta_para_aviso([m]) is True
            assert pp.cuenta_para_aviso([MOTIVO_SUSTITUIDO, m]) is True
    assert pp.NO_CUENTAN == frozenset({MOTIVO_SUSTITUIDO})


def test_f084_r10_resumen_cuenta_y_desglosa() -> None:
    nuevo = _doc("n1", email_id="b",
                 created_at_utc="2026-11-26T11:00:00+00:00")
    docs = [
        nuevo,
        _doc("a", obra_ide=None, lineas_vivas=0),
        _doc("b", fecha_int=None),
        _sustituido("c", sustituido_por_id="n1"),            # sustituido
        _sustituido("d", sustituido_por_id="nadie"),          # sin rastro
        _sustituido("e", email_id="b", sustituido_por_id="n1"),  # mismo envio
    ]
    filas = pp.clasificar(docs)
    res = pp.resumen(filas)
    assert res["total"] == 4                      # a, b, d, e (c no cuenta)
    assert res["por_motivo"] == {
        MOTIVO_SIN_OBRA: 1, MOTIVO_SIN_FECHA: 1, MOTIVO_SIN_LINEAS: 1,
        MOTIVO_SUSTITUIDO_MISMO_ENVIO: 1, MOTIVO_SIN_RASTRO: 1,
        MOTIVO_SUSTITUIDO: 1}
    assert pp.resumen([]) == {"total": 0, "por_motivo": {}}


def test_f084_r11_clasificar_ordena_por_motivo_y_fecha_descendente() -> None:
    nuevo = _doc("n1", email_id="b",
                 created_at_utc="2026-11-26T11:00:00+00:00")
    docs = [
        nuevo,
        _sustituido("c", sustituido_por_id="n1", fecha_int=20261120),
        _doc("l1", lineas_vivas=0, fecha_int=20261101),
        _doc("o1", obra_ide=None, fecha_int=20261110),
        _doc("l2", lineas_vivas=0, fecha_int=20261115),
        _doc("o2", obra_ide=None, lineas_vivas=0, fecha_int=20261112),
        _doc("f0", fecha_int=None),
        _sustituido("d", sustituido_por_id="nadie", fecha_int=20261101),
    ]
    filas = pp.clasificar(docs)
    assert [f.doc.id for f in filas] == [
        "o2", "o1", "f0", "l2", "l1", "d", "c"]
    assert [f.motivo for f in filas] == [
        MOTIVO_SIN_OBRA, MOTIVO_SIN_OBRA, MOTIVO_SIN_FECHA,
        MOTIVO_SIN_LINEAS, MOTIVO_SIN_LINEAS, MOTIVO_SIN_RASTRO,
        MOTIVO_SUSTITUIDO]
    assert [f.cuenta for f in filas] == [True] * 6 + [False]
    # Un activo no tiene sustituto.
    assert filas[0].sustituto is None


def test_f084_r8_clasificar_usa_la_pista_entre_los_activos() -> None:
    viejo = _sustituido("s1", created_at_utc="2026-11-26T10:00:00+00:00")
    nuevo = _doc("n1", email_id="correo-1",
                 created_at_utc="2026-11-26T10:02:00+00:00")
    [fila] = pp.clasificar([viejo, nuevo])
    assert fila.sustituto is nuevo
    assert fila.motivos == (MOTIVO_SUSTITUIDO_MISMO_ENVIO,)


def test_f084_r6_docproblema_es_inmutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        _doc().id = "otro"  # type: ignore[misc]


# ============================ excepciones ================================ #

def test_f084_r22_motivo_no_recuperable() -> None:
    assert pp.motivo_no_recuperable(_sustituido()) is None
    assert pp.motivo_no_recuperable(_doc()) == pp.MOTIVO_NO_REC_ACTIVO
    assert pp.motivo_no_recuperable(_sustituido(
        deleted_at_utc="2026-11-26T11:00:00+00:00")) == pp.MOTIVO_NO_REC_PAPELERA
    assert pp.motivo_no_recuperable(_sustituido(
        deleted_by=MARCA_RETIRADO)) == pp.MOTIVO_NO_REC_RETIRADO


def test_f084_r19_las_excepciones_llevan_motivo() -> None:
    e = NoRecuperableError("porque si")
    assert e.motivo == "porque si" and str(e) == "porque si"
    partes = [{"id": "x", "fecha": "2026-11-23", "obra": "0100"}]
    c = ChoqueRecuperarError(partes)
    assert c.partes == partes
    assert c.motivo == pp.MOTIVO_CHOQUE
    assert "Corrige la fecha o descarta antes el otro parte" in c.motivo
