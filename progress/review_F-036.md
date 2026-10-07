<!-- progress/review_F-036.md -->
Revisión completa (pasada 1): `git diff dev...HEAD` (base `6e56244`, HEAD `f5104ca`).

# F-036 · Review

**Veredicto: CHANGES_REQUESTED** (solo documental: comandos exactos de M2 y M3 en `progress/current.md`; el
código, los tests, la lista cerrada y la mutación están bien).

**Rigor:** `critico` (declarado en `features.json`): fase RED, cobertura de lo cambiado ≥ 80 %, mutación con 0
supervivientes sin justificar, y verificaciones `MANUAL (humano)` listadas **con su comando exacto**.

## Qué ejecuté (resultado real)

- `bash harness/init.sh` tal cual desde el worktree, **sin caché de suites** (aparté `.arnes_cache` al
  scratchpad para forzarlas): raíz 454 passed, 3 skipped; sv1 74, sv2 8, **sv3 915**, sv4 1682 (1 skipped), **sv5
  524**; su único KO fue TAMAÑO por este informe a medio escribir. 2.ª, tras recortarlo: **exit 0, ENTORNO LISTO**;
  **PUERTA COBERTURA [OK] 99,7 %** (308/309); ruff 621 avisos (no bloquea).
- **Fase RED reproducida**: `git archive 6e56244` (código previo) en el scratchpad con los tests finales de F-036:
  caracterización **18 passed** (R20/R21, como declara T1); `maestro` 25 failed; `seleccion`, `casado`, `pipeline` y
  `medicion` error de colección (no existen `casar_por_dni`, `casado_recurso`, `medicion_casado`); sv5 R18 1 failed /
  1 passed; guardián raíz R19 8 failed / 3 passed. Coincide con las trazas T2–T12 del informe.
- **Mutación, recálculo puro**: `alcance_de_feature("F-036")` = 11 ficheros, **727 líneas**; `generar_mutantes` =
  **108** (2+15+7+57+11+2+0+0+0+14+0). Coinciden con el informe. Los SQL (`res.cla` en sv3/sv5) no generan mutantes
  (cadenas): los vigilan R1, R18 y el guardián R19.
- **Campaña no reejecutada entera: 882,8 s según el informe** (> 60 s). **RM4** sobre una copia `git archive HEAD`
  en el scratchpad: reproduje 6 de los 108 al pie de la letra, los más sospechosos de equivalencia, y **los 6 caen**:
  `medir_casado_recursos.py:102` `or→and` (1 fallo), `empleado_matcher.py:60` `<→<=` (2), `medicion_casado.py:139`
  y `:163` `fecha_int or hoy→and hoy` (1 y 1), `seleccion_sigrid.py:187` `==→!=` (11), `medicion_casado.py:166`
  `or→and` (12). Revisé además los 108 uno a uno buscando equivalentes (RM3): ninguno; los dudosos
  (`exist_ok`, `__name__`, `memo_nombre[1]`, `assert r is None`) los mata un test concreto (`main` con carpeta
  existente, `SystemExit` al importar, `IndexError`, `AssertionError`).
- **Merge de prueba con dev** (`git merge-tree --write-tree dev HEAD`, sin tocar ningún árbol): código y tests
  **mezclan limpio**; conflictos solo en `BACKLOG.md`, `harness/features.json` y `progress/current.md`. Sobre el árbol
  mezclado (en el scratchpad): sv3 **985 passed** (915 + los 70 de F-037) y guardianes raíz F-015/F-023/F-024/F-036
  **87 passed**.
- **Herramienta no ejecutada contra producción**: no hay `.env` en `services/partes-persistencia` del worktree (sin
  él `main()` sale con 2 antes de cualquier red), no existe `logs/` y no hay ningún `medicion_casado_*` en
  `PycharmProjects/` ni en `%TEMP%`. El informe lo declara («No se ha ejecutado»).

## Decisiones del humano y lista cerrada

- **Casado contra recursos persona** [x]: `casar_trabajador` (DNI → alias → nombre) sobre `IndicePersonas`, solo
  `cla = 1` (`es_persona` filtra los índices por DNI/ficha y `candidatos_nombre`), de alta a la fecha y de la empresa
  del parte. **DNI del recurso** = `emp.dni` de la ficha enlazada y, si vacío, `res.cif` (`dni_de_recurso`, DA1); el
  casado **busca por ambos** (`_recursos_de` por `conide` de las fichas del DNI y por `res.cif`): leído el `cif`
  distinto de la ficha, casa y guarda el de la ficha, y el conciliador vuelve al mismo recurso por `conide` (R15).
- **DA2** [x]: el casado solo corre en la ingesta de un parte nuevo (R22, dos tests); lo activo solo ve el filtro R2.
- **DA3** [x]: `CLA_PERSONA = 1` en sv3 y `AND res.cla = 1` en **las dos ramas** de sv5 `recursos_por_dni` (su único
  consumidor es el paso 2b de `registro_pipeline`, `elegir_por_dni`). Entrada nueva en la lista cerrada de
  `CLAUDE.md` y guardián `tests/test_f036_recurso_persona_gemelos.py`, que además prueba que sabe fallar.
