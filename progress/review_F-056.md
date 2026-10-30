<!-- progress/review_F-056.md -->
Revisión incremental desde 3b37113 (pasada 2) · rama `feature/F-056-franquicia-de-extras`, HEAD 8c6b9e8
# F-056 · Franquicia de extras — revisión
**Veredicto pasada 2: APROBADO (APPROVED)**. La pasada 1 (más abajo, resumida) sigue valiendo: nada del
delta la invalida. Fuera de esta pasada, por encargo: M2–M4, T21 y T22 (humano).
**Rigor** `critico` (declarado): fase RED, cobertura ≥ 80 %, mutación sin supervivientes sin
justificar, RM5 y verificaciones MANUAL listadas.

## Pasada 2: ejecución

- `bash harness/init.sh` → **ENTORNO LISTO**: raíz 529 passed, 3 skipped (180 s); PUERTA COBERTURA
  **[OK] 99,0 %** (1049/1060); PUERTA TAMAÑO **[OK]** (150/150, 250/250, 204/220, review 139/140 antes
  de esta edición).
- sv3, sv4 y sv5 salieron de caché; lanzados a mano con `python -m pytest -q -p no:cacheprovider`
  desde cada ruta: sv4 **3224 passed, 1 skipped** (1133,5 s); sv5 **1485 passed** (22,9 s); sv3
  **2345 passed** (63,2 s). Árbol limpio después.

## Pasada 2: delta

1. **DA32 / T27** [x]. `fq.lineas_del_recurso` es pura y `_propuesta` la aplica a las líneas del día y
   a las del periodo; es el único llamador de `elegir_obra`. `_dia_ajuste`, `varios_recursos` y
   `lineas_trabajador_periodo` no cambian. Decisión humana en `design.md` §7 con su literal; R5 y R7
   enmendados. Mi observación 6 queda cubierta en preflight (`da32_preflight_…`) y `decidir`
   (`da32_decidir_…`). Fase RED real en `impl_F-056.md` (3 failed: obra 0200 en vez de 0100).
   Quitar el filtro en la copia da **2 failed, 230 passed**: esos tests protegen el caso de verdad.
2. **Observaciones**. Obs. 1 [x] T20 y T26. Obs. 2 [x] Evidencias con «4 workers» y «aceptados».
   Obs. 4 [x] los tres docstrings; `orm_models.py` byte-idénticos (`cmp`). Obs. 5 [x]
   `partes-proyecto.md` y `azure-apps` 33ebb49 (una línea, sin datos nuevos). Obs. 7 [x]
   `test_f056_r1_r41_da22_…`. Obs. 3 sigue del humano.
3. **Merge y rigor** [x]. `git diff 2e910d1^1 2e910d1` trae solo `reviewer.md` (RM4), `BACKLOG.md`,
   `features.json`, `rigor.json` y `current.md`: **nada bajo `services/` ni `infra/`**. `rigor.json`:
   solo `timeout_por_mutante_s` 300→600; la decisión consta en dc693cc («si, y continua»).

## Pasada 2: mutación (`progress/mutacion_F-056_da32.md`)

- **Recálculo puro** 3b37113..2e910d1: **25 líneas y 4 mutantes**, igual fichero a fichero (3 en
  `franquicia.py:192`, 1 en `app.py:2789`; los docstrings no generan mutantes). Sin cabecera NO VÁLIDA
  ni base rota. **Campaña no reejecutada: 3800,9 s según el informe**, por encima de 60 s.
- **RM1** [x]: medida en 2e910d1; hasta HEAD solo cambian un test y `progress/`, ninguna producción.
- **RM2** [x]: 4 × 950,2 ≈ 3800,9; media frente a base 965–969 s con 2 workers. Los muertos caen en
  `test_f056_*`, ya avanzada la suite: coherente con `-x`.
- **RM3** [x]: ninguno de los 4 es equivalente. **RM5**: N/A, el delta no declara equivalentes.
  **RM6**: N/A, no se quita ninguna guarda.
- **RM4** [x], copia de sv4 en el scratchpad, `sys.executable -m pytest`, mismo intérprete y base
  **exit 0** (232 passed en `franquicia`, `decisiones` y `vista`):

