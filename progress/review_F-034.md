<!-- progress/review_F-034.md -->
Revisión completa (pasada 1), `git diff 4bda57e...HEAD` con dev `4bda57e` y HEAD `a6040ad`.

# F-034 · sv5 solo escribe en partes de Sigrid abiertos — review

- **Veredicto: CHANGES_REQUESTED** por un único `[ ]`, documental (C4: las verificaciones
  MANUAL no están en `progress/current.md` con su comando exacto). Código, SQL, tests y
  campaña de mutación, bien: ningún hallazgo de código bloqueante.
- **Nivel de rigor:** `critico` (declarado en `features.json`): fase RED, cobertura ≥ 80 %,
  mutación completa con cero supervivientes sin test o justificación, RM5 y MANUAL listadas.

## Verificación ejecutada por el reviewer

- **`bash harness/init.sh`** tal cual sobre `a6040ad`: exit 0, «ENTORNO LISTO»; raíz `493
  passed, 3 skipped`; `PUERTA COBERTURA: 100.0% de 75 líneas`; tamaño en topes. **El
  `0xC0000005` de `test_f024_borrado_no_congela_gemelos.py` NO se repitió.** Las suites de
  servicio salieron por caché, así que las reejecuté aparte sin caché: **sv5 `736 passed`**;
  **sv4 `2359 passed, 1 skipped`** (5 min 36 s); `test_f034_resultado_omitidas.py` `11 passed` con `node` v24.
- **Recálculo puro** (`alcance_de_feature("F-034", base="4bda57e")` + `generar_mutantes`):
  3 ficheros, **252 líneas** (99 + 87 + 66), **22 mutantes**: igual que el informe. Los 4
  supervivientes existen con el mismo operador y texto (`registro_pipeline.py:599` ×2,
  `sigrid_write_client.py:569` y `:571`).
- **Campaña no reejecutada: 227,0 s según el informe (> 60 s).** **RM4** sí: copia de
  `services/partes-transfer` en el scratchpad, cada superviviente aplicado con
  `aplicar_mutante` y los tests F-034 de cliente y pipeline: `1 failed`, `2 failed`, `1
  failed`, `1 failed`; sin mutante `59 passed`. `git status` del worktree, limpio.
- **Gemelos con `porcentajes`**: `git diff --quiet 4bda57e HEAD` sobre `estado_parte.py`,
  `cuenta_analitica.py`, `reajuste_lineas.py`, `reglas_registro.py` → 0. `stmts_crear_parte`
  textualmente igual (solo aparece detrás el helper nuevo); `_crear_parte` idéntico. Su
  `test_f037_copias_partes.py` vigila solo `estado_parte.py` y `cuenta_analitica.py`.

## Revisión del SQL y del flujo

- Sentencias de sv5 sobre `hmores` (grep fuera de tests): `stmt_insert_linea`,
  `stmt_borrar_linea`, `stmt_guardia_reajuste`, `stmt_actualizar_linea`,
  `stmt_insertar_extra`. **Las cinco** llevan `EXISTS (SELECT 1 FROM con c WITH (UPDLOCK,
  HOLDLOCK) WHERE c.ide = <?|hmores.hmoide|h.hmoide> AND c.est = ?)`, fijado con texto y
  parámetros exactos. `prueba_escritura_sigrid.py`, fuera por diseño (§1.5).
- **Sin trampa del agregado**: `SELECT x.n, … FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM
  hmores WITH (UPDLOCK, HOLDLOCK)) x WHERE <guarda> [AND NOT EXISTS …]` ⇒ 0 filas si la
  guarda falla. 19 columnas = 19 valores; `?` = parámetros (16 + `hmoide, est` + pisadas).
- La guarda mira el parte correcto (`hmores.hmoide` = `hmo.ide` = `con.ide`); `self._est` =
  `settings.est_parte_activo` (`main.py:85`, `app.py:131`), el mismo que `_est_registro`.
