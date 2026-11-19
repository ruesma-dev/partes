# add_sesame_partes.ps1
# F-032, F-077 - Encender (o apagar) los festivos de Sesame HR en UN solo paso.
#
# Con Sesame encendido (F-077, sin la pasarela sesame-api):
#   - sv3 (ca-sv3-persistencia) es el UNICO que llama a la API oficial de
#     Sesame HR (token Bearer, solo GET): al ingerir un parte pide los
#     festivos de cada trabajador y los guarda en la tabla
#     festivos_trabajador;
#   - sv4 (ca-sv4-front) NO llama a Sesame: solo lee esa tabla, encendida
#     con FESTIVOS_SESAME_ENABLED=true.
# Un trabajador sin fila sigue con el calendario local, con un aviso en el
# portal y SIN bloqueo (DA17 = B de F-032).
#
# Que hace, en sv3 y DESPUES en sv4 (sv3 primero: es quien escribe la tabla):
#   0. retira de cada app las variables de la pasarela que tenga
#      (SESAME_API_BASE_URL, SESAME_API_KEY, SESAME_API_TIMEOUT_S,
#      SESAME_CACHE_TTL_S) y, si existe, su secreto 'sesame-key';
#   1. sv3: secreto 'sesame-token' de la app = referencia al Key Vault
#      (SESAME-TOKEN) por la identidad gestionada $MI_ID: el token nunca
#      pasa por este script ni por la linea de comandos;
#   2. sv3: SESAME_BASE_URL, SESAME_TOKEN=secretref:sesame-token,
#      SESAME_TIMEOUT_S y SESAME_FESTIVOS_MINIMOS;
#   3. sv4: solo FESTIVOS_SESAME_ENABLED=true (sin secreto);
#   4. espera a que la revision nueva de cada app este lista.
# Es IDEMPOTENTE. No encola nada ni lee el valor de ningun secreto.
#
# Antes de tocar NINGUNA app comprueba que $SESAME_BASE_URL tiene valor y
# empieza por https://, y que el secreto SESAME-TOKEN existe en $KV (R28).
#
# Con -Quitar retira de sv3 sus cuatro SESAME_* y de sv4
# FESTIVOS_SESAME_ENABLED, mas las de la pasarela, SOLO las que cada app
# tenga (los dos servicios vuelven al calendario local; el secreto
# 'sesame-token' queda inerte).
#
# Uso:
#     . .\00_vars_partes.ps1          (y tu 00_vars_partes.local.ps1)
#     . .\00_capps_vars_partes.ps1
#     .\add_sesame_partes.ps1            # encender
#     .\add_sesame_partes.ps1 -Quitar    # apagar
#
# Comprobacion posterior (guia de despliegue de F-077, M4 y M6):
#     az containerapp logs show -n ca-sv3-persistencia -g $RG --tail 100
#     az containerapp logs show -n ca-sv4-front -g $RG --tail 100
# y buscar "[sesame][wiring] CABLEADO" (o "DESACTIVADO" tras -Quitar).

