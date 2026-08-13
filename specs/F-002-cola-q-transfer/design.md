<!-- specs/F-002-cola-q-transfer/design.md -->
# F-002 · Cola q-transfer — Diseño técnico

## Servicios que toca y por qué (regla LÍMITE DE SERVICIO)

- **sv4 (partes-front)**: es el productor de aprobaciones y el ÚNICO dueño
  de `parte_registros` en este flujo → publica en `q-transfer`, consume
  `q-transfer-result` y actualiza las columnas `sigrid_*`.
- **sv5 (partes-transfer)**: es el ÚNICO servicio con credencial de
  escritura en Sigrid → consume `q-transfer`, ejecuta el pipeline de
  registro existente y publica el resultado en `q-transfer-result`.
- **infra/**: colas y contenedor nuevos + variables de entorno.
- sv1, sv2 y sv3 NO se tocan.

Sobre la duplicación: sv4 y sv5 reciben cada uno sus adaptadores de
Storage (`infrastructure/azure/`), adaptación del patrón que ya tienen sv1,
sv2 y sv3 por separado. No es la duplicación tolerada de `orm_models.py` /
clientes Sigrid (que no crece): es la arquitectura declarada en
`docs/ARCHITECTURE.md` — sin librería compartida, cada servicio lleva sus
adaptadores y se acoplan solo por mensajes.

## La decisión central: cómo vuelve el resultado a `parte_registros`

El registro produce un veredicto por línea (escrita / omitida / ya
registrada / conflicto) que hoy sv4 guarda en las columnas `sigrid_*` justo
después del HTTP síncrono (`marcar_registros_sigrid`). Al volverse
asíncrono, alguien tiene que cerrar ese lazo. Alternativas evaluadas:

**Elegida — B: cola de respuesta `q-transfer-result` consumida por sv4.**
sv5 publica el resultado (mismo JSON que hoy devuelve por HTTP) y un hilo
consumidor en sv4 aplica `marcar_registros_sigrid`. Razones:
- sv5 sigue sin BBDD (R11): no gana responsabilidad de persistencia ni
  credencial de PostgreSQL, y la duplicación tolerada de `orm_models.py`
  (sv3+sv4) NO crece a una tercera copia — el CLAUDE.md lo prohíbe.
- Simetría con el resto del pipeline (sv1→sv2→sv3 ya se hablan por colas
  con hand-off por blob): mismo patrón operativo, misma DLQ, mismos logs.
- La reentrega at-least-once es benigna: el marcado es idempotente (R13).
- Coste: un hilo consumidor dentro del proceso web de sv4. Con 2 réplicas
  de sv4 ambas compiten por la cola; inocuo por idempotencia.

**Descartada — A: sv5 escribe directamente en PostgreSQL.** Exigiría una
tercera copia de `orm_models.py` (prohibido: la duplicación tolerada no
crece), otra credencial de PG, y rompe la responsabilidad única de sv5
(«escribe en Sigrid, nada más»). Además acoplaría el despliegue de sv5 al
esquema de la base.

**Descartada — C: polling de sv4 a sv5 (job id en memoria).** sv5 se vuelve
stateful (los jobs se pierden en cada reinicio/redeploy), hay que inventar
un almacén de resultados con TTL, y el polling desde un proceso web con 2
réplicas y usuarios que cierran el navegador deja resultados huérfanos.

**Descartada — D: webhook sv5 → sv4.** El ingress de sv4 está detrás de
Easy Auth (Entra): una llamada interna de sv5 necesitaría token o una
excepción de auth, y acopla sv5 a la URL y disponibilidad de sv4. La cola
ya da el desacoplamiento y el reintento gratis.

## Otras decisiones

1. **Hand-off por blob, no payload en el mensaje.** Una obra×mes puede
   superar los 64 KB de un mensaje de Storage Queue (cientos de líneas).
   Mismo patrón que sv1→sv2→sv3: el mensaje lleva solo la referencia.
2. **sv5 consume en hilos del MISMO proceso/réplica que la API** (no un
   Container App worker aparte con KEDA). Motivos: (a) la restricción dura
   maxReplicas=1 — un worker separado sumaría una segunda instancia
   escribiendo en paralelo con el HTTP de pisado; (b) el HTTP de
   preflight/pisado exige min=1, así que KEDA 0→1 no ahorra nada; (c) el
   lock de proceso (R7) solo protege si API y consumidor comparten proceso.
   KEDA queda explícitamente fuera para sv5. (Ampliación 1: son
   `TRANSFER_WORKERS` hilos, no uno; ver sección propia.)
3. **Pisar conflictos sigue siendo síncrono** (R5): es una acción humana
   interactiva del modal que quiere resultado inmediato, y mantenerla en
   HTTP evita transportar `pisar_claves` (decisión destructiva) por una
   cola con reentregas.
4. **Fallback síncrono** (R3): sin colas configuradas, el endpoint nuevo de
   sv4 degrada al flujo HTTP actual. Permite desarrollo local sin Azurite y
   despliegue en dos pasos (código primero, infra después).
5. **Estados nuevos en `sigrid_estado`** (`encolado`, `conflicto`,
   `error`): son valores nuevos de una columna String(16) existente — NO
   hay cambio de schema, NO se tocan los `orm_models.py`.
6. **Errores globales del pipeline** (R14): sv5 captura la excepción,
   publica resultado `ok=false` con el error y BORRA el mensaje (el error
   queda trazado en sv4 como `sigrid_estado='error'`; reaprobar es seguro
   por synckey). Solo los fallos de infraestructura (blob inaccesible,
   JSON corrupto) dejan el mensaje reaparecer hacia poison (R9).

## Ampliación 1 — preparación en paralelo, escritura serializada (R18–R22)

### El corte del pipeline, estudiado sobre `registro_pipeline.py`

El pipeline actual mezcla en `preflight()` (pasos 1–7) lecturas de dos
naturalezas distintas, y ese es el criterio del corte:

- **Datos maestros que sv5 nunca escribe** — paso 1 (obra destino), paso
  2b (DNI → `res.ide`), paso 3 (carga de `reshor`, la llamada que más
  crece con el tamaño del lote), paso 4 (reglas, CPU puro). Leerlos en
  paralelo es seguro: ninguna escritura de sv5 los altera.
- **Estado que la propia escritura modifica** — paso 5 (búsqueda del parte
  `hmo` + propuesta de correlativo con `siguiente_cod_pt`), paso 6
  (synckeys ya escritas) y paso 7 (conflictos con líneas existentes).
  Estos NO pueden evaluarse fuera del lock: dos preparaciones paralelas
  propondrían el MISMO correlativo `PT<AA>/NNNNN` (y crearían dos
  cabeceras para la misma obra+mes), y dos peticiones con líneas del mismo
  recurso+día+código de hora no se verían mutuamente como conflicto ⇒
  horas duplicadas en Sigrid. Es exactamente el caso que hoy evita la
  serialización HTTP.

Por tanto el corte es: **`preparar` = pasos 1–4 (paralelo)** y
**`registrar` = pasos 5–9 (bajo lock)**. La cabecera `hmo` pertenece
íntegra a la fase de escritura, como se sospechaba.

### Estimación honesta de la ganancia

Fuera del lock quedan 2–3 llamadas a sigrid-api (obra; DNI opcional;
`reshor`, la más pesada y la que crece con el nº de recursos) más el CPU
de las reglas. Bajo el lock quedan 3–5 lecturas (partes existentes,
`siguiente_cod_pt` si hay parte nuevo, synckeys ×2, líneas existentes por
periodo) más las escrituras. La fracción serializada ronda el 50–70 % de
la latencia por petición ⇒ por Amdahl, con `TRANSFER_WORKERS=3` el
throughput del lote mejora como mucho **×1,4–×2, no ×3**. Merece la pena
(en lotes grandes `reshor` domina), pero el lock sigue siendo el cuello.
Si en real la mejora no aparece, la palanca siguiente sería sacar más
lecturas con revalidación bajo lock — fuera de alcance aquí.

### Refactor mínimo de `registro_pipeline.py` (sin tocar `reglas_registro`)

- `ContextoRegistro` — dataclass nueva en
  `domain/models/registro_models.py`: `obra_origen`, `obra_destino`,
  `forzada_pruebas`, `lineas`, `acciones`. Es el producto de `preparar` y
  el insumo de `registrar`.
- `preparar(*, obra, lineas) -> ContextoRegistro` — pasos 1, 2b, 3, 4
  (código actual movido, no reescrito).
- `_evaluar(ctx) -> Preflight` — pasos 5, 6, 7 desde el contexto.
- `registrar(ctx, *, pisar_claves=None, usuario=None) -> ResultadoRegistro`
  — **adquiere el lock** y ejecuta `_evaluar` + pasos 8–9. Evaluar los
  conflictos DENTRO de registrar es lo que garantiza R20.
- `preflight()` y `ejecutar()` conservan firma y comportamiento,
  recompuestos: `preflight = _evaluar(preparar(...))` (sin lock: no
  escribe, y su resultado siempre fue consultivo);
  `ejecutar = registrar(preparar(...), ...)`.
- **El lock pasa al constructor**: `RegistroPipeline(cliente=, settings=,
  lock=None)` (con `None` crea el suyo). Lo adquiere `registrar`, de modo
  que NINGÚN llamante puede olvidarlo. Esto simplifica el diseño previo de
  `build_app`: el endpoint HTTP `ejecutar` ya no toma el lock
  explícitamente (y además deja de retener el lock durante la fase de
  preparación, acortando la espera de los workers). `main.py` crea UN lock
  y lo pasa al único pipeline compartido por HTTP y workers.

Invariante que protege el lock: **entre que `registrar` lee el estado
escrito de Sigrid (partes, correlativo, synckeys, conflictos) y termina de
escribir, ninguna otra escritura —de cola o de HTTP— toca Sigrid.**

### Consumidor con pool

`transfer_consumer` lanza `TRANSFER_WORKERS` hilos daemon idénticos; cada
uno ejecuta su propio bucle `consumir` con **su propia instancia de
cliente de cola/blob** (los clientes del SDK no se comparten entre hilos)
y el MISMO handler: receive → `preparar` (paralelo) → `registrar`
(serializa el lock) → publicar resultado → delete. Alternativa descartada:
un receptor único + `ThreadPoolExecutor` — más piezas (futures, gestión de
visibilidad por mensaje en vuelo) para el mismo resultado; N consumidores
idénticos reutilizan el bucle con poison/max_dequeue/SIGTERM tal cual.

Los tests usan **fakes con latencia simulada** (`time.sleep` pequeño o
eventos de threading en el cliente fake) para probar que las preparaciones
solapan (R18), que `registrar` serializa (R19), que el estado se evalúa
bajo el lock —dos peticiones a la misma obra+mes crean UN solo parte con
UN solo correlativo— (R20), que el orden de publicación no está
garantizado (R21) y que el fallo de una petición no tumba a las demás
(R22). Sin red ni BBDD.

## Ampliación 2 — gestión de poison desde el portal (R23–R26)

Todo en sv4; sv5 no interviene (los mensajes reencolados los procesa por
la vía normal, idempotente por synckey).

- `infrastructure/azure/cola_cliente.py` (sv4, ya previsto) gana dos
  métodos:
  - `contar_aproximado(cola) -> int` — `get_queue_properties().
    approximate_message_count`. Aproximado vale: es un aviso, no un
    contador contable; la acción de reencolar re-lee la cola real.
  - `mover(origen, destino, maximo=32) -> list[str]` — por cada mensaje:
    receive de la poison → send a la principal → **delete de la poison
    SOLO tras el send con éxito** (R25) → log con id y contenido.
    Devuelve los ids movidos.
- Endpoints en `interface_adapters/web/app.py` (allowlist cerrada de dos
  colas; NUNCA nombres libres del cliente):
  - `GET /api/admin/poison` → `{"habilitado": true, "colas": [{"cola":
    "q-transfer-poison", "principal": "q-transfer", "mensajes_aprox": N},
    {...}]}`. Sin colas configuradas → `{"habilitado": false}` (200).
  - `POST /api/admin/poison/reencolar` body `{"cola": "q-transfer" |
    "q-transfer-result"}` → mueve ≤32 mensajes de `<cola>-poison` a
    `<cola>` y responde `{movidos, restantes_aprox}`. 409 si las colas no
    están configuradas; 422 si la cola no está en la allowlist.
- UI: aviso en la cabecera común (`templates/base.html`) pintado por
  `static/app.js`, que consulta `GET /api/admin/poison` al cargar cada
  página (sin polling continuo). Con recuento > 0, badge visible que
  despliega el detalle por cola y el botón «Reencolar (máx. 32)». Sin
  página nueva.
- **Autorización — decisión abierta para el humano**: el portal entero ya
  está detrás de Easy Auth (Entra) y no existe modelo de roles, así que la
  acción queda disponible para cualquier usuario autenticado del portal.
  Restringirla a administradores exigiría un modelo de roles (fuera de
  alcance de F-002).

## Contratos de mensajes y blobs

Contenedor blob: `transfer` (en `stpartespt7m3`).

- Mensaje `q-transfer`:
  `{"peticion_id": "<uuid4>", "blob": "peticiones/<peticion_id>.json"}`
- Blob `peticiones/<id>.json`: `{"peticion_id", "usuario", "creado_at_utc",
  "obra": {...}, "lineas": [...], "pisar_claves": []}` — `obra` y `lineas`
  con el MISMO esquema que hoy acepta `PeticionIn` de sv5 (sale de
  `lineas_para_registro`, sin cambios). `pisar_claves` siempre vacío (R5).
- Mensaje `q-transfer-result`:
  `{"peticion_id": "<uuid4>", "blob": "resultados/<peticion_id>.json"}`
- Blob `resultados/<id>.json`: `{"peticion_id", "usuario",
  "procesado_at_utc", "resultado": {...}}` — `resultado` con el MISMO JSON
  que hoy devuelve `POST /api/registro/ejecutar` (incluye `ok`, `escritas`,
  `omitidas`, `ya_registradas`, `pendientes_confirmacion` con `registros`
  —los ids—, y `error`).

Reutilizar el esquema HTTP existente en ambos sentidos es deliberado: sv5
no cambia su dominio ni su pipeline, solo gana un transporte nuevo.

## Ficheros a CREAR

### sv5 — `services/partes-transfer/`
- `infrastructure/azure/__init__.py`
- `infrastructure/azure/cola_cliente.py` — adaptación del de sv3 (productor
  `enviar`, consumidor `consumir` con poison/max_dequeue/SIGTERM; log por
  `peticion_id` en vez de `document_id`).
- `infrastructure/azure/blob_cliente.py` — adaptación del de sv3
  (`descargar`, `subir`, `asegurar_contenedores`).
- `infrastructure/azure/credenciales.py` — adaptación del de sv3
  (connection string local/Azurite o account_url + DefaultAzureCredential).
- `interface_adapters/queue/__init__.py`
- `interface_adapters/queue/transfer_consumer.py` — el handler de cola
  (equivalente en capa al `app.py` HTTP): parsea el blob de petición,
  construye el dominio, ejecuta el pipeline BAJO el lock y publica el
  resultado.
- `tests/` — suite del servicio (hoy no existe; init.sh la ejecuta al
  aparecer): `test_f002_transfer_consumer.py`, `test_f002_lock.py`,
  `test_f002_cola_cliente.py`, `test_f002_pipeline_fases.py` (split
  preparar/registrar + regresión) y `test_f002_workers.py` (concurrencia
  R18–R22 con fakes con latencia), con dobles (fakes de
  cola/blob/pipeline/cliente Sigrid).

### sv4 — `services/partes-front/`
- `infrastructure/azure/__init__.py`
- `infrastructure/azure/cola_cliente.py`, `blob_cliente.py`,
  `credenciales.py` — misma adaptación que en sv5; el de sv4 añade además
  `contar_aproximado` y `mover` (ampliación 2).
- `infrastructure/transfer/transfer_queue_publisher.py` — clase
  `TransferQueuePublisher(cola, blob, cola_transfer, contenedor)` con
  `publicar(payload: dict, usuario: str|None) -> str` (devuelve
  `peticion_id`): sube el blob de petición y encola el mensaje.
- `interface_adapters/workers/__init__.py`
- `interface_adapters/workers/resultado_consumer.py` — handler del mensaje
  de `q-transfer-result`: descarga el blob de resultado y llama al
  repositorio (`marcar_registros_sigrid` extendido). Función
  `arrancar_consumidor_resultados(...)` que lanza el hilo daemon.
- `tests/test_f002_publisher.py`, `tests/test_f002_resultado_consumer.py`,
  `tests/test_f002_aprobar_encolar.py`, `tests/test_f002_poison.py`
  (ampliación 2, R23–R26 con fakes) — la suite del servicio ya existe.

### infra/
- `infra/add_qtransfer_partes.ps1` — crea `q-transfer`,
  `q-transfer-result`, sus `-poison` y el contenedor `transfer` en
  `stpartespt7m3` (idempotente, patrón de los scripts existentes; PS 5.1,
  sin BOM, CRLF). Las variables de entorno de los Container Apps se aplican
  con `az containerapp update` documentado en el propio script (MANUAL).

## Ficheros a MODIFICAR

### sv5
- `config/settings.py` — añade: `colas_connection_string` /
  `colas_account_url`, `blobs_connection_string` / `blobs_account_url`,
  `cola_transfer` (`q-transfer`), `cola_transfer_result`
  (`q-transfer-result`), `blob_transfer` (`transfer`),
  `cola_visibility_s` (600), `cola_max_dequeue` (5) y `transfer_workers`
  (3, mínimo 1 — ampliación 1). Todas opcionales: sin ellas, sv5 arranca
  como hoy (solo HTTP).
- `application/pipelines/registro_pipeline.py` — ampliación 1: split en
  fases `preparar` / `_evaluar` / `registrar` con el lock en el
  constructor; `preflight` y `ejecutar` conservan firma y comportamiento
  (código movido, no reescrito; detalle en la sección de la ampliación).
- `domain/models/registro_models.py` — dataclass nueva `ContextoRegistro`
  (producto de `preparar`).
- `main.py` — composición en el punto de entrada: crea `Settings`,
  `SigridWriteClient`, un `threading.Lock` y el `RegistroPipeline`
  compartido (con el lock en el constructor); si hay storage configurado,
  arranca los `TRANSFER_WORKERS` hilos consumidores (`transfer_consumer`)
  antes de `uvicorn.run`; pasa el pipeline a `build_app`.
- `interface_adapters/api/app.py` — `build_app(settings, pipeline=None)`:
  acepta el pipeline inyectado (si `None`, lo construye como hoy —
  retrocompatible). Los endpoints NO toman lock: lo adquiere
  `registrar` dentro del pipeline (ampliación 1), con lo que `ejecutar`
  queda serializado igualmente y `preflight` sigue sin lock.

### sv4
- `config/settings.py` — añade las mismas claves de storage
  (`colas_*`, `blobs_*`, `cola_transfer`, `cola_transfer_result`,
  `blob_transfer`, `cola_visibility_s`, `cola_max_dequeue`) y la propiedad
  `transfer_queue_enabled` (storage configurado). Opcionales.
- `main.py` — si `transfer_queue_enabled`, arranca el hilo consumidor de
  resultados (daemon) antes de `uvicorn.run`.
- `interface_adapters/web/app.py` — endpoint nuevo
  `POST /api/aprobar/encolar`: construye el payload con
  `_payload_registro` (rechaza peticiones con `pisar_claves` no vacío →
  422, esas van por `/api/aprobar/ejecutar`); si hay publisher → publica,
  marca `encolado` y responde `modo:"asincrono"`; si no → delega en el
  flujo síncrono actual y responde `modo:"sincrono"` con el resultado.
  `/api/aprobar/preflight` y `/api/aprobar/ejecutar` quedan como están.
  Ampliación 2: endpoints `GET /api/admin/poison` y
  `POST /api/admin/poison/reencolar` (detalle en su sección).
- `infrastructure/database/parte_repository.py` — dos cambios:
  `marcar_registros_encolado(registro_ids, usuario) -> int` (nuevo) y
  extensión de `marcar_registros_sigrid(..., conflictos: list[dict] = [],
  error_global: str | None = None)` para R12/R14 (mapea
  `pendientes_confirmacion[].registros` → `'conflicto'` y, con
  `error_global`, todas las líneas de la petición → `'error'`).
- `static/app.js` — en el modal de aprobación: sin conflictos que pisar →
  botón «Registrar» llama a `/api/aprobar/encolar` y muestra «Encolado: se
  registrará en segundo plano» (o el resultado completo si vino
  `modo:"sincrono"`); el flujo de pisar conflictos sigue llamando a
  `/api/aprobar/ejecutar`. Badges/estilo para `encolado`/`conflicto`/
  `error` donde ya se pinta `sigrid_estado`. Ampliación 2: aviso de poison
  en cabecera + acción de reencolado.
- `templates/base.html` — ampliación 2: hueco del aviso de poison en la
  cabecera común (lo rellena `app.js`).
- `docs/ARCHITECTURE.md` — la frase «sv4→sv5 por HTTP síncrono interno»
  pasa a describir el doble canal: colas `q-transfer`/`q-transfer-result`
  para lotes + HTTP interno para preflight y pisado.
- `azure-apps/partes.md` (repo `azure-apps`, MISMO trabajo) — añadir las
  dos colas y el contenedor `transfer` a lo que el proyecto expone/consume.

## Ficheros que NO se tocan (y podrían tentar)

- `infrastructure/database/orm_models.py` de sv3 y sv4: CERO cambios de
  schema (los estados nuevos son valores de una columna existente).
- `application/services/reglas_registro.py` (sv5): las reglas de negocio
  NO se reescriben. El split de fases (ampliación 1) vive en
  `registro_pipeline.py` moviendo código, no cambiando decisiones: la
  acción calculada por línea, los conflictos y la idempotencia se
  comportan exactamente igual (test de regresión explícito).
- `infrastructure/sigrid/sigrid_write_client.py` (sv5) y los clientes
  Sigrid de sv3/sv4 (duplicación tolerada: no se toca ninguna copia).
- `infrastructure/transfer/transfer_client.py` (sv4): el cliente HTTP
  queda tal cual para preflight/pisado/fallback.
- sv1, sv2, sv3 completos. `infra/create_*.ps1` existentes (la infra nueva
  va en script propio para no reprovisionar).

## Clases/funciones principales (capa hexagonal)

| Elemento | Capa | Responsabilidad |
|---|---|---|
| `ColaCliente`, `BlobCliente`, `credenciales` (sv4 y sv5) | infrastructure | transporte Storage (adaptación del patrón sv3) |
| `TransferQueuePublisher.publicar(payload, usuario) -> peticion_id` (sv4) | infrastructure | blob de petición + mensaje `q-transfer` |
| `construir_handler_transfer(pipeline, blob, cola, settings) -> Callable[[dict], None]` (sv5) | interface_adapters/queue | mensaje → dominio → `pipeline.preparar` + `pipeline.registrar` (el lock lo adquiere `registrar`) → blob+mensaje de resultado |
| `RegistroPipeline.preparar(*, obra, lineas) -> ContextoRegistro` (sv5) | application/pipelines | fase paralela: pasos 1–4 (datos maestros + reglas) |
| `RegistroPipeline.registrar(ctx, *, pisar_claves, usuario) -> ResultadoRegistro` (sv5) | application/pipelines | fase serializada bajo lock: pasos 5–9 |
| `ContextoRegistro` (sv5) | domain/models | contexto preparado entre fases |
| `ColaCliente.contar_aproximado(cola)` / `ColaCliente.mover(origen, destino, maximo=32)` (sv4) | infrastructure | recuento y reencolado de poison (ampliación 2) |
| `GET /api/admin/poison` / `POST /api/admin/poison/reencolar` (sv4) | interface_adapters/web | visibilidad y reencolado manual de poison |
| `construir_handler_resultados(repository, blob) -> Callable[[dict], None]` (sv4) | interface_adapters/workers | mensaje de resultado → `marcar_registros_sigrid` |
| `arrancar_consumidor_resultados(...)` (sv4) / arranque de los hilos (sv5 `main.py`) | punto de entrada | composición; hilos daemon |
| `marcar_registros_encolado`, `marcar_registros_sigrid` extendido (sv4) | infrastructure/database | traza `sigrid_*` idempotente |
| `POST /api/aprobar/encolar` (sv4) | interface_adapters/web | decide asíncrono vs fallback síncrono |

Los handlers se construyen como closures/clases puras que reciben TODOS sus
colaboradores por parámetro: los unit tests los ejercitan con fakes en
memoria, sin red ni BBDD (repositorio de sv4 contra SQLite en memoria,
patrón ya usado en su suite).

## SQL

No aplica: sin cambios de schema ni ficheros SQL nuevos.

## Configuración e infra (resumen)

| Dónde | Clave | Valor |
|---|---|---|
| sv4 y sv5 (Container App) | `COLAS_ACCOUNT_URL` / `BLOBS_ACCOUNT_URL` | endpoints de `stpartespt7m3` (MI `id-partes-dev`, roles ya concedidos) |
| sv4 y sv5 | `COLA_TRANSFER` / `COLA_TRANSFER_RESULT` / `BLOB_TRANSFER` | `q-transfer` / `q-transfer-result` / `transfer` (defaults en código) |
| local | `COLAS_CONNECTION_STRING` / `BLOBS_CONNECTION_STRING` | Azurite (opcional; sin ellas, fallback síncrono) |
| sv5 | `TRANSFER_WORKERS` | nº de hilos consumidores (default 3, mínimo 1) |
| sv5 | escala | sigue `min=1/max=1`, ingress interno; SIN regla KEDA |

## Riesgos

- **Líneas huérfanas en `encolado`** si un mensaje acaba en poison (R9) o
  el hilo consumidor de sv4 muere: el humano las ve por el badge (R15) y
  por el aviso de poison del portal (R23, ampliación 2), y puede reencolar
  manualmente (R24) o reaprobar (seguro por synckey). Sin reencolado
  automático (sigue fuera de alcance).
- **Hilo consumidor dentro de un proceso web** (sv4): debe ser daemon y
  tolerar excepciones sin tumbar uvicorn; el bucle `consumir` ya traga
  excepciones por mensaje. Mismo patrón en sv5 junto a la API.
- **Doble vía de escritura en sv5** (HTTP de pisado + cola): serializada
  por el lock de proceso (R7) — condición necesaria: una sola réplica
  (R16), que ya es restricción dura del servicio.
- **Orden de despliegue**: primero infra (colas/contenedor/env), luego
  sv5, luego sv4 (el orden seguro de `redeploy_partes.ps1` ya cumple
  sv5→sv4). Con el fallback R3, el código nuevo sin infra no rompe nada.
- **Cola de espera del lock vs visibility timeout** (ampliación 1): con
  N workers esperando el lock, un mensaje puede quedar invisible cerca de
  `cola_visibility_s` (600 s) mientras su fase de escritura espera turno.
  Con N=3 y escrituras de segundos hay margen de sobra; si se subiera
  mucho `TRANSFER_WORKERS`, habría que subir el visibility en proporción
  (anotado en settings como comentario).
- **Reencolado manual duplicando mensajes** (ampliación 2, R25): el orden
  send→delete puede duplicar un mensaje si falla en medio; benigno por
  idempotencia (synckey / marcado). Nunca se pierde ninguno, que es la
  propiedad importante.

## Fuera de alcance (explícito)

- KEDA en sv5 (imposible con maxReplicas=1 útil; queda descartado aquí).
- Migrar preflight o pisado de conflictos a la cola.
- Reencolado AUTOMÁTICO de `-poison` (el manual desde el portal SÍ entra:
  ampliación 2, R23–R26); notificaciones push al navegador (el estado se
  ve al recargar, como hoy).
- Modelo de roles en el portal para restringir la acción de reencolado
  (decisión abierta anotada en la ampliación 2).
- Congelar registros aprobados (es F-004) y cualquier cambio de schema.
- Encolar desde sv3 u otros productores; eliminar `TRANSFER_BASE_URL`.
