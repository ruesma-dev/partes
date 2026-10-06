<!-- specs/F-032-sesame-festivos-produccion/design.md -->
# F-032 · Activar Sesame en producción — Diseño

## 1. Estado de partida (verificado el 2026-10-06, solo lectura)

- **Código**: F-003 lo dejó todo hecho y apagado. sv3 `interface_adapters/api/
  app.py::construir_calendario` devuelve `JsonCalendarioLaboral` si
  `settings.sesame_enabled` es falso (log «DESACTIVADO (faltan SESAME_API_*)»)
  y, si no, `SesameCalendarioLaboral` con el JSON de respaldo. sv4 monta
  `CalendarioProvider` en `interface_adapters/web/app.py` (respaldo `holidays`
  `MD`). Cascada, caché (DNI × año, 6 h), `review_required` en sv3 y bloqueo
  del registro con override `[SIN-SESAME]` en sv4: R5–R10 y R22–R27 de F-003.
- **Respaldos distintos hoy**: sv3 paga extras con nacionales + 28-feb (sábado
  en 2026) y sv4 avisa con nacionales + Madrid: ningún autonómico ni local en sv3.
- **`infra/`**: `create_capps_partes.ps1` y `create_sv4_front.ps1` ya cablean
  `SESAME_*` por `secretref:sesame-key` → `keyvaultref` `SESAME-API-KEY` si
  `$SESAME_BASE_URL` tiene valor, pero solo al **crear** la app;
  `redeploy_partes.ps1` solo cambia la imagen. Falta el «encender sobre apps
  existentes» (patrón `add_qtransfer_partes.ps1`). `SESAME-API-KEY` ya está en
  `add_secrets_partes.ps1`.
- **Recálculo**: cada mensaje de `q-persistencia` ejecuta
  `RecursoConciliador.conciliar_todos()` sobre **todos los partes activos**
  (revierte `extra_auto` y recalcula; congeladas excluidas, F-015 R31/R32).
- **sesame-api** (repo aparte, rama `dev` = `origin/dev`, `dcef288`): el
  rediseño hexagonal (`application/`, `config/`, `domain/`, `infrastructure/`,
  `interface_adapters/`) está **sin versionar** y el paquete viejo borrado sin
  commit; incluye el fix `daysOff`. **No hay Dockerfile.** `GET /health` sin
  clave; el resto con `x-api-key` contra el CSV `API_KEYS`; token
  `SESAME_TOKEN`. Los handlers son `async def` y llaman a un cliente `httpx`
  **síncrono**: cada llamada a Sesame HR bloquea el bucle de eventos.
- **Hallazgo de seguridad (sesame-api)**: `.env` está **versionado** pese al
  `.gitignore` (commits `d226936` y `dcef288`, publicados en `origin/dev` y
  `origin/pruebas` de GitHub) y hoy aparece modificado. No se ha leído su
  contenido. Ver P0 en §2.
- **Local**: 8006 lo ocupa hoy `porcentajes-transfer`; contraste 2026 ⇒ M2.
- **F-013 (2026-08-18)**: 218 empleados; Madrid (defecto) 196, Tomares 15,
  Sevilla 4, Málaga 2, Alicante 1 **parcial**; 0 contratos.

## 2. Límite de servicio y trabajo fuera del repositorio

| Dónde | Qué | Quién |
|---|---|---|
| sv3 | Mínimo de festivos en el cliente gemelo, setting espejo, cableado, herramienta de contraste | implementer |
| sv4 | Mismo cliente gemelo, setting espejo, cableado | implementer |
| `infra/` | `add_sesame_partes.ps1` (encender/apagar) y `SESAME_FESTIVOS_MINIMOS` en los `create_*` | implementer |
| `azure-apps/partes.md` | R27 | implementer |
| repo **sesame-api** | P0–P5 de abajo | **humano** (los agentes no lo tocan) |
| Azure | Imagen, Container App, secretos, encendido | **humano** con la guía §7 |

