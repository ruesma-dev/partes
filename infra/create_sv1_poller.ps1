# create_sv1_poller.ps1
# Crea el Container App POLLER de partes (sv1): lee el buzon M365 e INGIERE
# cada parte al pipeline de colas (Blob input/{id}.pdf + q-extraccion).
#
# A diferencia de sv2/sv3 NO escala por KEDA: su fuente es el BUZON, no una
# cola -> min=max=1 (una sola replica; >1 duplicaria la lectura del buzon).
# Sin ingress y sin Easy Auth: no hay usuarios. La auth a Graph es por
# GRAPH_KEY (client-credentials) y a Blob/Cola por managed identity.
#
# Requisitos previos:
#   - Imagen sv1-partes en el ACR:   .\build_images_partes.ps1 -Solo sv1
#   - Secreto GRAPH-KEY en el Key Vault de partes (el MISMO de sv3, ya sin BOM).
#     El app de Graph necesita permiso de APLICACION Mail.ReadWrite sobre el
#     buzon partes@ruesma.es (el poller MUEVE correos a Procesados/Errores),
#     con consentimiento de administrador.
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\create_sv1_poller.ps1

$ErrorActionPreference = "Stop"
if (-not $MI_ID) { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars_partes.ps1" }
if (-not $IMG)   { throw "Falta `$IMG. Haz:  . .\00_vars_partes.ps1" }
az account set --subscription $SUBSCRIPTION

# Secreto de container app -> referencia a Key Vault con la managed identity.
function KvRef($kvSecretName) { "keyvaultref:$KV_URI/secrets/$kvSecretName,identityref:$MI_ID" }

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

# --- Parametros del buzon (ajusta aqui si cambian) --------------------------
$MAILBOX        = "partes@ruesma.es"
$SOURCE_FOLDER  = "inbox"
$POLL_INTERVAL  = "60"
$MAX_EMAILS     = "10"
$MAX_ATTACH_MB  = "25"

# ====================================================== sv1 (poller) =========
Write-Host "`n=== sv1 (poller buzon -> q-extraccion) ===" -ForegroundColor Green
$sv1Secrets = @("graph-key=$(KvRef 'GRAPH-KEY')")
$sv1Env = @(
    "AZURE_CLIENT_ID=$MI_CLIENTID",
    "COLAS_ACCOUNT_URL=$QUEUE_URL", "BLOBS_ACCOUNT_URL=$BLOB_URL",
    "LOG_DIR=/tmp/logs",
    "GRAPH_KEY=secretref:graph-key", "GRAPH_TIMEOUT_S=60",
    "MAILBOX_ADDRESS=$MAILBOX",
    "SOURCE_FOLDER=$SOURCE_FOLDER",
    "FOLDER_PROCESADOS=Procesados", "FOLDER_ERRORES=Errores",
    "NEST_FOLDERS_UNDER_SOURCE=true", "CREATE_SOURCE_IF_MISSING=false",
    "POLL_INTERVAL_S=$POLL_INTERVAL", "MAX_EMAILS=$MAX_EMAILS",
    "MAX_ATTACHMENT_MB=$MAX_ATTACH_MB",
    "COLA_EXTRACCION=q-extraccion", "BLOB_INPUT=input"
)
$a = @("containerapp","create","-n","ca-sv1-poller","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv1'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","1","--max-replicas","1",
       "--command","python","--args","main.py",
       "--secrets") + $sv1Secrets + @("--env-vars") + $sv1Env + @("--tags") + $TAGS
Run-Az $a

Write-Host "`n=== sv1 creado (1 replica fija, sin ingress) ===" -ForegroundColor Green
az containerapp show -n ca-sv1-poller -g $RG `
  --query "{name:name, estado:properties.provisioningState, min:properties.template.scale.minReplicas, max:properties.template.scale.maxReplicas}" `
  -o table
Write-Host "Logs:  az containerapp logs show -n ca-sv1-poller -g $RG --tail 60 --follow" -ForegroundColor Yellow
Write-Host "El poller lista 'inbox' cada $POLL_INTERVAL s; mueve a Procesados/Errores tras ingerir." -ForegroundColor Yellow
