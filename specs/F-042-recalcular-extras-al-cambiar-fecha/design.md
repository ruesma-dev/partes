<!-- specs/F-042-recalcular-extras-al-cambiar-fecha/design.md -->
# F-042 · Recalcular el reparto normal/extra al cambiar la fecha — Diseño

## 1. Encaje y límite de servicio

- El reparto ordinaria/extra es responsabilidad **exclusiva de sv3**
  (semántica 3). F-042 no lo duplica: sv4 solo **pide** una pasada y sv3 hace la
  de siempre (`conciliar_todos`). Ninguna lógica de extras se copia a sv4.
- Canal: `q-persistencia`, la cola que ya consume sv3 con KEDA (min 0). Es la
  única vía: el worker de sv3 no sirve HTTP en Azure (su `/admin/reconciliar-
  recursos` solo existe con `main.py` en local) y la cola despierta a sv3 desde
  cero réplicas. Mismo patrón que el resto del pipeline (at-least-once).
- Sin librería compartida: el formato vive en un módulo de cada lado, atados
  por un test de contrato de la raíz (R22). Es contrato de transporte (como
  `q-transfer`), no lógica: fuera de la lista cerrada de `CLAUDE.md` (DA6).

## 2. Contrato del mensaje (`q-persistencia`)

```json
{"tipo": "recalcular", "motivo": "cambio_fecha" | "deshacer_cambio_fecha",
 "document_id": "<uuid del parte>", "solicitado_por": "<actor o null>",
 "solicitado_at_utc": "<ISO 8601 UTC>"}
```

- Discriminante: `tipo`. El mensaje de sv2 (`document_id`, `filename`,
  `mime_type`, `context`) no lo lleva ⇒ ingesta. Compatible hacia atrás sin
  versionar nada.
- `document_id` va para trazas: `ColaCliente.consumir` ya lo pinta en sus logs
  (`[cola] OK q-persistencia document_id=…`). sv3 **no** lo usa para acotar la
  pasada: `conciliar_todos` siempre recalcula todo lo activo (la jornada se
  mide por trabajador y día entre obras y partes).
- Sin nombres ni DNIs; < 1 KB (tope de Storage Queue: 64 KB).

## 3. sv4 (`services/partes-front/`)

**Crear** `infrastructure/persistencia/__init__.py` (vacío) y
`infrastructure/persistencia/recalculo_publisher.py` — **solo biblioteca
estándar** (lo carga el test de contrato por ruta):

- Constantes `TIPO_RECALCULAR = "recalcular"`, `MOTIVO_CAMBIO_FECHA`,
  `MOTIVO_DESHACER_FECHA`, `ESTADO_PEDIDO = "pedido"`, `ESTADO_FALLO = "fallo"`,
  `ESTADO_SIN_COLA = "sin_cola"`.
- `mensaje_recalculo(*, document_id: str, motivo: str, solicitado_por: str |
  None, ahora: datetime) -> dict` — función pura del §2.
- `class RecalculoPublisher` — `__init__(self, *, cola, cola_persistencia: str,
  reloj: Callable[[], datetime] = <utc now>)`; `pedir(self, *, document_id,
  motivo, solicitado_por) -> None`: construye el mensaje y llama
  `cola.enviar(cola_persistencia, mensaje)`; log INFO; **lanza** si la cola
  falla.
- `pedir_recalculo(publisher: RecalculoPublisher | None, *, document_id,
  motivo, solicitado_por) -> str` — nunca lanza: `None` ⇒ `sin_cola`; éxito ⇒
  `pedido`; excepción ⇒ WARNING `[recalculo] no se pudo pedir … document_id=%s
  (%s)` con el nombre del tipo de error y `fallo` (R3).

**Modificar**

- `config/settings.py`: `cola_persistencia: str = Field("q-persistencia",
  alias="COLA_PERSISTENCIA")` en el bloque de colas (mismo nombre de variable
  que sv2 y sv3). En Azure **no** hace falta definirla: el defecto es el real.
