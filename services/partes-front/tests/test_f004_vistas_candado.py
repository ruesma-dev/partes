# tests/test_f004_vistas_candado.py
"""F-004 · el candado en las vistas (R14, R15, R17).

La UI no es la que manda —el servidor ya responde 409—, pero una fila que
se deja escribir y luego rebota es una trampa: el usuario teclea, guarda,
ve un error y no sabe por que. Aqui se comprueba sobre el HTML REAL que
la fila congelada sale bloqueada, con su candado y su motivo, y que la
fila libre no cambia en nada.

El flag y el motivo los calcula el SERVIDOR con la misma funcion que las
guardas (R1): en JS no se recalcula nada.
"""
from __future__ import annotations

import json
import re

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte

CANDADO = "\U0001F512"          # 🔒


def _settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def montaje(entorno):
    def _montar(lineas, *, aprobado: bool = False, **kw):
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, lineas, aprobado=aprobado, **kw)
        app = build_app(_settings(),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app), fabrica, ids
    return _montar


def _fila(html: str, registro_id: int) -> str:
    """La fila <tr> de ese registro (para no confundirla con las demas)."""
    marca = f'data-registro-id="{registro_id}"'
    ini = html.index(marca)
    return html[ini:html.index("</tr>", ini)]


def _regs_de_la_matriz(html: str) -> list[dict]:
    """Los `regs` que la celda de la matriz le pasa al popup (R15)."""
    crudo = re.search(r"data-regs='([^']*)'", html)
    assert crudo, "la celda de la matriz tiene que llevar sus lineas"
    return json.loads(crudo.group(1).replace("&#34;", '"')
                      .replace("&amp;", "&"))


VISTAS = [
    pytest.param("/obras/obr-10?period=2026-03&modo=natural", id="obra"),
    pytest.param("/trabajadores/emp-77?period=2026-03&modo=natural",
                 id="trabajador"),
    pytest.param("/partes/doc-f004", id="parte"),
]


# ------------------------------ R14 ------------------------------------ #

@pytest.mark.parametrize("url", VISTAS)
@pytest.mark.parametrize("linea,aprobado", [
    pytest.param({"estado": None}, True, id="doc-aprobado"),
    pytest.param({"estado": "encolado"}, False, id="linea-encolada"),
    pytest.param({"estado": "registrado"}, False, id="linea-registrada"),
])
def test_f004_r14_la_linea_congelada_sale_bloqueada(
        montaje, url, linea, aprobado) -> None:
    cliente, _f, ids = montaje([linea], aprobado=aprobado)
    fila = _fila(cliente.get(url).text, ids[0])
    assert 'data-congelado="1"' in fila
    assert CANDADO in fila
    assert "disabled" in fila
    assert "line-del" not in fila     # sin aspa de borrado


@pytest.mark.parametrize("url", VISTAS)
def test_f004_r14_la_linea_libre_no_lleva_candado(montaje, url) -> None:
    cliente, _f, ids = montaje([{"estado": "omitido"}])
    fila = _fila(cliente.get(url).text, ids[0])
    assert 'data-congelado="1"' not in fila
    assert CANDADO not in fila
    assert "disabled" not in fila
    assert "line-del" in fila


@pytest.mark.parametrize("url", VISTAS)
def test_f004_r14_el_candado_explica_el_motivo(montaje, url) -> None:
    """El tooltip viene del servidor: el mismo texto del 409."""
    cliente, _f, ids = montaje([{"estado": "registrado"}])
    fila = _fila(cliente.get(url).text, ids[0])
    assert "Sigrid" in fila
    assert "congelado-motivo" in fila


@pytest.mark.parametrize("url", VISTAS)
def test_f004_r14_en_la_misma_tabla_conviven_congelada_y_libre(
        montaje, url) -> None:
    cliente, _f, ids = montaje(
        [{"estado": "registrado"}, {"estado": "omitido"}])
    html = cliente.get(url).text
    assert 'data-congelado="1"' in _fila(html, ids[0])
    assert 'data-congelado="1"' not in _fila(html, ids[1])


