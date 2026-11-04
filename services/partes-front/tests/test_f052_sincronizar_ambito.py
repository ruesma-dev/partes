# tests/test_f052_sincronizar_ambito.py
"""F-052 en sv4: `SincronizadorAmbito.sincronizar` (design §2).

- R7: ámbito -> líneas del portal -> sv5 (con sus `registro_ids`) ->
  clasificar; sin escribir nada salvo R10.
- R10: un `registrado` sin pareja se confirma con `comprobar_ids`
  (`forzar`, origen `sincronizar`). DA18: en modo seco NO se llama; se
  pide a sv5 solo el veredicto y se informa en `marcaria_borrado_sigrid`.
- R12: `donde` de las `solo_sigrid_nuestra`.
- R13: recuento, periodo, hora y firma; un fallo de sv5 es error sin ítems.
- R15: claves que no permiten leer Sigrid ⇒ 422 sin leer nada.
- R29: candado por ámbito en el proceso.

Dobles del repositorio, de sv5 y de la comprobación; sin red ni base.
"""
from __future__ import annotations

import threading
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest
from application.services.congelacion import CongeladoError
from application.services.parte_vacio import DuplicadoActivoError
from application.services.sincronizacion import LineaPortal
from application.services.sincronizar_ambito import (
    Ambito,
    SincronizadorAmbito,
    lineas_de_sv5,
    motivo_no_sincronizable,
)

INSTANTE = datetime(2026, 11, 3, 9, 30, tzinfo=timezone.utc)
AMBITO_OBRA = {"vista": "obra", "obra_key": "obr-686", "period": "2026-10",
               "mode": "natural"}
AMBITO_PERSONA = {"vista": "trabajador", "worker_key": "rec-501",
                  "period": "2026-10", "mode": "nomina"}


def P(rid: int, estado: str | None = "registrado", **cambios) -> LineaPortal:
    base = dict(registro_id=rid, fecha_int=20261014, recurso_ide=501,
                obra_ide=686, horas=8.0, extra=False, es_incidencia=False,
                hora_codigo="HL01", partida_ide=11, partida_cod="P1",
                sigrid_estado=estado, sigrid_motivo=None,
                sigrid_hmores_ide=9000 + rid, sigrid_hmoide=7001)
    base.update(cambios)
    return LineaPortal(**base)


def S(ide: int, origen: str = "partes", registro_id: int | None = None,
      **cambios) -> dict:
    base = dict(hmores_ide=ide, hmoide=7001, parte_cod="PT26/00001",
                parte_est=1, obra_ide=686, obra_cod="0686", recurso_ide=501,
                fecha_int=20261014, hora_ide=3, hora_cod="HL01", hora_ext=0,
                partida_ide=11, partida_cod="P1", can=8.0, tot=120.0,
                enlazada=False, origen=origen, registro_id=registro_id,
                ajuste_id=None)
    base.update(cambios)
    return base


class RepoFalso:
    """Repositorio de lectura: apunta cada llamada. No tiene métodos que
    escriban: si alguien escribiera, el test rompería."""

    def __init__(self, portal=(), donde=None) -> None:
        self.portal = list(portal)
        self.donde = donde or {}
        self.llamadas: list[tuple[str, object]] = []

    def lineas_para_sincronizar(self, **kwargs):
        self.llamadas.append(("lineas_para_sincronizar", kwargs))
        return list(self.portal)

    def donde_estan(self, ids):
        self.llamadas.append(("donde_estan", sorted(ids)))
        return {i: self.donde.get(i, "no_existe") for i in ids}

    def registrados_para_comprobar(self, ids):
        self.llamadas.append(("registrados_para_comprobar", sorted(ids)))
        return [{"registro_id": p.registro_id,
                 "hmores_ide": p.sigrid_hmores_ide,
                 "hmoide": p.sigrid_hmoide, "recurso_ide": p.recurso_ide,
                 "fecha_int": p.fecha_int, "horas": p.horas,
                 "es_incidencia": p.es_incidencia}
                for p in self.portal if p.registro_id in set(ids)
                and (p.sigrid_estado or "") == "registrado"]


class Sv5Falso:
    """Doble de `TransferClient`: `sincronizar_leer` y `comprobar`."""

    def __init__(self, lineas=(), *, respuesta=None, borradas=(),
                 comprobar=None, espera: threading.Event | None = None,
                 dentro: threading.Event | None = None) -> None:
        self.lineas = list(lineas)
        self.respuesta = respuesta
        self.borradas = set(borradas)
        self.respuesta_comprobar = comprobar
        self.espera = espera
        self.dentro = dentro
        self.leer: list[tuple[dict, float]] = []
        self.comprobaciones: list[tuple[dict, float]] = []

    def sincronizar_leer(self, payload, *, timeout_s):
        self.leer.append((payload, timeout_s))
        if self.dentro is not None:
            self.dentro.set()
        if self.espera is not None:
            assert self.espera.wait(timeout=10)
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        if self.respuesta is not None:
            return self.respuesta
        return {"ok": True, "lineas": list(self.lineas)}

    def comprobar(self, payload, *, timeout_s):
        self.comprobaciones.append((payload, timeout_s))
        if self.respuesta_comprobar is not None:
            return self.respuesta_comprobar
        return {"ok": True, "veredictos": [
            {"registro_id": l["registro_id"],
             "estado": "borrada" if l["registro_id"] in self.borradas
             else "presente"} for l in payload["lineas"]]}


