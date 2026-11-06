<!-- progress/review_F-066.md -->
Revisión completa (pasada 1), base `0d8fc14` (punta de F-052) .. HEAD `7d5c968`

# F-066 · Review

**Veredicto: CHANGES_REQUESTED**. Solo por el cierre documental (C4 y C5): el código, los tests y
la mutación están bien. Los cambios pedidos no tocan producción ni tests, así que la pasada 2 se
limitará al delta.

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED, cobertura,
mutación completa con cero supervivientes sin justificar y las MANUAL listadas.

## Ejecución

- `bash harness/init.sh` sobre `7d5c968`: **ENTORNO LISTO**, exit 0. sv4 se ejecutó **entero, sin
  caché**: `3740 passed, 1 skipped in 1289.51s`. sv5 y el resto salieron de caché, y es correcto
  (la feature no toca esos árboles; `git diff --stat` solo muestra `services/partes-front`).
- `PUERTA COBERTURA: 99.9% de 784 líneas cambiadas (783/784, umbral 80%, nivel critico)` [OK].
- `PUERTA TAMAÑO`: [OK], aunque **impl ya está en 219/220** (ver el cambio 4).

## Checkpoints

- C1: [x] init.sh en verde · [x] están los ficheros del arnés.
- C2: [x] solo F-066 en `in_progress` · [x] la rama es la de la feature · [x] `current.md`: la
  acumulación de secciones de features cerradas ya venía de antes (287 KB en `dev`); F-066 solo
  añade la suya. No es de esta feature, pero ver el cambio 2 · [x] `history.md`: no hay `done` nuevo.
- C3: [x] Hexagonal: `clase_hora.py` es puro, vive en application y no hace E/S. Infrastructure
  importa de application, como dice design §5 · [x] primera línea con la ruta en los 5 ficheros
  nuevos · [x] ni `print` ni secretos ni dependencias nuevas (el único `console.log` es el script de
  node de un test) · [x] trampas del monorepo: no hay cambio de esquema, `orm_models.py`
  queda intacto y las incidencias conservan su `tipo_hora` (R14).
- C3 bis: N/A. No se toca `docs/referencia/`. C4 ter: N/A, no existe `harness/rutas_sensibles.json`.
- C4: [x] trazabilidad completa (tabla de abajo) y todo en verde · [x] sin red ni BBDD (SQLite en
  memoria, `_post_sql_read` falso, node con `skip` si falta) · **[ ] M2 sin listar en
  `progress/current.md` con sus pasos**. La sección de F-066 solo dice «T10 M2 (humano, tras
  desplegar sv4)» (cambio 2).
