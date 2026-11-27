<!-- progress/review_F-084.md -->
Revisión de evidencias desde a738cb3 (evidencias, pasada 2) · HEAD 8b80fec · `git diff a738cb3..HEAD`

# F-084 · Review

**Veredicto: APPROVED** (SHA aprobado **34a5dbb**; delta 34a5dbb..HEAD vacío). C1: `bash harness/init.sh` exit 0
a la 3.ª: la 1.ª la paró el sistema por falta de memoria; la 2.ª, roja solo en el inestable `test_f059_r9`
(`nieto.pid`). En la 3.ª, raíz 2549 passed/50 skip; sv4 por caché (verde de 12:19, test ya renombrado); cobertura 100 %.

**Pasada 2 (delta a738cb3..8b80fec):** 7384a14, e1a6626 y 8b80fec. Toca solo `progress/` (impl, mutacion .md,
`equivalentes_F-084.py`) y el renombrado de un test de sv4; **ni producción ni `mutacion_F-084.json`**.
- Cambio 1 [x]: `grep -c PENDIENTE progress/mutacion_F-084.md` = 0; los 7 análisis y las 2 declaraciones,
  correctos y coherentes con mi criterio de abajo.
- Cambio 2 [x] **RM5**: `cd services/partes-front && ..\.venv\…\python ../../progress/equivalentes_F-084.py` (venv
  del repo principal): **exit 0**, «7/7 equivalentes demostrados» (5000/5000/5000/960/30/128/128 casos). Leído
  el script: muta en memoria solo dentro de la función (`_mutar` exige una aparición), los textos coinciden con
  el informe, y cada control negativo **aborta con exit 1 si no distingue** (`_falla(… banco ciego)`); árbol limpio.
- Cambio 3 [x]: `test_f084_clasificado_es_inmutable`, docstring «protege el DISEÑO, no un requisito», sin R7.
- Observación: también se cambió el texto fijo del generador («quedarse en `PENDIENTE`» → «sin escribir») en el
  encabezado de «Ficheros sin mutantes»; inocuo, pero lo regenerará la próxima campaña.

Pasada 1 de evidencias (a HEAD bb8e55f): CHANGES_REQUESTED por esos tres cambios; detalle a continuación.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 90 %, mutación
(uno por línea, muestra 60 %, [100, 300]), cero supervivientes salvo justificación aceptada por el humano,
RM1–RM7 (RM5 con muestra de uno). Campaña **no reejecutada**: «Tiempo total» 7109 s (repaso) y 22865 s
(primera), por encima del umbral de 60 s; recálculo puro + RM1–RM6 + reproducción propia de un equivalente.

## Pasada de evidencias

**Delta 986f868..HEAD** (`git diff --stat`): `progress/` (impl, mutacion .md/.json, review), `tasks.md` (T10 `[x]`)
y tres ficheros de test de sv4 (+104 líneas). **Ningún fichero de producción**: lo aprobado sigue en pie.

**init.sh** (`bash harness/init.sh`, a HEAD bb8e55f; caché permitida): **exit 0 a la 3.ª**. Las 1.ª y
2.ª, rojas solo en `tests/test_f059_ejecucion.py::test_f059_r9_…` (`nieto.pid`, inestable conocido; 55 procesos
python en la máquina); el fichero aislado, 98 passed. 3.ª: raíz 2549 passed/50 skip (34 min); sv1–sv5 por
caché (sv4, verde de las 07:00 con los 11 tests nuevos, nada de sv4 cambió después); cobertura 100,0 % (303/303),
tamaño, carril y e2e en [OK]/N/A.

**Recálculo independiente** (`harness.alcance` + `generar_mutantes`, puro): 8 ficheros, **646** líneas,
**198** mutantes, **131** candidatos uno por línea; tope = max(100, ceil(0,6·131)=79) = **100**. Coincide fila a
fila con el informe. Muestreados 3 supervivientes (`pcp:144`, `repo:5035`, `app:2300`): existen con el mismo
operador `veracidad` y el mismo texto original→mutado.
**Ficheros sin mutantes** (prueba de control sin exclusión de alcance): `recalculo_publisher.py` da 3 mutantes en
el fichero entero y 0 en sus líneas 52–54; `identidad.py`, 42 y 0 en 10–16. Generador sano; el cero es
legítimo (dos constantes de cadena y un docstring), **pero la declaración no está escrita** (cambio 1).

