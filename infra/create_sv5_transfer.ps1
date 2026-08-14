# create_sv5_transfer.ps1
# Crea el Container App del REGISTRO EN SIGRID (sv5-partes / partes-transfer),
# con ingress INTERNO. Fase 5.1.
#
# A diferencia del portal (sv4):
#   - Ingress INTERNO: solo alcanzable desde dentro del CAE. Nadie desde
#     Internet puede disparar escrituras en el ERP; el unico cliente es sv4.
#   - --allow-insecure: sv4 lo llama por http:// (httpx no sigue el 307 que
#     el ingress devolveria hacia https).
#   - min=1 (evita cold start en el preflight de aprobar) / max=1: la
#     escritura en Sigrid usa MAX(ide)+1 con UPDLOCK, mejor una sola replica.
#   - NO usa PostgreSQL: sv4 le pasa las lineas en el payload.
#
# Es el UNICO servicio con credencial de ESCRITURA en Sigrid (base 'ruesma').
# Arranca en modo NORMAL (produccion): cada parte se registra en SU obra.
#
# Requisitos previos:
#   - Imagen sv5 en el ACR:  .\build_images_partes.ps1 -Solo sv5
#   - Secreto en Key Vault: SIGRID-API-FUNCTION-KEY (ya lo puso add_secrets_partes.ps1)
#
# Uso:
#     . .\00_vars_partes.ps1
#     . .\00_capps_vars_partes.ps1
#     .\create_sv5_transfer.ps1
#
# Si alguna vez necesitas volver a MODO PRUEBAS (desviar TODO a la obra 0404
# con marca PRUEBA-IA para poder limpiarlo despues):
#     az containerapp update -n ca-sv5-transfer -g $RG `
#         --set-env-vars OBRA_PRUEBAS_FORZAR=true
# ...o crear la app directamente con:  .\create_sv5_transfer.ps1 -ObraPruebasForzar true

