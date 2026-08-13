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
2. **sv5 consume en un hilo del MISMO proceso/réplica que la API** (no un
   Container App worker aparte con KEDA). Motivos: (a) la restricción dura
   maxReplicas=1 — un worker separado sumaría una segunda instancia
   escribiendo en paralelo con el HTTP de pisado; (b) el HTTP de
   preflight/pisado exige min=1, así que KEDA 0→1 no ahorra nada; (c) el
   lock de proceso (R7) solo protege si API y consumidor comparten proceso.
   KEDA queda explícitamente fuera para sv5.
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
  `test_f002_cola_cliente.py`, con dobles (fakes de cola/blob/pipeline).

### sv4 — `services/partes-front/`
- `infrastructure/azure/__init__.py`
- `infrastructure/azure/cola_cliente.py`, `blob_cliente.py`,
  `credenciales.py` — misma adaptación que en sv5.
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
  `tests/test_f002_aprobar_encolar.py` (la suite del servicio ya existe).

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
  `cola_visibility_s` (600), `cola_max_dequeue` (5). Todas opcionales:
  sin ellas, sv5 arranca como hoy (solo HTTP).
- `main.py` — composición en el punto de entrada: crea `Settings`,
  `SigridWriteClient`, `RegistroPipeline` y un `threading.Lock`
  compartido; si hay storage configurado, arranca el hilo consumidor
  (`transfer_consumer`) antes de `uvicorn.run`; pasa pipeline y lock a
  `build_app`.
- `interface_adapters/api/app.py` — `build_app(settings, pipeline=None,
  lock=None)`: acepta pipeline y lock inyectados (si `None`, los construye
  como hoy — retrocompatible); los endpoints `ejecutar` (y solo ese;
  preflight no escribe) toman el lock antes de llamar al pipeline.

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
  `error` donde ya se pinta `sigrid_estado`.
- `docs/ARCHITECTURE.md` — la frase «sv4→sv5 por HTTP síncrono interno»
  pasa a describir el doble canal: colas `q-transfer`/`q-transfer-result`
  para lotes + HTTP interno para preflight y pisado.
- `azure-apps/partes.md` (repo `azure-apps`, MISMO trabajo) — añadir las
  dos colas y el contenedor `transfer` a lo que el proyecto expone/consume.

## Ficheros que NO se tocan (y podrían tentar)

- `infrastructure/database/orm_models.py` de sv3 y sv4: CERO cambios de
  schema (los estados nuevos son valores de una columna existente).
- `application/pipelines/registro_pipeline.py` y
  `application/services/reglas_registro.py` de sv5: el pipeline de
  registro no cambia; solo gana un transporte.
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
| `construir_handler_transfer(pipeline, lock, blob, cola, settings) -> Callable[[dict], None]` (sv5) | interface_adapters/queue | mensaje → dominio → `pipeline.ejecutar` bajo lock → blob+mensaje de resultado |
| `construir_handler_resultados(repository, blob) -> Callable[[dict], None]` (sv4) | interface_adapters/workers | mensaje de resultado → `marcar_registros_sigrid` |
| `arrancar_consumidor_resultados(...)` (sv4) / arranque del hilo (sv5 `main.py`) | punto de entrada | composición; hilos daemon |
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
| sv5 | escala | sigue `min=1/max=1`, ingress interno; SIN regla KEDA |

## Riesgos

- **Líneas huérfanas en `encolado`** si un mensaje acaba en poison (R9) o
  el hilo consumidor de sv4 muere: el humano las ve por el badge (R15) y
  reaprueba (seguro por synckey). Sin reencolado automático en esta feature
  (fuera de alcance); el poison se vigila como en sv2/sv3.
- **Hilo consumidor dentro de un proceso web** (sv4): debe ser daemon y
  tolerar excepciones sin tumbar uvicorn; el bucle `consumir` ya traga
  excepciones por mensaje. Mismo patrón en sv5 junto a la API.
- **Doble vía de escritura en sv5** (HTTP de pisado + cola): serializada
  por el lock de proceso (R7) — condición necesaria: una sola réplica
  (R16), que ya es restricción dura del servicio.
- **Orden de despliegue**: primero infra (colas/contenedor/env), luego
  sv5, luego sv4 (el orden seguro de `redeploy_partes.ps1` ya cumple
  sv5→sv4). Con el fallback R3, el código nuevo sin infra no rompe nada.

## Fuera de alcance (explícito)

- KEDA en sv5 (imposible con maxReplicas=1 útil; queda descartado aquí).
- Migrar preflight o pisado de conflictos a la cola.
- Reencolado/gestión automática de `-poison`; notificaciones push al
  navegador (el estado se ve al recargar, como hoy).
- Congelar registros aprobados (es F-004) y cualquier cambio de schema.
- Encolar desde sv3 u otros productores; eliminar `TRANSFER_BASE_URL`.
