# tests/test_f022_reparto_obras.py
"""F-022 · `reparto_obras.py`, la parte pura del reparto por obra.

Tablas de casos sin red ni BBDD. Datos SINTETICOS (obras 0100/0200,
personas «Persona A/B», partes PT26/0000x).

Bloques (los `-k` de tasks.md): `claves` y `agregar` (T3), `listado` y
`totales` (T4).
"""
from __future__ import annotations

import pytest
from application.services.reparto_obras import (
    SEPARADOR_CLAVE,
    agregar_ejecucion,
    agregar_preflight,
    repartir_claves,
)

# ===================================================================== #
# T3 · R19 · repartir_claves
# ===================================================================== #


def test_f022_r19_claves_con_prefijo_van_a_su_grupo() -> None:
    assert SEPARADOR_CLAVE == "::"
    assert repartir_claves(
        ["obr-10::501|20260302|1", "obr-20::502|20260303|2",
         "obr-10::503|20260304|1"],
        ["obr-10", "obr-20"]) == {
        "obr-10": ["501|20260302|1", "503|20260304|1"],
        "obr-20": ["502|20260303|2"]}


def test_f022_r19_claves_cada_grupo_recibe_solo_las_suyas_o_ninguna() -> None:
    assert repartir_claves(["obr-10::k1"], ["obr-10", "obr-20"]) == {
        "obr-10": ["k1"], "obr-20": []}
    assert repartir_claves([], ["obr-10", "obr-20"]) == {
        "obr-10": [], "obr-20": []}


def test_f022_r19_claves_de_un_grupo_desconocido_se_ignoran() -> None:
    assert repartir_claves(["obr-99::k1", "obr-10::k2"], ["obr-10"]) == {
        "obr-10": ["k2"]}


def test_f022_r19_claves_sin_prefijo_con_un_solo_grupo_van_a_el() -> None:
    assert repartir_claves(["501|20260302|1", "obr-10::k2"], ["obr-10"]) == {
        "obr-10": ["501|20260302|1", "k2"]}


@pytest.mark.parametrize("grupos", [["obr-10", "obr-20"], []])
def test_f022_r19_claves_sin_prefijo_con_varios_grupos_es_none(grupos) -> None:
    assert repartir_claves(["obr-10::k1", "501|20260302|1"], grupos) is None


def test_f022_r19_claves_el_prefijo_se_corta_en_el_primer_separador() -> None:
    assert repartir_claves(["obr-10::a::b"], ["obr-10"]) == {
        "obr-10": ["a::b"]}


def test_f022_r19_claves_admite_claves_no_texto() -> None:
    assert repartir_claves([501], ["obr-10"]) == {"obr-10": ["501"]}


# ===================================================================== #
# T3 · R16, R17 · agregar_preflight
# ===================================================================== #

def _grupo_pf(clave: str, codigo: str, **pf) -> dict:
    base = {"clave": clave, "obra": {"ide": 1, "codigo": codigo,
                                     "nombre": "Obra"},
            "registro_ids": [1], "listado": [{"registro_id": 1}],
            "avisos_calendario": [], "totales": _tot(1, 8.0, 0.0, 0,
                                                     {"nuevo": 1})}
    base.update(pf)
    return base


def _tot(lineas, hord, hext, inc, por_estado) -> dict:
    return {"lineas": lineas, "por_estado": por_estado,
            "horas_ordinarias": hord, "horas_extra": hext,
            "incidencias": inc}


def test_f022_r16_agregar_un_grupo_es_su_respuesta_tal_cual() -> None:
    g = _grupo_pf("obr-10", "0100", ok=True, escribir=2, raro={"x": 1},
                  partes=[{"cod": "PT26/00001"}], sesame_bloqueo="motivo")
    plano = agregar_preflight([g])
    esperado = {k: v for k, v in g.items()
                if k not in ("clave", "obra", "registro_ids", "listado")}
    assert plano == esperado


def test_f022_r16_agregar_un_grupo_fallido_tambien_tal_cual() -> None:
    g = _grupo_pf("obr-10", "0100", ok=False, error="sv5 caido")
    assert agregar_preflight([g])["error"] == "sv5 caido"
    assert agregar_preflight([g])["ok"] is False


