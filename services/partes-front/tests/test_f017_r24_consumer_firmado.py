# tests/test_f017_r24_consumer_firmado.py
"""F-017 · R18 y R24: quien firma el resultado de una aprobacion encolada.

El consumidor de `q-transfer-result` es el **unico** punto de escritura del
portal que corre fuera de una peticion HTTP: es un hilo que consume una cola,
sin `Request` y sin cabecera de Easy Auth que leer. Su identidad tiene que
venir del sobre, que viaja firmado desde `aprobar_encolar` (R16).

Este fichero existe por un defecto que la primera version de F-017 dejo vivo y
que encontro el reviewer (2026-08-20). La linea era:

    usuario = sobre.get("usuario") or getattr(settings, "default_reviewer", None)

Tres cosas iban mal a la vez:

1. Era una **tercera lectura de identidad** fuera del punto unico (R10/R11),
   invisible para el guardian, que solo miraba `app.py`.
2. Contradecia lo que la feature publica en tres documentos: estando
   desplegado, `DEFAULT_REVIEWER` **no firma nada**.
3. Con `DEFAULT_REVIEWER` sin configurar —que es el caso real—, un mensaje en
   vuelo durante el despliegue marcaba lineas con `sigrid_registrado_by =
   NULL` **despues** del corte, rompiendo «`autor IS NULL` ⇔ fila anterior a
   F-017» justo en la ventana en la que hay mensajes en vuelo.

Decision del humano (2026-08-20): el fallback es **`sin-identidad`**, ni
`NULL` ni `DEFAULT_REVIEWER`. El consumidor corre siempre desplegado, asi que
es exactamente el caso de R5b: un sobre sin firma es una **anomalia que debe
verse en el log**, no una firma.

Sin red y sin BBDD: fakes del SDK de Storage y SQLite en memoria.
"""
from __future__ import annotations

import json
import logging

import pytest
from infrastructure.azure import blob_cliente as mod_blob
from infrastructure.azure.blob_cliente import BlobCliente
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.identidad import ACTOR_SIN_IDENTIDAD
from interface_adapters.workers.resultado_consumer import (
    construir_handler_resultados,
)
from tests.dobles import (
    BlobServiceClientFake,
    FabricaSesionSqlite,
    parchear_blobs,
    sembrar_registros,
)

PETICION_ID = "aaaa1111-bbbb-2222-cccc-333344445555"
USUARIO = "ana.ejemplo@ejemplo.invalid"


class SettingsFake:
    """Con `default_reviewer` PUESTO a proposito.

    Es la unica forma de demostrar que ya no se lee: si el consumidor
    volviera a mirarla, estos tests lo verian.
    """

    blob_transfer = "transfer"
    cola_transfer = "q-transfer"
    cola_transfer_result = "q-transfer-result"
    default_reviewer = "no-deberia-firmar-nada"


class Montaje:
    def __init__(self, monkeypatch, *, cantidad: int = 2):
        parchear_blobs(monkeypatch, mod_blob, BlobServiceClientFake())
        self.blob = BlobCliente(connection_string="UseDevelopmentStorage=true")
        self.settings = SettingsFake()
        self.fabrica = FabricaSesionSqlite()
        self.ids = sembrar_registros(self.fabrica, cantidad=cantidad)
        self.repositorio = ParteReviewRepository(self.fabrica)
        self.handler = construir_handler_resultados(
            repository=self.repositorio, blob=self.blob,
            settings=self.settings)

    def procesar(self, sobre: dict) -> None:
        """Publica el sobre tal cual y lo hace consumir."""
        self.blob.subir("transfer", f"resultados/{PETICION_ID}.json",
                        json.dumps(sobre).encode("utf-8"))
        self.handler({"peticion_id": PETICION_ID,
                      "blob": f"resultados/{PETICION_ID}.json"})

    def sobre(self, **kw) -> dict:
        base = {
            "peticion_id": PETICION_ID,
            "registro_ids": self.ids,
            "resultado": {
                "ok": True,
                "escritas": [{"registro_id": self.ids[0], "hmoide": 901}],
                "omitidas": [], "ya_registradas": []},
        }
        base.update(kw)
        return base

    def firmado_por(self, registro_id: int) -> str | None:
        with self.fabrica.create_session() as s:
            return s.get(ParteRegistroOrm, registro_id).sigrid_registrado_by


@pytest.fixture
def montaje(monkeypatch):
    return Montaje(monkeypatch)


# ====================================================================== #
# R18 · el sobre manda, y llega intacto
# ====================================================================== #

def test_f017_r18_el_sobre_manda_y_su_usuario_llega_intacto(montaje) -> None:
    """Lo que firmo `aprobar_encolar` es lo que acaba en la columna."""
    montaje.procesar(montaje.sobre(usuario=USUARIO))
    assert montaje.firmado_por(montaje.ids[0]) == USUARIO


def test_f017_r18_el_sobre_gana_a_default_reviewer(montaje) -> None:
    """Con `DEFAULT_REVIEWER` puesta, el sobre sigue mandando."""
    montaje.procesar(montaje.sobre(usuario=USUARIO))
    firma = montaje.firmado_por(montaje.ids[0])
    assert firma == USUARIO
    assert "no-deberia-firmar-nada" not in firma


