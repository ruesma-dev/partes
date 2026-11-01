<!-- progress/review_F-055.md -->
Revisión completa (pasada 1) · rama `feature/F-055-sv5-omite-lineas-sin-fecha`, base `dev` 14b3cd5, HEAD 73a8ec6
# F-055 · sv5 omite las líneas sin fecha válida — revisión

**Veredicto: CHANGES_REQUESTED.** El código, los tests, la campaña y la documentación están bien:
no hay nada que cambiar en `services/`. Faltan **solo papeles de cierre** (tareas T10/T11 sin marcar,
M2 sin anotar, «Evidencias» sin la mutación ni los workers, equivalentes sin aceptación humana,
MANUAL sin comando en `current.md`). Con eso, la pasada 2 puede ser incremental y corta.

**Rigor**: `critico` (declarado en `harness/features.json`). Exige fase RED, cobertura ≥ 80 % de
las líneas cambiadas, mutación completa con cero supervivientes salvo justificación **aceptada por
el humano**, RM5 y verificaciones MANUAL listadas con comando y resultado.

## Ejecución

- `bash harness/init.sh` (desde el worktree, tal cual) → **ENTORNO LISTO**: raíz 537 passed,
  3 skipped (94,9 s); PUERTA COBERTURA **[OK] 100,0 %** (44/44); PUERTA TAMAÑO [OK] (106/150,
  249/250, 146/220). Avisos previos ajenos: F-032 `blocked`, ruff 909, infra sin tests.
- sv5 salió **de caché** y toca la feature: lanzada a mano desde `services/partes-transfer` con
  `python -m pytest -q -p no:cacheprovider` → **1554 passed, 1 warning in 14,13 s**. Árbol limpio.

## Diff contra el diseño

- Solo los ficheros de `design.md` §3: nuevo `fecha_linea.py` (application, puro), paso 2a y `_hoy()`
  en `registro_pipeline.py`, `fecha_int` opcional en `LineaEntrada` (con `ano`/`mes` `or 0`) y en
  `LineaIn`; tres ficheros de test nuevos; ninguno existente modificado (`--name-status`: solo `A`).
- **Paso 2a**: tras `_con_empresa` (sin obra, el error de siempre); `validas` alimenta 2b, 2c y
  `horas_de_recursos`; `ReglasRegistro` recibe `{**omisiones, **por_fecha}` (la de fecha pisa) y
  `decidir` corre sobre todas. `horas_de_recursos([])` no consulta (`if not ides: return {}` en
  `sigrid_write_client.py:285`). `roles_in` sigue sobre `lineas`, pero solo registra un INFO.
- `_evaluar`, `_ciz_de_racha`, `registrar`, `franquicia_pipeline.py`, `reajuste_*.py` y
  `transfer_consumer.py` intactos (DA1 A, DA11 A), como dice §3.
- Hexagonal respetada: `registro_models.py` sin imports nuevos; la regla vive en `application`.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-055) · [x] rama correcta · [x] `current.md` con la sesión activa
arriba (las entradas cerradas siguen el uso del repositorio, ya aceptado en revisiones previas)
· [x] F-047 en `history.md`.
**C3** [x] hexagonal · [x] primera línea con ruta en los 7 ficheros · [x] sin `print`, TODOs,
secretos ni dependencias nuevas · [x] trampas: (1) el recurso se sigue verificando igual para las
válidas; (2) racha/hermano CIZ: una omitida no busca racha ni escribe hermano (`r3_racha_y_hermano`);
(3) `orm_models.py` no se toca.
**C3 bis** N/A: no añade ni toca nada en `docs/referencia/`.
**C4** [x] trazabilidad (tabla abajo), todos en verde · [x] sin red ni BBDD (`SigridFake`,
`TestClient`, `Montaje`) · **[ ] MANUAL en `current.md` con su comando exacto**: solo dice
«M2/M2b y M3» sin comando (cambio 4).
**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED con trazas reales para T2 (`ImportError`) y T4 (31 failed, motivos uno a uno).
- [x] Cobertura [OK] 100 % (44/44).
- [x] Mutación: `progress/mutacion_F-055.md` generado por la herramienta. **Recalculado**:
  `alcance_de_feature` → 4 ficheros, 96 líneas (32/56/5/3), igual que el informe;
  `generar_mutantes` → **28** (3 + 16 + 9 + 0), igual. Los 2 supervivientes existen tal cual
  (`registro_models.py:42` y `:46`, operador `entero`, `or 0` → `or 1`).
- [x] Muertos: **campaña no reejecutada: 215,7 s según el informe**, por encima de 60 s; vale el
  recálculo puro más RM1–RM6.
- [x] Coste por mutante 215,7 × 3 ÷ 28 = 23,1 s (> 1 s).
- [x] Sin cabecera «CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base 25,8–27,3 s.
- [x] **RM1**: medido en c7f846b; hasta HEAD (73a8ec6) solo entra `progress/mutacion_F-055.md`.
- [x] **RM2**: media × W = 7,7 × 3 = 23,1 s frente a base 25,8 s, con 26/28 muertos por `-x`.
- [x] **RM3**: los 26 muertos no son equivalentes (los repasé: constantes con test directo,
  `//`/`%` del calendario, `<=`/`<` en los límites, guarda `is not None`, `and`/`or` de 2b).
- [x] **RM5**: reproducida la equivalencia de los dos, no solo una muestra: para `None`, `0`,
  `False`, `0.0` y `""`, `int(v or 0)//10000 == int(v or 1)//10000` y
  `(int(v or 0)//100)%100 == (int(v or 1)//100)%100` (todo `True`); con `v` truthy el `or` no
  actúa. Son equivalentes.
