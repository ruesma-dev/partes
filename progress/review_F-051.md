<!-- progress/review_F-051.md -->
Revisión completa (pasada 1), `git diff dev...HEAD` con HEAD `8818271`.

# F-051 · Extracción fila a fila — review

- **Veredicto: APPROVED**
- **Nivel de rigor:** `estandar` (declarado en `features.json`): fase RED, cobertura de
  lo cambiado ≥ 80 % y mutación muestreada (20, semilla `20260820`) con supervivientes
  analizados. RM5 N/A (solo `critico`).
- **Fuera del veredicto (encargo del líder):** M1/M2 (T10, T11) y la línea de
  `azure-apps/partes.md` para `REVISAR_TABLA_DISPERSA`; constan como pendientes en
  `progress/impl_F-051.md` y `progress/current.md` (con el texto propuesto).

## Verificación ejecutada (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | exit 0, **ENTORNO LISTO**; raíz `493 passed, 3 skipped` |
| sv2 / sv3 (sin caché, lanzadas por mí) | `32 passed` (24 F-051 + 8 F-023) / `2254 passed in 29.09s` |
| sv1, sv4, sv5 | verdes (caché de init.sh; sin diff en esos servicios) |
| Puertas | COBERTURA `[OK] 100.0% de 66 líneas`; TAMAÑO `[OK]` (148/150, 249/250, 186/220) |
| Tests existentes | ninguno tocado (el diff en `tests/` solo trae los 3 `test_f051_*`); árbol limpio |

## Lo que pedía comprobar el líder

- **Prompt R1–R8.** `prompts.yaml` cambia en tres hunks y nada más: una viñeta en
  «Reglas absolutas» de `system`; bloque «LECTURA FILA A FILA» + viñeta
  `numero_linea_horas` en el punto 3; `schema_hint` (`numero_linea_horas`, `dni` y una
  línea en «Reglas de tipo», que vive dentro de `schema_hint`). Cabecera, firma,
  puntos 4–6 y catálogo intactos; los 8 tests de F-023 pasan sin tocarse (R8). La línea
  «Para cada fila, rellena:» es pulido permitido por `design.md` §5 y está anotada.
- **JSON Schema real.** Gemini recibe `ParteTrabajo.model_json_schema()` como
  `response_json_schema` (`gemini_genai_client.py:104,128`; `schema_registry` mapea
  `parte_trabajo` → `ParteTrabajo`), que es lo que mide el test R10:
  `numero_linea_horas` justo tras `numero_linea` y antes de las dos horas,
  `integer|null`, sin cotas. Ausente ⇒ `None` (R11); `extra="forbid"` intacto (R12).
  sv4/sv5 no parsean `raw_extraction_json` con modelo estricto: la clave no rompe nada.
- **Red de sv3 pura (R17).** `lectura_dudosa.py` solo importa
  `domain.models.parte_records`. El normalizer solo asigna `parte.lectura_dudosa` antes
  del bucle (`test_f051_r17_los_registros_no_cambian`: registros idénticos). En
  `_compute_review_required` hay un único `return True` nuevo y ningún `return False`
  previo: solo puede subir el flag. Nada en sv3 lo baja después.
- **Interruptor.** Solo entra en `if tabla_dispersa and alguna_con_horas and vacias`;
  la autocomprobación no lo mira (tests de interruptor apagado en detector y
  normalizer; R13 probada con `tabla_dispersa=False`). Defecto `True`, se apaga por
  entorno y `build_app` (único constructor de producción) lo pasa.
- **LÍMITE DE SERVICIO.** sv2 pide el dato y sv3 lo juzga; nada copiado entre
  servicios, ninguna gemela de la lista cerrada ni `orm_models.py` tocadas.
  `_a_float`/`_a_int` repiten dentro de sv3 la tolerancia del normalizer para evitar
  un import circular (justificado; no cruza servicios).
- **Datos personales.** Nombres sintéticos («TRABAJADOR UNO»…, «Trabajador A») y DNIs
  de relleno ya presentes en el repo (`11111111H` en `test_f013_informe_sesame.py`).
  Barrido `\d{8}[A-Z]` y `[XYZ]\d{7}[A-Z]` sobre las líneas añadidas: solo esa lista.
  Spec, ARCHITECTURE e informes solo citan obra 0686 y fechas. El WARNING lleva fecha,
  nº de obra, motivo y filas, y un test lo comprueba sin nombres ni DNIs.

## Mutación (C4 bis, RM1–RM6)

- **Tiempo total 207 s (> 60 s): campaña no reejecutada**; recálculo puro + RM1–RM6.
- **Recálculo** (`harness.alcance` + `generar_mutantes`): 162 líneas, 7 ficheros,
  **31 mutantes**, igual que el informe. Rehecho el sorteo con
  `random.Random(20260820).sample(…, 20)`: los mismos 20, con los 3 supervivientes
  (`:32` logico, `:73` entero, `parte_records.py:113` booleano) con idéntico texto.
- **RM1.** Medido en `b06420b…`; de ahí a HEAD solo cambian tests, `progress/` y
  `tasks.md`: ningún fichero del alcance.
- **RM2.** Base 26–27 s; media 10,4 s × 3 workers ≈ 31 s por mutante, coherente con
  17/20 muertos con `-x`; `20 × 10,4 ≈ 207 s`. Sin «CAMPAÑA NO VÁLIDA» ni base rota.
- **RM3.** Los 17 muertos cambian el comportamiento (`or`↔`and`, `is None`↔
  `is not None`, `==`, flag a `False`, clave de orden). Ninguno equivalente.
