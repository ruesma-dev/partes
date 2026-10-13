<!-- specs/F-043-fecha-del-parte-confirmar-y-recargar/design.md -->
# F-043 · Fecha del parte: rótulo, confirmación y parte «en espera» — Diseño

> **Enmienda 2026-10-13**: cambian §3, §4, §6, §9 y §12 (**DA6 y DA8
> cambiadas; DA10–DA13 nuevas**). §2, §5 y el resto de DA, igual.

## 1. Encaje, límite de servicio y rigor

- **sv4**: rótulo, alcance, confirmación, marca de «pedido», estado, parte en
  espera (vista, guarda y aviso). **sv3**: solo la marca de «terminado» tras la
  pasada de F-042. El reparto sigue siendo exclusivo de sv3.
- **Sin lógica duplicada**: sv4 escribe el pedido y decide el estado; sv3 copia
  el pedido que leyó a «terminado». La lista cerrada de `CLAUDE.md` no crece;
  `congelacion.py` (gemelo de sv3) **no** cambia: la espera es otra guarda.
- Mensaje de F-042 intacto (DA2). **Rigor crítico**: worker de producción,
  esquema de la base `partes` (servidor compartido) y guarda nueva de edición.

## 2. Esquema (`orm_models.py`, las dos copias, byte-idénticas)

En `ParteDocumentOrm`, tras «Dia del parte», un bloque «Seguimiento del
recalculo (F-043)» con quién escribe cada columna:

```python
recalculo_pedido_id: Mapped[str | None] = mapped_column(String(36))        # sv4
recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(64))    # sv4
recalculo_terminado_id: Mapped[str | None] = mapped_column(String(36))     # sv3
recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(64)) # sv3
```

Nullables, sin índice; las genera `ddl_complementario()`; ningún guardián de
F-010/F-015 cambia (no listan las columnas de `parte_documents`).

## 3. sv4 · servidor (`services/partes-front/`)

**Crear** `application/services/seguimiento_recalculo.py` (sin dependencias de
infraestructura): constantes de los cuatro estados, `ESPERA_MAX_S = 600` (DA13),
`estado_seguimiento(pedido_id, terminado_id, pedido_at_utc, ahora: datetime)
-> str` (glosario; un `pedido_at_utc` ilegible cuenta como vencido) y
`class RecalculandoError(CongeladoError)` con el motivo de R38 (subclase: el
manejador 409 de F-004 y los `except CongeladoError` existentes ya la tratan).

**Modificar** `infrastructure/database/parte_repository.py`
(`ParteReviewRepository`):

- `alcance_parte(document_id) -> dict | None` (R2–R4, solo lectura).
- `marcar_recalculo_pedido(document_id, *, peticion_id, ahora_utc) -> bool` y
  `anular_recalculo_pedido(document_id, *, peticion_id) -> None` (R12, R13):
  sin guarda de congelación ni `undo_log`.
- `estados_recalculo(ids: list[str]) -> dict[str, dict]` — una consulta `IN`;
  id ausente o inactivo ⇒ `no_existe` (R17). `documentos_en_espera(ids) ->
  set[str]` — los `pendiente` (R37).
- `_exigir_sin_recalculo(doc)` (función de módulo, reloj `_ahora_utc()`
  parcheable) que lanza `RecalculandoError` si `pendiente`; se llama justo
  después de **cada** `_exigir_reg_editable` / `_exigir_doc_editable` de hoy
  (`crear_extra_desde`, `update_registro`, `set_registro_hora`,
  `set_registro_partida`, `update_parte_obra`, `delete_document`,
  `soft_delete_registro`) **salvo** en `update_parte_fecha` (R38). `undo_last`
  no usa esas guardas: deshacer sigue libre (R38).

`_DOC_UNDO_FIELDS` y `update_parte_fecha` **no cambian** (R34).

**Modificar** `interface_adapters/web/app.py`:

- Closure `_pedir_recalculo_seguido(document_id, motivo, solicitado_por) -> str`
  en `build_app`: con publicador, `pid = str(uuid4())` y
  `marcar_recalculo_pedido` (excepción ⇒ WARNING `[recalculo] no se pudo
  marcar …`); `pedir_recalculo` de F-042 sin cambios; con `fallo` y marca,
  `anular_recalculo_pedido` (excepción ⇒ WARNING). `patch_parte_fecha` y
  `undo_apply` la usan con el `solicitado_por` que ya calculan: `_actor(request)`
  sigue en **17**. Respuestas sin claves nuevas (R16).
- `GET /api/partes/{document_id}/alcance` y `GET /api/recalculo?ids=…`
  (`include_in_schema=False`; ids separados por coma, 1–50, si no 422).
