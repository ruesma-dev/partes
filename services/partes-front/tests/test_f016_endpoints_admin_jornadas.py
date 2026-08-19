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


# ====================================================================== #
# Los endpoints (T4)
# ====================================================================== #

# ------------------------------- R3 · alta ---------------------------- #

def test_f016_r3_crear() -> None:
    cliente, _, fabrica, proveedor = _montaje()
    respuesta = cliente.post("/api/admin/jornadas",
                             json=_alta(nota="convenio propio"))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True and isinstance(cuerpo["id"], int)

    fila = _fila_cruda(fabrica, cuerpo["id"])
    assert (fila.dni_norm, fila.jornada_semanal, fila.desde, fila.hasta) == (
        DNI, 48.0, "2026-07-01", None)
    assert (fila.origen, fila.is_active, fila.nota) == (
        "manual", True, "convenio propio")
    # En el alta no hay nada que actualizar todavia.
    assert (fila.updated_at_utc, fila.updated_by) == (None, None)


def test_f016_r3_el_origen_no_es_del_cliente() -> None:
    """Mande lo que mande el cuerpo, `origen` lo pone el servidor."""
    cliente, _, fabrica, _ = _montaje()
    nuevo = cliente.post("/api/admin/jornadas",
                         json=_alta(origen="sigrid")).json()["id"]
    assert _fila_cruda(fabrica, nuevo).origen == "manual"


def test_f016_r3_el_alta_con_patron_guarda_los_siete_dias() -> None:
    cliente, _, fabrica, _ = _montaje()
    patron = {"h_lun": "7", "h_mar": "7", "h_mie": "7", "h_jue": "7",
              "h_vie": "6,5", "h_sab": "0", "h_dom": "0"}
    nuevo = cliente.post("/api/admin/jornadas", json=_alta(
        jornada_semanal="", **patron)).json()["id"]
    fila = _fila_cruda(fabrica, nuevo)
    assert [getattr(fila, dia) for dia in DIAS] == [7.0] * 4 + [6.5, 0.0, 0.0]
    assert fila.jornada_semanal is None


@pytest.mark.parametrize("cuerpo, estado", [
    ({"dni": DNI, "desde": "2026-07-01"}, 422),            # R8: ni S ni patron
    (_alta(jornada_semanal="0"), 422),                     # R10
    (_alta(jornada_semanal="169"), 422),                   # R10
    (_alta(h_lun="8"), 422),                               # R9: patron a medias
    (_alta(desde=""), 422),                                # R11
    (_alta(desde="2026-02-30"), 422),                      # R11
    (_alta(hasta_inclusivo="2026-06-30"), 422),            # R11: fin < desde
    (_alta(dni=""), 422),                                  # R18
])
def test_f016_un_alta_rechazada_no_escribe_nada(cuerpo, estado) -> None:
    """La regla de F-004 repetida aqui: un 4xx que ya escribio no sirve."""
    cliente, _, fabrica, proveedor = _montaje()
    antes = _cuantas(fabrica)
    respuesta = cliente.post("/api/admin/jornadas", json=cuerpo)
    assert respuesta.status_code == estado
    assert respuesta.json()["ok"] is False
    assert respuesta.json()["error"]
    assert _cuantas(fabrica) == antes == 0
    assert proveedor.invalidaciones == 0       # R14: sin exito, sin invalidar


def test_f016_un_cuerpo_ilegible_es_un_422_y_no_un_500() -> None:
    cliente, _, fabrica, _ = _montaje()
    respuesta = cliente.post("/api/admin/jornadas",
                             content=b"esto no es json",
                             headers={"content-type": "application/json"})
    assert respuesta.status_code == 422
    assert _cuantas(fabrica) == 0


# ------------------------------ R4 · edicion -------------------------- #

def test_f016_r4_editar() -> None:
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "jornada_semanal": 48.0,
         "created_by": "quien-creo"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    respuesta = cliente.patch(f"/api/admin/jornadas/{jid}", json={
        "dni": OTRO_DNI,                       # se IGNORA (R4)
        "jornada_semanal": "42", "desde": "2026-07-15",
        "hasta_inclusivo": "2026-08-31", "nota": "revisada"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "id": jid}

    fila = _fila_cruda(fabrica, jid)
    assert fila.dni_norm == DNI                # sigue siendo el mismo
    assert fila.created_by == "quien-creo"     # la autoria del alta, intacta
    assert (fila.jornada_semanal, fila.desde, fila.hasta, fila.nota) == (
        42.0, "2026-07-15", "2026-09-01", "revisada")
    assert fila.updated_at_utc is not None


def test_f016_r4_editar_puede_quitar_el_patron() -> None:
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01",
         "patron": [8.0] * 5 + [0.0, 0.0]}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    assert cliente.patch(f"/api/admin/jornadas/{jid}", json={
        "jornada_semanal": "40", "desde": "2026-07-01"}).status_code == 200
    assert [getattr(_fila_cruda(fabrica, jid), d) for d in DIAS] == [None] * 7


