# tests/test_f049_guardar_celda.py
"""F-049 · repositorio y rutas del editor de celda de la matriz de obra.

`POST /api/matriz/celda` guarda la celda entera en una transacción con su
entrada de deshacer, crea la ordinaria o la extra que falte desde la
plantilla y pide UN recálculo con un pedido compartido (DA13-C) en los
partes tocados y en los de otras obras del mismo (recurso, día).

SQLite en memoria con el ORM real (`tests/dobles.py`), publicador de
recálculo y cliente de Sigrid falsos. Ni red ni PostgreSQL. Nombres, DNIs
y recursos SINTÉTICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-10-14T08:00:00+00:00"
FECHA = "2026-10-14"                 # martes
FINT = 20261014
MES = {"period_key": "2026-10", "mode": "natural"}
OBRA_Y, OBRA_X = 678, 686
KEY_Y, KEY_X = f"obr-{OBRA_Y}", f"obr-{OBRA_X}"
RECURSO = 501
WK = f"rec-{RECURSO}"


def _doc(s, doc_id: str, obra: int, *, fecha: str = FECHA,
         aprobado: bool = False) -> None:
    s.add(ParteDocumentOrm(
        id=doc_id, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + doc_id,
        fecha=fecha, fecha_int=int(fecha.replace("-", "")),
        created_at_utc=AHORA, obra_ide=obra, obra_codigo=f"0{obra}",
        obra_nombre=f"Obra {obra}", approved=aprobado,
        approved_by="ana" if aprobado else None))


def _reg(s, doc_id: str, obra: int, line_index: int, *,
         fecha: str = FECHA, tipo: str = "normal", horas: float = 8.0,
         recurso: int | None = RECURSO, **campos) -> int:
    datos = dict(
        empleado_line_no=1, empleado_ide=77, empleado_dni="00000077A",
        empleado_nombre="Persona Siete", trabajador_nombre_leido="P. Siete",
        categoria="OFICIAL 1ª", hora_ide=1, hora_codigo="HL01",
        hora_candef=8.0, recurso_cif="00000077A")
    datos.update(campos)
    reg = ParteRegistroOrm(
        document_id=doc_id, line_index=line_index, fecha=fecha,
        fecha_int=int(fecha.replace("-", "")), obra_ide=obra,
        obra_codigo=f"0{obra}", obra_nombre=f"Obra {obra}",
        tipo_hora=tipo, horas=horas, recurso_ide=recurso, **datos)
    s.add(reg)
    s.flush()
    return reg.id


def _celda_de_la_matriz(repo, obra_key: str = KEY_Y, wk: str = WK,
                        fecha: str = FECHA):
    detalle = repo.get_obra(obra_key, **MES)
    fila = next(r for r in detalle.rows if r.worker_key == wk)
    return next(c for c in fila.cells if c.date_iso == fecha)


# ===================== R10 · `a` en las extra_auto ===================== #

def test_f049_r10_regs_marcan_solo_las_extra_auto():
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-y", OBRA_Y)
        base = _reg(s, "d-y", OBRA_Y, 0, horas=8.0, horas_orig=10.0)
        auto = _reg(s, "d-y", OBRA_Y, 0, tipo="extra", horas=2.0,
                    extra_auto=True)
        explicita = _reg(s, "d-y", OBRA_Y, 1, tipo="extra", horas=1.0)
        s.commit()
    celda = _celda_de_la_matriz(ParteReviewRepository(fabrica))
    por_id = {r["id"]: r for r in celda.regs}
    assert por_id[auto] == {"id": auto, "t": "e", "h": 2.0, "p": None,
                            "a": 1}
    assert "a" not in por_id[base]
    assert "a" not in por_id[explicita]
    assert por_id[base] == {"id": base, "t": "n", "h": 8.0, "p": None}


# ======================================================================= #
# T6 · repositorio y rutas (R11-R24, R33-R35, R38, R39)
# ======================================================================= #

import logging  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402
from config.settings import Settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from application.services.edicion_celda import (  # noqa: E402
    MOTIVO_CELDA_CAMBIADA,
    Cambio,
    CeldaInvalida,
)
from application.services.seguimiento_recalculo import (  # noqa: E402
    MOTIVO_RECALCULANDO,
)
from infrastructure.database.orm_models import (  # noqa: E402
    RepartoPendienteOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import (  # noqa: E402
    MOTIVO_REPARTO_APLICANDO,
    obra_key_for_registro,
    worker_key_for_registro,
)
from infrastructure.sigrid.sigrid_lookup_client import (  # noqa: E402
    TipoHoraOption,
)
from interface_adapters.web import app as app_mod  # noqa: E402
from interface_adapters.web.app import build_app  # noqa: E402

ACTOR = "revisora@ejemplo.es"
CABECERA = {"X-MS-CLIENT-PRINCIPAL-NAME": ACTOR}
HORA_EXTRA_RECURSO = {"ide": 31, "cod": "HE01", "res": "HORA EXTRA",
                      "pre": 21.5}


class SigridFake:
    """Doble de `SigridLookupClient`: tipos de hora y hora extra del
    recurso. `falla` hace fallar las dos consultas de F-049."""

    falla = False
    sin_extra = False
    llamadas: list = []

    def __init__(self, **_kw) -> None:
        pass

    def fetch_tipos_hora(self) -> list[TipoHoraOption]:
        SigridFake.llamadas.append("tipos")
        if SigridFake.falla:
            raise RuntimeError("sigrid caido")
        return [
            TipoHoraOption(ide=11, codigo="HN-OF", ext=0, pre=15.0,
                           descripcion="HORA LABORABLE OFICIAL", prenom=9.0),
            TipoHoraOption(ide=12, codigo="HX-OF", ext=1, pre=20.0,
                           descripcion="HORA EXTRA OFICIAL", prenom=None),
        ]

    def fetch_hora_extra_recurso(self, reside: int):
        SigridFake.llamadas.append(("extra", reside))
        if SigridFake.falla:
            raise RuntimeError("sigrid caido")
        return None if SigridFake.sin_extra else dict(HORA_EXTRA_RECURSO)

    def fetch_obras(self) -> list:
        return []

    def fetch_empleados(self) -> list:
        return []

    def fetch_partidas_obra(self, _obra_ide: int) -> list:
        return []

    def fetch_dnis_sin_extra(self, _dnis) -> set:
        return set()


class ColaFake:
    """`ColaCliente` reducido a `enviar`; apunta o falla."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.enviados: list[tuple[str, dict]] = []
        self.error = error
        self.al_enviar = None

    def enviar(self, queue_name: str, payload: dict) -> None:
        if self.al_enviar is not None:
            self.al_enviar()
        if self.error is not None:
            raise self.error
        self.enviados.append((queue_name, payload))


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    SigridFake.falla = False
    SigridFake.sin_extra = False
    SigridFake.llamadas = []
    return monkeypatch


@pytest.fixture
def montaje(entorno):
    """`_montar(sembrar, ...) -> (cliente, repo, fabrica, ids, cola)`."""

    def _montar(sembrar, *, con_sigrid: bool = True, sin_cola: bool = False,
                cola: ColaFake | None = None):
        if con_sigrid:
            for clave, valor in {
                "SIGRID_API_BASE_URL": "http://sigrid.interno",
                "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
                "SIGRID_API_DATABASE": "ruesma_rep",
            }.items():
                entorno.setenv(clave, valor)
            entorno.setattr(app_mod, "SigridLookupClient", SigridFake)
        fabrica = FabricaSesionSqlite()
        with fabrica.create_session() as s:
            ids = sembrar(s)
            s.commit()
        repo = ParteReviewRepository(fabrica)
        cola = None if sin_cola else (cola or ColaFake())
        app = build_app(Settings(_env_file=None), repository=repo,
                        cola_cliente=cola)
        return TestClient(app), repo, fabrica, ids, cola
    return _montar


