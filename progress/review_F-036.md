<!-- progress/review_F-036.md -->
Revisión incremental desde 78148f6 (pasada 2): `git diff 78148f6..068aba9`. Pasada 1 completa: `git diff dev...f5104ca`.

# F-036 · Review

**Veredicto: APPROVED** (pasada 2). Pasada 1: CHANGES_REQUESTED solo por los comandos de M2 y M3.

**Rigor:** `critico` (declarado en `features.json`): fase RED, cobertura de lo cambiado ≥ 80 %, mutación con 0
supervivientes sin justificar y verificaciones `MANUAL (humano)` con su comando exacto.

## Pasada 2 (incremental desde `78148f6`)

- **Delta**: `dd7309c` (docs de M1–M3, I001, `_METODOS_RECURSO`), `a6eeb64` (R6 opción A), `b431a08` (mutación),
  `068aba9` (evidencias). Código: `casado_recurso.py`, `seleccion_sigrid.py`, `medicion_casado.py` (comentario) y
  `parte_records.py` (comentario), todo sv3. **sv4, sv5, ORM y lista cerrada sin diff**: no invalida nada de lo ya
  aprobado (el delta solo añade una salida antes del alias; R4/R5/R15 intactos).
- **Cambio 1 resuelto** [x]: `current.md` trae M1 (comando), el despliegue (`redeploy_partes.ps1 -Solo sv3,sv5`),
  M2 (Log Analytics con `[recurso-concil] registros=` y el INFO de R3), M2b y M3 (SQL de solo lectura en `partes`),
  con lo esperado y «las lanza el humano». Comprobé las columnas contra `orm_models.py` (`obra_codigo`,
  `created_at_utc`, `line_index`, `parte_estado`, `is_active`) y los valores (`sin_recurso`, empresa 28 = Porsan).
- **R6 nuevo (opción A del humano)** [x]: con DNI leído y `casar_por_dni` = `desconocido` (la persona no tiene
  **ningún** recurso persona), si `IndicePersonas.dni_conocido` (ficha `emp` de cualquier empresa/estado o recurso de
  cualquier clase con ese `res.cif`) ⇒ `dni_sin_recurso` y fin, sin alias ni nombre. Con recursos persona fuera de
  la empresa o de baja ya cerraba (`dni_otra_empresa`/`dni_solo_baja`, R5): juntos cubren «sin recurso persona de
  alta en la empresa del parte». Solo un DNI que Sigrid no conoce sigue al alias y al nombre. Spec (R6, design §4,
  T19), `ARCHITECTURE.md`, `partes-proyecto.md` y `azure-apps` (`de0d1b0`) alineados. Cabe en `String(24)` (15).
- **sv4 lo trata como sin casar sin tocarlo** [x]: leí `services/partes-front/infrastructure/database/parte_repository.py`:
  `esta_casado` = `empleado_ide` no NULL **o** método en `METODOS_RECURSO` ⇒ `False`; `_sin_casar_en_cola` =
  `empleado_ide IS NULL AND (método NULL OR NOT IN (recurso_dni, recurso_nombre))` ⇒ entra en Conciliar. sv4 no
  tiene etiquetas por método `dni_*`. Test de pipeline: línea sin `empleado_*`, `recurso_ide` NULL y
  `review_required = True`. `git diff 6e56244..HEAD -- services/partes-front` vacío.
- **Fase RED reproducida**: los tests finales sobre `git archive 78148f6`: **12 failed, 138 passed** (3 de casado,
  8 de `dni_conocido`, 1 de pipeline), igual que la traza T19 del informe.
- **Mutación**: recálculo puro **749 líneas, 110 mutantes** (= informe; +2 en `seleccion_sigrid.py`: `- {""}`→`+`,
  `or`→`and` de `dni_conocido`). SHA medido `a6eeb64` (RM1: después solo `progress/` y `tasks.md`). 110/110
  muertos, 0 supervivientes, 0 sin veredicto. **Campaña no reejecutada entera: 680,6 s según el informe** (> 60 s).
  RM2: 6,2 s × 6 workers = 37 s frente a base ~41 s: coherente. **RM4** sobre copia `git archive HEAD`: `or→and` en
  `dni_conocido` (8 fallos), guarda R6 de `casar_trabajador` → `if False:` (4) y sin el `- {""}` (2): **caen las 3**.
  RM3: ningún equivalente muerto. RM6: no se quitó ninguna guarda.
