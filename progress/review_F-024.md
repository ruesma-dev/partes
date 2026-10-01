<!-- progress/review_F-024.md -->
Revisión completa (pasada 1) · `ce04e20..2565a26` (spec de F-021, explore y spec de F-024 fuera por encargo del líder)

# F-024 · Review

**Veredicto: APPROVED.** Condición de cierre, que no le toca al reviewer: en
rigor `critico` el humano tiene que **aceptar el equivalente n.º 12** (lo he
reproducido y recomiendo aceptarlo, ver RM5). M1–M5 siguen siendo MANUAL.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, mutación completa con 0 supervivientes sin test o sin
justificación aceptada por el humano, y MANUAL con su comando exacto.

## Verificación ejecutada

- `bash harness/init.sh` tal cual: **exit 0**. Raíz 419 passed / 1 skipped;
  sv1–sv5 en verde; COBERTURA [OK] 99,7 % (346/347); TAMAÑO [OK].
- Suites **sin caché**: sv5 203 passed · sv3 640 · sv4 1219 (104,5 s).
  `node --check app.js` OK. Árbol limpio; las copias, en el scratchpad.

## Lo que pidió el líder

1. **sv5 solo lee**: sus tres lecturas van por `_read` (`/api/sql/read`,
   `truncated` ⇒ excepción), con SQL estático, `?` e ids `int`. Sin lock ni
   `escribir` (probado con un lock retenido y un `escribir` que revienta).
2. **`borrado_sigrid` solo si no está.** Se busca por `synckey_de` (la misma
   lectura que el paso 6 del pipeline). Si no aparece, se acepta el respaldo
   por `hmores.ide` solo con `synckey` vacía y el mismo recurso, fecha y
   `hmoide`. Si tampoco, `borrada`. Lectura fallida o truncada: 502 sin
   veredictos. En sv4, `ok:false`, una excepción, un timeout o un veredicto
   ausente o malformado ⇒ el lote no se aplica y la comprobación se para. El
   CAS es `get(with_for_update=True)` + `registrado` + `hmores_ide` igual al
   enviado, en una sola transacción (tests r11_*, r14_*).
3. **DA7.** Lo impone el servidor: `registrado` no viaja nunca, y
   `borrado_sigrid` solo con `incluir_borradas`, en preflight, ejecutar y
   encolar, también por `obra_key` («Aprobar todo»). Si no queda nada, 422
   sin llamar a sv5 ni publicar. «Reaprobar» pasa la línea a `encolado`
   (`r22_payload_encolar_reaprobar_una_borrada`). Las 35 quedan protegidas
   tanto antes como después de comprobarlas.
4. **No congela** en sv4 ni en sv3 (guardián de raíz). El borrado
   definitivo usa `es_registrado`. Desaprobar no llama a sv5.
5. **Vista.** El `fetch` sale después de pintar, sin `forzar` y con
   `AbortController` a 90 s; si falla, solo deja una nota. El `GET` no llama a
   sv5 (r18). El TTL se sella al reservar (r19_*). La vista de persona
   también comprueba (`origen=vista-trabajador`).
6. **Modal** sin `reload()` al encolar: sondea cada 3 s durante 120 s
   (JS: M5). 7. **Límite de servicio**: sv4 no lee `hmores`; los ORM están
   intactos y la lista cerrada no crece.

**Desviaciones 1–8 de `impl_F-024.md`: todas aceptables.** 1, 2 y 5 son
conservadoras. 3: el origen se sanea. 4: 502 si sv5 falla y 503 si no está
configurado. 6: ver la observación 3. 7: normaliza igual que la congelación.
8: el guardián de F-016 se amplía, no se afloja.

## Checkpoints

