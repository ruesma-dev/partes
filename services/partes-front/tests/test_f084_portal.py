# tests/test_f084_portal.py
"""F-084 · el portal: pestaña `/problemas`, contador, recuperar y deshacer.

`build_app` con el repositorio real sobre SQLite y una cola doble (como
F-042). Cubre R11-R16 (la pestaña), R17-R22 por HTTP, R18 y su fallo de
cola, R23 (la rama de deshacer), R25 (navegación y contador, también
cuando el resumen falla) y R26 (descartar con `back=/problemas`). Ni red ni
PostgreSQL. Datos sintéticos, sin DNIs ni nombres reales.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.persistencia import recalculo_publisher as rp
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite
from tests.test_f084_recuperar import _sembrar

RAIZ = Path(__file__).resolve().parents[1]
ACTOR = "revisora@ejemplo.es"
CABECERA = {"X-MS-CLIENT-PRINCIPAL-NAME": ACTOR}
DNI_FALSO = "DNI-FICTICIO-1"


class ColaFake:
    """`ColaCliente` reducido a `enviar`; apunta o falla."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.enviados: list[tuple[str, dict]] = []
        self._error = error

    def enviar(self, queue_name: str, payload: dict) -> None:
        if self._error is not None:
            raise self._error
        self.enviados.append((queue_name, payload))


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    return monkeypatch


def _montar(*, cola: ColaFake | None = None, repo=None, pdf: bool = True):
    fabrica = FabricaSesionSqlite()
    cola = cola or ColaFake()
    settings = Settings(_env_file=None, graph_key="clave-de-pruebas"
                        if pdf else None)
    app = build_app(settings,
                    repository=repo or ParteReviewRepository(fabrica),
                    cola_cliente=cola)
    return TestClient(app), cola, fabrica


def _doc(fabrica, id_: str) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, id_)


def _sustituido(fabrica, **kw) -> None:
    _sembrar(fabrica, "nuevo", email_id="correo-1",
             creado="2026-11-26T10:01:39+00:00")
    _sembrar(fabrica, "viejo", activo=False, sustituido_por_id="nuevo",
             sustituido_at="2026-11-26T10:01:39+00:00", **kw)


def _recuperar(cliente, doc: str = "viejo", **cuerpo):
    return cliente.post(f"/api/partes/{doc}/recuperar", json=cuerpo,
                        headers=CABECERA)


def _motivos_enviados(cola: ColaFake) -> list[str]:
    return [p.get("motivo") for _q, p in cola.enviados]


# ======================== R11-R16 · la pestaña =========================== #

def test_f084_r11_la_pestana_lista_por_motivo_con_sus_datos() -> None:
    cliente, _cola, fabrica = _montar()
    _sustituido(fabrica, aprobado=True)
    _sembrar(fabrica, "sin-obra", obra_ide=None, obra_codigo=None,
             fecha="2026-11-20", lineas=[{"ide": 1, "horas": 8.0},
                                         {"ide": 2, "horas": 4.5}])
    r = cliente.get("/problemas")
    assert r.status_code == 200
    html = r.text
    # Agrupado por motivo, los que cuentan primero.
    assert html.index("Sin obra casada") < html.index(
        "Sustituido por otra página del mismo correo")
    fila_obra = _fila(html, "sin-obra")
    assert "20/11/2026" in fila_obra or "2026-11-20" in fila_obra
    assert "100" in fila_obra and "Obra leida" in fila_obra
    assert "4/6" in fila_obra                     # página / páginas
    assert "Partes semana" in fila_obra
    assert "12.5" in fila_obra                    # horas de líneas vivas
    assert re.search(r">\s*2\s*<", fila_obra)     # nº de trabajadores
    fila_viejo = _fila(html, "viejo")
    assert "aprobado" in fila_viejo
    assert 'href="/partes/nuevo"' in fila_viejo   # sustituto activo
    assert "2026-11-26" in fila_viejo             # hora de la sustitución


def test_f084_r11_la_insignia_en_sigrid() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "en-sigrid", activo=False,
             lineas=[{"estado": "registrado"}])
    assert "en Sigrid" in _fila(cliente.get("/problemas").text, "en-sigrid")


