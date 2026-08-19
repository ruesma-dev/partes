# tests/test_f016_vista_admin_jornadas.py
"""F-016 · La pagina `/admin/jornadas`: puerta, listado, aviso y selector.

Cubre R1 (el schema no se toca), R2 (listado), R14 (aviso de cache e
invalidacion), R15 (puerta de acceso unica), R17 (nada de red) y R20
(selector de trabajador reutilizado).

Todo con TestClient + SQLite en memoria y `Settings(_env_file=None)`: la
app se levanta SIN cliente de Sigrid, SIN Sesame, SIN colas y SIN sv5.

DNIs sinteticos: aqui no aparece ningun DNI ni nombre de persona real.
"""
from __future__ import annotations

import pytest
from application.services.jornada_admin import DIAS
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_jornadas

DNI = "AAA1"
OTRO_DNI = "BBB2"

#: Las seis rutas de la pantalla: la pagina y los cinco endpoints (R15).
RUTAS = (
    ("get", "/admin/jornadas", None),
    ("post", "/api/admin/jornadas", {}),
    ("patch", "/api/admin/jornadas/1", {}),
    ("post", "/api/admin/jornadas/1/cerrar", {}),
    ("post", "/api/admin/jornadas/1/desactivar", {}),
    ("post", "/api/admin/jornadas/1/reactivar", {}),
)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


class ProveedorFake:
    def __init__(self) -> None:
        self.invalidaciones = 0

    def invalidar(self) -> None:
        self.invalidaciones += 1

    def excepcion_para(self, dni, fecha):
        return None


def _montaje(filas=(), *, settings=None, proveedor=None):
    fabrica = FabricaSesionSqlite()
    if filas:
        sembrar_jornadas(fabrica, list(filas))
    repositorio = ParteReviewRepository(fabrica)
    app = build_app(settings or _settings(), repository=repositorio,
                    jornada_provider=proveedor or ProveedorFake())
    return TestClient(app), fabrica


def _pedir(cliente, metodo: str, ruta: str, cuerpo):
    fn = getattr(cliente, metodo)
    return fn(ruta) if cuerpo is None else fn(ruta, json=cuerpo)


# ====================================================================== #
# R15 · la puerta de acceso, escrita UNA sola vez
# ====================================================================== #

@pytest.mark.parametrize("metodo, ruta, cuerpo", RUTAS)
def test_f016_r15_puerta_de_acceso(metodo, ruta, cuerpo) -> None:
    """Con `JORNADAS_ADMIN_ENABLED` en falso, las SEIS rutas dan 404."""
    cliente, _ = _montaje(settings=_settings(JORNADAS_ADMIN_ENABLED=False))
    assert _pedir(cliente, metodo, ruta, cuerpo).status_code == 404


@pytest.mark.parametrize("metodo, ruta, cuerpo", RUTAS)
def test_f016_r15_con_la_variable_a_verdadero_las_seis_responden(
    metodo, ruta, cuerpo,
) -> None:
    """Y con ella encendida (el DEFAULT) ninguna es un 404 de ruta.

    Es la mitad que de verdad prueba algo: una ruta que NO EXISTE tambien
    devuelve 404, asi que sin este caso el test de arriba pasaria con la
    feature entera sin escribir.
    """
    cliente, fabrica = _montaje([{"dni_norm": DNI, "desde": "2026-07-01"}])
    respuesta = _pedir(cliente, metodo, ruta.replace("/1", "/1"), cuerpo)
    assert respuesta.status_code != 404


def test_f016_r15_el_interruptor_llega_encendido_de_fabrica() -> None:
    assert _settings().jornadas_admin_enabled is True


def test_f016_r15_apagarla_no_cambia_ninguna_otra_ruta() -> None:
    """La puerta es de esta pantalla, no del portal."""
    cliente, _ = _montaje(settings=_settings(JORNADAS_ADMIN_ENABLED=False))
    assert cliente.get("/health").status_code == 200
    assert cliente.get("/trabajadores").status_code == 200


