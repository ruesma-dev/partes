# tests/test_f056_franquicia.py
"""F-056 · Franquicia de extras en sv4: reglas puras (T13,
`application/services/franquicia.py`).

  - periodo de nomina 16 -> 15 por la fecha real (R4) y dia de ajuste: el
    ultimo dia con jornada > 0 (R5);
  - obra y partida del ajuste (R7, con sus desempates);
  - candidatos del aviso (R9-R12, R44; DA7: dispara una linea del dia de
    ajuste o un ajuste ya existente) con la franquicia que da sv5;
  - `extras_pendientes` (R9), el bloque del modal (R9-R14), la validacion
    de las decisiones (R15) y el payload de sv5 (design §6).

Sin red ni BBDD. Recursos, obras y personas SINTETICOS.
"""
from __future__ import annotations

import dataclasses
from datetime import date, timedelta

import pytest
from application.services import franquicia as fq

REC = 501
P10 = fq.periodo_de(date(2026, 10, 1))      # 2026-09-16 .. 2026-10-15


def _l(rid, fecha, *, horas=8.0, tipo="normal", obra=10, cod="0100",
       partida=33, pcod="01.01", rec=REC, inc=False, dni="00000000T",
       nombre="Persona Prueba") -> dict:
    return {"registro_id": rid, "fecha_int": int(fecha.strftime("%Y%m%d")),
            "recurso_ide": rec, "dni": dni, "nombre": nombre,
            "tipo_hora": tipo, "es_incidencia": inc, "horas": horas,
            "obra_ide": obra, "obra_codigo": cod, "partida_ide": partida,
            "partida_cod": pcod}


# ------------------------------ periodo y dia ------------------------------ #

@pytest.mark.parametrize("d, clave, inicio, fin", [
    (date(2026, 9, 16), "2026-10", date(2026, 9, 16), date(2026, 10, 15)),
    (date(2026, 10, 15), "2026-10", date(2026, 9, 16), date(2026, 10, 15)),
    (date(2026, 10, 16), "2026-11", date(2026, 10, 16), date(2026, 11, 15)),
    (date(2026, 12, 20), "2027-01", date(2026, 12, 16), date(2027, 1, 15)),
    (date(2027, 1, 3), "2027-01", date(2026, 12, 16), date(2027, 1, 15)),
])
def test_f056_r4_periodo_de_nomina(d, clave, inicio, fin):
    p = fq.periodo_de(d)
    assert (p.clave, p.inicio, p.fin) == (clave, inicio, fin)
    assert p.inicio_int == int(inicio.strftime("%Y%m%d"))
    assert p.fin_int == int(fin.strftime("%Y%m%d"))


@pytest.mark.parametrize("clave, esperado", [
    ("2026-10", (date(2026, 9, 16), date(2026, 10, 15))),
    ("2027-01", (date(2026, 12, 16), date(2027, 1, 15))),
    ("2026-13", None), ("26-10", None), ("", None), (None, None),
    ("2026-1", None), ("2026-10x", None)])
def test_f056_r15_periodo_de_clave(clave, esperado):
    p = fq.periodo_de_clave(clave)
    assert (None if p is None else (p.inicio, p.fin)) == esperado


def test_f056_r5_dia_de_ajuste_es_el_ultimo_con_jornada():
    # 2026-10-15 es jueves; el 12 es festivo nacional (lunes).
    festivos = {date(2026, 10, 12)}

    def jornada(d):
        return 0.0 if d.weekday() >= 5 or d in festivos else 8.0
    assert fq.dia_de_ajuste(P10, jornada) == date(2026, 10, 15)

    def sin_ultimos(d):
        return 0.0 if d >= date(2026, 10, 14) else 8.0
    assert fq.dia_de_ajuste(P10, sin_ultimos) == date(2026, 10, 13)


def test_f056_r5_dia_de_ajuste_sin_jornada_en_todo_el_periodo():
    vistos = []

    def nada(d):
        vistos.append(d)
        return 0.0
    assert fq.dia_de_ajuste(P10, nada) is None
    assert vistos[0] == P10.fin and vistos[-1] == P10.inicio
    assert len(vistos) == (P10.fin - P10.inicio).days + 1


# ------------------------------- obra (R7) -------------------------------- #

D15 = date(2026, 10, 15)


