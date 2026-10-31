# tests/test_f047_portal_parte_nuevo.py
"""F-047 · R18-R23: el portal y el parte nuevo «en espera» (`static/app.js`).

El servidor pinta `data-recalculo-motivo="nuevo"` en los contenedores de un
parte que sv3 aún no ha repartido. Al cargar, el portal lo pone en espera
con la marca «procesando…» y textos propios (R19-R21); sin ese atributo, o
cuando es `wireFechaInput` quien lo pone en espera, todo es como en F-043
(R22). Lo demás de F-043 no cambia (R23): se fija con la huella de cada
función.

Las funciones de `app.js` se EJECUTAN con node (doble de DOM de
`test_f043_portal_fecha`; se saltan sin node). Sin red. Datos sintéticos.
"""
from __future__ import annotations

import hashlib
import json
import re

import pytest

from tests.test_f043_portal_fecha import (
    ESPERA,
    VARIABLES,
    _funcion,
    _js,
    _node,
    _programa,
)

FECHA = "2026-10-01"
D = "01/10/2026"

ESPERA_NUEVO = (f"Procesando el parte nuevo del {D}: se están repartiendo "
                "sus horas normales y extra (suele tardar menos de 1 min; "
                "con más partes en cola, unos minutos). Puedes seguir "
                "trabajando con el resto.")
TERMINADO_NUEVO = f"Parte nuevo del {D} procesado: horas repartidas."
VENCIDO_NUEVO = (f"No se ha podido confirmar el reparto de horas del parte "
                 f"nuevo del {D}. Pulsa Actualizar; si siguen sin repartir, "
                 "avisa a quien mantiene el portal.")
ESPERA_F043 = (f"Recalculando extras del parte del {D} (suele tardar "
               "1–2 min). Puedes seguir trabajando con el resto.")
TERMINADO_F043 = f"Extras del parte del {D} recalculadas."
VENCIDO_F043 = (f"No se ha podido confirmar el recálculo de extras del parte "
                f"del {D}. Pulsa Actualizar; si las extras no cambian, "
                "vuelve a guardar la fecha.")

#: Una fila del parte doc-1 (con o sin motivo), su detalle y su barra de
#: acciones, y una fila de doc-2 sin espera.
PAGINA = r"""
function fila(doc, reg, extra) {
  return el("tr", Object.assign({"data-registro-id": reg,
    "data-document-id": doc, "data-fecha": "%(fecha)s"}, extra || {}),
    [el("td", {"class": "cell-fecha"}, [
      el("input", {"class": "fecha-edit", "data-document-id": doc,
                   value: "%(fecha)s"})]),
     el("td", {}, [el("input", {"class": "horas-edit", value: "8"})])]);
}
var espera = {"data-recalculando": "1"};
if (%(nuevo)s) espera["data-recalculo-motivo"] = "nuevo";
var marca = el("span", {"class": "recalculando-marca"});
marca.textContent = %(nuevo)s ? "procesando…" : "recalculando…";
var f1 = fila("doc-1", "1", espera);
f1.children[0].appendChild(marca);
body.appendChild(el("table", {}, [f1, fila("doc-2", "2")]));
var barra = el("div", {"class": "action-bar", "data-parte-acciones": "",
  "data-document-id": "doc-1"}, [el("button", {"class": "aprobar"}),
  el("button", {"class": "borrar", disabled: "disabled"})]);
body.appendChild(barra);
function foto() {
  return {
    marcas: document.querySelectorAll(".recalculando-marca")
      .map(function (m) { return m.textContent; }),
    barra: barra.querySelectorAll("button").map(function (b) {
      return b.disabled; }),
    barraMarcas: barra.querySelectorAll(".recalculando-marca").length,
    horas: document.querySelectorAll(".horas-edit").map(function (i) {
      return i.disabled; }),
    tarjetas: document.querySelectorAll(".recalculo-tarjeta").map(
      function (t) { return [t.getAttribute("data-document-id"),
        t.querySelector(".recalculo-texto").textContent,
        !!t.querySelector("[data-recalculo-actualizar]")]; }),
    vigilados: Object.keys(recalculoVigilados),
  };
}
"""


