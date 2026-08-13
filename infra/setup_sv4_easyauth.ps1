# setup_sv4_easyauth.ps1
# Fase 4.2: protege el portal sv4 (ca-sv4-front) con Easy Auth (Entra ID) y
# restringe el acceso a los miembros de un GRUPO de seguridad propio.
#
# Mecanismo (mismo patron que albaranes-portal):
#   1) Grupo de seguridad 'partes-portal-users'.
#   2) App Registration dedicada (redirect /.auth/login/aad/callback + secret).
#   3) Enterprise App con "asignacion requerida" + el grupo asignado a ella
#      -> Entra solo emite token a miembros del grupo.
#   4) Easy Auth en el Container App con login obligatorio (redirect a login).
#   5) Admin-consent de permisos basicos -> SSO silencioso desde Portal Ruesma.
#
# IDEMPOTENTE: relanzable sin duplicar (reusa grupo, App, secret de KV y SP).
#
# REQUISITOS:
#   - Permisos Entra para crear grupos y App Registrations (pgris ya es owner).
#   - Asignar GRUPOS a una Enterprise App requiere Entra ID P1. Si el paso de
#     asignacion falla por licencia, lo resolvemos por claim 'groups'.
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\setup_sv4_easyauth.ps1

$ErrorActionPreference = "Stop"
foreach ($v in @('RG','KV','KV_URI','TENANT','MI_ID','SUBSCRIPTION')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_partes.ps1 ; . .\00_capps_vars_partes.ps1"
    }
}
az account set --subscription $SUBSCRIPTION

# --- Parametros -------------------------------------------------------------
$APP_NAME       = "ca-sv4-front"
$GROUP_NAME     = "partes-portal-users"
$GROUP_NICK     = "partes-portal-users"
$APP_REG_NAME   = "partes-portal (sv4 EasyAuth)"
$SECRET_KV_NAME = "EASYAUTH-CLIENT-SECRET"
$CA_SECRET_NAME = "easyauth-client-secret"

# --- 0) FQDN del portal (dinamico) ------------------------------------------
$FQDN = az containerapp show -n $APP_NAME -g $RG `
          --query "properties.configuration.ingress.fqdn" -o tsv
if (-not $FQDN) { throw "No encuentro el FQDN de $APP_NAME (existe el portal?)" }
$REDIRECT = "https://$FQDN/.auth/login/aad/callback"
Write-Host "[easyauth] FQDN=$FQDN" -ForegroundColor Cyan
Write-Host "[easyauth] redirect=$REDIRECT" -ForegroundColor Cyan

# --- 1) Grupo de seguridad (idempotente) ------------------------------------
$GROUP_ID = az ad group list --display-name $GROUP_NAME --query "[0].id" -o tsv
if (-not $GROUP_ID) {
    $GROUP_ID = az ad group create --display-name $GROUP_NAME `
                  --mail-nickname $GROUP_NICK --query id -o tsv
    Write-Host "[easyauth] grupo creado: $GROUP_ID" -ForegroundColor Green
} else {
    Write-Host "[easyauth] grupo ya existe: $GROUP_ID" -ForegroundColor Yellow
}

# --- 2) Anadir al usuario actual como miembro (para poder probar) -----------
$ME = az ad signed-in-user show --query id -o tsv
$isMember = az ad group member check --group $GROUP_ID --member-id $ME --query value -o tsv
if ($isMember -ne "true") {
    az ad group member add --group $GROUP_ID --member-id $ME
    Write-Host "[easyauth] anadido usuario actual ($ME) al grupo" -ForegroundColor Green
} else {
    Write-Host "[easyauth] usuario actual ya es miembro" -ForegroundColor Yellow
}

