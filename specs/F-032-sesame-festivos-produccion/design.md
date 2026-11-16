<!-- specs/F-032-sesame-festivos-produccion/design.md -->
# F-032 · Activar Sesame en producción — Diseño

**Rigor: `estandar`** (DA10), sin disparador de `critico`: un `raise` en cascadas ya
mutadas en F-003, una herramienta de solo lectura, pintado en sv4 y scripts; el riesgo
de dinero está en el encendido, manual y detrás de M2–M3.

## 1. Estado de partida (verificado el 2026-11-16 en `dev` `95982ac`, solo lectura)

- **Integración apagada** (sin cambios desde octubre): sv3 `interface_adapters/api/
  app.py::construir_calendario` (:59) da `JsonCalendarioLaboral` sin `SESAME_API_*` y,
  con ellas, `SesameCalendarioLaboral`; sv4 monta `CalendarioProvider` en `build_app`
  (log :572). Ningún cliente tiene aún mínimo de festivos.
- **Recálculo (DA7, revisado)**: la pasada sigue siendo **global**:
  `RecursoConciliador.conciliar_todos()` lee con `leer_pasada` todas las líneas de
  partes `is_active` (F-069), revierte en memoria las `extra_auto` y reparte de nuevo
  todo lo no congelado (`_congelado` = `esta_congelado` o `congelada_por_pareja`,
  F-037). Corre tras **cada** ingesta (`_conciliar_recursos_safely`) y con **cada**
  mensaje `recalcular` de sv4 (`despacho.py`: el `document_id` no acota la pasada;
  F-042/F-043/F-047/F-049/F-068 solo cambian **quién la pide** y el seguimiento).
  Novedades: (a) sv3 es worker KEDA a 0 réplicas y sin ingress, así que **encender no
  recalcula nada** hasta el siguiente mensaje y aprobar entre tanto congela el reparto
  del JSON ⇒ DA11; (b) con `REPARTO_REAJUSTE` encendido (desde 2026-10-18) un día con
  congeladas reajustables y alguna libre cuyo ideal cambie sale como propuesta en
  `reparto_pendiente` (F-046), que el humano aplica o mantiene; (c) el festivo mueve el
  **último laborable** de la semana si `S ≠ 5c` (F-015): el impacto se mide por semana.
- **Rejilla de obra (sv4)**: `obra_detail` (app.py :1293) pasa a `get_obra`
  `holiday_name_para(None)` (D6 de F-003): cabecera **y todas las celdas**
  (`ObraMatrixCell.is_holiday = dc.is_holiday`) salen del calendario por defecto; el
  aviso de jornada incompleta ya usa el de la fila (:1344) y el degradado añade
  `(None, año)` (:1370). Las demás vistas ya van por persona: `trabajador_detail`
  (:1088), `/api/calendario` de «+ Nuevo» (DNI elegido; sin él, el por defecto) y los
  avisos de registro (:2664).
- **Respaldos**: sv3 paga con nacionales + 28-feb; sv4 avisa con nacionales + Madrid.
- **`infra/`**: los `create_*` cablean `SESAME_*` solo al crear; `SESAME-API-KEY` ya está
  en `add_secrets_partes.ps1`; `enqueue_test.py` es el precedente de encolar en Python.
- **sesame-api** (sin cambios desde el 2026-10-06): `dev` en `dcef288`; rediseño sin
  versionar, sin Dockerfile, handlers `async` con `httpx` síncrono, `contract_not_found`
  ⇒ 502 y **`.env` versionado** (no leído). Su puerto por defecto, 8006, en local es de
  `porcentajes-transfer`: allí se arranca con `$env:API_PORT` (manda sobre su `.env`).
- **F-013 (2026-08-18)**: 218 empleados; Madrid 196, Tomares 15, Sevilla 4, Málaga 2,
  Alicante 1 parcial; 0 contratos. **No se sabe** si Sesame da todas las fiestas del
  año o solo las particulares de cada calendario: por eso DA5 = 1 y DA12.

## 2. Límite de servicio y trabajo fuera del repositorio

