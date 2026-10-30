# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Requisitos

**sv4 y sv3** (sv3 solo marca el pedido compartido, DA13-C), sin esquema, sv5 ni Sigrid. Rigor
**crítico** (DA9). **Aprobada** el 2026-10-20: DA1–DA12 opción A y DA13 opción C (design §12).

Petición literal del humano (2026-10-15): «cuando en el calendario hago click para editar si
solo hay extras u ordinarias edita pero no me sale 0+2 por ejemplo para poder añadir linea».
Y el 2026-10-20: «confirmo que e esa pantalla. al añadir horas nuevas por este metodo podria
tener que recalcular horas de otros dias si es la 2 obra o siguiente de este trabjador en el
mismo dia».

## Interpretación y contexto (dev `ff2ed8e` + rama de F-050, revisado el 2026-10-20)

- **M1 superada (2026-10-20)**: popup del **doble clic** en la matriz **Horas por día** de la
  obra (`app.js`): con solo ordinarias ofrece «Extra» (`/extra`); con solo extras, nada.
- Con **ordinaria + `extra_auto`**, la pasada de sv3 restaura la base desde `horas_orig`: **la
  edición se pierde** (F-037 §9 R-c). Cada línea es un `PATCH` suelto y ninguno pide recálculo.
- **F-048**: la ingesta ya no crea «solo extras» en laborable (quedan datos viejos, altas y E10).
  **F-050** (antes): fila por `worker_key_for_registro`; una celda junta IA, altas y varios partes.
- **Otras obras del mismo día** (design §8): la pasada de sv3 es **completa** y reparte por
  (recurso, día) entre obras (F-045): guardar puede cambiar ese día en otra obra; **otros días
  no**. DA13-C: aviso antes y después y **una sola pasada** espera y libera a todos.

## Glosario

- **Celda**: líneas de horas activas (no incidencia ni papelera, documento activo) con la misma
  `obra_key_for_registro`, `worker_key_for_registro` y fecha; se identifica por esas tres claves.
- **Pareja automática**: base con `horas_orig` y sus `extra_auto` de la misma clave de F-037.
  **Materializar**: `horas_orig = NULL`, `extra_auto = False`. **Plantilla**: la que se clona.
- **Grupo del día**: líneas activas con el mismo (`recurso_ide`, `fecha_int`) que la celda
  (`_claves_de`, F-046). **Afectadas**: las del grupo fuera de la celda (otras obras).
- **Pedido compartido**: un único `recalculo_pedido_id` (uuid4 nuevo) que sv4 escribe a la vez
  en los documentos tocados y afectados de un guardado (o deshacer) antes de publicar UN mensaje.

## Editor (JS y plantilla)

- **R1.** CUANDO el usuario hace doble clic en una celda con ≥ 1 línea de horas, el popup muestra
  una fila por línea («Ord.» / «Extra», «· partida» si la tiene; `extra_auto`: «Extra (jornada)»).
- **R2.** SI la celda no tiene ninguna ordinaria y tiene ≥ 1 línea no congelada, ENTONCES el
  popup debe ofrecer «Ord. (nueva)» a 0. Lo mismo con «Extra (nueva)» si no tiene extra.
- **R3.** SI todas las líneas están congeladas, ENTONCES solo lectura, sin nuevas ni «Guardar».
- **R4.** Una celda sin líneas de horas (vacía o solo incidencia) no abre popup (como hoy).
- **R5.** El popup debe mostrar la nota fija: «En día laborable, las ordinarias del día se
  ajustan a la jornada y la diferencia pasa a extra. Las extras que escribas se respetan.»
- **R6.** CUANDO se pulsa «Guardar» sin valores distintos y las nuevas a 0 o vacías, cierra sin petición.
- **R7.** CUANDO se pulsa «Guardar» con cambios, el JS envía UNA `POST /api/matriz/celda` con
  `obra_key` (tabla), `worker_key` (fila), `fecha` (ISO), todas las líneas no congeladas (`id`,
  `antes`, `horas`; vacío vale `antes`) y `nueva_ordinaria` / `nueva_extra` (null si 0 o vacío).
- **R8.** CUANDO la respuesta es ok sin `afectadas`, recarga (si `recalculo` es `fallo`, antes
  avisa «Horas guardadas, pero no se pudo pedir el recálculo de extras: se hará en la siguiente
  pasada.»). SI es error, el título muestra el motivo y el popup sigue abierto (F-004 R16).