class ComprobacionFalsa:
    """Doble de `ComprobacionSigrid` (la que escribe `borrado_sigrid`)."""

    def __init__(self, *, borradas=(), ok: bool = True) -> None:
        self.borradas = list(borradas)
        self.ok = ok
        self.llamadas: list[tuple[list, str, bool]] = []

    def comprobar_ids(self, ids, *, origen, forzar=False):
        self.llamadas.append((list(ids), origen, forzar))
        if not self.ok:
            return {"ok": False, "error": "sv5 caido", "borradas_ids": []}
        return {"ok": True, "borradas_ids": [i for i in ids
                                             if i in self.borradas]}


def _sync(repo, sv5, *, comprobacion=None, seco=False, lote=500,
          max_items=500):
    return SincronizadorAmbito(
        repository=repo, transfer_client=sv5,
        comprobacion=comprobacion or ComprobacionFalsa(), timeout_s=150.0,
        seco=seco, lote_comprobar=lote, timeout_comprobar_s=30.0,
        max_items_accion=max_items, reloj_utc=lambda: INSTANTE)


# --------------------------------- R7 ----------------------------------- #

def test_f052_r7_obra_flujo_completo() -> None:
    repo = RepoFalso([P(1), P(2, "")])
    sv5 = Sv5Falso([S(9001, registro_id=1), S(9002, registro_id=2),
                    S(9100, "manual")])
    r = _sync(repo, sv5).sincronizar(AMBITO_OBRA)
    assert r.status == 200
    c = r.cuerpo
    assert repo.llamadas[0] == ("lineas_para_sincronizar", {
        "obra_ide": 686, "recurso_ide": None, "desde": 20261001,
        "hasta": 20261031})
    assert sv5.leer == [({"obra_ide": 686, "desde": 20261001,
                          "hasta": 20261031, "registro_ids": [1, 2]}, 150.0)]
    assert [i["clase"] for i in c["items"]] == [
        "igual", "en_sigrid_sin_registrar", "solo_sigrid_manual"]
    assert c["ok"] is True and c["seco"] is False
    assert c["ambito"] == {"vista": "obra", "clave": "obr-686"}
    assert c["periodo"] == {"period": "2026-10", "mode": "natural",
                            "desde": 20261001, "hasta": 20261031}
    assert c["leido_at"] == INSTANTE.isoformat()
    assert c["recuento"]["total"] == 3
    assert c["recuento"]["por_clase"]["igual"] == 1
    assert all(len(i["firma"]) == 16 for i in c["items"])
    assert c["marcadas_borrado_sigrid"] == []
    assert "marcaria_borrado_sigrid" not in c


def test_f052_r7_persona_rec_en_nomina() -> None:
    repo = RepoFalso([])
    sv5 = Sv5Falso([])
    r = _sync(repo, sv5).sincronizar(AMBITO_PERSONA)
    assert r.status == 200 and r.cuerpo["items"] == []
    assert repo.llamadas == [("lineas_para_sincronizar", {
        "obra_ide": None, "recurso_ide": 501, "desde": 20260916,
        "hasta": 20261015})]
    assert sv5.leer[0][0] == {"recurso_ide": 501, "desde": 20260916,
                              "hasta": 20261015, "registro_ids": []}
    assert r.cuerpo["ambito"] == {"vista": "trabajador", "clave": "rec-501"}


def test_f052_r7_modo_por_defecto_nomina() -> None:
    sv5 = Sv5Falso([])
    _sync(RepoFalso(), sv5).sincronizar(
        {"vista": "obra", "obra_key": "obr-686", "period": "2026-01"})
    assert (sv5.leer[0][0]["desde"], sv5.leer[0][0]["hasta"]) == (
        20251216, 20260115)


def test_f052_r7_sin_registrado_huerfano_no_comprueba() -> None:
    comp = ComprobacionFalsa()
    sv5 = Sv5Falso([S(9001, registro_id=1)])
    r = _sync(RepoFalso([P(1), P(2, "")]), sv5,
              comprobacion=comp).sincronizar(AMBITO_OBRA)
    assert r.status == 200
    assert comp.llamadas == [] and sv5.comprobaciones == []


# --------------------------------- R15 ---------------------------------- #

@pytest.mark.parametrize("ambito", [
    {"vista": "obra", "obra_key": "cod-0686", "period": "2026-10"},
    {"vista": "obra", "obra_key": "nom-obra_uno", "period": "2026-10"},
    {"vista": "obra", "obra_key": "sin-obra", "period": "2026-10"},
    {"vista": "obra", "obra_key": "obr-abc", "period": "2026-10"},
    {"vista": "obra", "obra_key": "obr-0", "period": "2026-10"},
    {"vista": "trabajador", "worker_key": "emp-77", "period": "2026-10"},
    {"vista": "trabajador", "worker_key": "nom-pepe", "period": "2026-10"},
    {"vista": "trabajador", "worker_key": "sin-trabajador",
     "period": "2026-10"},
    {"vista": "trabajador", "worker_key": "rec-x", "period": "2026-10"},
    {"vista": "obra", "worker_key": "rec-501", "period": "2026-10"},
    {"vista": "otra", "obra_key": "obr-686", "period": "2026-10"},
    {"vista": "obra", "obra_key": "obr-686"},
    {"vista": "obra", "obra_key": "obr-686", "period": "2026-13"},
    {"vista": "obra", "obra_key": "obr-686", "period": "octubre"},
    {},
    None,
    "obr-686",
])
def test_f052_r15_ambito_no_valido_422_sin_leer(ambito) -> None:
    repo, sv5 = RepoFalso([P(1)]), Sv5Falso([])
    r = _sync(repo, sv5).sincronizar(ambito)
    assert r.status == 422
    assert r.cuerpo["ok"] is False and r.cuerpo["error"]
    assert "items" not in r.cuerpo
    assert repo.llamadas == [] and sv5.leer == []


