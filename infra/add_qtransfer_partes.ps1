# add_qtransfer_partes.ps1
# F-002 - Colas de la APROBACION ASINCRONA de partes.
#
# Crea en el storage de partes ($STORAGE) lo que necesita el nuevo canal
# sv4 <-> sv5:
#
#   q-transfer                 sv4 -> sv5: peticion de registro
#   q-transfer-poison          DLQ de la anterior
#   q-transfer-result          sv5 -> sv4: veredicto por linea
#   q-transfer-result-poison   DLQ de la anterior
#   contenedor 'transfer'      hand-off del payload (peticiones/ y resultados/)
#
# Va en script APARTE de fase1_infra_partes.ps1 para no reprovisionar la
# infraestructura entera solo por anadir dos colas. Es IDEMPOTENTE: se puede
# ejecutar tantas veces como haga falta.
#
# NO toca la escala de sv5: sigue con min=1 / max=1 e ingress interno, porque
# la escritura en Sigrid usa MAX(ide)+1 con UPDLOCK y el lock que la serializa
# es de PROCESO. Una segunda replica escribiria en paralelo. Tampoco se anade
# regla KEDA: sv5 consume la cola en hilos del MISMO proceso que su API.
#
# Los roles de datos sobre el storage (Storage Queue/Blob Data Contributor para
# la managed identity id-partes-dev) YA los concedio la Fase 1: las colas y el
# contenedor nuevos quedan cubiertos por el mismo ambito.
#
# Todo el acceso de datos va con --auth-mode login (el token de 'az login'),
# nunca con la clave de cuenta. Quien ejecute el script necesita por tanto los
# roles de DATOS sobre el storage (Storage Queue Data Contributor y Storage
# Blob Data Contributor); 'Contributor' del plano de control NO basta.
#
# Uso:
#     . .\00_vars_partes.ps1
#     .\add_qtransfer_partes.ps1
#
# Comprobacion posterior:
#     az storage queue list --account-name stpartespt7m3 --auth-mode login -o table

param(
    # Solo crea colas y contenedor; NO toca las variables de los Container Apps.
    [switch] $SoloStorage,

    # Numero de hilos consumidores de q-transfer en sv5 (fase de preparacion
    # en paralelo; la escritura sigue serializada por el lock).
    [int] $TransferWorkers = 3
)

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"   # az containerapp escribe a stderr

if (-not $STORAGE) { throw "Falta `$STORAGE. Haz:  . .\00_vars_partes.ps1" }
if (-not $RG)      { throw "Falta `$RG. Haz:  . .\00_vars_partes.ps1" }
if ($TransferWorkers -lt 1) { throw "TransferWorkers debe ser 1 o mas." }

az account set --subscription $SUBSCRIPTION

$SV4APP = "ca-sv4-front"
$SV5APP = "ca-sv5-transfer"
$COLA_TRANSFER = "q-transfer"
$COLA_RESULT   = "q-transfer-result"
$CONTENEDOR    = "transfer"

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

Write-Host "`n=== F-002: colas de aprobacion asincrona en $STORAGE ===" -ForegroundColor Green

# La clave de cuenta abre el storage ENTERO y, pasada como parametro,
# viaja en la linea de comandos del proceso. Se usa el token de 'az login'.
# Si az responde AuthorizationPermissionMismatch, faltan los roles de datos
# (ver cabecera), no la clave.

# --- Colas + sus poison (idempotente: 'create' sobre una existente no falla) --
foreach ($q in @($COLA_TRANSFER, $COLA_RESULT)) {
    foreach ($nombre in @($q, "$q-poison")) {
        Run-Az @("storage","queue","create","--name",$nombre,
                 "--account-name",$STORAGE,"--auth-mode","login",
                 "--only-show-errors")
        Write-Host "  cola OK: $nombre" -ForegroundColor Cyan
    }
}

# --- Contenedor del hand-off (privado) ---------------------------------------
Run-Az @("storage","container","create","--name",$CONTENEDOR,
         "--account-name",$STORAGE,"--auth-mode","login",
         "--public-access","off","--only-show-errors")
Write-Host "  contenedor OK: $CONTENEDOR" -ForegroundColor Cyan