def _post(cliente, lineas, *, nueva_ordinaria=None, nueva_extra=None,
          obra_key: str = KEY_Y, wk: str = WK, fecha: str = FECHA):
    return cliente.post("/api/matriz/celda", headers=CABECERA, json={
        "obra_key": obra_key, "worker_key": wk, "fecha": fecha,
        "lineas": [{"id": i, "antes": a, "horas": h} for i, a, h in lineas],
        "nueva_ordinaria": nueva_ordinaria, "nueva_extra": nueva_extra})


def _otras(cliente, *, obra_key: str = KEY_Y, wk: str = WK,
           fecha: str = FECHA):
    return cliente.get("/api/matriz/celda/otras", params={
        "obra_key": obra_key, "worker_key": wk, "fecha": fecha})


def _fila(fabrica, rid: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        return s.get(ParteRegistroOrm, rid)


def _lineas_doc(fabrica, doc_id: str) -> list[ParteRegistroOrm]:
    with fabrica.create_session() as s:
        return list(s.execute(select(ParteRegistroOrm).where(
            ParteRegistroOrm.document_id == doc_id).order_by(
            ParteRegistroOrm.id)).scalars().all())


def _seguimiento(fabrica, doc_id: str) -> tuple:
    with fabrica.create_session() as s:
        d = s.get(ParteDocumentOrm, doc_id)
        return d.recalculo_pedido_id, d.recalculo_terminado_id


def _undos(fabrica) -> list[UndoLogOrm]:
    with fabrica.create_session() as s:
        return list(s.execute(select(UndoLogOrm).order_by(
            UndoLogOrm.id)).scalars().all())


def _poner_pedido(fabrica, doc_id: str, pedido: str) -> None:
    with fabrica.create_session() as s:
        d = s.get(ParteDocumentOrm, doc_id)
        d.recalculo_pedido_id = pedido
        d.recalculo_pedido_at_utc = datetime.now(timezone.utc).isoformat()
        s.commit()


# ------------------------------ escenarios ------------------------------ #

def _solo_extra(s) -> dict:
    """E2: solo una extra de 10 en Y, con partida; el parte tiene otra
    persona y una línea en la papelera (el `line_index` mayor)."""
    _doc(s, "d-y", OBRA_Y)
    ids = {"extra": _reg(
        s, "d-y", OBRA_Y, 3, tipo="extra", horas=10.0, empleado_line_no=2,
        partida="ENC", partida_ide=44, partida_cod="CI-01",
        partida_res="Oficiales", partida_capitulo="CI",
        partida_match_method="categoria", partida_match_score=0.9,
        hmo_ide=7001, parte_estado="abierto", recurso_precio_hora=17.5,
        empleado_reside=RECURSO, empleado_match_method="dni",
        empleado_match_score=1.0, empleado_codigo="E77",
        horas_extra_leidas=10.0, sigrid_estado="error",
        sigrid_motivo="fallo previo")}
    ids["otra"] = _reg(s, "d-y", OBRA_Y, 5, recurso=502, empleado_ide=78,
                       empleado_line_no=4, empleado_dni="00000078A",
                       trabajador_nombre_leido="Otra Persona")
    ids["papelera"] = _reg(s, "d-y", OBRA_Y, 7, recurso=503,
                           empleado_ide=79, empleado_line_no=5,
                           deleted_at_utc=AHORA)
    return ids


def _solo_ordinaria(s) -> dict:
    _doc(s, "d-y", OBRA_Y)
    return {"ord": _reg(s, "d-y", OBRA_Y, 0, horas=8.0)}


def _pareja(s) -> dict:
    """E4/E5: pareja automática 8 (orig 10) + 2 y otra pareja ajena en
    otra clave de la misma celda."""
    _doc(s, "d-y", OBRA_Y)
    return {
        "base": _reg(s, "d-y", OBRA_Y, 0, horas=8.0, horas_orig=10.0,
                     horas_extra_leidas=2.0),
        "auto": _reg(s, "d-y", OBRA_Y, 0, tipo="extra", horas=2.0,
                     extra_auto=True),
        "base2": _reg(s, "d-y", OBRA_Y, 1, horas=1.0, horas_orig=1.5),
        "auto2": _reg(s, "d-y", OBRA_Y, 1, tipo="extra", horas=0.5,
                      extra_auto=True),
    }


def _e12(s, *, x_aprobada: bool = False) -> dict:
    """E12: Y (2 extra) y X (8 ord.) del mismo recurso y día; más ruido
    que NO es del grupo: X al día siguiente, otro recurso el mismo día,
    una incidencia del recurso en otra obra y una línea en la papelera."""
    _doc(s, "d-y", OBRA_Y)
    _doc(s, "d-x", OBRA_X, aprobado=x_aprobada)
    _doc(s, "d-x2", OBRA_X, fecha="2026-10-15")
    _doc(s, "d-z", 700)
    _doc(s, "d-v", 701)
    _doc(s, "d-p", 702)
    ids = {"y": _reg(s, "d-y", OBRA_Y, 0, tipo="extra", horas=2.0),
           "x": _reg(s, "d-x", OBRA_X, 0, horas=8.0)}
    ids["x2"] = _reg(s, "d-x2", OBRA_X, 0, fecha="2026-10-15")
    ids["z"] = _reg(s, "d-z", 700, 0, recurso=502, empleado_ide=78)
    ids["v"] = _reg(s, "d-v", 701, 0, tipo="V", horas=None,
                    es_incidencia=True, incidencia_codigo="V")
    ids["p"] = _reg(s, "d-p", 702, 0, deleted_at_utc=AHORA)
    return ids


# ======================= E2 · crear la ordinaria ======================== #

def test_f049_e2_r20_r21_ordinaria_nueva_clona_la_plantilla(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_solo_extra)
    r = _post(cliente, [(ids["extra"], 10.0, 2.0)], nueva_ordinaria=8.0)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    (nueva_id,) = cuerpo["creadas"]
    base, nueva = _fila(fabrica, ids["extra"]), _fila(fabrica, nueva_id)
    assert base.horas == 2.0
    assert (nueva.document_id, nueva.fecha, nueva.fecha_int) == (
        "d-y", FECHA, FINT)
    assert nueva.line_index == 8                 # papelera (7) incluida
    assert (nueva.tipo_hora, nueva.horas, nueva.es_incidencia) == (
        "normal", 8.0, False)
    for campo in ("empleado_ide", "empleado_codigo", "empleado_nombre",
                  "empleado_dni", "empleado_reside", "empleado_match_method",
                  "empleado_match_score", "categoria", "obra_ide",
                  "obra_codigo", "obra_nombre", "partida", "partida_ide",
                  "partida_cod", "partida_res", "partida_capitulo",
                  "partida_match_method", "partida_match_score",
                  "recurso_ide", "recurso_cif", "hora_candef",
                  "recurso_precio_hora", "hmo_ide", "parte_estado"):
        assert getattr(nueva, campo) == getattr(base, campo), campo
    # R21: código de la ordinaria por categoría, como «+ Nuevo».
    assert (nueva.hora_ide, nueva.hora_codigo, nueva.hora_descripcion,
            nueva.hora_ext, nueva.hora_precio_coste,
            nueva.hora_precio_nomina, nueva.hora_match_method) == (
        11, "HN-OF", "HORA LABORABLE OFICIAL", 0, 15.0, 9.0,
        "categoria_normal")
    assert nueva.extra_auto is False
    assert (nueva.horas_orig, nueva.horas_extra_leidas) == (None, None)
    assert (nueva.sigrid_estado, nueva.sigrid_motivo, nueva.sigrid_hmoide,
            nueva.sigrid_hmores_ide, nueva.sigrid_parte_cod) == (
        None, None, None, None, None)
    assert nueva.deleted_at_utc is None
    # R34: misma fila del papel y mismo leído que la persona en el parte.
    assert (nueva.empleado_line_no, nueva.trabajador_nombre_leido) == (
        2, base.trabajador_nombre_leido)
    with fabrica.create_session() as s:
        n = s.get(ParteRegistroOrm, nueva_id)
        assert worker_key_for_registro(n) == WK
        assert obra_key_for_registro(n) == KEY_Y
    assert len(cola.enviados) == 1


def test_f049_r22_respuesta_ok(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(_solo_extra)
    cuerpo = _post(cliente, [(ids["extra"], 10.0, 2.0)],
                   nueva_ordinaria=8.0).json()
    assert set(cuerpo) == {"ok", "editadas", "creadas", "recalculo",
                           "afectadas"}
    assert cuerpo["ok"] is True
    assert cuerpo["editadas"] == [ids["extra"]]
    assert cuerpo["recalculo"] == "pedido"
    assert cuerpo["afectadas"] == []


def test_f049_e1_r21_extra_nueva_con_la_hora_extra_del_recurso(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=2.0)
    assert r.status_code == 200, r.text
    (nueva_id,) = r.json()["creadas"]
    assert r.json()["editadas"] == []
    nueva = _fila(fabrica, nueva_id)
    assert (nueva.tipo_hora, nueva.horas, nueva.line_index) == (
        "extra", 2.0, 1)
    assert (nueva.hora_ide, nueva.hora_codigo, nueva.hora_descripcion,
            nueva.hora_ext, nueva.hora_precio_coste,
            nueva.hora_match_method) == (31, "HE01", "HORA EXTRA", 1, 21.5,
                                         "manual")
    assert ("extra", RECURSO) in SigridFake.llamadas
    assert "tipos" not in SigridFake.llamadas    # solo lo que hace falta
    assert _fila(fabrica, ids["ord"]).horas == 8.0


def test_f049_r21_sin_nuevas_no_se_pregunta_a_sigrid(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(_solo_ordinaria)
    assert _post(cliente, [(ids["ord"], 8.0, 7.0)]).status_code == 200
    assert SigridFake.llamadas == []


@pytest.mark.parametrize("nueva", ["ordinaria", "extra"])
def test_f049_r21_sigrid_caido_crea_sin_codigo_y_avisa(montaje, caplog,
                                                       nueva):
    sembrar = _solo_extra if nueva == "ordinaria" else _solo_ordinaria
    cliente, _repo, fabrica, ids, _cola = montaje(sembrar)
    SigridFake.falla = True
    lineas = ([(ids["extra"], 10.0, 10.0)] if nueva == "ordinaria"
              else [(ids["ord"], 8.0, 8.0)])
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, lineas, **{f"nueva_{nueva}": 2.0})
    assert r.status_code == 200, r.text
    n = _fila(fabrica, r.json()["creadas"][0])
    assert (n.hora_ide, n.hora_codigo, n.hora_ext,
            n.hora_match_method) == (None, None, None, None)
    assert any("[celda]" in m.getMessage() for m in caplog.records
               if m.levelno == logging.WARNING)


@pytest.mark.parametrize("nueva", ["ordinaria", "extra"])
def test_f049_r21_sin_codigo_crea_sin_codigo_y_avisa(montaje, caplog, nueva):
    def sembrar(s):
        ids = (_solo_extra if nueva == "ordinaria" else _solo_ordinaria)(s)
        s.flush()
        for r in s.execute(select(ParteRegistroOrm)).scalars():
            r.categoria = "SIN PARECIDO"
        return ids
    cliente, _repo, fabrica, ids, _cola = montaje(sembrar)
    SigridFake.sin_extra = True
    lineas = ([(ids["extra"], 10.0, 10.0)] if nueva == "ordinaria"
              else [(ids["ord"], 8.0, 8.0)])
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, lineas, **{f"nueva_{nueva}": 2.0})
    n = _fila(fabrica, r.json()["creadas"][0])
    assert (n.hora_ide, n.hora_codigo) == (None, None)
    assert any("[celda]" in m.getMessage() for m in caplog.records
               if m.levelno == logging.WARNING)


def test_f049_r21_sin_sigrid_configurado_crea_sin_codigo(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria,
                                                  con_sigrid=False)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=1.5)
    assert r.status_code == 200, r.text
    n = _fila(fabrica, r.json()["creadas"][0])
    assert (n.tipo_hora, n.horas, n.hora_codigo) == ("extra", 1.5, None)