# --- 3) App Registration (idempotente por displayName) ----------------------
$APP_ID = az ad app list --display-name $APP_REG_NAME --query "[0].appId" -o tsv
if (-not $APP_ID) {
    $APP_ID = az ad app create --display-name $APP_REG_NAME `
                --sign-in-audience AzureADMyOrg `
                --web-redirect-uris $REDIRECT `
                --enable-id-token-issuance true `
                --query appId -o tsv
    Write-Host "[easyauth] App Registration creada: appId=$APP_ID" -ForegroundColor Green
} else {
    az ad app update --id $APP_ID `
        --web-redirect-uris $REDIRECT --enable-id-token-issuance true | Out-Null
    Write-Host "[easyauth] App Registration ya existe: appId=$APP_ID (redirect actualizado)" -ForegroundColor Yellow
}

# --- 4) Client secret -> Key Vault (solo si NO existe ya en KV) --------------
$secretExists = az keyvault secret list --vault-name $KV `
                  --query "[?name=='$SECRET_KV_NAME'] | [0].name" -o tsv
if (-not $secretExists) {
    $CLIENT_SECRET = az ad app credential reset --id $APP_ID --append `
                       --display-name "easyauth" --years 2 --query password -o tsv
    az keyvault secret set --vault-name $KV --name $SECRET_KV_NAME `
        --value $CLIENT_SECRET --only-show-errors | Out-Null
    Write-Host "[easyauth] client secret generado y guardado en KV: $SECRET_KV_NAME" -ForegroundColor Green
} else {
    Write-Host "[easyauth] client secret ya estaba en KV ($SECRET_KV_NAME); lo reuso" -ForegroundColor Yellow
}

# --- 5) Service principal + asignacion requerida + asignar grupo ------------
# Deteccion SIN error (list/filter en vez de show).
$SP_OID = az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv
if (-not $SP_OID) {
    # La App recien creada tarda en propagarse en Entra: reintentos.
    for ($i=1; $i -le 6 -and -not $SP_OID; $i++) {
        try { $SP_OID = az ad sp create --id $APP_ID --query id -o tsv } catch { }
        if (-not $SP_OID) { Start-Sleep -Seconds 10 }
    }
    if (-not $SP_OID) { throw "No pude crear el Service Principal de $APP_ID (propagacion Entra)." }
    Write-Host "[easyauth] Enterprise App (SP) creada: $SP_OID" -ForegroundColor Green
} else {
    Write-Host "[easyauth] Enterprise App (SP) ya existe: $SP_OID" -ForegroundColor Yellow
}
az ad sp update --id $APP_ID --set appRoleAssignmentRequired=true | Out-Null
Write-Host "[easyauth] asignacion-requerida = ON" -ForegroundColor Green

# Asignar el grupo a la Enterprise App (appRoleId 0000.. = acceso por defecto).
$already = az rest --method GET `
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OID/appRoleAssignedTo" `
    --query "value[?principalId=='$GROUP_ID'] | [0].id" -o tsv
if (-not $already) {
    $bodyObj = @{
        principalId = $GROUP_ID
        resourceId  = $SP_OID
        appRoleId   = "00000000-0000-0000-0000-000000000000"
    }
    $tmp = Join-Path $env:TEMP "appRoleAssign_partes.json"
    [System.IO.File]::WriteAllText($tmp, ($bodyObj | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
    az rest --method POST `
        --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OID/appRoleAssignedTo" `
        --headers "Content-Type=application/json" --body "@$tmp" | Out-Null
    Remove-Item $tmp -ErrorAction SilentlyContinue
    Write-Host "[easyauth] grupo $GROUP_NAME asignado a la Enterprise App" -ForegroundColor Green
} else {
    Write-Host "[easyauth] grupo ya asignado a la Enterprise App" -ForegroundColor Yellow
}

# --- 6) Secret en el Container App (KvRef) + Easy Auth ----------------------
az containerapp secret set -n $APP_NAME -g $RG `
    --secrets "$CA_SECRET_NAME=keyvaultref:$KV_URI/secrets/$SECRET_KV_NAME,identityref:$MI_ID" | Out-Null
Write-Host "[easyauth] secret '$CA_SECRET_NAME' (KvRef) anadido al Container App" -ForegroundColor Green

az containerapp auth microsoft update -n $APP_NAME -g $RG `
    --client-id $APP_ID `
    --client-secret-name $CA_SECRET_NAME `
    --issuer "https://login.microsoftonline.com/$TENANT/v2.0" `
    --yes | Out-Null
Write-Host "[easyauth] proveedor Microsoft (Entra) configurado" -ForegroundColor Green

az containerapp auth update -n $APP_NAME -g $RG `
    --enabled true `
    --redirect-provider azureactivedirectory `
    --unauthenticated-client-action RedirectToLoginPage `
    --yes | Out-Null
Write-Host "[easyauth] login OBLIGATORIO activado (no autenticado -> redirige a login)" -ForegroundColor Green

# --- 7) Admin-consent de permisos basicos (SSO silencioso desde el portal) --
# Mejor esfuerzo: si no tienes rol para consent, no aborta (el 1er usuario
# consiente al entrar). Con consent hecho, NO se pide permiso a cada usuario.
try {
    az ad app permission admin-consent --id $APP_ID 2>$null | Out-Null
    Write-Host "[easyauth] admin-consent OK (acceso sin prompt de permisos)" -ForegroundColor Green
} catch {
    Write-Host "[easyauth] admin-consent no aplicado (lo hara el 1er usuario o un admin)" -ForegroundColor DarkYellow
}

# --- Resumen ----------------------------------------------------------------
Write-Host "`n=== Easy Auth LISTA ===" -ForegroundColor Green
Write-Host "Portal:   https://$FQDN" -ForegroundColor Cyan
Write-Host "Acceso:   solo miembros del grupo '$GROUP_NAME' (groupId=$GROUP_ID)" -ForegroundColor Cyan
Write-Host "appId=$APP_ID   sp=$SP_OID" -ForegroundColor DarkGray
Write-Host "`nPrueba en ventana de incognito: deberia pedir login Entra." -ForegroundColor Yellow
Write-Host "Dar acceso a alguien:  az ad group member add --group $GROUP_ID --member-id <objectIdUsuario>" -ForegroundColor Yellow