Write-Host "`nColas del storage:" -ForegroundColor Green
az storage queue list --account-name $STORAGE --auth-mode login `
    --query "[].name" -o tsv

if ($SoloStorage) {
    Write-Host "`n(-SoloStorage) No se tocan los Container Apps." -ForegroundColor Yellow
    Write-Host "Las variables de entorno estan mas abajo, en los comandos comentados." -ForegroundColor Yellow
    return
}

# --- Variables de entorno de sv4 y sv5 ---------------------------------------
# Ambos leen el storage con la MANAGED IDENTITY (id-partes-dev): se pasan las
# URLs de los endpoints, nunca una connection string ni una clave.
$QUEUE_URL = "https://$STORAGE.queue.core.windows.net"
$BLOB_URL  = "https://$STORAGE.blob.core.windows.net"

$envComunes = @(
    "COLAS_ACCOUNT_URL=$QUEUE_URL",
    "BLOBS_ACCOUNT_URL=$BLOB_URL",
    "COLA_TRANSFER=$COLA_TRANSFER",
    "COLA_TRANSFER_RESULT=$COLA_RESULT",
    "BLOB_TRANSFER=$CONTENEDOR"
)

# Orden de despliegue: primero sv5 (el consumidor) y luego sv4 (el productor).
# Al reves, sv4 encolaria peticiones que todavia no consume nadie.
foreach ($par in @(@{App=$SV5APP; Extra=@("TRANSFER_WORKERS=$TransferWorkers")},
                   @{App=$SV4APP; Extra=@()})) {
    $app = $par.App
    # `containerapp show` de una app inexistente escribe en stderr y, con
    # ErrorActionPreference=Stop, PS 5.1 lo convierte en error terminante
    # aunque haya 2>$null. `list --query` devuelve vacio sin tocar stderr.
    $existe = az containerapp list -g $RG --query "[?name=='$app'].name" -o tsv
    if (-not $existe) {
        Write-Warning "No existe $app : fija a mano las variables (ver abajo)."
        continue
    }
    $suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")
    $vars = $envComunes + $par.Extra
    Write-Host "`n=== $app : variables de cola ===" -ForegroundColor Green
    Run-Az (@("containerapp","update","-n",$app,"-g",$RG,"--set-env-vars") `
            + $vars + @("--revision-suffix",$suf))
    Write-Host "  actualizado (revision $suf)" -ForegroundColor Green
}

# --- Comprobacion de que la escala de sv5 sigue intacta (R16) ----------------
Write-Host "`n=== Escala de sv5 (debe seguir 1/1) ===" -ForegroundColor Green
az containerapp show -n $SV5APP -g $RG `
  --query "{Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, Ingress:properties.configuration.ingress.external}" `
  -o table

Write-Host @"

=== Equivalente MANUAL de lo anterior (por si hay que repetirlo a mano) ===

  az containerapp update -n $SV5APP -g $RG --set-env-vars ``
      COLAS_ACCOUNT_URL=$QUEUE_URL ``
      BLOBS_ACCOUNT_URL=$BLOB_URL ``
      COLA_TRANSFER=$COLA_TRANSFER ``
      COLA_TRANSFER_RESULT=$COLA_RESULT ``
      BLOB_TRANSFER=$CONTENEDOR ``
      TRANSFER_WORKERS=$TransferWorkers

  az containerapp update -n $SV4APP -g $RG --set-env-vars ``
      COLAS_ACCOUNT_URL=$QUEUE_URL ``
      BLOBS_ACCOUNT_URL=$BLOB_URL ``
      COLA_TRANSFER=$COLA_TRANSFER ``
      COLA_TRANSFER_RESULT=$COLA_RESULT ``
      BLOB_TRANSFER=$CONTENEDOR

Para VOLVER al registro sincrono (rollback sin desplegar codigo): quita
COLAS_ACCOUNT_URL de sv4 y el portal registrara por HTTP como antes.

  az containerapp update -n $SV4APP -g $RG --remove-env-vars COLAS_ACCOUNT_URL

Logs:
  az containerapp logs show -n $SV5APP -g $RG --tail 60 --follow
  (en el arranque de sv5 debe verse: [transfer-cola] N worker(s) consumiendo 'q-transfer')
  (en el de sv4:                      [transfer-cola][wiring] CABLEADO cola=q-transfer ...)
"@ -ForegroundColor Yellow