- `interface_adapters/web/app.py`:
  - `build_app(..., recalculo_publisher: RecalculoPublisher | None = None)`;
    sin inyección, `RecalculoPublisher(cola=cola_cliente,
    cola_persistencia=settings.cola_persistencia)` si `cola_cliente` no es None;
    si no, None (R4, R10). `main.py` **no cambia**: ya pasa `cola_cliente`
    solo cuando hay colas.
  - `patch_parte_fecha(document_id, payload, request: Request)`: tras
    `update_parte_fecha` con éxito (400/404/409 salen antes, R5),
    `recalculo = pedir_recalculo(..., motivo=MOTIVO_CAMBIO_FECHA,
    solicitado_por=_actor(request))` y se añade a la respuesta (R1–R4, R6).
    No compara fecha vieja y nueva (DA5).
  - `undo_apply(request: Request)`: si `res["ok"]` y `res.get("action") ==
    "parte_fecha"`, pide el recálculo con `MOTIVO_DESHACER_FECHA` sobre el
    `id` de cada snapshot de documento de la entrada (en la práctica uno) y
    añade `recalculo` (el peor estado si hubiera varios: `fallo` > `sin_cola`
    > `pedido`). Otra acción ⇒ sin clave `recalculo` (R7, R8).
- `infrastructure/database/parte_repository.py::undo_last`: devuelve además
  `action` (`row.action`) y `document_ids` (ids de los snapshots de documento
  de la entrada). Ningún otro cambio en el repositorio (R9).
- `static/app.js`:
  - `wireFechaInput`: según `data.recalculo` pinta los textos de R11;
    `fallo` con `setStatus(..., "error")` (persistente) y `pedido`/`sin_cola`
    con `saved`. Sin `recalculo` (sv4 viejo) ⇒ «✓ Guardado» de hoy.
  - Botón deshacer (`/api/undo`): si `res.recalculo === "fallo"`, `alert` con
    el aviso antes del `reload`.

## 4. sv3 (`services/partes-persistencia/`)

**Crear** `interface_adapters/workers/__init__.py` (vacío; `workers` en plural
como en sv4) y:

- `interface_adapters/workers/mensajes.py` — **solo biblioteca estándar**:
  `TIPO_RECALCULAR = "recalcular"`, `CLASE_INGESTA = "ingesta"`,
  `CLASE_RECALCULO = "recalcular"`, `class MensajeDesconocido(ValueError)`,
  `clasificar(payload: object) -> str` (R12: no-dict o `tipo` desconocido ⇒
  `MensajeDesconocido` con el tipo recibido en el texto).
- `interface_adapters/workers/despacho.py`:
  `construir_handler(*, blob, pipeline, recurso_conciliador,
  contenedor_input: str, contenedor_envelopes: str) -> Callable[[dict], None]`.
  El handler clasifica y: ingesta ⇒ el cuerpo actual de `handler` de
  `main_worker.py`, **movido sin cambios** (R13); recálculo ⇒ si
  `recurso_conciliador is None`, WARNING `[sv3-worker] recalculo pedido pero
  Sigrid no esta cableado` y vuelve (R17); si no, `res =
  recurso_conciliador.conciliar_todos()` **sin try/except** (R15) e INFO
  `[sv3-worker] recalculo motivo=%s document_id=%s por=%s -> %s` (R14);
  `MensajeDesconocido` ⇒ ERROR y se relanza (R16).

**Modificar**

- `main_worker.py`: el `handler` local pasa a ser `construir_handler(blob=blob,
  pipeline=app.state.pipeline, recurso_conciliador=
  app.state.recurso_conciliador, contenedor_input=CONTENEDOR_INPUT,
  contenedor_envelopes=CONTENEDOR_ENVELOPES)`; se construye `app =
  build_app(settings)` una vez. Docstring: los dos tipos de mensaje.
- `interface_adapters/api/app.py`: `app.state.recurso_conciliador =
  recurso_conciliador` junto a `app.state.pipeline` (R18).

No se reutiliza `_conciliar_recursos_safely`: traga la excepción porque allí
importa guardar el parte; aquí la pasada **es** el trabajo y se reintenta (DA3).

## 5. Tests (sin red ni BBDD real; datos sintéticos, sin nombres ni DNIs)

- `services/partes-front/tests/test_f042_recalculo_fecha.py` — `build_app` con
  repositorio SQLite de los dobles de sv4 y una cola falsa que registra
  `enviar` (o que lanza): R1–R11 (`test_f042_rN_…`). R2 con un repositorio
  espía que anota el orden de llamadas; R11 leyendo `static/app.js` (los tres
  estados y los textos) + `node --check`.
