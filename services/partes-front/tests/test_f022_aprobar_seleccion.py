# tests/test_f022_aprobar_seleccion.py
"""F-022 · aprobar solo lo seleccionado: repositorio y endpoints de sv4.

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`) y
dobles de sv5, del publisher y del calendario. Obras, personas, DNIs y
codigos de parte SINTETICOS.

Bloques (los `-k` de tasks.md): `repo` (T2), `ambito` (T5), `preflight`
(T6), `ejecutar` (T7) y `encolar` (T8).
"""
from __future__ import annotations

import copy
import logging

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_parte
from tests.test_f003_r2_vistas_festivos import ProveedorFake

# Tres obras: dos con `obra_ide` y una solo con codigo. Sus claves
# (`obra_key_for_registro`) ordenadas: cod-0300 < obr-10 < obr-20.
OBRA_10 = {"ide": 10, "codigo": "0100", "nombre": "Obra Uno"}
OBRA_20 = {"ide": 20, "codigo": "0200", "nombre": "Obra Uno"}
OBRA_300 = {"ide": None, "codigo": "0300", "nombre": "Obra Uno"}


def _sembrar(fabrica, obra: dict, estados: list, *, doc: str,
             fecha: str = "2026-03-02", **kw) -> list[int]:
    return sembrar_parte(fabrica, [{"estado": e} for e in estados],
                         document_id=doc, fecha=fecha,
                         obra_ide=obra["ide"], obra_codigo=obra["codigo"],
                         **kw)


def _tres_obras():
    """obr-20: [nueva, error]; obr-10: [nueva, registrado];
    cod-0300: [borrado_sigrid, nueva]. Todas de la persona emp-77."""
    fabrica = FabricaSesionSqlite()
    a = _sembrar(fabrica, OBRA_20, [None, "error"], doc="doc-a")
    b = _sembrar(fabrica, OBRA_10, [None, "registrado"], doc="doc-b",
                 fecha="2026-03-03")
    c = _sembrar(fabrica, OBRA_300, ["borrado_sigrid", None], doc="doc-c",
                 fecha="2026-03-04")
    return ParteReviewRepository(fabrica), fabrica, a, b, c


# ===================================================================== #
# T2 · repositorio: registro_ids_de_trabajador, grupos, excluidas_detalle
# ===================================================================== #

def test_f022_r10_repo_ids_de_trabajador_son_los_de_su_tabla() -> None:
    repo, fabrica, a, b, c = _tres_obras()
    otra = _sembrar(fabrica, OBRA_10, [None], doc="doc-otra",
                    empleado_ide=88, empleado_dni="00000001R")
    papelera = _sembrar(fabrica, OBRA_10, [None], doc="doc-pap",
                        doc_en_papelera=True)
    borrada = sembrar_parte(fabrica, [{"borrada": True}], document_id="doc-bo",
                            obra_ide=10, obra_codigo="0100")
    ids = repo.registro_ids_de_trabajador("emp-77")
    assert sorted(ids) == sorted(a + b + c)
    assert ids == [v.id for v in repo.get_worker("emp-77").registros]
    assert not set(ids) & set(otra + papelera + borrada)


def test_f022_r10_repo_ids_de_trabajador_inexistente_es_lista_vacia() -> None:
    repo, *_ = _tres_obras()
    assert repo.registro_ids_de_trabajador("emp-999") == []


def test_f022_r14_repo_grupos_uno_por_obra_en_orden_de_clave() -> None:
    repo, _f, a, b, c = _tres_obras()
    datos = repo.lineas_para_registro(a + b + c)
    grupos = datos["grupos"]
    assert [g["clave"] for g in grupos] == ["cod-0300", "obr-10", "obr-20"]
    assert [g["obra"] for g in grupos] == [OBRA_300, OBRA_10, OBRA_20]
    # Solo viajan las lineas que pasan F-024 R22 (sin registrado ni
    # borrado_sigrid), cada una en el grupo de SU obra.
    assert [[l["registro_id"] for l in g["lineas"]] for g in grupos] == [
        [c[1]], [b[0]], [a[0], a[1]]]
    assert grupos[2]["estado_previo"] == {a[0]: "", a[1]: "error"}
    assert grupos[1]["estado_previo"] == {b[0]: ""}


def test_f022_r14_repo_grupos_con_borradas_incluidas() -> None:
    repo, _f, _a, _b, c = _tres_obras()
    grupos = repo.lineas_para_registro(c, incluir_borradas=True)["grupos"]
    assert len(grupos) == 1
    assert [l["registro_id"] for l in grupos[0]["lineas"]] == c
    assert grupos[0]["estado_previo"] == {c[0]: "borrado_sigrid", c[1]: ""}


def test_f022_r14_repo_el_estado_previo_va_normalizado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, [" Error ", "ENCOLADO"], doc="doc-n")
    grupos = ParteReviewRepository(fabrica).lineas_para_registro(ids)["grupos"]
    assert grupos[0]["estado_previo"] == {ids[0]: "error", ids[1]: "encolado"}


def test_f022_r14_repo_los_planos_de_hoy_no_cambian() -> None:
    repo, _f, a, b, c = _tres_obras()
    datos = repo.lineas_para_registro(a + b + c)
    viajan = sorted(l["registro_id"] for g in datos["grupos"]
                    for l in g["lineas"])
    assert sorted(l["registro_id"] for l in datos["lineas"]) == viajan
    assert datos["excluidas"] == {"registrado": 1, "borrado_sigrid": 1}
    # R33: el estado previo no se cuela en las lineas del payload.
    for g in datos["grupos"]:
        for linea in g["lineas"]:
            assert "estado_previo" not in linea
            assert linea in datos["lineas"]


def test_f022_r14_repo_sin_lineas_no_hay_grupos() -> None:
    repo, _f, _a, b, _c = _tres_obras()
    assert repo.lineas_para_registro([])["grupos"] == []
    # Todo excluido: tampoco hay grupos.
    assert repo.lineas_para_registro([b[1]])["grupos"] == []


def test_f022_r14_repo_grupo_sin_obra_identificada_va_con_obra_vacia() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, {"ide": None, "codigo": None, "nombre": None},
                   [None], doc="doc-s")
    grupos = ParteReviewRepository(fabrica).lineas_para_registro(ids)["grupos"]
    assert grupos[0]["clave"] == "nom-OBRA_UNO"
    assert grupos[0]["obra"] == {}


