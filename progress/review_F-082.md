<!-- progress/review_F-082.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (base `dev` 4d806fd, HEAD 78957b7)

# Review F-082 · El portal siempre ofrece «Sin partida» al editar la partida

**Veredicto: CHANGES_REQUESTED** (pasada principal, carril `estandar`, ciclo 1 de 2).

**Nivel de rigor: `estandar`** (declarado en `features.json`; pasa de `express` a `estandar`
por la D1 de la PARADA 1, 4 ficheros). Exige fase RED y cobertura; mutación y capa e2e son
informativas. El diff no toca `harness/rigor.local.json`. Sin pasada de evidencias: la capa
e2e es N/A y no hay Python de producción que mutar.

## Lo que ejecuté yo

- `bash harness/init.sh` **tal cual** sobre 78957b7 (encargo del líder; no
  `ARNES_SIN_CACHE=1`): INIT_RESULTADO.
- **Fase RED reproducida**: `git archive 2f033d9` de `static/`, `templates/` y el test a una
  copia del scratchpad (2f033d9 solo añade el test: producción idéntica a `dev`) ⇒
  `8 failed, 5 passed`, los mismos 8 que cita el informe. En HEAD: 13 passed.
- **Backend con partida vacía, comprobado a mano** (script en scratchpad, SQLite de
  `tests/dobles.py`): línea con leída `0716` y método `sin` ⇒
  `set_registro_partida(todo None)` devuelve True, deja `partida_ide/cod` a None, **conserva
  la leída** (`partida='0716'`) y método `manual`. Una entrada F-072 (E29) con todo None ⇒
  `PartidaFijaError` y la partida fija intacta (R32 respetada).
- **sv3 no la re-casa**: `PartidaConciliador.conciliar_todos` salta `manual` antes de mirar la
  leída (`partida_conciliador.py:149-151`); lo vigila
  `test_f072_r20_la_marca_de_entrada_no_se_toca` (caso `manual`).
- **Mutación (informativa)**: recálculo puro con `harness.alcance.alcance_de_feature('F-082')`
  ⇒ `lineas={}`: 0 líneas Python de producción, 0 mutantes. El cero es legítimo: el diff de
  producción es solo `.js` y `.html`, que el generador no muta.

## Revisión del cambio

- `buildPartidaPicker` (app.js 3032-3042): la fila «— Sin partida —» se pinta en `show()`
  **fuera** de `filtrados()` y antes del `if (!list.length)`, así que sale siempre: con
  partidas, con texto que no casa, con chip CD/CI y en obra sin presupuesto. Es el único picker
  de los dos usos: el ✎ de celda (`wirePartidaEdit`, 3123) y «Editar partida» en bloque
  (`wireBulkSelect`/`doPartida`, 3310). `onPick({ide,cod,res,capitulo: null})` ⇒
  `applyPartidaToIds` manda los cuatro campos a null. Bien.
- El texto del vacío distingue «Esta obra no tiene partidas» de «Sin partidas con ese filtro».
  Es una mejora pequeña fuera de la letra de la descripción, coherente con ella.
- Las plantillas solo añaden una rama `manual` **dentro del `else`** (sin `partida_cod`). Las
  ramas con partida (todos los métodos), leída no encontrada con método ≠ manual y «⚠ sin
  partida» no cambian. Las entradas F-072 llevan partida fija, entran por la primera rama y no
  se ven afectadas. Las congeladas siguen sin ✎ (`MotivoHttp.congelado`) y el backend las
  sigue rechazando con 409. `papelera.html` no pinta partida. Ningún JS ni CSS depende del
  marcado de la celda (`partida-warn` solo tiene regla CSS; `partida-sin` no tiene ninguna).
- No se toca el backend ni sv3: confirmado con `git diff --stat`.

## Checkpoints

- **C1** [x] init.sh en verde (ver arriba; ejecutado tal cual por encargo, con caché de suites
  donde aplicó). [x] Ficheros base presentes.
- **C2** [x] Una sola activa (F-082). [x] Orden de prioridad: la cola acordada el 2026-11-23
  (F-083 → F-082). [x] Rama `feature/F-082-opcion-sin-partida`. [x] `current.md` describe la
  sesión activa. [x] Lo `done` tiene historia (sin cambios aquí).
- **C3** [x] Hexagonal: solo static/templates. [x] Cabecera de ruta en `app.js` y en el test.
  Las plantillas no la llevan desde antes de F-082 (empiezan por `{% extends %}`): no es
  regresión. [x] Sin prints, TODOs, secretos ni dependencias nuevas. [x] Trampas de dominio:
  no aplican (no toca recurso/empleado, incidencias ni schema).
