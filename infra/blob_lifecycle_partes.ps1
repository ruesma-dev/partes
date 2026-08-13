# blob_lifecycle_partes.ps1
# Lifecycle policy que purga los blobs efimeros del hand-off (input/ y
# envelopes/) a los 14 dias en el storage de PARTES. Los datos durables viven
# en SharePoint (PDF) y PostgreSQL (datos); esto solo limpia plumbing.
#
# Uso:
#     . .\00_vars_partes.ps1     # da $RG y $STORAGE
#     .\blob_lifecycle_partes.ps1
#
# Los workers NO borran en linea (idempotencia at-least-once); el borrado lo
# hace esta policy pasada la ventana.

$ErrorActionPreference = "Stop"
if (-not $STORAGE) { throw "Falta `$STORAGE. Haz primero:  . .\00_vars_partes.ps1" }

$DIAS = 14   # ventana de retencion (7-30 recomendado)

$policy = @"
{
  "rules": [
    {
      "enabled": true,
      "name": "purge-efimeros-handoff",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": [ "blockBlob" ],
          "prefixMatch": [ "input/", "envelopes/" ]
        },
        "actions": {
          "baseBlob": {
            "delete": { "daysAfterModificationGreaterThan": $DIAS }
          }
        }
      }
    }
  ]
}
"@

# En PowerShell Windows el JSON inline rompe az; se escribe a fichero ASCII
# (sin BOM) y se referencia con @ruta.
$tmp = Join-Path $env:TEMP "blob_lifecycle_partes.json"
[System.IO.File]::WriteAllText($tmp, $policy, (New-Object System.Text.ASCIIEncoding))

az storage account management-policy create `
    --account-name $STORAGE -g $RG `
    --policy "@$tmp" --only-show-errors | Out-Null

Remove-Item $tmp -Force
Write-Host "OK lifecycle policy en ${STORAGE}: borra input/ y envelopes/ a los $DIAS dias." -ForegroundColor Green
az storage account management-policy show --account-name $STORAGE -g $RG `
    --query "policy.rules[].name" -o tsv
