# tests/test_f077_ingesta_hr.py
"""F-077 · R15: la ingesta de sv3 con Sesame HR cableado da lo de F-032.

`PersistPartePipeline` REAL con `RefrescoFestivos` REAL, el adaptador
`FestivosSesameHr` y el cliente `SesameHrClient` REALES sobre
`httpx.MockTransport` (solo GET) y la tabla `festivos_trabajador` REAL
(`SqlAlchemyFestivosRepository` sobre SQLite en memoria):

  - lista buena ⇒ upsert de la fila;
  - no encontrado (DNI fuera del indice) ⇒ ni fila ni revision;
  - fallo con fila previa ⇒ la fila se conserva y no hay revision;
  - fallo sin fila ⇒ el parte va a `review_required`;
  - la pasada `conciliar_todos` lee la tabla y no pide nada a Sesame.

Datos ficticios. (capa: integracion)
"""
from __future__ import annotations

import datetime as dt

from application.services.festivos_guardados import FilaFestivos
from application.services.recurso_conciliador import RecursoConciliador
from application.services.refresco_festivos import RefrescoFestivos
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)
from infrastructure.database.sqlalchemy_festivos_repository import (
    SqlAlchemyFestivosRepository,
)
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import SesameHrClient
from tests.dobles import (
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    recurso_persona,
    registro,
    reshor_par,
)
from tests.fixtures_sesame import (
    BASE_URL,
    DNI_A,
    DNI_AUSENTE,
    DNI_B,
    FESTIVOS_A_2026,
    ID_A,
    ID_B,
    TOKEN,
    Dormir,
    SesameHrFalso,
)
from tests.test_f032_ingesta import _parte, _pipeline
from tests.test_f047_parte_nuevo_sv3 import _request

AHORA = dt.datetime(2026, 11, 18, 9, 0, tzinfo=dt.timezone.utc)
PREVIA = FilaFestivos(dni_norm=DNI_B, ano=2026,
                      festivos={"2026-06-24": "San Juan"},
                      leido_en_utc="2026-11-01T08:00:00Z")


def _montar(sesame: SesameHrFalso, *, previas=()):
    fabrica = FabricaSesionSqlite()
    tabla = SqlAlchemyFestivosRepository(fabrica)
    for fila in previas:
        tabla.guardar(fila)
    cliente = SesameHrClient(base_url=BASE_URL, token=TOKEN,
                             transport=sesame.transport(), dormir=Dormir())
    refresco = RefrescoFestivos(
        cliente=FestivosSesameHr(cliente=cliente), repositorio=tabla,
        minimo=1, ahora_utc=lambda: AHORA)
    return tabla, refresco


def _ingerir(refresco, dnis):
    eventos: list = []
    pipeline, repo = _pipeline(eventos, _parte(dnis=dnis), refresco)
    pipeline.run(_request())
    return repo.guardados[0]


def test_f077_r15_lista_buena_upsert_sin_revision() -> None:
    sesame = SesameHrFalso(festivos={ID_A: FESTIVOS_A_2026})
    tabla, refresco = _montar(sesame)
    guardado = _ingerir(refresco, (DNI_A,))
    assert guardado["review_required"] is False
    assert tabla.leer_todas() == {(DNI_A, 2026): FilaFestivos(
        dni_norm=DNI_A, ano=2026,
        festivos={"2026-01-01": "Ano Nuevo",
                  "2026-05-15": "Fiesta local ficticia"},
        leido_en_utc="2026-11-18T09:00:00Z")}


def test_f077_r15_no_encontrado_sin_fila_ni_revision() -> None:
    sesame = SesameHrFalso()
    tabla, refresco = _montar(sesame)
    guardado = _ingerir(refresco, (DNI_AUSENTE,))
    assert guardado["review_required"] is False
    assert tabla.leer_todas() == {}
    assert "/schedule/v1/holidays" not in sesame.rutas()


def test_f077_r15_fallo_con_fila_la_conserva() -> None:
    sesame = SesameHrFalso(festivos={ID_B: 500})
    tabla, refresco = _montar(sesame, previas=[PREVIA])
    guardado = _ingerir(refresco, (DNI_B,))
    assert guardado["review_required"] is False
    assert tabla.leer_todas() == {(DNI_B, 2026): PREVIA}


def test_f077_r15_fallo_sin_fila_va_a_revision() -> None:
    sesame = SesameHrFalso(festivos={ID_A: 503})
    tabla, refresco = _montar(sesame)
    guardado = _ingerir(refresco, (DNI_A,))
    assert guardado["review_required"] is True
    assert tabla.leer_todas() == {}


def test_f077_r15_indice_caido_todo_el_parte_a_revision_sin_esperar() -> None:
    """El corte: el segundo DNI ya no toca la red (R14 dentro de R15)."""
    sesame = SesameHrFalso(empleados=[500])
    tabla, refresco = _montar(sesame)
    guardado = _ingerir(refresco, (DNI_A, DNI_B))
    assert guardado["review_required"] is True
    assert len(sesame.peticiones) == 3            # solo el primer listado


def test_f077_r15_la_pasada_no_pide_nada_a_sesame() -> None:
    sesame = SesameHrFalso(festivos={ID_A: FESTIVOS_A_2026})
    tabla, refresco = _montar(sesame)
    _ingerir(refresco, (DNI_A,))
    antes = len(sesame.peticiones)
    calendario = TablaCalendarioLaboral(
        repositorio=tabla,
        respaldo=JsonCalendarioLaboral(path="config/calendario_laboral.json"))
    partes = RepositorioFake([registro(1, fecha_int=20260515, horas=8.0,
                                       dni=DNI_A, document_id="doc-A")])
    RecursoConciliador(
        repository=partes,
        lookup=LookupFake(recursos=[recurso_persona(
            ide=501, conide=1, cif=DNI_A, restip_res="Oficial",
            horide_def=100)], reshor=reshor_par(501), hmo={}),
        calendario=calendario, jornada_ordinaria_horas=8.0,
        candef_minimo=2.0).conciliar_todos()
    assert len(sesame.peticiones) == antes
    # El viernes 15 es festivo en la fila de A: sus 8 h pasan a extra.
    assert [(s["horas_norm"], s["extra_horas"]) for s in partes.splits] == [
        (0.0, 8.0)]
