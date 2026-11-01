# tests/test_f034_parte_abierto.py
"""F-034 · Regla pura de lo que no entra en Sigrid (R9, R11).

  - `motivo_parte_no_abierto` / `motivo_no_escrita`: prefijo, codigo del
    parte, nombre del estado, «reaprueba», sin tildes ni nombres, <= 255.
  - `confirmar_escritas`: escrita = synckey releida Y en el parte elegido;
    rellena `hmores_ide`; las demas, no escritas.
  - `parte_que_impidio`: el parte cerrado de una pisada viva primero; si
    no, el elegido si esta cerrado; si ninguno lo esta, None.

Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.parte_abierto import (
    LIMITE_MOTIVO,
    MOTIVO_NO_ESCRITA,
    MOTIVO_PARTE_NO_ABIERTO,
    confirmar_escritas,
    motivo_no_escrita,
    motivo_parte_no_abierto,
    parte_que_impidio,
)
from domain.models.registro_models import LineaSigrid

REGISTRO, CERRADO, IMPUTADO = 1, 3, 10


# ------------------------------ motivos (R11) ------------------------------ #

def test_f034_r11_prefijos_y_limite() -> None:
    assert MOTIVO_PARTE_NO_ABIERTO == "parte_no_abierto"
    assert MOTIVO_NO_ESCRITA == "no_escrita"
    assert LIMITE_MOTIVO == 255


def test_f034_r11_motivo_parte_no_abierto_texto_exacto() -> None:
    """DA3 = A: el texto de design §5, sin tildes como el resto de sv5."""
    assert motivo_parte_no_abierto("PT26/00314", "Cerrado") == (
        "parte_no_abierto: el parte PT26/00314 ya no esta En registro "
        "(Cerrado); no se registra. Reaprueba para llevarla al parte En "
        "registro del mes")


def test_f034_r11_motivo_parte_no_abierto_nombra_el_estado() -> None:
    m = motivo_parte_no_abierto("PT26/00400", "estado 7")
    assert m.startswith("parte_no_abierto: el parte PT26/00400 ")
    assert "(estado 7)" in m


def test_f034_r11_motivo_sin_codigo_no_dice_none() -> None:
    m = motivo_parte_no_abierto(None, "Imputado")
    assert "None" not in m and "el parte ? ya no esta" in m


def test_f034_r11_motivo_no_escrita_texto_exacto() -> None:
    assert motivo_no_escrita("PT26/00314") == (
        "no_escrita: Sigrid no confirmo la linea en el parte PT26/00314; "
        "reaprueba")
    assert motivo_no_escrita(None) == (
        "no_escrita: Sigrid no confirmo la linea en el parte ?; reaprueba")


@pytest.mark.parametrize("cod", ["PT26/" + "9" * 400, "x" * 300],
                         ids=["codigo-400", "texto-300"])
def test_f034_r11_motivos_caben_en_255(cod) -> None:
    for m in (motivo_parte_no_abierto(cod, "Cerrado"),
              motivo_no_escrita(cod)):
        assert len(m) == LIMITE_MOTIVO
    assert motivo_parte_no_abierto(cod, "Cerrado").startswith(
        "parte_no_abierto: ")
    assert motivo_no_escrita(cod).startswith("no_escrita: ")


def test_f034_r11_motivos_normales_no_se_recortan() -> None:
    assert len(motivo_parte_no_abierto("PT26/00314", "Imputado")) < 255
    assert motivo_parte_no_abierto("PT26/00314", "Imputado").endswith(
        "registro del mes")
    assert motivo_no_escrita("PT26/00314").endswith("; reaprueba")


# ------------------------- confirmar_escritas (R9) ------------------------- #

def _ls(ide, hmoide, rid) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=501, fecha_int=20261014, horide=1,
                       hora_codigo=None, can=8.0, tot=80.0,
                       synckey=f"partes:{rid}", nuestra=True, hmoide=hmoide)


def _e(rid, hmoide=900) -> dict:
    return {"registro_id": rid, "hmoide": hmoide, "parte_cod": "PT26/00314",
            "hora_codigo": "HL01", "can": 8.0, "tot": 80.0, "caa_cod": None}


def test_f034_r9_confirmada_si_esta_en_el_parte_elegido() -> None:
    ok, no = confirmar_escritas([_e(1), _e(2)], {
        "partes:1": _ls(5001, 900, 1), "partes:2": _ls(5002, 900, 2)})
    assert [(e["registro_id"], e["hmores_ide"]) for e in ok] == [
        (1, 5001), (2, 5002)]
    assert no == []


def test_f034_r9_ausente_es_no_escrita_y_sin_hmores_ide() -> None:
    ok, no = confirmar_escritas([_e(1), _e(2), _e(3)],
                                {"partes:2": _ls(5002, 900, 2)})
    assert [e["registro_id"] for e in ok] == [2]
    assert [e["registro_id"] for e in no] == [1, 3]
    assert all("hmores_ide" not in e for e in no)


def test_f034_r9_en_otro_parte_es_no_escrita() -> None:
    """La synckey existe pero en OTRO parte (no la escribimos ahora)."""
    ok, no = confirmar_escritas([_e(1, hmoide=900)],
                                {"partes:1": _ls(5001, 905, 1)})
    assert ok == [] and [e["registro_id"] for e in no] == [1]


def test_f034_r9_conserva_el_orden_y_los_campos() -> None:
    entrada = [_e(3), _e(1)]
    ok, _no = confirmar_escritas(entrada, {
        "partes:1": _ls(5001, 900, 1), "partes:3": _ls(5003, 900, 3)})
    assert [e["registro_id"] for e in ok] == [3, 1]
    assert ok[0] == dict(_e(3), hmores_ide=5003)


def test_f034_r9_sin_escritas_nada() -> None:
    assert confirmar_escritas([], {"partes:1": _ls(5001, 900, 1)}) == ([], [])


# ------------------------- parte_que_impidio (R11) ------------------------- #

def test_f034_r11_la_pisada_viva_en_cerrado_va_primero() -> None:
    """Ejemplo 2: si el parte de la pisada se cerro, es el que lo impidio
    aunque el elegido tambien este cerrado."""
    assert parte_que_impidio(
        900, [905], {900: CERRADO, 905: IMPUTADO},
        est_registro=REGISTRO) == 905


def test_f034_r11_pisada_viva_abierta_cae_al_elegido() -> None:
    assert parte_que_impidio(
        900, [905], {900: CERRADO, 905: REGISTRO},
        est_registro=REGISTRO) == 900


def test_f034_r11_sin_pisadas_el_elegido_cerrado() -> None:
    assert parte_que_impidio(900, [], {900: IMPUTADO},
                             est_registro=REGISTRO) == 900


def test_f034_r11_ninguno_cerrado_es_none() -> None:
    assert parte_que_impidio(900, [905], {900: REGISTRO, 905: REGISTRO},
                             est_registro=REGISTRO) is None


def test_f034_r11_parte_desconocido_no_cuenta_como_cerrado() -> None:
    """Un parte que no sale en la relectura no se puede nombrar."""
    assert parte_que_impidio(900, [905], {}, est_registro=REGISTRO) is None


def test_f034_r11_estado_nulo_es_no_abierto() -> None:
    """Como F-031: «cerrado» = cualquier estado distinto de En registro."""
    assert parte_que_impidio(900, [], {900: None},
                             est_registro=REGISTRO) == 900


def test_f034_r11_est_registro_es_parametro() -> None:
    assert parte_que_impidio(900, [], {900: 1}, est_registro=2) == 900
    assert parte_que_impidio(900, [], {900: 2}, est_registro=2) is None


def test_f034_r11_varias_pisadas_la_primera_cerrada() -> None:
    assert parte_que_impidio(
        900, [901, 902, 903], {900: CERRADO, 901: REGISTRO, 902: CERRADO,
                               903: IMPUTADO},
        est_registro=REGISTRO) == 902