def test_f056_r7_obra_de_mas_horas_el_dia_y_su_partida():
    dia = [_l(1, D15, horas=3, obra=10, cod="0100", partida=31, pcod="A"),
           _l(2, D15, horas=5, obra=20, cod="0200", partida=41, pcod="B"),
           _l(3, D15, horas=2, obra=20, cod="0200", partida=42, pcod="C")]
    assert fq.elegir_obra(dia, dia) == {
        "obra_ide": 20, "obra_codigo": "0200", "partida_ide": 41,
        "partida_cod": "B"}


def test_f056_r7_empate_de_horas_mas_extras_del_periodo():
    dia = [_l(1, D15, horas=4, obra=10, cod="0100"),
           _l(2, D15, horas=4, obra=20, cod="0200", partida=41)]
    periodo = dia + [_l(3, D15 - timedelta(days=3), horas=2, tipo="extra",
                        obra=20, cod="0200")]
    assert fq.elegir_obra(dia, periodo)["obra_ide"] == 20


def test_f056_r7_empate_total_menor_codigo():
    dia = [_l(1, D15, horas=4, obra=20, cod="0200", partida=41),
           _l(2, D15, horas=4, obra=10, cod="0100", partida=31)]
    assert fq.elegir_obra(dia, dia)["obra_codigo"] == "0100"


def test_f056_r7_partida_empate_menor_registro_id():
    dia = [_l(9, D15, horas=4, partida=39, pcod="Z"),
           _l(5, D15, horas=4, partida=35, pcod="Y")]
    assert fq.elegir_obra(dia, dia)["partida_ide"] == 35


def test_f056_r7_sin_lineas_de_trabajo_el_dia_el_ultimo_dia_que_las_tenga():
    dia = [_l(1, D15, horas=8, inc=True, obra=90, cod="0900"),
           _l(2, D15, horas=0, obra=91, cod="0910")]
    periodo = dia + [
        _l(3, date(2026, 10, 9), horas=8, obra=10, cod="0100"),
        _l(4, date(2026, 10, 13), horas=3, obra=30, cod="0300", partida=7),
        _l(5, date(2026, 10, 13), horas=1, obra=40, cod="0400")]
    assert fq.elegir_obra(dia, periodo) == {
        "obra_ide": 30, "obra_codigo": "0300", "partida_ide": 7,
        "partida_cod": "01.01"}


def test_f056_r7_sin_ninguna_linea_de_trabajo_es_none():
    assert fq.elegir_obra([], []) is None
    assert fq.elegir_obra([], [_l(1, D15, inc=True)]) is None


def test_f056_r12_varios_recursos_con_extras():
    lineas = [_l(1, D15, tipo="extra", horas=2),
              _l(2, D15, tipo="normal", rec=777)]
    assert fq.varios_recursos(lineas) is False
    lineas.append(_l(3, D15, tipo="extra", horas=1, rec=777))
    assert fq.varios_recursos(lineas) is True
    assert fq.varios_recursos([_l(4, D15, tipo="extra", horas=0,
                                  rec=778)] + lineas[:1]) is False


# --------------------------- extras pendientes ---------------------------- #

def _acc(accion="escribir", rec=REC, cod="HE01", can=2.0, fecha=D15):
    return {"accion": accion, "recurso_ide": rec, "hora_codigo": cod,
            "can": can, "fecha_int": int(fecha.strftime("%Y%m%d"))}


def test_f056_r9_extras_pendientes_de_las_acciones_escribir_he():
    grupos = [
        {"acciones": [_acc(can=2.0), _acc(cod="he02", can=1.5),
                      _acc(accion="omitir", can=9.0),
                      _acc(cod="HL01", can=8.0), _acc(rec=502, can=4.0),
                      _acc(fecha=date(2026, 10, 16), can=5.0),
                      _acc(fecha=date(2026, 9, 16), can=-0.5),
                      _acc(cod=None, can=3.0)]},
        {"ok": False, "error": "obra caida"},
        {"acciones": [_acc(can=1.0)]}]
    assert fq.extras_pendientes(grupos, REC, P10) == 4.0


# ------------------------------- candidatos -------------------------------- #

ACTIVA = {"franquicia": 8.0, "estado": "activa"}


def _dia15(_clave):
    return fq.DiaAjuste(D15)


