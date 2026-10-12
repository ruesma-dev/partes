<!-- specs/F-043-fecha-del-parte-confirmar-y-recargar/requirements.md -->
# F-043 · Fecha del parte: rótulo, confirmación y recarga — Requisitos

**Servicios: sv4** (rótulo, confirmación, marca de «pedido», sondeo y recarga)
y **sv3** (marca de «terminado» tras su pasada); sv1, sv2 y sv5 no cambian.
Esquema: **4 columnas nullables** en `parte_documents` (las dos copias de
`orm_models.py`). Rigor **crítico** (design §1). Humano, 2026-10-12: opción «A»
con recarga automática.

## Contexto (verificado en el código el 2026-10-12)

- Cada fila del detalle de obra y de trabajador lleva un `.fecha-edit` que hace
  `PATCH /api/partes/{id}/fecha`, y `update_parte_fecha` mueve el **parte
  entero**: el humano quiso mover a un trabajador y movió a los cuatro. El
  detalle del parte usa el mismo input y PATCH; no hay más llamadas a él.
- El recálculo de F-042 tarda ~1–2 min (KEDA en frío); en las filas no hay
  `data-status`, así que su aviso **no se ve**, y nada recarga. sv4 no sabe
  cuándo termina sv3: la cola borra el mensaje y la pasada no deja rastro (DA1).
- El portal confirma con `window.confirm` (obra en bloque, papelera, jornadas);
  los modales propios son del registro en Sigrid.

## Glosario

- **Alcance del parte**: trabajadores (claves `worker_key_for_registro`
  distintas) y líneas activas (`deleted_at_utc` NULL) del documento.
- **Seguimiento**: `recalculo_pedido_id` (sv4) y `recalculo_terminado_id` (sv3)
  del documento. **Estado**: `pendiente` (pedido no nulo y distinto de
  terminado), `terminado` (iguales), `sin_seguimiento` (pedido nulo).
- **Editando**: foco en un `input`/`select`/`textarea` que no sea `.fecha-edit`,
  un modal abierto (`body.modal-open`) o líneas seleccionadas (`PartidaSel`).

## sv4 · rótulo

- **R1.** En `obra_detail.html` y `trabajador_detail.html` la cabecera debe
  decir «Fecha del parte» con `title` «Es la fecha del PARTE: cambiarla mueve
  todas sus líneas y trabajadores»; los `.fecha-edit` de esas dos y de
  `parte_detail.html`, ese `title` y `aria-label="Fecha del parte"` (DA5).

## sv4 · alcance

- **R2.** `GET /api/partes/{id}/alcance` debe responder 200 con `{ok: true,
  document_id, fecha, trabajadores, lineas}` según el glosario.
- **R3.** SI el parte no existe o no está activo, ENTONCES 404. **R4.** El
  alcance no debe escribir nada (ni `undo_log` ni el documento).

## sv4 · confirmación (`static/app.js`)

- **R5.** CUANDO el usuario fija en un `.fecha-edit` una fecha no vacía y
  distinta de la guardada, el portal debe pedir el alcance y mostrar
  `window.confirm` con el texto de R6 **antes** de llamar al PATCH. Disparo:
  `change` si el input no tiene el foco; si lo tiene, al perderlo o con Enter
  (DA3). En las tres plantillas (DA4).
- **R6.** `textoConfirmacionFecha(alcance, vieja, nueva)` (fechas `dd/mm/aaaa`):
  con N ≥ 2 «Vas a cambiar la fecha del PARTE entero: sus N trabajadores (M
  líneas) pasan del D1 al D2. ¿Seguro?»; con N = 1 «… su único trabajador (M
  líneas) pasa del D1 al D2. ¿Seguro?»; con N = 0 «El parte no tiene líneas
  activas; su fecha pasa del D1 al D2. ¿Seguro?». «1 línea» en singular.
- **R7.** SI el alcance falla (red o HTTP ≠ 200), ENTONCES el texto debe ser «Vas
  a cambiar la fecha del PARTE entero (todas sus líneas y trabajadores) al D2. ¿Seguro?».
- **R8.** CUANDO el usuario cancela, el input vuelve a la fecha guardada y no se envía nada.
- **R9.** SI el PATCH falla, ENTONCES el input debe volver a la fecha guardada,
  conservando el motivo del servidor en el estado y el `title` (F-004 R16; DA9).
- **R10.** CUANDO el PATCH tiene éxito, la fecha guardada pasa a ser la nueva en
  ese input y en sus hermanos del mismo documento.
- **R11.** MIENTRAS haya una confirmación o un PATCH en curso de ese input, no
  debe abrirse otra (el `blur` que provoca el propio diálogo no cuenta).

## sv4 · seguimiento (servidor)

- **R12.** CUANDO sv4 va a pedir un recálculo (guardar fecha o deshacer
  `parte_fecha`) con publicador, debe escribir en el documento un
  `recalculo_pedido_id` nuevo (uuid4) y su `_at_utc`, con commit **antes** de publicar.
- **R13.** SI la publicación devuelve `fallo`, ENTONCES sv4 debe poner a NULL
  esas dos columnas solo si siguen siendo las suyas.
- **R14.** SI escribir o anular la marca lanza, ENTONCES WARNING `[recalculo]`
  con `document_id` y tipo de error, y la petición sigue como en F-042.
