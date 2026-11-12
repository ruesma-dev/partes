# Spec F-069 · sv3: extras automáticas con ids estables y recálculo en una sola transacción

Fecha: 2026-11-12. Autor: spec-author. Rama `feature/F-069-extras-ids-estables` (desde `dev`
53498d0), worktree `C:\Users\pgris\PycharmProjects\partes-wt-f069`. Prioridad 1, rigor
crítico, urgente.

## Ficheros

- `specs/F-069-extras-ids-estables/requirements.md` (141/150): R1-R21 y M1-M2.
- `specs/F-069-extras-ids-estables/design.md` (219/250).
- `specs/F-069-extras-ids-estables/tasks.md`: T1-T19 (T12-T13 solo con DA1).
- `python -m harness.tamano --feature F-069`: dentro de los topes.

## Qué propone, en corto

- **Servicio**: sv3. sv4 solo para el mensaje opcional (DA1). Sin esquema, colas ni contratos
  nuevos. La regla de congelación gemela y `orm_models.py` no se tocan.
- `_pasada` deja de hacer el commit del revert. Lee una sola vez (`leer_pasada`): aplica
  `plan_revert` **en memoria** (la «vista revertida», que da al cálculo las mismas filas que hoy)
  y guarda una **huella** por pareja del estado crudo.
- Al final, `escribir_pasada` hace en **una transacción** casados, revert y splits, con
  `FOR UPDATE` en PostgreSQL. Cada split **reutiliza en el sitio** la extra que la pareja ya tenía,
  así que el `id` es el mismo. Se emparejan por orden dentro de la clave; lo que sobra se borra o
  se crea.
- Si sv4 cambió una pareja entre la lectura y la escritura (horas, `encolado`, papelera,
  aprobación, fila nueva o borrada), esa pareja **no se toca** en esta pasada: WARNING y
  `parejas_cambiadas`.
- `materializar_repartos` (F-046) sigue antes de leer y sin cambios: solo toca congeladas.
- `revert_extras_auto` y `apply_extras_splits` se quedan como envoltorios para sus tests.
  `extras_reclasificadas` mantiene su significado. Los contadores nuevos van solo al log.
- Un único test existente cambia de expectativa: el orden de `test_f046_conciliar.py:608`.

## Decisiones abiertas (las valida el humano)

| DA | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| DA1 | ¿Entra el mensaje de sv4 «ya no existen, se están recalculando las extras, recarga»? | A) Entra (R20-R21, T12-T13: un método de repositorio y un `if` en `_validar_ambito`; JS sin cambios). B) Fuera. | **A**. Es pequeño y sigue sirviendo cuando una extra desaparece de verdad. |
| DA2 | Una extra reutilizada, ¿se deja igual que una recién creada (borra `sigrid_estado` omitido/error, `deleted_at_utc` y el resto de columnas no clonadas)? | A) Igual que hoy al recrearla, salvo el `id`. B) Conserva lo que tenía. | **A**. No cambia ninguna semántica: hoy esos campos se pierden en cada pasada. Cambiarlo merece su propia feature. |
| DA3 | ¿Cómo se casa split con extra cuando una clave tiene varias bases (partidas)? | A) Por orden (`normal_id`, `id`). B) Columna de enlace base↔extra (cambio de esquema en los dos ORM gemelos). | **A**. Es estable mientras no cambie nada, que es el caso que hay que arreglar. B solo si aparece un caso real. |
| DA4 | M1 necesita un PostgreSQL desechable en Docker. ¿Lo hay? | A) Sí: M1 como está. B) No: solo los tests de SQLite y M2 en Azure (solo lectura). | **A** si hay Docker. Si no, B. El bloqueo real y el READ COMMITTED solo se ven en PostgreSQL. |
| DA5 | Pareja que cambió durante la pasada | A) No tocarla, WARNING y reintentar en la siguiente pasada. B) Abortar la pasada entera y reintentar el mensaje. | **A**. B, con sv4 editando en plena tanda, podría no terminar nunca una pasada. |
| DA6 | Alcance del `FOR UPDATE` | A) Todas las filas de los documentos con parejas afectadas, en orden de `id`. B) Solo las filas de las claves. | **A**. Es más simple y la transacción es corta. B obliga a un `IN` de tuplas. |
| DA7 | ¿Los casados de recurso van en la misma transacción? | A) Sí (R8). B) Aparte, como hoy. | **A**. La extra se rellena con el recurso y el `hmo_ide` de su base: así son coherentes siempre. |
| DA8 | Contadores nuevos (`extras_nuevas`, `extras_reutilizadas`, `extras_borradas`, `parejas_cambiadas`) | A) Solo en el log. B) También en el dict de resultado. | **A**. El dict lo fijan los tests de F-042, F-045 y F-046 (R19). |
| DA9 | La rama sale de `dev`, que aún no tiene el commit del backlog (`adff337`, en `chore/backlog-F-069-F-071`). En la rama, `features.json` no tiene F-069. | A) Fusionar `chore/backlog-F-069-F-071` en `dev` y luego `dev` en la rama, antes del implementer. B) Seguir así. | **A**. Sin ese commit, `init.sh` no puede poner F-069 `in_progress`. |

## Fuera de alcance

- Que cada parte nuevo dispare una pasada global (pedido explícito del líder).
- Las extras automáticas con fecha NULL de la observación del diagnóstico.
- Casados de filas que no son de una pareja cuando sv4 las cambia a media pasada: se quedan como
  hoy, sin comprobar huella.

## Riesgos principales (detalle en design §10)

- El bloqueo dura un poco más, porque los casados entran en la transacción.
- Puede haber un interbloqueo con sv4. Si pasa, se hace rollback y se reintenta el mensaje (R16).
- Si hay varias bases por clave y cambia su orden, las extras podrían intercambiar ids (DA3).

## Aprobación

2026-11-12: el humano aprueba la spec («ok a spec») con todas las decisiones abiertas según la
recomendación: DA1 = A (entra el mensaje de sv4), DA2–DA8 = A, DA4 = A (Docker 29.5.3 disponible).
DA9 = A, resuelta trayendo `chore/backlog-F-069-F-071` a la rama de F-069. F-069 pasa a `in_progress`.

## Cierre

2026-11-12: el humano acepta el mutante equivalente n.º 10 («acepto»; `zip(..., strict=True→False)`
en `leer_pasada`, equivalente por construcción, reproducido por el reviewer). F-069 pasa a `done`.
Pendiente: desplegar sv3 y sv4 y M2 del líder.