def _fila(estado, **kw):
    return dict({"id": 7, "recurso_ide": REC, "periodo": "2026-10",
                 "estado": estado, "fecha_int": 20261015, "obra_ide": 10,
                 "obra_codigo": "0100", "partida_ide": 33,
                 "partida_cod": "01.01", "franquicia": 8.0}, **kw)


def test_f056_r9_dia7_linea_del_dia_de_ajuste_con_franquicia_activa():
    [c] = fq.candidatos([_l(1, D15)], {}, {REC: ACTIVA}, _dia15)
    assert (c["tipo"], c["recurso_ide"], c["periodo"].clave, c["dia"]) == (
        "nuevo", REC, "2026-10", D15)
    assert (c["franquicia"], c["franquicia_estado"], c["motivo"]) == (
        8.0, "activa", None)
    assert c["clave"] == "501|2026-10" and c["fila"] is None
    assert (c["dni"], c["nombre"]) == ("00000000T", "Persona Prueba")


def test_f056_dia7_linea_de_otro_dia_no_dispara():
    assert fq.candidatos([_l(1, date(2026, 10, 14))], {}, {REC: ACTIVA},
                         _dia15) == []


@pytest.mark.parametrize("estado", ["inactiva", "apagada", None])
def test_f056_r9_sin_franquicia_activa_no_hay_candidato(estado):
    mapa = {} if estado is None else {REC: {"franquicia": 0.0,
                                            "estado": estado}}
    assert fq.candidatos([_l(1, D15)], {}, mapa, _dia15) == []


def test_f056_r11_franquicia_invalida_sale_con_motivo():
    mapa = {REC: {"franquicia": None, "estado": "invalida"}}
    [c] = fq.candidatos([_l(1, D15)], {}, mapa, _dia15)
    assert c["tipo"] == "invalida" and "invalida" in c["motivo"]


def test_f056_r44_sin_mapa_de_sv5_no_hay_candidatos_nuevos_pero_si_vivos():
    filas = {(REC, "2026-10"): _fila("aplicado")}
    lineas = [_l(1, D15), _l(2, D15, rec=502)]
    [c] = fq.candidatos(lineas, filas, None, _dia15)
    assert (c["tipo"], c["recurso_ide"], c["fila"]["id"]) == (
        "existente", REC, 7)


@pytest.mark.parametrize("estado", ["aplicado", "decidido", "error"])
def test_f056_r10_ajuste_vivo_sale_con_cualquier_linea_del_periodo(estado):
    """R10: aunque la linea no sea del dia de ajuste y la franquicia ya no
    este activa."""
    filas = {(REC, "2026-10"): _fila(estado)}
    mapa = {REC: {"franquicia": 0.0, "estado": "inactiva"}}
    [c] = fq.candidatos([_l(1, date(2026, 9, 20))], filas, mapa,
                        lambda _c: pytest.fail("no hace falta el dia"))
    assert c["tipo"] == "existente" and c["dia"] == D15


def test_f056_r11_ajuste_rechazado_solo_informa():
    filas = {(REC, "2026-10"): _fila("rechazado")}
    [c] = fq.candidatos([_l(1, D15)], filas, {REC: ACTIVA}, _dia15)
    assert c["tipo"] == "rechazado" and c["motivo"]


def test_f056_r6_calendario_no_fiable_sale_sin_propuesta():
    def no_fiable(_c):
        return fq.DiaAjuste(None, "calendario Sesame no disponible")
    [c] = fq.candidatos([_l(1, date(2026, 10, 1))], {}, {REC: ACTIVA},
                        no_fiable)
    assert (c["tipo"], c["dia"]) == ("nuevo", None)
    assert c["motivo"] == "calendario Sesame no disponible"


def test_f056_r5_periodo_sin_dia_de_ajuste_no_dispara():
    assert fq.candidatos([_l(1, D15)], {}, {REC: ACTIVA},
                         lambda _c: fq.DiaAjuste(None)) == []


def test_f056_r9_un_candidato_por_recurso_y_periodo():
    lineas = [_l(1, D15), _l(2, D15, tipo="extra", horas=2),
              _l(3, date(2026, 10, 16)), _l(4, None or D15, rec=None),
              {"registro_id": 5, "fecha_int": 0, "recurso_ide": REC}]
    llamadas = []

    def dia(clave):
        llamadas.append(clave)
        return fq.DiaAjuste(fq.periodo_de_clave(clave[1]).fin)
    out = fq.candidatos(lineas, {}, {REC: ACTIVA}, dia)
    assert [c["clave"] for c in out] == ["501|2026-10"]
    assert sorted(llamadas) == [(REC, "2026-10"), (REC, "2026-11")]