def test_f022_r16_agregar_varios_grupos_concatena_y_suma() -> None:
    a = _grupo_pf("obr-10", "0100", ok=True,
                  obra_destino={"codigo": "0100"}, forzada_pruebas=False,
                  partes=[{"cod": "PT26/00001"}],
                  acciones=[{"registro_id": 1}],
                  conflictos=[{"clave": "k1"}],
                  avisos_calendario=[{"registro_id": 1}],
                  resumen={"escribir": 2, "omitir": 1, "ya_registrado": 0,
                           "conflictos": 1},
                  totales=_tot(3, 8.0, 2.0, 1, {"nuevo": 2, "omitida": 1}))
    b = _grupo_pf("obr-20", "0200", ok=True,
                  obra_destino={"codigo": "0200"}, forzada_pruebas=True,
                  partes=[{"cod": "PT26/00002"}],
                  acciones=[{"registro_id": 2}, {"registro_id": 3}],
                  conflictos=[],
                  avisos_calendario=[{"registro_id": 3}],
                  resumen={"escribir": 1, "omitir": 0, "ya_registrado": 4,
                           "conflictos": 0, "texto": "no se suma"},
                  totales=_tot(5, 1.5, 0.25, 0, {"nuevo": 1,
                                                 "ya_registrada": 4}))
    plano = agregar_preflight([a, b])
    assert plano["ok"] is True
    assert "error" not in plano
    assert plano["partes"] == [{"cod": "PT26/00001"}, {"cod": "PT26/00002"}]
    assert plano["acciones"] == [{"registro_id": 1}, {"registro_id": 2},
                                 {"registro_id": 3}]
    assert plano["conflictos"] == [{"clave": "k1"}]
    assert plano["avisos_calendario"] == [{"registro_id": 1},
                                          {"registro_id": 3}]
    assert plano["resumen"] == {"escribir": 3, "omitir": 1,
                                "ya_registrado": 4, "conflictos": 1}
    assert plano["obra_destino"] == {"codigo": "0100"}
    assert plano["forzada_pruebas"] is False
    assert plano["totales"] == _tot(8, 9.5, 2.25, 1, {
        "nuevo": 3, "omitida": 1, "ya_registrada": 4})
    assert "sesame_bloqueo" not in plano
    for clave in ("clave", "obra", "registro_ids", "listado"):
        assert clave not in plano


def test_f022_r17_agregar_un_grupo_fallido_no_tumba_a_los_demas() -> None:
    malo = _grupo_pf("obr-10", "0100", ok=False, error="sv5 caido",
                     totales=_tot(2, 0.0, 0.0, 0, {"no_se_registra": 2}))
    bueno = _grupo_pf("obr-20", "0200", ok=True,
                      obra_destino={"codigo": "0200"},
                      forzada_pruebas=True, partes=[{"cod": "P2"}],
                      resumen={"escribir": 1})
    plano = agregar_preflight([malo, bueno])
    assert plano["ok"] is True
    assert plano["obra_destino"] == {"codigo": "0200"}
    assert plano["forzada_pruebas"] is True
    assert plano["partes"] == [{"cod": "P2"}]
    assert plano["resumen"] == {"escribir": 1}
    assert plano["totales"]["por_estado"] == {"no_se_registra": 2,
                                              "nuevo": 1}


def test_f022_r17_agregar_todos_fallidos_ok_falso_con_el_motivo() -> None:
    a = _grupo_pf("obr-10", "0100", ok=False, error="sv5 caido")
    b = _grupo_pf("obr-20", None, ok=False, error=None)
    plano = agregar_preflight([a, b])
    assert plano["ok"] is False
    assert plano["error"] == ("ninguna obra se pudo evaluar: 0100: sv5 "
                              "caido; obr-20: error desconocido")
    assert "obra_destino" not in plano and "forzada_pruebas" not in plano
    assert plano["partes"] == [] and plano["resumen"] == {}


