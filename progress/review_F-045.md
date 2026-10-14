<!-- progress/review_F-045.md -->
Revisión incremental desde `7144932` (pasada 2) · delta `7144932..eb5b6b8`

# F-045 · Review

- **Veredicto (pasada 2): APPROVED.** Hay una condición de cierre que no decide el
  reviewer: en rigor `critico`, el humano tiene que **aceptar los 8 equivalentes** de
  `progress/mutacion_F-045.md`. Reproduje uno (RM5) y recomiendo aceptarlos. M1, el
  despliegue y M2 siguen siendo MANUAL.
- **Rigor:** `critico` (declarado): C1–C5, C3 bis, RED, cobertura ≥ 80 %, mutación, RM1–RM6, MANUAL.

## Pasada 2 · Ejecuciones propias (worktree `partes-wt-f045`, 2026-10-14)

- `bash harness/init.sh` → **ENTORNO LISTO**. Raíz: 487 passed, 3 skipped. COBERTURA
  [OK] 100 % (162/162). TAMAÑO [OK]. ruff: 698 avisos, los mismos que en `dev`;
  `ruff check` sobre los ficheros nuevos → All checks passed.
- sv3 salió de caché: la relancé a mano, **1391 passed** (eran 1387 + 4 tests nuevos).
- `progress/equivalentes_F-045.py` (con `python -I`) → **`8 mutantes, 0 distintos`**,
  60 s. Árbol limpio al terminar (`git status` vacío).

## Pasada 2 · Los 4 cambios requeridos

1. **Desempate con pesos de media hora: resuelto.**
   - Tests: `test_f045_r2_empate_de_restos_con_pesos_de_media_hora` (`repartir`),
     `test_f045_r2_repartir_dia_empate_de_restos_con_congelada` (`repartir_dia`: el
     caso real, A 0,5 + 1 y B 1,5 + 1) y un modelo exacto con `Fraction`, comparado
     en 3.000 repartos.
   - Prueba propia sobre una copia `git archive HEAD`: con `_RESOLUCION = 10001`
     fallan **los 3** (`3 failed, 208 passed`).
   - Código: el cálculo no cambia, y no es un parche. Con escala 10⁴ y horas de ≤ 4
     decimales, `peso × escala` es entero salvo ruido ≪ 0,5. Así la comparación de
     restos es exacta y el original nunca tuvo el defecto: solo lo tenía el mutante.
     La precondición queda escrita en `_RESOLUCION` y vigilada por el test del
     modelo.
   - Análisis: #2 reconocido como erróneo en «Historia de la campaña», y los otros
     8 se rehicieron con demostración ejecutable.
2. **Guarda `base_id` repuesta**: `if extra_auto and tipo_linea == EXTRA`
   (`recurso_conciliador.py:769-770`), con su comentario.
   - Test: `test_f045_r25_extra_auto_reclasificada_a_normal_pesa_por_si_misma`, mi
     caso de la pasada 1. Comprueba `8 → 5,00` y `2 → 1,00`.
   - Sobre la copia y sin la guarda, falla solo ese test (`1 failed, 1390 passed`).
     Es la RED que trae `impl` §Pasada 2.
3. **`progress/current.md`: resuelto.** 0 bytes CR, LF como `dev`; la línea 24 dice
   `` `.\redeploy_partes.ps1 -Solo sv3` ``; `git diff dev --stat`: +55, solo F-045.
4. **Mutación relanzada: resuelto.** Campaña 3 en `259e609`: 84 mutantes, 76 muertos,
   8 supervivientes, 0 timeouts, 0 sin veredicto, 387,1 s, 6 workers. Cada
   equivalente trae su demostración ejecutable (RM5, abajo).

## Pasada 2 · C4 bis y RM1–RM6 sobre la campaña 3

- [x] Recálculo puro (`alcance_de_feature` + `generar_mutantes`): **408 líneas y 84
  mutantes**, igual que el informe. Muestreé los supervivientes #1 (`:663`
  `<= → <`), #4 (`:79` `> 0 → >= 0`) y #7 (`:205` `> → >=`): existen con el mismo
  operador y el mismo texto.
- [x] Total de 387,1 s, más de 60 s: **campaña no reejecutada** (6,5 min según el
  informe). Me quedo en el recálculo puro, RM1–RM6 y RM4.
- [x] Sin «NO VÁLIDA» · base rota = 0 · línea base declarada (28,6–29,3 s × 6).
- [x] **RM1:** mide `259e609`. Hasta HEAD solo cambian tests (orden de imports de
  ruff, `noqa` y `recursos: tuple`) y `progress/`; nada del alcance.
- [x] **RM2:** 4,6 s × 6 = 27,6 s por mutante, frente a una base de unos 29 s.
  Coherente con `-x` y un 90 % de muertos.
- [x] **RM3:** las 3 muertes nuevas no son equivalentes: `10001` (3 tests) y las dos de
  la guarda (`or` vuelve a emparejar la reclasificada; `!=` deja sin base a las
  `extra_auto` de verdad). Los 73 restantes, ya recorridos en la pasada 1.
