<!-- progress/review_F-040.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (merge-base `1a5b795`, HEAD `d099001`)

# F-040 · Review (pasada 1)

**Veredicto: CHANGES_REQUESTED.**

El código, los tests, la cobertura y la mutación están bien; no hay que tocarlos. El rechazo es solo
por `progress/current.md`: no trae el comando exacto de las MANUAL de T15 (C4) y arrastra texto que
ya no es verdad (C2). La pasada 2 será incremental, limitada a ese delta. Si el delta no toca el
alcance (RM1), no hace falta repetir la campaña de mutación.

**Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura de las líneas cambiadas, mutación
completa con 0 supervivientes y las MANUAL con su comando exacto en `current.md`.

## Qué ejecuté (resultados reales)

- **`bash harness/init.sh`**, dos veces:
  - 1.ª, **roja**: falla `tests/test_mutacion_prueba_de_verdad.py::test_A_antes_la_campania_paralela_daba_cero_supervivientes_falsos`
    (`assert 3 == 5`, la raíz tardó 299 s). Es un test del arnés que F-040 no toca. Aislado: 6 passed
    en 16 s.
  - 2.ª, **verde** (`ENTORNO LISTO`): raíz 461 passed / 3 skipped, `PUERTA COBERTURA` [OK] 100 % (66/66),
    `PUERTA TAMAÑO` [OK].
- **Suites de servicio a mano** (en `init.sh` venían de caché): sv3 1109 passed; sv4 1833 passed /
  1 skipped de diseño (13 min 45 s); sv5 537 passed.
- **JS con node v24.14.1:** los 37 tests f040 de sv4 pasan, ninguno saltado.

## Checkpoints

- **C1:** [x] `init.sh` termina con exit 0 (2.ª ejecución). [x] Están los ficheros base.
- **C2**
  - [x] Una sola feature `in_progress`.
  - [x] Rama correcta.
  - [x] `history.md` al día.
  - [ ] **`current.md` no describe solo la sesión activa.**
    - Conserva «F-039 · in_progress», pero `features.json` dice `done`. dev lo corrigió en `1114e33`,
      que la rama no tiene.
    - En F-040 sigue «Pendiente de decisión del humano; al retomar, seguir por T4», con la opción A
      ya aplicada.
- **C3**
  - [x] Hexagonal: la lógica está en `application/services`, el ORM y el repositorio en
    `infrastructure`; el dominio solo cambia un comentario.
  - [x] Los 11 ficheros nuevos llevan su ruta en la primera línea.
  - [x] Sin `print`, TODO, secretos ni dependencias nuevas.
  - [x] DNIs sintéticos.
  - [x] Trampas: el alias guarda los dos ides; las incidencias no se tocan; `orm_models.py` es
    **byte-idéntico** (`cmp`).
- **C3 bis** (`partes-proyecto.md`)
  - [x] Cabecera: N/A, no entra ningún documento de fuera.
  - [x] Sin PDF ni ofimática.
  - [x] Nada redactado.
  - [x] Barrido mío del diff de `docs/`: 0 coincidencias. Patrones: correo, IPv4, GUID,
    `password|secret|token|apikey|AccountKey|SharedAccess|Bearer`, `[0-9]{8}[A-Z]` y
    `[XYZ][0-9]{7}[A-Z]`.
- **C4**
  - [x] Trazabilidad completa (tabla de abajo).
  - [x] Sin red ni BBDD en los tests.
  - [ ] **T15, M2 y M3 no traen su comando exacto en `current.md`**: dicen «según `tasks.md`». M1 sí
    lo trae.
- **C4 bis**
  - [x] **Fase RED:** trazas reales de T2–T7 y T9–T12. T1 y T8 son caracterización. T11 incluye node
    sobre el `app.js` anterior.
  - [x] **Cobertura:** 100 %.
  - [x] **Mutación recalculada:** 225 líneas y **40 mutantes**, como el informe. Los dos timeouts
    existen con ese texto.
  - [x] **Muertos:** la campaña tardó 3244 s (> 60 s), así que **no la reejecuté entera**. RM4 sobre
    una copia en el scratchpad; el worktree quedó limpio.
    - `app.py:1431` or→and: 3 fallos. `reside is None`: 2 fallos. Los dos, como el informe.
    - `seleccion_sigrid.py:255` and→or: 15 fallos.
    - `casado_recurso.py:127` !=→==: 14 fallos.
  - [x] **Coste por mutante:** 3244 × 6 / 40 = 487 s. Encaja con 15 mutantes de sv4 (base ~545 s) y
    25 de sv3 (base ~22 s).
  - [x] Sin marca «NO VÁLIDA»; 0 sin veredicto; línea base en los 6 workers.
  - [x] **RM1:** medido sobre `0c851f4`; lo posterior solo toca `progress/` y `tasks.md`.
  - [x] **RM2:** media × W = 487 s; el total cuadra.
  - [x] **RM3:** sin equivalentes muertos.
  - [x] **RM5:** N/A, no hay supervivientes.
  - [x] **RM6:** no se quitaron guardas para matar mutantes. `ide in sin_dni` sale por R14; R18 añade
    una guarda.
  - [x] Campaña manual: N/A. 0 supervivientes. «Evidencias» completa, con 6 workers.