def test_f016_una_edicion_rechazada_no_toca_la_fila() -> None:
    cliente, repositorio, fabrica, proveedor = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "jornada_semanal": 48.0}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    respuesta = cliente.patch(f"/api/admin/jornadas/{jid}",
                              json={"jornada_semanal": "999",
                                    "desde": "2026-07-01"})
    assert respuesta.status_code == 422
    assert _fila_cruda(fabrica, jid).jornada_semanal == 48.0
    assert proveedor.invalidaciones == 0


# ------------------------------- R5 · cierre -------------------------- #

def test_f016_r5_cerrar() -> None:
    """El ultimo dia incluido 31/07 se guarda como `hasta = 2026-08-01`."""
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    respuesta = cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                             json={"hasta_inclusivo": "2026-07-31"})
    assert respuesta.status_code == 200 and respuesta.json()["ok"] is True
    fila = _fila_cruda(fabrica, jid)
    assert fila.hasta == "2026-08-01"
    assert fila.is_active is True              # cerrar NO es desactivar
    assert fila.updated_at_utc is not None


def test_f016_r5_una_fila_ya_cerrada_se_recierra_con_la_fecha_nueva() -> None:
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    assert cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                        json={"hasta_inclusivo": "2026-09-30"}
                        ).status_code == 200
    assert _fila_cruda(fabrica, jid).hasta == "2026-10-01"


def test_f016_r5_cerrar_antes_del_inicio_se_rechaza_sin_escribir() -> None:
    cliente, repositorio, fabrica, proveedor = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    respuesta = cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                             json={"hasta_inclusivo": "2026-06-30"})
    assert respuesta.status_code == 422
    assert _fila_cruda(fabrica, jid).hasta is None
    assert proveedor.invalidaciones == 0


def test_f016_r5_cerrar_sin_fecha_reabre_la_vigencia() -> None:
    """«Sin fecha de fin» es `hasta = NULL` tambien al cerrar (R7)."""
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    assert cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                        json={"hasta_inclusivo": ""}).status_code == 200
    assert _fila_cruda(fabrica, jid).hasta is None


# --------------------------- R6 · papelera logica --------------------- #

def test_f016_r6_papelera_logica() -> None:
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]

    assert cliente.post(f"/api/admin/jornadas/{jid}/desactivar"
                        ).status_code == 200
    assert _cuantas(fabrica) == 1                       # sigue en la tabla
    assert _fila_cruda(fabrica, jid).is_active is False
    assert repositorio.list_jornadas_empleado() == []   # y fuera de F-015

    assert cliente.post(f"/api/admin/jornadas/{jid}/reactivar"
                        ).status_code == 200
    assert _fila_cruda(fabrica, jid).is_active is True


def test_f016_r6_reactivar_con_solape_devuelve_409_y_la_deja_inactiva() -> None:
    """No se toca ni ella ni la otra: el humano decide (DA3)."""
    cliente, repositorio, fabrica, proveedor = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01",
         "is_active": False},
        {"dni_norm": DNI, "desde": "2026-07-10"},          # activa, la pisa
    ])
    filas = repositorio.list_jornadas_admin()
    inactiva = next(f for f in filas if not f["is_active"])
    activa = next(f for f in filas if f["is_active"])

    respuesta = cliente.post(f"/api/admin/jornadas/{inactiva['id']}/reactivar")
    assert respuesta.status_code == 409
    assert respuesta.json()["conflicto"]["id"] == activa["id"]
    assert _fila_cruda(fabrica, inactiva["id"]).is_active is False
    assert _fila_cruda(fabrica, activa["id"]).desde == "2026-07-10"   # intacta
    assert proveedor.invalidaciones == 0


def test_f016_r6_ningun_endpoint_borra_la_fila() -> None:
    cliente, repositorio, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    for ruta in ("desactivar", "reactivar", "desactivar"):
        cliente.post(f"/api/admin/jornadas/{jid}/{ruta}")
    cliente.patch(f"/api/admin/jornadas/{jid}",
                  json={"jornada_semanal": "40", "desde": "2026-07-01"})
    cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                 json={"hasta_inclusivo": "2026-07-31"})
    assert _cuantas(fabrica) == 1