@pytest.mark.parametrize("vista, clave, sincronizable", [
    ("obra", "obr-686", True), ("obra", "cod-0686", False),
    ("obra", "nom-x", False), ("obra", "sin-obra", False),
    ("obra", None, False), ("trabajador", "rec-501", True),
    ("trabajador", "emp-77", False), ("trabajador", "nom-x", False),
    ("trabajador", "sin-trabajador", False), ("trabajador", "rec-", False),
    ("otra", "obr-686", False)])
def test_f052_r15_motivo_no_sincronizable(vista, clave,
                                          sincronizable) -> None:
    motivo = motivo_no_sincronizable(vista, clave)
    assert (motivo is None) is sincronizable
    if not sincronizable:
        assert isinstance(motivo, str) and motivo


# --------------------------------- R13 ---------------------------------- #

@pytest.mark.parametrize("respuesta", [
    {"ok": False, "error": "sigrid-api caida"},
    {"ok": True},
    {"ok": True, "lineas": "no es una lista"},
    {"ok": True, "lineas": [{"hmores_ide": 1, "otra": 2, "can": "x"}]},
    RuntimeError("sv5 reventó"),
])
def test_f052_r13_fallo_de_sv5_error_sin_items(respuesta) -> None:
    comp = ComprobacionFalsa()
    repo = RepoFalso([P(1)])
    r = _sync(repo, Sv5Falso(respuesta=respuesta),
              comprobacion=comp).sincronizar(AMBITO_OBRA)
    assert r.status == 502
    assert r.cuerpo["ok"] is False and r.cuerpo["error"]
    assert "items" not in r.cuerpo
    assert comp.llamadas == []
    assert [n for n, _ in repo.llamadas] == ["lineas_para_sincronizar"]


def test_f052_r13_error_de_sv5_conserva_su_texto() -> None:
    r = _sync(RepoFalso(), Sv5Falso(respuesta={
        "ok": False, "error": "sigrid-api caida"})).sincronizar(AMBITO_OBRA)
    assert "sigrid-api caida" in r.cuerpo["error"]


# --------------------------------- R10 ---------------------------------- #

def test_f052_r10_fuera_de_seco_confirma_con_comprobar_ids() -> None:
    comp = ComprobacionFalsa(borradas=[1])
    sv5 = Sv5Falso([S(9002, registro_id=2)])
    r = _sync(RepoFalso([P(1), P(2)]), sv5, comprobacion=comp,
              seco=False).sincronizar(AMBITO_OBRA)
    assert r.status == 200
    assert comp.llamadas == [([1], "sincronizar", True)]
    assert sv5.comprobaciones == []
    item = r.cuerpo["items"][0]
    assert (item["clase"], item["registro_id"]) == ("borrada_en_sigrid", 1)
    assert item["notas"] == ["pasada a borrado_sigrid (F-024)"]
    assert item["acciones"] == ["a_papelera", "reaprobar"]
    assert r.cuerpo["marcadas_borrado_sigrid"] == [1]


def test_f052_r10_fuera_de_seco_comprobacion_fallida_es_error() -> None:
    comp = ComprobacionFalsa(ok=False)
    r = _sync(RepoFalso([P(1)]), Sv5Falso([]), comprobacion=comp,
              seco=False).sincronizar(AMBITO_OBRA)
    assert r.status == 502 and "items" not in r.cuerpo
    assert "sv5 caido" in r.cuerpo["error"]


def test_f052_r10_lo_que_f024_no_confirma_es_409() -> None:
    """Si la comprobación no da por borrada una línea que la lectura no
    encontró, Sigrid (o el portal) cambió entre las dos: no se devuelve
    una comparación que no cuadra."""
    comp = ComprobacionFalsa(borradas=[1])
    r = _sync(RepoFalso([P(1), P(2)]), Sv5Falso([]), comprobacion=comp,
              seco=False).sincronizar(AMBITO_OBRA)
    assert r.status == 409 and "items" not in r.cuerpo
    assert "vuelve a sincronizar" in r.cuerpo["error"]


# ------------------------- DA18 · modo seco ----------------------------- #

def test_f052_da18_seco_no_llama_a_comprobar_ids_ni_escribe() -> None:
    comp = ComprobacionFalsa(borradas=[1, 2])
    repo = RepoFalso([P(1), P(2), P(3, "")])
    sv5 = Sv5Falso([], borradas={1, 2})
    r = _sync(repo, sv5, comprobacion=comp, seco=True).sincronizar(
        AMBITO_OBRA)
    assert r.status == 200
    assert comp.llamadas == []
    assert {n for n, _ in repo.llamadas} <= {
        "lineas_para_sincronizar", "registrados_para_comprobar",
        "donde_estan"}
    assert [l["registro_id"] for l in sv5.comprobaciones[0][0]["lineas"]] \
        == [1, 2]
    assert sv5.comprobaciones[0][1] == 30.0
    c = r.cuerpo
    assert c["seco"] is True
    assert c["marcaria_borrado_sigrid"] == [1, 2]
    assert "marcadas_borrado_sigrid" not in c
    assert [i["clase"] for i in c["items"]] == [
        "borrada_en_sigrid", "borrada_en_sigrid", "pendiente"]
    assert c["items"][0]["notas"] == [
        "modo seco: se pasaría a borrado_sigrid (no se ha escrito)"]


