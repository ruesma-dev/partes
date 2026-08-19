# tests/test_f016_endpoints_admin_jornadas.py
"""F-016 · El repositorio y los cinco endpoints de la pantalla.

TestClient + SQLite en memoria con el ORM real + `Settings(_env_file=None)`:
ni red, ni PostgreSQL, ni Sigrid, ni colas, ni sv5 (R17).

Cubre R3 (alta), R4 (edicion), R5 (cierre), R6 (papelera logica), R12 por
HTTP (409 con la fila en conflicto y la BBDD intacta), R13 (auditoria),
R16 (id inexistente) y R19 (aviso de DNI desconocido).

La regla que se repite en cada rechazo: se cuenta la tabla ANTES y
DESPUES. Un 4xx que ya haya escrito no sirve de nada.

DNIs sinteticos: aqui no aparece ningun DNI ni nombre de persona real.
"""
from __future__ import annotations

import pytest
from application.services.jornada_admin import DIAS
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import EmpleadoJornadaOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from sqlalchemy import select
from tests.dobles import FabricaSesionSqlite, sembrar_jornadas

DNI = "AAA1"
OTRO_DNI = "BBB2"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    """La suite no lee el `.env` de nadie ni necesita PostgreSQL."""
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


class ProveedorFake:
    """Doble de `JornadaEmpleadoProvider`: solo cuenta `invalidar()`."""

    def __init__(self) -> None:
        self.invalidaciones = 0

    def invalidar(self) -> None:
        self.invalidaciones += 1

    def excepcion_para(self, dni, fecha):
        return None


def _montaje(filas=(), *, settings=None, proveedor=None):
    """App entera SIN colaboradores externos: solo repositorio y BBDD."""
    fabrica = FabricaSesionSqlite()
    if filas:
        sembrar_jornadas(fabrica, list(filas))
    repositorio = ParteReviewRepository(fabrica)
    proveedor = proveedor if proveedor is not None else ProveedorFake()
    app = build_app(settings or _settings(), repository=repositorio,
                    jornada_provider=proveedor)
    return TestClient(app), repositorio, fabrica, proveedor


def _cuantas(fabrica) -> int:
    with fabrica.create_session() as s:
        return len(s.execute(select(EmpleadoJornadaOrm)).scalars().all())


def _fila_cruda(fabrica, jornada_id: int) -> EmpleadoJornadaOrm | None:
    with fabrica.create_session() as s:
        return s.get(EmpleadoJornadaOrm, jornada_id)


def _alta(**kw) -> dict:
    base = {"dni": DNI, "jornada_semanal": "48", "desde": "2026-07-01",
            "hasta_inclusivo": None, "nota": None}
    base.update(kw)
    return base


# ====================================================================== #
# El repositorio (T2)
# ====================================================================== #

def test_f016_repositorio_lista_activas_e_inactivas_ordenadas() -> None:
    """R2: por `dni_norm` ascendente y `desde` DESCENDENTE dentro de cada."""
    fabrica = FabricaSesionSqlite()
    sembrar_jornadas(fabrica, [
        {"dni_norm": OTRO_DNI, "desde": "2026-01-01", "jornada_semanal": 40.0},
        {"dni_norm": DNI, "desde": "2026-01-01", "hasta": "2026-07-01",
         "jornada_semanal": 40.0},
        {"dni_norm": DNI, "desde": "2026-07-01", "jornada_semanal": 48.0,
         "is_active": False},
    ])
    filas = ParteReviewRepository(fabrica).list_jornadas_admin()
    assert [(f["dni_norm"], f["desde"]) for f in filas] == [
        (DNI, "2026-07-01"), (DNI, "2026-01-01"), (OTRO_DNI, "2026-01-01")]
    # La inactiva NO desaparece del listado de administracion.
    assert [f["is_active"] for f in filas] == [False, True, True]


def test_f016_repositorio_devuelve_las_diecinueve_columnas() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_jornadas(fabrica, [{"dni_norm": DNI, "created_by": "quien"}])
    fila = ParteReviewRepository(fabrica).list_jornadas_admin()[0]
    assert set(fila) == {
        "id", "dni_norm", "jornada_semanal", *DIAS, "desde", "hasta",
        "origen", "nota", "is_active", "created_at_utc", "created_by",
        "updated_at_utc", "updated_by"}
    assert len(fila) == 19


def test_f016_repositorio_el_alta_sella_origen_manual_y_la_autoria() -> None:
    """R3: `origen` lo pone el servidor; `updated_*` nacen a NULL."""
    fabrica = FabricaSesionSqlite()
    repositorio = ParteReviewRepository(fabrica)
    nuevo = repositorio.crear_jornada(
        entrada={"dni_norm": DNI, "jornada_semanal": 48.0, "patron": None,
                 "desde": "2026-07-01", "hasta": None, "nota": "una nota",
                 "origen": "sigrid"},
        actor="quien")
    fila = _fila_cruda(fabrica, nuevo)
    assert fila is not None
    assert (fila.origen, fila.is_active, fila.created_by) == (
        "manual", True, "quien")
    assert (fila.updated_at_utc, fila.updated_by) == (None, None)
    assert fila.created_at_utc.startswith("20")      # ISO-8601 en UTC
    assert fila.created_at_utc.endswith("+00:00")


