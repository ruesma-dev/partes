<!-- progress/impl_F-045.md -->
# F-045 · Informe del implementer: reparto ponderado de la jornada entre obras

Rama `feature/F-045-reparto-ponderado-entre-obras` (worktree `partes-wt-f045`),
rigor **crítico**, solo sv3. Bloqueada en T4 y desbloqueada el mismo día
(2026-10-14) con la **opción A** del humano (`progress/current.md`). R33
(candef 9) se añadió después, a petición del humano.

## Qué cambió

| Tarea | Commit | Ficheros |
|---|---|---|
| T1 | `f500429` | `application/services/reparto_ponderado.py` (nuevo): `PASOS`, `elegir_paso`, `Participante`, `repartir` |
| T2 | `1ca0ab8` | `LineaDia`, `Ajuste`, `ResultadoDia`, `repartir_dia` |
| T3 | `4c9d3ae` | `diferencias_ideal` (R25) |
| T4 | `198a8f8` | `sqlalchemy_parte_repository.py`: `fetch_registros_para_recurso` trae `horas_orig`, `deleted_at_utc`, `extra_auto`, `line_index` y `empleado_line_no`. Además `tests/dobles.py`, la enmienda A (design §4/§5, R27, T4) y `test_f037_r9` |
| T5 | `8a11c74` | `recurso_conciliador.py`: `repartir_dia` sustituye al recorte/pivote por `registro_id` mayor; la papelera sale del grupo; nuevos `_lineas_dia` y `_medir_ideal`; `repartos_con_congeladas` en el dict y en el log final; INFO de reparto |
| T6 | `1f1b5d7` | valores esperados de los tests de design §5 (tabla abajo) |
| T7 | `9266555` | solo comprobación |
| T8 | `9ded4f4` | `docs/ARCHITECTURE.md` (semántica 3), `docs/referencia/partes-proyecto.md` |
| T9 | `4960287` | `azure-apps/partes.md` §3.3, con commit local `b4df33e` en `azure-apps` (solo `partes.md`, +4 −1) |
| T10 | `cc3f910`, `f9931a2` | refuerzo tras la mutación e informe `progress/mutacion_F-045.md` |
| T13 | `3143e5d` | R33 candef 9 (`requirements.md`, `tests/test_f045_conciliar.py`) |

Tests nuevos: 211 en total, repartidos en `test_f045_reparto_puro.py` (130),
`test_f045_reparto_dia.py` (53) y `test_f045_conciliar.py` (28); 4 de ellos son
de la pasada 2.

## Decisiones de diseño

- **Cuentas en enteros**: `repartir` cuenta en pasos enteros y con los pesos
  en diezmilésimas de hora. Suelos y restos salen con `//` y `%`, así que la
  suma es exacta.
- **Un solo paso por día**: `elegir_paso(J', pesos de obra + horas de las
  ordinarias ajustables)`, el mismo en los dos niveles. design §3 nombraba un
  `paso'` sin definirlo; con un paso único R28 se cumple también dentro de
  cada obra.
- **R5**: si nadie tiene peso > 0, todas las cuotas son 0.
- **Desempate**: después de DA4 decide `repr(clave)`, para que el orden de
  entrada nunca influya.
- **Ordinaria ≤ 0**: la fija `repartir_dia`. El conciliador solo pasa
  `fija = _congelado(r)`, que ya incluye la pareja de F-037.
- **WARNING de R23**: mismo literal y mismas cifras que hoy («faltan |Σord − J|
  h… hay Σ no congeladas»). La condición nueva equivale a la de hoy: los 18
  tests de `test_f015_r32` pasan sin tocarlos.
- **WARNING de R25**: «el reparto ideal cambiaria lineas ya en Sigrid o de
  parte aprobado», con fecha, recurso y `registro N antes -> después`, sin DNI.
  No usa la palabra `CONGELADAS`, que es la del WARNING de R23.