# ===================== E9/E10 · celda de F-050 ========================= #

def _f050_e1(s, *, con_manual: bool = True) -> dict:
    """F-050 E1: la IA leyó una extra de 2 (fila 3, sin ficha, casada por
    DNI al recurso 6001); el alta manual añadió la ordinaria de 8 (fila 1,
    recurso elegido, sin `recurso_ide`) en el mismo parte."""
    _doc(s, "d-e1", OBRA_Y)
    ids = {"ia": _reg(
        s, "d-e1", OBRA_Y, 0, tipo="extra", horas=2.0, empleado_line_no=3,
        recurso=6001, empleado_ide=None, empleado_match_method="recurso_dni",
        empleado_dni="00000061A", empleado_nombre=None,
        trabajador_nombre_leido="Nombre Apellido")}
    if con_manual:
        ids["manual"] = _reg(
            s, "d-e1", OBRA_Y, 1, empleado_line_no=1, recurso=None,
            empleado_ide=None, empleado_reside=6001,
            empleado_match_method="recurso_manual", empleado_dni="00000061A",
            empleado_nombre="APELLIDO NOMBRE",
            trabajador_nombre_leido="APELLIDO NOMBRE")
    return ids


def test_f049_e9_celda_de_f050_edita_solo_la_extra(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_f050_e1)
    r = _post(cliente, [(ids["manual"], 8.0, 8.0), (ids["ia"], 2.0, 3.0)],
              wk="rec-6001")
    assert r.status_code == 200, r.text
    assert r.json()["editadas"] == [ids["ia"]]
    assert _fila(fabrica, ids["ia"]).horas == 3.0
    assert _fila(fabrica, ids["manual"]).horas == 8.0