def test_f016_r15_el_enlace_de_la_barra_sigue_al_interruptor() -> None:
    encendida, _ = _montaje()
    apagada, _ = _montaje(settings=_settings(JORNADAS_ADMIN_ENABLED=False))
    assert '/admin/jornadas' in encendida.get("/trabajadores").text
    assert '/admin/jornadas' not in apagada.get("/trabajadores").text


def test_f016_r15_hay_exactamente_una_funcion_que_decide_el_acceso() -> None:
    """F-008 tiene que poder enchufar el rol tocando UN solo punto.

    Si algun dia aparece una segunda comprobacion del interruptor, este
    test lo dice antes de que haya dos sitios que mantener.
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1]
              / "interface_adapters" / "web" / "app.py").read_text(
                  encoding="utf-8")
    assert fuente.count("settings.jornadas_admin_enabled") == 2, (
        "solo la puerta unica y el global de la plantilla pueden leer el "
        "interruptor")
    # Se declara una vez...
    assert fuente.count("def _exigir_admin_jornadas()") == 1
    # ...y las seis rutas de la pantalla la llaman, cada una la primera.
    assert fuente.count("\n        _exigir_admin_jornadas()\n") == 6


# ====================================================================== #
# R1 · el schema no se toca
# ====================================================================== #

def test_f016_r1_schema_intacto() -> None:
    """F-016 trabaja sobre `empleado_jornada` tal como la dejo F-015.

    Las 19 columnas, con sus tipos y su `nullable`. Si esta feature
    hubiera necesitado una columna nueva es que el diseno se torcio.
    """
    from infrastructure.database.orm_models import EmpleadoJornadaOrm

    columnas = EmpleadoJornadaOrm.__table__.columns
    assert tuple(c.name for c in columnas) == (
        "id", "dni_norm", "jornada_semanal",
        "h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom",
        "desde", "hasta", "origen", "nota", "is_active",
        "created_at_utc", "created_by", "updated_at_utc", "updated_by")
    assert len(columnas) == 19
    # Los `nullable` que sostienen las reglas de la pantalla.
    assert columnas["dni_norm"].nullable is False
    assert columnas["desde"].nullable is False
    assert columnas["hasta"].nullable is True          # vigencia abierta
    assert columnas["is_active"].nullable is False     # papelera logica
    assert all(columnas[d].nullable for d in DIAS)


def test_f016_r1_la_semantica_heredada_de_f015_sigue_igual() -> None:
    """`origen` con default `manual` e `is_active` con default `true`."""
    from infrastructure.database.orm_models import EmpleadoJornadaOrm

    columnas = EmpleadoJornadaOrm.__table__.columns
    assert columnas["origen"].default.arg == "manual"
    assert columnas["is_active"].default.arg is True


# ====================================================================== #
# R2 · el listado
# ====================================================================== #

def test_f016_r2_listado() -> None:
    """Todas las filas, ordenadas, y la vigencia en formato INCLUSIVO."""
    cliente, _ = _montaje([
        {"dni_norm": OTRO_DNI, "desde": "2026-01-01", "jornada_semanal": 40.0},
        {"dni_norm": DNI, "desde": "2026-01-01", "hasta": "2026-08-01",
         "jornada_semanal": 40.0, "nota": "convenio viejo",
         "created_by": "quien-creo"},
        {"dni_norm": DNI, "desde": "2026-08-01", "jornada_semanal": 48.0},
    ])
    respuesta = cliente.get("/admin/jornadas")
    assert respuesta.status_code == 200

    filas = respuesta.context["filas"]
    assert [(f["dni_norm"], f["desde"]) for f in filas] == [
        (DNI, "2026-08-01"), (DNI, "2026-01-01"), (OTRO_DNI, "2026-01-01")]

    html = respuesta.text
    # `hasta = 2026-08-01` se pinta como ULTIMO DIA INCLUIDO 2026-07-31...
    assert "2026-07-31" in html
    # ...y el valor exclusivo NO aparece como fin de esa vigencia.
    assert "2026-01-01 … 2026-08-01" not in html
    assert "sin fin" in html                     # la vigencia abierta
    assert "convenio viejo" in html and "quien-creo" in html
    # Y la palabra que el humano no tiene por que conocer, en ningun sitio.
    assert "exclusiv" not in html.lower()


def test_f016_r2_una_fila_inactiva_se_marca_pero_no_desaparece() -> None:
    cliente, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "is_active": False}])
    respuesta = cliente.get("/admin/jornadas")
    assert len(respuesta.context["filas"]) == 1
    assert "inactiva" in respuesta.text
    assert "Reactivar" in respuesta.text


def test_f016_r2_la_tabla_vacia_no_es_un_error() -> None:
    cliente, _ = _montaje()
    respuesta = cliente.get("/admin/jornadas")
    assert respuesta.status_code == 200
    assert respuesta.context["filas"] == []
    assert "No hay ninguna excepcion" in respuesta.text


def test_f016_r2_el_patron_se_pinta_con_sus_siete_valores() -> None:
    cliente, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01",
         "patron": [7.0, 7.0, 7.0, 7.0, 6.5, 0.0, 0.0]}])
    respuesta = cliente.get("/admin/jornadas")
    assert respuesta.context["filas"][0]["patron"] == [
        "7", "7", "7", "7", "6.5", "0", "0"]


def test_f016_r2_una_fila_sin_patron_ni_semanal_no_rompe_la_pagina() -> None:
    """Las filas anteriores a F-016 las cargo el humano por SQL."""
    cliente, _ = _montaje([{"dni_norm": DNI, "desde": "2026-07-01"}])
    respuesta = cliente.get("/admin/jornadas")
    assert respuesta.status_code == 200
    assert respuesta.context["filas"][0]["patron"] is None


def test_f016_r2_editar_precarga_el_formulario_desde_el_servidor() -> None:
    cliente, _ = _montaje([
        {"dni_norm": DNI, "desde": "2026-07-01", "hasta": "2026-08-01",
         "jornada_semanal": 48.0, "nota": "la nota"}])
    jid = cliente.get("/admin/jornadas").context["filas"][0]["id"]
    respuesta = cliente.get(f"/admin/jornadas?editar={jid}")
    edicion = respuesta.context["edicion"]
    assert edicion["id"] == jid
    assert edicion["semanal_texto"] == "48"
    # El formulario ensena el ULTIMO DIA INCLUIDO, no el valor guardado.
    assert edicion["hasta_inclusivo"] == "2026-07-31"
    assert 'value="2026-07-31"' in respuesta.text
    assert "Guardar cambios" in respuesta.text


def test_f016_r2_editar_un_id_que_no_existe_cae_al_modo_alta() -> None:
    cliente, _ = _montaje()
    respuesta = cliente.get("/admin/jornadas?editar=999")
    assert respuesta.status_code == 200
    assert respuesta.context["edicion"] is None


# ====================================================================== #
# R14 · el aviso de cache y la invalidacion del proveedor
# ====================================================================== #

def test_f016_r14_cache_y_aviso() -> None:
    """El aviso lleva los minutos DERIVADOS de `JORNADA_CACHE_TTL_S`."""
    cliente, _ = _montaje()
    assert "10 minutos" in cliente.get("/admin/jornadas").text

    otro, _ = _montaje(settings=_settings(JORNADA_CACHE_TTL_S=900))
    assert "15 minutos" in otro.get("/admin/jornadas").text


def test_f016_r14_el_aviso_es_permanente_y_dice_a_quien_afecta() -> None:
    cliente, _ = _montaje()
    html = cliente.get("/admin/jornadas").text
    assert "Los cambios tardan en aplicarse" in html
    assert "sv3" in html


@pytest.mark.parametrize("accion", [
    "crear", "editar", "cerrar", "desactivar", "reactivar"])
def test_f016_r14_cada_escritura_con_exito_invalida_una_vez(accion) -> None:
    proveedor = ProveedorFake()
    cliente, fabrica = _montaje(
        [{"dni_norm": DNI, "desde": "2026-07-01"}], proveedor=proveedor)
    jid = cliente.get("/admin/jornadas").context["filas"][0]["id"]
    if accion == "reactivar":
        cliente.post(f"/api/admin/jornadas/{jid}/desactivar")
    proveedor.invalidaciones = 0

    respuestas = {
        "crear": lambda: cliente.post("/api/admin/jornadas", json={
            "dni": OTRO_DNI, "jornada_semanal": "40", "desde": "2026-07-01"}),
        "editar": lambda: cliente.patch(f"/api/admin/jornadas/{jid}", json={
            "jornada_semanal": "40", "desde": "2026-07-01"}),
        "cerrar": lambda: cliente.post(
            f"/api/admin/jornadas/{jid}/cerrar",
            json={"hasta_inclusivo": "2026-07-31"}),
        "desactivar": lambda: cliente.post(
            f"/api/admin/jornadas/{jid}/desactivar"),
        "reactivar": lambda: cliente.post(
            f"/api/admin/jornadas/{jid}/reactivar"),
    }
    assert respuestas[accion]().status_code == 200
    assert proveedor.invalidaciones == 1


def test_f016_r14_un_rechazo_no_invalida_nada() -> None:
    proveedor = ProveedorFake()
    cliente, _ = _montaje(
        [{"dni_norm": DNI, "desde": "2026-07-01"}], proveedor=proveedor)
    # 422 (mal escrito), 409 (solape) y 404 (no existe).
    cliente.post("/api/admin/jornadas", json={"dni": DNI, "desde": ""})
    cliente.post("/api/admin/jornadas", json={
        "dni": DNI, "jornada_semanal": "40", "desde": "2026-07-15"})
    cliente.post("/api/admin/jornadas/999/desactivar")
    assert proveedor.invalidaciones == 0


def test_f016_r14_sin_proveedor_las_escrituras_siguen_funcionando() -> None:
    cliente, _ = _montaje()
    cliente.app.state.jornada_provider = None
    respuesta = cliente.post("/api/admin/jornadas", json={
        "dni": DNI, "jornada_semanal": "40", "desde": "2026-07-01"})
    assert respuesta.status_code == 200


def test_f016_r14_el_proveedor_de_verdad_sabe_invalidarse() -> None:
    """El doble no vale como unica prueba: `invalidar()` existe y funciona."""
    from application.services.jornada_provider import JornadaEmpleadoProvider

    lecturas = []

    def cargar():
        lecturas.append(1)
        return []

    proveedor = JornadaEmpleadoProvider(cargar, ttl_seconds=600)
    proveedor.excepcion_para(DNI, __import__("datetime").date(2026, 7, 1))
    proveedor.excepcion_para(DNI, __import__("datetime").date(2026, 7, 1))
    assert len(lecturas) == 1               # la segunda salio de la cache
    proveedor.invalidar()
    proveedor.excepcion_para(DNI, __import__("datetime").date(2026, 7, 1))
    assert len(lecturas) == 2               # tras invalidar, relee


# ====================================================================== #
# R17 · nada de red
# ====================================================================== #

def test_f016_r17_sin_red() -> None:
    """La app SIN Sigrid, SIN Sesame, SIN colas y SIN sv5 sirve la pantalla
    y las cinco operaciones enteras."""
    ajustes = _settings()
    assert ajustes.sigrid_lookup_enabled is False
    assert ajustes.sesame_enabled is False
    assert ajustes.transfer_enabled is False
    assert ajustes.transfer_queue_enabled is False

    cliente, _ = _montaje(settings=ajustes)
    assert cliente.get("/admin/jornadas").status_code == 200

    jid = cliente.post("/api/admin/jornadas", json={
        "dni": DNI, "jornada_semanal": "48", "desde": "2026-07-01"}
    ).json()["id"]
    assert cliente.patch(f"/api/admin/jornadas/{jid}", json={
        "jornada_semanal": "40", "desde": "2026-07-01"}).status_code == 200
    assert cliente.post(f"/api/admin/jornadas/{jid}/cerrar", json={
        "hasta_inclusivo": "2026-07-31"}).status_code == 200
    assert cliente.post(f"/api/admin/jornadas/{jid}/desactivar"
                        ).status_code == 200
    assert cliente.post(f"/api/admin/jornadas/{jid}/reactivar"
                        ).status_code == 200


def test_f016_r17_pintar_la_pagina_no_consulta_el_catalogo() -> None:
    """El combo pide el catalogo por `fetch` DESPUES, desde el navegador."""
    class CatalogoEspia:
        enabled = True

        def __init__(self) -> None:
            self.llamadas = 0

        def list(self):
            self.llamadas += 1
            return []

    cliente, _ = _montaje()
    espia = CatalogoEspia()
    cliente.app.state.empleado_catalog = espia
    assert cliente.get("/admin/jornadas").status_code == 200
    assert espia.llamadas == 0


# ====================================================================== #
# R20 · el selector de trabajador, reutilizando lo que ya existe
# ====================================================================== #

def test_f016_r20_selector_trabajador() -> None:
    """El marcado del combo es el de `nuevo_parte.html`, con sus ids."""
    cliente, _ = _montaje()
    html = cliente.get("/admin/jornadas").text
    for pieza in ('class="combo-simple" id="jor-emp-combo"',
                  'id="jor-emp-input"',
                  'class="combo-panel" id="jor-emp-panel"',
                  'type="hidden" id="jor-dni"',
                  'data-empleados-url="/api/sigrid/empleados"'):
        assert pieza in html, pieza


def test_f016_r20_sin_sigrid_la_pagina_sigue_entera_por_el_camino_manual() -> None:
    """Con `sigrid_lookup_enabled` falso —como corre la suite— el combo
    llega deshabilitado y el DNI a mano, descubierto."""
    cliente, _ = _montaje()
    respuesta = cliente.get("/admin/jornadas")
    assert respuesta.status_code == 200
    assert respuesta.context["sigrid_enabled"] is False
    html = respuesta.text
    assert 'placeholder="Sigrid no configurado"' in html
    assert 'id="jor-manual"' in html and "checked" in html
    assert 'id="jor-dni-manual"' in html
    # El campo manual NO llega oculto cuando es el unico camino.
    assert '<div id="jor-manual-campo" hidden>' not in html


def test_f016_r20_en_modo_edicion_no_se_puede_cambiar_de_trabajador() -> None:
    cliente, _ = _montaje([{"dni_norm": DNI, "desde": "2026-07-01"}])
    jid = cliente.get("/admin/jornadas").context["filas"][0]["id"]
    html = cliente.get(f"/admin/jornadas?editar={jid}").text
    assert 'id="jor-emp-fijo"' in html and "readonly" in html
    assert 'id="jor-emp-combo"' not in html      # ni combo...
    assert 'id="jor-manual"' not in html         # ...ni alta manual
    assert f'value="{DNI}"' in html


def test_f016_r20_f016_no_anade_ni_cambia_ninguna_ruta_de_sigrid() -> None:
    """El selector CONSUME `GET /api/sigrid/empleados` (F-003) tal cual."""
    cliente, _ = _montaje()
    rutas = {(r.path, tuple(sorted(r.methods)))
             for r in cliente.app.routes if hasattr(r, "methods")}
    de_sigrid = {r for r in rutas if r[0].startswith("/api/sigrid/")}
    assert de_sigrid == {
        ("/api/sigrid/tipos-hora", ("GET",)),
        ("/api/sigrid/obras", ("GET",)),
        ("/api/sigrid/empleados", ("GET",)),
        ("/api/sigrid/partidas", ("GET",)),
    }, "F-016 no crea ni modifica endpoints de catalogo"


def test_f016_r20_el_js_cablea_el_combo_sin_tocar_el_componente() -> None:
    """`_comboSimple` se reutiliza, no se duplica ni se modifica (DA11)."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text(
        encoding="utf-8")
    # Una sola definicion del componente...
    assert js.count("function _comboSimple(") == 1
    # ...y el bloque de F-016 la LLAMA, dentro del mismo IIFE.
    assert js.count('_comboSimple("jor-emp-combo"') == 1
    assert js.index("function _comboSimple(") < js.index(
        '_comboSimple("jor-emp-combo"')
