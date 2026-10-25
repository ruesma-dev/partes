# tests/test_f058_relectura_cabecera.py
"""F-058 · relectura de la cabecera con Gemini (sv2).

Si la lectura primaria trae trabajadores y su cabecera sale vacía (sin obra
ni fecha) o su obra no existe en Sigrid, sv2 relee el mismo documento una
vez con el proveedor de relectura y se queda con la cabecera releída si es
útil (``design.md`` §4).

Primera parte: las reglas puras de
``application/services/relectura_cabecera.py`` (R2–R5, R8). Segunda: el
pipeline con un cliente de IA doble por proveedor, el servicio, los prompts
y los esquemas reales y ``ComprobadorObra`` con un puerto doble y un reloj
falso (R1, R3, R4, R6–R9, R11–R20). Sin red ni IA: fixtures inventadas,
obra ``"9999"``.
"""
from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from application.pipelines.extract_parte_pipeline import (
    ExtractPartePipeline,
    ExtractParteRequest,
)
from application.services.obra_sigrid import ComprobadorObra
from application.services.parte_extraction_service import (
    ParteExtractionService,
    ProviderClientSpec,
)
from application.services.relectura_cabecera import (
    MOTIVO_CABECERA_VACIA,
    MOTIVO_OBRA_INEXISTENTE,
    RESULTADO_APLICADA,
    RESULTADO_NO_CASA,
    RESULTADO_VACIA,
    cabecera_vacia,
    clave_obra,
    con_trabajadores,
    es_vacio,
    motivo_relectura,
    resultado_relectura,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.conversion_adjunto import ResultadoConversion
from domain.models.llm_attachment import LlmAttachment
from domain.models.parte_models import ParteTrabajo
from domain.ports.conversor_pagina import ConversorPaginaImagen
from domain.ports.llm_client import LlmVisionClient
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

FILA ={"numero_linea": 1, "nombre": "Fulano de Tal", "dni": "12345678Z",
        "horas_ordinarias": 8.0}


def _data(obra=None, fecha=None, empleados=(FILA,), **cabecera) -> dict:
    return {
        "cabecera": {"obra_numero": obra, "fecha": fecha, **cabecera},
        "firma": {"firmado": True},
        "empleados": list(empleados),
    }


class ExisteDoble:
    """``ExisteObra`` que apunta cada código consultado y da una respuesta fija
    (o por código)."""

    def __init__(self, respuesta: bool | None = True,
                 por_codigo: dict[str, bool | None] | None = None) -> None:
        self.respuesta = respuesta
        self.por_codigo = por_codigo or {}
        self.llamadas: list[str] = []

    def __call__(self, codigo: str) -> bool | None:
        self.llamadas.append(codigo)
        return self.por_codigo.get(codigo, self.respuesta)


# ------------------------------ R5 · vacío -------------------------------- #

@pytest.mark.parametrize("valor", [None, "", " ", "\t \n"])
def test_f058_r5_none_y_solo_espacios_son_vacio(valor) -> None:
    assert es_vacio(valor) is True


@pytest.mark.parametrize("valor", ["9999", " 9 ", "0", 0, False, []])
def test_f058_r5_lo_demas_no_es_vacio(valor) -> None:
    assert es_vacio(valor) is False


# ------------------------------ clave de obra ----------------------------- #

@pytest.mark.parametrize(("codigo", "clave"), [
    ("0672", "672"),
    ("672", "672"),
    ("00672", "672"),
    ("000", "0"),
    ("0", "0"),
    (" a-12 ", "A12"),
    ("Obra Ñ-é", "OBRANE"),
    ("12 34", "1234"),
    ("0A1", "0A1"),          # no es solo de dígitos: los ceros se quedan
    (672, "672"),
    (None, ""),
    ("   ", ""),
    (" - ", ""),
])
def test_f058_r7_clave_de_obra(codigo, clave: str) -> None:
    assert clave_obra(codigo) == clave


# ---------------------------- cabecera vacía ------------------------------ #

def test_f058_r2_cabecera_vacia_sin_obra_ni_fecha() -> None:
    assert cabecera_vacia(_data(obra=None, fecha="  ")) is True


def test_f058_r2_cabecera_vacia_aunque_traiga_otros_campos() -> None:
    assert cabecera_vacia(_data(obra_nombre="Calle Falsa",
                                encargado_nombre="Mengano")) is True


@pytest.mark.parametrize("data", [
    {"firma": {}, "empleados": [FILA]},
    {"cabecera": None, "firma": {}, "empleados": [FILA]},
    {"cabecera": "texto", "firma": {}, "empleados": [FILA]},
])
def test_f058_r2_sin_cabecera_es_cabecera_vacia(data) -> None:
    assert cabecera_vacia(data) is True


@pytest.mark.parametrize(("obra", "fecha"), [
    ("9999", None), (None, "6/4/26"), ("9999", "6/4/26")])
def test_f058_r2_con_obra_o_fecha_no_es_vacia(obra, fecha) -> None:
    assert cabecera_vacia(_data(obra=obra, fecha=fecha)) is False


# --------------------------- con trabajadores ----------------------------- #

def test_f058_r4_con_trabajadores() -> None:
    assert con_trabajadores(_data()) is True
    assert con_trabajadores(_data(empleados=())) is False
    assert con_trabajadores({"cabecera": {}}) is False
    assert con_trabajadores({"empleados": None}) is False
    assert con_trabajadores({"empleados": "fila"}) is False


# --------------------------- R2–R4 · el motivo ---------------------------- #

def test_f058_r2_cabecera_vacia_sin_consultar_sigrid() -> None:
    existe = ExisteDoble()
    assert motivo_relectura(_data(), existe) == MOTIVO_CABECERA_VACIA
    assert existe.llamadas == []


def test_f058_r2_obra_inexistente() -> None:
    existe = ExisteDoble(False)
    data = _data(obra="9999", fecha="6/4/26")
    assert motivo_relectura(data, existe) == MOTIVO_OBRA_INEXISTENTE
    assert existe.llamadas == ["9999"]


def test_f058_r2_obra_inexistente_tambien_sin_fecha() -> None:
    assert motivo_relectura(_data(obra="9999"), ExisteDoble(False)) == (
        MOTIVO_OBRA_INEXISTENTE)


def test_f058_r3_obra_que_existe_no_relee() -> None:
    existe = ExisteDoble(True)
    assert motivo_relectura(_data(obra="9999", fecha="6/4/26"), existe) is None
    assert existe.llamadas == ["9999"]


def test_f058_r3_fecha_sin_obra_no_relee_ni_consulta() -> None:
    existe = ExisteDoble(False)
    assert motivo_relectura(_data(obra="  ", fecha="6/4/26"), existe) is None
    assert existe.llamadas == []


def test_f058_r9_no_se_sabe_no_es_inexistente() -> None:
    assert motivo_relectura(_data(obra="9999"), ExisteDoble(None)) is None


@pytest.mark.parametrize("obra", [None, "9999"])
def test_f058_r4_sin_trabajadores_ni_relee_ni_consulta(obra) -> None:
    existe = ExisteDoble(False)
    assert motivo_relectura(_data(obra=obra, empleados=()), existe) is None
    assert existe.llamadas == []


# ---------------------- R8, R12–R13 · el resultado ------------------------ #

def test_f058_r12_cabecera_vacia_releida_con_obra_es_aplicada() -> None:
    existe = ExisteDoble(False)
    rel = _data(obra="9999")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, existe, None) == (
        RESULTADO_APLICADA)
    assert existe.llamadas == []          # con cabecera_vacia no se consulta