- `services/partes-persistencia/tests/test_f042_despacho.py` — `clasificar` y
  `construir_handler` con blob, pipeline y conciliador falsos: R12–R18 (R18:
  `construir_casado_sigrid`/`build_app` no se levanta; se comprueba con el
  mismo patrón que `test_f023_wiring_sv3.py`, o leyendo `app.py` por AST si el
  wiring exige PostgreSQL).
- `services/partes-persistencia/tests/test_f042_domingo_a_jueves.py` — ciclo
  real con `SqlAlchemyParteRepository` sobre `FabricaSesionSqlite`,
  `RecursoConciliador` real y los dobles de F-037 (`IndiceFijo`, `LookupFake`,
  `CalendarioFake` con el domingo 2026-10-11 no laborable): sembrar el parte el
  domingo, pasada, `UPDATE` de `fecha`/`fecha_int` de documento y **todas** sus
  líneas a 2026-10-01 (lo mismo que `update_parte_fecha`), handler con un
  mensaje de recálculo ⇒ R19 (oráculo: el mismo parte sembrado el jueves en otra
  base y una pasada; se comparan `(line_index, empleado_line_no, tipo_hora,
  extra_auto, horas, horas_orig)`), R20 y R21.
- `tests/test_f042_contrato_recalculo.py` (raíz) — carga por ruta con
  `importlib.util.spec_from_file_location` (nombres de módulo únicos) los dos
  módulos del contrato; R22 (el de sv2, por AST: el dict de `cola.enviar(
  COLA_SALIDA, …)` no tiene clave `tipo`; imports de los dos módulos ⊂ stdlib
  por AST).

## 6. Ficheros que NO se tocan

`recurso_conciliador.py`, `pareja_extra.py` y
`sqlalchemy_parte_repository.py` de sv3; `congelacion.py`, `orm_models.py`
(las dos copias), `cola_cliente.py` (las dos), `credenciales.py`,
`transfer_queue_publisher.py`, `resultado_consumer.py` y `main.py` de sv4;
`services/partes-api/` (sv2), `services/partes-transfer/` (sv5),
`services/partes-email/` (sv1); `infra/`; la lista cerrada de `CLAUDE.md`;
tests existentes (si uno se rompe por un cambio de forma ⇒ `blocked`).
Excepción prevista: añadir la clave `recalculo` a la respuesta puede afectar a
un test que compare el JSON entero; si pasa, se para y se consulta.

## 7. Infra, permisos y despliegue

- **Permiso (verificado, solo lectura, 2026-10-09)**: `ca-sv4-front` es
  `UserAssigned` con la identidad `id-partes-dev` (su `AZURE_CLIENT_ID` coincide
  con el `clientId` de esa identidad). Sus roles: *Storage Queue Data
  Contributor* y *Storage Blob Data Contributor* con ámbito la cuenta de
  almacenamiento de partes entera, donde vive `q-persistencia` (misma cuenta
  que `COLAS_ACCOUNT_URL` de sv3 y sv4). **No hace falta rol nuevo.**
- **Variables**: ninguna nueva en Azure (`COLA_PERSISTENCIA` por defecto
  `q-persistencia`). `infra/` no cambia (los «manifiestos» de sv4 son solo
  `Dockerfile` y `requirements.txt`).
- **KEDA**: la regla `q-persistencia-scaler` de sv3 ya escala por esa cola; los
  recálculos lo despiertan como cualquier parte.
- **Orden de despliegue**: sv3 → sv4 (el de siempre). Si sv4 llegase antes, un
  sv3 viejo trataría el mensaje como ingesta: descarga el PDF del parte (si la
  lifecycle no lo ha borrado), el dedup por sha256 lo da por existente y no
  recalcula; si el blob ya no está, reintentos y `-poison`. Inocuo, pero inútil.
- **azure-apps/partes.md**: sv4 pasa a **producir** en `q-persistencia`
  (diagrama y texto). Commit local en ese repositorio, en el mismo trabajo.

## 8. Riesgos y alternativas

- **R-a · Ventana hasta el recálculo** (arranque de sv3 desde 0 + pasada,
  ~1–2 min): quien apruebe en ese rato congela el reparto viejo. Se avisa en la
  pantalla (R11); bloquear exigiría un estado nuevo compartido sv3↔sv4 (DA4).
