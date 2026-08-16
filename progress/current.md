<!-- progress/current.md -->
# Trabajo en curso

## F-003 · Integración sesame-api: festivos y jornada reales

- Estado: **IMPLEMENTADA + CORRECCIONES DE REVIEW APLICADAS** (2026-08-15)
  en la rama `feature/F-003-sesame-festivos-jornada`. Rigor critico ·
  sdd=true. Las 18 tareas de `tasks.md` están marcadas y commiteadas (un
  commit por tarea, más tres de refuerzo de tests guiado por mutación).
- La review (`progress/review_F-003.md`) devolvió **CHANGES_REQUESTED**
  con 4 puntos: los **4 están aplicados** (commits `F-003 fix-review:`,
  detalle en la sección «Correcciones tras review» de
  `progress/impl_F-003.md`). El quinto punto —la redacción del
  `CLAUDE.md`— **no se ha tocado**: necesita decisión del humano (ver
  «Pendiente del humano», punto 5). Pendiente de re-review.
- Informe completo: **`progress/impl_F-003.md`**.
  Campaña de mutación y análisis de supervivientes:
  **`progress/mutacion_F-003.md`**.
- `bash harness/init.sh` en verde, con `PUERTA COBERTURA` al **94,5 %** de
  las líneas cambiadas (**586/620**, umbral 80 % para rigor `critico`).
  Antes de aplicar las correcciones de la review era 94,5 % de **587/621**:
  el total baja en 1 porque el arreglo del punto 1 elimina una línea
  cambiada (el import sobrante).

### Lo que hay que saber para revisar

- **La feature va APAGADA**: sin `SESAME_API_BASE_URL` + `SESAME_API_KEY`
  no hay ni una llamada de red, los festivos salen del respaldo de
  siempre (`holidays` en sv4, JSON en sv3) y no existe ningún bloqueo ni
  marca. Hay tests de regresión que lo fijan (R7, R10, R27).
- **Cero cambios de schema**: ninguna copia de `orm_models.py` se ha
  tocado. La marca `[SIN-SESAME]` va en `sigrid_motivo`, que ya existía.
- **Desviación consciente del design**: `marcar_registros_sigrid` recibe
  un `motivo_ok` opcional (el design decía «nada más» de
  `parte_repository.py` aparte del `dni` de `ObraMatrixRow`). Sin ese
  parámetro no había forma de escribir la marca de R25, porque la traza
  se escribe dentro del repositorio. Por defecto no cambia nada.
- **Un bug real encontrado y arreglado** por la campaña de mutación:
  `SesameCalendarioLaboral.es_no_laborable` normalizaba la fecha para el
  fin de semana pero buscaba el festivo con la cadena cruda; un ISO con
  hora daba «laborable» en pleno festivo. Detalle en el informe.

### Pendiente del humano

1. **Verificaciones MANUALES**, con su comando exacto. Ninguna la puede
   cerrar un agente: tres son revisión de diff y dos son navegador.

   | # | Qué verificar | Comando exacto |
   |---|---|---|
   | 1 | **T13 · diff de `infra/`**: que no viaje ningún secreto y que el orden de pasos para encender Sesame sea el esperado | `git diff dev...HEAD -- infra/` |
   | 2 | **T17 · diff de `CLAUDE.md`**: es el fichero que gobierna todas las sesiones; la edición implementa la decisión D1, pero la redacción del cierre de la regla necesita el visto bueno explícito del humano (ver punto 5) | `git diff dev...HEAD -- CLAUDE.md` |
   | 3 | **T14 · `azure-apps/partes.md`**: commit local en ESE repositorio, sin push | `git -C ../azure-apps show 5a95c03` |
   | 4 | **T9 · «+ Nuevo» en el navegador**: crear un parte con un domingo y ver la confirmación («N día(s) son festivo/domingo — ¿continuar?»); al aceptar, el alta procede. Ctrl+F5 para recoger los estáticos | navegador (sv4 en local) |
   | 5 | **T15 · modal de override**: con Sesame activado y caído, el modal enseña el bloqueo, sin marcar la casilla no deja registrar, y al marcarla las líneas salen con el badge `SIN-SESAME`. **No se puede probar de verdad hasta P2** | navegador (sv4 en local) |
2. `azure-apps/partes.md` actualizado con el consumo de sesame-api:
   commit local `5a95c03` en ESE repositorio, **sin push**.
3. **Peticiones al proyecto sesame-api** (no se implementan aquí):
   - **P1**: exponer la jornada del contrato en horas; hasta entonces la
     jornada teórica sigue saliendo del `candef` de Sigrid.
   - **P2**: commitear y desplegar sesame-api, con la clave de partes en
     `kv-partes-pt7m3` (`sesame-api-key`). Hasta P2 la feature no se
     puede encender.
   - **P3**: escribir `azure-apps/sesame-api.md` (dueño: ese proyecto).
4. **Aviso operativo**: encender `SESAME_*` contra una URL que no
   responda BLOQUEA las aprobaciones (R23). Es deliberado —calcular mal
   en silencio es peor— pero conviene saberlo antes de tocar Azure.
5. **DECISIÓN PENDIENTE · redacción del `CLAUDE.md` (T17)**. La review
   señala que el commit `a4a9a61` no solo añadió los clientes
   `infrastructure/sesame/` a la lista de duplicación tolerada (que era
   la decisión D1), sino que además reescribió el cierre de la regla:
   de «la ya existente (…): **no crece**» a «**esta lista cerrada** (…):
   **solo crece con una decisión así**». Es un cambio de significado en
   una regla dura, y **un reviewer no lo puede aprobar**: o el humano
   firma la nueva redacción, o se vuelve al absoluto y se limita a
   añadir el ítem. **Queda tal cual está** hasta que el humano decida.
   Diff: `git diff dev...HEAD -- CLAUDE.md`.

### Contexto operativo heredado

- F-002 desplegada en Azure; sv5 en MODO PRUEBAS (obra 0404) hasta que el
  humano valide en navegador y pase a modo normal.
- F-010 (resincronizar `orm_models.py` entre sv3 y sv4) sigue en el
  backlog: F-003 no lo ha tocado, a propósito.

### Decisión del humano (2026-08-16, tras la review)

El humano FIRMA la nueva redacción de la regla de duplicación tolerada del
CLAUDE.md («lista cerrada… solo crece con una decisión así»), tal como la
dejó el implementer en T17. El punto elevado por el reviewer queda
resuelto: no hay que revertir nada.
