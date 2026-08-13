# add_secrets_partes.ps1
# Carga en el Key Vault de PARTES los secretos de la app, pedidos de forma
# SEGURA (no se guardan en disco ni se imprimen). Correlo DESPUES de
# fase1_infra_partes.ps1 (PG-PASSWORD ya la dejo ese script).
#
# Uso:
#     . .\00_vars_partes.ps1
#     .\add_secrets_partes.ps1

$ErrorActionPreference = "Stop"
if (-not $KV) { throw "Falta `$KV. Haz primero:  . .\00_vars_partes.ps1" }

# Nombre de secreto en KV  ->  descripcion de lo que tienes que pegar.
$secretos = [ordered]@{
    "GRAPH-KEY"               = "JSON de Graph {tenant_id,client_id,client_secret} (correo + SharePoint)"
    "SIGRID-API-FUNCTION-KEY" = "function key de sigrid-api"
    "GEMINI-API-KEY"          = "clave de Gemini (sv2, primario)"
    "ANTHROPIC-API-KEY"       = "clave de Anthropic (sv2, alterno) - opcional"
    "OPENAI-API-KEY"          = "clave de OpenAI (sv2, alterno) - opcional"
}

foreach ($nombre in $secretos.Keys) {
    Write-Host "`n$nombre  ->  $($secretos[$nombre])" -ForegroundColor Cyan
    $sec = Read-Host "  Pega el valor (vacio para SALTAR)" -AsSecureString
    $val = [System.Net.NetworkCredential]::new("", $sec).Password
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "  (saltado)" -ForegroundColor DarkGray
        continue
    }
    az keyvault secret set --vault-name $KV --name $nombre --value $val --only-show-errors | Out-Null
    Write-Host "  OK guardado en $KV" -ForegroundColor Green
}

Write-Host "`nSecretos en el Key Vault de partes:" -ForegroundColor Yellow
az keyvault secret list --vault-name $KV --query "[].name" -o tsv