- **R9.** La leyenda dice «Doble clic en una celda: editar ordinarias y extra (se puede añadir la que falte).».
- **R10.** Los `regs` de la celda llevan `"a": 1` solo en las `extra_auto` (lo demás igual).
- **R31.** La tabla lleva `data-obra-key` y cada fila `data-wk`; el popup los lee de ahí.
- **R32.** SI la celda lleva `data-reparto` (F-046 R37), ENTONCES el popup añade «Este día
  tiene un reparto entre obras pendiente de decidir: al guardar se vuelve a calcular.» (DA11).
- **R36.** CUANDO se abre, el popup pide `GET /api/matriz/celda/otras` (si falla, nada); SI hay afectadas, añade
  «Este trabajador tiene horas ese día en otras obras (códigos): al guardar se recalcula el reparto del día en todas.».
- **R37.** CUANDO la respuesta ok trae `afectadas`, el popup muestra «Guardado. Este cambio recalcula
  también ese día en:», un enlace por obra a `/obras/{obra_key}` («aprobada o en Sigrid: si su
  reparto cambia, quedará pendiente de decidir al aprobar» si `congelada`) y «Cerrar», que recarga.

## Servidor (sv4) · `POST /api/matriz/celda` y `GET /api/matriz/celda/otras`

- **R11.** SI las líneas están vacías o repiten ids, o falta `obra_key`, `worker_key` o `fecha` ISO, ENTONCES 422.
- **R12.** SI los ids no son exactamente las no congeladas de la celda reconstruida (movida o
  vacía incluidas), algún `antes` no es la hora actual o se pide una nueva de un tipo presente,
  ENTONCES 409 «La celda ha cambiado desde que la abriste: recarga la página.» sin tocar nada.
- **R13.** SI una ordinaria no está en [0, 24], una extra no está en [−24, 24], la ordinaria
  nueva no es > 0 o un valor no es un número finito, ENTONCES 422.
- **R14.** SI una línea a cambiar o la plantilla está congelada, ENTONCES 409 con el motivo de `congelacion.py`.
- **R15.** SI el documento de una línea a cambiar o de la plantilla está en espera (F-043; con
  F-047, también el parte nuevo), ENTONCES 409 con el texto de `RecalculandoError`.
- **R33.** SI el grupo del día tiene un reparto en `aplicando` (F-046), ENTONCES 409 «Este día
  tiene un reajuste en Sigrid en curso: espera a que termine.» sin tocar nada (DA11).
- **R16.** Todo se guarda en UNA transacción, con su entrada de deshacer: o todo o nada.
- **R17.** Cada línea cambiada queda con `horas` = valor; a 0 se queda a 0, no a la papelera.
- **R18.** CUANDO cambia un miembro de una pareja automática, las no congeladas de la celda con
  esa clave se materializan con su valor; otras parejas y `horas_extra_leidas`, intactas.
- **R19.** La plantilla es la primera no congelada de la celda por (ordinaria antes, `id`).
- **R20.** Una nueva va al documento y fecha de la plantilla, `line_index` = máximo del documento (papelera
  incluida) + 1 (la segunda, + 2), clona trabajador, recurso y su método, obra, partida, `hora_candef`,
  `recurso_precio_hora`, `hmo_ide` y `parte_estado`; `extra_auto` False; `horas_orig`, `horas_extra_leidas`, `sigrid_*` NULL.
- **R34.** `empleado_line_no` y `trabajador_nombre_leido` de la nueva salen de `fila_para_alta_manual` (F-050
  R16–R17) sobre el documento de la plantilla; la nueva tiene la clave de trabajador y de obra de la celda (DA6).
- **R35.** SI la clave es `sin-trabajador`, ENTONCES el popup no ofrece nuevas y el servidor
  da 422 a una nueva; sus líneas sí se editan (DA12).
- **R21.** La extra nueva lleva la primera hora `HE%` del recurso (`fetch_hora_extra_recurso`)
  y la ordinaria nueva la de `TipoHoraMatcher.match(categoria, extra=False)` («+ Nuevo»). SI
  Sigrid falla o no hay código, ENTONCES se crea sin código y WARNING.
- **R22.** La respuesta ok es `{ok, editadas, creadas, recalculo, afectadas}`.
- **R38.** `afectadas` (POST, misma sesión) y `GET …/otras` (solo lectura): `[{obra_key,
  obra_codigo, document_id, congelada}]`, uno por documento con líneas no incidencia del grupo
  del día fuera de la celda; nunca de otro día ni recurso. Sin `recurso_ide`: vacía.
