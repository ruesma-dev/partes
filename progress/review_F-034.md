<!-- progress/review_F-034.md -->
Revisión incremental desde 33472c3 (pasada 2), `git diff 33472c3..ffc62b9`; la pasada 1 fue completa sobre `a6040ad` (`git diff 4bda57e...a6040ad`).

# F-034 · sv5 solo escribe en partes de Sigrid abiertos — review

## Pasada 2 (2026-10-21) · HEAD `ffc62b9`

- **Veredicto: APPROVED.** El único `[ ]` de la pasada 1 (C4: M2–M4 sin comando exacto en
  `progress/current.md`) queda resuelto, y nada más ha cambiado.
- **Nivel de rigor:** `critico` (declarado). Puertas: fase RED, cobertura ≥ 80 %, mutación
  completa sin supervivientes sin test o justificación, RM5 y MANUAL listadas con comando.
- **Delta sin código**: `git diff --name-only 33472c3..ffc62b9` = `progress/current.md`,
  `progress/impl_F-034.md`, `specs/F-034-…/design.md` y `…/tasks.md`. Ningún fichero de
  `services/`, `infra/`, `tests/` ni `harness/`: lo aprobado en la pasada 1 (código, SQL,
  tests, campaña de mutación y su SHA medido, RM1–RM6) sigue valiendo y el alcance medido no
  se mueve.
- **`bash harness/init.sh`** tal cual sobre `ffc62b9`: exit 0, «ENTORNO LISTO»; raíz `493
  passed, 3 skipped`; suites sv1–sv5 en verde por caché (árbol sin cambios desde el último
  verde); `PUERTA COBERTURA: 100.0% de 75 líneas`; `PUERTA TAMAÑO` en topes (requirements
  125/150, design 223/250, impl 209/220).

### M2–M4 contrastadas con el código (no ejecutadas: son del humano)

- **Preparación**: `/health` devuelve `modo_pruebas`, `obra_pruebas` y `database`
  (`app.py:187`); `API_PORT` = 8005 (`settings.py:55`); `..\..\.venv` existe en el repo
  principal. El `.env` de sv5 del repo principal trae `OBRA_PRUEBAS_FORZAR=false` y **0 claves
  `COLAS_*`** (contadas sin leer valores): el «si `modo_pruebas` no es `True`, PARA» y el «no
  consume `q-transfer`» son ciertos.
- **M2**: los cuerpos de `preflight`/`ejecutar` encajan en `PeticionIn`/`LineaIn`, y el del
  reajuste en `ReajusteIn`/`LineaReajusteIn`; los campos esperados (`forzada_pruebas`,
  `partes[].existe/cod/complementario/cerrados/del_periodo`, `escritas` `{registro_id,
  hmoide}`, `omitidas`, `ya_registradas`; `lineas[].can/escrita`) existen en
  `resultado_a_dict`, `ParteDestino` y `ResultadoReajuste`. `comprobar_asiento_analitico.py
  --empresa --obra --ano --mes` imprime «`cod · En registro · N linea(s) (M nuestras) · …`».
  `redeploy_partes.ps1 -Solo sv5|sv4`, válido (`ValidateSet`). Probar el SQL guardado en local
  **antes** de desplegar es mejor orden que el de la pasada 1.
- **M3**: reformulada en lo observable: R15 (complementario), R16 (`ya_registradas`) y R17
  (`comprobar` da `ok = all(editable)` y el motivo «su parte de Sigrid no esta En registro»,
  `reajuste_lineas.py:44`). Lo no observable (`parte_no_abierto`, `affected_rows = 0`) queda
  declarado y remitido a los tests de R2, R4, R9 y R11, con su motivo; es la alternativa que la
  pasada 1 aceptaba. **Limpieza**: `fase_limpiar` actúa sobre el primer parte de `parte_mes`
  (sin `ORDER BY`), borra solo `tex = 'PRUEBA-IA'` y la cabecera si `con.res` lleva la marca,
  que sv5 pone en modo pruebas («Parte … (PRUEBA-IA)», `registro_pipeline.py:541`): dos
  pasadas cubren P1 y P2 en cualquier orden. DRY-RUN previo, `git checkout` del `ANO, MES`
  local y veto a 10/2026 (líneas de F-046 en PT26/00373), presentes.
- **M4**: «N linea(s) no registradas:» existe (`static/app.js:3532`); Ctrl+F5 y lo esperado,
  concretos.
- **Coherencia**: `design.md` §9 y `tasks.md` (M2–M4 `[ ]`, del humano) dicen lo mismo que
  `current.md`; `impl_F-034.md` lo resume y remite.

### Checkpoints afectados por el delta

- **C4** [x] R1–R21 con test en verde (sin cambios) · [x] sin red ni BBDD · **[x] MANUAL en
  `current.md` con comando exacto y resultado esperado** (M2, M3, M4).
