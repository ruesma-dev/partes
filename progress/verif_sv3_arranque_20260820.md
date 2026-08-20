# Verificación de arranque de sv3 tras el despliegue del 2026-08-20

- **Fecha de la verificación**: 2026-08-20, ~10:29–10:35 (hora local; 08:29–08:35 UTC).
- **Alcance**: solo `ca-sv3-persistencia` en `rg-partes-dev`. No se tocó sv4 ni sv5,
  no se construyó ninguna imagen, no se desplegó nada.
- **Motivo**: el despliegue de anoche (`redeploy_partes.ps1 -Solo sv3,sv4`, revisión
  `r20260820000737`, con F-015 + F-016 + DDL pendiente de F-010) dejó sv3 en
  `ScaledToZero`, así que había que forzar un arranque para ver la inicialización
  del esquema.
- **Escrituras realizadas contra producción** (las autorizadas, ninguna más):
  `az containerapp update --min-replicas 1` y, al terminar,
  `az containerapp update --min-replicas 0`.

## 1. Estado previo (antes de tocar nada)

`az containerapp show -n ca-sv3-persistencia -g $RG`:

| Campo | Valor |
|---|---|
| provisioningState | `Succeeded` |
| runningStatus | `Running` |
| latestRevisionName | `ca-sv3-persistencia--r20260820000737` |
| latestReadyRevisionName | `ca-sv3-persistencia--r20260820000737` |
| imagen | `acralbaranesdev.azurecr.io/sv3-partes:latest` |
| minReplicas / maxReplicas | `0` / `5` |

`az containerapp revision list`: una sola revisión activa,
`ca-sv3-persistencia--r20260820000737`, creada el 2026-08-19T22:09:00Z,
`replicas=0`, estado `ScaledToZero`.

Digest de la imagen en el ACR (`az acr manifest show-metadata
acralbaranesdev.azurecr.io/sv3-partes:latest`):

```
digest         sha256:b3b533c557e205d1a8457e9e6d1c77247ff1960f85dc93d47135df8497f4e523
lastUpdateTime 2026-08-19T22:08:39Z
```

El tag `:latest` se actualizó por última vez a las 22:08:39Z, 21 segundos antes de
crearse la revisión desplegada (22:09:00Z). Es decir: **desde el despliegue de anoche
no se ha publicado ninguna imagen nueva**, así que cualquier revisión que se cree hoy
arranca exactamente el mismo binario.

## 2. Revisión creada al forzar el arranque

`az containerapp update -n ca-sv3-persistencia -g $RG --min-replicas 1` →
revisión nueva **`ca-sv3-persistencia--0000009`** (creada 2026-08-20T08:29:45Z),
`minReplicas=1`, `maxReplicas=5`, `provisioningState=Succeeded`.

**Imagen idéntica**: `acralbaranesdev.azurecr.io/sv3-partes:latest`, mismo tag y mismo
digest (`sha256:b3b533c5…`, sin cambios desde 22:08:39Z de anoche). Los logs de sistema
lo confirman:

```
Pulling image 'acralbaranesdev.azurecr.io/sv3-partes:latest'
Successfully pulled image "acralbaranesdev.azurecr.io/sv3-partes:latest" in 2.48s. Image size: 78643200 bytes.
Created container 'ca-sv3-persistencia'
Started container 'ca-sv3-persistencia'
```

Réplica `ca-sv3-persistencia--0000009-7c8b8bb689-rwh9q`, estado `Running`,
`healthState=Healthy`, sin reinicios.

No hubo `RequestDisallowedByAzure`: la sesión de Azure ya admitía escrituras y el
`update` pasó a la primera, sin necesidad del `az login --claims-challenge`.

## 3. Log de arranque (literal, vía Log Analytics)

Consulta sobre `ContainerAppConsoleLogs_CL` en el workspace
`047d0955-9964-41c6-b74a-c3052b093aca`, filtrando por `RevisionName_s`. Líneas
relevantes del arranque de `--0000009` (se omiten las trazas HTTP del SDK de Azure y
el polling de cola, que son ruido):