def test_f052_da18_seco_por_lotes() -> None:
    repo = RepoFalso([P(i) for i in range(1, 6)])
    sv5 = Sv5Falso([], borradas={1, 2, 3, 4, 5})
    r = _sync(repo, sv5, seco=True, lote=2).sincronizar(AMBITO_OBRA)
    assert r.status == 200
    assert [len(p["lineas"]) for p, _ in sv5.comprobaciones] == [2, 2, 1]


@pytest.mark.parametrize("comprobar", [
    {"ok": False, "error": "sv5 caido"},
    {"ok": True, "veredictos": []},
    {"ok": True, "veredictos": "x"},
])
def test_f052_da18_seco_fallo_del_veredicto_es_error(comprobar) -> None:
    r = _sync(RepoFalso([P(1)]), Sv5Falso([], comprobar=comprobar),
              seco=True).sincronizar(AMBITO_OBRA)
    assert r.status == 502 and "items" not in r.cuerpo


def test_f052_da18_seco_lo_que_no_confirma_es_409() -> None:
    sv5 = Sv5Falso([], borradas=set())
    r = _sync(RepoFalso([P(1)]), sv5, seco=True).sincronizar(AMBITO_OBRA)
    assert r.status == 409


def test_f052_da18_seco_linea_que_ya_no_esta_registrado_es_409() -> None:
    """Entre la lectura del portal y la comprobación, la línea dejó de
    estar `registrado`: no hay veredicto que dar, no cuadra."""
    repo = RepoFalso([P(1)])
    repo.registrados_para_comprobar = lambda ids: []
    sv5 = Sv5Falso([], borradas={1})
    r = _sync(repo, sv5, seco=True).sincronizar(AMBITO_OBRA)
    assert r.status == 409 and sv5.comprobaciones == []


# --------------------------------- R12 ---------------------------------- #

def test_f052_r12_donde_de_las_nuestras_sin_pareja() -> None:
    repo = RepoFalso([P(1)], donde={509: "papelera", 510: "otro_ambito"})
    sv5 = Sv5Falso([S(9001, registro_id=1), S(9509, registro_id=509),
                    S(9510, registro_id=510), S(9600, "ajena"),
                    S(9002, registro_id=1)])
    r = _sync(repo, sv5).sincronizar(AMBITO_OBRA)
    assert ("donde_estan", [509, 510]) in repo.llamadas
    por_ide = {i["hmores_ide"]: i for i in r.cuerpo["items"]}
    assert por_ide[9509]["donde"] == "papelera"
    assert por_ide[9509]["acciones"] == ["restaurar"]
    assert por_ide[9510]["donde"] == "otro_ambito"
    assert por_ide[9510]["acciones"] == []
    assert por_ide[9002]["donde"] is None
    assert por_ide[9600]["donde"] is None


def test_f052_r12_sin_nuestras_no_pregunta_donde() -> None:
    repo = RepoFalso([P(1)])
    _sync(repo, Sv5Falso([S(9001, registro_id=1)])).sincronizar(AMBITO_OBRA)
    assert all(n != "donde_estan" for n, _ in repo.llamadas)


# --------------------------------- R29 ---------------------------------- #

def test_f052_r29_mismo_ambito_a_la_vez_409() -> None:
    espera, dentro = threading.Event(), threading.Event()
    sv5 = Sv5Falso([], espera=espera, dentro=dentro)
    sync = _sync(RepoFalso(), sv5)
    resultado: dict = {}
    hilo = threading.Thread(
        target=lambda: resultado.setdefault("r", sync.sincronizar(
            AMBITO_OBRA)), daemon=True)
    hilo.start()
    assert dentro.wait(timeout=10)
    try:
        segunda = sync.sincronizar(dict(AMBITO_OBRA, period="2026-09"))
        assert segunda.status == 409
        assert "ya se está sincronizando" in segunda.cuerpo["error"]
        otra = _sync(RepoFalso(), Sv5Falso([])).sincronizar(AMBITO_OBRA)
        assert otra.status == 200
        sv5.espera = None
        persona = sync.sincronizar(AMBITO_PERSONA)
        assert persona.status == 200
    finally:
        espera.set()
    hilo.join(timeout=10)
    assert resultado["r"].status == 200
    assert sync.sincronizar(AMBITO_OBRA).status == 200


def test_f052_r29_el_candado_se_suelta_si_algo_revienta() -> None:
    class RepoQueRevienta(RepoFalso):
        def lineas_para_sincronizar(self, **kwargs):
            raise RuntimeError("base caida")

    sync = _sync(RepoQueRevienta(), Sv5Falso([]))
    with pytest.raises(RuntimeError):
        sync.sincronizar(AMBITO_OBRA)
    sync._repo = RepoFalso()
    assert sync.sincronizar(AMBITO_OBRA).status == 200


