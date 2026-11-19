# tests/test_f077_sin_pasarela.py
"""F-077 · guardianes del monorepo: sv3 habla con Sesame HR, nadie con la pasarela.

  - R31: ningun `.py` de produccion de sv3 ni de sv4 nombra la pasarela
    `sesame-api` (`x-api-key`, sus rutas `/api/v1/...` ni `SESAME_API_`).
    Excepcion cerrada: los dos `jornada_resolver.py`, que design §6 deja
    intactos aunque su docstring cite `/api/v1/jornada`.
  - R20: sv4 no tiene cliente de Sesame (`infrastructure/sesame/` sin
    `.py`), no lo importa y no nombra `SESAME_TOKEN`.
  - R23: `validar_datos_sesame.py` (F-013) ya no existe.
  - R9 (estatico, por AST): el cliente y el adaptador de Sesame HR de sv3
    no tienen ni una llamada que escriba (`post`, `put`, `patch`,
    `delete`, `request`, `send`, `stream`) ni nombran otro metodo HTTP.
  - R33: la lista cerrada de duplicaciones de `CLAUDE.md` ya no incluye los
    clientes `infrastructure/sesame/` (sigue `festivos_guardados.py`) y
    `harness/servicios.json` no hace depender a sv3 del cliente de sv4.

Lectura estatica: ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SV3 = RAIZ / "services" / "partes-persistencia"
SV4 = RAIZ / "services" / "partes-front"
CLIENTE_HR = SV3 / "infrastructure" / "sesame" / "sesame_hr_client.py"
ADAPTADOR_HR = SV3 / "infrastructure" / "sesame" / "festivos_sesame_hr.py"

#: Lo que solo dice quien habla con la pasarela (R31).
PASARELA = ("x-api-key", "/api/v1/festivos", "/api/v1/jornada",
            "/api/v1/calendarios-festivos", "SESAME_API_")

#: Ficheros que design §6 prohibe tocar aunque su docstring cite la
#: pasarela. Lista CERRADA: crecer exige volver a la spec.
EXCLUIDOS_R31 = {
    SV3 / "application" / "services" / "jornada_resolver.py",
    SV4 / "application" / "services" / "jornada_resolver.py",
}

#: Atributos que escriben o permiten escribir por httpx (R9).
ESCRITURAS = {"post", "put", "patch", "delete", "request", "send", "stream"}


def _produccion(servicio: Path) -> list[Path]:
    """Los `.py` del servicio que no son tests ni cache."""
    out = []
    for ruta in sorted(servicio.rglob("*.py")):
        partes = set(ruta.relative_to(servicio).parts)
        if partes & {"tests", "__pycache__", ".venv", "venv", "logs"}:
            continue
        out.append(ruta)
    return out


# --------------------------------- R31 ---------------------------------- #

@pytest.mark.parametrize("servicio", [SV3, SV4], ids=["sv3", "sv4"])
def test_f077_r31_ningun_codigo_de_produccion_nombra_la_pasarela(
        servicio) -> None:
    hallazgos = []
    for ruta in _produccion(servicio):
        if ruta in EXCLUIDOS_R31:
            continue
        texto = ruta.read_text(encoding="utf-8")
        for marca in PASARELA:
            if marca in texto:
                hallazgos.append(f"{ruta.relative_to(RAIZ)}: {marca}")
    assert hallazgos == []


def test_f077_r31_los_excluidos_existen() -> None:
    """La excepcion no puede tapar un fichero que ya no esta."""
    for ruta in EXCLUIDOS_R31:
        assert ruta.is_file(), ruta


# --------------------------------- R20 ---------------------------------- #

def test_f077_r20_sv4_sin_cliente_de_sesame() -> None:
    carpeta = SV4 / "infrastructure" / "sesame"
    assert not list(carpeta.glob("*.py")), "sv4 conserva infrastructure/sesame/"


def test_f077_r20_sv4_no_importa_el_cliente_ni_nombra_el_token() -> None:
    hallazgos = []
    for ruta in _produccion(SV4):
        texto = ruta.read_text(encoding="utf-8")
        if re.search(r"\binfrastructure\.sesame\b", texto):
            hallazgos.append(f"{ruta.relative_to(RAIZ)}: import")
        if "SESAME_TOKEN" in texto:
            hallazgos.append(f"{ruta.relative_to(RAIZ)}: SESAME_TOKEN")
    assert hallazgos == []


# --------------------------------- R23 ---------------------------------- #

def test_f077_r23_validar_datos_sesame_retirado() -> None:
    assert not (SV4 / "validar_datos_sesame.py").exists()
    assert not (SV4 / "tests" / "test_f013_informe_sesame.py").exists()


# ---------------------------------- R9 ---------------------------------- #

@pytest.mark.parametrize("ruta", [CLIENTE_HR, ADAPTADOR_HR],
                         ids=["cliente", "adaptador"])
def test_f077_r9_sin_llamadas_que_escriban(ruta) -> None:
    assert ruta.is_file(), f"falta {ruta.relative_to(RAIZ)}"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    prohibidos = sorted({
        n.attr for n in ast.walk(arbol)
        if isinstance(n, ast.Attribute) and n.attr in ESCRITURAS})
    assert prohibidos == []
    # Ni un metodo HTTP distinto de GET en un literal (p. ej. `method=`).
    literales = {n.value.upper() for n in ast.walk(arbol)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert not literales & {"POST", "PUT", "PATCH", "DELETE"}
    assert not [k for n in ast.walk(arbol) if isinstance(n, ast.keyword)
                for k in [n.arg] if k == "method"]


def test_f077_r9_el_cliente_pide_con_get() -> None:
    """Y el unico verbo que usa sobre httpx es `get`."""
    arbol = ast.parse(CLIENTE_HR.read_text(encoding="utf-8"))
    llamadas = [n.func.attr for n in ast.walk(arbol)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id in {"client", "cliente_http", "http"}]
    assert llamadas and set(llamadas) == {"get"}


# --------------------------------- R33 ---------------------------------- #

def _lista_cerrada() -> str:
    texto = (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
    inicio = texto.index("LÍMITE DE SERVICIO")
    return texto[inicio:texto.index("Una responsabilidad nueva", inicio)]


def test_f077_r33_claude_md_sin_los_clientes_de_sesame() -> None:
    lista = re.sub(r"\s+", " ", _lista_cerrada())
    assert "los clientes `infrastructure/sesame/`" not in lista
    assert "festivos_guardados.py" in lista


def test_f077_r33_servicios_json_sin_el_cliente_de_sv4() -> None:
    datos = json.loads((RAIZ / "harness" / "servicios.json").read_text(
        encoding="utf-8"))
    for servicio in datos["servicios"]:
        for ruta in servicio.get("depende_de", []):
            assert "infrastructure/sesame" not in ruta, (servicio["nombre"],
                                                         ruta)