- C1 [x] init.sh exit 0 · [x] ficheros del arnés.
- C2 [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md`
  con F-024 arriba (el resto es histórico, como en reviews anteriores) ·
  [x] las 13 `done` están en `history.md`.
- C3 [x] hexagonal: `comprobacion_lineas` importa `synckey_de` igual que
  `registro_pipeline` (R2, «misma lectura») · [x] ruta en la primera línea de
  los 6 ficheros nuevos · [x] sin `print` de producción (los del guardián son
  la salida del subproceso), sin TODO, secretos ni dependencias nuevas ·
  [x] trampas: se compara `reside`, las incidencias no comparan horas y no
  hay cambio de schema.
- C3 bis N/A: no toca `docs/referencia/` y no añade PDF ni ofimática
  (`--diff-filter=A`: 0).
- C4 [x] trazabilidad (tabla) · [x] sin red ni BBDD: `httpx` simulado, hosts
  `*.interno`/`*.invalid`, SQLite, datos sintéticos · [x] M1–M5 en
  `current.md`, con los comandos en `impl_F-024.md` y en el design §9.
- C4 bis
  - [x] rigor declarado.
  - [x] fase RED con trazas reales para R1–R4, R8–R11, R14–R17, R19, R22
    y R28. R13 en sv4 ya pasaba por construcción; su evidencia es la copia
    de sv3 rota (2 failed). R18 es un requisito negativo; su parte JS va a
    M3.
  - [x] cobertura 99,7 %.
  - [x] recálculo propio: `alcance_de_feature` da 10 ficheros y 746 líneas;
    `generar_mutantes` da **175** (100 de sv4 y 75 de sv5). Coincide.
  - [x] Tiempo total 4.130,5 s > 60 s: **campaña no reejecutada** (69 min
    según el informe); recálculo más RM1–RM6.
  - [x] coste: 4.130,5 × 6 ÷ 175 = 141,6 s/mutante ≫ 1 s.
  - [x] sin «⚠ CAMPAÑA NO VÁLIDA»; base rota = 0.
  - [x] RM1: SHA `156d6e3`. Después solo cambian `progress/`, `tasks.md` y
    tres ficheros de tests, así que el alcance de producción es idéntico.
  - [x] RM2: 23,6 × 6 = 141,6 s frente a bases de 278 s (sv4) y 12 s (sv5).
    El ponderado da 164 s, y queda por debajo por `-x`. Coherente.
  - [x] RM5: el implementer razonó el #12 sin dar un script; **la
    demostración ejecutable la he hecho yo**. En una copia, con
    `sed -i '98s/return False/return True/' application/services/comprobacion_lineas.py`,
    `tests/test_f024_comprobacion.py` da 62 passed. Un diferencial de
    `clasificar` original frente a mutado sale idéntico en **1.296
    combinaciones** de `hmores_ide`, `hmoide`, recurso, fecha, acierto por
    `synckey`, `synckey` de la fila por `ide` (None, '', propia, ajena) y
    partes. Comprobé además que el módulo cargado era el mutado.
    Equivalente: **lo acepta o lo rebate el humano.**
  - [x] RM6: tras la medición no se tocó producción y no se quitó ninguna
    guarda.
  - [x] campaña automática.
  - [x] 23 supervivientes analizados: 22 muertos con un test nuevo y 1
    equivalente; ninguno en PENDIENTE. Muestreé el #4, #5, #7, #12 y #23:
    existen en el generador con el mismo operador y texto. Reproduje dos
    muertes en copias (RM4): el #23 (`is not None`) hace fallar
    `r1_endpoint_respeta_el_comprobador_inyectado_sin_pipeline` y el #7
    (`with_for_update=False`) hace fallar
    `r11_repo_lee_cada_linea_con_bloqueo_de_fila`.
  - [x] «Evidencias» con 6 workers · [x] ningún N/A sin motivo.
  - RM3: repasé los 175; ningún muerto es equivalente.
- C4 ter N/A: no existe `harness/rutas_sensibles.json`.
- C5 [x] T1–T18 `[x]`, con 18 commits `F-024 Tn:` más el de estilo ·
  [x] nada sin trackear · [x] `features.json` en `in_progress`.

## Cobertura (requisito → test, prefijo `test_f024_`)

| Req. | Test |
|---|---|
| R1–R9 (sv5) | `r1_endpoint_no_toma_el_lock_de_escritura`, `r2_clasificar_acierto_por_synckey_es_presente`, `r3_clasificar_ide_reutilizado_es_borrada[*]`, `r4_clasificar_cabecera_borrada`, `r5_…referencias_actuales`, `r6_…tolerancia_justo_en_el_limite`, `r7_cliente_lineas_por_ide_en_lotes_de_200`, `r8_endpoint_truncated_es_502`, `r9_…es_422_sin_leer` |
| R10–R16 | `r10_repo_borrada_pasa_a_borrado_sigrid_y_conserva_rastro`, `r11_repo_si_cambio_su_hmores_ide_no_se_toca`, `r12_repo_presente_con_referencias_nuevas…`, gemelos de raíz (R13), `r14_servicio_lote_fallido_no_aplica_y_para`, `r15_vuelo_ya_registrada…`, `r16_motivo_explica_la_via_nueva` |
| R17–R19, R21 | `r17_endpoint_comprobar_aplica_y_responde`, `r18_…servir_las_vistas_no_llama_a_sv5`, `r19_recientes_*`, `r21_endpoint_log_con_el_origen` |
| R22–R24, R26–R28, R30 | `r22_payload_*`, `r23_payload_todo_excluido_es_422_con_el_motivo`, `r24_vista_*`, `r26_vista_*`, `r27_payload_encolar_devuelve_registro_ids`, `r28_endpoint_estado_cuenta_sin_escribir`, `r30_vista_el_tooltip…` |
| R20, R25, R29 · R31, R32 | JS: `node --check` + M3/M5 · M3/M4 + suites F-002/F-004/F-017/F-023 en verde |

## Observaciones (no bloquean)

1. Ruff: no es exacto que los nuevos queden limpios. `test_f024_comprobacion.py`
   de sv5 tiene 3 I001 (l. 14, 221, 336); `api/app.py` de sv5 suma 8 UP045 y
   1 RUF100, y `sigrid_write_client.py:357` un B010. Autofixable.
2. Con varios lotes, un fallo a mitad deja aplicados los anteriores (lo pide
   R14). Una excepción de PG al aplicar devuelve 500, sin cambios.
3. Vista de persona con hasta 10 lotes: el navegador corta a los 90 s y
   dice «no se pudo» aunque sv4 termine (inocuo por el CAS y el TTL).

## Automejora propuesta (no aplicada; genérica ⇒ `arnes-base`)

- RM5 / plantilla de `mutacion_F-XXX.md`: exigir el **comando exacto** de la
  demostración de cada equivalente. Aquí tuvo que construirla el reviewer.
- `reviewer.md`: si no se relanza la campaña, reproducir dos «muertos con
  test nuevo» (aquí, #7 y #23).