def test_f049_e10_r34_ordinaria_nueva_en_la_fila_del_papel(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(
        lambda s: _f050_e1(s, con_manual=False))
    r = _post(cliente, [(ids["ia"], 2.0, 2.0)], nueva_ordinaria=8.0,
              wk="rec-6001")
    assert r.status_code == 200, r.text
    (nueva_id,) = r.json()["creadas"]
    n = _fila(fabrica, nueva_id)
    assert (n.empleado_line_no, n.trabajador_nombre_leido) == (
        3, "Nombre Apellido")
    with fabrica.create_session() as s:
        assert worker_key_for_registro(s.get(ParteRegistroOrm,
                                             nueva_id)) == "rec-6001"
    matriz = _celda_de_la_matriz(ParteReviewRepository(fabrica),
                                 wk="rec-6001")
    assert sorted(x["id"] for x in matriz.regs) == sorted(
        [ids["ia"], nueva_id])


# ===================== E4/E5 · materializar (R18) ====================== #

def test_f049_e4_r18_materializa_solo_la_pareja_tocada(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_pareja)
    r = _post(cliente, [(ids["base"], 8.0, 8.0), (ids["auto"], 2.0, 3.0),
                        (ids["base2"], 1.0, 1.0), (ids["auto2"], 0.5, 0.5)])
    assert r.status_code == 200, r.text
    base, auto = _fila(fabrica, ids["base"]), _fila(fabrica, ids["auto"])
    assert (base.horas, base.horas_orig, base.extra_auto) == (8.0, None,
                                                              False)
    assert (auto.horas, auto.horas_orig, auto.extra_auto) == (3.0, None,
                                                              False)
    assert base.horas_extra_leidas == 2.0                 # F-048, intacta
    base2, auto2 = _fila(fabrica, ids["base2"]), _fila(fabrica, ids["auto2"])
    assert (base2.horas_orig, auto2.extra_auto) == (1.5, True)
    assert sorted(r.json()["editadas"]) == sorted([ids["base"], ids["auto"]])


def test_f049_e5_r18_cambiar_la_base_materializa_con_su_valor(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_pareja)
    _post(cliente, [(ids["base"], 8.0, 7.0), (ids["auto"], 2.0, 2.0),
                    (ids["base2"], 1.0, 1.0), (ids["auto2"], 0.5, 0.5)])
    base, auto = _fila(fabrica, ids["base"]), _fila(fabrica, ids["auto"])
    assert (base.horas, base.horas_orig, auto.horas, auto.extra_auto) == (
        7.0, None, 2.0, False)


def test_f049_e6_r17_a_cero_se_queda_a_cero(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    assert _post(cliente, [(ids["ord"], 8.0, 0.0)]).status_code == 200
    linea = _fila(fabrica, ids["ord"])
    assert (linea.horas, linea.deleted_at_utc) == (0.0, None)


# ================== R14, R15, R33 · 409 sin escribir =================== #

def _dos_partes(s, *, aprobado: bool = True) -> dict:
    """Una celda con una línea libre (d-y) y otra de un parte aprobado."""
    _doc(s, "d-y", OBRA_Y)
    _doc(s, "d-y2", OBRA_Y, aprobado=aprobado)
    return {"libre": _reg(s, "d-y", OBRA_Y, 0, tipo="extra", horas=2.0),
            "congelada": _reg(s, "d-y2", OBRA_Y, 0, horas=8.0)}


def _sin_cambios(fabrica, ids) -> None:
    for rid, horas in ids.items():
        assert _fila(fabrica, rid).horas == horas


def test_f049_r14_linea_congelada_es_409_con_su_motivo(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_dos_partes)
    r = _post(cliente, [(ids["libre"], 2.0, 3.0),
                        (ids["congelada"], 8.0, 7.0)])
    assert r.status_code == 409
    assert r.json()["congelado"] is True and "aprobado" in r.json()["error"]
    _sin_cambios(fabrica, {ids["libre"]: 2.0, ids["congelada"]: 8.0})
    assert _undos(fabrica) == [] and cola.enviados == []


def test_f049_r14_la_congelada_no_se_envia_y_lo_libre_se_guarda(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_dos_partes)
    r = _post(cliente, [(ids["libre"], 2.0, 3.0)])
    assert r.status_code == 200, r.text
    assert _fila(fabrica, ids["libre"]).horas == 3.0


def test_f049_r15_parte_en_espera_es_409(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_solo_ordinaria)
    _poner_pedido(fabrica, "d-y", "pedido-en-curso")
    r = _post(cliente, [(ids["ord"], 8.0, 7.0)])
    assert r.status_code == 409
    assert r.json()["error"] == MOTIVO_RECALCULANDO
    _sin_cambios(fabrica, {ids["ord"]: 8.0})
    assert _undos(fabrica) == [] and cola.enviados == []


def test_f049_r15_espera_de_la_plantilla_tambien_con_nueva(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    _poner_pedido(fabrica, "d-y", "pedido-en-curso")
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=2.0)
    assert r.status_code == 409
    assert len(_lineas_doc(fabrica, "d-y")) == 1


def _reparto(fabrica, estado: str, *, recurso: int = RECURSO,
             fecha_int: int = FINT) -> None:
    with fabrica.create_session() as s:
        s.add(RepartoPendienteOrm(recurso_ide=recurso, fecha_int=fecha_int,
                                  estado=estado, firma="f", cambios="{}",
                                  creado_at_utc=AHORA,
                                  actualizado_at_utc=AHORA))
        s.commit()


def test_f049_e11_r33_reparto_aplicando_es_409(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_solo_ordinaria)
    _reparto(fabrica, "aplicando")
    r = _post(cliente, [(ids["ord"], 8.0, 7.0)], nueva_extra=1.0)
    assert r.status_code == 409
    assert r.json() == {"ok": False, "error": MOTIVO_REPARTO_APLICANDO}
    assert MOTIVO_REPARTO_APLICANDO == ("Este día tiene un reajuste en "
                                        "Sigrid en curso: espera a que "
                                        "termine.")
    _sin_cambios(fabrica, {ids["ord"]: 8.0})
    assert len(_lineas_doc(fabrica, "d-y")) == 1
    assert _undos(fabrica) == [] and cola.enviados == []


@pytest.mark.parametrize("estado", ["pendiente", "rechazado", "aplicado"])
def test_f049_r33_otros_estados_del_reparto_no_bloquean(montaje, estado):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    _reparto(fabrica, estado)
    assert _post(cliente, [(ids["ord"], 8.0, 7.0)]).status_code == 200


def test_f049_r33_aplicando_de_otro_dia_o_recurso_no_bloquea(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    _reparto(fabrica, "aplicando", fecha_int=FINT + 1)
    _reparto(fabrica, "aplicando", recurso=999)
    assert _post(cliente, [(ids["ord"], 8.0, 7.0)]).status_code == 200


# =========================== R12 · 409 recarga =========================== #

def _recarga(r) -> None:
    assert r.status_code == 409, r.text
    assert r.json() == {"ok": False, "error": MOTIVO_CELDA_CAMBIADA}


def test_f049_r12_antes_obsoleto(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_solo_ordinaria)
    _recarga(_post(cliente, [(ids["ord"], 7.0, 6.0)]))
    _sin_cambios(fabrica, {ids["ord"]: 8.0})
    assert _undos(fabrica) == [] and cola.enviados == []


def test_f049_r12_nueva_que_ya_aparecio(montaje):
    def sembrar(s):
        ids = _solo_ordinaria(s)
        ids["extra"] = _reg(s, "d-y", OBRA_Y, 1, tipo="extra", horas=1.0)
        return ids
    cliente, _repo, fabrica, ids, _cola = montaje(sembrar)
    _recarga(_post(cliente, [(ids["ord"], 8.0, 8.0),
                             (ids["extra"], 1.0, 1.0)], nueva_extra=2.0))
    assert len(_lineas_doc(fabrica, "d-y")) == 2


def test_f049_r12_linea_movida_a_otro_dia(montaje):
    def sembrar(s):
        ids = _solo_ordinaria(s)
        ids["movida"] = _reg(s, "d-y", OBRA_Y, 1, tipo="extra", horas=1.0,
                             fecha="2026-10-15")
        return ids
    cliente, _repo, fabrica, ids, _cola = montaje(sembrar)
    _recarga(_post(cliente, [(ids["ord"], 8.0, 7.0),
                             (ids["movida"], 1.0, 2.0)]))
    _sin_cambios(fabrica, {ids["ord"]: 8.0, ids["movida"]: 1.0})


@pytest.mark.parametrize("wk", ["emp-999", "nom-OTRO", "rec-77"])
def test_f049_r12_clave_sin_celda(montaje, wk):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    _recarga(_post(cliente, [(ids["ord"], 8.0, 7.0)], wk=wk))
    _sin_cambios(fabrica, {ids["ord"]: 8.0})


def test_f049_r12_otra_obra_u_otra_fecha_sin_celda(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    _recarga(_post(cliente, [(ids["ord"], 8.0, 7.0)], obra_key=KEY_X))
    _recarga(_post(cliente, [(ids["ord"], 8.0, 7.0)], fecha="2026-10-15"))
    _sin_cambios(fabrica, {ids["ord"]: 8.0})


def test_f049_r12_plantilla_distinta_de_la_esperada(montaje):
    _cliente, repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    with pytest.raises(CeldaInvalida) as exc:
        repo.guardar_celda(
            obra_key=KEY_Y, worker_key=WK, fecha_iso=FECHA,
            cambios=[Cambio(ids["ord"], 8.0, 8.0)], nueva_ordinaria=None,
            nueva_extra=2.0, hora_ordinaria=None, hora_extra=None,
            plantilla_esperada=ids["ord"] + 1, by=ACTOR)
    assert (exc.value.status, str(exc.value)) == (409, MOTIVO_CELDA_CAMBIADA)
    assert len(_lineas_doc(fabrica, "d-y")) == 1


def test_f049_r12_incidencia_y_papelera_no_son_de_la_celda(montaje):
    def sembrar(s):
        ids = _solo_ordinaria(s)
        _reg(s, "d-y", OBRA_Y, 1, tipo="V", horas=None, es_incidencia=True,
             incidencia_codigo="V")
        _reg(s, "d-y", OBRA_Y, 2, tipo="extra", horas=1.0,
             deleted_at_utc=AHORA)
        return ids
    cliente, _repo, fabrica, ids, _cola = montaje(sembrar)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=1.0)
    assert r.status_code == 200, r.text
    assert _fila(fabrica, r.json()["creadas"][0]).line_index == 3


def test_f049_r12_parte_en_papelera_no_es_de_la_celda(montaje):
    def sembrar(s):
        ids = _solo_ordinaria(s)
        _doc(s, "d-borrado", OBRA_Y)
        ids["borrado"] = _reg(s, "d-borrado", OBRA_Y, 0, tipo="extra",
                              horas=1.0)
        s.get(ParteDocumentOrm, "d-borrado").is_active = False
        return ids
    cliente, _repo, _fabrica, ids, _cola = montaje(sembrar)
    _recarga(_post(cliente, [(ids["ord"], 8.0, 8.0),
                             (ids["borrado"], 1.0, 2.0)]))
    assert _post(cliente, [(ids["ord"], 8.0, 8.0)],
                 nueva_extra=1.0).status_code == 200


# ============================ R11, R13, R35 ============================== #

@pytest.mark.parametrize("cuerpo", [
    {"worker_key": WK, "fecha": FECHA, "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": KEY_Y, "fecha": FECHA, "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": KEY_Y, "worker_key": WK, "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": "", "worker_key": WK, "fecha": FECHA,
     "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": KEY_Y, "worker_key": "", "fecha": FECHA,
     "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": KEY_Y, "worker_key": WK, "fecha": "14/10/2026",
     "lineas": [{"id": 1, "antes": 8}]},
    {"obra_key": KEY_Y, "worker_key": WK, "fecha": FECHA},
])
def test_f049_r11_peticion_mal_formada_es_422(montaje, cuerpo):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = cliente.post("/api/matriz/celda", json=cuerpo, headers=CABECERA)
    assert r.status_code == 422, r.text
    _sin_cambios(fabrica, {ids["ord"]: 8.0})


def test_f049_r11_lineas_vacias_o_repetidas_es_422(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [])
    assert r.status_code == 422 and r.json()["ok"] is False
    assert r.json()["error"]
    r = _post(cliente, [(ids["ord"], 8.0, 7.0), (ids["ord"], 8.0, 6.0)])
    assert r.status_code == 422
    _sin_cambios(fabrica, {ids["ord"]: 8.0})


@pytest.mark.parametrize("lineas,nuevas", [
    ([("ord", 8.0, 25.0)], {}),
    ([("ord", 8.0, -1.0)], {}),
    ([("ord", 8.0, 8.0)], {"nueva_extra": 30.0}),
])
def test_f049_r13_fuera_de_rango_es_422(montaje, lineas, nuevas):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids[i], a, h) for i, a, h in lineas], **nuevas)
    assert r.status_code == 422 and r.json()["ok"] is False
    _sin_cambios(fabrica, {ids["ord"]: 8.0})
    assert len(_lineas_doc(fabrica, "d-y")) == 1


