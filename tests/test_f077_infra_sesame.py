# tests/test_f077_infra_sesame.py
"""F-077 · R27–R30: el encendido de Sesame HR en `infra/`, por lectura estatica.

`add_sesame_partes.ps1` sigue siendo el unico paso del humano para encender
(y con `-Quitar`, apagar):

  - R27: en `ca-sv3-persistencia` crea el secreto `sesame-token`
    (`keyvaultref` a `SESAME-TOKEN` por `$MI_ID`) y fija `SESAME_BASE_URL`,
    `SESAME_TOKEN=secretref:sesame-token`, `SESAME_TIMEOUT_S` y
    `SESAME_FESTIVOS_MINIMOS`; despues, en `ca-sv4-front`, solo
    `FESTIVOS_SESAME_ENABLED=true`, sin secreto. Antes retira de cada app
    las variables de la pasarela que tenga (y el secreto `sesame-key`).
  - R28: valida `https://` y el secreto `SESAME-TOKEN` antes del primer
    `containerapp`.
  - R29: `-Quitar` retira solo las variables que la app tenga.
  - R30: `create_capps_partes.ps1` y `create_sv4_front.ps1` cablean lo
    mismo; `add_secrets_partes.ps1` pide `SESAME-TOKEN` y no
    `SESAME-API-KEY`; `00_vars_partes.ps1` deja la URL vacia; ningun `.ps1`
    lleva URL de Sesame ni token; CRLF y sin BOM.

No se ejecuta nada: se lee. Sustituye a `test_f032_infra_sesame.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

INFRA = Path(__file__).resolve().parents[1] / "infra"
SCRIPT = INFRA / "add_sesame_partes.ps1"
CAPPS = INFRA / "create_capps_partes.ps1"
SV4 = INFRA / "create_sv4_front.ps1"
SECRETOS = INFRA / "add_secrets_partes.ps1"
VARS = INFRA / "00_vars_partes.ps1"
TOCADOS = [SCRIPT, CAPPS, SV4, SECRETOS, VARS]

RETIRADAS = ("SESAME_API_BASE_URL", "SESAME_API_KEY", "SESAME_API_TIMEOUT_S",
             "SESAME_CACHE_TTL_S")
PROPIAS_SV3 = ("SESAME_BASE_URL", "SESAME_TOKEN", "SESAME_TIMEOUT_S",
               "SESAME_FESTIVOS_MINIMOS")


def _codigo(ruta: Path) -> str:
    """El script sin comentarios de linea (lo que de verdad se ejecuta)."""
    return "\n".join(l for l in ruta.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("#"))


@pytest.fixture(scope="module")
def script() -> str:
    return _codigo(SCRIPT)


def _lista(script: str, nombre: str) -> list[str]:
    """Los literales de `$nombre = @( ... )`."""
    m = re.search(r"\$" + nombre + r"\s*=\s*@\((.*?)\)", script, re.S)
    assert m, f"sin ${nombre}"
    return re.findall(r'"([^"]+)"', m.group(1))


# --------------------------------- R27 ---------------------------------- #

def test_f077_r27_solo_el_parametro_quitar(script) -> None:
    bloque = re.search(r"param\s*\((.*?)\)\s*\n", script, re.S | re.I)
    assert bloque and re.findall(r"\$(\w+)", bloque.group(1)) == ["Quitar"]


def test_f077_r27_las_retiradas_son_las_de_la_pasarela(script) -> None:
    assert _lista(script, "RETIRADAS") == list(RETIRADAS)


def test_f077_r27_sv3_secreto_por_key_vault_e_identidad(script) -> None:
    assert re.search(
        r'"sesame-token=keyvaultref:\$KV_URI/secrets/SESAME-TOKEN,'
        r'identityref:\$MI_ID"', script)
    assert "SESAME-API-KEY" not in script
    assert script.count('"secret", "set"') == 1        # solo en sv3


def test_f077_r27_variables_de_sv3(script) -> None:
    sv3 = _lista(script, "VARS_SV3")
    assert sv3 == ["SESAME_BASE_URL=$SESAME_BASE_URL",
                   "SESAME_TOKEN=secretref:sesame-token",
                   "SESAME_TIMEOUT_S=10",
                   "SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS"]


def test_f077_r27_sv4_solo_el_interruptor_y_sin_secreto(script) -> None:
    assert _lista(script, "VARS_SV4") == ["FESTIVOS_SESAME_ENABLED=true"]
    assert "FESTIVOS_SESAME_ENABLED" not in " ".join(_lista(script,
                                                            "VARS_SV3"))


def test_f077_r27_sv3_antes_que_sv4(script) -> None:
    assert re.search(r'\$SV3APP\s*=\s*"ca-sv3-persistencia"', script)
    assert re.search(r'\$SV4APP\s*=\s*"ca-sv4-front"', script)
    llamadas = re.findall(r"^\s*(Encender-Sv[34]|Apagar-App)\b", script, re.M)
    assert llamadas.index("Encender-Sv3") < llamadas.index("Encender-Sv4")


def test_f077_r27_retira_las_presentes_antes_y_el_secreto_viejo(
        script) -> None:
    assert ('--query "properties.template.containers[0].env[].name"'
            in script)
    limpiar = re.search(r"function Retirar-Viejas.*?\n\}", script, re.S)
    assert limpiar, "sin Retirar-Viejas"
    cuerpo = limpiar.group(0)
    assert "--remove-env-vars" in cuerpo
    assert re.search(r'"secret",\s*"remove".*"--secret-names",\s*'
                     r'"sesame-key"', cuerpo, re.S)
    # La limpieza va ANTES de fijar nada en cada app.
    for funcion in ("Encender-Sv3", "Encender-Sv4"):
        f = re.search(r"function " + funcion + r".*?\n\}", script, re.S)
        assert f, funcion
        assert f.group(0).index("Retirar-Viejas") < f.group(0).index(
            "--set-env-vars")


def test_f077_r27_espera_a_la_revision_nueva(script) -> None:
    assert "latestReadyRevisionName" in script
    assert "latestRevisionName" in script


# --------------------------------- R28 ---------------------------------- #

def test_f077_r28_valida_antes_del_primer_containerapp(script) -> None:
    previo = script[:script.index("containerapp")]
    assert re.search(r"\$SESAME_BASE_URL\s+-notmatch\s+'\^https://'", previo)
    assert "-not $SESAME_BASE_URL" in previo
    assert re.search(r"az keyvault secret show --vault-name \$KV --name "
                     r'"SESAME-TOKEN" --query id', previo)
    assert previo.count("throw") >= 2
    assert "http(s)" not in previo and "^https?" not in previo


def test_f077_r28_no_lee_el_valor_del_token(script) -> None:
    texto = script.lower()
    assert "--query value" not in texto
    assert "storage" not in texto and "enqueue" not in texto


# --------------------------------- R29 ---------------------------------- #

def test_f077_r29_quitar_retira_solo_las_presentes(script) -> None:
    assert re.search(r"if\s*\(\$Quitar\)", script)
    apagar = re.search(r"function Apagar-App.*?\n\}", script, re.S).group(0)
    assert "Get-EnvNames" in apagar
    assert "--remove-env-vars" in apagar
    assert re.search(r"Where-Object\s*\{\s*\$presentes\s+-contains", apagar)
    # Sin nada que quitar no se crea revision.
    assert re.search(r"if\s*\(-not\s+\$quitar\b|\.Count\s+-eq\s+0", apagar,
                     re.I)


def test_f077_r29_que_quita_en_cada_app(script) -> None:
    assert _lista(script, "QUITAR_SV3") == list(PROPIAS_SV3)
    assert _lista(script, "QUITAR_SV4") == ["FESTIVOS_SESAME_ENABLED"]
    assert re.search(r"Apagar-App\s+\$SV3APP\s+\(\$QUITAR_SV3\s*\+\s*"
                     r"\$RETIRADAS\)", script)
    assert re.search(r"Apagar-App\s+\$SV4APP\s+\(\$QUITAR_SV4\s*\+\s*"
                     r"\$RETIRADAS\)", script)


# --------------------------------- R30 ---------------------------------- #

def _bloque_sesame(ruta: Path) -> str:
    texto = _codigo(ruta)
    i = texto.index("if ($SESAME_BASE_URL)")
    return texto[i:texto.index("$a = @(", i)]


def test_f077_r30_create_capps_cablea_sv3_como_el_script() -> None:
    bloque = _bloque_sesame(CAPPS)
    assert "sesame-token=$(KvRef 'SESAME-TOKEN')" in bloque
    for var in ('"SESAME_BASE_URL=$SESAME_BASE_URL"',
                '"SESAME_TOKEN=secretref:sesame-token"',
                '"SESAME_TIMEOUT_S=10"',
                '"SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS"'):
        assert var in bloque, var
    for viejo in RETIRADAS + ("sesame-key", "SESAME-API-KEY"):
        assert viejo not in bloque, viejo


def test_f077_r30_create_sv4_solo_el_interruptor() -> None:
    bloque = _bloque_sesame(SV4)
    assert '"FESTIVOS_SESAME_ENABLED=true"' in bloque
    assert "Secrets" not in bloque and "KvRef" not in bloque
    for viejo in RETIRADAS + ("SESAME_TOKEN", "SESAME_BASE_URL="):
        assert viejo not in bloque, viejo


def test_f077_r30_add_secrets_pide_el_token() -> None:
    texto = _codigo(SECRETOS)
    assert re.search(r'"SESAME-TOKEN"\s*=\s*"token de la API de Sesame HR',
                     texto)
    assert "SESAME-API-KEY" not in texto and "x-api-key" not in texto


def test_f077_r30_vars_con_la_url_vacia() -> None:
    texto = VARS.read_text(encoding="utf-8")
    assert re.search(r'^\$Global:SESAME_BASE_URL\s*=\s*""\s*$', texto, re.M)
    assert re.search(r"^\$Global:SESAME_FESTIVOS_MINIMOS\s*=\s*1\s*$",
                     texto, re.M)
    assert "SESAME-API-KEY" not in texto


@pytest.mark.parametrize("ruta", TOCADOS, ids=lambda r: r.name)
def test_f077_r30_sin_urls_ni_tokens_literales(ruta) -> None:
    texto = ruta.read_text(encoding="utf-8")
    for linea in texto.splitlines():
        if "SESAME" in linea.upper():
            assert not re.search(r"https?://[\w.-]", linea), linea
    assert not re.search(r"(?i)x-api-key|bearer\s+[A-Za-z0-9._~+/-]{16,}", texto)
    assert not re.search(r"SESAME_TOKEN=(?!secretref:)", texto)
    assert not re.search(r"(?i)sesametime\.com|sesamehr\.\w", texto)


@pytest.mark.parametrize("ruta", TOCADOS, ids=lambda r: r.name)
def test_f077_r30_ps1_en_crlf_y_sin_bom(ruta) -> None:
    crudo = ruta.read_bytes()
    assert not crudo.startswith(b"\xef\xbb\xbf"), ruta.name
    lineas = crudo.split(b"\n")[:-1]
    assert lineas and all(l.endswith(b"\r") for l in lineas), ruta.name