Sin responsabilidad nueva (sv3 y sv4 consumen sesame-api desde F-003); lo
nuevo vive en el **cliente gemelo** de la lista cerrada de `CLAUDE.md` (DA5).

**Precondiciones en sesame-api (humano, antes de M1):**
- **P0** `git rm --cached .env`; comprobar si los `.env` versionados llevan
  `SESAME_TOKEN` y, si es así, **rotar el token** en Sesame antes de cargarlo
  en el Key Vault (el historial publicado no se limpia con un commit).
- **P1** Commitear el rediseño y el fix `daysOff` (sin `.env`, `logs/`,
  `sesame-api.zip`, `.py` suelto).
- **P2** Dockerfile (`python:3.12-slim`, `requirements.txt`, `python main.py`,
  `API_HOST=0.0.0.0`, puerto 8006) y `.dockerignore` (`.env`, `.venv`,
  `logs`, `*.zip`).
- **P3** Recomendado: handlers `def` (o cliente asíncrono) para que una
  llamada lenta a Sesame no congele las demás; `contract_not_found` → 404 (DA8).
- **P4** `azure-apps/sesame-api.md` (DA9). **P5** RRHH completa Alicante y lo que destape M2.

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/contrastar_festivos_sesame.py` | Herramienta de §5.3 (consola, `print` permitido) |
| `services/partes-persistencia/tests/test_f032_cliente_minimo.py` | R1–R4 del cliente de sv3 (`httpx.MockTransport`) |
| `services/partes-persistencia/tests/test_f032_calendario_incompleto.py` | R5 (settings y cableado de sv3), R6 |
| `services/partes-persistencia/tests/test_f032_contraste.py` | R10–R18 con cliente simulado y repositorio falso |
| `services/partes-persistencia/tests/test_f032_r24_recalculo.py` | R24–R25 sobre el conciliador con calendario falso |
| `services/partes-front/tests/test_f032_cliente_minimo.py` | R1–R4 del cliente de sv4 |
| `services/partes-front/tests/test_f032_calendario_incompleto.py` | R5 (sv4), R7, R9 |
| `tests/test_f032_sesame_cliente_gemelos.py` | R8 |
| `tests/test_f032_infra_sesame.py` | R19–R23 por inspección estática de los `.ps1` |
| `infra/add_sesame_partes.ps1` | §5.4 |

## 4. Ficheros a modificar

- `services/partes-{persistencia,front}/infrastructure/sesame/sesame_api_client.py`:
  `CalendarioIncompletoError`, parámetro `festivos_minimos`, control en
  `festivos` y `calendario_por_defecto`. Cuerpo idéntico en los dos.
- `services/partes-persistencia/config/settings.py` y
  `services/partes-front/config/settings.py`: `sesame_festivos_minimos: int =
  Field(8, alias="SESAME_FESTIVOS_MINIMOS", ge=0)`.
- sv3 `interface_adapters/api/app.py::construir_calendario` y sv4
  `interface_adapters/web/app.py::build_app`: pasar el mínimo y loguearlo.
- `infra/create_capps_partes.ps1`, `infra/create_sv4_front.ps1`: R22.
- `infra/00_vars_partes.ps1`: comentario Sesame (paso 3 = `add_sesame_partes.ps1`) y `$SESAME_FESTIVOS_MINIMOS = 8`.
- `infra/README_partes.md` y `docs/ARCHITECTURE.md` (herramientas de consola).
  No hay `.env.example` versionado en sv3 ni sv4: no se crea.
- `azure-apps/partes.md` (5.3 bis, 5.4, tabla de variables, hoja de ruta) y
  `harness/features.json` según el flujo.

## 5. Clases y funciones

### 5.1 Cliente gemelo (infrastructure, sv3 y sv4)

```python
class CalendarioIncompletoError(RuntimeError): ...
SesameApiClient(*, base_url, api_key, timeout_s=10.0, transport=None,
                festivos_minimos: int = 0)