- **INFO de R30**: sale con `n_lineas >= 2`, o con una sola línea si hay marca
  de jornada de F-015. Así se conserva la traza que daban los antiguos INFO de
  recorte y de jornada incompleta (`test_f015_r28` sigue verde).
- **Atajo `delta == 0` eliminado**: aunque las ordinarias sumen J, un día con
  extras explícitas puede necesitar reparto (R19).
- **Papelera (R27)**: se filtra en memoria al formar los grupos. El casado de
  recurso no cambia.
- **Enmienda A**: `LineaDia.extra_auto` y `LineaDia.base_id` son opcionales.
  El conciliador calcula `base_id` con `pareja_extra.clave_pareja`, sin tocar
  ese módulo.

## Tests existentes reescritos: antes → después

Formato `(registro_id, ordinaria, extra)`.

| Test | Antes | Después |
|---|---|---|
| `test_f003_r15_…recorta_desde_el_registro_de_mayor_id` (5+5, J 8) | `[(2, 3, 2)]` | `[(1, 4, 1), (2, 4, 1)]` |
| `test_f003_r15_…desborda_al_siguiente_registro` (5+5+5, J 8) | `[(3, 0, 5), (2, 3, 2)]` | `[(1, 3, 2), (2, 2.5, 2.5), (3, 2.5, 2.5)]` |
| `test_f003_r15_agrupa_por_recurso_y_dia_across_obras` (4+6, J 8) | `[(2, 4, 2)]` | `[(1, 3, 1), (2, 5, 1)]` |
| `test_f015_r20_el_recorte_empieza_por_el_registro_de_mayor_id` (5+5, J 6) | `[(2, 1, 4)]` | `[(1, 3, 2), (2, 3, 2)]` |
| `test_f015_r20_el_exceso_desborda_al_registro_anterior` (5+5+5, J 6) | `[(3, 0, 5), (2, 1, 4)]` | `[(1, 2, 3), (2, 2, 3), (3, 2, 3)]` |
| `test_f015_r20_agrupa_por_recurso_y_dia_across_obras` (4+4, J 6) | `[(2, 2, 2)]` | `[(1, 3, 1), (2, 3, 1)]` |
| `test_f037_revert::test_f037_r9_la_unica_clave_nueva_es_la_marca` | 17 claves | + `horas_orig`, `extra_auto`, `deleted_at_utc`, `line_index`, `empleado_line_no` |

En cada uno solo cambian el valor esperado y una línea de comentario
«F-045 … antes …»; el docstring de `test_f037_r9` nombra F-045. **No cambian**
`test_f015_r32` ni `test_f037_dos_pasadas::test_f037_r10`. Comprobado con
`git diff dev --stat -- services/partes-persistencia/tests`: solo salen
`dobles.py`, los tres `test_f045_*`, `test_f003_r15`, `test_f015_r20` y
`test_f037_revert`.

## Fase RED (trazas reales)

Todos los comandos se lanzaron desde `services/partes-persistencia` con
`C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest -q …`.

**T1 · R1–R6** (`tests/test_f045_reparto_puro.py`), sin el módulo:
```
tests\test_f045_reparto_puro.py:18: in <module>
    from application.services.reparto_ponderado import (
E   ModuleNotFoundError: No module named 'application.services.reparto_ponderado'
1 error in 0.46s
```
En verde: `125 passed in 0.29s`.

**T2 · R7–R23, R26** (`tests/test_f045_reparto_dia.py -k "repartir_dia"`),
con un `repartir_dia` vacío que devolvía `ResultadoDia(True, 0.5, (), 0, 0)`:
```
>       assert _aj(repartir_dia([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0)) == {
            1: (5.5, 4.5), 2: (2.5, 1.5)}
E       assert {} == {1: (5.5, 4.5), 2: (2.5, 1.5)}
31 failed, 5 passed in 1.38s
```
Los 5 que pasaban son los que esperan «sin ajustes». En verde: `36 passed`.