def test_f049_r13_ordinaria_nueva_a_cero_es_422(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(_solo_extra)
    r = _post(cliente, [(ids["extra"], 10.0, 10.0)], nueva_ordinaria=0.0)
    assert r.status_code == 422


def _sin_trabajador(s) -> dict:
    _doc(s, "d-y", OBRA_Y)
    return {"ord": _reg(s, "d-y", OBRA_Y, 0, recurso=None, empleado_ide=None,
                        empleado_dni=None, empleado_nombre=None,
                        trabajador_nombre_leido=None, recurso_cif=None)}


def test_f049_r35_sin_trabajador_no_crea_pero_edita(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_sin_trabajador)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=2.0,
              wk="sin-trabajador")
    assert r.status_code == 422 and r.json()["ok"] is False
    assert len(_lineas_doc(fabrica, "d-y")) == 1
    r = _post(cliente, [(ids["ord"], 8.0, 6.0)], wk="sin-trabajador")
    assert r.status_code == 200, r.text
    assert _fila(fabrica, ids["ord"]).horas == 6.0
    assert r.json()["afectadas"] == []


# =============================== R16 =================================== #

def test_f049_r16_todo_o_nada(montaje, entorno):
    cliente, _repo, fabrica, ids, cola = montaje(_pareja)

    def revienta(self, session, **_kw):
        raise RuntimeError("undo_log caido")
    entorno.setattr(ParteReviewRepository, "_record_undo", revienta)
    with pytest.raises(RuntimeError):
        _post(cliente, [(ids["base"], 8.0, 7.0), (ids["auto"], 2.0, 2.0),
                        (ids["base2"], 1.0, 1.0), (ids["auto2"], 0.5, 0.5)],
              nueva_ordinaria=None)
    base = _fila(fabrica, ids["base"])
    assert (base.horas, base.horas_orig) == (8.0, 10.0)
    assert _fila(fabrica, ids["auto"]).extra_auto is True
    assert cola.enviados == []


