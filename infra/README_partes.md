# Infra de PARTES — Tanda 1 (Fase 1: provisión)

Clon del patrón de albaranes (Container Apps de **Consumo público**, **managed
identity** para Storage/KV/ACR, **Key Vault** para secretos, **KEDA azure-queue**
en los workers, hand-off por **Blob**, **lifecycle** de limpieza). Diferencias:

- Recursos **propios** de partes en `rg-partes-dev`.
- **Reutiliza** el ACR (`acralbaranesdev`) y el **servidor PostgreSQL**
  (`psql-albaranes-rs9k2`) de albaranes. La BBDD es **nueva**: `partes`.
- Partes es **autocontenido**: los Dockerfiles **no** copian la librería
  `comun`. Sin pgvector.

## Qué crea la Fase 1
`rg-partes-dev`, managed identity `id-partes-dev`, Log Analytics `log-partes-dev`,
storage `stpartes<suffix>` (colas `q-emails`/`q-extraccion`/`q-persistencia` +
sus `-poison`, contenedores `input`/`envelopes`), Key Vault `kv-partes-<suffix>`,
environment `cae-partes-dev`. Concede **AcrPull** a la MI sobre el ACR
compartido y crea la BBDD `partes` en el servidor PostgreSQL compartido.

## Login con MFA obligatorio (desde 2026-08)

Azure exige la reclamación de MFA en el token para crear/modificar/borrar
recursos (`RequestDisallowedByAzure ... MFA`). El `az login` normal reutiliza
la sesión cacheada por SSO **sin** esa reclamación, así que las lecturas
funcionan pero las escrituras fallan. La receta que funciona (también usada
en datamart):

```powershell
az logout
az login --tenant "<tenant-id>" --scope "https://management.core.windows.net//.default" --claims-challenge "eyJhY2Nlc3NfdG9rZW4iOnsiYWNycyI6eyJlc3NlbnRpYWwiOnRydWUsInZhbHVlcyI6WyJwMSJdfX19"
# el claims-challenge decodificado es {"access_token":{"acrs":{"essential":true,"values":["p1"]}}}
# si el navegador no se abre, añade --use-device-code
```

El tenant id real está en `00_vars_partes.local.ps1` (`$TENANT`). Regla
práctica: **cada consola nueva** necesita los dos dot-source
(`. .\00_vars_partes.local.ps1` y `. .\00_capps_vars_partes.ps1`) antes de
usar `$RG`, `$MI_CLIENTID`, etc.

## Orden de ejecución (PowerShell, con `az login` hecho)
```powershell
. .\00_vars_partes.ps1          # revisa $SUFFIX (storage/KV son únicos en Azure)
.\fase1_infra_partes.ps1         # te pedirá la contraseña del admin de PG
.\add_secrets_partes.ps1         # pega GRAPH-KEY / SIGRID / GEMINI / (ANTHROPIC/OPENAI)
.\blob_lifecycle_partes.ps1      # purga input/ y envelopes/ a 14 días
```

> Si `fase1_infra_partes.ps1` falla por nombre global pillado (storage o KV),
> cambia `$SUFFIX` en `00_vars_partes.ps1` y re-ejecuta (es idempotente).

## Secretos (Key Vault `kv-partes-<suffix>`)
`PG-PASSWORD` la deja `fase1`. El resto los pides con `add_secrets_partes.ps1`:
`GRAPH-KEY` (JSON `{tenant_id,client_id,client_secret}`), `SIGRID-API-FUNCTION-KEY`,
`GEMINI-API-KEY`, y opcionalmente `ANTHROPIC-API-KEY` / `OPENAI-API-KEY`.

## sv5 — registro de partes en Sigrid (`partes-transfer`)
Servicio de ESCRITURA en el ERP. Alta e integración:

```powershell
. .\00_vars_partes.ps1
. .\00_capps_vars_partes.ps1
.\build_images_partes.ps1 -Solo sv5
.\create_sv5_transfer.ps1                 # crea ca-sv5-transfer y cablea sv4
```

- **Ingress interno**: solo accesible desde el CAE; su único cliente es sv4.
  Nadie desde Internet puede disparar escrituras en Sigrid.
- **min=max=1 réplica**: la asignación de `ide` en Sigrid es `MAX(ide)+1` con
  `UPDLOCK`; una sola réplica evita carreras.
- **`SIGRID_API_DATABASE=ruesma`**: la escritura NO admite la réplica
  `ruesma_rep`.
- Nace en **modo normal** (`OBRA_PRUEBAS_FORZAR=false`): cada parte aprobado
  se registra en **su** obra. El modo pruebas sigue disponible por si hace
  falta (desvía todo a la obra `0404` y marca las líneas `PRUEBA-IA` en
  `hmores.tex` para poder limpiarlas):
  `.\create_sv5_transfer.ps1 -ObraPruebasForzar true`, o en caliente
  `az containerapp update -n ca-sv5-transfer -g $RG --set-env-vars OBRA_PRUEBAS_FORZAR=true`
- sv4 lo localiza por `TRANSFER_BASE_URL` (lo fija `create_sv5_transfer.ps1`).
  En el arranque del portal debe verse `[transfer][wiring] CABLEADO`.

Republicar tras cambios de código: `.\redeploy_partes.ps1 -Solo sv5`
(orden seguro: `sv2 → sv3 → sv5 → sv4 → sv1`).

## Pendiente (próximas tandas)
- **Tanda 2**: fontanería de partes (cola/blob) + `main_worker.py` de sv2 y sv3,
  y `build_images_partes.ps1` + `create_capps_partes.ps1` (workers con KEDA).
- **Tanda 3**: sv1 como **webhook** (suscripción Graph + handshake) + Job de
  renovación (`create_sv1_webhook.ps1`).
- **Tanda 4**: sv4 (portal) con Easy Auth + prueba e2e (correo → portal).
- **Tanda 5**: cola `q-transfer` para que la aprobación en sv4 sea asíncrona
  (hoy sv4 llama a sv5 por HTTP síncrono, que es lo que permite confirmar los
  conflictos de pisado en la misma pantalla).

## Notas operativas (del piloto de albaranes)
- **PostgreSQL SSL**: Azure PG exige TLS; psycopg3 negocia SSL por defecto. Si
  algún servicio diera error de SSL, se ajusta `sslmode` en su `.env`/env-var.
- **GRAPH-KEY** es un JSON; la app lo parsea. Si no es el JSON correcto, fallará
  al tocar SharePoint/correo.
- Los workers irán a **min-replicas=0** y escalan con KEDA al encolar; requieren
  el rol *Storage Queue Data Contributor* (lo concede esta Fase 1) y
  `--scale-rule-identity` (lo pondrá `create_capps_partes.ps1`).
