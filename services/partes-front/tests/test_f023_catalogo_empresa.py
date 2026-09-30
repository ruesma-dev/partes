# tests/test_f023_catalogo_empresa.py
"""F-023 · R3-R4 y R38-R42 en el portal (sv4).

  - `cliente`: `SigridLookupClient` pagina los listados como sv3 (R3),
    trata `truncated: true` como excepcion (R4), da la empresa de cada
    ficha sin tocar su filtro de alta a hoy (R38) y lista las obras una por
    `ide` con su empresa, sin esconder la gemela de la otra empresa (R39).
  - `endpoint`: `/api/sigrid/empleados` y `/api/sigrid/obras` anaden
    `empresa` sin quitar ni renombrar nada (R40).
  - `soltar`: al casar o reasignar el empleado de unas lineas se sueltan
    su reside, recurso, cif, hmo y estado, solo en las no congeladas (R42).

Sin red ni PostgreSQL: sigrid-api simulado con `httpx.MockTransport` y
SQLite en memoria. Datos SINTETICOS.
"""
from __future__ import annotations

import json
from datetime import datetime

import httpx
import pytest

from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import (
    EmpleadoOption,
    ObraOption,
    SigridLookupClient,
)

PAGINA = 5000


class SigridFalso:
    """sigrid-api en memoria que sirve la tabla por OFFSET/FETCH."""

    def __init__(self, columnas, filas, *, truncated=False) -> None:
        self.columnas = list(columnas)
        self.filas = [list(f) for f in filas]
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        self.peticiones.append(cuerpo)
        filas = self.filas
        if "FETCH NEXT ? ROWS ONLY" in cuerpo["sql"]:
            desde, cuantas = cuerpo["parameters"][-2:]
            filas = filas[desde:desde + cuantas]
        filas = filas[:cuerpo["max_rows"]]
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso) -> SigridLookupClient:
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    return SigridLookupClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


COLS_OBRA = ["ide", "codigo", "nombre", "empresa"]


def _obras(n: int) -> list[list]:
    return [[i, f"{i:04d}", f"Obra {i}", 1] for i in range(1, n + 1)]


# ============================ cliente · R3 ============================== #

def test_f023_r3_cliente_encadena_paginas(monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(PAGINA + 2))
    obras = _cliente(monkeypatch, falso).fetch_obras()
    assert len(obras) == PAGINA + 2
    assert [p["parameters"] for p in falso.peticiones] == \
        [[0, PAGINA], [PAGINA, PAGINA]]
    assert {p["max_rows"] for p in falso.peticiones} == {PAGINA + 1}


def test_f023_r3_cliente_pagina_justa_y_tres_paginas(monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(PAGINA))
    assert len(_cliente(monkeypatch, falso).fetch_obras()) == PAGINA
    assert len(falso.peticiones) == 2
    tres = SigridFalso(COLS_OBRA, _obras(2 * PAGINA + 1))
    assert len(_cliente(monkeypatch, tres).fetch_obras()) == 2 * PAGINA + 1
    assert [p["parameters"][0] for p in tres.peticiones] == \
        [0, PAGINA, 2 * PAGINA]


def test_f023_r3_cliente_pagina_desbordada_es_error(monkeypatch) -> None:
    class Desbocado(SigridFalso):
        def __call__(self, request):
            self.peticiones.append(json.loads(request.content))
            return httpx.Response(200, json={
                "ok": True, "columns": self.columnas, "rows": self.filas})

    with pytest.raises(RuntimeError):
        _cliente(monkeypatch, Desbocado(COLS_OBRA,
                                        _obras(PAGINA + 1))).fetch_obras()