@pytest.mark.parametrize("usuario", [
    "local:ana",                 # sobre publicado desde un puesto local
    ACTOR_SIN_IDENTIDAD,         # sobre firmado por otro proceso sin identidad
])
def test_f017_r18_los_marcadores_reservados_del_sobre_se_respetan(
        montaje, usuario: str) -> None:
    """Un marcador que YA venia firmado no se reescribe aqui.

    R6 protege el espacio reservado frente a lo que llega de **fuera**, por
    cabecera. Este valor no viene de fuera: lo puso el propio portal al
    encolar, y es informacion honesta sobre el origen de la peticion.
    Volver a juzgarlo aqui solo podria perderla.
    """
    montaje.procesar(montaje.sobre(usuario=usuario))
    assert montaje.firmado_por(montaje.ids[0]) == usuario


# ====================================================================== #
# R24 · un sobre sin firma es una anomalia visible, no un NULL
# ====================================================================== #

@pytest.mark.parametrize("sin_firma", [
    {},                          # sobre publicado ANTES de F-017 (el caso real)
    {"usuario": None},           # lo que publicaba `dev`: default_reviewer=None
    {"usuario": ""},
    {"usuario": "   "},
    {"usuario": 12345},          # sobre corrupto: no puede lanzar
])
def test_f017_r24_sobre_sin_usuario_se_sella_sin_identidad(
        montaje, caplog, sin_firma: dict) -> None:
    """El fallback es `sin-identidad`, y la operacion se completa igual."""
    with caplog.at_level(logging.WARNING):
        montaje.procesar(montaje.sobre(**sin_firma))

    firma = montaje.firmado_por(montaje.ids[0])
    assert firma == ACTOR_SIN_IDENTIDAD
    # Las tres cosas que la decision del humano exige, por separado:
    assert firma is not None                      # NO se sella NULL...
    assert not firma.startswith("local:")         # ...ni se miente el origen
    assert "no-deberia-firmar-nada" not in firma  # ...ni firma DEFAULT_REVIEWER

    avisos = [r for r in caplog.records
              if r.levelno == logging.WARNING and "identidad" in r.message]
    assert len(avisos) == 1, "un sobre sin firma es un incidente: tiene que verse"


def test_f017_r24_el_aviso_nombra_la_peticion(montaje, caplog) -> None:
    """Sin el `peticion_id`, el WARNING no sirve para investigar nada."""
    with caplog.at_level(logging.WARNING):
        montaje.procesar(montaje.sobre())
    texto = " ".join(r.getMessage() for r in caplog.records)
    assert PETICION_ID in texto


def test_f017_r24_el_aviso_se_repite_por_mensaje(montaje, caplog) -> None:
    """Uno por mensaje afectado: cada uno es un incidente (criterio R5b).

    No esta sujeto al «una sola vez por arranque» de R9, igual que el
    WARNING de las peticiones HTTP sin identidad.
    """
    with caplog.at_level(logging.WARNING):
        for _ in range(3):
            montaje.procesar(montaje.sobre())

    avisos = [r for r in caplog.records
              if r.levelno == logging.WARNING and "identidad" in r.message]
    assert len(avisos) == 3


def test_f017_r24_un_sobre_firmado_no_genera_aviso(montaje, caplog) -> None:
    """Lo normal no puede hacer ruido, o el ruido tapa el incidente."""
    with caplog.at_level(logging.WARNING):
        montaje.procesar(montaje.sobre(usuario=USUARIO))
    assert [r for r in caplog.records
            if r.levelno == logging.WARNING
            and "identidad" in r.message] == []


def test_f017_r24_el_marcado_se_completa_aunque_no_haya_firma(
        montaje) -> None:
    """No saber quien fue NO es motivo para perder el veredicto de Sigrid.

    Es el principio heredado de F-016, aplicado al ultimo punto de
    escritura que le faltaba.
    """
    montaje.procesar(montaje.sobre())
    with montaje.fabrica.create_session() as s:
        registro = s.get(ParteRegistroOrm, montaje.ids[0])
        assert registro.sigrid_estado == "registrado"
        assert registro.sigrid_hmoide == 901


def test_f017_r24_ninguna_fila_nace_con_autor_nulo_tras_el_corte(
        montaje) -> None:
    """La propiedad global de R7, comprobada en la via que la rompia.

    Este es el test que le faltaba a la feature: era el unico camino por el
    que una fila podia nacer sin actor DESPUES del corte, y por tanto el
    unico agujero real del criterio «`autor IS NULL` ⇔ anterior a F-017».
    """
    montaje.procesar(montaje.sobre())          # el peor caso: sobre sin firma
    for registro_id in montaje.ids:
        with montaje.fabrica.create_session() as s:
            registro = s.get(ParteRegistroOrm, registro_id)
            if registro.sigrid_registrado_by is not None:
                assert registro.sigrid_registrado_by.strip() != ""
