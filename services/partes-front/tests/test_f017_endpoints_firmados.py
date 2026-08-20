# tests/test_f017_endpoints_firmados.py
"""F-017 · R12-R15: los puntos del portal que hasta hoy firmaban en blanco.

Aprobar (R12), borrar un parte (R13), borrar una linea / una obra / un
trabajador (R14) y dar de alta un parte manual (R15). Antes de esta feature
los cinco sellaban `settings.default_reviewer`, que en el despliegue real
**no esta configurado**: la auditoria del portal llevaba `NULL` desde el
primer dia.

Cada requisito se comprueba por los dos extremos que estan en manos de sv4:

* **el valor que llega al repositorio** — un espia sobre los metodos, que
  es lo que la ruta controla y lo unico que R14/R15 pueden garantizar;
* **el valor que acaba en la fila**, donde la columna existe y se escribe.

La distincion no es un capricho: al implementar se descubrio que dos de
esos destinos no son los que `requirements.md` daba por hechos. Ver el
bloque «SOBRE R14 Y R15» al final del fichero.

TestClient + SQLite en memoria: ni red, ni PostgreSQL, ni colas, ni sv5.
Dominio `ejemplo.invalid` (RFC 2606).
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.web.identidad import (
    ACTOR_SIN_IDENTIDAD,
    CABECERA_NOMBRE,
    CABECERA_TOKEN,
    VARIABLES_DESPLIEGUE,
)
from tests.dobles import FabricaSesionSqlite, sembrar_parte

USUARIO = "ana.ejemplo@ejemplo.invalid"
DOC = "doc-firmado"


def _como(usuario: str) -> dict[str, str]:
    return {CABECERA_NOMBRE: usuario}


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    for variable in VARIABLES_DESPLIEGUE:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("DEFAULT_REVIEWER", raising=False)
    return monkeypatch


class RepositorioEspia(ParteReviewRepository):
    """El repositorio de verdad, anotando con que actor le llaman.

    Subclase y no `Mock`: las escrituras ocurren de verdad contra SQLite,
    asi que el test comprueba a la vez el paso del actor y que la
    operacion sigue funcionando.
    """

    def __init__(self, fabrica) -> None:
        super().__init__(fabrica)
        self.firmas: list[tuple[str, str | None]] = []

    def approve_document(self, *, document_id: str, approved_by=None):
        self.firmas.append(("approve_document", approved_by))
        return super().approve_document(document_id=document_id,
                                        approved_by=approved_by)

    def delete_document(self, *, document_id: str, deleted_by=None):
        self.firmas.append(("delete_document", deleted_by))
        return super().delete_document(document_id=document_id,
                                       deleted_by=deleted_by)

    def soft_delete_registro(self, *, registro_id: int, by=None):
        self.firmas.append(("soft_delete_registro", by))
        return super().soft_delete_registro(registro_id=registro_id, by=by)

    def soft_delete_obra(self, *, obra_key: str, by=None):
        self.firmas.append(("soft_delete_obra", by))
        return super().soft_delete_obra(obra_key=obra_key, by=by)

    def soft_delete_worker(self, *, worker_key: str, by=None):
        self.firmas.append(("soft_delete_worker", by))
        return super().soft_delete_worker(worker_key=worker_key, by=by)

    def crear_parte_manual(self, **kw):
        self.firmas.append(("crear_parte_manual", kw.get("by")))
        return super().crear_parte_manual(**kw)

    def firma_de(self, metodo: str) -> str | None:
        for nombre, actor in self.firmas:
            if nombre == metodo:
                return actor
        raise AssertionError(f"no se llamo a {metodo}: {self.firmas}")


def _montaje(*, aprobado: bool = False):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"horas": 8.0}, {"horas": 4.0}],
                        document_id=DOC, aprobado=aprobado)
    repositorio = RepositorioEspia(fabrica)
    app = build_app(Settings(_env_file=None), repository=repositorio)
    return TestClient(app), repositorio, fabrica, ids


def _doc(fabrica) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, DOC)


def _registro(fabrica, registro_id: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, registro_id)


# ====================================================================== #
# R12 · aprobar un parte
# ====================================================================== #

def test_f017_r12_approved_by() -> None:
    """La columna que `parte_detail.html` pinta como «Aprobado por …»."""
    cliente, _repo, fabrica, _ids = _montaje()
    respuesta = cliente.post(f"/documents/{DOC}/approve",
                             headers=_como(USUARIO), follow_redirects=False)

    assert respuesta.status_code in (302, 303)
    documento = _doc(fabrica)
    assert documento.approved is True
    assert documento.approved_by == USUARIO


def test_f017_r12_approved_by_desde_el_token() -> None:
    """Sin `-NAME`, el suplente de R2 firma igual de bien."""
    import base64
    import json

    token = base64.b64encode(json.dumps({
        "claims": [{"typ": "preferred_username", "val": USUARIO}],
    }).encode("utf-8")).decode("ascii")

    cliente, _repo, fabrica, _ids = _montaje()
    cliente.post(f"/documents/{DOC}/approve",
                 headers={CABECERA_TOKEN: token}, follow_redirects=False)
    assert _doc(fabrica).approved_by == USUARIO


def test_f017_r12_el_parametro_back_sigue_funcionando() -> None:
    """Añadir `request: Request` a la firma no toca el contrato HTTP.

    `approve_document` tiene un `Form(default=...)`: si FastAPI hubiera
    empezado a tratar `request` como un campo mas, este `back` se
    perderia. Es la comprobacion de que el riesgo R1 de design.md §11 no
    se ha materializado.
    """
    cliente, _repo, _f, _ids = _montaje()
    respuesta = cliente.post(f"/documents/{DOC}/approve",
                             data={"back": "/trabajadores"},
                             headers=_como(USUARIO), follow_redirects=False)
    assert respuesta.status_code in (302, 303)
    assert "/trabajadores" in respuesta.headers["location"]


# ====================================================================== #
# R13 · borrar un parte
# ====================================================================== #

def test_f017_r13_deleted_by() -> None:
    cliente, _repo, fabrica, _ids = _montaje()
    respuesta = cliente.post(f"/documents/{DOC}/delete",
                             headers=_como(USUARIO), follow_redirects=False)

    assert respuesta.status_code in (302, 303)
    documento = _doc(fabrica)
    assert documento.is_active is False
    assert documento.deleted_by == USUARIO


def test_f017_r13_el_parametro_back_sigue_funcionando() -> None:
    cliente, _repo, _f, _ids = _montaje()
    respuesta = cliente.post(f"/documents/{DOC}/delete",
                             data={"back": "/partes"},
                             headers=_como(USUARIO), follow_redirects=False)
    assert respuesta.status_code in (302, 303)


# ====================================================================== #
# R14 · los tres borrados
# ====================================================================== #

def test_f017_r14_borrar_linea_sella_deleted_by() -> None:
    """El destino REAL del actor en un borrado de linea."""
    cliente, _repo, fabrica, ids = _montaje()
    respuesta = cliente.post(f"/api/registro/{ids[0]}/delete",
                             headers=_como(USUARIO))

    assert respuesta.json() == {"ok": True}
    registro = _registro(fabrica, ids[0])
    assert registro.deleted_at_utc is not None
    assert registro.deleted_by == USUARIO


@pytest.mark.parametrize("ruta, metodo", [
    (f"/api/registro/{{id}}/delete", "soft_delete_registro"),
    ("/api/obra/0100/delete", "soft_delete_obra"),
    ("/api/trabajador/cualquiera/delete", "soft_delete_worker"),
])
def test_f017_r14_undo_log_actor_borrados(ruta: str, metodo: str) -> None:
    """Los tres borrados entregan el actor de SU peticion al repositorio.

    Se comprueba en el punto que la ruta controla —el argumento con el que
    llama al repositorio— porque los tres borran cosas distintas y dos de
    ellos pueden no encontrar nada que borrar sin que eso invalide la
    firma. Ver «SOBRE R14 Y R15» al final del fichero.
    """
    cliente, repositorio, _f, ids = _montaje()
    cliente.post(ruta.format(id=ids[0]), headers=_como(USUARIO))
    assert repositorio.firma_de(metodo) == USUARIO


@pytest.mark.parametrize("ruta", [
    "/api/registro/{id}/delete",
    "/api/obra/0100/delete",
    "/api/trabajador/cualquiera/delete",
])
def test_f017_r14_sin_cabecera_tambien_se_firma(ruta: str) -> None:
    """R7: ninguna de las tres puede volver a entregar `None`."""
    cliente, repositorio, _f, ids = _montaje()
    cliente.post(ruta.format(id=ids[0]))
    assert repositorio.firmas
    for _nombre, actor in repositorio.firmas:
        assert actor == "local:sin-identidad"


def test_f017_r14_cada_peticion_lleva_su_actor() -> None:
    """Dos borrados seguidos de dos personas distintas, dos firmas."""
    otra = "otra.persona@ejemplo.invalid"
    cliente, repositorio, fabrica, ids = _montaje()
    cliente.post(f"/api/registro/{ids[0]}/delete", headers=_como(USUARIO))
    cliente.post(f"/api/registro/{ids[1]}/delete", headers=_como(otra))

    assert _registro(fabrica, ids[0]).deleted_by == USUARIO
    assert _registro(fabrica, ids[1]).deleted_by == otra


# ====================================================================== #
# R15 · alta de un parte manual
# ====================================================================== #

def _alta_manual() -> dict:
    return {
        "dias": ["2026-03-02"],
        "empleado_nombre": "Trabajador De Prueba",
        "obra_codigo": "0100",
        "obra_ide": 10,
        "horas_ordinaria": 8,
        "horas_extra": 0,
    }


def test_f017_r15_undo_log_actor_parte_manual() -> None:
    """El alta manual entrega el actor de su peticion (punto 11 de §5.2)."""
    cliente, repositorio, _f, _ids = _montaje()
    cliente.post("/api/partes/nuevo", json=_alta_manual(),
                 headers=_como(USUARIO))
    assert repositorio.firma_de("crear_parte_manual") == USUARIO


def test_f017_r15_sin_cabecera_el_alta_manual_tambien_se_firma() -> None:
    cliente, repositorio, _f, _ids = _montaje()
    cliente.post("/api/partes/nuevo", json=_alta_manual())
    assert repositorio.firma_de("crear_parte_manual") == "local:sin-identidad"


def test_f017_r15_desplegado_sin_cabecera_el_alta_lleva_sin_identidad(
        monkeypatch) -> None:
    monkeypatch.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")
    cliente, repositorio, _f, _ids = _montaje()
    cliente.post("/api/partes/nuevo", json=_alta_manual())
    assert repositorio.firma_de("crear_parte_manual") == ACTOR_SIN_IDENTIDAD


# ====================================================================== #
# R7 sobre los cinco puntos a la vez
# ====================================================================== #

def test_f017_r7_ninguno_de_los_cinco_puntos_entrega_none() -> None:
    """El barrido que hace exacto el criterio del corte (R22).

    Si alguno de estos puntos volviera a entregar `None`, la regla
    «`autor IS NULL` ⇔ fila anterior a F-017» dejaria de ser cierta y con
    ella el criterio en el que F-018 se va a apoyar.
    """
    cliente, repositorio, _f, ids = _montaje()
    for peticion in (
        lambda: cliente.post(f"/documents/{DOC}/approve",
                             follow_redirects=False),
        lambda: cliente.post(f"/api/registro/{ids[0]}/delete"),
        lambda: cliente.post("/api/obra/0100/delete"),
        lambda: cliente.post("/api/trabajador/cualquiera/delete"),
        lambda: cliente.post("/api/partes/nuevo", json=_alta_manual()),
        lambda: cliente.post(f"/documents/{DOC}/delete",
                             follow_redirects=False),
    ):
        peticion()

    assert len(repositorio.firmas) == 6
    for nombre, actor in repositorio.firmas:
        assert actor, f"{nombre} entrego un actor vacio"
        assert actor == "local:sin-identidad"


# ====================================================================== #
# SOBRE R14 Y R15 — lo que se encontro al implementar
# ====================================================================== #
#
# `requirements.md` R14 y R15 dicen que el actor debe escribirse en
# `undo_log.actor`. Comprobado contra el arbol el 2026-08-20, eso NO
# describe el codigo:
#
#   * `undo_log.actor` existe como columna (F-010) pero **no la escribe
#     nadie**: `_record_undo` ni siquiera acepta un actor.
#   * Las cuatro operaciones de R14/R15 —los tres borrados y el alta
#     manual— **no generan ninguna fila de `undo_log`**. Solo la generan
#     las ediciones (`update_registro`, `set_registro_hora`,
#     `reassign_empleado_*`, `update_parte_*`).
#   * `crear_parte_manual` **acepta `by=` y lo ignora**: el parametro no
#     se usa en ninguna linea de su cuerpo.
#
# Lo que esta feature hace es lo que manda `design.md` §5.2 (puntos 8-11):
# entregar `_actor(request)` por el parametro `by=` que esas rutas ya
# usaban. Para los borrados eso llega de verdad a `deleted_by`; para el
# alta manual se queda en la puerta del repositorio.
#
# NO se ha hecho por cuenta propia ninguna de las dos cosas que faltarian
# —que los borrados escriban en `undo_log` (funcionalidad nueva: los haria
# deshacibles) o que `crear_parte_manual` use su `by`— porque cambian el
# alcance y tocan `parte_repository.py`, que `design.md` §5.3 marca como
# fichero que NO se toca. Queda elevado al humano en el informe.
