<!-- progress/spec_F-049.md -->
# F-049 · Informe del spec-author

## Cierre del 2026-10-20: spec aprobada (DA1–DA12 = A, DA13 = C)

Decisiones del humano (2026-10-20, chat con el líder, citas literales): a la DA13, «c»; a las
demás, «apruebo las DA con los comentarios que te he hecho anteriormente» (los comentarios:
la confirmación de la pantalla, M1 superada, y el caso de otras obras del mismo día). Estado
`spec_ready`; se implementa cuando F-050 esté en dev.

### Comprobado en el código (rama en `f0c4fc5`)

- sv3 `recalculo_seguimiento.py`: `marcar_terminado` hace hoy `UPDATE … WHERE id ==
  document_id AND recalculo_pedido_id == peticion_id` y devuelve `rowcount == 1`. Con DA13-C
  el filtro pasa a ser solo el pedido y devuelve `rowcount >= 1`; misma firma; `despacho.py`
  (`_pedido_leido`, `_marcar_terminado`), `mensajes.py` y la pasada no cambian.
- Compatibilidad: los pedidos de sv4 son uuid4 (`_pedir_recalculo_seguido`) y el de F-047
  (rama `feature/F-047-parte-nuevo-en-espera`, requirements R1 y R4) es el id del propio
  documento: ningún pedido coincide con el de otro documento, así que los marcados de un
  documento siguen igual (R42). El desorden de F-043 R32 se conserva (filtro por pedido).
- Test existente a invertir: `test_f043_r28_adaptador_solo_toca_su_documento`
  (`services/partes-persistencia/tests/test_f043_seguimiento_sv3.py`, ~l. 122) afirma lo
  contrario de R41. Va a la lista cerrada de design §3 (invertido y renombrado
  `test_f043_r28_adaptador_marca_todo_documento_con_su_pedido`). Los demás tests del
  adaptador (más nuevo, idempotente, viejo no pisa, inexistente, reloj UTC) siguen valiendo.
  El contrato de la raíz `tests/test_f043_contrato_seguimiento.py` solo ata nombres: sin cambio.
- sv4 `parte_repository.py`: `marcar_recalculo_pedido` / `anular_recalculo_pedido` son por
  documento; se añaden `marcar_recalculo_pedido_compartido(ids, *, peticion_id)` (`UPDATE … id
  IN`, un commit) y `anular_recalculo_pedido_compartido` (solo donde siga ese pedido). `app.py`
  gana `_pedir_recalculo_compartido` (UN mensaje con `document_id` = primer documento tocado);
  `_pedir_recalculo_seguido` no cambia.
- Despliegue: `infra/redeploy_partes.ps1` ordena `$ORDEN = sv2, sv3, sv5, sv4, sv1`; sv3 es
  KEDA con mínimo 0 réplicas. Con sv4 nuevo y sv3 viejo los afectados esperarían hasta
  `ESPERA_MAX_S` = 600 (`seguimiento_recalculo.py` de sv4 ⇒ `vencido`), bloqueando edición y
  «Aplicar» de F-046. Mitigación en design §10: `-Solo sv3`, comprobar que su revisión nueva
  está activa y luego `-Solo sv4`. Sin variable de entorno nueva.

### Qué cambia en la spec

- requirements: cabecera (sv4 y sv3, aprobada); glosario «pedido compartido»; R23, R26, R27,
  R29 y R39 reescritos para DA13-C; R41–R42 nuevos (sv3); E12a con el pedido y E12d nuevo
  (riesgo residual); M2–M8 tras desplegar sv3 y luego sv4. 149 líneas.
- design (250 líneas, reorganizado para caber): §1 límite con el porqué de sv3; §2 absorbe el
  antiguo §11 (orden y F-047); §3 añade el adaptador de sv3, el test sv3 nuevo y la lista
  cerrada (b); §4 absorbe «por qué materializar»; §5–§6 las funciones de pedido compartido;
  §8 (antes 8 bis) la espera con DA13-C; §9 tests de R39 y R41–R42; §10 orden de despliegue y
  M8; §11 riesgos (despliegue mixto, E12d, B descartada); §12 decisiones APROBADAS con cita.