# ====================== T10 · aplicar (R18-R25) ========================== #

class RepoAcciones(RepoFalso):
    """El repositorio de lectura más los métodos que escriben, apuntados.
    `descartar` = {id: motivo} que el CAS del repositorio rechazaría."""

    def __init__(self, portal=(), donde=None, *, descartar=None,
                 congeladas=None, duplicadas=(), no_restaura=()) -> None:
        super().__init__(portal, donde)
        self.descartar = dict(descartar or {})
        self.congeladas = dict(congeladas or {})
        self.duplicadas = set(duplicadas)
        self.no_restaura = set(no_restaura)
        self.escrituras: list[tuple[str, object]] = []

    def _partir(self, items):
        ok = [it["registro_id"] for it in items
              if it["registro_id"] not in self.descartar]
        fuera = [{"registro_id": i, "motivo": m}
                 for i, m in self.descartar.items()
                 if i in {it["registro_id"] for it in items}]
        return ok, fuera

    def aplicar_marcar_registrada(self, items, *, actor, ahora_iso):
        self.escrituras.append(("marcar", (list(items), actor, ahora_iso)))
        ok, fuera = self._partir(items)
        return {"aplicados": ok, "descartados": fuera}

    def aplicar_traer_de_sigrid(self, items, *, actor, ahora_iso):
        self.escrituras.append(("traer", (list(items), actor, ahora_iso)))
        ok, fuera = self._partir(items)
        return {"aplicados": ok, "descartados": fuera,
                "documentos": ["d1"] if ok else [],
                "pares": [(501, 20261014)] if ok else []}

    def documentos_de_los_dias(self, pares):
        self.llamadas.append(("documentos_de_los_dias", list(pares)))
        return ["d0", "d1", "d2"]

    def borrar_linea(self, *, registro_id, by=None):
        self.escrituras.append(("borrar", (registro_id, by)))
        if registro_id in self.congeladas:
            raise CongeladoError(self.congeladas[registro_id])
        return {"ok": registro_id not in self.descartar}

    def restore_registro(self, *, registro_id):
        self.escrituras.append(("restaurar", registro_id))
        if registro_id in self.duplicadas:
            raise DuplicadoActivoError()
        return registro_id not in self.no_restaura


class Recalculo:
    """El recálculo compartido que la ruta liga al motivo `sincronizar`
    (`_pedir_recalculo_compartido`): apunta y responde."""

    def __init__(self, estado: str = "pedido") -> None:
        self.estado = estado
        self.llamadas: list[tuple[list, str | None]] = []

    def __call__(self, ids, solicitado_por):
        self.llamadas.append((list(ids), solicitado_por))
        return self.estado, "pedido-1"


def _firmas(sync, ambito=AMBITO_OBRA) -> dict:
    """Primera sincronización: {registro_id: firma} (la última si se repite)."""
    r = sync.sincronizar(ambito)
    assert r.status == 200
    return {i["registro_id"]: i["firma"] for i in r.cuerpo["items"]
            if i["registro_id"] is not None}


def _pedir(firmas: dict, *ids) -> list[dict]:
    return [{"registro_id": i, "firma": firmas[i]} for i in ids]


def test_f052_r18_aplicar_resincroniza_y_solo_aplica_firma_igual() -> None:
    repo = RepoAcciones([P(1, "error"), P(2, "error")])
    sv5 = Sv5Falso([S(9001, registro_id=1), S(9002, registro_id=2)])
    sync = _sync(repo, sv5)
    firmas = _firmas(sync)
    repo.portal[1] = P(2, "error", horas=7.0)       # cambió tras verlo
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA,
                     _pedir(firmas, 1, 2), actor="ana")
    assert r.status == 200
    assert len(sv5.leer) == 2                         # volvió a leer Sigrid
    c = r.cuerpo
    assert c["ok"] is True and c["accion"] == "marcar_registrada"
    assert c["aplicados"] == [1]
    assert c["descartados"] == [{"registro_id": 2,
                                 "motivo": "cambió desde que lo viste"}]
    assert repo.escrituras == [("marcar", ([{
        "registro_id": 1, "estado_visto": "error", "hmores_ide_visto": 9001,
        "hmores_ide": 9001, "hmoide": 7001, "parte_cod": "PT26/00001"}],
        "ana", INSTANTE.isoformat()))]


def test_f052_r18_descarte_del_cas_del_repositorio_vuelve_en_descartados(
        ) -> None:
    repo = RepoAcciones([P(1, "error")], descartar={1: "cambió desde que "
                                                    "lo viste"})
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1)]))
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA,
                     _pedir(_firmas(sync), 1), actor="ana")
    assert r.cuerpo["aplicados"] == []
    assert r.cuerpo["descartados"] == [{"registro_id": 1,
                                        "motivo": "cambió desde que lo viste"}]


def test_f052_r18_id_ajeno_al_ambito_422_sin_tocar_nada() -> None:
    repo = RepoAcciones([P(1, "error")])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1)]))
    firmas = _firmas(sync)
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA,
                     _pedir(firmas, 1) + [{"registro_id": 77,
                                           "firma": "0" * 16}], actor="ana")
    assert r.status == 422 and r.cuerpo["ok"] is False
    assert "1 línea(s) no son de este ámbito" in r.cuerpo["error"]
    assert repo.escrituras == []