| Mutante | Resultado |
|---|---|
| `or 0`→`or 1` (superviviente) | exit 1: 1 failed, 81 passed; el test nuevo solo: 1 failed |
| `or`→`and` | exit 1: 15 failed, 217 passed |
| `== rec`→`!= rec` | exit 1: 14 failed, 218 passed |
| `app.py:2789` `==`→`!=` | exit 1: 1 failed, 231 passed |

  El superviviente queda muerto por `test_f056_da32_linea_sin_recurso_no_es_del_recurso_1`, y los
  otros tres reproducen «muerto». Cero supervivientes sin justificar.

## Pasada 2: checkpoints

- **C1** [x] `init.sh` en verde. **C2** [x] una sola feature `in_progress`, rama correcta, `current.md`
  al día. **C3** [x] `franquicia.py` sigue puro; sin `print`, secretos ni dependencias.
- **C3 bis** [x] el diff de `partes-proyecto.md` y de `azure-apps` es una sola frase, sin datos
  sensibles; [x] N/A cabecera y redacción: nada nuevo de fuera. Sin originales.
- **C4** [x] trazabilidad abajo. **C4 bis** [x] RED real, cobertura 99 %, mutación verificada, RM1,
  RM2, RM5 (N/A justificado) y RM6, «Evidencias» presente. **C4 ter** N/A: sin
  `harness/rutas_sensibles.json`.
- **C5** [x] T1–T20 y T23–T27 con `[x]` y commits `F-056 Tn:`. T21 y T22 abiertas: fuera por encargo,
  son del humano. `features.json` sigue `in_progress`, su estado real.

## Pasada 2: cobertura del delta

| Requisito | Test |
|---|---|
| R7, R48 (DA32) | `da32_lineas_del_recurso_solo_las_suyas`, `da32_linea_sin_recurso_no_es_del_recurso_1`, `da32_preflight_obra_del_recurso_del_ajuste`, `da32_decidir_obra_del_recurso_del_ajuste` |
| R1 | `r1_r41_da22_vale_la_x_de_sigrid_al_ejecutar` |

## Pasada 2: observaciones (no bloquean)

1. `docs/ARCHITECTURE.md:667` dice «la obra de más horas de ese día» sin decir que son las líneas del
   recurso. No es falso, pero conviene retocarlo. Igual el docstring de `elegir_obra`, que dice «del
   trabajador» cuando ya recibe solo las del recurso.
2. Sigue de la pasada 1: M2 antes de activar `FRANQUICIA_CAMPO_EXT=10` en producción.

---

## Pasada 1 (APROBADO, e3dff2f), resumen

Detalle íntegro: `git show 3b37113:progress/review_F-056.md`. Revisión completa de `dev...HEAD`
(base 39aef7b).

- **Ejecución**: `init.sh` verde, cobertura 99,0 %; a mano sv5 1485, sv3 2345, sv4 3220 passed.
- **Mutación**: recálculo 513 mutantes (2294 líneas) y 23 (156 líneas), coincidentes. Los 102
  supervivientes casan con mutantes reales. Campañas no reejecutadas (57 637 s y 273 s). RM1–RM6
  cumplidas; RM4 reproducido en #1, #3 y #4; RM5 sobre #95 (20 626 entradas, 0 diferencias).
- **Equivalentes**: 14, aceptados por el humano el 2026-10-29, literal «si»: #79, #90, #92, #3, #10,
  #17, #80, #86, #87, #84, #89, #95, #31 y #19.
- **Cuidado revisado**: escritura solo en sv5 y bajo `self._reg.lock`; sin `DELETE`; «no se sabe» ≠
  X = 0; R47 (tip 33) y R48 (por `recurso_ide`, nunca DNI); lista cerrada de `CLAUDE.md` intacta;
  `_actor` 18→20; R45/R46 reutilizan CAS y 409; documentación coherente.
- **Checkpoints**: C1, C2, C3, C3 bis (barrido sin coincidencias), C4, C4 bis y C5 en [x].
- **Cobertura**: 334 tests `test_f056_*`; cada R de R2–R34 y R36–R48 tiene test; R26 por el fixture
  autouse `_grabar`; R35 documental; R37 de proceso.
- **Observaciones**: las siete se resuelven o se heredan arriba. La 6 dio lugar a DA32.
