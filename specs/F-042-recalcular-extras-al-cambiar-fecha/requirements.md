<!-- specs/F-042-recalcular-extras-al-cambiar-fecha/requirements.md -->
# F-042 · Recalcular el reparto normal/extra al cambiar la fecha de un parte — Requisitos

**Servicios: sv4** (publica el recálculo al guardar o deshacer la fecha) y
**sv3** (lo consume y ejecuta su pasada de siempre). sv1, sv2 y sv5 no cambian;
esquema sin cambios. Rigor **crítico** (decide horas que acaban en Sigrid).
Petición del humano (2026-10-09): «en este caso el dia 11 al ser domingo lo puso
como extras, al cambiar el dia, no ha recalculado, sino que ha puesto eso mismo
como extra pero en el dia 1».

## Contexto (verificado el 2026-10-09)

- Parte de la obra 0694: la IA leyó «1/10/26» como 2026-10-11 (domingo); sv3 lo
  repartió como no laborable (bases `horas=0` con `horas_orig` 8,5/9/8,5 y sus
  `extra_auto`). El humano pasó la fecha a 2026-10-01 (jueves) y las líneas
  quedaron con el reparto del domingo.
- El reparto lo calcula SOLO sv3 (`RecursoConciliador.conciliar_todos`, que
  empieza por `revert_extras_auto` y recalcula **todo** lo no congelado de
  todos los partes activos), y solo cuando llega un mensaje a `q-persistencia`.
  sv4 `update_parte_fecha` cambia la fecha del documento y de sus líneas
  (también las `extra_auto`, así que la clave de pareja de F-037 se mantiene) y
  no avisa a nadie.
- Consecuencia: el reparto queda mal **hasta que entra el siguiente parte**
  (esa pasada lo arregla). En esa ventana alguien puede aprobarlo y congelarlo
  con el reparto equivocado. F-042 cierra la ventana.
- Permiso: sv4 usa la identidad `id-partes-dev`, que ya tiene *Storage Queue
  Data Contributor* sobre la cuenta de colas entera (leído con `az role
  assignment list` el 2026-10-09). No hace falta rol nuevo (design §7).

## Glosario

- **Mensaje de recálculo**: mensaje de `q-persistencia` con `tipo:
  "recalcular"` (formato en design §2). El de sv2 de hoy no lleva `tipo`.
- **Estado del recálculo** (respuesta de sv4): `pedido`, `fallo` o `sin_cola`.
- **Congelada**: la regla de hoy (semántica 10 y F-037): sv3 `_congelado`.

## sv4 · pedir el recálculo

- **R1.** CUANDO `PATCH /api/partes/{id}/fecha` guarda la fecha, sv4 debe
  publicar en la cola `COLA_PERSISTENCIA` (por defecto `q-persistencia`) **un**
  mensaje de recálculo con `motivo: "cambio_fecha"`, el `document_id`, el autor
  (`_actor(request)`) y la hora UTC de la petición, y responder con
  `recalculo: "pedido"` además de los campos de hoy.
- **R2.** sv4 debe publicar **después** de que `update_parte_fecha` haya
  confirmado (commit) el cambio, nunca antes.
- **R3.** SI la publicación lanza cualquier excepción, ENTONCES la fecha debe
  quedar guardada, la respuesta debe ser 200 con `recalculo: "fallo"` y sv4 debe
  registrar un WARNING con el `document_id` y el tipo de error.
- **R4.** MIENTRAS sv4 no tenga cola configurada (sin `COLAS_*`), debe guardar la
  fecha, no intentar publicar y responder `recalculo: "sin_cola"`.
- **R5.** SI la fecha es inválida (400), el parte no existe (404) o está
  congelado (409), ENTONCES sv4 NO debe publicar nada.
- **R6.** CUANDO la fecha guardada es igual a la que ya tenía, sv4 debe publicar
  igualmente (volver a guardarla es el reintento manual; DA5).
- **R7.** CUANDO `POST /api/undo` deshace con éxito una entrada `parte_fecha`,
  sv4 debe publicar un recálculo con `motivo: "deshacer_cambio_fecha"` y
  devolver `recalculo` con la semántica de R1, R3 y R4 (DA1).
- **R8.** CUANDO `POST /api/undo` deshace cualquier otra acción, o no deshace
  nada, sv4 NO debe publicar ni añadir `recalculo` a la respuesta.
- **R9.** `undo_last` debe devolver también la `action` de la entrada deshecha.
- **R10.** sv4 debe publicar con el cliente de cola que ya recibe `build_app`
  (`cola_cliente`, el de la gestión de poison); sin él no hay publicador.
