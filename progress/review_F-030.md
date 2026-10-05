<!-- progress/review_F-030.md -->
Revisión de delta (pasada 2) desde `a4a308c` · HEAD `88140da`

# F-030 · Review

- **Veredicto: APPROVED.**
- **Nivel de rigor:** `critico` (declarado en `features.json`). Exige fase
  RED, cobertura ≥ 80 %, mutación con 0 supervivientes y verificaciones MANUAL
  con comando.
- Pasada 1 (`901750f`, CHANGES_REQUESTED): su texto completo está en
  `git show 901750f:progress/review_F-030.md`. Aquí va solo el resumen.

## Pasada 2 · el delta (`git diff a4a308c..HEAD`)

- **Ficheros:** `tests/test_f030_casado_recurso.py` (+21 líneas, un test),
  `tasks.md` (T16), `impl_F-030.md` §7 y esta review. **Ningún fichero de
  producción**: el alcance de la mutación (8 ficheros, 199 líneas, 18
  mutantes) y la campaña de `551a1d8` siguen valiendo (RM1).
- **El test** `test_f030_proveedor_los_recursos_con_ficha_no_son_fichas_de_recurso`
  pasa por el `SigridMatcherProvider` real (`_proveedor(lookup).get()`) con
  dos recursos `MO/`:
  - el `970`: `cif` = DNI de la ficha 10 y `conide` = 10;
  - el `971`: `cif` = DNI de la ficha 20 y `conide` None.

  Comprueba dos cosas. **(a)** `matchers.recursos.fichas_candidatas(None, HOY)`
  es `[950, 951]`. **(b)** «Pedro Gomez», leído sin DNI, casa `nombre` con la
  ficha 10 (`reside` 900). Cubre los dos casos pedidos.
- **Reproducido en una copia `git archive HEAD` en el scratchpad** (fuera del
  repo), con la rotura `fichas_de_recurso([], recursos)` en
  `sigrid_matcher_provider.py:133`:
  - suite sv3 entera: `1 failed, 754 passed`, con
    `assert [950, 951, 970, 971] == [950, 951]`;
  - con (a) anulada en la copia, (b) cae sola:
    `assert (None, 'nombre_ambiguo', None) == (10, 'nombre', 900)`.

  Las dos aserciones cazan la rotura cada una por su lado. Sin rotura,
  `1 passed`. La traza RED del implementer (§7) coincide con la mía.
- **`bash harness/init.sh` tal cual: ENTORNO LISTO.** Raíz `445 passed, 1
  skipped`. sv3 `755 passed`, sin caché: su árbol cambió. sv1, sv2, sv4 y sv5
  en verde con caché, porque su código no ha cambiado desde la pasada 1, en la
  que se ejecutaron sin caché (sv4 `1657`, sv5 `362`). Cobertura 100 % (59/59).
  Tamaño OK (impl 220/220). `git status` limpio salvo esta review.
- El cambio 1 de la pasada 1 queda **resuelto**. El checkbox de C4 bis «tests
  de verdad» pasa a `[x]`.

## Resumen de la pasada 1 (completa, `dev...a4a308c`)

- **(1) Decide igual.** Diferencial dev vs HEAD en copias del scratchpad:
  20.000 partes sintéticos, 59.870 líneas, pipeline real (`_match` +
  `review_required`).
  - dev con el DNI ya canónico frente a HEAD sin fichas de recurso:
    **0 diferencias**.
  - Con fichas de recurso, cada cambio va a `recurso_*` o a `nombre_ambiguo`
    por empate con una de ellas.
  - Un oráculo independiente coincide en las 59.870 líneas (2.044
    `recurso_dni`, 1.315 `recurso_nombre`, 637 `nombre_ambiguo`).
- **(2) Lista cerrada intacta:** `seleccion_sigrid.py`,
  `coherencia_recurso.py`, los dos `text_match.py` (idénticos), los dos
  `orm_models.py`, `jornada_resolver.py`, `recurso_conciliador.py` y
  `empleado_matcher.py`. Se reutilizan `elegir_ficha`, `fichas_candidatas` y
  `match_nombre`: no hay lógica copiada. `METODOS_RECURSO` está en sv3 y en
  sv4, pero es el contrato de valores de la columna (design §6.4) y lo fijan
  tests en los dos servicios.
- **(3)** Los empates recurso↔empleado y recurso↔recurso dan
  `nombre_ambiguo`. «APELLIDOS, NOMBRE» casa en cualquier orden. **(4)** El
  DNI casa con y sin cero, con guion y en minúscula.
- **(5)** sv5 no tiene cambios de código. R17 y R21 (`caaide` 0) están en
  verde.