**Coherencia informe ↔ logs** (`scratchpad/mutacion_F-084.log` y `_repaso.log`):
- Primera pasada: HEAD 8474ce9, «100 evaluados, 82 muertos, 18 supervivientes, 0 timeouts, 0 sin veredicto
  en 22864.8 s» = tabla de 4320031. Repaso: «27 evaluados, 20 muertos, 7 supervivientes … en 7109.1 s»;
  27 = 18 reevaluados + 9 de control (max(5, ceil(0,1·82))); 73 reutilizados + 20 = **93 muertos**. Los 9 de
  control (líneas 19–27 del log) salen muertos. 8474ce9 es antepasado de 6ef7b5e. Líneas base en verde en los 3
  worktrees (623–644 s); «Sin veredicto (base rota)» 0; sin cabecera de campaña no válida.

| Punto C4 bis / RM | Estado | Motivo |
|---|---|---|
| Mutación del nivel, informe real | [x] | totales recalculados; muestra y modo incremental conformes a `rigor.json` |
| **RM1** SHA medido | [x] | 6ef7b5e; desde ahí solo `progress/` (`git diff --stat 6ef7b5e..HEAD`); 8474ce9→6ef7b5e solo tests |
| **RM2** coherencia del tiempo | [x] | 27×263,3 = 7109 s; 100×228,6 = 22860 s; media de pared ÷3 workers, por suite 627,8 s ≈ base |
| **RM3** equivalente muerto | [x] | ninguno de los 7 equivalentes murió; el `frozen=False` sobrevivió en la 1.ª pasada (coherente) |
| **Supervivientes sin PENDIENTE** | **[ ]** | `mutacion_F-084.md`: los 7 análisis y las 2 declaraciones siguen en `PENDIENTE` (19 marcas) |
| **RM5** demostración ejecutable | **[ ]** | no hay `progress/equivalentes_F-084.py` ni equivalente: «probado»/«comprobado» en prosa |
| **RM6** guardas quitadas | [x] | el delta no toca producción: ninguna guarda quitada |
| Cero supervivientes salvo aceptación | pendiente | 7 equivalentes a la espera de la aceptación escrita del humano (ver criterio abajo) |
| «Evidencias» con workers | [x] | 3 workers declarados en el informe y en el log |
| Capa e2e | N/A | `CAPA E2E: N/A`, ningún requisito `(capa: e2e)` |

## Criterio sobre los 7 «equivalentes» (uno por uno; la aceptación es del humano)

1. **`pcp:144`** `fecha_int is not None and fecha_int > 0` → `fecha_int and …`: **equivalente.** Con None/0 da
   None/0 en vez de False; `_fecha_valida` es privada y sus 3 llamadores (171, 185, 225) la usan con `not`; no
   hay más (grep en sv4). **RM5 reproducido por mí** en memoria, sin tocar el árbol
   (`scratchpad/rm5/rm5_f084.py`): `motivos_activo`, `fecha_posterior_al_correo` y `clasificar` iguales en
   5.000 casos con None, 0, −5, 1 y fechas reales; control negativo (`>= 0`) sí distingue. Exit 0.
2. **`pcp:174`** `recibido is None` → `not recibido`: **equivalente.** `_instante` tiene 3 `return`: None (except),
   `momento.replace(tzinfo=…)` y `momento.astimezone(…)`; un `datetime` nunca es falso.
3. **`pcp:244`** `sustituto is None` → `not sustituto`: **equivalente hoy.** Único llamador `clasificar:273`, que
   pasa `elegir_sustituto` (None, `por_id.get` sobre `DocProblema` o un candidato `DocProblema`); `DocProblema`
   es dataclass sin `__bool__`/`__len__`. `motivo_sustituido` es pública: equivalencia de dominio, no de firma.
4. **`repo:4910`** `motivo is None` → `not motivo`: **equivalente.** `_motivo_congelado_doc` →
   `motivo_congelacion_documento`, 5 `return`: None o `MOTIVO_DOC_ENCOLADO/REGISTRADO/DEDICACION/APROBADO`
   (este = `MOTIVO_LINEA_APROBADA`), las cuatro cadenas no vacías.
5. **`repo:5035`** `motivo is not None` → `if motivo`: **equivalente.** `motivo_no_recuperable`, 4 `return`:
   `MOTIVO_NO_REC_ACTIVO/PAPELERA/RETIRADO` (no vacías) o None.
6. **`app:2284`** `parsed is None` → `not parsed`: **equivalente.** `_parse_fecha_to_iso_int`: 3 `return None` y
   una tupla de 2; nunca vacía. Único otro llamador (`:2212`) no está mutado.
7. **`app:2300`** `res is None` → `not res`: **equivalente.** Una sola implementación de `recuperar_parte`
   (`parte_repository.py:5020`; `_RepoRoto` hereda de ella): None o `{"document_id", "fecha"}`.

