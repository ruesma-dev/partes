<!-- progress/review_F-085.md -->
Revisión de evidencias desde 05e25f6 · delta `05e25f6..aef7024`

# F-085 · Review

**Veredicto final: APPROVED** (pasada de evidencias, HEAD `aef7024`). Pasada principal:
**APPROVED en `05e25f6`** (pasada 1 en 33663c4: CHANGES_REQUESTED por R1 y R8/D16, resueltos en
la 2.ª); resumida abajo, sigue válida.

**Nivel de rigor: `critico`** (declarado): fase RED, cobertura ≥ 90 %, mutación con 0
supervivientes sin justificar, RM1–RM7. Capa e2e N/A (ningún servicio declara el bloque). El
diff no toca `harness/rigor.local.json` (la capa local solo trae `mutacion.timeout_por_mutante_s`).

## Pasada de evidencias

**C1 [x]** `ARNES_SIN_CACHE=1 bash harness/init.sh`: **exit 0 a la primera**, sin caché ni
repeticiones (y con el equipo cargado por campañas de otros proyectos). Raíz 2553 passed,
50 skipped (1422 s); sv1 74, sv2 579, sv3 2989, sv4 4264 (1056 s), sv5 1989. `PUERTA COBERTURA`
100,0 % (220/220), `PUERTA TAMAÑO` dentro, `CAPA E2E: N/A`, `ENTORNO LISTO`. Árbol limpio después.

**Delta sin producción [x]**: `git diff --name-only 05e25f6..HEAD` = `progress/` (impl,
mutación .md/.json, `equivalentes_F-085.py`, review), `tasks.md` (T9, T14 `[x]`) y 3 ficheros de
tests (`test_f085_conversion.py`, `test_f085_inicio_movido_sv4.py` de sv4;
`test_f085_inicio_movido.py` de sv5). Lo aprobado en 05e25f6 sigue valiendo. Sin guardas
quitadas ⇒ **RM6 N/A**.

### C4 bis · mutación (RM1–RM5)
- [x] **RM1**: el informe mide `17dee7e3cea3…` (completo); `git diff --stat 17dee7e..HEAD` solo
  `progress/` y `tasks.md`: el alcance medido es el revisado.
- [x] **Recálculo independiente** (`harness.alcance` + `generar_mutantes`, base `dev` = b5e935b):
  14 ficheros, 595 líneas, 172 mutantes, fila a fila igual que el informe; 110 candidatos (uno
  por línea, semilla 20261030), tope `min(300, max(100, ⌈0,6·110⌉))` = 100. Coincide.
- [x] **Los 5 supervivientes existen** como mutantes reales del generador, operador `veracidad`,
  con el mismo texto original→mutado del informe (comprobados los 5).
- [x] **JSON y log coherentes**: el JSON da 100 evaluados = 95 muertos + 5 supervivientes; el log
  `mutacion_F-085_repaso.log`, 19 evaluados (9 supervivientes + 10 de control) = 14 muertos,
  5 supervivientes, 0 timeouts, 0 sin veredicto, línea base en verde. Sin «CAMPAÑA NO VÁLIDA».
- [x] **RM2**: repaso 4613 s = 19 × 242,8 s; media con suite entera 394,6 s frente a línea base
  sv4 836 s, coherente con `-x` y 14/19 muertos (los 3 supervivientes de sv4 agotan suites
  enteras, los 2 de sv5 ~40 s). 1.ª pasada: 14 416 s para 100 mutantes con 3 workers. Sin saltos
  de orden de magnitud. **Campaña no reejecutada**: 4613 s y 14 416 s según los informes (> 60 s)
  y por orden del líder.
- [x] **RM3**: repasados todos los muertos de operadores propensos a equivalentes (`booleano`,
  `veracidad`, `formato`, `entero`): defaults de `ClaseNueva` (cambian `actual`), `frozen=False`
  (hash y mutabilidad), `:09d` (fecha), `getattr(..., True)` (dobles sin el atributo). Ninguno
  equivalente.