- **R23.** CUANDO se guarda algún cambio, sv4 pide UN recálculo con pedido compartido (R39) de tocados y
  afectados, motivo `edicion_celda`; `recalculo` = su estado (sin cambios, null). Un fallo de cola no deshace.
- **R39.** El pedido se escribe en todos en UNA sentencia confirmada ANTES de publicar UN mensaje
  con `document_id` = el primer tocado; SI publicar falla, ENTONCES se quita donde siga siendo ese.
  Hasta que sv3 lo marque (R41) o venza (10 min, F-043), editar cualquiera de ellos da el 409 R15.
- **R24.** Cada guardado deja un INFO `[celda]` con ids editados, materializados y creados,
  documentos tocados y afectados, pedido y recálculo; sin nombres, DNIs ni clave de trabajador.

## Deshacer (sv4)

- **R25.** La entrada `celda_edit` guarda, de cada línea editada o materializada, los campos
  de deshacer de siempre más `horas_orig`, `extra_auto` y `document_id`, y los ids creados.
- **R26.** CUANDO se deshace una `celda_edit`, restaura horas y marcas (salvo hoy congeladas, F-004 R9), manda
  las creadas no congeladas a la papelera (`deleted_by` = actor) y da `document_ids` y `afectadas` de ese momento.
- **R27.** CUANDO se deshace una `celda_edit`, sv4 pide UN recálculo con pedido compartido
  (R39) de esos documentos y de esas afectadas, motivo `deshacer_edicion_celda`.
- **R28.** Deshacer cualquier otra acción no cambia: no restaura marcas.

## sv3 · marcado del pedido compartido (DA13-C)

- **R41.** CUANDO sv3 acaba sin excepción la pasada del pedido P (leído del documento del mensaje, F-043 R27),
  marca terminado (P y hora) **todo** documento con `recalculo_pedido_id` = P y ninguno más.
- **R42.** Los pedidos de un solo documento (F-042/F-043) y el de F-047 (pedido = id del parte)
  se marcan como hoy; repetir es idempotente y un pedido viejo nunca marca un documento con
  otro (F-043 R32). La pasada, `despacho.py`, `mensajes.py` y el mensaje no cambian.

## Lo que no cambia

- **R29.** Siguen igual sv5, sv3 salvo `marcar_terminado` (R41), `orm_models.py`, `congelacion.py`,
  los gemelos de `CLAUDE.md`, `worker_key_for_registro`, `fila_para_alta_manual`, `edit_*_id`,
  `PATCH` y `/extra`, `crear_extra_desde`, `_pedir_recalculo_seguido`; tests, salvo design §3.
- **R30.** sv3 clasifica como recálculo los dos motivos nuevos (test de contrato en la raíz).
- **R40.** sv3 reparte el grupo como F-045/F-046, sin cambios (E12; caracterización en sv3).

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
| E9 | F-050 E1: manual 8 ord. (fila 1) + IA 2 extra (fila 3), un parte | Ord. 8, Extra 2 | Extra 3: solo esa línea | 8+3 |
| E10 | IA solo extra 2 en la fila 3, clave `rec-R` | Ord. (nueva) 8 | nueva en la fila 3 | 8+2 en una fila |
| E11 | reparto `aplicando` ese día | cualquiera | 409 sin tocar nada | — |
| E12a | celda en Y: 2 extra; X: 8 ord. libre | aviso R36; Ord. (nueva) 2 | Y 2 + 2; `afectadas` = [X]; pedido P en Y y X | X 5,5 + 2,5 jornada; Y 2,5 − 0,5 jornada + 2; Y y X terminados |
| E12b | igual, X congelada, `REPARTO_REAJUSTE` apagado | igual | igual | X 8 intacta; Y 0 + 2 jornada + 2 |
| E12c | igual, X `registrado`, interruptor encendido | igual | igual | Y 2,5 − 0,5 + 2; reparto `pendiente` X 8 → 5,5 + 2,5 nueva |
| E12d | E12a y, antes de la pasada de P, otro pedido Q en X | igual | X con Q | la pasada de P marca Y, no X; X espera a la de Q |

**Verificaciones manuales (humano)**: M1 superada; M2–M8 tras desplegar sv3 y luego sv4 (design §10).
