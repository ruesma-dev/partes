# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Requisitos

**Solo sv4** (`services/partes-front/`), sin esquema, sv3, sv5 ni Sigrid. Rigor **crítico**
propuesto (DA9). Decisiones: design §13 (DA1–DA12, **todas propuestas**). Orden: §11.

Petición literal del humano (2026-10-15): «cuando en el calendario hago click para editar si
solo hay extras u ordinarias edita pero no me sale 0+2 por ejemplo para poder añadir linea».

## Interpretación y contexto (dev `ff2ed8e` + rama de F-050, revisado el 2026-10-20)

- El «calendario» es la matriz **Horas por día** de la vista de obra: **doble clic** en una
  celda abre un popup (`app.js`, IIFE «Matriz de obra») con una fila por línea de horas. Con
  **solo ordinarias** ofrece una «Extra» a 0 (`/extra`, sin partida); con **solo extras** no
  ofrece ordinaria: ese es el hueco. El calendario del trabajador no tiene editor (M1).
- Con **ordinaria + `extra_auto`**, la siguiente pasada de sv3 borra la `extra_auto` y
  restaura la base desde `horas_orig`: **la edición se pierde** (F-037 §9 R-c). Cada línea es
  un `PATCH` suelto en paralelo (no atómico) y ninguno pide recálculo (F-042).
- **F-048** (en dev): la ingesta ya no crea «solo extras» en laborable (base con `horas_orig`
  + `extra_auto`); el hueco sigue en datos anteriores, altas manuales y filas de F-050 (E10).
- **F-050** (se fusiona antes): la fila de la matriz es una por **clave de trabajador**
  (`worker_key_for_registro`: `rec-` > `emp-` > `nom-` > `sin-trabajador`). Una celda puede
  juntar líneas de la IA y del alta manual, de filas del papel distintas y de más de un parte.

## Glosario

- **Celda**: líneas de horas activas (no incidencia, no papelera, documento activo) con la
  misma clave de obra (`obra_key_for_registro`), clave de trabajador (`worker_key_for_registro`)
  y fecha. Se identifica por esas tres claves, no por sus ids.
- **Pareja automática**: base ordinaria con `horas_orig` y sus `extra_auto`, misma clave
  `(document_id, line_index, empleado_line_no, fecha_int)` (F-037).
- **Materializar**: `horas_orig = NULL` y `extra_auto = False`. **Plantilla**: línea de la
  celda de la que se clona el contexto de una línea nueva.

## Editor (JS y plantilla)

- **R1.** CUANDO el usuario hace doble clic en una celda con ≥ 1 línea de horas, el popup debe
  mostrar una fila por línea («Ord.» / «Extra», con «· partida» si la tiene); las
  `extra_auto` se rotulan «Extra (jornada)».
- **R2.** SI la celda no tiene ninguna ordinaria y tiene ≥ 1 línea no congelada, ENTONCES el
  popup debe ofrecer «Ord. (nueva)» a 0. Lo mismo con «Extra (nueva)» si no tiene extra.
- **R3.** SI todas las líneas de la celda están congeladas, ENTONCES el popup es de solo
  lectura, sin filas nuevas ni «Guardar» (F-004 R15, sin cambios).
- **R4.** Una celda sin líneas de horas (vacía o solo incidencia) no abre popup (como hoy).
- **R5.** El popup debe mostrar la nota fija: «En día laborable, las ordinarias del día se
  ajustan a la jornada y la diferencia pasa a extra. Las extras que escribas se respetan.»
- **R6.** CUANDO se pulsa «Guardar» sin ningún valor distinto y con las nuevas a 0 o vacías,
  el popup se cierra sin ninguna petición.
- **R7.** CUANDO se pulsa «Guardar» con cambios, el JS debe enviar UNA petición
  `POST /api/matriz/celda` con `obra_key` (de la tabla), `worker_key` (de la fila), `fecha`
  (ISO de la celda), todas las líneas no congeladas (`id`, `antes`, `horas`; un campo vacío
  vale `antes`) y `nueva_ordinaria` / `nueva_extra` (null si 0 o vacío).