@pytest.mark.parametrize("accion, items", [
    ("borrar_en_sigrid", [{"registro_id": 1, "firma": "x" * 16}]),
    ("marcar_registrada", []),
    ("marcar_registrada", [{"registro_id": "1", "firma": "x" * 16}]),
    ("marcar_registrada", [{"registro_id": 0, "firma": "x" * 16}]),
    ("marcar_registrada", [{"registro_id": True, "firma": "x" * 16}]),
    ("marcar_registrada", [{"registro_id": 1, "firma": 5}]),
    ("marcar_registrada", [{"registro_id": 1}]),
    ("marcar_registrada", ["1"]),
    ("marcar_registrada", "1"),
    ("marcar_registrada", [{"registro_id": 1, "firma": "x" * 16}] * 2),
])
def test_f052_r18_peticion_no_valida_422_sin_leer(accion, items) -> None:
    repo = RepoAcciones([P(1, "error")])
    sv5 = Sv5Falso([S(9001, registro_id=1)])
    r = _sync(repo, sv5).aplicar(accion, AMBITO_OBRA, items, actor="ana")
    assert r.status == 422 and r.cuerpo["ok"] is False
    assert sv5.leer == [] and repo.escrituras == []


def test_f052_r18_tope_de_items_422() -> None:
    sv5 = Sv5Falso([])
    sync = _sync(RepoAcciones(), sv5, max_items=2)
    items = [{"registro_id": i, "firma": "x" * 16} for i in (1, 2, 3)]
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA, items, actor="ana")
    assert r.status == 422 and "máximo es 2" in r.cuerpo["error"]
    assert sv5.leer == []


def test_f052_r18_ambito_no_valido_422() -> None:
    sv5 = Sv5Falso([])
    r = _sync(RepoAcciones(), sv5).aplicar(
        "marcar_registrada", dict(AMBITO_OBRA, obra_key="cod-0686"),
        [{"registro_id": 1, "firma": "x" * 16}], actor="ana")
    assert r.status == 422 and sv5.leer == []


@pytest.mark.parametrize("respuesta", [
    {"ok": False, "error": "sigrid-api caída"}, RuntimeError("timeout")])
def test_f052_r18_si_la_relectura_falla_no_aplica(respuesta) -> None:
    repo = RepoAcciones([P(1, "error")])
    sv5 = Sv5Falso([S(9001, registro_id=1)])
    sync = _sync(repo, sv5)
    firmas = _firmas(sync)
    sv5.respuesta = respuesta
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA, _pedir(firmas, 1),
                     actor="ana")
    assert r.status == 502 and "items" not in r.cuerpo
    assert repo.escrituras == []


def test_f052_r16_accion_que_no_es_de_la_clase_se_descarta() -> None:
    repo = RepoAcciones([P(1)])                         # igual
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1)]))
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA,
                     _pedir(_firmas(sync), 1), actor="ana")
    assert r.cuerpo["aplicados"] == []
    assert r.cuerpo["descartados"] == [{
        "registro_id": 1,
        "motivo": "«marcar_registrada» no aplica a una línea «igual»"}]
    assert repo.escrituras == []


# ------------------------------ traer (R20, R23) ------------------------- #

def test_f052_r20_traer_horas_de_sigrid_y_recalculo_compartido() -> None:
    repo = RepoAcciones([P(1)])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1, can=6.0)]))
    rec = Recalculo()
    r = sync.aplicar("traer_de_sigrid", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=rec)
    assert r.status == 200
    assert r.cuerpo["aplicados"] == [1] and r.cuerpo["recalculo"] == "pedido"
    assert repo.escrituras == [("traer", ([{
        "registro_id": 1, "horas_vistas": 8.0, "horas_nuevas": 6.0,
        "hmores_ide_visto": 9001}], "ana", INSTANTE.isoformat()))]
    assert ("documentos_de_los_dias", [(501, 20261014)]) in repo.llamadas
    assert rec.llamadas == [(["d1", "d0", "d2"], "ana")]


def test_f052_r20_traer_anulada_en_sigrid_pone_cero() -> None:
    repo = RepoAcciones([P(1, extra=True, hora_codigo="HE01")])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1, can=0.0,
                                   hora_cod="HE01")]))
    r = sync.aplicar("traer_de_sigrid", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=Recalculo())
    assert r.cuerpo["aplicados"] == [1]
    assert repo.escrituras[0][1][0][0]["horas_nuevas"] == 0.0


def test_f052_r23_cola_que_falla_el_cambio_queda_y_avisa() -> None:
    repo = RepoAcciones([P(1)])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1, can=6.0)]))
    r = sync.aplicar("traer_de_sigrid", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=Recalculo("fallo"))
    assert r.status == 200
    assert r.cuerpo["aplicados"] == [1] and r.cuerpo["recalculo"] == "fallo"


def test_f052_r23_sin_aplicados_no_pide_recalculo() -> None:
    repo = RepoAcciones([P(1)], descartar={1: "cambió desde que lo viste"})
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1, can=6.0)]))
    rec = Recalculo()
    r = sync.aplicar("traer_de_sigrid", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=rec)
    assert r.cuerpo["recalculo"] is None and rec.llamadas == []