```
2026-08-20 10:30:03,790 | INFO | __main__ | main_worker.py:35 | [sv3-worker] arrancando. cola=q-persistencia
2026-08-20 10:30:03,902 | INFO | interface_adapters.api.app | app.py:103 | [jornada][wiring] mapa candef -> jornada semanal: 8:40, 9:42
2026-08-20 10:30:04,660 | INFO | infrastructure.database.sqlalchemy_parte_repository | sqlalchemy_parte_repository.py:69 | [parte-repo] esquema inicializado (137 sentencias complementarias).
2026-08-20 10:30:04,660 | INFO | infrastructure.calendario.json_calendario_laboral | json_calendario_laboral.py:91 | [calendario] nacionales=True, 1 festivos extra, 0 localizaciones, 0 convenios (sabado=True domingo=True).
2026-08-20 10:30:04,661 | INFO | interface_adapters.api.app | app.py:67 | [sesame][wiring] DESACTIVADO (faltan SESAME_API_*); los festivos salen del JSON local config/calendario_laboral.json.
2026-08-20 10:30:04,661 | INFO | interface_adapters.api.app | app.py:169 | [svc3][wiring] Sigrid CABLEADO base_url=https://func-sigridapi-dev-huyke.azurewebsites.net db=ruesma empresa=0
2026-08-20 10:30:04,660 | INFO | infrastructure.sigrid.sigrid_api_client | sigrid_api_client.py:169 | [sigrid-client] Instanciado. base_url=... database=ruesma empresa=0 timeout_s=30.0 max_rows=10000 key_len=56
2026-08-20 10:30:04,694 | INFO | interface_adapters.api.app | app.py:201 | [svc3][wiring] SharePoint CABLEADO mode=drive_id root=partes
2026-08-20 10:30:04,719 | INFO | infrastructure.azure.cola_cliente | cola_cliente.py:91 | [cola] consumiendo 'q-persistencia' (vt=300s, max_dequeue=5)
```

A partir de ahí, solo polling de `q-persistencia` cada ~5 s (respuestas HTTP 200), que
es el comportamiento normal del worker en reposo.

### Búsqueda explícita de errores

Consulta con `Log_s has_any ('Traceback','ERROR','WARNING','Exception','error',
'jornada','esquema','arrancando')` sobre las dos revisiones (`--0000009` y
`r20260820000737`): devuelve **6 filas, todas INFO**, las tres de arranque de cada
revisión. **Cero `Traceback`, cero `ERROR`, cero `WARNING`.**

En particular, **ningún WARNING de jornada**: no aparece el aviso de F-015 por
`candef` fuera del mapa ni el de fallo al leer `empleado_jornada`. El wiring de jornada
cargó el mapa `candef -> jornada semanal: 8:40, 9:42` sin incidencias.

## 4. Hallazgo: la revisión desplegada anoche YA había arrancado

Contando filas por revisión en Log Analytics:

```
ca-sv3-persistencia--0000009          268 filas   última 2026-08-20T08:31:01Z
ca-sv3-persistencia--r20260820000737 1170 filas   última 2026-08-19T22:14:04Z
ca-sv3-persistencia--r20260723094803 3549 filas   última 2026-07-23T08:02:33Z
ca-sv3-persistencia--r20260726133153 1168 filas   última 2026-07-26T11:39:10Z
```

La revisión del despliegue **sí llegó a levantar réplica** entre las 22:09 y las 22:14
UTC de anoche (probablemente el arranque que hace el propio `containerapp update` antes
de que KEDA la escale a cero por cola vacía), y su log de arranque existe y es idéntico:

```
2026-08-20 00:09:16,888 | INFO | __main__ | main_worker.py:35 | [sv3-worker] arrancando. cola=q-persistencia
2026-08-20 00:09:17,005 | INFO | interface_adapters.api.app | app.py:103 | [jornada][wiring] mapa candef -> jornada semanal: 8:40, 9:42
2026-08-20 00:09:17,607 | INFO | infrastructure.database.sqlalchemy_parte_repository | sqlalchemy_parte_repository.py:69 | [parte-repo] esquema inicializado (137 sentencias complementarias).
```

Es decir, el arranque forzado ha servido de confirmación, pero la evidencia ya estaba
en Log Analytics. **Para la próxima: antes de forzar réplicas, mirar primero si la
revisión tiene filas en `ContainerAppConsoleLogs_CL`.** Se ahorra crear revisiones.

