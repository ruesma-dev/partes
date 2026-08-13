# create_capps_partes.ps1
# Crea los Container Apps WORKER de partes (sv2 extraccion, sv3 persistencia),
# min 0 / max N, con KEDA azure-queue. Clon del create_capps.ps1 de albaranes.
# sv1 (webhook) y sv4 (portal) van aparte (Tanda 3/4).
#
# Requisitos previos:
#   - Imagenes sv2/sv3 en el ACR (build_images_partes.ps1).
#   - Secretos en el Key Vault de partes (PG-PASSWORD, GRAPH-KEY,
#     SIGRID-API-FUNCTION-KEY, GEMINI-API-KEY).
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\create_capps_partes.ps1

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

# ====================================================== sv2 (worker) =========
Write-Host "`n=== sv2 (extraccion, worker q-extraccion, Gemini) ===" -ForegroundColor Green
$sv2Secrets = @("gemini-key=$(KvRef 'GEMINI-API-KEY')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
$sv2Env = @(
    "AZURE_CLIENT_ID=$MI_CLIENTID",
    "COLAS_ACCOUNT_URL=$QUEUE_URL", "BLOBS_ACCOUNT_URL=$BLOB_URL",
    "LOG_DIR=/tmp/logs", "COLA_VISIBILITY_S=600",
    "IA_PROVIDER=gemini", "ENABLE_GEMINI=true",
    "GEMINI_MODEL=gemini-3.1-pro-preview",
    "GEMINI_API_KEY=secretref:gemini-key",
    "ENABLE_CLAUDE=false",
    "PROMPT_KEY=parte_trabajo_es", "PROMPTS_YAML_PATH=config/prompts.yaml",
    "MAX_FILE_MB=25",
    "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
    "AUXHOR_CACHE_TTL_S=600",
    "AUXHOR_EXCLUDE_KEYWORDS=MAQUINARIA,MAQUINA,BECARIO,BECARIA"
)
$a = @("containerapp","create","-n","ca-sv2-extraccion","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv2'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas",$WORKER_MAX_REPLICAS,
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-extraccion-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-extraccion","queueLength=$KEDA_QUEUE_LENGTH",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv2Secrets + @("--env-vars") + $sv2Env + @("--tags") + $TAGS
Run-Az $a

# ====================================================== sv3 (worker) =========
Write-Host "`n=== sv3 (persistencia, worker q-persistencia) ===" -ForegroundColor Green
$sv3Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "graph-key=$(KvRef 'GRAPH-KEY')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
$sv3Env = @(
    "AZURE_CLIENT_ID=$MI_CLIENTID",
    "COLAS_ACCOUNT_URL=$QUEUE_URL", "BLOBS_ACCOUNT_URL=$BLOB_URL",
    "LOG_DIR=/tmp/logs", "COLA_VISIBILITY_S=300",
    "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
    "PG_USER=$PG_ADMIN", "PG_PASSWORD=secretref:pg-password",
    "PG_ADMIN_DB=postgres", "PG_ADMIN_USER=$PG_ADMIN",
    "PG_ADMIN_PASSWORD=secretref:pg-password",
    "GRAPH_KEY=secretref:graph-key",
    "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB", "SIGRID_EMPRESA=0",
    "EMPLEADO_MIN_SCORE=0.6", "OBRA_MIN_SCORE=0.6", "JORNADA_ORDINARIA_HORAS=8",
    "SHAREPOINT_MODE=$($SP['SHAREPOINT_MODE'])",
    "SHAREPOINT_DRIVE_ID=$($SP['SHAREPOINT_DRIVE_ID'])",
    "SHAREPOINT_FOLDER_ROOT=$($SP['SHAREPOINT_FOLDER_ROOT'])",
    "SHAREPOINT_CREATE_LINK=true",
    "SHAREPOINT_LINK_TYPE=$($SP['SHAREPOINT_LINK_TYPE'])",
    "SHAREPOINT_LINK_SCOPE=$($SP['SHAREPOINT_LINK_SCOPE'])"
)
$a = @("containerapp","create","-n","ca-sv3-persistencia","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv3'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas",$WORKER_MAX_REPLICAS,
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-persistencia-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-persistencia","queueLength=$KEDA_QUEUE_LENGTH",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv3Secrets + @("--env-vars") + $sv3Env + @("--tags") + $TAGS
Run-Az $a

Write-Host "`n=== Workers creados ===" -ForegroundColor Green
az containerapp list -g $RG --query "[].name" -o tsv
Write-Host "min-replicas=0: escalan con KEDA al haber mensajes en su cola." -ForegroundColor Yellow
Write-Host "Logs:  az containerapp logs show -n ca-sv2-extraccion -g $RG --tail 60 --follow" -ForegroundColor Yellow
