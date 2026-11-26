<!-- specs/F-084-partes-con-problemas/requirements.md -->
# F-084 · Pestaña de partes con problemas — requisitos (EARS)

## Contexto

Petición del humano (2026-11-26): «los partes no leidos o no casados o con problemas deben
quedar visitables en una pestaña nueva para, como pasa en conciliar, conciliarlos con las
obras o fecha etc.».

Caso de origen (0692, correo del 2026-11-26 09:56Z, PDF de 6 páginas, una por parte): la
página 4 (documento `5c1a9b04`, parte del 25/11) se leyó con fecha 23/11; la página 6
(`89f17181`, el 23/11 de verdad, misma obra y mismos trabajadores) entró 1 min 39 s después y
el reemplazo de sv3 (`_deactivate_same_day_obra`, «comparten trabajador -> reemplazo») dejó la
página 4 con `is_active = false` y `deleted_at_utc`/`deleted_by` a NULL: ni en el portal ni en
la papelera. Si el orden hubiera sido el inverso, se habría perdido el parte bueno.

Datos del líder (base `partes`, solo lectura, 2026-11-26): 642 documentos; 112 inactivos sin
borrar, 93 desde el 2026-10-01; 11 sustituidos por otra página del **mismo correo**, varios
con horas distintas de su sustituto (no eran copias); 21 inactivos sin ningún parte posterior
de la misma obra y fecha; activos sin obra 1, sin fecha 5, sin líneas 2.

Términos: **sustituido** = inactivo, fuera de la papelera (`deleted_at_utc` NULL) y no
retirado por F-061 (`deleted_by` sin la marca `sin-lineas`). **Sustituto** = el parte cuya
ingesta lo desactivó. **Mismo envío** = sustituido y sustituto con el mismo `email_id` no vacío.

## A. sv3: el reemplazo deja rastro (D1, D2)

R1. CUANDO sv3 desactiva un parte por el reemplazo, el sistema debe escribir en él
`sustituido_por_id` = id del parte nuevo y `sustituido_at_utc` = hora UTC ISO, en la misma
transacción que guarda el nuevo, dejando `deleted_at_utc` y `deleted_by` a NULL. (capa: integración)

R2. El sistema debe seguir sustituyendo también entre páginas del mismo envío: quién queda
activo no cambia con F-084. (capa: integración)

R3. CUANDO el reemplazo desactiva un parte del mismo envío, sv3 debe registrar un WARNING
`[parte-repo] reemplazo del mismo envio` con los dos ids, `fecha_int` y la obra, sin nombres
ni DNIs. Uno de otro envío sigue con el INFO de hoy. (capa: unit)

R4. Las reglas que deciden qué se sustituye (fecha, obra, trabajador en común y entrada de
F-072) no cambian: los tests del reemplazo que ya existen siguen en verde sin tocarlos. (capa: integración)

R5. `ParteDocumentOrm` debe declarar `sustituido_por_id` (`String(36)`) y `sustituido_at_utc`
(`String(64)`), nullables y sin `server_default`, igual en las dos copias de `orm_models.py`;
`ddl_complementario()` debe generar su `ADD COLUMN IF NOT EXISTS`. Los partes anteriores
quedan a NULL. (capa: unit)

## B. Clasificación (sv4, módulo puro)

R6. El sistema debe dar a un parte ACTIVO estos motivos, en este orden y sin repetir:
`sin_obra` (`obra_ide` NULL), `sin_fecha` (`fecha_int` NULL o ≤ 0), `fecha_futura` (la regla
de `_doc_es_futuro`), `fecha_posterior_al_correo` (D5: `fecha_int` mayor que el día UTC de
`email_received_datetime` más un día de margen; sin correo o fecha ilegible, no salta) y
`sin_lineas` (ninguna línea viva). Sin ninguno, el parte no tiene problemas. (capa: unit)

R7. El sistema debe dar a un sustituido exactamente un motivo: `sustituido_mismo_envio` si su
sustituto es del mismo envío; `sustituido` si tiene sustituto de otro envío o sin correo;
`desactivado_sin_rastro` si no se encuentra ningún sustituto. (capa: unit)

R8. El sustituto de un parte con `sustituido_por_id` debe ser ese documento (y, si ya no
existe, `desactivado_sin_rastro`). Sin `sustituido_por_id` (los anteriores a F-084, D4), los
candidatos deben ser los partes ACTIVOS de la misma `fecha_int`, la misma obra (`obra_codigo`;
sin código, `obra_numero_leido`) y `created_at_utc` posterior; si alguno es del mismo envío,
ese es el sustituto, y si no, el más antiguo. Es una pista para la pantalla, no una regla de
reemplazo. (capa: unit)

R9. El sistema nunca debe listar en la pestaña un parte en la papelera (`deleted_at_utc` no
NULL) ni un retirado de F-061 (`es_retirado`). (capa: unit)

R10. El contador debe sumar los partes con algún motivo, salvo los que solo tienen
`sustituido` (D3): esos se listan, pero no cuentan. (capa: unit)