def test_f049_r16_todo_o_nada_tambien_la_creada(montaje, entorno):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_extra)

    def revienta(self, session, **_kw):
        raise RuntimeError("undo_log caido")
    entorno.setattr(ParteReviewRepository, "_record_undo", revienta)
    with pytest.raises(RuntimeError):
        _post(cliente, [(ids["extra"], 10.0, 2.0)], nueva_ordinaria=8.0)
    assert len(_lineas_doc(fabrica, "d-y")) == 3
    assert _fila(fabrica, ids["extra"]).horas == 10.0


def test_f049_r16_una_entrada_de_deshacer_por_guardado(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_extra)
    _post(cliente, [(ids["extra"], 10.0, 2.0)], nueva_ordinaria=8.0)
    (entrada,) = _undos(fabrica)
    assert entrada.action == "celda_edit"


# ========================== R6 · sin cambios ============================ #

def test_f049_r6_sin_cambios_no_escribe_ni_pide(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=0.0)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "editadas": [], "creadas": [],
                        "recalculo": None, "afectadas": []}
    assert _undos(fabrica) == [] and cola.enviados == []
    assert _seguimiento(fabrica, "d-y") == (None, None)


# ===================== E12 · otras obras (R38, R36) ==================== #

AFECTADA_X = {"obra_key": KEY_X, "obra_codigo": f"0{OBRA_X}",
              "document_id": "d-x", "congelada": False}


def test_f049_e12a_r38_afectadas_solo_el_grupo_del_dia(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(_e12)
    r = _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    assert r.status_code == 200, r.text
    assert r.json()["afectadas"] == [AFECTADA_X]


def test_f049_e12b_r38_afectada_congelada(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(
        lambda s: _e12(s, x_aprobada=True))
    r = _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    assert r.json()["afectadas"] == [dict(AFECTADA_X, congelada=True)]


def test_f049_r38_un_elemento_por_documento(montaje):
    def sembrar(s):
        ids = _e12(s)
        _reg(s, "d-x", OBRA_X, 1, tipo="extra", horas=1.0)
        _doc(s, "d-x3", OBRA_X)
        _reg(s, "d-x3", OBRA_X, 0, horas=1.0)
        return ids
    cliente, _repo, _fabrica, ids, _cola = montaje(sembrar)
    afectadas = _otras(cliente).json()["afectadas"]
    assert [a["document_id"] for a in afectadas] == ["d-x", "d-x3"]


def test_f049_r38_congelada_si_alguna_linea_del_documento_lo_esta(montaje):
    def sembrar(s):
        ids = _e12(s)
        _reg(s, "d-x", OBRA_X, 1, tipo="extra", horas=1.0,
             sigrid_estado="registrado")
        return ids
    cliente, _repo, _fabrica, _ids, _cola = montaje(sembrar)
    assert _otras(cliente).json()["afectadas"] == [
        dict(AFECTADA_X, congelada=True)]


def test_f049_r36_r38_get_otras_igual_y_sin_escribir(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_e12)
    r = _otras(cliente)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "afectadas": [AFECTADA_X]}
    assert _undos(fabrica) == [] and cola.enviados == []
    assert _seguimiento(fabrica, "d-x") == (None, None)


def test_f049_r38_get_otras_sin_recurso_o_sin_celda_es_vacia(montaje):
    cliente, _repo, _fabrica, _ids, _cola = montaje(_sin_trabajador)
    assert _otras(cliente, wk="sin-trabajador").json() == {
        "ok": True, "afectadas": []}
    assert _otras(cliente, wk="emp-999").json() == {"ok": True,
                                                    "afectadas": []}


def test_f049_r38_get_otras_fecha_invalida_es_422(montaje):
    cliente, _repo, _fabrica, _ids, _cola = montaje(_e12)
    assert _otras(cliente, fecha="ayer").status_code == 422


# ================= R23, R39 · un pedido compartido ===================== #

def test_f049_e12a_r39_mismo_pedido_en_y_y_x_y_un_solo_mensaje(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_e12)
    r = _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    assert r.json()["recalculo"] == "pedido"
    pedido_y, _ = _seguimiento(fabrica, "d-y")
    pedido_x, _ = _seguimiento(fabrica, "d-x")
    assert pedido_y is not None and pedido_y == pedido_x
    for otro in ("d-x2", "d-z", "d-v", "d-p"):
        assert _seguimiento(fabrica, otro) == (None, None)
    ((_nombre, mensaje),) = cola.enviados
    assert mensaje["document_id"] == "d-y"
    assert mensaje["motivo"] == "edicion_celda"
    assert mensaje["tipo"] == "recalcular"
    assert mensaje["solicitado_por"] == ACTOR


def test_f049_r39_editar_la_afectada_espera_al_recalculo(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_e12)
    _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    r = cliente.patch(f"/api/registros/{ids['x']}", json={"horas": 7.0},
                      headers=CABECERA)
    assert r.status_code == 409
    assert r.json()["error"] == MOTIVO_RECALCULANDO
    assert _fila(fabrica, ids["x"]).horas == 8.0


def test_f049_r39_cola_caida_quita_el_pedido_solo_donde_sigue(montaje):
    cola = ColaFake(error=RuntimeError("cola caida"))
    cliente, _repo, fabrica, ids, _ = montaje(_e12, cola=cola)
    cola.al_enviar = lambda: _poner_pedido(fabrica, "d-x", "pedido-q")
    r = _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    assert r.status_code == 200, r.text
    assert r.json()["recalculo"] == "fallo"
    assert len(r.json()["creadas"]) == 1                 # no se deshace
    assert _seguimiento(fabrica, "d-y") == (None, None)
    assert _seguimiento(fabrica, "d-x") == ("pedido-q", None)


def test_f049_r23_sin_cola_no_marca_pedido(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_e12, sin_cola=True)
    r = _post(cliente, [(ids["y"], 2.0, 3.0)])
    assert r.json()["recalculo"] == "sin_cola"
    assert _seguimiento(fabrica, "d-y") == (None, None)


def test_f049_r23_fallo_al_marcar_publica_igual(montaje, entorno, caplog):
    cliente, repo, fabrica, ids, cola = montaje(_e12)

    def revienta(*_a, **_kw):
        raise RuntimeError("bbdd caida")
    entorno.setattr(repo, "marcar_recalculo_pedido_compartido", revienta)
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, [(ids["y"], 2.0, 3.0)])
    assert r.json()["recalculo"] == "pedido"
    assert len(cola.enviados) == 1
    assert _seguimiento(fabrica, "d-y") == (None, None)
    assert any("marcar" in m.getMessage() for m in caplog.records
               if m.levelno == logging.WARNING)


def test_f049_r23_fallo_al_anular_solo_avisa(montaje, entorno, caplog):
    cola = ColaFake(error=RuntimeError("cola caida"))
    cliente, repo, fabrica, ids, _ = montaje(_e12, cola=cola)

    def revienta(*_a, **_kw):
        raise RuntimeError("bbdd caida")
    entorno.setattr(repo, "anular_recalculo_pedido_compartido", revienta)
    with caplog.at_level(logging.WARNING):
        r = _post(cliente, [(ids["y"], 2.0, 3.0)])
    assert r.status_code == 200 and r.json()["recalculo"] == "fallo"
    assert _seguimiento(fabrica, "d-y")[0] is not None
    assert any("anular" in m.getMessage() for m in caplog.records
               if m.levelno == logging.WARNING)


