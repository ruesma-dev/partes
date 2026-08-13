<!-- specs/F-002-cola-q-transfer/requirements.md -->
# F-002 · Cola q-transfer para aprobación asíncrona — Requisitos (EARS)

Contexto: hoy sv4 registra en Sigrid llamando a sv5 por HTTP síncrono
(`/api/registro/ejecutar`) con timeout de 120 s. Para lotes grandes (obra ×
mes completos) eso bloquea al usuario y roza los cortes del balanceador. La
feature introduce la cola `q-transfer` (aprobación asíncrona) y la cola de
retorno `q-transfer-result` (traza del resultado por línea), manteniendo el
HTTP donde hace falta respuesta inmediata: preflight y confirmación de
conflictos en el modal.

Convención de tests: cada requisito Rn tiene al menos un test trazable
`test_f002_rN_...`. Los unit tests NO tocan red ni BBDD (dobles, fixtures,
SQLite en memoria).

## Publicación (sv4)

- **R1** (evento). CUANDO el usuario confirma en el modal una aprobación SIN
  conflictos que pisar (`pisar_claves` vacío) Y las colas están configuradas,
  sv4 debe publicar la petición de registro en `q-transfer` (payload completo
  en blob `transfer/peticiones/<peticion_id>.json`, mensaje con la
  referencia) y responder al navegador `{ok, modo:"asincrono", peticion_id,
  encoladas:N}` sin esperar al registro en Sigrid.

- **R2** (evento). CUANDO sv4 encola una petición, debe marcar cada línea
  incluida con `sigrid_estado='encolado'` (y `sigrid_motivo=NULL`) en
  `parte_registros`, antes de responder al navegador.

- **R3** (opcional). DONDE las colas NO estén configuradas (sv4 sin
  `COLAS_CONNECTION_STRING` ni `COLAS_ACCOUNT_URL`), el endpoint de
  aprobación debe ejecutar el registro por HTTP síncrono contra sv5 como
  hasta ahora y devolver el resultado completo en la misma respuesta
  (`modo:"sincrono"`). Es la vía de retro-compatibilidad y de trabajo en
  local sin Azurite.

- **R4** (ubicuo). El preflight de aprobación (`/api/aprobar/preflight` →
  sv5 `/api/registro/preflight`) debe seguir siendo una llamada HTTP
  síncrona: el modal necesita la respuesta inmediata.

- **R5** (evento). CUANDO el usuario confirma pisar conflictos en el modal
  (`pisar_claves` NO vacío), sv4 debe ejecutar el registro por HTTP síncrono
  (como hoy: `/api/aprobar/ejecutar` → sv5 `/api/registro/ejecutar`) y
  trazar el resultado en `parte_registros` en la misma petición. Pisar nunca
  viaja por la cola.

## Consumo (sv5)

- **R6** (evento). CUANDO llega un mensaje a `q-transfer`, sv5 debe
  descargar la petición del blob referenciado, ejecutar el pipeline de
  registro con `pisar_claves` vacío y publicar el resultado por línea en
  `q-transfer-result` (resultado completo en blob
  `transfer/resultados/<peticion_id>.json`, mensaje con la referencia).

- **R7** (estado). MIENTRAS haya una escritura en Sigrid en curso (vía HTTP
  o vía cola), sv5 debe serializar cualquier otra ejecución del pipeline de
  escritura mediante un lock de proceso: nunca dos escrituras concurrentes
  dentro de la réplica única (`MAX(ide)+1` exige serialización).

- **R8** (error). SI un mensaje de `q-transfer` se reentrega (semántica
  at-least-once), ENTONCES el reproceso no debe duplicar líneas en Sigrid:
  las ya escritas se detectan por synckey y se reportan como
  `ya_registradas` en el resultado.

- **R9** (error). SI el handler de un mensaje falla, ENTONCES sv5 no debe
  borrar el mensaje (reaparece tras el visibility timeout) y, superado
  `max_dequeue` reintentos, debe moverlo a `q-transfer-poison` sin borrar el
  blob de petición.

- **R10** (error). SI el pipeline detecta conflictos al ejecutar desde la
  cola, ENTONCES las líneas afectadas deben quedar SIN escribir en Sigrid y
  reportarse en el resultado como `pendientes_confirmacion` (con sus
  `registro_id`): la confirmación de pisado es siempre humana y síncrona
  (R5).

- **R11** (ubicuo). sv5 no debe tener conexión ni credencial de PostgreSQL:
  sigue sin BBDD; su única traza de vuelta es la cola de resultados.

## Retorno de resultados (sv4)

- **R12** (evento). CUANDO llega un mensaje a `q-transfer-result`, sv4 debe
  actualizar las columnas `sigrid_*` de `parte_registros`: `escritas` →
  `sigrid_estado='registrado'` con `sigrid_hmoide`, `sigrid_hmores_ide` y
  `sigrid_parte_cod`; `omitidas` → `'omitido'` con `sigrid_motivo`;
  `ya_registradas` → `'registrado'`; `pendientes_confirmacion` →
  `'conflicto'` con motivo descriptivo.

- **R13** (error). SI un mensaje de `q-transfer-result` se reentrega,
  ENTONCES aplicar la actualización dos veces debe dejar exactamente el
  mismo estado (idempotencia del marcado).

- **R14** (error). SI el resultado llega con `ok=false` (fallo global del
  pipeline en sv5), ENTONCES sv4 debe dejar las líneas de la petición en
  `sigrid_estado='error'` con el motivo, para que el humano pueda reaprobar
  (reaprobar es seguro por synckey).

## Portal (UI)

- **R15** (estado). MIENTRAS existan líneas con `sigrid_estado` en
  `('encolado','conflicto','error')`, el portal debe distinguirlas
  visualmente de `'registrado'`/`'omitido'` en las vistas que hoy muestran
  el estado Sigrid. La verificación de renderizado es
  `node --check static/app.js` + comprobación MANUAL en navegador; el mapeo
  estado→etiqueta se cubre con test unitario si vive en Python.

## Despliegue (infra — verificación MANUAL del humano)

- **R16** (ubicuo). sv5 debe mantenerse en `min-replicas=1 / max-replicas=1`
  (réplica única por `MAX(ide)+1` con UPDLOCK) y conservar su ingress
  interno para el HTTP de preflight/pisado. NO se añade regla KEDA a sv5.

- **R17** (ubicuo). Las colas `q-transfer`, `q-transfer-result` (y sus
  `-poison`) y el contenedor blob `transfer` deben existir en
  `stpartespt7m3`; sv4 y sv5 acceden con la managed identity existente
  (`id-partes-dev`, roles de Storage ya concedidos en Fase 1).