- [x] **RM6**: no se quitó ninguna guarda. Campaña manual: N/A, la automática dio 28.
- **[ ] Cero supervivientes salvo justificación aceptada por el humano**: la justificación es del
  líder y correcta, pero **no consta la aceptación del humano** (cambio 3).
- **[ ] «Evidencias»**: la fila de mutación dice «pendiente» y no declara los workers (cambio 2).
**C4 ter** N/A: sin `harness/rutas_sensibles.json`.
**C5** **[ ] `tasks.md`**: T10 sigue `[ ]` aunque existe 73a8ec6 «F-055 T10»; T11 (M2) sigue `[ ]`
y su resultado no está en `impl_F-055.md`, que es donde la tarea dice anotarlo (cambio 1). T12 (M3)
queda `[ ]` **justificado**: se hace tras `redeploy_partes.ps1 -Solo sv5`, que pide el humano.
· [x] sin temporales ni no trackeados · [ ] `features.json`: el campo `spec` aún dice «pendiente
de aprobación» (cambio 5).

## Cobertura requisito → test (todos en verde)

| R | Tests |
|---|---|
| R1 | `test_f055_r1_*` (sin fecha, calendario, límites, bisiesto, constantes, `pipeline_usa_hoy`) |
| R2 | `test_f055_r2_texto_del_motivo[…]` (prefijo, sin «:» extra, ASCII, ≤ 255) |
| R3 | `r3_preflight_omite`, `r3_no_synckey_ni_conflictos`, `r3_racha_y_hermano` |
| R4 | `r4_manda_sobre_recurso[6 casos]`, `r4_mensual_no_va_a_dedicacion` |
| R5 | `r5_no_lee_sigrid` (espías de `recursos_por_dni`, `datos_recursos`, `horas_de_recursos`) |
| R6 | `r6_mezcla` (acciones, partes, escritas y WARNING de 2c idénticos) |
| R7 | `r7_ejecutar_sin_validas` |
| R8 | `r8_preflight_http`, `r8_ejecutar_http`, `r8_cola` |
| R9 | `r9_null_y_ausente_http[4]`, `r9_null_y_ausente_cola[2]`, `r9_ano_mes_*`, `r9_a_dominio_sin_la_clave` |
| R10 | `r10_reajuste_extra_nueva`, `r10_reajuste_extra_nueva_no_escribe` |
| R11 | `r11_warning_sin_nombres`, `r11_sin_invalidas_no_hay_warning` |
| R12 | suite de sv5 1554 passed sin tocar tests existentes |
| R13 | `git diff dev...HEAD --stat -- services/partes-front services/partes-persistencia services/partes-email services/partes-api infra` → **vacío**; lista cerrada sin cambios |
| R14 | revisión: `ARCHITECTURE.md` semántica 6 = texto de §10; `azure-apps` 8913f8e (abajo) |
| R15 | `r15_franquicia_posterior_no_editable[2]`, `r15_franquicia_hoy_mas_30_se_ajusta[2]` |

## Documentación y propagación

- `docs/ARCHITECTURE.md` semántica 6: texto literal de `design.md` §10. [x]
- `azure-apps` 8913f8e (local, sin push; árbol limpio): punto 6 de §3.5 de `partes.md` con el motivo,
  `fecha_int` nulo, reajuste y franquicia `no_editable`, «sin desplegar»; nota informativa a
  `porcentajes` sin tocar su repositorio (DA7). Sin secretos. [x]
- Regla de propagación al arnés: **N/A**, la feature no toca `harness/`, `.claude/`, `CHECKPOINTS.md`
  ni convenciones.

## M2 (hecha por el líder el 2026-11-01, según su encargo)

Lo que me transmite el líder coincide con lo esperado en `design.md` §9: preflight `ok`,
`forzada_pruebas: true`, `partes` vacío, las tres `omitir` con `fecha_no_valida`, `resumen.omitir`
= 3; `ejecutar` `ok: true`, 0 escritas, 3 omitidas; consola con el WARNING de R11 y «nada que
escribir», sin `[sigrid-write]` salvo el «Instanciado». **No lo anoto yo en `impl_F-055.md`**: el
reviewer no edita el trabajo de otros; queda pendiente del líder (cambio 1). M2b no consta.

## Cambios requeridos (solo papeles; nada de código)

1. `specs/F-055-sv5-omite-lineas-sin-fecha/tasks.md`: T10 `[ ]` → `[x]`. Anotar la M2 (fecha,
   comando, resultado real de arriba) en `progress/impl_F-055.md` y marcar T11 `[x]`; decir si M2b se
   hizo o por qué no (es opcional en §9).
2. `progress/impl_F-055.md`, sección «Evidencias»: fila de mutación con «28 generados, 26 muertos,
   2 supervivientes equivalentes, 0 timeouts, **3 workers**, 215,7 s» (y quitar el «pendiente» del
   apartado «Pendiente»).
3. Rigor `critico`: presentar al humano los dos equivalentes de `mutacion_F-055.md` y registrar su
   aceptación con el literal y la fecha (en el informe de mutación y en «Evidencias»), como en F-056.
4. `progress/current.md`, entrada de F-055: listar M3 con su comando exacto (`design.md` §9: el SQL
   de M1 sobre `partes` tras `redeploy_partes.ps1 -Solo sv5`) y el resultado esperado, pendiente del
   humano; y la M2 como hecha.
5. `harness/features.json`, F-055, campo `spec`: quitar «pendiente de aprobación» (aprobada el
   2026-11-01).

## Automejora (propuesta, no aplicada)

- En C5, cuando una tarea de `tasks.md` la hace el líder (mutación, M2), que el líder la marque y
  anote en el mismo commit que la ejecuta: F-047, F-056 y F-055 han caído en la pasada 1 por eso.