def test_f058_r12_cabecera_vacia_releida_solo_con_fecha_es_aplicada() -> None:
    rel = _data(fecha="6/4/26")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, ExisteDoble(), None) == (
        RESULTADO_APLICADA)


def test_f058_r13_cabecera_vacia_releida_vacia_es_vacia() -> None:
    rel = _data(fecha=" ", obra_nombre="Calle Falsa")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, ExisteDoble(), None) == (
        RESULTADO_VACIA)


def test_f058_r12_obra_inexistente_releida_con_obra_que_existe() -> None:
    existe = ExisteDoble(por_codigo={"8888": True})
    rel = _data(obra="8888")
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, rel, existe, "9999") == RESULTADO_APLICADA
    assert existe.llamadas == ["8888"]


@pytest.mark.parametrize("respuesta", [False, None])
def test_f058_r8_obra_inexistente_releida_que_no_existe_o_no_se_sabe(
    respuesta,
) -> None:
    existe = ExisteDoble(respuesta)
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, _data(obra="8888"), existe, "9999") == (
        RESULTADO_NO_CASA)
    assert existe.llamadas == ["8888"]


@pytest.mark.parametrize("releida", ["9999", "09999", " 9999 ", "9-999"])
def test_f058_r8_misma_clave_que_la_primaria_no_casa_sin_consultar(
    releida: str,
) -> None:
    existe = ExisteDoble(True)
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, _data(obra=releida), existe, "9999") == (
        RESULTADO_NO_CASA)
    assert existe.llamadas == []