- [x] **Ficheros sin mutantes**: las 2 declaraciones escritas y ciertas. Prueba de control
  (`generar_mutantes` con el fichero entero, sin exclusión de alcance): 3 mutantes en
  `recalculo_publisher.py` y 320 en `sqlalchemy_parte_repository.py`, luego el generador
  funciona y **el cero es legítimo**: las líneas en alcance son comentarios, docstring, dos
  constantes de cadena y una columna/nombre/clave más, sin operador ni rama.
- [x] `grep -c PENDIENTE progress/mutacion_F-085.md` = 0.

### Los 4 tests nuevos (9495e47) [x]
Reproducidos con el mutante **real** del generador (`aplicar_mutante`) en copias de sv4/sv5 en
mi scratchpad, nunca en el árbol de trabajo:

| Mutante | Test | Original | Mutado |
|---|---|---|---|
| `parte_repository.py:2644` `mover_inicio = False` → `True` | `test_f085_r29_roles_de_racha_apagado_por_defecto` | 1 passed | 1 failed |
| `racha_ciz.py:106` `frozen=True` → `False` | `test_f085_decision_inicio_inmutable` | 1 passed | 1 failed |
| `parte_repository.py:3410` `elif clase.es_incidencia` → `not` | `test_f085_deshacer_describe_la_clase_nueva` | verde (init) | 2 failed (CIA, HL01) |
| `parte_repository.py:748` `frozen=True` → `False` | `test_f085_resultado_hora_inmutable` | verde (init) | muerto en el repaso (no reproducido a mano) |

Etiquetado correcto: solo `r29_*` lleva `rN` y afirma R29 («el interruptor apagado, como hoy»,
y también el encendido); los de diseño (`*_inmutable`) y el del texto del deshacer van sin `rN`.