- **(6)** En sv4 solo cambia `parte_repository.py`. La cola de conciliación y
  su «Confirmar» (`backfill_empleado`) excluyen al casado por recurso, con el
  NULL bien tratado: no pueden soltarle el recurso. Reasignar a mano sí lo
  suelta (R20, como hoy).
- **(7)** Datos sintéticos. Sin secretos ni `print`; el barrido de patrones
  solo encuentra `clave-de-test`. Docs y `azure-apps` (`1c7238c`) coherentes.
- **Roturas deliberadas:** 17 en la pasada 1. Las cazaron todas salvo la del
  cableado, que con este delta ya también se caza.

## Mutación (C4 bis, RM1–RM6)

- **Recalculado:** 8 ficheros, 199 líneas, 18 mutantes, igual que el
  informe. Sin «campaña no válida»; 0 sin veredicto.
- **RM1:** medido en `551a1d8`. Desde entonces solo cambian tests y
  `progress/`, así que el alcance de producción es el mismo.
- **RM2:** 957,2 s con 6 workers dan 319 s por mutante, que no baja de la
  línea base de sv4 (312 s). Coherente.
- **Campaña no reejecutada entera** (pasa de 60 s). En su lugar, **RM4 en el
  scratchpad**: los 18 mutantes, uno a uno, con la suite completa de su
  servicio y `-x`. **18/18 muertos** por aserciones reales.
- **RM3:** ningún mutante es equivalente. **RM5:** N/A, no hay supervivientes
  ni equivalentes. **RM6:** no se quitó ninguna guarda; `fetch_empleados`
  descarta los `ide` None (`sigrid_api_client.py:222-224`).

## Checkpoints

- **C1** [x] init.sh en verde · [x] ficheros del arnés.
- **C2** [x] una sola feature `in_progress` · [x] rama de la feature ·
  [x] `current.md` con F-030 arriba · [x] las `done` están en history.
- **C3** [x] arquitectura hexagonal (`fichas_de_recurso` pura en application)
  · [x] cabeceras con ruta · [x] sin prints, TODOs, secretos ni dependencias
  nuevas · [x] trampas: la línea se guarda en el recurso (R14); incidencias y
  `orm_models.py` intactos.
- **C3 bis** N/A: no entra ningún documento de fuera. `partes-proyecto.md` es
  documentación propia.
- **C4** [x] R1–R22 trazados y en verde · [x] sin red ni BBDD · [x] M1–M4 en
  `current.md` con comandos, pendientes del humano.
- **C4 bis** [x] rigor declarado · [x] RED pegada (R1–R5, R9–R13, R18, R19 y
  T16) · [x] cobertura 100 % · [x] mutación recalculada · [x] muertos
  comprobados (RM4) · [x] tiempos · [x] informe válido · [x] RM1 · [x] RM2
  · [x] RM5 (N/A justificado: 0 supervivientes) · [x] RM6.
  N/A la campaña manual, porque hubo campaña automática. [x] 0 supervivientes
  · [x] «Evidencias» con workers · [x] tests de verdad (resuelto en la
  pasada 2).

## Cobertura requisito → test

| Req. | Tests (`services/<svc>/tests/…`) |
|---|---|
| R1–R3 | `test_f030_dni_canonico.py`: `r1_*`, `r2_*`, `r3_*` |
| R4–R13 | `test_f030_casado_recurso.py`: `r4_*`, `proveedor_*` (3), `r5_*`…`r13_*` |
| R14–R15 | `test_f030_conciliador_sin_ficha.py`: `r14_*` (5), `r15_*` (2) |
| R16 | `tests/test_f023_de_alta_gemelos.py` sin tocar + diff vacío |
| R17, R21 | `partes-transfer/…/test_f030_coherencia_sin_ficha.py`: `r17_*` (3), `r21_*` (2) |
| R18–R20 | `partes-front/…/test_f030_portal_recurso.py`: `r18_*` (6), `r19_*` (4), `r20_*` (2) |
| R22 | lectura: ARCHITECTURE §2 y §12, `partes-proyecto.md` §4.6 y §7, `azure-apps/partes.md` |

## Cambios requeridos: ninguno

**Pendiente del humano, no del reviewer:** desplegar sv3 y después sv4, y las
verificaciones M1–M4 de `progress/current.md`.

**Observaciones (no bloquean):**
- El DNI canónico alimenta también los discriminantes de obra (F-023 R11):
  en el diferencial cambian 74 de 20.000 partes. Es lo que prevén design §5 y
  DA7.
- `azure-apps/partes.md` dice «umbral 0.55», pero eso es anterior a F-030.

**Automejora (propuesta, no aplicada):** en `reviewer.md`, para `critico`,
**roturas de cableado** (`[]`/`None` por el argumento real al montar objetos):
el mutador no muta argumentos y fue la única rotura viva con 18/18 muertos.
