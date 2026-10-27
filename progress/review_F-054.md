Revisión completa (pasada 1) · rama `feature/F-054-sin-obra-o-fecha-a-revision`, `git diff dev...HEAD` (merge-base `38f273a`), HEAD `4d00c01`
<!-- progress/review_F-054.md -->
# F-054 · Review (reviewer, 2026-10-23)

**Veredicto: APPROVED**

**Nivel de rigor: `estandar`** (declarado en `harness/features.json`). Exige C1–C5, C3 bis,
fase RED en los requisitos centrales, cobertura de lo cambiado ≥ 80 % y campaña de mutación
con los supervivientes analizados (sin exigencia de cero). RM5 es N/A por nivel.

## Verificación ejecutada por el reviewer (resultado real)

- `bash harness/init.sh` (worktree, HEAD `4d00c01`): exit 0, «ENTORNO LISTO». Raíz `498
  passed, 3 skipped`; `PUERTA COBERTURA [OK] 100.0% de 13 líneas cambiadas (13/13)`;
  `PUERTA TAMAÑO [OK]` (requirements 108/150, design 235/250, impl 201/220). sv1–sv5 por
  caché, así que la suite de sv3 se reejecutó entera sin caché (`-p no:cacheprovider`):
  **`2305 passed in 22.02s`**. Avisos previos, ajenos a F-054: F-032 `blocked`, ruff 772
  (en los ficheros tocados solo queda `UP045` en `__init__`, l. 117, sin tocar) e infra sin tests.
- Límite de servicio: `git diff dev...HEAD --stat` sobre sv1, sv2, sv4, sv5,
  `services/partes-persistencia/infrastructure` e `infra/` ⇒ **vacío**. Solo sv3
  (`application/` y `tests/`), sin esquema, sin colas, sin gemelos de la lista cerrada.
- `_compute_review_required` y `motivos_cabecera`: sus únicos llamantes de producción están en
  `persist_parte_pipeline.py` (l. 188, 204, 408); ningún conciliador ni sv4 los usa (R10–R11).
  `OBRA_A_REVISAR` solo sobrevive en el test de R6 y en la spec.
- `git status` limpio antes y después (la reproducción de mutantes fue sobre una copia en el
  scratchpad).

## Mutación (verificación independiente)

- **Recálculo puro**: `alcance_de_feature('F-054')` ⇒ origen `rama`, `38f273a..feature/…`,
  1 fichero (`persist_parte_pipeline.py`), **31 líneas**; `generar_mutantes` ⇒ **5**
  (l. 79 `is None`→`is not None`; l. 81 `is None`→`is not None`, `or`→`and`, `<= 0`→`< 0`,
  `<= 0`→`<= 1`). Coincide con el informe. Control sin exclusión: 67 mutantes en el fichero
  entero (el generador funciona; el 5 sale del alcance, no de un fallo).
- **Campaña no reejecutada: 106,4 s según el informe** (> 60 s): recálculo puro, RM1–RM6 y
  RM4 sobre los cinco mutantes.
- **RM4**: en una copia de sv3 en el scratchpad apliqué los 5 mutantes con
  `aplicar_mutante` y corrí `test_f054_revision_cabecera.py` + `test_f023_pipeline_match.py`:
  36, 29, 11, 1 y 1 fallos respectivamente; el original, `81 passed`. Los cinco muertos son
  reales (los de frontera mueren por `fecha=0` y `fecha=1`).
- **RM1**: SHA medido `9764fad…`; el delta `9764fad..HEAD` solo toca `progress/` y `tasks.md`,
  nada del alcance. Válido.
- **RM2**: 5 × 21,3 = 106,5 ≈ 106,4 s. Coste real por mutante `21,3 × 3 workers ≈ 64 s`
  frente a una línea base de 33,5–33,7 s: mismo orden de magnitud (contención de 3 suites en
  paralelo). Coherente. Coste por mutante (`106,4 × 3 ÷ 5 ≈ 64 s`) ≫ 1 s.
- **RM3**: ninguno de los cinco es equivalente (cada uno cambia el booleano o lanza
  `TypeError` con `None <= 0`); que salgan muertos es correcto.
- **RM6**: no se quitó ninguna guarda; `OBRA_A_REVISAR` se borra porque `obra.ide is None` la
  contiene (DA1), no para matar un mutante.
- Sin cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; la línea base corrió
  (tres filas, una por worker).

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] solo F-054 `in_progress` · [x] rama `feature/F-054-…` · [x] `current.md`:
  sección F-054 arriba; el resto es el registro acumulado que ya había en `dev` (mismo
  criterio que las reviews de F-046, F-048 y F-051) · [x] las `done` tienen su resumen en
  `history.md` (F-054 no toca ninguna).
- **C3** [x] hexagonal: la regla vive en `application/` de sv3 junto a la que ya había, sin
  imports de infraestructura · [x] primera línea con ruta en los ficheros tocados y en el
  nuevo (`# tests/test_f054_revision_cabecera.py`) · [x] sin `print()`, TODOs, secretos ni
  dependencias nuevas; el WARNING solo lleva `document_id`, motivos, método y número de obra
  leído · [x] trampas: empleado ≠ recurso (no se toca el casado), incidencias (no se tocan),
  ORM duplicado (intacto en sv3 y sv4).
- **C3 bis** N/A: la feature no añade ni modifica nada en `docs/referencia/` (comprobado en
  el `--stat` del diff).
