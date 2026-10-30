# tests/test_f047_parte_nuevo_sv4.py
"""F-047 · R11-R18: el parte nuevo «en espera» en sv4 (servidor).

sv3 escribe `recalculo_pedido_id` = id del documento al guardar un parte
nuevo. sv4 deduce de ahí el motivo de la espera (`nuevo` o `recalculo`,
R11-R12), lo pinta en las vistas (R13-R14, R18), mantiene el 409 de F-043
(R15) y no aprueba un parte en espera (R16-R17, DA3).

Sin red: repositorio real sobre SQLite, reloj fijo. Datos sintéticos.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, update

from application.services.seguimiento_recalculo import (
    MOTIVO_NUEVO,
    MOTIVO_RECALCULO,
    motivo_espera,
)
from infrastructure.database import parte_repository as modulo_repo
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, sembrar_parte

AHORA = datetime(2026, 10, 30, 9, 0, 0, tzinfo=timezone.utc)
PID = "00000000-0000-4000-8000-00000000000a"
PID2 = "00000000-0000-4000-8000-00000000000b"


def _hace(segundos: float) -> str:
    return (AHORA - timedelta(seconds=segundos)).isoformat()


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("COLA_PERSISTENCIA", raising=False)
    monkeypatch.setattr(modulo_repo, "_ahora_utc", lambda: AHORA)
    return monkeypatch


@pytest.fixture
def fabrica():
    return FabricaSesionSqlite()


def _poner_marca(fabrica, document_id: str, *, pedido: str | None,
                 pedido_at: str | None, terminado: str | None = None) -> None:
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(recalculo_pedido_id=pedido,
                          recalculo_pedido_at_utc=pedido_at,
                          recalculo_terminado_id=terminado))
        s.commit()


# ================================ R11 ================================== #

def test_f047_r11_constantes_del_motivo() -> None:
    assert (MOTIVO_NUEVO, MOTIVO_RECALCULO) == ("nuevo", "recalculo")


@pytest.mark.parametrize("document_id, pedido_id, esperado", [
    ("doc-1", "doc-1", "nuevo"),
    ("doc-1", PID, "recalculo"),
    ("doc-1", None, "recalculo"),
    ("doc-1", "", "recalculo"),
    ("", "", "recalculo"),
    (None, None, "recalculo"),
])
def test_f047_r11_motivo_espera(document_id, pedido_id, esperado) -> None:
    assert motivo_espera(document_id, pedido_id) == esperado


# ================================ R12 ================================== #

#: (document_id, pedido, segundos desde el pedido, terminado, en papelera)
CASOS_R12 = [
    ("d-nuevo", "d-nuevo", 30, None, False),            # pendiente, nuevo
    ("d-borde", "d-borde", 600, None, False),           # pendiente (borde)
    ("d-recalc", PID2, 30, PID, False),                  # pendiente, recalc.
    ("d-nuevo-term", "d-nuevo-term", 30, "d-nuevo-term", False),
    ("d-nuevo-venc", "d-nuevo-venc", 601, None, False),  # vencido
    ("d-sin", None, None, None, False),                  # sin seguimiento
    ("d-papelera", "d-papelera", 30, None, True),        # en papelera
]
ESPERADO_R12 = {"d-nuevo": "nuevo", "d-borde": "nuevo",
                "d-recalc": "recalculo"}


@pytest.fixture
def siete(entorno, fabrica):
    for i, (doc, pedido, segundos, terminado, papelera) in enumerate(
            CASOS_R12):
        sembrar_parte(fabrica, [{"horas": 8.0}], document_id=doc,
                      empleado_ide=100 + i, doc_en_papelera=papelera)
        _poner_marca(fabrica, doc, pedido=pedido,
                     pedido_at=None if segundos is None else _hace(segundos),
                     terminado=terminado)
    return ParteReviewRepository(fabrica)


def _sentencias(fabrica, funcion) -> tuple:
    sentencias: list[str] = []

    def _anotar(_conn, _cursor, sentencia, *_a):
        sentencias.append(sentencia)

    event.listen(fabrica.engine, "before_cursor_execute", _anotar)
    try:
        resultado = funcion()
    finally:
        event.remove(fabrica.engine, "before_cursor_execute", _anotar)
    return resultado, [s for s in sentencias
                       if s.lstrip().upper().startswith("SELECT")]


def test_f047_r12_motivos_de_los_ids_en_una_consulta(siete,
                                                       fabrica) -> None:
    ids = [c[0] for c in CASOS_R12] + ["no-existe", None, "d-nuevo"]
    motivos, selects = _sentencias(fabrica, lambda: siete.motivos_espera(ids))
    assert motivos == ESPERADO_R12
    assert len(selects) == 1


def test_f047_r12_motivos_de_toda_la_base(siete, fabrica) -> None:
    motivos, selects = _sentencias(fabrica,
                                   lambda: siete.motivos_espera(None))
    assert motivos == ESPERADO_R12
    assert len(selects) == 1
    # Filtrada en la base: activos con pedido distinto del terminado.
    consulta = " ".join(selects[0].split())
    assert "parte_documents.is_active IS 1" in consulta
    assert "parte_documents.recalculo_pedido_id IS NOT NULL" in consulta
    assert ("parte_documents.recalculo_terminado_id IS NULL OR "
            "parte_documents.recalculo_terminado_id != "
            "parte_documents.recalculo_pedido_id") in consulta


@pytest.mark.parametrize("ids", [[], [None, ""], set()])
def test_f047_r12_sin_ids_no_consulta(siete, fabrica, ids) -> None:
    motivos, selects = _sentencias(fabrica, lambda: siete.motivos_espera(ids))
    assert motivos == {}
    assert selects == []


def test_f047_r12_usa_el_reloj_del_repositorio(siete, entorno) -> None:
    entorno.setattr(modulo_repo, "_ahora_utc",
                    lambda: AHORA + timedelta(seconds=1))
    # d-borde pasa de 600 s a 601 s: vencido.
    assert siete.motivos_espera(None) == {"d-nuevo": "nuevo",
                                          "d-recalc": "recalculo"}


def test_f047_r12_acepta_un_generador(siete) -> None:
    assert siete.motivos_espera(c[0] for c in CASOS_R12) == ESPERADO_R12


# ======================= R15-R17 · ediciones y aprobación ================ #

from urllib.parse import unquote_plus  # noqa: E402

from config.settings import Settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from application.services.reparto_aviso import (  # noqa: E402
    MOTIVO_APROBAR_CON_REPARTO,
    RepartoPendienteError,
)
from application.services.seguimiento_recalculo import (  # noqa: E402
    MOTIVO_RECALCULANDO,
    RecalculandoError,
)
from infrastructure.database.orm_models import (  # noqa: E402
    RepartoPendienteOrm,
)
from infrastructure.database.parte_repository import (  # noqa: E402
    EXCLUIDA_RECALCULANDO,
    MOTIVO_EXCLUIDA_RECALCULANDO,
)
from interface_adapters.web import app as app_mod  # noqa: E402
from interface_adapters.web.app import build_app  # noqa: E402
from tests.dobles import datos_registros  # noqa: E402
from tests.test_f022_aprobar_seleccion import (  # noqa: E402
    CalendarioFalso,
    PublisherFalso,
    Sv5Falso,
)
from tests.test_f004_endpoints_congelados import (  # noqa: E402
    SigridLookupClientFake,
)
from tests.test_f043_guarda_espera import JSON, LLAMADAS  # noqa: E402

DOC = "doc-f004"           # el `document_id` por defecto de `sembrar_parte`
OTRO = "doc-otro"
CUERPO_409 = {"ok": False, "congelado": True, "error": MOTIVO_RECALCULANDO}

#: Marcas que dejan el parte DOC en cada situación (reloj en AHORA).
NUEVO = dict(pedido=DOC, pedido_at=_hace(30))
RECALCULO = dict(pedido=PID2, pedido_at=_hace(30), terminado=PID)
NUEVO_TERMINADO = dict(pedido=DOC, pedido_at=_hace(30), terminado=DOC)
NUEVO_VENCIDO = dict(pedido=DOC, pedido_at=_hace(601))


def _cliente(fabrica, **extra) -> TestClient:
    return TestClient(build_app(Settings(_env_file=None),
                                repository=ParteReviewRepository(fabrica),
                                **extra))


@pytest.fixture
def nuevo_en_espera(entorno, fabrica):
    """DOC con dos líneas, recién guardado por sv3 y aún sin repartir.
    Sigrid de mentira, como en F-043: la ruta del código de hora lo pide."""
    for clave, valor in {"DEFAULT_REVIEWER": "ana",
                         "SIGRID_API_BASE_URL": "http://sigrid.interno",
                         "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
                         "SIGRID_API_DATABASE": "ruesma_rep"}.items():
        entorno.setenv(clave, valor)
    entorno.setattr(app_mod, "SigridLookupClient", SigridLookupClientFake)
    ids = sembrar_parte(fabrica, [{"horas": 10.0}, {"horas": 9.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    return ids


def _aprobado(fabrica, doc: str = DOC) -> bool:
    with fabrica.create_session() as s:
        return bool(s.get(ParteDocumentOrm, doc).approved)


# -------------------------------- R15 ---------------------------------- #

@pytest.mark.parametrize("nombre", sorted(JSON))
def test_f047_r15_editar_un_parte_nuevo_en_espera_da_el_409(
        nuevo_en_espera, fabrica, nombre) -> None:
    antes = datos_registros(fabrica, nuevo_en_espera)
    r = JSON[nombre](_cliente(fabrica), nuevo_en_espera)
    assert r.status_code == 409, r.text
    assert r.json() == CUERPO_409
    assert datos_registros(fabrica, nuevo_en_espera) == antes


@pytest.mark.parametrize("nombre", sorted(LLAMADAS))
def test_f047_r15_las_guardas_del_repositorio_con_un_parte_nuevo(
        nuevo_en_espera, fabrica, nombre) -> None:
    with pytest.raises(RecalculandoError) as exc:
        LLAMADAS[nombre](ParteReviewRepository(fabrica), nuevo_en_espera)
    assert exc.value.motivo == MOTIVO_RECALCULANDO


def test_f047_r15_la_fecha_y_deshacer_siguen_permitidos(
        nuevo_en_espera, fabrica) -> None:
    cliente = _cliente(fabrica)
    r = cliente.patch(f"/api/partes/{DOC}/fecha", json={"fecha": "2026-03-05"})
    assert r.status_code == 200, r.text
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, DOC).fecha == "2026-03-05"
    r = cliente.post("/api/undo")
    assert r.status_code == 200 and r.json()["ok"] is True
    with fabrica.create_session() as s:
        assert s.get(ParteDocumentOrm, DOC).fecha == "2026-03-02"


# -------------------------------- R16 ---------------------------------- #

def test_f047_r16_el_repositorio_no_aprueba_un_parte_nuevo_en_espera(
        entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    with pytest.raises(RecalculandoError) as exc:
        ParteReviewRepository(fabrica).approve_document(
            document_id=DOC, approved_by="ana")
    assert exc.value.motivo == MOTIVO_RECALCULANDO
    assert _aprobado(fabrica) is False


@pytest.mark.parametrize("marca", [NUEVO_TERMINADO, NUEVO_VENCIDO, None,
                                   RECALCULO],
                         ids=["terminado", "vencido", "sin_seguimiento",
                              "recalculo_en_espera"])
def test_f047_r16_fuera_de_espera_se_aprueba_como_siempre(
        entorno, fabrica, marca) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    if marca is not None:
        _poner_marca(fabrica, DOC, **marca)
    assert ParteReviewRepository(fabrica).approve_document(
        document_id=DOC, approved_by="ana") is True
    assert _aprobado(fabrica) is True


def test_f047_r16_el_reparto_pendiente_manda_sobre_la_espera(
        entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    _reparto(fabrica)
    with pytest.raises(RepartoPendienteError) as exc:
        ParteReviewRepository(fabrica).approve_document(
            document_id=DOC, approved_by="ana")
    assert exc.value.motivo == MOTIVO_APROBAR_CON_REPARTO


def test_f047_r16_la_ruta_redirige_con_el_motivo(entorno, fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    r = _cliente(fabrica).post(f"/documents/{DOC}/approve",
                               data={"back": f"/partes/{DOC}"},
                               follow_redirects=False)
    assert r.status_code == 303
    destino = unquote_plus(r.headers["location"])
    assert destino.startswith(f"/partes/{DOC}")
    assert MOTIVO_RECALCULANDO in destino
    assert _aprobado(fabrica) is False


def test_f047_r16_la_ruta_sigue_avisando_del_reparto(entorno,
                                                     fabrica) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    _reparto(fabrica)
    r = _cliente(fabrica).post(f"/documents/{DOC}/approve",
                               data={"back": "/partes"},
                               follow_redirects=False)
    assert r.status_code == 303
    assert MOTIVO_APROBAR_CON_REPARTO in unquote_plus(r.headers["location"])


@pytest.mark.parametrize("marca", [NUEVO_TERMINADO, RECALCULO],
                         ids=["terminado", "recalculo_en_espera"])
def test_f047_r16_la_ruta_aprueba_fuera_de_espera(entorno, fabrica,
                                                  marca) -> None:
    sembrar_parte(fabrica, [{"horas": 10.0}])
    _poner_marca(fabrica, DOC, **marca)
    r = _cliente(fabrica).post(f"/documents/{DOC}/approve",
                               data={"back": "/partes"},
                               follow_redirects=False)
    assert r.status_code == 303
    assert "Parte aprobado" in unquote_plus(r.headers["location"])
    assert _aprobado(fabrica) is True


# -------------------------------- R17 ---------------------------------- #

def _reparto(fabrica, fecha: int = 20260302) -> None:
    with fabrica.create_session() as s:
        s.add(RepartoPendienteOrm(recurso_ide=501, fecha_int=fecha,
                                  estado="pendiente", firma="f", cambios="{}",
                                  creado_at_utc="x", actualizado_at_utc="x"))
        s.commit()


def test_f047_r17_constantes() -> None:
    assert EXCLUIDA_RECALCULANDO == "recalculando"
    assert MOTIVO_EXCLUIDA_RECALCULANDO == (
        "parte en espera: se están repartiendo sus horas; pulsa Actualizar "
        "cuando termine")


def test_f047_r17_las_lineas_de_un_parte_nuevo_en_espera_no_viajan(
        entorno, fabrica) -> None:
    en_espera = sembrar_parte(fabrica, [{"horas": 10.0}, {"horas": 9.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    libres = sembrar_parte(fabrica, [{"horas": 8.0}], document_id=OTRO,
                           empleado_ide=78, recurso_ide=502)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(
        en_espera + libres)
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0,
                                  "recalculando": 2}
    assert [l["registro_id"] for l in datos["lineas"]] == libres
    detalle = {d["registro_id"]: d for d in datos["excluidas_detalle"]}
    assert set(detalle) == set(en_espera)
    for d in detalle.values():
        assert d["estado"] == "recalculando"
        assert d["motivo"] == MOTIVO_EXCLUIDA_RECALCULANDO


@pytest.mark.parametrize("marca", [NUEVO_TERMINADO, NUEVO_VENCIDO, None,
                                   RECALCULO],
                         ids=["terminado", "vencido", "sin_seguimiento",
                              "recalculo_en_espera"])
def test_f047_r17_sin_espera_las_claves_no_cambian(entorno, fabrica,
                                                   marca) -> None:
    ids = sembrar_parte(fabrica, [{"horas": 10.0}])
    if marca is not None:
        _poner_marca(fabrica, DOC, **marca)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(ids)
    assert datos["excluidas"] == {"registrado": 0, "borrado_sigrid": 0}
    assert [l["registro_id"] for l in datos["lineas"]] == ids


def test_f047_r17_va_detras_de_registrado_dedicacion_y_reparto(
        entorno, fabrica) -> None:
    ids = sembrar_parte(fabrica, [{"horas": 1.0, "estado": "registrado"},
                                  {"horas": 2.0, "estado": "dedicacion"},
                                  {"horas": 3.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    _reparto(fabrica)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(ids)
    assert datos["excluidas"] == {"registrado": 1, "borrado_sigrid": 0,
                                  "dedicacion": 1, "reparto_pendiente": 1}


def _n_selects(fabrica, ids) -> int:
    _datos, selects = _sentencias(
        fabrica, lambda: ParteReviewRepository(fabrica).lineas_para_registro(
            ids))
    return len(selects)


def test_f047_r17_sin_sentencias_nuevas(entorno, fabrica) -> None:
    """Desviacion aprobada el 2026-10-31: el estado se lee en el SELECT de
    lineas que ya existia (F-062 R5 fija sus sentencias)."""
    a = sembrar_parte(fabrica, [{"horas": 1.0}, {"horas": 2.0}])
    b = sembrar_parte(fabrica, [{"horas": 3.0}], document_id=OTRO,
                      empleado_ide=78, recurso_ide=502)
    sin_espera = _n_selects(fabrica, a + b)
    _poner_marca(fabrica, DOC, **NUEVO)
    assert _n_selects(fabrica, a + b) == sin_espera
    _datos, selects = _sentencias(
        fabrica, lambda: ParteReviewRepository(fabrica).lineas_para_registro(
            a + b))
    # El de las lineas trae su documento en la misma sentencia.
    assert "JOIN parte_documents" in selects[0]


def test_f047_r17_un_parte_en_papelera_no_cuenta_como_en_espera(
        entorno, fabrica) -> None:
    ids = sembrar_parte(fabrica, [{"horas": 3.0}], doc_en_papelera=True)
    _poner_marca(fabrica, DOC, **NUEVO)
    datos = ParteReviewRepository(fabrica).lineas_para_registro(ids)
    assert "recalculando" not in datos["excluidas"]


@pytest.fixture
def portal(entorno, fabrica):
    entorno.setenv("DEFAULT_REVIEWER", "ana")
    entorno.setenv("TRANSFER_BASE_URL", "http://sv5.interno")
    sv5, publisher = Sv5Falso(), PublisherFalso()
    cliente = _cliente(fabrica, transfer_client=sv5, publisher=publisher,
                       calendario_provider=CalendarioFalso())
    return cliente, sv5, publisher


@pytest.mark.parametrize("ruta", ["/api/aprobar/preflight",
                                  "/api/aprobar/ejecutar",
                                  "/api/aprobar/encolar"])
def test_f047_r17_si_solo_hay_lineas_en_espera_el_422_lo_dice(
        nuevo_en_espera, portal, ruta) -> None:
    cliente, sv5, publisher = portal
    r = cliente.post(ruta, json={"registro_ids": nuevo_en_espera})
    assert r.status_code == 422
    assert r.json()["error"] == (
        "no hay lineas que registrar: 2 en espera de reparto (pulsa "
        "Actualizar cuando termine)")
    assert r.json()["excluidas"]["recalculando"] == 2
    assert sv5.preflights == [] and sv5.ejecutadas == []
    assert publisher.publicadas == []


def test_f047_r17_el_motivo_se_suma_a_los_demas(entorno, fabrica,
                                                portal) -> None:
    ids = sembrar_parte(fabrica, [{"horas": 1.0, "estado": "registrado"},
                                  {"horas": 3.0}])
    _poner_marca(fabrica, DOC, **NUEVO)
    cliente, _sv5, _p = portal
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": ids})
    assert r.json()["error"] == (
        "no hay lineas que registrar: 1 ya registrada(s) en Sigrid (no se "
        "reenvian) y 1 en espera de reparto (pulsa Actualizar cuando "
        "termine)")