## C. La pestaña `/problemas` (sv4)

R11. CUANDO el usuario abre `/problemas`, el sistema debe listar los partes con problemas
agrupados por motivo (los que cuentan, primero) y, por parte: fecha, obra (código y nombre;
la leída si no está casada), página y páginas del PDF, asunto y hora del correo, nº de
trabajadores y horas de sus líneas vivas, y la insignia «aprobado» o «en Sigrid» si está
congelado (`_motivo_congelado_doc`). De un sustituido, además, el sustituto (fecha, obra,
enlace a `/partes/{id}` si está activo) y la hora de la sustitución si consta. (capa: integración)

R12. CUANDO el parte tiene PDF archivado, la fila debe ofrecer «Ver PDF», que abre el visor
del portal (`/partes/{id}/preview`, que ya sirve también los inactivos). (capa: integración)

R13. La fila de un parte ACTIVO debe enlazar a `/partes/{id}`, donde ya se corrigen la obra y
la fecha, sin endpoints nuevos. (capa: integración)

R14. La fila de un sustituido debe ofrecer «Recuperar» (sección D) y «Descartar», que manda
el parte a la papelera por el camino de hoy (`POST /documents/{id}/delete`, `back=/problemas`). (capa: integración)

R15. SI no hay partes con problemas, ENTONCES la pestaña debe decir que no hay ninguno. (capa: integración)

R16. La pestaña no debe mostrar DNIs. (capa: integración)

## D. Recuperar un sustituido (sv4)

R17. CUANDO el usuario pide `POST /api/partes/{id}/recuperar` con `{"fecha": "dd/mm/aaaa"}`
opcional, sobre un sustituido, el sistema debe, en una transacción: aplicar la fecha si viene
(al documento y a todas sus líneas, como `update_parte_fecha`); poner `is_active = true`;
conservar `sustituido_por_id` y `sustituido_at_utc`; y anotar en `undo_log` la acción
`parte_recuperar`, con `actor`. Responde `{ok, document_id, fecha, recalculo}`. (capa: integración)

R18. Tras el commit, el sistema debe pedir el recálculo seguido de F-043 con motivo
`recuperar_parte`; un fallo de la cola no deshace la recuperación. (capa: integración)

R19. SI, con la fecha final, hay otro parte ACTIVO de la misma `fecha_int` y la misma obra
que comparte con él alguna clave de trabajador del portal (`worker_key_for_registro`, líneas
vivas), ENTONCES el sistema debe responder 409 con esos partes (id, fecha, obra) y el texto
«Corrige la fecha o descarta antes el otro parte», sin escribir nada (D6). (capa: integración)

R20. SI otro parte activo tiene el mismo `source_sha256`, ENTONCES 409 con el motivo de
F-061 (`DuplicadoActivoError`), sin escribir. (capa: integración)

R21. SI viene fecha y el parte está congelado (F-004), o si el parte está en espera de
recálculo (F-043), ENTONCES 409 con el motivo de esa guarda, sin escribir. Sin fecha, un
parte congelado se puede recuperar. (capa: integración)

R22. SI el parte no existe, ENTONCES 404; SI está activo, en la papelera o retirado,
ENTONCES 409 con el motivo; SI la fecha no es válida, ENTONCES 400; en todos, sin escribir. (capa: integración)

R23. CUANDO el usuario deshace un `parte_recuperar`, el sistema debe volver a dejar el parte
inactivo y restaurar la fecha anterior en el documento y sus líneas, salvo lo que hoy esté
congelado (se omite, como en F-004 R9), y pedir el recálculo con motivo
`deshacer_recuperar_parte`. El widget de deshacer la llama «Recuperar parte». (capa: integración)

R24. Recuperar debe registrar un INFO con el id, la fecha anterior y la nueva y el actor, sin
nombres ni DNIs. (capa: unit)

## E. Aviso en la navegación (sv4)

R25. La navegación debe tener «Problemas» entre «Conciliar» y «Partes». CUANDO se carga
cualquier página, el portal debe pedir `GET /api/problemas/resumen` (`{ok, total,
por_motivo}`) y pintar el contador si `total` > 0. SI la petición falla, ENTONCES no se pinta
nada y la página sigue funcionando. (capa: integración)

R26. CUANDO se descarta un parte desde la pestaña, el sistema debe mandarlo a la papelera con
`deleted_by` = actor (guardas de F-004 y F-043 de `delete_document`) y volver a `/problemas`
con mensaje; el parte deja de salir en la pestaña y en el contador. (capa: integración)

## Fuera de alcance

- Páginas que fallan en sv2 o sv3 y no llegan a la base: acaban en `q-extraccion-poison` o
  `q-persistencia-poison` sin rastro en `partes` (D7: feature aparte).
- Cambiar qué se sustituye, también cuando el sustituido está aprobado o en Sigrid (D10).
- Editar las líneas de un sustituido o abrir su detalle (`/partes/{id}` sigue dando 404).