- **C3 bis / C3 ter** N/A: no entra documento externo ni acta de conversación.
- **C3 quater** N/A: no cambia lo que sv4 expone ni consume (mismo endpoint, mismo payload).
- **C4** [ ] **Trazabilidad de A2 incompleta** (cambio 1). [x] Sin red ni BBDD (node y Jinja2
  locales). [ ] **MANUAL no listadas en `progress/current.md`** (cambio 2). [x] Dobles: el
  DOM mínimo del test JS no imita ninguna clase Python; la barrida automática de init.sh pasa.
- **C4 bis** [x] `rigor` declarado. [x] Fase RED con salida real, reproducida por mí.
  [x] Cobertura: `PUERTA COBERTURA: N/A` con motivo impreso (sin líneas Python de producción);
  el JS tocado se ejecuta entero en node. Mutación: N/A por nivel (informativa en `estandar`),
  y además 0 mutantes por alcance vacío, recalculado. RM1–RM7 y supervivientes: N/A por
  carril `estandar`. [x] «Evidencias» con los cuatro números y la fila «Capa e2e».
  Capa e2e: N/A (`CAPA E2E: N/A`, ningún servicio la declara).
- **C4 ter** N/A: sin rutas sensibles señaladas por init.sh.
- **C5** N/A `tasks.md` (sdd=false); commits `F-082 T1/T2` correctos. [x] Árbol limpio.
  [x] `features.json` en `in_review`.

## Cobertura (acceptance → test)

| Criterio | Tests | Estado |
|---|---|---|
| A1 Los dos selectores ofrecen «Sin partida», también sin presupuesto | `test_f082_a1_*` (5): picker ejecutado en node con partidas, filtro, chip CI y obra vacía; cableado de los dos usos (estático) | cubierto |
| A2 Elegirla deja la línea sin partida y sin aviso | JS ⇒ PATCH con todo null (`_a2_elegir_sin_partida_manda_todo_null`); celda `manual` sin ⚠ en las 3 plantillas; regresión del resto | **falta el eslabón backend** (cambio 1) |
| A3 init.sh verde + APPROVED | init.sh arriba | pendiente de este veredicto |

## Cambios requeridos

1. **`services/partes-front/tests/test_f082_sin_partida.py`: fija con un test el eslabón del
   servidor de A2.** Hoy A2 se prueba en sus dos extremos: el JS manda los cuatro null y la
   plantilla oculta el aviso **si** el método es `manual`. Lo que une los dos extremos es que
   `PATCH /api/registros/{id}/partida` con todo null deje la línea sin partida **y en
   `manual`**, y eso no lo vigila ningún test (los de `set_registro_partida`,
   `test_f072_repositorio.py:223-234`, `test_f004_endpoints_congelados.py:169-214`, siempre
   mandan partida). Si alguien hiciera que la partida vacía devolviera el método a `None`/`sin`,
   la celda volvería a pintar «⚠ 0716 no encontrada», sv3 la re-casaría y la suite seguiría
   verde. Basta un test (repositorio sobre `FabricaSesionSqlite`, o el endpoint con
   `TestClient` como en F-004) que: (a) parta de una línea con leída y sin casar, mande todo
   null y compruebe ⇒ True/200, cuatro campos None y `partida_match_method == "manual"`;
   (b) con una entrada F-072, el mismo payload ⇒ `PartidaFijaError`/409 y la partida fija
   intacta. Opcional: que el undo (`registro_partida`) devuelve el estado anterior. Lo
   verifiqué a mano y hoy pasa: es fijar lo que ya funciona, no tocar producción.
2. **`progress/current.md`, sección «F-082 · in_review»: lista las 4 verificaciones MANUAL
   (humano)** que hoy solo están en `progress/impl_F-082.md` (§ «Verificaciones MANUAL
   pendientes»), con su paso exacto: página, acción y resultado esperado, más Ctrl+F5. C4 las
   exige en `current.md`, que es lo que lee el humano al cerrar.

## Observaciones (no bloquean)

- O1. Si después se cambia la obra del parte, `parte_repository.py:4190-4208` re-casa la línea
  por su leída y pierde el «sin partida» manual. Pasa lo mismo con cualquier partida manual
  desde antes de F-082. Lo mismo con un reproceso que cree un documento nuevo.
- O2. `test_f082_a1_los_dos_selectores_usan_el_picker` es una búsqueda de texto. Es aceptable
  porque el picker se ejecuta de verdad en los otros cuatro.
- O3. En bloque, si la selección incluye una entrada F-072, `Promise.all` rechaza con un
  mensaje genérico tras aplicar las demás. Ya pasaba con cualquier partida.

## Automejora (propuesta, no aplicada)

- Ninguna al protocolo. La revisión pidió `ARNES_SIN_CACHE=1` y el encargo, `init.sh` tal cual.
  Sugiero que `leader.md` diga explícitamente cuál manda cuando las suites pasan de 10 min.