@pytest.mark.parametrize("metodo, args, orden, params", [
    ("fetch_obras", (), "con.ide", []),
    ("fetch_tipos_hora", (), "auxhor.ide", []),
    ("fetch_partidas_obra", (77,), "obrparpar.ide", [77]),
])
def test_f023_r3_cliente_cada_listado_pagina_por_su_clave(
        monkeypatch, metodo, args, orden, params) -> None:
    falso = SigridFalso(["ide"], [])
    getattr(_cliente(monkeypatch, falso), metodo)(*args)
    (peticion,) = falso.peticiones
    sql = _sql(peticion["sql"])
    assert sql.endswith(
        f"ORDER BY {orden} OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert sql.count("ORDER BY") == 1
    assert peticion["parameters"] == [*params, 0, PAGINA]
    assert peticion["max_rows"] == PAGINA + 1


def test_f023_r3_r38_cliente_empleados_paginados_con_su_filtro_de_alta(
        monkeypatch) -> None:
    falso = SigridFalso(["ide"], [])
    _cliente(monkeypatch, falso).fetch_empleados()
    (peticion,) = falso.peticiones
    sql = _sql(peticion["sql"])
    hoy = int(datetime.now().strftime("%Y%m%d"))
    assert peticion["parameters"] == [hoy, hoy, 0, PAGINA]
    assert "(con.fecbaj IS NULL OR con.fecbaj = 0 OR con.fecbaj > ?)" in sql
    assert ("rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR "
            "rescon.fecbaj > ?") in sql
    assert sql.endswith(
        "ORDER BY con.ide, res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")


def test_f023_cliente_tipos_de_hora_en_el_orden_de_siempre(monkeypatch) -> None:
    falso = SigridFalso(
        ["ide", "codigo", "descripcion", "ext", "pre", "prenom"],
        [[1, "HL02", "b", 0, None, None], [2, "HE01", "c", 1, None, None],
         [3, "HL01", "a", 0, None, None], [4, None, "d", 0, None, None]])
    assert [t.ide for t in _cliente(monkeypatch, falso).fetch_tipos_hora()] \
        == [4, 3, 1, 2]


# ============================ cliente · R4 ============================== #

@pytest.mark.parametrize("metodo, args", [
    ("fetch_obras", ()), ("fetch_empleados", ()), ("fetch_tipos_hora", ()),
    ("fetch_partidas_obra", (77,)), ("fetch_dnis_sin_extra", ({"1A"},)),
    ("fetch_hora_extra_recurso", (5,)),
])
def test_f023_r4_cliente_truncated_es_una_excepcion(
        monkeypatch, metodo, args) -> None:
    falso = SigridFalso(COLS_OBRA, _obras(2), truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(_cliente(monkeypatch, falso), metodo)(*args)


def test_f023_r4_cliente_los_lotes_acotados_no_paginan(monkeypatch) -> None:
    falso = SigridFalso(["dni", "max_he"], [["1A", 1]])
    assert _cliente(monkeypatch, falso).fetch_dnis_sin_extra({"1a"}) == set()
    (peticion,) = falso.peticiones
    assert "OFFSET" not in peticion["sql"]
    assert peticion["max_rows"] == 10000


# ======================= cliente · R38 y R39 =========================== #

def test_f023_r38_cliente_cada_ficha_trae_su_empresa(monkeypatch) -> None:
    falso = SigridFalso(
        ["ide", "codigo", "nombre", "dni", "reside", "categoria", "candef",
         "empresa"],
        [[10, "E10", "Uno", "00000001R", 900, "Oficial", 8.0, 1],
         [11, "E11", "Uno", "00000001R", 902, None, None, 28],
         [11, "E11", "Uno", "00000001R", 903, "Peon", 8.0, 28]])
    fichas = _cliente(monkeypatch, falso).fetch_empleados()
    assert [(e.ide, e.empresa, e.reside, e.categoria) for e in fichas] == \
        [(10, 1, 900, "Oficial"), (11, 28, 902, "Peon")]
    assert "con.emp AS empresa" in _sql(falso.peticiones[0]["sql"])


def test_f023_r39_cliente_las_gemelas_salen_las_dos_con_su_empresa(
        monkeypatch) -> None:
    falso = SigridFalso(COLS_OBRA, [
        [100, "0100", "Norte", 1], [200, "0100", "Sur", 28],
        [200, "0100", "Sur", 28], [300, None, "Sin codigo", 1],
        [None, "0400", "Sin ide", 1]])
    obras = _cliente(monkeypatch, falso).fetch_obras()
    assert obras == [ObraOption(ide=100, codigo="0100", nombre="Norte",
                                empresa=1),
                     ObraOption(ide=200, codigo="0100", nombre="Sur",
                                empresa=28)]
    assert "con.emp AS empresa" in _sql(falso.peticiones[0]["sql"])


def test_f023_r38_r39_la_empresa_tiene_valor_por_defecto() -> None:
    """Los dobles anteriores a F-023 construyen las opciones sin empresa."""
    assert EmpleadoOption(ide=1, codigo=None, nombre=None,
                          dni=None).empresa is None
    assert ObraOption(ide=1, codigo=None, nombre=None).empresa is None


# ============================ endpoint · R40 ============================ #

from fastapi.testclient import TestClient  # noqa: E402

from application.services.obra_catalog import ObraCatalog  # noqa: E402
from config.settings import Settings  # noqa: E402
from infrastructure.database.orm_models import ParteDocumentOrm  # noqa: E402
from infrastructure.database.parte_repository import (  # noqa: E402
    ParteReviewRepository,
)
from interface_adapters.web import app as app_mod  # noqa: E402
from interface_adapters.web.app import build_app  # noqa: E402
from tests.dobles import FabricaSesionSqlite, sembrar_parte  # noqa: E402

GEMELAS = [ObraOption(ide=100, codigo="0100", nombre="Norte", empresa=1),
           ObraOption(ide=200, codigo="0100", nombre="Sur", empresa=28),
           ObraOption(ide=300, codigo="0300", nombre="Este", empresa=1)]
FICHAS = [EmpleadoOption(ide=10, codigo="E10", nombre="Uno", dni="00000001R",
                         categoria="Oficial", candef=8.0, reside=900,
                         empresa=1),
          EmpleadoOption(ide=11, codigo="E11", nombre="Uno", dni="00000001R",
                         categoria=None, candef=None, reside=902, empresa=28)]


class LookupPortalFake:
    """Doble de `SigridLookupClient` para montar el portal sin red."""

    def __init__(self, **_kw) -> None:
        pass

    def fetch_tipos_hora(self) -> list:
        return []

    def fetch_obras(self) -> list:
        return list(GEMELAS)

    def fetch_empleados(self) -> list:
        return list(FICHAS)

    def fetch_partidas_obra(self, _obra_ide: int) -> list:
        return []

    def fetch_hora_extra_recurso(self, _recurso_ide: int):
        return None

    def fetch_dnis_sin_extra(self, _dnis) -> set:
        return set()


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": "clave-de-test",
        "SIGRID_API_DATABASE": "bd",
    }.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(app_mod, "SigridLookupClient", LookupPortalFake)
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"estado": None}])
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    return TestClient(app), fabrica