- **R11.** El portal debe pintar el estado tras guardar la fecha: `pedido` ⇒
  «✓ Guardado · recalculando extras (recarga en 1–2 min)»; `fallo` ⇒ aviso
  persistente (clase `error`) «Fecha guardada, pero no se pudo pedir el
  recálculo de extras: vuelve a guardar la fecha»; `sin_cola` ⇒ «✓ Guardado
  (sin recálculo automático)». Tras deshacer con `recalculo: "fallo"`, un
  `alert` con el mismo aviso antes de recargar.

## sv3 · consumir el recálculo

- **R12.** El worker de sv3 debe clasificar cada mensaje de `q-persistencia`:
  sin `tipo` (o `tipo` nulo) ⇒ **ingesta**; `tipo == "recalcular"` ⇒
  **recálculo**; cualquier otro valor, o un payload que no sea objeto JSON ⇒
  excepción `MensajeDesconocido` con ERROR en el log.
- **R13.** CUANDO llega un mensaje de ingesta, el worker debe hacer exactamente
  lo de hoy: descargar `input/{document_id}.pdf` y
  `envelopes/{document_id}.json` y ejecutar el pipeline con la misma
  `PersistParteRequest`.
- **R14.** CUANDO llega un mensaje de recálculo, sv3 debe ejecutar
  `conciliar_todos()` del conciliador de recursos **una vez**, sin descargar
  blobs, sin pipeline de ingesta y sin conciliar partidas, y registrar INFO con
  `motivo`, `document_id`, autor y el resumen devuelto.
- **R15.** SI `conciliar_todos()` lanza durante un recálculo, ENTONCES el
  handler debe propagar la excepción (el mensaje no se borra: reintento y, tras
  `max_dequeue`, `q-persistencia-poison`; DA3).
- **R16.** SI `MensajeDesconocido`, ENTONCES el handler debe propagarla sin
  tocar blobs, pipeline ni conciliador (mismo camino de reintento y poison).
- **R17.** MIENTRAS sv3 no tenga Sigrid cableado (sin conciliador), un recálculo
  debe registrar WARNING y darse por consumido sin error.
- **R18.** `build_app` de sv3 debe exponer el conciliador de recursos en
  `app.state.recurso_conciliador` (None sin Sigrid), y `main_worker.py` debe
  usar el handler de R12–R17.

## Resultado del recálculo (sv3, repositorio real sobre SQLite)

- **R19.** CUANDO un parte repartido como domingo no laborable pasa a un jueves
  laborable (sv4 cambia la fecha de documento y líneas) y llega el recálculo,
  sus líneas deben quedar **iguales** que las de ese mismo parte ingerido ya con
  la fecha del jueves: con candef 8, 8,5 h ⇒ 8 + 0,5 extra y 9 h ⇒ 8 + 1 extra,
  sin ninguna `extra_auto` heredada del domingo.
- **R20.** Las líneas congeladas de otro parte del mismo trabajador y día
  (`registrado`, `encolado`, `dedicacion` o parte aprobado) no deben cambiar en
  el recálculo y deben contar en el total del día (con 8 h congeladas, las
  8,5 h del parte movido van enteras a extra).
- **R21.** Dos recálculos seguidos deben dejar las mismas filas que uno (ninguna
  `extra_auto` duplicada).

## Contrato sv4 → sv3

- **R22.** Un test de la raíz debe comprobar que todo mensaje que construye sv4
  (los dos motivos) sv3 lo clasifica como recálculo, que un mensaje con la forma
  del de sv2 lo clasifica como ingesta, que el productor de sv2
  (`services/partes-api/main_worker.py`) no emite `tipo`, y que los dos módulos
  del contrato solo importan la biblioteca estándar.

## Documentación

- **R23.** `docs/ARCHITECTURE.md` (comunicación entre servicios y semántica 3),
  `docs/referencia/partes-proyecto.md` («Cómputo de extras» y diagrama) y
  `azure-apps/partes.md` deben contar que sv4 también publica en
  `q-persistencia` (mensaje «recalcular») y cuándo.

## Fuera de alcance (decisión del humano, 2026-10-09)

- Recalcular al editar horas o tipo, cambiar trabajador u obra, borrar o crear
  líneas, o crear un parte manual: siguen esperando a la siguiente pasada.
- Bloquear la aprobación mientras el recálculo está pendiente (DA4).
- Coalescer recálculos (DA2) y reencolar `q-persistencia-poison` desde el
  portal (la allowlist de F-002 sigue con dos colas).
- La carrera de pasadas concurrentes entre réplicas de sv3 (preexistente;
  design §8).
- Cualquier cambio de `recurso_conciliador.py`, `pareja_extra.py`, la regla de
  congelación, el esquema o la lista cerrada de `CLAUDE.md` (DA6).