| Dónde | Qué | Quién |
|---|---|---|
| sv3 | Mínimo en el cliente gemelo, setting espejo, cableado, herramienta de contraste | implementer |
| sv4 | Mismo cliente y setting; rejilla de obra por persona | implementer |
| `infra/` | `add_sesame_partes.ps1`, `pedir_recalculo_partes.py`, mínimo en `create_*` | implementer |
| `azure-apps/partes.md` | R32 | implementer |
| repo **sesame-api** | P0–P5 | **humano** |
| Azure | Imagen, Container App, secretos, encendido | **humano** (§7) |

Sin responsabilidad nueva: el mínimo vive en el cliente gemelo de la lista cerrada de
`CLAUDE.md`; R26 es el contrato `recalcular` de F-042 con un productor más.

**Precondiciones en sesame-api (humano, antes de M1):** **P0** `git rm --cached .env`;
si algún `.env` publicado lleva `SESAME_TOKEN`, **rotarlo** en Sesame antes de cargarlo
en el Key Vault. **P1** Commitear el rediseño y el fix `daysOff` (sin `.env`, `logs/`,
`sesame-api.zip`). **P2** Dockerfile (`python:3.12-slim`, `python main.py`,
`API_HOST=0.0.0.0`, 8006) y `.dockerignore`. **P3** Recomendado: handlers `def` y
`contract_not_found` ⇒ 404 (DA8). **P4** `azure-apps/sesame-api.md` (DA9). **P5** RRHH
completa lo que M2 marque.

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/contrastar_festivos_sesame.py` | §5.4 (consola, `print` permitido) |
| `services/partes-{persistencia,front}/tests/test_f032_cliente_minimo.py` | R1–R4 (`httpx.MockTransport`) |
| `services/partes-{persistencia,front}/tests/test_f032_calendario_incompleto.py` | R5; sv3 R6; sv4 R7, R9 |
| `services/partes-persistencia/tests/test_f032_contraste.py` | R14–R22 con dobles |
| `services/partes-persistencia/tests/test_f032_r29_recalculo.py` | R29–R30 (caracterización) |
| `services/partes-front/tests/test_f032_rejilla_obra.py` | R10–R13 |
| `tests/test_f032_sesame_cliente_gemelos.py` | R8 |
| `tests/test_f032_infra_sesame.py` | R23–R28 (inspección estática) y contrato de R26 |
| `infra/add_sesame_partes.ps1` | §5.5 |
| `infra/pedir_recalculo_partes.py` | §5.6 |

## 4. Ficheros a modificar

- `services/partes-{persistencia,front}/infrastructure/sesame/sesame_api_client.py`:
  §5.1, cuerpo idéntico en los dos, mismo commit.
- Los dos `config/settings.py`: `sesame_festivos_minimos: int = Field(1,
  alias="SESAME_FESTIVOS_MINIMOS", ge=0)`.
- sv3 `interface_adapters/api/app.py::construir_calendario` y sv4
  `interface_adapters/web/app.py::build_app`: pasar el mínimo y loguearlo.
- sv4 `infrastructure/database/parte_repository.py` (`get_obra`, `ObraDayCol`,
  `ObraMatrixCell`), `interface_adapters/web/app.py::obra_detail` y
  `templates/obra_detail.html` (:76, :118–119, :140, :145): §5.3.
- sv4 `tests/test_f003_r2_vistas_festivos.py`: **cambia a propósito**
  `test_f003_r2_la_columna_de_la_matriz_usa_el_calendario_por_defecto` (fija la D6 que
  esta feature revoca): pasa a afirmar R11 y la celda por persona. Ningún otro test
  existente se toca.
- `infra/create_capps_partes.ps1`, `create_sv4_front.ps1` (R27), `00_vars_partes.ps1`
  (`$SESAME_FESTIVOS_MINIMOS = 1`; paso 3 = `add_sesame_partes.ps1`), `README_partes.md`;
  `docs/ARCHITECTURE.md`, `azure-apps/partes.md` (R32) y `harness/features.json`.

## 5. Clases y funciones

### 5.1 Cliente gemelo (infrastructure, sv3 y sv4)

```python
class CalendarioIncompletoError(RuntimeError): ...
SesameApiClient(*, base_url, api_key, timeout_s=10.0, transport=None,
                festivos_minimos: int = 0)