def test_f004_r14_el_flag_lo_calcula_el_repositorio(montaje) -> None:
    """R14: el flag y el motivo viajan del servidor. Si la vista los
    recalculase en JS, acabarian discrepando de la guarda."""
    _cliente, fabrica, ids = montaje(
        [{"estado": "registrado"}, {"estado": None}])
    detalle = ParteReviewRepository(fabrica).get_worker("emp-77")
    congelados = {v.id: (v.congelado, v.congelado_motivo)
                  for v in detalle.registros}
    assert congelados[ids[0]][0] is True
    assert "Sigrid" in congelados[ids[0]][1]
    assert congelados[ids[1]] == (False, None)


# ------------------------------ R15 ------------------------------------ #

def test_f004_r15_la_celda_de_la_matriz_marca_las_lineas_congeladas(
        montaje) -> None:
    cliente, _f, ids = montaje(
        [{"estado": "registrado", "tipo": "normal"},
         {"estado": None, "tipo": "extra", "horas": 2.0}])
    regs = _regs_de_la_matriz(
        cliente.get("/obras/obr-10?period=2026-03&modo=natural").text)
    por_id = {r["id"]: r for r in regs}
    assert por_id[ids[0]].get("c") == 1
    assert por_id[ids[1]].get("c") in (0, None)


def test_f004_r15_sin_congeladas_la_celda_no_marca_nada(montaje) -> None:
    cliente, _f, _ids = montaje([{"estado": "omitido"}])
    regs = _regs_de_la_matriz(
        cliente.get("/obras/obr-10?period=2026-03&modo=natural").text)
    assert all(r.get("c") in (0, None) for r in regs)


# ------------------------------ R17 ------------------------------------ #

def test_f004_r17_el_parte_aprobado_avisa_y_bloquea_la_cabecera(
        montaje) -> None:
    cliente, _f, _ids = montaje([{"estado": None}], aprobado=True)
    html = cliente.get("/partes/doc-f004").text
    aviso = re.search(r'<div class="alert[^"]*parte-congelado"[^>]*>(.*?)</div>',
                      html, re.S)
    assert aviso, "un parte aprobado tiene que avisar de por que no se edita"
    assert "Marcar pendiente" in aviso.group(1)
    assert 'class="fecha-edit" id="fechaEdit"' in html
    fecha = html[html.index('id="fechaEdit"'):]
    assert "disabled" in fecha[:400]
    assert "data-add-line" in html
    boton = html[html.index("data-add-line"):]
    assert "disabled" in boton[:400]


def test_f004_r17_el_parte_pendiente_no_lleva_aviso_ni_bloqueos(
        montaje) -> None:
    cliente, _f, _ids = montaje([{"estado": "omitido"}])
    html = cliente.get("/partes/doc-f004").text
    assert "parte-congelado" not in html
    fecha = html[html.index('id="fechaEdit"'):]
    assert "disabled" not in fecha[:400]


def test_f004_r17_un_parte_sin_aprobar_con_linea_en_sigrid_tambien_avisa(
        montaje) -> None:
    """R2: la cabecera propaga a TODAS las lineas; basta una en Sigrid."""
    cliente, _f, _ids = montaje([{"estado": "registrado"}, {"estado": None}])
    html = cliente.get("/partes/doc-f004").text
    assert "parte-congelado" in html


def test_f004_r18_el_boton_de_aprobar_sigue_en_el_parte(montaje) -> None:
    """La congelacion bloquea ediciones, nunca el camino a Sigrid."""
    cliente, _f, _ids = montaje([{"estado": "omitido"}], aprobado=True)
    html = cliente.get("/partes/doc-f004").text
    assert "/unapprove" in html
    assert "aprobar-linea" in cliente.get(
        "/obras/obr-10?period=2026-03&modo=natural").text
