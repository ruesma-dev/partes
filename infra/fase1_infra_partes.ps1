# fase1_infra_partes.ps1
# Provision de la infraestructura de PARTES (Fase 1) con az CLI.
# Crea los recursos PROPIOS de partes y REUTILIZA el ACR y el SERVIDOR
# PostgreSQL de albaranes (no los duplica). NO crea los Container Apps (Fase 2).
#
# Uso:
#     . .\00_vars_partes.ps1
#     .\fase1_infra_partes.ps1
#
# Se te pedira la contrasena del admin de PostgreSQL (el MISMO servidor de
# albaranes) de forma segura, para guardarla en el Key Vault de partes.

$ErrorActionPreference = "Stop"

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }
function Require($val, $msg) {
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "`nABORTADO: $msg" -ForegroundColor Red
        exit 1
    }
}

# --- 0) Precondiciones ------------------------------------------------------
Section "0) Suscripcion, proveedores y extension containerapp"
az account set --subscription $SUBSCRIPTION
foreach ($p in @(
    "Microsoft.App","Microsoft.OperationalInsights","Microsoft.Storage",
    "Microsoft.KeyVault","Microsoft.ManagedIdentity")) {
    az provider register --namespace $p --only-show-errors | Out-Null
}
az extension add --name containerapp --upgrade --only-show-errors | Out-Null

# Contrasena del admin de PostgreSQL (segura; nunca se imprime). Es la del
# servidor COMPARTIDO de albaranes ($PG); la guardaremos en el KV de partes.
if ($env:PG_ADMIN_PASSWORD) {
    $PGPASS = $env:PG_ADMIN_PASSWORD
} else {
    $sec = Read-Host "Contrasena del admin '$PG_ADMIN' del servidor PG '$PG'" -AsSecureString
    $PGPASS = [System.Net.NetworkCredential]::new("", $sec).Password
}
Require $PGPASS "Necesito la contrasena del admin de PostgreSQL para guardarla en el KV de partes."

# objectId del que ejecuta (para darle permiso de escribir secretos en KV).
$ME = az ad signed-in-user show --query "id" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($ME)) {
    Write-Host "  (aviso) no pude resolver tu objectId; me salto el rol 'Key Vault Secrets Officer' para ti." -ForegroundColor Yellow
}

# --- 1) Resource group ------------------------------------------------------
Section "1) Resource group $RG"
az group create -n $RG -l $LOCATION --tags $TAGS | Out-Null

# --- 2) Managed identity (compartida por todos los Container Apps de partes) -
Section "2) Managed identity $MI"
az identity create -n $MI -g $RG -l $LOCATION --tags $TAGS | Out-Null
$MI_PRINCIPAL = az identity show -n $MI -g $RG --query "principalId" -o tsv
$MI_CLIENT    = az identity show -n $MI -g $RG --query "clientId"    -o tsv
$MI_ID        = az identity show -n $MI -g $RG --query "id"          -o tsv
Require $MI_PRINCIPAL "No pude crear/leer la managed identity '$MI'."
Write-Host "  principalId=$MI_PRINCIPAL"

function Assign-Role($role, $scope) {
    # Idempotente: si ya esta asignado, az avisa pero no rompemos.
    az role assignment create --assignee-object-id $MI_PRINCIPAL `
        --assignee-principal-type ServicePrincipal `
        --role $role --scope $scope --only-show-errors 2>$null | Out-Null
}

# --- 3) ACR REUTILIZADO: AcrPull para la MI de partes (cross-RG) -------------
Section "3) AcrPull sobre el ACR compartido $ACR ($ACR_RG)"
$ACR_ID = az acr show -n $ACR -g $ACR_RG --query "id" -o tsv
Require $ACR_ID "No encuentro el ACR '$ACR' en '$ACR_RG'. Revisa el nombre en 00_vars_partes.ps1."
Assign-Role "AcrPull" $ACR_ID
Write-Host "  AcrPull concedido a la MI de partes sobre $ACR."

# --- 4) Log Analytics workspace ---------------------------------------------
Section "4) Log Analytics $LAW"
az monitor log-analytics workspace create -g $RG -n $LAW -l $LOCATION --tags $TAGS | Out-Null
$LAW_CUSTOMERID = az monitor log-analytics workspace show -g $RG -n $LAW --query "customerId" -o tsv
$LAW_KEY = az monitor log-analytics workspace get-shared-keys -g $RG -n $LAW --query "primarySharedKey" -o tsv
Require $LAW_CUSTOMERID "No pude obtener el customerId de Log Analytics '$LAW'."

# --- 5) Storage account + colas + contenedores ------------------------------
Section "5) Storage $STORAGE (3 colas + poison + 2 contenedores)"
az storage account create -n $STORAGE -g $RG -l $LOCATION `
    --sku Standard_LRS --kind StorageV2 `
    --allow-blob-public-access false --min-tls-version TLS1_2 --tags $TAGS | Out-Null
$STKEY = az storage account keys list -n $STORAGE -g $RG --query "[0].value" -o tsv
$STID  = az storage account show -n $STORAGE -g $RG --query "id" -o tsv
Require $STID "El storage '$STORAGE' no se creo (nombre global pillado u otro error). Cambia `$SUFFIX en 00_vars_partes.ps1 y re-ejecuta."
Require $STKEY "No pude leer la clave del storage '$STORAGE'."