# ------------------------------ bloque (R9-R14) ----------------------------- #

def _sv5(accion="crear", ok=True, **kw):
    return dict({"ok": ok, "accion": accion, "extras": 14.0,
                 "objetivo": -6.0, "actual": None, "franquicia": 8.0,
                 "franquicia_estado": "activa", "motivo": None,
                 "parte_cod": "PT26/00314"}, **kw)


PROP = {"fecha_int": 20261015, "obra_ide": 10, "obra_codigo": "0100",
        "partida_ide": 33, "partida_cod": "01.01"}


def _cand(tipo="nuevo", **kw):
    base = fq.candidatos([_l(1, D15)], {}, {REC: ACTIVA}, _dia15)[0]
    return dict(base, tipo=tipo, **kw)


def test_f056_r9_r13_bloque_nuevo_ajustable_pide_decision():
    c = _cand()
    b = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": PROP, "sv5": _sv5(), "pendientes": 2.0}}, None)
    assert b["aviso"] is None
    [it] = b["items"]
    assert (it["clave"], it["tipo"], it["ajustable"], it["pide_decision"]) == (
        "501|2026-10", "nuevo", True, True)
    assert it["decisiones"] == ["ajustar", "no_ajustar"]
    assert (it["franquicia"], it["extras"], it["extras_pendientes"],
            it["objetivo"], it["actual"]) == (8.0, 14.0, 2.0, -6.0, None)
    assert (it["dia"], it["obra"], it["partida_cod"]) == (
        "2026-10-15", {"ide": 10, "codigo": "0100"}, "01.01")
    assert it["motivo"] is None and it["id"] is None


def test_f056_r10_bloque_existente_recalcular_o_mantener():
    c = _cand("existente", fila=_fila("aplicado", franquicia=7.5))
    [it] = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": PROP, "sv5": _sv5("actualizar", actual=-5.0)}},
        None)["items"]
    assert it["decisiones"] == ["recalcular", "mantener"]
    assert (it["id"], it["estado"], it["actual"]) == (7, "aplicado", -5.0)
    assert (it["franquicia"], it["franquicia_usada"]) == (8.0, 7.5)


@pytest.mark.parametrize("sv5, texto", [
    (None, "sin respuesta"),
    (_sv5("no_editable", ok=False, motivo="parte_no_abierto: PT cerrado"),
     "parte_no_abierto"),
    (_sv5("no_editable", ok=False, motivo=None, error="sv5 dijo no"),
     "sv5 dijo no"),
    (_sv5("ya_aplicado"), "ya"),
    (_sv5("sin_ajuste", objetivo=0.0), "sin extras"),
])
def test_f056_r12_r14_bloque_no_ajustable_no_pide_decision(sv5, texto):
    c = _cand()
    [it] = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": PROP, "sv5": sv5}}, None)["items"]
    assert (it["ajustable"], it["pide_decision"], it["decisiones"]) == (
        False, False, [])
    assert texto in it["motivo"]


def test_f056_r12_motivo_propio_manda_sobre_sv5():
    c = _cand()
    [it] = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": PROP, "sv5": _sv5(),
        "motivo": fq.MOTIVO_VARIOS_RECURSOS}}, None)["items"]
    assert (it["ajustable"], it["motivo"]) == (False,
                                               fq.MOTIVO_VARIOS_RECURSOS)


@pytest.mark.parametrize("tipo", ["rechazado", "invalida"])
def test_f056_r11_rechazado_e_invalida_solo_informan(tipo):
    c = _cand(tipo, motivo="lo que sea",
              fila=_fila("rechazado") if tipo == "rechazado" else None)
    [it] = fq.bloque_franquicias([c], {}, None)["items"]
    assert (it["ajustable"], it["pide_decision"], it["motivo"]) == (
        False, False, "lo que sea")


def test_f056_r6_candidato_con_motivo_sin_veredicto():
    c = _cand(dia=None, motivo="calendario Sesame no disponible")
    [it] = fq.bloque_franquicias([c], {}, None)["items"]
    assert (it["dia"], it["ajustable"], it["motivo"]) == (
        None, False, "calendario Sesame no disponible")