# --------------------- R12 · el solape, por HTTP ---------------------- #

def test_f016_r12_solape() -> None:
    """409 con la fila en conflicto en el cuerpo y la BBDD intacta."""
    cliente, repositorio, fabrica, proveedor = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01"}])
    existente = repositorio.list_jornadas_admin()[0]

    respuesta = cliente.post("/api/admin/jornadas",
                             json=_alta(desde="2026-07-31"))
    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert cuerpo["conflicto"] == {
        "id": existente["id"], "desde": "2026-07-01",
        "hasta_inclusivo": "2026-07-31"}
    # Ni se creo la nueva, ni se ajusto la vieja (DA3).
    assert _cuantas(fabrica) == 1
    assert _fila_cruda(fabrica, existente["id"]).hasta == "2026-08-01"
    assert proveedor.invalidaciones == 0


def test_f016_r12_encadenar_vigencias_contiguas_se_acepta() -> None:
    """`hasta` de una = `desde` de la otra: es el caso NORMAL."""
    cliente, _, fabrica, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01"}])
    assert cliente.post("/api/admin/jornadas",
                        json=_alta(desde="2026-08-01")).status_code == 200
    assert _cuantas(fabrica) == 2


def test_f016_r12_una_fila_inactiva_no_reserva_vigencia() -> None:
    cliente, _, _, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "is_active": False}])
    assert cliente.post("/api/admin/jornadas",
                        json=_alta(desde="2026-07-15")).status_code == 200


def test_f016_r12_otro_trabajador_no_choca() -> None:
    cliente, _, _, _ = _montaje([{"dni_norm": OTRO_DNI, "desde": "2026-07-01"}])
    assert cliente.post("/api/admin/jornadas",
                        json=_alta(desde="2026-07-15")).status_code == 200


def test_f016_r12_guardar_una_fila_sin_cambios_no_choca_consigo_misma() -> None:
    cliente, repositorio, _, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01"}])
    jid = repositorio.list_jornadas_admin()[0]["id"]
    assert cliente.patch(f"/api/admin/jornadas/{jid}", json={
        "jornada_semanal": "48", "desde": "2026-07-01",
        "hasta_inclusivo": "2026-07-31"}).status_code == 200


def test_f016_r12_el_dni_escrito_de_otra_forma_sigue_solapando() -> None:
    """R18 + R12: normalizar el DNI es lo que hace util el control."""
    cliente, _, fabrica, _ = _montaje([
        {"dni_norm": "1234ABCD", "desde": "2026-07-01"}])
    respuesta = cliente.post("/api/admin/jornadas",
                             json=_alta(dni=" 1234-abcd ", desde="2026-08-01"))
    assert respuesta.status_code == 409
    assert _cuantas(fabrica) == 1


# --------------------------- R13 · auditoria -------------------------- #

def test_f016_r13_auditoria(monkeypatch) -> None:
    """Las cuatro modificaciones sellan `updated_by`; el alta, `created_by`.

    El actor se parchea por su RESULTADO (`DEFAULT_REVIEWER`), no
    fabricando cabeceras: asi este test sigue en verde el dia que F-017
    cambie el interior de `_actor`.
    """
    monkeypatch.setenv("DEFAULT_REVIEWER", "quien-firma")
    cliente, _, fabrica, _ = _montaje()

    jid = cliente.post("/api/admin/jornadas", json=_alta()).json()["id"]
    fila = _fila_cruda(fabrica, jid)
    assert fila.created_by == "quien-firma"
    assert fila.created_at_utc.endswith("+00:00")
    assert (fila.updated_at_utc, fila.updated_by) == (None, None)

    for peticion in (
        lambda: cliente.patch(f"/api/admin/jornadas/{jid}", json={
            "jornada_semanal": "40", "desde": "2026-07-01"}),
        lambda: cliente.post(f"/api/admin/jornadas/{jid}/cerrar",
                             json={"hasta_inclusivo": "2026-07-31"}),
        lambda: cliente.post(f"/api/admin/jornadas/{jid}/desactivar"),
        lambda: cliente.post(f"/api/admin/jornadas/{jid}/reactivar"),
    ):
        with fabrica.create_session() as s:
            s.get(EmpleadoJornadaOrm, jid).updated_by = None
            s.commit()
        assert peticion().status_code == 200
        sellada = _fila_cruda(fabrica, jid)
        assert sellada.updated_by == "quien-firma"
        assert sellada.updated_at_utc is not None
        # Y el alta nunca se reescribe.
        assert sellada.created_by == "quien-firma"