def test_f023_r40_endpoint_obras_anade_la_empresa(portal) -> None:
    cliente, _ = portal
    cuerpo = cliente.get("/api/sigrid/obras").json()
    assert cuerpo["ok"] is True
    assert cuerpo["items"] == [
        {"ide": 100, "codigo": "0100", "nombre": "Norte", "empresa": 1},
        {"ide": 200, "codigo": "0100", "nombre": "Sur", "empresa": 28},
        {"ide": 300, "codigo": "0300", "nombre": "Este", "empresa": 1},
    ]


def test_f023_r40_endpoint_empleados_anade_la_empresa_sin_quitar_nada(
        portal) -> None:
    cliente, _ = portal
    items = cliente.get("/api/sigrid/empleados").json()["items"]
    assert [(i["ide"], i["empresa"]) for i in items] == [(10, 1), (11, 28)]
    for i in items:
        assert {"ide", "codigo", "nombre", "dni", "reside", "categoria",
                "candef", "jornada_sugerida", "empresa"} <= set(i)
    assert items[0]["reside"] == 900 and items[0]["categoria"] == "Oficial"


def test_f023_r39_endpoint_el_cambio_de_obra_respeta_la_gemela_elegida(
        portal) -> None:
    """El combo envia el ide de la obra elegida: con dos obras del mismo
    codigo, el servidor no puede cambiarla por la otra al resolver."""
    cliente, fabrica = portal
    for ide, nombre in ((200, "Sur"), (100, "Norte")):
        # Sin nombre: el del catalogo manda, asi que la obra se resolvio.
        r = cliente.patch("/api/partes/doc-f004/obra",
                          json={"codigo": "0100", "ide": ide})
        assert r.status_code == 200, r.text
        with fabrica.create_session() as s:
            doc = s.get(ParteDocumentOrm, "doc-f004")
            assert (doc.obra_ide, doc.obra_nombre) == (ide, nombre)


def test_f023_r39_endpoint_codigo_unico_sin_ide_se_resuelve(portal) -> None:
    cliente, fabrica = portal
    r = cliente.patch("/api/partes/doc-f004/obra", json={"codigo": "0300"})
    assert r.status_code == 200, r.text
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, "doc-f004")
        assert (doc.obra_ide, doc.obra_nombre) == (300, "Este")


def test_f023_r39_endpoint_catalogo_por_codigo_solo_si_es_unico() -> None:
    catalogo = ObraCatalog(client=LookupPortalFake())
    assert catalogo.get_by_codigo("0100") is None          # dos empresas
    assert catalogo.get_by_codigo(" 0300 ").ide == 300
    assert catalogo.get_by_codigo(None) is None
    assert catalogo.get_by_ide(200).empresa == 28
    assert catalogo.get_by_ide(999) is None
    assert catalogo.get_by_ide(None) is None
    assert [o.ide for o in catalogo.list()] == [100, 200, 300]
