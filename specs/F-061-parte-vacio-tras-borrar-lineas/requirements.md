<!-- specs/F-061-parte-vacio-tras-borrar-lineas/requirements.md -->
# F-061 · Un parte que se queda sin líneas no puede seguir activo — Requisitos

**Servicios tocados: sv4** (`services/partes-front`: borrado, restauración, papelera, listado
y un script de consola) **y sv3** (`services/partes-persistencia`: deduplicación por
sha256). Ni sv1, sv2 ni sv5. **Sigrid no se toca.** Sin cambios de esquema
(`orm_models.py` intactos en los dos). Rigor **estándar** (propuesta en `design.md` §10, DA8).

**Petición del humano**: 2026-10-25, «añade una feature para ver por que no los borro
bien»; 2026-10-26, «si, spec de la siguiente».

**Causa** (`design.md` §2): borrar una línea suelta (`soft_delete_registro`) nunca mira si
el parte se queda sin líneas vivas —el borrado por persona sí lo hace—, y vaciar la papelera
borra físicamente las líneas sueltas sin mirar sus partes. El parte queda `is_active`, sin
`deleted_at_utc` y con 0 líneas, y sv3 (`get_by_sha256` filtra solo `is_active`) descarta
la reingesta del mismo PDF.

## Glosario

- **Línea viva**: `parte_registros.deleted_at_utc IS NULL`.
- **Parte vacío**: `parte_documents.is_active` y **ninguna línea viva** (sin filas, o con
  todas sus filas en la papelera). Es la definición única (ARCHITECTURE semántica 8, DA7).
- **A la papelera (documento)**: `is_active = false`, `deleted_at_utc` = ahora (ISO UTC),
  `deleted_by` = actor. Nunca `DELETE`.
- **Estados que viven fuera**: `registrado`, `dedicacion` (los de `vive_fuera`) y
  `encolado`.

## Requisitos

### sv4 · Un parte que se queda vacío va a la papelera (DA1)

- **R1.** CUANDO `POST /api/registro/{id}/delete` manda a la papelera la última línea viva de
  un parte, sv4 debe mandar ese parte a la papelera **en la misma transacción**, con el
  `deleted_by` del actor, y responder `{"ok": true, "documento_a_papelera": true,
  "document_id": "<id>"}`. Si quedan líneas vivas, `documento_a_papelera` debe ser `false`
  y el parte no se toca.
- **R2.** El borrado por persona (`POST /api/trabajador/{key}/delete`) y el deshacer de una
  edición de celda (`_deshacer_creadas`, F-049) deben aplicar la misma regla con la misma
  función; las líneas congeladas que se omiten (F-004 R13) siguen vivas y su parte no va a
  la papelera.
- **R3.** Antes de mirar si un parte se queda vacío y antes de cambiar sus líneas, sv4 debe
  bloquear su fila de `parte_documents` (`SELECT … FOR UPDATE`; varios partes, por `id`
  ascendente), para que dos borrados simultáneos de las dos últimas líneas (el borrado en
  bloque lanza N peticiones a la vez) no dejen el parte activo y vacío.
- **R4.** El borrado de obra (`soft_delete_obra`) y el de parte (`delete_document`) no
  cambian: ya mandan el documento entero a la papelera.

### sv4 · Vaciar la papelera (DA3)

- **R5.** CUANDO `POST /api/papelera/vaciar` borra líneas sueltas y alguno de sus partes
  activos se queda vacío, sv4 debe mandar ese parte a la papelera (no borrarlo físicamente)
  y devolver su número en `documentos_a_papelera`; el portal debe avisarlo con un mensaje.
  Lo demás de vaciar (omitidos, cascada, F-010 R11) no cambia.

### sv4 · Restaurar (DA2)

- **R6.** Restaurar una línea de un parte que está en la papelera debe seguir devolviéndolo a
  activo (comportamiento actual de `restore_registro`).
- **R7.** CUANDO se restaura un parte (`POST /api/documento/{id}/restore`) y no tiene ninguna
  línea viva, sv4 debe restaurar también todas sus líneas de la papelera; si tiene alguna
  viva, solo el parte (como hoy).