def festivos(self, dni, ano) -> list[FestivoDia] | None       # R2, R4
def calendario_por_defecto(self, ano) -> list[FestivoDia] | None  # R3, R4
def _exigir_minimo(self, festivos, ano, origen: str) -> list[FestivoDia]
```

`_exigir_minimo` cuenta los festivos ya filtrados al año; si `0 < minimo` y
`len < minimo`, lanza con «calendario incompleto: N festivos en AAAA (mínimo
M) en <origen>». Es un `RuntimeError`, así que **las dos cascadas existentes lo
tratan como fallo sin tocarlas**: sv3 `SesameCalendarioLaboral._festivos` →
`_degradar` (caché caducada o JSON, `consumir_degradacion()` → R26) y sv4
`CalendarioProvider._resolver` → `_degradar` (fuente `stale`/`respaldo`, no
fiable → R22–R24). Al lanzar `festivos(dni)` no se prueba el calendario por
defecto: un trabajador de Alicante con calendario roto no debe recibir los
festivos de Madrid (R6). `validar_datos_sesame.py` no pasa el mínimo (R9).

### 5.2 Settings y cableado

Mínimo en los dos `settings.py` (negativo ⇒ no arranca, R5), pasado al cliente
en los dos cableados y añadido al log `[sesame][wiring] CABLEADO … festivos_minimos=…`.

### 5.3 `contrastar_festivos_sesame.py` (consola, sv3)

Funciones puras (testeables sin E/S) y un `main()` fino:
- `contrastar_calendario(cal, ano, respaldo, minimo) -> ContrasteCalendario`
  (solo-Sesame, solo-respaldo, L–V, recuento, `por_defecto`, `incompleto`).
  El respaldo es un `JsonCalendarioLaboral` y se consulta con
  `es_no_laborable(fecha)` día a día del año (sin DNI): no se copia su lógica.
- `clasificar_impacto(registros, festivos_por_dni, respaldo) -> Impacto`:
  para cada línea con horas ≠ 0 compara laborable/no laborable con Sesame y
  con el respaldo; si difiere, `congelada` = `esta_congelado(sigrid_estado,
  doc_approved)` importado de `application/services/recurso_conciliador.py`.
- `render_markdown(...)`, `escribir_csv(...)` (UTF-8 BOM, `;`).
- `main(argv)`: `--ano`, `--base-url`, `--api-key`, `--calendario`,
  `--festivos-minimos`, `--salida` (por defecto `logs/`), `--impacto`. Con
  `--impacto` construye `Settings` + `SessionFactory` +
  `SqlAlchemyParteRepository` y llama a `fetch_registros_para_recurso()`
  (**sin SQL nuevo**). Los festivos por DNI se piden con el cliente **sin
  mínimo** (`festivos` → `None` ⇒ `calendario_por_defecto`) para poder
  informar del recuento real; el mínimo solo etiqueta.

### 5.4 `infra/add_sesame_partes.ps1` (PowerShell 5.1, CRLF, sin BOM)

Uso: `. .\00_vars_partes.ps1; . .\00_capps_vars_partes.ps1;
.\add_sesame_partes.ps1 [-Quitar]`. Validaciones de R20
(`az keyvault secret show --vault-name $KV --name SESAME-API-KEY --query id`
sin imprimir el valor). Para `ca-sv3-persistencia` y `ca-sv4-front`:
`az containerapp secret set --secrets "sesame-key=keyvaultref:$KV_URI/secrets/SESAME-API-KEY,identityref:$MI_ID"`
y `az containerapp update --set-env-vars SESAME_API_BASE_URL=… SESAME_API_KEY=secretref:sesame-key
SESAME_API_TIMEOUT_S=10 SESAME_CACHE_TTL_S=21600 SESAME_FESTIVOS_MINIMOS=$SESAME_FESTIVOS_MINIMOS`.
`-Quitar`: `--remove-env-vars` de las cinco (el secreto de la app puede
quedarse: sin variable que lo use es inerte). Termina imprimiendo los comandos
de logs de §7. Mismo `Run-Az` que los demás scripts.

## 6. Ficheros que NO se tocan

- `sesame_calendario_laboral.py` (sv3) y `calendario_provider.py` (sv4): la
  cascada ya trata el error nuevo como fallo (§5.1).
- `recurso_conciliador.py`, `congelacion.py`, `jornada_resolver.py` (gemelos),
  `orm_models.py`: ni regla de congelación ni jornada ni schema cambian (R26).
- `config/calendario_laboral.json` (DA4), `validar_datos_sesame.py`,
  `redeploy_partes.ps1`, `add_secrets_partes.ps1`, sv1, sv2, sv5, `sesame-api`.

## 7. Guía de despliegue y verificación manual (humano)

- **M1 sesame-api en Azure** (DA1, tras P0–P2): `az acr build -r acralbaranesdev
  -t sesame-api:rYYYYMMDD-HHmm .`; secretos `SESAMEAPI-TOKEN` y
  `SESAMEAPI-API-KEYS` (CSV con la clave de partes) en `$KV` y la clave de
  partes en `SESAME-API-KEY` (`add_secrets_partes.ps1`), siempre por consola;
  `az containerapp create -n ca-sesame-api -g $RG --environment $CAE --image …
  --registry-server acralbaranesdev.azurecr.io --registry-identity $MI_ID
  --user-assigned $MI_ID --ingress internal --target-port 8006 --min-replicas 1
  --max-replicas 1 --secrets token=<KvRef SESAMEAPI-TOKEN> keys=<KvRef …>
  --env-vars SESAME_TOKEN=secretref:token API_KEYS=secretref:keys
  SESAME_REGION=<región> API_HOST=0.0.0.0 API_PORT=8006`. Comprobar `/health`
  desde dentro del entorno (`az containerapp exec` en sv4). El FQDN interno va
  a `$SESAME_BASE_URL` de `00_vars_partes.local.ps1`.
- **M2 contraste** (sin BBDD): `python contrastar_festivos_sesame.py --ano 2026
  --base-url <url> --api-key <clave>` (local, túnel o desde la app). El humano
  revisa cada calendario y lo que salga `INCOMPLETO` lo corrige RRHH (P5).
- **M3 impacto**: igual con `--impacto` y el `.env` de sv3; el humano decide
  sobre las `congelada` (corregir en Sigrid queda fuera, DA7).
- **M4 apagado**: `redeploy_partes.ps1 -Solo sv3,sv4`; logs «DESACTIVADO», sin errores.
- **M5 encendido**: `add_sesame_partes.ps1`; logs de sv3 y sv4 con «CABLEADO …
  festivos_minimos=8»; tras el siguiente parte, `[sesame-calendario] … fuente=
  sesame` y `extras_reclasificadas` en `[recurso-concil]`.
- **M6 portal**: persona de Sevilla con su autonómico pintado, sin aviso de
  degradación; preflight sin bloqueo.
- **M7** (opcional): `-Quitar` y vuelta a «DESACTIVADO».

## 8. Decisiones abiertas (recomendación en negrita)

- **DA1 Dónde vive sesame-api.** (A) **Container App `ca-sesame-api` en
  `rg-partes-dev`/`cae-partes-dev`, ingress interno, 1 réplica fija, imagen de
  `acralbaranesdev` y secretos en `kv-partes` por `id-partes-dev`**: es lo
  único alcanzable por sv3/sv4 sin red nueva y no expone datos de RRHH (DNIs,
  ausencias) a Internet. Coste: la identidad de partes puede leer el token de
  Sesame y el servicio «general» queda en casa de partes; se muda a recursos
  propios cuando haya un segundo consumidor. (B) RG, entorno y Key Vault
  propios con ingress **externo** + `x-api-key` (modelo `sigrid-api`):
  reutilizable, pero publica datos personales tras una sola clave.
  (C) Propio con ingress interno: inalcanzable desde `cae-partes-dev`.
- **DA2 Réplicas.** **min = max = 1**: caché de proceso; con 0, cada arranque
  en frío vuelve a pedir a Sesame HR los 218 empleados.
- **DA3 Encendido.** **`add_sesame_partes.ps1` sobre sv3 y sv4 a la vez**, con
  `-Quitar` como rollback, frente a recrear las apps.
- **DA4 Si Sesame no responde.** **Mantener los dos niveles de F-003 tal
  cual** (decisión del humano del 2026-08-15): sv3 caché caducada o JSON +
  `review_required`; sv4 aviso + bloqueo del registro con override
  `[SIN-SESAME]`. La propuesta «solo respaldo + log» quitaría el bloqueo que
  el humano pidió expresamente. Mitigan DA2 y la caché de 6 h. No se alinean
  los respaldos de sv3 (nacional) y sv4 (Madrid): solo actúan degradados.
- **DA5 Calendario incompleto ⇒ degradado.** **Sí, mínimo 8 en el cliente
  gemelo.** Hoy una lista vacía es «dato bueno» (F-003): un año sin calendario
  en Sesame borraría hasta los nacionales y pagaría el 1 de enero como
  ordinario sin aviso. España tiene 12–14 festivos al año. Consecuencia: las
  personas con calendario incompleto (Alicante) quedan con aviso, bloqueo y
  `review_required` hasta que RRHH lo complete. 0 desactiva el control.
- **DA6 Contraste.** **Herramienta de consola en sv3** (el respaldo que paga
  extras vive ahí), con `--impacto` opcional sobre la BBDD en solo lectura.
- **DA7 Partes ya conciliados.** **Recálculo automático** de lo no congelado
  en la siguiente pasada (es lo que el sistema hace hoy con cualquier cambio
  de calendario); lo congelado no se toca y el informe M3 lo lista para que
  el humano decida. Limitarlo a fechas posteriores al encendido exigiría
  código nuevo en el conciliador. Ojo: líneas de un año sin calendario en
  Sesame marcarán su parte para revisión en cada pasada (M3 da los años).
- **DA8 `/jornada` con 0 contratos.** Encendido, sv4 llama a `/api/v1/jornada`
  para el KPI; sesame-api responde **502** a `contract_not_found`, que no se
  cachea: un WARNING y una llamada por persona en cada vista. **Precondición
  P3 en sesame-api (404 ⇒ `None` cacheado)**; alternativa: interruptor
  `SESAME_JORNADA_ENABLED` en sv4 (código nuevo, no incluido).
- **DA9 `azure-apps/sesame-api.md`.** **Lo escribe su dueño**; `partes.md` enlaza.
- **DA10 Rigor.** **Estándar**: el código nuevo es un `raise` que entra en
  cascadas mutadas con rigor crítico en F-003, más una herramienta de solo
  lectura y un script; el riesgo de dinero está en el encendido, que es
  manual y va precedido de M2–M3. Subir a crítico si el humano lo prefiere.

## 9. Riesgos y alternativas descartadas

- Encender sin M2/M3 recalcularía lo no congelado con calendarios mal cargados.
- Arranque en frío de sv3 (KEDA a 0): un (DNI × año) por persona con líneas
  activas, en serie, 10 s de plazo; con sesame-api caliente, segundos.
- Descartado: control del mínimo en los adaptadores (duplicaría lógica fuera
  de la lista cerrada); unir festivos de Sesame con los nacionales (hay
  comunidades que sustituyen nacionales: el calendario del trabajador manda).
- El `.ps1` solo se cubre con inspección estática y M5–M7.
