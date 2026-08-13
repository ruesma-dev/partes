# redeploy_partes.ps1
# Republica uno o varios servicios de PARTES tras cambiar su codigo:
#   1) reconstruye su imagen (build_images_partes.ps1 -Solo svX) y la sube al ACR,
#   2) fuerza una REVISION NUEVA del Container App que tira de esa imagen.
#
# El codigo va HORNEADO en la imagen; reiniciar NO basta: hay que reconstruir
# y crear revision nueva. Con tag mutable 'latest', el --revision-suffix es lo
# que OBLIGA el pull de la imagen recien subida (si no, la app podria quedarse
# con la vieja en cache del nodo).
#
# ORDEN SEGURO (fijo, sin importar como los pases en -Solo):
#     sv2 -> sv3 -> sv5 -> sv4 -> sv1
# El PRODUCTOR (sv1, poller de correo) va SIEMPRE el ultimo, para que cuando
# empiece a encolar los CONSUMIDORES (sv2/sv3) ya esten sanos. Asi evitamos el
# escenario en que sv1 encola y el worker esta en crash-loop (mensajes que se
# agotan en reintentos y se pierden).
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1        # opcional (no lo necesita, pero no molesta)
#     .\redeploy_partes.ps1 -Solo sv4,sv5         # solo los tocados en esta tanda
#     .\redeploy_partes.ps1 -Solo sv1,sv2,sv3,sv4,sv5 # los cinco (sincroniza todo)
#     .\redeploy_partes.ps1                        # sin -Solo = TODOS
#
# NOTA sv5 (partes-transfer): la PRIMERA publicacion se hace con
# create_sv5_transfer.ps1; este script solo REPUBLICA apps existentes.
#
# Prerequisito: haber aplicado los cambios en los proyectos PyCharm
# correspondientes y estar logueado (az login) con AcrPush en 'acralbaranesdev'.

param(
    # Servicios a redesplegar. Se ACEPTAN en cualquier orden; el script los
    # reordena al orden seguro. Sin este parametro se redespliegan todos.
    [ValidateSet("sv1", "sv2", "sv3", "sv4", "sv5")]
    [string[]] $Solo = @("sv1", "sv2", "sv3", "sv4", "sv5"),

    # Salta el 'az acr build' y solo fuerza la revision nueva (util si ya
    # construiste las imagenes a mano y solo quieres re-tirarlas).
    [switch] $SinBuild
)
$ErrorActionPreference = "Stop"
# La extension 'containerapp' de az escribe un WARNING benigno en stderr
# ("The behavior of this command has been altered..."). Con -Stop, PowerShell
# lo trata como error terminante (NativeCommandError). Silenciamos los
# warnings de la CLI en toda la sesion del script para evitarlo.
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

if (-not $ACR) { throw "Falta `$ACR. Haz primero:  . .\00_vars_partes.ps1" }
if (-not $IMG) { throw "Falta `$IMG (mapa de imagenes). Haz primero:  . .\00_vars_partes.ps1" }
if (-not $RG)  { throw "Falta `$RG. Haz primero:  . .\00_vars_partes.ps1" }

# --- Mapa servicio -> nombre REAL del Container App -------------------------
# (Confirmado en el despliegue: rg-partes-dev.)
$APPS = @{
    "sv1" = "ca-sv1-poller"          # productor: poller de correo (min/max 1)
    "sv2" = "ca-sv2-extraccion"      # worker KEDA (min 0) q-extraccion
    "sv3" = "ca-sv3-persistencia"    # worker KEDA (min 0) q-persistencia
    "sv4" = "ca-sv4-front"           # portal, ingress externo (min 1)
    "sv5" = "ca-sv5-transfer"        # registro en Sigrid, ingress INTERNO (min 1)
}
# Workers KEDA a min-replicas 0: la revision NO arranca hasta que su cola
# tenga mensajes. Es esperado; no es un fallo de deploy.
$WORKERS = @("sv2", "sv3")

# --- Orden seguro de despliegue (consumidores antes que el productor) -------
# sv5 (transfer) va ANTES que sv4: sv4 es su consumidor, asi el registro en
# Sigrid ya esta sano cuando el portal levanta con codigo nuevo.
$ORDEN = @("sv2", "sv3", "sv5", "sv4", "sv1")
$pedidos = $Solo | Select-Object -Unique
$plan = $ORDEN | Where-Object { $pedidos -contains $_ }
if (-not $plan) { throw "No hay servicios validos que desplegar en -Solo." }

$acrLogin = if ($ACR_LOGIN) { $ACR_LOGIN } else { "$ACR.azurecr.io" }
$suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")   # unico, [a-z0-9-]

az account set --subscription $SUBSCRIPTION | Out-Null

Write-Host "`n=== Redeploy PARTES ===" -ForegroundColor Cyan
Write-Host "  Pedidos : $($pedidos -join ', ')"
Write-Host "  Orden   : $($plan -join ' -> ')  (consumidores primero, sv1 el ultimo)"
Write-Host "  Suffix  : $suf"
Write-Host "  Build   : $(if ($SinBuild) { 'NO (--SinBuild)' } else { 'si' })"

