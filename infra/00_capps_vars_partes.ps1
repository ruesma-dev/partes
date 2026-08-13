# 00_capps_vars_partes.ps1
# Variables para crear los Container Apps de PARTES. Dot-source DESPUES de
# 00_vars_partes.ps1:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#
# Calcula valores derivados de Fase 1 y deja el bloque SharePoint/Sigrid (no
# secretos) que ya usa partes (copiado de tu sv3/.env y sv4/.env).

$ErrorActionPreference = "Stop"
if (-not $RG) { throw "Falta `$RG. Haz primero:  . .\00_vars_partes.ps1" }

# --- Derivados de Fase 1 ----------------------------------------------------
$Global:MI_ID       = az identity show -n $MI -g $RG --query "id"       -o tsv
$Global:MI_CLIENTID = az identity show -n $MI -g $RG --query "clientId" -o tsv
$Global:ACR_LOGIN   = "$ACR.azurecr.io"
$Global:KV_URI      = "https://$KV.vault.azure.net"
$Global:PG_HOST     = "$PG.postgres.database.azure.com"
$Global:QUEUE_URL   = "https://$STORAGE.queue.core.windows.net"
$Global:BLOB_URL    = "https://$STORAGE.blob.core.windows.net"

# --- SharePoint (NO secreto; el secreto GRAPH_KEY va por Key Vault) ----------
# Mismo drive del piloto; carpeta raiz 'partes'. (De tu sv3/.env y sv4/.env.)
$Global:SP = [ordered]@{
  "SHAREPOINT_MODE"        = "drive_id"
  "SHAREPOINT_DRIVE_ID"    = "b!1MGRgCm-hU2ZQzBy5nJKU0IHpwhGorZHmWz-yozHEtpEwh0tlcBwQqMKgTOZjcR_"
  "SHAREPOINT_FOLDER_ROOT" = "partes"
  "SHAREPOINT_LINK_TYPE"   = "view"
  "SHAREPOINT_LINK_SCOPE"  = "organization"
}

# --- Sigrid (no secreto) ----------------------------------------------------
$Global:SIGRID_DB = "ruesma"   # SIGRID_API_DATABASE

# --- Escalado KEDA ----------------------------------------------------------
$Global:KEDA_QUEUE_LENGTH = 5     # mensajes objetivo por replica
$Global:WORKER_MAX_REPLICAS = 5   # tope de replicas de cada worker
# NOTA: para sv2 (Gemini) este tope = tu presupuesto de concurrencia LLM.

Write-Host "[capps-vars-partes] MI_CLIENTID=$MI_CLIENTID  PG_HOST=$PG_HOST" -ForegroundColor Cyan
Write-Host "[capps-vars-partes] QUEUE_URL=$QUEUE_URL" -ForegroundColor Cyan
Write-Host "[capps-vars-partes] BLOB_URL=$BLOB_URL" -ForegroundColor Cyan