def _pagina(nuevo: bool, acciones: str) -> dict:
    cuerpo = (PAGINA % {"fecha": FECHA, "nuevo": "true" if nuevo else "false"}
              + acciones + "\nsalir(foto());")
    return _node(_programa(cuerpo, ESPERA, VARIABLES))


# ================================ R19 ================================== #

def test_f047_r19_al_cargar_el_parte_nuevo_espera_procesando() -> None:
    r = _pagina(True, "esperasDeLaPagina();")
    assert r["marcas"] == ["procesando…"]
    assert r["tarjetas"] == [["doc-1", ESPERA_NUEVO, False]]
    assert r["horas"] == [True, False]          # solo doc-1 espera
    assert r["vigilados"] == ["doc-1"]


def test_f047_r18_la_barra_de_acciones_se_deshabilita_y_vuelve() -> None:
    r = _pagina(True, "esperasDeLaPagina();")
    assert r["barra"] == [True, True]
    assert r["barraMarcas"] == 0               # sin td ni fecha: sin marca
    r = _pagina(True, "esperasDeLaPagina();"
                      "aplicarEstadoRecalculo('doc-1', 'sin_seguimiento');")
    assert r["barra"] == [False, True]          # cada botón, como estaba


# ================================ R20 ================================== #

def test_f047_r20_terminado_dice_procesado_y_ofrece_actualizar() -> None:
    r = _pagina(True, "esperasDeLaPagina();"
                      "aplicarEstadoRecalculo('doc-1', 'terminado');")
    assert r["marcas"] == ["procesado · pulsa Actualizar"]
    assert r["tarjetas"] == [["doc-1", TERMINADO_NUEVO, True]]
    assert r["horas"] == [True, False]          # sus datos están viejos
    assert r["barra"] == [True, True]


# ================================ R21 ================================== #

def test_f047_r21_vencido_lo_dice_con_la_marca_de_f043() -> None:
    r = _pagina(True, "esperasDeLaPagina();"
                      "aplicarEstadoRecalculo('doc-1', 'vencido');")
    assert r["marcas"] == ["sin confirmar · pulsa Actualizar"]
    assert r["tarjetas"] == [["doc-1", VENCIDO_NUEVO, True]]


# ================================ R22 ================================== #

def test_f047_r22_sin_motivo_todo_es_de_f043() -> None:
    r = _pagina(False, "esperasDeLaPagina();")
    assert r["marcas"] == ["recalculando…"]
    assert r["tarjetas"] == [["doc-1", ESPERA_F043, False]]
    r = _pagina(False, "esperasDeLaPagina();"
                       "aplicarEstadoRecalculo('doc-1', 'terminado');")
    assert r["marcas"] == ["recalculado · pulsa Actualizar"]
    assert r["tarjetas"] == [["doc-1", TERMINADO_F043, True]]
    r = _pagina(False, "esperasDeLaPagina();"
                       "aplicarEstadoRecalculo('doc-1', 'vencido');")
    assert r["tarjetas"] == [["doc-1", VENCIDO_F043, True]]


def test_f047_r22_un_cambio_de_fecha_lo_pasa_a_recalculo() -> None:
    """`wireFechaInput` llama a `ponerEnEspera(docId)` sin motivo."""
    r = _pagina(True, "esperasDeLaPagina(); ponerEnEspera('doc-1');"
                      "avisoRecalculo('doc-1', 'espera', '%s');"
                      "aplicarEstadoRecalculo('doc-1', 'terminado');" % FECHA)
    assert r["marcas"] == ["recalculado · pulsa Actualizar"]
    assert r["tarjetas"] == [["doc-1", TERMINADO_F043, True]]


@pytest.mark.parametrize("motivo", ["undefined", "''", "'recalculo'",
                                    "'otro'"])
def test_f047_r22_los_textos_sin_motivo_nuevo_son_los_de_f043(motivo) -> None:
    textos = _node(_programa(
        "salir(['espera', 'terminado', 'vencido', 'soltar', 'fallo'].map("
        "function (t) { return [textoAvisoRecalculo(t, '%s'),"
        " textoAvisoRecalculo(t, '%s', %s)]; }));" % (FECHA, FECHA, motivo),
        ("flashEl", "setStatus", "estadoRecalculo", "fmtFechaEs",
         "textoAvisoRecalculo")))
    for sin, con in textos:
        assert sin == con
    assert [t[0] for t in textos][:3] == [ESPERA_F043, TERMINADO_F043,
                                          VENCIDO_F043]