- `bash harness/init.sh` completo: **exit 0, ENTORNO LISTO**; raíz 454 passed, 3 skipped; sv1–sv5 verdes (caché por
  hash del árbol); **suite sv3 sin caché por mí: 928 passed**; sv4/sv5 sin cambios desde mi ejecución sin caché de
  la pasada 1 (1682 / 524). **COBERTURA [OK] 99,7 %** (314/315); TAMAÑO OK.
- Merge de prueba con dev (`merge-tree`): siguen chocando solo `BACKLOG.md`, `features.json` y `current.md`.
- Menores de la pasada 1 resueltos: I001 corregido; `_METODOS_RECURSO` se queda (application no importa de un
  pipeline) con test que lo iguala a `METODOS_RECURSO`.

## Pasada 1 (resumen; completa en `git show 78148f6:progress/review_F-036.md`)

- init.sh **sin caché de suites**: raíz 454/3 skipped, sv1 74, sv2 8, sv3 915, sv4 1682, sv5 524; COBERTURA 99,7 %.
- **RED** reproducida sobre `6e56244` con los tests finales (caracterización R20/R21 18 passed; el resto en rojo).
- **Mutación**: 727 líneas / 108 mutantes recalculados; RM4 sobre 6 (todos muertos); revisados los 108 (RM3).
- **Merge con dev (F-037)**: código limpio; sobre el árbol mezclado sv3 985 passed y guardianes raíz 87 passed.
- **Herramienta de impacto** de solo lectura y **no ejecutada contra producción**: sin `.env` de sv3 en el worktree
  (`main()` sale con 2 antes de la red), sin `logs/` y ningún `medicion_casado_*` en `PycharmProjects/` ni `%TEMP%`.

## Decisiones del humano y lista cerrada

- **Casado contra recursos persona** [x]: DNI → alias → nombre sobre `IndicePersonas`, solo `cla = 1`, de alta a la
  fecha y de la empresa del parte. **DA1** [x]: DNI del recurso = `emp.dni` de la ficha y, si vacío, `res.cif`; el
  casado busca por ambos (`_recursos_de` por `conide` y por `res.cif`) y el conciliador vuelve al mismo (R15).
- **DA2** [x]: solo partes nuevos (R22). **DA3** [x]: `CLA_PERSONA = 1` en sv3 y `AND res.cla = 1` en las dos ramas
  de sv5 `recursos_por_dni` (único consumidor: `elegir_por_dni`), entrada en `CLAUDE.md` y guardián
  `tests/test_f036_recurso_persona_gemelos.py` (prueba también que sabe fallar).
- **Copias de la lista cerrada** [x]: la elección por DNI cambia a la vez en sv3 y sv5. `de_alta`, sv5
  `coherencia_recurso.py`, `recurso_conciliador.py` (`esta_congelado`, `ESTADOS_CONGELADOS`), sv4 (`congelacion.py`),
  `jornada_resolver.py` y `orm_models.py`: diff vacío; guardianes F-015/F-023/F-024 sin tocar y verdes.
- **Solo lectura** [x] (R23): engine propio, `SET TRANSACTION READ ONLY` y `rollback`; tests que capturan solo
  `SELECT` y prohíben escrituras y otra ruta que `/api/sql/read`. Sin nombres ni DNIs (R27).

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-036, pasa a `done` con este informe) · [x] rama `feature/F-036-…` ·
  [x] `current.md` con F-036 arriba; el resto son entradas vigentes de otras features (práctica del repo) ·
  [x] las `done` con resumen (el de F-036 lo añade el líder al cerrar, como en F-037).
- **C3** [x] hexagonal (núcleos puros en application; script de consola en la raíz del servicio) · [x] ruta en la
  primera línea de todos los `.py` tocados · [x] `print` solo en el script de consola; sin TODOs, secretos ni
  dependencias nuevas · [x] trampas: empleado ≠ recurso reforzado (`empleado_reside` = recurso; `recurso_ide` solo
  del conciliador, R16), incidencias sin tocar, sin schema.
- **C3 bis** [x] solo se edita `docs/referencia/partes-proyecto.md` (cabecera intacta) · [x] sin PDF/ofimática
  (`--diff-filter=A` vacío) · [x] barrido de líneas añadidas (correo, IPv4, GUID, `password|secret|token|apikey|
  AccountKey|Bearer`, DNI `\d{8}[A-Z]`): solo DNIs sintéticos de tests; el delta añade `12121212R`/`70707070X`,
  también sintéticos · N/A redacciones: nada que redactar.
- **C4** [x] R1–R28 con test `test_f036_rN_*` en verde (tabla) · [x] sin red ni PostgreSQL (SQLite y dobles) ·
  [x] MANUAL M1, despliegue, M2, M2b y M3 en `current.md` con comando exacto (pasada 1 `[ ]`, cerrado en la 2).