- **R15.** MIENTRAS no haya publicador (`sin_cola`), sv4 no debe escribir marca.
- **R16.** Las respuestas de `PATCH …/fecha` y `POST /api/undo` no deben ganar
  ni perder claves respecto a F-042, ni el mensaje de recálculo cambiar.
- **R17.** `GET /api/partes/{id}/recalculo` debe responder `{ok: true, estado,
  pedido_at_utc, terminado_at_utc}` (glosario), 404 si no existe; sin escribir.

## sv4 · espera y recarga (`static/app.js`)

- **R18.** CUANDO el PATCH responde `recalculo: "pedido"`, el portal debe
  mostrar un aviso global «Recalculando extras del parte… la página se
  recargará sola al terminar (suele tardar 1–2 min).» y sondear R17 cada 5 s.
- **R19.** CUANDO todos los documentos esperados están `terminado` y no se está
  editando, el portal debe borrar la espera guardada y recargar.
- **R20.** MIENTRAS estén `terminado` y se esté editando, el aviso debe decir
  «Extras recalculadas.» con botón «Recargar», y reevaluarse en cada sondeo.
- **R21.** SI a los 5 min no han terminado, ENTONCES deja de sondear y fija el
  aviso «El recálculo de extras está tardando más de lo normal. Recarga la
  página dentro de unos minutos; si las extras no cambian, vuelve a guardar la fecha.»
- **R22.** SI algún documento da `sin_seguimiento`, ENTONCES deja de sondear y
  el aviso dice «✓ Guardado · recalculando extras (recarga en 1–2 min)».
- **R23.** Un sondeo con error de red o 5xx no corta la espera (cuenta para el plazo); un 404 la corta y retira el aviso.
- **R24.** CUANDO el PATCH responde `recalculo: "fallo"`, además del estado de
  F-042 el aviso global debe mostrar fijo su texto de fallo (en las filas no
  hay `data-status`). `sin_cola` no sondea ni avisa más que hoy.
- **R25.** La espera (`{ids, desde}`) debe guardarse en `sessionStorage` al
  empezar y borrarse al terminar, agotarse o cortarse. Al cargar una página,
  `esperaReanudable` debe reanudarla con el plazo restante solo si algún id está
  en la página (`[data-document-id]`) y no ha vencido; si no, la descarta.
- **R26.** CUANDO deshacer responde `ok` con `recalculo: "pedido"` y
  `document_ids`, el portal debe guardar la espera antes de recargar (DA8). Sin
  `sessionStorage` disponible, recarga sin espera, como en F-042.

## sv3 · marca de terminado

- **R27.** CUANDO llega un recálculo con conciliador y seguimiento cableados,
  sv3 debe leer `recalculo_pedido_id` del documento **antes** de la pasada.
- **R28.** CUANDO `conciliar_todos()` termina sin excepción y el pedido leído no
  es nulo, sv3 debe escribir `recalculo_terminado_id = <ese pedido>` y
  `recalculo_terminado_at_utc` **solo si** el documento sigue con ese pedido.
- **R29.** SI `conciliar_todos()` lanza, ENTONCES no marca y propaga (F-042 R15).
- **R30.** SI leer o marcar lanza, ENTONCES WARNING `[sv3-worker]` y el mensaje
  se da por consumido (DA7); si falla leer, la pasada se hace sin marcar.
- **R31.** MIENTRAS falte el seguimiento, el conciliador (F-042 R17) o un
  `document_id` de texto, sv3 no lee ni marca: comportamiento de F-042.
- **R32.** Con un pedido más nuevo escrito durante la pasada, el viejo no se
  marca; repetir el mensaje es idempotente; procesarlos desordenados nunca deja
  `terminado` un pedido posterior al inicio de la pasada.
- **R33.** `build_app` de sv3 debe exponer `app.state.recalculo_seguimiento` y
  `main_worker.py` pasarlo a `construir_handler`.

## Esquema y contrato

- **R34.** `parte_documents` gana `recalculo_pedido_id`, `recalculo_terminado_id`
  (`String(36)`), `recalculo_pedido_at_utc` y `recalculo_terminado_at_utc`
  (`String(64)`), nullables, en las dos copias byte-idénticas; `ddl_complementario()`
  las añade; no entran en `_DOC_UNDO_FIELDS` (deshacer no las restaura).
- **R35.** Un test de la raíz debe comprobar que las dos copias declaran las 4
  columnas nullables, que el adaptador de sv3 y el repositorio de sv4 usan esos
  nombres y que `_DOC_UNDO_FIELDS` no las contiene.

## Documentación

- **R36.** `docs/ARCHITECTURE.md` (semánticas 3 y 7), `partes-proyecto.md` (§5
  y «Cómputo de extras») y `azure-apps/partes.md` (§4.1 y nota de F-042) deben
  contar las columnas, quién escribe cada una y los dos endpoints nuevos.

## Fuera de alcance

- Mover **una** línea o trabajador a otra fecha: **F-044** (reutiliza la
  confirmación y la espera; design §10).
- Cambiar el recálculo de sv3 (sigue recalculando todo), bloquear la aprobación
  mientras dura (F-042 DA4), esperar recálculos de otras ediciones, reintentar
  desde el aviso o reencolar la poison.