- `obra_detail`, `trabajador_detail` y `parte_detail`: `recalculando =
  repository.documentos_en_espera(<document_id de la vista>)` al contexto
  (R37). Los repositorios de vistas no cambian.

## 4. sv4 · portal (plantillas, `static/app.js`, `static/styles.css`)

**Plantillas**: R1 como se aprobó; además (R37) en las filas de
`obra_detail.html` y `trabajador_detail.html` `{% if r.document_id in
recalculando %} data-recalculando="1"{% endif %}` y una marca
`<span class="recalculando-marca">recalculando…</span>` en la celda de fecha;
en `parte_detail.html`, `data-parte-contenido` + `data-document-id` (+
`data-recalculando`) en el contenedor de cabecera y líneas.

**`app.js`**, en el IIFE principal, funciones puras a dos espacios de sangría
(las ejecuta el test con node, como `empresaSufijo` en F-039):

- Constantes `RECALCULO_SONDEO_MS = 5000`, `RECALCULO_SIN_RESPUESTA_MS = 720000`,
  `VISTA_CLAVE = "partes.vista.restaurar"`, `VISTA_MAX_MS = 60000`.
- Puras: `fmtFechaEs(iso)`; `textoConfirmacionFecha(alcance, vieja, nueva)`
  (R6/R7); `accionPorEstado(estado)` (R25); `vistaRestaurable(guardada, url,
  ahoraMs)` (R21: objeto válido, misma URL, < `VISTA_MAX_MS`).
- `ponerEnEspera(docId, fecha)`: marca y deshabilita los controles de
  `tr[data-document-id=docId]` y `[data-parte-contenido][data-document-id=docId]`
  (guardando cuáles ya estaban `disabled`); `soltarEspera(docId)` los devuelve
  a su estado (R23). `wireBulkSelect` («Seleccionar visibles») salta las filas
  `data-recalculando`.
- `avisoRecalculo`: un contenedor `#recalculo-avisos` (`role="status"`, fijo
  abajo a la derecha, no modal) con una tarjeta por documento: texto, botón
  «Actualizar» cuando procede y «×» para descartarla (R18, R20, R22–R24).
- `vigilarRecalculo(docId, fecha)`: añade el documento al conjunto vigilado y,
  si no hay, arranca **un** temporizador que cada `RECALCULO_SONDEO_MS` pide
  `GET /api/recalculo?ids=…` con todos y aplica `accionPorEstado` a cada uno;
  se para cuando el conjunto queda vacío o tras `RECALCULO_SIN_RESPUESTA_MS`
  sin respuesta válida. **Nunca recarga** (R19, R40). **Punto de entrada F-044.**
- `actualizarVista()` (botón «Actualizar»): guarda la vista (try/catch) y
  recarga; `restaurarVista()` en `DOMContentLoaded`: `vistaRestaurable`,
  `scrollTo`, `scrollTop` de cada contenedor por orden y valor de cada
  `.col-filter` por orden + evento `input` (reaplica el filtro existente).
- `DOMContentLoaded`: `restaurarVista()`, y `ponerEnEspera` + `vigilarRecalculo`
  para cada `data-document-id` con `data-recalculando="1"` (R18, R26).
- `wireFechaInput` (R5–R11, como se aprobó); con `pedido`, `ponerEnEspera` +
  `vigilarRecalculo`; con `fallo`, tarjeta fija (R24). `wireUndo` **no cambia**.
- `estadoRecalculo` y sus textos **no cambian** (los vigila F-042 R11).
- **`styles.css`**: `#recalculo-avisos`, `.recalculo-tarjeta`, `.recalculando-marca`
  y `tr[data-recalculando="1"]` (atenuada), con los tokens de `.alert`.

## 5. sv3 (`services/partes-persistencia/`) — sin cambios por la enmienda

**Crear** `infrastructure/database/recalculo_seguimiento.py`:
`SqlAlchemyRecalculoSeguimiento(session_factory, reloj=<utc now ISO>)` con
`pedido_actual(document_id) -> str | None` y `marcar_terminado(document_id,
peticion_id) -> bool` (`UPDATE parte_documents SET recalculo_terminado_id =
:pid, recalculo_terminado_at_utc = :ahora WHERE id = :doc AND
recalculo_pedido_id = :pid`; True si tocó una fila).