def test_f022_r26_repo_excluidas_detalle() -> None:
    repo, fabrica, _a, b, c = _tres_obras()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, c[0]).sigrid_parte_cod = "PT26/00007"
        s.commit()
    detalle = repo.lineas_para_registro(b + c)["excluidas_detalle"]
    assert [d["registro_id"] for d in detalle] == [b[1], c[0]]
    reg, bor = detalle
    assert reg == {
        "registro_id": b[1], "fecha_int": 20260303, "nombre": "Pepe Perez",
        "obra_codigo": "0100", "horas": 8.0, "hora_codigo": "HL01",
        "estado": "registrado", "parte_cod": "PT26/00001",
        "motivo": "ya registrada en Sigrid (parte PT26/00001): no se reenvia",
    }
    assert bor["estado"] == "borrado_sigrid"
    assert bor["parte_cod"] == "PT26/00007"
    assert bor["motivo"] == (
        "borrada en Sigrid: para reenviarla marca «Incluir las borradas en "
        "Sigrid» o usa «Reaprobar»")


def test_f022_r26_repo_excluida_sin_parte_conocido() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, ["registrado"], doc="doc-x")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).sigrid_parte_cod = None
        s.commit()
    detalle = ParteReviewRepository(fabrica).lineas_para_registro(ids)[
        "excluidas_detalle"]
    assert detalle[0]["motivo"] == ("ya registrada en Sigrid (parte ?): no "
                                    "se reenvia")


def test_f022_r26_repo_excluida_sin_fecha_va_con_cero() -> None:
    """Sin fecha, `fecha_int` es 0 (como en las lineas que viajan): el
    navegador la pinta vacia y ordena al principio."""
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, ["registrado"], doc="doc-sf")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).fecha_int = None
        s.commit()
    detalle = ParteReviewRepository(fabrica).lineas_para_registro(ids)[
        "excluidas_detalle"]
    assert detalle[0]["fecha_int"] == 0


