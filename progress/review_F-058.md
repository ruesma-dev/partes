<!-- progress/review_F-058.md -->
Revisión completa (pasada 1) · diff de la feature `9b1a7e3..791a427` (HEAD `791a427`)

# F-058 · Review — relectura de la cabecera con Gemini y prompt de cabecera (sv2)

**Veredicto: APPROVED.** Sin cambios requeridos. **Condición de cierre** (no de este veredicto):
la feature no se mezcla ni pasa a `done` sin la puerta MB (T3, DA9) en verde; si MB obliga a
tocar el prompt, ese delta pide pasada 2 incremental desde `791a427`.

**Nivel de rigor: `estandar`** (declarado en `harness/features.json`): C1–C5, C3 bis, fase RED,
cobertura ≥ 80 % de las líneas cambiadas y mutación muestreada (20, semilla `20260820`) con los
supervivientes analizados. Sin exigencia de cero supervivientes; RM5 N/A por nivel.

## Lo verificado (resultado real)

- **`bash harness/init.sh`** ⇒ **ENTORNO LISTO** (exit 0): raíz 522 passed / 3 skipped; sv2
  331 passed; sv1, sv3–sv5 en verde; `PUERTA COBERTURA [OK] 100.0 % (214/214)`; `PUERTA TAMAÑO`
  en verde (requirements 150/150, design 250/250, impl 162/220). Árbol limpio.
- **Límite de servicio (R27)**: `git diff --name-only 9b1a7e3..HEAD -- services` solo da
  `services/partes-api/`; sin cambios en `domain/models` (`parte_models.py`),
  `infrastructure/llm/*`, `auxhor_catalog_provider.py`, ORM ni sv1/sv3–sv5. `prompts.yaml`: solo
  el punto 1 de `task` (16 líneas ±). La clave de obra de sv2 no copia `obra_matcher` de sv3: es
  la misma normalización de `normalize_code` más quitar todos los ceros (más gruesa a propósito,
  `design.md` §1); no elige obra ni empresa. La lista cerrada de duplicados no crece.
- **Consulta de obra solo lectura y F-038**: `existe_obra` va por `POST /api/sql/read` con un
  `SELECT TOP 1` y la clave como único `?` en `parameters` (test: clave fuera del texto SQL);
  `max_rows` = el del cliente (`SIGRID_API_MAX_ROWS`), `truncated: true` ⇒ `RuntimeError` en el
  `_post_sql_read` común; guardián `tests/test_f038_lectores_sigrid.py` en verde en la raíz.
- **Ningún fallo tumba la extracción**: `ComprobadorObra.consultar` captura toda excepción
  (timeout de httpx incluido) ⇒ «no se sabe» + WARNING con el tipo; `_releer_cabecera` captura
  toda excepción de la relectura (y el `KeyError` de `model_name`) ⇒ `data` primario y
  `resultado=error`. Un fallo de la primaria sigue propagándose (test R14). Las dos capturas
  amplias llevan `noqa` justificado.
- **Sin datos personales en logs**: los INFO/WARNING de `[obra-sigrid]` y `[sv2][relectura]`
  llevan `document_id`, fichero, proveedor, modelo, motivo, resultado, ms y tipo de error; el
  test R20 barre nombre, DNI, obra, fecha, dirección y mensaje de excepción. Fixtures inventadas
  (`12345678Z` es el DNI de ejemplo canónico, «Fulano», obra `9999`). Sin secretos en el diff,
  en `current.md` (claves leídas del KV en el proceso) ni en azure-apps.
- **azure-apps `7470cf2`** (sin push): solo `partes.md` (diagrama, §3.2, fila de sigrid-api y
  fila sv2 de §5.6), sin secretos. `sigrid_api.md` no se toca (es de sigrid-api).
- **Docs**: `ARCHITECTURE.md` punto 20 y «Acceso a datos»; comentario de sv2 en
  `infra/create_capps_partes.ps1` (solo comentarios); docstrings de T12 al día.
- **`dev` avanzó** a `463869d` sin tocar `services/partes-api`, `docs/ARCHITECTURE.md` ni
  `infra/create_capps_partes.ps1`; `git merge-tree` solo da conflicto en `BACKLOG.md` (generado).

## Desviaciones del implementer (las 7 de `impl_F-058.md`)