# --- 0) Precheck: todas las apps deben existir (esto es REPUBLICAR) ----------
foreach ($svc in $plan) {
    $app = $APPS[$svc]
    $exists = & { $ErrorActionPreference = "SilentlyContinue"; az containerapp show -n $app -g $RG --query "name" -o tsv 2>$null }
    if (-not $exists) {
        Write-Host "El Container App '$app' ($svc) no existe en '$RG'." -ForegroundColor Red
        if ($svc -eq "sv5") {
            Write-Host "sv5 aun no esta dado de alta: usa .\create_sv5_transfer.ps1" -ForegroundColor Red
        }
        throw "Abortado: '$app' no existe (seria PRIMERA publicacion, no republicacion)."
    }
    if (-not $IMG[$svc]) { throw "No hay entrada '$svc' en `$IMG (00_vars_partes.ps1)." }
}

$build = Join-Path $PSScriptRoot "build_images_partes.ps1"
if (-not $SinBuild -and -not (Test-Path $build)) {
    throw "No encuentro build_images_partes.ps1 junto a este script."
}

# --- Despliegue por servicio en el orden seguro -----------------------------
foreach ($svc in $plan) {
    $app = $APPS[$svc]
    $imageRef = "$acrLogin/$($IMG[$svc])"

    Write-Host "`n============================================================" -ForegroundColor DarkGray
    Write-Host "=== $svc -> $app" -ForegroundColor Green
    Write-Host "    imagen: $imageRef"

    # 1) Build (salvo -SinBuild)
    if (-not $SinBuild) {
        Write-Host "--- 1) Build ($svc) ---" -ForegroundColor Green
        try {
            & $build -Solo $svc
        } catch {
            throw "Fallo el build de ${svc}: $($_.Exception.Message)"
        }
        if ($LASTEXITCODE -ne 0) { throw "Build de $svc fallo (exit $LASTEXITCODE)." }
    }

    # 2) Revision nueva que hace PULL de la imagen recien subida
    Write-Host "--- 2) Nueva revision de $app (suffix=$suf) ---" -ForegroundColor Green
    az containerapp update -n $app -g $RG `
        --image $imageRef `
        --revision-suffix $suf | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az containerapp update fallo en $app (exit $LASTEXITCODE)." }

    if ($WORKERS -contains $svc) {
        Write-Host "    (worker KEDA min-replicas=0: la revision nueva arrancara" -ForegroundColor DarkYellow
        Write-Host "     cuando su cola tenga mensajes; hasta entonces figura a 0 replicas)" -ForegroundColor DarkYellow
    }
}

# --- 3) Verificacion final --------------------------------------------------
Write-Host "`n=== 3) Estado tras el redeploy ===" -ForegroundColor Green
foreach ($svc in $plan) {
    $app = $APPS[$svc]
    $deployedImg = az containerapp show -n $app -g $RG `
        --query "properties.template.containers[0].image" -o tsv
    $activa = az containerapp show -n $app -g $RG `
        --query "properties.latestRevisionName" -o tsv
    Write-Host ("  {0,-22} imagen={1}  revision={2}" -f $app, $deployedImg, $activa)
}

if ($plan -contains "sv4") {
    $fqdn = az containerapp show -n $APPS["sv4"] -g $RG `
        --query "properties.configuration.ingress.fqdn" -o tsv
    Write-Host "`nPortal sv4: https://$fqdn   (Ctrl+F5 para refrescar app.js/styles.css)" -ForegroundColor Yellow
}

if ($plan -contains "sv5") {
    Write-Host "`nsv5 (transfer) es INTERNO (sin URL publica). Comprueba su arranque:" -ForegroundColor Yellow
    Write-Host "  az containerapp logs show -n $($APPS['sv5']) -g $RG --tail 40" -ForegroundColor Yellow
    Write-Host "y en el arranque de sv4 debe aparecer: [transfer][wiring] CABLEADO" -ForegroundColor Yellow
}

# Recordatorio para probar la logica nueva de sv3 (worker a 0):
if ($plan -contains "sv3") {
    Write-Host "`nPara PROBAR sv3 en vivo (conciliacion: computo de horas + casado de partidas):" -ForegroundColor Yellow
    Write-Host "  - Reenvia un correo a partes@ruesma.es (encola y despierta al worker), o" -ForegroundColor Yellow
    Write-Host "  - Subelo un momento a min 1:" -ForegroundColor Yellow
    Write-Host "      az containerapp update -n $($APPS['sv3']) -g $RG --min-replicas 1" -ForegroundColor Yellow
    Write-Host "      # ...prueba y mira logs..." -ForegroundColor Yellow
    Write-Host "      az containerapp update -n $($APPS['sv3']) -g $RG --min-replicas 0" -ForegroundColor Yellow
}

Write-Host "`nLogs de cualquier servicio:" -ForegroundColor Yellow
Write-Host "  az containerapp logs show -n <ca-svX-...> -g $RG --tail 60 --follow" -ForegroundColor Yellow