@pytest.mark.parametrize("obra", [None, "", "  "])
def test_f058_r16_obra_inexistente_releida_sin_obra_es_vacia(obra) -> None:
    existe = ExisteDoble(True)
    rel = _data(obra=obra, fecha="6/4/26")
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, rel, existe, "9999") == RESULTADO_VACIA
    assert existe.llamadas == []


# =========================================================================== #
#                      Pipeline (T8): R1, R3, R4, R6–R20                      #
# =========================================================================== #

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"
LOGGER_PIPELINE = "application.pipelines.extract_parte_pipeline"
PDF = b"%PDF-1.4 parte de prueba F-058"
FICHERO = "parte_escaneado.pdf"
DOC = "doc-f058"
MODELO_PRIMARIO = "modelo-primario"
MODELO_RELECTURA = "modelo-relectura"
CAMPOS_CABECERA = ("fecha", "obra_numero", "obra_nombre", "encargado_nombre",
                   "jefe_obra_nombre", "empresa_membrete")
CLAVES_META_RELECTURA = {"motivo", "provider", "model", "resultado",
                         "error_tipo", "consulta_obra_ms"}
#: Datos «personales» o de la cabecera que nunca deben salir en el log (R20).
SECRETOS_LOG = ("Fulano", "12345678Z", "9999", "8888", "6/4/26",
                "Calle Falsa", "Mengano", "detalle-secreto")


def _parte(obra=None, fecha=None, empleados=(FILA,), **cabecera) -> dict:
    """Un ``ParteTrabajo`` válido con la cabecera dada."""
    return {
        "cabecera": {"obra_numero": obra, "fecha": fecha, **cabecera},
        "firma": {"firmado": True, "firma_encargado": True},
        "empleados": [dict(e) for e in empleados],
    }


PRIMARIA_VACIA = _parte(obra_nombre="Calle Falsa")
RELEIDA = _parte(obra="8888", fecha="6/4/26", obra_nombre="Calle Falsa",
                 encargado_nombre="Mengano", empleados=(
                     {**FILA, "nombre": "Otro Nombre", "horas_ordinarias": 1.0},))


class ClienteIaDoble(LlmVisionClient):
    """Cliente de un proveedor: devuelve ``respuesta`` o lanza ``error``."""

    def __init__(self, respuesta: dict | None = None,
                 error: Exception | None = None) -> None:
        self.respuesta = respuesta
        self.error = error
        self.llamadas: list[dict] = []

    def extract_document(self, *, model, instructions, user_text, attachment,
                         response_model):
        self.llamadas.append({"model": model, "instructions": instructions,
                              "attachment": attachment})
        if self.error is not None:
            raise self.error
        return response_model.model_validate(self.respuesta)


