<!-- specs/F-043-fecha-del-parte-confirmar-y-recargar/requirements.md -->
# F-043 · Fecha del parte: rótulo, confirmación y parte «en espera» — Requisitos

**sv4** (rótulo, confirmación, marca de «pedido», parte en espera, aviso) y
**sv3** (marca de «terminado»); 4 columnas nullables en `parte_documents`; rigor
**crítico** (design §1). **Enmienda 2026-10-13** («tengo que seguir usando la
plataforma para el resto de partes, solo queda en espera el que está
recalculando»): cambian R17–R26, entran R37–R40 (**[enmienda]**).

## Contexto (verificado en el código el 2026-10-12/13)

- El `.fecha-edit` de cada fila (obra, trabajador) y del detalle del parte hace
  `PATCH /api/partes/{id}/fecha`, que mueve el **parte entero**. El recálculo
  de F-042 tarda ~1–2 min y sv4 no sabe cuándo termina (DA1).
- Una pasada de sv3 revierte (commit), **lee** todas las líneas, calcula y
  **escribe** después (`apply_extras_splits`, `apply_recurso_matches`): una
  edición confirmada entre la lectura y la escritura **se pisa** (horas de la
  base, código de hora) o cae sobre una `extra_auto` ya borrada (design §9).
- El portal confirma con `window.confirm` y, tras cambios estructurales, recarga entero.

## Glosario

- **Alcance del parte**: trabajadores (`worker_key_for_registro` distintas) y
  líneas activas (`deleted_at_utc` NULL) del documento.
- **Estado del seguimiento** (`recalculo_pedido_id` de sv4, `recalculo_terminado_id`
  de sv3, `recalculo_pedido_at_utc`): `sin_seguimiento` (pedido nulo),
  `terminado` (iguales), `vencido` (distintos y el pedido tiene más de
  `RECALCULO_ESPERA_MAX_S`, por defecto 600 s), `pendiente` (distintos, en
  plazo). **En espera** = `pendiente`. **[enmienda]**

## sv4 · rótulo, alcance y confirmación (sin cambios)

- **R1.** En `obra_detail.html` y `trabajador_detail.html` la cabecera debe
  decir «Fecha del parte» con `title` «Es la fecha del PARTE: cambiarla mueve
  todas sus líneas y trabajadores»; los `.fecha-edit` de esas dos y de
  `parte_detail.html`, ese `title` y `aria-label="Fecha del parte"` (DA5).
- **R2.** `GET /api/partes/{id}/alcance` debe responder 200 con `{ok: true,
  document_id, fecha, trabajadores, lineas}` según el glosario.
- **R3.** SI el parte no existe o no está activo, ENTONCES 404. **R4.** El
  alcance no debe escribir nada (ni `undo_log` ni el documento).
- **R5.** CUANDO el usuario fija en un `.fecha-edit` una fecha no vacía y
  distinta de la guardada, el portal debe pedir el alcance y mostrar
  `window.confirm` con el texto de R6 **antes** del PATCH. Disparo: `change` sin
  foco; con foco, al perderlo o con Enter (DA3). En las tres plantillas (DA4).
- **R6.** `textoConfirmacionFecha(alcance, vieja, nueva)` (fechas `dd/mm/aaaa`):
  N ≥ 2 «Vas a cambiar la fecha del PARTE entero: sus N trabajadores (M líneas)
  pasan del D1 al D2. ¿Seguro?»; N = 1 «… su único trabajador (M líneas) pasa
  del D1 al D2. ¿Seguro?»; N = 0 «El parte no tiene líneas activas; su fecha
  pasa del D1 al D2. ¿Seguro?». «1 línea» en singular.
- **R7.** SI el alcance falla, ENTONCES el texto debe ser «Vas a cambiar la
  fecha del PARTE entero (todas sus líneas y trabajadores) al D2. ¿Seguro?».
- **R8.** CUANDO el usuario cancela, el input vuelve a la fecha guardada y no se envía nada.
- **R9.** SI el PATCH falla, ENTONCES el input vuelve a la fecha guardada con el
  motivo del servidor en el estado y el `title` (F-004 R16; DA9).
- **R10.** CUANDO el PATCH tiene éxito, la nueva fecha es la guardada en él y sus hermanos.
- **R11.** MIENTRAS haya una confirmación o un PATCH en curso de ese input, no
  debe abrirse otra (el `blur` que provoca el propio diálogo no cuenta).

## sv4 · seguimiento y parte en espera (servidor)

- **R12.** CUANDO sv4 va a pedir un recálculo (guardar fecha o deshacer
  `parte_fecha`) con publicador, debe escribir en el documento un
  `recalculo_pedido_id` nuevo (uuid4) y su `_at_utc`, con commit **antes** de publicar.
- **R13.** SI publicar da `fallo`, ENTONCES sv4 pone a NULL esas columnas si siguen siendo suyas.
- **R14.** SI escribir o anular la marca lanza, ENTONCES WARNING `[recalculo]`
  con `document_id` y tipo de error, y la petición sigue como en F-042.
- **R15.** MIENTRAS no haya publicador (`sin_cola`), sv4 no debe escribir marca.
- **R16.** Las respuestas de `PATCH …/fecha` y `POST /api/undo` no deben ganar
  ni perder claves respecto a F-042, ni el mensaje de recálculo cambiar.
- **R17. [enmienda]** `GET /api/recalculo?ids=a,b,…` (1–50 ids) debe responder
  `{ok: true, estados: {id: {estado, pedido_at_utc, terminado_at_utc}}}` con el
  estado del glosario y `no_existe` para un id desconocido o inactivo; 0 o más
  de 50 ids ⇒ 422; sin escribir nada.