def test_f016_r13_sin_default_reviewer_se_sella_nulo_y_no_falla() -> None:
    cliente, _, fabrica, _ = _montaje()
    assert _settings().default_reviewer is None
    jid = cliente.post("/api/admin/jornadas", json=_alta()).json()["id"]
    assert _fila_cruda(fabrica, jid).created_by is None


def test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio() -> None:
    """`grep`: ninguna otra lectura de la identidad en el codigo de F-016."""
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1]
              / "interface_adapters" / "web" / "app.py").read_text(
                  encoding="utf-8")
    inicio = fuente.index("F-016 · administracion de")
    fin = fuente.index('@app.patch("/api/registros/{registro_id}/hora")')
    bloque = fuente[inicio:fin]
    assert inicio < fin, "el bloque de F-016 ya no esta donde se creo"
    # El bloque de F-016 no lee la identidad por su cuenta ni una vez...
    assert "settings.default_reviewer" not in bloque
    # ...y las cinco escrituras la piden al MISMO helper.
    assert bloque.count("_actor(request)") == 5
    # `_actor` es el unico sitio de F-016 con `settings.default_reviewer`,
    # y esta fuera del bloque de endpoints, junto a la puerta de acceso.
    assert fuente.count("def _actor(request: Request)") == 1


# ------------------------- R16 · id inexistente ----------------------- #

@pytest.mark.parametrize("metodo, ruta, cuerpo", [
    ("patch", "/api/admin/jornadas/999", {"jornada_semanal": "40",
                                          "desde": "2026-07-01"}),
    ("post", "/api/admin/jornadas/999/cerrar", {"hasta_inclusivo": None}),
    ("post", "/api/admin/jornadas/999/desactivar", {}),
    ("post", "/api/admin/jornadas/999/reactivar", {}),
])
def test_f016_r16_no_encontrada(metodo, ruta, cuerpo) -> None:
    cliente, _, _, _ = _montaje()
    respuesta = getattr(cliente, metodo)(ruta, json=cuerpo)
    assert respuesta.status_code == 404
    assert respuesta.json()["ok"] is False
    assert respuesta.json()["error"]


def test_f016_r16_un_id_no_numerico_es_un_422_de_ruta_no_un_500() -> None:
    cliente, _, _, _ = _montaje()
    assert cliente.post("/api/admin/jornadas/abc/desactivar"
                        ).status_code == 422


# ---------------------- R19 · DNI que no consta ----------------------- #

class CatalogoFake:
    """Doble del `EmpleadoCatalog`: enciende/apaga y cuenta las llamadas."""

    def __init__(self, dnis=(), *, activo: bool = True) -> None:
        self.enabled = activo
        self._dnis = list(dnis)
        self.llamadas = 0

    def list(self):
        self.llamadas += 1
        return [type("E", (), {"dni": d})() for d in self._dnis]


def test_f016_r19_dni_desconocido_avisa() -> None:
    """Se avisa, NO se bloquea: la fila se crea igual."""
    cliente, _, fabrica, _ = _montaje()
    cliente.app.state.empleado_catalog = CatalogoFake(["9999ZZZZ"])
    respuesta = cliente.post("/api/admin/jornadas", json=_alta())
    assert respuesta.status_code == 200
    assert "Sigrid" in respuesta.json()["aviso"]
    assert _cuantas(fabrica) == 1


def test_f016_r19_un_dni_del_catalogo_no_molesta_al_humano() -> None:
    cliente, _, _, _ = _montaje()
    cliente.app.state.empleado_catalog = CatalogoFake([" aaa-1 "])
    assert "aviso" not in cliente.post("/api/admin/jornadas",
                                       json=_alta()).json()


def test_f016_r19_con_el_catalogo_apagado_no_se_consulta_a_sigrid() -> None:
    """La pantalla no depende de que Sigrid este cableado (R17)."""
    cliente, _, _, _ = _montaje()
    catalogo = CatalogoFake(["9999ZZZZ"], activo=False)
    cliente.app.state.empleado_catalog = catalogo
    respuesta = cliente.post("/api/admin/jornadas", json=_alta())
    assert respuesta.status_code == 200
    assert "aviso" not in respuesta.json()
    assert catalogo.llamadas == 0


def test_f016_r19_si_sigrid_falla_el_alta_se_guarda_igual() -> None:
    class CatalogoRoto:
        enabled = True

        def list(self):
            raise RuntimeError("Sigrid no contesta")

    cliente, _, fabrica, _ = _montaje()
    cliente.app.state.empleado_catalog = CatalogoRoto()
    respuesta = cliente.post("/api/admin/jornadas", json=_alta())
    assert respuesta.status_code == 200
    assert _cuantas(fabrica) == 1