- **C4 bis**
  - [x] `rigor` declarado: `critico` · [x] **Fase RED**: trazas reales T2–T12 y T19, reproducidas por mí.
  - [x] **Cobertura** `[OK]` 99,7 % (314/315; falta el `raise` de `_nodo` del guardián).
  - [x] **Mutación** generada por la herramienta; totales recalculados (749 / 110).
  - [x] **Muertos comprobados**: > 60 s, no reejecutada entera; RM4 en pasada 1 (6) y 2 (3), todos muertos.
  - [x] Coste por mutante: 680,6 × 6 ÷ 110 = 37 s (≫ 1 s) · [x] sin «⚠ CAMPAÑA NO VÁLIDA», base rota = 0.
  - [x] RM1 · [x] RM2 (arriba) · [x] RM5 N/A justificado: ningún superviviente declarado equivalente (los 3 de la
    primera campaña se resolvieron quitando código muerto) · [x] RM6: sin guardas quitadas (`round` redundante:
    `name_similarity` ya devuelve `round(…, 4)` o `0.0`).
  - N/A campaña MANUAL (hubo automática) · [x] sin `PENDIENTE` · [x] «Evidencias» con los 4 números y 6 workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md` T1–T19 `[x]`, commit `F-036 Tn:` por tarea · [x] sin artefactos sin trackear ·
  [x] `features.json`: `done` en el commit de este informe.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1–R3 | `r1_el_sql_de_recursos_lee_res_cla` (+2) · `r2_…_no_es_persona_no_casa` (+7) · `r3_…_sin_dni_no_casa` (+4) |
| R4, R5 | `r4_r13_dni_con_ficha_enlazada` (+10) · `r5_dni_sin_candidato_cierra_sin_alias_ni_nombre` (+5) |
| R6 | `r6_sin_dni_o_dni_desconocido_sigue_al_alias_y_al_nombre` · `r6_persona_conocida_sin_recurso_persona_queda_sin_casar` (3) · `r6_dni_conocido` (8) · `r6_persona_sin_recurso_persona_sin_casar_y_a_revision` (pipeline) · `r6_el_metodo_cabe_en_la_columna` (+2) |
| R7, R8 | `r7_r14_ficha_en_a_y_recurso_sin_enlazar_en_b` (+1) · `r8_alias_con_dni` (+7) |
| R9 | por diseño (§7): diff vacío de sv4 y `orm_models.py`, comprobado por mí |
| R10–R12 | `r10_nombre_puntua_el_maximo_de_recurso_y_ficha` (+10) · `r11_…nombre_ambiguo` (+6) · `r12_…umbral_none` (+4) |
| R13–R16 | `r13_r14_r15_el_conciliador_confirma_el_recurso_del_casado` (SQLite) · `r14_dni_sin_ficha_recurso_dni` (+5) · `r16_…no_escribe_recurso` |
| R17–R19 | `r17_sin_fichas_de_recurso`, `r17_nadie_los_usa` · sv5 `r18_las_dos_ramas_filtran_recurso_persona` (+1) · raíz `r19_*` (11) |
| R20–R22 | caracterización `r20_*` · `r21_congelada_no_se_re_resuelve…` · `r22_un_parte_ya_guardado_no_se_re_casa` (+1) |
| R23–R28 | `test_f036_medicion.py`: `r23_*` (9), `r24_*` (5), `r25_*` (7), `r26_*` (13), `r27_*` (5), `r28_*` |
| R29 | revisado contra design §6: `ARCHITECTURE.md`, `partes-proyecto.md`, `CLAUDE.md`, `azure-apps` (`6355a5f`, `de0d1b0`) |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **Merge con dev (F-037)**: resolver a mano `harness/features.json` (conservar las dos entradas nuevas),
  `progress/current.md` (los dos bloques) y regenerar `BACKLOG.md` con `init.sh`.
- **F-035** ya usa `res.cla = 1` en sv4 `_SQL_RECURSOS_ACTIVOS`: al integrarla, ampliar el guardián de F-036 a esa
  copia (hoy vigila sv3 y sv5).
- Antes de desplegar, M1 dirá cuántas líneas pasarían a `dni_sin_recurso` si se re-casaran (`casado_pierde_casado`):
  por DA2 no se re-casan, solo afecta a partes nuevos.

**Automejora (propuesta, no aplicada)**: `.claude/agents/implementer.md`, en `critico`, comprobar antes de terminar
que **cada** MANUAL de `current.md` trae comando o consulta pegados (F-037 y F-036 rechazadas por lo mismo).