def test_f049_r23_marcar_sin_filas_no_anula(montaje, entorno):
    """Si no se marcó ningún documento, no hay nada que anular."""
    cola = ColaFake(error=RuntimeError("cola caida"))
    cliente, repo, _fabrica, ids, _ = montaje(_e12, cola=cola)
    anuladas: list = []
    entorno.setattr(repo, "marcar_recalculo_pedido_compartido",
                    lambda *_a, **_kw: 0)
    entorno.setattr(repo, "anular_recalculo_pedido_compartido",
                    lambda *a, **kw: anuladas.append((a, kw)))
    assert _post(cliente, [(ids["y"], 2.0, 3.0)]).json()["recalculo"] \
        == "fallo"
    assert anuladas == []


def test_f049_r39_marcar_compartido_una_sentencia_y_rowcount(montaje):
    _cliente, repo, fabrica, _ids, _cola = montaje(_e12)
    assert repo.marcar_recalculo_pedido_compartido(
        ["d-y", "d-x", "d-y", "no-existe"], peticion_id="p-1") == 2
    assert _seguimiento(fabrica, "d-y") == ("p-1", None)
    assert _seguimiento(fabrica, "d-x") == ("p-1", None)
    assert _seguimiento(fabrica, "d-z") == (None, None)
    assert repo.marcar_recalculo_pedido_compartido([], peticion_id="p-2") == 0


def test_f049_r39_marcar_compartido_anota_la_hora(montaje):
    _cliente, repo, fabrica, _ids, _cola = montaje(_e12)
    hora = datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc)
    repo.marcar_recalculo_pedido_compartido(["d-y"], peticion_id="p-1",
                                            ahora_utc=hora)
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, "d-y").recalculo_pedido_at_utc \
            == hora.isoformat()


def test_f049_r39_marcar_compartido_hora_por_defecto(montaje):
    _cliente, repo, fabrica, _ids, _cola = montaje(_e12)
    antes = datetime.now(timezone.utc)
    repo.marcar_recalculo_pedido_compartido(["d-y"], peticion_id="p-1")
    with fabrica.create_session() as s:
        hora = datetime.fromisoformat(
            s.get(ParteDocumentOrm, "d-y").recalculo_pedido_at_utc)
    assert (hora - antes).total_seconds() < 5


def test_f049_r39_anular_compartido_respeta_un_pedido_posterior(montaje):
    _cliente, repo, fabrica, _ids, _cola = montaje(_e12)
    repo.marcar_recalculo_pedido_compartido(["d-y", "d-x"],
                                            peticion_id="p-1")
    _poner_pedido(fabrica, "d-x", "p-2")
    repo.anular_recalculo_pedido_compartido(["d-y", "d-x"],
                                            peticion_id="p-1")
    with fabrica.create_session() as s:
        y = s.get(ParteDocumentOrm, "d-y")
        assert (y.recalculo_pedido_id, y.recalculo_pedido_at_utc) == (
            None, None)
    assert _seguimiento(fabrica, "d-x") == ("p-2", None)


# ============================= R24 · traza ============================== #

def test_f049_r24_info_celda_sin_datos_personales(montaje, caplog):
    cliente, _repo, fabrica, ids, _cola = montaje(_e12)
    with caplog.at_level(logging.INFO):
        r = _post(cliente, [(ids["y"], 2.0, 2.5)], nueva_ordinaria=2.0)
    pedido, _ = _seguimiento(fabrica, "d-y")
    (traza,) = [m.getMessage() for m in caplog.records
                if m.getMessage().startswith("[celda] guardada")]
    (nueva,) = r.json()["creadas"]
    for trozo in (str(ids["y"]), str(nueva), "d-y", "d-x", pedido,
                  "recalculo=pedido"):
        assert trozo in traza, trozo
    for prohibido in ("Persona Siete", "P. Siete", "00000077A", WK):
        assert prohibido not in traza


# ====================== contexto del repositorio ======================= #

def test_f049_contexto_celda(montaje):
    _cliente, repo, _fabrica, ids, _cola = montaje(_solo_extra)
    assert repo.contexto_celda(obra_key=KEY_Y, worker_key=WK,
                               fecha_iso=FECHA) == {
        "plantilla_id": ids["extra"], "reside": RECURSO,
        "categoria": "OFICIAL 1ª"}
    assert repo.contexto_celda(obra_key=KEY_Y, worker_key="emp-1",
                               fecha_iso=FECHA) is None


def test_f049_contexto_celda_reside_del_recurso_elegido(montaje):
    _cliente, repo, _fabrica, ids, _cola = montaje(_f050_e1)
    ctx = repo.contexto_celda(obra_key=KEY_Y, worker_key="rec-6001",
                              fecha_iso=FECHA)
    assert ctx["plantilla_id"] == ids["manual"]
    assert ctx["reside"] == 6001


def test_f049_contexto_celda_toda_congelada(montaje):
    def sembrar(s):
        _doc(s, "d-y", OBRA_Y, aprobado=True)
        return {"ord": _reg(s, "d-y", OBRA_Y, 0)}
    cliente, repo, _fabrica, ids, _cola = montaje(sembrar)
    assert repo.contexto_celda(obra_key=KEY_Y, worker_key=WK,
                               fecha_iso=FECHA) == {
        "plantilla_id": None, "reside": None, "categoria": None}
    r = _post(cliente, [(ids["ord"], 8.0, 7.0)])
    assert r.status_code == 409 and r.json()["congelado"] is True


def test_f049_otras_de_celda_del_repositorio(montaje):
    _cliente, repo, _fabrica, _ids, _cola = montaje(_e12)
    assert repo.otras_de_celda(obra_key=KEY_Y, worker_key=WK,
                               fecha_iso=FECHA) == [AFECTADA_X]
    assert repo.otras_de_celda(obra_key=KEY_X, worker_key=WK,
                               fecha_iso=FECHA) == [
        {"obra_key": KEY_Y, "obra_codigo": f"0{OBRA_Y}",
         "document_id": "d-y", "congelada": False}]


# ======================================================================= #
# T9 · deshacer `celda_edit` (R25-R28)
# ======================================================================= #

import json  # noqa: E402


def _undo(cliente):
    return cliente.post("/api/undo", headers=CABECERA)


def _payload_undo(fabrica) -> dict:
    (entrada,) = _undos(fabrica)
    return json.loads(entrada.payload)


def _guardar_pareja(cliente, ids):
    r = _post(cliente, [(ids["base"], 8.0, 8.0), (ids["auto"], 2.0, 3.0),
                        (ids["base2"], 1.0, 1.0), (ids["auto2"], 0.5, 0.5)])
    assert r.status_code == 200, r.text
    return r


def test_f049_r25_entrada_con_marcas_documento_y_creadas(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_pareja)
    _guardar_pareja(cliente, ids)
    payload = _payload_undo(fabrica)
    por_id = {s["id"]: s for s in payload["registros"]}
    assert set(por_id) == {ids["base"], ids["auto"]}
    assert (por_id[ids["base"]]["horas"], por_id[ids["base"]]["horas_orig"],
            por_id[ids["base"]]["extra_auto"],
            por_id[ids["base"]]["document_id"]) == (8.0, 10.0, False, "d-y")
    assert (por_id[ids["auto"]]["horas"], por_id[ids["auto"]]["horas_orig"],
            por_id[ids["auto"]]["extra_auto"]) == (2.0, None, True)
    assert por_id[ids["auto"]]["hora_codigo"] == "HL01"     # los de siempre
    assert payload["creadas"] == []