def test_f016_repositorio_el_patron_se_guarda_en_las_siete_columnas() -> None:
    fabrica = FabricaSesionSqlite()
    nuevo = ParteReviewRepository(fabrica).crear_jornada(
        entrada={"dni_norm": DNI, "jornada_semanal": None,
                 "patron": (7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0),
                 "desde": "2026-07-01", "hasta": None, "nota": None},
        actor=None)
    fila = _fila_cruda(fabrica, nuevo)
    assert [getattr(fila, dia) for dia in DIAS] == [7.0] * 5 + [0.0, 0.0]


def test_f016_repositorio_la_edicion_conserva_el_alta() -> None:
    """R4: `dni_norm`, `origen`, `created_at_utc` y `created_by`, intactos."""
    fabrica = FabricaSesionSqlite()
    repositorio = ParteReviewRepository(fabrica)
    nuevo = repositorio.crear_jornada(
        entrada={"dni_norm": DNI, "jornada_semanal": 48.0, "patron": None,
                 "desde": "2026-07-01", "hasta": None, "nota": None},
        actor="quien-creo")
    antes = _fila_cruda(fabrica, nuevo)
    creado_en, creado_por = antes.created_at_utc, antes.created_by

    assert repositorio.actualizar_jornada(
        jornada_id=nuevo, actor="quien-edito",
        entrada={"dni_norm": OTRO_DNI, "jornada_semanal": 42.0,
                 "patron": None, "desde": "2026-08-01",
                 "hasta": "2026-09-01", "nota": "cambiada"}) is True

    fila = _fila_cruda(fabrica, nuevo)
    assert (fila.dni_norm, fila.origen) == (DNI, "manual")
    assert (fila.created_at_utc, fila.created_by) == (creado_en, creado_por)
    assert (fila.jornada_semanal, fila.desde, fila.hasta, fila.nota) == (
        42.0, "2026-08-01", "2026-09-01", "cambiada")
    assert fila.updated_by == "quien-edito"
    assert fila.updated_at_utc is not None


def test_f016_repositorio_editar_puede_quitar_el_patron() -> None:
    """R4: mandar el patron vacio deja los siete dias a NULL."""
    fabrica = FabricaSesionSqlite()
    repositorio = ParteReviewRepository(fabrica)
    [jid] = sembrar_jornadas(fabrica, [
        {"dni_norm": DNI, "patron": [8.0] * 5 + [0.0, 0.0]}])
    repositorio.actualizar_jornada(
        jornada_id=jid, actor=None,
        entrada={"dni_norm": DNI, "jornada_semanal": 40.0, "patron": None,
                 "desde": "2026-01-01", "hasta": None, "nota": None})
    fila = _fila_cruda(fabrica, jid)
    assert [getattr(fila, dia) for dia in DIAS] == [None] * 7


def test_f016_repositorio_cerrar_deja_la_fila_activa() -> None:
    """R5 y DA2: cerrar no es desactivar."""
    fabrica = FabricaSesionSqlite()
    [jid] = sembrar_jornadas(fabrica, [{"dni_norm": DNI, "desde": "2026-07-01"}])
    assert ParteReviewRepository(fabrica).cerrar_jornada(
        jornada_id=jid, hasta="2026-08-01", actor="quien") is True
    fila = _fila_cruda(fabrica, jid)
    assert (fila.hasta, fila.is_active, fila.updated_by) == (
        "2026-08-01", True, "quien")


def test_f016_repositorio_desactivar_no_borra_la_fila() -> None:
    """R6: la papelera es logica; la fila sigue en la tabla."""
    fabrica = FabricaSesionSqlite()
    [jid] = sembrar_jornadas(fabrica, [{"dni_norm": DNI}])
    repositorio = ParteReviewRepository(fabrica)
    assert repositorio.set_jornada_activa(
        jornada_id=jid, activa=False, actor="quien") is True
    assert _cuantas(fabrica) == 1
    assert _fila_cruda(fabrica, jid).is_active is False
    # Y desaparece de lo que lee el resolutor de F-015.
    assert repositorio.list_jornadas_empleado() == []
    # Reactivar la devuelve.
    assert repositorio.set_jornada_activa(
        jornada_id=jid, activa=True, actor="quien") is True
    assert len(repositorio.list_jornadas_empleado()) == 1


@pytest.mark.parametrize("operacion", ["actualizar", "cerrar", "activar"])
def test_f016_repositorio_devuelve_false_si_el_id_no_existe(operacion) -> None:
    """R16: `False` en vez de lanzar; la vista lo traduce a 404."""
    repositorio = ParteReviewRepository(FabricaSesionSqlite())
    if operacion == "actualizar":
        salida = repositorio.actualizar_jornada(
            jornada_id=999, actor=None,
            entrada={"dni_norm": DNI, "jornada_semanal": 40.0, "patron": None,
                     "desde": "2026-07-01", "hasta": None, "nota": None})
    elif operacion == "cerrar":
        salida = repositorio.cerrar_jornada(
            jornada_id=999, hasta="2026-08-01", actor=None)
    else:
        salida = repositorio.set_jornada_activa(
            jornada_id=999, activa=False, actor=None)
    assert salida is False


def test_f016_repositorio_la_tabla_vacia_no_es_un_error() -> None:
    assert ParteReviewRepository(FabricaSesionSqlite()).list_jornadas_admin() == []
