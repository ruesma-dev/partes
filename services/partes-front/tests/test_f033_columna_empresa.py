# tests/test_f033_columna_empresa.py
"""F-033 · columna «Empresa» en el listado de obras del portal (R1-R8).

Sin red ni PostgreSQL: SQLite en memoria con el ORM real
(`FabricaSesionSqlite`), el `ParteReviewRepository` de verdad y, para el
HTML, `TestClient` sobre `build_app`. Obras, DNIs y recursos SINTETICOS:
dos fichas gemelas `0678` (mismo codigo y nombre, `obra_ide` 501 y 502)
con partes de las empresas 1 (Ruesma) y 28 (Porsan).

La empresa se importa dentro de cada test para que la fase RED falle test
a test (y no como un error de coleccion del modulo entero).
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from jinja2 import Environment, FileSystemLoader
from tests.dobles import FabricaSesionSqlite

CODIGO_GEMELA = "0678"
NOMBRE_GEMELA = "Obra Gemela Sintetica"
RAIZ_SERVICIO = Path(__file__).resolve().parents[1]


def sembrar_parte(
    fabrica: FabricaSesionSqlite,
    doc: str,
    *,
    empresa: int | None,
    obra_ide: int | None,
    obra_codigo: str | None = CODIGO_GEMELA,
    obra_nombre: str | None = NOMBRE_GEMELA,
    recursos: tuple[int | None, ...] = (900,),
    horas: float = 8.0,
) -> None:
    """Un parte activo con una linea normal por recurso."""
    ahora = "2026-03-02T08:00:00+00:00"
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=doc, source_filename=f"{doc}.pdf",
            source_mime_type="application/pdf", source_sha256="sha-" + doc,
            fecha="2026-03-02", fecha_int=20260302, created_at_utc=ahora,
            obra_ide=obra_ide, obra_codigo=obra_codigo,
            obra_nombre=obra_nombre, empresa=empresa))
        for i, recurso in enumerate(recursos):
            s.add(ParteRegistroOrm(
                document_id=doc, line_index=i, fecha="2026-03-02",
                fecha_int=20260302, obra_ide=obra_ide,
                obra_codigo=obra_codigo, obra_nombre=obra_nombre,
                empleado_dni=f"0000{i}{doc[-2:]}X",
                empleado_nombre=f"Persona {doc} {i}", recurso_ide=recurso,
                empleado_ide=recurso,
                tipo_hora="normal", horas=horas, hora_ide=1,
                hora_codigo="HL01"))
        s.commit()


def _repo() -> tuple[ParteReviewRepository, FabricaSesionSqlite]:
    fabrica = FabricaSesionSqlite()
    return ParteReviewRepository(fabrica), fabrica


def _fila(rows, obra_key: str):
    return next(r for r in rows if r.obra_key == obra_key)


# ===================================================================== #
# T1 · reglas puras y repositorio
# ===================================================================== #

def test_f033_r2_varias_empresas_unidas() -> None:
    """Varias empresas en la fila: nombres unidos por « / » en orden
    numerico; un parte con empresa NULL junto a otros con empresa no
    activa el respaldo por recurso."""
    repo, fabrica = _repo()
    sembrar_parte(fabrica, "r2-28", empresa=28, obra_ide=700,
                  obra_codigo="0700", recursos=(910,))
    sembrar_parte(fabrica, "r2-01", empresa=1, obra_ide=700,
                  obra_codigo="0700", recursos=(911,))
    sembrar_parte(fabrica, "r2-nn", empresa=None, obra_ide=700,
                  obra_codigo="0700", recursos=(912,))
    # El recurso 912 es de la empresa 7 en otra obra: NO debe colarse.
    sembrar_parte(fabrica, "r2-ot", empresa=7, obra_ide=701,
                  obra_codigo="0701", recursos=(912,))

    fila = _fila(repo.list_obras(), "obr-700")
    assert fila.empresas == [1, 28]
    assert fila.empresa_texto == "Ruesma / Porsan"


def test_f033_r2_texto_empresas_puro() -> None:
    from application.services.empresas import texto_empresas
    assert texto_empresas([1]) == "Ruesma"
    assert texto_empresas([28]) == "Porsan"
    assert texto_empresas([1, 28]) == "Ruesma / Porsan"
    assert texto_empresas([1, 7, 28]) == "Ruesma / Empresa 7 / Porsan"


def test_f033_r4_partes_null_usa_empresa_del_recurso() -> None:
    """Todos los partes de la fila con empresa NULL: manda la empresa de
    sus recursos, deducida de otros partes con empresa (cualquier obra)."""
    repo, fabrica = _repo()
    sembrar_parte(fabrica, "r4-vj", empresa=None, obra_ide=800,
                  obra_codigo="0800", recursos=(920, 921, None))
    sembrar_parte(fabrica, "r4-p1", empresa=28, obra_ide=801,
                  obra_codigo="0801", recursos=(920,))
    sembrar_parte(fabrica, "r4-p2", empresa=1, obra_ide=802,
                  obra_codigo="0802", recursos=(921,))
    # Un recurso que no esta en la fila no suma aunque tenga empresa.
    sembrar_parte(fabrica, "r4-p3", empresa=7, obra_ide=803,
                  obra_codigo="0803", recursos=(999,))

    fila = _fila(repo.list_obras(), "obr-800")
    assert fila.empresas == [1, 28]
    assert fila.empresa_texto == "Ruesma / Porsan"


def test_f033_r4_empresas_de_fila_puro() -> None:
    from application.services.empresas import empresas_de_fila
    por_recurso = {920: {28}, 921: {1}, 930: {7}}
    # Con empresa en los partes, el respaldo no se mira.
    assert empresas_de_fila({None, 28}, {930}, por_recurso) == [28]
    # Todos NULL: respaldo por recurso, sin nulos y ordenado.
    assert empresas_de_fila({None}, {920, 921, None}, por_recurso) == [1, 28]
    assert empresas_de_fila(set(), {921}, por_recurso) == [1]
    # Recurso desconocido o nulo: nada.
    assert empresas_de_fila({None}, {None, 555}, por_recurso) == []


def test_f033_r5_sin_empresa_guion() -> None:
    from application.services.empresas import texto_empresas
    repo, fabrica = _repo()
    sembrar_parte(fabrica, "r5-vj", empresa=None, obra_ide=850,
                  obra_codigo="0850", recursos=(940, None))
    # El recurso 940 solo sale en otro parte tambien sin empresa.
    sembrar_parte(fabrica, "r5-ot", empresa=None, obra_ide=851,
                  obra_codigo="0851", recursos=(940,))

    fila = _fila(repo.list_obras(), "obr-850")
    assert fila.empresas == []
    assert fila.empresa_texto == "—"
    assert texto_empresas([]) == "—"


def test_f033_r6_numero_desconocido_empresa_n() -> None:
    from application.services.empresas import NOMBRES_EMPRESA, nombre_empresa
    assert NOMBRES_EMPRESA == {1: "Ruesma", 28: "Porsan"}
    assert nombre_empresa(1) == "Ruesma"
    assert nombre_empresa(28) == "Porsan"
    assert nombre_empresa(7) == "Empresa 7"
    repo, fabrica = _repo()
    sembrar_parte(fabrica, "r6-07", empresa=7, obra_ide=860,
                  obra_codigo="0860")
    fila = _fila(repo.list_obras(), "obr-860")
    assert fila.empresas == [7]
    assert fila.empresa_texto == "Empresa 7"


def test_f033_r7_orden_gemelas() -> None:
    """Gemelas (mismo codigo y nombre): por menor empresa, sin empresa
    detras. Se siembran en el orden contrario al esperado."""
    repo, fabrica = _repo()
    sembrar_parte(fabrica, "r7-sn", empresa=None, obra_ide=503,
                  recursos=(950,))
    sembrar_parte(fabrica, "r7-28", empresa=28, obra_ide=501,
                  recursos=(951,))
    sembrar_parte(fabrica, "r7-01", empresa=1, obra_ide=502,
                  recursos=(952,))
    # Otra obra de codigo menor va delante; el orden por codigo manda.
    sembrar_parte(fabrica, "r7-ot", empresa=28, obra_ide=600,
                  obra_codigo="0100", obra_nombre="Otra", recursos=(953,))

    rows = repo.list_obras()
    assert [r.obra_key for r in rows] == [
        "obr-600", "obr-502", "obr-501", "obr-503"]
    assert [r.empresa_texto for r in rows] == [
        "Porsan", "Ruesma", "Porsan", "—"]


# ===================================================================== #
# T2 · plantilla `obras_list.html`
# ===================================================================== #

class _Tabla(HTMLParser):
    """Filas (`tr`) de la tabla del listado: por celda, su etiqueta, su
    texto normalizado y si lleva un `input.col-filter`."""

    def __init__(self) -> None:
        super().__init__()
        self.filas: list[list[dict]] = []
        self._celda: dict | None = None

    def handle_starttag(self, tag, attrs) -> None:
        clases = (dict(attrs).get("class") or "").split()
        if tag == "tr":
            self.filas.append([])
        elif tag in ("th", "td") and self.filas:
            self._celda = {"tag": tag, "texto": "", "filtro": False}
            self.filas[-1].append(self._celda)
        elif tag == "input" and self._celda is not None \
                and "col-filter" in clases:
            self._celda["filtro"] = True

    def handle_endtag(self, tag) -> None:
        if tag in ("th", "td") and self._celda is not None:
            self._celda["texto"] = " ".join(self._celda["texto"].split())
            self._celda = None

    def handle_data(self, data) -> None:
        if self._celda is not None:
            self._celda["texto"] += data


def _gemelas(fabrica: FabricaSesionSqlite) -> None:
    """Las dos fichas 0678: Porsan (501) con dos partes y Ruesma (502)."""
    sembrar_parte(fabrica, "g-28a", empresa=28, obra_ide=501,
                  recursos=(960, 961))
    sembrar_parte(fabrica, "g-28b", empresa=28, obra_ide=501,
                  recursos=(960,), horas=2.0)
    sembrar_parte(fabrica, "g-01a", empresa=1, obra_ide=502,
                  recursos=(962,), horas=6.0)


@pytest.fixture
def entorno_portal(monkeypatch) -> None:
    """Variables obligatorias de `Settings`, con valores de relleno."""
    for clave in ("PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.setenv(clave, "irrelevante-en-tests")
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)


def _html_obras(fabrica: FabricaSesionSqlite, query: str = "") -> str:
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica))
    resp = TestClient(app).get("/obras" + query)
    assert resp.status_code == 200
    return resp.text


def _filas(html: str) -> list[list[dict]]:
    parser = _Tabla()
    parser.feed(html)
    return parser.filas


def test_f033_r1_columna_y_filtro_alineados(entorno_portal) -> None:
    fabrica = FabricaSesionSqlite()
    _gemelas(fabrica)
    cabecera, filtros, *cuerpo = _filas(_html_obras(fabrica))
    titulos = [c["texto"] for c in cabecera]
    assert titulos[:2] == ["Obra", "Empresa"]
    assert len(cabecera) == len(filtros)
    # El filtro de la columna Empresa esta en su misma posicion.
    assert filtros[1]["filtro"] is True
    assert "Filtrar empresa" in _html_obras(fabrica)
    for fila in cuerpo:
        assert len(fila) == len(cabecera)


def test_f033_r3_gemelas_dos_filas_ruesma_porsan(entorno_portal) -> None:
    fabrica = FabricaSesionSqlite()
    _gemelas(fabrica)
    _cab, _fil, *cuerpo = _filas(_html_obras(fabrica))
    assert len(cuerpo) == 2
    obras = [f[0]["texto"] for f in cuerpo]
    assert obras == [f"{CODIGO_GEMELA} · {NOMBRE_GEMELA}"] * 2
    # Orden R7: Ruesma (1) delante de Porsan (28).
    assert [f[1]["texto"] for f in cuerpo] == ["Ruesma", "Porsan"]


def test_f033_r8_obra_key_y_totales_intactos(entorno_portal) -> None:
    fabrica = FabricaSesionSqlite()
    _gemelas(fabrica)
    repo = ParteReviewRepository(fabrica)
    rows = repo.list_obras()
    por_clave = {r.obra_key: r for r in rows}
    assert set(por_clave) == {"obr-501", "obr-502"}
    porsan, ruesma = por_clave["obr-501"], por_clave["obr-502"]
    assert (porsan.num_partes, porsan.num_registros,
            porsan.num_trabajadores, porsan.horas_normales) == (2, 3, 2, 18.0)
    assert (ruesma.num_partes, ruesma.num_registros,
            ruesma.num_trabajadores, ruesma.horas_normales) == (1, 1, 1, 6.0)
    # La busqueda sigue siendo por codigo o nombre, no por empresa.
    assert {r.obra_key for r in repo.list_obras(search="0678")} == {
        "obr-501", "obr-502"}
    assert repo.list_obras(search="Porsan") == []
    # Los enlaces y el borrado siguen apuntando a cada ficha por su clave.
    html = _html_obras(fabrica)
    for clave in ("obr-501", "obr-502"):
        assert f'href="/obras/{clave}"' in html
        assert f'data-del-obra="{clave}"' in html


def test_f033_plantilla_obras_list_parsea() -> None:
    entorno = Environment(loader=FileSystemLoader(
        str(RAIZ_SERVICIO / "templates")))
    entorno.parse(entorno.loader.get_source(entorno, "obras_list.html")[0])
