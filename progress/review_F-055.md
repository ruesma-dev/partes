<!-- progress/review_F-055.md -->
Revisión incremental desde c6bb18d (pasada 3) · HEAD 143976c · lo aprobado hasta 73a8ec6 (código) y los papeles de f7f2b25 salvo `current.md` quedan dados por buenos
# F-055 · sv5 omite las líneas sin fecha válida — revisión

## Pasada 3 (2026-11-01) · Veredicto: **APPROVED**

Nivel de rigor: `critico` (declarado). Delta revisado: `git diff c6bb18d..HEAD` = solo
`progress/current.md` (commit 143976c). Lo aprobado en código no se toca.

- `git ls-files --eol progress/current.md` ⇒ `i/lf w/lf`; 0 CR en `git show HEAD:progress/current.md`.
- `git diff --stat 1c2307d..HEAD -- progress/current.md` ⇒ 15 líneas (14+, 1−): ya no reescribe el fichero.
- `git diff --ignore-cr-at-eol c6bb18d..HEAD` ⇒ un único cambio de contenido: la M3 dice
  `` `.\redeploy_partes.ps1 -Solo sv5` `` (antes `.^Medeploy…`, CR suelto). Cambio requerido 1 y 2 de la pasada 2: hechos.
- `bash harness/init.sh` ⇒ ENTORNO LISTO: 537 passed, 3 skipped; cobertura 100 % (44/44, nivel
  critico); tamaño dentro de topes. sv5 servida de caché ⇒ lanzada a mano
  (`python -m pytest -q -p no:cacheprovider` en `services/partes-transfer`): **1554 passed**.
- Checkpoints C1–C5, C3 bis, C4 bis: sin cambios respecto a la pasada 2 (el delta es documental);
  C3 bis y C4 ter siguen N/A por los motivos escritos abajo. Mutación: sin cambios en el alcance
  (el delta no toca código), RM1 sigue válida.
- Árbol limpio tras la revisión (`git status`), salvo este informe.

Cambios requeridos: ninguno. Queda pendiente del humano la M3 (fuera de la revisión).

## Pasada 2 (2026-11-01) · Veredicto: **CHANGES_REQUESTED**

**Rigor**: `critico` (declarado). Puertas: RED, cobertura ≥ 80 %, mutación con 0 supervivientes
salvo aceptación humana, RM5, MANUAL con comando. Ninguna cambia respecto a la pasada 1.

**Ejecución**: `bash harness/init.sh` desde el worktree, tal cual → **ENTORNO LISTO** (exit 0):
raíz 537 passed, 3 skipped (166 s); PUERTA COBERTURA [OK] 100,0 % (44/44); PUERTA TAMAÑO [OK]
(106/150, 249/250, 153/220, 136/140). sv5 salió de caché: **lanzada a mano** desde
`services/partes-transfer` con `python -m pytest -q -p no:cacheprovider` → **1554 passed,
1 warning, 21,5 s**. `git status` limpio.

**Delta** (`git diff 1c2307d..HEAD`): 6 ficheros, ninguno en `services/`, `docs/` ni `infra/`
(stat vacío). La campaña de mutación sigue válida (RM1: el alcance no se ha tocado).

| Cambio pasada 1 | Estado |
|---|---|
| 1 · T10/T11 `[x]`, M2 en `impl_F-055.md`, M2b con motivo | [x] `tasks.md` T10 y T11 `[x]`, T12 `[ ]` justificado; M2 con `registro_id`, recurso, fechas, preflight/ejecutar y consola; M2b no hecha con motivo (franquicia `apagada`, R15 cubierto por test) |
| 2 · «Evidencias» con mutación y workers | [x] 28/26/2/0, **3 workers**, 215,7 s; «Pendiente» sustituido |
| 3 · Aceptación humana de los equivalentes | [x] literal «si» y fecha 2026-11-01 en `mutacion_F-055.md` (los dos) y en «Evidencias» |
| 4 · M3 en `current.md` con comando y esperado | **[ ]** contenido correcto (SQL de M1 de solo lectura, esperado = `design.md` §9), pero el fichero quedó dañado: ver cambios 1 y 2 |
| 5 · `features.json` sin «pendiente de aprobación» | [x] y `BACKLOG.md` regenerado (`BACKLOG.md al día`) |