class PuertoObra:
    """``ExistenciaObraPort`` con respuesta por clave (o error)."""

    def __init__(self, existentes=(), error: Exception | None = None,
                 errores_desde: int = 0) -> None:
        self.existentes = set(existentes)
        self.error = error
        self.errores_desde = errores_desde
        self.llamadas: list[str] = []

    def existe_obra(self, clave: str, *, timeout_s: float) -> bool:
        self.llamadas.append(clave)
        if self.error is not None and len(self.llamadas) > self.errores_desde:
            raise self.error
        return clave in self.existentes


class RelojPasos:
    """Reloj que avanza 10 ms en cada lectura: cada consulta dura 10 ms."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        self.t += 0.010
        return self.t


class ConversorDoble(ConversorPaginaImagen):
    def __init__(self) -> None:
        self.llamadas = 0

    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion:
        self.llamadas += 1
        imagen = LlmAttachment(kind="image", filename="p.jpg",
                               mime_type="image/jpeg", data=b"\xff\xd8 jpeg")
        return ResultadoConversion(adjunto=imagen, motivo="", giro_grados=90,
                                   ancho_px=10, alto_px=20)


def _montar(primaria: dict, *, releida: dict | None = None,
            error_relectura: Exception | None = None,
            puerto: PuertoObra | None = None, con_obras: bool = True,
            relectura: str | None = "gemini", catalogo: str | None = None,
            conversor: ConversorPaginaImagen | None = None,
            proveedores_imagen=frozenset({"openai"})):
    primario = ClienteIaDoble(primaria)
    secundario = ClienteIaDoble(releida if releida is not None else RELEIDA,
                                error_relectura)
    servicio = ParteExtractionService(
        providers=[
            ProviderClientSpec(provider="openai", model_name=MODELO_PRIMARIO,
                               client=primario),
            ProviderClientSpec(provider="gemini", model_name=MODELO_RELECTURA,
                               client=secundario),
        ],
        prompt_repo=YamlPromptRepository(str(RUTA_PROMPTS)),
        schema_registry=SchemaRegistry(),
    )
    puerto = puerto if puerto is not None else PuertoObra()
    obras = (ComprobadorObra(client=puerto, timeout_s=5.0, reloj=RelojPasos())
             if con_obras else None)
    catalogo_doble = (None if catalogo is None else SimpleNamespace(
        enabled=True, prompt_block=lambda: catalogo))
    pipeline = ExtractPartePipeline(
        extraction_service=servicio, max_file_mb=25, service_version="test",
        provider="openai", prompt_key="parte_trabajo_es",
        catalog_provider=catalogo_doble, conversor=conversor,
        proveedores_imagen=proveedores_imagen,
        relectura_provider=relectura, obras=obras,
    )
    return SimpleNamespace(pipeline=pipeline, primario=primario,
                           secundario=secundario, puerto=puerto)


def _correr(montaje, document_id: str | None = DOC) -> dict:
    return montaje.pipeline.run(ExtractParteRequest(
        filename=FICHERO, mime_type="application/pdf", file_bytes=PDF,
        document_id=document_id))


def _logs(caplog, nivel: int | None = None) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == LOGGER_PIPELINE
            and (nivel is None or r.levelno == nivel)
            and "[sv2][relectura]" in r.getMessage()]


def _primaria(data: dict) -> dict:
    return ParteTrabajo.model_validate(data).model_dump()


# ------------------------- R1, R12 · cabecera vacía ----------------------- #

def test_f058_r1_cabecera_vacia_relee_una_vez_con_el_mismo_prompt() -> None:
    m = _montar(PRIMARIA_VACIA, catalogo="CATALOGO AUXHOR DE PRUEBA")
    _correr(m)
    (primera,) = m.primario.llamadas
    (segunda,) = m.secundario.llamadas
    assert segunda["model"] == MODELO_RELECTURA
    assert segunda["instructions"] == primera["instructions"]
    assert "CATALOGO AUXHOR DE PRUEBA" in segunda["instructions"]
    assert segunda["attachment"].data == PDF
    assert segunda["attachment"].filename == FICHERO
    assert m.puerto.llamadas == []          # R8: con cabecera_vacia no consulta


def test_f058_r12_toma_la_cabecera_entera_y_firma_y_empleados_primarios() -> None:
    releida = _parte(obra="8888", fecha=None, obra_nombre="Calle Falsa")
    sobre = _correr(_montar(PRIMARIA_VACIA, releida=releida))
    primaria = _primaria(PRIMARIA_VACIA)
    assert sobre["data"]["cabecera"] == _primaria(releida)["cabecera"]
    assert set(sobre["data"]["cabecera"]) == set(CAMPOS_CABECERA)
    assert sobre["data"]["cabecera"]["fecha"] is None          # también nulos
    assert sobre["data"]["firma"] == primaria["firma"]
    assert sobre["data"]["empleados"] == primaria["empleados"]
    assert sobre["meta"]["relectura_cabecera"]["resultado"] == RESULTADO_APLICADA


def test_f058_r14_el_data_resultante_valida_contra_el_esquema() -> None:
    sobre = _correr(_montar(PRIMARIA_VACIA))
    ParteTrabajo.model_validate(sobre["data"])


def test_f058_r5_cabecera_con_solo_espacios_relee() -> None:
    m = _montar(_parte(obra="  ", fecha=" \t"))
    sobre = _correr(m)
    assert len(m.secundario.llamadas) == 1
    assert sobre["meta"]["relectura_cabecera"]["motivo"] == MOTIVO_CABECERA_VACIA


# ------------------------- R13 · releída no útil -------------------------- #

def test_f058_r13_releida_vacia_se_queda_la_primaria(caplog) -> None:
    m = _montar(PRIMARIA_VACIA, releida=_parte(fecha="  "))
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        sobre = _correr(m)
    assert sobre["data"] == _primaria(PRIMARIA_VACIA)
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel["resultado"] == RESULTADO_VACIA
    assert rel["error_tipo"] is None
    (aviso,) = _logs(caplog, logging.WARNING)
    assert "resultado=vacia" in aviso


# --------------------------- R14 · fallo de la relectura ------------------ #

def test_f058_r14_la_relectura_que_lanza_no_se_propaga(caplog) -> None:
    m = _montar(PRIMARIA_VACIA,
                error_relectura=RuntimeError("detalle-secreto 12345678Z"))
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        sobre = _correr(m)
    assert sobre["data"] == _primaria(PRIMARIA_VACIA)
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel == {"motivo": MOTIVO_CABECERA_VACIA, "provider": "gemini",
                   "model": MODELO_RELECTURA, "resultado": "error",
                   "error_tipo": "RuntimeError", "consulta_obra_ms": []}
    debug = sobre["debug"]["relectura_cabecera"]
    assert set(debug) == {"cabecera_primaria"}               # R18: no respondió
    (aviso,) = _logs(caplog, logging.WARNING)
    assert "resultado=error" in aviso and "error_tipo=RuntimeError" in aviso
    for texto in _logs(caplog):
        assert "detalle-secreto" not in texto


def test_f058_r14_proveedor_de_relectura_sin_instanciar_no_se_propaga() -> None:
    sobre = _correr(_montar(PRIMARIA_VACIA, relectura="claude"))
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel["resultado"] == "error"
    assert rel["error_tipo"] == "KeyError"
    assert rel["model"] is None
    assert rel["provider"] == "claude"


def test_f058_r14_un_fallo_de_la_primaria_sigue_propagandose() -> None:
    m = _montar(PRIMARIA_VACIA)
    m.primario.error = RuntimeError("primaria caida")
    with pytest.raises(RuntimeError, match="primaria caida"):
        _correr(m)
    assert m.secundario.llamadas == []


# ------------------------- R2, R7, R8 · obra inexistente ------------------ #

def test_f058_r7_obra_inexistente_relee_y_aplica_si_la_releida_existe() -> None:
    puerto = PuertoObra(existentes={"8888"})
    m = _montar(_parte(obra="09999", fecha="6/4/26"), puerto=puerto)
    sobre = _correr(m)
    assert puerto.llamadas == ["9999", "8888"]               # dos consultas
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel["motivo"] == MOTIVO_OBRA_INEXISTENTE
    assert rel["resultado"] == RESULTADO_APLICADA
    assert rel["consulta_obra_ms"] == [10, 10]
    assert sobre["data"]["cabecera"]["obra_numero"] == "8888"
    assert sobre["data"]["cabecera"]["encargado_nombre"] == "Mengano"
    assert sobre["data"]["empleados"] == _primaria(_parte())["empleados"]


def test_f058_r12_obra_inexistente_toma_la_cabecera_entera_aunque_pierda_fecha() -> None:
    """DA11 = A: la releída entera, también su fecha nula."""
    puerto = PuertoObra(existentes={"8888"})
    sobre = _correr(_montar(_parte(obra="9999", fecha="6/4/26"),
                            releida=_parte(obra="8888"), puerto=puerto))
    assert sobre["data"]["cabecera"]["obra_numero"] == "8888"
    assert sobre["data"]["cabecera"]["fecha"] is None


@pytest.mark.parametrize("releida", ["9999", "009999"])
def test_f058_r8_misma_clave_no_casa_con_una_sola_consulta(releida) -> None:
    puerto = PuertoObra()
    primaria = _parte(obra="9999", fecha="6/4/26")
    sobre = _correr(_montar(primaria, releida=_parte(obra=releida),
                            puerto=puerto))
    assert puerto.llamadas == ["9999"]
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel["resultado"] == RESULTADO_NO_CASA
    assert rel["consulta_obra_ms"] == [10]
    assert sobre["data"] == _primaria(primaria)


def test_f058_r8_releida_con_otra_obra_que_tampoco_existe_no_casa() -> None:
    puerto = PuertoObra()
    primaria = _parte(obra="9999", fecha="6/4/26")
    sobre = _correr(_montar(primaria, puerto=puerto))
    assert puerto.llamadas == ["9999", "8888"]
    assert sobre["meta"]["relectura_cabecera"]["resultado"] == RESULTADO_NO_CASA
    assert sobre["data"] == _primaria(primaria)


def test_f058_r16_pipeline_obra_inexistente_releida_sin_obra_es_vacia() -> None:
    puerto = PuertoObra()
    sobre = _correr(_montar(_parte(obra="9999"), releida=_parte(fecha="6/4/26"),
                            puerto=puerto))
    assert puerto.llamadas == ["9999"]
    assert sobre["meta"]["relectura_cabecera"]["resultado"] == RESULTADO_VACIA
    assert sobre["data"]["cabecera"]["obra_numero"] == "9999"


# ------------------------------ R3, R4 · no relee ------------------------- #

def test_f058_r3_obra_que_existe_una_sola_llamada_al_modelo() -> None:
    puerto = PuertoObra(existentes={"9999"})
    m = _montar(_parte(obra="9999", fecha="6/4/26"), puerto=puerto)
    sobre = _correr(m)
    assert len(m.primario.llamadas) == 1
    assert m.secundario.llamadas == []
    assert puerto.llamadas == ["9999"]
    assert "relectura_cabecera" not in sobre["meta"]
    assert "relectura_cabecera" not in sobre["debug"]


def test_f058_r3_pipeline_fecha_sin_obra_no_relee_ni_consulta() -> None:
    m = _montar(_parte(fecha="6/4/26"))
    _correr(m)
    assert m.secundario.llamadas == []
    assert m.puerto.llamadas == []


@pytest.mark.parametrize("obra", [None, "9999"])
def test_f058_r4_sin_trabajadores_no_relee_ni_consulta(obra) -> None:
    m = _montar(_parte(obra=obra, empleados=()))
    sobre = _correr(m)
    assert m.secundario.llamadas == []
    assert m.puerto.llamadas == []
    assert "relectura_cabecera" not in sobre["meta"]


# ------------------------------ R6 · inactiva ----------------------------- #

@pytest.mark.parametrize("primaria", [PRIMARIA_VACIA, _parte(obra="9999")])
def test_f058_r6_sin_relectura_activa_ni_relee_ni_consulta(primaria) -> None:
    m = _montar(primaria, relectura=None)
    sobre = _correr(m)
    assert m.secundario.llamadas == []
    assert m.puerto.llamadas == []
    assert "relectura_cabecera" not in sobre["meta"]


# ------------------------ R9 · la consulta no responde -------------------- #

def test_f058_r9_consulta_que_falla_no_relee_por_obra() -> None:
    puerto = PuertoObra(error=RuntimeError("sigrid-api respondio 500"))
    m = _montar(_parte(obra="9999", fecha="6/4/26"), puerto=puerto)
    sobre = _correr(m)
    assert puerto.llamadas == ["9999"]                        # sin reintento
    assert m.secundario.llamadas == []
    assert "relectura_cabecera" not in sobre["meta"]
    assert sobre["data"]["cabecera"]["obra_numero"] == "9999"


def test_f058_r9_consulta_que_falla_sigue_releyendo_por_cabecera_vacia() -> None:
    puerto = PuertoObra(error=RuntimeError("sigrid-api respondio 500"))
    m = _montar(PRIMARIA_VACIA, puerto=puerto)
    sobre = _correr(m)
    assert len(m.secundario.llamadas) == 1
    assert sobre["meta"]["relectura_cabecera"]["resultado"] == RESULTADO_APLICADA


def test_f058_r9_sin_sigrid_cableado_relee_solo_por_cabecera_vacia() -> None:
    con_obra = _montar(_parte(obra="9999"), con_obras=False)
    _correr(con_obra)
    assert con_obra.secundario.llamadas == []
    vacia = _montar(PRIMARIA_VACIA, con_obras=False)
    sobre = _correr(vacia)
    assert len(vacia.secundario.llamadas) == 1
    assert sobre["meta"]["relectura_cabecera"]["consulta_obra_ms"] == []


def test_f058_r9_la_segunda_consulta_que_falla_da_no_casa() -> None:
    puerto = PuertoObra(error=TimeoutError("lento"), errores_desde=1)
    sobre = _correr(_montar(_parte(obra="9999", fecha="6/4/26"), puerto=puerto))
    assert puerto.llamadas == ["9999", "8888"]
    rel = sobre["meta"]["relectura_cabecera"]
    assert rel["resultado"] == RESULTADO_NO_CASA
    assert rel["consulta_obra_ms"] == [10, 10]


def test_f058_r9_obra_con_clave_vacia_no_consulta_ni_relee() -> None:
    m = _montar(_parte(obra=" - ", fecha="6/4/26"))
    _correr(m)
    assert m.puerto.llamadas == []
    assert m.secundario.llamadas == []


# --------------------- R16–R19 · traza en meta y debug -------------------- #

def test_f058_r16_meta_relectura_con_sus_claves() -> None:
    sobre = _correr(_montar(PRIMARIA_VACIA))
    rel = sobre["meta"]["relectura_cabecera"]
    assert set(rel) == CLAVES_META_RELECTURA
    assert rel == {"motivo": MOTIVO_CABECERA_VACIA, "provider": "gemini",
                   "model": MODELO_RELECTURA, "resultado": RESULTADO_APLICADA,
                   "error_tipo": None, "consulta_obra_ms": []}


def test_f058_r17_provider_y_model_siguen_siendo_los_primarios() -> None:
    sobre = _correr(_montar(PRIMARIA_VACIA))
    assert sobre["meta"]["provider"] == "openai"
    assert sobre["meta"]["model"] == MODELO_PRIMARIO


def test_f058_r18_debug_guarda_la_cabecera_primaria_y_la_relectura() -> None:
    sobre = _correr(_montar(PRIMARIA_VACIA))
    debug = sobre["debug"]["relectura_cabecera"]
    assert debug["cabecera_primaria"] == _primaria(PRIMARIA_VACIA)["cabecera"]
    assert debug["gemini_request"]["model"] == MODELO_RELECTURA
    assert "gemini_response" in debug
    assert "openai_request" in sobre["debug"]                 # la primaria sigue


def test_f058_r19_sin_relectura_las_claves_de_hoy() -> None:
    hoy = _correr(_montar(_parte(obra="9999"), relectura=None))
    sin_releer = _correr(_montar(_parte(obra="9999"),
                                 puerto=PuertoObra(existentes={"9999"})))
    assert set(sin_releer["meta"]) == set(hoy["meta"])
    assert set(sin_releer["debug"]) == set(hoy["debug"])
    assert "relectura_cabecera" not in hoy["meta"]
    assert "relectura_cabecera" not in hoy["debug"]


# ----------------------------- R15, R20 · logs ---------------------------- #

def test_f058_r15_document_id_opcional_en_la_peticion() -> None:
    peticion = ExtractParteRequest(filename="a.pdf", mime_type="application/pdf",
                                   file_bytes=PDF)
    assert peticion.document_id is None


def test_f058_r20_info_al_disparar_y_al_aplicar(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        _correr(_montar(PRIMARIA_VACIA))
    disparo, final = _logs(caplog, logging.INFO)
    assert f"document_id={DOC}" in disparo
    assert "motivo=cabecera_vacia" in disparo
    assert "filas=1" in disparo
    assert FICHERO in disparo and f"gemini/{MODELO_RELECTURA}" in disparo
    for parte in (f"document_id={DOC}", FICHERO, "provider=gemini",
                  f"model={MODELO_RELECTURA}", "resultado=aplicada"):
        assert parte in final, (parte, final)
    assert _logs(caplog, logging.WARNING) == []


def test_f058_r20_warning_si_no_casa_y_sin_datos(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        _correr(_montar(_parte(obra="9999", fecha="6/4/26",
                               obra_nombre="Calle Falsa",
                               encargado_nombre="Mengano")))
    disparo, aviso = _logs(caplog)
    assert "motivo=obra_inexistente" in disparo
    assert "motivo=obra_inexistente" in aviso and "resultado=no_casa" in aviso
    assert _logs(caplog, logging.WARNING) == [aviso]
    for texto in _logs(caplog):
        for secreto in SECRETOS_LOG:
            assert secreto not in texto, (secreto, texto)


def test_f058_r20_sin_document_id_sale_guion(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        _correr(_montar(PRIMARIA_VACIA), document_id=None)
    textos = _logs(caplog)
    assert len(textos) == 2
    for texto in textos:
        assert "document_id=- " in texto


# ---------------- Encaje con F-059: cada proveedor, su adjunto ------------ #

def test_f058_f059_gemini_fuera_de_la_lista_relee_el_pdf_original() -> None:
    conversor = ConversorDoble()
    m = _montar(PRIMARIA_VACIA, conversor=conversor)
    sobre = _correr(m)
    assert m.primario.llamadas[0]["attachment"].kind == "image"
    assert m.secundario.llamadas[0]["attachment"].data == PDF
    assert conversor.llamadas == 1
    assert sobre["meta"]["adjunto_ia"]["conversion"] == "convertida"


def test_f058_f059_gemini_en_la_lista_relee_la_imagen() -> None:
    m = _montar(PRIMARIA_VACIA, conversor=ConversorDoble(),
                proveedores_imagen=frozenset({"openai", "gemini"}))
    sobre = _correr(m)
    assert m.secundario.llamadas[0]["attachment"].kind == "image"
    assert sobre["meta"]["adjunto_ia"]["conversion"] == "convertida"


# --------------------------- model_name del servicio ---------------------- #

def test_f058_r16_model_name_del_servicio() -> None:
    servicio = _montar(PRIMARIA_VACIA).pipeline._service
    assert servicio.model_name("gemini") == MODELO_RELECTURA
    with pytest.raises(KeyError):
        servicio.model_name("claude")