- Relectura: escrita = synckey releída **y** `hmoide` del elegido (int contra int);
  `borradas` por `lineas_por_ide`; una `partes_del_periodo` por periodo con no escritas;
  `parte_no_abierto` (pisada viva primero, luego elegido) o `no_escrita` + ERROR; sin `try`
  (R14); todo bajo `self._lock` (R8).
- **Sin escrituras reales**: el cliente de los tests apunta a `http://sigrid.invalid` y solo
  construye sentencias; los pipelines usan `SigridFake`/`SigridReajusteFake`.
- **Modal sv4**: `esc(k)` sobre la clave, números en lo demás, sin nombres ni `registro_id`.

## Nivel de rigor (C4 bis)

- [x] Fase RED con trazas reales: T2 (R9, R11), T3 (R1–R4, R7), T4 (R5, R6), T6 (R4, R12),
  T7 (R8–R11, R13), T8 (R19); R15–R18 y R20, caracterización en verde previa (`6 passed`).
- [x] Cobertura `[OK] 100.0%`. [x] Informe de mutación de la herramienta, totales
  verificados, sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» = 0, línea base por worker.
- [x] Coste por mutante 227,0 × 4 ÷ 22 = 41,3 s. [x] **RM1**: SHA medido `2afb1ae`; de ahí a
  HEAD solo cambian tests, `progress/` y `tasks.md`: el alcance medido es el revisado.
- [x] **RM2**: media 10,3 s × 4 workers = 41,2 s frente a base 29,5–31,2 s, coherente.
- [x] **RM3**: ninguno de los 18 muertos es equivalente (`sum(2 …)`, `or`→`and`, `!=`↔`==`,
  `is not`, `grupo[1]`, `LIMITE_MOTIVO = 256`, `sql -=`, `//`, `tex and ""`, `- str`…).
- **RM5** N/A justificado: crítico, pero **0 equivalentes declarados** (los 4 supervivientes
  son huecos con test nuevo, comprobados por RM4): no hay muestra que reproducir.
- [x] **RM6**: no se quitó ninguna guarda (`hit is not None` sigue en `confirmar_escritas`).
- Campaña manual / cero mutantes: N/A (automática, 22). [x] Ningún análisis `PENDIENTE`.
- [x] «Evidencias» con los cuatro números y los workers (4).

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros base.
- **C2** [x] solo F-034 `in_progress` · [x] rama `feature/F-034-…` · [x] `current.md`:
  F-034 arriba; el resto es el registro acumulado previo de `dev` (criterio de las reviews de
  F-046 y F-050) · [x] `history.md` (F-034 aún no es `done`).
- **C3** [x] hexagonal (el import de `synckey_de` desde infraestructura en
  `parte_abierto.py` es deuda con precedente en `reajuste_lineas.py` y
  `comprobacion_lineas.py`, justificada en `current.md`) · [x] primera línea con ruta · [x]
  sin prints, TODOs, secretos ni dependencias; solo el DNI sintético `00000000T`, con
  precedente en F-015 · [x] trampas: `reside` sigue siendo el recurso; incidencias y ORM
  sin tocar.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: no hay
  `harness/rutas_sensibles.json`.
- **C4** [x] R1–R21 con test trazable en verde · [x] sin red ni BBDD · **[ ] MANUAL en
  `current.md` con comando exacto**: la sección F-034 de `progress/current.md` no nombra M2,
  M3 ni M4 (acaba en «Siguiente: reviewer»). Están en `design.md` §9 y en el informe, sin
  comando exacto: M3 no dice cómo se lanza «un `stmt_insert_linea` sobre el parte cerrado»
  ni con qué se ve `affected_rows = 0`.
- **C4 bis** [x] (arriba).
- **C5** [x] T1–T13 `[x]`, 13 commits `F-034 Tn:`; M2–M4 abiertas por ser del humano · [x]
  sin temporales · [x] `features.json` = `in_progress`.
