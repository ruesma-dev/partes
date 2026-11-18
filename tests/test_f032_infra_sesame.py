# tests/test_f032_infra_sesame.py
"""F-032 · R34–R37: el encendido de Sesame en `infra/`, por lectura estatica.

`add_sesame_partes.ps1` es el unico paso del humano para encender (y con
`-Quitar`, apagar) Sesame en sv3 y sv4: crea el secreto `sesame-key` como
referencia al Key Vault por la identidad gestionada y fija las variables
`SESAME_*`, primero en sv3 y luego en sv4, sin tocar nada si falta la URL o
la clave (R35). No se ejecuta: se lee. El bloque Sesame de
`create_capps_partes.ps1` (sv3) lleva `SESAME_FESTIVOS_MINIMOS` en vez de
`SESAME_CACHE_TTL_S` (R37). Ningun fichero versionado lleva URL real,
claves ni tokens. Los `.ps1` tocados, en CRLF y sin BOM (PowerShell 5.1).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

INFRA = Path(__file__).resolve().parents[1] / "infra"
SCRIPT = INFRA / "add_sesame_partes.ps1"
CAPPS = INFRA / "create_capps_partes.ps1"
VARS = INFRA / "00_vars_partes.ps1"


def _codigo(ruta: Path) -> str:
    """El script sin comentarios de linea (lo que de verdad se ejecuta)."""
    lineas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.lstrip().startswith("#"):
            continue
        lineas.append(linea)
    return "\n".join(lineas)


@pytest.fixture(scope="module")
def script() -> str:
    assert SCRIPT.is_file(), "falta infra/add_sesame_partes.ps1"
    return _codigo(SCRIPT)


# ------------------------------- R34 --------------------------------------- #

def test_f032_r34_solo_el_parametro_quitar(script) -> None:
    bloque = re.search(r"param\s*\((.*?)\)\s*\n", script, re.S | re.I)
    assert bloque, "sin bloque param()"
    parametros = re.findall(r"\$(\w+)", bloque.group(1))
    assert parametros == ["Quitar"]
    assert "-Servicio" not in script and "$Servicio" not in script


def test_f032_r34_carga_las_variables_de_siempre(script) -> None:
    assert "MI_ID" in script and "KV_URI" in script and "$KV" in script
    assert "00_vars_partes.ps1" in SCRIPT.read_text(encoding="utf-8")
    assert "00_capps_vars_partes.ps1" in SCRIPT.read_text(encoding="utf-8")


def _entrada(script: str, app: str) -> str:
    """La entrada `@{ App = $SVnAPP ... }` de la lista de apps."""
    m = re.search(r"@\{\s*App\s*=\s*\$" + app + r"\b(.*?)\n\s*\}",
                  script, re.S)
    assert m, f"sin entrada para {app}"
    return m.group(1)


def test_f032_r34_sv3_antes_que_sv4(script) -> None:
    assert re.search(r'\$SV3APP\s*=\s*"ca-sv3-persistencia"', script)
    assert re.search(r'\$SV4APP\s*=\s*"ca-sv4-front"', script)
    assert script.index("App    = $SV3APP") < script.index("App    = $SV4APP")


def test_f032_r34_secreto_por_key_vault_e_identidad(script) -> None:
    assert re.search(
        r"sesame-key=keyvaultref:\$KV_URI/secrets/SESAME-API-KEY,"
        r"identityref:\$MI_ID", script)
    assert re.search(r'"containerapp",\s*"secret",\s*"set"', script)


def test_f032_r34_las_variables_de_cada_app(script) -> None:
    for var in ("SESAME_API_BASE_URL=$SESAME_BASE_URL",
                "SESAME_API_KEY=secretref:sesame-key",
                "SESAME_API_TIMEOUT_S="):
        assert var in script, var
    assert "--set-env-vars" in script
    sv3, sv4 = _entrada(script, "SV3APP"), _entrada(script, "SV4APP")
    extra3 = re.search(r"Extra\s*=\s*@\((.*?)\)", sv3, re.S).group(1)
    extra4 = re.search(r"Extra\s*=\s*@\((.*?)\)", sv4, re.S).group(1)
    # El minimo de festivos es solo de sv3; el TTL de cache, solo de sv4.
    assert "SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS" in extra3
    assert "SESAME_CACHE_TTL_S" not in extra3
    assert "SESAME_CACHE_TTL_S=" in extra4
    assert "SESAME_FESTIVOS_MINIMOS" not in extra4


def test_f032_r34_espera_a_la_revision_nueva(script) -> None:
    assert "latestReadyRevisionName" in script
    assert "latestRevisionName" in script


# ------------------------------- R35 --------------------------------------- #

def test_f032_r35_valida_antes_del_primer_containerapp(script) -> None:
    primero = script.index("containerapp")
    validaciones = script[:primero]
    assert "SESAME_BASE_URL" in validaciones
    assert re.search(r"-notmatch\s+['\"]\^https?", validaciones) or \
        re.search(r"StartsWith\(['\"]http", validaciones)
    assert re.search(r"keyvault\s*\"?,?\s*\"?secret\"?,?\s*\"?show",
                     validaciones.replace("\",\"", " ")) or \
        "keyvault secret show" in validaciones
    assert "SESAME-API-KEY" in validaciones
    assert "throw" in validaciones


# ------------------------------- R36 --------------------------------------- #

def test_f032_r36_quitar_retira_las_variables_de_las_dos(script) -> None:
    comunes = ("SESAME_API_BASE_URL", "SESAME_API_KEY", "SESAME_API_TIMEOUT_S")
    for app, propia in (("SV3APP", "SESAME_FESTIVOS_MINIMOS"),
                        ("SV4APP", "SESAME_CACHE_TTL_S")):
        quitar = re.search(r"Quitar\s*=\s*@\((.*?)\)",
                           _entrada(script, app), re.S).group(1)
        for var in comunes + (propia,):
            assert f'"{var}"' in quitar, (app, var)
    assert re.search(r"if\s*\(\$Quitar\)", script)
    assert re.search(r'"--remove-env-vars"\)\s*\+\s*\$par\.Quitar', script)


def test_f032_r34_no_encola_ni_lee_claves(script) -> None:
    texto = script.lower()
    for prohibido in ("storage", "enqueue", "accountkey", "--query value",
                      "secret show --vault-name $kv --name sesame-api-key "
                      "--query value"):
        assert prohibido not in texto, prohibido


# ------------------------------- R37 --------------------------------------- #

def _bloque_sesame_sv3() -> str:
    texto = CAPPS.read_text(encoding="utf-8")
    i = texto.index("if ($SESAME_BASE_URL)")
    return texto[i:texto.index("$a = @(", i)]


def test_f032_r37_create_capps_lleva_el_minimo_y_no_el_ttl() -> None:
    bloque = _bloque_sesame_sv3()
    assert "SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS" in bloque
    assert "SESAME_CACHE_TTL_S" not in bloque


def test_f032_r37_vars_tiene_el_minimo_y_la_url_vacia() -> None:
    texto = VARS.read_text(encoding="utf-8")
    assert re.search(r"^\$Global:SESAME_FESTIVOS_MINIMOS\s*=\s*1\s*$",
                     texto, re.M)
    assert re.search(r'^\$Global:SESAME_BASE_URL\s*=\s*""\s*$', texto, re.M)


@pytest.mark.parametrize("ruta", [SCRIPT, CAPPS, VARS])
def test_f032_r37_sin_urls_ni_claves_literales(ruta) -> None:
    texto = ruta.read_text(encoding="utf-8")
    sesame = [l for l in texto.splitlines() if "SESAME" in l.upper()]
    for linea in sesame:
        assert not re.search(r"https?://", linea), linea
        assert not re.search(r"SESAME_API_KEY=(?!secretref:)", linea), linea
    assert not re.search(r"(?i)x-api-key|bearer\s+\w", texto)


@pytest.mark.parametrize("ruta", [SCRIPT, CAPPS, VARS])
def test_f032_ps1_en_crlf_y_sin_bom(ruta) -> None:
    crudo = ruta.read_bytes()
    assert not crudo.startswith(b"\xef\xbb\xbf"), ruta.name
    lineas = crudo.split(b"\n")[:-1]
    assert lineas and all(l.endswith(b"\r") for l in lineas), ruta.name