### RM5 · los 5 equivalentes [x] (aceptación pendiente del humano)
- `progress/equivalentes_F-085.py`, desde la raíz de la copia con el `.venv`: «5/5 equivalentes
  demostrados», **exit 0** (48 s; #1 84, #2 6048, #5 252, #8 4000, #9 4000 casos). Leído entero:
  muta exactamente el texto del informe, dentro de su función y una sola vez; el dominio es el
  real (AST de `return` y asignaciones, `TABLA` real de `test_f025_deteccion`, tipos
  `ClaseIncidencia`/`LineaSigrid`/`ParteSigrid` sin `__bool__`/`__len__`, el
  `partes = {h: ParteSigrid(...)}` real del pipeline); cada control negativo (`is None`
  invertido) aborta con exit 1 si no distingue, y el banco de sv5 exige ≥ 50 `mover` y ≥ 50
  `parte_cerrado`.
- **Muestra de uno, reproducida por mi cuenta: #2** (`conversion_clase.py:89`), con el mutante
  del **generador** (no el texto del script) y un banco propio: los códigos de la tabla + 3000
  cadenas al azar (semilla 1128) × las dos tablas. `error_de_codigo` es siempre `None` o una
  cadena no vacía; 6016 casos de `decidir` iguales; el control negativo difiere en 4622.

**Criterio sobre cada uno.** Los cinco son la misma familia: `x is (not) None` frente a la
veracidad sobre un valor que solo es `None` o algo siempre verdadero. **La justificación se
sostiene en los cinco**; ningún test razonable los mata sin inyectar un valor que el código no
produce (un `ClaseIncidencia` con `__bool__`, un motivo «», un `ParteSigrid` falso).
- #1 `conversion_clase.py:78`: `por_sigrid.get` sin defecto, dataclass siempre verdadera.
- #2 `conversion_clase.py:89`: tres `return` de `error_de_codigo`, ninguno vacío (reproducido).
- #5 `parte_repository.py:3388`: hereda el dominio de #2 por `ClaseNueva.error`.
- #9 `racha_ciz.py:324`: `inicio_previo` da `None` o `primera` (`LineaSigrid`).
- #8 `racha_ciz.py:327`: `ParteSigrid` siempre verdadera.

Matiz: dependen de que nadie añada `__len__`/`__bool__` a esas dataclasses; el script lo vigila
(`_sin_bool`), pero solo si alguien lo vuelve a ejecutar.

**Evidencias de `impl_F-085.md` [x]**: coinciden con el informe de mutación (172 / 100 / 95 / 5 /
0) y con este `init.sh` (220/220; sv4 4264 y sv5 1989, con los tests nuevos). Fila «Capa e2e»
presente.

### Observaciones (no bloquean)
1. La fila «Tests ejecutados» de «Evidencias» aún cita el ciclo 1 (12 442); hoy suman 12 448
   (+6 de la campaña). Cosmético.
2. La aceptación de los 5 equivalentes es del humano: la avalan la demostración y mi muestra.
3. Push de `azure-apps` (de la principal): del líder con el humano.

## Pasada principal (APPROVED en 05e25f6), resumida
- **C1** [x]: 1.ª ejecución en verde salvo el inestable conocido
  `test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`; 2.ª con exit 0. **C2** [x]: una activa, en
  su rama.
- **C3** [x]: hexagonal (`conversion_clase.py` y `racha_ciz.decidir_inicio` puros), convenciones;
  LÍMITE DE SERVICIO: `es_codigo_ci` (sv5, incluye `CIZ`) y `es_codigo_incidencia` (sv4) no son
  gemelas. **C3 quater** [x]: `azure-apps` `761c28e` y `60d7f70`, solo `partes.md`, aparte.
- **C4** [x]: cada R con su test, sin red; M1, M2, M3 y M5 con comando; M4 fuera (D15).
- **C4 bis**: RED real y cobertura 100 %; **RM7** en copias del scratchpad: bajar la guarda R19
  por debajo de los mensuales ⇒ rojo; llevar el 400 de R5/R6 tras la escritura ⇒ rojo. El delta
  no toca esas puertas.
- **C5** [x]: T1–T14 y T18 `[x]` con commits `F-085 Tn:`; T15–T17 MANUAL del humano (N/A
  justificado); `features.json` = `in_review`.
- **C3 bis / C3 ter / C4 ter**: N/A (sin documento de fuera ni conversación nueva ni rutas).
- Ciclo 1: R1 (`_fin_movido` con `es_codigo_fin`, con RED); D16 = (b) («,1 b», humano,
  2026-11-27) con R8, R13 y design §2 enmendados. Tests ajenos enmendados con motivo.

### Cobertura requisito → test (todos en verde; detalle en la tabla de la principal, `git show 7bf0a63:progress/review_F-085.md`)
| R | Test(s) |
|---|---|
| R1–R11 | sv4 `r1_*`, `r2..r7_puro_*`, `r2..r4_repo_*`, `r5_r6_*`, `r7_repo_*`, `r8_*`, `r9_*`, `r10_*`, `r11_*` |
| R12–R18 | sv3 `r12_*`, `r15_*`–`r18_*`; sv4 `r13_js_*`, `r13_d16_*`, `r14_*` |
| R19–R27, R30–R32 | sv5 `r19_*`, `r20_*`, `puro_r21..r27_*`, `pipeline_r21..r32_*` |
| R28–R29 | sv4 `r28_*` (4), `r29_*` (6, con el de la campaña), `settings_mover_inicio_*` |
| R33 / R34 | `test_f085_documentacion.py` (4) / MANUAL: M1, M2, M3 y M5 |

**Observaciones de la principal (abiertas)**: push de `azure-apps` sin confirmar (líder); aviso
D16 por id y D8 (`manual` en alta y clon de celda, decidido por el humano): a mirar en M1.

**Automejora (propuestas, no aplicadas)**:
- `CHECKPOINTS.md` C4: un requisito de selección múltiple cuyo único test corre con la cola
  apagada no está demostrado en producción.
- `test_f047_r23`: que cuente también `var x = function`.
- `reviewer.md` RM5: la muestra se reproduce con el mutante de `generar_mutantes` y un banco
  propio, no con el texto ni el banco del script del implementer (si no, el script se valida a
  sí mismo).