Aceptadas todas. (1) `max_rows` del cliente en vez de 2 y (2) sin `exigir_completo`: F-038
llegó después de la spec, su guardián prohíbe el literal y `truncated` ya es error en toda
lectura; con `TOP 1` el resultado es idéntico. (3) F-059: la relectura aplica la regla de imagen
con SU proveedor (tests de los dos casos); coherente con la medición 6/6 sobre PDF. (4)
`model_name` ausente = `error`, no tumba (R14). (5) clave vacía no consulta ni apunta ms: es lo
que dice `design.md` §4.2. (6) Punto 20 y no 18 (el 18 y el 19 ya existían). (7) R15 hecho en T9
como decía `tasks.md`.

## Mutación (C4 bis)

- **Recálculo puro** (`alcance_de_feature` + `generar_mutantes`, con el mismo sorteo
  `random.Random(20260820)`): **9 ficheros, 560 líneas, 63 mutantes** = el informe; la muestra
  recalculada contiene el superviviente `settings.py:100` `gt=0`→`gt=1` con el mismo texto.
- **Campaña no reejecutada: 242,9 s según el informe (> 60 s)**; vale el recálculo + RM1–RM6 +
  RM4 de abajo.
- **RM1**: midió `da0317c`; `da0317c..791a427` solo toca `progress/`, `tasks.md` y un test; el
  alcance a HEAD es el mismo (560 líneas, mismos 9 ficheros).
- **RM2**: workers 1 ⇒ coste por mutante 12,1 s, base 18,8 s; 20 × 12,1 ≈ 242,9 s. Coherente
  (19 de 20 muertos con `-x`). Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto» 0.
- **RM3**: repasados los 19 muertos de la muestra; ninguno es equivalente (p. ej.
  `or ""`→`and ""` en `_clave_de` deja toda clave vacía; `transport or`→`and` usa red real).
- **RM4** (copia de `services/partes-api` en el scratchpad, sin bytecode y con la caché limpia;
  base 330 passed con 1 deselect de F-059 que lee `infra/`, ajeno): `gt=0`→`gt=1` ⇒ **2 failed**
  (el test nuevo, como dice el informe). Fuera de la muestra: `len(rows) >= 2` ⇒ 1 failed;
  `max(2, ...)` ⇒ 1 failed; `data.get("empleados") and []` ⇒ 1 failed;
  `* 1000`→`* 1001` en `obra_sigrid.py:84` ⇒ **sobrevive** (observación 1). Copia sin cambios.
- **RM5** N/A (nivel `estandar`). **RM6**: no se quitó ninguna guarda; se añadió un test.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] solo F-058 `in_progress` · [x] rama `feature/F-058-relectura-cabecera-gemini` ·
  [x] `current.md`: F-058 es la activa, con estado y MANUAL (las demás secciones son el registro
  de features desplegadas, criterio de reviews anteriores) · [x] F-058 no está `done`.
- **C3** [x] hexagonal: puerto `ExistenciaObraPort` en `domain/ports` sin imports; reglas puras y
  `ComprobadorObra` en `application`; HTTP solo en `infrastructure/sigrid`; cableado en `app.py`
  · [x] primera línea con la ruta en los 7 `.py` nuevos y en los tocados · [x] sin `print`, TODO
  ni secretos; sin dependencias nuevas · [x] trampas del dominio (recurso, incidencias, ORM): no
  aplican (sv2 no escribe ni toca esquema).
- **C3 bis** N/A: la feature no añade ni toca nada en `docs/referencia/`.
- **C4** [x] requisitos con test trazable, todo en verde (tabla abajo; R11, R27 y R28 por
  test indirecto o verificación del reviewer, criterio de F-059) · [x] sin red ni BBDD
  (`httpx.MockTransport`, dobles de IA, reloj falso) · [x] MANUAL en `current.md` con comando
  exacto: `az containerapp show` (M0), script de M1, SELECT en `READ ONLY` (M2), las dos KQL
  (M4), portal sin escrituras de agentes (M3), MB con sus flags.
