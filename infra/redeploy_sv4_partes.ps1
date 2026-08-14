# redeploy_sv4_partes.ps1
# Republica SOLO el portal sv4 (ca-sv4-front) tras cambiar su codigo:
#   1) reconstruye la imagen (build_images_partes.ps1 -Solo sv4) y la sube al ACR,
#   2) fuerza una REVISION NUEVA del Container App que tira de esa imagen.
#
# El codigo del portal (app.py, plantillas, static/) va HORNEADO en la imagen;
# reiniciar o Ctrl+F5 NO basta: hay que reconstruir + nueva revision.
#
# Con tag mutable 'latest' el --revision-suffix es lo que OBLIGA el pull de la
# imagen recien subida (si no, el Container App puede quedarse con la vieja).
#
# VERSIONAR (recomendado): en 00_vars_partes.ps1 cambia
#     "sv4" = "sv4-partes:latest"   ->   "sv4" = "sv4-partes:v2"
# vuelve a dot-source 00_vars_partes.ps1 y relanza este script. Asi tienes
# builds reproducibles y rollback trivial (apuntas a un tag anterior).
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\redeploy_sv4_partes.ps1
#
# Prerequisito: haber aplicado los cambios en
#   services/partes-front (monorepo partes)
# y estar logueado (az login) con AcrPush en 'acralbaranesdev'.

param(
    [string] $App = "ca-sv4-front"
)
$ErrorActionPreference = "Stop"

if (-not $ACR) { throw "Falta `$ACR. Haz primero:  . .\00_vars_partes.ps1" }
if (-not $IMG) { throw "Falta `$IMG (mapa de imagenes). Haz primero:  . .\00_vars_partes.ps1" }
if (-not $RG)  { throw "Falta `$RG. Haz primero:  . .\00_vars_partes.ps1" }

$img = $IMG['sv4']
if (-not $img) { throw "No hay entrada 'sv4' en `$IMG (00_vars_partes.ps1)." }
$acrLogin = if ($ACR_LOGIN) { $ACR_LOGIN } else { "$ACR.azurecr.io" }
$imageRef = "$acrLogin/$img"

az account set --subscription $SUBSCRIPTION | Out-Null

# --- 0) El Container App debe existir (esto es REPUBLICAR, no primera vez) ---
$exists = az containerapp show -n $App -g $RG --query "name" -o tsv 2>$null
if (-not $exists) {
    Write-Host "El Container App '$App' no existe en '$RG'." -ForegroundColor Red
    Write-Host "Seria PRIMERA publicacion, no republicacion. Corre en su lugar:" -ForegroundColor Yellow
    Write-Host "    .\create_sv4_front.ps1        # crea ca-sv4-front (ingress 8014)" -ForegroundColor Yellow
    Write-Host "    .\setup_sv4_easyauth.ps1      # Easy Auth + grupo partes-portal-users" -ForegroundColor Yellow
    throw "Abortado: '$App' no existe."
}

# --- 1) Reconstruir SOLO el front y subir la imagen al ACR ------------------
Write-Host "`n=== 1) Build de sv4 -> $imageRef ===" -ForegroundColor Green
try {
    & (Join-Path $PSScriptRoot "build_images_partes.ps1") -Solo sv4
} catch {
    throw "Fallo el build de sv4: $($_.Exception.Message)"
}

# --- 2) Forzar revision nueva que haga PULL de la imagen recien subida ------
# El sufijo debe ser unico y en minusculas [a-z0-9-]. El timestamp lo garantiza.
$suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")
Write-Host "`n=== 2) Nueva revision de $App (suffix=$suf) ===" -ForegroundColor Green
az containerapp update -n $App -g $RG `
    --image $imageRef `
    --revision-suffix $suf | Out-Null
if ($LASTEXITCODE -ne 0) { throw "az containerapp update fallo (exit $LASTEXITCODE)." }

# --- 3) Verificacion --------------------------------------------------------
Write-Host "`n=== 3) Estado tras el redeploy ===" -ForegroundColor Green
$deployedImg = az containerapp show -n $App -g $RG `
    --query "properties.template.containers[0].image" -o tsv
$fqdn = az containerapp show -n $App -g $RG `
    --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "Imagen desplegada : $deployedImg"
Write-Host "Portal            : https://$fqdn"
Write-Host "`nRevisiones (la activa con Trafico=100):" -ForegroundColor Yellow
az containerapp revision list -n $App -g $RG `
    --query "[].{Revision:name, Activa:properties.active, Trafico:properties.trafficWeight, Creada:properties.createdTime}" `
    -o table
Write-Host "`nLogs:  az containerapp logs show -n $App -g $RG --tail 60 --follow" -ForegroundColor Yellow
Write-Host "Tras esto, Ctrl+F5 en el navegador (cache de app.js/styles.css)." -ForegroundColor Yellow
