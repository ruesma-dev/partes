# create_sv4_front.ps1
# Crea el Container App del PORTAL de partes (sv4-partes), CON ingress externo.
# Fase 4.1: sin autenticacion todavia (la Easy Auth + grupo Entra va en 4.2).
#
# A diferencia de los workers (sv2/sv3):
#   - Lleva INGRESS externo (target-port 8014, el puerto de uvicorn del portal).
#   - min=1 (portal siempre vivo, sin cold start) / max=2.
#   - NO tiene scale-rule de cola (escala por HTTP por defecto).
#   - NO override de command/args: el Dockerfile ya hace CMD ["python","main.py"].
#
# Lee la MISMA BBDD 'partes' que sv3 (usuario admin del servidor). Activa:
#   - Sigrid (solo lectura): desplegable de codigos de hora (auxhor).
#   - Graph (GRAPH_KEY): visor del PDF del parte archivado en SharePoint.
#
# Requisitos previos:
#   - Imagen sv4 en el ACR:  .\build_images_partes.ps1 -Solo sv4
#   - Secretos en el Key Vault: PG-PASSWORD, GRAPH-KEY, SIGRID-API-FUNCTION-KEY.
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\create_sv4_front.ps1

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

Write-Host "`n=== sv4 (portal de revision, ingress externo) ===" -ForegroundColor Green

$sv4Secrets = @(
    "pg-password=$(KvRef 'PG-PASSWORD')",
    "graph-key=$(KvRef 'GRAPH-KEY')",
    "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')"
)

$sv4Env = @(
    # --- API / uvicorn: ESCUCHAR EN 0.0.0.0 dentro del contenedor ---
    "API_HOST=0.0.0.0", "API_PORT=8014",
    "LOG_DIR=/tmp/logs", "LOG_LEVEL=INFO",
    "APP_TITLE=Partes de Trabajo",
    # --- BBDD 'partes' (misma que sv3); la DB ya existe -> NO autocrear ---
    "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
    "PG_USER=$PG_ADMIN", "PG_PASSWORD=secretref:pg-password",
    "PG_ADMIN_DB=postgres", "PG_ADMIN_USER=$PG_ADMIN",
    "PG_ADMIN_PASSWORD=secretref:pg-password",
    "AUTO_CREATE_DATABASE=false",
    # --- Sigrid (solo lectura): desplegable de codigos de hora ---
    "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
    "SIGRID_API_TIMEOUT_S=30",
    # --- Graph: visor del PDF (drive/item se toman del propio parte) ---
    "GRAPH_KEY=secretref:graph-key", "GRAPH_TIMEOUT_S=60",
    "SHAREPOINT_DRIVE_ID=$($SP['SHAREPOINT_DRIVE_ID'])",
    # --- Jornada del DIA (F-015): mapa candef -> jornada SEMANAL. ESPEJO
    #     del de sv3; el mismo valor en los dos o los avisos del portal
    #     dejan de coincidir con el reparto de horas. No es secreto. ---
    "JORNADA_SEMANAL_POR_CANDEF=8:40,9:42", "JORNADA_CACHE_TTL_S=600",
    # --- Festivos del calendario (RESPALDO de sesame-api, ver mas abajo) ---
    "HOLIDAYS_ENABLED=true", "HOLIDAYS_SUBDIV=MD"
)

# --- sesame-api (F-003): festivos reales por trabajador ---------------------
# Solo se cablea si $SESAME_BASE_URL tiene valor (mira 00_vars_partes.ps1).
# Sin ella, sv4 sale con la integracion APAGADA y usa su calendario de
# festivos local: exactamente el comportamiento anterior a F-003.
if ($SESAME_BASE_URL) {
    $sv4Secrets += "sesame-key=$(KvRef 'SESAME-API-KEY')"
    $sv4Env += @(
        "SESAME_API_BASE_URL=$SESAME_BASE_URL",
        "SESAME_API_KEY=secretref:sesame-key",
        "SESAME_API_TIMEOUT_S=10",
        "SESAME_CACHE_TTL_S=21600"
    )
    Write-Host "[sv4] sesame-api CABLEADO ($SESAME_BASE_URL)" -ForegroundColor Cyan
} else {
    Write-Host "[sv4] sesame-api NO cableado (SESAME_BASE_URL vacia): festivos locales" -ForegroundColor DarkGray
}

$a = @("containerapp","create","-n","ca-sv4-front","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv4'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,
       "--min-replicas","1","--max-replicas","2",
       "--ingress","external","--target-port","8014","--transport","auto",
       "--secrets") + $sv4Secrets + @("--env-vars") + $sv4Env + @("--tags") + $TAGS
Run-Az $a

# --- FQDN publico (lo necesitaras para 4.2 Easy Auth y la card del Portal) ---
$FQDN = az containerapp show -n ca-sv4-front -g $RG `
          --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "`n=== sv4 creado (portal, ingress externo) ===" -ForegroundColor Green
az containerapp show -n ca-sv4-front -g $RG `
  --query "{Estado:properties.provisioningState, Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, FQDN:properties.configuration.ingress.fqdn}" `
  -o table

Write-Host "`nURL del portal:  https://$FQDN" -ForegroundColor Cyan
Write-Host "Logs:  az containerapp logs show -n ca-sv4-front -g $RG --tail 60 --follow" -ForegroundColor Yellow
Write-Host "`nGUARDA este FQDN: lo usaras en 4.2 (redirect URI del App Registration) y en la card del Portal." -ForegroundColor Yellow
