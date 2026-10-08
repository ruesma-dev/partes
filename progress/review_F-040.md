<!-- progress/review_F-040.md -->
Revisión incremental desde 100a4a4 (pasada 2) · delta `100a4a4..7ccdb5f`: `07d5ad1` + merge de dev `1114e33`

# F-040 · Review (pasada 2)

**Veredicto: APPROVED.** Nivel de rigor `critico` (declarado): fase RED, cobertura, mutación completa
con 0 supervivientes y MANUAL con comando exacto en `current.md`; todo cumplido.

**Pasada 2 (delta):** solo cambia `progress/current.md` (`git diff 100a4a4..HEAD --stat`); el merge de
dev trae únicamente F-039 `done` en `current.md`. Ningún fichero del alcance de mutación cambia desde
`0c851f4` (RM1): la campaña y la cobertura siguen valiendo. `bash harness/init.sh` en verde
(`ENTORNO LISTO`, raíz 461 passed / 3 skipped, COBERTURA [OK] 100 % 66/66, TAMAÑO [OK]).
- Cambio 1 resuelto: T14/M1, T15 (`.\redeploy_partes.ps1 -Solo sv3` y luego `-Solo sv4`, desde `infra/`;
  el script acepta `-Solo`), M2 (SQL y esperado: dos `YES`) y M3 (pasos) con su comando exacto. C4 → [x].
- Cambio 2 resuelto: F-039 aparece `done` (coherente con `features.json`) y el bloqueo de T4 queda en una
  línea. C2 → [x].
Lo demás, lo de la pasada 1 (abajo, ya dado por bueno): no se relee.

Detalle de la pasada 1 (`dev...d099001`, commit `100a4a4`, entonces CHANGES_REQUESTED), vigente:

## Qué ejecuté en la pasada 1 (resultados reales)

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
  - [x] `current.md` coherente (en la pasada 1 era `[ ]`: F-039 seguía `in_progress` y quedaba el
    bloqueo de T4; resuelto en la pasada 2).
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
  - [x] MANUAL T14/M1, T15, M2 y M3 con su comando exacto en `current.md` (en la pasada 1 era `[ ]`:
    T15, M2 y M3 solo remitían a `tasks.md`; resuelto en la pasada 2).
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
  - [x] `features.json`: F-040 pasa a `done` con este veredicto.

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

Ninguno (los dos de la pasada 1, resueltos en `07d5ad1` y `7ccdb5f`).

## Automejora (propuesta, no aplicada)

- **`test_A_antes_la_campania_paralela_*`:** con la máquina cargada da `muertos == 3` en vez de 5.
  Propuesta para `arnes-base`: comprobar `muertos + timeouts == 5` o subir `TIMEOUT_S`.
- **`CHECKPOINTS.md`, C4:** que cada MANUAL lleve su comando escrito en `current.md`, no una
  referencia a `tasks.md`.
