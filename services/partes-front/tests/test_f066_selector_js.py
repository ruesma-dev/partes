# tests/test_f066_selector_js.py
"""F-066 · el catálogo y el desplegable de código de hora (R7, R9–R11, R23).

- R7: `fetch_tipos_hora` (cliente REAL con sigrid-api falso) omite los
  excluidos, y con él ni `TipoHoraCatalog.get_by_ide` ni el
  `TipoHoraMatcher` de «+ Nuevo» los ven.
- R9: `GET /api/sigrid/tipos-hora` añade `extra` y conserva `ext`.
- R10: `buildOptions` de `app.js`, EJECUTADO en node sobre un DOM mínimo
  (patrón de `test_f064_filtros_js.py`), agrupa por `extra`.
- R11 y R23: fuente (sin regla en el JS; disyuntivos intactos).

Sin red ni BBDD. Datos sintéticos.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from application.services.tipo_hora_catalog import TipoHoraCatalog
from application.services.tipo_hora_matcher import TipoHoraMatcher
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite
from tests.test_f066_set_registro_hora import SigridLookupFalso

SV4 = Path(__file__).resolve().parents[1]
APP_JS = SV4 / "static" / "app.js"
NODE = shutil.which("node")

COLS = ["ide", "codigo", "descripcion", "ext", "pre", "prenom"]


class SigridConFilas(SigridLookupFalso):
    """El cliente real; `auxhor` lo pone cada test."""

    filas: list[list] = []

    def _post_sql_read(self, *, sql, parameters, label, max_rows=None):
        if "FROM auxhor" in sql and parameters[-2] == 0:
            return list(COLS), [list(f) for f in self.filas]
        return [], []


def _cliente(filas) -> SigridConFilas:
    c = SigridConFilas(base_url="http://sigrid.invalid",
                       function_key="clave-de-test", database="bd")
    c.filas = filas
    return c


FILAS = [
    [1, "HL01", "HORA LABORABLE OFICIAL", 0, 15.0, 12.0],
    [63, "HENC", "HORA ENCARGADO", 0, 1.0, None],
    [7, "HEOF", "HORA EXTRA OFICIAL", 0, 20.0, 18.0],
    [64, " henc ", "Otra HENC con espacios", 0, None, None],
    [3, "CI01", "INCIDENCIA", 0, None, None],
]


# --------------------------------- R7 ----------------------------------- #

def test_f066_r7_catalogo_sin_excluidos() -> None:
    tipos = _cliente(FILAS).fetch_tipos_hora()
    assert [t.codigo for t in tipos] == ["CI01", "HEOF", "HL01"]
    assert all(t.ide not in (63, 64) for t in tipos)


def test_f066_r7_catalogo_por_ide_no_ve_excluidos() -> None:
    catalogo = TipoHoraCatalog(client=_cliente(FILAS))
    assert catalogo.get_by_ide(63) is None
    assert catalogo.get_by_ide(64) is None
    assert catalogo.get_by_ide(7).codigo == "HEOF"
    assert "HENC" not in {(t.codigo or "").strip().upper()
                          for t in catalogo.list()}


def test_f066_r7_matcher_encargado_no_elige_henc() -> None:
    tipos = _cliente(FILAS).fetch_tipos_hora()
    matcher = TipoHoraMatcher(tipos)
    for extra in (False, True):
        m = matcher.match("Encargado", extra=extra)
        assert m is None or (m.codigo or "").strip().upper() != "HENC"


def test_f066_r7_sin_excluidos_nada_cambia() -> None:
    filas = [f for f in FILAS if f[0] not in (63, 64)]
    assert [t.codigo for t in _cliente(filas).fetch_tipos_hora()] == \
        ["CI01", "HEOF", "HL01"]


# --------------------------------- R9 ----------------------------------- #

def test_f066_r9_tipos_hora_lleva_extra(monkeypatch) -> None:
    for clave in ("PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.setenv(clave, "irrelevante-en-tests")
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-prueba")
    monkeypatch.setenv("SIGRID_API_DATABASE", "ruesma_rep")
    monkeypatch.setattr(app_mod, "SigridLookupClient", SigridLookupFalso)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(FabricaSesionSqlite()))
    r = TestClient(app).get("/api/sigrid/tipos-hora")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    vistos = {i["codigo"]: (i["ext"], i["extra"]) for i in cuerpo["items"]}
    # `SigridLookupFalso` sirve HL01, HEOF, HECAP, HL09 (ext 1), "" (sale
    # como None) y HENC.
    assert vistos == {"HL01": (0, False), "HEOF": (0, True),
                      "HECAP": (0, True), "HL09": (1, False),
                      None: (0, False)}
    assert all(set(i) == {"ide", "codigo", "descripcion", "ext", "extra"}
               for i in cuerpo["items"])
    assert all(i["extra"] is True or i["extra"] is False
               for i in cuerpo["items"])


# --------------------------------- R10 ---------------------------------- #

def _build_options() -> str:
    js = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"\n  function buildOptions\(.*?\n  \}\n", js, re.DOTALL)
    assert m, "app.js no define buildOptions"
    return m.group(0)


_DOM = """
function El(tag) { this.tag = tag; this.children = []; this.label = "";
  this.value = ""; this.textContent = ""; this.selected = false; }