def test_f049_r25_entrada_con_las_creadas(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_extra)
    r = _post(cliente, [(ids["extra"], 10.0, 2.0)], nueva_ordinaria=8.0)
    payload = _payload_undo(fabrica)
    assert payload["creadas"] == r.json()["creadas"]
    assert [s["id"] for s in payload["registros"]] == [ids["extra"]]
    assert (_undos(fabrica)[0].description
            == "Editar celda · Persona Siete (2026-10-14)")


def test_f049_r26_deshacer_restaura_horas_y_marcas(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_pareja)
    _guardar_pareja(cliente, ids)
    r = _undo(cliente)
    assert r.status_code == 200, r.text
    base, auto = _fila(fabrica, ids["base"]), _fila(fabrica, ids["auto"])
    assert (base.horas, base.horas_orig, base.extra_auto) == (8.0, 10.0,
                                                              False)
    assert (auto.horas, auto.horas_orig, auto.extra_auto) == (2.0, None,
                                                              True)
    cuerpo = r.json()
    assert cuerpo["action"] == "celda_edit"
    assert cuerpo["document_ids"] == ["d-y"]
    assert cuerpo["afectadas"] == []
    assert cuerpo["omitidos"] == 0


def test_f049_r26_deshacer_manda_las_creadas_a_la_papelera(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_extra)
    r = _post(cliente, [(ids["extra"], 10.0, 2.0)], nueva_ordinaria=8.0)
    (nueva,) = r.json()["creadas"]
    cuerpo = _undo(cliente).json()
    assert cuerpo["ok"] is True
    linea = _fila(fabrica, nueva)
    assert linea.deleted_at_utc is not None
    assert linea.deleted_by == ACTOR
    assert _fila(fabrica, ids["extra"]).horas == 10.0
    assert cuerpo["document_ids"] == ["d-y"]


def test_f049_r26_solo_creada_da_su_documento(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=2.0)
    (nueva,) = r.json()["creadas"]
    cuerpo = _undo(cliente).json()
    assert cuerpo["document_ids"] == ["d-y"]
    assert _fila(fabrica, nueva).deleted_at_utc is not None


def test_f049_r26_creada_hoy_congelada_no_se_toca(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids["ord"], 8.0, 7.0)], nueva_extra=2.0)
    (nueva,) = r.json()["creadas"]
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, nueva).sigrid_estado = "registrado"
        s.commit()
    cuerpo = _undo(cliente).json()
    assert cuerpo["omitidos"] == 1
    assert _fila(fabrica, nueva).deleted_at_utc is None
    assert _fila(fabrica, ids["ord"]).horas == 8.0


def test_f049_r26_creada_ya_borrada_no_se_vuelve_a_borrar(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    r = _post(cliente, [(ids["ord"], 8.0, 8.0)], nueva_extra=2.0)
    (nueva,) = r.json()["creadas"]
    with fabrica.create_session() as s:
        linea = s.get(ParteRegistroOrm, nueva)
        linea.deleted_at_utc, linea.deleted_by = AHORA, "otra"
        s.commit()
    cuerpo = _undo(cliente).json()
    assert cuerpo["omitidos"] == 0
    assert (_fila(fabrica, nueva).deleted_at_utc,
            _fila(fabrica, nueva).deleted_by) == (AHORA, "otra")


def test_f049_r26_snapshot_hoy_congelado_se_omite(montaje):
    cliente, _repo, fabrica, ids, _cola = montaje(_pareja)
    _guardar_pareja(cliente, ids)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["auto"]).sigrid_estado = "registrado"
        s.commit()
    cuerpo = _undo(cliente).json()
    assert cuerpo["omitidos"] == 1
    auto = _fila(fabrica, ids["auto"])
    assert (auto.horas, auto.extra_auto) == (3.0, False)
    assert _fila(fabrica, ids["base"]).horas_orig == 10.0


def test_f049_r26_r27_deshacer_e12_pide_un_recalculo_compartido(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_e12)
    _post(cliente, [(ids["y"], 2.0, 2.0)], nueva_ordinaria=2.0)
    pedido_guardar, _ = _seguimiento(fabrica, "d-y")
    cuerpo = _undo(cliente).json()
    assert cuerpo["afectadas"] == [AFECTADA_X]
    assert cuerpo["recalculo"] == "pedido"
    assert len(cola.enviados) == 2
    _nombre, mensaje = cola.enviados[1]
    assert (mensaje["document_id"], mensaje["motivo"]) == (
        "d-y", "deshacer_edicion_celda")
    pedido_y, _ = _seguimiento(fabrica, "d-y")
    pedido_x, _ = _seguimiento(fabrica, "d-x")
    assert pedido_y == pedido_x and pedido_y != pedido_guardar
    assert _seguimiento(fabrica, "d-z") == (None, None)


def test_f049_r27_deshacer_sin_cola(montaje):
    cliente, _repo, _fabrica, ids, _cola = montaje(_solo_ordinaria,
                                                   sin_cola=True)
    _post(cliente, [(ids["ord"], 8.0, 7.0)])
    assert _undo(cliente).json()["recalculo"] == "sin_cola"


def test_f049_r27_deshacer_todo_congelado_pide_igual_su_documento(montaje):
    """Todo hoy congelado: nada se restaura, pero el documento de la
    entrada se recalcula igual (deshacer no mira la congelación)."""
    cliente, _repo, fabrica, ids, cola = montaje(_solo_ordinaria)
    _post(cliente, [(ids["ord"], 8.0, 7.0)])
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "d-y").approved = True
        s.commit()
    cuerpo = _undo(cliente).json()
    assert cuerpo["omitidos"] == 1
    assert cuerpo["document_ids"] == ["d-y"]
    assert cuerpo["recalculo"] == "pedido"
    assert len(cola.enviados) == 2


def test_f049_r28_deshacer_otra_accion_no_restaura_marcas(montaje):
    cliente, _repo, fabrica, ids, cola = montaje(_pareja)
    assert cliente.patch(f"/api/registros/{ids['base']}",
                         json={"horas": 7.0},
                         headers=CABECERA).status_code == 200
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids["base"]).horas_orig = 5.0
        s.commit()
    cuerpo = _undo(cliente).json()
    base = _fila(fabrica, ids["base"])
    assert (base.horas, base.horas_orig) == (8.0, 5.0)
    assert cuerpo["action"] == "registro_edit"
    assert "recalculo" not in cuerpo and "afectadas" not in cuerpo
    assert cola.enviados == []
    assert "creadas" not in json.loads(_undos(fabrica)[0].payload)


def test_f049_r28_undo_last_sin_actor_sigue_valiendo(montaje):
    _cliente, repo, fabrica, ids, _cola = montaje(_solo_ordinaria)
    repo.guardar_celda(
        obra_key=KEY_Y, worker_key=WK, fecha_iso=FECHA,
        cambios=[Cambio(ids["ord"], 8.0, 8.0)], nueva_ordinaria=None,
        nueva_extra=2.0, hora_ordinaria=None, hora_extra=None,
        plantilla_esperada=ids["ord"], by=None)
    res = repo.undo_last()
    assert res["ok"] is True and res["action"] == "celda_edit"
    nueva = _lineas_doc(fabrica, "d-y")[-1]
    assert nueva.deleted_at_utc is not None and nueva.deleted_by is None
