<!-- progress/review_F-052.md -->
Revisión incremental desde 8d7a563 (pasada 2), hasta HEAD 2f04997 (rama `feature/F-052-sincronizar-con-sigrid`)

# F-052 · Review (pasada 2)

**Veredicto: APPROVED condicionado** a que el humano acepte los equivalentes 5, 8, 9 y 14,
ratifique ID8 e ID10 y haga M3. Los cuatro cambios de la pasada 1 están hechos. El delta solo
trae tests, spec y `progress/`: **no toca producción**, así que la campaña sigue valiendo (RM1).

La pasada 1 (revisión completa de 69af0f5 a 8d7a563, CHANGES_REQUESTED) está en el commit
8d20b1d. Lo aprobado allí se da por bueno y no se ha vuelto a leer: código, campaña (331
mutantes, 8,8 h), RM2 a RM6, ID9 e ID11 a ID14, escrituras de §6 y ficheros que no se tocan.

**Rigor:** `critico` (declarado). Exige RED, cobertura ≥ 80 %, mutación completa con cero
supervivientes sin test o sin justificación aceptada por el humano, y RM5 con muestra de uno.

## Verificación ejecutada (resultado real)

- `bash harness/init.sh` (HEAD 2f04997): **ENTORNO LISTO**, exit 0. Raíz **544 passed, 3 skipped**
  (incluye `test_f052_r28_*`). COBERTURA 99,9 % (741/742). TAMAÑO OK (design 250/250, impl
  218/220). sv1 a sv5 salieron de caché, así que lancé sv4 y sv5 **a mano** con
  `python -m pytest -q -p no:cacheprovider`: sv5 **1628 passed** (10 s); sv4 **3624 passed, 1 skipped** (284 s).
- **Producción intacta (RM1)**: `git diff 8d7a563..HEAD` solo trae 3 ficheros de test, `design.md`,
  `tasks.md` y `progress/`. Y `git diff 3424919..HEAD -- services/` sin los `tests/`
  (3424919 es el SHA que midió la campaña) sale **vacío**. Alcance y mutantes no cambian
  desde lo recalculado en la pasada 1. No hace falta repetir la campaña.
- **RED reproducido** por mí, sobre una copia `git archive HEAD` en el scratchpad: inyecté
  `self._repo.guardar_sincronizacion(None)` en `_sincronizar` y corrí `-k r14`. Salió
  **13 failed, 2 passed**, igual que en el informe. El control sin la rotura da 15 passed.

## Cambios de la pasada 1: comprobación uno a uno

1. **[x] Tests de R14, R26 y R28, con su RED** (31ba861; RED en `impl_F-052.md` §Review 1, con
   las líneas `E` reales de cada rotura):
   - sv4 `test_f052_r14_r26_solo_lectura.py` (15 tests).
     - **R14**: un espía de repositorio que anota cualquier método, también los que no existen.
       En seco solo se usan las tres lecturas, no hay escrituras y no se llama a F-024. Fuera de
       seco tampoco se guarda nada. Cada sincronización vuelve a leer.
     - **R26**: las 5 acciones × seco o no, con `Sv5Espia.otras == []`. Hay una guardia AST
       que comprueba que `self._sv5` solo se usa para `sincronizar_leer` y `comprobar`, sin alias.
   - sv5 `test_f052_r26_leer_no_escribe.py` (6 tests): `/api/sincronizar/leer` nunca llama a
     `escribir`. Lo comprueba en los casos 200, 502 por cada lectura y 422, más una guardia AST
     del cuerpo de la ruta (sin `escribir`, lock ni pipeline).
   - Raíz `test_f052_r28_congelacion_intacta.py` (4 tests):
     - `registrado` sigue congelando en sv3 y en sv4, cada uno en su propio subproceso.
     - Las dos reglas no nombran la sincronización.
     - Solo `aplicar_traer_de_sigrid` asigna `horas` sin pasar por `_exigir_reg_editable`.
     - Solo el orquestador llama a ese método.

   Espías que no revientan: un `except` no puede tapar una llamada indebida. Correcto.
2. **[x] T8 `[x]`** en `tasks.md` (e425e2e), citando `progress/m2_F-052.md` (M2 superada, líder,
   2026-11-03, repetida tras H-M2-1).
3. **[x] ID8 e ID10** (6f138a2). La celda «APROBADA A» de DA18 queda con el texto aprobado (bc1de1c),
   sin la frase sobre `aplicar`. **ID10** pasa a un párrafo propio bajo la tabla, «añadido en T10
   (64188c0), PENDIENTE DE RATIFICAR POR EL HUMANO», con sus tests. **ID8** va en §4, con la misma
   marca, el motivo (F-022 impediría el `restaurar` de R24), la defensa (re-sync con 422 y
   `acciones_de` exige `papelera`) y tres tests. En azure-apps, d098bc6 añade ID8 a la fila
   `/api/sincronizar/aplicar` de `partes.md`, también como pendiente de ratificar. Sin secretos.
   `current.md` lo anota.
   - Los recortes de §9 y §10, hechos para quedar en 250 líneas, solo juntan viñetas en una
     línea. No cambia el contenido.
