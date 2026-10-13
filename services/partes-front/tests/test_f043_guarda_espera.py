# tests/test_f043_guarda_espera.py
"""F-043 · R38-R39: el servidor rechaza las ediciones del parte en espera.

Mientras sv3 recalcula un parte (estado `pendiente`), una edicion
confirmada entre su lectura y su escritura se pisa (design §9 R-a). El
portal deshabilita las filas, pero eso no basta (otra pestana, otro
usuario, una peticion a pelo): la guarda vive en el repositorio, justo
detras de cada guarda de congelacion de F-004, y responde con el mismo
409. Salvo la fecha y deshacer, que piden su propia pasada (DA11).

Sin red ni PostgreSQL: SQLite en memoria con el ORM real. Sintetico.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import unquote_plus

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy import update

from application.services.seguimiento_recalculo import (
    MOTIVO_RECALCULANDO,
    RecalculandoError,
)
from infrastructure.database import parte_repository as modulo_repo
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, datos_registros, sembrar_parte
from tests.test_f004_endpoints_congelados import SigridLookupClientFake

DOC = "doc-f004"
OTRO = "doc-otro"
AHORA = datetime(2026, 10, 13, 9, 0, 0, tzinfo=timezone.utc)
PID = "00000000-0000-4000-8000-00000000000a"
PID2 = "00000000-0000-4000-8000-00000000000b"
CUERPO_409 = {"ok": False, "congelado": True, "error": MOTIVO_RECALCULANDO}


def _hace(segundos: float) -> str:
    return (AHORA - timedelta(seconds=segundos)).isoformat()


#: Estado -> marca que lo produce con el reloj fijo en AHORA.
MARCAS = {
    "pendiente": dict(pedido=PID2, pedido_at=_hace(30), terminado=PID),
    "vencido": dict(pedido=PID2, pedido_at=_hace(601), terminado=PID),
    "terminado": dict(pedido=PID, pedido_at=_hace(30), terminado=PID),
    "sin_seguimiento": dict(pedido=None, pedido_at=None, terminado=None),
}


def _marcar(fabrica, document_id: str, estado: str) -> None:
    m = MARCAS[estado]
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=m["pedido"],
                          recalculo_pedido_at_utc=m["pedido_at"],
                          recalculo_terminado_id=m["terminado"]))
        s.commit()


@pytest.fixture
def montaje(monkeypatch):
    """`_montar(estado, aprobado=False) -> (cliente, fabrica, ids)`."""
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
        "SIGRID_API_BASE_URL": "http://sigrid.interno",
        "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
        "SIGRID_API_DATABASE": "ruesma_rep",
    }.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    monkeypatch.setattr(app_mod, "SigridLookupClient", SigridLookupClientFake)
    monkeypatch.setattr(modulo_repo, "_ahora_utc", lambda: AHORA)

    def _montar(estado: str, *, aprobado: bool = False,
                lineas: list[dict] | None = None):
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, lineas or [{"horas": 8.0},
                                                {"horas": 9.0}],
                            aprobado=aprobado)
        _marcar(fabrica, DOC, estado)
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica))
        return TestClient(app), fabrica, ids
    return _montar


def _doc(fabrica, document_id: str = DOC) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, document_id)


# ------- las siete ediciones que pasan por una guarda de F-004 ---------- #

def _crear_extra(c, ids):
    return c.post(f"/api/registros/{ids[0]}/extra", json={"horas": 2.0})


def _horas(c, ids):
    return c.patch(f"/api/registros/{ids[0]}", json={"horas": 3.0})


def _hora(c, ids):
    return c.patch(f"/api/registros/{ids[0]}/hora", json={"hora_ide": 2})


def _partida(c, ids):
    return c.patch(f"/api/registros/{ids[0]}/partida",
                   json={"partida_ide": 5, "partida_cod": "3.1",
                         "partida_res": "Ppp", "partida_capitulo": "CD"})


def _obra(c, _ids):
    return c.patch(f"/api/partes/{DOC}/obra",
                   json={"codigo": "0999", "nombre": "Otra"})


def _borrar_linea(c, ids):
    return c.post(f"/api/registro/{ids[0]}/delete")


JSON = {"crear_extra_desde": _crear_extra, "update_registro": _horas,
        "set_registro_hora": _hora, "set_registro_partida": _partida,
        "update_parte_obra": _obra, "soft_delete_registro": _borrar_linea}


@pytest.mark.parametrize("nombre", sorted(JSON))
def test_f043_r38_en_espera_cada_edicion_da_409_y_no_escribe(
        montaje, nombre) -> None:
    cliente, fabrica, ids = montaje("pendiente")
    antes = datos_registros(fabrica, ids)
    doc_antes = (_doc(fabrica).obra_codigo, _doc(fabrica).fecha)
    r = JSON[nombre](cliente, ids)
    assert r.status_code == 409, r.text
    assert r.json() == CUERPO_409
    assert datos_registros(fabrica, ids) == antes
    assert (_doc(fabrica).obra_codigo, _doc(fabrica).fecha) == doc_antes
    with fabrica.create_session() as s:
        from infrastructure.database.orm_models import ParteRegistroOrm
        assert s.query(ParteRegistroOrm).count() == len(ids)


def test_f043_r38_en_espera_mandar_el_parte_a_la_papelera_avisa(
        montaje) -> None:
    """Flujo de formulario de F-004 R7: redirige con el motivo visible."""
    cliente, fabrica, _ids = montaje("pendiente")
    r = cliente.post(f"/documents/{DOC}/delete", data={"back": "/partes"},
                     follow_redirects=False)
    assert r.status_code == 303
    assert MOTIVO_RECALCULANDO in unquote_plus(r.headers["location"])
    assert _doc(fabrica).is_active is True


@pytest.mark.parametrize("estado", ["vencido", "terminado",
                                    "sin_seguimiento"])
@pytest.mark.parametrize("nombre", sorted(JSON))
def test_f043_r39_fuera_de_espera_se_edita_como_siempre(
        montaje, estado, nombre) -> None:
    cliente, _fabrica, ids = montaje(estado)
    r = JSON[nombre](cliente, ids)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("estado", ["vencido", "terminado",
                                    "sin_seguimiento"])
def test_f043_r39_fuera_de_espera_se_manda_a_la_papelera(montaje,
                                                         estado) -> None:
    cliente, fabrica, _ids = montaje(estado)
    r = cliente.post(f"/documents/{DOC}/delete", data={"back": "/partes"},
                     follow_redirects=False)
    assert r.status_code == 303
    assert _doc(fabrica).is_active is False


def test_f043_r38_la_fecha_se_puede_cambiar_en_espera(montaje) -> None:
    cliente, fabrica, ids = montaje("pendiente")
    r = cliente.patch(f"/api/partes/{DOC}/fecha",
                      json={"fecha": "2026-10-01"})
    assert r.status_code == 200
    assert _doc(fabrica).fecha == "2026-10-01"
    assert {d["fecha"] for d in datos_registros(fabrica, ids).values()} == {
        "2026-10-01"}


def test_f043_r38_deshacer_se_puede_en_espera(montaje) -> None:
    cliente, fabrica, ids = montaje("sin_seguimiento")
    assert cliente.patch(f"/api/registros/{ids[0]}",
                         json={"horas": 3.0}).status_code == 200
    _marcar(fabrica, DOC, "pendiente")
    r = cliente.post("/api/undo")
    assert r.status_code == 200 and r.json()["ok"] is True
    assert datos_registros(fabrica, ids)[ids[0]]["horas"] == 8.0


def test_f043_r38_otro_parte_se_edita_mientras_uno_espera(montaje) -> None:
    cliente, fabrica, ids = montaje("pendiente")
    otros = sembrar_parte(fabrica, [{"horas": 8.0}], document_id=OTRO,
                          empleado_ide=78)
    assert cliente.patch(f"/api/registros/{otros[0]}",
                         json={"horas": 5.0}).status_code == 200
    assert cliente.patch(f"/api/registros/{ids[0]}",
                         json={"horas": 5.0}).status_code == 409


def test_f043_r39_congelado_y_en_espera_manda_la_congelacion(montaje) -> None:
    """La regla de F-004 va primero y no cambia: su motivo es el que sale."""
    cliente, _fabrica, ids = montaje(
        "pendiente", lineas=[{"horas": 8.0, "estado": "registrado"}])
    r = _horas(cliente, ids)
    assert r.status_code == 409
    assert r.json()["error"] != MOTIVO_RECALCULANDO
    r = _obra(cliente, ids)
    assert r.status_code == 409
    assert r.json()["error"] != MOTIVO_RECALCULANDO


def test_f043_r38_el_parte_vuelve_a_editarse_al_vencer(montaje) -> None:
    cliente, _fabrica, ids = montaje("pendiente")
    assert _horas(cliente, ids).status_code == 409
    # Mismo pedido, 571 s despues: 601 s de antiguedad => vencido.
    modulo_repo._ahora_utc = lambda: AHORA + timedelta(seconds=571)
    assert _horas(cliente, ids).status_code == 200


# --------------- directamente sobre el repositorio --------------------- #

def _repo_en_espera(monkeypatch, estado: str = "pendiente"):
    monkeypatch.setattr(modulo_repo, "_ahora_utc", lambda: AHORA)
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 9.0}])
    _marcar(fabrica, DOC, estado)
    return ParteReviewRepository(fabrica), fabrica, ids


LLAMADAS = {
    "crear_extra_desde": lambda r, ids: r.crear_extra_desde(
        registro_id=ids[0], horas=2.0),
    "update_registro": lambda r, ids: r.update_registro(
        registro_id=ids[0], horas=3.0),
    "set_registro_hora": lambda r, ids: r.set_registro_hora(
        registro_id=ids[0], hora_ide=2, hora_codigo="HE01",
        hora_descripcion="Extra", hora_ext=1, hora_precio_coste=None,
        hora_precio_nomina=None),
    "set_registro_partida": lambda r, ids: r.set_registro_partida(
        registro_id=ids[0], partida_ide=5, partida_cod="3.1",
        partida_res="Ppp", partida_capitulo="CD"),
    "update_parte_obra": lambda r, _ids: r.update_parte_obra(
        document_id=DOC, obra_ide=None, obra_codigo="0999",
        obra_nombre="Otra"),
    "delete_document": lambda r, _ids: r.delete_document(
        document_id=DOC, deleted_by="ana"),
    "soft_delete_registro": lambda r, ids: r.soft_delete_registro(
        registro_id=ids[0], by="ana"),
}


@pytest.mark.parametrize("nombre", sorted(LLAMADAS))
def test_f043_r38_las_siete_guardas_del_repositorio(monkeypatch,
                                                    nombre) -> None:
    repo, fabrica, ids = _repo_en_espera(monkeypatch)
    antes = datos_registros(fabrica, ids)
    with pytest.raises(RecalculandoError) as exc:
        LLAMADAS[nombre](repo, ids)
    assert exc.value.motivo == MOTIVO_RECALCULANDO
    assert datos_registros(fabrica, ids) == antes
    assert _doc(fabrica).is_active is True


@pytest.mark.parametrize("nombre", sorted(LLAMADAS))
def test_f043_r39_las_siete_funcionan_si_vencio(monkeypatch, nombre) -> None:
    repo, _fabrica, ids = _repo_en_espera(monkeypatch, "vencido")
    assert LLAMADAS[nombre](repo, ids) not in (False, None)


def test_f043_r38_update_parte_fecha_no_tiene_la_guarda(monkeypatch) -> None:
    repo, fabrica, _ids = _repo_en_espera(monkeypatch)
    assert repo.update_parte_fecha(document_id=DOC, fecha_iso="2026-10-01",
                                   fecha_int=20261001) is True
    assert repo.undo_last()["ok"] is True
    assert _doc(fabrica).fecha == "2026-03-02"