- **R8.** CUANDO la respuesta es ok, la página se recarga; si `recalculo` es `fallo`, antes
  avisa «Horas guardadas, pero no se pudo pedir el recálculo de extras: se hará en la
  siguiente pasada.». SI es error, el título del popup muestra el motivo del servidor y el
  popup sigue abierto (F-004 R16).
- **R9.** La leyenda de la matriz debe decir «Doble clic en una celda: editar ordinarias y
  extra (se puede añadir la que falte).».
- **R10.** Los `regs` de la celda deben llevar `"a": 1` solo en las `extra_auto` (lo demás igual).
- **R31.** La tabla de la matriz debe llevar `data-obra-key` y cada fila `data-wk` con su
  `worker_key`; el popup los lee de ahí, nunca del nombre pintado.
- **R32.** SI la celda lleva `data-reparto` (F-046 R37), ENTONCES el popup debe añadir el
  aviso «Este día tiene un reparto entre obras pendiente de decidir: al guardar se vuelve a
  calcular.» (DA11).

## Servidor · `POST /api/matriz/celda`

- **R11.** SI la lista de líneas está vacía o repite ids, o falta `obra_key`, `worker_key` o
  una `fecha` ISO válida, ENTONCES 422 sin tocar nada.
- **R12.** SI los ids enviados no son exactamente las líneas no congeladas de la celda
  reconstruida con las tres claves (también si una se movió a otra celda o la celda ya no
  existe), o algún `antes` no es la hora actual, o se pide una nueva de un tipo que la celda
  ya tiene (congeladas incluidas), ENTONCES 409 «La celda ha cambiado desde que la abriste:
  recarga la página.» sin tocar nada.
- **R13.** SI una ordinaria (existente o nueva) no está en [0, 24], una extra no está en
  [−24, 24], la ordinaria nueva no es > 0 o un valor no es un número finito, ENTONCES 422.
- **R14.** SI una línea a cambiar o la plantilla está congelada, ENTONCES 409 con el motivo de
  `congelacion.py` sin tocar nada.
- **R15.** SI el documento de una línea a cambiar o de la plantilla está en espera (F-043; con
  F-047, también el parte nuevo), ENTONCES 409 con el texto de `RecalculandoError`.
- **R33.** SI el grupo (recurso, fecha) de la celda tiene un reparto en `aplicando` (F-046),
  ENTONCES 409 «Este día tiene un reajuste en Sigrid en curso: espera a que termine.» sin
  tocar nada (DA11).
- **R16.** Todo se guarda en UNA transacción, con su entrada de deshacer: o todo o nada.
- **R17.** Cada línea cambiada queda con `horas` = valor; a 0 se queda a 0, no a la papelera.
- **R18.** CUANDO cambia una línea miembro de una pareja automática, todas las líneas no
  congeladas de la celda con esa clave deben materializarse con su valor del popup. Las
  parejas sin ningún miembro cambiado no se tocan. `horas_extra_leidas` (F-048) no cambia.
- **R19.** La plantilla debe ser la primera línea no congelada de la celda por (ordinaria
  antes que extra, `id`).
- **R20.** Una línea nueva va al documento de la plantilla con `line_index` = máximo del
  documento (papelera incluida) + 1 (la segunda, + 2) y fecha de la plantilla, y clona
  trabajador, recurso y su método, obra, partida, `hora_candef`, `recurso_precio_hora`,
  `hmo_ide` y `parte_estado`; `extra_auto` False, `horas_orig`, `horas_extra_leidas` y
  `sigrid_*` a NULL.
- **R34.** `empleado_line_no` y `trabajador_nombre_leido` de una línea nueva deben salir de
  `fila_para_alta_manual` (F-050 R16–R17) sobre el documento de la plantilla, y la línea nueva
  debe tener la misma clave de trabajador y de obra que la celda (DA6).
- **R35.** SI la clave de la celda es `sin-trabajador`, ENTONCES el popup no ofrece nuevas y
  el servidor responde 422 a una nueva; sus líneas sí se editan (DA12).