- **C4** [x] R1–R13 trazados y en verde (tabla abajo) · [x] sin red ni BBDD real (dobles en
  memoria y SQLite en memoria de `test_f036_pipeline`; nombres y DNIs ficticios) · [x] M2 y
  M3 pendientes en `current.md` e impl; el comando exacto de M2 está literal en
  `impl_F-054.md` y en `design.md` §8 (enlazado desde `current.md`, mismo criterio que F-051).
  M2 **no** ejecutada ni autorizada: solo sube la bandera (`is_active AND NOT approved AND
  review_required IS NOT TRUE AND (obra_ide IS NULL OR fecha_int IS NULL OR fecha_int <= 0)`;
  `approved` es NOT NULL y `IS NOT TRUE` cubre el `review_required` nulo).
- **C4 bis**
  - [x] `rigor` declarado (`estandar`).
  - [x] Fase RED con salida real en `impl_F-054.md`: RED 1 (ImportError y el caso
    `none-False-True` de `test_f023` en `assert False is True`) y RED 2 (15 fallos de
    comportamiento con la función presente y sin usar, con el detalle de R9 en dobles y en
    SQLite).
  - [x] Cobertura `[OK]` 100 % (13/13).
  - [x] Informe de mutación generado por la herramienta y totales verificados (arriba).
  - [x] Muertos: > 60 s, recálculo puro + RM4 de los cinco, dicho arriba.
  - [x] Coste por mutante ≈ 64 s.
  - [x] Sin cabecera de campaña no válida ni sin-veredicto.
  - [x] RM1 · [x] RM2 · N/A RM5 (nivel `estandar`: no hay supervivientes ni equivalentes)
    · [x] RM6.
  - N/A campaña manual: la automática generó 5 mutantes, no 0.
  - N/A análisis de supervivientes: 0 supervivientes, nada en `PENDIENTE`.
  - [x] «Evidencias» con tests (2.305), cobertura (100 %), mutantes (5/0) y tiempo de la
    suite; los workers (`--workers 3`) constan en la sección «Mutación» del informe y en la
    fila «Workers» del informe de mutación.
  - [x] Ningún N/A sin justificar.
- **C4 ter** N/A: el repo no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1–T7 y T10 `[x]`; commit `F-054 Tn:` para T1–T6 y T10 (T7 es la M1 del líder,
  con su resultado en `design.md` §8, commit de la spec aprobada `9e8e80d`); T8 (M2) y T9
  (M3) en `[ ]` por ser MANUAL del humano/líder, pendientes y documentadas · [x] árbol limpio,
  sin temporales · [x] `features.json` en `in_progress`, coherente con la M2 pendiente.

## Cobertura requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f054_r1_sin_obra_va_a_revision` (5 métodos, uno inventado), `…_r1_por_el_casado_real`; `test_f023_review_required_por_la_obra[none-False-True]` |
| R2 | `test_f054_r2_sin_fecha_va_a_revision` (`None`, 0, -1), `…_r2_con_fecha_positiva_no_hay_motivo` (frontera 1), `…_r2_sin_fecha_por_el_casado_real` |
| R3 | `test_f054_r3_motivos_cabecera` (4 combinaciones, orden), `…_r3_constantes_de_los_motivos` |
| R4 | `test_f054_r4_casado_completo_no_va_a_revision` (6 métodos), `…_r4_casado_por_recurso_no_cambia`; `test_f030_r13_*` |
| R5 | `test_f054_r5_las_demas_causas_no_cambian` (5 causas); `test_f051_r15_*`/`r17_*` |
| R6 | `test_f054_r6_obra_a_revisar_desaparece` |
| R7 | `test_f054_r7_warning_con_motivos_sin_nombres`, `…_r7_el_warning_lleva_la_obra_leida`, `…_r7_sin_motivos_no_hay_warning` |
| R8 | Diff vacío en sv4/sv5/infraestructura (T4, comprobado por el reviewer) |
| R9 | `test_f054_r9_ingesta_del_hallazgo` (dobles), `…_r9_columnas_guardadas` (SQLite) |
| R10 | Suites de F-023 (R16, fecha de referencia), dedup y conciliadores sin tocar y en verde |
| R11 | Sin cambios en conciliadores ni sv4 (grep de llamantes y diff vacío) |
| R12 | M1 hecha (resultado en `design.md` §8); M2 MANUAL pendiente, comando revisado arriba |
| R13 | Semántica 18 en `docs/ARCHITECTURE.md` y paso 5 del docstring, revisados en el diff |

## Cambios requeridos: ninguno.

## Observaciones (no bloquean)

1. La semántica 18 dice «se corrige una sola vez a mano (M2 de F-054…)». Si el humano
   descarta la M2, esa frase hay que quitarla (el implementer ya lo avisa).
2. M1 daba 3 documentos el 2026-10-21; con las 4 páginas del 23/10 podrían ser 7.
   Repetir M1 (solo lectura) justo antes de la M2 para fijar el `n` esperado.

## Automejora propuesta (no aplicada)

1. **`CHECKPOINTS.md` C4**: aceptar por escrito que `current.md` enlace al comando exacto
   (en `design.md` o en el informe del implementer) en vez de copiarlo; hoy cada reviewer lo
   justifica por su cuenta (F-051, F-054) y una copia más es otra que diverge.
2. **Plantilla de «Evidencias»** del implementer: añadir la fila «Workers de la campaña»,
   que C4 bis exige y hoy hay que buscar en otra sección.