param(
    # false (por defecto) = comportamiento NORMAL: cada parte a SU obra.
    # true = desvia TODAS las escrituras a la obra de pruebas (0404), ignorando
    # la obra del parte, y marca las lineas para poder limpiarlas.
    [ValidateSet("true", "false")]
    [string] $ObraPruebasForzar = "false",

    # Salta el cableado automatico de sv4 (TRANSFER_BASE_URL).
    [switch] $SinCablearSv4
)

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"   # az containerapp escribe a stderr
if (-not $MI_ID) { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars_partes.ps1" }
if (-not $IMG)   { throw "Falta `$IMG. Haz:  . .\00_vars_partes.ps1" }
if (-not $IMG["sv5"]) { throw "No hay entrada 'sv5' en `$IMG (00_vars_partes.ps1)." }
az account set --subscription $SUBSCRIPTION

$APP    = "ca-sv5-transfer"
$SV4APP = "ca-sv4-front"

# Secreto de container app -> referencia a Key Vault con la managed identity.
function KvRef($kvSecretName) { "keyvaultref:$KV_URI/secrets/$kvSecretName,identityref:$MI_ID" }

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

Write-Host "`n=== sv5 (registro en Sigrid, ingress interno) ===" -ForegroundColor Green
if ($ObraPruebasForzar -eq "true") {
    Write-Host "  MODO PRUEBAS: todo se desviara a la obra 0404 (marca PRUEBA-IA)" -ForegroundColor Yellow
} else {
    Write-Host "  Modo NORMAL: cada parte se registrara en SU obra (produccion)" -ForegroundColor Green
}

# `containerapp show` de una app inexistente escribe en stderr y, con
# ErrorActionPreference=Stop, PS 5.1 lo convierte en error terminante aunque
# haya 2>$null: el alta moria justo en el caso "no existe". `list --query`
# devuelve vacio sin tocar stderr.
$existe = az containerapp list -g $RG --query "[?name=='$APP'].name" -o tsv
if ($existe) {
    throw "El Container App '$APP' ya existe. Para republicar: .\redeploy_partes.ps1 -Solo sv5"
}

$sv5Secrets = @(
    "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')"
)

$sv5Env = @(
    # --- API / uvicorn: ESCUCHAR EN 0.0.0.0 dentro del contenedor ---
    "API_HOST=0.0.0.0", "API_PORT=8005",
    "LOG_DIR=/tmp/logs", "LOG_LEVEL=INFO",
    # --- Sigrid con ESCRITURA: solo la base real 'ruesma' (nunca la replica) ---
    "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
    "SIGRID_EMPRESA=1",
    "SIGRID_API_TIMEOUT_S=60",
    # Tope de sentencias por lote (sigrid-api permite 20; dejamos margen).
    "SIGRID_MAX_STATEMENTS=15",
    # --- Modo pruebas (por defecto false = cada parte a SU obra) ---
    # Si se pone a true, TODO se desvia a OBRA_PRUEBAS_COD y las lineas se
    # marcan en hmores.tex con MARCA_PRUEBAS (limpiables con el script).
    "OBRA_PRUEBAS_FORZAR=$ObraPruebasForzar",
    "OBRA_PRUEBAS_COD=0404",
    "MARCA_PRUEBAS=PRUEBA-IA"
)

$a = @("containerapp","create","-n",$APP,"-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv5'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,
       "--min-replicas","1","--max-replicas","1",
       "--cpu","0.25","--memory","0.5Gi",
       "--ingress","internal","--target-port","8005","--transport","auto",
       "--secrets") + $sv5Secrets + @("--env-vars") + $sv5Env + @("--tags") + $TAGS
Run-Az $a

# --- HTTP plano en el ingress interno (sv4 llama por http://) ----------------
Run-Az @("containerapp","ingress","update","-n",$APP,"-g",$RG,"--allow-insecure","true")

$FQDN = az containerapp show -n $APP -g $RG `
          --query "properties.configuration.ingress.fqdn" -o tsv
if (-not $FQDN) { throw "No pude leer el FQDN interno de $APP." }
$TRANSFER_URL = "http://$FQDN"

Write-Host "`n=== sv5 creado (ingress interno) ===" -ForegroundColor Green
az containerapp show -n $APP -g $RG `
  --query "{Estado:properties.provisioningState, Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, FQDN:properties.configuration.ingress.fqdn}" `
  -o table
Write-Host "`nURL interna (la consume sv4):  $TRANSFER_URL" -ForegroundColor Cyan

# --- Cablear sv4 -> sv5 (revision nueva del portal) -------------------------
if ($SinCablearSv4) {
    Write-Host "`n(-SinCablearSv4) Fija a mano en sv4:" -ForegroundColor Yellow
    Write-Host "  az containerapp update -n $SV4APP -g $RG --set-env-vars TRANSFER_BASE_URL=$TRANSFER_URL" -ForegroundColor Yellow
} else {
    Write-Host "`n=== Cableando sv4 ($SV4APP): TRANSFER_BASE_URL ===" -ForegroundColor Green
    $sv4Existe = az containerapp list -g $RG --query "[?name=='$SV4APP'].name" -o tsv
    if (-not $sv4Existe) {
        Write-Warning "No existe ${SV4APP}: crealo con create_sv4_front.ps1 y luego fija TRANSFER_BASE_URL=$TRANSFER_URL"
    } else {
        $suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")
        Run-Az @("containerapp","update","-n",$SV4APP,"-g",$RG,
                 "--set-env-vars","TRANSFER_BASE_URL=$TRANSFER_URL","TRANSFER_TIMEOUT_S=120",
                 "--revision-suffix",$suf)
        Write-Host "  sv4 actualizado (revision $suf)" -ForegroundColor Green
    }
}

Write-Host "`nLogs de sv5:  az containerapp logs show -n $APP -g $RG --tail 60 --follow" -ForegroundColor Yellow
Write-Host "En el arranque de sv4 debe aparecer:" -ForegroundColor Yellow
Write-Host "  [transfer][wiring] CABLEADO base_url=$TRANSFER_URL" -ForegroundColor Yellow
if ($ObraPruebasForzar -eq "true") {
    Write-Host "`nAVISO: sv5 esta en MODO PRUEBAS (obra 0404, marca PRUEBA-IA)." -ForegroundColor Yellow
    Write-Host "Limpia las pruebas con prueba_escritura_sigrid.py (fase limpiar)." -ForegroundColor Yellow
} else {
    Write-Host "`nAVISO: sv5 escribe EN PRODUCCION en Sigrid (base 'ruesma'):" -ForegroundColor Red
    Write-Host "  cada parte aprobado en el portal va a SU obra real." -ForegroundColor Red
    Write-Host "Antes de aprobar en serio, borra las lineas de PRUEBA de la obra 0404" -ForegroundColor Yellow
    Write-Host "con prueba_escritura_sigrid.py (fase limpiar, un mes por pasada)." -ForegroundColor Yellow
}