# Roles de DATOS para la managed identity (runtime usa MI, no la clave).
Assign-Role "Storage Queue Data Contributor" $STID
Assign-Role "Storage Blob Data Contributor"  $STID

# Colas del pipeline de partes + sus poison (DLQ).
foreach ($q in @("q-emails","q-extraccion","q-persistencia")) {
    az storage queue create --name $q          --account-name $STORAGE --account-key $STKEY --only-show-errors | Out-Null
    az storage queue create --name "$q-poison" --account-name $STORAGE --account-key $STKEY --only-show-errors | Out-Null
}
# Contenedores efimeros del hand-off entre workers (privados).
foreach ($c in @("input","envelopes")) {
    az storage container create --name $c --account-name $STORAGE --account-key $STKEY `
        --public-access off --only-show-errors | Out-Null
}

# --- 6) Key Vault (RBAC) + permisos -----------------------------------------
Section "6) Key Vault $KV (RBAC)"
az keyvault create -n $KV -g $RG -l $LOCATION `
    --enable-rbac-authorization true --tags $TAGS | Out-Null
$KV_ID = az keyvault show -n $KV -g $RG --query "id" -o tsv
Require $KV_ID "El Key Vault '$KV' no se creo (nombre global pillado u otro error). Cambia `$SUFFIX en 00_vars_partes.ps1 y re-ejecuta."
# La MI puede LEER secretos en runtime.
Assign-Role "Key Vault Secrets User" $KV_ID
# Tu (el que despliega) puedes ESCRIBIR secretos (para add_secrets_partes.ps1).
if (-not [string]::IsNullOrWhiteSpace($ME)) {
    az role assignment create --assignee-object-id $ME --assignee-principal-type User `
        --role "Key Vault Secrets Officer" --scope $KV_ID --only-show-errors 2>$null | Out-Null
}

# --- 7) Container Apps Environment (Consumo, publico; como albaranes) --------
Section "7) Container Apps Environment $CAE"
az containerapp env create -n $CAE -g $RG -l $LOCATION `
    --logs-destination log-analytics `
    --logs-workspace-id $LAW_CUSTOMERID --logs-workspace-key $LAW_KEY `
    --tags $TAGS | Out-Null

# --- 8) PostgreSQL REUTILIZADO: BBDD nueva 'partes' + firewall + secreto -----
Section "8) BBDD '$PG_DB' en el servidor compartido $PG ($PG_RG)"
$PG_FQDN = az postgres flexible-server show -n $PG -g $PG_RG --query "fullyQualifiedDomainName" -o tsv
Require $PG_FQDN "No encuentro el servidor PG '$PG' en '$PG_RG'. Revisa el nombre en 00_vars_partes.ps1."

# Permitir servicios de Azure (los Container Apps de Consumo tienen IP saliente
# dinamica). Idempotente (create actua como upsert).
az postgres flexible-server firewall-rule create -g $PG_RG -s $PG `
    --rule-name AllowAzureServices `
    --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --only-show-errors | Out-Null

# Crear la BBDD 'partes' si no existe (las tablas las crea el DDL de arranque
# de sv3/sv4 al bootear; aqui solo la base de datos).
$dbExists = az postgres flexible-server db show -g $PG_RG -s $PG -d $PG_DB --query "name" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($dbExists)) {
    az postgres flexible-server db create -g $PG_RG -s $PG -d $PG_DB --only-show-errors | Out-Null
    Write-Host "  BBDD '$PG_DB' creada en $PG."
} else {
    Write-Host "  BBDD '$PG_DB' ya existe en $PG."
}

# Guardar la contrasena de PG en el Key Vault de partes (RBAC ya propago).
az keyvault secret set --vault-name $KV --name "PG-PASSWORD" --value $PGPASS --only-show-errors | Out-Null
Write-Host "  PG-PASSWORD guardada en $KV."

# --- 9) Resumen -------------------------------------------------------------
Section "9) RESUMEN"
Write-Host "RG               : $RG"
Write-Host "Managed identity : $MI  (clientId=$MI_CLIENT)"
Write-Host "ACR (reutilizado): $ACR.azurecr.io  (AcrPull concedido)"
Write-Host "Log Analytics    : $LAW"
Write-Host "Storage          : $STORAGE  (q-emails/q-extraccion/q-persistencia + poison; input/envelopes)"
Write-Host "Key Vault        : $KV  (PG-PASSWORD ya guardada)"
Write-Host "CA Environment   : $CAE  (Consumo, publico)"
Write-Host "PostgreSQL       : $PG_FQDN  db=$PG_DB user=$PG_ADMIN  (servidor compartido)"
Write-Host "`nSIGUIENTE:" -ForegroundColor Yellow
Write-Host "  1) Rellena y corre .\add_secrets_partes.ps1 con tus claves (GRAPH/SIGRID/GEMINI/...)."
Write-Host "  2) .\blob_lifecycle_partes.ps1 (purga input/ y envelopes/ a 14 dias)."
Write-Host "  3) Tanda 2/3: build de imagenes y creacion de los Container Apps."

# Exporta a la sesion para Fase 2.
$Global:MI_ID = $MI_ID; $Global:MI_CLIENT = $MI_CLIENT; $Global:PG_FQDN = $PG_FQDN