- **Copias de la lista cerrada** [x]: `de_alta` intacto (el diff solo lo usa); sv5 `coherencia_recurso.py`
  (`de_alta`, `elegir_por_dni`), `recurso_conciliador.py` (`esta_congelado`, `ESTADOS_CONGELADOS`), sv4 entero
  (`congelacion.py`), `jornada_resolver.py` y `orm_models.py`: **diff vacío**. La elección por DNI cambia en las dos
  copias a la vez (candidatos `cla = 1` en `elegir_recurso` sv3 y en `recursos_por_dni` sv5). Guardianes
  `test_f023_de_alta_gemelos.py` y `test_f024_borrado_no_congela_gemelos.py` sin tocar y en verde.
- **Solo lectura** [x] (R23): engine propio sin `SessionFactory`, `SET TRANSACTION READ ONLY` (PG) y `rollback`; el
  test captura todas las sentencias (solo `SELECT`), y otro prohíbe escrituras/rutas en el fuente y comprueba que el
  cliente de sv3 solo conoce `/api/sql/read`. Sin nombres ni DNIs en la salida (R27).

## Checkpoints

- **C1** [x] init.sh exit 0 (ver arriba) · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-036) · [x] rama `feature/F-036-…` · [x] `current.md` con F-036 arriba; lo
  demás son entradas vigentes de otras features (práctica del repo, como en F-037) · [x] las `done` con resumen.
- **C3** [x] hexagonal: `casado_recurso` y `medicion_casado` puros en application; el script de consola compone en
  la raíz del servicio, como los demás · [x] primera línea con ruta en los 27 `.py` tocados · [x] `print` solo en el
  script de consola (permitido); sin TODOs, secretos ni dependencias nuevas · [x] trampas: (1) empleado ≠ recurso
  respetado y reforzado (`empleado_reside` = recurso elegido; `recurso_ide` solo lo escribe el conciliador, R16);
  (2) incidencias no tocadas; (3) sin cambio de schema.
- **C3 bis** [x] solo se **edita** `docs/referencia/partes-proyecto.md` (cabecera intacta) · [x] sin PDF/ofimática
  (`git log --diff-filter=A` vacío) · [x] barrido de las líneas añadidas con correo, IPv4, GUID,
  `password|secret|token|apikey|AccountKey|Bearer` y DNI `\d{8}[A-Z]`: solo DNIs sintéticos de los tests
  (`11111111H`, `12345678Z`…) · N/A redacciones: nada que redactar.
- **C4** [x] R1–R28 con test `test_f036_rN_*` en verde (tabla abajo) · [x] sin red ni PostgreSQL (SQLite y dobles)
  · **[ ] verificaciones MANUAL con su comando exacto**: M1 lo trae; **M2 y M3 no** (ver cambio 1).