- C4 bis:
  - [x] `rigor` declarado: `critico`.
  - [x] Fase RED: hay trazas reales de T1, T2, T4 y T6 en `impl_F-066.md`.
  - [x] Cobertura: [OK] 99.9%.
  - [x] Mutación, recálculo independiente con `harness.alcance` (base `0d8fc14`) y
    `generar_mutantes`. Sale **7 ficheros, 138 líneas, 21 mutantes**, igual que el informe. Los 3
    supervivientes existen tal cual, con el mismo operador y el mismo texto
    (`sigrid_lookup_client.py:238 [entero] omitidos = 0 -> 1`, `:247 [aritmetico] += -> -=`,
    `:247 [entero] += 1 -> += 2`).
  - [x] Muertos: **campaña no reejecutada: 10220,6 s según el informe** (más de 60 s). Vale el
    recálculo puro más RM1–RM6.
  - [x] Coste por mutante: 486,7 × 4 workers = 1947 s, más de 1 s.
  - [x] Sin cabecera «CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; corrió la línea base
    (4 workers, de 2710 a 2779 s).
  - [x] RM1: midió `2bc2ef0`. Lo que llega después (`7d5c968`) solo toca tests y `progress/`, así que
    el alcance de producción es el mismo y lo he confirmado recalculando sobre HEAD.
  - [x] RM2: media × W = 1947 s, frente a una línea base de unos 2730 s. Es coherente: 18 de 21
    mueren con `-x`, y los 3 supervivientes recorren la suite entera.
  - RM3, a criterio: he repasado los 18 muertos y ninguno es equivalente. Por ejemplo, `and`→`or`
    en `:71` lanza TypeError en vez de ValueError, y `-=` sobre str da TypeError.
  - [x] RM4: en una copia de `services/partes-front` en el scratchpad (`git archive`), el test
    `test_f066_r7_log_cuenta_excluidas` da `3 passed` con el original. Con `omitidos += 2` da
    `2 failed, 1 passed` y con `omitidos = 1` da `3 failed`. Coincide al pie de la letra con las filas
    del informe. El mismo intérprete sale con 0 sin mutante.
  - [x] RM5: N/A justificado, no hay equivalentes declarados.
  - [x] RM6: no se quitó código defensivo. Los supervivientes murieron añadiendo un test con `caplog`.
  - [x] Campaña manual: N/A justificado (la automática dio 21 mutantes).
  - [x] Supervivientes: los 3 tienen análisis («hueco real») y un test que los mata, verificado
    arriba. No queda ningún `PENDIENTE` y no hace falta aceptación del humano: no queda ninguno vivo.
  - [x] «Evidencias»: trae tests, cobertura, mutantes y tiempo. El nº de workers (4) no está en
    `impl`, pero sí en la fila «Workers» del informe que genera la herramienta, y lo doy por bueno.
  - [x] Ningún N/A sin motivo.
- C5: **[ ] `tasks.md`**: T9 sigue `[ ]` aunque su commit `F-066 T9` existe y la tarea está hecha;
  T11 (`init.sh` en verde) sigue `[ ]` aunque `init.sh` está en verde. T10 (M2 tras desplegar) en
  `[ ]` es legítimo, porque depende de un despliegue que pide el humano (mismo criterio que T12 de
  F-055) · [x] sin ficheros temporales (`git status` limpio) · [x] `features.json` en `in_progress`,
  coherente con una feature aún sin aprobar.

## Puntos que pidió vigilar el líder

- **Límite de servicio:** solo `services/partes-front`. sv3, sv5, `CLAUDE.md`, `congelacion.py`,
  `orm_models.py` y los gemelos (`_SQL_EMPLEADOS`, `_SQL_RECURSOS_ACTIVOS`, `de_alta`, `res.cla`)
  quedan sin cambios (`git diff --stat` vacío sobre ellos).
- **Sitio único:** grep de `startswith("HE`, `LIKE 'HE`, `HENC` y `startsWith("HE` en `.py`,
  `.js` y `.html` de sv4 (sin tests). Solo aparecen en `clase_hora.py`, más dos menciones en
  docstrings (`franquicia.py:239` y `tipo_hora_catalog.py:9`) que no son literales. Lo vigilan R6 y
  R11. `buildOptions` agrupa por `t.extra` y no lee `.ext`.
- **Sincronizar de F-052:** `sincronizacion.es_hora_extra` es la misma función que la de
  `clase_hora` (R5 lo comprueba con `is`), y `HENC` en Sigrid frente a portal `normal` no da
  diferencia. Los tests de F-052 están en verde dentro de los 3740.
- **`azure-apps/partes.md`:** el contrato no cambia. `/api/sigrid/tipos-hora` es interno y `extra`
  es un campo aditivo, como dice design §4, aprobado. Observación que **no bloquea**: dos frases han
  quedado desfasadas. La l.933 llama a `hora_ext` «(¿es extra?)», cuando ahora es informativo. La
  l.1233 lista «`tipo_hora_resolver` con `auxhor.ext` para variantes HE%», que es F-006, ya
  retirada. Recomiendo corregirlas en este trabajo o en F-067.