def test_f084_r11_sustituto_inactivo_sin_enlace() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "nuevo", activo=False, sustituido_por_id="otro")
    _sembrar(fabrica, "viejo", activo=False, sustituido_por_id="nuevo")
    fila = _fila(cliente.get("/problemas").text, "viejo")
    assert 'href="/partes/nuevo"' not in fila
    assert "inactivo" in fila


def _fila(html: str, doc_id: str) -> str:
    m = re.search(r'<tr[^>]*data-document-id="' + re.escape(doc_id)
                  + r'"[^>]*>(.*?)</tr>', html, re.S)
    assert m, f"no hay fila para {doc_id}"
    return m.group(1)


def test_f084_r12_ver_pdf_si_hay_pdf_archivado() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "con-pdf", obra_ide=None)
    _sembrar(fabrica, "sin-pdf", obra_ide=None, pdf=False,
             obra_codigo="0200")
    html = cliente.get("/problemas").text
    assert 'data-parte-pdf="con-pdf"' in _fila(html, "con-pdf")
    assert "data-parte-pdf" not in _fila(html, "sin-pdf")


def test_f084_r12_sin_visor_no_hay_ver_pdf() -> None:
    cliente, _cola, fabrica = _montar(pdf=False)
    _sembrar(fabrica, "con-pdf", obra_ide=None)
    assert "data-parte-pdf" not in cliente.get("/problemas").text


def test_f084_r13_un_activo_enlaza_a_su_detalle_sin_recuperar() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "sin-obra", obra_ide=None)
    fila = _fila(cliente.get("/problemas").text, "sin-obra")
    assert 'href="/partes/sin-obra"' in fila
    assert "data-recuperar" not in fila
    assert "/documents/sin-obra/delete" not in fila


def test_f084_r14_un_sustituido_ofrece_recuperar_y_descartar() -> None:
    cliente, _cola, fabrica = _montar()
    _sustituido(fabrica)
    fila = _fila(cliente.get("/problemas").text, "viejo")
    assert 'data-recuperar="viejo"' in fila
    assert 'action="/documents/viejo/delete"' in fila
    assert 'name="back" value="/problemas"' in fila
    assert 'href="/partes/viejo"' not in fila


def test_f084_r15_sin_problemas_lo_dice() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "sano")
    html = cliente.get("/problemas").text
    assert "No hay partes con problemas" in html
    assert "data-document-id" not in html


def test_f084_r16_la_pestana_no_muestra_dnis() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "sin-obra", obra_ide=None)
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, "sin-obra")
        for reg in doc.registros:
            reg.empleado_dni = DNI_FALSO
            reg.recurso_cif = DNI_FALSO
        s.commit()
    assert DNI_FALSO not in cliente.get("/problemas").text


# ================ R17-R22 · POST /api/partes/{id}/recuperar ============== #

def test_f084_r17_r18_recuperar_pide_el_recalculo() -> None:
    cliente, cola, fabrica = _montar()
    _sustituido(fabrica)
    r = _recuperar(cliente, fecha="25/11/2026")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "document_id": "viejo",
                        "fecha": "2026-11-25", "recalculo": "pedido"}
    assert _motivos_enviados(cola) == [rp.MOTIVO_RECUPERAR_PARTE]
    assert cola.enviados[0][1]["document_id"] == "viejo"
    assert cola.enviados[0][1]["solicitado_por"] == ACTOR
    doc = _doc(fabrica, "viejo")
    assert (doc.is_active, doc.fecha) == (True, "2026-11-25")


def test_f084_r17_recuperar_sin_cuerpo_ni_fecha() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "viejo", activo=False)
    r = cliente.post("/api/partes/viejo/recuperar", headers=CABECERA)
    assert r.status_code == 200 and r.json()["fecha"] == "2026-11-23"
    r2 = _recuperar(_montar()[0], "otro", fecha="")
    assert r2.status_code == 404