def test_f056_r44_bloque_lleva_el_aviso():
    b = fq.bloque_franquicias([], {}, "sv5 caido")
    assert b == {"aviso": fq.AVISO_NO_COMPROBADA + "sv5 caido", "items": []}


# ---------------------------- decisiones (R15) ---------------------------- #

VALIDAS = {"501|2026-10", "502|2026-10"}


def test_f056_r15_validar_decisiones():
    crudo = [{"recurso_ide": 501, "periodo": "2026-10", "decision": "ajustar"},
             {"recurso_ide": "502", "periodo": "2026-10",
              "decision": "mantener"}]
    assert fq.validar_decisiones(crudo, VALIDAS) == [
        (501, "2026-10", "ajustar"), (502, "2026-10", "mantener")]
    assert fq.validar_decisiones(None, VALIDAS) == []
    assert fq.validar_decisiones([], VALIDAS) == []


@pytest.mark.parametrize("crudo", [
    "x", {"recurso_ide": 501}, [None], [{"periodo": "2026-10",
                                         "decision": "ajustar"}],
    [{"recurso_ide": 0, "periodo": "2026-10", "decision": "ajustar"}],
    [{"recurso_ide": "x", "periodo": "2026-10", "decision": "ajustar"}],
    [{"recurso_ide": 501, "periodo": "2026-13", "decision": "ajustar"}],
    [{"recurso_ide": 501, "periodo": "2026-10", "decision": "borrar"}],
    [{"recurso_ide": 503, "periodo": "2026-10", "decision": "ajustar"}],
    [{"recurso_ide": 501, "periodo": "2026-10", "decision": "ajustar"},
     {"recurso_ide": 501, "periodo": "2026-10", "decision": "no_ajustar"}],
])
def test_f056_r15_decisiones_invalidas(crudo):
    with pytest.raises(fq.DecisionInvalida):
        fq.validar_decisiones(crudo, VALIDAS)


def test_f056_r15_estados_y_decisiones_literales():
    assert fq.ESTADOS == ("decidido", "aplicado", "rechazado", "error")
    assert fq.DECISIONES == ("ajustar", "no_ajustar", "recalcular",
                             "mantener")


# ------------------------------ payload (§6) ------------------------------ #

def test_f056_r17_payload_franquicia():
    fila = _fila("decidido")
    assert fq.payload_franquicia(fila, usuario="ana") == {
        "ajuste_id": 7, "recurso_ide": REC, "periodo": "2026-10",
        "inicio": 20260916, "fin": 20261015, "fecha_int": 20261015,
        "obra": {"ide": 10, "codigo": "0100"}, "partida_ide": 33,
        "partida_cod": "01.01", "extras_pendientes": 0.0, "usuario": "ana"}
    assert "franquicia" not in fq.payload_franquicia(fila)


def test_f056_r9_payload_de_comprobar_sin_fila():
    datos = dict(PROP, recurso_ide=REC, periodo="2026-10")
    p = fq.payload_franquicia(datos, extras_pendientes=2.5)
    assert (p["ajuste_id"], p["extras_pendientes"], p["usuario"]) == (
        0, 2.5, None)


# ============ supervivientes de la campana de mutacion (2026-10-29) ============ #
# Cada test caza un mutante que la suite dejaba vivo (numero entre corchetes:
# el de `progress/mutacion_F-056.md`). Los `or 0` son el «sin dato» de una
# linea o una accion: no puede convertirse en el recurso, la fecha o el
# registro 1.

def _sin(linea: dict, *claves: str) -> dict:
    return dict(linea, **{k: None for k in claves})