- **`init.sh`:** en verde (ver arriba).

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f066_r1_constantes`, `test_f066_r1_excluidos` |
| R2 | `test_f066_r2_regla_extra`, `test_f066_r2_tipo_hora_de_codigo` |
| R3 | `test_f066_r3_derivadas_del_prefijo`, `…_de_la_lista`, `…_lista_vacia` |
| R4 | `test_f066_r4_condicion_sql_texto_exacto`, `…_columna_valida`, `…_columna_invalida` |
| R5 | `test_f066_r5_sincronizacion_misma_funcion`, `…_excluido_no_es_extra` |
| R6 | `test_f066_r6_sin_otra_regla`, `test_f066_r6_clase_hora_si_la_declara` |
| R7 | `test_f066_r7_catalogo_sin_excluidos`, `…_por_ide_no_ve_excluidos`, `…_matcher_encargado_no_elige_henc`, `…_sin_excluidos_nada_cambia`, `…_log_cuenta_excluidas` |
| R8 | `test_f066_r8_patch_excluido_400` |
| R9 | `test_f066_r9_tipos_hora_lleva_extra` |
| R10 | `test_f066_r10_grupos_por_extra`, `…_solo_true_es_extra`, `…_grupo_vacio_no_sale` (node) |
| R11 | `test_f066_r11_js_sin_regla` |
| R12–R15 | `test_f066_r12_he_ext_0_extra`, `…_r13_sin_prefijo_ext_1_normal`, `…_r14_incidencia_no_cambia`, `…_r15_sin_codigo_no_toca_tipo` |
| R16 | `test_f066_r16_campos_y_deshacer`, `…_deshacer_devuelve_extra`, `…_registro_inexistente` |
| R17 | `test_f066_r17_respuesta`, `…_respuesta_sin_codigo_es_normal` |
| R18 | `test_f066_r18_varias_lineas`, `…_guardas`, `…_sin_sigrid_503` y los tests de F-004, F-043 y F-048 |
| R19 | `test_f066_r19_hora_extra_recurso_salta_el_excluido`, `…_usa_condicion_sql` |
| R20 | `test_f066_r20_dnis_sin_extra_excluido_no_cuenta`, `…_las_dos_ramas` |
| R21 | `test_f066_r21_extras_pendientes` |
| R22 | Revisado: `docs/ARCHITECTURE.md` semántica 3 recoge la lista, la regla, la M1 y el desfase hasta F-067 |
| R23 | `test_f066_r23_disyuntivos_intactos` (los 6) |
| R24 | Los 4 ficheros corren sin red ni BBDD |

## Cambios requeridos

1. `specs/F-066-selector-hora-por-prefijo-he/tasks.md` l.15: marcar **T9 `[x]`**. La campaña está en
   `progress/mutacion_F-066.md` y los supervivientes, matados en `7d5c968`.
2. `progress/current.md`, sección F-066 (l.4–36): ponerla al día. T9 está hecha y no queda
   «Pendiente: T9». Las DA ya están aprobadas, así que «Decisiones que debe validar el humano» y
   «`features.json` en `pending`» sobran. Además hay que **listar la M2 con sus pasos exactos**
   (los de `requirements.md` §Verificaciones manuales: tras desplegar sv4, obra 0404, línea
   ordinaria sin registrar, el desplegable no ofrece `HENC`, `HEOF` en «Horas extra» ⇒ badge
   extra al recargar, deshacer ⇒ vuelve, sin aprobar ni enviar). Así lo pide C4.
3. `tasks.md` l.17: marcar **T11 `[x]`** después de ejecutar `bash harness/init.sh` en verde sobre el
   commit de estos cambios.
4. `progress/impl_F-066.md` está en 219/220 líneas. Si hay que anotar algo, que sea resumiendo, o
   la `PUERTA TAMAÑO` se pondrá en rojo.

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4 bis pide los workers en la sección «Evidencias» del implementer. Cuando la
campaña la lanza el líder, el dato ya está en la fila «Workers» del informe que genera la
herramienta, que es más fiable que copiarlo a mano. Propongo aceptar esa fila como fuente válida.