def test_f084_r18_un_fallo_de_la_cola_no_deshace_la_recuperacion() -> None:
    cliente, _cola, fabrica = _montar(cola=ColaFake(error=OSError("caida")))
    _sustituido(fabrica)
    r = _recuperar(cliente, fecha="2026-11-25")
    assert r.status_code == 200 and r.json()["recalculo"] == "fallo"
    assert _doc(fabrica, "viejo").is_active is True


def test_f084_r19_choque_da_409_con_los_partes() -> None:
    cliente, cola, fabrica = _montar()
    _sustituido(fabrica)
    r = _recuperar(cliente)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert "Corrige la fecha o descarta antes el otro parte" in cuerpo["error"]
    assert cuerpo["partes"] == [
        {"id": "nuevo", "fecha": "2026-11-23", "obra": "0100"}]
    assert cola.enviados == []
    assert _doc(fabrica, "viejo").is_active is False


def test_f084_r20_mismo_sha_da_409() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "activo", sha="sha-comun", obra_ide=50,
             obra_codigo="0500")
    _sembrar(fabrica, "viejo", activo=False, sha="sha-comun")
    r = _recuperar(cliente)
    assert r.status_code == 409 and r.json()["ok"] is False
    assert "mismo PDF" in r.json()["error"]


def test_f084_r21_congelado_con_fecha_da_409() -> None:
    cliente, cola, fabrica = _montar()
    _sembrar(fabrica, "viejo", activo=False, aprobado=True)
    r = _recuperar(cliente, fecha="2026-11-25")
    assert r.status_code == 409 and r.json()["ok"] is False
    assert cola.enviados == []
    ok = _recuperar(cliente)
    assert ok.status_code == 200


def test_f084_r22_fecha_invalida_da_400_sin_escribir() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "viejo", activo=False)
    r = _recuperar(cliente, fecha="31/02/2026")
    assert r.status_code == 400
    assert _doc(fabrica, "viejo").is_active is False


def test_f084_r22_inexistente_404_y_activo_409() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "activo")
    assert _recuperar(cliente, "no-existe").status_code == 404
    r = _recuperar(cliente, "activo")
    assert r.status_code == 409
    assert "ya está activo" in r.json()["error"]


# ======================== R23 · deshacer =================================== #

def test_f084_r23_deshacer_recuperar_pide_su_recalculo() -> None:
    cliente, cola, fabrica = _montar()
    _sembrar(fabrica, "viejo", activo=False)
    assert _recuperar(cliente, fecha="2026-11-25").status_code == 200
    r = cliente.post("/api/undo", headers=CABECERA)
    assert r.status_code == 200
    assert r.json()["action"] == "parte_recuperar"
    assert r.json()["recalculo"] == "pedido"
    assert _motivos_enviados(cola) == [rp.MOTIVO_RECUPERAR_PARTE,
                                       rp.MOTIVO_DESHACER_RECUPERAR]
    doc = _doc(fabrica, "viejo")
    assert (doc.is_active, doc.fecha) == (False, "2026-11-23")


def test_f084_r23_el_widget_llama_recuperar_parte() -> None:
    js = (RAIZ / "static" / "app.js").read_text(encoding="utf-8")
    assert re.search(r'parte_recuperar:\s*"Recuperar parte"', js)


def test_f084_motivos_del_recalculo() -> None:
    assert rp.MOTIVO_RECUPERAR_PARTE == "recuperar_parte"
    assert rp.MOTIVO_DESHACER_RECUPERAR == "deshacer_recuperar_parte"


# ================== R25 · navegación y contador =========================== #

def test_f084_r25_problemas_entre_conciliar_y_partes() -> None:
    cliente, _cola, fabrica = _montar()
    html = cliente.get("/problemas").text
    nav = html[html.index('<nav class="topnav">'):html.index("</nav>")]
    assert (nav.index('href="/conciliacion"') < nav.index('href="/problemas"')
            < nav.index('href="/partes"'))
    assert 'id="problemas-badge"' in nav
    assert re.search(r'id="problemas-badge"[^>]*hidden', nav)


def test_f084_r25_el_resumen() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "sin-obra", obra_ide=None)
    _sustituido(fabrica)
    r = cliente.get("/api/problemas/resumen")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "total": 2, "por_motivo": {
        "sin_obra": 1, "sustituido_mismo_envio": 1}}


