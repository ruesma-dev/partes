<!-- progress/review_F-052.md -->
Revisión completa (pasada 1) de `dev` 69af0f5 a HEAD 8d7a563 (rama `feature/F-052-sincronizar-con-sigrid`)

# F-052 · Review (pasada 1)

**Veredicto: CHANGES_REQUESTED.** El código, las suites, la cobertura y la campaña cuadran,
pero quedan `[ ]` de papeleo en C4, en C5 y en la spec (cambios 1 a 3). Ninguno toca producción
ni obliga a repetir la campaña. Con ellos hechos, la pasada 2 (incremental desde 8d7a563) puede
cerrar en **«APROBADO condicionado a aceptación de equivalentes y M3»**.

**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación completa con cero supervivientes
sin test o sin justificación aceptada por el humano, RM5 con muestra de uno y MANUAL con su comando.

## Verificación ejecutada (resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. COBERTURA 99,9 % (741/742). TAMAÑO OK. sv4
  y sv5 salieron de caché, así que las lancé **a mano** con `python -m pytest -q -p no:cacheprovider`:
  sv5 **1622 passed** (11 s); sv4 **3609 passed, 1 skipped (299 s)**.
- **RM1**: el informe mide 3424919 (T17). `git diff 3424919..HEAD -- services/` solo trae
  `tests/test_f052_*` y quita una única línea (un import). Recalculé con `harness.alcance` y
  `generar_mutantes`, en 3424919 y en HEAD: **11 ficheros, 1488 líneas y 331 mutantes** en los
  dos, igual que el informe. La campaña sigue valiendo.
- **RM2**: 331 × 95,8 = 31 710 s, que cuadra con el total (31 711,7 s). Media × 4 workers = 383 s
  por mutante, entre la línea base de sv5 (29 s) y la de sv4 (692 s), coherente con `-x` y 289
  muertos. Sin cabecera de no válida y con 0 sin veredicto. **Campaña no reejecutada: 8,8 h**
  según el informe.
- Muestreo: el 9, el 14 y el 25 existen como mutantes reales (mismo operador y mismo texto).
- **RM4** (copia `git archive HEAD` en el scratchpad, `sys.executable`, control sin mutante rc 0): 25
  `with_for_update` → `r20_bloqueo_for_update_…` **1 failed**; 15 (2 variantes) →
  `da18_seco_veredicto_sin_registro_id_…` **1 failed** en cada una; 42 → `r1_log_dice_el_ambito` **2 failed**.
- **RM5**: el 14 (grep), y además las demos del 5 y del 8/9 (salida literal). **RM3**: ningún
  equivalente sale muerto. **RM6** N/A: los 38 se mataron con tests nuevos, sin quitar código.

## Equivalentes (PENDIENTES de aceptar por el humano)

- **14 · escritura muerta: lo confirmo.** `por_confirmar` en producción: `sincronizacion.py:141`
  y `:248` y `sincronizar_ambito.py:279` (lectura, antes) y `:294`. Después nadie lo lee (ni
  `item_a_dict`, ni `firma`, ni `resumen`, ni `acciones_de`; `_aplicar` empareja por `firma`, no por `==`).
- **5 y 8 · los confirmo**: `split(":", n)[0]` no depende de `n ≥ 1`; el orden de claves es fijo.
- **9 · equivalente en la práctica, pero la justificación está incompleta.** Con un
  **surrogate suelto** (`'\ud800'`), el original revienta en `firma` (`UnicodeEncodeError`) y
  el mutante no. Probado con `clasificar([], [S(9100, 'manual', partida_cod='\ud800')])`. No se
  puede observar desde el portal: `JSONResponse` también revienta (500 en los dos casos). Solo
  cambia un `aplicar` a mano con un id que el panel no enseñó (500 contra 200). Cambio 4.

## Puntos de especial atención

- **ID10 · `aplicar` no depende del seco.** Encaja con el alcance **literal** de DA18 («¿Escribe
  **R10**… **al comparar**?»): una acción confirmada (R17) y revalidada por firma bajo candado
  (R18) no es la escritura implícita que DA18 quería parar. El re-sync de `aplicar` sí respeta
  el seco (tests `da18_aplicar_no_depende_del_modo_seco` y `r10_fuera_de_seco_la_firma_ve_…`).
  **Pero** la frase la añadió el implementer en T10 (64188c0) **dentro de la celda «APROBADA A
  (humano, 2026-11-03)»**: el texto aprobado (bc1de1c) no la llevaba (cambio 3).