- **RM4.** En una copia de sv3 en el scratchpad apliqué los dos supervivientes
  «cazados»: `n or 1` hace fallar `…_una_fila_cero_se_ordena_antes_que_la_uno` y
  `frozen=False` hace fallar `…_el_motivo_es_inmutable_y_hashable` (`1 failed,
  43 passed` en los dos). Confirmado.
- **Equivalente `:32`** (`or` → `and` en `_a_float`): justificación correcta (`None` y
  `""` acaban en `None` por la excepción de `float()`). **RM6:** no se quitó ninguna
  guarda; los huecos se cerraron con tests.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] solo F-051 `in_progress` · [x] rama `feature/F-051-…` · [x] `current.md`:
  sección F-051 arriba; el resto es el registro acumulado de pendientes que ya había en
  `dev` (mismo criterio que las reviews de F-046 y F-048) · [x] `done` en `history.md`.
- **C3** [x] hexagonal (`MotivoLectura` en domain para no importar application) ·
  [x] primera línea con ruta · [x] sin prints, secretos ni dependencias; ruff 732 → 734
  por dos `UP045` (`Optional[int]`), estilo de esos ficheros · [x] trampas
  empleado ≠ recurso, incidencias y ORM duplicado: no se tocan.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1–R17 trazados y en verde (tabla abajo) · [x] sin red ni BBDD (YAML real,
  Pydantic, dobles) · [x] M1/M2 pendientes en `current.md` e impl; el comando exacto
  (`curl … /v1/partes/extract`) está en `design.md` §9, enlazado.
- **C4 bis** [x] rigor declarado · [x] RED con trazas reales (T1, T3, T5, T6→T7) ·
  [x] cobertura `[OK]` 100 % · [x] informe de mutación verificado · [x] muertos:
  >60 s, recálculo puro + RM4, dicho aquí · [x] coste por mutante ≈ 31 s ·
  [x] sin cabecera de campaña no válida · [x] RM1 · [x] RM2 · N/A RM5 (nivel
  `estandar`) · [x] RM6 · N/A campaña manual (la automática generó 31) ·
  [x] 3 supervivientes analizados, ninguno PENDIENTE · [x] «Evidencias» completa,
  workers (`--workers 3`) en T9 y en el informe de mutación.
- **C4 ter** N/A: el repo no declara `harness/rutas_sensibles.json` (solo el ejemplo).
  Ver automejora 1.
- **C5** [x] T1–T9 y T12 `[x]` con commit `F-051 Tn:` (T8 en dos, explicado); T10/T11
  en `[ ]` por ser las MANUAL M1/M2 del líder, documentadas como pendientes ·
  [x] árbol limpio · [x] `features.json` en `in_progress`, a la espera de M1/M2.

## Cobertura requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f051_r1_el_system_prohibe_…`, `…_identifica_la_fila_por_numero_y_dni`, `…_el_bloque_cubre_todas_las_cifras_…` |
| R2–R5 | `test_f051_r2_recorrido_fila_a_fila_…`, `test_f051_r3_*` (2), `test_f051_r4_escaneos_girados_…`, `test_f051_r5_todas_las_filas_…` |
| R6 | `test_f051_r6_vineta_numero_linea_horas_en_el_punto_3`, `…_la_vineta_va_tras_numero_linea_…` |
| R7 | `test_f051_r7_el_schema_hint_lista_dni_…`, `…_las_reglas_de_tipo_dicen_entero_o_null` |
| R8 | 8 tests de F-023 sin tocar y en verde + diff de `prompts.yaml` revisado |
| R9–R12 | `test_f051_r9_*` (4), `test_f051_r10_*` (2), `test_f051_r11_*`, `test_f051_r12_*` |
| R13 | `test_f051_r13_*` (9: ordinaria, extra negativa, varias filas, coherente, sin horas, sin `numero_linea`, texto, ilegibles) |
| R14 | `test_f051_r14_*` (caso 17/10 leído y en papel, incidencia, trabajador, interruptor en detector, normalizer, Settings y build_app) |
| R15 | `test_f051_r15_*` (WARNING sin datos personales, dos motivos, `_compute_review_required`, ingesta completa) |
| R16 | `test_f051_r16_sin_numero_linea_horas_no_salta` (ausente, null, ""), `…_parte_anterior_sin_la_clave_…` |
| R17 | `test_f051_r17_*` (registros iguales, `review_required` como hoy, lleno y coherente sin revisión, no-dict) |
| R18–R20 | MANUAL M1/M2 (T10, T11), del líder, fuera de este veredicto |

## Cambios requeridos: ninguno.

## Observaciones (no bloquean)

1. `docs/referencia/partes-proyecto.md` (documento maestro) no menciona la lectura
   dudosa ni `REVISAR_TABLA_DISPERSA` (F-046 sí anotó ahí su interruptor). El diseño no
   lo pedía; a criterio del líder.

## Automejora propuesta (no aplicada)

1. **Declarar `harness/rutas_sensibles.json` en este repo** con
   `services/partes-api/config/prompts.yaml` y `domain/models/parte_models.py` →
   informe de verificación con PDF/modelo, exigencia `aviso`. Un cambio de prompt no
   se verifica con tests unitarios, y C4 ter queda N/A justo en su caso de diseño.
2. **`CHECKPOINTS.md` C5**: aclarar que una tarea `MANUAL (humano o líder)` puede
   quedar en `[ ]` al pasar la review si consta pendiente en `current.md`; hoy cada
   reviewer lo justifica por su cuenta.
