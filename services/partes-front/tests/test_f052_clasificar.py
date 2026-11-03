# tests/test_f052_clasificar.py
"""F-052 en sv4: comparación pura portal ↔ Sigrid (R8, R9, R11, R16).

- `clasificar`: las 12 clases con los ejemplos de design §3, `a_cero`
  (DA13), R9 (tolerancia, clase de hora, partida, recurso, fecha, obra; el
  código de hora es nota), R11 con los motivos de DA14, el respaldo por
  `sigrid_hmores_ide` y la prioridad de estados.
- `firma`: estable ante el orden de entrada y sensible a los valores.
- `ACCIONES_POR_CLASE` / `acciones_de`: la tabla de design §4.

Datos sintéticos (obra 686, recurso 501); sin red ni base de datos.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from application.services.sincronizacion import (
    ACCIONES_POR_CLASE,
    CAMPOS_TRAER,
    CLASES,
    Diferencia,
    LineaPortal,
    LineaSigridSync,
    acciones_de,
    clasificar,
    firma,
    item_a_dict,
    resumen,
)


def P(rid: int, estado: str = "registrado", **cambios) -> LineaPortal:
    base = dict(registro_id=rid, fecha_int=20261014, recurso_ide=501,
                obra_ide=686, horas=8.0, extra=False, es_incidencia=False,
                hora_codigo="HL01", partida_ide=11, partida_cod="P1",
                sigrid_estado=estado, sigrid_motivo=None,
                sigrid_hmores_ide=None, sigrid_hmoide=None)
    base.update(cambios)
    return LineaPortal(**base)


def S(ide: int, origen: str = "partes", registro_id: int | None = None,
      **cambios) -> LineaSigridSync:
    base = dict(hmores_ide=ide, hmoide=7001, parte_cod="PT26/00001",
                parte_est=1, obra_ide=686, obra_cod="0686", recurso_ide=501,
                fecha_int=20261014, hora_ide=3, hora_cod="HL01", hora_ext=0,
                partida_ide=11, partida_cod="P1", can=8.0, tot=120.0,
                enlazada=False, origen=origen, registro_id=registro_id,
                ajuste_id=None)
    base.update(cambios)
    return LineaSigridSync(**base)


def _uno(portal, sigrid):
    items = clasificar(portal, sigrid)
    assert len(items) == 1, items
    return items[0]


def test_f052_r8_doce_clases() -> None:
    assert CLASES == (
        "igual", "distinta", "anulada_en_sigrid", "borrada_en_sigrid",
        "en_sigrid_sin_registrar", "pendiente", "no_viaja", "en_vuelo",
        "solo_sigrid_nuestra", "solo_sigrid_ajena", "solo_sigrid_manual",
        "solo_sigrid_auxiliar")


# ------------------------- ejemplos de design §3 ------------------------- #

def test_f052_r8_igual_501() -> None:
    it = _uno([P(501)], [S(9001, registro_id=501)])
    assert (it.clase, it.diferencias, it.notas) == ("igual", [], [])
    assert it.sigrid.hmores_ide == 9001 and it.registro_id == 501


def test_f052_r8_distinta_502_horas() -> None:
    it = _uno([P(502)], [S(9002, registro_id=502, can=6.0)])
    assert it.clase == "distinta"
    assert it.diferencias == [Diferencia("horas", 8.0, 6.0)]


def test_f052_r8_anulada_en_sigrid_503() -> None:
    it = _uno([P(503, horas=2.0, extra=True)],
              [S(9003, registro_id=503, can=0.0, hora_cod="HE01",
                 hora_ext=1)])
    assert it.clase == "anulada_en_sigrid"
    assert it.diferencias == [Diferencia("horas", 2.0, 0.0)]


def test_f052_r8_anulada_tambien_con_can_nulo() -> None:
    it = _uno([P(503)], [S(9003, registro_id=503, can=None)])
    assert it.clase == "anulada_en_sigrid"


def test_f052_r8_portal_a_cero_y_sigrid_a_cero_es_igual() -> None:
    it = _uno([P(503, horas=0.0)], [S(9003, registro_id=503, can=0.0)])
    assert it.clase == "igual"


def test_f052_r8_borrada_en_sigrid_504_registrado_por_confirmar() -> None:
    it = _uno([P(504, sigrid_hmores_ide=9004)], [])
    assert (it.clase, it.por_confirmar) == ("borrada_en_sigrid", True)


def test_f052_r8_borrada_en_sigrid_ya_marcada_no_se_confirma() -> None:
    it = _uno([P(504, "borrado_sigrid")], [])
    assert (it.clase, it.por_confirmar) == ("borrada_en_sigrid", False)


@pytest.mark.parametrize("estado", ["", "omitido", "error", "conflicto",
                                    "borrado_sigrid"])
def test_f052_r8_en_sigrid_sin_registrar_505(estado) -> None:
    it = _uno([P(505, estado, sigrid_motivo="parte_cerrado: x")],
              [S(9005, registro_id=505, can=7.0)])
    assert it.clase == "en_sigrid_sin_registrar"
    assert it.diferencias == [Diferencia("horas", 8.0, 7.0)]


@pytest.mark.parametrize("estado, motivo", [
    ("", None), ("error", "timeout de sv5"), ("conflicto", None),
    ("omitido", "parte_no_abierto: el parte PT26/1 no esta abierto"),
    ("omitido", "pisada_no_anulada: reaprueba"),
])
def test_f052_r11_pendiente_506(estado, motivo) -> None:
    it = _uno([P(506, estado, sigrid_motivo=motivo)], [])
    assert it.clase == "pendiente"


@pytest.mark.parametrize("motivo, nota", [
    ("fecha_no_valida: sin fecha", "fecha_no_valida"),
    ("fin_movido: el CIZ ya se movio", "fin_movido"),
    ("incidencia_en_sigrid: ya hay CIV", "incidencia_en_sigrid"),
    ("linea_enlazada: albaran", "linea_enlazada"),
    ("parte_cerrado: cerrado", "parte_cerrado"),
    ("regla de mensuales sin dos puntos", "regla de mensuales sin dos puntos"),
    (None, "omitido"),
])
def test_f052_r11_no_viaja_507_con_el_motivo_como_nota(motivo, nota) -> None:
    it = _uno([P(507, "omitido", sigrid_motivo=motivo)], [])
    assert it.clase == "no_viaja"
    assert it.notas == [nota]


def test_f052_r11_dedicacion_no_viaja_y_nota_si_esta_en_sigrid() -> None:
    assert _uno([P(507, "dedicacion")], []).clase == "no_viaja"
    it = _uno([P(507, "dedicacion")], [S(9007, registro_id=507)])
    assert it.clase == "no_viaja"
    assert it.notas == ["aparece en Sigrid (línea 9007)"]


def test_f052_r11_en_vuelo_508_no_compara() -> None:
    it = _uno([P(508, "encolado")], [S(9008, registro_id=508, can=1.0)])
    assert (it.clase, it.diferencias) == ("en_vuelo", [])
    assert _uno([P(508, "Encolado ")], []).clase == "en_vuelo"


def test_f052_r8_solo_sigrid_por_origen() -> None:
    items = clasificar([], [
        S(9009, registro_id=509), S(9010, "ajena"),
        S(9011, "manual"), S(9012, "ciz", registro_id=505),
        S(9013, "franquicia", ajuste_id=4)])
    assert [(i.clase, i.registro_id) for i in items] == [
        ("solo_sigrid_nuestra", 509), ("solo_sigrid_ajena", None),
        ("solo_sigrid_manual", None), ("solo_sigrid_auxiliar", 505),
        ("solo_sigrid_auxiliar", None)]
    assert all(i.diferencias == [] for i in items)


def test_f052_r8_ciz_hermano_no_casa_con_su_inicio() -> None:
    """DA12: `partes:505:ciz` es auxiliar aunque la 505 esté en el portal."""
    items = clasificar([P(505)], [S(9005, registro_id=505),
                                  S(9006, "ciz", registro_id=505)])
    assert [i.clase for i in items] == ["igual", "solo_sigrid_auxiliar"]


@pytest.mark.parametrize("can, cod, esperado", [
    (0.0, "HL01", True), (None, "HL01", True), (0.004, "HL01", True),
    (0.0, "CIV", False), (0.0, "civ", False), (1.0, "HL01", False)])
def test_f052_r8_a_cero(can, cod, esperado) -> None:
    it = _uno([], [S(9011, "manual", can=can, hora_cod=cod)])
    assert it.a_cero is esperado


def test_f052_r8_a_cero_solo_en_solo_sigrid() -> None:
    it = _uno([P(1, horas=0.0)], [S(1, registro_id=1, can=0.0)])
    assert it.a_cero is False


# --------------------------------- R9 ----------------------------------- #

@pytest.mark.parametrize("can, distinta", [
    (8.004, False), (7.996, False), (8.006, True), (7.99, True)])
def test_f052_r9_tolerancia_de_horas(can, distinta) -> None:
    it = _uno([P(1)], [S(1, registro_id=1, can=can)])
    assert (it.clase == "distinta") is distinta


def test_f052_r9_horas_no_se_comparan_en_incidencias() -> None:
    it = _uno([P(1, es_incidencia=True, horas=8.0, hora_codigo="CIV")],
              [S(1, registro_id=1, can=0.0, hora_cod="CIV", hora_ext=1)])
    assert (it.clase, it.diferencias) == ("igual", [])


def test_f052_r9_clase_de_hora() -> None:
    it = _uno([P(1, extra=True, hora_codigo="HE01")],
              [S(1, registro_id=1, hora_ext=0, hora_cod="HL01")])
    assert it.diferencias == [Diferencia("clase_hora", "extra", "ordinaria")]
    assert it.notas == []
    it = _uno([P(1)], [S(1, registro_id=1, hora_ext=1, hora_cod="HE01")])
    assert it.diferencias == [Diferencia("clase_hora", "ordinaria", "extra")]


def test_f052_r9_sin_clase_en_sigrid_no_compara_la_clase() -> None:
    """Sin codigo de hora en Sigrid no hay clase que comparar (H-M2-1)."""
    for cod in (None, "", "  "):
        it = _uno([P(1, extra=True)],
                  [S(1, registro_id=1, hora_cod=cod, hora_ext=None)])
        assert it.diferencias == []


# H-M2-1 (M2 de F-052): en Sigrid las 7 horas `HE*` tienen `auxhor.ext = 0`;
# la clase de la hora de Sigrid sale del prefijo `HE` del codigo, como en
# sv5 (`HoraRecurso.es_extra`) y en `fetch_dnis_sin_extra` de sv4. Datos de
# la M2: registro 4322 / hmores 410171 (HECAP) y 4323 / 410172 (HLOF).

def test_f052_h_m2_1_hecap_con_ext_cero_es_extra() -> None:
    it = _uno([P(4322, extra=True, hora_codigo="HECAP")],
              [S(410171, registro_id=4322, hora_cod="HECAP", hora_ext=0)])
    assert (it.clase, it.diferencias, it.notas) == ("igual", [], [])


def test_f052_h_m2_1_hlof_con_ext_cero_es_ordinaria() -> None:
    it = _uno([P(4323, extra=False, hora_codigo="HLOF")],
              [S(410172, registro_id=4323, hora_cod="HLOF", hora_ext=0)])
    assert (it.clase, it.diferencias, it.notas) == ("igual", [], [])


def test_f052_h_m2_1_ext_uno_en_una_hl_no_la_hace_extra() -> None:
    it = _uno([P(1, extra=False, hora_codigo="HLOF")],
              [S(1, registro_id=1, hora_cod="HLOF", hora_ext=1)])
    assert (it.clase, it.diferencias) == ("igual", [])


@pytest.mark.parametrize("cod", ["HECAP", " hecap", "he01"])
def test_f052_h_m2_1_prefijo_sin_mayusculas_ni_espacios(cod) -> None:
    it = _uno([P(1, extra=True, hora_codigo="HECAP")],
              [S(1, registro_id=1, hora_cod=cod, hora_ext=0)])
    assert it.diferencias == []


def test_f052_h_m2_1_cambio_real_de_clase_sigue_saliendo() -> None:
    it = _uno([P(1, extra=False, hora_codigo="HLGR")],
              [S(1, registro_id=1, hora_cod="HEGR", hora_ext=0)])
    assert it.clase == "distinta"
    assert it.diferencias == [Diferencia("clase_hora", "ordinaria", "extra")]
    assert it.notas == []
    it = _uno([P(1, extra=True, hora_codigo="HEGR")],
              [S(1, registro_id=1, hora_cod="HLGR", hora_ext=0)])
    assert it.diferencias == [Diferencia("clase_hora", "extra", "ordinaria")]


def test_f052_r9_codigo_de_hora_con_la_misma_clase_es_nota() -> None:
    it = _uno([P(1, hora_codigo="HL01")],
              [S(1, registro_id=1, hora_cod="HL02")])
    assert (it.clase, it.diferencias) == ("igual", [])
    assert it.notas == ["código de hora: HL01 en el portal, HL02 en Sigrid"]
    it = _uno([P(1, hora_codigo=" hl01")], [S(1, registro_id=1)])
    assert it.notas == []


@pytest.mark.parametrize("portal, sigrid, campo", [
    (dict(partida_ide=12, partida_cod="P2"), {}, "partida"),
    (dict(partida_ide=None, partida_cod="P2"), {}, "partida"),
    (dict(partida_ide=None, partida_cod=None), {}, "partida"),
    ({}, dict(partida_ide=None, partida_cod=None), "partida"),
    (dict(recurso_ide=502), {}, "recurso"),
    ({}, dict(fecha_int=20261015), "fecha"),
    ({}, dict(obra_ide=404, obra_cod="0404"), "obra"),
])
def test_f052_r9_cada_campo_es_una_diferencia(portal, sigrid, campo) -> None:
    it = _uno([P(1, **portal)], [S(1, registro_id=1, **sigrid)])
    assert it.clase == "distinta"
    assert [d.campo for d in it.diferencias] == [campo]


def test_f052_r9_valores_de_cada_diferencia() -> None:
    it = _uno([P(110, fecha_int=20261015, obra_ide=686, partida_ide=12,
                 partida_cod="P2", recurso_ide=502)],
              [S(9110, registro_id=110, fecha_int=20261016, obra_ide=404,
                 recurso_ide=501)])
    assert it.diferencias == [
        Diferencia("partida", "P2", "P1"), Diferencia("recurso", 502, 501),
        Diferencia("fecha", 20261015, 20261016),
        Diferencia("obra", 686, 404)]


@pytest.mark.parametrize("portal, sigrid", [
    (dict(partida_ide=None, partida_cod="p1 "), {}),
    (dict(partida_ide=11, partida_cod="otra"), dict(partida_cod="P1")),
    (dict(recurso_ide=None), {}),
    (dict(obra_ide=None), {}),
    (dict(partida_ide=0, partida_cod=None),
     dict(partida_ide=None, partida_cod=None)),
])
def test_f052_r9_lo_que_no_es_diferencia(portal, sigrid) -> None:
    it = _uno([P(1, **portal)], [S(1, registro_id=1, **sigrid)])
    assert (it.clase, it.diferencias) == ("igual", [])


def test_f052_r9_horas_nulas_en_el_portal_cuentan_como_cero() -> None:
    it = _uno([P(1, horas=None)], [S(1, registro_id=1, can=0.0)])
    assert it.clase == "igual"


# ------------------------------ casado ---------------------------------- #

def test_f052_casa_por_respaldo_de_hmores_ide_sin_synckey() -> None:
    portal = [P(1, sigrid_hmores_ide=9001, sigrid_hmoide=7001)]
    it = _uno(portal, [S(9001, "manual")])
    assert (it.clase, it.sigrid.hmores_ide) == ("igual", 9001)
    assert it.notas == ["casada por la línea 9001 (sin synckey en Sigrid)"]


@pytest.mark.parametrize("cambio", [
    dict(origen="ajena"), dict(recurso_ide=502), dict(fecha_int=20261015),
    dict(hmoide=7002)])
def test_f052_respaldo_estricto_como_f024(cambio) -> None:
    portal = [P(1, sigrid_hmores_ide=9001, sigrid_hmoide=7001)]
    items = clasificar(portal, [S(9001, **dict({"origen": "manual"},
                                               **cambio))])
    assert items[0].clase == "borrada_en_sigrid"
    assert len(items) == 2


def test_f052_respaldo_sin_hmoide_del_portal_no_mira_el_parte() -> None:
    it = _uno([P(1, sigrid_hmores_ide=9001)], [S(9001, "manual", hmoide=1)])
    assert it.clase == "igual"


def test_f052_respaldo_sin_recurso_en_el_portal_no_casa() -> None:
    items = clasificar([P(1, recurso_ide=None, sigrid_hmores_ide=9001)],
                       [S(9001, "manual")])
    assert [i.clase for i in items] == ["borrada_en_sigrid",
                                        "solo_sigrid_manual"]


def test_f052_synckey_gana_al_respaldo() -> None:
    items = clasificar([P(1, sigrid_hmores_ide=9001)],
                       [S(9001, "manual"), S(9002, registro_id=1)])
    assert [(i.clase, i.sigrid.hmores_ide) for i in items] == [
        ("igual", 9002), ("solo_sigrid_manual", 9001)]


def test_f052_synckey_repetida_la_segunda_queda_aparte_con_nota() -> None:
    items = clasificar([P(1)], [S(9002, registro_id=1),
                                S(9001, registro_id=1)])
    assert [(i.clase, i.sigrid.hmores_ide) for i in items] == [
        ("igual", 9001), ("solo_sigrid_nuestra", 9002)]
    assert items[1].notas == [("synckey repetida: la línea 1 ya casa con "
                               "la 9001")]
    assert items[1].repetida is True and items[0].repetida is False


def test_f052_prioridad_encolado_y_dedicacion_antes_que_el_casado() -> None:
    items = clasificar([P(1, "encolado"), P(2, "dedicacion")], [])
    assert [i.clase for i in items] == ["en_vuelo", "no_viaja"]


def test_f052_estado_se_normaliza() -> None:
    assert _uno([P(1, " Registrado ")],
                [S(1, registro_id=1)]).clase == "igual"
    assert _uno([P(1, None)], []).clase == "pendiente"


def test_f052_orden_portal_por_id_y_luego_sigrid_por_ide() -> None:
    items = clasificar([P(3), P(1)], [S(50, "manual"), S(40, "ajena"),
                                      S(9, registro_id=3)])
    assert [(i.registro_id, i.sigrid.hmores_ide if i.sigrid else None)
            for i in items] == [(1, None), (3, 9), (None, 40), (None, 50)]


# ------------------------------- firma ---------------------------------- #

def test_f052_r18_firma_estable_ante_el_orden() -> None:
    portal = [P(1), P(2, horas=4.0), P(3, "omitido")]
    sigrid = [S(9001, registro_id=1), S(9002, registro_id=2, can=3.0),
              S(9100, "manual")]
    a = {(i.registro_id, i.sigrid and i.sigrid.hmores_ide): firma(i)
         for i in clasificar(portal, sigrid)}
    b = {(i.registro_id, i.sigrid and i.sigrid.hmores_ide): firma(i)
         for i in clasificar(list(reversed(portal)), list(reversed(sigrid)))}
    assert a == b
    assert all(len(f) == 16 and int(f, 16) >= 0 for f in a.values())
    assert len(set(a.values())) == len(a)


@pytest.mark.parametrize("lado, cambio", [
    ("portal", dict(horas=7.0)), ("portal", dict(sigrid_estado="error")),
    ("portal", dict(partida_cod="P9")), ("sigrid", dict(can=7.0)),
    ("sigrid", dict(hmores_ide=9999)), ("sigrid", dict(parte_est=3))])
def test_f052_r18_firma_sensible_a_los_valores(lado, cambio) -> None:
    p, s = P(1), S(9001, registro_id=1)
    base = firma(_uno([p], [s]))
    if lado == "portal":
        p = replace(p, **cambio)
    else:
        s = replace(s, **cambio)
    assert firma(clasificar([p], [s])[0]) != base


# ---------------------------- acciones (R16) ---------------------------- #

def test_f052_r16_tabla_de_acciones() -> None:
    assert ACCIONES_POR_CLASE == {
        "igual": (), "distinta": ("traer_de_sigrid",),
        "anulada_en_sigrid": ("traer_de_sigrid",),
        "borrada_en_sigrid": ("a_papelera", "reaprobar"),
        "en_sigrid_sin_registrar": ("marcar_registrada",),
        "pendiente": ("reaprobar",), "no_viaja": (), "en_vuelo": (),
        "solo_sigrid_nuestra": ("restaurar",), "solo_sigrid_ajena": (),
        "solo_sigrid_manual": (), "solo_sigrid_auxiliar": ()}


def test_f052_r16_restaurar_solo_si_esta_en_la_papelera() -> None:
    it = _uno([], [S(9009, registro_id=509)])
    assert acciones_de(it) == ()
    for donde, acciones in (("papelera", ("restaurar",)), ("otro_ambito", ()),
                            ("parte_reemplazado", ()), ("no_existe", ())):
        it.donde = donde
        assert acciones_de(it) == acciones
    it.repetida = True
    it.donde = "papelera"
    assert acciones_de(it) == ()


def test_f052_r16_acciones_de_las_demas_clases() -> None:
    assert acciones_de(_uno([P(1)], [S(1, registro_id=1, can=1.0)])) == (
        "traer_de_sigrid",)
    assert acciones_de(_uno([P(1, "")], [S(1, registro_id=1)])) == (
        "marcar_registrada",)
    assert acciones_de(_uno([P(1)], [])) == ("a_papelera", "reaprobar")


@pytest.mark.parametrize("sigrid, acciones", [
    ({"can": 6.0}, ("traer_de_sigrid",)),
    ({"can": 6.0, "partida_ide": 12, "partida_cod": "P2"},
     ("traer_de_sigrid",)),
    ({"partida_ide": 12, "partida_cod": "P2"}, ()),
    ({"fecha_int": 20261015}, ()),
    ({"hora_cod": "HE01"}, ()),
])
def test_f052_da3_traer_solo_si_difieren_las_horas(sigrid, acciones) -> None:
    """DA3 = A: `traer_de_sigrid` trae solo horas; una `distinta` sin
    diferencia de horas es informativa (no hay nada que traer)."""
    it = _uno([P(1)], [S(1, registro_id=1, **sigrid)])
    assert it.clase == "distinta"
    assert acciones_de(it) == acciones
    assert CAMPOS_TRAER == ("horas",)


# ------------------------- resumen y serializado ------------------------- #

def test_f052_r13_resumen_por_clase_y_a_cero() -> None:
    items = clasificar([P(1), P(2, "encolado")],
                       [S(1, registro_id=1), S(5, "manual", can=0.0),
                        S(6, "manual", can=2.0)])
    r = resumen(items)
    assert r["total"] == 4 and r["a_cero"] == 1
    assert list(r["por_clase"]) == list(CLASES)
    assert r["por_clase"]["igual"] == 1 and r["por_clase"]["en_vuelo"] == 1
    assert r["por_clase"]["solo_sigrid_manual"] == 2
    assert r["por_clase"]["distinta"] == 0


def test_f052_r13_item_a_dict() -> None:
    it = _uno([P(502)], [S(9002, registro_id=502, can=6.0)])
    d = item_a_dict(it)
    assert d["clase"] == "distinta" and d["registro_id"] == 502
    assert d["hmores_ide"] == 9002 and d["firma"] == firma(it)
    assert d["diferencias"] == [{"campo": "horas", "portal": 8.0,
                                 "sigrid": 6.0}]
    assert d["acciones"] == ["traer_de_sigrid"]
    assert d["portal"]["horas"] == 8.0 and d["sigrid"]["can"] == 6.0
    assert (d["notas"], d["a_cero"], d["donde"]) == ([], False, None)
    solo = item_a_dict(_uno([], [S(5, "manual")]))
    assert (solo["portal"], solo["registro_id"], solo["hmores_ide"]) == (
        None, None, 5)


def test_f052_desde_dict_de_sv5_ignora_claves_de_mas() -> None:
    s = S(1, registro_id=1)
    d = dict(item_a_dict(_uno([], [s]))["sigrid"], otra="x")
    assert LineaSigridSync.desde_dict(d) == s