- **ID8 · `restaurar` sin `_validar_ambito`: la decisión es correcta.** F-022 haría imposible el
  `restaurar` de R24, porque una línea de la papelera no está en los ids de la vista. La
  pertenencia la prueba el re-sync: un id que no sale da 422 sin escribir (`_aplicar`, 410-417),
  y `acciones_de` exige `donde == "papelera"` y no `repetida`. Se aparta de R18 y no consta en
  la spec (cambio 3).
- **ID9, ID11, ID12 (`CAMPOS_TRAER = ("horas",)`) e ID14**: correctos (R24 reutiliza las rutas
  tal cual). **ID13**: F-017 pasa de 20 a 21, justificado; el guardián de F-047 exige por nombre las 17
  de `F052_PANEL` y deja el resto en 302, así que sigue cazando funciones nuevas.
- **R26**: sv5 solo usa `_read` (`/api/sql/read`), sin lock ni `escribir`. sv4 solo llama a
  `sincronizar_leer`/`comprobar` (`sv5.otras == []`). Ninguna DML contra Sigrid en el diff.
- **No se tocan** (`git diff --stat dev...HEAD` vacío): `congelacion.py`, `orm_models.py`, sv1, sv2
  y sv3 entero (con `esta_congelado`), `jornada_resolver.py`, sigrid y sesame de sv4, `application/`
  de sv5, `comprobacion_sigrid.py`, `reparto_aviso.py`, `seguimiento_recalculo.py` y
  `edicion_celda.py`. En el gemelo `sigrid_write_client.py` (sv5), solo añadidos y el reflow de un import.
- **Escrituras (§6)**: FOR UPDATE en orden de id, CAS en la transacción, R21 con
  `_exigir_sin_recalculo`/`_filas_reparto` (clave de F-046), `horas_orig` intacta y motivo ≤ 255.
- **azure-apps 1289301**: rutas, variable nueva y que el seco no gobierna las acciones. Sin
  secretos. Falta ID8 (cambio 3).

## Checkpoints

- **C1** [x] init.sh en verde · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] la rama es la de la feature · [x] `current.md`
  describe F-052 (la sección de F-055 viene de `dev`, con su M3 del humano) · [x] historia de las
  `done` sin cambios.
- **C3** [x] hexagonal (`sincronizacion.py` es puro; el orquestador recibe sus colaboradores
  inyectados; el SQL va en `infrastructure`) · [x] ruta en la primera línea de los 11 ficheros
  nuevos · [x] sin `print`, `console.log`, TODO, secretos ni dependencias · [x] trampas:
  recurso por `_recurso_de`/`reside`, incidencias sin horas y `a_cero` sin `CI*`, ORM intacto.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [ ] **R14, R26 y R28 sin ningún `test_f052_rN_*`** (cambio 1). Su comportamiento sí
  está probado con otros nombres (`da18_seco_…_ni_escribe`, `r5_*` de sv5, `otras == []`, el
  guardián de F-024). Los otros 27 tienen de 1 a 19 tests, en verde · [x] sin red ni BBDD
  (dobles, SQLite, TestClient) · [x] M3 y M4 en `current.md`, con los comandos en `m3_F-052.md`.
- **C4 bis** [x] rigor · [x] RED real (T2–T13, líneas `E` pegadas) · [x] cobertura [OK] ·
  [x] totales recalculados · [x] muertos: campaña no reejecutada, recálculo, muestreo y RM4 ·
  [x] coste de 383 s por mutante · [x] sin cabecera de no válida · [x] RM1 · [x] RM2 · [x] RM5 ·
  [x] RM6 N/A (justificado) · N/A campaña manual: fue automática · [x] ningún análisis en
  PENDIENTE (los 4 equivalentes esperan la aceptación del humano: es la condición) ·
  [x] «Evidencias» con los 4 números y los 4 workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [ ] **T8 sigue `[ ]`** con la M2 superada (`m2_F-052.md`) (cambio 2); el resto, `[x]` con
  commit `F-052 Tn:` · [x] el worktree está limpio · [x] `features.json` en `in_progress`.