- **C4 bis** [x] `rigor` declarado · [x] fase RED con trazas reales (T1: 11 failed; T4/T6
  `ModuleNotFoundError` y 14 failed; T8: 36 failed; T10: 23 failed) · [x] cobertura `[OK]`
  100 % · [x] informe de la herramienta, totales recalculados · [x] muertos: campaña > 60 s,
  dicho arriba, más RM4 · [x] coste por mutante 12,1 s > 1 s · [x] sin cabecera de no válida
  · [x] RM1 · [x] RM2 · N/A RM5 (nivel `estandar`) · [x] RM6 · N/A campaña manual (la
  automática generó 63) · [x] el superviviente con análisis completo (hueco real, test nuevo)
  · [x] «Evidencias» con los cuatro números y «workers: 1» · [x] ningún N/A sin justificar.
- **C4 ter** N/A: el repositorio no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1, T2, T4–T16 y T22 `[x]` con commit `F-058 Tn:` (T7 con dos) · T3 y T17–T21 en
  `[ ]` por ser MANUAL del líder o del humano (MB antes de mezclar; M0 antes de desplegar; M1–M4
  tras desplegar), criterio de F-054/F-059 · [x] árbol limpio · [x] `features.json` coherente.

## Cobertura requisito → test (`services/partes-api/tests/test_f058_*.py`)

| Req | Test(s) |
|---|---|
| R1 | `relectura_cabecera::test_f058_r1_cabecera_vacia_relee_una_vez_con_el_mismo_prompt` |
| R2–R5 | `…_r2_*` (7), `…_r3_*` (4), `…_r4_*` (3), `…_r5_*` (3) |
| R6 | `…_r6_sin_relectura_activa_ni_relee_ni_consulta` |
| R7–R10 | `…_r7_*` y `obra_sigrid::…_r7_*` (10), `…_r8_*` (4), `…_r9_*` (13: falla, `truncated`, 500, tope, sin cablear, 2.ª consulta), `obra_sigrid::…_r10_*` (3) |
| R11 | indirecto: `…_r7_obra_inexistente_relee_y_aplica_si_la_releida_existe` (la obra es la releída, nada de Sigrid), `…_r16_meta_relectura_con_sus_claves`, `…_r19_*`; el puerto devuelve `bool` |
| R12–R14 | `…_r12_*` (5), `…_r13_*` (2), `…_r14_*` (4) |
| R15–R20 | `…_r15_*` (2, también el worker), `…_r16_*` (4), `…_r17_*`, `…_r18_*`, `…_r19_*`, `…_r20_*` (3) |
| R21–R23 | `prompt::…_r21_*` (6), `…_r22_*`, `…_r23_*`; F-023 y F-051 sin tocar, en verde |
| R24–R26 | `settings_wiring::…_r24_*` (13, con 0,5 y 1), `…_r25_*` (5), `…_r26_*` (2) |
| R27–R28 | reviewer: `git diff` (arriba) y lectura de ARCHITECTURE, `create_capps_partes.ps1` y azure-apps `7470cf2` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

1. `obra_sigrid.py:84` `* 1000`→`* 1001` sobrevive (fuera de la muestra): con pasos de 10 ms y
   42,1 ms el redondeo esconde el 0,1 %. Un caso con 2,0 s (2000 frente a 2002 ms) lo mataría.
2. `requirements.md` R9 aún dice «propuesta pendiente, DA12» y R28 «punto 18»: texto viejo
   (DA12 aprobada A; el punto es el 20). Cosmético.
3. `clave_obra` quita todo blanco (`split`) y el SQL solo `' '`: un tabulador en `con.cod` no
   casaría. Irrelevante en la práctica.
4. Antes de mezclar: **MB (T3)**, puerta de DA9. Antes de desplegar: M0 (T17). M1 dirá si
   sigrid-api acepta `CROSS APPLY` y `COLLATE` (si no, `error` y la extracción sigue).
5. Al mezclar `dev`, el único conflicto es `BACKLOG.md`: regenerarlo con `harness/backlog.py`.
6. Avisar al dueño de `azure-apps/sigrid_api.md` de la lectura nueva por página (sin índice).

**Automejora (propuesta, no aplicada)**: en `reviewer.md` RM4, avisar de que un mutante del
mismo tamaño aplicado y revertido en el mismo segundo deja bytecode viejo: correr la copia con
`PYTHONDONTWRITEBYTECODE=1` y `__pycache__` borrado (me pasó en esta revisión: un revertido
seguía «mutado» hasta purgar la caché).