Ninguno se vuelve observable con un valor falso alcanzable. Mi criterio: los 7 son aceptables.

## Los 11 tests nuevos (c38ed73)

Todos en verde, en ficheros ya existentes de F-084, sin tocar ni aflojar tests previos. Comportamiento de
requisito, bien anclados: `r8_pista_exige_creado_estrictamente_despues` (R8 «posterior»),
`r11_sin_fecha_va_tras_cualquier_fecha` (design §6 «fecha descendente»), `r5_ddl_declara_las_columnas_del_rastro`
(R5 pide literalmente `String(36)`/`String(64)` y el `ADD COLUMN IF NOT EXISTS` de `ddl_complementario()`: es
el requisito, no un detalle), `r12_tiene_pdf_exige_drive_e_item`, `r19_obra_ide_cero_es_una_obra`,
`r23_la_descripcion_del_deshacer_lleva_la_obra`, `r10_la_cabecera_cuenta_solo_los_que_cuentan` (sustituido de
otro envío no cuenta: R10/D3) y `r22_el_404_lleva_ok_false`.
- **`test_f084_r7_clasificado_es_inmutable`: mal anclado.** R7 es el motivo único de un SUSTITUIDO; el test
  usa un activo sin obra (R6) y afirma `FrozenInstanceError`, un detalle de implementación que ni R7 ni design
  §5 piden (design solo declara `frozen=True` para `DocProblema`). En producción nadie muta ni hashea un
  `Clasificado` (`clasificar`, `resumen`, `_fila_problema`). Es un test puesto para matar el mutante y su
  nombre infla la traza de R7 (cambio 3).
- `r25_las_rutas_nuevas_no_salen_en_el_esquema`: lo que fija es design §7 («todas `include_in_schema=False`»);
  solo `/api/problemas/resumen` es de R25. Legítimo; observación 5.

## Cambios requeridos (pasada 1 de evidencias; los tres, atendidos en la pasada 2)

1. Rellenar los 7 análisis y las 2 declaraciones `PENDIENTE` de `progress/mutacion_F-084.md`.
2. RM5: demostración ejecutable de los 7 equivalentes (`progress/equivalentes_F-084.py`) con control negativo.
3. `test_f084_r7_clasificado_es_inmutable`: quitar (y declarar `pcp:110` equivalente) o renombrar sin R7.

## Observaciones (no bloquean)

5. `r25_las_rutas_nuevas_no_salen_en_el_esquema` se apoya en design §7 más que en R25; vale como está.
6. El repaso `--incremental` reescribe `mutacion_F-084.md` y borra lo rellenado a mano: rellenar después.

## Pasada principal (resumen, SHA aprobado 986f868)

- Ciclo 1 (8f559d1): CHANGES_REQUESTED por MANUAL M1–M3 en `current.md`, `undo_log.actor` mal documentado e
  init.sh sin exit 0; ciclo 2 (986f868): los tres atendidos, APPROVED.
- C1–C5, C3 bis/ter/quater, C4 ter: `[x]` o N/A justificado (hexagonal, gemelos `orm_models.py` byte-idénticos,
  `azure-apps` e09fd49 solo `partes.md`, sin push). C4 bis principal: RED con salida real (T1, T3, T5, T7),
  cobertura 100,0 % (303/303), «Evidencias» completa, e2e N/A.
- **RM7** aplicada a mano en copia desechable: bajar el recálculo antes de `recuperar_parte` y mover tras el
  `commit` el choque, el sha256, la congelación y la espera de recálculo ⇒ ROJO, cazado por tests de F-084.
- Trazabilidad R1–R26 → `test_f084_rN_*` en A (sv3 `test_f084_rastro_reemplazo.py`), C (`clasificacion`),
  P (`recuperar`) y W (`portal`): todos con ≥ 1 test en verde; tabla completa en la versión 8474ce9 de este fichero.
- Observaciones de la principal (vigentes): 1) riesgo §10, clave F-050 por línea frente al conjunto de sv3
  (dos activos posibles en dos filas); 2) «Ver PDF» solo con `preview_enabled`; 3) «en Sigrid» agrupa tres
  estados; 4) `_choques` con dos líneas sin trabajador da un falso 409 (lado seguro).

## Automejora (propuesta, no aplicada)

- `harness.mutacion --incremental` podría conservar los análisis ya rellenos de los supervivientes que
  repiten (mismo fichero, línea y texto) en vez de regenerarlos en `PENDIENTE`: aquí se perdió ese paso.
- `reviewer.md`/C4 bis: decir que un test añadido para matar un mutante solo lleva `rN` si afirma ese requisito.