**Defecto nuevo introducido por f7f2b25 en `progress/current.md`** (comprobado con bytes, no a ojo):

- En 1c2307d el fichero era LF puro (0 CRLF, 4176 LF). En f7f2b25 es **CRLF entero** (4189 CRLF) y
  además lleva **un CR suelto**. Por eso `git diff --stat` cuenta 8365 líneas cambiadas por 14 reales,
  `git ls-files --eol` lo marca `i/-text` (git ya no lo trata como texto) y la fusión con `dev`, que
  toca `current.md` en cada feature, chocará en el fichero entero.
- El CR suelto es la M3: «tras `.\redeploy_partes.ps1`» se escribió con `\r` interpretado como
  retorno de carro; en el fichero pone «`.`␍`edeploy_partes.ps1 -Solo sv5`». El comando que se
  le deja al humano está roto justo en el nombre del script.

### Checkpoints (solo lo que mueve el delta; el resto, como en la pasada 1)

- C4 · MANUAL en `current.md` con su comando exacto: **[ ]** (defecto anterior: el nombre del script
  de despliegue está corrompido).
- C4 bis · aceptación humana de equivalentes: [x] · «Evidencias» completa: [x].
- C5 · `tasks.md`: [x] (T12 `[ ]` justificado: tras despliegue que pide el humano) · `features.json`: [x]
  · sin temporales: [x] · **[ ] `progress/current.md` con finales de línea y contenido íntegros**.

### Cambios requeridos (pasada 2; solo papeles)

1. `progress/current.md`: devolverlo a **LF** (como en 1c2307d y en `dev`), sin tocar el contenido;
   comprobar con `git ls-files --eol progress/current.md` que sale `i/lf` y con
   `git diff --stat 1c2307d..HEAD -- progress/current.md` que quedan ~15 líneas, no ~8000.
2. Misma entrada de F-055, línea de M3: sustituir el `.`+CR+`edeploy_partes.ps1` por
   `` `.\redeploy_partes.ps1 -Solo sv5` `` escrito con el editor (no con una cadena que interprete `\r`).
   Comprobar que el fichero tiene 0 CR (`python -c "print(open('progress/current.md','rb').read().count(b'\r'))"`).

Con eso la pasada 3 es de un minuto: init.sh, los dos bytes y el diff de `current.md`.

### Automejora (propuesta, no aplicada)

- Añadir a `harness/init.sh` un aviso si algún `progress/*.md` o `specs/**/*.md` trackeado tiene CR
  (`git ls-files --eol` con `i/crlf` o `i/-text`): este fallo pasa init.sh en verde y solo lo caza
  mirar el `--stat`. Vale para cualquier proyecto ⇒ portar a `arnes-base`.

---

## Pasada 1 (resumen; completa en `git show 1c2307d:progress/review_F-055.md`)

Revisión completa sobre HEAD 73a8ec6, base `dev` 14b3cd5. **CHANGES_REQUESTED solo por papeles**:
código, tests, campaña y documentación correctos; nada que cambiar en `services/`.

- init.sh ENTORNO LISTO; sv5 a mano 1554 passed. Diff = ficheros de `design.md` §3; hexagonal
  respetada; ningún test existente modificado; R13 (`git diff dev...HEAD` fuera de sv5) vacío.
- C1, C2, C3 [x]; C3 bis y C4 ter N/A (no toca `docs/referencia/`; sin `rutas_sensibles.json`).
- C4 bis: RED con trazas reales (T2 `ImportError`, T4 31 failed); cobertura 100 %; mutación
  **recalculada** (alcance 4 ficheros/96 líneas, `generar_mutantes` = 28, los 2 supervivientes
  existen tal cual en `registro_models.py:42` y `:46`); campaña no reejecutada (215,7 s > 60 s);
  RM1–RM3, RM6 [x]; RM5 reproducida en los dos equivalentes (`or 0` → `or 1` con `fecha_int` falsy).
- Documentación: `ARCHITECTURE.md` semántica 6 = `design.md` §10; `azure-apps` 8913f8e local.
- Cambios 1–5 (T10/T11 y M2, «Evidencias», aceptación humana, M3 en `current.md`, `features.json`):
  estado en la tabla de la pasada 2.

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