def test_f052_da3_distinta_solo_por_partida_no_trae() -> None:
    repo = RepoAcciones([P(1)])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1, partida_ide=12,
                                   partida_cod="P2")]))
    r = sync.aplicar("traer_de_sigrid", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=Recalculo())
    assert r.cuerpo["aplicados"] == []
    assert "no aplica" in r.cuerpo["descartados"][0]["motivo"]
    assert repo.escrituras == []


# --------------------------- rutas existentes (R24) ---------------------- #

def test_f052_r24_a_papelera_reutiliza_borrar_linea() -> None:
    repo = RepoAcciones([P(1, "borrado_sigrid"), P(2, "borrado_sigrid")],
                        congeladas={2: "Línea congelada: registrada"})
    sync = _sync(repo, Sv5Falso([]))
    r = sync.aplicar("a_papelera", AMBITO_OBRA, _pedir(_firmas(sync), 1, 2),
                     actor="ana")
    assert r.cuerpo["aplicados"] == [1]
    assert r.cuerpo["descartados"] == [{"registro_id": 2,
                                        "motivo": "Línea congelada: "
                                                  "registrada"}]
    assert repo.escrituras == [("borrar", (1, "ana")), ("borrar", (2, "ana"))]


def test_f052_r24_a_papelera_que_ya_no_esta() -> None:
    repo = RepoAcciones([P(1, "borrado_sigrid")],
                        descartar={1: "x"})
    sync = _sync(repo, Sv5Falso([]))
    r = sync.aplicar("a_papelera", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana")
    assert r.cuerpo["descartados"] == [{
        "registro_id": 1, "motivo": "la línea ya no existe o ya está en la "
                                    "papelera"}]


def test_f052_r24_restaurar_reutiliza_restore_y_su_409() -> None:
    repo = RepoAcciones([], donde={5: "papelera", 6: "papelera",
                                   7: "papelera"},
                        duplicadas={6}, no_restaura={7})
    sync = _sync(repo, Sv5Falso([S(9005, registro_id=5),
                                 S(9006, registro_id=6),
                                 S(9007, registro_id=7)]))
    r = sync.aplicar("restaurar", AMBITO_OBRA,
                     _pedir(_firmas(sync), 5, 6, 7), actor="ana")
    c = r.cuerpo
    assert c["aplicados"] == [5]
    assert c["descartados"][0]["registro_id"] == 6
    assert "otro parte activo" in c["descartados"][0]["motivo"] or \
        c["descartados"][0]["motivo"] == DuplicadoActivoError().motivo
    assert c["descartados"][1] == {"registro_id": 7,
                                   "motivo": "la línea ya no existe"}
    assert repo.escrituras == [("restaurar", 5), ("restaurar", 6),
                               ("restaurar", 7)]


def test_f052_r24_restaurar_fuera_de_la_papelera_no_aplica() -> None:
    repo = RepoAcciones([], donde={5: "otro_ambito"})
    sync = _sync(repo, Sv5Falso([S(9005, registro_id=5)]))
    r = sync.aplicar("restaurar", AMBITO_OBRA, _pedir(_firmas(sync), 5),
                     actor="ana")
    assert r.cuerpo["aplicados"] == [] and repo.escrituras == []


def test_f052_r24_reaprobar_no_escribe_y_abre_el_modal() -> None:
    repo = RepoAcciones([P(1, ""), P(2, "borrado_sigrid")])
    sync = _sync(repo, Sv5Falso([]))
    r = sync.aplicar("reaprobar", AMBITO_OBRA, _pedir(_firmas(sync), 1, 2),
                     actor="ana")
    c = r.cuerpo
    assert c["aplicados"] == [1, 2] and c["descartados"] == []
    assert c["abrir_aprobar"] is True and c["incluir_borradas"] is True
    assert repo.escrituras == []


def test_f052_r24_reaprobar_pendientes_sin_borradas() -> None:
    repo = RepoAcciones([P(1, "")])
    sync = _sync(repo, Sv5Falso([]))
    r = sync.aplicar("reaprobar", AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana")
    assert r.cuerpo["incluir_borradas"] is False


# ------------------------ seco, candado, log, R10 ------------------------ #

def test_f052_da18_aplicar_no_depende_del_modo_seco() -> None:
    """La acción confirmada del usuario escribe también en seco; el seco
    solo gobierna la escritura implícita de R10 (design §8, DA18)."""
    repo = RepoAcciones([P(1, "error")])
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1)]), seco=True)
    r = sync.aplicar("marcar_registrada", AMBITO_OBRA,
                     _pedir(_firmas(sync), 1), actor="ana")
    assert r.cuerpo["aplicados"] == [1] and r.cuerpo["seco"] is True
    assert repo.escrituras[0][0] == "marcar"


def test_f052_r10_fuera_de_seco_la_firma_ve_lo_que_quedo_escrito() -> None:
    """Fuera de seco, R10 pasa la línea a `borrado_sigrid`: el ítem lleva
    ese estado (el que leerá la siguiente sincronización), no el leído
    antes; si no, ninguna acción sobre él casaría la firma."""
    repo = RepoAcciones([P(1)])

    class ComprobacionQueEscribe(ComprobacionFalsa):
        def comprobar_ids(self, ids, *, origen, forzar=False):
            res = super().comprobar_ids(ids, origen=origen, forzar=forzar)
            repo.portal = [P(1, "borrado_sigrid", sigrid_motivo="Borrada")]
            return res

    sync = _sync(repo, Sv5Falso([]),
                 comprobacion=ComprobacionQueEscribe(borradas=[1]))
    primera = sync.sincronizar(AMBITO_OBRA).cuerpo["items"][0]
    assert primera["portal"]["sigrid_estado"] == "borrado_sigrid"
    r = sync.aplicar("a_papelera", AMBITO_OBRA,
                     [{"registro_id": 1, "firma": primera["firma"]}],
                     actor="ana")
    assert r.cuerpo["aplicados"] == [1]


