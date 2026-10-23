<!-- progress/spec_F-056.md -->
# spec-author · F-056 · Franquicia de extras (2026-10-23)

Spec en `specs/F-056-franquicia-de-extras/` (rama `feature/F-056-franquicia-de-extras` desde
`dev` 560d753, worktree `partes-wt-f056`). Topes: requirements 141/150, design 245/250, tasks
20 tareas (una por línea). `features.json`: F-056 `spec_ready`, prioridad 1, rigor crítico,
con criterios `acceptance` nuevos; `BACKLOG.md` regenerado.

## Qué hace (con la recomendación A de todas las DA)

- **Regla**: periodo = mes de nómina de Ruesma (16 → 15, ya existe en sv4 como
  `MODE_NOMINA`). E = extras `HE*` netas del recurso en Sigrid en el periodo (todas las obras,
  partes de cualquier estado, también manuales). A = −min(E, X) si E > 0; si no, 0.
- **sv5**: `/api/franquicia/comprobar` (solo lectura) y `/api/franquicia/ejecutar` (bajo el
  lock del registro). Alta de UNA línea `HE*` con `can = A` el día de ajuste, en el parte En
  registro de la obra (alta protegida si falta), precio de `reshor`, cuenta F-021, `tex`
  explicativo y synckey `partes:franquicia:<id>`; recálculo = `UPDATE` de la misma línea
  (`stmt_actualizar_linea` de F-046, a 0 sin borrar). Ningún `DELETE`. Los dos `_choques`
  ignoran esa synckey: si no, la extra real del día chocaría con el ajuste y el modal
  ofrecería pisarla a 0.
- **sv4**: X por trabajador en la tabla nueva `empleado_franquicia` (sección de
  `/admin/jornadas`); día de ajuste = último del periodo con `jornada_dia` > 0 (F-015 + Sesame);
  obra = la de más horas ese día. Aviso en el modal de aprobar cuando la selección trae ese día
  (o ya hay ajuste: «Recalcular» / «Mantener»); decisión obligatoria en el modal; la decisión se
  guarda en `franquicia_ajuste` y el ajuste se aplica al terminar el registro (también desde la
  vista de trabajador). sv3 solo recibe la copia del ORM.

## Hallazgos que el humano debe conocer

1. «Mes nómina» en el portal ya es 16 → 15 (`calendar_builder.py`): el ajuste cae el último
   laborable ≤ 15 y en el parte de Sigrid del mes natural de ese día.
2. Sin la exclusión de choques (R31), el ajuste y la extra del mismo día y obra serían
   conflicto (la clave es recurso + día + código de hora, sin partida).
3. M1 (solo lectura, agregados): 138 recursos persona con un único `HE*` y ninguno con dos;
   las `HE*` se enlazan a nómina al procesarla (ene–may ~70 %, jul–oct 0 %), así que tras la
   nómina el ajuste ya no se puede editar (DA9); Administración ya mete a mano `HE*` negativas
   con `tex` «Ajuste…» (días 15/16), ninguna de franquicia.
4. En modo asíncrono las líneas llegan a Sigrid después de la respuesta: por eso la decisión se
   guarda al registrar y el ajuste se aplica cuando ya no quedan líneas `encolado` (R18).

## Decisiones abiertas para el humano (`design.md` §7, recomendación A en todas)

DA1 dónde se guarda X · DA2 mensual por mes de nómina · DA3 qué extras cuentan · DA4 obra con
varias obras · DA5 código y precio · DA6 qué es «último laborable» · DA7 qué dispara el aviso ·
DA8 recálculo ante cambios · DA9 parte cerrado o línea enlazada · DA10 pantalla y momento ·
DA11 rechazar · DA12 bloquear sin decisión · DA13 qué ve Sigrid · DA14 identificación de la
línea · DA15 quién calcula · DA16 varios recursos / mensuales · DA17 interruptor · DA18 lista
cerrada de `CLAUDE.md` · DA19 pantalla de configuración · DA20 una feature o dos.

## Pendiente fuera de la spec

- M2–M4 (`design.md` §10) son del humano; M1 ya está hecha.
- Tamaño: es una feature grande (dos tablas, dos endpoints de sv5, modal y dos pantallas de
  sv4). DA20 deja un punto de corte tras T7 (sv5 entero, verificable en la 0404).