## Cobertura requisito → test `test_f052_…` (uno por R; el recuento sale de `grep "def test_f052_rN_"`)

| R | Test | R | Test | R | Test |
|---|---|---|---|---|---|
| 1 | `r1_endpoint_une_ambito_y_synckeys_…` | 11 | `r11_pendiente_506` | 21 | `r21_traer_parte_en_espera_descarta` |
| 2 | `r2_linea_de_sv5_con_origen_desconocido_…` | 12 | `r12_donde_estan` | 22 | `r22_motivo_cabe_en_255` |
| 3 | `r3_pasa_de_pagina_solo_si_viene_llena` | 13 | `r13_resumen_por_clase_y_a_cero` | 23 | `r23_documentos_de_los_dias` |
| 4 | `r4_endpoint_fallo_de_lectura_502_…` | 14 | **falta** (`da18_seco_…_ni_escribe`) | 24 | `r24_aplicar_restaurar_desde_la_papelera` |
| 5 | `r5_endpoint_no_toma_el_lock_…` | 15 | `r15_endpoint_ambito_no_valido_422` | 25 | `r25_al_terminar_vuelve_a_sincronizar_…` |
| 6 | `r6_endpoint_admite_62_dias_…` | 16 | `r16_tabla_de_acciones` | 26 | **falta** (`r5_*`, `otras == []`) |
| 7 | `r7_endpoint_sin_ambito_422` | 17 | `r17_confirma_con_recuento_…` | 27 | `r27_abrir_la_vista_no_llama_a_sv5` |
| 8 | `r8_doce_clases` | 18 | `r18_firma_estable_ante_el_orden` | 28 | **falta** (guardián de F-024) |
| 9 | `r9_tolerancia_de_horas` | 19 | `r19_aplicar_marcar_registrada_…` | 29 | `r29_mismo_ambito_a_la_vez_409` |
| 10 | `r10_endpoint_fuera_de_seco_…` | 20 | `r20_aplicar_traer_de_sigrid_y_recalculo` | 30 | `r30_sin_transfer_503` |

## Cambios requeridos

1. **C4.** Añadir `test_f052_r14_*`, `test_f052_r26_*` y `test_f052_r28_*`:
   - R14: `sincronizar`, en seco, solo hace lecturas en el repositorio.
   - R26: ninguna de las 5 acciones de `aplicar` llama a sv5 fuera de `sincronizar_leer` y
     `comprobar`, y `/api/sincronizar/leer` nunca llama a `escribir`.
   - R28: la excepción de traer vive solo en `aplicar_traer_de_sigrid`, y `congelacion.py` y
     `esta_congelado` no cambian (en la raíz, junto al guardián de F-024). Solo tests: sin campaña.
2. **C5.** En `specs/F-052-sincronizar-con-sigrid/tasks.md`, marcar T8 `[x]` citando
   `progress/m2_F-052.md` (M2 superada, líder, 2026-11-03).
3. **Spec.** En `design.md` §8, sacar de la celda aprobada de DA18 la frase sobre `aplicar` y
   dejarla como «ID10, añadido en T10 (64188c0), pendiente de ratificar por el humano». Anotar
   ID8 (`restaurar` sin `_validar_ambito`, cubierto por el re-sync con 422) en R18 o en §4 con
   la misma marca y en la fila `/api/sincronizar/aplicar` de `azure-apps/partes.md`. El líder
   lleva ID8 e ID10 al humano junto con los equivalentes.
4. **`progress/mutacion_F-052.md`, superviviente 9.** Completar el análisis con lo del
   surrogate suelto. La alternativa de matarlo (`ensure_ascii=True` más un test con `'\ud800'`)
   cambia producción y obliga a repetir la campaña de ese fichero: lo decide el humano.

## Pendiente del humano (condición del APROBADO definitivo)

Aceptar los equivalentes 5, 8, 9 y 14, ratificar ID8 e ID10, hacer M3 (`progress/m3_F-052.md`) y,
antes de M4, decidir `SINCRONIZAR_SECO` en Azure.

## Automejora (propuesta, no aplicada)

- `reviewer.md` RM5: un equivalente de serialización se prueba también con entradas límite
  (surrogates, `NaN`). `CHECKPOINTS.md` C5: una tarea MANUAL ya hecha se marca `[x]` citando su informe.