- **C4 ter:** [x] N/A, no existe `rutas_sensibles.json`.
- **C5**
  - [x] T1–T13 y T16 en `[x]`, cada una con su commit `F-040 Tn:`. T14 y T15 son MANUAL.
  - [x] Árbol limpio.
  - [x] `features.json` en `in_progress`.

## Lo que se pidió comprobar especialmente

- **Ninguna ruta casa sola sin DNI:** el nombre da `nombre_sin_dni` sin `ide`/`reside` y la línea queda
  en la cola. En la copia, quitar la guarda `startswith` rompe **13 tests** y quitar la rama R10, **6**.
  El alias sin DNI solo existe si se confirmó en Conciliar y `elegir_sin_dni` lo revalida. Los 3 tests
  F-023 de la opción A siguen exigiendo `ide`/`reside` None y `review`.
- **Lista cerrada:** `orm_models.py` idénticos; guardianes F-010/F-023/F-024/F-036 verdes y sin tocar;
  `CLAUDE.md` anota R10 sin gemela en sv5; `de_alta`, `esta_congelado` y los SQL de sv4 intactos.
- **Esquema (F-017):** ni `.sql` ni `UPDATE`; `ADD COLUMN IF NOT EXISTS` sale del ORM; `DROP NOT NULL`
  va en `DDL_EXTRA_POSTGRES`, en la transacción de `initialize()` de sv3 y sv4: idempotente y sin
  tocar filas. F-010 exenta solo esa sentencia y un test impide que la exención crezca.
- **sv5:** su diff es solo `tests/test_f040_sv5_sin_dni.py`. **azure-apps:** commit local `ec971c2`.

## Cobertura requisito → test (`services/<svc>/tests/`)

| R | Test |
|---|---|
| R1, R10, R11 | sv3 `test_f040_seleccion.py` |
| R2–R5 | sv3 `test_f040_casado.py`, más los F-023/F-036 adaptados |
| R6, R20 | `test_f040_alias_repo.py` (sv3 y sv4) |
| R7, R8, R12 | sv3 `test_f040_casado.py` |
| R9 | sv3 `test_f040_elegir_sin_dni.py` (19 casos) |
| R13 | sv3 `test_f040_caracterizacion.py` |
| R14, R16 | sv4 `test_f040_catalogo.py` |
| R15 | sv4 `test_f040_vistas.py` (node y Jinja2) |
| R17–R19 | sv4 `test_f040_alias.py` |
| R21 | `test_f010_r6_ddl_complementario*` (sv3 y sv4) |
| R22 | sv5 `test_f040_sv5_sin_dni.py` |
| R27, R30 | Guardianes de la raíz y lectura de la documentación |
| R28, R29 | sv3 `test_f040_medicion.py` |
| R31 | Sin acción (DA4); lo cubren R14 y R15 |

R23–R26 se retiraron por DA3.

## Cambios requeridos

1. **`progress/current.md`, líneas 13–16.** Cambiar «según `tasks.md`» por los comandos exactos:
   - **T15:** `infra/redeploy_partes.ps1 -Solo sv3`, y después `infra/redeploy_partes.ps1 -Solo sv4`.
   - **M2:** `SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name =
     'empleado_alias' AND column_name IN ('empleado_ide','recurso_ide');`. Debe dar dos filas, las
     dos con `YES`.
   - **M3:** en Conciliar de Porsan, `MO/0032` y `MO/0033` salen «sin DNI». Al confirmar uno, el alias
     queda con `recurso_ide` y la línea en `recurso_manual`. El preflight de la obra 0692 la da por
     verificada.
2. **`progress/current.md`, C2.** Integrar `dev` (`1114e33`) y dejar el párrafo del bloqueo de T4 en
   una línea: «bloqueada en T4, desbloqueada con la opción A; ver `impl_F-040.md`».

## Automejora (propuesta, no aplicada)

- **`test_A_antes_la_campania_paralela_*`:** con la máquina cargada da `muertos == 3` en vez de 5.
  Propuesta para `arnes-base`: comprobar `muertos + timeouts == 5` o subir `TIMEOUT_S`.
- **`CHECKPOINTS.md`, C4:** que cada MANUAL lleve su comando escrito en `current.md`, no una
  referencia a `tasks.md`.