class _RepoRoto(ParteReviewRepository):
    def resumen_problemas(self) -> dict:
        raise RuntimeError("base caida")


def test_f084_r25_si_el_resumen_falla_no_se_pinta_nada(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    cliente, _cola, _f = _montar(repo=_RepoRoto(fabrica))
    with caplog.at_level(logging.WARNING):
        r = cliente.get("/api/problemas/resumen")
    assert r.status_code == 200
    assert r.json() == {"ok": False, "total": 0}
    assert any("problemas" in rec.getMessage() for rec in caplog.records
               if rec.levelno == logging.WARNING)


def test_f084_r25_el_js_pinta_el_contador_y_se_traga_el_fallo() -> None:
    js = (RAIZ / "static" / "app.js").read_text(encoding="utf-8")
    assert "function wireProblemasBadge" in js
    cuerpo = js[js.index("function wireProblemasBadge"):]
    cuerpo = cuerpo[:cuerpo.index("\n  }\n")]
    assert "/api/problemas/resumen" in cuerpo
    assert "problemas-badge" in cuerpo
    assert ".catch(" in cuerpo
    assert "total > 0" in cuerpo


# ======================= R26 · descartar =================================== #

def test_f084_r26_descartar_vuelve_a_la_pestana_y_lo_saca() -> None:
    cliente, _cola, fabrica = _montar()
    _sustituido(fabrica)
    _sembrar(fabrica, "huerfano", activo=False, sustituido_por_id="x",
             obra_ide=50, obra_codigo="0500")
    assert cliente.get("/api/problemas/resumen").json()["total"] == 2
    r = cliente.post("/documents/viejo/delete", data={"back": "/problemas"},
                     headers=CABECERA, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/problemas?message=")
    doc = _doc(fabrica, "viejo")
    assert doc.deleted_at_utc is not None and doc.deleted_by == ACTOR
    assert 'data-document-id="viejo"' not in cliente.get("/problemas").text
    assert cliente.get("/api/problemas/resumen").json()["total"] == 1


def test_f084_r26_descartar_un_congelado_avisa_y_no_borra() -> None:
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "viejo", activo=False, aprobado=True)
    r = cliente.post("/documents/viejo/delete", data={"back": "/problemas"},
                     headers=CABECERA, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/problemas?message=")
    assert _doc(fabrica, "viejo").deleted_at_utc is None


# ======================= plantillas ====================================== #

def test_f084_las_plantillas_parsean() -> None:
    env = Environment(loader=FileSystemLoader(str(RAIZ / "templates")))
    for nombre in ("problemas.html", "base.html"):
        env.parse(env.loader.get_source(env, nombre)[0])


# ================= T10 · supervivientes de la mutación =================== #

def test_f084_r10_la_cabecera_cuenta_solo_los_que_cuentan() -> None:
    """El título suma los partes que cuentan, uno por parte (mutante 13)."""
    cliente, _cola, fabrica = _montar()
    _sembrar(fabrica, "sin-obra", obra_ide=None, obra_codigo=None)
    _sembrar(fabrica, "nuevo", email_id="correo-2",
             creado="2026-11-26T10:05:00+00:00")
    _sembrar(fabrica, "viejo", activo=False, sustituido_por_id="nuevo")
    html = cliente.get("/problemas").text
    assert "Partes con problemas (1)</h1>" in html


def test_f084_r25_las_rutas_nuevas_no_salen_en_el_esquema() -> None:
    """Como el resto del portal, fuera de `/openapi.json` (mutantes 14 y
    15)."""
    cliente, _cola, _f = _montar()
    rutas = cliente.app.openapi()["paths"]
    for ruta in ("/problemas", "/api/problemas/resumen",
                 "/api/partes/{document_id}/recuperar"):
        assert ruta not in rutas


def test_f084_r22_el_404_lleva_ok_false() -> None:
    """El JS decide por `ok`: un 404 no puede decir `ok: true` (mutante
    18)."""
    cliente, _cola, _f = _montar()
    r = _recuperar(cliente, "no-existe")
    assert r.status_code == 404
    assert r.json() == {"ok": False, "error": "Parte no encontrado"}