**T3 · R25** (`-k "ideal"`), con `diferencias_ideal` devolviendo `()`:
```
___________________ test_f045_r25_ideal_caso_real_0678_0704 ___________________
E       assert () == ((1, 8.0, 2.5...2, -4.0, 1.5))
7 failed, 4 passed, 36 deselected in 0.70s
```

**T5 · integración** (`tests/test_f045_conciliar.py`), contra el
`recurso_conciliador.py` de `dev` (el nuevo, apartado con `git stash`):
```
E       assert [(1, 8.0, 2.0), (2, 0.0, 4.0)] == [(1, 5.5, 4.5), (2, 2.5, 1.5)]
_____________ test_f045_r27_la_papelera_ni_pesa_ni_recibe_split ______________
E       assert [(1, 8.0, 2.0), (2, 0.0, 4.0)] == [(1, 8.0, 2.0)]
________________ test_f045_r30_info_del_reparto_con_dos_obras _________________
E       StopIteration
___________________ test_f045_r25_caso_real_avisa_y_cuenta ____________________
E       KeyError: 'repartos_con_congeladas'
___________________ test_f045_r29_dos_pasadas_dan_lo_mismo ____________________
E       assert 2 == 3
12 failed, 10 passed in 2.91s
```
Los 10 que pasaban comprueban «lo que no cambia»: R20, R21 ×4, R24 (la 0704
sigue en 0 + 8, como hoy), R26, la lectura de R27 (hecha ya en T4), R30 con
una sola línea y el orden de R29. En verde: `22 passed`.

**T13 · R33**: estos tests se añadieron **después de la campaña de
mutación**, sobre código ya medido, y no tienen fase RED. Pasaron a la primera
con el algoritmo de §3 y DA4, sin tocar código: `3 passed`.

## R33 · candef 9 (pedido por el humano el 2026-10-14)

Los tres casos pasan por `_reclasificar_extras_jornada` con la jornada real
de `_detalle_jornada` (mapa `9:42`, `CalendarioFake`), en la semana del 16
al 20 de marzo de 2026.

| Caso | J real (log) | A 5 h | B 4 h |
|---|---|---|---|
| Viernes laborable | `jornada_dia=6.00`, `ultimo_laborable=si` | 3,5 + 1,5 | 2,5 + 1,5 |
| Jueves | 9 (sin marca) | 5 + 0 | 4 + 0 (ningún split) |
| Viernes festivo, jueves trabajado | **6, no 15** (`jornada_dia=6.00`, `ultimo_laborable=si`) | 3,5 + 1,5 | 2,5 + 1,5 |

Con el viernes festivo, F-015 hace del jueves el último laborable y le da
`S − 4c = 42 − 36 = 6`, porque los festivos entre semana cuentan como
jornada. Ese es el valor real del código. Ningún esperado discrepó.

## MANUAL pendiente (humano)

- **M1**, antes de desplegar: SQL de design §9 en la base `partes`.
- **Despliegue solo de sv3**: `.\redeploy_partes.ps1 -Solo sv3` desde `infra/`.
- **M2**: Log Analytics de `ca-sv3-persistencia` con `Log_s has 'reparto'`;
  después, la SQL de F-042 M1 sobre un día con dos obras sin aprobar.
- **Aceptar las 8 justificaciones de mutantes equivalentes** (rigor crítico),
  cada una con su demostración ejecutable (`progress/equivalentes_F-045.py`).

## Fuera de alcance

- El reajuste en Sigrid de lo ya congelado es F-046 (design §8). Hasta
  entonces el caso real de la 0678 sigue en 0 + 8 (R24); F-045 solo lo mide.
- Pasadas concurrentes (DA10).

## Pasada 2 (review del 2026-10-14: CHANGES_REQUESTED, ciclo 1)

`progress/review_F-045.md` se commiteó tal cual (`6c2f94b`). Arreglos en
`259e609`:

1. **Superviviente `_RESOLUCION = 10_000 → 10001`: no era equivalente** (el
   análisis anterior era erróneo). Tests nuevos: el caso del reviewer en
   `repartir` (2 h entre 1,5 y 2,5 → 0,5 y 1,5) y en `repartir_dia`
   (congelada 6 + A 1,5 + B 2,5, J 8 → A 0,5 + 1 y B 1,5 + 1), más un
   **modelo exacto con fracciones** comparado en 3.000 repartos con horas de
   parte. Los tres fallan con 10 001 (`3 failed`, comprobado a mano).
   Revisión del código: con una escala potencia de 10 y horas de ≤ 4
   decimales, `peso × 10 000` es entero salvo ruido ≪ 0,5 y `round` nunca cae
   en un .5. Por eso no hace falta cambiar el cálculo: se documenta la
   condición en `_RESOLUCION` y la vigila el test del modelo.
2. **Guarda de `base_id` repuesta** (`extra_auto and tipo_linea == EXTRA`):
   cubre una `extra_auto` reclasificada a normal en sv4 y congelada. Test
   `test_f045_r25_extra_auto_reclasificada_a_normal_pesa_por_si_misma`, con
   su RED contra la versión sin guarda:
   ```
   E       AssertionError: assert 'registro 1 8.00 -> 5.00' in '[recurso-concil] reparto 2026-03-02 (recurso=501): el reparto ideal cambiaria lineas ya en Sigrid o de parte aprobado (se mantienen; F-046): registro 1 8.00 -> 5.50, registro 2 2.00 -> 0.00.'
   1 failed, 27 deselected in 1.77s
   ```
3. **`progress/current.md`**: restaurado el literal `.edeploy_partes.ps1
   -Solo sv3` (había un byte CR que hacía que git tratara el fichero como
   binario) y vuelto a LF. `git diff dev --stat` del fichero: +55, solo la
   sección de F-045.
4. **Mutación relanzada** en `259e609` (campaña 3): 84 mutantes, 76 muertos,
   **8 supervivientes**, todos equivalentes y con **demostración ejecutable**
   (RM5) en `progress/equivalentes_F-045.py`. El script carga el módulo
   mutado y lo compara con el original en 20.000 días y 3.000 grupos con
   horas de parte: `8 mutantes, 0 distintos`, exit 0. Como control, con el
   mutante 10 001 sale DISTINTO. La campaña 3 ya incluye los tests de R33.
   Después de `259e609` solo cambian tests (avisos de ruff) y `progress/`;
   nada del alcance de la mutación, así que la campaña sigue valiendo (RM1).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv3 | **1391 passed** en 31,57 s (`bash harness/init.sh`) |
| Tests raíz | **487 passed, 3 skipped** (`bash harness/init.sh`) |
| Tests nuevos de F-045 | 211 passed en 2,97 s |
| Cobertura de líneas cambiadas | **100,0 %** (162/162; umbral 80 %, crítico), según `PUERTA COBERTURA` |
| Mutación, campaña 3 (HEAD `259e609`, la del informe) | 84 generados, **76 muertos**, **8 supervivientes**, 0 timeouts, 0 sin veredicto, 387,1 s; completa, 6 workers, `--timeout 600` |
| Campañas anteriores | 1: 88/64/24 (442,9 s) · 2: 82/73/9 (383,4 s) |
| Supervivientes | 8 equivalentes, cada uno con su demostración ejecutable (`8 mutantes, 0 distintos`): 6 son `>`/`>=` o `<`/`<=` contra una tolerancia; 1 es el redondeo a 6/7 decimales; 1 es `peso > 0` → `>= 0`. Pendientes de que el humano los acepte |
| `bash harness/init.sh` | **ENTORNO LISTO**, todas las puertas en verde. ruff: 698 avisos, los mismos que `dev`; los de los ficheros nuevos se corrigieron |