- **Límite de servicio**: sv5 + `resultadoHtml` de sv4; lista cerrada sin cambios (DA8).
  **azure-apps `5e95d6e`**: solo `partes.md` (pasos 5–6, «Qué se rompe», nota a
  `porcentajes`), sin secretos, árbol limpio. Tildes en docs y spec; los motivos y
  comentarios de sv5 van sin tildes por DA3 y el estilo de esos ficheros.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R3 | `test_f034_r1_*`, `r2_*`, `r3_*` (`test_f034_cliente_guarda.py`), `test_f021_r14_*` ampliados |
| R4 | `test_f034_r4_*` (cliente y pipeline: la pisada que no entra bloquea la nueva) |
| R5, R6 | `test_f034_r5_*`, `r6_*`, `test_f046_r24_*`/`r25_*` ampliados |
| R7 | `test_f034_r7_el_cliente_tiene_un_solo_delete`, `…_ninguna_escritura_en_con_ni_hmo…` |
| R8 | `test_f034_r8_todo_corre_bajo_el_lock` |
| R9, R10 | `test_f034_r9_*` (ejemplo 1, dos periodos, lotes), `r10_*`, `confirmar_escritas` (puro) |
| R11–R14 | `test_f034_r11_*`, `r12_*` (5), `r13_warning_sin_nombres`, `r14_*` (3) |
| R15–R18 | `test_f034_r15_*`, `r16_*`, `r17_*` (2), `r18_*` |
| R19, R20 | `services/partes-front/tests/test_f034_resultado_omitidas.py` |
| R21 | lectura: `docs/ARCHITECTURE.md` semántica 16 y `azure-apps/partes.md` |

## Cambios requeridos

1. `progress/current.md`, sección «F-034 · in_progress»: añadir M2, M3 y M4 con su comando
   exacto y el resultado esperado. M2: `.\infra\redeploy_partes.ps1 -Solo sv5` y `-Solo sv4`
   y el registro en modo pruebas (`OBRA_PRUEBAS_FORZAR=true`, obra 0404, `PRUEBA-IA`) ⇒
   `registrado` en el parte En registro de 0404. M3: cómo se cierra el parte de pruebas, qué
   se reaprueba y **con qué herramienta y comando** se ve que un INSERT guardado sobre el parte
   cerrado afecta 0 filas (o reformularla en algo observable desde el portal: `omitido`
   `parte_no_abierto` y complementario al reaprobar), con la limpieza (`cd
   services/partes-transfer` y `python prueba_escritura_sigrid.py limpiar --ejecutar`). M4:
   Ctrl+F5 en el portal y qué debe verse en el modal. Commit `F-034: …`.

## Observaciones (no bloquean)

- **O1 · Pisado parcial** (hueco de la spec, no del código): si un conflicto pisa líneas de
  dos partes En registro y solo uno se cierra en la ventana, el `DELETE` del abierto entra,
  el del cerrado no y la nueva tampoco (R4): quedan menos horas, no duplicadas
  (`test_f034_r12_borradas_cuenta_varias_pisadas_por_relectura` lo fija). Igual si `DELETE`
  e `INSERT` caen en lotes distintos. Hoy improbable (M1: 0 periodos con dos partes En
  registro). Propuesta: que F-053 («pisar = poner a 0») lo trate.
- **O2**: `design.md` §2 preveía ampliar `test_f046_t22_cliente_bordes.py`; no hizo falta
  (índices intactos) y está justificado en `current.md`.

## Automejora (propuesta, no aplicada)

- `.claude/agents/implementer.md`, paso 4: exigir que al cerrar se copien a
  `progress/current.md` las tareas `MANUAL (humano)` con su comando exacto; C4 lo pide y hoy
  depende de que el implementer lo recuerde (aquí quedó solo en `design.md` §9 y el informe).