def test_f022_r26_repo_excluida_con_el_nombre_casado() -> None:
    """El nombre es el del empleado casado; el leido solo si no lo hay."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"estado": "registrado", "leido": "Leido X"},
                                  {"estado": "registrado", "leido": "Leido Y"}],
                        document_id="doc-n", obra_ide=10, obra_codigo="0100")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[1]).empleado_nombre = None
        s.commit()
    detalle = ParteReviewRepository(fabrica).lineas_para_registro(ids)[
        "excluidas_detalle"]
    assert [d["nombre"] for d in detalle] == ["Pepe Perez", "Leido Y"]


def test_f022_r14_repo_la_obra_del_grupo_es_la_de_su_primera_linea() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, OBRA_10, [None, None], doc="doc-o")
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[1]).obra_codigo = "0100-bis"
        s.commit()
    grupos = ParteReviewRepository(fabrica).lineas_para_registro(ids)["grupos"]
    assert len(grupos) == 1
    assert grupos[0]["obra"] == OBRA_10


def test_f022_r26_repo_con_borradas_incluidas_no_hay_detalle_de_ellas() -> None:
    repo, _f, _a, _b, c = _tres_obras()
    assert repo.lineas_para_registro(
        c, incluir_borradas=True)["excluidas_detalle"] == []


# ===================================================================== #
# Dobles de los endpoints: sv5, publisher y calendario
# ===================================================================== #

def _codigo(payload: dict) -> str | None:
    return (payload.get("obra") or {}).get("codigo")


class Sv5Falso:
    """sv5 por obra: `preflight_por_obra` / `ejecutar_por_obra` mapean el
    codigo de obra del payload a una respuesta, a una excepcion o a una
    funcion; sin entrada, la respuesta por defecto (todo se escribe)."""

    def __init__(self, preflight_por_obra=None, ejecutar_por_obra=None):
        self.preflights: list[dict] = []
        self.ejecutadas: list[dict] = []
        self._pf = preflight_por_obra or {}
        self._ej = ejecutar_por_obra or {}

    @staticmethod
    def _responder(tabla, payload, defecto):
        r = tabla.get(_codigo(payload))
        if isinstance(r, Exception):
            raise r
        if callable(r):
            return r(payload)
        return copy.deepcopy(r) if r is not None else defecto(payload)

    def preflight(self, payload: dict) -> dict:
        self.preflights.append(copy.deepcopy(payload))
        return self._responder(self._pf, payload, pf_por_defecto)

    def ejecutar(self, payload: dict) -> dict:
        self.ejecutadas.append(copy.deepcopy(payload))
        return self._responder(self._ej, payload, ej_por_defecto)

    def comprobar(self, payload: dict, *, timeout_s: float) -> dict:
        return {"ok": True, "veredictos": []}


def pf_por_defecto(payload: dict) -> dict:
    lineas = payload["lineas"]
    return {
        "ok": True, "obra_destino": payload["obra"], "forzada_pruebas": False,
        "partes": [{"ano": 2026, "mes": 3, "existe": False,
                    "cod": f"PT-{_codigo(payload)}"}],
        "acciones": [{"registro_id": l["registro_id"], "accion": "escribir",
                      "fecha_int": l["fecha_int"], "nombre": l["nombre"],
                      "hora_codigo": l["hora_codigo"], "can": l["horas"],
                      "recurso_ide": l["recurso_ide"]} for l in lineas],
        "conflictos": [],
        "resumen": {"escribir": len(lineas), "omitir": 0, "ya_registrado": 0,
                    "conflictos": 0},
    }


def ej_por_defecto(payload: dict) -> dict:
    return {
        "ok": True, "obra_destino": payload["obra"], "forzada_pruebas": False,
        "partes": [{"cod": f"PT-{_codigo(payload)}", "creado": True}],
        "escritas": [{"registro_id": l["registro_id"], "hmoide": 900,
                      "hmores_ide": 1000 + l["registro_id"],
                      "parte_cod": f"PT-{_codigo(payload)}"}
                     for l in payload["lineas"]],
        "omitidas": [], "ya_registradas": [],
        "pisadas": list(payload["pisar_claves"]), "borradas": 0,
        "pendientes_confirmacion": [],
    }


class PublisherFalso:
    def __init__(self, fallan=()) -> None:
        self.publicadas: list[tuple[dict, str | None]] = []
        self._fallan = set(fallan)

    def publicar(self, payload: dict, usuario: str | None = None) -> str:
        if _codigo(payload) in self._fallan:
            raise RuntimeError("cola caida")
        self.publicadas.append((copy.deepcopy(payload), usuario))
        return f"peticion-{len(self.publicadas)}"


class CalendarioFalso(ProveedorFake):
    """Sesame no fiable solo para los DNIs de `no_fiables`."""

    def __init__(self, no_fiables=()) -> None:
        super().__init__(por_dni={}, por_defecto=set())
        self._no_fiables = set(no_fiables)

    def fiable_para(self, consultas):
        consultas = list(consultas)
        self.consultas.append(("fiable_para", sorted(
            (str(d), a) for d, a in consultas)))
        return not any(d in self._no_fiables for d, _a in consultas)


DNI_A = "12345678Z"      # emp-77
DNI_B = "00000001R"      # emp-88
MARZO = {"vista": "obra", "obra_key": "obr-10", "period": "2026-03",
         "mode": "nomina"}
PERSONA_A = {"vista": "trabajador", "worker_key": "emp-77"}
ENDPOINTS = ("/api/aprobar/preflight", "/api/aprobar/ejecutar",
             "/api/aprobar/encolar")


def _escenario(fabrica) -> dict[str, list[int]]:
    """obr-10 · marzo: 2 de A y 1 de B; obr-10 · abril: 1 de A; obr-20 ·
    marzo: 2 de A (una `error`); obr-10 · marzo: 1 de A en la papelera."""
    return {
        "o10_a": _sembrar(fabrica, OBRA_10, [None, None], doc="d-10a"),
        "o10_b": _sembrar(fabrica, OBRA_10, [None], doc="d-10b",
                          fecha="2026-03-04", empleado_ide=88,
                          empleado_dni=DNI_B, empleado_nombre="Persona B"),
        "o10_abril": _sembrar(fabrica, OBRA_10, [None], doc="d-10abr",
                              fecha="2026-04-02"),
        "o20_a": _sembrar(fabrica, OBRA_20, [None, "error"], doc="d-20a",
                          fecha="2026-03-03"),
        "papelera": sembrar_parte(fabrica, [{"borrada": True}],
                                  document_id="d-pap", obra_ide=10,
                                  obra_codigo="0100"),
    }


@pytest.fixture
def portal(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)

    def _levantar(*, sv5=None, publisher="si", calendario=None, env=None):
        for clave, valor in (env or {}).items():
            monkeypatch.setenv(clave, valor)
        fabrica = FabricaSesionSqlite()
        ids = _escenario(fabrica)
        sv5 = sv5 or Sv5Falso()
        if publisher == "si":
            publisher = PublisherFalso()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=publisher,
                        calendario_provider=calendario or CalendarioFalso())
        return TestClient(app), fabrica, ids, sv5, publisher
    return _levantar


def _todos(ids: dict) -> list[int]:
    return [i for v in ids.values() for i in v]


# ===================================================================== #
# T5 · R10-R13 · el ambito de la vista
# ===================================================================== #

def test_f022_r10_ambito_obra_sigue_solo_con_los_pedidos(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"][:1], "ambito": MARZO})
    assert r.status_code == 200
    assert [[l["registro_id"] for l in p["lineas"]]
            for p in sv5.preflights] == [ids["o10_a"][:1]]


def test_f022_r10_ambito_obra_sin_periodo_usa_el_de_la_vista(portal) -> None:
    """Sin `period`, la vista de obra abre el periodo mas reciente."""
    cliente, _f, ids, _sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_abril"],
        "ambito": {"vista": "obra", "obra_key": "obr-10"}})
    assert r.status_code == 200
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"],
        "ambito": {"vista": "obra", "obra_key": "obr-10", "period": None,
                   "mode": None}})
    assert r.status_code == 422


def test_f022_r10_ambito_obra_respeta_el_modo_natural(portal) -> None:
    """2026-03-02 es de marzo en natural y de marzo en nomina; el 04-02,
    de abril en los dos. El modo viaja hasta la consulta de la vista."""
    cliente, fabrica, _ids, _sv5, _p = portal()
    tardia = _sembrar(fabrica, OBRA_10, [None], doc="d-10-20mar",
                      fecha="2026-03-20")
    nomina = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": tardia, "ambito": MARZO})
    natural = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": tardia, "ambito": dict(MARZO, mode="natural")})
    assert nomina.status_code == 422          # nomina: va a abril
    assert natural.status_code == 200


def test_f022_r10_ambito_persona_es_toda_su_tabla(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    pedidos = ids["o10_a"] + ids["o10_abril"] + ids["o20_a"]
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": pedidos, "ambito": PERSONA_A})
    assert r.status_code == 200
    assert sorted(l["registro_id"] for p in sv5.preflights
                  for l in p["lineas"]) == sorted(pedidos)


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("intruso,ambito", [
    ("o20_a", MARZO),               # otra obra
    ("o10_abril", MARZO),           # otro periodo
    ("o10_b", PERSONA_A),           # otra persona
    ("papelera", MARZO),            # en la papelera
    ("papelera", PERSONA_A),
])
def test_f022_r11_ambito_id_ajeno_es_422_sin_tocar_nada(
        portal, endpoint, intruso, ambito) -> None:
    cliente, fabrica, ids, sv5, publisher = portal()
    antes = estados_sigrid(fabrica, _todos(ids))
    r = cliente.post(endpoint, json={
        "registro_ids": ids["o10_a"] + ids[intruso][:1], "ambito": ambito})
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert r.json()["fuera_de_ambito"] == 1
    assert "no son de esta vista" in r.json()["error"]
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []
    assert estados_sigrid(fabrica, _todos(ids)) == antes


def test_f022_r11_ambito_cuenta_todos_los_ids_ajenos(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o20_a"] + [999999] + ids["o10_a"],
        "ambito": MARZO})
    assert r.status_code == 422
    assert r.json()["fuera_de_ambito"] == 3
    assert sv5.preflights == []


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("ambito,ids_fn,texto", [
    ({"vista": "parte", "obra_key": "obr-10"}, lambda i: i["o10_a"],
     "vista desconocida"),
    ({"obra_key": "obr-10"}, lambda i: i["o10_a"], "vista desconocida"),
    ("obra", lambda i: i["o10_a"], "ambito no valido"),
    ({"vista": "obra"}, lambda i: i["o10_a"], "falta obra_key"),
    ({"vista": "obra", "obra_key": "  "}, lambda i: i["o10_a"],
     "falta obra_key"),
    ({"vista": "trabajador", "obra_key": "obr-10"}, lambda i: i["o10_a"],
     "falta worker_key"),
    (MARZO, lambda i: [], "no hay lineas seleccionadas"),
    (MARZO, lambda i: list(range(1, 5002)), "el maximo es 5000"),
])
def test_f022_r12_ambito_mal_formado_es_422_sin_sv5(
        portal, endpoint, ambito, ids_fn, texto) -> None:
    cliente, fabrica, ids, sv5, publisher = portal()
    antes = estados_sigrid(fabrica, _todos(ids))
    r = cliente.post(endpoint, json={"registro_ids": ids_fn(ids),
                                     "ambito": ambito})
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert texto in r.json()["error"]
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []
    assert estados_sigrid(fabrica, _todos(ids)) == antes


def test_f022_r12_ambito_5000_ids_es_el_limite_admitido(portal) -> None:
    """5000 se admite (llega a la validacion de ambito); 5001 no."""
    cliente, _f, ids, _sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"] + list(range(100000, 104998)),
        "ambito": MARZO})
    assert r.status_code == 422
    assert r.json()["fuera_de_ambito"] == 4998


def test_f022_r12_ambito_los_ids_repetidos_cuentan_una_vez(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "registro_ids": ids["o10_a"] * 3000, "ambito": MARZO})
    assert r.status_code == 200
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == \
        ids["o10_a"]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("raros", [["x"], [[1]], [{"id": 1}]])
def test_f022_r12_ambito_ids_no_numericos_son_422(portal, endpoint,
                                                  raros) -> None:
    cliente, _f, _ids, sv5, _p = portal()
    r = cliente.post(endpoint, json={"registro_ids": raros, "ambito": MARZO})
    assert r.status_code == 422
    assert r.json()["error"] == "registro_ids no validos"
    assert r.json()["ok"] is False
    assert sv5.preflights == [] and sv5.ejecutadas == []


def test_f022_r13_ambito_ausente_con_obra_key_heredado(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={
        "obra_key": "obr-10", "period": "2026-03", "mode": "nomina"})
    assert r.status_code == 200
    assert sorted(l["registro_id"] for l in sv5.preflights[0]["lineas"]) == \
        sorted(ids["o10_a"] + ids["o10_b"])


def test_f022_r13_ambito_ausente_sin_ids_ni_obra_es_422(portal) -> None:
    cliente, _f, _ids, _sv5, _p = portal()
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": []})
    assert r.status_code == 422
    assert r.json()["error"] == "faltan registro_ids u obra_key"


# ===================================================================== #
# T6 · preflight por grupo (R14-R18, R23-R26, R31)
# ===================================================================== #

def _preflight(cliente, ids, **extra):
    return cliente.post("/api/aprobar/preflight",
                        json=dict({"registro_ids": ids}, **extra))


def test_f022_r14_preflight_una_llamada_a_sv5_por_obra(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = _preflight(cliente, ids["o20_a"] + ids["o10_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    assert [p["obra"] for p in sv5.preflights] == [OBRA_10, OBRA_20]
    assert [[l["registro_id"] for l in p["lineas"]]
            for p in sv5.preflights] == [ids["o10_a"], ids["o20_a"]]
    grupos = r.json()["grupos"]
    assert [g["clave"] for g in grupos] == ["obr-10", "obr-20"]
    assert [g["obra"] for g in grupos] == [OBRA_10, OBRA_20]
    assert [g["registro_ids"] for g in grupos] == [ids["o10_a"],
                                                    ids["o20_a"]]


def test_f022_r13_preflight_sin_vista_reparte_por_obra(portal) -> None:
    """Sin `ambito` no se valida la vista (JS en cache, botones por linea):
    los ids van tal cual, ya repartidos por obra (§D)."""
    cliente, _f, ids, sv5, _p = portal()
    r = _preflight(cliente, ids["o10_b"] + ids["o20_a"], ambito=None)
    assert r.status_code == 200
    assert [_codigo(p) for p in sv5.preflights] == ["0100", "0200"]


def _sembrar_obras(fabrica, n: int) -> list[int]:
    """`n` obras mas (ide 101..) de la persona A, una linea cada una."""
    ids: list[int] = []
    for k in range(n):
        ids += _sembrar(fabrica, {"ide": 101 + k, "codigo": f"09{k:02d}"},
                        [None], doc=f"d-x{k}")
    return ids


def test_f022_r15_preflight_mas_de_diez_obras_es_422_con_desglose(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal()
    extra = _sembrar_obras(fabrica, 9)                 # 2 + 9 = 11 obras
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"] + extra,
                   ambito=PERSONA_A)
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == ("la aprobacion abarca 11 obras y el maximo "
                               "es 10: filtra la tabla o selecciona menos "
                               "obras")
    assert len(cuerpo["obras"]) == 11
    assert cuerpo["obras"][0] == {"clave": "obr-10", "codigo": "0100",
                                  "nombre": "Obra Uno", "lineas": 2}
    assert cuerpo["obras"][-1]["clave"] == "obr-20"
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    assert sv5.preflights == []


def test_f022_r15_preflight_diez_obras_si_se_admiten(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal()
    extra = _sembrar_obras(fabrica, 8)                 # 2 + 8 = 10 obras
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"] + extra,
                   ambito=PERSONA_A)
    assert r.status_code == 200
    assert len(sv5.preflights) == 10


def test_f022_r15_preflight_el_tope_sale_de_la_configuracion(portal) -> None:
    cliente, _f, ids, sv5, _p = portal(env={"APROBACION_MAX_OBRAS": "1"})
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 422
    assert "el maximo es 1:" in r.json()["error"]
    assert sv5.preflights == []


@pytest.mark.parametrize("valor,valido", [("0", False), ("1", True),
                                          ("50", True), ("51", False)])
def test_f022_r15_preflight_tope_de_obras_entre_1_y_50(
        monkeypatch, valor, valido) -> None:
    monkeypatch.setenv("PG_PASSWORD", "x")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "x")
    monkeypatch.setenv("APROBACION_MAX_OBRAS", valor)
    if valido:
        assert Settings(_env_file=None).aprobacion_max_obras == int(valor)
    else:
        with pytest.raises(ValueError):
            Settings(_env_file=None)


def test_f022_r15_preflight_tope_por_defecto(monkeypatch) -> None:
    monkeypatch.setenv("PG_PASSWORD", "x")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "x")
    monkeypatch.delenv("APROBACION_MAX_OBRAS", raising=False)
    assert Settings(_env_file=None).aprobacion_max_obras == 10


def test_f022_r16_preflight_un_grupo_planos_identicos_a_hoy(portal) -> None:
    respuesta = {"ok": True, "obra_destino": {"codigo": "0404"},
                 "forzada_pruebas": True, "partes": [{"cod": "PT26/00009"}],
                 "acciones": [], "conflictos": [], "escribir": 2,
                 "resumen": {"escribir": 2}}
    cliente, _f, ids, _sv5, _p = portal(
        sv5=Sv5Falso(preflight_por_obra={"0100": respuesta}))
    cuerpo = _preflight(cliente, ids["o10_a"], ambito=MARZO).json()
    for clave, valor in respuesta.items():
        assert cuerpo[clave] == valor
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    assert cuerpo["avisos_calendario"] == []
    assert cuerpo["umbral_plegado"] == 40
    assert cuerpo["excluidas_detalle"] == []
    assert "sesame_bloqueo" not in cuerpo
    for clave in ("clave", "obra", "registro_ids", "listado"):
        assert clave not in cuerpo
    assert cuerpo["totales"] == cuerpo["grupos"][0]["totales"]
    assert len(cuerpo["grupos"]) == 1


def test_f022_r17_preflight_un_grupo_fallido_y_el_otro_sigue(portal) -> None:
    cliente, _f, ids, sv5, _p = portal(sv5=Sv5Falso(preflight_por_obra={
        "0100": {"ok": False, "error": "sigrid-api caido"}}))
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    malo, bueno = cuerpo["grupos"]
    assert (malo["ok"], malo["error"]) == (False, "sigrid-api caido")
    assert {f["estado"] for f in malo["listado"]} == {"no_se_registra"}
    assert bueno["ok"] is True
    assert cuerpo["obra_destino"] == OBRA_20
    assert len(sv5.preflights) == 2


def test_f022_r17_preflight_una_excepcion_de_sv5_solo_tumba_su_grupo(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal(sv5=Sv5Falso(preflight_por_obra={
        "0200": RuntimeError("se corto la conexion")}))
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    bueno, malo = r.json()["grupos"]
    assert bueno["ok"] is True
    assert malo["ok"] is False
    assert malo["error"] == ("no se pudo evaluar la obra: se corto la "
                             "conexion")


def test_f022_r17_preflight_todos_fallidos(portal) -> None:
    caido = {"ok": False, "error": "caido"}
    cliente, _f, ids, _sv5, _p = portal(sv5=Sv5Falso(preflight_por_obra={
        "0100": caido, "0200": caido}))
    cuerpo = _preflight(cliente, ids["o10_a"] + ids["o20_a"],
                        ambito=PERSONA_A).json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == ("ninguna obra se pudo evaluar: 0100: caido; "
                               "0200: caido")


def test_f022_r18_preflight_sesame_no_fiable_solo_en_un_grupo(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    cuerpo = _preflight(cliente, ids["o10_b"] + ids["o20_a"]).json()
    o10, o20 = cuerpo["grupos"]
    assert o10["sesame_bloqueo"]
    assert "sesame_bloqueo" not in o20
    assert cuerpo["sesame_bloqueo"] == o10["sesame_bloqueo"]


def test_f022_r31_preflight_avisos_y_bloqueo_solo_de_lo_pedido(portal) -> None:
    """La vista tiene una linea de B (Sesame caido) y una en domingo; si no
    se piden, ni bloquean ni avisan, aunque sean de la misma obra."""
    cliente, fabrica, ids, sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    domingo = _sembrar(fabrica, OBRA_10, [None], doc="d-dom",
                       fecha="2026-03-01")
    cuerpo = _preflight(cliente, ids["o10_a"], ambito=MARZO).json()
    assert "sesame_bloqueo" not in cuerpo
    assert cuerpo["avisos_calendario"] == []
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == \
        ids["o10_a"]
    cuerpo = _preflight(cliente, ids["o10_a"] + domingo,
                        ambito=MARZO).json()
    assert [a["registro_id"] for a in cuerpo["avisos_calendario"]] == domingo
    assert [a["registro_id"] for a in
            cuerpo["grupos"][0]["avisos_calendario"]] == domingo


def test_f022_r31_preflight_lo_excluido_no_viaja(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal()
    reg = _sembrar(fabrica, OBRA_10, ["registrado"], doc="d-reg")
    cuerpo = _preflight(cliente, ids["o10_a"] + reg, ambito=MARZO).json()
    assert [l["registro_id"] for l in sv5.preflights[0]["lineas"]] == \
        ids["o10_a"]
    assert cuerpo["excluidas"] == {"registrado": 1, "borrado_sigrid": 0}
    assert [d["registro_id"] for d in cuerpo["excluidas_detalle"]] == reg
    assert cuerpo["excluidas_detalle"][0]["motivo"].startswith(
        "ya registrada en Sigrid")


def test_f022_r23_preflight_listado_y_totales_por_grupo(portal) -> None:
    def con_conflicto(payload):
        pf = pf_por_defecto(payload)
        rid = payload["lineas"][0]["registro_id"]
        pf["conflictos"] = [{"clave": "501|20260303|1", "registros": [rid],
                             "parte_cod": "PT26/00004"}]
        pf["acciones"][1]["hora_codigo"] = "HX99"
        return pf
    cliente, _f, ids, _sv5, _p = portal(sv5=Sv5Falso(preflight_por_obra={
        "0200": con_conflicto}))
    cuerpo = _preflight(cliente, ids["o10_a"] + ids["o20_a"],
                        ambito=PERSONA_A).json()
    o10, o20 = cuerpo["grupos"]
    assert [f["estado"] for f in o10["listado"]] == ["nuevo", "nuevo"]
    assert [(f["registro_id"], f["estado"], f["hora_codigo"])
            for f in o20["listado"]] == [
        (ids["o20_a"][0], "conflicto", "HL01"),
        (ids["o20_a"][1], "reaprobacion", "HX99")]
    assert o20["listado"][1]["motivo"] == "antes: error"
    assert o20["totales"] == {"lineas": 2, "por_estado": {
        "conflicto": 1, "reaprobacion": 1}, "horas_ordinarias": 16.0,
        "horas_extra": 0.0, "incidencias": 0}
    assert cuerpo["totales"] == {"lineas": 4, "por_estado": {
        "nuevo": 2, "conflicto": 1, "reaprobacion": 1},
        "horas_ordinarias": 32.0, "horas_extra": 0.0, "incidencias": 0}
    assert cuerpo["umbral_plegado"] == 40
    assert set(o10["listado"][0]) == {
        "registro_id", "fecha_int", "nombre", "tipo", "hora_codigo",
        "horas", "partida_cod", "recurso_ide", "estado", "motivo"}


def test_f022_r19_preflight_claves_sin_grupo_con_varias_obras_es_422(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = _preflight(cliente, ids["o10_a"] + ids["o20_a"],
                   pisar_claves=["501|20260302|1"])
    assert r.status_code == 422
    assert sv5.preflights == []


def test_f022_r33_preflight_payload_de_siempre(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    _preflight(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A,
               incluir_borradas=True)
    for p in sv5.preflights:
        assert set(p) == {"obra", "lineas", "pisar_claves", "usuario"}
        assert p["pisar_claves"] == []
        for linea in p["lineas"]:
            assert "estado_previo" not in linea


# ===================================================================== #
# T7 · ejecutar por grupo (R18, R19, R22, R32, R33)
# ===================================================================== #

MOTIVO_SIN_SESAME_PREFIJO = "[SIN-SESAME]"


def _ejecutar(cliente, ids, **extra):
    return cliente.post("/api/aprobar/ejecutar",
                        json=dict({"registro_ids": ids}, **extra))


def test_f022_r19_ejecutar_cada_grupo_recibe_solo_sus_claves(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    r = _ejecutar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A,
                  pisar_claves=["obr-20::502|20260303|1", "obr-10::k1",
                                "obr-99::kx"])
    assert r.status_code == 200
    assert [(_codigo(p), p["pisar_claves"]) for p in sv5.ejecutadas] == [
        ("0100", ["k1"]), ("0200", ["502|20260303|1"])]


def test_f022_r19_ejecutar_claves_sin_grupo_con_varias_obras_es_422(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal()
    antes = estados_sigrid(fabrica, _todos(ids))
    r = _ejecutar(cliente, ids["o10_a"] + ids["o20_a"],
                  pisar_claves=["obr-10::k1", "501|20260302|1"])
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert r.json()["error"] == ("con varias obras, cada clave que pisar "
                                 "tiene que llevar su obra "
                                 "(<obra>::<clave>)")
    assert sv5.ejecutadas == []
    assert estados_sigrid(fabrica, _todos(ids)) == antes


def test_f022_r19_ejecutar_claves_sin_grupo_con_una_obra_van_a_ella(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    _ejecutar(cliente, ids["o10_a"], pisar_claves=["501|20260302|1"])
    assert sv5.ejecutadas[0]["pisar_claves"] == ["501|20260302|1"]


def test_f022_r22_ejecutar_obras_en_orden_y_cada_una_con_su_traza(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal()
    r = _ejecutar(cliente, ids["o20_a"] + ids["o10_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    assert [_codigo(p) for p in sv5.ejecutadas] == ["0100", "0200"]
    estados = estados_sigrid(fabrica, ids["o10_a"] + ids["o20_a"])
    assert {rid: e[4] for rid, e in estados.items()} == dict(
        [(rid, "PT-0100") for rid in ids["o10_a"]]
        + [(rid, "PT-0200") for rid in ids["o20_a"]])
    assert {e[0] for e in estados.values()} == {"registrado"}
    cuerpo = r.json()
    assert (cuerpo["ok"], cuerpo["parcial"]) == (True, False)
    assert [g["clave"] for g in cuerpo["grupos"]] == ["obr-10", "obr-20"]
    assert [g["registro_ids"] for g in cuerpo["grupos"]] == [
        ids["o10_a"], ids["o20_a"]]
    assert len(cuerpo["escritas"]) == 4


def test_f022_r22_ejecutar_un_grupo_mal_solo_deja_en_error_sus_lineas(portal) -> None:
    cliente, fabrica, ids, _sv5, _p = portal(sv5=Sv5Falso(ejecutar_por_obra={
        "0100": {"ok": False, "error": "sigrid-api caido"}}))
    r = _ejecutar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    cuerpo = r.json()
    assert (cuerpo["ok"], cuerpo["parcial"]) == (False, True)
    assert cuerpo["error"] == "0100: sigrid-api caido"
    estados = estados_sigrid(fabrica, ids["o10_a"] + ids["o20_a"])
    assert [estados[i][:2] for i in ids["o10_a"]] == [
        ("error", "sigrid-api caido")] * 2
    assert [estados[i][0] for i in ids["o20_a"]] == ["registrado"] * 2
    assert [g["ok"] for g in cuerpo["grupos"]] == [False, True]


def test_f022_r22_ejecutar_una_excepcion_no_para_a_las_demas_obras(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(sv5=Sv5Falso(ejecutar_por_obra={
        "0100": RuntimeError("se corto")}))
    r = _ejecutar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    assert len(sv5.ejecutadas) == 2
    malo = r.json()["grupos"][0]
    assert malo["error"] == "no se pudo registrar la obra: se corto"
    estados = estados_sigrid(fabrica, ids["o10_a"] + ids["o20_a"])
    assert [estados[i][0] for i in ids["o10_a"]] == ["error"] * 2
    assert [estados[i][0] for i in ids["o20_a"]] == ["registrado"] * 2


def test_f022_r16_ejecutar_un_grupo_planos_identicos_a_hoy(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal()
    cuerpo = _ejecutar(cliente, ids["o10_a"], ambito=MARZO).json()
    esperado = ej_por_defecto({"obra": OBRA_10, "pisar_claves": [],
                               "lineas": [{"registro_id": i}
                                          for i in ids["o10_a"]]})
    for clave, valor in esperado.items():
        assert cuerpo[clave] == valor
    assert cuerpo["parcial"] is False
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    for clave in ("clave", "obra", "registro_ids"):
        assert clave not in cuerpo


def test_f022_r18_ejecutar_grupo_bloqueado_sin_override_no_se_envia(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    antes = estados_sigrid(fabrica, ids["o10_b"])
    r = _ejecutar(cliente, ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 200
    assert [_codigo(p) for p in sv5.ejecutadas] == ["0200"]
    bloqueado, bueno = r.json()["grupos"]
    assert bloqueado == {"clave": "obr-10", "obra": OBRA_10,
                         "registro_ids": ids["o10_b"], "ok": False,
                         "bloqueado_sesame": True,
                         "error": "calendario Sesame no disponible: el "
                                  "calculo puede ser incorrecto"}
    assert bueno["ok"] is True
    assert (r.json()["ok"], r.json()["parcial"]) == (False, True)
    assert estados_sigrid(fabrica, ids["o10_b"]) == antes


def test_f022_r18_ejecutar_todos_bloqueados_es_el_422_de_hoy(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_A, DNI_B}))
    antes = estados_sigrid(fabrica, _todos(ids))
    r = _ejecutar(cliente, ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 422
    assert r.json() == {"ok": False,
                        "error": "calendario Sesame no disponible: el "
                                 "calculo puede ser incorrecto",
                        "sesame_bloqueo": "calendario Sesame no disponible: "
                                          "el calculo puede ser incorrecto"}
    assert sv5.ejecutadas == []
    assert estados_sigrid(fabrica, _todos(ids)) == antes


def test_f022_r18_ejecutar_override_solo_marca_los_bloqueados(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    r = _ejecutar(cliente, ids["o10_b"] + ids["o20_a"],
                  forzar_sin_sesame=True)
    assert r.status_code == 200
    assert len(sv5.ejecutadas) == 2
    estados = estados_sigrid(fabrica, ids["o10_b"] + ids["o20_a"])
    assert estados[ids["o10_b"][0]][1].startswith(MOTIVO_SIN_SESAME_PREFIJO)
    assert [estados[i][1] for i in ids["o20_a"]] == [None, None]


def test_f022_r18_ejecutar_bloqueo_y_override_quedan_en_el_log(
        portal, caplog) -> None:
    cliente, _f, ids, _sv5, _p = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    with caplog.at_level(logging.WARNING):
        _ejecutar(cliente, ids["o10_b"] + ids["o20_a"])
        _ejecutar(cliente, ids["o10_b"], forzar_sin_sesame=True)
    textos = [r.getMessage() for r in caplog.records]
    assert any("registro BLOQUEADO" in t and "obr-10" in t for t in textos)
    assert any("registro FORZADO por local:ana" in t and "obr-10" in t
               for t in textos)


def test_f022_r32_ejecutar_lo_no_pedido_no_cambia(portal) -> None:
    cliente, fabrica, ids, _sv5, _p = portal()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["o20_a"][1]).sigrid_motivo = "fallo viejo"
        s.commit()
    resto = [i for i in _todos(ids) if i != ids["o10_a"][0]]
    antes = estados_sigrid(fabrica, resto)
    _ejecutar(cliente, ids["o10_a"][:1], ambito=MARZO)
    assert estados_sigrid(fabrica, resto) == antes
    assert estados_sigrid(fabrica, ids["o10_a"][:1])[ids["o10_a"][0]][0] == \
        "registrado"


def test_f022_r33_ejecutar_payload_de_siempre(portal) -> None:
    cliente, _f, ids, sv5, _p = portal()
    _ejecutar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A,
              pisar_claves=["obr-10::k1"])
    for p in sv5.ejecutadas:
        assert set(p) == {"obra", "lineas", "pisar_claves", "usuario"}
        assert p["usuario"] == "local:ana"


# ===================================================================== #
# T8 · encolar por grupo (R18, R20, R21, R32, R33)
# ===================================================================== #

def _encolar(cliente, ids, **extra):
    return cliente.post("/api/aprobar/encolar",
                        json=dict({"registro_ids": ids}, **extra))


def test_f022_r20_encolar_una_publicacion_por_obra(portal) -> None:
    cliente, fabrica, ids, sv5, publisher = portal()
    r = _encolar(cliente, ids["o20_a"] + ids["o10_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    assert [(_codigo(p), [l["registro_id"] for l in p["lineas"]], u)
            for p, u in publisher.publicadas] == [
        ("0100", ids["o10_a"], "local:ana"),
        ("0200", ids["o20_a"], "local:ana")]
    assert sv5.ejecutadas == []
    cuerpo = r.json()
    assert cuerpo == {
        "ok": True, "modo": "asincrono", "peticion_id": "peticion-1",
        "peticiones": ["peticion-1", "peticion-2"], "encoladas": 4,
        "registro_ids": ids["o10_a"] + ids["o20_a"],
        "excluidas": {"registrado": 0, "borrado_sigrid": 0},
        "grupos": [
            {"clave": "obr-10", "obra": OBRA_10,
             "registro_ids": ids["o10_a"], "ok": True, "estado": "encolado",
             "peticion_id": "peticion-1", "error": None},
            {"clave": "obr-20", "obra": OBRA_20,
             "registro_ids": ids["o20_a"], "ok": True, "estado": "encolado",
             "peticion_id": "peticion-2", "error": None}]}
    estados = estados_sigrid(fabrica, ids["o10_a"] + ids["o20_a"])
    assert {e[0] for e in estados.values()} == {"encolado"}


def test_f022_r21_encolar_si_falla_una_obra_las_demas_siguen(portal) -> None:
    cliente, fabrica, ids, _sv5, _p = portal(
        publisher=PublisherFalso(fallan={"0100"}))
    antes = estados_sigrid(fabrica, ids["o10_a"])
    r = _encolar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    cuerpo = r.json()
    malo, bueno = cuerpo["grupos"]
    assert malo == {"clave": "obr-10", "obra": OBRA_10,
                    "registro_ids": ids["o10_a"], "ok": False,
                    "estado": "error_cola", "peticion_id": None,
                    "error": "no se pudo encolar: cola caida"}
    assert bueno["estado"] == "encolado"
    assert cuerpo["peticiones"] == ["peticion-1"]
    assert cuerpo["registro_ids"] == ids["o20_a"]
    assert cuerpo["encoladas"] == 2
    assert estados_sigrid(fabrica, ids["o10_a"]) == antes
    assert {e[0] for e in estados_sigrid(fabrica, ids["o20_a"]).values()} \
        == {"encolado"}


def test_f022_r21_encolar_si_fallan_todas_es_502_sin_marcas(portal) -> None:
    cliente, fabrica, ids, _sv5, _p = portal(
        publisher=PublisherFalso(fallan={"0100", "0200"}))
    antes = estados_sigrid(fabrica, _todos(ids))
    r = _encolar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 502
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == ("no se pudo encolar ninguna obra: 0100: no "
                               "se pudo encolar: cola caida; 0200: no se "
                               "pudo encolar: cola caida")
    assert [g["estado"] for g in cuerpo["grupos"]] == ["error_cola"] * 2
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    assert estados_sigrid(fabrica, _todos(ids)) == antes


def test_f022_r21_encolar_falla_el_marcado_y_sigue_encolada(portal) -> None:
    """Ya esta en la cola: el resultado marcara las lineas al volver (el
    aviso con traza lo cubre `test_f002_mutantes`)."""
    _c, fabrica, ids, _sv5, publisher = portal()

    def roto(*_a, **_kw):
        raise RuntimeError("PostgreSQL caido")
    repo = ParteReviewRepository(fabrica)
    repo.marcar_registros_encolado = roto
    app = build_app(Settings(_env_file=None), repository=repo,
                    transfer_client=Sv5Falso(), publisher=publisher,
                    calendario_provider=CalendarioFalso())
    r = TestClient(app).post("/api/aprobar/encolar", json={
        "registro_ids": ids["o10_a"] + ids["o20_a"]})
    assert r.status_code == 200
    assert [g["estado"] for g in r.json()["grupos"]] == ["encolado"] * 2
    assert len(publisher.publicadas) == 2


def test_f022_r18_encolar_grupo_bloqueado_no_se_publica(portal) -> None:
    cliente, fabrica, ids, _sv5, publisher = portal(
        calendario=CalendarioFalso(no_fiables={DNI_B}))
    antes = estados_sigrid(fabrica, ids["o10_b"])
    r = _encolar(cliente, ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 200
    assert [_codigo(p) for p, _u in publisher.publicadas] == ["0200"]
    bloqueado = r.json()["grupos"][0]
    assert bloqueado == {"clave": "obr-10", "obra": OBRA_10,
                         "registro_ids": ids["o10_b"], "ok": False,
                         "bloqueado_sesame": True,
                         "error": "calendario Sesame no disponible: el "
                                  "calculo puede ser incorrecto",
                         "estado": "bloqueado_sesame", "peticion_id": None}
    assert r.json()["registro_ids"] == ids["o20_a"]
    assert estados_sigrid(fabrica, ids["o10_b"]) == antes


def test_f022_r18_encolar_todos_bloqueados_es_el_422_de_hoy(portal) -> None:
    cliente, _f, ids, _sv5, publisher = portal(
        calendario=CalendarioFalso(no_fiables={DNI_A, DNI_B}))
    r = _encolar(cliente, ids["o10_b"] + ids["o20_a"])
    assert r.status_code == 422
    assert r.json()["sesame_bloqueo"] == ("calendario Sesame no disponible: "
                                          "el calculo puede ser incorrecto")
    assert "usa /api/aprobar/ejecutar" in r.json()["error"]
    assert publisher.publicadas == []


def test_f022_r20_encolar_sin_publisher_es_sincrono_por_obra(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(publisher=None)
    r = _encolar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["modo"] == "sincrono"
    assert (cuerpo["ok"], cuerpo["parcial"]) == (True, False)
    assert [_codigo(p) for p in sv5.ejecutadas] == ["0100", "0200"]
    assert [p["pisar_claves"] for p in sv5.ejecutadas] == [[], []]
    assert [g["clave"] for g in cuerpo["grupos"]] == ["obr-10", "obr-20"]
    assert cuerpo["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    estados = estados_sigrid(fabrica, ids["o10_a"] + ids["o20_a"])
    assert {e[0] for e in estados.values()} == {"registrado"}


def test_f022_r20_encolar_sin_publisher_un_grupo_es_como_hoy(portal) -> None:
    cliente, _f, ids, _sv5, _p = portal(publisher=None)
    cuerpo = _encolar(cliente, ids["o10_a"]).json()
    assert cuerpo["modo"] == "sincrono"
    assert cuerpo["parcial"] is False
    assert len(cuerpo["escritas"]) == 2
    assert "clave" not in cuerpo and "registro_ids" not in cuerpo


def test_f022_r20_encolar_sin_publisher_bloqueado_y_fallido(portal) -> None:
    cliente, fabrica, ids, sv5, _p = portal(
        publisher=None, calendario=CalendarioFalso(no_fiables={DNI_B}),
        sv5=Sv5Falso(ejecutar_por_obra={"0200": RuntimeError("caido")}))
    r = _encolar(cliente, ids["o10_b"] + ids["o20_a"] + ids["o10_a"])
    assert r.status_code == 200
    assert [_codigo(p) for p in sv5.ejecutadas] == ["0200"]
    cuerpo = r.json()
    assert cuerpo["ok"] is False
    # obr-10 mezcla A (fiable) y B (no): el grupo entero se bloquea.
    assert cuerpo["grupos"][0]["bloqueado_sesame"] is True
    assert [estados_sigrid(fabrica, ids["o20_a"])[i][0]
            for i in ids["o20_a"]] == ["error"] * 2


def test_f022_r32_encolar_lo_no_pedido_conserva_estado_y_motivo(portal) -> None:
    cliente, fabrica, ids, _sv5, _p = portal()
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, ids["o20_a"][1])
        reg.sigrid_motivo = "fallo viejo"
        s.commit()
    resto = [i for i in _todos(ids) if i not in ids["o10_a"]]
    antes = estados_sigrid(fabrica, resto)
    _encolar(cliente, ids["o10_a"], ambito=MARZO)
    assert estados_sigrid(fabrica, resto) == antes
    assert antes[ids["o20_a"][1]][:2] == ("error", "fallo viejo")


def test_f022_r33_encolar_publicacion_de_siempre_sin_listado(portal) -> None:
    cliente, _f, ids, _sv5, publisher = portal()
    _encolar(cliente, ids["o10_a"] + ids["o20_a"], ambito=PERSONA_A,
             incluir_borradas=True)
    for payload, _u in publisher.publicadas:
        assert set(payload) == {"obra", "lineas", "pisar_claves", "usuario"}
        assert payload["pisar_claves"] == []
        for linea in payload["lineas"]:
            assert "estado_previo" not in linea


def test_f022_r20_encolar_con_claves_sigue_siendo_422(portal) -> None:
    cliente, _f, ids, _sv5, publisher = portal()
    r = _encolar(cliente, ids["o10_a"], pisar_claves=["obr-10::k"])
    assert r.status_code == 422
    assert "usa /api/aprobar/ejecutar" in r.json()["error"]
    assert publisher.publicadas == []


# ===================================================================== #
# Los fallos de una obra quedan en el log CON su traza (exc_info)
# ===================================================================== #

def _avisos_con_traza(caplog, fragmento: str) -> list:
    return [r for r in caplog.records
            if fragmento in r.getMessage() and bool(r.exc_info)]


def test_f022_r17_preflight_el_fallo_de_una_obra_deja_traza(
        portal, caplog) -> None:
    cliente, _f, ids, _sv5, _p = portal(sv5=Sv5Falso(preflight_por_obra={
        "0100": RuntimeError("se corto")}))
    with caplog.at_level(logging.WARNING):
        _preflight(cliente, ids["o10_a"])
    assert _avisos_con_traza(caplog, "preflight de la obra obr-10 fallo")


def test_f022_r22_ejecutar_el_fallo_de_una_obra_deja_traza(
        portal, caplog) -> None:
    cliente, _f, ids, _sv5, _p = portal(sv5=Sv5Falso(ejecutar_por_obra={
        "0100": RuntimeError("se corto")}))
    with caplog.at_level(logging.WARNING):
        _ejecutar(cliente, ids["o10_a"])
    assert _avisos_con_traza(caplog, "registro de la obra obr-10 fallo")


def test_f022_r21_encolar_el_fallo_al_publicar_deja_traza(
        portal, caplog) -> None:
    cliente, _f, ids, _sv5, _p = portal(
        publisher=PublisherFalso(fallan={"0100"}))
    with caplog.at_level(logging.WARNING):
        _encolar(cliente, ids["o10_a"] + ids["o20_a"])
    assert _avisos_con_traza(caplog, "no se pudo encolar la obra obr-10")