**Modificar** `interface_adapters/workers/despacho.py`
(`construir_handler(..., recalculo_seguimiento: Any = None)`: en `_recalcular`,
tras la guarda de R17 de F-042, lee el pedido (None si falta algo o lanza, con
WARNING), `conciliar_todos()` **sin try**, y si hay pedido marca (WARNING si
lanza; INFO `[sv3-worker] recalculo terminado document_id=%s marcado=%s`);
`interface_adapters/api/app.py` (`app.state.recalculo_seguimiento`) y
`main_worker.py` (lo pasa).

**Por qué es correcto (R32)**: el pedido se confirma antes de publicar y sv3 lo
lee antes de la pasada (READ COMMITTED), que ve la fecha nueva; un pedido más
nuevo no se pisa (UPDATE condicional). Sin relojes comparados.

## 6. Tests (sin red ni BBDD real; datos sintéticos)

- `services/partes-front/tests/test_f043_alcance_y_seguimiento.py` —
  `build_app` sobre `FabricaSesionSqlite` y la `ColaFake` de F-042 (importada):
  R2–R4, R12–R17 (R12 con una cola que lee la marca desde otra sesión al
  enviar), `estado_seguimiento` con reloj fijo (los cuatro estados y el borde
  de 600 s), R37 (HTML de las tres vistas con un documento en espera y otro no).
- `services/partes-front/tests/test_f043_guarda_espera.py` — R38–R39: cada uno
  de los siete métodos da 409 con el motivo sobre un documento `pendiente` y
  funciona con `vencido`/`terminado`/`sin_seguimiento`; `update_parte_fecha` y
  deshacer pasan; un documento ajeno en la misma vista se edita sin trabas.
- `…/tests/test_f043_portal_fecha.py` — R1, R5–R11, R18–R26, R40: puras **con node** (`skipif` sin node),
  cableado de `app.js` (URLs, `window.confirm` en `wireFechaInput`, `location.reload` solo en `actualizarVista`,
  `wireUndo` y los previos —se cuentan—, `restaurarVista` en `DOMContentLoaded`, textos F-042) + `node --check`.
- **Enmienda (opción A del humano, 2026-10-13)**: `test_f042_recalculo_fecha.py::test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo`
  es ADAPTABLE: su doble de DOM gana `window.confirm` (acepta), alcance, `activeElement` y las funciones nuevas;
  cambian el orden de peticiones (alcance, PATCH) y los temporizadores; los textos de `estadoRecalculo`, NO.
- `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py` — adaptador
  sobre SQLite (R28, R32), handler con dobles (R27, R29–R31), R33 por AST.
- `tests/test_f043_contrato_seguimiento.py` (raíz) — R35 y mensaje F-042 intacto.

## 7. Ficheros que NO se tocan

`update_parte_fecha`, `undo_last`, `_DOC_UNDO_FIELDS`, los repositorios de
vistas (`get_obra`, `get_worker`, `get_parte`) y `congelacion.py` de sv4;
`recalculo_publisher.py` (sv4) y `mensajes.py` (sv3); `recurso_conciliador.py`,
`pareja_extra.py` y `sqlalchemy_parte_repository.py` de sv3; `cola_cliente.py`
(las dos) y `main.py` de sv4; sv1, sv2, sv5; `infra/`; `CLAUDE.md`; **todos los tests existentes**
salvo el de la enmienda de §6 (otro que se rompa ⇒ `blocked`).

## 8. Despliegue

Sin variables, roles ni infra nuevos (DDL de arranque). **Orden sv3 → sv4**; con
sv4 antes, un sv3 viejo no marca y el parte espera hasta `vencido` (10 min):
inocuo. `azure-apps/partes.md` (§4.1): commit local en ese repositorio.

## 9. Riesgos y alternativas

- **R-a · Ediciones a mitad de pasada (respuesta a la pregunta del humano)**:
  sv3 revierte y confirma, lee todas las líneas activas, calcula y escribe en
  transacciones posteriores. Una edición confirmada entre su lectura y su
  escritura **se pisa**: horas de una base partida (`apply_extras_splits` pone
  `horas_norm` calculado con las horas viejas), código de hora o categoría
  (`apply_recurso_matches`), o va a una `extra_auto` que el revert ya borró
  (404) o que la siguiente pasada borra. La guarda R38 lo evita para el parte
  en espera; la fecha y deshacer se permiten porque piden otra pasada que lo
  arregla todo.
- **R-g · Vale igual para cualquier otro parte** en cualquier pasada (cada ingesta
  recalcula todo): riesgo **anterior a F-043**; feature aparte si se quiere.
- **R-b** Marca de sv4 fallida (improbable): no hay espera; queda el WARNING.
  **R-c** Pasada parcial (Sigrid a mitad): se marca igual, como hoy. **R-d**
  Reintento de sv3 a los 300 s: cabe en los 10 min. **R-e** `change` al teclear
  en Chromium: DA3 y M2.
- **R-f · Choques de merge con F-044** (`app.js`, plantillas, repositorio,
  `features.json`, `current.md`): mejor integrar F-043 antes.
- **Descartadas**: HTTP sv4→sv3 (sv3 en Azure es solo worker); DA1-B/C/D;
  DA10-B/C; recarga automática (la DA6 anterior, rechazada por el humano).

## 10. Punto de contacto con F-044 (mover una sola línea)

F-044 **no** cambia `.fecha-edit` y añade su acción aparte. Reutiliza
`_pedir_recalculo_seguido` por cada documento afectado, `ponerEnEspera` +
`vigilarRecalculo` por documento, `fmtFechaEs`, el idioma `window.confirm`,
`GET /api/partes/{id}/alcance` y la guarda R38 (sus endpoints de mover línea
deben llamar a `_exigir_sin_recalculo`).

## 11. Verificación MANUAL (humano; solo lectura salvo el despliegue)

- **M1 · tras desplegar sv3 y luego sv4**: `SELECT column_name FROM information_schema.columns WHERE table_name = 'parte_documents' AND column_name LIKE 'recalculo%';` ⇒ 4 filas.
- **M2 · portal (Chrome/Edge)**, vista de obra con dos partes sin congelar:
  teclear la fecha no abre un diálogo por tecla; al salir sale el texto con sus
  N trabajadores; Cancelar restaura; Aceptar ⇒ ese parte «recalculando…» y el
  otro se sigue editando, filtrando y desplazando; a los 1–2 min, tarjeta
  «Actualizar»; al pulsarla, misma posición y filtros con el reparto nuevo.
- **M3 · otra pestaña** con el mismo parte durante la espera ⇒ sale en espera.
- **M4 · base `partes`**: `SELECT recalculo_pedido_id, recalculo_pedido_at_utc, recalculo_terminado_id,
  recalculo_terminado_at_utc FROM parte_documents WHERE id = '<id>';` ⇒ ids iguales.

## 12. Decisiones (las aprobadas el 2026-10-12, salvo las marcadas)

- **DA1–DA5, DA7, DA9 · aprobadas, sin cambios**: marca en `parte_documents`
  sondeada por GET; sv3 marca el pedido que leyó; confirmar al salir del campo
  o con Enter; también en el detalle del parte; rótulo «Fecha del parte»; si sv3
  no puede marcar, WARNING y mensaje consumido; tras error, el input se restaura.
- **DA6 · CAMBIADA · Nada recarga solo**: el parte queda en espera y, al
  terminar, una tarjeta ofrece «Actualizar». Sustituye a «recarga automática
  salvo editando», que interrumpía el trabajo con otros partes.
- **DA8 · CAMBIADA · Deshacer**: conserva su recarga inmediata (la pide el
  usuario, como hoy) y el parte sale en espera porque lo pinta el servidor
  (DA13); desaparece la espera guardada en `sessionStorage`.
- **DA10 · NUEVA · Cómo se ve el parte cuando sv3 termina.** A) tarjeta con
  «Actualizar» que recarga conservando scroll y filtros de columna
  (**recomendada**: la matriz, los totales por día y trabajador y el calendario
  los pinta Jinja y cambian; recargar es el idioma del portal tras cambios
  estructurales). B) pedir de nuevo la página y sustituir en el sitio las filas
  del parte y las celdas de la matriz (DOMParser): habría que volver a cablear
  una decena de editores por elemento y la matriz y el calendario llevan
  escuchas por celda; frágil sin reescribir. C) endpoint JSON y repintar en JS:
  duplica las plantillas. D) refrescar solo las filas, sin totales: deja la
  matriz incoherente.
- **DA11 · NUEVA · El servidor rechaza las ediciones del parte en espera**
  (409), salvo fecha y deshacer (**recomendada**; R-a). Solo en el portal no
  basta: otra pestaña antigua, otro usuario o una acción en bloque saltan el
  bloqueo y la edición se pisa.
- **DA12 · NUEVA · La aprobación no se bloquea** en F-043 (F-042 DA4 sigue;
  **recomendada**): tocarla entra en el flujo de F-022/sv5. Alternativa:
  excluir los partes en espera de toda aprobación (`excluidas.recalculando`).
- **DA13 · NUEVA · La espera la pinta el servidor** (columnas + `ESPERA_MAX_S`
  = 600 s, constante en código) y no el navegador: vale en cualquier pestaña o
  usuario y un parte nunca queda bloqueado más de 10 min (**recomendada**).
