# tests/test_f004_endpoints_congelados.py
"""F-004 · el SERVIDOR rechaza las ediciones sobre lo congelado (R3-R13).

La UI que deshabilita inputs es papel mojado: una peticion a pelo (curl,
una pestana vieja abierta, un doble clic con la pagina desactualizada)
llega igual. Aqui se comprueba el rechazo donde de verdad cuenta —el
endpoint— y, sobre todo, que la BBDD queda INTACTA: un 409 que ya haya
escrito no sirve de nada.

Sin red y sin PostgreSQL: SQLite en memoria con el ORM real y
`Settings(_env_file=None)`.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from infrastructure.sigrid.sigrid_lookup_client import TipoHoraOption
from interface_adapters.web import app as app_mod
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, datos_registros, sembrar_parte

LIBRE = {"estado": None, "horas": 8.0}
APROBADO_MOTIVO = "aprobado"


class SigridLookupClientFake:
    """Doble del cliente de sigrid-api: ni red ni claves.

    Se inyecta por monkeypatch del simbolo importado en `app.py`, igual
    que los dobles de Storage: asi el catalogo de tipos de hora queda
    ENCENDIDO (si no, `/api/registros/{id}/hora` responde 503 y nunca
    llegariamos a la guarda que queremos probar).
    """

    def __init__(self, **_kw) -> None:
        pass

    def fetch_tipos_hora(self) -> list[TipoHoraOption]:
        return [
            TipoHoraOption(ide=1, codigo="HL01", descripcion="Ordinaria",
                           ext=0, pre=None, prenom=None),
            TipoHoraOption(ide=2, codigo="HE01", descripcion="Extra",
                           ext=1, pre=None, prenom=None),
        ]

    def fetch_obras(self) -> list:
        return []

    def fetch_empleados(self) -> list:
        return []

    def fetch_partidas_obra(self, _obra_ide: int) -> list:
        return []

    def fetch_hora_extra_recurso(self, _recurso_ide: int):
        return None

    def fetch_dnis_sin_extra(self, _dnis) -> set:
        return set()


def _settings() -> Settings:
    """Sin leer el `.env` del desarrollador (patron de F-002/F-003)."""
    return Settings(_env_file=None)


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
        "DEFAULT_REVIEWER": "ana",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


@pytest.fixture
def montaje(entorno):
    """Devuelve `_montar(lineas, ...) -> (cliente, repo, fabrica, ids)`."""
    def _montar(lineas, *, aprobado: bool = False, con_sigrid: bool = True,
                **kw):
        if con_sigrid:
            for clave, valor in {
                "SIGRID_API_BASE_URL": "http://sigrid.interno",
                "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
                "SIGRID_API_DATABASE": "ruesma_rep",
            }.items():
                entorno.setenv(clave, valor)
            entorno.setattr(app_mod, "SigridLookupClient",
                            SigridLookupClientFake)
        fabrica = FabricaSesionSqlite()
        ids = sembrar_parte(fabrica, lineas, aprobado=aprobado, **kw)
        repositorio = ParteReviewRepository(fabrica)
        app = build_app(_settings(), repository=repositorio)
        return TestClient(app), repositorio, fabrica, ids
    return _montar


def _congelado(respuesta) -> str:
    """Comprueba la forma del 409 y devuelve el motivo."""
    assert respuesta.status_code == 409, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo.get("ok") is False
    assert cuerpo.get("congelado") is True
    motivo = cuerpo.get("error") or ""
    assert motivo.strip(), "el 409 tiene que explicar POR QUE"
    return motivo


def _num_lineas(fabrica, document_id: str = "doc-f004") -> int:
    with fabrica.create_session() as s:
        from sqlalchemy import select
        return len(list(s.execute(
            select(ParteRegistroOrm).where(
                ParteRegistroOrm.document_id == document_id)
        ).scalars().all()))


def _doc(fabrica, document_id: str = "doc-f004") -> ParteDocumentOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, document_id)


#: Las tres condiciones que congelan una linea (R1), para recorrer cada
#: endpoint con todas ellas: si la guarda mirase solo `approved`, la
#: linea encolada o registrada de un parte nunca aprobado (el flujo por
#: obra x mes registra sin aprobar el documento) se colaria.
CONGELANTES = [
    pytest.param({"estado": None}, True, id="doc-aprobado"),
    pytest.param({"estado": "encolado"}, False, id="linea-encolada"),
    pytest.param({"estado": "registrado"}, False, id="linea-registrada"),
]


# ------------------------------- R3 ------------------------------------ #

@pytest.mark.parametrize("linea,aprobado", CONGELANTES)
def test_f004_r3_patch_horas_de_linea_congelada_responde_409(
        montaje, linea, aprobado) -> None:
    cliente, _repo, fabrica, ids = montaje([linea], aprobado=aprobado)
    antes = datos_registros(fabrica, ids)
    _congelado(cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 3.0}))
    assert datos_registros(fabrica, ids) == antes


@pytest.mark.parametrize("linea,aprobado", CONGELANTES)
def test_f004_r3_patch_codigo_de_hora_de_linea_congelada_responde_409(
        montaje, linea, aprobado) -> None:
    cliente, _repo, fabrica, ids = montaje([linea], aprobado=aprobado)
    antes = datos_registros(fabrica, ids)
    _congelado(cliente.patch(f"/api/registros/{ids[0]}/hora",
                             json={"hora_ide": 2}))
    assert datos_registros(fabrica, ids) == antes


@pytest.mark.parametrize("linea,aprobado", CONGELANTES)
def test_f004_r3_patch_partida_de_linea_congelada_responde_409(
        montaje, linea, aprobado) -> None:
    cliente, _repo, fabrica, ids = montaje([linea], aprobado=aprobado)
    antes = datos_registros(fabrica, ids)
    _congelado(cliente.patch(
        f"/api/registros/{ids[0]}/partida",
        json={"partida_ide": 5, "partida_cod": "3.1", "partida_res": "Ppp",
              "partida_capitulo": "CD"}))
    assert datos_registros(fabrica, ids) == antes


def test_f004_r3_el_motivo_del_409_distingue_el_caso(montaje) -> None:
    """Un «✗ Error» generico no le dice a nadie que hacer; el motivo si."""
    cliente, _repo, _f, ids = montaje(
        [{"estado": "registrado"}, {"estado": "encolado"}, {"estado": None}],
        aprobado=True)
    registrada = _congelado(
        cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 1.0}))
    encolada = _congelado(
        cliente.patch(f"/api/registros/{ids[1]}", json={"horas": 1.0}))
    aprobada = _congelado(
        cliente.patch(f"/api/registros/{ids[2]}", json={"horas": 1.0}))
    assert "sigrid" in registrada.lower()
    assert "encolada" in encolada.lower()
    assert APROBADO_MOTIVO in aprobada.lower()
    assert len({registrada, encolada, aprobada}) == 3


@pytest.mark.parametrize("estado", [None, "", "omitido", "error",
                                    "conflicto"])
def test_f004_r3_la_linea_editable_sigue_editandose(montaje, estado) -> None:
    """`omitido`/`error`/`conflicto` son justo las que hay que poder
    arreglar: si la congelacion las tocase, no habria salida."""
    cliente, _repo, fabrica, ids = montaje([{"estado": estado, "horas": 8.0}])
    assert cliente.patch(f"/api/registros/{ids[0]}",
                         json={"horas": 5.0}).status_code == 200
    assert cliente.patch(f"/api/registros/{ids[0]}/hora",
                         json={"hora_ide": 2}).status_code == 200
    assert cliente.patch(
        f"/api/registros/{ids[0]}/partida",
        json={"partida_ide": 5, "partida_cod": "3.1", "partida_res": "P",
              "partida_capitulo": "CD"}).status_code == 200
    datos = datos_registros(fabrica, ids)[ids[0]]
    assert datos["horas"] == 5.0
    assert datos["hora_codigo"] == "HE01"
    assert datos["partida_cod"] == "3.1"


def test_f004_r3_solo_se_congela_la_linea_congelada(montaje) -> None:
    """Un parte sin aprobar con una linea registrada y otra omitida: la
    omitida se edita. La congelacion es POR LINEA, no por parte."""
    cliente, _repo, fabrica, ids = montaje(
        [{"estado": "registrado"}, {"estado": "omitido"}])
    _congelado(cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 1.0}))
    assert cliente.patch(f"/api/registros/{ids[1]}",
                         json={"horas": 6.0}).status_code == 200
    assert datos_registros(fabrica, ids)[ids[1]]["horas"] == 6.0


# ------------------------------- R4 ------------------------------------ #

@pytest.mark.parametrize("linea,aprobado", CONGELANTES)
def test_f004_r4_papelera_de_linea_congelada_responde_409(
        montaje, linea, aprobado) -> None:
    """Una linea registrada que desaparece del portal pero sigue viva en
    Sigrid es la desincronizacion SILENCIOSA que esto viene a impedir."""
    cliente, _repo, fabrica, ids = montaje([linea], aprobado=aprobado)
    _congelado(cliente.post(f"/api/registro/{ids[0]}/delete"))
    assert datos_registros(fabrica, ids)[ids[0]]["deleted_at_utc"] is None


def test_f004_r4_la_linea_libre_se_sigue_pudiendo_borrar(montaje) -> None:
    cliente, _repo, fabrica, ids = montaje([{"estado": "omitido"}])
    assert cliente.post(f"/api/registro/{ids[0]}/delete").json()["ok"] is True
    assert datos_registros(fabrica, ids)[ids[0]]["deleted_at_utc"] is not None


# ------------------------------- R5 ------------------------------------ #

@pytest.mark.parametrize("linea,aprobado", CONGELANTES)
def test_f004_r5_crear_extra_desde_linea_congelada_responde_409(
        montaje, linea, aprobado) -> None:
    """Un parte aprobado no cambia de contenido, tampoco por adicion."""
    cliente, _repo, fabrica, ids = montaje([linea], aprobado=aprobado)
    _congelado(cliente.post(f"/api/registros/{ids[0]}/extra",
                            json={"horas": 2.0}))
    assert _num_lineas(fabrica) == 1


def test_f004_r5_la_extra_se_crea_desde_una_linea_libre(montaje) -> None:
    cliente, _repo, fabrica, ids = montaje([{"estado": None, "horas": 8.0}])
    respuesta = cliente.post(f"/api/registros/{ids[0]}/extra",
                             json={"horas": 2.0})
    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is True
    assert _num_lineas(fabrica) == 2


def test_f004_r5_el_repositorio_tambien_se_niega(montaje) -> None:
    """La guarda vive en el REPOSITORIO, dentro de la misma sesion que la
    mutacion: no hay ventana entre comprobar y escribir, y cualquier
    llamador futuro la hereda sin tener que acordarse."""
    from application.services.congelacion import CongeladoError

    _cliente, repositorio, _f, ids = montaje([{"estado": "registrado"}])
    with pytest.raises(CongeladoError):
        repositorio.update_registro(registro_id=ids[0], horas=1.0)
    with pytest.raises(CongeladoError):
        repositorio.soft_delete_registro(registro_id=ids[0], by="ana")
    with pytest.raises(CongeladoError):
        repositorio.crear_extra_desde(registro_id=ids[0], horas=2.0)


def test_f004_r3_el_registro_inexistente_sigue_dando_404(montaje) -> None:
    """La congelacion no puede tapar el 404: son errores distintos."""
    cliente, _repo, _f, _ids = montaje([LIBRE])
    assert cliente.patch("/api/registros/9999",
                         json={"horas": 1.0}).status_code == 404


def test_f004_r18_marcar_encolado_y_registrado_no_se_congelan(
        montaje) -> None:
    """R18: las escrituras del SISTEMA (la traza del registro) NO son
    ediciones de usuario. Si la guarda las alcanzara, ninguna linea
    podria pasar de `encolado` a `registrado` y el pipeline se romperia
    entero."""
    _cliente, repositorio, fabrica, ids = montaje([{"estado": None}])
    assert repositorio.marcar_registros_encolado(ids, "ana") == 1
    assert repositorio.marcar_registros_sigrid(
        escritas=[{"registro_id": ids[0], "hmoide": 1, "hmores_ide": 2,
                   "parte_cod": "PT26/00007"}],
        omitidas=[], ya_registradas=[], usuario="ana") == 1
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]).sigrid_estado == "registrado"
    assert repo_mod.ESTADO_ENCOLADO == "encolado"