- **R21.** La extra nueva lleva la primera hora `HE%` del recurso (`fetch_hora_extra_recurso`,
  como hoy) y la ordinaria nueva la de `TipoHoraMatcher.match(categoria, extra=False)` (como
  «+ Nuevo»). SI Sigrid falla o no hay código, ENTONCES la línea se crea sin código y WARNING.
- **R22.** La respuesta ok debe ser `{ok, editadas, creadas, recalculo}`.
- **R23.** CUANDO se guarda algún cambio, sv4 debe pedir el recálculo seguido (F-043) de cada
  documento tocado con motivo `edicion_celda`; `recalculo` = el peor estado. Sin cambios, no
  pide y `recalculo` es null. Un fallo de la cola no deshace lo guardado.
- **R24.** Cada guardado deja un INFO `[celda]` con ids editados, materializados y creados,
  documentos y estado del recálculo, sin nombres, DNIs ni la clave de trabajador (una `nom-`
  lleva el nombre leído).

## Deshacer

- **R25.** La entrada `celda_edit` debe guardar, de cada línea editada o materializada, los
  campos de deshacer de siempre más `horas_orig`, `extra_auto` y `document_id`, y los ids
  de las creadas.
- **R26.** CUANDO se deshace una `celda_edit`, se restauran horas y marcas de esas líneas
  (omitiendo las hoy congeladas, F-004 R9), las creadas no congeladas van a la papelera con
  `deleted_by` = actor y la respuesta lleva sus `document_ids`.
- **R27.** CUANDO se deshace una `celda_edit`, sv4 debe pedir el recálculo seguido de esos
  documentos con motivo `deshacer_edicion_celda`.
- **R28.** Deshacer cualquier otra acción no cambia: no restaura marcas.

## Lo que no cambia

- **R29.** sv3, sv5, `orm_models.py` (gemelos), `congelacion.py`, las reglas gemelas de
  `CLAUDE.md`, `worker_key_for_registro`, `fila_para_alta_manual`, `edit_normal_id` /
  `edit_extra_id`, `PATCH /api/registros/{id}`, `POST /api/registros/{id}/extra` y
  `crear_extra_desde` siguen igual; el calendario del trabajador sigue sin editor. Los tests
  existentes pasan sin más cambio que los dos dobles de `undo_last` (design §3).
- **R30.** sv3 debe clasificar como recálculo los mensajes con los dos motivos nuevos (test de
  contrato en la raíz; sv3 solo traza el motivo).

## Ejemplos (día laborable, jornada 8)

| Caso | Celda antes | Popup | Guardado | Tras el recálculo |
|---|---|---|---|---|
| E1 | 8 ord. | Extra (nueva) 2 | 8 + 2 explícita | 8+2 |
| E2 | 10 extra | Ord. (nueva) 8, Extra 2 | 8 nueva + 2 | 8+2 |
| E3 | 10 extra | Extra 2 (Ord. nueva a 0) | 2, sin ordinaria | +2 (sin ordinarias no se normaliza) |
| E4 | 8 (orig 10) + 2 jornada | Extra 3 | 8 sin orig + 3 explícita | 8+3 |
| E5 | 8 (orig 10) + 2 jornada | Ord. 7 | 7 + 2, materializadas | 8+1 (8, −1 jornada, 2) |
| E6 | 8 ord. | Ord. 0 | línea a 0 | vacía de horas, sin papelera |
| E7 | vacía o solo «V» | — | sin popup | — |
| E8 | sábado, 4 extra | Ord. (nueva) 4 | 4 + 4 | +8 (no laborable) |
| E9 | F-050 E1: manual 8 ord. (fila 1) + IA 2 extra (fila 3), un parte | Ord. 8, Extra 2, sin nuevas | Extra 3: solo esa línea | 8+3 |
| E10 | IA solo extra 2 en la fila 3, clave `rec-R` | Ord. (nueva) 8 | nueva en la fila 3, clave `rec-R` | 8+2 en una sola fila |
| E11 | reparto `aplicando` ese día | cualquiera | 409 sin tocar nada | — |

**Verificaciones manuales (humano)**: M1 antes de implementar y M2–M6 tras desplegar sv4,
con los pasos exactos en design §10.