- tasks: T1 sin condición de DA13; T6–T9 con el pedido compartido; T14 (RED sv3 + test F-043
  invertido) y T15 (`marcar_terminado`) dejan de ser condicionales; T16–T19 renumeradas; la
  mutación (T17) incluye `recalculo_seguimiento.py`.
- `harness/features.json` (description y acceptance de F-049: sv3 + sv4, aprobada, despliegue
  sv3 → sv4) y `progress/current.md` (sección de F-049).

### Decisiones abiertas

Ninguna. Queda para el humano: el orden de despliegue sv3 → sv4 y las verificaciones M2–M8.


## Revisión acotada del 2026-10-20 (tarde): M1 y otras obras del mismo día

Respuesta del humano (2026-10-20, literal): «confirmo que e esa pantalla. al añadir horas
nuevas por este metodo podria tener que recalcular horas de otros dias si es la 2 obra o
siguiente de este trabjador en el mismo dia».

### M1 superada

La pantalla es el popup del doble clic en la matriz «Horas por día» de la vista de obra
(requirements, interpretación; design §10). DA1 sigue igual.

### Qué recalcula hoy, de verdad, el sistema (dev `ff2ed8e`; F-050 no toca sv3)

- **La pasada es completa.** `despacho._recalcular` (sv3) llama a
  `RecursoConciliador.conciliar_todos()`, que bajo `candado_pasada` ejecuta `_pasada`:
  `revert_extras_auto` (todas las `extra_auto` no congeladas de toda la base),
  `materializar_repartos` (F-046), `fetch_registros_para_recurso` (todo lo activo),
  casado de recurso y `_reclasificar_extras_jornada`, que agrupa por `(recurso, fecha_int)`
  **entre obras y partes** y reparte con `repartir_dia` (F-045) o `_reajustar` (F-046). El
  `document_id` del mensaje no acota nada: solo sirve para el seguimiento. Así que guardar en
  la obra Y recalcula sola la obra X del mismo día (sus `extra_auto` se borran y se crean con
  ids nuevos).
- **Otros días no cambian.** `_detalle_jornada` → `jornada_resolver.detalle_jornada_dia(d,
  candef, mapa, es_laborable, excepcion)` no recibe horas: con candef 9 (semanal 42), de lunes
  a jueves 9 y el último laborable `max(0, 42 − 36)` = 6, lo trabaje como lo trabaje los otros
  días. Cada (recurso, día) se reparte por separado. La pasada recorre todos los días pero, si
  nada más cambió, les da lo mismo (idempotente).
- **La espera de F-043 cubre solo el documento pedido.** `_exigir_sin_recalculo(doc)` mira
  `recalculo_pedido_id` / `recalculo_terminado_id` de ESE documento; sv3 lee el pedido del
  `document_id` del mensaje y `SqlAlchemyRecalculoSeguimiento.marcar_terminado` actualiza
  solo esa fila. `alcance_parte` no tiene que ver con la espera: solo cuenta trabajadores y
  líneas para el diálogo de cambio de fecha. Los partes de la otra obra se reescriben sin
  espera (riesgo R-g de F-043, anterior a F-049). La aprobación no la para la espera (F-043
  DA12).
- **Líneas de la otra obra congeladas.** Cuentan en el día y no se tocan. Con
  `REPARTO_REAJUSTE` apagado (F-045): la obra editada absorbe lo que quede de jornada (E12b: Y
  sale 0 + 2 de jornada + 2). Encendido (el líder lo anotó encendido en Azure el 2026-10-18; el
  repo aún lo da por pendiente): si hay alguna ordinaria libre, lo libre recibe el ideal ya y
  lo congelado reajustable queda en `reparto_pendiente` `pendiente` (E12c: X 8 → 5,5 y una
  extra nueva de 2,5); se ve como `data-reparto` en la matriz de las dos obras, se decide en el
  aviso al aprobar, bloquea aprobar el documento (F-046 R36) y registrar las líneas del día
  (F-046 R32). Un `mantenido` previo con otra `firma_grupo` vuelve a `pendiente`. Líneas
  `encolado`/`dedicacion` o día sin cuadre: nada y WARNING. «Aplicar» ya da 409 si un parte
  del día está en espera (`documentos_en_espera`) o si sus líneas cambiaron.