def test_f052_r29_aplicar_toma_el_candado_del_ambito() -> None:
    repo = RepoAcciones([P(1, "error")])
    sv5 = Sv5Falso([S(9001, registro_id=1)])
    sync = _sync(repo, sv5)
    firmas = _firmas(sync)
    sv5.espera, sv5.dentro = threading.Event(), threading.Event()
    res = {}
    hilo = threading.Thread(target=lambda: res.setdefault("r", sync.aplicar(
        "marcar_registrada", AMBITO_OBRA, _pedir(firmas, 1), actor="ana")))
    hilo.start()
    assert sv5.dentro.wait(timeout=10)
    otra = sync.sincronizar(AMBITO_OBRA)
    sv5.espera.set()
    hilo.join(timeout=10)
    assert otra.status == 409
    assert res["r"].status == 200


def test_f052_r22_log_info_con_accion_ids_recuentos_y_actor(caplog) -> None:
    repo = RepoAcciones([P(1, "error"), P(2, "error")],
                        descartar={2: "cambió desde que lo viste"})
    sync = _sync(repo, Sv5Falso([S(9001, registro_id=1),
                                 S(9002, registro_id=2)]))
    firmas = _firmas(sync)
    with caplog.at_level("INFO", logger="application.services."
                                        "sincronizar_ambito"):
        sync.aplicar("marcar_registrada", AMBITO_OBRA, _pedir(firmas, 1, 2),
                     actor="ana@x")
    linea = next(m for m in caplog.messages
                 if "[sincronizar][aplicar]" in m)
    for trozo in ("accion=marcar_registrada", "actor=ana@x", "pedidos=2",
                  "aplicados=1", "descartados=1", "ids=[1]"):
        assert trozo in linea


# ------------- supervivientes de la mutación (mutacion_F-052.md) -------- #

@pytest.mark.parametrize("vista, clave", [("obra", "obr-1"),
                                          ("trabajador", "rec-1")])
def test_f052_r15_ide_1_es_sincronizable(vista, clave) -> None:
    """El ide 1 es un ide válido (mutante 10: `<= 0` -> `<= 1`)."""
    assert motivo_no_sincronizable(vista, clave) is None


def test_f052_r15_ambito_inmutable() -> None:
    """El ámbito resuelto no cambia durante la sincronización ni la
    relectura de `aplicar` (mutante 11)."""
    amb = Ambito(vista="obra", clave="obr-686", period="2026-10",
                 mode="natural", obra_ide=686, recurso_ide=None,
                 desde=20261001, hasta=20261031)
    with pytest.raises(FrozenInstanceError):
        amb.obra_ide = 1


def test_f052_r2_linea_de_sv5_con_origen_desconocido_es_error() -> None:
    """Una línea completa pero con un `origen` que no es de R2 no se
    compara (mutante 12: `or` -> `and`)."""
    with pytest.raises(ValueError, match="origen"):
        lineas_de_sv5({"ok": True, "lineas": [S(9001, origen="rara")]})
    r = _sync(RepoFalso([P(1)]), Sv5Falso([S(9001, origen="rara",
                                                registro_id=1)])
              ).sincronizar(AMBITO_OBRA)
    assert r.status == 502 and "items" not in r.cuerpo


def test_f052_r18_tope_por_defecto_500() -> None:
    """Sin `max_items_accion`, el tope de R18 es 500 (mutante 13)."""
    sync = SincronizadorAmbito(
        repository=RepoFalso(), transfer_client=Sv5Falso(),
        comprobacion=ComprobacionFalsa(), timeout_s=150.0, seco=False,
        lote_comprobar=500, timeout_comprobar_s=30.0)
    items = [{"registro_id": i, "firma": "x" * 16} for i in range(1, 502)]
    assert sync.validar_peticion("marcar_registrada", items[:500]) is None
    assert "máximo es 500" in sync.validar_peticion("marcar_registrada",
                                                    items)


def test_f052_r18_tope_justo_es_valido() -> None:
    """Exactamente `max_items_accion` líneas es válido (mutante 16)."""
    sync = _sync(RepoAcciones(), Sv5Falso([]), max_items=2)
    assert sync.validar_peticion("marcar_registrada", [
        {"registro_id": i, "firma": "x" * 16} for i in (1, 2)]) is None


def test_f052_da18_seco_veredicto_sin_registro_id_se_ignora() -> None:
    """Un veredicto de sv5 sin `registro_id` no es de ninguna línea: se
    ignora y no revienta (mutante 15: `and` -> `or`)."""
    sv5 = Sv5Falso([], comprobar={"ok": True, "veredictos": [
        {"registro_id": 1, "estado": "borrada"},
        {"registro_id": None, "estado": "borrada"}]})
    r = _sync(RepoFalso([P(1)]), sv5, seco=True).sincronizar(AMBITO_OBRA)
    assert r.status == 200
    assert r.cuerpo["marcaria_borrado_sigrid"] == [1]