def test_f047_r19_r21_los_textos_del_parte_nuevo() -> None:
    textos = _node(_programa(
        "salir(['espera', 'terminado', 'vencido', 'soltar', 'fallo'].map("
        "function (t) { return textoAvisoRecalculo(t, '%s', 'nuevo'); }));"
        % FECHA,
        ("flashEl", "setStatus", "estadoRecalculo", "fmtFechaEs",
         "textoAvisoRecalculo")))
    f043 = _node(_programa(
        "salir(['soltar', 'fallo'].map(function (t) {"
        " return textoAvisoRecalculo(t, '%s'); }));" % FECHA,
        ("flashEl", "setStatus", "estadoRecalculo", "fmtFechaEs",
         "textoAvisoRecalculo")))
    assert textos == [ESPERA_NUEVO, TERMINADO_NUEVO, VENCIDO_NUEVO] + f043


# ================================ R23 ================================== #

#: Huella sha256 de lo que F-047 no toca (medida en `dev` 75816f2).
HUELLAS = {
    "soltarEspera": "fc076b20d7f31fa20330a835e6dbed6e74df79aa08a74066ddf4a08435b80210",
    "vigilarRecalculo": "ddee2b476b3baa2e60fc6fa5a2d3d63b27cb280f5d65cf46346ece1ecce6f127",
    "sondearRecalculo": "35bec9d38869565f2c88afa00e9bcf6b69bd25b9816f9c266dbfeea4a0443d0f",
    "actualizarVista": "9593826b31aca6fa777a2900c0044e903b8a1fe128c293ff28eed9285bc6f198",
    "restaurarVista": "8c08766cae4315b102499dd1e49fbcfe56eb1a4ac4026708a268b8eb37e98c46",
    "accionPorEstado": "5303520519220e3f15d38f241144c84c4a8d21cf7243351acd5ea74e01e050fe",
    "estadoRecalculo": "429dfdedbe7c0140c5859405f6230f07d72c58966cee419ed2fc9f1fca3d27c3",
    "wireUndo": "ea984a5f54843ba7f3daaf7109d79a82453bf8157668fd8d6927fe38a8263533",
    "marcarEspera": "26b6e7232b637dc71cc9441ac27056c0739469d84477e6ecfe49ff2ba03ca276",
    "vistaRestaurable": "025c76ad623a79addbd5bb04061e03b0a7e2c281e09cdb9fb36674d64f29e381",
    "wireFechaInput": "d3ef172dc5c5ce2812a39d6d4e7f845ffa4cb35e6ac1a763169b93299c593ae3",
}


@pytest.mark.parametrize("nombre", sorted(HUELLAS))
def test_f047_r23_lo_de_f043_no_cambia(nombre) -> None:
    texto = _funcion(_js(), nombre)
    assert hashlib.sha256(texto.encode("utf-8")).hexdigest() == \
        HUELLAS[nombre]


def test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable() -> None:
    js = _js()
    # Funciones con nombre en `app.js` en `dev` 75816f2: F-047 no añade.
    assert len(re.findall(r"function \w+\(", js)) == 302
    variables = [l for l in js.split("\n") if l.startswith("  var recalculo")]
    assert variables == [
        "  var recalculoVigilados = {};        // document_id -> fecha (ISO)",
        "  var recalculoSondeo = null;         // {ultimaValida: ms} mientras sondea",
        "  var recalculoMotivos = {};          // document_id -> motivo (F-047)",
    ]


def test_f047_r19_el_motivo_se_lee_del_primer_contenedor() -> None:
    """El detalle tiene dos contenedores: basta con el primero."""
    r = _node(_programa(
        PAGINA % {"fecha": FECHA, "nuevo": "true"}
        + "body.appendChild(el('div', {'data-parte-contenido': '',"
          " 'data-document-id': 'doc-1', 'data-recalculando': '1'}, []));"
          "esperasDeLaPagina(); salir(recalculoMotivos);",
        ESPERA, VARIABLES))
    assert json.dumps(r) == json.dumps({"doc-1": "nuevo"})