def test_f056_periodo_y_dia_de_ajuste_son_valores_inmutables():
    """[1, 2] `Periodo` y `DiaAjuste` son valores: nadie los cambia por el
    camino y sirven de clave (iguales por valor)."""
    for valor, campo in ((P10, "clave"), (fq.DiaAjuste(D15), "fecha")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(valor, campo, None)
    assert {P10, fq.periodo_de(D15)} == {P10}
    assert len({fq.DiaAjuste(D15), fq.DiaAjuste(D15, None)}) == 1


@pytest.mark.parametrize("quita", ["obra_ide", "obra_codigo"])
def test_f056_r7_obra_solo_por_ide_o_solo_por_codigo_es_trabajo(quita):
    """[4] Una linea con obra por ide O por codigo es de trabajo."""
    linea = _sin(_l(1, D15), quita)
    obra = fq.elegir_obra([linea], [linea])
    assert obra is not None
    assert (obra["obra_ide"], obra["obra_codigo"]) == (
        linea["obra_ide"], linea["obra_codigo"])


def test_f056_r7_lineas_del_periodo_sin_fecha_siguen_eligiendo_obra():
    """[5, 6] Sin lineas el dia, el ultimo dia con trabajo: una linea sin
    `fecha_int` cuenta como dia 0 en el maximo Y en el filtro."""
    linea = _sin(_l(1, D15, cod="0200", obra=20), "fecha_int")
    assert fq.elegir_obra([], [linea])["obra_codigo"] == "0200"


def test_f056_r7_partida_empate_sin_registro_id_va_primero():
    """[7] En el desempate de la partida, sin `registro_id` es el 0."""
    con = _l(1, D15, pcod="01.01", partida=33)
    sin = _sin(_l(2, D15, pcod="09.09", partida=99), "registro_id")
    assert fq.elegir_obra([con, sin], [con, sin])["partida_cod"] == "09.09"


def test_f056_r12_extra_sin_recurso_cuenta_como_otro_recurso():
    """[8] DA16: una extra sin recurso no es del recurso 1: con la del 1 ya
    son dos y no se ajusta (lado seguro)."""
    lineas = [_l(1, D15, tipo="extra", horas=2.0, rec=1),
              _sin(_l(2, D15, tipo="extra", horas=1.0), "recurso_ide")]
    assert fq.varios_recursos(lineas) is True


def test_f056_r9_accion_sin_recurso_no_es_del_recurso_1():
    """[9] Una accion sin `recurso_ide` no suma a ningun recurso."""
    accion = dict(_acc(can=2.0), recurso_ide=None)
    assert fq.extras_pendientes([{"acciones": [accion]}], 1, P10) == 0.0


def test_f056_r9_linea_sin_recurso_no_es_candidata_del_recurso_1():
    """[11] Una linea sin recurso no dispara nada (no es el recurso 1)."""
    linea = _sin(_l(1, D15), "recurso_ide")
    assert fq.candidatos([linea], {}, {1: ACTIVA}, _dia15) == []


def test_f056_r9_bloque_dia_del_candidato_y_si_no_el_de_la_propuesta():
    """[12] El dia del item es el del candidato; sin el, el de la
    propuesta."""
    def _dia(c, prop):
        b = fq.bloque_franquicias([c], {c["clave"]: {
            "propuesta": prop, "sv5": _sv5(), "pendientes": 0.0}}, None)
        return b["items"][0]["dia"]
    otra = dict(PROP, fecha_int=20261014)
    assert _dia(_cand(), otra) == "2026-10-15"
    assert _dia(_cand(dia=None), otra) == "2026-10-14"


@pytest.mark.parametrize("quita, obra", [
    ("obra_ide", {"ide": None, "codigo": "0100"}),
    ("obra_codigo", {"ide": 10, "codigo": None})])
def test_f056_r9_bloque_obra_solo_por_ide_o_por_codigo(quita, obra):
    """[13] La obra del item sale con su ide O con su codigo."""
    c = _cand()
    b = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": dict(PROP, **{quita: None}), "sv5": _sv5(),
        "pendientes": 0.0}}, None)
    assert b["items"][0]["obra"] == obra


def test_f056_r9_bloque_parte_de_sv5_sin_fila():
    """[14] Sin fila, el parte es el que dice sv5."""
    c = _cand()
    b = fq.bloque_franquicias([c], {c["clave"]: {
        "propuesta": PROP, "sv5": _sv5(), "pendientes": 0.0}}, None)
    assert b["items"][0]["parte_cod"] == "PT26/00314"


def test_f056_r15_el_recurso_1_es_valido():
    """[15] R15: recurso >= 1; el 1 vale."""
    assert fq.validar_decisiones(
        [{"recurso_ide": 1, "periodo": "2026-10", "decision": "ajustar"}],
        {"1|2026-10"}) == [(1, "2026-10", "ajustar")]


def test_f056_r9_payload_sin_dia_va_con_fecha_0():
    """[16] Sin dia en los datos, `fecha_int` 0 (sin dato), no 1."""
    datos = _sin(dict(PROP, recurso_ide=REC, periodo="2026-10"), "fecha_int")
    assert fq.payload_franquicia(datos)["fecha_int"] == 0