- **Libres**: se recalculan solas en esa misma pasada (E12a: X 5,5 + 2,5 de jornada; Y 2,5 −
  0,5 de jornada + 2). Cifras calculadas con `repartir_dia` y `proponer_dia` reales.

### Qué cambia en la spec

- Requisitos nuevos R36 (aviso al abrir con `GET /api/matriz/celda/otras`), R37 (lista con
  enlaces tras guardar, sin recargar hasta «Cerrar»), R38 (`afectadas`: un elemento por
  documento del grupo (recurso, día) fuera de la celda, nunca otro día ni recurso), R39 (con
  DA13-B, recálculo seguido de los afectados) y R40 (caracterización de sv3 sin tocar su
  código). R8, R22, R24, R27 y R29 ajustados; ejemplos E12a/b/c.
- Design §8 bis nuevo (lo de arriba, con referencias), §5 `_afectadas` y `otras_de_celda`,
  §6 la ruta GET, §7 `textoOtras` y `avisoAfectadas`, §9 tests, §10 M1 superada y M7, §12
  riesgos (aprobar durante la pasada; celda sin `recurso_ide`).
- Tareas: T1 exige DA13 decidida; T13 test de caracterización de sv3; T14 solo con DA13-C;
  las demás renumeradas (T15–T18).
- Topes: requirements 150/150, design 250/250 (`python -m harness.tamano --feature F-049`).

### DA13 (nueva) · otras obras del mismo día

| Opción | Qué | Coste |
|---|---|---|
| A | Aviso antes (R36) y después con enlaces (R37); espera solo de la celda | Solo sv4; queda el riesgo R-g en la otra obra durante la pasada |
| **B (recomendada)** | A + recálculo seguido de cada parte afectado (R39) | Solo sv4; N pasadas completas serializadas (~30 s cada una) |
| C | A + un solo pedido compartido: sv3 `marcar_terminado` marca todo documento con ese pedido | Toca sv3 (`recalculo_seguimiento.py`), despliegue sv3 antes que sv4; una pasada |
| D | Nada (spec anterior) | — |

Ninguna opción duplica lógica fuera de la lista cerrada de `CLAUDE.md`: sv4 solo reutiliza
`_claves_de` (F-046) para saber qué partes comparten el día; el reparto lo sigue calculando
solo sv3.


## Revisión del 2026-10-20: rebase sobre dev `ff2ed8e` y diseño sobre dev + F-050

Encargo del líder (2026-10-20): poner al día la spec escrita el 2026-10-15 sobre `dc03468`,
con el orden de cola decidido por el humano (F-050 → **F-049** → F-014 → F-047) y el código
de dev más el de F-050 (rama `feature/F-050-misma-fila-para-el-mismo-trabajador`, leída solo
con `git show` / `git diff`; su worktree no se ha tocado).

### Rebase

`git rebase dev` de la rama `feature/F-049-editor-calendario-normal-y-extra`: conflictos solo
en `harness/features.json` (resuelto: el de dev más la entrada F-049 tras F-048),
`progress/current.md` (las dos partes; la sección de F-049 reescrita abajo) y `BACKLOG.md`
(regenerado con `harness/backlog.py`). El commit original queda reescrito sobre `ff2ed8e`.

### Qué cambió en la spec (`specs/F-049-editor-calendario-normal-y-extra/`)

- **Orden y dependencias**: fuera «después de F-046 y F-047». Va después de F-050 y antes de
  F-047. **No depende de F-047**: solo usa la guarda `_exigir_sin_recalculo` de F-043, que
  F-047 amplía al parte nuevo sin cambiar el texto (su R15); la celda hereda ese 409 cuando
  F-047 se fusione. Solape solo textual (`parte_repository.py`, `obra_detail.html`,
  `app.js`). Design §11; T1 ahora exige F-050 en dev.
