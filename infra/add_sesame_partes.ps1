# add_sesame_partes.ps1
# F-032 - Encender (o apagar) sesame-api en sv3 y sv4 en UN solo paso.
#
# Con Sesame encendido:
#   - sv3 (ca-sv3-persistencia) pide los festivos de cada trabajador al
#     ingerir un parte y los guarda en la tabla festivos_trabajador.
#   - sv4 (ca-sv4-front) los lee de esa tabla y pide a Sesame solo la
#     jornada del contrato.
# Un trabajador sin fila sigue con el calendario local, con un aviso en el
# portal y SIN bloqueo (DA17 = B).
#
# Que hace, en sv3 y DESPUES en sv4 (sv3 primero: es quien escribe la tabla):
#   1. secreto 'sesame-key' de la app = referencia al Key Vault
#      (SESAME-API-KEY) por la identidad gestionada $MI_ID: la clave nunca
#      pasa por este script ni por la linea de comandos;
#   2. variables SESAME_API_BASE_URL, SESAME_API_KEY=secretref:sesame-key,
#      SESAME_API_TIMEOUT_S y, solo en sv3, SESAME_FESTIVOS_MINIMOS (en sv4,
#      SESAME_CACHE_TTL_S, la cache de la jornada);
#   3. espera a que la revision nueva este lista.
# Es IDEMPOTENTE. No encola nada ni lee el valor de ninguna clave.
#
# Antes de tocar NINGUNA app comprueba que $SESAME_BASE_URL tiene valor y
# empieza por http, y que el secreto SESAME-API-KEY existe en $KV (R35).
#
# Con -Quitar retira de las dos apps sus variables SESAME_* (los dos
# servicios vuelven al calendario local; el secreto queda inerte).
#
# Uso:
#     . .\00_vars_partes.ps1          (y tu 00_vars_partes.local.ps1)
#     . .\00_capps_vars_partes.ps1
#     .\add_sesame_partes.ps1            # encender
#     .\add_sesame_partes.ps1 -Quitar    # apagar
#
# Comprobacion posterior (guia de despliegue de F-032, M5 y M7):
#     az containerapp logs show -n ca-sv3-persistencia -g $RG --tail 100
#     az containerapp logs show -n ca-sv4-front -g $RG --tail 100
# y buscar "[sesame][wiring] CABLEADO" (o "DESACTIVADO" tras -Quitar).

param(
    # Retira las variables SESAME_* de sv3 y sv4 en vez de fijarlas.
    [switch] $Quitar
)

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"   # az escribe avisos a stderr

if (-not $RG)     { throw "Falta `$RG. Haz:  . .\00_vars_partes.ps1" }
if (-not $KV)     { throw "Falta `$KV. Haz:  . .\00_vars_partes.ps1" }
if (-not $MI_ID)  { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars_partes.ps1" }
if (-not $KV_URI) { throw "Falta `$KV_URI. Haz:  . .\00_capps_vars_partes.ps1" }
if ($null -eq $SESAME_FESTIVOS_MINIMOS -or "$SESAME_FESTIVOS_MINIMOS" -eq "") {
    $SESAME_FESTIVOS_MINIMOS = 1
}

az account set --subscription $SUBSCRIPTION

# --- R35: validaciones ANTES de tocar ninguna Container App -----------------
if (-not $Quitar) {
    if (-not $SESAME_BASE_URL -or $SESAME_BASE_URL -notmatch '^https?://') {
        throw "`$SESAME_BASE_URL vacia o sin http(s)://. Ponla en tu 00_vars_partes.local.ps1."
    }
    # `secret show` de un secreto inexistente escribe en stderr: con Stop,
    # PS 5.1 lo convertiria en error terminante. Se mira el codigo de salida.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $kvId = az keyvault secret show --vault-name $KV --name "SESAME-API-KEY" --query id -o tsv 2>$null
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($codigo -ne 0 -or -not $kvId) {
        throw "Falta el secreto SESAME-API-KEY en $KV. Cargalo con add_secrets_partes.ps1."
    }
}

$SV3APP = "ca-sv3-persistencia"
$SV4APP = "ca-sv4-front"

# Orden: sv3 (escribe festivos_trabajador) y despues sv4 (la lee).
$APPS = @(
    @{
        App    = $SV3APP
        Extra  = @("SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS")
        Quitar = @("SESAME_API_BASE_URL", "SESAME_API_KEY", "SESAME_API_TIMEOUT_S", "SESAME_FESTIVOS_MINIMOS")
    },
    @{
        App    = $SV4APP
        Extra  = @("SESAME_CACHE_TTL_S=21600")
        Quitar = @("SESAME_API_BASE_URL", "SESAME_API_KEY", "SESAME_API_TIMEOUT_S", "SESAME_CACHE_TTL_S")
    }
)

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

function Wait-Revision($app) {
    # Lista cuando la ultima revision creada es tambien la ultima lista.
    for ($i = 0; $i -lt 60; $i++) {
        $estado = az containerapp show -n $app -g $RG `
            --query "{ready:properties.latestReadyRevisionName, latest:properties.latestRevisionName}" `
            -o json | ConvertFrom-Json
        if ($estado.ready -and $estado.ready -eq $estado.latest) {
            Write-Host "  $app : revision $($estado.ready) lista" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 10
    }
    throw "La revision nueva de $app no llego a estar lista en 10 minutos: mira sus logs."
}

# Las dos apps tienen que existir antes de tocar ninguna.
foreach ($par in $APPS) {
    $existe = az containerapp list -g $RG --query "[?name=='$($par.App)'].name" -o tsv
    if (-not $existe) { throw "No existe $($par.App) en ${RG}: no se toca nada." }
}

foreach ($par in $APPS) {
    $app = $par.App
    $suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")
    if ($Quitar) {
        Write-Host "`n=== $app : retirando SESAME_* ===" -ForegroundColor Green
        Run-Az ((@("containerapp", "update", "-n", $app, "-g", $RG, "--remove-env-vars") + $par.Quitar) `
                + @("--revision-suffix", $suf))
    } else {
        Write-Host "`n=== $app : encendiendo Sesame ===" -ForegroundColor Green
        Run-Az @("containerapp", "secret", "set", "-n", $app, "-g", $RG, "--secrets",
                 "sesame-key=keyvaultref:$KV_URI/secrets/SESAME-API-KEY,identityref:$MI_ID")
        $vars = @(
            "SESAME_API_BASE_URL=$SESAME_BASE_URL",
            "SESAME_API_KEY=secretref:sesame-key",
            "SESAME_API_TIMEOUT_S=10"
        ) + $par.Extra
        Run-Az ((@("containerapp", "update", "-n", $app, "-g", $RG, "--set-env-vars") + $vars) `
                + @("--revision-suffix", $suf))
    }
    Wait-Revision $app
}

$esperado = if ($Quitar) { "DESACTIVADO" } else { "CABLEADO" }
Write-Host "`nHecho. Comprueba en los logs de arranque '[sesame][wiring] $esperado':" -ForegroundColor Green
Write-Host "  az containerapp logs show -n $SV3APP -g $RG --tail 100"
Write-Host "  az containerapp logs show -n $SV4APP -g $RG --tail 100"