El.prototype.appendChild = function (c) { this.children.push(c); return c; };
var document = { createElement: function (t) { return new El(t); } };
"""


def _node(programa: str):
    if NODE is None:
        pytest.skip("node no está instalado: no se puede ejecutar el JS")
    with tempfile.TemporaryDirectory() as carpeta:
        fichero = Path(carpeta) / "programa.js"
        fichero.write_text(programa, encoding="utf-8")
        r = subprocess.run([NODE, str(fichero)], capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _grupos(items, current):
    programa = (_DOM + _build_options() + f"""
var select = new El("select");
buildOptions(select, {json.dumps(items)}, {json.dumps(current)});
console.log(JSON.stringify(select.children.map(function (g) {{
  return {{ tag: g.tag, label: g.label, opciones: g.children.map(function (o) {{
    return [o.tag, o.value, o.textContent, o.selected]; }}) }};
}})));
""")
    return _node(programa)


ITEMS = [
    {"ide": 1, "codigo": "HL01", "descripcion": "Ordinaria", "ext": 0,
     "extra": False},
    {"ide": 7, "codigo": "HEOF", "descripcion": "Extra oficial", "ext": 0,
     "extra": True},
    {"ide": 9, "codigo": "HL09", "descripcion": "Con ext", "ext": 1,
     "extra": False},
    {"ide": 8, "codigo": "HECAP", "descripcion": "Extra capataz", "ext": 0,
     "extra": True},
    {"ide": 11, "codigo": None, "descripcion": "Sin campo extra", "ext": 1},
]


def test_f066_r10_grupos_por_extra() -> None:
    grupos = _grupos(ITEMS, "8")
    assert grupos == [
        {"tag": "optgroup", "label": "Horas ordinarias", "opciones": [
            ["option", "1", "HL01 · Ordinaria", False],
            ["option", "9", "HL09 · Con ext", False],
            ["option", "11", "Sin campo extra", False]]},
        {"tag": "optgroup", "label": "Horas extra", "opciones": [
            ["option", "7", "HEOF · Extra oficial", False],
            ["option", "8", "HECAP · Extra capataz", True]]},
    ]


def test_f066_r10_solo_true_es_extra() -> None:
    items = [{"ide": 1, "codigo": "A", "descripcion": "a", "extra": "true"},
             {"ide": 2, "codigo": "B", "descripcion": "b", "extra": 1},
             {"ide": 3, "codigo": "C", "descripcion": "c", "extra": True}]
    grupos = _grupos(items, "")
    assert [(g["label"], [o[1] for o in g["opciones"]]) for g in grupos] == [
        ("Horas ordinarias", ["1", "2"]), ("Horas extra", ["3"])]
    assert not any(o[3] for g in grupos for o in g["opciones"])


def test_f066_r10_grupo_vacio_no_sale() -> None:
    solo_extra = [i for i in ITEMS if i.get("extra") is True]
    assert [g["label"] for g in _grupos(solo_extra, "7")] == ["Horas extra"]


# --------------------------------- R11 ---------------------------------- #

def test_f066_r11_js_sin_regla() -> None:
    fuente = _build_options()
    assert not re.search(r"\.ext\b", fuente)
    assert "HENC" not in fuente and "startsWith" not in fuente
    assert "t.extra === true" in fuente
    js = APP_JS.read_text(encoding="utf-8")
    assert "HENC" not in js
    assert not re.search(r"""startsWith\(\s*["']HE""", js)


# --------------------------------- R23 ---------------------------------- #

DISYUNTIVOS = [
    ("infrastructure/database/parte_repository.py",
     'return (reg.tipo_hora or "") == "extra" or reg.hora_ext == 1'),
    ("infrastructure/database/parte_repository.py",
     'if r.hora_ext == 1 or (r.tipo_hora or "") == "extra":'),
    ("interface_adapters/web/app.py",
     'elif (r.tipo_hora or "") == "extra" or r.hora_ext == 1:'),
    ("templates/obra_detail.html",
     "{% elif r.hora_ext == 1 or r.tipo_hora == 'extra' %}"),
    ("templates/parte_detail.html",
     "{% elif r.hora_ext == 1 or r.tipo_hora == 'extra' %}"),
    ("templates/trabajador_detail.html",
     "{% elif r.hora_ext == 1 or r.tipo_hora == 'extra' %}"),
]


@pytest.mark.parametrize("fichero, texto", DISYUNTIVOS)
def test_f066_r23_disyuntivos_intactos(fichero, texto) -> None:
    assert (SV4 / fichero).read_text(encoding="utf-8").count(texto) == 1
