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

## Secretos (Key Vault `$KV`, es decir `kv-partes-<suffix>`)
`PG-PASSWORD` la deja `fase1`. El resto los pides con `add_secrets_partes.ps1`:
`GRAPH-KEY` (JSON `{tenant_id,client_id,client_secret}`), `SIGRID-API-FUNCTION-KEY`,
`GEMINI-API-KEY`, `SESAME-TOKEN` (token de Sesame HR, solo sv3), y opcionalmente `ANTHROPIC-API-KEY` /
`OPENAI-API-KEY`.

### Ningún script lee secretos de ficheros en disco

Regla de esta carpeta, y conviene no romperla:

- **El Key Vault es la única fuente de los secretos de la app.** No hay
  fichero de secretos que haya que tener al lado para desplegar.
- `add_secrets_partes.ps1` los pide **por consola** con
  `Read-Host -AsSecureString` y los sube con `az keyvault secret set`. No los
  escribe en disco ni los imprime: el **fichero versionado solo contiene los
  nombres** de los secretos; el valor existe únicamente en memoria durante la
  ejecución del script.
- Los servicios los reciben por **referencia**: `create_capps_partes.ps1`,
  `create_sv1_poller.ps1` y `create_sv4_front.ps1` montan
  `GRAPH_KEY=secretref:graph-key`, y el secreto de la Container App es un
  `keyvaultref` al Key Vault resuelto con la **identidad gestionada**
  `id-partes-dev`. En ningún punto del despliegue viaja el valor en claro.
- **`GRAPH-KEY`** (correo de sv1 + SharePoint de sv3 + sv4) vive ahí y solo
  ahí. Para consultarlo o rotarlo se va al Key Vault, no a un fichero.

Hasta el 2026-08-25 existió un `infra/graphkey_nobom.json` (no versionado, con
los valores en claro) que se usó para la carga manual inicial. **Ya no forma
parte del despliegue y se ha borrado** (F-005): ningún script lo leía. Sigue
en `.gitignore` por si alguien lo regenera; si te lo encuentras, sobra.

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

## Sesame — festivos de cada trabajador (F-032, F-077)
sv3 pide a la **API oficial de Sesame HR** (token Bearer, solo `GET`; sin la
pasarela `sesame-api` desde F-077) los festivos de cada trabajador al ingerir y
los guarda en la tabla `festivos_trabajador`; sv4 no llama a Sesame: lee esa
tabla con `FESTIVOS_SESAME_ENABLED=true`. Sin `SESAME_BASE_URL`/`SESAME_TOKEN`
(sv3) ni `FESTIVOS_SESAME_ENABLED` (sv4), los dos usan su calendario local.

**URL**: la API pública de la región de nuestra cuenta de Sesame HR, de la forma
`https://api-<región>.sesametime.com` (la región la da el panel de Sesame). Va
SOLO en tu `00_vars_partes.local.ps1` (`$SESAME_BASE_URL`); la versionada queda
vacía (DA13). **Token**: rótalo antes de encender (el `.env` de sesame-api estuvo
en git) y, si Sesame lo permite, que sea de solo lectura; se carga como
`SESAME-TOKEN` con `add_secrets_partes.ps1`.

Antes de encender, el **contraste** (guía de despliegue de F-077, M1 y M2). El
token sale de `SESAME_TOKEN` (el `.env` de sv3) o se pide por consola sin eco;
no hay opción de línea de comandos para él:

```powershell
cd ..\services\partes-persistencia
python contrastar_festivos_sesame.py --ano 2026 --base-url https://api-<región>.sesametime.com
python contrastar_festivos_sesame.py --ano 2026 --impacto   # con el .env de sv3
```

`FALTAN DEL RESPALDO` ⇒ no se enciende. `INCOMPLETO` ⇒ consultar con RRHH.

**Encendido en un solo paso** (sv3 y después sv4), fuera del horario de aprobación:

```powershell
. .\00_vars_partes.ps1          # $SESAME_BASE_URL en tu 00_vars_partes.local.ps1
. .\00_capps_vars_partes.ps1
.\add_sesame_partes.ps1          # encender
.\add_sesame_partes.ps1 -Quitar  # apagar (retira las variables de Sesame de las dos apps)
```

- Antes de tocar ninguna app comprueba que `$SESAME_BASE_URL` empieza por
  `https://` y que `SESAME-TOKEN` existe en `$KV`. Si falla algo, aborta sin tocar nada.
- Retira primero de cada app las variables de la pasarela que tenga
  (`SESAME_API_BASE_URL`, `SESAME_API_KEY`, `SESAME_API_TIMEOUT_S`,
  `SESAME_CACHE_TTL_S`) y su secreto `sesame-key`.
- En sv3 crea el secreto `sesame-token` como `keyvaultref` por la identidad
  gestionada y fija `SESAME_BASE_URL`, `SESAME_TOKEN=secretref:sesame-token`,
  `SESAME_TIMEOUT_S` y `SESAME_FESTIVOS_MINIMOS` (`$SESAME_FESTIVOS_MINIMOS`, por
  defecto 1). En sv4, solo `FESTIVOS_SESAME_ENABLED=true` (sin secreto). Después
  de cada cambio espera a que la revisión nueva esté lista.
- `-Quitar` retira solo las variables que cada app tenga (el secreto queda inerte).
- Idempotente. No encola nada ni lee el valor de ningún secreto.
- Comprobación: en los logs de arranque, `[sesame][wiring] CABLEADO` (o
  `DESACTIVADO` tras `-Quitar`). Con el siguiente parte, en sv3
  `[sesame-hr] indice …` y `[festivos] refresco guardadas=…`, sin ningún DNI. Un trabajador sin fila sale con un aviso en
  el portal, sin bloqueo.

## Obras agrupadas — postventa y VAR (F-072)

Las obras de postventa y de obras varias se tratan como **entradas**: la obra
agrupada más una partida suya (`docs/ARCHITECTURE.md`, semántica 24). No son
secretos: van como variables normales de cada app. **Todo vacío = apagado**, el
comportamiento de antes de F-072.

| Variable | sv2 | sv3 | sv4 | sv5 | Producción (de porcentajes) |
|---|---|---|---|---|---|
| `POSTVENTA_OBRA_COD` | sí | sí | sí | sí | `POSTV2` |
| `VAR_OBRA_COD` | sí | sí | sí | sí | `VAR` |
| `VAR_PARTIDA_DESDE` | sí | sí | sí | sí | `29` (obligatoria con VAR) |
| `POSTVENTA_ALIAS` | sí | sí | — | — | `POSTVENTA,POSTV,POST` |
| `VAR_ALIAS` | sí | sí | — | — | `V` |

- Con `VAR_OBRA_COD` y sin un `VAR_PARTIDA_DESDE` entero, la app **no arranca**
  (el error nombra la variable).
- **Orden de encendido: sv5 → sv3 → sv2 → sv4.** Primero la guarda de sv5 y
  el último el portal, que es el que manda `partida_metodo`. Para apagar, se
  quitan en orden inverso.
- Para poner las variables:
  `az containerapp update -g $RG -n <app> --set-env-vars POSTVENTA_OBRA_COD=POSTV2 ...`.
  Para quitarlas: `--remove-env-vars`.
- Comprobaciones antes y después: M0–M2 de `specs/F-072-postventa-var-como-obras/tasks.md`
  (T29–T31). Hay que avisar a porcentajes: escribe en las mismas obras y partidas.

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
