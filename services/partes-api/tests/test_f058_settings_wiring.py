# tests/test_f058_settings_wiring.py
"""F-058 · R15, R24–R26: configuración, cableado, ``/health`` y worker.

- ``Settings`` lee ``RELECTURA_CABECERA`` (encendida), ``RELECTURA_CABECERA_
  PROVIDER`` (``gemini``) y ``OBRA_EXISTE_TIMEOUT_S`` (5 s, > 0) y expone el
  proveedor de relectura activo o, si está encendida pero no puede, el motivo
  (``mismo_proveedor``, ``no_habilitado``, ``sin_clave``). La relectura no
  impide arrancar (R24).
- ``build_app`` pasa al pipeline el proveedor activo y, con sigrid-api
  cableado, la consulta de obra con el mismo cliente que el catálogo auxhor,
  y lo dice en el log sin secretos (R25); ``/health`` lo enseña (R26).
- ``main_worker`` pasa al pipeline el ``document_id`` del mensaje (R15).

Sin red: los clientes se construyen con claves falsas y no se llaman; los
SDK de IA, si faltan, son dobles (``f059_sdk_falsos``).
"""
from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.f059_sdk_falsos import instalar_si_faltan

# Los SDK de IA no están en el .venv de la raíz: dobles solo si faltan.
instalar_si_faltan()

import main_worker
from application.services.obra_sigrid import ComprobadorObra
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient
from interface_adapters.api.app import build_app
from pydantic import ValidationError

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
CLAVE_FALSA = "clave-falsa-de-test-f058"
CLAVE_SIGRID = "clave-sigrid-falsa-f058"
LOGGER_APP = "interface_adapters.api.app"
VARIABLES = (
    "ENABLE_GEMINI", "ENABLE_CLAUDE", "ENABLE_OPENAI", "IA_PROVIDER",
    "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_MODEL",
    "OPENAI_MODEL", "PAGINA_COMO_IMAGEN", "PAGINA_COMO_IMAGEN_PROVEEDORES",
    "OPENAI_IMAGE_DETAIL", "PROMPTS_YAML_PATH", "SIGRID_API_BASE_URL",
    "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE", "IA_LOGGING_ENABLED",
    "RELECTURA_CABECERA", "RELECTURA_CABECERA_PROVIDER",
    "OBRA_EXISTE_TIMEOUT_S",
)
SIGRID = {"SIGRID_API_BASE_URL": "https://sigrid.invalid",
          "SIGRID_API_FUNCTION_KEY": CLAVE_SIGRID,
          "SIGRID_API_DATABASE": "ruesma"}


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch) -> None:
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def _settings(**entorno) -> Settings:
    """Como en Azure: OpenAI primario y Gemini habilitado con clave."""
    base = {"ENABLE_GEMINI": True, "GEMINI_API_KEY": CLAVE_FALSA,
            "GEMINI_MODEL": "gemini-falso", "ENABLE_OPENAI": True,
            "IA_PROVIDER": "openai", "OPENAI_API_KEY": CLAVE_FALSA,
            "OPENAI_MODEL": "openai-falso",
            "PROMPTS_YAML_PATH": str(RAIZ_SERVICIO / "config" / "prompts.yaml")}
    base.update(entorno)
    return Settings(_env_file=None, **base)


# ------------------------------ R24 · Settings ---------------------------- #

def test_f058_r24_por_defecto_encendida_con_gemini_y_5_s() -> None:
    s = _settings()
    assert s.relectura_cabecera_enabled is True
    assert s.relectura_cabecera_provider == "gemini"
    assert s.obra_existe_timeout_s == 5.0
    assert s.relectura_cabecera_activa == "gemini"
    assert s.relectura_cabecera_motivo_inactiva is None


def test_f058_r24_se_leen_del_entorno(monkeypatch) -> None:
    monkeypatch.setenv("RELECTURA_CABECERA", "false")
    monkeypatch.setenv("RELECTURA_CABECERA_PROVIDER", "claude")
    monkeypatch.setenv("OBRA_EXISTE_TIMEOUT_S", "2.5")
    s = _settings()
    assert s.relectura_cabecera_enabled is False
    assert s.relectura_cabecera_provider == "claude"
    assert s.obra_existe_timeout_s == 2.5


def test_f058_r24_apagada_no_hay_activa_ni_motivo() -> None:
    s = _settings(RELECTURA_CABECERA=False)
    assert s.relectura_cabecera_activa is None
    assert s.relectura_cabecera_motivo_inactiva is None


@pytest.mark.parametrize("tope", ["0", "-1", "-0.5"])
def test_f058_r24_tope_de_la_consulta_no_positivo_no_arranca(
    monkeypatch, tope: str,
) -> None:
    monkeypatch.setenv("OBRA_EXISTE_TIMEOUT_S", tope)
    with pytest.raises(ValidationError, match="OBRA_EXISTE_TIMEOUT_S"):
        _settings()