Las **137 sentencias complementarias** coinciden exactamente con las que reportó sv4,
que era lo esperable: ambos servicios comparten
`infrastructure/database/orm_models.py` y aplican el mismo DDL complementario sobre la
base `partes`.

## 5. Estado final (confirmado)

`az containerapp update -n ca-sv3-persistencia -g $RG --min-replicas 0` ejecutado al
terminar. Resultado:

| Campo | Valor |
|---|---|
| minReplicas / maxReplicas | **`0`** / `5` |
| provisioningState | `Succeeded` |
| latestRevisionName | `ca-sv3-persistencia--0000010` |
| imagen | `acralbaranesdev.azurecr.io/sv3-partes:latest` (mismo digest) |

Tras el `update` quedó **una sola revisión activa**, `ca-sv3-persistencia--0000010`
(la `--0000009` se retiró automáticamente, modo single-revision).

Reglas de escalado vigentes, sin cambios respecto a lo normal:

```
minReplicas 0   maxReplicas 5   cooldownPeriod 300   pollingInterval 30
regla q-persistencia-scaler: azureQueue stpartespt7m3 / q-persistencia, queueLength 5
```

**Drenado confirmado.** Se esperó al cooldown de KEDA y se comprobó el estado real:

```
ca-sv3-persistencia--0000010   active=True   replicas=0   ScaledToZero
```

sv3 queda exactamente como estaba antes de la verificación: a cero réplicas, escalando
solo por mensajes en `q-persistencia`.

## 6. Veredicto

**APROBADO. sv3 arranca limpio en la imagen desplegada.**

- Contenedor creado e iniciado sin reinicios; réplica `Running` / `Healthy`.
- Esquema inicializado correctamente: **137 sentencias complementarias**, sin error.
  Esto cubre la tabla nueva `empleado_jornada` de F-015 y el DDL pendiente de F-010.
- Wiring completo y correcto: jornada (mapa candef 8:40 / 9:42), calendario laboral
  JSON, Sigrid, SharePoint y consumo de `q-persistencia`.
- **Ningún `Traceback`, ningún `ERROR`, ningún `WARNING`** — en particular ninguno de
  los WARNING de jornada que F-015 emite ante un `candef` desconocido o un fallo de
  lectura de `empleado_jornada`.
- Estado final confirmado: `minReplicas=0` y **0 réplicas efectivas**
  (`ca-sv3-persistencia--0000010`, `ScaledToZero`).

## 7. Notas operativas para recordar

1. **Mirar Log Analytics antes de forzar réplicas.** Una revisión `ScaledToZero` puede
   tener perfectamente su log de arranque guardado: `az containerapp update` levanta
   réplica al desplegar y KEDA la baja después. Consultar
   `ContainerAppConsoleLogs_CL | summarize count() by RevisionName_s` cuesta nada.
2. **Cambiar `--min-replicas` crea revisión nueva.** Ida y vuelta 1 → 0 dejó dos
   revisiones (`--0000009` y `--0000010`) con la misma imagen. No es un problema
   funcional (el tag `:latest` no se movió), pero el nombre de revisión ya no es el
   `r2026…` del despliegue: para rastrear qué código corre hay que mirar el digest del
   ACR, no el nombre de la revisión.
3. **`az containerapp logs show --tail` no vale aquí.** El polling de `q-persistencia`
   cada 5 s llena el buffer en minutos y el arranque desaparece. Log Analytics es la
   única vía fiable, con unos 1–2 minutos de latencia de ingesta.
4. **Fallo transitorio de `az`.** Un `az account show` devolvió
   `Please run 'az login' to setup account` y al reintentar funcionó sin cambiar nada;
   parece contención sobre la caché de tokens MSAL cuando corren dos comandos `az` casi
   a la vez. No confundirlo con una sesión caducada: reintentar antes de pedir login.
5. El log de sistema muestra varios `ScaledObjectCheckFailed / Target resource doesn't
   exist` justo al crear la revisión, seguidos de `KEDAScalersStarted` y
   `Scaler azure-queue is built`. Es la carrera normal entre KEDA y la revisión recién
   creada, se resuelve sola en ~1 s. No es un síntoma.