- **Sección nueva «lo que cambia con F-050 y lo fusionado desde `dc03468`»** (design §2):
  F-046 (`data-reparto`, `_filas_reparto`, `_claves_de`, `ESTADOS_BLOQUEAN`, editar sin
  guarda de reparto), F-048 (`horas_extra_leidas`, solo traza), F-051 (nada de sv4) y F-050
  (`worker_key_for_registro` con `rec-`, `fila_para_alta_manual`, celda que junta IA y alta
  manual de filas del papel distintas y posiblemente de varios partes; `edit_*_id` no los usa
  ni plantilla ni JS).
- **Identificación de la celda (DA2, cambia por F-050)**: `POST /api/matriz/celda` recibe
  `obra_key`, `worker_key` (clave de F-050) y `fecha`; el servidor reconstruye la celda con
  `obra_key_for_registro` + `worker_key_for_registro` + `fecha_int` (`_celda`) y exige que los
  ids enviados sean exactamente sus líneas no congeladas (con `antes` = hora actual). Una
  línea movida, una clave antigua o una celda vacía dan el 409 «recarga» (R7, R11, R12, R31;
  plantilla con `data-obra-key` en la tabla y `data-wk` en cada fila).
- **Fila del papel de la línea nueva (DA6, cambia por F-050)**: `empleado_line_no` y leído
  de `fila_para_alta_manual` sobre el documento de la plantilla, y la nueva con la misma
  clave que la celda (R34; E9/E10 con el fixture E1 de F-050).
- **Fila `sin-trabajador` (DA12, nueva)**: se editan sus líneas pero no se le crean (R35).
- **Reparto de F-046 (DA11, nueva)**: aviso en el popup si la celda lleva `data-reparto`
  (R32) y 409 si el grupo (recurso, fecha) tiene un reparto `aplicando` (R33). Congelación
  sin cambios (`congelacion.py`, `_exigir_reg_editable`).
- **F-048**: materializar no toca `horas_extra_leidas` y la nueva nace con NULL (R18, R20).
- Ejemplos E9–E11 nuevos; tests y tareas al día (T1, T6, T7, T10–T12). Topes: requirements
  150/150, design ≤ 250 (`python -m harness.tamano --feature F-049` en verde).

### Decisiones abiertas que necesita validar el humano (design §13)

Todas son **propuestas** (las del commit original nunca se aprobaron). Recomendación: A en
todas.

| DA | Tema | Recomendación | ¿Cambia? |
|---|---|---|---|
| DA1 | Alcance: solo el popup de la matriz de obra | A | No |
| DA2 | Ruta atómica con CAS y celda por (obra, clave de trabajador, fecha) | A | **Sí, por F-050** |
| DA3 | Lo escrito manda: materializar las parejas tocadas | A | Matiz F-048 |
| DA4 | Recálculo seguido con espera al guardar | A | No |
| DA5 | A 0 no va a la papelera | A | No |
| DA6 | Plantilla, su documento, `line_index` nuevo y fila de `fila_para_alta_manual` | A | **Sí, por F-050** |
| DA7 | La nueva clona también la partida | A | No |
| DA8 | Deshacer manda las creadas a la papelera (`undo_last(actor=…)`, dos dobles) | A | No |
| DA9 | Rigor crítico | A | No |
| DA10 | Rangos 0–24 / −24–24 / nueva > 0 | A | No |
| DA11 | Reparto vivo: aviso y 409 solo en `aplicando` | A | **Nueva, por F-046** |
| DA12 | `sin-trabajador`: editar sí, crear no | A | **Nueva, por F-050** |

### Pendiente

- PARADA 1: aprobación del humano de DA1–DA13 y de la spec.
- M1: superada el 2026-10-20 (sección de arriba).
- Implementación solo cuando F-050 esté fusionada en dev (T1).