- **C5** [x] T1–T13 y M1 `[x]`; M2–M4 `[ ]` por ser del humano · [x] commit `F-034: …` del
  arreglo · [x] sin temporales (`services/partes-transfer/coverage.json` lo ignora
  `.gitignore`) · [x] `features.json` = `in_progress`.
- **Topes de tamaño** [x] los de `init.sh`; este informe, ≤ 140 líneas.
- C1–C3, C3 bis, C4 bis y C4 ter: sin cambios respecto a la pasada 1 (abajo).

## Pasada 1 (2026-10-21) · HEAD `a6040ad` · CHANGES_REQUESTED (resumen)

- **Verificación**: `init.sh` exit 0, raíz `493 passed, 3 skipped`, cobertura 100,0 % de 75
  líneas; sin caché, sv5 `736 passed` y sv4 `2359 passed, 1 skipped`;
  `test_f034_resultado_omitidas.py` `11 passed` (node v24).
- **Mutación**: recálculo puro igual al informe (3 ficheros, 252 líneas, 22 mutantes; los 4
  supervivientes existen con mismo operador y texto). Campaña no reejecutada: 227,0 s según
  el informe (> 60 s). **RM4** en copia del scratchpad: los 4 mueren con sus tests nuevos.
- **SQL**: las cinco sentencias de sv5 sobre `hmores` llevan `EXISTS (… con c WITH (UPDLOCK,
  HOLDLOCK) … c.est = ?)`; sin trampa del agregado; relectura por synckey + `hmoide`; todo
  bajo `self._lock`. Gemelos con `porcentajes`, intactos.

### Nivel de rigor (C4 bis)

- [x] Fase RED con trazas reales (T2–T4, T6–T8); R15–R18 y R20, caracterización previa.
- [x] Cobertura `[OK] 100.0%`. [x] Informe de la herramienta, sin «⚠ CAMPAÑA NO VÁLIDA»,
  «Sin veredicto» = 0, línea base por worker. [x] **RM1**: SHA medido `2afb1ae`; desde ahí
  solo tests, `progress/` y specs (también en la pasada 2). [x] **RM2**: 10,3 s × 4 workers =
  41,2 s frente a base 29,5–31,2 s. [x] **RM3**: ningún muerto equivalente.
- **RM5** N/A justificado: crítico, pero 0 equivalentes declarados (los 4 supervivientes son
  huecos con test nuevo, comprobados por RM4). [x] **RM6**: no se quitó ninguna guarda.
- Campaña manual / cero mutantes: N/A (automática, 22). [x] Sin `PENDIENTE`. [x] «Evidencias».

### Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros base.
- **C2** [x] solo F-034 `in_progress` · [x] rama `feature/F-034-…` · [x] `current.md` con
  F-034 arriba · [x] `history.md` (aún no `done`).
- **C3** [x] hexagonal (import de `synckey_de` en `parte_abierto.py`: deuda con precedente,
  justificada) · [x] primera línea con ruta · [x] sin prints, TODOs, secretos ni
  dependencias · [x] trampas del dominio respetadas.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: no hay
  `harness/rutas_sensibles.json`.
- **C4** [ ] en la pasada 1 (MANUAL sin comando) → [x] en la pasada 2. **C4 bis** [x]. **C5** [x].
- **Límite de servicio**: sv5 + `resultadoHtml` de sv4; lista cerrada sin cambios (DA8).
  `azure-apps` `5e95d6e`: solo `partes.md`, sin secretos.

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

Ninguno. (Pasada 1: añadir M2–M4 con comando exacto a `current.md`; hecho en `ffc62b9`.)

## Observaciones (no bloquean)

- **O1 · Pisado parcial** (hueco de la spec, no del código): si un conflicto pisa líneas de
  dos partes En registro y solo uno se cierra en la ventana, entra el `DELETE` del abierto y
  ni el del cerrado ni la nueva (R4): quedan menos horas, no duplicadas (lo fija
  `test_f034_r12_borradas_cuenta_varias_pisadas_por_relectura`). Hoy improbable (M1: 0
  periodos con dos partes En registro). Propuesta: que F-053 («pisar = poner a 0») lo trate.
- **O2**: `test_f046_t22_cliente_bordes.py` no se amplió (índices intactos), justificado.
- **O3 (pasada 2)**: en M3, «`$r` de M2 con `antes = 6; despues = 5`» obliga a rehacer `$r`
  a mano (es la cadena JSON ya serializada); ejecutable, pero una línea copiable lo haría a
  prueba de despistes. M2 y M3 escriben en Sigrid (0404): siguen necesitando la autorización
  del humano en el momento, como dice la propia sección.

## Automejora (propuesta, no aplicada)

- `.claude/agents/implementer.md`, paso 4: exigir que al cerrar se copien a
  `progress/current.md` las tareas `MANUAL (humano)` con su comando exacto; C4 lo pide y hoy
  depende de que el implementer lo recuerde (en F-034 costó una pasada de review).