- **R37. [enmienda]** Las vistas de obra, trabajador y parte deben pintar con
  `data-recalculando="1"` y la marca «recalculando…» las filas (y, en el
  detalle del parte, el contenedor `[data-parte-contenido]`) de los documentos
  en espera, sea cual sea la pestaña o el usuario.
- **R38. [enmienda]** MIENTRAS un documento está en espera, sv4 debe rechazar
  con 409 `{ok: false, congelado: true, error: "El parte se está recalculando
  (extras): espera a que termine."}` toda edición que pase por
  `_exigir_reg_editable` o `_exigir_doc_editable`, **salvo** `update_parte_fecha`
  y deshacer (las dos piden su propio recálculo; DA11).
- **R39. [enmienda]** Un documento `vencido`, `terminado` o `sin_seguimiento` se
  edita como hoy; la regla de congelación (F-004) no cambia.

## sv4 · espera y aviso (`static/app.js`) **[enmienda]**

- **R18.** CUANDO el PATCH responde `recalculo: "pedido"`, o al cargar una página
  con filas `data-recalculando="1"`, el portal debe marcar en espera **solo**
  ese parte (deshabilitar `input`, `select`, `textarea` y `button` de sus filas
  y de `[data-parte-contenido]`, marca «recalculando…», fuera de «Seleccionar
  visibles»), mostrar un aviso no modal y descartable «Recalculando extras del
  parte del D (suele tardar 1–2 min). Puedes seguir trabajando con el resto.» y
  sondear R17 cada 5 s con todos los documentos en espera en una petición.
- **R19.** El resto de la página debe seguir usable: ningún modal, ninguna
  recarga automática, sin tocar foco, scroll, filtros ni selección.
- **R20.** CUANDO un documento pasa a `terminado`, sus filas deben mostrar
  «recalculado · pulsa Actualizar» (siguen deshabilitadas: sus datos están
  viejos) y el aviso «Extras del parte del D recalculadas.» con un botón
  «Actualizar» (DA10).
- **R21.** CUANDO el usuario pulsa «Actualizar», el portal debe guardar en
  `sessionStorage` la vista (URL, scroll de la ventana y de cada `.table-scroll`
  y `.matrix-scroll`, valores de `.col-filter`) y recargar; al cargar,
  `vistaRestaurable` debe devolverla solo si es la misma URL y tiene < 60 s, y
  el portal restaurarla y borrarla. Sin `sessionStorage`, recarga sin más.
- **R22.** CUANDO un documento da `vencido`, deja de sondearlo y su aviso queda
  fijo: «No se ha podido confirmar el recálculo de extras del parte del D.
  Pulsa Actualizar; si las extras no cambian, vuelve a guardar la fecha.»
- **R23.** CUANDO da `sin_seguimiento`, se desmarca y el aviso dice «✓ Guardado ·
  recalculando extras (recarga en 1–2 min)»; con `no_existe`, se desmarca y se
  deja de sondear. Un sondeo con error de red o 5xx no corta nada; tras 12 min
  sin respuesta válida, deja de sondear con el aviso de R22.
- **R24.** CUANDO el PATCH da `recalculo: "fallo"`, el aviso fija el texto de fallo de F-042.
- **R25.** `accionPorEstado(estado)` debe dar `esperar` (pendiente o error),
  `terminado`, `vencido`, `soltar` (sin_seguimiento) o `quitar` (no_existe).
- **R26.** Deshacer mantiene su recarga inmediata (la pide el usuario, como
  hoy); tras ella el parte sale en espera por R37 (DA8).
- **R40.** Ninguna recarga de página debe producirse sin un clic del usuario.

## sv3 · marca de terminado (sin cambios)

- **R27.** CUANDO llega un recálculo con conciliador y seguimiento, sv3 debe leer
  `recalculo_pedido_id` del documento **antes** de la pasada.
- **R28.** CUANDO `conciliar_todos()` termina sin excepción con pedido leído, sv3
  debe escribir `recalculo_terminado_id` = ese pedido (y su `_at_utc`) **solo
  si** el documento sigue con ese pedido. **R29.** SI la pasada lanza, no marca y propaga.
- **R30.** SI leer o marcar lanza, ENTONCES WARNING `[sv3-worker]` y el mensaje
  se consume (DA7); si falla leer, la pasada se hace sin marcar.
- **R31.** Sin seguimiento, conciliador o `document_id` de texto: F-042 intacto.
- **R32.** Un pedido más nuevo escrito durante la pasada no se marca; repetir el
  mensaje es idempotente; el desorden nunca marca un pedido posterior.
- **R33.** sv3 expone `app.state.recalculo_seguimiento` y `main_worker.py` lo pasa.

## Esquema, contrato y documentación

- **R34.** `parte_documents` gana `recalculo_pedido_id`, `recalculo_terminado_id`
  (`String(36)`) y sus `_at_utc` (`String(64)`), nullables, en las dos copias;
  no entran en `_DOC_UNDO_FIELDS`. **R35.** Un test de la raíz lo comprueba y
  que el adaptador de sv3 y el repositorio de sv4 usan esos nombres.
- **R36.** `ARCHITECTURE.md` (semánticas 3, 7, 10), `partes-proyecto.md` (§5,
  «Cómputo de extras») y `azure-apps/partes.md` (§4.1) cuentan columnas, autores,
  parte en espera y endpoints.

## Fuera de alcance

- Mover **una** línea o trabajador a otra fecha: **F-044** (design §10).
- Cambiar el recálculo de sv3; bloquear la aprobación del parte en espera
  (DA12); proteger de la pasada las ediciones de **otros** partes (riesgo
  previo, design §9 R-g); refrescar filas en el sitio sin recargar (DA10-B).