param(
    # Retira las variables de Sesame de sv3 y sv4 en vez de fijarlas.
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

# --- R28: validaciones ANTES de tocar ninguna Container App -----------------
if (-not $Quitar) {
    if (-not $SESAME_BASE_URL -or $SESAME_BASE_URL -notmatch '^https://') {
        throw "`$SESAME_BASE_URL vacia o no empieza por https:// (ponla en tu 00_vars_partes.local.ps1)."
    }
    # `secret show` de un secreto inexistente escribe en stderr: con Stop,
    # PS 5.1 lo convertiria en error terminante. Se mira el codigo de salida.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $kvId = az keyvault secret show --vault-name $KV --name "SESAME-TOKEN" --query id -o tsv 2>$null
    $codigo = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($codigo -ne 0 -or -not $kvId) {
        throw "Falta el secreto SESAME-TOKEN en $KV. Cargalo con add_secrets_partes.ps1."
    }
}

$SV3APP = "ca-sv3-persistencia"
$SV4APP = "ca-sv4-front"

# Variables de la pasarela sesame-api (F-003, F-032), ya sin uso.
$RETIRADAS = @("SESAME_API_BASE_URL", "SESAME_API_KEY", "SESAME_API_TIMEOUT_S", "SESAME_CACHE_TTL_S")

# Lo que se fija al encender (R27).
$VARS_SV3 = @(
    "SESAME_BASE_URL=$SESAME_BASE_URL",
    "SESAME_TOKEN=secretref:sesame-token",
    "SESAME_TIMEOUT_S=10",
    "SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS"
)
$VARS_SV4 = @("FESTIVOS_SESAME_ENABLED=true")

# Lo que se retira al apagar (R29), ademas de $RETIRADAS.
$QUITAR_SV3 = @("SESAME_BASE_URL", "SESAME_TOKEN", "SESAME_TIMEOUT_S", "SESAME_FESTIVOS_MINIMOS")
$QUITAR_SV4 = @("FESTIVOS_SESAME_ENABLED")

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

function Get-Sufijo {
    return "r" + (Get-Date -Format "yyyyMMddHHmmss")
}

function Get-EnvNames($app) {
    # Nombres de las variables de entorno del contenedor de la app.
    $nombres = az containerapp show -n $app -g $RG --query "properties.template.containers[0].env[].name" -o tsv
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron leer las variables de $app." }
    return @($nombres | Where-Object { $_ })
}

function Get-SecretNames($app) {
    $nombres = az containerapp secret list -n $app -g $RG --query "[].name" -o tsv
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron leer los secretos de $app." }
    return @($nombres | Where-Object { $_ })
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

function Retirar-Viejas($app) {
    # Paso 0: las variables de la pasarela que la app tenga y, despues (un
    # secreto referenciado no se puede quitar), su secreto 'sesame-key'.
    $presentes = Get-EnvNames $app
    $viejas = @($RETIRADAS | Where-Object { $presentes -contains $_ })
    if ($viejas.Count -gt 0) {
        Write-Host "  $app : retirando $($viejas -join ', ')" -ForegroundColor Yellow
        Run-Az ((@("containerapp", "update", "-n", $app, "-g", $RG, "--remove-env-vars") + $viejas) `
                + @("--revision-suffix", (Get-Sufijo)))
        Wait-Revision $app
    }
    if ((Get-SecretNames $app) -contains "sesame-key") {
        Write-Host "  $app : retirando el secreto sesame-key" -ForegroundColor Yellow
        Run-Az @("containerapp", "secret", "remove", "-n", $app, "-g", $RG,
                 "--secret-names", "sesame-key")
    }
}

function Encender-Sv3 {
    Write-Host "`n=== $SV3APP : encendiendo Sesame HR ===" -ForegroundColor Green
    Retirar-Viejas $SV3APP
    Run-Az @("containerapp", "secret", "set", "-n", $SV3APP, "-g", $RG, "--secrets",
             "sesame-token=keyvaultref:$KV_URI/secrets/SESAME-TOKEN,identityref:$MI_ID")
    Run-Az ((@("containerapp", "update", "-n", $SV3APP, "-g", $RG, "--set-env-vars") + $VARS_SV3) `
            + @("--revision-suffix", (Get-Sufijo)))
    Wait-Revision $SV3APP
}

function Encender-Sv4 {
    Write-Host "`n=== $SV4APP : encendiendo la tabla de festivos ===" -ForegroundColor Green
    Retirar-Viejas $SV4APP
    Run-Az ((@("containerapp", "update", "-n", $SV4APP, "-g", $RG, "--set-env-vars") + $VARS_SV4) `
            + @("--revision-suffix", (Get-Sufijo)))
    Wait-Revision $SV4APP
}

function Apagar-App($app, $candidatas) {
    # R29: solo las que la app tenga; sin nada que quitar, ni revision.
    Write-Host "`n=== $app : retirando Sesame ===" -ForegroundColor Green
    $presentes = Get-EnvNames $app
    $quitar = @($candidatas | Where-Object { $presentes -contains $_ })
    if ($quitar.Count -eq 0) {
        Write-Host "  $app : no tiene variables de Sesame; nada que hacer" -ForegroundColor DarkGray
        return
    }
    Write-Host "  $app : retirando $($quitar -join ', ')" -ForegroundColor Yellow
    Run-Az ((@("containerapp", "update", "-n", $app, "-g", $RG, "--remove-env-vars") + $quitar) `
            + @("--revision-suffix", (Get-Sufijo)))
    Wait-Revision $app
}

# Las dos apps tienen que existir antes de tocar ninguna.
foreach ($app in @($SV3APP, $SV4APP)) {
    $existe = az containerapp list -g $RG --query "[?name=='$app'].name" -o tsv
    if (-not $existe) { throw "No existe $app en ${RG}: no se toca nada." }
}

# Orden: sv3 (escribe festivos_trabajador) y despues sv4 (la lee).
if ($Quitar) {
    Apagar-App $SV3APP ($QUITAR_SV3 + $RETIRADAS)
    Apagar-App $SV4APP ($QUITAR_SV4 + $RETIRADAS)
} else {
    Encender-Sv3
    Encender-Sv4
}

$esperado = if ($Quitar) { "DESACTIVADO" } else { "CABLEADO" }
Write-Host "`nHecho. Comprueba en los logs de arranque '[sesame][wiring] $esperado':" -ForegroundColor Green
Write-Host "  az containerapp logs show -n $SV3APP -g $RG --tail 100"
Write-Host "  az containerapp logs show -n $SV4APP -g $RG --tail 100"