@pytest.mark.parametrize("tope", ["0.5", "1"])
def test_f058_r24_tope_de_la_consulta_positivo_menor_o_igual_a_1_se_acepta(
    monkeypatch, tope: str,
) -> None:
    """La frontera es «> 0», no «> 1»: medio segundo y un segundo valen.

    Mata el superviviente de T16 (``gt=0`` → ``gt=1``), el mismo hueco que
    tuvo F-038: ningún test probaba un tope válido entre 0 y 1.
    """
    monkeypatch.setenv("OBRA_EXISTE_TIMEOUT_S", tope)
    assert _settings().obra_existe_timeout_s == float(tope)


def test_f058_r24_proveedor_de_relectura_desconocido_no_arranca(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RELECTURA_CABECERA_PROVIDER", "mistral")
    with pytest.raises(ValidationError, match="RELECTURA_CABECERA_PROVIDER"):
        _settings()


def test_f058_r24_mismo_proveedor() -> None:
    s = _settings(IA_PROVIDER="gemini")
    assert s.relectura_cabecera_activa is None
    assert s.relectura_cabecera_motivo_inactiva == "mismo_proveedor"


def test_f058_r24_mismo_proveedor_va_antes_que_no_habilitado() -> None:
    s = _settings(ENABLE_GEMINI=False, IA_PROVIDER="openai",
                  RELECTURA_CABECERA_PROVIDER="openai")
    assert s.relectura_cabecera_motivo_inactiva == "mismo_proveedor"


def test_f058_r24_no_habilitado() -> None:
    s = _settings(ENABLE_GEMINI=False)
    assert s.relectura_cabecera_activa is None
    assert s.relectura_cabecera_motivo_inactiva == "no_habilitado"


@pytest.mark.parametrize("clave", [None, "", "   "])
def test_f058_r24_sin_clave(clave) -> None:
    s = _settings(GEMINI_API_KEY=clave)
    assert s.relectura_cabecera_activa is None
    assert s.relectura_cabecera_motivo_inactiva == "sin_clave"


@pytest.mark.parametrize(("proveedor", "flag", "clave"), [
    ("claude", "ENABLE_CLAUDE", "ANTHROPIC_API_KEY"),
    ("openai", "ENABLE_OPENAI", "OPENAI_API_KEY"),
])
def test_f058_r24_cada_proveedor_mira_su_flag_y_su_clave(
    proveedor, flag, clave,
) -> None:
    base = {"IA_PROVIDER": "gemini", "ENABLE_OPENAI": False,
            "RELECTURA_CABECERA_PROVIDER": proveedor}
    assert _settings(**{**base, flag: False}
                     ).relectura_cabecera_motivo_inactiva == "no_habilitado"
    assert _settings(**{**base, flag: True, clave: None}
                     ).relectura_cabecera_motivo_inactiva == "sin_clave"
    s = _settings(**{**base, flag: True, clave: CLAVE_FALSA})
    assert s.relectura_cabecera_activa == proveedor
    assert s.relectura_cabecera_motivo_inactiva is None


def test_f058_r24_la_relectura_no_impide_arrancar() -> None:
    s = _settings(RELECTURA_CABECERA_PROVIDER="claude")      # sin habilitar
    assert s.relectura_cabecera_motivo_inactiva == "no_habilitado"


@pytest.mark.parametrize(("entorno", "mensaje"), [
    ({"IA_PROVIDER": "openai", "OPENAI_API_KEY": None},
     "IA_PROVIDER=openai requiere OPENAI_API_KEY."),
    ({"IA_PROVIDER": "gemini", "GEMINI_API_KEY": " "},
     "IA_PROVIDER=gemini requiere GEMINI_API_KEY."),
    ({"IA_PROVIDER": "claude", "ENABLE_CLAUDE": True},
     "IA_PROVIDER=claude requiere ANTHROPIC_API_KEY."),
    ({"IA_PROVIDER": "claude"},
     "IA_PROVIDER='claude' pero ENABLE_CLAUDE no esta a true."),
])
def test_f058_r24_el_validador_del_primario_no_cambia(entorno, mensaje) -> None:
    with pytest.raises(ValidationError) as exc:
        _settings(**entorno)
    assert mensaje in str(exc.value)


# ------------------------------- R25 · cableado --------------------------- #

def _wiring(caplog, **entorno):
    with caplog.at_level(logging.INFO, logger=LOGGER_APP):
        app = build_app(_settings(**entorno))
    lineas = [(r.levelno, r.getMessage()) for r in caplog.records
              if r.name == LOGGER_APP and "relectura cabecera" in r.getMessage()]
    return app, lineas


def test_f058_r25_activa_con_sigrid_cablea_la_consulta_de_obra(caplog) -> None:
    app, lineas = _wiring(caplog, OBRA_EXISTE_TIMEOUT_S=2.5, **SIGRID)
    pipeline = app.state.pipeline
    assert pipeline._relectura_provider == "gemini"
    assert isinstance(pipeline._obras, ComprobadorObra)
    assert pipeline._obras.timeout_s == 2.5
    # El mismo cliente de sigrid-api que el catálogo auxhor.
    assert isinstance(pipeline._obras._client, SigridLookupClient)
    assert pipeline._obras._client is pipeline._catalog_provider._client
    assert lineas == [(logging.INFO, (
                       "[partes-sv2][wiring] relectura cabecera ACTIVA "
                       "provider=gemini model=gemini-falso comprueba_obra=True "
                       "timeout_obra_s=2.5"))]


def test_f058_r25_activa_sin_sigrid_avisa_y_no_comprueba_obra(caplog) -> None:
    app, lineas = _wiring(caplog)
    pipeline = app.state.pipeline
    assert pipeline._relectura_provider == "gemini"
    assert pipeline._obras is None
    assert lineas == [(logging.WARNING, (
                       "[partes-sv2][wiring] relectura cabecera ACTIVA "
                       "provider=gemini model=gemini-falso comprueba_obra=False "
                       "timeout_obra_s=5.0"))]


def test_f058_r25_inactiva_avisa_con_el_motivo(caplog) -> None:
    app, lineas = _wiring(caplog, GEMINI_API_KEY=None, **SIGRID)
    pipeline = app.state.pipeline
    assert pipeline._relectura_provider is None
    assert pipeline._obras is None
    assert lineas == [(logging.WARNING, (
                       "[partes-sv2][wiring] relectura cabecera INACTIVA "
                       "motivo=sin_clave"))]


def test_f058_r25_desactivada(caplog) -> None:
    app, lineas = _wiring(caplog, RELECTURA_CABECERA=False, **SIGRID)
    assert app.state.pipeline._relectura_provider is None
    assert app.state.pipeline._obras is None
    assert lineas == [(logging.INFO, (
                       "[partes-sv2][wiring] relectura cabecera DESACTIVADA"))]


def test_f058_r25_ningun_log_de_cableado_lleva_secretos(caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        build_app(_settings(**SIGRID))
    for registro in caplog.records:
        texto = registro.getMessage()
        assert CLAVE_FALSA not in texto
        assert CLAVE_SIGRID not in texto


# ------------------------------- R26 · /health ---------------------------- #

def _health(**entorno) -> dict:
    return TestClient(build_app(_settings(**entorno))).get("/health").json()


def test_f058_r26_health_con_relectura_activa() -> None:
    assert _health(**SIGRID)["relectura_cabecera"] == {
        "provider": "gemini", "model": "gemini-falso", "comprueba_obra": True}
    assert _health()["relectura_cabecera"] == {
        "provider": "gemini", "model": "gemini-falso", "comprueba_obra": False}


@pytest.mark.parametrize("entorno", [
    {"RELECTURA_CABECERA": False}, {"ENABLE_GEMINI": False}])
def test_f058_r26_health_sin_relectura_es_null(entorno) -> None:
    cuerpo = _health(**entorno)
    assert "relectura_cabecera" in cuerpo
    assert cuerpo["relectura_cabecera"] is None
    assert cuerpo["provider"] == "openai"                      # lo de antes


# ------------------------- R15 · el worker y su document_id ---------------- #

class ColaDoble:
    def __init__(self, mensajes: list[dict]) -> None:
        self.mensajes = mensajes
        self.enviados: list[tuple[str, dict]] = []

    def asegurar_colas(self, nombres) -> None:
        pass

    def consumir(self, cola: str, handler) -> None:
        for mensaje in self.mensajes:
            handler(mensaje)

    def enviar(self, cola: str, mensaje: dict) -> None:
        self.enviados.append((cola, mensaje))


class BlobDoble:
    def __init__(self) -> None:
        self.subidos: list[str] = []

    def asegurar_contenedores(self, nombres) -> None:
        pass

    def descargar(self, contenedor: str, nombre: str) -> bytes:
        return b"%PDF-1.4 " + nombre.encode()

    def subir(self, contenedor, nombre, datos, tipo) -> None:
        self.subidos.append(nombre)


class PipelineDoble:
    def __init__(self) -> None:
        self.peticiones = []

    def run(self, request) -> dict:
        self.peticiones.append(request)
        return {"meta": {}, "data": {}, "debug": {}}


def test_f058_r15_el_worker_pasa_el_document_id(monkeypatch) -> None:
    pipeline = PipelineDoble()
    cola = ColaDoble([{"document_id": "doc-uno", "filename": "a.pdf"},
                      {"document_id": "doc-dos"}])
    blob = BlobDoble()
    ajustes = SimpleNamespace(
        log_dir="logs", log_level="INFO", colas_connection_string="cs-falsa",
        colas_account_url=None, blobs_connection_string=None,
        blobs_account_url=None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "construir_cola_cliente",
                        lambda **k: cola)
    monkeypatch.setattr(main_worker, "construir_blob_cliente",
                        lambda **k: blob)
    monkeypatch.setattr(main_worker, "build_app", lambda s: SimpleNamespace(
        state=SimpleNamespace(pipeline=pipeline)))
    assert main_worker.main() == 0
    assert [p.document_id for p in pipeline.peticiones] == ["doc-uno", "doc-dos"]
    assert [p.filename for p in pipeline.peticiones] == ["a.pdf", "document.pdf"]
    assert blob.subidos == ["doc-uno.json", "doc-dos.json"]