def _exigir_minimo(self, festivos, ano, origen: str) -> list[FestivoDia]
```

`festivos` y `calendario_por_defecto` pasan su lista ya filtrada al año por
`_exigir_minimo`: si `0 < minimo` y `len < minimo`, lanza «calendario incompleto: N
festivos en AAAA (mínimo M) en <origen>». Es un `RuntimeError`: las cascadas de sv3
(`SesameCalendarioLaboral._degradar`, `consumir_degradacion()` ⇒ `review_required`) y
sv4 (`CalendarioProvider._degradar`, fuente `stale`/`respaldo`, no fiable) lo tratan
como fallo **sin tocarlas**. Al lanzar `festivos(dni)` no se prueba el por defecto: a un
trabajador de Alicante con calendario roto no se le dan los festivos de Madrid.

### 5.2 Settings y cableado

Mínimo en los dos `settings.py` (negativo ⇒ `ValidationError`), al cliente y al log
`[sesame][wiring] CABLEADO … festivos_minimos=…`.

### 5.3 Rejilla de obra por persona (sv4, DA13)

- `get_obra(..., holiday_name_de: Callable[[str | None], Callable[[date], str | None]]
  | None = None)` sustituye a `holiday_name` (ningún otro llamador lo pasa). Por fila
  pide `holiday_name_de(w["dni"])` una vez y con él rellena cada celda.
- `ObraMatrixCell` gana `holiday_name: str | None = None`; `ObraDayCol` pierde
  `is_holiday`/`holiday_name` (solo los leía la cabecera).
- `obra_detail` pasa `holiday_name_de=calendario_provider.holiday_name_para` y el aviso
  de jornada incompleta reutiliza el mismo resolutor de la fila. Se borra
  `_consultas.update((None, ano) …)`: las filas sin DNI ya añaden `(None, año)`.
- Plantilla: cabecera sin `mx-hol` ni nombre de festivo; celda con `mx-hol` por
  `c.is_holiday` y `title` con `c.holiday_name` (unido con « · » a lo que ya lleva);
  texto del aviso (:76) según R13. CSS sin cambios.
- Coste: una llamada a `holiday_name_para` por fila; a Sesame, una por (DNI × año) y
  6 h gracias a la caché del provider.

### 5.4 `contrastar_festivos_sesame.py` (consola, sv3)

Funciones puras y un `main()` fino:
- `contrastar_calendario(cal, ano, respaldo, minimo) -> ContrasteCalendario`
  (solo-Sesame, solo-respaldo, L–V, recuento, `por_defecto`, `incompleto`,
  `faltan_del_respaldo`). El respaldo es un `JsonCalendarioLaboral` consultado con
  `es_no_laborable(fecha)` día a día (sin copiar su lógica).
- `clasificar_impacto(registros, festivos_por_dni, respaldo) -> Impacto`: por línea
  con horas ≠ 0 y sin `deleted_at_utc`, si su día cambia o su semana ISO está afectada,
  la clase es `clase_linea(reg, congelada=_congelado(reg))` (importados de
  `reajuste_reparto.py` y `recurso_conciliador.py`). Día mixto = mismo DNI × día con
  `libre` y `reajustable`.
- `render_markdown(...)`, `escribir_csv(...)` (UTF-8 BOM, `;`).
- `main(argv)`: `--ano`, `--base-url`, `--api-key`, `--calendario`,
  `--festivos-minimos`, `--salida` (por defecto `logs/`), `--impacto`. Con `--impacto`:
  `Settings` + `SessionFactory` + `SqlAlchemyParteRepository.
  fetch_registros_para_recurso()`. Los festivos por DNI se piden con el cliente **sin
  mínimo** (`None` ⇒ `calendario_por_defecto`) para informar del recuento real.

### 5.5 `infra/add_sesame_partes.ps1` (PowerShell 5.1, CRLF, sin BOM)

Uso: tras cargar `00_vars_partes.ps1` y `00_capps_vars_partes.ps1`, con `[-Quitar]`.
Valida R24 (`az keyvault secret show … --query id`, sin imprimir el valor).
Orden de R23: sv3 (`az containerapp secret set --secrets "sesame-key=keyvaultref:
$KV_URI/secrets/SESAME-API-KEY,identityref:$MI_ID"` y `az containerapp update
--set-env-vars …`), espera a `latestReadyRevisionName == latestRevisionName`, llama a
`pedir_recalculo_partes.py`, y sv4 igual. `-Quitar`: `--remove-env-vars` de las cinco en
sv3, pasada (`apagado_sesame`), sv4; el secreto de la app queda inerte. La clave de la
storage se lee a `$env:STKEY` (patrón de `enqueue_test.py`) y se borra al terminar. Si
`python` o el encolado fallan: WARNING con el comando exacto y sigue (R26). Termina
imprimiendo los comandos de logs de §7. Mismo `Run-Az` que los demás scripts.

### 5.6 `infra/pedir_recalculo_partes.py`

`mensaje(motivo, ahora, solicitado_por) -> dict` pura y solo con la biblioteca estándar
(el test de contrato la carga por ruta y la pasa por `clasificar` de sv3);
`main(argv)`: `<STORAGE> <motivo>` con `STKEY` del entorno, `azure.storage.queue`
importado dentro de `main`, `json.dumps` sin codificación base64 (como
`ColaCliente.enviar`); motivos admitidos `encendido_sesame` y `apagado_sesame`; no
imprime la clave. Código 0 al encolar.

## 6. Ficheros que NO se tocan

`sesame_calendario_laboral.py`, `calendario_provider.py` (§5.1); `recurso_conciliador.py`,
`reajuste_reparto.py`, `congelacion.py`, `jornada_resolver.py`, `orm_models.py`,
`despacho.py`, `mensajes.py`, `recalculo_publisher.py` (ni congelación, ni jornada, ni
contrato, ni esquema cambian); `calendario_laboral.json` (DA4), `validar_datos_sesame.py`,
`redeploy_*.ps1`, `add_secrets_partes.ps1`, `enqueue_test.py`, sv1, sv2, sv5,
`trabajador_detail.html`, `nuevo_parte.html`, `app.js` y el repo `sesame-api`.

## 7. Guía de despliegue y verificación manual (humano)

- **M1 sesame-api en Azure** (DA1, tras P0–P2): `az acr build -r acralbaranesdev`;
  secretos `SESAMEAPI-TOKEN`, `SESAMEAPI-API-KEYS` y `SESAME-API-KEY` en `$KV` por
  consola; `az containerapp create -n ca-sesame-api` en `$CAE` con `--ingress internal
  --target-port 8006 --min-replicas 1 --max-replicas 1`, identidad `$MI_ID` y
  `SESAME_TOKEN`/`API_KEYS` por `secretref`. `/health` desde dentro del entorno; el FQDN
  interno va a `$SESAME_BASE_URL` de `00_vars_partes.local.ps1`.
- **M2 contraste (puerta, DA12)**: `python contrastar_festivos_sesame.py --ano 2026
  --base-url <url> --api-key <clave>` (y `--ano 2025` si hay partes activos de 2025).
  En local, sesame-api con `$env:API_PORT="8016"` (8006 es de porcentajes-transfer). Si
  algún calendario sale `FALTAN DEL RESPALDO`, **no se enciende**: se vuelve a la spec.
  Lo `INCOMPLETO` lo corrige RRHH (P5).
- **M3 impacto**: igual con `--impacto` y el `.env` de sv3; el humano revisa las
  `dura` y los días mixtos (corregir en Sigrid queda fuera).
- **M4**: `redeploy_partes.ps1 -Solo sv3,sv4`; logs «DESACTIVADO», sin errores.
- **M5 encendido**, fuera del horario de aprobación: `add_sesame_partes.ps1`; logs con
  «CABLEADO … festivos_minimos=1»; en sv3 `[sv3-worker] recalculo motivo=encendido_sesame`,
  `[sesame-calendario] … fuente=sesame` y `extras_reclasificadas`/`repartos_propuestos`.
- **M6 portal**: obra con dos calendarios: cabecera sin festivos y cada fila con los
  suyos; persona de Sevilla con su autonómico, sin aviso degradado ni bloqueo.
- **M7** decidir las propuestas nuevas de `reparto_pendiente`. **M8** (opcional):
  `-Quitar` y vuelta a «DESACTIVADO» con su pasada.

## 8. Frontera

¿Cruza la frontera del proyecto? **Sí.** Pasa a consumir **sesame-api** (servicio
interno nuevo en `cae-partes-dev`, DA1) con la variable nueva `SESAME_FESTIVOS_MINIMOS`
y el secreto `SESAME-API-KEY`; `q-persistencia` gana dos motivos de traza. Se actualiza
`azure-apps/partes.md` (R32); `azure-apps/sesame-api.md` lo escribe su dueño (P4).

## 9. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| DA1 Dónde vive sesame-api | (A) `ca-sesame-api` en `cae-partes-dev`, ingress interno, 1 réplica, secretos en `kv-partes`; (B) recursos propios con ingress externo + `x-api-key`; (C) propios con ingress interno (inalcanzable) | (A) | |
| DA2 Réplicas | (A) min = max = 1; (B) 0–1 (arranque en frío vuelve a pedir los 218) | (A) | |
| DA3 Encendido | (A) `add_sesame_partes.ps1` con `-Quitar`; (B) recrear las apps | (A) | |
| DA4 Si Sesame no responde | (A) los dos niveles de F-003 tal cual; (B) solo respaldo + log | (A) | |
| DA5 Mínimo de festivos | (A) **1** configurable (`SESAME_FESTIVOS_MINIMOS`); (B) 8; (C) 0 | (A); volver a 8 si M2 prueba que Sesame da todas las fiestas | |
| DA6 Contraste | (A) consola en sv3 con `--impacto` opcional; (B) sin herramienta | (A) | |
| DA7 Partes ya conciliados | (A) recálculo de lo libre en la siguiente pasada, congelado intacto salvo propuesta F-046; (B) solo fechas posteriores (código nuevo en el conciliador) | (A) | |
| DA8 `/jornada` con 0 contratos | (A) P3 en sesame-api (404 cacheado); (B) interruptor en sv4 (no incluido) | (A) | |
| DA9 `sesame-api.md` | (A) lo escribe su dueño, `partes.md` enlaza | (A) | |
| DA10 Rigor | (A) estándar; (B) crítico | (A) | |
| DA11 Cuándo corre la pasada tras encender/apagar | (A) la pide el script por `q-persistencia` tras la revisión nueva de sv3 y antes de sv4; (B) esperar al siguiente parte (horas con reparto viejo aprobable); (C) botón en sv4 (código y permisos nuevos) | (A) | |
| DA12 Si Sesame no trae algún festivo del respaldo | (A) puerta: no se enciende y se re-decide (que RRHH los cargue, o unir respaldo y Sesame en una feature aparte); (B) encender igual (el 1-ene se pagaría ordinario) | (A) | |
| DA13 Rejilla de obra | (A) celda por persona, cabecera sin festivos; (B) dejar D6 de F-003 | (A) (pedida por el humano el 2026-11-16) | |

## 10. Riesgos y alternativas descartadas

- Encender sin M2/M3 recalcularía lo libre con calendarios mal cargados; con DA5 = 1
  un calendario solo con fiestas locales pasa el control: M2 es la única defensa (DA12).
- Ventana entre el encendido y la pasada (~1 min con KEDA): aprobar en ella congela el
  reparto del JSON. Mitigan el orden de R23 y M5 fuera de horario.
- Arranque en frío de sv3: un (DNI × año) por persona con líneas activas, en serie, 10 s
  de plazo; con sesame-api caliente, segundos.
- Descartados: el mínimo en los adaptadores (fuera de la lista cerrada);
  `/admin/reconciliar-recursos` (sin ingress en Azure; en local escribiría en producción
  desde el portátil); `az storage message put` (comillas). Los `.ps1`: estático y M5–M8.