- **R-b · Pasadas concurrentes** (preexistente): sv3 tiene `maxReplicas=5` y
  dos réplicas pueden ejecutar `conciliar_todos` a la vez (revertir y partir en
  paralelo puede duplicar `extra_auto` hasta la siguiente pasada). Con
  `KEDA_QUEUE_LENGTH=5` (`infra/00_capps_vars_partes.ps1`) hace falta más de 5
  mensajes pendientes para una segunda réplica; F-042 añade un mensaje por
  cambio de fecha manual. No se arregla aquí; si el humano quiere, feature
  aparte (p. ej. `maxReplicas=1` en sv3 o un candado consultivo en PostgreSQL).
- **R-c · Poison**: un recálculo agotado acaba en `q-persistencia-poison` sin
  reencolado desde el portal; la siguiente ingesta recalcula igual (M3).
- **R-d · Sigrid caído a mitad de pasada**: como hoy (`_hmo_index` None ⇒ esa
  obra se salta sin error).
- **Descartadas**: sv4 llama a sv3 por HTTP (sv3 en Azure es solo worker y
  escala a cero); sv4 recalcula el reparto (duplicaría el cómputo de extras);
  sv3 recalcula solo el `document_id` (la jornada cruza partes y obras: lógica
  nueva en `conciliar_todos`); coalescer comparando `solicitado_at_utc` con la
  última pasada (relojes de contenedores distintos y estado nuevo; las pasadas
  son idempotentes, R21).

## 9. Verificación MANUAL (humano; solo lectura salvo el despliegue)

- **M1 · antes de desplegar** (base `partes`, firewall abierto a mano por el
  humano): estado del parte de la obra 0694 del 01/10. Puede estar **ya
  arreglado** si después entró otro parte (cualquier ingesta recalcula todo):

```sql
SELECT r.line_index, r.empleado_line_no, r.tipo_hora, r.extra_auto,
       r.horas, r.horas_orig, r.sigrid_estado, d.approved
FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
WHERE d.is_active AND d.obra_codigo = '0694' AND d.fecha_int = 20261001
  AND r.deleted_at_utc IS NULL
ORDER BY r.line_index, r.empleado_line_no, r.extra_auto;
```

- **M2 · tras desplegar sv3 y sv4** (`.\redeploy_partes.ps1 -Solo sv3` y luego
  `-Solo sv4`, desde `infra/`, cuando lo pida el humano): en el portal, volver
  a guardar la fecha 01/10 de ese parte (si no está aprobado; si lo está,
  otro parte sin congelar) ⇒ «recalculando extras». A los 1–2 min, en Log
  Analytics (`$WS = az containerapp env show -n cae-partes-dev -g
  rg-partes-dev --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv`):
  `az monitor log-analytics query -w $WS --analytics-query
  "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv3-persistencia'
  | where Log_s has 'recalculo' | project TimeGenerated, Log_s | order by
  TimeGenerated desc | take 20"` ⇒ una línea `[sv3-worker] recalculo
  motivo=cambio_fecha document_id=<el del parte>`. Repetir la SQL de M1: cada
  base con `horas` = jornada del jueves y su `extra_auto` con el exceso.
- **M3 · poison**: `az storage message peek --queue-name q-persistencia-poison
  --account-name stpartespt7m3 --auth-mode login --num-messages 32` ⇒ ningún
  mensaje con `"tipo": "recalcular"`.

## 10. Decisiones abiertas (humano)

- **DA1 · Deshacer un cambio de fecha también pide recálculo** (R7–R9). Sin
  ello, deshacer tras el recálculo deja la fecha vieja con el reparto nuevo
  (las `extra_auto` creadas por sv3 no están en el snapshot) hasta la siguiente
  pasada. Es la misma acción en sentido contrario. *Recomendado*; si no, se
  retiran R7–R9 y su tarea.
- **DA2 · Sin coalescer**: cada cambio de fecha, una pasada idempotente.
  *Recomendado* (§8).
- **DA3 · El recálculo no es best-effort**: un fallo se reintenta y acaba en
  poison, a diferencia de la conciliación tras ingesta. *Recomendado*.
- **DA4 · No bloquear la aprobación** durante el recálculo; solo aviso.
  *Recomendado*.
- **DA5 · Publicar aunque la fecha no cambie** (reguardar = reintento manual,
  y lo que usa M2). *Recomendado*.
- **DA6 · Fuera de la lista cerrada de `CLAUDE.md`**: contrato de mensaje
  vigilado por test de contrato, no lógica duplicada. *Recomendado*.