- **C4 bis**
  - [x] `rigor` declarado: `critico`.
  - [x] **Fase RED**: trazas reales en `impl` (T2–T12) y reproducidas por mí (arriba).
  - [x] **Cobertura**: `[OK]` 99,7 % (308/309); la que falta es el `raise` de `_nodo` del guardián.
  - [x] **Mutación**: informe generado por la herramienta; totales recalculados (727 líneas, 108 mutantes).
  - [x] **Muertos comprobados**: campaña > 60 s, no reejecutada entera; RM4 sobre 6 de 108, todos muertos.
  - [x] **Coste por mutante**: 882,8 × 6 ÷ 108 = 49 s (≫ 1 s).
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; líneas base de los 6 workers (64,8–66,6 s).
  - [x] **RM1**: SHA medido `ee2c5d1…` ≠ HEAD `f5104ca`; desde entonces solo `progress/` y `tasks.md`: el alcance
    medido es el revisado.
  - [x] **RM2**: media 8,2 s × 6 workers = 49 s frente a línea base ~65 s: coherente (`-x`, 108/108 muertos).
  - [x] **RM5**: N/A justificado: no hay supervivientes declarados equivalentes en la campaña válida; los 3
    equivalentes de la primera campaña se resolvieron **quitando el código muerto**, no justificándolos.
  - [x] **RM6**: no se quitó ninguna guarda. Lo eliminado en `eca56bb` son dos `round(…, 4)` (el invariante está en
    quien construye el dato: todas las salidas de `text_match.name_similarity` son `0.0` o `round(score, 4)`), un
    `argv` ignorado y un `sorted` con clave reescrito.
  - N/A campaña MANUAL (hubo automática, 108) · [x] sin `PENDIENTE` · [x] «Evidencias» con los 4 números y 6 workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md` T1–T18 `[x]`, un commit `F-036 Tn:` por tarea (T16 en dos) · [x] sin artefactos sin trackear
  (`coverage.json` y `.arnes_cache` ignorados) · [x] `features.json` en `in_progress` (pasa a `done` con el APPROVED).

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f036_r1_el_sql_de_recursos_lee_res_cla` (+2) |
| R2, R3 | `r2_nombre_de_un_recurso_que_no_es_persona_no_casa` (+7) · `r3_nombre_de_un_recurso_sin_dni_no_casa` (+4) |
| R4–R8 | `r4_r13_dni_con_ficha_enlazada` (+10) · `r5_dni_sin_candidato_cierra_sin_alias_ni_nombre` (+5) · `r6_…sigue_al_alias_y_al_nombre` (+4) · `r7_r14_ficha_en_a_y_recurso_sin_enlazar_en_b` (+1) · `r8_alias_con_dni` (+7) |
| R9 | por diseño (§7): diff vacío de sv4 y `orm_models.py`, comprobado por mí |
| R10–R12 | `r10_nombre_puntua_el_maximo_de_recurso_y_ficha` (+10) · `r11_…empata_nombre_ambiguo` (+6) · `r12_…umbral_none` (+4) |
| R13–R16 | `r13_r14_r15_el_conciliador_confirma_el_recurso_del_casado` (parametrizado, SQLite) · `r14_dni_sin_ficha_recurso_dni` (+5) · `r16_sin_conciliador_el_casado_no_escribe_recurso` |
| R17 | `r17_sin_fichas_de_recurso`, `r17_nadie_los_usa` |
| R18, R19 | sv5 `r18_las_dos_ramas_filtran_recurso_persona` (+1) · raíz `r19_*` (11) |
| R20, R21 | caracterización `r20_*` (3, parametrizados) · `r21_congelada_no_se_re_resuelve…` |
| R22 | `r22_un_parte_ya_guardado_no_se_re_casa`, `r22_reingerir_el_mismo_parte_no_lo_re_casa` |
| R23–R28 | `test_f036_medicion.py` (44): `r23_*` (9), `r24_*` (5), `r25_*` (7), `r26_*` (12), `r27_*` (5), `r28_*` |
| R29 | revisado contra design §6: `ARCHITECTURE.md` (sem. 2, 12 y Herramientas), `partes-proyecto.md` (§3.3, §4.6, §7), `CLAUDE.md` y `azure-apps` commit `6355a5f` |

## Cambios requeridos

1. **`progress/current.md`, bloque F-036 «Verificaciones MANUAL»: pegar el comando exacto de M2 y M3** (`critico`
   lo exige en C4; mismo motivo del rechazo de F-037 en su pasada 1). Hoy M2 y M3 se describen, sin comando:
   - **M2**: comando de Log Analytics de `ca-sv3-persistencia` con la cadena `[recurso-concil] registros=`
     (`recurso_conciliador.py:488`, trae `actualizados=`), en el formato de la M3 de F-037 en `dev` (workspace
     leído con `az`, no versionado), y el valor esperado frente a M1 (`recurso_cambia + recurso_pierde + recurso_gana`).
   - **M3**: SQL de solo lectura (base `partes`) que localiza el parte nuevo de Porsan de la 0678 y enseña por línea
     `empleado_match_method`, `empleado_ide`, `empleado_reside`, `recurso_ide` y `parte_estado`, con lo esperado
     (`recurso_dni`, `empleado_ide` NULL, `empleado_reside` = `recurso_ide`; `parte_estado` `ok`/`sin_parte`).
   - Despliegue: `infra/redeploy_partes.ps1 -Solo sv3,sv5` (el script ordena sv3 → sv5); lo lanza el humano.

## Observaciones (no bloquean)

- **Merge con dev (F-037)**: sin choques de código; resolver a mano `harness/features.json` (las dos entradas
  nuevas al final de la lista: conservar ambas), `progress/current.md` (conservar los dos bloques) y regenerar
  `BACKLOG.md` con `init.sh`. Verificado: sv3 mezclado 985 passed y guardianes verdes.
- **F-035** (paralela) ya usa `res.cla = 1` en sv4 `_SQL_RECURSOS_ACTIVOS` y toca otro párrafo de la lista cerrada:
  al integrar las dos, conviene que el guardián de F-036 vigile también esa copia de sv4 (hoy solo sv3/sv5).
- Comportamiento aceptado por la spec (R6) que conviene que el humano conozca: un DNI leído con ficha pero **sin
  ningún recurso persona** sigue por alias y nombre, y el nombre podría casar a otra persona.
- Menores: ruff nuevo `I001` en `seleccion_sigrid.py:22` (dos líneas en blanco tras los imports);
  `medicion_casado._METODOS_RECURSO` repite `METODOS_RECURSO` del pipeline (mismo servicio, podría importarse).

**Automejora (propuesta, no aplicada)**: `.claude/agents/implementer.md`, en `critico`, comprobar antes de terminar
que **cada** MANUAL de `current.md` trae comando o consulta pegados (F-037 y F-036 rechazadas por lo mismo).
