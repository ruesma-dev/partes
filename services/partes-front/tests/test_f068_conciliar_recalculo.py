# tests/test_f068_conciliar_recalculo.py
"""F-068 · casar o reasignar un trabajador (o deshacerlo) pide a sv3 el
recálculo de extras.

Una línea sin casar no tiene jornada y sv3 no la parte en ordinaria y
extra. Hasta F-068, casarla en Conciliar la dejaba con todas sus horas
como ordinarias y aprobable hasta la siguiente pasada completa de sv3
(obra 0694, 04/11/2026). Desde F-068, sv4 pide UN recálculo con pedido
compartido (F-049) sobre los partes de las líneas que escribió.

Sin red: repositorio real sobre SQLite, una cola doble y un cliente de
Sigrid falso. Datos sintéticos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest
from application.services import text_match as tm
from application.services.seguimiento_recalculo import MOTIVO_RECALCULANDO
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import (
    EmpleadoAliasOrm,
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.persistencia.recalculo_publisher import (
    MOTIVO_CASADO_CONCILIACION,
    MOTIVO_DESHACER_TRABAJADOR,
    MOTIVO_REASIGNACION,
)
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import (
    FabricaSesionSqlite,
    datos_registros,
    estados_sigrid,
    sembrar_parte,
)
from tests.test_f004_endpoints_congelados import SigridLookupClientFake
from tests.test_f022_aprobar_seleccion import (
    ENDPOINTS,
    CalendarioFalso,
    PublisherFalso,
    Sv5Falso,
)
from tests.test_f042_recalculo_fecha import ColaFake

LEIDO = "Juan Leido"
ACTOR = "revisora@ejemplo.es"
CABECERA = {"X-MS-CLIENT-PRINCIPAL-NAME": ACTOR}
#: El trabajador que ofrece `SigridLookupClientFake` (ide 4242).
NOMBRE_SIGRID, DNI_SIGRID = "Ana Casada", "99999999R"


# ======================= R20 · las constantes ========================== #

def test_f068_r20_constantes_de_motivo() -> None:
    assert MOTIVO_CASADO_CONCILIACION == "casado_conciliacion"
    assert MOTIVO_REASIGNACION == "reasignacion_trabajador"
    assert MOTIVO_DESHACER_TRABAJADOR == "deshacer_trabajador"


# ============================== montaje ================================ #

def _libre(leido: str = LEIDO) -> dict:
    return {"estado": None, "leido": leido}


def _sin_casar(fabrica, lineas, *, doc: str, aprobado: bool = False,
               fecha: str = "2026-03-02") -> list[int]:
    return sembrar_parte(fabrica, lineas, document_id=doc, aprobado=aprobado,
                         fecha=fecha, empleado_ide=None)


@pytest.fixture
def montaje(monkeypatch):
    """`_montar(sembrar, ...) -> (cliente, cola, fabrica, ids)`.

    `sembrar(fabrica)` siembra y devuelve los ids de las líneas."""
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

    def _montar(sembrar, *, cola: ColaFake | None = None,
                sin_cola: bool = False, repositorio=None, fabrica=None,
                **kw):
        fabrica = fabrica or FabricaSesionSqlite()
        ids = sembrar(fabrica)
        cola = None if sin_cola else (cola or ColaFake())
        app = build_app(
            Settings(_env_file=None),
            repository=repositorio or ParteReviewRepository(fabrica),
            cola_cliente=cola, **kw)
        return TestClient(app), cola, fabrica, ids
    return _montar


def _uno(fabrica):
    return _sin_casar(fabrica, [_libre(), _libre("Otro Distinto")],
                      doc="d-1")


def _dos(fabrica):
    """D2 se siembra antes: sus líneas tienen ids menores (va delante)."""
    return (_sin_casar(fabrica, [_libre()], doc="d-2", fecha="2026-03-03")
            + _sin_casar(fabrica, [_libre(), _libre()], doc="d-1"))


def _mezcla(fabrica):
    """D1 libre; D2 aprobado (sus líneas congeladas)."""
    return (_sin_casar(fabrica, [_libre()], doc="d-1")
            + _sin_casar(fabrica, [_libre()], doc="d-2", aprobado=True,
                         fecha="2026-03-03"))


def _solo_congeladas(fabrica):
    return _sin_casar(fabrica, [_libre()], doc="d-2", aprobado=True)


def _casar(cliente, leido: str = LEIDO):
    return cliente.post("/api/conciliacion/confirmar", headers=CABECERA,
                        json={"nombre_leido": leido, "ide": 4242})


def _pedido(fabrica, doc: str) -> str | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, doc).recalculo_pedido_id


def _alias(fabrica, leido: str = LEIDO):
    with fabrica.create_session() as s:
        a = s.get(EmpleadoAliasOrm, tm.normalize(leido))
        return None if a is None else a.empleado_ide


def _poner_pedido(fabrica, doc: str, pedido: str) -> None:
    with fabrica.create_session() as s:
        d = s.get(ParteDocumentOrm, doc)
        d.recalculo_pedido_id = pedido
        d.recalculo_pedido_at_utc = datetime.now(timezone.utc).isoformat()
        s.commit()


def _sin_pedidos(fabrica) -> bool:
    with fabrica.create_session() as s:
        return all(d.recalculo_pedido_id is None
                   for d in s.query(ParteDocumentOrm).all())


# ====================== R1 · Conciliar pide uno ======================== #

def test_f068_conciliar_e1_r1_un_parte_un_recalculo(montaje) -> None:
    cliente, cola, fabrica, ids = montaje(_uno)
    r = _casar(cliente)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["updated"], cuerpo["congeladas"]) == (1, 0)
    assert (cuerpo["recalculo"], cuerpo["partes_recalculo"]) == ("pedido", 1)
    (cola_nombre, mensaje), = cola.enviados
    assert cola_nombre == "q-persistencia"
    assert {k: mensaje[k] for k in ("tipo", "motivo", "document_id",
                                    "solicitado_por")} == {
        "tipo": "recalcular", "motivo": "casado_conciliacion",
        "document_id": "d-1", "solicitado_por": ACTOR}
    pedido = _pedido(fabrica, "d-1")
    assert pedido is not None and len(pedido) == 36      # uuid4
    assert datos_registros(fabrica, ids)[ids[0]]["empleado_ide"] == 4242


def test_f068_conciliar_e2_r1_dos_partes_un_solo_mensaje(montaje) -> None:
    cliente, cola, fabrica, _ids = montaje(_dos)
    cuerpo = _casar(cliente).json()
    assert (cuerpo["updated"], cuerpo["partes_recalculo"]) == (3, 2)
    (_, mensaje), = cola.enviados
    assert mensaje["document_id"] == "d-2"              # el primero por id
    p1, p2 = _pedido(fabrica, "d-1"), _pedido(fabrica, "d-2")
    assert p1 is not None and p1 == p2                  # pedido compartido


def test_f068_conciliar_r1_el_mensaje_sale_tras_el_casado_y_el_alias(
        montaje) -> None:
    """Al publicar, el casado y el alias ya están confirmados: sv3 los lee
    en su pasada. Y el pedido se marcó antes de publicar."""
    visto: dict = {}
    cola = ColaFake()
    cliente, _cola, fabrica, ids = montaje(_uno, cola=cola)
    cola.al_enviar = lambda: visto.update(
        empleado=datos_registros(fabrica, ids)[ids[0]]["empleado_ide"],
        alias=_alias(fabrica), pedido=_pedido(fabrica, "d-1"))
    assert _casar(cliente).status_code == 200
    assert visto["empleado"] == 4242 and visto["alias"] == 4242
    assert visto["pedido"] is not None


def test_f068_conciliar_e3_r4_solo_los_partes_escritos(montaje) -> None:
    cliente, cola, fabrica, _ids = montaje(_mezcla)
    cuerpo = _casar(cliente).json()
    assert (cuerpo["updated"], cuerpo["congeladas"]) == (1, 1)
    assert (cuerpo["recalculo"], cuerpo["partes_recalculo"]) == ("pedido", 1)
    assert _pedido(fabrica, "d-1") is not None
    assert _pedido(fabrica, "d-2") is None
    assert [m["document_id"] for _c, m in cola.enviados] == ["d-1"]


# ================= R2 · sin líneas escritas, nada ====================== #

@pytest.mark.parametrize("sembrar,leido,esperado", [
    pytest.param(_solo_congeladas, LEIDO, (0, 1), id="e4-solo-congeladas"),
    pytest.param(_uno, "Nadie Asi", (0, 0), id="sin-coincidencias"),
])
def test_f068_conciliar_e4_r2_sin_lineas_no_marca_ni_publica(
        montaje, sembrar, leido, esperado) -> None:
    cliente, cola, fabrica, _ids = montaje(sembrar)
    r = _casar(cliente, leido)
    assert r.status_code == 200
    cuerpo = r.json()
    assert (cuerpo["updated"], cuerpo["congeladas"]) == esperado
    assert cuerpo["recalculo"] is None and cuerpo["partes_recalculo"] == 0
    assert cola.enviados == [] and _sin_pedidos(fabrica)


# ===================== R3 · forma de la respuesta ====================== #

def test_f068_conciliar_r3_claves_de_hoy_mas_las_dos_nuevas(montaje) -> None:
    cliente, _cola, _f, _ids = montaje(_uno)
    cuerpo = _casar(cliente).json()
    assert set(cuerpo) == {"ok", "updated", "alias_ok", "congeladas",
                           "empleado", "recalculo", "partes_recalculo"}
    assert cuerpo["ok"] is True and cuerpo["alias_ok"] is True
    assert cuerpo["empleado"] == {"ide": 4242, "codigo": "E42",
                                  "nombre": NOMBRE_SIGRID}


# ================== R5 · la cola falla: casado guardado ================ #

def test_f068_conciliar_e5_r5_cola_caida(montaje) -> None:
    cliente, _cola, fabrica, ids = montaje(
        _uno, cola=ColaFake(error=RuntimeError("cola caida")))
    r = _casar(cliente)
    assert r.status_code == 200
    assert (r.json()["recalculo"], r.json()["partes_recalculo"]) == (
        "fallo", 1)
    assert _pedido(fabrica, "d-1") is None            # pedido quitado
    assert datos_registros(fabrica, ids)[ids[0]]["empleado_ide"] == 4242
    assert _alias(fabrica) == 4242


def test_f068_conciliar_e6_sin_cola(montaje) -> None:
    cliente, _cola, fabrica, ids = montaje(_uno, sin_cola=True)
    r = _casar(cliente)
    assert r.status_code == 200
    assert (r.json()["recalculo"], r.json()["partes_recalculo"]) == (
        "sin_cola", 1)
    assert _pedido(fabrica, "d-1") is None
    assert datos_registros(fabrica, ids)[ids[0]]["empleado_ide"] == 4242


# ============ R6 · marcar o anular que lanzan: solo un WARNING ========== #

class RepoMarcarFalla(ParteReviewRepository):
    def marcar_recalculo_pedido_compartido(self, ids, **_kw) -> int:
        raise RuntimeError("bbdd caida al marcar")


class RepoAnularFalla(ParteReviewRepository):
    def anular_recalculo_pedido_compartido(self, ids, **_kw) -> None:
        raise RuntimeError("bbdd caida al anular")


def _warnings(caplog, texto: str) -> bool:
    return any(texto in m.getMessage() for m in caplog.records
               if m.levelno == logging.WARNING)


def test_f068_conciliar_r6_marcar_lanza(montaje, caplog) -> None:
    fabrica = FabricaSesionSqlite()
    cliente, cola, _f, ids = montaje(
        _uno, fabrica=fabrica, repositorio=RepoMarcarFalla(fabrica))
    with caplog.at_level(logging.WARNING):
        r = _casar(cliente)
    assert r.status_code == 200 and r.json()["recalculo"] == "pedido"
    assert len(cola.enviados) == 1
    assert datos_registros(fabrica, ids)[ids[0]]["empleado_ide"] == 4242
    assert _warnings(caplog, "no se pudo marcar el pedido compartido")


def test_f068_conciliar_r6_anular_lanza(montaje, caplog) -> None:
    fabrica = FabricaSesionSqlite()
    cliente, _c, _f, ids = montaje(
        _uno, fabrica=fabrica, repositorio=RepoAnularFalla(fabrica),
        cola=ColaFake(error=RuntimeError("cola caida")))
    with caplog.at_level(logging.WARNING):
        r = _casar(cliente)
    assert r.status_code == 200 and r.json()["recalculo"] == "fallo"
    assert datos_registros(fabrica, ids)[ids[0]]["empleado_ide"] == 4242
    assert _warnings(caplog, "no se pudo anular el pedido compartido")


# ============ R7 · los errores de hoy, y solo esos, sin pedido ========== #

def test_f068_conciliar_r7_cuerpo_invalido_400(montaje) -> None:
    cliente, cola, fabrica, _ids = montaje(_uno)
    r = cliente.post("/api/conciliacion/confirmar", headers=CABECERA,
                     content=b"no-json")
    assert r.status_code == 400
    assert cola.enviados == [] and _sin_pedidos(fabrica)


def test_f068_conciliar_r7_trabajador_desconocido_404(montaje) -> None:
    cliente, cola, fabrica, _ids = montaje(_uno)
    r = cliente.post("/api/conciliacion/confirmar", headers=CABECERA,
                     json={"nombre_leido": LEIDO, "ide": 1})
    assert r.status_code == 404
    assert cola.enviados == [] and _sin_pedidos(fabrica)


class RepoBackfillFalla(ParteReviewRepository):
    def backfill_empleado(self, **_kw):
        raise RuntimeError("bbdd caida")


def test_f068_conciliar_r7_backfill_falla_500_sin_pedido(montaje) -> None:
    fabrica = FabricaSesionSqlite()
    cliente, cola, _f, _ids = montaje(
        _uno, fabrica=fabrica, repositorio=RepoBackfillFalla(fabrica))
    assert _casar(cliente).status_code == 500
    assert cola.enviados == [] and _sin_pedidos(fabrica)


class RepoAliasFalla(ParteReviewRepository):
    def upsert_empleado_alias(self, **_kw) -> None:
        raise RuntimeError("alias")


def test_f068_conciliar_r7_alias_falla_igual_pide(montaje) -> None:
    fabrica = FabricaSesionSqlite()
    cliente, cola, _f, _ids = montaje(
        _uno, fabrica=fabrica, repositorio=RepoAliasFalla(fabrica))
    r = _casar(cliente)
    assert r.status_code == 200
    assert r.json()["alias_ok"] is False and r.json()["recalculo"] == "pedido"
    assert len(cola.enviados) == 1


# ===================== R8 · el INFO, sin datos personales ============== #

def _infos(caplog, prefijo: str) -> list[str]:
    return [m.getMessage() for m in caplog.records
            if m.levelno == logging.INFO
            and m.getMessage().startswith(prefijo)]


def test_f068_conciliar_r8_info_sin_nombres(montaje, caplog) -> None:
    cliente, _cola, fabrica, _ids = montaje(_mezcla)
    with caplog.at_level(logging.INFO):
        _casar(cliente)
    texto, = _infos(caplog, "[conciliacion] casado")
    pedido = _pedido(fabrica, "d-1")
    assert texto == ("[conciliacion] casado updated=1 congeladas=1 "
                     f"documentos=['d-1'] pedido={pedido} recalculo=pedido")
    for prohibido in (LEIDO, NOMBRE_SIGRID, DNI_SIGRID):
        assert prohibido not in texto


def test_f068_conciliar_r8_sin_pedido_no_hay_info(montaje, caplog) -> None:
    cliente, _cola, _f, _ids = montaje(_solo_congeladas)
    with caplog.at_level(logging.INFO):
        _casar(cliente)
    assert _infos(caplog, "[conciliacion] casado") == []


# =========== R10 · un parte ya en espera: el pedido nuevo manda ========= #

def test_f068_conciliar_r10_sustituye_el_pedido_en_curso(montaje) -> None:
    cliente, _cola, fabrica, _ids = montaje(_uno)
    _poner_pedido(fabrica, "d-1", "pedido-viejo")
    assert _casar(cliente).json()["recalculo"] == "pedido"
    nuevo = _pedido(fabrica, "d-1")
    assert nuevo not in (None, "pedido-viejo")
    estados = cliente.get("/api/recalculo?ids=d-1").json()["estados"]
    assert estados["d-1"]["estado"] == "pendiente"


# ====== R9 · caracterización: el parte del casado queda en espera ======= #
# Pasan sin código nuevo de F-068 más allá de T6: la espera y el 409 son de
# F-043 (R38) y basta con que el casado marque el pedido.

def test_f068_r9_tras_casar_editar_el_parte_da_409(montaje) -> None:
    cliente, _cola, fabrica, ids = montaje(_uno)
    assert _casar(cliente).json()["recalculo"] == "pedido"
    antes = datos_registros(fabrica, ids)
    r = cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 3.0})
    assert r.status_code == 409, r.text
    assert r.json() == {"ok": False, "congelado": True,
                        "error": MOTIVO_RECALCULANDO}
    assert datos_registros(fabrica, ids) == antes


def test_f068_r9_tras_casar_el_parte_sale_recalculando(montaje) -> None:
    cliente, _cola, _f, _ids = montaje(_dos)
    _casar(cliente)
    estados = cliente.get("/api/recalculo?ids=d-1,d-2").json()["estados"]
    assert {d: e["estado"] for d, e in estados.items()} == {
        "d-1": "pendiente", "d-2": "pendiente"}


def test_f068_r9_sin_cola_el_parte_no_queda_en_espera(montaje) -> None:
    cliente, _cola, _f, ids = montaje(_uno, sin_cola=True)
    _casar(cliente)
    r = cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 3.0})
    assert r.status_code == 200, r.text


# ===== R11-R13 · el 422 de F-069 al aprobar tras un casado (E7) ======== #
# El pedido de recálculo no responde nunca 422: es una publicación en
# cola. El 422 posible es el de APROBAR con ids de una página cargada antes
# de la pasada, si la pasada borró una extra. (capa: integración)

MARZO = {"vista": "obra", "obra_key": "obr-10", "period": "2026-03",
         "mode": "nomina"}
TEXTO_F069 = ("1 línea(s) no son de esta vista: 1 ya no existen porque se "
              "están recalculando las extras. Recarga en unos segundos y "
              "vuelve a seleccionar")


def _con_extra(fabrica):
    """d-1 (obra 10, marzo): la línea sin casar y una extra que la
    pasada de sv3 borrará."""
    return _sin_casar(fabrica, [_libre(), {"estado": None, "tipo": "extra",
                                           "horas": 0.5,
                                           "leido": "Otro Distinto"}],
                      doc="d-1")


def _borrar_fila(fabrica, registro_id: int) -> None:
    """Lo que hace la pasada de sv3 con una extra que ya no toca."""
    with fabrica.create_session() as s:
        s.delete(s.get(ParteRegistroOrm, registro_id))
        s.commit()


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_f068_e7_r12_r13_aprobar_con_ids_viejos_es_422_y_no_toca_nada(
        montaje, endpoint) -> None:
    sv5 = Sv5Falso()
    cliente, cola, fabrica, ids = montaje(
        _con_extra, transfer_client=sv5, publisher=PublisherFalso(),
        calendario_provider=CalendarioFalso())
    casado = _casar(cliente)
    assert (casado.status_code, casado.json()["recalculo"]) == (200,
                                                                "pedido")
    pedido = _pedido(fabrica, "d-1")
    enviados = list(cola.enviados)
    _borrar_fila(fabrica, ids[1])
    r = cliente.post(endpoint, headers=CABECERA,
                     json={"registro_ids": ids, "ambito": MARZO})
    # R11: el 422 es el de aprobar (`_validar_ambito`), no del recálculo.
    assert r.status_code == 422, r.text
    cuerpo = r.json()
    assert (cuerpo["fuera_de_ambito"], cuerpo["inexistentes"]) == (1, 1)
    assert cuerpo["error"] == TEXTO_F069                      # R13
    # R12: el casado sigue intacto (empleado, alias y pedido)...
    assert datos_registros(fabrica, ids[:1])[ids[0]]["empleado_ide"] == 4242
    assert _alias(fabrica) == 4242
    assert _pedido(fabrica, "d-1") == pedido
    assert cola.enviados == enviados
    # ...y la aprobación no escribe nada.
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert estados_sigrid(fabrica, ids[:1]) == {ids[0]: (None, None, None, None, None)}
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "d-1").approved is False