- **R8.** SI al restaurar una línea o un parte existe **otro** parte activo con el mismo
  `source_sha256`, ENTONCES sv4 debe responder 409 `{"ok": false, "error": "<motivo>"}` sin
  escribir nada, y el portal debe enseñar el motivo.

### sv4 · Portal (DA5)

- **R9.** CUANDO se borra desde el detalle de un parte su última línea (una a una o en
  bloque), el portal debe avisar de que el parte ha ido a la papelera y llevar a `/partes`
  en vez de recargar una página que daría 404.
- **R10.** El listado `/partes` debe contar empleados y horas solo con las líneas vivas, y
  marcar con la insignia «Sin líneas» el parte activo sin ninguna línea viva.

### sv3 · La deduplicación no se bloquea con un parte vacío (DA6)

- **R11.** CUANDO llega un PDF cuyo sha256 coincide con un parte activo, vacío y no
  aprobado, sv3 debe mandar ese parte a la papelera (`deleted_by = "sv3-reingesta"`) y
  guardar el nuevo en la **misma transacción**, con la papelera escrita (`flush`) antes de
  insertar (índice único parcial `WHERE is_active`), y dejar un INFO con los dos
  `document_id` (sin nombres ni DNIs).
- **R12.** SI el parte activo con ese sha256 tiene alguna línea viva o está aprobado,
  ENTONCES sv3 debe deduplicar como hoy (`already_existed`, sin escribir).
- **R13.** SI entre la deduplicación y el guardado el parte deja de estar vacío o de estar
  activo, ENTONCES sv3 no debe tocarlo ni insertar, y el resultado debe ser
  `already_existed`.

### sv4 · Limpieza de los existentes (DA4)

- **R14.** El script `services/partes-front/limpiar_partes_vacios.py` debe, sin argumentos,
  **solo leer** (transacción `READ ONLY` en PostgreSQL) y escribir en
  `services/partes-front/logs/` un Markdown y un CSV (UTF-8 BOM, `;`) con, por parte vacío:
  `document_id`, fecha, `obra_codigo`, `created_at_utc`, categoría y, si se excluye, motivo.
  Sin nombres ni DNIs.
- **R15.** Las categorías deben ser `todas_en_papelera` (tiene filas, ninguna viva),
  `sin_filas_leidos` (sin filas y la extracción guardada traía empleados), `sin_filas_nada_leido`
  y `sin_filas_manual` (`source_mime_type = 'manual'`).
- **R16.** Debe excluir (y listar con su motivo) el parte aprobado, el que tenga alguna
  línea —viva o en papelera— en un estado que vive fuera, y el que tenga alguna línea de los
  partes de Sigrid protegidos `PT26/00373`, `PT26/00375` y `PT26/00376` (lista cerrada).
- **R17.** Con `--ejecutar --esperados N` debe abortar sin escribir (código 2) si los
  candidatos no excluidos no son exactamente N; si lo son, mandarlos a la papelera
  (`deleted_by = "F-061-limpieza"`) en una transacción, recomprobando cada uno bajo
  bloqueo. `--ejecutar` sin `--esperados` debe ser un error de uso. Nunca `DELETE`.
- **R18.** El script no debe usar `SessionFactory` (no toca nada a nivel de servidor) ni
  llevar secretos: lee `DATABASE_URL` de la configuración de sv4.

### Generales

- **R19.** La feature no debe añadir ningún borrado físico, ni tocar Sigrid, ni cambiar
  `orm_models.py`, la regla de congelación (sv3 y sv4) ni los demás ficheros de la lista
  cerrada de duplicación.
- **R20.** `docs/ARCHITECTURE.md` (semántica 8 y «Herramientas de consola») y
  `azure-apps/partes.md` (la fila de `source_sha256`) deben describir la regla nueva.

## Fuera de alcance

- Reprocesar los partes limpiados: lo pide el humano reenviando o reencolando, como hoy.
- Que borrar una línea pida a sv3 recalcular el reparto del día (F-042): no cambia.
- Cambiar qué borra físicamente «Vaciar papelera» o «Eliminar» (F-004 R12, F-019 R16).