4. **[x] Superviviente 9** (3747c50): `mutacion_F-052.md` añade el caso del surrogate suelto
   con su salida real (el original da `UnicodeEncodeError` y el mutante firma). Explica por qué
   no se observa:
   - El `JSONResponse` de sv4 revienta igual en los dos.
   - En la cadena real, sv5 ya da 500 y sv4 responde 502 sin ítems.
   - La única divergencia es un `aplicar` lanzado a mano.

   Deja la alternativa de matarlo (`ensure_ascii=True` más un test) **sin aplicar**, para que la
   decida el humano. Ningún análisis queda en PENDIENTE.

## Checkpoints (pasada 2)

- **C1** [x] init.sh en verde · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] la rama es la de la feature · [x] `current.md`
  describe el estado (review 1 y siguiente paso) · [x] historia de las `done` sin cambios.
- **C3** [x] hexagonal: el delta no toca código de producción · [x] los 3 ficheros nuevos llevan
  la ruta en la primera línea · [x] sin `print` de depuración, TODO, secretos ni dependencias
  (los `print` de `_SV3`/`_SV4` son el canal del subproceso del test, no depuración).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] **los 30 requisitos tienen un `test_f052_rN_*`** (R14, R26 y R28 se cierran ahora;
  ver la tabla) · [x] sin red ni BBDD (dobles, AST, subproceso local) · [x] M3 y M4 en
  `current.md`, con sus comandos en `m3_F-052.md`.
- **C4 bis** [x] rigor `critico` · [x] RED real (T2–T13 en la pasada 1; review 1 en §Review 1,
  reproducido) · [x] cobertura [OK] 99,9 % · [x] totales: sin cambios de producción desde
  3424919 (vale el recálculo de la pasada 1) · [x] muertos: campaña no reejecutada (8,8 h según
  el informe); en la pasada 1 se hicieron recálculo, muestreo y RM4 · [x] sin cabecera de no
  válida · [x] RM1 · [x] RM2 · [x] RM5 · [x] RM6 N/A (ninguna guarda quitada; el delta no toca
  producción) · N/A campaña manual: la campaña fue automática · [x] ningún análisis en
  PENDIENTE (los 4 equivalentes esperan la aceptación: es la condición) · [x] «Evidencias»
  con los 4 números.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] tareas `[x]`, T8 incluida, con commits `F-052 Tn:` y `F-052 review1:` · [x] el
  worktree queda limpio · [x] `features.json` sigue en `in_progress` (lo cierra el líder).

## Cobertura de los requisitos que faltaban (los otros 27, en la tabla de la pasada 1, 8d20b1d)

| R | Test |
|---|---|
| 14 | `test_f052_r14_seco_sincronizar_solo_lee_el_repositorio`, `…_fuera_de_seco_el_repositorio_tampoco_guarda_nada`, `…_cada_sincronizacion_vuelve_a_leer` |
| 26 | sv4 `test_f052_r26_aplicar_solo_lee_de_sv5` (10 casos), `…_el_orquestador_solo_nombra_lecturas_de_sv5`; sv5 `test_f052_r26_leer_nunca_llama_a_escribir` (5 casos), `…_la_ruta_de_leer_no_nombra_escrituras` |
| 28 | raíz `test_f052_r28_registrado_sigue_congelando_en_sv3_y_sv4`, `…_las_reglas_no_conocen_la_sincronizacion`, `…_la_excepcion_vive_solo_en_aplicar_traer_de_sigrid`, `…_solo_el_orquestador_llama_al_metodo_que_salta` |

## Cambios requeridos

Ninguno en el código ni en la spec.

## Condiciones del APROBADO definitivo (las decide el humano; el líder se las lleva)

1. **Aceptar los equivalentes 5, 8, 9 y 14** (`progress/mutacion_F-052.md`).
   - El 9, aceptarlo tal cual (no se observa desde el portal) **o** pedir que se mate: con
     `ensure_ascii=True` en `firma` más un test con `'\ud800'`. Esa vía cambia producción y
     obliga a repetir la campaña de `sincronizacion.py`.
2. **Ratificar ID8 e ID10** (`design.md` §4 y §8; `azure-apps/partes.md` d098bc6).
   - Si no se ratifica ID10, en seco `aplicar` no debería escribir. Eso es código y campaña nuevos.
   - Si no se ratifica ID8, `restaurar` tendría que validar el ámbito de otra forma.
3. **M3** (`progress/m3_F-052.md`, local, obra 0404, `PRUEBA-IA`) y, antes de M4, decidir
   `SINCRONIZAR_SECO` en Azure.

## Automejora (propuesta, no aplicada)

- `reviewer.md`, revisión incremental: si el delta no toca producción, que baste
  `git diff <SHA medido>..HEAD -- services/ ':!services/*/tests/*'` vacío para dar RM1 por
  bueno. Así queda escrito el atajo que se ha usado aquí.