- [x] **RM4** (copia en scratchpad): 10001 → 3 failed; sin la guarda → 1 failed.
- [x] **RM5:** muestra elegida, **#4 `p.peso > 0 → >= 0`**.
  - El script del implementer lo prueba solo a través de `repartir_dia`, que nunca
    pasa pesos 0 a `repartir`: obras con peso > 0, ordinarias ajustables con horas
    > 0. Por ese camino, la rama mutada no se ejercita.
  - Lo reproduje directo sobre `repartir`, con el original frente al mutante:
    200.000 repartos, **140.795 con algún peso 0**, negativos incluidos y horas de
    parte → **0 distintos**.
  - El argumento del análisis se sostiene: hay al menos `faltan` participantes con
    resto > 0, y los de resto 0 van al final. Recomiendo aceptarlo.
- [x] **RM6:** la guarda está repuesta (cambio 2). No se quitó ninguna otra entre las
  campañas 2 y 3.
- [x] Los 8 análisis están completos, ninguno en `PENDIENTE`. Falta la aceptación del
  humano (condición de cierre, como en F-024).
- [x] «Evidencias» al día: 1391/487, 100 %, 84/76/8, 6 workers y tiempos.

## Pasada 2 · Lo esencial de la pasada 1, repetido

- **Tests existentes tocados en toda la rama:** `dobles.py`, `test_f003_r15`,
  `test_f015_r20` y `test_f037_revert` (`f037_r9`, enmienda A). Es lo que permiten
  design §5 y la enmienda A, y no cambió desde la pasada 1: el delta solo toca
  `test_f045_*`.
- **Ejemplos del humano** (`repartir_dia`, reejecutados en HEAD): 10 + 4, J 8 → 5,5 + 4,5
  y 2,5 + 1,5 · 5 + 4, J 8 → 4,5 + 0,5 y 3,5 + 0,5 · viernes candef 9, J 6 → 3,5 + 1,5 y
  2,5 + 1,5 · jueves, J 9 → sin ajustes. `test_f045_r33_*` los repite con el conciliador.
- **Sin cambios** desde la pasada 1: modo residual de las congeladas y R25; papelera en
  memoria (DA9); `esta_congelado`, `ESTADOS_CONGELADOS` y `_congelado` intactos; diff
  vacío contra `dev` en sv1, sv2, sv4, sv5, `infra/`, `CLAUDE.md`, `orm_models.py` y los
  dos `jornada_resolver.py`.

## Checkpoints (pasada 2)

**C1** [x] init.sh en verde · [x] ficheros base. **C2** [x] una `in_progress` · [x] rama ·
[x] `current.md` · [x] `history.md`. **C3** [x] hexagonal · [x] primera línea con ruta
(también `equivalentes_F-045.py`) · [x] sin prints, secretos ni dependencias.
**C3 bis** [N/A] ningún documento nuevo en `docs/` en el delta · [x] sin PDF ni
ofimática · [N/A] nada redactado. **C4** [x] trazabilidad (tabla de la pasada 1, más
R2 y R25 ampliados) · [x] sin red ni BBDD · [x] MANUAL con su comando exacto (M1, el
despliegue y M2). **C4 bis** [x] (sección anterior). **C4 ter** [N/A] el repo no tiene
`rutas_sensibles.json`. **C5** [x] T1–T13 `[x]` · [x] sin temporales (el script de
`progress/` es evidencia que cita el informe) · [x] `features.json` coherente.

## Observaciones (no bloquean)

1. `current.md` sigue diciendo «82 mutantes, 73 muertos, 9 supervivientes»: el líder
   debe poner 84/76/8 al cerrar.
2. `equivalentes_F-045.py` no prueba #4 por la rama mutada (ver RM5). Conviene añadir
   un comparador directo de `repartir` con pesos 0. El docstring dice 45 s; medí 60.
3. La precondición de ≤ 4 decimales no la impone nadie: `horas` es `Float`. Si
   entrara una hora con más decimales, R1 seguiría exacto, pero el desempate de R2
   trabajaría a resolución de 10⁻⁴ h. Hoy ningún origen produce esos valores.

**Automejora (propuesta, no aplicada)** para RM5 en `reviewer.md`: comprobar que la
demostración ejecutable **alcanza la línea mutada** (cobertura de la rama o un
contador). Un corpus que nunca la ejecuta da «equivalente» por vacuidad.

---

## Pasada 1 (resumen; texto íntegro en `git show 6c2f94b:progress/review_F-045.md`)

Revisión completa · `git diff dev...HEAD` hasta `7144932` · **CHANGES_REQUESTED**.

- init.sh en verde, sv3 1387 passed, cobertura 100 %. Mi propiedad propia dio 16.172
  días cuadrados y 0 fallos. Ejemplos del humano exactos, tests tocados según design §5,
  papelera, modo residual e intactos correctos. `azure-apps` en commit local `b4df33e`.
- Mutación (campaña 2: 82/73/9, 383,4 s): recálculo correcto. RM1–RM4 [x].
- **Cambios requeridos:**
  1. El superviviente `_RESOLUCION = 10001` no era equivalente: el redondeo bancario
     deshace el empate de R2. Había que añadir el test en `repartir` y en
     `repartir_dia` y corregir el análisis.
  2. RM6: guarda `and tipo_linea == EXTRA` quitada de `_lineas_dia`; una `extra_auto`
     reclasificada y congelada daba `(1, 8→5,5), (2, 2→0)`. Reponerla con su test.
  3. `current.md`: byte CR en `.\redeploy` y fichero en CRLF; volver a LF.
  4. Relanzar la mutación en la HEAD final, con una demostración ejecutable para
     cada equivalente (RM5).
- Automejora propuesta: en mutantes de escala o redondeo, exigir un empate de restos.
