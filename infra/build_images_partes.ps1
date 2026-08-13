# build_images_partes.ps1
# Construye y empuja las imagenes de PARTES al ACR compartido con az acr build.
# Clon del de albaranes pero SIN paquete 'comun' (partes es autocontenido).
#
# Uso:
#     . .\00_vars_partes.ps1
#     .\build_images_partes.ps1                # construye todas las que tengan codigo+manifest
#     .\build_images_partes.ps1 -Solo sv2,sv3  # solo esas
#
# Estructura esperada junto a este script:  .\manifests\sv1 ... \sv4
# Requisito: az login con AcrPush en 'acralbaranesdev'.

param(
    [string[]] $Solo = @(),
    [string]   $ManifestsRoot = ""
)
$ErrorActionPreference = "Stop"
if (-not $ACR) { throw "Falta `$ACR. Haz primero:  . .\00_vars_partes.ps1" }
if (-not $IMG) { throw "Falta `$IMG (mapa de imagenes). Haz primero:  . .\00_vars_partes.ps1" }
if (-not $ManifestsRoot) { $ManifestsRoot = Join-Path $PSScriptRoot "manifests" }
if (-not (Test-Path $ManifestsRoot)) { throw "No encuentro 'manifests' en $ManifestsRoot" }

az account set --subscription $SUBSCRIPTION

# --- AJUSTA estas rutas a tus 4 proyectos PyCharm de partes -----------------
$SVC = [ordered]@{
    "sv1" = "C:\Users\pgris\PycharmProjects\partes-email"   # webhook (Tanda 3)
    "sv2" = "C:\Users\pgris\PycharmProjects\partes-api"   # worker extraccion
    "sv3" = "C:\Users\pgris\PycharmProjects\partes-persistencia"   # worker persistencia
    "sv4" = "C:\Users\pgris\PycharmProjects\partes-front"   # portal
    "sv5" = "C:\Users\pgris\PycharmProjects\partes-transfer"   # registro en Sigrid
}

$keys = if ($Solo.Count) { $Solo } else { @($SVC.Keys) }

foreach ($svcKey in $keys) {
    $mf  = Join-Path $ManifestsRoot $svcKey
    $dir = $SVC[$svcKey]
    if (-not $dir)            { Write-Warning "Salto ${svcKey}: sin ruta en `$SVC"; continue }
    if (-not (Test-Path $mf)) { Write-Warning "Salto ${svcKey}: no hay manifests\$svcKey"; continue }
    if (-not (Test-Path $dir)){ Write-Warning "Salto ${svcKey}: no existe $dir (ajusta `$SVC)"; continue }
    $imgRef = $IMG[$svcKey]
    if (-not $imgRef) { Write-Warning "Salto ${svcKey}: sin entrada en `$IMG"; continue }

    Write-Host "`n=== $svcKey  ($dir)  ->  $imgRef ===" -ForegroundColor Cyan
    $rand = [guid]::NewGuid().ToString("N").Substring(0,8)
    $ctx  = Join-Path $env:TEMP "acrbuild_partes_${svcKey}_$rand"
    New-Item -ItemType Directory -Path $ctx | Out-Null
    try {
        # 1) codigo del servicio -> contexto temporal (sin pesados ni basura)
        robocopy $dir $ctx /E `
            /XD .venv .git .idea __pycache__ .pytest_cache logs manifests `
            /XF *.log *.pyc .env *.zip /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy fallo copiando $dir (code $LASTEXITCODE)" }
        $global:LASTEXITCODE = 0   # robocopy: 0-7 son exito

        # 2) Dockerfile/requirements/.dockerignore del manifest (sobrescriben)
        Copy-Item (Join-Path $mf "Dockerfile")       (Join-Path $ctx "Dockerfile")       -Force
        Copy-Item (Join-Path $mf "requirements.txt") (Join-Path $ctx "requirements.txt") -Force
        Copy-Item (Join-Path $mf ".dockerignore")    (Join-Path $ctx ".dockerignore")    -Force

        # 3) build en ACR (sin Docker local)
        Push-Location $ctx
        az acr build --registry $ACR --image $imgRef .
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) { throw "Build de $svcKey FALLO (exit $code). Revisa el log." }
        Write-Host "OK $svcKey -> $ACR.azurecr.io/$imgRef" -ForegroundColor Green
    }
    finally {
        if (Test-Path $ctx) { Remove-Item -Recurse -Force $ctx -ErrorAction SilentlyContinue }
    }
}