def test_f022_r18_agregar_el_bloqueo_de_sesame_sube_si_algun_grupo_lo_tiene() -> None:
    a = _grupo_pf("obr-10", "0100", ok=True)
    b = _grupo_pf("obr-20", "0200", ok=True, sesame_bloqueo="sin Sesame")
    assert agregar_preflight([a, b])["sesame_bloqueo"] == "sin Sesame"
    assert "sesame_bloqueo" not in agregar_preflight([a, a])


# ===================================================================== #
# T3 · R22 · agregar_ejecucion
# ===================================================================== #

def _grupo_ej(clave: str, codigo: str, **r) -> dict:
    base = {"clave": clave, "obra": {"codigo": codigo},
            "registro_ids": [1, 2]}
    base.update(r)
    return base


def test_f022_r22_agregar_ejecucion_un_grupo_es_su_respuesta() -> None:
    g = _grupo_ej("obr-10", "0100", ok=False, error="sigrid caido",
                  escritas=[], raro=1)
    plano = agregar_ejecucion([g])
    assert plano == {"ok": False, "error": "sigrid caido", "escritas": [],
                     "raro": 1, "parcial": False}


def test_f022_r22_agregar_ejecucion_todos_bien() -> None:
    a = _grupo_ej("obr-10", "0100", ok=True,
                  obra_destino={"codigo": "0100"}, forzada_pruebas=False,
                  escritas=[{"registro_id": 1}], omitidas=[],
                  ya_registradas=[7], pisadas=["k1"], borradas=1,
                  pendientes_confirmacion=[{"clave": "c1"}],
                  partes=[{"cod": "P1"}])
    b = _grupo_ej("obr-20", "0200", ok=True,
                  obra_destino={"codigo": "0200"}, forzada_pruebas=True,
                  escritas=[{"registro_id": 2}],
                  omitidas=[{"registro_id": 3}], ya_registradas=[8, 9],
                  pisadas=[], borradas=2, pendientes_confirmacion=[],
                  partes=[{"cod": "P2"}])
    plano = agregar_ejecucion([a, b])
    assert plano == {
        "ok": True, "parcial": False,
        "escritas": [{"registro_id": 1}, {"registro_id": 2}],
        "omitidas": [{"registro_id": 3}], "ya_registradas": [7, 8, 9],
        "pisadas": ["k1"], "pendientes_confirmacion": [{"clave": "c1"}],
        "partes": [{"cod": "P1"}, {"cod": "P2"}], "borradas": 3,
        "obra_destino": {"codigo": "0100"}, "forzada_pruebas": False,
    }


def test_f022_r22_agregar_ejecucion_parcial_sin_todo_o_nada() -> None:
    malo = _grupo_ej("obr-10", "0100", ok=False, error="sigrid caido")
    bueno = _grupo_ej("obr-20", "0200", ok=True,
                      obra_destino={"codigo": "0200"}, forzada_pruebas=True,
                      escritas=[{"registro_id": 2}], borradas=None)
    plano = agregar_ejecucion([malo, bueno])
    assert plano["ok"] is False
    assert plano["parcial"] is True
    assert plano["error"] == "0100: sigrid caido"
    assert plano["escritas"] == [{"registro_id": 2}]
    assert plano["borradas"] == 0
    assert plano["obra_destino"] == {"codigo": "0200"}
    assert plano["forzada_pruebas"] is True


def test_f022_r22_agregar_ejecucion_bloqueado_cuenta_como_no_ok() -> None:
    bloqueado = _grupo_ej("obr-10", "0100", ok=False, bloqueado_sesame=True,
                          error="sin Sesame")
    bueno = _grupo_ej("obr-20", "0200", ok=True)
    plano = agregar_ejecucion([bloqueado, bueno])
    assert (plano["ok"], plano["parcial"]) == (False, True)
    assert plano["error"] == "0100: sin Sesame"


def test_f022_r22_agregar_ejecucion_todos_mal_no_es_parcial() -> None:
    a = _grupo_ej("obr-10", "0100", ok=False, error="uno")
    b = _grupo_ej("obr-20", None, ok=False)
    plano = agregar_ejecucion([a, b])
    assert (plano["ok"], plano["parcial"]) == (False, False)
    assert plano["error"] == "0100: uno; obr-20: error desconocido"
    assert "obra_destino" not in plano
